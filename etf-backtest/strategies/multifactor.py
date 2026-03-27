#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-
"""
멀티팩터 스코어링 시스템
- 기술적 팩터 (MA, RSI, BB) : 40%
- 수급 팩터 (외국인/기관 순매수) : 40%
- 모멘텀 팩터 (가격 모멘텀) : 20%

최종 스코어 0~100, 70점 이상 매수 신호
"""

import numpy as np
import pandas as pd


def score_technical(df: pd.DataFrame, params: dict = None) -> float:
    """
    기술적 팩터 스코어 (0~100)
    - MA 크로스: 단기 > 장기 = 가산점
    - RSI: 과매도(30 이하) 가산, 과매수(70 이상) 감점
    - BB: 하단 근처 가산, 상단 근처 감점
    """
    if params is None:
        params = {'ma_short': 3, 'ma_long': 15, 'rsi_period': 14, 'bb_window': 20, 'bb_std': 2.0}

    if len(df) < params.get('ma_long', 15):
        return 50.0  # 데이터 부족 시 중립

    close = df['close'].values
    score = 50.0  # 기본 중립

    # 1. MA 크로스 (0~40점)
    ma_short = pd.Series(close).rolling(params.get('ma_short', 3)).mean().iloc[-1]
    ma_long = pd.Series(close).rolling(params.get('ma_long', 15)).mean().iloc[-1]
    if ma_long > 0:
        ma_ratio = (ma_short - ma_long) / ma_long * 100
        ma_score = np.clip(ma_ratio * 10 + 20, 0, 40)  # -2%~+2% → 0~40
        score = score - 20 + ma_score  # 기본 20을 교체

    # 2. RSI (0~30점)
    delta = pd.Series(close).diff()
    gain = delta.where(delta > 0, 0).rolling(params.get('rsi_period', 14)).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(params.get('rsi_period', 14)).mean()
    rs = gain.iloc[-1] / max(loss.iloc[-1], 0.001)
    rsi = 100 - (100 / (1 + rs))

    if rsi <= 30:
        rsi_score = 30  # 과매도 → 최고점
    elif rsi >= 70:
        rsi_score = 0   # 과매수 → 최저점
    else:
        rsi_score = (70 - rsi) / 40 * 30  # 30~70 사이 선형

    score += rsi_score - 15  # 기본 15 교체

    # 3. BB 위치 (0~30점)
    bb_ma = pd.Series(close).rolling(params.get('bb_window', 20)).mean().iloc[-1]
    bb_std = pd.Series(close).rolling(params.get('bb_window', 20)).std().iloc[-1]
    bb_upper = bb_ma + params.get('bb_std', 2.0) * bb_std
    bb_lower = bb_ma - params.get('bb_std', 2.0) * bb_std

    if bb_upper > bb_lower:
        bb_pos = (close[-1] - bb_lower) / (bb_upper - bb_lower)  # 0=하단, 1=상단
        bb_score = np.clip((1 - bb_pos) * 30, 0, 30)  # 하단일수록 높은 점수
    else:
        bb_score = 15

    score += bb_score - 15  # 기본 15 교체

    return np.clip(score, 0, 100)


def score_supply_demand(investor_df: pd.DataFrame, days: int = 5) -> float:
    """
    수급 팩터 스코어 (0~100)
    - 외국인 순매수 추세: 50%
    - 기관 순매수 추세: 30%
    - 개인 순매도(역지표): 20%
    """
    if investor_df is None or len(investor_df) < days:
        return 50.0  # 데이터 부족 시 중립

    recent = investor_df.tail(days)

    # 외국인 순매수 비율 (양수 비율)
    frgn_positive = (recent['frgn_net_vol'] > 0).sum() / days
    frgn_score = frgn_positive * 100  # 0~100

    # 기관 순매수 비율
    orgn_positive = (recent['orgn_net_vol'] > 0).sum() / days
    orgn_score = orgn_positive * 100

    # 개인 순매도 = 기관+외국인 매수 신호 (역지표)
    prsn_negative = (recent['prsn_net_vol'] < 0).sum() / days
    prsn_score = prsn_negative * 100  # 개인이 팔수록 좋은 신호

    # 가중 합산
    score = frgn_score * 0.5 + orgn_score * 0.3 + prsn_score * 0.2

    return np.clip(score, 0, 100)


def score_momentum(df: pd.DataFrame, periods: list = None) -> float:
    """
    모멘텀 팩터 스코어 (0~100)
    - 5일 수익률, 20일 수익률 기반
    """
    if periods is None:
        periods = [5, 20]

    if len(df) < max(periods):
        return 50.0

    close = df['close'].values
    scores = []

    for p in periods:
        ret = (close[-1] - close[-p]) / close[-p] * 100
        # -5%~+5% → 0~100
        s = np.clip(ret * 10 + 50, 0, 100)
        scores.append(s)

    return np.mean(scores)


def multifactor_score(
    price_df: pd.DataFrame,
    investor_df: pd.DataFrame = None,
    weights: dict = None,
    params: dict = None,
) -> dict:
    """
    멀티팩터 통합 스코어 계산

    Args:
        price_df: OHLCV DataFrame (columns: date, open, high, low, close, volume)
        investor_df: 투자자별 매매동향 (columns: trade_dt, frgn_net_vol, orgn_net_vol, prsn_net_vol)
        weights: 팩터 가중치 {'technical': 0.4, 'supply': 0.4, 'momentum': 0.2}
        params: 기술적 분석 파라미터

    Returns:
        dict: {
            'total_score': float,      # 통합 스코어 (0~100)
            'technical_score': float,   # 기술적 팩터
            'supply_score': float,      # 수급 팩터
            'momentum_score': float,    # 모멘텀 팩터
            'signal': str,             # 'BUY', 'HOLD', 'SELL'
            'confidence': str,         # 'HIGH', 'MEDIUM', 'LOW'
        }
    """
    if weights is None:
        weights = {'technical': 0.4, 'supply': 0.4, 'momentum': 0.2}

    tech_score = score_technical(price_df, params)
    supply_score = score_supply_demand(investor_df)
    momentum_score = score_momentum(price_df)

    total = (
        tech_score * weights['technical'] +
        supply_score * weights['supply'] +
        momentum_score * weights['momentum']
    )

    # 신호 판정
    if total >= 70:
        signal = 'BUY'
    elif total <= 30:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    # 신뢰도
    if total >= 80 or total <= 20:
        confidence = 'HIGH'
    elif total >= 65 or total <= 35:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'

    return {
        'total_score': round(total, 1),
        'technical_score': round(tech_score, 1),
        'supply_score': round(supply_score, 1),
        'momentum_score': round(momentum_score, 1),
        'signal': signal,
        'confidence': confidence,
    }
