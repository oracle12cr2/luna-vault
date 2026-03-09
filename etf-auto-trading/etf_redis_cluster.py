#!/usr/bin/env python3
"""
ETF Redis 클러스터 연결 및 관리
실제 Redis 클러스터 (192.168.50.3/4/5) 연동
"""

import redis
from redis.cluster import RedisCluster
import yaml
import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional

class ETFRedisCluster:
    def __init__(self, config_file='config_redis_cluster.yaml'):
        """Redis 클러스터 연결 초기화"""
        self.load_config(config_file)
        self.setup_cluster()
        self.setup_logging()
        
    def load_config(self, config_file):
        """설정 파일 로드"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
    def setup_cluster(self):
        """Redis 클러스터 연결 설정"""
        cluster_config = self.config['redis_cluster']
        
        # 클러스터 노드 설정
        startup_nodes = []
        for node in cluster_config['nodes']:
            startup_nodes.append({
                'host': node['host'], 
                'port': node['port']
            })
            
        self.logger = logging.getLogger(__name__)
        
        try:
            # Redis 클러스터 연결
            self.redis_cluster = RedisCluster(
                startup_nodes=startup_nodes,
                password=cluster_config['password'],
                decode_responses=cluster_config['decode_responses'],
                skip_full_coverage_check=cluster_config['skip_full_coverage_check'],
                health_check_interval=cluster_config['health_check_interval'],
                max_connections=cluster_config.get('max_connections', 50),
                retry_on_timeout=cluster_config.get('retry_on_timeout', True),
                socket_timeout=cluster_config.get('socket_timeout', 5),
                socket_connect_timeout=cluster_config.get('socket_connect_timeout', 5)
            )
            
            # 클러스터 상태 확인
            self.redis_cluster.ping()
            print("✅ Redis 클러스터 연결 성공!")
            
            # 클러스터 노드 정보 출력
            self.print_cluster_info()
            
        except Exception as e:
            print(f"❌ Redis 클러스터 연결 실패: {e}")
            
            # 폴백: 단일 노드 연결 시도
            self.setup_fallback_connection()
            
    def setup_fallback_connection(self):
        """폴백: 단일 Redis 노드 연결"""
        print("🔄 단일 노드 연결 시도...")
        
        # 첫 번째 노드로 연결 시도
        fallback_config = self.config['redis']
        
        try:
            self.redis_cluster = redis.Redis(
                host=fallback_config['host'],
                port=fallback_config['port'],
                password=fallback_config['password'],
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            self.redis_cluster.ping()
            print(f"✅ 단일 노드 연결 성공: {fallback_config['host']}")
            
        except Exception as e:
            print(f"❌ 단일 노드 연결도 실패: {e}")
            raise
            
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def print_cluster_info(self):
        """클러스터 정보 출력"""
        try:
            # 클러스터 정보 조회
            cluster_info = self.redis_cluster.cluster_info()
            nodes_info = self.redis_cluster.cluster_nodes()
            
            print("\n📊 Redis 클러스터 상태:")
            print(f"  클러스터 상태: {cluster_info.get('cluster_state', 'unknown')}")
            print(f"  클러스터 슬롯: {cluster_info.get('cluster_slots_assigned', 0)}/16384")
            print(f"  마스터 노드: {cluster_info.get('cluster_known_nodes', 0)}개")
            
            print("\n📍 클러스터 노드 목록:")
            active_nodes = 0
            for node_id, node_data in nodes_info.items():
                if 'master' in node_data['flags']:
                    host = node_data['host']
                    port = node_data['port']
                    status = "🟢 활성" if 'fail' not in node_data['flags'] else "🔴 실패"
                    print(f"  {host}:{port} - {status}")
                    if 'fail' not in node_data['flags']:
                        active_nodes += 1
                        
            print(f"\n✅ 활성 노드: {active_nodes}개")
            
        except Exception as e:
            print(f"⚠️ 클러스터 정보 조회 실패: {e}")

    def test_cluster_operations(self):
        """클러스터 기본 동작 테스트"""
        print("\n🧪 Redis 클러스터 동작 테스트")
        print("=" * 40)
        
        try:
            # 1. 기본 SET/GET 테스트
            test_key = "etf:test:cluster"
            test_value = {"test": True, "timestamp": datetime.now().isoformat()}
            
            self.redis_cluster.hset(test_key, mapping=test_value)
            retrieved = self.redis_cluster.hgetall(test_key)
            
            if retrieved:
                print("✅ SET/GET 테스트 성공")
            else:
                print("❌ SET/GET 테스트 실패")
                
            # 2. TTL 테스트
            self.redis_cluster.expire(test_key, 60)
            ttl = self.redis_cluster.ttl(test_key)
            print(f"✅ TTL 설정 성공: {ttl}초")
            
            # 3. 다중 키 테스트
            for i in range(3):
                key = f"etf:test:node:{i}"
                value = f"test_value_{i}"
                self.redis_cluster.set(key, value)
                
            print("✅ 다중 키 분산 저장 성공")
            
            # 4. 키 분포 확인
            print("\n📊 키 분포 확인:")
            for i in range(3):
                key = f"etf:test:node:{i}"
                try:
                    # 키가 어느 노드에 있는지 확인 (클러스터 모드)
                    node_info = self.redis_cluster.cluster_keyslot(key)
                    print(f"  {key} → 슬롯 {node_info}")
                except:
                    print(f"  {key} → 저장됨")
                    
            # 5. 정리
            self.redis_cluster.delete(test_key)
            for i in range(3):
                self.redis_cluster.delete(f"etf:test:node:{i}")
                
            print("✅ 테스트 데이터 정리 완료")
            
        except Exception as e:
            print(f"❌ 클러스터 테스트 실패: {e}")

    def store_etf_data(self, etf_code: str, data: Dict):
        """ETF 데이터를 클러스터에 저장"""
        try:
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            # 1. 실시간 가격 정보
            current_key = f"etf:current:{etf_code}"
            self.redis_cluster.hset(current_key, mapping=data)
            self.redis_cluster.expire(current_key, 86400)  # 24시간 TTL
            
            # 2. 시계열 데이터
            timeseries_key = f"etf:timeseries:{etf_code}"
            timeseries_data = {
                'timestamp': timestamp,
                'price': data['current_price'],
                'volume': data['volume']
            }
            
            score = int(datetime.now().timestamp())
            self.redis_cluster.zadd(
                timeseries_key,
                {json.dumps(timeseries_data): score}
            )
            self.redis_cluster.expire(timeseries_key, 86400)
            
            # 3. 일일 통계 업데이트
            today = datetime.now().strftime('%Y-%m-%d')
            daily_key = f"etf:daily:{etf_code}:{today}"
            
            # 기존 일일 데이터 조회
            existing_data = self.redis_cluster.hgetall(daily_key)
            
            # 최고/최저가 업데이트
            high_price = max(
                float(existing_data.get('high_price', 0)),
                data['high_price']
            )
            low_price = min(
                float(existing_data.get('low_price', float('inf'))),
                data['low_price']
            )
            
            daily_data = {
                'etf_code': etf_code,
                'date': today,
                'open_price': existing_data.get('open_price', data['open_price']),
                'high_price': high_price,
                'low_price': low_price,
                'current_price': data['current_price'],
                'volume': data['volume'],
                'last_update': timestamp
            }
            
            self.redis_cluster.hset(daily_key, mapping=daily_data)
            self.redis_cluster.expire(daily_key, 604800)  # 7일 TTL
            
            self.logger.debug(f"클러스터 저장 완료: {etf_code} - {data['current_price']}")
            
        except Exception as e:
            self.logger.error(f"클러스터 저장 실패 {etf_code}: {e}")

    def get_etf_data(self, etf_code: str) -> Dict:
        """ETF 실시간 데이터 조회"""
        try:
            current_key = f"etf:current:{etf_code}"
            data = self.redis_cluster.hgetall(current_key)
            return data
            
        except Exception as e:
            self.logger.error(f"데이터 조회 실패 {etf_code}: {e}")
            return {}

    def get_timeseries_data(self, etf_code: str, count: int = 100) -> List[Dict]:
        """시계열 데이터 조회"""
        try:
            timeseries_key = f"etf:timeseries:{etf_code}"
            data_list = self.redis_cluster.zrevrange(
                timeseries_key, 0, count-1, withscores=True
            )
            
            result = []
            for data_json, score in data_list:
                data_point = json.loads(data_json)
                data_point['score'] = score
                result.append(data_point)
                
            return result
            
        except Exception as e:
            self.logger.error(f"시계열 조회 실패 {etf_code}: {e}")
            return []

    def get_cluster_stats(self) -> Dict:
        """클러스터 통계 정보 조회"""
        try:
            stats = {
                'cluster_info': self.redis_cluster.cluster_info(),
                'cluster_nodes_count': len(self.redis_cluster.cluster_nodes()),
                'total_keys': 0,
                'etf_keys': {}
            }
            
            # ETF별 키 개수 계산
            etf_codes = self.config['etf']['target_codes']
            for etf_code in etf_codes:
                try:
                    # 각 ETF의 키 패턴별 개수
                    current_exists = self.redis_cluster.exists(f"etf:current:{etf_code}")
                    timeseries_count = self.redis_cluster.zcard(f"etf:timeseries:{etf_code}")
                    
                    stats['etf_keys'][etf_code] = {
                        'current': 1 if current_exists else 0,
                        'timeseries': timeseries_count
                    }
                except:
                    pass
                    
            return stats
            
        except Exception as e:
            self.logger.error(f"클러스터 통계 조회 실패: {e}")
            return {}

    def cleanup_old_data(self, days_old: int = 7):
        """오래된 데이터 정리"""
        try:
            cutoff_timestamp = int(
                (datetime.now().timestamp() - (days_old * 86400))
            )
            
            etf_codes = self.config['etf']['target_codes']
            cleaned_count = 0
            
            for etf_code in etf_codes:
                timeseries_key = f"etf:timeseries:{etf_code}"
                
                # 오래된 시계열 데이터 삭제
                removed = self.redis_cluster.zremrangebyscore(
                    timeseries_key, 0, cutoff_timestamp
                )
                
                if removed > 0:
                    cleaned_count += removed
                    self.logger.info(f"{etf_code} 오래된 데이터 {removed}개 정리")
                    
            self.logger.info(f"총 {cleaned_count}개 오래된 데이터 정리 완료")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"데이터 정리 실패: {e}")
            return 0

def main():
    """Redis 클러스터 테스트 실행"""
    print("🚀 ETF Redis 클러스터 테스트")
    print("=" * 50)
    
    try:
        # Redis 클러스터 연결
        cluster = ETFRedisCluster()
        
        # 클러스터 동작 테스트
        cluster.test_cluster_operations()
        
        # ETF 데이터 테스트 저장
        print("\n📊 ETF 데이터 저장 테스트")
        print("-" * 30)
        
        test_etf_data = {
            'etf_code': '069500',
            'current_price': 27500,
            'open_price': 27450,
            'high_price': 27600,
            'low_price': 27400,
            'volume': 1500000,
            'timestamp': datetime.now().isoformat()
        }
        
        cluster.store_etf_data('069500', test_etf_data)
        print("✅ ETF 데이터 저장 완료")
        
        # 데이터 조회 테스트
        retrieved_data = cluster.get_etf_data('069500')
        if retrieved_data:
            print(f"✅ ETF 데이터 조회 성공: {retrieved_data['current_price']}")
        
        # 클러스터 통계
        stats = cluster.get_cluster_stats()
        print(f"\n📈 클러스터 통계:")
        print(f"  노드 수: {stats.get('cluster_nodes_count', 'N/A')}")
        print(f"  ETF 데이터: {len(stats.get('etf_keys', {}))}")
        
        print("\n✅ Redis 클러스터 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    main()