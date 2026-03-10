# 한국 ETF 백테스트 프레임워크

한국 주식시장 ETF를 대상으로 다양한 투자 전략을 백테스트할 수 있는 Python 프레임워크입니다.

## 주요 기능

- 🇰🇷 **한국 ETF 데이터 수집**: yfinance를 활용한 한국 ETF 데이터 자동 수집
- 📈 **다양한 전략**: 이동평균 크로스, RSI, 듀얼모멘텀, 자산배분 전략 제공
- 📊 **백테스트 엔진**: backtrader 기반 고성능 백테스트 실행
- 📋 **결과 분석**: 수익률, 드로다운, 샤프비율 등 상세 성과 분석
- 🎨 **시각화**: matplotlib 기반 차트 및 성과 그래프 생성

## 설치

### 1. 필요 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 디렉토리 구조

```
etf-backtest/
├── README.md              # 사용 설명서
├── requirements.txt       # 필요 패키지 목록
├── config.yaml           # 전략 설정 파일
├── main.py               # 메인 실행 파일
├── data/                 # 데이터 수집 모듈
│   └── collector.py
├── strategies/           # 전략 구현 모듈
│   ├── __init__.py
│   ├── ma_cross.py      # 이동평균 크로스 전략
│   ├── rsi.py           # RSI 전략
│   ├── dual_momentum.py # 듀얼모멘텀 전략
│   └── asset_allocation.py # 자산배분 전략
├── backtest/            # 백테스트 엔진
│   ├── __init__.py
│   └── engine.py
└── results/             # 결과 저장 폴더
```

## 사용법

### 1. 기본 실행

모든 전략을 한번에 실행:

```bash
python main.py
```

### 2. 특정 전략만 실행

```bash
# 이동평균 크로스 전략만
python main.py --strategy ma

# RSI 전략만  
python main.py --strategy rsi

# 듀얼모멘텀 전략만
python main.py --strategy momentum

# 자산배분 전략만
python main.py --strategy allocation
```

### 3. 설정 파일 커스터마이징

`config.yaml` 파일을 수정하여 전략 파라미터를 조정할 수 있습니다:

```yaml
# 백테스트 기간 설정
data:
  start_date: \"2020-01-01\"
  end_date: \"2023-12-31\"

# 전략별 파라미터 조정
strategies:
  moving_average_cross:
    enabled: true
    params:
      short_period: 20    # 단기 이동평균
      long_period: 60     # 장기 이동평균
```

## 제공 전략

### 1. 이동평균 크로스 전략 (Golden/Dead Cross)
- **골든크로스**: 단기 이동평균이 장기 이동평균을 상향돌파 → 매수
- **데드크로스**: 단기 이동평균이 장기 이동평균을 하향돌파 → 매도
- **파라미터**: 단기/장기 이동평균 기간

### 2. RSI 과매수/과매도 전략
- **과매도 반등**: RSI가 30 이하에서 상승전환 → 매수
- **과매수 조정**: RSI가 70 이상에서 하락전환 → 매도  
- **파라미터**: RSI 기간, 과매수/과매도 기준선

### 3. 듀얼 모멘텀 전략
- **절대모멘텀**: 자산 수익률이 무위험 수익률보다 높은지 확인
- **상대모멘텀**: 여러 자산 중 가장 좋은 성과의 자산 선택
- **파라미터**: 모멘텀 계산 기간, 무위험 수익률, 리밸런싱 주기

### 4. 정적 자산배분 전략
- **고정 비율**: 주식/채권 비율을 설정된 비율로 유지
- **리밸런싱**: 주기적으로 목표 비율로 재조정
- **파라미터**: 주식/채권 비율, 리밸런싱 주기, 허용 편차

## 지원 ETF

기본적으로 다음 한국 ETF들을 지원합니다:

- **KODEX 200** (069500.KS): KOSPI 200 추종
- **TIGER 미국S&P500** (360750.KS): S&P 500 추종  
- **KODEX 레버리지** (122630.KS): KOSPI 200 2배 레버리지
- **TIGER 나스닥100** (133690.KS): 나스닥 100 추종
- **KODEX 국고채10년** (148070.KS): 국고채 10년 추종

`config.yaml` 파일에서 다른 ETF 티커를 추가하거나 변경할 수 있습니다.

## 결과 분석

백테스트 완료 후 다음 정보들이 제공됩니다:

### 기본 정보
- 초기자금, 최종가치, 총수익률
- 수수료 정보

### 성과 지표  
- **샤프 비율**: 위험 대비 수익률 측정
- **최대 드로다운**: 최대 손실 폭과 기간
- **승률**: 수익 거래 / 전체 거래 비율

### 거래 분석
- 총 거래 횟수
- 수익/손실 거래 분석
- SQN (System Quality Number)

### 차트 및 파일
- 성과 차트 (PNG/JPEG)
- 상세 결과 CSV 파일
- 백테스트 로그 파일

## 커스터마이징

### 새로운 전략 추가

1. `strategies/` 폴더에 새 전략 파일 생성
2. backtrader.Strategy를 상속받아 구현
3. `strategies/__init__.py`에 import 추가
4. `main.py`에서 새 전략 실행 함수 추가

예시:
```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    def __init__(self):
        # 전략 초기화
        pass
    
    def next(self):
        # 매 봉에서 실행될 로직
        pass
```

### 새로운 지표 추가

backtrader의 다양한 기술적 지표들을 활용할 수 있습니다:

```python
# 볼린저 밴드
self.boll = bt.indicators.BollingerBands()

# MACD  
self.macd = bt.indicators.MACD()

# 스토캐스틱
self.stoch = bt.indicators.Stochastic()
```

## 주의사항

1. **데이터 품질**: yfinance 데이터의 정확성을 항상 확인하세요
2. **수수료 고려**: 실제 거래 시 수수료와 슬리피지를 고려하세요  
3. **과최적화 주의**: 과거 데이터에만 최적화된 전략은 실제 성과가 다를 수 있습니다
4. **위험 관리**: 백테스트는 과거 성과이며, 미래를 보장하지 않습니다

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여하기

버그 리포트나 기능 개선 제안은 언제든 환영합니다!

## 참고 자료

- [backtrader 문서](https://www.backtrader.com/)
- [yfinance 문서](https://pypi.org/project/yfinance/)
- [한국거래소 ETF 정보](http://www.krx.co.kr/)