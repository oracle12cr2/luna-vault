#!/usr/bin/env python3
"""
한국투자증권 OpenAPI 실제 ETF 데이터 수집기
계좌 개설 및 API 승인 후 사용
"""

import sys
import os
import requests
import json
import time
from datetime import datetime, timedelta
import cx_Oracle
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/etf_collector/kis_real.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KISRealCollector:
    def __init__(self):
        # API 설정 (승인 후 입력)
        self.app_key = os.getenv('KIS_APP_KEY', '')  # 환경변수에서 로드
        self.app_secret = os.getenv('KIS_APP_SECRET', '')
        self.account_no = os.getenv('KIS_ACCOUNT_NO', '')
        
        # API 엔드포인트
        self.base_url_real = "https://openapi.koreainvestment.com:9443"  # 실서버
        self.base_url_demo = "https://openapivts.koreainvestment.com:29443"  # 모의서버
        
        # 현재는 모의서버 사용 (테스트용)
        self.base_url = self.base_url_demo
        
        self.access_token = None
        
        # DB 설정
        self.db_host = 'oracle19c01'
        self.db_port = 1521
        self.db_service = 'PROD'
        self.db_user = 'stock'
        self.db_password = 'stock123'
        self.connection = None

    def get_access_token(self):
        """OAuth 2.0 토큰 발급"""
        if not self.app_key or not self.app_secret:
            logger.error("API KEY가 설정되지 않았습니다. 환경변수를 확인하세요.")
            return False
        
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result['access_token']
                logger.info("한투 API 토큰 발급 성공")
                return True
            else:
                logger.error(f"토큰 발급 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"토큰 발급 중 오류: {e}")
            return False

    def get_etf_current_price(self, etf_code):
        """ETF 현재가 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": etf_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                
                if result['rt_cd'] == '0':  # 성공
                    data = result['output']
                    return {
                        'etf_code': etf_code,
                        'current_price': float(data['stck_prpr']),  # 현재가
                        'open_price': float(data['stck_oprc']),    # 시가
                        'high_price': float(data['stck_hgpr']),    # 고가
                        'low_price': float(data['stck_lwpr']),     # 저가
                        'volume': int(data['acml_vol']),           # 거래량
                        'change_rate': float(data['prdy_ctrt']),   # 등락률
                        'timestamp': datetime.now()
                    }
                else:
                    logger.error(f"API 응답 오류: {result['msg1']}")
                    return None
            else:
                logger.error(f"HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"현재가 조회 중 오류 ({etf_code}): {e}")
            return None

    def get_etf_daily_chart(self, etf_code, period='D', count=30):
        """ETF 일봉 차트 데이터 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        
        headers = {
            "content-type": "application/json; charset=utf-8", 
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST03010100"
        }
        
        # 조회 종료일 (오늘)
        end_date = datetime.now().strftime('%Y%m%d')
        
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": etf_code,
            "fid_input_date_1": "",  # 시작일 (비워두면 count만큼)
            "fid_input_date_2": end_date,  # 종료일
            "fid_period_div_code": period,  # D: 일봉
            "fid_org_adj_prc": "0"  # 0: 수정주가 적용
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                
                if result['rt_cd'] == '0':
                    chart_data = []
                    
                    for item in result['output2']:  # output2에 차트 데이터
                        chart_data.append({
                            'etf_code': etf_code,
                            'trade_date': datetime.strptime(item['stck_bsop_date'], '%Y%m%d').date(),
                            'open_price': float(item['stck_oprc']),
                            'high_price': float(item['stck_hgpr']),
                            'low_price': float(item['stck_lwpr']),
                            'close_price': float(item['stck_clpr']),
                            'volume': int(item['acml_vol'])
                        })
                    
                    return chart_data
                else:
                    logger.error(f"일봉 조회 오류: {result['msg1']}")
                    return None
            else:
                logger.error(f"일봉 HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"일봉 조회 중 오류 ({etf_code}): {e}")
            return None

    def connect_db(self):
        """Oracle 데이터베이스 연결"""
        try:
            dsn = cx_Oracle.makedsn(self.db_host, self.db_port, service_name=self.db_service)
            self.connection = cx_Oracle.connect(self.db_user, self.db_password, dsn)
            logger.info("Oracle DB 연결 성공")
            return True
        except Exception as e:
            logger.error(f"Oracle DB 연결 실패: {e}")
            return False

    def save_current_price(self, price_data):
        """현재가 데이터를 실시간 테이블에 저장"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # 실시간 가격 테이블에 저장 (별도 테이블)
            insert_sql = """
            MERGE INTO etf_realtime_price r
            USING (
                SELECT :etf_code as etf_code, SYSDATE as update_time,
                       :current_price as current_price, :open_price as open_price,
                       :high_price as high_price, :low_price as low_price,
                       :volume as volume, :change_rate as change_rate
                FROM dual
            ) s ON (r.etf_code = s.etf_code)
            WHEN MATCHED THEN
                UPDATE SET 
                    current_price = s.current_price,
                    open_price = s.open_price,
                    high_price = s.high_price,
                    low_price = s.low_price,
                    volume = s.volume,
                    change_rate = s.change_rate,
                    update_time = s.update_time
            WHEN NOT MATCHED THEN
                INSERT (etf_code, current_price, open_price, high_price, low_price,
                       volume, change_rate, update_time)
                VALUES (s.etf_code, s.current_price, s.open_price, s.high_price,
                       s.low_price, s.volume, s.change_rate, s.update_time)
            """
            
            cursor.execute(insert_sql, {
                'etf_code': price_data['etf_code'],
                'current_price': price_data['current_price'],
                'open_price': price_data['open_price'],
                'high_price': price_data['high_price'],
                'low_price': price_data['low_price'],
                'volume': price_data['volume'],
                'change_rate': price_data['change_rate']
            })
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"{price_data['etf_code']} 실시간 가격 저장: {price_data['current_price']}원")
            return True
            
        except Exception as e:
            logger.error(f"실시간 가격 저장 실패: {e}")
            return False

    def collect_all_etfs(self):
        """모든 ETF 데이터 수집"""
        logger.info("=== 한투 OpenAPI ETF 데이터 수집 시작 ===")
        
        # DB 연결
        if not self.connect_db():
            return False
        
        try:
            # ETF 목록
            etf_codes = ['069500', '229200', '102110', '133690', '449180',
                        '161510', '091230', '160580', '091170', '130680']
            
            success_count = 0
            
            for etf_code in etf_codes:
                logger.info(f"[{etf_code}] 데이터 수집 중...")
                
                # 현재가 조회
                current_data = self.get_etf_current_price(etf_code)
                
                if current_data:
                    # 실시간 가격 저장
                    if self.save_current_price(current_data):
                        success_count += 1
                    
                    # API 호출 간격 (초당 최대 10건 권장)
                    time.sleep(0.1)
                else:
                    logger.warning(f"{etf_code}: 데이터 수집 실패")
                
                # API 부하 방지
                time.sleep(0.5)
            
            logger.info(f"=== 수집 완료: {success_count}/{len(etf_codes)} ===")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"데이터 수집 중 오류: {e}")
            return False
            
        finally:
            if self.connection:
                self.connection.close()

def setup_realtime_table():
    """실시간 가격 테이블 생성 (최초 1회)"""
    print("=== 실시간 가격 테이블 설정 ===")
    print("Oracle에서 다음 테이블을 생성하세요:")
    print("""
    CREATE TABLE etf_realtime_price (
        etf_code VARCHAR2(10) PRIMARY KEY,
        current_price NUMBER(10,2),
        open_price NUMBER(10,2),
        high_price NUMBER(10,2),
        low_price NUMBER(10,2),
        volume NUMBER(15),
        change_rate NUMBER(8,4),
        update_time DATE,
        FOREIGN KEY (etf_code) REFERENCES etf_master(etf_code)
    );
    """)

def main():
    """메인 함수"""
    print("=== 한국투자증권 OpenAPI ETF 수집기 ===")
    print("⚠️ 사용 전 준비사항:")
    print("1. 계좌 개설 완료")
    print("2. API 승인 완료") 
    print("3. 환경변수 설정:")
    print("   export KIS_APP_KEY='your_app_key'")
    print("   export KIS_APP_SECRET='your_app_secret'")
    print("   export KIS_ACCOUNT_NO='your_account'")
    print("")
    
    collector = KISRealCollector()
    
    # API 키 확인
    if not collector.app_key:
        print("❌ KIS_APP_KEY 환경변수가 설정되지 않았습니다.")
        setup_realtime_table()
        return
    
    # 데이터 수집 실행
    success = collector.collect_all_etfs()
    
    if success:
        print("✅ 실시간 ETF 데이터 수집 성공!")
        sys.exit(0)
    else:
        print("❌ 실시간 ETF 데이터 수집 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()