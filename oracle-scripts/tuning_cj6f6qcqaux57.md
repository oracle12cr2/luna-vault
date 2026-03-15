# SQL 튜닝 분석 보고서 - cj6f6qcqaux57

**분석일:** 2026-03-15  
**분석자:** 유나  

---

## 대상 SQL

```sql
SELECT DISTINCT STOCK_CODE
FROM stock.TB_FINANCIAL_STMT
WHERE STOCK_CODE IS NOT NULL
ORDER BY STOCK_CODE
```

- **SQL_ID:** cj6f6qcqaux57
- **Plan Hash Value:** 198740622
- **실행 스키마:** STOCK

---

## 성능 현황 (AWR)

| 날짜 | 평균 실행시간 | CPU | Buffer Gets | Disk Reads |
|------|-------------|-----|------------|------------|
| 2026-03-15 | 5.47초 | 3.68초 | 19,916 | 191 |
| 2026-03-14 | 2.61초 | 2.27초 | 19,952 | 0 |
| 2026-03-13 | 5.74초 | 3.68초 | 19,968 | 0 |
| **2026-03-12** | **463.24초** | 9.20초 | 19,943 | **19,655** |
| 2026-03-10 | 11.26초 | 3.95초 | 21,670 | 0 |

> ⚠️ 3/12 Disk Read 급증 → 버퍼 캐시 미스 시 463초 소요 (최악 케이스)

---

## 실행계획 분석

```
| Id | Operation              | Name         | Starts | A-Rows |   A-Time   | Buffers | Reads  |
|----|------------------------|--------------|--------|--------|------------|---------|--------|
|  0 | SELECT STATEMENT       |              |      1 |   1057 | 00:00:05.47|   19916 |    191 |
|  1 |  SORT UNIQUE           |              |      1 |   1057 | 00:00:05.47|   19916 |    191 |
|  2 |   PARTITION LIST ALL   |              |      1 |  3802K | 00:00:04.63|   19916 |    191 |
|  3 |    INDEX FAST FULL SCAN| IDX_FS_STOCK |      5 |  3802K | 00:00:04.33|   19916 |    191 |
```

---

## 테이블 정보

- **테이블:** STOCK.TB_FINANCIAL_STMT
- **파티션:** LIST 5개 (P_ANNUAL/P_HALF/P_Q1/P_Q3/P_ETC, REPRT_CODE 기준)
- **전체 건수:** 3,802,835건
- **DISTINCT STOCK_CODE:** 1,057개
- **인덱스:** IDX_FS_STOCK (STOCK_CODE, BSNS_YEAR) - LOCAL 파티션 인덱스

---

## 문제 원인

1. **PARTITION LIST ALL** — WHERE 조건이 `IS NOT NULL`뿐이라 파티션 Pruning 불가, 전체 5개 파티션 스캔
2. **380만건 → 1,057건** — 3,600배 과다 읽기 (DISTINCT 비효율)
3. **INDEX FAST FULL SCAN 5회 반복** — 파티션 수만큼 인덱스 전체 스캔
4. **통계정보 미수집** — 수집 후에도 동일 플랜 (인덱스 구조 문제)

---

## 튜닝 방안

### 방안 1: Materialized View (검증 완료, 운영 적용 어려움)
```sql
CREATE MATERIALIZED VIEW STOCK.MV_STOCK_CODES
BUILD IMMEDIATE REFRESH COMPLETE ON DEMAND AS
SELECT DISTINCT STOCK_CODE FROM STOCK.TB_FINANCIAL_STMT
WHERE STOCK_CODE IS NOT NULL ORDER BY STOCK_CODE;
```
- **결과:** 2.08초 → **0.02초 (100배 개선)**
- **제약:** MV 관리 부담, 운영 환경 제약

### 방안 2: 요약 테이블 별도 관리 (권장)
```sql
-- STOCK 소유자로 실행
CREATE TABLE STOCK.TB_STOCK_CODE_LIST (
    STOCK_CODE  VARCHAR2(10) PRIMARY KEY,
    LOAD_DT     DATE DEFAULT SYSDATE
);

CREATE INDEX STOCK.IDX_STOCK_CODE_LIST ON STOCK.TB_STOCK_CODE_LIST(STOCK_CODE);

-- 데이터 적재 (배치 또는 트리거)
INSERT INTO STOCK.TB_STOCK_CODE_LIST (STOCK_CODE)
SELECT DISTINCT STOCK_CODE FROM STOCK.TB_FINANCIAL_STMT
WHERE STOCK_CODE IS NOT NULL
  AND STOCK_CODE NOT IN (SELECT STOCK_CODE FROM STOCK.TB_STOCK_CODE_LIST);
COMMIT;
```
- 애플리케이션 SQL 변경: `TB_FINANCIAL_STMT` → `TB_STOCK_CODE_LIST`
- DART 재무제표 수집 시 STOCK_CODE 함께 적재

### 방안 3: 애플리케이션 캐싱 (Redis)
```python
# STOCK_CODE 목록은 자주 바뀌지 않으므로 Redis에 캐싱
# 매일 1회만 DB 조회 후 Redis SET에 저장
# TTL: 24시간
```

### 방안 4: SQL 힌트 (임시 방편)
```sql
-- PARALLEL 힌트 (CPU 가속)
SELECT /*+ PARALLEL(t, 4) */ DISTINCT STOCK_CODE
FROM stock.TB_FINANCIAL_STMT t
WHERE STOCK_CODE IS NOT NULL
ORDER BY STOCK_CODE;
```

---

## 조치 이력

| 날짜 | 조치 | 결과 |
|------|------|------|
| 2026-03-15 | 통계정보 수집 (DEGREE=4) | 플랜 변경 없음 |
| 2026-03-15 | MV 생성 검증 | 0.02초 확인, 운영 미적용 |

---

## 결론 및 권장사항

1. **단기:** DART 재무제표 수집 배치에서 STOCK_CODE를 별도 테이블(`TB_STOCK_CODE_LIST`)에 관리
2. **중기:** Redis 캐싱으로 DB 조회 자체를 줄임
3. **장기:** 파티션 키 재설계 검토 (STOCK_CODE 포함 시 Pruning 가능)
