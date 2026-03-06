#!/usr/bin/env python3
"""
Redis에서 Oracle로 주식 데이터 일괄 백업
- 실시간 저장 실패한 데이터 복구용
- 주기적 백업용
- TTL 만료 전 백업용
"""

import cx_Oracle
import redis
import json
from datetime import datetime, timedelta
import os
import argparse

class RedisToOracleBackup:
    def __init__(self):
        # TNS 설정
        os.environ['TNS_ADMIN'] = '/usr/lib/oracle/23/client64/lib/network/admin'
        
        # Redis 연결
        self.redis_client = redis.Redis(host='192.168.50.9', port=6379, password='redis', decode_responses=True)
        
        # Oracle 연결
        self.oracle_conn = None
        
    def connect_oracle(self):
        """오라클 연결"""
        try:
            self.oracle_conn = cx_Oracle.connect('hr/oracle@PROD', encoding='UTF-8')
            print("✅ 오라클 연결 성공")
            return True
        except Exception as e:
            print(f"❌ 오라클 연결 실패: {e}")
            return False
    
    def get_redis_stats_data(self):
        """Redis에서 통계 데이터 수집"""
        try:
            stats_keys = self.redis_client.keys('stats:stock:*')
            redis_data = []
            
            print(f"📊 Redis에서 {len(stats_keys)}개 종목 데이터 발견")
            
            for key in stats_keys:
                data = self.redis_client.get(key)
                if data:
                    try:
                        stock_data = json.loads(data)
                        redis_data.append({
                            'stock_code': stock_data.get('stock_code'),
                            'stock_name': stock_data.get('stock_name'),
                            'current_price': stock_data.get('current_price'),
                            'change': stock_data.get('change', 0),
                            'change_rate': stock_data.get('change_rate', 0),
                            'volume': stock_data.get('volume', 0),
                            'timestamp': stock_data.get('timestamp'),
                            'last_update': stock_data.get('last_update')
                        })
                    except json.JSONDecodeError:
                        continue
                        
            return redis_data
            
        except Exception as e:
            print(f"❌ Redis 데이터 수집 실패: {e}")
            return []
    
    def get_redis_historical_data(self):
        """Redis에서 시계열 데이터 수집"""
        try:
            ts_keys = self.redis_client.keys('ts:stock:*')
            historical_data = []
            
            print(f"📈 Redis에서 {len(ts_keys)}개 시계열 데이터 발견")
            
            for key in ts_keys[:100]:  # 최대 100개만 처리
                data = self.redis_client.get(key)
                if data:
                    try:
                        ts_data = json.loads(data)
                        
                        # timestamp를 datetime으로 변환
                        timestamp = ts_data.get('timestamp')
                        if timestamp:
                            trade_datetime = datetime.fromtimestamp(timestamp)
                            
                            historical_data.append({
                                'stock_code': ts_data.get('stock_code'),
                                'stock_name': ts_data.get('stock_name'),
                                'price': ts_data.get('price'),
                                'volume': ts_data.get('volume'),
                                'trade_datetime': trade_datetime
                            })
                    except (json.JSONDecodeError, ValueError):
                        continue
                        
            return historical_data
            
        except Exception as e:
            print(f"❌ Redis 시계열 데이터 수집 실패: {e}")
            return []
    
    def backup_to_oracle(self, data_list, data_type='minute'):
        """Oracle에 데이터 백업"""
        if not self.oracle_conn or not data_list:
            return 0
            
        cursor = self.oracle_conn.cursor()
        
        # 분봉 데이터용 MERGE 쿼리
        merge_sql = """
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
        """
        
        saved_count = 0
        
        try:
            for data in data_list:
                if data_type == 'minute' and 'trade_datetime' in data:
                    # 시계열 데이터
                    cursor.execute(merge_sql, {
                        'stock_code': data['stock_code'],
                        'stock_name': data['stock_name'],
                        'trade_datetime': data['trade_datetime'],
                        'close_price': data['price'],
                        'volume': data['volume']
                    })
                elif data_type == 'stats' and 'timestamp' in data:
                    # 통계 데이터 (현재 시간으로 저장)
                    trade_time = datetime.fromtimestamp(data['timestamp']) if data['timestamp'] else datetime.now()
                    cursor.execute(merge_sql, {
                        'stock_code': data['stock_code'],
                        'stock_name': data['stock_name'],
                        'trade_datetime': trade_time,
                        'close_price': data['current_price'],
                        'volume': data['volume']
                    })
                
                saved_count += 1
            
            self.oracle_conn.commit()
            print(f"💾 {saved_count}개 데이터 Oracle 백업 완료")
            return saved_count
            
        except Exception as e:
            print(f"❌ Oracle 백업 실패: {e}")
            self.oracle_conn.rollback()
            return 0
        finally:
            cursor.close()
    
    def check_oracle_data(self):
        """Oracle 저장 현황 확인"""
        if not self.oracle_conn:
            return
            
        cursor = self.oracle_conn.cursor()
        
        try:
            # 종목별 데이터 개수
            cursor.execute("""
                SELECT STOCK_CODE, STOCK_NAME, 
                       COUNT(*) as DATA_COUNT,
                       MAX(TRADE_DATETIME) as LATEST_TIME,
                       MAX(CREATED_DATE) as LATEST_CREATED
                FROM STOCK_MINUTE_DATA
                GROUP BY STOCK_CODE, STOCK_NAME
                ORDER BY STOCK_CODE
            """)
            
            print("\\n📊 Oracle 저장 현황:")
            print("-" * 80)
            print(f"{'종목코드':<8} {'종목명':<15} {'데이터수':<8} {'최신거래시간':<18} {'최신저장시간':<18}")
            print("-" * 80)
            
            total_records = 0
            for row in cursor.fetchall():
                code, name, count, latest_trade, latest_created = row
                total_records += count
                
                trade_str = latest_trade.strftime('%m-%d %H:%M') if latest_trade else 'N/A'
                created_str = latest_created.strftime('%m-%d %H:%M') if latest_created else 'N/A'
                
                print(f"{code:<8} {name:<15} {count:<8} {trade_str:<18} {created_str:<18}")
            
            print("-" * 80)
            print(f"총 Oracle 데이터: {total_records:,}개")
            
            # 오늘 저장된 데이터
            cursor.execute("""
                SELECT COUNT(*) FROM STOCK_MINUTE_DATA
                WHERE TRUNC(CREATED_DATE) = TRUNC(SYSDATE)
            """)
            today_count = cursor.fetchone()[0]
            print(f"오늘 저장된 데이터: {today_count:,}개")
            
        except Exception as e:
            print(f"Oracle 현황 확인 실패: {e}")
        finally:
            cursor.close()
    
    def run_backup(self, backup_type='all'):
        """백업 실행"""
        print(f"🔄 Redis → Oracle 백업 시작 ({backup_type})")
        print("=" * 60)
        
        if not self.connect_oracle():
            return
            
        try:
            # Redis 서버 상태 확인
            redis_keys = self.redis_client.dbsize()
            print(f"📊 Redis 서버: {redis_keys}개 키 존재")
            
            total_backed_up = 0
            
            if backup_type in ['all', 'stats']:
                # 통계 데이터 백업
                stats_data = self.get_redis_stats_data()
                if stats_data:
                    backed_up = self.backup_to_oracle(stats_data, 'stats')
                    total_backed_up += backed_up
                    print(f"📊 통계 데이터: {backed_up}개 백업")
            
            if backup_type in ['all', 'historical']:
                # 시계열 데이터 백업
                historical_data = self.get_redis_historical_data()
                if historical_data:
                    backed_up = self.backup_to_oracle(historical_data, 'minute')
                    total_backed_up += backed_up
                    print(f"📈 시계열 데이터: {backed_up}개 백업")
            
            print("=" * 60)
            print(f"✅ 총 {total_backed_up}개 데이터 백업 완료")
            
            # 백업 후 Oracle 현황 확인
            self.check_oracle_data()
            
        except Exception as e:
            print(f"❌ 백업 프로세스 오류: {e}")
        finally:
            if self.oracle_conn:
                self.oracle_conn.close()
                print("\\n🔐 Oracle 연결 종료")

def main():
    parser = argparse.ArgumentParser(description='Redis → Oracle 백업 도구')
    parser.add_argument('--type', choices=['all', 'stats', 'historical'], 
                       default='all', help='백업 타입')
    parser.add_argument('--check-only', action='store_true', 
                       help='백업 없이 현황만 확인')
    
    args = parser.parse_args()
    
    backup = RedisToOracleBackup()
    
    if args.check_only:
        print("📊 Oracle 저장 현황 확인만 실행")
        if backup.connect_oracle():
            backup.check_oracle_data()
    else:
        backup.run_backup(args.type)

if __name__ == "__main__":
    main()