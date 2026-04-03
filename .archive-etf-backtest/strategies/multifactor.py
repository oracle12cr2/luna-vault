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


def score_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
    """
    MACD 팩터 스코어 (0~100)
    - MACD선이 시그널선 위 = 강세, 아래 = 약세
    - 골든크로스(상향돌파) = 최고점, 데드크로스(하향돌파) = 최저점
    - MACD 히스토그램 증가 = 가산
    """
    if len(df) < slow + signal:
        return 50.0  # 데이터 부족

    close = df['close']
    
    # EMA 계산
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    cur_macd = float(macd_line.iloc[-1])
    cur_signal = float(signal_line.iloc[-1])
    cur_hist = float(histogram.iloc[-1])
    prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0
    
    prev_macd = float(macd_line.iloc[-2]) if len(macd_line) > 1 else cur_macd
    prev_signal_val = float(signal_line.iloc[-2]) if len(signal_line) > 1 else cur_signal
    
    score = 50.0
    
    # 골든크로스: MACD가 시그널 상향 돌파 → +30
    if prev_macd <= prev_signal_val and cur_macd > cur_signal:
        score += 30
    # 데드크로스: MACD가 시그널 하향 돌파 → -30
    elif prev_macd >= prev_signal_val and cur_macd < cur_signal:
        score -= 30
    # MACD > 시그널 (강세 유지) → +15
    elif cur_macd > cur_signal:
        score += 15
    # MACD < 시그널 (약세 유지) → -15
    else:
        score -= 15
    
    # 히스토그램 증가 → +10 (모멘텀 강화)
    if cur_hist > prev_hist and cur_hist > 0:
        score += 10
    # 히스토그램 감소 → -10 (모멘텀 약화)
    elif cur_hist < prev_hist and cur_hist < 0:
        score -= 10
    
    return np.clip(score, 0, 100)


def score_fundamental(financial_df: pd.DataFrame = None) -> float:
    """
    펀더멘탈 팩터 스코어 (0~100)
    - PER: 낮을수록 좋음 (저평가)
    - ROE: 높을수록 좋음 (수익성)
    - 매출성장률: 높을수록 좋음 (성장성)
    
    financial_df: columns = [per, roe, revenue_growth]
    """
    if financial_df is None or financial_df.empty:
        return 50.0  # 데이터 없으면 중립
    
    score = 50.0
    
    # PER (0~35점) — 낮을수록 좋음
    per = financial_df.get('per', None)
    if per is not None and per > 0:
        if per <= 10:
            score += 20      # 저평가
        elif per <= 15:
            score += 10      # 적정
        elif per <= 25:
            score += 0       # 보통
        elif per <= 40:
            score -= 10      # 고평가
        else:
            score -= 15      # 과대평가
    
    # ROE (0~35점) — 높을수록 좋음
    roe = financial_df.get('roe', None)
    if roe is not None:
        if roe >= 20:
            score += 20      # 우수
        elif roe >= 10:
            score += 10      # 양호
        elif roe >= 5:
            score += 0       # 보통
        else:
            score -= 10      # 부진
    
    # 매출성장률 (0~30점) — 높을수록 좋음
    growth = financial_df.get('revenue_growth', None)
    if growth is not None:
        if growth >= 20:
            score += 15      # 고성장
        elif growth >= 10:
            score += 8       # 성장
        elif growth >= 0:
            score += 0       # 정체
        else:
            score -= 10      # 역성장
    
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
    financial_df: pd.DataFrame = None,
    weights: dict = None,
    params: dict = None,
) -> dict:
    """
    멀티팩터 통합 스코어 계산 (6팩터)

    Args:
        price_df: OHLCV DataFrame (columns: date, open, high, low, close, volume)
        investor_df: 투자자별 매매동향 (columns: trade_dt, frgn_net_vol, orgn_net_vol, prsn_net_vol)
        financial_df: 펀더멘탈 지표 dict (per, roe, revenue_growth) — optional
        weights: 팩터 가중치
        params: 기술적 분석 파라미터

    Returns:
        dict with total_score, individual scores, signal, confidence
    """
    if weights is None:
        weights = {
            'technical': 0.30,   # MA/RSI/BB (기존 0.4 → 0.3)
            'macd': 0.10,        # MACD (신규)
            'supply': 0.30,      # 수급 (기존 0.4 → 0.3)
            'momentum': 0.15,    # 모멘텀 (기존 0.2 → 0.15)
            'fundamental': 0.15, # 펀더멘탈 (신규)
        }

    tech_score = score_technical(price_df, params)
    macd_score = score_macd(price_df)
    supply_score = score_supply_demand(investor_df)
    momentum_score = score_momentum(price_df)
    fundamental_score_val = score_fundamental(financial_df)

    total = (
        tech_score * weights['technical'] +
        macd_score * weights['macd'] +
        supply_score * weights['supply'] +
        momentum_score * weights['momentum'] +
        fundamental_score_val * weights['fundamental']
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
        'macd_score': round(macd_score, 1),
        'supply_score': round(supply_score, 1),
        'momentum_score': round(momentum_score, 1),
        'fundamental_score': round(fundamental_score_val, 1),
        'signal': signal,
        'confidence': confidence,
    }
