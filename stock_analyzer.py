#!/usr/bin/env python3
"""
한국 주식 분석기 - 최종 버전
네이버 금융에서 정확한 등락률을 포함한 실시간 데이터 수집
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import re
import argparse
import os

class StockAnalyzer:
    def __init__(self):
        self.base_url = "https://finance.naver.com/item/main.naver"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.stock_groups = {
            'major': {
                '삼성전자': '005930', 'SK하이닉스': '000660', 'NAVER': '035420',
                '카카오': '035720', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
                'POSCO홀딩스': '005490', '현대차': '005380', 'KB금융': '105560', 'LG화학': '051910'
            },
            'it': {
                'NAVER': '035420', '카카오': '035720', '카카오뱅크': '323410',
                'NCSoft': '036570', 'SK텔레콤': '017670', 'KT': '030200',
                'LG전자': '066570', '삼성SDS': '018260'
            },
            'finance': {
                'KB금융': '105560', '신한지주': '055550', 'KakaoBank': '323410',
                '하나금융지주': '086790', '우리금융지주': '316140'
            }
        }
    
    def get_stock_data(self, stock_code):
        """종목 데이터 수집 - 등락률 정확히 파싱"""
        url = f"{self.base_url}?code={stock_code}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
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
            
            # 현재가
            price_elem = soup.select_one('.no_today .blind')
            if price_elem:
                price_text = price_elem.text.strip().replace(',', '')
                if price_text.isdigit():
                    data['current_price'] = int(price_text)
            
            # 전일대비
            change_elem = soup.select_one('.no_exday .blind')
            if change_elem:
                change_text = change_elem.text.strip().replace(',', '')
                if change_text.isdigit():
                    data['change'] = int(change_text)
            
            # 등락률 - 정확한 파싱
            # f_up (상승) 또는 f_down (하락) 클래스에서 %가 포함된 텍스트 찾기
            rate_elements = soup.find_all('em', class_=['f_up', 'f_down'])
            for elem in rate_elements:
                text = elem.text.strip()
                if '%' in text:
                    # +2.68% 형태에서 숫자만 추출
                    rate_match = re.search(r'([+-]?\d+\.?\d*)', text)
                    if rate_match:
                        rate_value = float(rate_match.group(1))
                        # f_down 클래스면 음수로 처리
                        if 'f_down' in elem.get('class', []):
                            rate_value = -abs(rate_value)
                        data['change_rate'] = rate_value
                        break
            
            # 거래량
            volume_elem = soup.select_one('#_volume')
            if volume_elem:
                volume_text = volume_elem.text.strip().replace(',', '')
                if volume_text.isdigit():
                    data['volume'] = int(volume_text)
            
            # 시가총액
            market_cap_elem = soup.select_one('#_market_sum')
            if market_cap_elem:
                data['market_cap_text'] = market_cap_elem.text.strip()
            
            return data
            
        except Exception as e:
            print(f"오류 발생 ({stock_code}): {e}")
            return None
    
    def analyze_group(self, group_name='major'):
        """그룹별 종목 분석"""
        if group_name not in self.stock_groups:
            print(f"지원하지 않는 그룹: {group_name}")
            return None
            
        stocks = self.stock_groups[group_name]
        results = []
        
        print(f"\n📊 {group_name.upper()} 종목 분석 시작...")
        print("=" * 80)
        
        for name, code in stocks.items():
            print(f"수집 중: {name} ({code})")
            data = self.get_stock_data(code)
            if data:
                data['display_name'] = name
                results.append(data)
            time.sleep(0.5)  # 과도한 요청 방지
        
        return results
    
    def print_analysis(self, results):
        """분석 결과 출력"""
        if not results:
            print("분석 데이터가 없습니다.")
            return
        
        print("\n" + "="*80)
        print(f"📈 주식 분석 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*80)
        print(f"{'종목명':<15} {'현재가':<12} {'전일대비':<12} {'등락률':<10} {'거래량':<15}")
        print("-" * 80)
        
        # 등락률 기준 정렬
        sorted_results = sorted(results, key=lambda x: x.get('change_rate', 0), reverse=True)
        
        total_up = sum(1 for x in results if x.get('change_rate', 0) > 0)
        total_down = sum(1 for x in results if x.get('change_rate', 0) < 0)
        total_flat = len(results) - total_up - total_down
        
        for stock in sorted_results:
            name = stock.get('display_name', '알수없음')
            price = stock.get('current_price', 0)
            change = stock.get('change', 0)
            rate = stock.get('change_rate', 0)
            volume = stock.get('volume', 0)
            
            # 상승/하락/보합 표시
            if rate > 0:
                change_symbol = "▲"
                rate_display = f"+{rate:.2f}%"
            elif rate < 0:
                change_symbol = "▼"
                rate_display = f"{rate:.2f}%"
            else:
                change_symbol = "-"
                rate_display = "0.00%"
            
            volume_display = f"{volume:,}" if volume > 0 else "N/A"
            
            print(f"{name:<15} {price:>9,}원 {change_symbol}{change:>6,}원 {rate_display:>8} {volume_display:>14}")
        
        print("-" * 80)
        print(f"📊 상승: {total_up}개 | 하락: {total_down}개 | 보합: {total_flat}개")
        
        # 최고/최저 종목
        if sorted_results:
            best = sorted_results[0]
            worst = sorted_results[-1]
            print(f"🚀 최고상승: {best['display_name']} ({best.get('change_rate', 0):+.2f}%)")
            print(f"📉 최대하락: {worst['display_name']} ({worst.get('change_rate', 0):+.2f}%)")
        
        print("=" * 80)
    
    def save_analysis(self, results, filename=None):
        """분석 결과 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"stock_analysis_{timestamp}.json"
        
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks': len(results),
            'summary': {
                'up': sum(1 for x in results if x.get('change_rate', 0) > 0),
                'down': sum(1 for x in results if x.get('change_rate', 0) < 0),
                'flat': sum(1 for x in results if x.get('change_rate', 0) == 0)
            },
            'stocks': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 분석 결과 저장: {filename}")
        return filename
    
    def screen_by_conditions(self, results, conditions):
        """조건에 맞는 종목 스크리닝"""
        filtered = []
        
        for stock in results:
            rate = stock.get('change_rate', 0)
            price = stock.get('current_price', 0)
            volume = stock.get('volume', 0)
            
            match = True
            
            if 'min_rate' in conditions and rate < conditions['min_rate']:
                match = False
            if 'max_rate' in conditions and rate > conditions['max_rate']:
                match = False
            if 'min_price' in conditions and price < conditions['min_price']:
                match = False
            if 'max_price' in conditions and price > conditions['max_price']:
                match = False
            if 'min_volume' in conditions and volume < conditions['min_volume']:
                match = False
                
            if match:
                filtered.append(stock)
        
        return filtered
    
    def quick_analysis(self, stock_code):
        """단일 종목 빠른 분석"""
        data = self.get_stock_data(stock_code)
        if not data:
            print(f"종목 코드 {stock_code} 데이터 수집 실패")
            return
        
        print(f"\n🔍 {data['name']} ({stock_code}) 분석")
        print("-" * 50)
        print(f"현재가: {data.get('current_price', 0):,}원")
        print(f"전일대비: {data.get('change', 0):+,}원")
        print(f"등락률: {data.get('change_rate', 0):+.2f}%")
        print(f"거래량: {data.get('volume', 0):,}")
        print(f"시가총액: {data.get('market_cap_text', 'N/A')}")
        print(f"업데이트: {data['timestamp']}")

def main():
    parser = argparse.ArgumentParser(description='한국 주식 분석기')
    parser.add_argument('--group', choices=['major', 'it', 'finance'], 
                       default='major', help='분석할 종목 그룹')
    parser.add_argument('--code', type=str, help='단일 종목 분석 (종목코드)')
    parser.add_argument('--screen', action='store_true', help='조건 스크리닝')
    
    args = parser.parse_args()
    
    analyzer = StockAnalyzer()
    
    if args.code:
        # 단일 종목 분석
        analyzer.quick_analysis(args.code)
    else:
        # 그룹 분석
        results = analyzer.analyze_group(args.group)
        if results:
            analyzer.print_analysis(results)
            
            # 스크리닝
            if args.screen:
                print("\n🔍 스크리닝 - 상승률 2% 이상 종목:")
                conditions = {'min_rate': 2.0}
                filtered = analyzer.screen_by_conditions(results, conditions)
                for stock in filtered:
                    name = stock['display_name']
                    rate = stock.get('change_rate', 0)
                    print(f"  • {name}: {rate:+.2f}%")
            
            # 결과 저장
            analyzer.save_analysis(results)

if __name__ == "__main__":
    main()