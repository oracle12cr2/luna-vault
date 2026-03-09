#!/usr/bin/env python3
"""
간단한 기술적 지표 계산 (우회 방법)
"""

import cx_Oracle
import pandas as pd
import talib
import sys

def calculate_for_all_etfs():
    print("=== 간단한 기술적 지표 계산 시작 ===")
    
    # DB 연결
    dsn = cx_Oracle.makedsn('oracle19c01', 1521, service_name='PROD')
    connection = cx_Oracle.connect('stock', 'stock123', dsn)
    
    try:
        # ETF 목록 조회
        cursor = connection.cursor()
        cursor.execute("SELECT etf_code, etf_name FROM etf_master ORDER BY etf_code")
        etf_list = cursor.fetchall()
        cursor.close()
        
        # 기존 데이터 삭제
        cursor = connection.cursor()
        cursor.execute("DELETE FROM etf_technical_indicators")
        connection.commit()
        cursor.close()
        print("기존 기술적 지표 데이터 삭제 완료")
        
        success_count = 0
        
        for etf_code, etf_name in etf_list:
            print(f"[{etf_code}] {etf_name} 처리 중...")
            
            # 가격 데이터 조회
            cursor = connection.cursor()
            cursor.execute("""
                SELECT trade_date, close_price, volume
                FROM etf_daily_price
                WHERE etf_code = :etf_code
                ORDER BY trade_date ASC
            """, {'etf_code': etf_code})
            
            rows = cursor.fetchall()
            cursor.close()
            
            if len(rows) < 20:
                print(f"  - 데이터 부족: {len(rows)}건")
                continue
            
            # DataFrame 변환
            df = pd.DataFrame(rows, columns=['date', 'close', 'volume'])
            df['close'] = pd.to_numeric(df['close'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # 기술적 지표 계산 (기본만)
            sma_5 = talib.SMA(df['close'], timeperiod=5)
            sma_20 = talib.SMA(df['close'], timeperiod=20)
            rsi_14 = talib.RSI(df['close'], timeperiod=14)
            
            # 유효한 데이터만 저장 (최근 50건)
            valid_count = 0
            cursor = connection.cursor()
            
            insert_sql = """
            INSERT INTO etf_technical_indicators 
            (etf_code, trade_date, close_price, sma_5, sma_20, rsi_14, volume, created_date)
            VALUES (:etf_code, :trade_date, :close_price, :sma_5, :sma_20, :rsi_14, :volume, SYSDATE)
            """
            
            # 최근 50건만 저장 (전체를 저장하면 시간이 오래 걸림)
            start_idx = max(0, len(df) - 50)
            
            for i in range(start_idx, len(df)):
                if pd.notna(sma_20.iloc[i]) and pd.notna(rsi_14.iloc[i]):  # 필수 지표가 있는 경우만
                    cursor.execute(insert_sql, {
                        'etf_code': etf_code,
                        'trade_date': df.iloc[i]['date'],
                        'close_price': float(df.iloc[i]['close']),
                        'sma_5': float(sma_5.iloc[i]) if pd.notna(sma_5.iloc[i]) else None,
                        'sma_20': float(sma_20.iloc[i]) if pd.notna(sma_20.iloc[i]) else None,
                        'rsi_14': float(rsi_14.iloc[i]) if pd.notna(rsi_14.iloc[i]) else None,
                        'volume': float(df.iloc[i]['volume'])
                    })
                    valid_count += 1
            
            connection.commit()
            cursor.close()
            
            if valid_count > 0:
                print(f"  - 성공: {valid_count}건 저장")
                success_count += 1
            else:
                print(f"  - 실패: 유효한 지표 없음")
        
        print(f"=== 완료: {success_count}/{len(etf_list)} ETF 처리됨 ===")
        return success_count > 0
        
    except Exception as e:
        print(f"오류: {e}")
        return False
        
    finally:
        connection.close()

if __name__ == "__main__":
    success = calculate_for_all_etfs()
    sys.exit(0 if success else 1)