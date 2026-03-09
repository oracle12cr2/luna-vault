#!/usr/bin/env python3
"""
ETF 과거 데이터 생성기 (기술적 분석용)
- 60일치 시뮬레이션 데이터 생성
"""

import sys
import cx_Oracle
import random
import math
from datetime import datetime, timedelta

class HistoricalDataGenerator:
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
            print(f"Oracle DB 연결 성공")
            return True
        except Exception as e:
            print(f"Oracle DB 연결 실패: {e}")
            return False

    def generate_price_series(self, etf_code, base_price, days=180):
        """현실적인 가격 시계열 생성 (기하 브라운 운동 기반)"""

        # ETF별 특성 설정
        etf_params = {
            '069500': {'drift': 0.0002, 'volatility': 0.015, 'trend_strength': 0.8},  # KODEX 200 - 안정적
            '229200': {'drift': 0.0003, 'volatility': 0.025, 'trend_strength': 0.6},  # KOSDAQ - 변동성 큼
            '102110': {'drift': 0.0004, 'volatility': 0.020, 'trend_strength': 0.7},  # IT섹터
            '133690': {'drift': 0.0005, 'volatility': 0.020, 'trend_strength': 0.7},  # 나스닥
            '449180': {'drift': 0.0003, 'volatility': 0.015, 'trend_strength': 0.8},  # S&P500
            '161510': {'drift': 0.0001, 'volatility': 0.010, 'trend_strength': 0.9},  # 고배당 - 안정적
            '091230': {'drift': 0.0006, 'volatility': 0.040, 'trend_strength': 0.4},  # 2차전지 - 고변동성
            '160580': {'drift': 0.0001, 'volatility': 0.012, 'trend_strength': 0.9},  # 우선주 - 매우 안정적
            '091170': {'drift': 0.0002, 'volatility': 0.025, 'trend_strength': 0.6},  # 건설
            '130680': {'drift': 0.0001, 'volatility': 0.050, 'trend_strength': 0.3},  # 원유 - 매우 높은 변동성
        }

        params = etf_params.get(etf_code, {'drift': 0.0002, 'volatility': 0.02, 'trend_strength': 0.5})

        prices = []
        volumes = []
        current_price = base_price

        # 장기 트렌드 생성 (다중 사이클 조합)
        # 주요 사이클: 30일(월간), 60일(분기), 120일(반기)
        short_cycle = random.uniform(25, 35)   # 월간 사이클
        mid_cycle = random.uniform(55, 70)     # 분기 사이클
        long_cycle = random.uniform(110, 140)  # 반기 사이클

        short_amplitude = base_price * 0.08   # ±8%
        mid_amplitude = base_price * 0.15     # ±15%
        long_amplitude = base_price * 0.25    # ±25%

        # 각 사이클별 시작 위상 랜덤
        short_phase = random.uniform(0, 2*math.pi)
        mid_phase = random.uniform(0, 2*math.pi)
        long_phase = random.uniform(0, 2*math.pi)

        for i in range(days):
            # 다중 사이클 트렌드 조합
            short_trend = math.sin(2 * math.pi * i / short_cycle + short_phase) * short_amplitude / base_price
            mid_trend = math.sin(2 * math.pi * i / mid_cycle + mid_phase) * mid_amplitude / base_price
            long_trend = math.sin(2 * math.pi * i / long_cycle + long_phase) * long_amplitude / base_price

            # 가중 합계 (장기 트렌드가 더 중요)
            trend_factor = (short_trend * 0.3 + mid_trend * 0.4 + long_trend * 0.5) * params['trend_strength']

            # 일일 변동 (기하 브라운 운동)
            random_factor = random.gauss(0, 1)  # 정규분포 난수
            daily_return = params['drift'] + trend_factor + params['volatility'] * random_factor

            # 가격 업데이트 (기하 브라운 운동)
            current_price *= (1 + daily_return)

            # 일중 변동성 (OHLC 생성)
            intraday_volatility = params['volatility'] * random.uniform(0.3, 0.8)

            open_price = current_price * random.uniform(0.995, 1.005)
            close_price = current_price

            # High/Low 계산
            high_factor = random.uniform(1.001, 1 + intraday_volatility)
            low_factor = random.uniform(1 - intraday_volatility, 0.999)

            high_price = max(open_price, close_price) * high_factor
            low_price = min(open_price, close_price) * low_factor

            # 거래량 생성 (변동성과 상관관계)
            base_volume = {
                '069500': 3000000, '229200': 1500000, '102110': 500000,
                '133690': 800000, '449180': 600000, '161510': 300000,
                '091230': 400000, '160580': 200000, '091170': 150000,
                '130680': 100000
            }.get(etf_code, 500000)

            # 변동성이 클수록 거래량 증가
            volume_multiplier = 1 + abs(daily_return) * 10
            volume = int(base_volume * volume_multiplier * random.uniform(0.5, 2.0))

            prices.append({
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })

        return prices

    def save_historical_data(self, etf_code, price_data):
        """과거 데이터를 DB에 저장"""
        try:
            cursor = self.connection.cursor()

            # 기존 데이터 삭제
            cursor.execute("DELETE FROM etf_daily_price WHERE etf_code = :etf_code", {'etf_code': etf_code})

            # 새로운 데이터 삽입
            insert_sql = """
            INSERT INTO etf_daily_price
            (etf_code, trade_date, open_price, high_price, low_price, close_price, volume, nav, created_date)
            VALUES (:etf_code, :trade_date, :open_price, :high_price, :low_price, :close_price, :volume, :nav, SYSDATE)
            """

            # 180일 전부터 데이터 생성 (약 6개월)
            start_date = datetime.now() - timedelta(days=200)  # 주말 제외하여 여유있게

            data_count = 0
            for i, data in enumerate(price_data):
                # 주말 건너뛰기
                current_date = start_date + timedelta(days=i)
                while current_date.weekday() >= 5:  # 토요일(5), 일요일(6) 제외
                    current_date += timedelta(days=1)

                nav = data['close'] * random.uniform(0.9999, 1.0001)  # NAV는 종가와 거의 동일

                cursor.execute(insert_sql, {
                    'etf_code': etf_code,
                    'trade_date': current_date,
                    'open_price': data['open'],
                    'high_price': data['high'],
                    'low_price': data['low'],
                    'close_price': data['close'],
                    'volume': data['volume'],
                    'nav': round(nav, 2)
                })

                data_count += 1
                start_date = current_date + timedelta(days=1)

            self.connection.commit()
            cursor.close()

            print(f"{etf_code}: {data_count}일 데이터 생성 완료")
            return True

        except Exception as e:
            print(f"{etf_code} 데이터 저장 실패: {e}")
            return False

    def run_generation(self):
        """전체 ETF 과거 데이터 생성"""
        print("=== ETF 반기(6개월/180일) 데이터 생성 시작 ===")

        if not self.connect_db():
            return False

        try:
            # ETF 목록과 기준가
            etf_info = [
                ('069500', 'KODEX 200', 27500),
                ('229200', 'KODEX KOSDAQ150', 8500),
                ('102110', 'TIGER 200IT', 19500),
                ('133690', 'TIGER NASDAQ100', 28500),
                ('449180', 'KODEX US SP500', 15200),
                ('161510', 'KODEX High Dividend', 11800),
                ('091230', 'KODEX Battery', 7500),
                ('160580', 'KODEX Samsung Pref', 9200),
                ('091170', 'TIGER Construction', 8100),
                ('130680', 'TIGER Oil Futures', 4200)
            ]

            success_count = 0

            for etf_code, etf_name, base_price in etf_info:
                print(f"[{etf_code}] {etf_name} 과거 데이터 생성 중...")

                # 가격 시계열 생성 (반기 = 180 거래일)
                price_data = self.generate_price_series(etf_code, base_price, days=180)

                # DB 저장
                if self.save_historical_data(etf_code, price_data):
                    success_count += 1

            print(f"=== 과거 데이터 생성 완료: {success_count}/{len(etf_info)} ===")
            return success_count == len(etf_info)

        finally:
            if self.connection:
                self.connection.close()

def main():
    generator = HistoricalDataGenerator()
    success = generator.run_generation()

    if success:
        print("✅ ETF 과거 데이터 생성 성공!")
        sys.exit(0)
    else:
        print("❌ ETF 과거 데이터 생성 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()