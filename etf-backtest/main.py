"""
한국 ETF 백테스트 메인 실행 파일
"""

import os
import yaml
import pandas as pd
from datetime import datetime
import argparse
import logging

# 로컬 모듈 import
from data.collector import KoreanETFDataCollector
from backtest.engine import BacktestEngine
from strategies import (
    MovingAverageCrossStrategy,
    RSIStrategy,
    DualMomentumStrategy, 
    AssetAllocationStrategy
)


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backtest.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    

def load_config(config_path='config.yaml'):
    """설정 파일 로드"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def collect_data(config):
    """ETF 데이터 수집"""
    collector = KoreanETFDataCollector()
    
    etf_config = config['data']['etfs']
    start_date = config['data']['start_date']
    end_date = config['data']['end_date']
    
    print("ETF 데이터 수집 중...")
    data_dict = {}
    
    for etf_name, ticker in etf_config.items():
        print(f"  - {etf_name} ({ticker}) 수집 중...")
        data = collector.get_etf_data(ticker, start_date, end_date)
        
        if data is not None and collector.validate_data(data, ticker):
            data_dict[etf_name] = data
            print(f"    성공: {len(data)}개 데이터")
        else:
            print(f"    실패: {etf_name}")
            
    return data_dict


def run_moving_average_strategy(data_dict, config):
    """이동평균 크로스 전략 실행"""
    print("\n=== 이동평균 크로스 전략 ===")
    
    strategy_config = config['strategies']['moving_average_cross']
    if not strategy_config['enabled']:
        print("전략이 비활성화되어 있습니다.")
        return None
    
    # 첫 번째 ETF 사용 (KODEX 200)
    primary_etf = list(data_dict.keys())[0]
    data = data_dict[primary_etf]
    
    # 백테스트 엔진 설정
    engine = BacktestEngine(
        initial_cash=config['backtest']['initial_cash'],
        commission=config['backtest']['commission']
    )
    
    # 데이터 추가
    engine.add_data(data, primary_etf)
    
    # 전략 추가
    engine.add_strategy(
        MovingAverageCrossStrategy,
        short_period=strategy_config['params']['short_period'],
        long_period=strategy_config['params']['long_period'],
        printlog=True
    )
    
    # 백테스트 실행
    results = engine.run()
    
    # 결과 분석
    analysis = engine.get_analysis()
    print_analysis(analysis)
    
    # 결과 저장
    if config['output']['save_charts']:
        results_dir = config['output']['results_dir']
        os.makedirs(results_dir, exist_ok=True)
        
        engine.save_results(f"{results_dir}/ma_cross_results.csv")
        engine.create_performance_chart(f"{results_dir}/ma_cross_performance.{config['output']['chart_format']}")
    
    return engine


def run_rsi_strategy(data_dict, config):
    """RSI 전략 실행"""
    print("\n=== RSI 과매수/과매도 전략 ===")
    
    strategy_config = config['strategies']['rsi_strategy']
    if not strategy_config['enabled']:
        print("전략이 비활성화되어 있습니다.")
        return None
    
    # 첫 번째 ETF 사용
    primary_etf = list(data_dict.keys())[0]
    data = data_dict[primary_etf]
    
    # 백테스트 엔진 설정
    engine = BacktestEngine(
        initial_cash=config['backtest']['initial_cash'],
        commission=config['backtest']['commission']
    )
    
    # 데이터 추가
    engine.add_data(data, primary_etf)
    
    # 전략 추가
    engine.add_strategy(
        RSIStrategy,
        period=strategy_config['params']['period'],
        oversold=strategy_config['params']['oversold'],
        overbought=strategy_config['params']['overbought'],
        printlog=True
    )
    
    # 백테스트 실행
    results = engine.run()
    
    # 결과 분석
    analysis = engine.get_analysis()
    print_analysis(analysis)
    
    # 결과 저장
    if config['output']['save_charts']:
        results_dir = config['output']['results_dir']
        os.makedirs(results_dir, exist_ok=True)
        
        engine.save_results(f"{results_dir}/rsi_results.csv")
        engine.create_performance_chart(f"{results_dir}/rsi_performance.{config['output']['chart_format']}")
    
    return engine


def run_dual_momentum_strategy(data_dict, config):
    """듀얼 모멘텀 전략 실행"""
    print("\n=== 듀얼 모멘텀 전략 ===")
    
    strategy_config = config['strategies']['dual_momentum']
    if not strategy_config['enabled']:
        print("전략이 비활성화되어 있습니다.")
        return None
    
    # 여러 ETF 사용
    if len(data_dict) < 2:
        print("듀얼 모멘텀 전략은 최소 2개의 자산이 필요합니다.")
        return None
    
    # 백테스트 엔진 설정
    engine = BacktestEngine(
        initial_cash=config['backtest']['initial_cash'],
        commission=config['backtest']['commission']
    )
    
    # 여러 데이터 추가
    for etf_name, data in data_dict.items():
        engine.add_data(data, etf_name)
    
    # 전략 추가
    engine.add_strategy(
        DualMomentumStrategy,
        lookback_period=strategy_config['params']['lookback_period'],
        risk_free_rate=strategy_config['params']['risk_free_rate'],
        printlog=True
    )
    
    # 백테스트 실행
    results = engine.run()
    
    # 결과 분석
    analysis = engine.get_analysis()
    print_analysis(analysis)
    
    # 결과 저장
    if config['output']['save_charts']:
        results_dir = config['output']['results_dir']
        os.makedirs(results_dir, exist_ok=True)
        
        engine.save_results(f"{results_dir}/dual_momentum_results.csv")
        engine.create_performance_chart(f"{results_dir}/dual_momentum_performance.{config['output']['chart_format']}")
    
    return engine


def run_asset_allocation_strategy(data_dict, config):
    """자산배분 전략 실행"""
    print("\n=== 정적 자산배분 전략 ===")
    
    strategy_config = config['strategies']['asset_allocation']
    if not strategy_config['enabled']:
        print("전략이 비활성화되어 있습니다.")
        return None
    
    # 주식 ETF와 채권 ETF 선택
    etf_names = list(data_dict.keys())
    if len(etf_names) < 2:
        print("자산배분 전략은 최소 2개의 자산(주식, 채권)이 필요합니다.")
        return None
    
    # 백테스트 엔진 설정
    engine = BacktestEngine(
        initial_cash=config['backtest']['initial_cash'],
        commission=config['backtest']['commission']
    )
    
    # 주식과 채권 데이터 추가 (첫 번째는 주식, 채권 ETF가 있다면 그것을 채권으로)
    stock_etf = etf_names[0]  # 첫 번째 ETF를 주식으로
    bond_etf = None
    
    # 채권 ETF 찾기
    for name in etf_names:
        if 'bond' in name.lower() or '채권' in name or 'bond' in data_dict[name].columns:
            bond_etf = name
            break
    
    if not bond_etf:
        bond_etf = etf_names[1] if len(etf_names) > 1 else etf_names[0]  # 두 번째 ETF를 채권으로
    
    engine.add_data(data_dict[stock_etf], stock_etf)
    engine.add_data(data_dict[bond_etf], bond_etf)
    
    # 전략 추가
    engine.add_strategy(
        AssetAllocationStrategy,
        stock_ratio=strategy_config['params']['stock_ratio'],
        bond_ratio=strategy_config['params']['bond_ratio'],
        rebalance_months=strategy_config['params']['rebalance_months'],
        printlog=True
    )
    
    # 백테스트 실행
    results = engine.run()
    
    # 결과 분석
    analysis = engine.get_analysis()
    print_analysis(analysis)
    
    # 결과 저장
    if config['output']['save_charts']:
        results_dir = config['output']['results_dir']
        os.makedirs(results_dir, exist_ok=True)
        
        engine.save_results(f"{results_dir}/asset_allocation_results.csv")
        engine.create_performance_chart(f"{results_dir}/asset_allocation_performance.{config['output']['chart_format']}")
    
    return engine


def print_analysis(analysis):
    """분석 결과 출력"""
    print("\n" + "="*50)
    print("백테스트 결과 분석")
    print("="*50)
    
    for category, data in analysis.items():
        print(f"\n[{category}]")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {category}: {data}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='한국 ETF 백테스트')
    parser.add_argument('--config', default='config.yaml', help='설정 파일 경로')
    parser.add_argument('--strategy', choices=['ma', 'rsi', 'momentum', 'allocation', 'all'], 
                       default='all', help='실행할 전략')
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    
    print("한국 ETF 백테스트 프레임워크")
    print("="*50)
    
    try:
        # 설정 파일 로드
        config = load_config(args.config)
        print(f"설정 파일 로드됨: {args.config}")
        
        # 데이터 수집
        data_dict = collect_data(config)
        
        if not data_dict:
            print("수집된 데이터가 없습니다. 프로그램을 종료합니다.")
            return
        
        print(f"\n수집된 ETF: {list(data_dict.keys())}")
        
        # 전략 실행
        if args.strategy == 'all':
            run_moving_average_strategy(data_dict, config)
            run_rsi_strategy(data_dict, config)
            run_dual_momentum_strategy(data_dict, config)
            run_asset_allocation_strategy(data_dict, config)
        elif args.strategy == 'ma':
            run_moving_average_strategy(data_dict, config)
        elif args.strategy == 'rsi':
            run_rsi_strategy(data_dict, config)
        elif args.strategy == 'momentum':
            run_dual_momentum_strategy(data_dict, config)
        elif args.strategy == 'allocation':
            run_asset_allocation_strategy(data_dict, config)
        
        print("\n백테스트 완료!")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    main()