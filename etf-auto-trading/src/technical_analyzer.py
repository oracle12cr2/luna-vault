#!/usr/bin/env python3
"""
ETF 기술적 지표 분석 엔진
- SMA/EMA, RSI, MACD, 볼린저 밴드 계산
- Oracle RAC stock 스키마에 저장
"""

import sys
import os
import time
from datetime import datetime, timedelta
import cx_Oracle
import pandas as pd
import numpy as np
import talib
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/etf_collector/technical_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    def __init__(self):
        self.db_host = 'oracle19c01'
        self.db_port = 1521
        self.db_service = 'PROD'
        self.db_user = 'stock'
        self.db_password = 'stock123'
        self.connection = None

    def connect_db(self):
        """Oracle 데이터베이스 연결"""
        try:
            dsn = cx_Oracle.makedsn(self.db_host, self.db_port, service_name=self.db_service)
            self.connection = cx_Oracle.connect(self.db_user, self.db_password, dsn)
            logger.info(f"Oracle DB 연결 성공: {self.db_host}:{self.db_port}/{self.db_service}")
            return True
        except Exception as e:
            logger.error(f"Oracle DB 연결 실패: {e}")
            return False

    def disconnect_db(self):
        """데이터베이스 연결 종료"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def get_etf_price_data(self, etf_code, days=100):
        """ETF 가격 데이터 조회 (기술적 지표 계산용)"""
        try:
            cursor = self.connection.cursor()
            
            # 최근 days일 데이터 조회 (기술적 지표 계산을 위해)
            cursor.execute("""
                SELECT trade_date, open_price, high_price, low_price, close_price, volume
                FROM etf_daily_price
                WHERE etf_code = :etf_code
                ORDER BY trade_date ASC
            """, {'etf_code': etf_code})
            
            rows = cursor.fetchall()
            cursor.close()
            
            if not rows:
                logger.warning(f"{etf_code}: 가격 데이터 없음")
                return None
            
            # DataFrame으로 변환
            df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # 데이터 타입 변환
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"{etf_code}: {len(df)}일 가격 데이터 로드")
            return df
            
        except Exception as e:
            logger.error(f"{etf_code} 가격 데이터 조회 실패: {e}")
            return None

    def calculate_technical_indicators(self, df):
        """기술적 지표 계산"""
        try:
            indicators = pd.DataFrame(index=df.index)
            
            # 기본 가격 정보
            indicators['close_price'] = df['close']
            indicators['volume'] = df['volume']
            
            # 1. 이동평균 (SMA) - 데이터 길이에 따라 계산
            indicators['sma_5'] = talib.SMA(df['close'], timeperiod=5)
            indicators['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            indicators['sma_60'] = talib.SMA(df['close'], timeperiod=60)
            
            # 200일 이동평균 (데이터 부족 시 NaN)
            indicators['sma_200'] = talib.SMA(df['close'], timeperiod=200)
            
            # 2. 지수이동평균 (EMA) - 데이터 길이에 따라 계산
            indicators['ema_5'] = talib.EMA(df['close'], timeperiod=5)
            indicators['ema_20'] = talib.EMA(df['close'], timeperiod=20)
            indicators['ema_60'] = talib.EMA(df['close'], timeperiod=60)
            
            # 200일 EMA (데이터 부족 시 NaN)
            indicators['ema_200'] = talib.EMA(df['close'], timeperiod=200)
            
            # 3. RSI (Relative Strength Index)
            indicators['rsi_14'] = talib.RSI(df['close'], timeperiod=14)
            
            # 4. MACD (Moving Average Convergence Divergence)
            macd_line, macd_signal, macd_hist = talib.MACD(df['close'], 
                                                          fastperiod=12, 
                                                          slowperiod=26, 
                                                          signalperiod=9)
            indicators['macd_line'] = macd_line
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_hist
            
            # 5. 볼린저 밴드 (Bollinger Bands)
            bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'], 
                                                        timeperiod=20, 
                                                        nbdevup=2, 
                                                        nbdevdn=2)
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle * 100
            
            # 6. 거래량 이동평균
            indicators['volume_sma_20'] = talib.SMA(df['volume'], timeperiod=20)
            
            # NaN 값 제거 (초기 계산 불가능한 구간)
            indicators = indicators.dropna()
            
            logger.info(f"기술적 지표 계산 완료: {len(indicators)}건")
            return indicators
            
        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")
            return None

    def save_technical_indicators(self, etf_code, indicators):
        """기술적 지표를 DB에 저장"""
        if not self.connection or indicators is None or indicators.empty:
            return False

        try:
            cursor = self.connection.cursor()
            
            # MERGE 구문으로 INSERT/UPDATE
            merge_sql = """
            MERGE INTO etf_technical_indicators t
            USING (
                SELECT :etf_code as etf_code, TO_DATE(:trade_date, 'YYYY-MM-DD') as trade_date,
                       :close_price as close_price,
                       :sma_5 as sma_5, :sma_20 as sma_20, :sma_60 as sma_60, :sma_200 as sma_200,
                       :ema_5 as ema_5, :ema_20 as ema_20, :ema_60 as ema_60, :ema_200 as ema_200,
                       :rsi_14 as rsi_14,
                       :macd_line as macd_line, :macd_signal as macd_signal, :macd_histogram as macd_histogram,
                       :bb_upper as bb_upper, :bb_middle as bb_middle, :bb_lower as bb_lower, :bb_width as bb_width,
                       :volume as volume, :volume_sma_20 as volume_sma_20,
                       SYSDATE as created_date, SYSDATE as updated_date
                FROM dual
            ) s ON (t.etf_code = s.etf_code AND t.trade_date = s.trade_date)
            WHEN MATCHED THEN
                UPDATE SET 
                    close_price = s.close_price,
                    sma_5 = s.sma_5, sma_20 = s.sma_20, sma_60 = s.sma_60, sma_200 = s.sma_200,
                    ema_5 = s.ema_5, ema_20 = s.ema_20, ema_60 = s.ema_60, ema_200 = s.ema_200,
                    rsi_14 = s.rsi_14,
                    macd_line = s.macd_line, macd_signal = s.macd_signal, macd_histogram = s.macd_histogram,
                    bb_upper = s.bb_upper, bb_middle = s.bb_middle, bb_lower = s.bb_lower, bb_width = s.bb_width,
                    volume = s.volume, volume_sma_20 = s.volume_sma_20,
                    updated_date = s.updated_date
            WHEN NOT MATCHED THEN
                INSERT (etf_code, trade_date, close_price,
                       sma_5, sma_20, sma_60, sma_200, ema_5, ema_20, ema_60, ema_200, rsi_14,
                       macd_line, macd_signal, macd_histogram,
                       bb_upper, bb_middle, bb_lower, bb_width,
                       volume, volume_sma_20, created_date, updated_date)
                VALUES (s.etf_code, s.trade_date, s.close_price,
                       s.sma_5, s.sma_20, s.sma_60, s.sma_200, s.ema_5, s.ema_20, s.ema_60, s.ema_200, s.rsi_14,
                       s.macd_line, s.macd_signal, s.macd_histogram,
                       s.bb_upper, s.bb_middle, s.bb_lower, s.bb_width,
                       s.volume, s.volume_sma_20, s.created_date, s.updated_date)
            """

            inserted_count = 0
            for date, row in indicators.iterrows():
                # NaN 값을 None으로 변환
                def safe_float(value):
                    return float(value) if not pd.isna(value) else None

                cursor.execute(merge_sql, {
                    'etf_code': etf_code,
                    'trade_date': date.strftime('%Y-%m-%d'),
                    'close_price': safe_float(row['close_price']),
                    'sma_5': safe_float(row['sma_5']),
                    'sma_20': safe_float(row['sma_20']),
                    'sma_60': safe_float(row['sma_60']),
                    'sma_200': safe_float(row['sma_200']),
                    'ema_5': safe_float(row['ema_5']),
                    'ema_20': safe_float(row['ema_20']),
                    'ema_60': safe_float(row['ema_60']),
                    'ema_200': safe_float(row['ema_200']),
                    'rsi_14': safe_float(row['rsi_14']),
                    'macd_line': safe_float(row['macd_line']),
                    'macd_signal': safe_float(row['macd_signal']),
                    'macd_histogram': safe_float(row['macd_histogram']),
                    'bb_upper': safe_float(row['bb_upper']),
                    'bb_middle': safe_float(row['bb_middle']),
                    'bb_lower': safe_float(row['bb_lower']),
                    'bb_width': safe_float(row['bb_width']),
                    'volume': safe_float(row['volume']),
                    'volume_sma_20': safe_float(row['volume_sma_20'])
                })
                inserted_count += 1

            self.connection.commit()
            cursor.close()
            
            logger.info(f"{etf_code}: {inserted_count}건 기술적 지표 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"{etf_code} 기술적 지표 저장 실패: {e}")
            return False

    def get_etf_list(self):
        """ETF 목록 조회"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT etf_code, etf_name FROM etf_master ORDER BY etf_code")
            results = cursor.fetchall()
            cursor.close()
            return [{'code': row[0], 'name': row[1]} for row in results]
        except Exception as e:
            logger.error(f"ETF 목록 조회 실패: {e}")
            return []

    def run_analysis(self):
        """전체 ETF 기술적 분석 실행"""
        logger.info("=== ETF 기술적 지표 분석 시작 ===")
        
        # DB 연결
        if not self.connect_db():
            return False

        try:
            # ETF 목록 조회
            etf_list = self.get_etf_list()
            if not etf_list:
                logger.error("분석할 ETF가 없습니다")
                return False

            success_count = 0
            total_count = len(etf_list)

            # 각 ETF별 기술적 지표 계산
            for etf_info in etf_list:
                etf_code = etf_info['code']
                etf_name = etf_info['name']
                
                logger.info(f"[{etf_code}] {etf_name} 기술적 분석 중...")
                
                # 1. 가격 데이터 조회
                price_data = self.get_etf_price_data(etf_code)
                
                if price_data is not None and len(price_data) >= 60:  # 기본 기술적 지표용 최소 데이터
                    # 2. 기술적 지표 계산
                    indicators = self.calculate_technical_indicators(price_data)
                    
                    if indicators is not None:
                        # 3. DB 저장
                        if self.save_technical_indicators(etf_code, indicators):
                            success_count += 1
                        else:
                            logger.warning(f"{etf_code}: 저장 실패")
                    else:
                        logger.warning(f"{etf_code}: 지표 계산 실패")
                else:
                    logger.warning(f"{etf_code}: 데이터 부족 (최소 60일 필요)")
                
                # API 부하 방지
                time.sleep(0.5)

            logger.info(f"=== 분석 완료: {success_count}/{total_count} ===")
            return success_count > 0
            
        finally:
            self.disconnect_db()

def main():
    """메인 함수"""
    analyzer = TechnicalAnalyzer()
    success = analyzer.run_analysis()
    
    if success:
        print("✅ ETF 기술적 지표 분석 성공!")
        sys.exit(0)
    else:
        print("❌ ETF 기술적 지표 분석 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()