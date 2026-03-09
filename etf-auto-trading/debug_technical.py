#!/usr/bin/env python3
"""
기술적 지표 계산 디버그
"""

import sys
import cx_Oracle
import pandas as pd
import numpy as np
import talib

def test_calculation():
    # DB 연결
    dsn = cx_Oracle.makedsn('oracle19c01', 1521, service_name='PROD')
    connection = cx_Oracle.connect('stock', 'stock123', dsn)
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT trade_date, open_price, high_price, low_price, close_price, volume
        FROM etf_daily_price
        WHERE etf_code = '069500'
        ORDER BY trade_date ASC
    """)
    
    rows = cursor.fetchall()
    print(f"조회된 데이터: {len(rows)}건")
    
    # DataFrame 변환
    df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    
    print(f"DataFrame 크기: {len(df)}")
    print(f"날짜 범위: {df.index[0]} ~ {df.index[-1]}")
    print(f"가격 범위: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
    
    # 데이터 타입 변환
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"NULL 값 확인:")
    print(f"- close: {df['close'].isnull().sum()}")
    print(f"- volume: {df['volume'].isnull().sum()}")
    
    # 기술적 지표 계산 테스트
    print("\n=== 기술적 지표 계산 테스트 ===")
    
    indicators = pd.DataFrame(index=df.index)
    indicators['close_price'] = df['close']
    
    # SMA 계산
    indicators['sma_5'] = talib.SMA(df['close'], timeperiod=5)
    indicators['sma_20'] = talib.SMA(df['close'], timeperiod=20)
    
    print(f"SMA5 계산 결과:")
    print(f"- 전체: {len(indicators['sma_5'])}")
    print(f"- 유효값: {indicators['sma_5'].notna().sum()}")
    print(f"- NULL: {indicators['sma_5'].isnull().sum()}")
    
    print(f"SMA20 계산 결과:")
    print(f"- 전체: {len(indicators['sma_20'])}")  
    print(f"- 유효값: {indicators['sma_20'].notna().sum()}")
    print(f"- NULL: {indicators['sma_20'].isnull().sum()}")
    
    # dropna 전후 비교
    print(f"\ndropna 전 indicators 크기: {len(indicators)}")
    indicators_clean = indicators.dropna()
    print(f"dropna 후 indicators 크기: {len(indicators_clean)}")
    
    # 최근 10건 확인
    print(f"\n최근 10건 지표 데이터:")
    recent_data = indicators.tail(10)[['close_price', 'sma_5', 'sma_20']]
    for idx, row in recent_data.iterrows():
        sma5_str = f"{row['sma_5']:.2f}" if pd.notna(row['sma_5']) else 'NaN'
        sma20_str = f"{row['sma_20']:.2f}" if pd.notna(row['sma_20']) else 'NaN'
        print(f"{idx.strftime('%m-%d')}: close={row['close_price']:.2f}, sma5={sma5_str}, sma20={sma20_str}")
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    test_calculation()