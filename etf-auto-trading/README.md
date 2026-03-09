# 🚀 ETF 자동매매 시스템 (Korean ETF Auto-Trading System)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Oracle](https://img.shields.io/badge/Database-Oracle%20RAC-red.svg)](https://oracle.com)
[![API](https://img.shields.io/badge/API-한국투자증권-green.svg)](https://apiportal.koreainvestment.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📊 프로젝트 개요

한국 ETF 10종목을 대상으로 한 **완전 자동화된 매매 신호 시스템**입니다.
- **실시간 데이터 수집** (한국투자증권 OpenAPI)
- **기술적 지표 분석** (SMA, RSI, MACD, 볼린저밴드)
- **매매 신호 생성** (BUY/SELL/HOLD + 강도)
- **백테스팅 환경** (Oracle RAC 기반)

## 🎯 주요 기능

### ✨ 핵심 기능
- 📈 **10개 ETF 실시간 모니터링**
- 🧮 **기술적 지표 자동 계산**
- 🎯 **매매 신호 생성** (AI 기반 다중 지표 종합)
- 💾 **Oracle RAC 기반 데이터 저장**
- 📱 **텔레그램 알림** (선택사항)

### 📊 지원 ETF 종목
| 코드 | ETF명 | 카테고리 | 특징 |
|------|-------|----------|------|
| 069500 | KODEX 200 | 대형주 | 🏢 안정적 |
| 229200 | KODEX KOSDAQ150 | 코스닥 | 🚀 성장주 |
| 102110 | TIGER 200IT | IT섹터 | 💻 기술주 |
| 133690 | TIGER NASDAQ100 | 미국기술주 | 🇺🇸 나스닥 |
| 449180 | KODEX US SP500 | 미국대형주 | 🇺🇸 S&P500 |
| 161510 | KODEX 고배당 | 배당주 | 💰 배당 |
| 091230 | KODEX 2차전지 | 테마주 | 🔋 친환경 |
| 160580 | KODEX 삼성우선주 | 우선주 | 🏢 삼성 |
| 091170 | TIGER 건설 | 섹터주 | 🏗️ 건설 |
| 130680 | TIGER 원유선물 | 원자재 | 🛢️ 원유 |

## 🏗️ 시스템 아키텍처

```
📊 데이터 수집 계층
    ├── 한국투자증권 OpenAPI (실시간)
    ├── 시뮬레이션 데이터 (개발/테스트)
    └── 과거 데이터 백필

🧮 분석 계층  
    ├── 기술적 지표 계산 (TA-Lib)
    ├── 다중 신호 종합 분석
    └── 매매 신호 생성

💾 데이터 계층
    ├── Oracle RAC (메인 DB)
    ├── 실시간 가격 테이블
    ├── 기술적 지표 테이블
    └── 매매 신호 이력

🎯 서비스 계층
    ├── REST API (선택사항)
    ├── 텔레그램 봇 (알림)
    └── 웹 대시보드 (선택사항)
```

## ⚡ 빠른 시작

### 1️⃣ 환경 요구사항
```bash
# 운영체제: Linux (Rocky/RHEL/Ubuntu)
# Python: 3.9+
# Database: Oracle 19c+ (또는 PostgreSQL)
# API: 한국투자증권 계좌 (선택사항)
```

### 2️⃣ 설치
```bash
# 저장소 복제
git clone https://github.com/your-username/etf-auto-trading.git
cd etf-auto-trading

# 의존성 설치
pip3 install -r requirements.txt

# 데이터베이스 설정
python3 setup_database.py

# 시뮬레이션 데이터 생성
python3 generate_historical_data.py
```

### 3️⃣ 기본 실행
```bash
# 기술적 지표 계산
python3 technical_analyzer.py

# 매매 신호 생성
python3 trading_signals.py

# 분석 결과 확인
python3 etf_analysis.py
```

### 4️⃣ 실시간 API 연동 (선택사항)
```bash
# 환경변수 설정
export KIS_APP_KEY="your_app_key"
export KIS_APP_SECRET="your_app_secret"  
export KIS_ACCOUNT_NO="your_account"

# 실시간 데이터 수집
python3 kis_real_collector.py
```

## 🔧 설정 파일

### config.yaml
```yaml
# 데이터베이스 설정
database:
  host: "oracle19c01"
  port: 1521
  service: "PROD"
  user: "stock"
  password: "stock123"

# API 설정  
api:
  kis:
    base_url: "https://openapi.koreainvestment.com:9443"
    demo_url: "https://openapivts.koreainvestment.com:29443"
    
# 매매 설정
trading:
  etf_codes: ["069500", "229200", "102110", "133690", "449180", 
              "161510", "091230", "160580", "091170", "130680"]
  
# 기술적 지표 설정
technical:
  sma_periods: [5, 20, 60, 200]
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
```

## 📊 매매 신호 예시

```bash
🎯 ETF 매매 신호 분석 결과 (2026-03-09 21:22)

🟢 매수 신호 (5개)
🔥 102110 TIGER 200IT    (STRONG) - SMA5 > SMA20 + RSI 과매도
📈 091230 KODEX 2차전지   (MEDIUM) - 상승 트렌드 지속
📊 069500 KODEX 200      (WEAK)   - RSI 극과매도 (6.8)

🔴 매도 신호 (1개)  
📊 449180 KODEX S&P500   (WEAK)   - RSI 과매수 (83.0)

⚪ 보유 신호 (4개)
⚪ 130680 TIGER 원유     (WEAK)   - 혼합 신호
```

## 🗂️ 프로젝트 구조

```
etf-auto-trading/
├── 📄 README.md                    # 프로젝트 가이드
├── 📄 requirements.txt             # Python 의존성
├── 📄 config.yaml                  # 설정 파일
├── 📄 LICENSE                      # MIT 라이선스
│
├── 📁 src/                         # 소스 코드
│   ├── 📄 multi_etf_collector.py   # ETF 데이터 수집
│   ├── 📄 technical_analyzer.py    # 기술적 지표 계산
│   ├── 📄 trading_signals.py       # 매매 신호 생성  
│   ├── 📄 etf_analysis.py          # 분석 리포트
│   └── 📄 kis_real_collector.py    # 실시간 API 수집
│
├── 📁 data/                        # 데이터 파일
│   ├── 📄 generate_historical_data.py  # 시뮬레이션 데이터
│   └── 📄 setup_database.py            # DB 스키마 설정
│
├── 📁 docs/                        # 문서
│   ├── 📄 kis_setup_guide.md       # API 설정 가이드
│   ├── 📄 technical_indicators.md  # 기술적 지표 설명
│   └── 📄 trading_strategy.md      # 매매 전략 가이드
│
├── 📁 scripts/                     # 유틸리티 스크립트
│   ├── 📄 cron_setup.sh           # 자동화 설정
│   └── 📄 backup_data.sh          # 데이터 백업
│
└── 📁 examples/                    # 예제 코드
    ├── 📄 backtest_example.py      # 백테스팅 예제
    └── 📄 telegram_bot_example.py  # 텔레그램 봇 예제
```

## ⚙️ 자동화 설정

### Cron 작업
```bash
# 실시간 데이터 수집 (10분마다)
*/10 * * * * cd /path/to/etf-auto-trading && python3 src/kis_real_collector.py

# 기술적 지표 계산 (30분마다)
*/30 * * * * cd /path/to/etf-auto-trading && python3 src/technical_analyzer.py

# 매매 신호 생성 (1시간마다)  
0 * * * * cd /path/to/etf-auto-trading && python3 src/trading_signals.py

# 일일 분석 리포트 (매일 오후 6시)
0 18 * * * cd /path/to/etf-auto-trading && python3 src/etf_analysis.py
```

## 📈 성과 추적

### 백테스팅 결과 (시뮬레이션)
- **테스트 기간**: 2025-08-21 ~ 2026-03-09 (180일)
- **대상 ETF**: 10종목 포트폴리오
- **매매 신호**: 8개 매수, 1개 매도, 1개 보유 (최신)

### 주요 지표
- **과매도 포착**: RSI < 30 구간에서 매수 신호 정확도 높음
- **추세 추종**: SMA 크로스오버 신호 유효성 확인  
- **리스크 관리**: 과매수 구간 매도 신호로 손실 제한

## 🔒 보안 고려사항

### API 키 관리
```bash
# 환경변수 사용 (권장)
export KIS_APP_KEY="your_key"
export KIS_APP_SECRET="your_secret"

# 또는 .env 파일 (프로젝트 루트)
KIS_APP_KEY=your_key
KIS_APP_SECRET=your_secret
```

### 데이터 보안
- **DB 연결**: SSL/TLS 암호화 권장
- **API 통신**: HTTPS 필수
- **로그 관리**: 민감 정보 로깅 금지

## 🤝 기여하기

1. **Fork** 프로젝트
2. **Feature Branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항 (`git commit -m 'Add amazing feature'`)
4. **Push** to Branch (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

## ⚖️ 라이선스

MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## ⚠️ 면책조항

본 프로젝트는 **교육 및 연구 목적**으로 제작되었습니다.
- **투자 권유가 아님**: 모든 투자 결정은 본인 책임입니다.
- **손실 위험**: 주식 투자에는 원금 손실 위험이 있습니다.
- **데이터 정확성**: 실시간 데이터의 지연이나 오류 가능성이 있습니다.

## 📞 문의

- **이슈 신고**: [GitHub Issues](https://github.com/your-username/etf-auto-trading/issues)
- **기능 요청**: [GitHub Discussions](https://github.com/your-username/etf-auto-trading/discussions)
- **이메일**: your-email@example.com

## 🎯 로드맵

### Version 1.0 (현재)
- ✅ 기본 ETF 데이터 수집
- ✅ 기술적 지표 계산
- ✅ 매매 신호 생성
- ✅ Oracle 데이터베이스 연동

### Version 1.1 (예정)
- 🔄 한국투자증권 API 완전 연동
- 📱 텔레그램 봇 알림
- 📊 웹 대시보드
- 🧪 고도화된 백테스팅

### Version 2.0 (계획)
- 🤖 머신러닝 기반 예측 모델
- 📈 포트폴리오 최적화
- ⚡ 실시간 자동 매매 (주의!)
- 🌐 다중 거래소 지원

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**