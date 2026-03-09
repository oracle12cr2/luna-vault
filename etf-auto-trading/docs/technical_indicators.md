# 🧮 기술적 지표 상세 가이드

## 📊 개요
ETF 자동매매 시스템에서 사용하는 기술적 지표들의 상세 설명과 매매 신호 해석 방법을 설명합니다.

## 🔄 이동평균 (Moving Average)

### SMA (Simple Moving Average)
```
SMA = (P1 + P2 + ... + Pn) / n
```
- **SMA 5**: 단기 추세 (5일)
- **SMA 20**: 중기 추세 (20일) 
- **SMA 60**: 장기 추세 (60일)
- **SMA 200**: 초장기 추세 (200일)

### 매매 신호
- **골든크로스**: SMA5 > SMA20 → 🟢 **매수 신호**
- **데드크로스**: SMA5 < SMA20 → 🔴 **매도 신호**

### EMA (Exponential Moving Average)  
```
EMA = (P × 2/(n+1)) + (EMA전일 × (1 - 2/(n+1)))
```
- SMA보다 최근 데이터에 더 큰 가중치
- 더 빠른 신호 생성

## 📈 모멘텀 지표

### RSI (Relative Strength Index)
```
RSI = 100 - (100 / (1 + RS))
RS = 평균상승분 / 평균하락분
```

#### 해석
- **RSI > 70**: 🔴 과매수 (매도 신호)
- **RSI > 80**: 🔴 극과매수 (강한 매도 신호)
- **RSI < 30**: 🟢 과매도 (매수 신호)  
- **RSI < 20**: 🟢 극과매도 (강한 매수 신호)

#### 시스템 적용
```python
def analyze_rsi_signal(rsi_value):
    if rsi_value < 20:
        return {"type": "BUY", "strength": "STRONG"}
    elif rsi_value < 30:
        return {"type": "BUY", "strength": "MEDIUM"}
    elif rsi_value > 80:
        return {"type": "SELL", "strength": "STRONG"}
    elif rsi_value > 70:
        return {"type": "SELL", "strength": "MEDIUM"}
    else:
        return {"type": "HOLD", "strength": "WEAK"}
```

### MACD (Moving Average Convergence Divergence)
```
MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(MACD, 9)
Histogram = MACD Line - Signal Line
```

#### 매매 신호
- **MACD Line > Signal Line**: 🟢 강세 신호
- **MACD Line < Signal Line**: 🔴 약세 신호
- **Histogram > 0**: 🟢 모멘텀 증가
- **Histogram < 0**: 🔴 모멘텀 감소

## 📊 변동성 지표

### 볼린저 밴드 (Bollinger Bands)
```
Middle Line = SMA(20)
Upper Band = Middle + (2 × Standard Deviation)
Lower Band = Middle - (2 × Standard Deviation)
```

#### 매매 신호
- **가격이 하단 밴드 근처**: 🟢 과매도 (매수 신호)
- **가격이 상단 밴드 근처**: 🔴 과매수 (매도 신호)
- **밴드 폭 확대**: 변동성 증가
- **밴드 폭 축소**: 변동성 감소

#### 밴드 위치 계산
```python
def bollinger_position(price, upper, lower):
    return (price - lower) / (upper - lower)

# 0.0 = 하단 밴드, 1.0 = 상단 밴드
# < 0.2: 매수 신호
# > 0.8: 매도 신호
```

## 📊 거래량 지표

### 거래량 이동평균
```
Volume SMA(20) = 최근 20일 거래량 평균
```

#### 분석 기준
- **거래량 급증** (평균의 2배 이상): 주목 필요
- **거래량 저조** (평균의 50% 이하): 신뢰도 낮음

## 🎯 종합 매매 신호 시스템

### 신호 강도 계산
```python
def calculate_signal_strength():
    signal_weights = {
        'STRONG': 3,
        'MEDIUM': 2,  
        'WEAK': 1
    }
    
    buy_score = sum(weights for signal in buy_signals)
    sell_score = sum(weights for signal in sell_signals)
    
    score_diff = abs(buy_score - sell_score)
    
    if score_diff >= 4:
        return 'STRONG'
    elif score_diff >= 2:
        return 'MEDIUM'
    else:
        return 'WEAK'
```

### 신호 우선순위
1. **RSI 극값** (RSI < 20 또는 RSI > 80) → **STRONG**
2. **이동평균 크로스오버** → **STRONG**  
3. **MACD 신호선 교차** → **MEDIUM**
4. **볼린저 밴드 터치** → **MEDIUM**
5. **EMA 정렬** → **MEDIUM**

## 📊 실제 적용 예시

### 매수 신호 예시
```
ETF: 069500 (KODEX 200)
현재가: 27,500원
RSI(14): 18.3 (극과매도) → STRONG BUY
SMA5: 27,450 > SMA20: 27,600 (상승추세) → MEDIUM BUY
MACD: 양전환 → MEDIUM BUY

최종 신호: BUY (STRONG) - RSI 극과매도 + 상승추세
```

### 매도 신호 예시  
```
ETF: 102110 (TIGER 200IT)
현재가: 19,800원
RSI(14): 85.2 (극과매수) → STRONG SELL
볼린저 위치: 0.95 (상단 근처) → MEDIUM SELL  
거래량: 평균의 3배 (급증) → 주의

최종 신호: SELL (STRONG) - RSI 극과매수 + 고점 신호
```

## ⚠️ 주의사항

### 잘못된 신호 (False Signal) 방지
1. **단일 지표 의존 금지**: 최소 2-3개 지표 종합 판단
2. **시장 상황 고려**: 급락장에서는 RSI 과매도 신호 신뢰도 낮음
3. **거래량 확인**: 거래량 없는 신호는 신뢰도 낮음
4. **추세와 역행 주의**: 강한 하락 추세에서 매수 신호 주의

### 백테스팅 결과 분석
- **승률**: 60-70% (일반적 목표)
- **손익비**: 1:2 이상 권장 (손실 1, 이익 2)
- **최대 연속 손실**: 리스크 관리 필수

## 🔧 파라미터 최적화

### 기본 설정값
```yaml
technical_indicators:
  rsi_period: 14
  sma_periods: [5, 20, 60, 200]
  macd: [12, 26, 9]
  bollinger: [20, 2]
```

### 최적화 고려사항
1. **ETF별 특성**: 변동성 높은 ETF는 파라미터 조정 필요
2. **시장 상황**: 횡보장 vs 추세장에 따른 조정
3. **백테스팅**: 최소 6개월-1년 데이터로 검증

## 📚 추가 학습 자료

### 권장 서적
- "기술적 분석의 기초" - 존 J. 머피
- "일본 캔들스틱 차트 기법" - 스티브 니슨
- "엘더 박사의 새로운 시장 매매법" - 알렉산더 엘더

### 온라인 자료
- [TradingView 교육 센터](https://www.tradingview.com/edu/)
- [Investopedia 기술적 분석](https://www.investopedia.com/technical-analysis-4689657)

---

이 문서는 ETF 자동매매 시스템의 기술적 지표 이해를 돕기 위해 작성되었습니다. 
실제 투자 시에는 추가적인 펀더멘털 분석과 리스크 관리가 필요합니다.