"""
한국 ETF 데이터 수집 모듈
yfinance를 사용하여 한국 주식/ETF 데이터를 수집합니다.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class KoreanETFDataCollector:
    """한국 ETF 데이터 수집 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 주요 한국 ETF 티커 매핑
        self.etf_mapping = {
            'KODEX200': '069500.KS',
            'TIGER_SP500': '360750.KS', 
            'KODEX_LEVERAGE': '122630.KS',
            'TIGER_NASDAQ100': '133690.KS',
            'KODEX_BOND': '148070.KS',
            'KODEX_KOSDAQ': '229200.KS',
            'TIGER_CHINA': '157490.KS',
            'KODEX_GOLD': '132030.KS'
        }
    
    def get_etf_data(self, 
                     ticker: str, 
                     start_date: str, 
                     end_date: str,
                     interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        단일 ETF 데이터를 가져옵니다.
        
        Args:
            ticker: ETF 티커 심볼 (예: '069500.KS')
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD) 
            interval: 데이터 간격 (1d, 1wk, 1mo)
            
        Returns:
            pandas.DataFrame: OHLCV 데이터
        """
        try:
            # yfinance를 사용하여 데이터 다운로드
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                self.logger.warning(f"데이터가 없습니다: {ticker}")
                return None
            
            # 실제 컬럼명 확인 및 정리
            self.logger.info(f"원본 컬럼: {list(data.columns)}")
            
            # 필요한 컬럼만 선택 (실제 yfinance 컬럼명 사용)
            required_cols = []
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    required_cols.append(col)
                    
            if len(required_cols) < 5:
                self.logger.error(f"필요한 컬럼이 부족합니다: {data.columns}")
                return None
                
            data = data[required_cols]
            
            # 인덱스를 datetime으로 설정
            data.index = pd.to_datetime(data.index)
            data.index.name = 'Date'
            
            self.logger.info(f"{ticker} 데이터 수집 완료: {len(data)}개 행")
            return data
            
        except Exception as e:
            self.logger.error(f"{ticker} 데이터 수집 실패: {str(e)}")
            return None
    
    def get_multiple_etfs_data(self, 
                              tickers: List[str], 
                              start_date: str, 
                              end_date: str) -> Dict[str, pd.DataFrame]:
        """
        여러 ETF 데이터를 한번에 가져옵니다.
        
        Args:
            tickers: ETF 티커 리스트
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            Dict[str, pd.DataFrame]: 티커별 데이터 딕셔너리
        """
        data_dict = {}
        
        for ticker in tickers:
            data = self.get_etf_data(ticker, start_date, end_date)
            if data is not None:
                data_dict[ticker] = data
            else:
                self.logger.warning(f"{ticker} 데이터 수집 실패")
                
        return data_dict
    
    def get_benchmark_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        벤치마크 데이터 (KOSPI)를 가져옵니다.
        
        Args:
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            pandas.DataFrame: KOSPI 데이터
        """
        return self.get_etf_data('^KS11', start_date, end_date)
    
    def validate_data(self, data: pd.DataFrame, ticker: str) -> bool:
        """
        데이터 품질을 검증합니다.
        
        Args:
            data: 검증할 데이터
            ticker: 티커 심볼
            
        Returns:
            bool: 검증 통과 여부
        """
        if data is None or data.empty:
            self.logger.error(f"{ticker}: 데이터가 비어있습니다")
            return False
            
        # 필수 컬럼 확인
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            self.logger.error(f"{ticker}: 필수 컬럼이 없습니다: {missing_columns}")
            return False
            
        # 결측값 확인
        null_counts = data.isnull().sum()
        if null_counts.any():
            self.logger.warning(f"{ticker}: 결측값 발견: {null_counts[null_counts > 0].to_dict()}")
            
        # 가격 데이터 유효성 확인
        if (data[['Open', 'High', 'Low', 'Close']] <= 0).any().any():
            self.logger.error(f"{ticker}: 가격 데이터에 0 이하 값이 있습니다")
            return False
            
        self.logger.info(f"{ticker}: 데이터 검증 통과")
        return True
    
    def save_data(self, data: pd.DataFrame, filepath: str) -> None:
        """
        데이터를 CSV 파일로 저장합니다.
        
        Args:
            data: 저장할 데이터
            filepath: 저장할 파일 경로
        """
        try:
            data.to_csv(filepath)
            self.logger.info(f"데이터 저장 완료: {filepath}")
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {str(e)}")