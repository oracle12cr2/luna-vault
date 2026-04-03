"""
백테스트 엔진
"""

import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime
import os
from typing import Dict, List, Optional, Any
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class BacktestEngine:
    """백테스트 실행 엔진"""
    
    def __init__(self, initial_cash=100000000, commission=0.0015):
        """
        엔진 초기화
        
        Args:
            initial_cash: 초기 자금
            commission: 수수료 (기본값: 0.15%)
        """
        self.cerebro = bt.Cerebro()
        self.initial_cash = initial_cash
        self.commission = commission
        self.results = None
        
        # 브로커 설정
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        
        # 분석기 추가
        self.add_analyzers()
        
    def add_analyzers(self):
        """분석기 추가"""
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        
    def add_data(self, data: pd.DataFrame, name: str):
        """
        데이터 추가
        
        Args:
            data: OHLCV 데이터
            name: 데이터 이름
        """
        # backtrader 데이터 형식으로 변환
        bt_data = bt.feeds.PandasData(
            dataname=data,
            datetime=None,  # 인덱스를 datetime으로 사용
            open='Open',
            high='High', 
            low='Low',
            close='Close',
            volume='Volume'
        )
        bt_data._name = name
        self.cerebro.adddata(bt_data)
        
    def add_strategy(self, strategy_class, **params):
        """
        전략 추가
        
        Args:
            strategy_class: 전략 클래스
            **params: 전략 파라미터
        """
        self.cerebro.addstrategy(strategy_class, **params)
        
    def run(self):
        """백테스트 실행"""
        print('백테스트 시작...')
        print(f'초기 자금: {self.initial_cash:,}원')
        
        start_time = datetime.now()
        self.results = self.cerebro.run()
        end_time = datetime.now()
        
        final_value = self.cerebro.broker.getvalue()
        
        print(f'백테스트 완료! (소요시간: {end_time - start_time})')
        print(f'최종 포트폴리오 가치: {final_value:,}원')
        print(f'총 수익률: {((final_value / self.initial_cash) - 1) * 100:.2f}%')
        
        return self.results
        
    def get_analysis(self) -> Dict[str, Any]:
        """분석 결과 추출"""
        if not self.results:
            raise ValueError("백테스트를 먼저 실행해주세요")
            
        strategy = self.results[0]
        analysis = {}
        
        # 기본 수익률 정보
        final_value = self.cerebro.broker.getvalue()
        total_return = (final_value / self.initial_cash - 1) * 100
        
        analysis['기본정보'] = {
            '초기자금': f'{self.initial_cash:,}원',
            '최종가치': f'{final_value:,}원',
            '총수익률': f'{total_return:.2f}%',
            '수수료': f'{self.commission * 100:.2f}%'
        }
        
        # 샤프 비율
        if hasattr(strategy.analyzers.sharpe, 'get_analysis'):
            sharpe = strategy.analyzers.sharpe.get_analysis()
            analysis['샤프비율'] = sharpe.get('sharperatio', 'N/A')
            
        # 수익률 분석
        if hasattr(strategy.analyzers.returns, 'get_analysis'):
            returns = strategy.analyzers.returns.get_analysis()
            analysis['수익률분석'] = {
                '평균수익률': f'{returns.get("ravg", 0) * 100:.3f}%',
                '연환산수익률': f'{returns.get("rnorm", 0) * 100:.2f}%' if returns.get("rnorm") else 'N/A'
            }
            
        # 드로다운 분석
        if hasattr(strategy.analyzers.drawdown, 'get_analysis'):
            drawdown = strategy.analyzers.drawdown.get_analysis()
            analysis['드로다운분석'] = {
                '최대드로다운': f'{drawdown.get("max", {}).get("drawdown", 0):.2f}%',
                '최대드로다운기간': f'{drawdown.get("max", {}).get("len", 0)}일'
            }
            
        # 거래 분석
        if hasattr(strategy.analyzers.trades, 'get_analysis'):
            trades = strategy.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            
            analysis['거래분석'] = {
                '총거래수': total_trades,
                '승률': f'{(won_trades / total_trades * 100) if total_trades > 0 else 0:.1f}%',
                '수익거래': won_trades,
                '손실거래': lost_trades
            }
            
        # SQN (System Quality Number)
        if hasattr(strategy.analyzers.sqn, 'get_analysis'):
            sqn = strategy.analyzers.sqn.get_analysis()
            analysis['SQN'] = sqn.get('sqn', 'N/A')
            
        return analysis
        
    def create_charts(self, save_path: str = None) -> None:
        """결과 차트 생성"""
        if not self.results:
            raise ValueError("백테스트를 먼저 실행해주세요")
            
        # backtrader 기본 차트
        fig = self.cerebro.plot(style='candlestick', barup='red', bardown='blue')[0][0]
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"차트 저장됨: {save_path}")
        else:
            plt.show()
            
    def create_performance_chart(self, save_path: str = None) -> None:
        """성과 차트 생성"""
        if not self.results:
            raise ValueError("백테스트를 먼저 실행해주세요")
            
        strategy = self.results[0]
        
        # 포트폴리오 가치 추적
        portfolio_values = []
        dates = []
        
        # cerebro에서 직접 가져오는 것이 어려우므로 간단한 차트만 생성
        plt.figure(figsize=(12, 8))
        
        # 기본 정보 표시
        analysis = self.get_analysis()
        
        plt.subplot(2, 1, 1)
        plt.title('포트폴리오 성과 요약', fontsize=14, fontweight='bold')
        plt.text(0.1, 0.8, f"총 수익률: {analysis['기본정보']['총수익률']}", fontsize=12)
        plt.text(0.1, 0.6, f"최대 드로다운: {analysis.get('드로다운분석', {}).get('최대드로다운', 'N/A')}", fontsize=12)
        plt.text(0.1, 0.4, f"샤프 비율: {analysis.get('샤프비율', 'N/A')}", fontsize=12)
        plt.text(0.1, 0.2, f"승률: {analysis.get('거래분석', {}).get('승률', 'N/A')}", fontsize=12)
        plt.axis('off')
        
        plt.subplot(2, 1, 2)
        plt.title('전략 성과 분석', fontsize=12)
        plt.text(0.5, 0.5, '상세 성과 차트는 cerebro.plot()을 사용하세요', 
                ha='center', va='center', fontsize=10)
        plt.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"성과 차트 저장됨: {save_path}")
        else:
            plt.show()
            
    def save_results(self, filepath: str) -> None:
        """결과를 CSV 파일로 저장"""
        if not self.results:
            raise ValueError("백테스트를 먼저 실행해주세요")
            
        analysis = self.get_analysis()
        
        # 분석 결과를 DataFrame으로 변환
        results_data = []
        for category, data in analysis.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    results_data.append({
                        '구분': category,
                        '항목': key,
                        '값': value
                    })
            else:
                results_data.append({
                    '구분': category,
                    '항목': category,
                    '값': data
                })
                
        df = pd.DataFrame(results_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"결과 저장됨: {filepath}")
        
    def compare_with_benchmark(self, benchmark_data: pd.DataFrame, benchmark_name: str = "벤치마크"):
        """벤치마크와 비교 분석"""
        if not self.results:
            raise ValueError("백테스트를 먼저 실행해주세요")
            
        # 벤치마크 수익률 계산 (간단한 매수후보유)
        start_price = benchmark_data['Close'].iloc[0]
        end_price = benchmark_data['Close'].iloc[-1]
        benchmark_return = (end_price / start_price - 1) * 100
        
        # 전략 수익률
        strategy_return = ((self.cerebro.broker.getvalue() / self.initial_cash) - 1) * 100
        
        print(f"\n=== 벤치마크 비교 ===")
        print(f"{benchmark_name} 수익률: {benchmark_return:.2f}%")
        print(f"전략 수익률: {strategy_return:.2f}%")
        print(f"초과 수익률: {strategy_return - benchmark_return:.2f}%")
        
        return {
            'benchmark_return': benchmark_return,
            'strategy_return': strategy_return,
            'excess_return': strategy_return - benchmark_return
        }