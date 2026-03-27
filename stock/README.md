# US Market Closing Analysis Script

## 개요
미국 증시 마감 후 주요 지표들을 자동으로 수집하여 한국어 리포트를 생성하는 스크립트입니다.

## 파일 구조
```
stock/
├── us_market_report.py     # 메인 스크립트
├── test_cron.sh           # Cron 호환성 테스트 스크립트
├── us_market.log          # 실행 로그
├── reports/               # 생성된 보고서 디렉토리
│   └── us_market_YYYYMMDD.txt
└── README.md             # 이 파일
```

## 수집 데이터

### 주요 지수 (5개)
- S&P 500 (^GSPC)
- NASDAQ Composite (^IXIC) 
- DOW Jones (^DJI)
- SOX Semiconductor (^SOX)
- Russell 2000 (^RUT)

### 섹터 ETF (11개)
- XLK (Technology), XLF (Financials), XLE (Energy)
- XLV (Healthcare), XLY (Consumer Discretionary), XLP (Consumer Staples)  
- XLI (Industrials), XLB (Materials), XLRE (Real Estate)
- XLU (Utilities), XLC (Communication)

### 채권/금리 (3개 + 스프레드)
- 2Y Treasury (^IRX), 10Y Treasury (^TNX), 30Y Treasury (^TYX)
- 10Y-2Y Spread 자동 계산

### 기타 지표 (4개)
- VIX (^VIX), USD/KRW (KRW=X)
- WTI Crude Oil (CL=F), Gold (GC=F)

### Fear & Greed Index
- CNN API에서 실시간 공포탐욕 지수 수집

## 실행 방법

### 직접 실행
```bash
cd /root/.openclaw/workspace/stock
python3 us_market_report.py
```

### Cron 스케줄링 예시
```cron
# 매일 오후 4:30 (미국 장 마감 후) 실행
30 16 * * 1-5 /root/.openclaw/workspace/stock/us_market_report.py
```

## 출력 형식

### 파일 저장
- 경로: `/root/.openclaw/workspace/stock/reports/us_market_YYYYMMDD.txt`
- 형식: 한국어 마크다운 보고서

### 콘솔 출력
1. 상세 보고서 (Markdown 형식)
2. 채팅용 간단 요약 (Chat notification 용도)

## Oracle DB 저장 (선택사항)
- 연결: app_user/oracle@192.168.50.35:1521/PROD
- 테이블: TB_US_MARKET_DAILY
- 자동 테이블 생성 및 중복 데이터 처리

## 의존성 패키지
```bash
pip install yfinance beautifulsoup4 oracledb requests
```

## 로깅
- 파일: `/root/.openclaw/workspace/stock/us_market.log`
- 레벨: INFO (성공/실패 모든 작업 로깅)

## 에러 처리
- 개별 데이터 소스 실패 시 계속 진행
- 네트워크 오류, API 제한 등 자동 처리
- DB 연결 실패 시에도 파일 저장은 계속

## 특징
- 🎯 Production-ready: 완전한 에러 처리
- 🔄 Cron 호환: 정확한 shebang과 절대 경로
- 🎨 이모지 지시자: 변화율에 따른 직관적 표시
- 🇰🇷 한국어 출력: 모든 결과를 한국어로 표시
- 💾 이중 저장: 파일 + Oracle DB
- 📊 다양한 출력: 상세 리포트 + 채팅용 요약

## 예시 출력
```
🇺🇸 미국 증시 마감 요약
💀 S&P 500: 🔴 -1.51%
💀 NASDAQ: 🔴 -2.01%  
🔴 Dow Jones: 🔴 -0.96%
📊 VIX: 26.8
😰 F&G: 14.6/100 (extreme fear)
```