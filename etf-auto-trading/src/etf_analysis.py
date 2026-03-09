#!/usr/bin/env python3
"""
ETF 포트폴리오 분석 도구
- 10개 ETF 현황 분석
- 수익률, 변동성, 상관관계 등
"""

import sys
import cx_Oracle
import pandas as pd
from datetime import datetime, timedelta
import json

class ETFAnalysis:
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
            return True
        except Exception as e:
            print(f"DB 연결 실패: {e}")
            return False

    def get_etf_summary(self):
        """ETF 포트폴리오 요약"""
        cursor = self.connection.cursor()
        
        # ETF별 최신 가격 및 통계
        cursor.execute("""
            SELECT e.etf_code, e.etf_name, e.category,
                   ROUND(e.nav, 2) as current_nav,
                   COUNT(p.trade_date) as data_points,
                   ROUND(AVG(p.volume), 0) as avg_volume,
                   ROUND(STDDEV(p.close_price), 2) as price_volatility
            FROM etf_master e
            LEFT JOIN etf_daily_price p ON e.etf_code = p.etf_code
            GROUP BY e.etf_code, e.etf_name, e.category, e.nav
            ORDER BY e.nav DESC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        print("\n" + "="*80)
        print("📊 ETF 포트폴리오 현황 요약")
        print("="*80)
        print(f"{'코드':<8} {'ETF명':<20} {'카테고리':<12} {'현재가':<10} {'변동성':<8} {'거래량':<12}")
        print("-"*80)
        
        total_value = 0
        for row in results:
            etf_code, etf_name, category, nav, data_points, avg_volume, volatility = row
            
            # 이름 길이 조정
            display_name = etf_name[:18] + ".." if len(etf_name) > 20 else etf_name
            display_category = category[:10] + ".." if len(category) > 12 else category
            
            print(f"{etf_code:<8} {display_name:<20} {display_category:<12} {nav:>8,.0f}원 {volatility or 0:>6,.1f} {avg_volume or 0:>10,.0f}")
            total_value += nav or 0
        
        print("-"*80)
        print(f"💰 포트폴리오 총 NAV 합계: {total_value:,.0f}원")
        print(f"📈 평균 ETF 가격: {total_value/len(results):,.0f}원")
        
        return results

    def get_category_distribution(self):
        """카테고리별 분포"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT category, COUNT(*) as etf_count,
                   ROUND(AVG(nav), 0) as avg_nav
            FROM etf_master
            GROUP BY category
            ORDER BY etf_count DESC, avg_nav DESC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        print("\n" + "="*50)
        print("📋 카테고리별 ETF 분포")
        print("="*50)
        print(f"{'카테고리':<15} {'종목수':<8} {'평균가격':<12}")
        print("-"*50)
        
        for category, count, avg_nav in results:
            display_category = category[:13] + ".." if len(category) > 15 else category
            print(f"{display_category:<15} {count:>6}개 {avg_nav:>10,.0f}원")
        
        return results

    def get_price_changes(self):
        """가격 변동 분석"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            WITH price_change AS (
                SELECT etf_code,
                       close_price,
                       LAG(close_price) OVER (PARTITION BY etf_code ORDER BY trade_date) as prev_price,
                       trade_date
                FROM etf_daily_price
            )
            SELECT e.etf_code, e.etf_name,
                   ROUND(((pc.close_price - pc.prev_price) / pc.prev_price * 100), 2) as daily_change
            FROM price_change pc
            JOIN etf_master e ON pc.etf_code = e.etf_code
            WHERE pc.prev_price IS NOT NULL
            AND pc.trade_date = (SELECT MAX(trade_date) FROM etf_daily_price WHERE etf_code = pc.etf_code)
            ORDER BY daily_change DESC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        print("\n" + "="*60)
        print("📈 최근 일일 변동률 (전일 대비)")
        print("="*60)
        print(f"{'코드':<8} {'ETF명':<25} {'변동률':<10}")
        print("-"*60)
        
        for etf_code, etf_name, change in results:
            display_name = etf_name[:23] + ".." if len(etf_name) > 25 else etf_name
            change_str = f"{change:+.2f}%" if change else "N/A"
            color = "🟢" if change and change > 0 else "🔴" if change and change < 0 else "⚪"
            print(f"{etf_code:<8} {display_name:<25} {color} {change_str:>6}")
        
        return results

    def generate_json_report(self):
        """JSON 형태 리포트 생성"""
        cursor = self.connection.cursor()
        
        # 전체 데이터 조회
        cursor.execute("""
            SELECT e.etf_code, e.etf_name, e.category, e.expense_ratio, e.nav,
                   COUNT(p.trade_date) as data_count,
                   MIN(p.trade_date) as first_date,
                   MAX(p.trade_date) as last_date
            FROM etf_master e
            LEFT JOIN etf_daily_price p ON e.etf_code = p.etf_code
            GROUP BY e.etf_code, e.etf_name, e.category, e.expense_ratio, e.nav
            ORDER BY e.etf_code
        """)
        
        results = cursor.fetchall()
        cursor.close()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_etfs": len(results),
            "etfs": []
        }
        
        for row in results:
            etf_data = {
                "code": row[0],
                "name": row[1],
                "category": row[2],
                "expense_ratio": float(row[3]) if row[3] else 0,
                "nav": float(row[4]) if row[4] else 0,
                "data_count": int(row[5]) if row[5] else 0,
                "first_date": row[6].isoformat() if row[6] else None,
                "last_date": row[7].isoformat() if row[7] else None
            }
            report["etfs"].append(etf_data)
        
        # JSON 파일로 저장
        report_file = '/root/.openclaw/workspace/etf_collector/etf_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 JSON 리포트 저장: {report_file}")
        return report

    def run_analysis(self):
        """분석 실행"""
        if not self.connect_db():
            return False
        
        try:
            print(f"\n🕒 분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. 포트폴리오 요약
            self.get_etf_summary()
            
            # 2. 카테고리 분포
            self.get_category_distribution()
            
            # 3. 가격 변동
            self.get_price_changes()
            
            # 4. JSON 리포트
            self.generate_json_report()
            
            print("\n" + "="*80)
            print("✅ ETF 포트폴리오 분석 완료!")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"❌ 분석 중 오류: {e}")
            return False
            
        finally:
            if self.connection:
                self.connection.close()

def main():
    analyzer = ETFAnalysis()
    success = analyzer.run_analysis()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()