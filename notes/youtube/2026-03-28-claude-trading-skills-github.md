# Claude Trading Skills — 33개 스킬 분석 (tradermonty/claude-trading-skills)

> GitHub: https://github.com/tradermonty/claude-trading-skills
> Notion: https://www.notion.so/Claude-Trading-Skills-tradermonty-313993d3695a80d6b2d2ff25959b4dcd

## 전체 33개 스킬 목록

### 시장 분석 (Market Analysis)
1. **Sector Analyst** — 섹터 로테이션 분석 (API 불필요, CSV)
2. **Breadth Chart Analyst** — S&P500 Breadth Index 분석
3. **Market Breadth Analyzer** — 시장 건강도 6요소 스코어 (0-100, API 불필요)
4. **Uptrend Analyzer** — ~2,800 미국주식 상승비율 추적 (API 불필요)
5. **Macro Regime Detector** — 매크로 레짐 감지 (FMP API 필요)
6. **Market Environment Analysis** — 글로벌 매크로 브리핑
7. **Market News Analyst** — 10일 뉴스 수집 → 영향도 분석 (WebSearch)
8. **Theme Detector** — 트렌딩 테마 감지 (AI, 반도체, 클린에너지 등)
9. **US Market Bubble Detector** — 버블 리스크 0-15점 (Minsky 프레임워크)

### 기술적 분석 (Technical)
10. **Technical Analyst** — 주간 차트 기술적 분석 (엘리어트파동, 다우이론, 캔들스틱)
11. **Backtest Expert** — 전략 백테스트 프레임워크 (슬리피지, 워크포워드)

### 종목 분석 (Stock Research)
12. **US Stock Analysis** — 종합 종목 분석 (펀더멘탈+기술적+피어비교)
13. **Institutional Flow Tracker** — 13F 기관 매매 추적 (버핏, 캐시우드 등)
14. **Earnings Calendar** — 어닝 캘린더 (FMP API)
15. **Economic Calendar Fetcher** — 경제 이벤트 (FOMC, CPI, NFP 등)
16. **Scenario Analyzer** — 뉴스 → 18개월 시나리오 프로젝션

### 전략/포지션 관리
17. **Stanley Druckenmiller Investment** — 드러켄밀러 매크로 전략
18. **Options Strategy Advisor** — 옵션 전략 (블랙숄즈, 그릭스)
19. **Portfolio Manager** — 포트폴리오 분석 + 리밸런싱 (Alpaca MCP)
20. **Position Sizer** — 리스크 기반 포지션 사이징 (켈리, ATR)
21. **Exposure Coach** — **전체 투자 비중 결정** (0-100%)

### Edge Research Pipeline (고급)
22. **Edge Candidate Agent** — 관찰 → 리서치 티켓 생성
23. **Trade Hypothesis Ideator** — 매매 가설 생성 (1-5개 카드)
24. **Strategy Pivot Designer** — 전략 정체 시 대안 제시
25. **Edge Strategy Reviewer** — 전략 품질 검증 (8가지 기준)
26. **Edge Pipeline Orchestrator** — 전체 파이프라인 오케스트레이션
27. **Edge Signal Aggregator** — 멀티 스킬 시그널 통합
28. **Trader Memory Core** — 매매 기록 라이프사이클 관리

### 기타
29-33. VCP Screener, PEAD Screener, CANSLIM Screener, FTD Detector, Dividend SOP 등

---

## 우리 시스템에 적용 가능한 것 (우선순위)

### 🔥 즉시 적용 가능 (API 불필요)

#### 1. Exposure Coach — 전체 투자 비중 결정
- **현재 우리 문제**: 종목별 매수/매도만 판단, 전체 비중 조절 없음
- **적용**: 시장 건강도 → 투자 비중 ceiling (예: FEAR → 30%, NORMAL → 70%)
- market-breadth + uptrend + macro-regime + bubble-detector 조합

#### 2. Market Breadth Analyzer — 시장 건강도 스코어
- 6요소: 전체 Breadth, 섹터 참여도, 섹터 로테이션, 모멘텀, 평균회귀 리스크, 역사적 맥락
- CSV 데이터만 필요 (무료)
- 우리 daytrading.py 매수 조건에 추가 가능

#### 3. Sector Analyst — 섹터 로테이션
- 경기 사이클별 섹터 강약 (Early/Mid/Late/Recession)
- 방어주(유틸, 필수소비재) vs 공격주(기술, 산업재)
- CSV 데이터 (무료)

#### 4. Bubble Detector — 버블 리스크
- Put/Call, VIX, 마진부채, Breadth, IPO 데이터
- 0-15점: Normal(0-4) → Caution(5-7) → Elevated(8-9) → Euphoria(10-12) → Critical(13-15)
- 각 단계별 행동 지침 포함

#### 5. Position Sizer — 포지션 사이징
- Fixed Fractional, ATR-based, Kelly Criterion
- 포트폴리오 제약 (종목별 max %, 섹터별 max %)
- API 불필요, 순수 계산

### 🟡 FMP API 필요 (무료 250회/일)

#### 6. Macro Regime Detector
- RSP/SPY 집중도, 수익률 곡선, 신용 상태, 규모 팩터
- 레짐: Concentration, Broadening, Contraction, Inflationary, Transitional

#### 7. Institutional Flow Tracker
- 13F 기관 매매 추적 (한국은 TB_INVESTOR_TREND로 대체 가능)

---

## 트러블슈팅 프롬프트 (참고)

| 현상 | 해결 프롬프트 |
|------|-------------|
| **yfinance 429 에러** | `각 종목 조회 사이에 time.sleep(1) 추가 + SPY 데이터 캐싱` |
| **모든 종목 점수 50점** | `info.get('trailingPE', 0) or 0 이중 방어 + 필드별 로그` |
| **RSI 값 NaN** | `rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50.0` |
| **SQLite database locked** | `sqlite3.connect(DB_PATH, timeout=10) + conn.close() 확실히 호출` |

---

## 핵심 철학 (tradermonty)
- 감이 아닌 **정량 스코어링** (0-100)
- **스킬 체이닝**: 여러 스킬 조합으로 워크플로우
- **자기 개선**: 품질 90점 미만 → 자동 수정
- 검증된 투자 전략: 오닐(CAN SLIM), 미너비니(추세추종), 드러켄밀러(매크로)

## TODO
- [ ] Exposure Coach 로직 우리 daytrading.py에 반영
- [ ] Market Breadth Analyzer CSV 데이터 수집 자동화
- [ ] Bubble Detector 점수 → 매크로 패닉 체크에 통합
- [ ] Position Sizer → 종목별 비중 최적화
- [ ] FMP API 키 발급 → Macro Regime Detector 연동
