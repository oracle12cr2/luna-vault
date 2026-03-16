# Oracle 19c RAC 성능 파라미터 가이드

> 📝 작성: 루나 (2026-03-16)
> 🏗️ 환경: Oracle 19c RAC 3노드 (PROD1/2/3), 192.168.50.21~23
> 📊 노드당: SGA ~5.7GB, PGA ~2.5GB

---

## 목차

1. [현재 파라미터 현황](#현재-파라미터-현황)
2. [즉시 변경 권장](#-즉시-변경-권장)
3. [검토 후 변경 권장](#-검토-후-변경-권장)
4. [현재 설정 양호](#-현재-설정-양호)
5. [RAC 전용 — 2노드 vs 3노드 차이](#-rac-전용--2노드-vs-3노드-차이)
6. [히든 파라미터](#히든-파라미터)
7. [적용 스크립트](#-적용-스크립트)
8. [적용 후 확인 쿼리](#-적용-후-확인-쿼리)

---

## 현재 파라미터 현황

### 메모리
| 파라미터 | 현재값 | 비고 |
|----------|--------|------|
| memory_target | 0 | AMM 비활성 |
| memory_max_target | 0 | AMM 비활성 |
| sga_target | **0** | ⚠️ ASMM 비활성 (수동 관리) |
| sga_max_size | 5.6GB | SGA 최대 |
| db_cache_size | 3.4GB | 수동 설정 |
| shared_pool_size | 1.7GB | 수동 설정 |
| large_pool_size | 208MB | 수동 설정 |
| java_pool_size | 96MB | 수동 설정 |
| streams_pool_size | 0 | 미사용 |
| result_cache_max_size | 17MB | |
| pga_aggregate_target | 2.4GB | |
| pga_aggregate_limit | 4.8GB | |
| use_large_pages | TRUE | ✅ HugePages 사용 |

### 옵티마이저
| 파라미터 | 현재값 |
|----------|--------|
| optimizer_mode | ALL_ROWS |
| optimizer_adaptive_plans | TRUE |
| optimizer_adaptive_statistics | FALSE |
| optimizer_index_cost_adj | 100 |
| optimizer_index_caching | 0 |

### 커서/세션
| 파라미터 | 현재값 |
|----------|--------|
| cursor_sharing | EXACT |
| open_cursors | 300 |
| session_cached_cursors | 200 |
| processes | 600 |
| sessions | 922 |

### I/O
| 파라미터 | 현재값 |
|----------|--------|
| db_block_size | 8192 |
| db_file_multiblock_read_count | 128 |
| disk_asynch_io | TRUE |
| filesystemio_options | none |
| db_block_checking | FALSE |
| db_block_checksum | TYPICAL |

### 병렬처리
| 파라미터 | 현재값 |
|----------|--------|
| parallel_max_servers | 8 |
| parallel_min_servers | 0 |
| parallel_degree_policy | MANUAL |
| parallel_adaptive_multi_user | FALSE |

### Redo/Undo
| 파라미터 | 현재값 |
|----------|--------|
| log_buffer | 7.1MB |
| undo_retention | 900 (15분) |

### RAC
| 파라미터 | 현재값 |
|----------|--------|
| cluster_database | TRUE |
| cluster_database_instances | 3 |
| statistics_level | **ALL** |
| timed_statistics | TRUE |

### 히든 파라미터
| 파라미터 | 현재값 | 설명 |
|----------|--------|------|
| _gc_policy_time | 20 | GC 정책 평가 주기(분) |
| _gc_read_mostly_locking | TRUE | Read-Mostly Lock 최적화 |
| _gc_undo_affinity | TRUE | UNDO Affinity |
| _lm_tickets | 1000 | Lock Manager 티켓 수 |
| _optimizer_use_feedback | TRUE | Cardinality Feedback 사용 |
| _optimizer_gather_feedback | TRUE | Feedback 수집 |
| _serial_direct_read | auto | Serial Direct Read 자동 |
| _small_table_threshold | 8002 | Small Table 기준 (블록 수) |
| _undo_autotune | TRUE | UNDO 자동 튜닝 |

---

## 🔴 즉시 변경 권장

### 1. statistics_level: ALL → TYPICAL

| 항목 | 내용 |
|------|------|
| **현재값** | ALL |
| **권장값** | **TYPICAL** |
| **이유** | ALL은 Plan Statistics + Timed OS Statistics까지 전부 수집 → **CPU 5~10% 오버헤드** |
| **영향** | AWR, ADDM, ASH 정상 동작에 TYPICAL이면 충분 |
| **재시작** | 필요 없음 (SCOPE=BOTH 가능) |

```sql
ALTER SYSTEM SET statistics_level = 'TYPICAL' SCOPE=BOTH SID='*';
```

### 2. sga_target: 0 → 5G (ASMM 활성화)

| 항목 | 내용 |
|------|------|
| **현재값** | 0 (수동 메모리 관리) |
| **권장값** | **5G** |
| **이유** | ASMM(Automatic Shared Memory Management) 활성화로 Oracle이 db_cache, shared_pool 등 자동 조절. 워크로드 변화에 유연하게 대응 |
| **영향** | 개별 pool 크기(db_cache_size 등)는 최소값으로 동작 |
| **재시작** | **필요** (SCOPE=SPFILE) |

```sql
ALTER SYSTEM SET sga_target = 5G SCOPE=SPFILE SID='*';
-- 개별 pool 사이즈는 그대로 두면 최소 보장값으로 작동
```

> ⚠️ AMM(memory_target) 대신 ASMM(sga_target)을 권장하는 이유:
> - Linux에서 HugePages 사용 시 AMM은 HugePages와 호환 불가
> - 현재 use_large_pages=TRUE이므로 ASMM이 적합

### 3. open_cursors: 300 → 500

| 항목 | 내용 |
|------|------|
| **현재값** | 300 |
| **권장값** | **500** (애플리케이션에 따라 1000까지) |
| **이유** | 복잡한 PL/SQL이나 ORM 사용 시 ORA-1000(maximum open cursors exceeded) 방지 |
| **재시작** | 불필요 |

```sql
ALTER SYSTEM SET open_cursors = 500 SCOPE=BOTH SID='*';
```

### 4. session_cached_cursors: 200 → 300

| 항목 | 내용 |
|------|------|
| **현재값** | 200 |
| **권장값** | **300** |
| **이유** | Soft Parse 비율 향상 → Library Cache Latch 경합 감소. 세션당 캐시하는 커서 수 증가 |
| **재시작** | **필요** (SCOPE=SPFILE) |

```sql
ALTER SYSTEM SET session_cached_cursors = 300 SCOPE=SPFILE SID='*';
```

> 확인: `SELECT * FROM V$SYSSTAT WHERE name LIKE '%parse%';`
> session cursor cache hits / parse count (total) 비율이 90%+ 되어야 함

---

## 🟡 검토 후 변경 권장

### 5. undo_retention: 900 → 1800

| 항목 | 내용 |
|------|------|
| **현재값** | 900 (15분) |
| **권장값** | **1800** (30분) |
| **이유** | 장시간 쿼리 실행 시 ORA-1555(snapshot too old) 방지. UNDO Tablespace 여유 필요 |
| **재시작** | 불필요 |

```sql
ALTER SYSTEM SET undo_retention = 1800 SCOPE=BOTH SID='*';
```

### 6. optimizer_index_caching: 0 → 90

| 항목 | 내용 |
|------|------|
| **현재값** | 0 |
| **권장값** | **90** (OLTP 환경) |
| **이유** | NL JOIN에서 내부 테이블의 INDEX가 Buffer Cache에 있을 확률(%). 높이면 옵티마이저가 NL JOIN을 더 적극 선택 |
| **주의** | DW 환경에서는 0 유지 |
| **재시작** | 불필요 |

```sql
ALTER SYSTEM SET optimizer_index_caching = 90 SCOPE=BOTH SID='*';
```

### 7. optimizer_index_cost_adj: 100 → 30

| 항목 | 내용 |
|------|------|
| **현재값** | 100 (기본) |
| **권장값** | **25~50** (OLTP), 100 (DW) |
| **이유** | INDEX SCAN 비용을 Full Table Scan 대비 몇 %로 볼 것인지. 낮추면 INDEX 선호 증가 |
| **주의** | 너무 낮추면 대량 데이터도 INDEX 타려고 함 → 25 이하는 위험 |
| **재시작** | 불필요 |

```sql
ALTER SYSTEM SET optimizer_index_cost_adj = 30 SCOPE=BOTH SID='*';
```

> ⚠️ optimizer_index_caching + optimizer_index_cost_adj는 세트로 조정.
> OLTP 기간계: (90, 25~30) / 정보계: (0, 100)

### 8. result_cache_max_size: 17MB → 0

| 항목 | 내용 |
|------|------|
| **현재값** | 17MB |
| **권장값** | **0 (비활성)** |
| **이유** | RAC 환경에서 Result Cache는 노드 간 무효화(Invalidation) 오버헤드 발생. 대부분의 RAC 환경에서 비활성 권장 |
| **재시작** | 불필요 |

```sql
ALTER SYSTEM SET result_cache_max_size = 0 SCOPE=BOTH SID='*';
```

### 9. parallel_max_servers: 8 → 16

| 항목 | 내용 |
|------|------|
| **현재값** | 8 |
| **권장값** | **16~32** (CPU 코어 수에 따라) |
| **이유** | 배치 작업, 대량 INDEX 생성, 통계 수집 등에서 병렬도 부족 방지 |
| **공식** | 일반적으로 CPU 코어 수 × 2 이하 |
| **재시작** | 불필요 |

```sql
ALTER SYSTEM SET parallel_max_servers = 16 SCOPE=BOTH SID='*';
```

### 10. filesystemio_options: none → setall (ASM이 아닌 경우)

| 항목 | 내용 |
|------|------|
| **현재값** | none |
| **권장값** | **setall** (파일시스템 기반일 때) |
| **이유** | Async I/O + Direct I/O 활성화 → I/O 성능 향상 |
| **주의** | ASM 사용 시 의미 없음. 파일시스템 확인 필요 |
| **재시작** | **필요** (SCOPE=SPFILE) |

```sql
-- 스토리지가 파일시스템인 경우만
ALTER SYSTEM SET filesystemio_options = 'setall' SCOPE=SPFILE SID='*';
```

---

## 🟢 현재 설정 양호

| 파라미터 | 현재값 | 평가 |
|----------|--------|------|
| cursor_sharing | EXACT | ✅ 정상 (FORCE는 실행계획 불안정) |
| optimizer_mode | ALL_ROWS | ✅ 19c 표준 |
| optimizer_adaptive_plans | TRUE | ✅ 19c 기본값, 유지 |
| optimizer_adaptive_statistics | FALSE | ✅ 19c 기본값 (TRUE는 불안정 사례 多) |
| db_block_size | 8192 | ✅ OLTP 표준 |
| disk_asynch_io | TRUE | ✅ 비동기 I/O |
| use_large_pages | TRUE | ✅ HugePages 활용 |
| parallel_degree_policy | MANUAL | ✅ 수동 제어 (예측 가능) |
| db_file_multiblock_read_count | 128 | ✅ Full Scan 최적 |
| db_block_checking | FALSE | ✅ 성능 우선 (TRUE는 CPU 10%+ 오버헤드) |
| db_block_checksum | TYPICAL | ✅ 표준 |
| _gc_read_mostly_locking | TRUE | ✅ RAC Read-Mostly 최적화 |
| _gc_undo_affinity | TRUE | ✅ UNDO 노드 친화성 |

---

## 🔵 RAC 전용 — 2노드 vs 3노드 차이

### 파라미터 차이

| 파라미터 | 2노드 | 3노드 | 변경 필요 |
|----------|-------|-------|----------|
| cluster_database_instances | 2 | 3 | ✅ |
| UNDO Tablespace | UNDO1, UNDO2 | UNDO1, UNDO2, UNDO3 | ✅ 추가 |
| Redo Thread | 1, 2 | 1, 2, 3 | ✅ 추가 |
| parallel_max_servers | 동일 | 동일 | ❌ |
| _gc_policy_time | 20 | 20 | ❌ |
| _lm_tickets | 1000 | 1000~1500 | 검토 |

### 2노드 → 3노드 확장 시 체크리스트

```sql
-- 1. cluster_database_instances 변경
ALTER SYSTEM SET cluster_database_instances = 3 SCOPE=SPFILE SID='*';

-- 2. 3번 노드 UNDO Tablespace 생성
CREATE UNDO TABLESPACE UNDO3 DATAFILE '+DATA' SIZE 2G AUTOEXTEND ON;

-- 3. 3번 노드 Redo Thread 추가
ALTER DATABASE ADD LOGFILE THREAD 3
  GROUP 7 ('+DATA', '+FRA') SIZE 512M,
  GROUP 8 ('+DATA', '+FRA') SIZE 512M,
  GROUP 9 ('+DATA', '+FRA') SIZE 512M;
ALTER DATABASE ENABLE THREAD 3;

-- 4. 3번 노드 init 파라미터
-- *.instance_number=3 (3번 노드)
-- *.undo_tablespace='UNDO3' (3번 노드)
-- *.thread=3 (3번 노드)
```

### 3노드 → 2노드 축소 시

```sql
-- 3번 노드 인스턴스 종료 후
ALTER DATABASE DISABLE THREAD 3;
-- UNDO3는 사용 완료될 때까지 유지
```

---

## 📋 적용 스크립트

### Phase 1: 재시작 불필요 (즉시 적용)

```sql
-- 성능 통계 레벨
ALTER SYSTEM SET statistics_level = 'TYPICAL' SCOPE=BOTH SID='*';

-- 커서
ALTER SYSTEM SET open_cursors = 500 SCOPE=BOTH SID='*';

-- UNDO
ALTER SYSTEM SET undo_retention = 1800 SCOPE=BOTH SID='*';

-- 옵티마이저 (OLTP 최적화)
ALTER SYSTEM SET optimizer_index_caching = 90 SCOPE=BOTH SID='*';
ALTER SYSTEM SET optimizer_index_cost_adj = 30 SCOPE=BOTH SID='*';

-- Result Cache 비활성
ALTER SYSTEM SET result_cache_max_size = 0 SCOPE=BOTH SID='*';

-- 병렬처리
ALTER SYSTEM SET parallel_max_servers = 16 SCOPE=BOTH SID='*';
```

### Phase 2: 재시작 필요 (점검 시간에 적용)

```sql
-- ASMM 활성화
ALTER SYSTEM SET sga_target = 5G SCOPE=SPFILE SID='*';

-- 커서 캐시
ALTER SYSTEM SET session_cached_cursors = 300 SCOPE=SPFILE SID='*';

-- I/O (파일시스템 기반인 경우만)
-- ALTER SYSTEM SET filesystemio_options = 'setall' SCOPE=SPFILE SID='*';
```

```bash
# Rolling Restart (RAC 무중단)
srvctl stop instance -d PROD -i PROD1
srvctl start instance -d PROD -i PROD1
# 1번 노드 확인 후 2번, 3번 순서대로
srvctl stop instance -d PROD -i PROD2
srvctl start instance -d PROD -i PROD2
srvctl stop instance -d PROD -i PROD3
srvctl start instance -d PROD -i PROD3
```

---

## 📊 적용 후 확인 쿼리

### Parse 효율 확인
```sql
SELECT name, value FROM V$SYSSTAT
WHERE name IN (
  'parse count (total)',
  'parse count (hard)',
  'session cursor cache hits'
);
-- session cursor cache hits / parse count (total) >= 90% 목표
```

### SGA 자동 관리 확인
```sql
SELECT component, current_size/1024/1024 MB, min_size/1024/1024 MIN_MB
FROM V$SGA_DYNAMIC_COMPONENTS
WHERE current_size > 0
ORDER BY current_size DESC;
```

### GC (Global Cache) 성능 확인
```sql
SELECT inst_id,
  ROUND(AVG(CASE WHEN name = 'gc cr block receive time' THEN value END) /
    NULLIF(AVG(CASE WHEN name = 'gc cr blocks received' THEN value END), 0) * 10, 2) AS "GC CR Avg(ms)",
  ROUND(AVG(CASE WHEN name = 'gc current block receive time' THEN value END) /
    NULLIF(AVG(CASE WHEN name = 'gc current blocks received' THEN value END), 0) * 10, 2) AS "GC Current Avg(ms)"
FROM GV$SYSSTAT
WHERE name IN ('gc cr block receive time', 'gc cr blocks received',
               'gc current block receive time', 'gc current blocks received')
GROUP BY inst_id;
-- 1ms 이하 양호, 3ms 이상이면 인터커넥트 점검
```

### Wait Event Top 10
```sql
SELECT event, total_waits, time_waited_micro/1000000 AS time_sec,
  ROUND(time_waited_micro/NULLIF(total_waits,0)/1000, 2) AS avg_ms
FROM V$SYSTEM_EVENT
WHERE wait_class NOT IN ('Idle')
ORDER BY time_waited_micro DESC
FETCH FIRST 10 ROWS ONLY;
```
