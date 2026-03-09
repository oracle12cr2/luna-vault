#!/usr/bin/env python3
"""
ETF 실시간 데이터를 Redis 클러스터에 저장하는 시스템
장중: Redis에서 빠른 읽기/쓰기 처리
장후: Oracle DB로 배치 이관
"""

import redis
import json
import time
import yaml
from datetime import datetime, timedelta
import requests
from typing import Dict, List
import logging

class ETFRedisCollector:
    def __init__(self, config_file='config.yaml'):
        """ETF Redis 수집기 초기화"""
        self.load_config(config_file)
        self.setup_redis()
        self.setup_logging()
        
    def load_config(self, config_file):
        """설정 파일 로드"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
    def setup_redis(self):
        """Redis 클러스터 연결"""
        redis_config = {
            'host': '192.168.50.3',  # Redis 클러스터 첫 번째 노드
            'port': 6379,
            'password': 'redis',
            'decode_responses': True
        }
        
        self.redis_client = redis.Redis(**redis_config)
        
        # 연결 테스트
        try:
            self.redis_client.ping()
            print("✅ Redis 클러스터 연결 성공")
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            raise
            
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/etf_redis.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def collect_etf_realtime_data(self):
        """실시간 ETF 데이터 수집"""
        etf_codes = self.config['etf']['target_codes']
        
        for etf_code in etf_codes:
            try:
                # 한투 API 또는 시뮬레이션 데이터 수집
                etf_data = self.fetch_etf_data(etf_code)
                
                if etf_data:
                    # Redis에 실시간 데이터 저장
                    self.store_to_redis(etf_code, etf_data)
                    
                    # 기술적 지표 실시간 계산
                    self.calculate_realtime_indicators(etf_code, etf_data)
                    
            except Exception as e:
                self.logger.error(f"ETF {etf_code} 데이터 수집 실패: {e}")
                
        self.logger.info(f"실시간 데이터 수집 완료: {len(etf_codes)}개 ETF")

    def fetch_etf_data(self, etf_code: str) -> Dict:
        """ETF 데이터 가져오기 (한투 API 또는 시뮬레이션)"""
        # 실제 구현: 한투 API 호출
        # 현재: 시뮬레이션 데이터
        
        import random
        
        current_time = datetime.now()
        
        # 시뮬레이션 데이터 생성 (실제로는 API 호출)
        base_price = {
            '069500': 27000,  # KODEX 200
            '229200': 15000,  # KOSDAQ150  
            '102110': 19000,  # TIGER IT
            '133690': 25000,  # NASDAQ100
            '449180': 13000,  # S&P500
        }.get(etf_code, 20000)
        
        change_rate = random.uniform(-0.03, 0.03)  # ±3%
        current_price = round(base_price * (1 + change_rate), 0)
        
        etf_data = {
            'etf_code': etf_code,
            'current_price': current_price,
            'open_price': round(current_price * random.uniform(0.98, 1.02), 0),
            'high_price': round(current_price * random.uniform(1.00, 1.03), 0),
            'low_price': round(current_price * random.uniform(0.97, 1.00), 0),
            'volume': random.randint(100000, 1000000),
            'change_rate': round(change_rate * 100, 2),
            'timestamp': current_time.isoformat(),
            'update_time': current_time.strftime('%H:%M:%S')
        }
        
        return etf_data

    def store_to_redis(self, etf_code: str, data: Dict):
        """Redis에 실시간 데이터 저장"""
        
        # 1. 최신 가격 정보 (실시간 조회용)
        redis_key_current = f"etf:current:{etf_code}"
        self.redis_client.hset(redis_key_current, mapping=data)
        
        # 2. 시계열 데이터 (차트용)
        timestamp = data['timestamp']
        redis_key_timeseries = f"etf:timeseries:{etf_code}"
        
        # JSON으로 시계열 데이터 추가
        timeseries_data = {
            'timestamp': timestamp,
            'price': data['current_price'],
            'volume': data['volume']
        }
        
        self.redis_client.zadd(
            redis_key_timeseries, 
            {json.dumps(timeseries_data): int(datetime.now().timestamp())}
        )
        
        # 3. 일일 통계 업데이트
        today = datetime.now().strftime('%Y-%m-%d')
        redis_key_daily = f"etf:daily:{etf_code}:{today}"
        
        # 일일 최고/최저 업데이트
        existing_high = self.redis_client.hget(redis_key_daily, 'high_price')
        existing_low = self.redis_client.hget(redis_key_daily, 'low_price')
        
        high_price = max(
            float(existing_high) if existing_high else 0,
            data['high_price']
        )
        
        low_price = min(
            float(existing_low) if existing_low else float('inf'),
            data['low_price']
        )
        
        daily_data = {
            'etf_code': etf_code,
            'date': today,
            'open_price': data['open_price'],
            'high_price': high_price,
            'low_price': low_price,
            'current_price': data['current_price'],
            'volume': data['volume'],
            'change_rate': data['change_rate'],
            'last_update': timestamp
        }
        
        self.redis_client.hset(redis_key_daily, mapping=daily_data)
        
        # 4. TTL 설정 (메모리 관리)
        self.redis_client.expire(redis_key_current, 86400)  # 24시간
        self.redis_client.expire(redis_key_timeseries, 86400)  # 24시간
        self.redis_client.expire(redis_key_daily, 86400 * 7)  # 7일
        
        self.logger.debug(f"Redis 저장 완료: {etf_code} - {data['current_price']}")

    def calculate_realtime_indicators(self, etf_code: str, current_data: Dict):
        """실시간 기술적 지표 계산"""
        
        # Redis에서 최근 데이터 가져오기
        redis_key_timeseries = f"etf:timeseries:{etf_code}"
        
        # 최근 200개 데이터 포인트 가져오기 (SMA 200 계산용)
        recent_data = self.redis_client.zrevrange(
            redis_key_timeseries, 0, 199, withscores=True
        )
        
        if len(recent_data) < 20:
            return  # 데이터 부족
            
        # 가격 데이터 추출
        prices = []
        for data_json, _ in recent_data:
            data_point = json.loads(data_json)
            prices.append(data_point['price'])
        
        # 기술적 지표 계산
        indicators = self.calculate_technical_indicators(prices)
        
        # 매매 신호 생성
        signal = self.generate_trading_signal(indicators, current_data)
        
        # Redis에 지표 및 신호 저장
        timestamp = datetime.now().isoformat()
        
        indicators_data = {
            'etf_code': etf_code,
            'timestamp': timestamp,
            'current_price': current_data['current_price'],
            **indicators,
            'signal': signal['type'],
            'signal_strength': signal['strength'],
            'signal_reason': signal['reason']
        }
        
        redis_key_indicators = f"etf:indicators:{etf_code}"
        self.redis_client.hset(redis_key_indicators, mapping=indicators_data)
        self.redis_client.expire(redis_key_indicators, 86400)
        
        # 매매 신호가 중요한 경우 알림
        if signal['strength'] in ['STRONG', 'MEDIUM']:
            self.store_trading_signal(etf_code, signal, indicators_data)

    def calculate_technical_indicators(self, prices: List[float]) -> Dict:
        """기술적 지표 계산"""
        import numpy as np
        
        if len(prices) < 20:
            return {}
        
        prices_array = np.array(prices)
        
        indicators = {}
        
        # SMA 계산
        if len(prices) >= 5:
            indicators['sma_5'] = round(np.mean(prices_array[:5]), 2)
        if len(prices) >= 20:
            indicators['sma_20'] = round(np.mean(prices_array[:20]), 2)
        if len(prices) >= 60:
            indicators['sma_60'] = round(np.mean(prices_array[:60]), 2)
        if len(prices) >= 200:
            indicators['sma_200'] = round(np.mean(prices_array[:200]), 2)
            
        # RSI 계산 (간단 버전)
        if len(prices) >= 15:
            rsi = self.calculate_rsi(prices_array[:15])
            indicators['rsi_14'] = round(rsi, 2)
            
        return indicators

    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def generate_trading_signal(self, indicators: Dict, current_data: Dict) -> Dict:
        """매매 신호 생성"""
        
        signals = []
        
        # RSI 기반 신호
        rsi = indicators.get('rsi_14')
        if rsi:
            if rsi < 20:
                signals.append(('BUY', 'STRONG', f'RSI 극과매도 ({rsi:.1f})'))
            elif rsi < 30:
                signals.append(('BUY', 'MEDIUM', f'RSI 과매도 ({rsi:.1f})'))
            elif rsi > 80:
                signals.append(('SELL', 'STRONG', f'RSI 극과매수 ({rsi:.1f})'))
            elif rsi > 70:
                signals.append(('SELL', 'MEDIUM', f'RSI 과매수 ({rsi:.1f})'))
        
        # SMA 기반 신호
        sma_5 = indicators.get('sma_5')
        sma_20 = indicators.get('sma_20')
        
        if sma_5 and sma_20:
            if sma_5 > sma_20:
                signals.append(('BUY', 'MEDIUM', '단기 상승추세 (SMA5 > SMA20)'))
            else:
                signals.append(('SELL', 'WEAK', '단기 하락추세 (SMA5 < SMA20)'))
        
        # 신호 통합
        buy_signals = [s for s in signals if s[0] == 'BUY']
        sell_signals = [s for s in signals if s[0] == 'SELL']
        
        strength_weights = {'STRONG': 3, 'MEDIUM': 2, 'WEAK': 1}
        
        buy_score = sum(strength_weights[s[1]] for s in buy_signals)
        sell_score = sum(strength_weights[s[1]] for s in sell_signals)
        
        if buy_score > sell_score + 1:
            signal_type = 'BUY'
            strength = 'STRONG' if buy_score >= 4 else 'MEDIUM'
            reason = '; '.join([s[2] for s in buy_signals])
        elif sell_score > buy_score + 1:
            signal_type = 'SELL'
            strength = 'STRONG' if sell_score >= 4 else 'MEDIUM'
            reason = '; '.join([s[2] for s in sell_signals])
        else:
            signal_type = 'HOLD'
            strength = 'WEAK'
            reason = '혼합 신호'
        
        return {
            'type': signal_type,
            'strength': strength,
            'reason': reason,
            'buy_score': buy_score,
            'sell_score': sell_score
        }

    def store_trading_signal(self, etf_code: str, signal: Dict, indicators_data: Dict):
        """중요한 매매 신호 저장"""
        
        redis_key_signals = "etf:trading_signals"
        
        signal_data = {
            'etf_code': etf_code,
            'timestamp': indicators_data['timestamp'],
            'signal_type': signal['type'],
            'signal_strength': signal['strength'],
            'signal_reason': signal['reason'],
            'price': indicators_data['current_price'],
            'rsi': indicators_data.get('rsi_14'),
            'sma_5': indicators_data.get('sma_5'),
            'sma_20': indicators_data.get('sma_20')
        }
        
        # 리스트에 추가 (최대 1000개 유지)
        self.redis_client.lpush(redis_key_signals, json.dumps(signal_data))
        self.redis_client.ltrim(redis_key_signals, 0, 999)  # 최신 1000개만 유지
        
        self.logger.info(f"매매 신호: {etf_code} {signal['type']} ({signal['strength']}) - {signal['reason']}")

    def get_realtime_data(self, etf_code: str) -> Dict:
        """실시간 데이터 조회"""
        redis_key = f"etf:current:{etf_code}"
        data = self.redis_client.hgetall(redis_key)
        return data

    def get_trading_signals(self, limit: int = 10) -> List[Dict]:
        """최신 매매 신호 조회"""
        redis_key = "etf:trading_signals"
        signals_json = self.redis_client.lrange(redis_key, 0, limit - 1)
        
        signals = []
        for signal_json in signals_json:
            signal_data = json.loads(signal_json)
            signals.append(signal_data)
            
        return signals

    def run_realtime_collection(self, interval: int = 10):
        """실시간 수집 실행 (장중)"""
        self.logger.info("ETF 실시간 수집 시작")
        
        try:
            while True:
                market_hours = self.is_market_hours()
                
                if market_hours:
                    self.collect_etf_realtime_data()
                    time.sleep(interval)  # 10초 간격
                else:
                    self.logger.info("장 시간이 아님. 1시간 대기...")
                    time.sleep(3600)  # 1시간 대기
                    
        except KeyboardInterrupt:
            self.logger.info("실시간 수집 중단")

    def is_market_hours(self) -> bool:
        """한국 주식시장 시간 확인"""
        now = datetime.now()
        
        # 평일 확인
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
            
        # 장 시간 확인 (9:00 ~ 15:30)
        market_start = now.replace(hour=9, minute=0, second=0)
        market_end = now.replace(hour=15, minute=30, second=0)
        
        return market_start <= now <= market_end

def main():
    """메인 실행 함수"""
    print("🚀 ETF Redis 실시간 수집기 시작")
    
    collector = ETFRedisCollector()
    
    # 실시간 수집 시작
    collector.run_realtime_collection()

if __name__ == "__main__":
    main()