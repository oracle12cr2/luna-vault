#!/usr/bin/env python3
"""
한국 주식 실시간 모니터링 시스템
매 1-2분마다 데이터 수집하고 변동사항 알림
"""

import cx_Oracle
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import os
import signal
import sys
import argparse
import json

class RealTimeStockMonitor:
    def __init__(self):
        # TNS 설정
        os.environ['TNS_ADMIN'] = '/usr/lib/oracle/23/client64/lib/network/admin'
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 모니터링 종목 (더 빠른 테스트를 위해 5개만)
        self.monitored_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660', 
            'NAVER': '035420',
            'LG전자': '066570',
            '현대차': '005380'
        }
        
        self.connection = None
        self.running = True
        self.last_prices = {}  # 이전 가격 저장
        
        # 신호 핸들러 등록
        signal.signal(signal.SIGINT, self.stop_monitoring)
        signal.signal(signal.SIGTERM, self.stop_monitoring)
    
    def stop_monitoring(self, signum, frame):
        """모니터링 중지"""
        print(f"\n🛑 모니터링 중지 신호 수신 (Signal {signum})")
        self.running = False
    
    def connect_db(self):
        """오라클 연결"""
        try:
            self.connection = cx_Oracle.connect('hr/oracle@PROD', encoding='UTF-8')
            print("✅ 오라클 연결 성공")
            return True
        except Exception as e:
            print(f"❌ 오라클 연결 실패: {e}")
            return False
    
    def get_current_price(self, stock_code):
        """현재가 및 기본 정보 빠르게 수집"""
        url = "https://fchart.stock.naver.com/sise.naver"
        params = {
            'timeframe': 'minute',
            'count': 5,  # 최근 5개만
            'requestType': 0,
            'symbol': stock_code
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            response.encoding = 'euc-kr'
            
            if response.status_code != 200:
                return None
                
            root = ET.fromstring(response.text)
            chartdata = root.find('chartdata')
            
            if chartdata is None:
                return None
                
            stock_name = chartdata.get('name')
            items = chartdata.findall('item')
            
            if not items:
                return None
            
            # 최신 데이터만 파싱
            latest_item = items[-1]
            data = latest_item.get('data')
            
            if not data:
                return None
                
            parts = data.split('|')
            if len(parts) < 6:
                return None
            
            datetime_str = parts[0]
            close_price = parts[4] if parts[4] != 'null' else None
            volume = parts[5] if parts[5] != 'null' else None
            
            if not close_price:
                return None
                
            # 시간 파싱
            if len(datetime_str) >= 12:
                try:
                    year = int(datetime_str[:4])
                    month = int(datetime_str[4:6])
                    day = int(datetime_str[6:8])
                    hour = int(datetime_str[8:10])
                    minute = int(datetime_str[10:12])
                    
                    trade_datetime = datetime(year, month, day, hour, minute)
                    
                    return {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'price': int(close_price),
                        'volume': int(volume) if volume else 0,
                        'datetime': trade_datetime
                    }
                except ValueError:
                    return None
            
            return None
            
        except Exception as e:
            print(f"⚠️ {stock_code} 데이터 수집 실패: {str(e)[:50]}")
            return None
    
    def save_realtime_data(self, stock_data):
        """실시간 데이터 오라클 저장"""
        if not self.connection or not stock_data:
            return False
            
        cursor = self.connection.cursor()
        
        try:
            # 빠른 UPSERT
            cursor.execute("""
                MERGE INTO STOCK_MINUTE_DATA target
                USING (
                    SELECT :stock_code as STOCK_CODE,
                           :stock_name as STOCK_NAME,
                           :trade_datetime as TRADE_DATETIME,
                           :close_price as CLOSE_PRICE,
                           :volume as VOLUME
                    FROM DUAL
                ) source
                ON (target.STOCK_CODE = source.STOCK_CODE 
                    AND target.TRADE_DATETIME = source.TRADE_DATETIME)
                WHEN NOT MATCHED THEN
                INSERT (STOCK_CODE, STOCK_NAME, TRADE_DATETIME, CLOSE_PRICE, VOLUME)
                VALUES (source.STOCK_CODE, source.STOCK_NAME, source.TRADE_DATETIME,
                        source.CLOSE_PRICE, source.VOLUME)
                WHEN MATCHED THEN
                UPDATE SET 
                    CLOSE_PRICE = source.CLOSE_PRICE,
                    VOLUME = source.VOLUME
            """, {
                'stock_code': stock_data['stock_code'],
                'stock_name': stock_data['stock_name'],
                'trade_datetime': stock_data['datetime'],
                'close_price': stock_data['price'],
                'volume': stock_data['volume']
            })
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"💾 저장 실패: {str(e)[:50]}")
            return False
        finally:
            cursor.close()
    
    def detect_changes(self, stock_data):
        """가격 변동 감지"""
        stock_code = stock_data['stock_code']
        current_price = stock_data['price']
        
        if stock_code in self.last_prices:
            last_price = self.last_prices[stock_code]['price']
            last_time = self.last_prices[stock_code]['time']
            
            # 가격 변동 계산
            change = current_price - last_price
            change_rate = (change / last_price) * 100 if last_price > 0 else 0
            
            # 시간 간격 계산
            time_diff = (stock_data['datetime'] - last_time).total_seconds() / 60
            
            return {
                'changed': change != 0,
                'change': change,
                'change_rate': change_rate,
                'time_diff': time_diff,
                'significant': abs(change_rate) >= 0.5  # 0.5% 이상 변동을 유의미하게 간주
            }
        
        # 첫 번째 수집인 경우
        return {'changed': False, 'change': 0, 'change_rate': 0, 'time_diff': 0, 'significant': False}
    
    def print_realtime_status(self, all_data):
        """실시간 현황 출력"""
        # 화면 지우기
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🔴 실시간 주식 모니터링")
        print("=" * 80)
        print(f"📅 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 모니터링 종목: {len(all_data)}개")
        print("-" * 80)
        
        # 변동률 기준 정렬
        sorted_data = sorted(all_data, key=lambda x: x.get('change_info', {}).get('change_rate', 0), reverse=True)
        
        print(f"{'종목명':<12} {'현재가':<10} {'변동':<12} {'등락률':<8} {'거래량':<12} {'시간':<8}")
        print("-" * 80)
        
        for data in sorted_data:
            name = data['stock_name']
            price = data['price']
            volume = data['volume']
            time_str = data['datetime'].strftime('%H:%M')
            
            change_info = data.get('change_info', {})
            
            if change_info.get('changed', False):
                change = change_info['change']
                rate = change_info['change_rate']
                
                if change > 0:
                    symbol = '📈'
                    change_str = f"+{change:,}원"
                    rate_str = f"+{rate:.1f}%"
                elif change < 0:
                    symbol = '📉'
                    change_str = f"{change:,}원"
                    rate_str = f"{rate:.1f}%"
                else:
                    symbol = '➡️'
                    change_str = "0원"
                    rate_str = "0.0%"
                
                # 유의미한 변동은 강조
                if change_info.get('significant', False):
                    symbol = '🚨' + symbol
            else:
                symbol = '🔵'
                change_str = "첫수집"
                rate_str = "0.0%"
            
            print(f"{symbol} {name:<10} {price:>8,}원 {change_str:<10} {rate_str:<6} {volume:>10,} {time_str:<8}")
        
        print("-" * 80)
        print("💡 Ctrl+C로 중지 | 📈=상승 📉=하락 🚨=급변동 🔵=신규")
    
    def start_monitoring(self, interval=60):
        """실시간 모니터링 시작"""
        if not self.connect_db():
            return
            
        print(f"🔴 실시간 모니터링 시작 (간격: {interval}초)")
        print(f"📊 모니터링 종목: {list(self.monitored_stocks.keys())}")
        print("💡 Ctrl+C로 중지")
        print("-" * 50)
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                all_data = []
                
                print(f"\n🔄 수집 사이클 {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                for stock_name, stock_code in self.monitored_stocks.items():
                    # 현재가 수집
                    stock_data = self.get_current_price(stock_code)
                    
                    if stock_data:
                        # 변동 감지
                        change_info = self.detect_changes(stock_data)
                        stock_data['change_info'] = change_info
                        
                        # 데이터베이스 저장
                        saved = self.save_realtime_data(stock_data)
                        
                        # 이전 가격 업데이트
                        self.last_prices[stock_code] = {
                            'price': stock_data['price'],
                            'time': stock_data['datetime']
                        }
                        
                        all_data.append(stock_data)
                        
                        # 유의미한 변동 알림
                        if change_info.get('significant', False):
                            change = change_info['change']
                            rate = change_info['change_rate']
                            print(f"🚨 {stock_name}: {change:+,}원 ({rate:+.1f}%) - 급변동 감지!")
                    
                    time.sleep(0.2)  # API 제한
                
                # 실시간 현황 출력
                if all_data:
                    self.print_realtime_status(all_data)
                
                # 다음 사이클까지 대기
                print(f"\n⏱️ {interval}초 후 다음 수집...")
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    if i % 10 == 0 and i > 0:  # 10초마다 점 출력
                        print(".", end="", flush=True)
                
            except KeyboardInterrupt:
                print("\n🛑 사용자에 의한 중지")
                break
            except Exception as e:
                print(f"\n❌ 모니터링 오류: {e}")
                print("⏱️ 5초 후 재시도...")
                time.sleep(5)
        
        print("\n✅ 실시간 모니터링 종료")
        if self.connection:
            self.connection.close()
    
    def get_today_summary(self):
        """오늘 거래 요약"""
        if not self.connection:
            return
            
        cursor = self.connection.cursor()
        
        try:
            print("\n📊 오늘 거래 요약")
            print("-" * 50)
            
            cursor.execute("""
                WITH daily_stats AS (
                    SELECT stock_name,
                           MIN(close_price) as low_price,
                           MAX(close_price) as high_price,
                           (SELECT close_price FROM stock_minute_data s1 
                            WHERE s1.stock_code = s.stock_code 
                            AND TRUNC(s1.trade_datetime) = TRUNC(SYSDATE)
                            ORDER BY s1.trade_datetime ASC 
                            FETCH FIRST 1 ROWS ONLY) as open_price,
                           (SELECT close_price FROM stock_minute_data s2 
                            WHERE s2.stock_code = s.stock_code 
                            ORDER BY s2.trade_datetime DESC 
                            FETCH FIRST 1 ROWS ONLY) as current_price,
                           COUNT(*) as data_points
                    FROM stock_minute_data s
                    WHERE TRUNC(trade_datetime) = TRUNC(SYSDATE)
                    GROUP BY stock_code, stock_name
                )
                SELECT stock_name, open_price, current_price, low_price, high_price,
                       (current_price - open_price) as change,
                       ROUND((current_price - open_price) * 100.0 / open_price, 2) as change_rate,
                       data_points
                FROM daily_stats
                ORDER BY change_rate DESC
            """)
            
            for row in cursor.fetchall():
                name, open_p, current_p, low_p, high_p, change, rate, points = row
                
                if rate > 0:
                    symbol = "📈"
                elif rate < 0:
                    symbol = "📉"
                else:
                    symbol = "➡️"
                
                print(f"{symbol} {name}")
                print(f"   현재: {current_p:,}원 | 시가: {open_p:,}원 | 고가: {high_p:,}원 | 저가: {low_p:,}원")
                print(f"   변동: {change:+,}원 ({rate:+.1f}%) | 데이터: {points}개")
                print()
                
        except Exception as e:
            print(f"요약 조회 실패: {e}")
        finally:
            cursor.close()

def main():
    parser = argparse.ArgumentParser(description='실시간 주식 모니터링')
    parser.add_argument('--interval', type=int, default=60, help='수집 간격(초), 기본 60초')
    parser.add_argument('--summary', action='store_true', help='오늘 거래 요약만 출력')
    
    args = parser.parse_args()
    
    monitor = RealTimeStockMonitor()
    
    if args.summary:
        if monitor.connect_db():
            monitor.get_today_summary()
            monitor.connection.close()
    else:
        monitor.start_monitoring(args.interval)

if __name__ == "__main__":
    main()