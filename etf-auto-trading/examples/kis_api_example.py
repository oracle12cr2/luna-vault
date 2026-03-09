#!/usr/bin/env python3
"""
한국투자증권 OpenAPI 연동 예시
실제 ETF 데이터 수집 (예시 코드)
"""

import requests
import json
from datetime import datetime

class KISAPICollector:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.base_url = "https://openapi.koreainvestment.com:9443"
    
    def get_access_token(self):
        """OAuth 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            self.access_token = result['access_token']
            return True
        return False
    
    def get_etf_price(self, etf_code='069500'):
        """ETF 현재가 조회 (KODEX 200 예시)"""
        if not self.access_token:
            self.get_access_token()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        
        params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": etf_code}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_etf_ohlcv(self, etf_code='069500', period='D'):
        """ETF 일봉 데이터 조회"""
        # 실제 구현 시 필요한 API 호출
        pass

def example_usage():
    """사용 예시"""
    print("=== 한국투자증권 OpenAPI 연동 예시 ===")
    print("⚠️ 실제 사용하려면:")
    print("1. 한국투자증권 계좌 개설")
    print("2. OpenAPI 신청 (https://apiportal.koreainvestment.com)")
    print("3. APP_KEY, APP_SECRET 발급")
    print("4. 일일 조회 한도 확인 (무료: 일 1만건)")
    print("")
    print("연동 후 장점:")
    print("- ✅ 실시간 ETF 가격")
    print("- ✅ 실제 거래량 데이터") 
    print("- ✅ 정확한 OHLCV")
    print("- ✅ 공식 데이터 (신뢰성)")

if __name__ == "__main__":
    example_usage()