#!/usr/bin/env python3
"""
한국 주식 데이터 수집기
네이버 금융에서 실시간 주가 데이터를 수집
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

class KoreanStockCollector:
    def __init__(self):
        self.base_url = "https://finance.naver.com/item/main.naver"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 주요 종목 코드
        self.major_stocks = {
            '삼성전자': '005930',
            'SK하이닉스': '000660', 
            'NAVER': '035420',
            '카카오': '035720',
            'LG에너지솔루션': '373220',
            '삼성바이오로직스': '207940',
            'POSCO홀딩스': '005490',
            '현대차': '005380',
            'KB금융': '105560',
            'LG화학': '051910'
        }
    
    def get_stock_data(self, stock_code):
        """단일 종목 데이터 수집"""
        url = f"{self.base_url}?code={stock_code}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 기본 정보
            data = {
                'code': stock_code,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 종목명
            name_elem = soup.select_one('.wrap_company h2 a')
            if name_elem:
                data['name'] = name_elem.text.strip()
            
            # 현재가
            price_elem = soup.select_one('.no_today .blind')
            if price_elem:
                price_text = price_elem.text.strip().replace(',', '')
                data['current_price'] = int(price_text)
            
            # 전일대비 (상승/하락)
            change_elem = soup.select_one('.no_exday .blind')
            if change_elem:
                change_text = change_elem.text.strip().replace(',', '')
                data['change'] = int(change_text)
            
            # 등락률
            rate_elem = soup.select_one('.no_exrate .blind')
            if rate_elem:
                rate_text = rate_elem.text.strip().replace('%', '')
                data['change_rate'] = float(rate_text)
            
            # 거래량
            volume_elem = soup.select_one('#_volume')
            if volume_elem:
                volume_text = volume_elem.text.strip().replace(',', '')
                if volume_text.isdigit():
                    data['volume'] = int(volume_text)
            
            # 시가총액
            market_cap_elem = soup.select_one('#_market_sum')
            if market_cap_elem:
                market_cap_text = market_cap_elem.text.strip()
                # "123조 4,567억" 형태를 숫자로 변환
                data['market_cap_text'] = market_cap_text
            
            # 52주 최고/최저
            high_52w = soup.select_one('table.tb_type1_ifrs tr:nth-of-type(9) td:nth-of-type(2)')
            low_52w = soup.select_one('table.tb_type1_ifrs tr:nth-of-type(9) td:nth-of-type(4)')
            
            if high_52w and low_52w:
                high_text = high_52w.text.strip().replace(',', '')
                low_text = low_52w.text.strip().replace(',', '')
                if high_text.isdigit() and low_text.isdigit():
                    data['high_52w'] = int(high_text)
                    data['low_52w'] = int(low_text)
            
            return data
            
        except Exception as e:
            print(f"오류 발생 ({stock_code}): {e}")
            return None
    
    def get_multiple_stocks(self, stock_codes=None):
        """여러 종목 데이터 수집"""
        if stock_codes is None:
            stock_codes = self.major_stocks
            
        results = []
        
        for name, code in stock_codes.items():
            print(f"수집 중: {name} ({code})")
            data = self.get_stock_data(code)
            if data:
                data['display_name'] = name
                results.append(data)
            time.sleep(0.5)  # 요청 간격 조절
            
        return results
    
    def save_to_json(self, data, filename=None):
        """데이터를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"stock_data_{timestamp}.json"
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"데이터 저장 완료: {filename}")
        return filename
    
    def print_summary(self, data):
        """수집된 데이터 요약 출력"""
        print("\n" + "="*60)
        print(f"주식 데이터 수집 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*60)
        
        for stock in data:
            name = stock.get('display_name', stock.get('name', '알수없음'))
            price = stock.get('current_price', 0)
            change = stock.get('change', 0)
            rate = stock.get('change_rate', 0)
            
            change_symbol = "▲" if change > 0 else "▼" if change < 0 else "-"
            
            print(f"{name:12} {price:>8,}원 {change_symbol}{change:>6,}원 ({rate:>+5.1f}%)")
        
        print("="*60)

def main():
    collector = KoreanStockCollector()
    
    print("한국 주식 데이터 수집 시작...")
    
    # 주요 10개 종목 데이터 수집
    stock_data = collector.get_multiple_stocks()
    
    if stock_data:
        # 결과 출력
        collector.print_summary(stock_data)
        
        # JSON 파일로 저장
        filename = collector.save_to_json(stock_data)
        
        print(f"\n총 {len(stock_data)}개 종목 데이터 수집 완료")
        print(f"저장 파일: {filename}")
    else:
        print("데이터 수집 실패")

if __name__ == "__main__":
    main()