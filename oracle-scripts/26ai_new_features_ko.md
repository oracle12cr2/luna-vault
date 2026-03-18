# Oracle AI Database 26ai 신기능 가이드 (한국어)

> 원문: Oracle AI Database New Features, Release 26ai (G43730-05, 2026-02-05)
> PDF: oracle-scripts/26ai_new_features.pdf
> 300개 이상의 신기능 포함 — AI와 개발자 생산성에 집중

---

## 1. 소개

Oracle AI Database 26ai는 **차세대 장기지원(LTS) 릴리스**. AI Vector Search를 통해 문서·이미지·음성의 벡터를 생성/저장/유사도 검색 가능. JSON/관계형 듀얼리티, 마이크로서비스, RAFT 프로토콜 샤딩 등 개발자 친화 기능 대폭 강화.

---

## 2. 주요 하이라이트

| 기능 | 설명 |
|------|------|
| **AI Vector Search** | 키워드가 아닌 의미 기반(시맨틱) 쿼리. 벡터 데이터를 DB 내에서 직접 검색 |
| **JSON Relational Duality** | 데이터를 JSON 문서 또는 관계형 테이블로 투명하게 접근/수정 |
| **Operational Property Graph** | SQL에서 실시간 그래프 분석. ISO SQL/PGQ 표준 지원 |
| **Microservice Support** | 크로스 서비스 트랜잭션 간소화 |
| **Lock-Free Reservations** | 행 잠금 없이 컬럼 값 예약 (잔액, 재고 등) |
| **Kafka APIs for TxEventQ** | Kafka 앱을 최소 코드 변경으로 Oracle DB 위에서 직접 실행 |
| **JavaScript Stored Procedures** | DB 내에서 JavaScript 스토어드 프로시저 생성 |
| **Priority Transactions** | 저우선순위 트랜잭션이 고우선순위를 블로킹하면 자동 중단 |
| **Data Use Case Domains** | 컬럼의 용도를 선언적으로 정의 (이메일, URL, 비밀번호, 통화 등) |
| **SQL BOOLEAN Data Type** | SQL에서 BOOLEAN 타입 네이티브 지원 |
| **Direct Joins for UPDATE/DELETE** | UPDATE/DELETE에서 직접 조인 |
| **SELECT Without FROM** | FROM 절 없는 SELECT 지원 |
| **GROUP BY 별칭/위치** | GROUP BY에서 컬럼 별칭이나 위치 번호 사용 가능 |
| **Schema Privileges** | 스키마 단위로 시스템 권한 부여 — 보안 간소화 |
| **DB_DEVELOPER_ROLE** | 앱 개발자에게 필요한 권한만 빠르게 부여하는 새 역할 |
| **SQL Firewall** | 비인가 SQL/SQL 인젝션을 실시간 모니터링 및 차단 |
| **Azure AD OAuth2** | Azure AD를 통한 SSO 지원 |

---

## 3. AI Vector Search (상세)

### 벡터 데이터 타입
- **VECTOR 데이터 타입** 내장 — 별도 벡터DB 불필요, 비즈니스 데이터와 AI 벡터를 하나의 SQL에서 결합
- **Sparse Vectors** — SPLADE, BM25 등 희소 인코딩 모델 지원. 키워드 민감도 우수
- **BINARY 벡터 포맷** — FLOAT32 대비 저장 32배↓, 연산 40배↑ 속도, 90%+ 정확도 유지
- **벡터 산술/집계 연산** — +, -, * 연산 및 SUM, AVG 집계 지원
- **PL/SQL 벡터 지원** — PL/SQL에서 벡터 타입 네이티브 사용
- **JSON 내 벡터** — JSON(OSON) 타입에 벡터 스칼라 포함 가능
- **외부 테이블 벡터** — DB 외부(파일시스템, 클라우드) 벡터도 외부 테이블로 유사도 검색
- **사용자 정의 거리 함수** — JavaScript로 커스텀 벡터 거리 메트릭 생성

