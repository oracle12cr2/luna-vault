# 🛠️ AI 스킬(SOP) 사용법 가이드

> 영상 "100배 강력한 AI 코딩, 1239개 에이전트 스킬 키트"의 핵심 개념을
> OpenClaw(유나/루나) 환경에서 바로 활용하는 실전 가이드

---

## 1. 스킬이란?

**스킬 = SOP (표준 작전 절차) = AI에게 주는 전문가 매뉴얼**

일반 AI에게 "대시보드 만들어줘" → 스파게티 코드
스킬 장착된 AI에게 "대시보드 만들어줘" → 구조화된 프로덕션 코드

차이: AI가 "어떻게 해야 하는지" 명확한 규칙을 갖고 있느냐

---

## 2. 스킬 구조 (SKILL.md)

모든 스킬은 `SKILL.md` 파일 하나로 정의됨:

```
skills/
└── my-skill/
    ├── SKILL.md          ← 핵심 (AI가 읽는 매뉴얼)
    ├── scripts/          ← 실행 스크립트 (선택)
    └── references/       ← 참고 자료 (선택)
```

### SKILL.md 기본 템플릿

```markdown
---
name: oracle-tuning
description: >
  Oracle SQL 튜닝 자동화. 느린 SQL 감지, 실행계획 분석, 튜닝 제안.
  Use when: SQL 튜닝, 실행계획 분석, AWR 리포트 해석 요청 시.
---

# Oracle SQL 튜닝 스킬

## Prerequisites
- Oracle 19c DB 접속 가능
- app_user 계정

## Quick Reference
\`\`\`bash
# V$SQL에서 느린 SQL 조회
sqlplus app_user/oracle@50.35:1521/PROD
\`\`\`

## Workflow

### 1. 느린 SQL 감지
- V$SQL에서 elapsed_time/executions 상위 조회
- buffer_gets 과다 SQL 식별

### 2. 실행계획 분석
- EXPLAIN PLAN 또는 DBMS_XPLAN.DISPLAY_CURSOR
- Full Table Scan, Nested Loop 과다 등 확인

### 3. 튜닝 제안
- 인덱스 추가/변경
- 힌트 적용
- 쿼리 리팩토링

## Safety Rules
1. DDL(CREATE INDEX 등)은 반드시 사용자 확인 후 실행
2. 프로덕션 DB에서 직접 ALTER 금지 — 테스트 먼저
```

---

## 3. 이미 설치된 스킬 확인

```bash
# OpenClaw 기본 스킬 (유나)
ls /opt/homebrew/lib/node_modules/openclaw/skills/

# 커스텀 스킬
ls ~/.agents/skills/
ls ~/.openclaw/workspace/skills/
```

현재 유나에 설치된 주요 스킬:
| 스킬 | 용도 |
|------|------|
| `kmsg` | 카카오톡 메시지 자동화 |
| `github` | GitHub PR/이슈 관리 |
| `weather` | 날씨 조회 |
| `summarize` | URL/영상 요약 |
| `coding-agent` | Codex/Claude Code 위임 |
| `apple-notes` | Apple 메모 관리 |
| `xurl` | X(트위터) API |
| `apple-neural-engine` | Apple ANE 활용 |

---

## 4. 커스텀 스킬 만들기 (실전 예제)

### 예제 1: Oracle AWR 리포트 스킬

```bash
mkdir -p ~/.openclaw/workspace/skills/oracle-awr
```

`~/.openclaw/workspace/skills/oracle-awr/SKILL.md`:

```markdown
---
name: oracle-awr
description: >
  Oracle AWR 리포트 생성 및 분석.
  Use when: AWR 리포트 생성, DB 성능 분석, Top SQL 확인 요청 시.
---

# Oracle AWR 리포트

## Quick Reference
\`\`\`sql
-- 스냅샷 목록 확인
SELECT snap_id, begin_interval_time
FROM dba_hist_snapshot
ORDER BY snap_id DESC
FETCH FIRST 10 ROWS ONLY;

-- AWR 리포트 생성 (HTML)
@?/rdbms/admin/awrrpt.sql
\`\`\`

## Workflow

### 1. 스냅샷 범위 선택
- 사용자에게 시간대 확인
- 해당 시간대의 snap_id 조회

### 2. 리포트 생성
\`\`\`sql
-- 자동화 스크립트
DEFINE begin_snap = &1
DEFINE end_snap = &2
@?/rdbms/admin/awrrpti.sql '' 1 &begin_snap &end_snap /tmp/awr_report.html
\`\`\`

### 3. 핵심 지표 분석
- **DB Time** vs **Elapsed Time** 비율
- **Top 5 Timed Events** (대기 이벤트)
- **SQL ordered by Elapsed Time** (느린 SQL)
- **Buffer Pool Hit Ratio** (목표: 99%+)

## Safety Rules
1. DBA 권한으로만 실행
2. 운영 시간대 부하 주의
```

