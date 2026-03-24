# ROOT.md — 메모리 인덱스

> "무엇이 어디에 있는지" 메타 인덱스. 필요한 정보를 빠르게 찾기 위한 지도.

## 📁 워크스페이스 구조

### Hot Layer (매 세션 로딩)
| 파일 | 용도 |
|------|------|
| `WORKING.md` | 현재 진행 중인 작업 컨텍스트 |
| `SCRATCHPAD.md` | 임시 메모, 중간 결과, 아이디어 |

### Warm Layer (필요 시 로딩)
| 파일 | 용도 |
|------|------|
| `memory/YYYY-MM-DD.md` | 일별 상세 로그 |
| `HEARTBEAT.md` | 주기적 체크 항목 |

### Cold Layer (검색 후 선택 로딩)
| 파일 | 용도 |
|------|------|
| `MEMORY.md` | 장기 기억 (큐레이팅된 요약) |
| `ROOT.md` | 이 파일 — 메모리 인덱스 |

### Identity & Config
| 파일 | 용도 |
|------|------|
| `SOUL.md` | 유나 페르소나 |
| `USER.md` | 남궁건 정보 |
| `IDENTITY.md` | 기본 신원 |
| `TOOLS.md` | 도구/인프라 메모 |
| `AGENTS.md` | 운영 규칙 |

## 🗂️ 프로젝트별 인덱스

### ETF 자동매매
- 위치: `etf-backtest/`, `etf-auto-trading/`, `etf_collector/`
- DB: `etf_trading.db`

### Oracle 관련
- DBA 스크립트: `oracle-scripts/`
- SQL 튜닝: `oracle-sql-tuning/`, `oracle-sql-tuning-compass/`
- Ora2PG: `ora2pg/`
- OGG→PG: `oracle-to-postgresql/`

### Debezium/Kafka
- 위치: `debezium/`

### 블로그
- 프론트: webserver01/02
- Luna Dashboard: `luna-dashboard/`

### 로또
- 위치: `lotto/`

## 📅 주간 요약 (Weekly Compaction)
<!-- 매주 일요일, 해당 주의 daily log를 요약해서 여기에 추가 -->

## 🔄 Compaction 이력
| 날짜 | 범위 | 요약 위치 |
|------|------|-----------|
| 2026-03-24 | 초기 구축 | ROOT.md 생성 |
