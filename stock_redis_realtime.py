#!/usr/bin/env python3
"""
한국 주식 Redis 캐싱 + 오라클 하이브리드 실시간 시스템
- Redis: 초고속 실시간 캐싱 (메모리)
- Oracle: 장기 데이터 보관 (디스크)
"""

import cx_Oracle
import redis
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import os
import signal
import json
import argparse

class HybridStockSystem:
    def __init__(self):
        # TNS 설정
        os.environ['TNS_ADMIN'] = '/usr/lib/oracle/23/client64/lib/network/admin'
        
        # Redis 연결
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Oracle 연결
        self.oracle_conn = None
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 모니터링 종목
        self.monitored_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660', 
            'NAVER': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220',
            'LG전자': '066570',
            '현대차': '005380'
        }
        
        self.running = True
        signal.signal(signal.SIGINT, self.stop_system)
        signal.signal(signal.SIGTERM, self.stop_system)
    
    def stop_system(self, signum, frame):
        """시스템 중지"""
        print(f"\n🛑 시스템 중지 신호 수신")
        self.running = False
    
    def connect_oracle(self):
        """오라클 연결"""
        try:
            self.oracle_conn = cx_Oracle.connect('hr/oracle@PROD', encoding='UTF-8')
            print("✅ 오라클 연결 성공")
            return True
        except Exception as e:
            print(f"❌ 오라클 연결 실패: {e}")
            return False
    
    def test_redis(self):
        """Redis 연결 테스트"""
        try:
            self.redis_client.ping()
            print("✅ Redis 연결 성공")
            
            # Redis 정보 출력
            info = self.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')
            print(f"   📊 Redis 메모리 사용: {memory_used}")
            return True
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            return False
    
    def get_current_price(self, stock_code):
        """현재가 수집"""
        url = "https://fchart.stock.naver.com/sise.naver"
        params = {
            'timeframe': 'minute',
            'count': 3,
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
            
            # 최신 데이터
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
                        'datetime': trade_datetime,
                        'timestamp': trade_datetime.timestamp()
                    }
                except ValueError:
                    return None
            
            return None
            
        except Exception as e:
            print(f"⚠️ {stock_code} 수집 실패: {str(e)[:50]}")
            return None
    
    def cache_to_redis(self, stock_data):
        """Redis에 실시간 데이터 캐싱"""
        stock_code = stock_data['stock_code']
        
        try:
            # 실시간 가격 정보 (60초 TTL)
            price_key = f"stock:price:{stock_code}"
            price_info = {
                'code': stock_data['stock_code'],
                'name': stock_data['stock_name'],
                'price': stock_data['price'],
                'volume': stock_data['volume'],
                'datetime': stock_data['datetime'].isoformat(),
                'timestamp': stock_data['timestamp']
            }
            self.redis_client.setex(price_key, 60, json.dumps(price_info))
            
            # 최근 가격 히스토리 (최대 50개 보관)
            history_key = f"stock:history:{stock_code}"
            history_entry = f"{stock_data['price']}:{stock_data['timestamp']}"
            self.redis_client.lpush(history_key, history_entry)
            self.redis_client.ltrim(history_key, 0, 49)  # 최근 50개만 보관
            self.redis_client.expire(history_key, 3600)  # 1시간 TTL
            
            # 변동률 계산 및 순위 업데이트
            self.update_change_ranking(stock_data)
            
            return True
            
        except Exception as e:
            print(f"Redis 캐싱 실패 ({stock_code}): {e}")
            return False
    
    def update_change_ranking(self, stock_data):
        """변동률 순위 업데이트 (Sorted Set)"""
        stock_code = stock_data['stock_code']
        current_price = stock_data['price']
        
        try:
            # 오늘 시작가 가져오기 (Redis에서 먼저 확인)
            open_key = f"stock:open:{stock_code}"
            open_price = self.redis_client.get(open_key)
            
            if not open_price:
                # Redis에 없으면 오라클에서 조회
                if self.oracle_conn:
                    cursor = self.oracle_conn.cursor()
                    cursor.execute("""
                        SELECT close_price FROM stock_minute_data
                        WHERE stock_code = :code
                        AND TRUNC(trade_datetime) = TRUNC(SYSDATE)
                        ORDER BY trade_datetime ASC
                        FETCH FIRST 1 ROWS ONLY
                    """, {'code': stock_code})
                    
                    result = cursor.fetchone()
                    if result:
                        open_price = result[0]
                        # Redis에 캐싱 (하루 TTL)
                        self.redis_client.setex(open_key, 86400, str(open_price))
                    cursor.close()
                else:
                    open_price = current_price  # 첫 데이터인 경우
            else:
                open_price = float(open_price)
            
            if open_price and open_price > 0:
                change_rate = ((current_price - float(open_price)) / float(open_price)) * 100
                
                # 변동률 순위 업데이트 (Sorted Set)
                ranking_key = "stock:ranking:change_rate"
                member_data = f"{stock_code}:{stock_data['stock_name']}"
                self.redis_client.zadd(ranking_key, {member_data: change_rate})
                self.redis_client.expire(ranking_key, 300)  # 5분 TTL
                
        except Exception as e:
            print(f"순위 업데이트 실패: {e}")
    
    def save_to_oracle(self, stock_data):
        """오라클에 데이터 저장 (장기 보관용)"""
        if not self.oracle_conn:
            return False
            
        cursor = self.oracle_conn.cursor()
        
        try:
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
                UPDATE SET CLOSE_PRICE = source.CLOSE_PRICE, VOLUME = source.VOLUME
            """, {
                'stock_code': stock_data['stock_code'],
                'stock_name': stock_data['stock_name'],
                'trade_datetime': stock_data['datetime'],
                'close_price': stock_data['price'],
                'volume': stock_data['volume']
            })
            
            self.oracle_conn.commit()
            return True
            
        except Exception as e:
            print(f"오라클 저장 실패: {e}")
            return False
        finally:
            cursor.close()
    
    def get_redis_ranking(self, limit=10):
        """Redis에서 변동률 순위 조회"""
        try:
            ranking_key = "stock:ranking:change_rate"
            # 내림차순으로 TOP 조회
            top_gainers = self.redis_client.zrevrange(ranking_key, 0, limit-1, withscores=True)
            # 오름차순으로 TOP 조회 (하락률)
            top_losers = self.redis_client.zrange(ranking_key, 0, limit-1, withscores=True)
            
            return {
                'gainers': [(member.split(':')[1], float(score)) for member, score in top_gainers],
                'losers': [(member.split(':')[1], float(score)) for member, score in top_losers]
            }
        except Exception as e:
            print(f"순위 조회 실패: {e}")
            return {'gainers': [], 'losers': []}
    
    def get_redis_price(self, stock_code):
        """Redis에서 실시간 가격 조회 (초고속)"""
        try:
            price_key = f"stock:price:{stock_code}"
            cached_data = self.redis_client.get(price_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Redis 조회 실패: {e}")
        return None
    
    def print_realtime_dashboard(self):
        """실시간 대시보드 출력"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🚀 Redis 캐싱 실시간 주식 모니터링")
        print("=" * 80)
        print(f"📅 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Redis 상태 정보
        try:
            info = self.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')
            connected_clients = info.get('connected_clients', 'N/A')
            print(f"💾 Redis: {memory_used} 사용 | 연결: {connected_clients}개")
        except:
            pass
        
        print("-" * 80)
        
        # 모든 종목의 실시간 가격
        all_stocks = []
        for name, code in self.monitored_stocks.items():
            cached_data = self.get_redis_price(code)
            if cached_data:
                all_stocks.append((name, cached_data))
        
        if all_stocks:
            print(f"{'종목명':<15} {'현재가':<10} {'거래량':<12} {'시간':<8} {'캐시':<5}")
            print("-" * 60)
            
            for name, data in all_stocks:
                price = data['price']
                volume = data['volume']
                dt = datetime.fromisoformat(data['datetime'])
                time_str = dt.strftime('%H:%M')
                
                print(f"💎 {name:<13} {price:>8,}원 {volume:>10,} {time_str:<8} Redis")
        
        # 변동률 순위
        ranking = self.get_redis_ranking(5)
        
        print(f"\n📈 상승률 TOP 5:")
        for name, rate in ranking['gainers'][:5]:
            print(f"  🚀 {name}: {rate:+.1f}%")
        
        print(f"\n📉 하락률 TOP 5:")
        for name, rate in ranking['losers'][:5]:
            print(f"  📉 {name}: {rate:+.1f}%")
        
        print("-" * 80)
        print("⚡ Redis 캐싱으로 초고속 조회 | 🛑 Ctrl+C로 중지")
    
    def start_hybrid_monitoring(self, interval=30):
        """하이브리드 실시간 모니터링 시작"""
        if not self.test_redis():
            return
        
        if not self.connect_oracle():
            print("⚠️ 오라클 없이 Redis만 사용합니다")
        
        print(f"🚀 하이브리드 실시간 모니터링 시작 (간격: {interval}초)")
        print(f"💾 Redis: 초고속 캐싱 | 🗄️ Oracle: 장기 보관")
        print("-" * 60)
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                print(f"\n🔄 수집 사이클 {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                collected = 0
                cached = 0
                saved = 0
                
                for stock_name, stock_code in self.monitored_stocks.items():
                    # 1. 데이터 수집
                    stock_data = self.get_current_price(stock_code)
                    
                    if stock_data:
                        collected += 1
                        
                        # 2. Redis 캐싱 (초고속)
                        if self.cache_to_redis(stock_data):
                            cached += 1
                        
                        # 3. Oracle 저장 (장기 보관)
                        if self.save_to_oracle(stock_data):
                            saved += 1
                    
                    time.sleep(0.1)  # API 제한
                
                print(f"📊 수집: {collected}개 | Redis: {cached}개 | Oracle: {saved}개")
                
                # 실시간 대시보드
                if collected > 0:
                    self.print_realtime_dashboard()
                
                # 대기
                print(f"\n⏱️ {interval}초 후 다음 수집...")
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    if i % 5 == 0 and i > 0:
                        print(".", end="", flush=True)
                
            except KeyboardInterrupt:
                print("\n🛑 사용자 중지")
                break
            except Exception as e:
                print(f"\n❌ 시스템 오류: {e}")
                time.sleep(5)
        
        print("\n✅ 하이브리드 모니터링 종료")
        if self.oracle_conn:
            self.oracle_conn.close()
    
    def redis_stats(self):
        """Redis 통계 출력"""
        try:
            print("📊 Redis 캐시 통계")
            print("-" * 40)
            
            # 기본 정보
            info = self.redis_client.info()
            print(f"메모리 사용: {info.get('used_memory_human', 'N/A')}")
            print(f"연결된 클라이언트: {info.get('connected_clients', 'N/A')}개")
            print(f"총 키 개수: {self.redis_client.dbsize()}개")
            
            # 주식 관련 키들
            stock_keys = self.redis_client.keys("stock:*")
            print(f"주식 관련 키: {len(stock_keys)}개")
            
            # 실시간 가격 키들
            price_keys = [k for k in stock_keys if k.startswith("stock:price:")]
            print(f"실시간 가격 캐시: {len(price_keys)}개")
            
            if price_keys:
                print("\n💎 캐시된 종목들:")
                for key in price_keys[:10]:  # 최대 10개만
                    try:
                        data = json.loads(self.redis_client.get(key))
                        name = data.get('name', 'N/A')
                        price = data.get('price', 0)
                        dt = datetime.fromisoformat(data.get('datetime', ''))
                        ttl = self.redis_client.ttl(key)
                        print(f"  {name}: {price:,}원 (TTL: {ttl}초)")
                    except:
                        pass
            
            # 변동률 순위
            ranking = self.get_redis_ranking(3)
            if ranking['gainers']:
                print(f"\n📈 실시간 상승률 TOP 3:")
                for name, rate in ranking['gainers'][:3]:
                    print(f"  🚀 {name}: {rate:+.1f}%")
            
        except Exception as e:
            print(f"Redis 통계 오류: {e}")

def main():
    parser = argparse.ArgumentParser(description='Redis 캐싱 실시간 주식 시스템')
    parser.add_argument('--interval', type=int, default=30, help='수집 간격(초)')
    parser.add_argument('--stats', action='store_true', help='Redis 통계만 출력')
    
    args = parser.parse_args()
    
    system = HybridStockSystem()
    
    if args.stats:
        system.redis_stats()
    else:
        system.start_hybrid_monitoring(args.interval)

if __name__ == "__main__":
    main()