### 예제 2: ETF 모의투자 모니터링 스킬

```markdown
---
name: etf-monitor
description: >
  ETF 모의투자 포트폴리오 모니터링 및 리포트.
  Use when: 손익 현황, 포트폴리오 조회, 수익률 분석 요청 시.
---

# ETF 모의투자 모니터

## Prerequisites
- Oracle DB 접속: app_user/oracle@50.35:1521/PROD
- Redis 클러스터: 50.3/4/5:6379 (password: redis)

## Quick Reference
\`\`\`sql
-- 최근 손익 조회
SELECT snap_date, deposit, evlu_amt, evlu_pnl,
       total_return, daily_return, holdings_json
FROM TB_PNL_DAILY
ORDER BY snap_date DESC
FETCH FIRST 7 ROWS ONLY;
\`\`\`

## Workflow

### 1. 일일 리포트
- TB_PNL_DAILY에서 최신 데이터 조회
- 총 평가금액, 수익률, 보유 종목 정리

### 2. 추세 분석
- 최근 7일 daily_return 추이
- 종목별 손익 변화

### 3. 알림 (카톡/디스코드)
- kmsg로 카카오톡 전송
- 디스코드 #etf-signals 채널 알림

## Output Format
📊 ETF 모의투자 손익 현황 (날짜 기준)
💰 총 평가: X원
📈 총 수익률: X%
🔹 보유 종목: ...
```

---

## 5. 스킬 작동 원리 (Call → Load → Release)

```
사용자: "ETF 손익 현황 알려줘"
    ↓
AI가 스킬 목록 스캔 → etf-monitor 매칭
    ↓
SKILL.md 로드 (토큰 사용)
    ↓
지시대로 DB 조회 → 리포트 생성
    ↓
응답 완료 → 스킬 언로드 (토큰 해제)
```

**핵심:** 1,200개 스킬이 있어도 한 번에 1~2개만 로드 → 토큰 낭비 없음

---

## 6. 스킬 vs 프롬프트 차이

| | 일반 프롬프트 | 스킬 (SOP) |
|---|---|---|
| 지식 | 범용, 얕음 | 전문적, 깊음 |
| 일관성 | 매번 다른 결과 | 규칙대로 일관된 결과 |
| 안전성 | 통제 어려움 | 권한/승인 체계 |
| 재사용 | 매번 설명 필요 | 한 번 작성, 계속 사용 |
| 예시 | "Oracle 튜닝해줘" | SKILL.md가 정확한 절차 제공 |

---

## 7. 권한 등급 (3단계)

| 등급 | 설명 | 예시 |
|------|------|------|
| **Official** | 공식 제공, 신뢰도 최고 | github, summarize |
| **Safe** | 읽기 전용, 기획용 | weather, apple-notes |
| **Risk** | 시스템 변경 가능, 승인 필수 | coding-agent, DB DDL |

→ OpenClaw에서는 AGENTS.md의 "Ask first" 규칙이 이 역할을 함

---

## 8. 실전 활용 팁

### 유나에게 스킬 요청하기
```
"ETF 손익 현황 카톡으로 보내줘"
→ etf-monitor + kmsg 스킬 자동 조합

"이 YouTube 영상 분석해줘"
→ summarize 스킬 자동 호출

"GitHub PR 리뷰해줘"
→ github 스킬 자동 호출
```

### 새 스킬 만들 때 체크리스트
- [ ] `SKILL.md` 작성 (name, description 필수)
- [ ] description에 "Use when:" 트리거 조건 명시
- [ ] Quick Reference에 핵심 명령어
- [ ] Workflow에 단계별 절차
- [ ] Safety Rules에 위험 작업 통제 규칙
- [ ] `~/.openclaw/workspace/skills/` 또는 `~/.agents/skills/`에 배치

---

## 요약

1. **스킬 = SKILL.md 파일 하나** (AI가 읽는 전문가 매뉴얼)
2. **필요할 때만 로드** → 토큰 효율적
3. **커스텀 스킬 직접 생성 가능** → 우리만의 규칙/절차 반영
4. **이미 OpenClaw에서 동일한 시스템 사용 중** (kmsg, github, summarize 등)
5. **핵심은 "AI에게 명확한 SOP를 주면 결과물 품질이 100배 달라진다"**
