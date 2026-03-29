# 국내 주식 차트 자동 분석 시스템 v2

코스피/코스닥 상위 97종목의 기술적 지표를 자동 분석하고 BUY/SELL 시그널을 생성합니다.

## 특징
- **비용 0원** — 수치 분석 전용 모드 (API 호출 없음)
- **하이브리드 모드** — 수치 1차 필터 → Gemini Vision 2차 검증 (선택)
- **97종목** — 코스피+코스닥 시가총액 상위
- **디스코드 알림** — BUY/SELL 시그널 자동 알림

## 분석 지표
- **이동평균선**: MA5/20/50/60/120/200 정배열/역배열, 골든크로스/데드크로스
- **RSI(14)**: 과매도(<30)/과매수(>70), 다이버전스
- **MACD(12/26/9)**: 골든크로스/데드크로스, 히스토그램
- **거래량**: 20일 평균 대비 급증/폭증 감지
- **볼린저밴드(20,2)**: 상단돌파/하단터치/스퀴즈

## 사용법

```bash
# 기본: 수치 분석 전용 (비용 0원)
python3 main_kr.py

# 상위 20개만
python3 main_kr.py --top20

# Gemini Vision 하이브리드 (BUY/SELL만 검증)
python3 main_kr.py --vision

# 디스코드 알림 없이
python3 main_kr.py --no-discord

# 차트 이미지 생성
python3 main_kr.py --chart
```

## 설치

```bash
pip install yfinance mplfinance pandas python-dotenv google-genai requests
cp .env.example .env  # API 키 설정
```

## .env 설정

```
GEMINI_API_KEY=your-key        # Vision 모드용 (선택)
GEMINI_MODEL=gemini-2.5-flash
DISCORD_WEBHOOK_URL=https://...  # 디스코드 알림용 (선택)
```

## 시그널 판단 기준 (score)
- **BUY**: score ≥ +30 (골든크로스, 과매도 반등, 거래량 폭증 등)
- **SELL**: score ≤ -20 (데드크로스, 역배열, 과매수 등)
- **HOLD**: 그 외

## 출력
- `gemini_chart_analysis_kr.csv` — 전체 결과 (utf-8-sig)
- `charts_kr/` — 캔들차트 PNG (--chart 옵션)
- 디스코드 알림 — BUY/SELL 요약