### 벡터 인덱스
- **Hybrid Vector Index (HVI)** — 풀텍스트 검색 + 시맨틱 벡터 검색 결합. JSON 컬럼도 지원
- **IVF / HNSW 인덱스** — 대규모 데이터셋 근사 유사도 검색
- **Partition-Local 벡터 인덱스** — 파티션별 독립 인덱스로 검색 최적화
- **Persistent Neighbor Graph** — HNSW 인덱스 디스크 체크포인트. 재시작 시 빠른 복구
- **트랜잭션 지원 HNSW** — DML 허용 + RAC 환경에서 트랜잭션 일관성 보장
- **Auto IVF Reorg** — 시스템이 자동으로 IVF 인덱스 재구성 판단/실행
- **RAC 분산 HNSW** — RAC 전체 메모리에 걸쳐 벡터 메모리 풀 확장
- **RAC 복제 HNSW** — 모든 RAC 인스턴스에 HNSW 인덱스 복제
- **Online Index Rebuild** — 테이블 DML 유지하면서 벡터 인덱스 온라인 리빌드
- **Scalar Quantized HNSW** — 스칼라 양자화로 HNSW 인덱스 압축
- **Included Columns** — 벡터 인덱스에 비벡터 컬럼 포함 → 테이블 액세스 제거

### 거리 함수
- **Jaccard Distance** — 이진 벡터용 새 거리 메트릭 (0~1 유사도)
- **PL/SQL JACCARD** — PL/SQL에서 JACCARD 거리 지원

### ONNX 지원
- **ONNX 모델을 DB 오브젝트로** — ONNX 포맷 ML 모델 임포트 → MINING MODEL로 사용
- **1GB 초과 대형 ONNX 모델** — 외부 이니셜라이저로 대형 트랜스포머 모델 지원
- **이미지 트랜스포머 모델** — 이미지 벡터화를 DB 내에서 직접 수행

### 벡터 유틸리티
- **VECTOR_CHUNKS** — 텍스트를 청크로 분할하는 SQL 함수 (임베딩 생성 전처리)

---

## 4. 개발자 생산성

### JSON Relational Duality
- 같은 데이터를 JSON 문서 또는 관계형 테이블로 투명하게 접근
- ORM보다 단순하고 강력

### JavaScript
- DB 내 JavaScript 스토어드 프로시저 생성
- 방대한 JavaScript 라이브러리 에코시스템 활용

### SQL/PL/SQL 강화
- BOOLEAN 데이터 타입
- Direct Joins for UPDATE/DELETE
- SELECT WITHOUT FROM
- GROUP BY 별칭/위치
- Unicode 15.0 지원

### 마이크로서비스
- Kafka APIs for TxEventQ
- Lock-Free Reservations
- Priority Transactions

---

## 5. 보안

- **SQL Firewall** — 비인가 SQL 실시간 차단
- **Schema Privileges** — 스키마 단위 권한 관리
- **DB_DEVELOPER_ROLE** — 개발자 전용 최소 권한 역할
- **Azure AD OAuth2** — SSO 통합

---

## 6. DBA 관리

- 테이블스페이스 빈 공간 회수 간소화
- True Cache (인프라 수준 성능 향상)
- SQL 레벨 성능 개선
- Machine Learning 알고리즘 개선 (텍스트/데이터 분류)

---

## 7. 샤딩/분산DB

- **RAFT 프로토콜** — 샤드 레플리카 생성/관리 간소화
- **Globally Distributed Database Vector Search** — 벡터 테이블 자동 분산/복제, 병렬 검색

---

## 8. COMPATIBLE 파라미터 주의사항

| 상황 | COMPATIBLE 설정 |
|------|----------------|
| 26ai RU 23.6 신규 설치 | 자동 23.6.0 |
| 26ai RU 23.4/23.5에서 패치 | **수동으로 23.6.0 설정 필요** (다운타임 필요) |
| 19c/21c에서 업그레이드 | 수동 설정 필요. 최소 COMPATIBLE 19.0.0 |
| 12c/18c → 26ai | **직접 업그레이드 불가** |

---

> 전체 문서(영문): https://docs.oracle.com/en/database/oracle/oracle-database/26/nfcoa/
> PDF: oracle-scripts/26ai_new_features.pdf
