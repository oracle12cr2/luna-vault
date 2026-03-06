#!/usr/bin/env python3
"""
한국 주식 외부 Redis + Grafana 연동 실시간 시스템
Redis 서버: 192.168.50.9
Grafana 모니터링 지원
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

class ExternalRedisStockSystem:
    def __init__(self, redis_host='192.168.50.9', redis_port=6379, redis_password=None):
        # TNS 설정
        os.environ['TNS_ADMIN'] = '/usr/lib/oracle/23/client64/lib/network/admin'
        
        # 외부 Redis 연결
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password
        self.redis_client = None
        
        # Oracle 연결
        self.oracle_conn = None
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 모니터링 종목 (Grafana 메트릭용)
        self.monitored_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660', 
            'NAVER': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220',
            'LG전자': '066570',
            '현대차': '005380',
            '기아': '000270',
            'KB금융': '105560',
            '삼성바이오로직스': '207940'
        }
        
        self.running = True
        signal.signal(signal.SIGINT, self.stop_system)
        signal.signal(signal.SIGTERM, self.stop_system)
    
    def stop_system(self, signum, frame):
        """시스템 중지"""
        print(f"\n🛑 시스템 중지 신호 수신")
        self.running = False
    
    def connect_redis(self):
        """외부 Redis 서버 연결"""
        try:
            if self.redis_password:
                self.redis_client = redis.Redis(
                    host=self.redis_host, 
                    port=self.redis_port, 
                    password=self.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
            else:
                self.redis_client = redis.Redis(
                    host=self.redis_host, 
                    port=self.redis_port, 
                    decode_responses=True,
                    socket_connect_timeout=5
                )
            
            # 연결 테스트
            self.redis_client.ping()
            
            # 서버 정보 출력
            info = self.redis_client.info()
            redis_version = info.get('redis_version', 'N/A')
            memory_used = info.get('used_memory_human', 'N/A')
            
            print(f"✅ 외부 Redis 연결 성공")
            print(f"   📍 서버: {self.redis_host}:{self.redis_port}")
            print(f"   🔧 버전: Redis {redis_version}")
            print(f"   💾 메모리: {memory_used}")
            return True
            
        except redis.AuthenticationError:
            print(f"❌ Redis 인증 실패 ({self.redis_host})")
            print("💡 Redis 비밀번호를 --redis-password 옵션으로 제공해주세요")
            return False
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            return False
    
    def connect_oracle(self):
        """오라클 연결"""
        try:
            self.oracle_conn = cx_Oracle.connect('hr/oracle@PROD', encoding='UTF-8')
            print("✅ 오라클 연결 성공")
            return True
        except Exception as e:
            print(f"❌ 오라클 연결 실패: {e}")
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
            response = requests.get(url, params=params, headers=self.headers, timeout=8)
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
        """외부 Redis에 Grafana 친화적 캐싱"""
        if not self.redis_client:
            return False
            
        stock_code = stock_data['stock_code']
        stock_name = stock_data['stock_name']
        
        try:
            # 1. 실시간 가격 정보 (Grafana용)
            price_key = f"stock:price:{stock_code}"
            price_info = {
                'code': stock_code,
                'name': stock_name,
                'price': stock_data['price'],
                'volume': stock_data['volume'],
                'datetime': stock_data['datetime'].isoformat(),
                'timestamp': int(stock_data['timestamp'])
            }
            self.redis_client.setex(price_key, 120, json.dumps(price_info))
            
            # 2. Grafana 메트릭 (시계열 데이터)
            metrics_key = f"metrics:stock:{stock_code}"
            metric_data = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'price': stock_data['price'],
                'volume': stock_data['volume'],
                'timestamp': int(stock_data['timestamp']),
                'datetime': stock_data['datetime'].strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Time Series로 저장 (Grafana가 읽기 쉽게)
            ts_key = f"ts:stock:{stock_code}:{int(stock_data['timestamp'])}"
            self.redis_client.setex(ts_key, 3600, json.dumps(metric_data))
            
            # 3. 최신 가격 히스토리 (차트용)
            history_key = f"history:stock:{stock_code}"
            history_entry = f"{stock_data['price']}:{int(stock_data['timestamp'])}"
            self.redis_client.lpush(history_key, history_entry)
            self.redis_client.ltrim(history_key, 0, 99)  # 최근 100개
            self.redis_client.expire(history_key, 7200)  # 2시간 TTL
            
            # 4. 실시간 통계 (Grafana 대시보드용)
            self.update_realtime_stats(stock_data)
            
            return True
            
        except Exception as e:
            print(f"Redis 캐싱 실패 ({stock_code}): {e}")
            return False
    
    def update_realtime_stats(self, stock_data):
        """실시간 통계 업데이트 (Grafana용)"""
        stock_code = stock_data['stock_code']
        current_price = stock_data['price']
        
        try:
            # 오늘 시작가 캐싱
            open_key = f"open:stock:{stock_code}"
            open_price = self.redis_client.get(open_key)
            
            if not open_price:
                # 오라클에서 시작가 조회
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
                        # 하루 동안 캐싱
                        self.redis_client.setex(open_key, 86400, str(open_price))
                    cursor.close()
                else:
                    open_price = current_price
            else:
                open_price = float(open_price)
            
            if open_price and open_price > 0:
                change = current_price - float(open_price)
                change_rate = (change / float(open_price)) * 100
                
                # 실시간 메트릭 저장
                stats_key = f"stats:stock:{stock_code}"
                stats_data = {
                    'stock_code': stock_code,
                    'stock_name': stock_data['stock_name'],
                    'current_price': current_price,
                    'open_price': float(open_price),
                    'change': change,
                    'change_rate': round(change_rate, 2),
                    'volume': stock_data['volume'],
                    'timestamp': int(stock_data['timestamp']),
                    'last_update': datetime.now().isoformat()
                }
                self.redis_client.setex(stats_key, 300, json.dumps(stats_data))
                
                # 변동률 랭킹 (Sorted Set)
                ranking_key = "ranking:change_rate"
                self.redis_client.zadd(ranking_key, {f"{stock_code}:{stock_data['stock_name']}": change_rate})
                self.redis_client.expire(ranking_key, 600)
                
                # Grafana 알림용 임계치 확인
                if abs(change_rate) >= 2.0:  # 2% 이상 변동
                    alert_key = f"alert:stock:{stock_code}"
                    alert_data = {
                        'stock_code': stock_code,
                        'stock_name': stock_data['stock_name'],
                        'alert_type': 'significant_change',
                        'change_rate': change_rate,
                        'current_price': current_price,
                        'timestamp': int(stock_data['timestamp']),
                        'severity': 'high' if abs(change_rate) >= 5.0 else 'medium'
                    }
                    self.redis_client.setex(alert_key, 1800, json.dumps(alert_data))  # 30분 보관
            
        except Exception as e:
            print(f"통계 업데이트 실패: {e}")
    
    def save_to_oracle(self, stock_data):
        """오라클 저장"""
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
    
    def print_grafana_compatible_dashboard(self):
        """Grafana 호환 대시보드 출력"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("📊 Grafana 연동 실시간 주식 모니터링")
        print("=" * 80)
        print(f"📅 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Redis: {self.redis_host}:{self.redis_port}")
        
        # Redis 서버 상태
        try:
            info = self.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')
            connected_clients = info.get('connected_clients', 'N/A')
            total_keys = self.redis_client.dbsize()
            print(f"💾 Redis: {memory_used} | 연결: {connected_clients}개 | 키: {total_keys}개")
        except:
            print("💾 Redis: 상태 확인 실패")
        
        print("-" * 80)
        
        # 실시간 통계 출력
        all_stats = []
        for name, code in self.monitored_stocks.items():
            try:
                stats_key = f"stats:stock:{code}"
                stats_data = self.redis_client.get(stats_key)
                if stats_data:
                    stats = json.loads(stats_data)
                    stats['display_name'] = name
                    all_stats.append(stats)
            except:
                continue
        
        if all_stats:
            # 변동률 기준 정렬
            all_stats.sort(key=lambda x: x.get('change_rate', 0), reverse=True)
            
            print(f"{'종목명':<15} {'현재가':<10} {'변동':<12} {'등락률':<8} {'거래량':<12}")
            print("-" * 70)
            
            for stats in all_stats:
                name = stats['display_name']
                price = stats['current_price']
                change = stats.get('change', 0)
                rate = stats.get('change_rate', 0)
                volume = stats.get('volume', 0)
                
                if rate >= 2.0:
                    symbol = "🚨📈"
                elif rate > 0:
                    symbol = "📈"
                elif rate <= -2.0:
                    symbol = "🚨📉"
                elif rate < 0:
                    symbol = "📉"
                else:
                    symbol = "➡️"
                
                change_str = f"{change:+,.0f}원" if change else "0원"
                rate_str = f"{rate:+.1f}%" if rate else "0.0%"
                
                print(f"{symbol} {name:<13} {price:>8,}원 {change_str:<10} {rate_str:<6} {volume:>10,}")
        
        # 알림 현황
        try:
            alert_keys = self.redis_client.keys("alert:stock:*")
            if alert_keys:
                print(f"\n🚨 실시간 알림 ({len(alert_keys)}개):")
                for alert_key in alert_keys[:5]:  # 최대 5개
                    alert_data = json.loads(self.redis_client.get(alert_key))
                    name = alert_data.get('stock_name', 'N/A')
                    rate = alert_data.get('change_rate', 0)
                    severity = alert_data.get('severity', 'medium')
                    emoji = "🔥" if severity == 'high' else "⚠️"
                    print(f"  {emoji} {name}: {rate:+.1f}% ({severity})")
        except:
            pass
        
        print("-" * 80)
        print("📊 Grafana 대시보드에서 실시간 차트 확인 가능")
        print("🔑 Redis 키 패턴: stock:*, metrics:*, ranking:*, alert:*")
    
    def start_monitoring(self, interval=30):
        """Grafana 연동 실시간 모니터링"""
        if not self.connect_redis():
            return
        
        if not self.connect_oracle():
            print("⚠️ 오라클 없이 Redis만 사용합니다")
        
        print(f"🚀 Grafana 연동 실시간 모니터링 시작 (간격: {interval}초)")
        print(f"🔗 Redis: {self.redis_host}:{self.redis_port}")
        print(f"📊 Grafana: 실시간 메트릭 저장 중")
        print("-" * 60)
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                start_time = time.time()
                
                print(f"\n🔄 수집 사이클 {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                collected = cached = saved = alerts = 0
                
                for stock_name, stock_code in self.monitored_stocks.items():
                    # 데이터 수집
                    stock_data = self.get_current_price(stock_code)
                    
                    if stock_data:
                        collected += 1
                        
                        # Redis 캐싱 (Grafana용)
                        if self.cache_to_redis(stock_data):
                            cached += 1
                        
                        # Oracle 저장
                        if self.save_to_oracle(stock_data):
                            saved += 1
                        
                        # 알림 확인
                        alert_key = f"alert:stock:{stock_code}"
                        if self.redis_client.exists(alert_key):
                            alerts += 1
                    
                    time.sleep(0.1)  # API 제한
                
                elapsed = time.time() - start_time
                print(f"📊 수집: {collected}개 | Redis: {cached}개 | Oracle: {saved}개 | 알림: {alerts}개 ({elapsed:.1f}초)")
                
                # 대시보드 출력
                if collected > 0:
                    self.print_grafana_compatible_dashboard()
                
                # 대기
                print(f"\n⏱️ {interval}초 후 다음 수집...")
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    if i % 10 == 0 and i > 0:
                        print(".", end="", flush=True)
                
            except KeyboardInterrupt:
                print("\n🛑 사용자 중지")
                break
            except Exception as e:
                print(f"\n❌ 모니터링 오류: {e}")
                time.sleep(5)
        
        print("\n✅ Grafana 연동 모니터링 종료")
        if self.oracle_conn:
            self.oracle_conn.close()
    
    def show_grafana_keys(self):
        """Grafana에서 사용할 수 있는 Redis 키 패턴 출력"""
        if not self.connect_redis():
            return
            
        print("📊 Grafana Redis 데이터소스 설정 가이드")
        print("=" * 60)
        print(f"🔗 Redis 서버: {self.redis_host}:{self.redis_port}")
        
        try:
            # 키 패턴별 분류
            all_keys = self.redis_client.keys("*")
            key_patterns = {
                'stock:price:*': [],
                'metrics:stock:*': [],
                'stats:stock:*': [],
                'ranking:*': [],
                'alert:*': [],
                'history:*': []
            }
            
            for key in all_keys:
                for pattern in key_patterns.keys():
                    if key.startswith(pattern.replace('*', '')):
                        key_patterns[pattern].append(key)
                        break
            
            print(f"\n📋 Redis 키 패턴 ({len(all_keys)}개 총 키):")
            for pattern, keys in key_patterns.items():
                if keys:
                    print(f"\n🔑 {pattern} ({len(keys)}개)")
                    for key in keys[:3]:  # 샘플 3개만
                        try:
                            sample_data = self.redis_client.get(key)
                            if sample_data:
                                data = json.loads(sample_data)
                                if 'stock_name' in data:
                                    print(f"    {key} → {data.get('stock_name', 'N/A')}")
                                else:
                                    print(f"    {key}")
                        except:
                            print(f"    {key}")
            
            # Grafana 쿼리 예시
            print(f"\n📊 Grafana 쿼리 예시:")
            print(f"1. 실시간 가격: GET stats:stock:005930")
            print(f"2. 변동률 순위: ZREVRANGE ranking:change_rate 0 9 WITHSCORES")
            print(f"3. 가격 히스토리: LRANGE history:stock:005930 0 99")
            print(f"4. 알림 목록: KEYS alert:stock:*")
            
        except Exception as e:
            print(f"키 분석 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description='외부 Redis + Grafana 연동 주식 시스템')
    parser.add_argument('--redis-host', default='192.168.50.9', help='Redis 서버 IP')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis 포트')
    parser.add_argument('--redis-password', help='Redis 비밀번호')
    parser.add_argument('--interval', type=int, default=30, help='수집 간격(초)')
    parser.add_argument('--grafana-keys', action='store_true', help='Grafana용 키 패턴 출력')
    
    args = parser.parse_args()
    
    system = ExternalRedisStockSystem(
        redis_host=args.redis_host,
        redis_port=args.redis_port, 
        redis_password=args.redis_password
    )
    
    if args.grafana_keys:
        system.show_grafana_keys()
    else:
        system.start_monitoring(args.interval)

if __name__ == "__main__":
    main()