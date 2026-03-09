#!/usr/bin/env python3
"""
ETF 데이터 배치 처리기
장 종료 후 Redis 데이터를 Oracle DB로 이관하는 시스템
"""

import redis
import cx_Oracle
import json
import yaml
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
import time

class ETFBatchProcessor:
    def __init__(self, config_file='config.yaml'):
        """배치 처리기 초기화"""
        self.load_config(config_file)
        self.setup_redis()
        self.setup_oracle()
        self.setup_logging()
        
    def load_config(self, config_file):
        """설정 파일 로드"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
    def setup_redis(self):
        """Redis 연결"""
        self.redis_client = redis.Redis(
            host='192.168.50.3',
            port=6379,
            password='redis',
            decode_responses=True
        )
        
        try:
            self.redis_client.ping()
            print("✅ Redis 연결 성공")
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            raise
            
    def setup_oracle(self):
        """Oracle 데이터베이스 연결"""
        db_config = self.config['database']
        
        dsn = cx_Oracle.makedsn(
            db_config['host'],
            db_config['port'],
            service_name=db_config['service']
        )
        
        self.oracle_conn = cx_Oracle.connect(
            db_config['user'],
            db_config['password'],
            dsn
        )
        
        print("✅ Oracle 연결 성공")
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/etf_batch.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def process_daily_batch(self, target_date: str = None):
        """일일 배치 처리 (장 종료 후 실행)"""
        
        if not target_date:
            # 오늘 날짜 (장 종료 후 처리)
            target_date = datetime.now().strftime('%Y-%m-%d')
            
        self.logger.info(f"🚀 배치 처리 시작: {target_date}")
        
        try:
            # 1. 일일 가격 데이터 이관
            self.migrate_daily_price_data(target_date)
            
            # 2. 기술적 지표 데이터 이관
            self.migrate_technical_indicators(target_date)
            
            # 3. 매매 신호 이관
            self.migrate_trading_signals(target_date)
            
            # 4. 실시간 데이터 정리 (Redis 메모리 정리)
            self.cleanup_redis_data(target_date)
            
            # 5. 통계 업데이트
            self.update_statistics(target_date)
            
            self.logger.info(f"✅ 배치 처리 완료: {target_date}")
            
        except Exception as e:
            self.logger.error(f"❌ 배치 처리 실패: {e}")
            raise

    def migrate_daily_price_data(self, target_date: str):
        """일일 가격 데이터 Redis → Oracle 이관"""
        
        etf_codes = self.config['etf']['target_codes']
        cursor = self.oracle_conn.cursor()
        
        migrated_count = 0
        
        for etf_code in etf_codes:
            try:
                # Redis에서 일일 데이터 조회
                redis_key = f"etf:daily:{etf_code}:{target_date}"
                daily_data = self.redis_client.hgetall(redis_key)
                
                if not daily_data:
                    self.logger.warning(f"Redis에 {etf_code} 일일 데이터 없음: {target_date}")
                    continue
                
                # Oracle에 일일 가격 데이터 삽입
                insert_sql = """
                    MERGE INTO etf_daily_price t1
                    USING (SELECT :etf_code as etf_code, TO_DATE(:trade_date, 'YYYY-MM-DD') as trade_date FROM dual) t2
                    ON (t1.etf_code = t2.etf_code AND t1.trade_date = t2.trade_date)
                    WHEN MATCHED THEN
                        UPDATE SET 
                            open_price = :open_price,
                            high_price = :high_price,
                            low_price = :low_price,
                            close_price = :close_price,
                            volume = :volume,
                            updated_date = SYSDATE
                    WHEN NOT MATCHED THEN
                        INSERT (etf_code, trade_date, open_price, high_price, low_price, close_price, volume, created_date)
                        VALUES (:etf_code, TO_DATE(:trade_date, 'YYYY-MM-DD'), :open_price, :high_price, :low_price, :close_price, :volume, SYSDATE)
                """
                
                cursor.execute(insert_sql, {
                    'etf_code': etf_code,
                    'trade_date': target_date,
                    'open_price': float(daily_data.get('open_price', 0)),
                    'high_price': float(daily_data.get('high_price', 0)),
                    'low_price': float(daily_data.get('low_price', 0)),
                    'close_price': float(daily_data.get('current_price', 0)),
                    'volume': int(daily_data.get('volume', 0))
                })
                
                migrated_count += 1
                
            except Exception as e:
                self.logger.error(f"일일 데이터 이관 실패 {etf_code}: {e}")
                
        self.oracle_conn.commit()
        cursor.close()
        
        self.logger.info(f"일일 가격 데이터 이관 완료: {migrated_count}개 ETF")

    def migrate_technical_indicators(self, target_date: str):
        """기술적 지표 데이터 이관"""
        
        etf_codes = self.config['etf']['target_codes']
        cursor = self.oracle_conn.cursor()
        
        migrated_count = 0
        
        for etf_code in etf_codes:
            try:
                # Redis에서 최신 기술적 지표 조회
                redis_key = f"etf:indicators:{etf_code}"
                indicators_data = self.redis_client.hgetall(redis_key)
                
                if not indicators_data:
                    continue
                
                # Oracle에 기술적 지표 삽입
                insert_sql = """
                    MERGE INTO etf_technical_indicators t1
                    USING (SELECT :etf_code as etf_code, TO_DATE(:trade_date, 'YYYY-MM-DD') as trade_date FROM dual) t2
                    ON (t1.etf_code = t2.etf_code AND t1.trade_date = t2.trade_date)
                    WHEN MATCHED THEN
                        UPDATE SET 
                            close_price = :close_price,
                            sma_5 = :sma_5,
                            sma_20 = :sma_20,
                            sma_60 = :sma_60,
                            sma_200 = :sma_200,
                            rsi_14 = :rsi_14,
                            updated_date = SYSDATE
                    WHEN NOT MATCHED THEN
                        INSERT (etf_code, trade_date, close_price, sma_5, sma_20, sma_60, sma_200, rsi_14, created_date)
                        VALUES (:etf_code, TO_DATE(:trade_date, 'YYYY-MM-DD'), :close_price, :sma_5, :sma_20, :sma_60, :sma_200, :rsi_14, SYSDATE)
                """
                
                cursor.execute(insert_sql, {
                    'etf_code': etf_code,
                    'trade_date': target_date,
                    'close_price': float(indicators_data.get('current_price', 0)),
                    'sma_5': float(indicators_data.get('sma_5', 0)) if indicators_data.get('sma_5') else None,
                    'sma_20': float(indicators_data.get('sma_20', 0)) if indicators_data.get('sma_20') else None,
                    'sma_60': float(indicators_data.get('sma_60', 0)) if indicators_data.get('sma_60') else None,
                    'sma_200': float(indicators_data.get('sma_200', 0)) if indicators_data.get('sma_200') else None,
                    'rsi_14': float(indicators_data.get('rsi_14', 0)) if indicators_data.get('rsi_14') else None
                })
                
                migrated_count += 1
                
            except Exception as e:
                self.logger.error(f"기술적 지표 이관 실패 {etf_code}: {e}")
                
        self.oracle_conn.commit()
        cursor.close()
        
        self.logger.info(f"기술적 지표 이관 완료: {migrated_count}개 ETF")

    def migrate_trading_signals(self, target_date: str):
        """매매 신호 이관"""
        
        cursor = self.oracle_conn.cursor()
        
        # Redis에서 당일 매매 신호 조회
        redis_key = "etf:trading_signals"
        signals_json = self.redis_client.lrange(redis_key, 0, -1)
        
        migrated_count = 0
        
        for signal_json in signals_json:
            try:
                signal_data = json.loads(signal_json)
                
                # 당일 신호인지 확인
                signal_date = signal_data['timestamp'][:10]  # YYYY-MM-DD 부분
                
                if signal_date != target_date:
                    continue
                
                # Oracle에 매매 신호 삽입
                insert_sql = """
                    INSERT INTO etf_trading_signals 
                    (etf_code, signal_date, signal_type, signal_strength, price, signal_reason, indicators_json, created_date)
                    VALUES (:etf_code, TO_DATE(:signal_date, 'YYYY-MM-DD'), :signal_type, :signal_strength, 
                            :price, :signal_reason, :indicators_json, SYSDATE)
                """
                
                # 기술적 지표를 JSON으로 변환
                indicators_json = json.dumps({
                    'rsi_14': signal_data.get('rsi'),
                    'sma_5': signal_data.get('sma_5'),
                    'sma_20': signal_data.get('sma_20'),
                    'timestamp': signal_data['timestamp']
                })
                
                cursor.execute(insert_sql, {
                    'etf_code': signal_data['etf_code'],
                    'signal_date': signal_date,
                    'signal_type': signal_data['signal_type'],
                    'signal_strength': signal_data['signal_strength'],
                    'price': float(signal_data['price']),
                    'signal_reason': signal_data['signal_reason'][:500],  # 길이 제한
                    'indicators_json': indicators_json
                })
                
                migrated_count += 1
                
            except Exception as e:
                self.logger.error(f"매매 신호 이관 실패: {e}")
                
        self.oracle_conn.commit()
        cursor.close()
        
        self.logger.info(f"매매 신호 이관 완료: {migrated_count}개")

    def cleanup_redis_data(self, target_date: str):
        """Redis 데이터 정리 (메모리 절약)"""
        
        etf_codes = self.config['etf']['target_codes']
        cleaned_keys = 0
        
        for etf_code in etf_codes:
            try:
                # 오래된 시계열 데이터 정리 (7일 이상)
                redis_key_timeseries = f"etf:timeseries:{etf_code}"
                week_ago = int((datetime.now() - timedelta(days=7)).timestamp())
                
                removed = self.redis_client.zremrangebyscore(
                    redis_key_timeseries, 0, week_ago
                )
                
                if removed:
                    self.logger.debug(f"{etf_code} 오래된 시계열 데이터 {removed}개 삭제")
                    cleaned_keys += 1
                    
            except Exception as e:
                self.logger.error(f"Redis 정리 실패 {etf_code}: {e}")
                
        # 오래된 매매 신호 정리 (1000개 이상시)
        try:
            redis_key_signals = "etf:trading_signals"
            signal_count = self.redis_client.llen(redis_key_signals)
            
            if signal_count > 1000:
                self.redis_client.ltrim(redis_key_signals, 0, 999)
                self.logger.info(f"매매 신호 {signal_count - 1000}개 정리")
                
        except Exception as e:
            self.logger.error(f"매매 신호 정리 실패: {e}")
            
        self.logger.info(f"Redis 정리 완료: {cleaned_keys}개 키 처리")

    def update_statistics(self, target_date: str):
        """일일 통계 업데이트"""
        
        cursor = self.oracle_conn.cursor()
        
        try:
            # ETF별 일일 통계 계산
            stats_sql = """
                SELECT etf_code,
                       COUNT(*) as signal_count,
                       SUM(CASE WHEN signal_type = 'BUY' THEN 1 ELSE 0 END) as buy_signals,
                       SUM(CASE WHEN signal_type = 'SELL' THEN 1 ELSE 0 END) as sell_signals,
                       AVG(price) as avg_price
                FROM etf_trading_signals 
                WHERE signal_date = TO_DATE(:target_date, 'YYYY-MM-DD')
                GROUP BY etf_code
            """
            
            cursor.execute(stats_sql, {'target_date': target_date})
            results = cursor.fetchall()
            
            for row in results:
                etf_code, signal_count, buy_signals, sell_signals, avg_price = row
                
                self.logger.info(
                    f"📊 {etf_code}: 신호 {signal_count}개 "
                    f"(매수 {buy_signals}, 매도 {sell_signals}), "
                    f"평균가격 {avg_price:.0f}"
                )
                
        except Exception as e:
            self.logger.error(f"통계 업데이트 실패: {e}")
        finally:
            cursor.close()

    def run_batch_scheduler(self):
        """배치 스케줄러 (장 종료 후 자동 실행)"""
        
        self.logger.info("📅 ETF 배치 스케줄러 시작")
        
        while True:
            try:
                now = datetime.now()
                
                # 평일 오후 4시에 배치 실행 (장 종료 후)
                if (now.weekday() < 5 and  # 평일
                    now.hour == 16 and     # 오후 4시
                    now.minute == 0):      # 정각
                    
                    today = now.strftime('%Y-%m-%d')
                    self.logger.info(f"⏰ 배치 실행 시간: {today}")
                    
                    self.process_daily_batch(today)
                    
                    # 24시간 대기 (다음 날까지)
                    time.sleep(24 * 3600)
                    
                else:
                    # 1분마다 시간 확인
                    time.sleep(60)
                    
            except KeyboardInterrupt:
                self.logger.info("배치 스케줄러 중단")
                break
            except Exception as e:
                self.logger.error(f"스케줄러 에러: {e}")
                time.sleep(300)  # 5분 대기 후 재시도

    def manual_batch_run(self, target_date: str = None):
        """수동 배치 실행"""
        
        if not target_date:
            target_date = input("배치 처리할 날짜 (YYYY-MM-DD, 엔터=오늘): ").strip()
            if not target_date:
                target_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"🚀 수동 배치 실행: {target_date}")
        self.process_daily_batch(target_date)
        print("✅ 배치 처리 완료")

def main():
    """메인 함수"""
    import sys
    
    processor = ETFBatchProcessor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'manual':
            # 수동 실행
            target_date = sys.argv[2] if len(sys.argv) > 2 else None
            processor.manual_batch_run(target_date)
            
        elif command == 'scheduler':
            # 스케줄러 실행
            processor.run_batch_scheduler()
            
        else:
            print("사용법: python etf_batch_processor.py [manual|scheduler] [날짜]")
    else:
        # 기본: 오늘 배치 실행
        processor.process_daily_batch()

if __name__ == "__main__":
    main()