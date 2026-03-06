#!/usr/bin/env python3
"""
한국 주식 분봉 데이터 수집기
네이버에서 분봉 데이터 수집하고 오라클 DB에 저장
"""

import requests
import xml.etree.ElementTree as ET
import cx_Oracle
from datetime import datetime, timedelta
import time
import json
import argparse
import os

class StockMinuteCollector:
    def __init__(self, db_config=None):
        """
        초기화
        db_config: {'host': '192.168.50.31', 'port': 1521, 'service_name': 'ORCL', 'user': 'scott', 'password': 'tiger'}
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 오라클 DB 설정 (기본값)
        self.db_config = db_config or {
            'host': '192.168.50.31',
            'port': 1521,
            'service_name': 'ORCL',
            'user': 'APP_USER',
            'password': 'app_user123'
        }
        
        # 주요 종목
        self.major_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660', 
            'NAVER': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220'
        }
        
        self.connection = None
        
    def connect_db(self):
        """오라클 DB 연결"""
        try:
            # DSN 생성
            dsn = cx_Oracle.makedsn(
                self.db_config['host'],
                self.db_config['port'],
                service_name=self.db_config['service_name']
            )
            
            # 연결
            self.connection = cx_Oracle.connect(
                user=self.db_config['user'],
                password=self.db_config['password'],
                dsn=dsn,
                encoding="UTF-8"
            )
            
            print(f"✅ 오라클 DB 연결 성공 ({self.db_config['host']})")
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
        CREATE TABLE STOCK_MINUTE_DATA (
            ID NUMBER(19) PRIMARY KEY,
            STOCK_CODE VARCHAR2(10) NOT NULL,
            STOCK_NAME VARCHAR2(100),
            TRADE_DATETIME DATE NOT NULL,
            OPEN_PRICE NUMBER(10),
            HIGH_PRICE NUMBER(10),
            LOW_PRICE NUMBER(10),
            CLOSE_PRICE NUMBER(10),
            VOLUME NUMBER(15),
            CREATED_DATE DATE DEFAULT SYSDATE,
            CONSTRAINT UK_STOCK_MINUTE UNIQUE (STOCK_CODE, TRADE_DATETIME)
        )
        """
        
        # 시퀀스
        sequence_ddl = """
        CREATE SEQUENCE STOCK_MINUTE_SEQ
        START WITH 1
        INCREMENT BY 1
        NOCACHE
        """
        
        # 인덱스
        index_ddl = """
        CREATE INDEX IDX_STOCK_MINUTE_CODE_DATE 
        ON STOCK_MINUTE_DATA (STOCK_CODE, TRADE_DATETIME)
        """
        
        try:
            # 기존 테이블 확인 후 생성
            cursor.execute("""
                SELECT COUNT(*) FROM USER_TABLES 
                WHERE TABLE_NAME = 'STOCK_MINUTE_DATA'
            """)
            
            if cursor.fetchone()[0] == 0:
                print("📝 분봉 데이터 테이블 생성...")
                cursor.execute(minute_table_ddl)
                
                print("📝 시퀀스 생성...")
                cursor.execute(sequence_ddl)
                
                print("📝 인덱스 생성...")
                cursor.execute(index_ddl)
                
                self.connection.commit()
                print("✅ 테이블 생성 완료")
            else:
                print("✅ 테이블이 이미 존재합니다")
            
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
            response = requests.get(url, params=params, headers=self.headers)
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
                    year = int(datetime_str[:4])
                    month = int(datetime_str[4:6])
                    day = int(datetime_str[6:8])
                    hour = int(datetime_str[8:10])
                    minute = int(datetime_str[10:12])
                    
                    trade_datetime = datetime(year, month, day, hour, minute)
                    
                    minute_data.append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'trade_datetime': trade_datetime,
                        'open_price': int(open_price) if open_price else None,
                        'high_price': int(high_price) if high_price else None,
                        'low_price': int(low_price) if low_price else None,
                        'close_price': int(close_price) if close_price else None,
                        'volume': int(volume) if volume else None
                    })
            
            return minute_data
            
        except Exception as e:
            print(f"데이터 수집 실패 ({stock_code}): {e}")
            return None
    
    def save_minute_data(self, minute_data):
        """분봉 데이터를 DB에 저장"""
        if not self.connection or not minute_data:
            return 0
            
        cursor = self.connection.cursor()
        
        insert_sql = """
        INSERT INTO STOCK_MINUTE_DATA 
        (ID, STOCK_CODE, STOCK_NAME, TRADE_DATETIME, OPEN_PRICE, HIGH_PRICE, 
         LOW_PRICE, CLOSE_PRICE, VOLUME)
        VALUES 
        (STOCK_MINUTE_SEQ.NEXTVAL, :stock_code, :stock_name, :trade_datetime, 
         :open_price, :high_price, :low_price, :close_price, :volume)
        """
        
        # UPSERT를 위한 MERGE 구문
        merge_sql = """
        MERGE INTO STOCK_MINUTE_DATA target
        USING (
            SELECT :stock_code as STOCK_CODE,
                   :stock_name as STOCK_NAME,
                   :trade_datetime as TRADE_DATETIME,
                   :open_price as OPEN_PRICE,
                   :high_price as HIGH_PRICE,
                   :low_price as LOW_PRICE,
                   :close_price as CLOSE_PRICE,
                   :volume as VOLUME
            FROM DUAL
        ) source
        ON (target.STOCK_CODE = source.STOCK_CODE 
            AND target.TRADE_DATETIME = source.TRADE_DATETIME)
        WHEN NOT MATCHED THEN
        INSERT (ID, STOCK_CODE, STOCK_NAME, TRADE_DATETIME, OPEN_PRICE, 
                HIGH_PRICE, LOW_PRICE, CLOSE_PRICE, VOLUME)
        VALUES (STOCK_MINUTE_SEQ.NEXTVAL, source.STOCK_CODE, source.STOCK_NAME,
                source.TRADE_DATETIME, source.OPEN_PRICE, source.HIGH_PRICE,
                source.LOW_PRICE, source.CLOSE_PRICE, source.VOLUME)
        WHEN MATCHED THEN
        UPDATE SET 
            STOCK_NAME = source.STOCK_NAME,
            OPEN_PRICE = source.OPEN_PRICE,
            HIGH_PRICE = source.HIGH_PRICE,
            LOW_PRICE = source.LOW_PRICE,
            CLOSE_PRICE = source.CLOSE_PRICE,
            VOLUME = source.VOLUME
        """
        
        saved_count = 0
        
        try:
            for data in minute_data:
                cursor.execute(merge_sql, data)
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
    
    def collect_and_save_all(self, count=240):
        """모든 종목 분봉 데이터 수집 및 저장"""
        if not self.connect_db():
            return
            
        if not self.create_tables():
            return
        
        print("📊 분봉 데이터 수집 시작...")
        print("=" * 60)
        
        total_saved = 0
        
        for stock_name, stock_code in self.major_stocks.items():
            print(f"수집 중: {stock_name} ({stock_code})")
            
            # 분봉 데이터 수집
            minute_data = self.get_minute_data(stock_code, count)
            
            if minute_data:
                print(f"  📈 {len(minute_data)}개 분봉 데이터 수집")
                saved = self.save_minute_data(minute_data)
                total_saved += saved
                
                # 최신 데이터 출력
                if minute_data:
                    latest = minute_data[-1]
                    print(f"  📅 최신: {latest['trade_datetime']} "
                          f"{latest['close_price']:,}원 거래량:{latest['volume']:,}")
            else:
                print(f"  ❌ {stock_name} 데이터 수집 실패")
            
            time.sleep(0.5)  # API 호출 제한
        
        print("=" * 60)
        print(f"✅ 총 {total_saved}개 분봉 데이터 저장 완료")
        
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
                SELECT STOCK_CODE, STOCK_NAME, COUNT(*), 
                       MIN(TRADE_DATETIME), MAX(TRADE_DATETIME)
                FROM STOCK_MINUTE_DATA
                GROUP BY STOCK_CODE, STOCK_NAME
                ORDER BY STOCK_CODE
            """)
            
            print("\n📊 저장된 분봉 데이터 통계:")
            print("-" * 80)
            print(f"{'종목코드':<8} {'종목명':<15} {'데이터수':<8} {'최초일시':<20} {'최신일시':<20}")
            print("-" * 80)
            
            for row in cursor.fetchall():
                code, name, count, min_date, max_date = row
                print(f"{code:<8} {name:<15} {count:<8} "
                      f"{min_date.strftime('%Y-%m-%d %H:%M'):<20} "
                      f"{max_date.strftime('%Y-%m-%d %H:%M'):<20}")
            
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
            cursor.execute("""
                SELECT TRADE_DATETIME, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, 
                       CLOSE_PRICE, VOLUME
                FROM STOCK_MINUTE_DATA
                WHERE STOCK_CODE = :stock_code
                  AND TRADE_DATETIME >= SYSDATE - :hours/24
                ORDER BY TRADE_DATETIME
            """, {'stock_code': stock_code, 'hours': hours})
            
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
    
    def close(self):
        """DB 연결 종료"""
        if self.connection:
            self.connection.close()
            print("DB 연결 종료")

def main():
    parser = argparse.ArgumentParser(description='주식 분봉 데이터 수집기')
    parser.add_argument('--count', type=int, default=240, help='수집할 분봉 개수')
    parser.add_argument('--host', default='192.168.50.31', help='DB 호스트')
    parser.add_argument('--port', type=int, default=1521, help='DB 포트')
    parser.add_argument('--service', default='ORCL', help='DB 서비스명')
    parser.add_argument('--user', default='APP_USER', help='DB 사용자')
    parser.add_argument('--password', default='app_user123', help='DB 비밀번호')
    
    args = parser.parse_args()
    
    # DB 설정
    db_config = {
        'host': args.host,
        'port': args.port, 
        'service_name': args.service,
        'user': args.user,
        'password': args.password
    }
    
    collector = StockMinuteCollector(db_config)
    
    try:
        collector.collect_and_save_all(args.count)
    finally:
        collector.close()

if __name__ == "__main__":
    main()