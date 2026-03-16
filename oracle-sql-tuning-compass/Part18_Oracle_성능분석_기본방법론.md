# Part 18. Oracle 성능 분석 기본 방법론

> 📖 출처: **Oracle SQL 실전 튜닝 나침반** — Part 18 Oracle 성능 분석 기본 방법론 (pp.725~803)

---

## 목차

| Section | 제목 | 바로가기 |
|---------|------|---------|
| 01 | 성능 분석 방법론 개요 | [→](#section-01-성능-분석-방법론-개요) |
| 02 | 핵심 성능 데이터 이해 | [→](#section-02-핵심-성능-데이터-이해) |
| 03 | 성능 분석 유틸리티 | [→](#section-03-성능-분석-유틸리티) |
| 04 | 기본적 성능 분석 | [→](#section-04-기본적-성능-분석) |

---

## Section 01. 성능 분석 방법론 개요

### 성능 분석 및 튜닝 흐름도

![성능 분석 흐름도](images/part18/01_performance_analysis_flow.jpeg)

| 단계 | 설명 |
|------|------|
| ① 성능 문제 발생/제기 | 시스템 내 성능 문제 존재를 인식 |
| ② 성능 분석 | Dynamic Performance View, AWR, ASH, ADDM 활용 |
| ③ 성능 튜닝 | 분석을 통해 식별된 문제에 대한 개선 방법 적용 |
| ④ 튜닝 적용 및 평가 | 변경 적용 후 성능 모니터링 및 개선 확인 |

### 성능 분석 로드맵

![성능 분석 로드맵](images/part18/02_performance_roadmap.jpeg)

**분석 흐름:**
1. **성능 문제 발생** → Database 기본 성능 분석
2. **문제 위치 파악** → Database인지 OS Level인지 판별
3. **SQL 성능 분석** → 정상 구간과 문제 구간의 SQL CPU_TIME, 실행시간, I/O 비교
4. **특정 SQL에 의한 문제?** → YES: SQL 튜닝 / NO: WAIT EVENT 분석
5. **WAIT EVENT 분석** → 특정 SQL? 하드웨어 이상? 인프라 분석?
6. **최종 분석 결과 도출** → 튜닝 및 적용

### 성능 튜닝 목표

- **응답 시간 최소화**: 쿼리 및 트랜잭션 완료 시간 단축
- **처리량 최대화**: 단위 시간당 처리 가능한 트랜잭션 수 증가
- **리소스 효율적 사용**: CPU, 메모리, 디스크 I/O 최적화
- **잠금 경합 감소**: 다중 사용자 환경에서 동시성 향상
- **SQL 실행 계획 최적화**: 최소 리소스로 쿼리 처리
- **디스크 I/O 효율화**: 메모리보다 느린 I/O 작업 최소화
- **대기 이벤트 효율화**: latch, buffer busy wait, enq 등 병목 방지
- **Redo/Undo 생성 최소화**: 과도한 생성으로 인한 성능 저하 방지

---

## Section 02. 핵심 성능 데이터 이해

### 1. 시간 모델 — V$SYS_TIME_MODEL

![시간 모델 계층도](images/part18/03_time_model_hierarchy.jpeg)

**Top Down 형태로 성능 분석하는 시간 통계:**

| STAT명 | 설명 |
|--------|------|
| **DB time** | 모든 사용자 프로세스의 총 소진 시간 (WAIT + CPU + I/O). Background 제외. 4개 세션이 10분씩 = DB time 40분 |
| **DB CPU** | 사용자 프로세스의 CPU 시간. Background 제외 |
| **background elapsed time** | Background Process 소비 시간 |
| **sql execute elapsed time** | SQL 수행 시간 (Fetch 포함) |
| **parse time elapsed** | 소프트 + 하드 파싱 시간 |
| **hard parse elapsed time** | 하드 파싱 시간 |
| **PL/SQL execution elapsed time** | PL/SQL 인터프리터 수행 시간 |
| **connection management call elapsed time** | 세션 연결/해제 소요 시간 |

> **핵심**: DB_TIME이 증가하면 성능 문제 발생. 일반적으로 DB_CPU, sql execute elapsed time이 DB_TIME의 대부분을 차지.

**DB_TIME 증가 원인:**
- 시스템 부하 증가 (접속자, 트랜잭션 증가)
- I/O 성능 저하
- 애플리케이션(SQL) 성능 저하
- CPU 리소스 고갈
- 경합에 의한 대기 시간 증가
- 악성 SQL / 하드 파싱 증가

---

### 2. 시스템 통계 — V$SYSSTAT

| STAT명 | 설명 |
|--------|------|
| **session logical reads** | `db block gets` + `consistent gets`. 총 논리적 읽기 수 |
| **db block gets** | Current Block 요청 수 (DML 활동) |
| **consistent gets** | 일관성 모드 Block 검색 (읽기 일관성) |
| **physical reads** | 디스크에서 읽은 총 Block 수 |
| **physical reads direct** | 버퍼 캐시 거치지 않고 직접 읽은 Block 수 |
| **redo size** | 생성된 Redo 데이터 총량 (BYTE) |
| **user commits** | 사용자 commit 수 |
| **user rollbacks** | 사용자 rollback 수 |
| **execute count** | SQL 실행 총 호출 수 |
| **parse count (total)** | 총 파싱 수 (하드 + 소프트) |
| **parse count (hard)** | 하드 파싱 수 |
| **db block changes** | Block 변경 횟수 (INSERT, UPDATE, DELETE 등) |
| **workarea executions - optimal** | PGA 내에서 완료된 작업 수 |
| **workarea executions - onepass** | PGA Overflow로 Disk Swap 1회 |
| **workarea executions - multipass** | PGA Overflow로 Disk Swap 수회 |

---

### 3. 대기 시간 — V$SYSTEM_EVENT

> **DB_TIME = CPU 시간 + 대기 시간**

![WAIT EVENT CLASS](images/part18/04_wait_event_class.jpeg)

| CLASS | 설명 |
|-------|------|
| **Application** | 사용자 Application 부적절한 로직에 의한 대기 (Lock 등) |
| **Concurrency** | 동시 자원 경합에 의한 대기 |
| **User I/O** | 사용자 I/O에 의한 대기 |
| **Commit** | Commit 후 Redo Log 쓰기 확인 대기 |
| **Cluster** | RAC 노드 간 경합에 의한 대기 |
| **Network** | 네트워크 데이터 전송 대기 |
| **System I/O** | Background Process I/O 대기 |
| **Configuration** | DB/Instance 부적절한 구성에 의한 대기 |
| **Idle** | 비활성 세션 대기 (SQL*Net message from client 등) |

### 주요 WAIT EVENT 상세

#### Application Class

| WAIT EVENT | 설명 | 해결 방안 |
|------------|------|----------|
| **enq: TX - row lock contention** | 다른 세션이 잠근 행을 수정하려 할 때 | Lock 경합 최소화, 트랜잭션 짧게 |
| **enq: TM - contention** | 테이블 수준 잠금 경합 | DDL은 비활성 시간에 스케줄링 |

#### Concurrency Class

| WAIT EVENT | 설명 | 해결 방안 |
|------------|------|----------|
| **latch: cache buffers chains** | 동일 Block 동시 접근 시 래치 경합 | 비효율적 SQL 튜닝으로 핫 Block 접근 줄이기 |
| **latch: shared pool** | Shared Pool 동시 할당 경합 (하드 파싱 빈번) | 바인드 변수로 소프트 파싱 유도 |
| **enq: TX - index contention** | INDEX Block Split 경합 | HASH 파티셔닝, INDEX 순서 변경 |
| **library cache lock** | Library Cache 객체 접근 경합 | DDL 줄이고, 바인드 변수 사용 |
| **cursor: pin S wait on X** | 동일 커서 경합 (하드 파싱 관련) | 바인드 변수 처리, 소프트 파싱 |
| **buffer busy waits** | 동일 Block 읽기/수정 경합 (HOT Block) | SQL 튜닝, HASH 파티셔닝으로 분산 |

#### User I/O Class

| WAIT EVENT | 설명 | 해결 방안 |
|------------|------|----------|
| **db file sequential read** | INDEX RANGE SCAN 등 Single Block I/O | SQL 튜닝으로 불필요한 I/O 최소화 |
| **db file scattered read** | FULL TABLE SCAN 등 Multi Block I/O | 비효율적 FULL SCAN 최소화 |
| **direct path read** | 버퍼 캐시 거치지 않는 직접 읽기 | SQL 튜닝, 파티셔닝으로 SCAN 감소 |
| **direct path read temp** | TEMP TABLESPACE 읽기 (SORT, HASH JOIN) | 정렬/JOIN 최적화로 TEMP 사용 감소 |
| **direct path write** | 버퍼 캐시 거치지 않는 직접 쓰기 (APPEND 힌트) | — |
| **read by other session** | 다른 세션이 읽는 Block 대기 | SQL 튜닝으로 동일 Block 접근 줄이기 |

#### Cluster Class (RAC)

| WAIT EVENT | 설명 | 해결 방안 |
|------------|------|----------|
| **gc buffer busy** | Global 버전의 buffer busy wait (HOT Block) | HASH 파티셔닝, 같은 Node에서 수행, SQL 튜닝 |
| **gc cr/current block busy** | Block 인터커넥트 전송 경합 | DML은 같은 Node에서 수행 |

---

### 4. CPU 사용률 — V$OSSTAT

```
CPU 사용률 = BUSY_TIME / (IDLE_TIME + BUSY_TIME)
```

| STAT명 | 설명 |
|--------|------|
| NUM_CPUS | 사용 중인 CPU 수 |
| IDLE_TIME | idle 상태 CPU 시간 (1/100초) |
| BUSY_TIME | busy 상태 CPU 시간 = USER_TIME + SYS_TIME |
| USER_TIME | user code 실행 CPU 시간 |
| SYS_TIME | kernel code 실행 CPU 시간 |
| IOWAIT_TIME | I/O 대기 시간 |

> ⚠️ 누적값이므로 **현재 값 - 이전 값 = DELTA**로 구간 사용률 계산

---

### 5. SQL 성능 — V$SQL

| 컬럼명 | 설명 |
|--------|------|
| **SQL_ID** | SQL 식별자 (문장 변경 시 변경됨) |
| **PLAN_HASH_VALUE** | 실행 계획 종속 값 (계획 변경 시 변경됨) |
| **EXECUTIONS** | SQL 실행 수 |
| **BUFFER_GETS** | 논리적 I/O 발생량 (Block 수) |
| **DISK_READS** | 물리적 I/O 발생량 (Block 수) |
| **ROWS_PROCESSED** | 반환된 행 수 |
| **CPU_TIME** | CPU 시간 (1/1,000,000초) |
| **ELAPSED_TIME** | 수행 시간 (1/1,000,000초) |
| **APPLICATION_WAIT_TIME** | Lock 대기 시간 |
| **CONCURRENCY_WAIT_TIME** | Concurrency 대기 시간 |
| **CLUSTER_WAIT_TIME** | Cluster 대기 시간 |
| **USER_IO_WAIT_TIME** | I/O 대기 시간 |
| **CHILD_NUMBER** | Child Cursor 번호 (너무 높으면 점검 필요) |

---

### 6. ASH (Active Session History)

![ASH 아키텍처](images/part18/05_ash_architecture.jpeg)

- **V$SESSION**에서 **1초 단위**로 정보 Sample 추출 (SQL 사용 안 함)
- AWR 수집 주기마다 MMON Process에 의해 **1/10 비율로** 디스크 저장
- ASH 메모리는 **Shared Pool의 5%** 또는 SGA_TARGET의 5%를 초과할 수 없음

**주요 Sampling 데이터:**
- SQL_ID, 객체 번호, 파일/Block 번호
- SESSION 식별자, 모듈, 프로그램, MACHINE 정보
- 대기 이벤트 식별자 및 파라미터
- 트랜잭션 ID, PGA/TEMP 사용량

| 주요 컬럼 | 설명 |
|-----------|------|
| SAMPLE_TIME | 활동 기록 시간 |
| SESSION_ID / SESSION_SERIAL# | 세션 고유 식별 |
| SQL_ID | 실행 중인 SQL 식별자 |
| SQL_PLAN_HASH_VALUE | 실행 계획 해시 값 |
| EVENT | 대기 중인 이벤트 |
| WAIT_CLASS | 대기 이벤트 클래스 |
| SESSION_STATE | ON CPU / WAITING / IDLE |
| BLOCKING_SESSION | 차단 세션 ID |
| IN_HARD_PARSE | 하드 파싱 중 여부 |
| IN_SQL_EXECUTION | SQL 실행 중 여부 |

---

### 7. AWR (Automatic Workload Repository)

![AWR 아키텍처](images/part18/06_awr_architecture.jpeg)

- 성능 통계를 **디스크에 주기적으로 저장**하는 서비스
- MMON Process에 의해 메모리 통계가 디스크로 전송
- **DBA_HIST_** 로 시작되는 딕셔너리 뷰로 접근
- 기본 **1시간 단위** SNAPSHOT, 최소 **10분 단위**까지 조정 가능
- **정확한 분석을 위해 10분 단위 수집 권고**

| AWR 딕셔너리 뷰 | 원본 | 설명 |
|-----------------|------|------|
| DBA_HIST_SNAPSHOT | — | SNAPSHOT 시간 정보, JOIN 키 |
| DBA_HIST_SQLSTAT | V$SQL | SQL 성능 통계 |
| DBA_HIST_OSSTAT | V$OSSTAT | OS 성능 통계 |
| DBA_HIST_SYS_TIME_MODEL | V$SYS_TIME_MODEL | 시간 모델 통계 |
| DBA_HIST_SYSSTAT | V$SYSSTAT | 시스템 통계 |
| DBA_HIST_SYSTEM_EVENT | V$SYSTEM_EVENT | 대기 시간 통계 |
| DBA_HIST_ACTIVE_SESS_HISTORY | V$ACTIVE_SESSION_HISTORY | ASH 1/10 Sampling |

---

## Section 03. 성능 분석 유틸리티

### AWR Report

**생성 방법:**

```sql
-- 스크립트 이용
SELECT OUTPUT
  FROM (SELECT INSTANCE_NUMBER, DBID,
               MIN(SNAP_ID) MIN_SNAP_ID,
               MAX(SNAP_ID) MAX_SNAP_ID
          FROM SYS.WRM$_SNAPSHOT
         WHERE END_INTERVAL_TIME >= TO_DATE('201707281400', 'YYYYMMDDHH24MI')
           AND END_INTERVAL_TIME <  TO_DATE('201707281450', 'YYYYMMDDHH24MI')
           AND INSTANCE_NUMBER = 1
         GROUP BY INSTANCE_NUMBER, DBID),
       TABLE(DBMS_WORKLOAD_REPOSITORY.AWR_REPORT_HTML(
             DBID, INSTANCE_NUMBER, MIN_SNAP_ID, MAX_SNAP_ID));
```

**AWR Report 주요 섹션:**

| 섹션 | 내용 |
|------|------|
| **Report Summary** | DB 기본 정보, Load Profile, Instance Efficiency |
| **Time Model Statistics** | DB TIME 구성 분석 |
| **Operating System Statistics** | CPU, 메모리, I/O 통계 |
| **Top 10 Foreground Events** | 상위 대기 이벤트 |
| **SQL Statistics** | TOP SQL (Elapsed Time, CPU Time, I/O 등) |
| **IO Statistics** | I/O 활동 분석 |
| **Advisory Statistics** | 메모리/복구 매개변수 최적화 권고 |
| **Wait Statistics** | 버퍼 대기, 큐 대기 통계 |
| **Segment Statistics** | 세그먼트별 통계 |

**Instance Efficiency 주요 지표:**

| 지표 | 목표 | 설명 |
|------|------|------|
| Buffer Nowait % | 100% | 버퍼 대기 없이 접근한 비율 |
| Buffer Hit % | 높을수록 | 버퍼 캐시에서 데이터 발견 비율 |
| Redo NoWait % | 100% | Redo 로그 대기 없이 접근 비율 |
| In-memory Sort % | 100% | 메모리 내 정렬 비율 |
| Soft Parse % | 100% | 소프트 파싱 비율 (하드 파싱 없이) |
| Latch Hit % | 100% | 래치 대기 없이 접근 비율 |
| % Non-Parse CPU | 높을수록 | CPU 중 파싱 제외 비율 |

> 📌 **저자 의견**: AWR Report만으로는 빠른 문제 파악이 어려움. **정상 구간과의 비교 + Trend 데이터**가 필요. 직접 Script를 만들어 사용하는 것을 권장.

---

### ASH Report

- V$ACTIVE_SESSION_HISTORY 데이터 기반
- **특정 시간 구간**의 활성 세션 활동 분석에 유용
- 주요 섹션: Top Events, Top SQL, Top Sessions, Top Objects

---

### ADDM Report

- AWR 데이터를 자동 분석하여 **성능 문제 감지 + 권장사항 제공**
- 최상위 SQL, 경합, I/O 등 문제 식별

```sql
-- ADDM Report 생성
DECLARE
  V_TASK_NAME    VARCHAR2(60);
  N_DBID         NUMBER;
  N_INST_ID      NUMBER;
  N_ST_SNAP_ID   NUMBER;
  N_ED_SNAP_ID   NUMBER;
BEGIN
  SELECT DBID, INSTANCE_NUMBER, MIN(SNAP_ID), MAX(SNAP_ID)
    INTO N_DBID, N_INST_ID, N_ST_SNAP_ID, N_ED_SNAP_ID
    FROM SYS.WRM$_SNAPSHOT
   WHERE END_INTERVAL_TIME >= TO_DATE('201707311400', 'YYYYMMDDHH24MI')
     AND END_INTERVAL_TIME <  TO_DATE('201707311430', 'YYYYMMDDHH24MI')
     AND INSTANCE_NUMBER = 1
   GROUP BY INSTANCE_NUMBER, DBID;

  DBMS_ADDM.ANALYZE_INST(V_TASK_NAME, N_ST_SNAP_ID, N_ED_SNAP_ID,
                          N_INST_ID, N_DBID);
END;
```

```sql
-- ADDM Report 출력
SELECT DBMS_LOB.SUBSTR(RPT_VAL, 2000, 1),
       DBMS_LOB.SUBSTR(RPT_VAL, 2000, 2001),
       DBMS_LOB.SUBSTR(RPT_VAL, 2000, 4001)
       -- ... (2000 단위로 잘라서 출력, CLOB 잘림 방지)
  FROM (SELECT DBMS_ADDM.GET_REPORT(TASK_NAME) RPT_VAL
          FROM (SELECT TASK_NAME
                  FROM USER_ADDM_TASKS
                 WHERE BEGIN_TIME >= TO_DATE('201707311400', 'YYYYMMDDHH24MI')
                   AND END_TIME < TO_DATE('201707311430', 'YYYYMMDDHH24MI')
                 ORDER BY LAST_MODIFIED DESC)
         WHERE ROWNUM <= 1);
```

---

## Section 04. 기본적 성능 분석

### 성능 문제 및 장애 발생 전 징후

| 징후 | 설명 |
|------|------|
| **CPU 사용률 증가** | Session Logical Reads, DB_TIME, SQL 실행 시간, DB_CPU 동반 증가. SYS_TIME만 증가 시 OS Level 점검 필요 |
| **DB_TIME 증가** | DB_TIME = CPU 시간 + 대기 시간. DB 부하 증가의 직접 지표 |
| **WAIT EVENT 대기 시간 증가** | 특정 또는 동시다발적 WAIT EVENT 급증 |
| **ACTIVE SESSION 수 증가** | 악성 SQL, WAIT EVENT 급증, BUG 등으로 세션 수 급증 |
| **Redo/Undo 생성량 증가** | log file sync 증가, 아카이브 로그 급증, DML 성능 영향 |
| **하드 파싱 증가** | CPU/메모리 부담 → 바인드 변수 사용으로 해결 |
| **TEMP TABLESPACE 경합** | 대량 SORT, HASH JOIN 시 TEMP FULL → SQL 중단 |

---

### 기본 성능 분석 Trend

**AWR 딕셔너리 뷰를 이용한 Trend 분석:**

> ⚠️ DBA_HIST_OSSTAT, DBA_HIST_SYS_TIME_MODEL, DBA_HIST_SYSSTAT의 값은 **누적값**이므로 현재 값 - 이전 값 = **DELTA** 계산 필요

**성능 지표 간 상관관계:**

```
CPU 사용률 증가 → DB_TIME ↑, DB_CPU ↑, SQL시간 ↑, Session Logical I/O ↑

DB_CPU 증가 없이 DB_TIME만 증가
  → DB_TIME = DB_CPU + 대기시간 → 대기 시간 증가 → WAIT EVENT 연계 분석

CPU 사용률 증가, BUT I/O·DB_TIME·DB_CPU 변화 없음
  → DB Level 문제 아님 → OS Level 점검 필요 (SYS_TIME 확인)
```

### 분석 연계 흐름

```
기본 성능 Trend (CPU, DB_TIME 등)
    ↓ 급증/점진적 증가 발견 시
SQL 시간 구간 성능 비교 (정상 vs 문제 구간)
    ↓ 특정 SQL 식별
SQL 수행 이력 연계 분석
```

---

### WAIT EVENT 성능 Trend

**분석 형태:**
1. WAIT EVENT **CLASS** 레벨 Trend 확인
2. 특정 CLASS 내 **개별 WAIT EVENT** 시간 구간 비교
3. 문제 WAIT EVENT의 **상세 Trend** 확인

```
DBA_HIST_SYSTEM_EVENT 활용
  - WAIT_CLASS: Application, Cluster, User I/O, Concurrency, Commit 등
  - TOTAL_WAITS: 대기 수
  - TIME_WAITED_MICRO: 대기 시간 (1/1,000,000초)
  - 평균 대기 시간 = TIME_WAITED_MICRO / TOTAL_WAITS / 1000 (ms)
```

---

### SQL 성능 분석

**DBA_HIST_SQLSTAT 주요 컬럼:**

| 컬럼 | 설명 |
|------|------|
| SQL_ID | SQL 식별자 |
| PLAN_HASH_VALUE | 실행 계획 식별자 |
| PARSING_SCHEMA_NAME | 수행 스키마명 |
| EXECUTIONS_DELTA | 실행 수 |
| ROWS_PROCESSED_DELTA | 결과 건수 |
| BUFFER_GETS_DELTA | 논리적 I/O (Block) |
| DISK_READS_DELTA | 물리적 I/O (Block) |
| ELAPSED_TIME_DELTA | 수행 시간 (μs) |
| CPU_TIME_DELTA | CPU 시간 (μs) |
| IOWAIT_DELTA | User I/O 대기 시간 (μs) |
| CCWAIT_DELTA | Concurrency 대기 시간 (μs) |
| CLWAIT_DELTA | Cluster 대기 시간 (μs) |
| DIRECT_WRITES_DELTA | TEMP TABLESPACE WRITE 수 |

---

## 핵심 체크리스트 ✅

1. **DB_TIME = CPU 시간 + 대기 시간** — 성능 분석의 기본 공식
2. **성능 분석은 Trend + 비교** — 정상 구간 대비 문제 구간 비교가 핵심
3. **Top Down 분석** — 시간 모델 → WAIT EVENT CLASS → 개별 EVENT → SQL
4. **AWR 10분 단위** 수집 권고 — 정확한 분석 위해
5. **누적값 주의** — DELTA 계산 필수 (현재 - 이전)
6. **CPU 사용률 증가 시** — DB Level인지 OS Level인지 먼저 판별
7. **WAIT EVENT 급증** — 특정 SQL? 하드웨어? BUG? 원인 추적
8. **하드 파싱 증가** — 바인드 변수 사용으로 소프트 파싱 유도
9. **ACTIVE SESSION 급증** — 즉시 원인 파악 필요 (장애 전조)
10. **직접 Script 작성 활용** — AWR Report보다 정형화된 Trend 분석이 빠름
