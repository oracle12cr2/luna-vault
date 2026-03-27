#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-

"""
US Market Closing Analysis Report
Daily market summary with Korean output
"""

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime, timezone, timedelta
import os
import sys
import oracledb
from typing import Dict, Any, Optional, List

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/stock/us_market.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarketDataCollector:
    """시장 데이터 수집 및 분석 클래스"""
    
    def __init__(self):
        self.data = {}
        self.fear_greed_index = None
        
        # 주요 지수
        self.indices = {
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            '^DJI': 'Dow Jones',
            '^SOX': 'SOX 반도체',
            '^RUT': 'Russell 2000'
        }
        
        # 섹터 ETF
        self.sectors = {
            'XLK': '기술',
            'XLF': '금융',
            'XLE': '에너지', 
            'XLV': '헬스케어',
            'XLY': '소비재(선택)',
            'XLP': '소비재(필수)',
            'XLI': '산업',
            'XLB': '소재',
            'XLRE': '부동산',
            'XLU': '유틸리티',
            'XLC': '통신'
        }
        
        # 채권/금리
        self.bonds = {
            '^IRX': '2년 국채',
            '^TNX': '10년 국채', 
            '^TYX': '30년 국채'
        }
        
        # 기타
        self.others = {
            '^VIX': 'VIX',
            'KRW=X': 'USD/KRW',
            'CL=F': 'WTI 유가',
            'GC=F': '금'
        }

    def format_percentage(self, value: float) -> str:
        """퍼센트 변화율 포맷팅"""
        if value > 0:
            return f"🟢 +{value:.2f}%"
        elif value < 0:
            return f"🔴 {value:.2f}%"
        else:
            return f"🟡 {value:.2f}%"
    
    def get_emoji_indicator(self, value: float) -> str:
        """변화율에 따른 이모지 지시자"""
        if value > 1.0:
            return "🚀"
        elif value > 0.5:
            return "🟢"
        elif value > 0:
            return "🟡"
        elif value > -0.5:
            return "🟠"
        elif value > -1.0:
            return "🔴"
        else:
            return "💀"

    def fetch_stock_data(self, symbols: Dict[str, str]) -> Dict[str, Any]:
        """주식 데이터 가져오기"""
        results = {}
        
        for symbol, name in symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    change = current_price - previous_price
                    change_pct = (change / previous_price) * 100
                    volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                    
                    results[symbol] = {
                        'name': name,
                        'price': current_price,
                        'change': change,
                        'change_pct': change_pct,
                        'volume': volume,
                        'symbol': symbol
                    }
                    
                    logger.info(f"✅ {name} ({symbol}): {current_price:.2f} {self.format_percentage(change_pct)}")
                else:
                    logger.warning(f"❌ {name} ({symbol}): 데이터 부족")
                    
            except Exception as e:
                logger.error(f"❌ {name} ({symbol}) 데이터 가져오기 실패: {e}")
                
        return results

    def fetch_fear_greed_index(self) -> Optional[Dict[str, Any]]:
        """CNN Fear & Greed Index 가져오기"""
        try:
            url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'fear_and_greed' in data:
                current_score = data['fear_and_greed']['score']
                rating = data['fear_and_greed']['rating']
                
                logger.info(f"✅ Fear & Greed Index: {current_score} ({rating})")
                return {
                    'score': current_score,
                    'rating': rating
                }
            else:
                logger.warning("❌ Fear & Greed Index: 응답 형식 오류")
                
        except Exception as e:
            logger.error(f"❌ Fear & Greed Index 가져오기 실패: {e}")
            
        return None

    def calculate_yield_spread(self, bonds_data: Dict[str, Any]) -> Optional[float]:
        """10Y-2Y 스프레드 계산"""
        try:
            if '^TNX' in bonds_data and '^IRX' in bonds_data:
                ten_year = bonds_data['^TNX']['price']
                two_year = bonds_data['^IRX']['price']
                spread = ten_year - two_year
                logger.info(f"✅ 10Y-2Y 스프레드: {spread:.2f}bp")
                return spread
            else:
                logger.warning("❌ 스프레드 계산: 필요한 데이터 없음")
        except Exception as e:
            logger.error(f"❌ 스프레드 계산 실패: {e}")
            
        return None

    def collect_all_data(self) -> Dict[str, Any]:
        """모든 데이터 수집"""
        logger.info("🚀 시장 데이터 수집 시작...")
        
        all_data = {
            'indices': self.fetch_stock_data(self.indices),
            'sectors': self.fetch_stock_data(self.sectors), 
            'bonds': self.fetch_stock_data(self.bonds),
            'others': self.fetch_stock_data(self.others),
            'fear_greed': self.fetch_fear_greed_index(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 스프레드 계산
        all_data['yield_spread'] = self.calculate_yield_spread(all_data['bonds'])
        
        logger.info("✅ 데이터 수집 완료")
        return all_data

class ReportGenerator:
    """보고서 생성 클래스"""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.collector = MarketDataCollector()
        
    def generate_section(self, title: str, items: Dict[str, Any]) -> str:
        """섹션별 보고서 생성"""
        if not items:
            return f"\n## {title}\n❌ 데이터 없음\n"
            
        section = f"\n## {title}\n"
        for symbol, info in items.items():
            emoji = self.collector.get_emoji_indicator(info['change_pct'])
            change_text = self.collector.format_percentage(info['change_pct'])
            section += f"{emoji} **{info['name']}**: ${info['price']:.2f} {change_text}\n"
            
        return section

    def generate_korean_report(self) -> str:
        """한국어 보고서 생성"""
        report_date = datetime.now().strftime('%Y년 %m월 %d일')
        
        report = f"""# 🇺🇸 미국 증시 마감 분석 - {report_date}

보고서 생성: {self.data['timestamp']}
"""
        
        # 주요 지수
        report += self.generate_section("📊 주요 지수", self.data['indices'])
        
        # 섹터 ETF
        report += self.generate_section("🏭 섹터별 ETF", self.data['sectors'])
        
        # 채권/금리
        bonds_section = self.generate_section("📈 채권 수익률", self.data['bonds'])
        if self.data.get('yield_spread'):
            spread = self.data['yield_spread']
            spread_emoji = "🟢" if spread > 0 else "🔴" if spread < 0 else "🟡"
            bonds_section += f"{spread_emoji} **10Y-2Y 스프레드**: {spread:.2f}bp\n"
        report += bonds_section
        
        # 기타 지표
        report += self.generate_section("📋 기타 지표", self.data['others'])
        
        # Fear & Greed Index
        if self.data.get('fear_greed'):
            fg = self.data['fear_greed']
            score = fg['score']
            rating = fg['rating']
            
            if score >= 75:
                emoji = "🔥"
            elif score >= 50:
                emoji = "🟢"
            elif score >= 25:
                emoji = "🟡"
            else:
                emoji = "🔴"
                
            report += f"\n## 😰 Fear & Greed Index\n{emoji} **{rating}**: {score:.1f}/100\n"
        
        # 요약
        report += self.generate_summary()
        
        return report

    def generate_summary(self) -> str:
        """시장 요약 생성"""
        summary = "\n## 📝 오늘의 시장 요약\n"
        
        # 주요 지수 동향
        indices = self.data.get('indices', {})
        if indices:
            sp500 = indices.get('^GSPC')
            nasdaq = indices.get('^IXIC')
            
            if sp500 and nasdaq:
                sp_change = sp500['change_pct']
                nq_change = nasdaq['change_pct']
                
                if sp_change > 0 and nq_change > 0:
                    trend = "상승세"
                elif sp_change < 0 and nq_change < 0:
                    trend = "하락세"
                else:
                    trend = "혼조세"
                    
                summary += f"• 주요 지수는 **{trend}**로 마감\n"
        
        # VIX 분석
        vix_data = self.data.get('others', {}).get('^VIX')
        if vix_data:
            vix = vix_data['price']
            if vix > 30:
                vix_text = "높음 (시장 불안)"
            elif vix > 20:
                vix_text = "보통"
            else:
                vix_text = "낮음 (시장 안정)"
                
            summary += f"• VIX {vix:.1f} - 변동성 **{vix_text}**\n"
        
        # Fear & Greed
        if self.data.get('fear_greed'):
            rating = self.data['fear_greed']['rating']
            summary += f"• 투자 심리: **{rating}**\n"
            
        return summary

    def generate_chat_summary(self) -> str:
        """채팅용 간단 요약"""
        summary = "🇺🇸 미국 증시 마감 요약\n"
        
        indices = self.data.get('indices', {})
        if indices:
            for symbol in ['^GSPC', '^IXIC', '^DJI']:
                if symbol in indices:
                    info = indices[symbol]
                    emoji = self.collector.get_emoji_indicator(info['change_pct'])
                    summary += f"{emoji} {info['name']}: {self.collector.format_percentage(info['change_pct'])}\n"
        
        # VIX
        vix_data = self.data.get('others', {}).get('^VIX')
        if vix_data:
            summary += f"📊 VIX: {vix_data['price']:.1f}\n"
        
        # Fear & Greed
        if self.data.get('fear_greed'):
            fg = self.data['fear_greed']
            summary += f"😰 F&G: {fg['score']:.1f}/100 ({fg['rating']})\n"
            
        return summary.strip()

class DatabaseManager:
    """Oracle 데이터베이스 관리 클래스"""
    
    def __init__(self):
        self.connection = None
        self.dsn = "192.168.50.35:1521/PROD"
        self.username = "app_user"
        self.password = "oracle"
        
    def connect(self) -> bool:
        """DB 연결"""
        try:
            self.connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn
            )
            logger.info("✅ Oracle DB 연결 성공")
            return True
        except Exception as e:
            logger.error(f"❌ Oracle DB 연결 실패: {e}")
            return False
    
    def create_table(self) -> bool:
        """테이블 생성"""
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            
            create_sql = """
            BEGIN
                EXECUTE IMMEDIATE '
                CREATE TABLE TB_US_MARKET_DAILY (
                    TRADE_DATE DATE,
                    SYMBOL VARCHAR2(20),
                    NAME VARCHAR2(100),
                    CLOSE_PRICE NUMBER,
                    CHANGE_PCT NUMBER,
                    VOLUME NUMBER,
                    CREATED_AT TIMESTAMP DEFAULT SYSTIMESTAMP
                )';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE = -955 THEN
                        NULL; -- Table already exists
                    ELSE
                        RAISE;
                    END IF;
            END;
            """
            
            cursor.execute(create_sql)
            self.connection.commit()
            cursor.close()
            
            logger.info("✅ 테이블 생성/확인 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 테이블 생성 실패: {e}")
            return False
    
    def save_market_data(self, data: Dict[str, Any]) -> bool:
        """시장 데이터 저장"""
        if not self.connection:
            return False
            
        try:
            cursor = self.connection.cursor()
            trade_date = datetime.now().date()
            
            # 기존 데이터 삭제 (오늘 날짜)
            delete_sql = "DELETE FROM TB_US_MARKET_DAILY WHERE TRADE_DATE = :trade_date"
            cursor.execute(delete_sql, trade_date=trade_date)
            
            # 새 데이터 삽입
            insert_sql = """
            INSERT INTO TB_US_MARKET_DAILY 
            (TRADE_DATE, SYMBOL, NAME, CLOSE_PRICE, CHANGE_PCT, VOLUME)
            VALUES (:trade_date, :symbol, :name, :close_price, :change_pct, :volume)
            """
            
            count = 0
            for category in ['indices', 'sectors', 'bonds', 'others']:
                category_data = data.get(category, {})
                for symbol, info in category_data.items():
                    cursor.execute(insert_sql,
                        trade_date=trade_date,
                        symbol=symbol,
                        name=info['name'],
                        close_price=float(info['price']),
                        change_pct=float(info['change_pct']),
                        volume=int(info['volume'])
                    )
                    count += 1
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ DB 저장 완료: {count}개 레코드")
            return True
            
        except Exception as e:
            logger.error(f"❌ DB 저장 실패: {e}")
            return False
    
    def close(self):
        """DB 연결 종료"""
        if self.connection:
            self.connection.close()
            logger.info("✅ DB 연결 종료")

def main():
    """메인 실행 함수"""
    logger.info("=" * 50)
    logger.info("🚀 미국 시장 분석 시작")
    logger.info("=" * 50)
    
    try:
        # 1. 데이터 수집
        collector = MarketDataCollector()
        market_data = collector.collect_all_data()
        
        # 2. 보고서 생성
        generator = ReportGenerator(market_data)
        report = generator.generate_korean_report()
        chat_summary = generator.generate_chat_summary()
        
        # 3. 파일 저장
        today = datetime.now().strftime('%Y%m%d')
        report_path = f"/root/.openclaw/workspace/stock/reports/us_market_{today}.txt"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ 보고서 저장: {report_path}")
        
        # 4. Oracle DB 저장 (선택사항)
        db = DatabaseManager()
        if db.connect() and db.create_table():
            db.save_market_data(market_data)
        db.close()
        
        # 5. 출력
        print("\n" + "=" * 60)
        print("📊 미국 시장 분석 보고서")
        print("=" * 60)
        print(report)
        
        print("\n" + "=" * 40)
        print("💬 채팅용 요약")
        print("=" * 40)
        print(chat_summary)
        
        logger.info("✅ 분석 완료!")
        
    except Exception as e:
        logger.error(f"❌ 실행 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()