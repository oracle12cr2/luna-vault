#!/usr/bin/env python3
"""
한국 주식 데이터 수집기 v2.0
- 등락률 파싱 개선
- 실시간 모니터링 추가
- 알람 기능
- 차트 데이터 수집
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import re
import argparse

class KoreanStockCollector:
    def __init__(self):
        self.base_url = "https://finance.naver.com/item/main.naver"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 주요 종목 코드 (업데이트)
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
            'LG화학': '051910',
            '기아': '000270',
            'LG전자': '066570'
        }
        
        # IT 종목
        self.it_stocks = {
            'NAVER': '035420',
            '카카오': '035720',
            'NAVER클라우드플랫폼': '376300',
            '카카오뱅크': '323410',
            'NCSoft': '036570',
            'SK텔레콤': '017670',
            'KT': '030200',
            'LG유플러스': '032640'
        }
    
    def get_stock_data(self, stock_code):
        """단일 종목 데이터 수집 (개선된 버전)"""
        url = f"{self.base_url}?code={stock_code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {
                'code': stock_code,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 종목명
            name_elem = soup.select_one('.wrap_company h2 a')
            if name_elem:
                data['name'] = name_elem.text.strip()
            
            # 현재가 - 여러 선택자 시도
            price_selectors = [
                '.no_today .blind',
                '.today .no_today .blind', 
                'p.no_today em .blind'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem and price_elem.text.strip():
                    price_text = price_elem.text.strip().replace(',', '')
                    if price_text.isdigit():
                        data['current_price'] = int(price_text)
                        break
            
            # 전일대비 및 등락률 - 통합 파싱
            change_area = soup.select_one('.today .no_exday')
            if change_area:
                # 전일대비 금액
                change_elem = change_area.select_one('.blind')
                if change_elem:
                    change_text = change_elem.text.strip().replace(',', '')
                    if change_text.isdigit():
                        data['change'] = int(change_text)
                
                # 등락률
                rate_elem = change_area.select_one('.no_exrate .blind')
                if not rate_elem:
                    # 다른 선택자 시도
                    rate_elem = soup.select_one('.no_exrate .blind')
                
                if rate_elem:
                    rate_text = rate_elem.text.strip().replace('%', '').replace('+', '').replace('-', '')
                    try:
                        rate_value = float(rate_text)
                        # 상승/하락 표시 확인
                        if '상승' in change_area.get('class', []) or 'red' in str(change_area):
                            data['change_rate'] = rate_value
                        elif '하락' in change_area.get('class', []) or 'blue' in str(change_area):
                            data['change_rate'] = -rate_value
                        else:
                            data['change_rate'] = rate_value
                    except ValueError:
                        pass
            
            # 거래량
            volume_selectors = ['#_volume', '.date_volume em']
            for selector in volume_selectors:
                volume_elem = soup.select_one(selector)
                if volume_elem and volume_elem.text.strip():
                    volume_text = volume_elem.text.strip().replace(',', '')
                    if volume_text.isdigit():
                        data['volume'] = int(volume_text)
                        break
            
            # 시가총액
            market_cap_elem = soup.select_one('#_market_sum')
            if market_cap_elem:
                data['market_cap_text'] = market_cap_elem.text.strip()
            
            # PER, PBR
            table_rows = soup.select('table.tb_type1_ifrs tr')
            for row in table_rows:
                cells = row.select('td')
                if len(cells) >= 4:
                    labels = [cell.text.strip() for cell in cells[::2]]  # 홀수 번째만
                    values = [cell.text.strip() for cell in cells[1::2]]  # 짝수 번째만
                    
                    for label, value in zip(labels, values):
                        if 'PER' in label and value.replace('.', '').replace(',', '').replace('-', '').isdigit():
                            data['per'] = float(value.replace(',', ''))
                        elif 'PBR' in label and value.replace('.', '').replace(',', '').replace('-', '').isdigit():
                            data['pbr'] = float(value.replace(',', ''))
            
            return data
            
        except Exception as e:
            print(f"오류 발생 ({stock_code}): {e}")
            return None
    
    def get_stock_news(self, stock_code, limit=5):
        """종목 관련 뉴스 수집"""
        news_url = f"https://finance.naver.com/item/news_list.naver?code={stock_code}"
        
        try:
            response = requests.get(news_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            news_list = []
            news_items = soup.select('.simpleNewsList li')[:limit]
            
            for item in news_items:
                title_elem = item.select_one('a')
                date_elem = item.select_one('.date')
                
                if title_elem and date_elem:
                    news_list.append({
                        'title': title_elem.text.strip(),
                        'url': 'https://finance.naver.com' + title_elem.get('href', ''),
                        'date': date_elem.text.strip()
                    })
            
            return news_list
            
        except Exception as e:
            print(f"뉴스 수집 오류 ({stock_code}): {e}")
            return []
    
    def monitor_stocks(self, stock_list=None, interval=30, duration=3600):
        """실시간 모니터링"""
        if stock_list is None:
            stock_list = self.major_stocks
            
        print(f"실시간 모니터링 시작 (간격: {interval}초, 지속시간: {duration}초)")
        print("-" * 80)
        
        start_time = time.time()
        previous_data = {}
        
        while time.time() - start_time < duration:
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{current_time}] 데이터 수집 중...")
            
            for name, code in stock_list.items():
                data = self.get_stock_data(code)
                if data:
                    price = data.get('current_price', 0)
                    change = data.get('change', 0)
                    rate = data.get('change_rate', 0)
                    
                    # 가격 변동 알림
                    if code in previous_data:
                        prev_price = previous_data[code].get('current_price', 0)
                        if abs(price - prev_price) > prev_price * 0.02:  # 2% 이상 변동
                            print(f"🚨 {name}: {prev_price:,} → {price:,} ({((price-prev_price)/prev_price*100):+.1f}%)")
                    
                    previous_data[code] = data
                    
                    change_symbol = "▲" if change > 0 else "▼" if change < 0 else "-"
                    print(f"{name:12} {price:>8,}원 {change_symbol}{change:>6,}({rate:>+5.1f}%)")
                
                time.sleep(0.2)
            
            print("-" * 50)
            time.sleep(interval)
    
    def screen_stocks(self, criteria):
        """종목 스크리닝"""
        print(f"스크리닝 조건: {criteria}")
        print("-" * 60)
        
        results = []
        all_stocks = {**self.major_stocks, **self.it_stocks}
        
        for name, code in all_stocks.items():
            data = self.get_stock_data(code)
            if not data:
                continue
            
            price = data.get('current_price', 0)
            change_rate = data.get('change_rate', 0)
            volume = data.get('volume', 0)
            per = data.get('per', 0)
            
            # 스크리닝 조건 체크
            match = True
            
            if 'min_price' in criteria and price < criteria['min_price']:
                match = False
            if 'max_price' in criteria and price > criteria['max_price']:
                match = False
            if 'min_change_rate' in criteria and change_rate < criteria['min_change_rate']:
                match = False
            if 'max_per' in criteria and per > criteria['max_per']:
                match = False
                
            if match:
                results.append((name, data))
                print(f"{name:15} {price:>8,}원 {change_rate:>+5.1f}% PER:{per:>5.1f}")
            
            time.sleep(0.3)
        
        return results

def main():
    parser = argparse.ArgumentParser(description='한국 주식 데이터 수집기')
    parser.add_argument('--mode', choices=['collect', 'monitor', 'screen'], 
                       default='collect', help='실행 모드')
    parser.add_argument('--stocks', choices=['major', 'it', 'all'], 
                       default='major', help='종목 그룹')
    parser.add_argument('--interval', type=int, default=30, 
                       help='모니터링 간격(초)')
    parser.add_argument('--duration', type=int, default=3600, 
                       help='모니터링 지속시간(초)')
    
    args = parser.parse_args()
    
    collector = KoreanStockCollector()
    
    # 종목 선택
    if args.stocks == 'major':
        stock_list = collector.major_stocks
    elif args.stocks == 'it':
        stock_list = collector.it_stocks
    else:
        stock_list = {**collector.major_stocks, **collector.it_stocks}
    
    if args.mode == 'collect':
        print("주식 데이터 수집 시작...")
        stock_data = []
        
        for name, code in stock_list.items():
            print(f"수집 중: {name} ({code})")
            data = collector.get_stock_data(code)
            if data:
                data['display_name'] = name
                stock_data.append(data)
            time.sleep(0.5)
        
        # 결과 출력
        print("\n" + "="*60)
        print(f"주식 데이터 수집 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*60)
        
        for stock in stock_data:
            name = stock.get('display_name')
            price = stock.get('current_price', 0)
            change = stock.get('change', 0)
            rate = stock.get('change_rate', 0)
            
            change_symbol = "▲" if change > 0 else "▼" if change < 0 else "-"
            print(f"{name:15} {price:>8,}원 {change_symbol}{change:>6,}원 ({rate:>+5.1f}%)")
        
        # JSON 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"stock_data_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2)
        print(f"\n데이터 저장: {filename}")
        
    elif args.mode == 'monitor':
        collector.monitor_stocks(stock_list, args.interval, args.duration)
        
    elif args.mode == 'screen':
        # 예시 스크리닝 조건
        criteria = {
            'min_change_rate': 2.0,  # 2% 이상 상승
            'max_per': 20.0          # PER 20 이하
        }
        collector.screen_stocks(criteria)

if __name__ == "__main__":
    main()