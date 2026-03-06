#!/usr/bin/env python3
"""
한국 주식 분봉 데이터 수집기 (SQLite 버전)
네이버에서 분봉 데이터 수집하고 SQLite DB에 저장
나중에 오라클로 이식 가능
"""

import requests
import xml.etree.ElementTree as ET
import sqlite3
from datetime import datetime, timedelta
import time
import json
import argparse
import os

class StockMinuteCollectorSQLite:
    def __init__(self, db_path="stock_minute.db"):
        """
        초기화
        db_path: SQLite 데이터베이스 파일 경로
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.db_path = db_path
        
        # 주요 종목 (더 많이 추가)
        self.major_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660', 
            'NAVER': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220',
            '삼성바이오로직스': '207940',
            '현대차': '005380',
            '기아': '000270',
            'LG전자': '066570',
            'KB금융': '105560'
        }
        
        self.connection = None
        
    def connect_db(self):
        """SQLite DB 연결"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            # Row factory 설정으로 딕셔너리처럼 사용 가능
            self.connection.row_factory = sqlite3.Row
            print(f"✅ SQLite DB 연결 성공 ({self.db_path})")
            return True
            
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            return False
    
    def create_tables(self):
        """주식 데이터 테이블 생성"""
        if not self.connection:
            print("DB 연결이 필요합니다.")
            return False
            
        cursor = self.connection.cursor()
        
        # 분봉 데이터 테이블
        minute_table_ddl = """
        CREATE TABLE IF NOT EXISTS stock_minute_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            trade_datetime TEXT NOT NULL,
            open_price INTEGER,
            high_price INTEGER,
            low_price INTEGER,
            close_price INTEGER,
            volume INTEGER,
            created_date TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(stock_code, trade_datetime)
        )
        """
        
        # 인덱스
        index_ddl = """
        CREATE INDEX IF NOT EXISTS idx_stock_minute_code_date 
        ON stock_minute_data (stock_code, trade_datetime)
        """
        
        # 종목 정보 테이블
        stock_info_ddl = """
        CREATE TABLE IF NOT EXISTS stock_info (
            stock_code TEXT PRIMARY KEY,
            stock_name TEXT NOT NULL,
            market_type TEXT,
            sector TEXT,
            last_updated TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
        
        try:
            print("📝 테이블 생성 중...")
            cursor.execute(minute_table_ddl)
            cursor.execute(index_ddl)
            cursor.execute(stock_info_ddl)
            
            self.connection.commit()
            print("✅ 테이블 생성 완료")
            return True
            
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            return False
        finally:
            cursor.close()
    
    def get_minute_data(self, stock_code, count=240):
        """분봉 데이터 수집"""
        url = f"https://fchart.stock.naver.com/sise.naver"
        params = {
            'timeframe': 'minute',
            'count': count,
            'requestType': 0,
            'symbol': stock_code
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.encoding = 'euc-kr'  # 한글 인코딩
            
            if response.status_code != 200:
                return None
                
            # XML 파싱
            root = ET.fromstring(response.text)
            chartdata = root.find('chartdata')
            
            if chartdata is None:
                return None
                
            stock_name = chartdata.get('name')
            items = chartdata.findall('item')
            
            minute_data = []
            
            for item in items:
                data = item.get('data')
                if not data:
                    continue
                    
                parts = data.split('|')
                if len(parts) < 6:
                    continue
                
                datetime_str = parts[0]
                open_price = parts[1] if parts[1] != 'null' else None
                high_price = parts[2] if parts[2] != 'null' else None
                low_price = parts[3] if parts[3] != 'null' else None
                close_price = parts[4] if parts[4] != 'null' else None
                volume = parts[5] if parts[5] != 'null' else None
                
                # 날짜시간 파싱 (202602110830)
                if len(datetime_str) >= 12:
                    try:
                        year = int(datetime_str[:4])
                        month = int(datetime_str[4:6])
                        day = int(datetime_str[6:8])
                        hour = int(datetime_str[8:10])
                        minute = int(datetime_str[10:12])
                        
                        trade_datetime = datetime(year, month, day, hour, minute)
                        
                        minute_data.append({
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'trade_datetime': trade_datetime.isoformat(),
                            'open_price': int(open_price) if open_price else None,
                            'high_price': int(high_price) if high_price else None,
                            'low_price': int(low_price) if low_price else None,
                            'close_price': int(close_price) if close_price else None,
                            'volume': int(volume) if volume else None
                        })
                    except ValueError:
                        continue
            
            return minute_data
            
        except Exception as e:
            print(f"데이터 수집 실패 ({stock_code}): {e}")
            return None
    
    def save_minute_data(self, minute_data):
        """분봉 데이터를 DB에 저장 (UPSERT)"""
        if not self.connection or not minute_data:
            return 0
            
        cursor = self.connection.cursor()
        
        # SQLite UPSERT 구문
        upsert_sql = """
        INSERT INTO stock_minute_data 
        (stock_code, stock_name, trade_datetime, open_price, high_price, 
         low_price, close_price, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(stock_code, trade_datetime) DO UPDATE SET
            stock_name = excluded.stock_name,
            open_price = excluded.open_price,
            high_price = excluded.high_price,
            low_price = excluded.low_price,
            close_price = excluded.close_price,
            volume = excluded.volume
        """
        
        saved_count = 0
        
        try:
            for data in minute_data:
                cursor.execute(upsert_sql, (
                    data['stock_code'], data['stock_name'], data['trade_datetime'],
                    data['open_price'], data['high_price'], data['low_price'],
                    data['close_price'], data['volume']
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            
            self.connection.commit()
            print(f"💾 {saved_count}개 분봉 데이터 저장 완료")
            return saved_count
            
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            self.connection.rollback()
            return 0
        finally:
            cursor.close()
    
    def save_stock_info(self, stock_code, stock_name):
        """종목 정보 저장"""
        if not self.connection:
            return
            
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO stock_info (stock_code, stock_name)
                VALUES (?, ?)
            """, (stock_code, stock_name))
            
            self.connection.commit()
            
        except Exception as e:
            print(f"종목 정보 저장 실패: {e}")
        finally:
            cursor.close()
    
    def collect_and_save_all(self, count=240):
        """모든 종목 분봉 데이터 수집 및 저장"""
        if not self.connect_db():
            return
            
        if not self.create_tables():
            return
        
        print("📊 분봉 데이터 수집 시작...")
        print(f"📈 수집 대상: {len(self.major_stocks)}개 종목, 각 {count}개 분봉")
        print("=" * 70)
        
        total_saved = 0
        success_count = 0
        
        for stock_name, stock_code in self.major_stocks.items():
            print(f"🔍 수집 중: {stock_name} ({stock_code})")
            
            # 분봉 데이터 수집
            minute_data = self.get_minute_data(stock_code, count)
            
            if minute_data:
                print(f"  📈 {len(minute_data)}개 분봉 데이터 수집")
                
                # 종목 정보 저장
                self.save_stock_info(stock_code, stock_name)
                
                # 분봉 데이터 저장
                saved = self.save_minute_data(minute_data)
                total_saved += saved
                success_count += 1
                
                # 최신 데이터 출력
                if minute_data:
                    latest = minute_data[-1]
                    dt = datetime.fromisoformat(latest['trade_datetime'])
                    print(f"  📅 최신: {dt.strftime('%m-%d %H:%M')} "
                          f"{latest['close_price']:,}원 "
                          f"거래량:{latest['volume']:,}" if latest['volume'] else "")
            else:
                print(f"  ❌ {stock_name} 데이터 수집 실패")
            
            time.sleep(0.3)  # API 호출 제한
        
        print("=" * 70)
        print(f"✅ 총 {total_saved}개 분봉 데이터 저장 완료")
        print(f"📊 성공: {success_count}/{len(self.major_stocks)}개 종목")
        
        # 저장 통계
        self.print_stats()
    
    def print_stats(self):
        """저장된 데이터 통계"""
        if not self.connection:
            return
            
        cursor = self.connection.cursor()
        
        try:
            # 종목별 분봉 데이터 개수
            cursor.execute("""
                SELECT stock_code, stock_name, COUNT(*), 
                       MIN(trade_datetime), MAX(trade_datetime)
                FROM stock_minute_data
                GROUP BY stock_code, stock_name
                ORDER BY stock_code
            """)
            
            print("\n📊 저장된 분봉 데이터 통계:")
            print("-" * 85)
            print(f"{'종목코드':<8} {'종목명':<15} {'데이터수':<8} {'최초일시':<18} {'최신일시':<18}")
            print("-" * 85)
            
            total_records = 0
            for row in cursor.fetchall():
                code, name, count, min_date, max_date = row
                total_records += count
                
                min_dt = datetime.fromisoformat(min_date)
                max_dt = datetime.fromisoformat(max_date)
                
                print(f"{code:<8} {name:<15} {count:<8} "
                      f"{min_dt.strftime('%m-%d %H:%M'):<18} "
                      f"{max_dt.strftime('%m-%d %H:%M'):<18}")
            
            print("-" * 85)
            print(f"총 데이터: {total_records:,}개")
            
            # DB 파일 크기
            db_size = os.path.getsize(self.db_path) / 1024 / 1024
            print(f"DB 크기: {db_size:.1f} MB")
            
        except Exception as e:
            print(f"통계 조회 실패: {e}")
        finally:
            cursor.close()
    
    def get_recent_data(self, stock_code, hours=1):
        """최근 N시간 분봉 데이터 조회"""
        if not self.connection:
            return None
            
        cursor = self.connection.cursor()
        
        try:
            # SQLite에서 시간 계산
            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute("""
                SELECT trade_datetime, open_price, high_price, low_price, 
                       close_price, volume
                FROM stock_minute_data
                WHERE stock_code = ? AND trade_datetime >= ?
                ORDER BY trade_datetime
            """, (stock_code, since_time))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'datetime': row[0],
                    'open': row[1],
                    'high': row[2], 
                    'low': row[3],
                    'close': row[4],
                    'volume': row[5]
                })
            
            return results
            
        except Exception as e:
            print(f"데이터 조회 실패: {e}")
            return None
        finally:
            cursor.close()
    
    def analyze_stock_movement(self, stock_code):
        """주식 움직임 분석"""
        recent_data = self.get_recent_data(stock_code, 2)  # 최근 2시간
        
        if not recent_data or len(recent_data) < 10:
            return None
        
        # 기본 통계
        prices = [d['close'] for d in recent_data if d['close']]
        volumes = [d['volume'] for d in recent_data if d['volume']]
        
        if not prices:
            return None
        
        current_price = prices[-1]
        start_price = prices[0]
        change = current_price - start_price
        change_rate = (change / start_price) * 100 if start_price else 0
        
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        return {
            'stock_code': stock_code,
            'current_price': current_price,
            'change': change,
            'change_rate': change_rate,
            'avg_volume': int(avg_volume),
            'data_points': len(recent_data)
        }
    
    def export_to_csv(self, stock_code=None, output_file=None):
        """데이터를 CSV로 내보내기"""
        if not self.connection:
            return None
            
        cursor = self.connection.cursor()
        
        try:
            if stock_code:
                cursor.execute("""
                    SELECT * FROM stock_minute_data
                    WHERE stock_code = ?
                    ORDER BY trade_datetime
                """, (stock_code,))
                output_file = output_file or f"{stock_code}_minute_data.csv"
            else:
                cursor.execute("""
                    SELECT * FROM stock_minute_data
                    ORDER BY stock_code, trade_datetime
                """)
                output_file = output_file or "all_minute_data.csv"
            
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 헤더
                writer.writerow(['ID', '종목코드', '종목명', '일시', '시가', '고가', '저가', '종가', '거래량', '생성일시'])
                # 데이터
                writer.writerows(cursor.fetchall())
            
            print(f"📄 CSV 파일 생성: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"CSV 내보내기 실패: {e}")
            return None
        finally:
            cursor.close()
    
    def close(self):
        """DB 연결 종료"""
        if self.connection:
            self.connection.close()
            print("DB 연결 종료")

def main():
    parser = argparse.ArgumentParser(description='주식 분봉 데이터 수집기 (SQLite)')
    parser.add_argument('--count', type=int, default=240, help='수집할 분봉 개수 (기본: 240개)')
    parser.add_argument('--db', default='stock_minute.db', help='SQLite DB 파일명')
    parser.add_argument('--export', metavar='STOCK_CODE', help='특정 종목 CSV 내보내기')
    parser.add_argument('--analyze', metavar='STOCK_CODE', help='종목 분석')
    
    args = parser.parse_args()
    
    collector = StockMinuteCollectorSQLite(args.db)
    
    try:
        if args.export:
            collector.connect_db()
            collector.export_to_csv(args.export)
        elif args.analyze:
            collector.connect_db()
            analysis = collector.analyze_stock_movement(args.analyze)
            if analysis:
                print(f"\n📈 {args.analyze} 분석 결과:")
                print(f"현재가: {analysis['current_price']:,}원")
                print(f"변동: {analysis['change']:+,}원 ({analysis['change_rate']:+.2f}%)")
                print(f"평균거래량: {analysis['avg_volume']:,}")
                print(f"데이터 포인트: {analysis['data_points']}개")
            else:
                print(f"{args.analyze} 데이터 없음")
        else:
            collector.collect_and_save_all(args.count)
    finally:
        collector.close()

if __name__ == "__main__":
    main()