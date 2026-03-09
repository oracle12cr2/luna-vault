#!/usr/bin/env python3
"""
월 350만원 수익 목표 ETF 자동매매 전략 분석기
현실적인 투자 계획 및 리스크 관리
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

class InvestmentStrategy350:
    def __init__(self):
        """투자 전략 분석기 초기화"""
        self.monthly_target = 3500000  # 월 350만원 목표
        self.annual_target = self.monthly_target * 12  # 연 4,200만원
        
        # ETF 예상 수익률 (보수적 추정)
        self.etf_expected_returns = {
            '069500': 0.08,   # KODEX 200 (8%)
            '229200': 0.12,   # KOSDAQ150 (12%) 
            '102110': 0.15,   # TIGER IT (15%)
            '133690': 0.18,   # NASDAQ100 (18%)
            '449180': 0.10,   # S&P500 (10%)
            '161510': 0.06,   # 고배당 (6%)
            '091230': 0.20,   # 2차전지 (20%, 고위험)
            '160580': 0.07,   # 삼성우선주 (7%)
            '091170': 0.09,   # 건설 (9%)
            '130680': 0.12    # 원유 (12%, 고변동)
        }
        
        # ETF 위험도 (표준편차)
        self.etf_volatility = {
            '069500': 0.18,   # KODEX 200
            '229200': 0.25,   # KOSDAQ150
            '102110': 0.28,   # TIGER IT
            '133690': 0.30,   # NASDAQ100  
            '449180': 0.20,   # S&P500
            '161510': 0.15,   # 고배당
            '091230': 0.35,   # 2차전지 (고위험)
            '160580': 0.12,   # 삼성우선주
            '091170': 0.22,   # 건설
            '130680': 0.28    # 원유
        }

    def calculate_required_capital(self) -> Dict:
        """필요한 투자 원금 계산"""
        
        scenarios = {
            'conservative': {
                'annual_return': 0.12,  # 연 12%
                'description': '보수적 (안정형)',
                'risk_level': '낮음'
            },
            'moderate': {
                'annual_return': 0.18,  # 연 18%
                'description': '중도형 (균형)',
                'risk_level': '중간'
            },
            'aggressive': {
                'annual_return': 0.25,  # 연 25%
                'description': '공격형 (성장)',
                'risk_level': '높음'
            }
        }
        
        results = {}
        
        for scenario_name, scenario in scenarios.items():
            required_capital = self.annual_target / scenario['annual_return']
            
            results[scenario_name] = {
                'required_capital': required_capital,
                'annual_return_rate': scenario['annual_return'],
                'monthly_return': required_capital * scenario['annual_return'] / 12,
                'description': scenario['description'],
                'risk_level': scenario['risk_level']
            }
            
        return results

    def create_portfolio_allocation(self, investment_amount: int, risk_profile: str) -> Dict:
        """리스크 프로필에 따른 포트폴리오 구성"""
        
        if risk_profile == 'conservative':
            # 보수적 포트폴리오 (안정성 중심)
            allocation = {
                '069500': 0.30,  # KODEX 200 (30%)
                '449180': 0.25,  # S&P500 (25%)
                '161510': 0.20,  # 고배당 (20%)
                '160580': 0.15,  # 삼성우선주 (15%)
                '091170': 0.10   # 건설 (10%)
            }
        elif risk_profile == 'moderate':
            # 균형 포트폴리오
            allocation = {
                '069500': 0.25,  # KODEX 200 (25%)
                '102110': 0.20,  # TIGER IT (20%)
                '133690': 0.15,  # NASDAQ100 (15%)
                '229200': 0.15,  # KOSDAQ150 (15%)
                '449180': 0.15,  # S&P500 (15%)
                '161510': 0.10   # 고배당 (10%)
            }
        else:  # aggressive
            # 공격적 포트폴리오 (성장성 중심)
            allocation = {
                '102110': 0.25,  # TIGER IT (25%)
                '133690': 0.20,  # NASDAQ100 (20%)
                '091230': 0.20,  # 2차전지 (20%)
                '229200': 0.15,  # KOSDAQ150 (15%)
                '130680': 0.10,  # 원유 (10%)
                '069500': 0.10   # KODEX 200 (10%)
            }
        
        # 투자 금액별 배분 계산
        portfolio = {}
        total_allocation = 0
        
        for etf_code, weight in allocation.items():
            amount = int(investment_amount * weight)
            portfolio[etf_code] = {
                'allocation_amount': amount,
                'weight': weight,
                'expected_annual_return': self.etf_expected_returns.get(etf_code, 0.10),
                'volatility': self.etf_volatility.get(etf_code, 0.20),
                'etf_name': self.get_etf_name(etf_code)
            }
            total_allocation += weight
            
        # 포트폴리오 전체 기대수익률 계산
        portfolio_return = sum(
            portfolio[code]['expected_annual_return'] * portfolio[code]['weight']
            for code in portfolio
        )
        
        # 포트폴리오 리스크 (간단한 가중평균)
        portfolio_risk = sum(
            portfolio[code]['volatility'] * portfolio[code]['weight']
            for code in portfolio
        )
        
        return {
            'allocation': portfolio,
            'total_investment': investment_amount,
            'expected_annual_return': portfolio_return,
            'expected_monthly_return': portfolio_return / 12,
            'expected_monthly_profit': investment_amount * portfolio_return / 12,
            'portfolio_risk': portfolio_risk,
            'risk_profile': risk_profile
        }

    def simulate_monthly_performance(self, portfolio: Dict, months: int = 12) -> List[Dict]:
        """월별 성과 시뮬레이션"""
        
        np.random.seed(42)  # 일관된 결과를 위한 시드 설정
        
        monthly_results = []
        cumulative_profit = 0
        current_balance = portfolio['total_investment']
        
        for month in range(1, months + 1):
            # 월별 수익률 시뮬레이션 (정규분포 가정)
            monthly_return_rate = np.random.normal(
                portfolio['expected_monthly_return'], 
                portfolio['portfolio_risk'] / 12
            )
            
            monthly_profit = current_balance * monthly_return_rate
            cumulative_profit += monthly_profit
            current_balance += monthly_profit
            
            # 목표 달성률 계산
            target_achievement = (monthly_profit / self.monthly_target) * 100
            
            monthly_results.append({
                'month': month,
                'monthly_profit': monthly_profit,
                'cumulative_profit': cumulative_profit,
                'current_balance': current_balance,
                'monthly_return_rate': monthly_return_rate * 100,
                'target_achievement': target_achievement,
                'target_gap': monthly_profit - self.monthly_target
            })
            
        return monthly_results

    def analyze_risk_scenarios(self, portfolio: Dict) -> Dict:
        """리스크 시나리오 분석"""
        
        scenarios = {
            'best_case': {
                'monthly_return_multiplier': 1.5,
                'description': '최선의 경우 (상승장)'
            },
            'normal_case': {
                'monthly_return_multiplier': 1.0,
                'description': '일반적인 경우 (횡보장)'
            },
            'worst_case': {
                'monthly_return_multiplier': 0.3,
                'description': '최악의 경우 (하락장)'
            },
            'crash_scenario': {
                'monthly_return_multiplier': -0.2,
                'description': '폭락 시나리오'
            }
        }
        
        base_monthly_profit = portfolio['expected_monthly_profit']
        
        results = {}
        for scenario_name, scenario in scenarios.items():
            monthly_profit = base_monthly_profit * scenario['monthly_return_multiplier']
            
            results[scenario_name] = {
                'monthly_profit': monthly_profit,
                'target_achievement': (monthly_profit / self.monthly_target) * 100,
                'annual_profit': monthly_profit * 12,
                'description': scenario['description']
            }
            
        return results

    def get_etf_name(self, etf_code: str) -> str:
        """ETF 코드를 이름으로 변환"""
        etf_names = {
            '069500': 'KODEX 200',
            '229200': 'KOSDAQ150',
            '102110': 'TIGER IT',
            '133690': 'NASDAQ100',
            '449180': 'S&P500',
            '161510': '고배당',
            '091230': '2차전지',
            '160580': '삼성우선주',
            '091170': '건설',
            '130680': '원유'
        }
        return etf_names.get(etf_code, etf_code)

    def generate_strategy_report(self, investment_amount: int = 200000000) -> Dict:
        """종합 투자 전략 리포트 생성"""
        
        print(f"🎯 월 350만원 수익 목표 달성 전략")
        print("=" * 50)
        
        # 1. 필요 투자금 분석
        required_capitals = self.calculate_required_capital()
        
        print("\n💰 필요 투자 원금 분석:")
        for scenario, data in required_capitals.items():
            print(f"  {data['description']}: {data['required_capital']:,.0f}원")
            print(f"    연 수익률: {data['annual_return_rate']*100:.1f}%")
            print(f"    위험도: {data['risk_level']}")
            print()
        
        # 2. 추천 포트폴리오 (2억원 기준)
        print(f"\n📊 추천 포트폴리오 (투자금: {investment_amount:,}원)")
        print("-" * 40)
        
        portfolios = {}
        for risk_profile in ['conservative', 'moderate', 'aggressive']:
            portfolio = self.create_portfolio_allocation(investment_amount, risk_profile)
            portfolios[risk_profile] = portfolio
            
            print(f"\n🎯 {risk_profile.upper()} 포트폴리오:")
            print(f"  예상 연 수익률: {portfolio['expected_annual_return']*100:.1f}%")
            print(f"  예상 월 수익: {portfolio['expected_monthly_profit']:,.0f}원")
            print(f"  목표 달성률: {portfolio['expected_monthly_profit']/self.monthly_target*100:.1f}%")
            
            print(f"\n  📋 ETF 구성:")
            for etf_code, data in portfolio['allocation'].items():
                print(f"    {data['etf_name']} ({etf_code}): {data['allocation_amount']:,}원 ({data['weight']*100:.0f}%)")
        
        # 3. 추천 전략 (Moderate 기준)
        recommended = portfolios['moderate']
        
        print(f"\n🏆 추천 전략: MODERATE 포트폴리오")
        print(f"  투자금: {investment_amount:,}원")
        print(f"  목표: 월 {self.monthly_target:,}원")
        print(f"  예상: 월 {recommended['expected_monthly_profit']:,.0f}원")
        
        # 4. 리스크 시나리오
        risk_analysis = self.analyze_risk_scenarios(recommended)
        
        print(f"\n⚠️ 리스크 시나리오 분석:")
        for scenario, data in risk_analysis.items():
            status = "✅" if data['monthly_profit'] >= self.monthly_target else "❌"
            print(f"  {status} {data['description']}: {data['monthly_profit']:,.0f}원/월 ({data['target_achievement']:.1f}%)")
        
        # 5. 성과 시뮬레이션
        simulation = self.simulate_monthly_performance(recommended, 12)
        
        print(f"\n📈 12개월 성과 시뮬레이션 (상위 6개월):")
        for result in simulation[:6]:
            status = "🎯" if result['monthly_profit'] >= self.monthly_target else "📊"
            print(f"  {status} {result['month']}월: {result['monthly_profit']:,.0f}원 "
                  f"({result['target_achievement']:.1f}% 달성)")
        
        return {
            'required_capitals': required_capitals,
            'portfolios': portfolios,
            'recommended': recommended,
            'risk_analysis': risk_analysis,
            'simulation': simulation
        }

def main():
    """월 350만원 목표 전략 분석 실행"""
    
    strategy = InvestmentStrategy350()
    
    # 투자금액 시나리오
    investment_scenarios = [
        100000000,  # 1억원
        150000000,  # 1.5억원  
        200000000,  # 2억원
        300000000   # 3억원
    ]
    
    print("🎯 월 350만원 수익 목표 ETF 자동매매 전략")
    print("=" * 60)
    
    for investment in investment_scenarios:
        print(f"\n💰 투자금 {investment//100000000}억원 시나리오")
        print("-" * 30)
        
        # 균형형 포트폴리오 기준 분석
        portfolio = strategy.create_portfolio_allocation(investment, 'moderate')
        
        monthly_profit = portfolio['expected_monthly_profit']
        achievement_rate = (monthly_profit / strategy.monthly_target) * 100
        
        print(f"  예상 월 수익: {monthly_profit:,.0f}원")
        print(f"  목표 달성률: {achievement_rate:.1f}%")
        
        if achievement_rate >= 100:
            print(f"  ✅ 목표 달성 가능!")
        elif achievement_rate >= 80:
            print(f"  📊 목표에 근접 (추가 최적화 필요)")
        else:
            print(f"  ❌ 목표 달성 어려움 (더 공격적 전략 필요)")
    
    print(f"\n" + "=" * 60)
    print(f"🏆 최종 추천: 2억원 투자 + MODERATE 포트폴리오")
    print(f"📊 상세 분석을 위해 generate_strategy_report() 실행")

if __name__ == "__main__":
    main()