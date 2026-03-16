# Part 19. 튜닝 실무 사례

> 📖 출처: **Oracle SQL 실전 튜닝 나침반** — Part 19 튜닝 실무 사례 (pp.805~871)

---

## 개요

지금까지 학습한 튜닝 원리와 패턴이 실무에서 어떻게 적용되는지 16개의 실전 사례를 통해 확인한다. 매우 복잡하고 긴 SQL도 하나씩 풀어내면 **대부분 기본 해법은 동일**하다.

---

## 목차

| Section | 관련 단원 | 핵심 튜닝 기법 | 개선 효과 |
|---------|----------|--------------|----------|
| [01](#section-01) | INDEX ACCESS 패턴 | INDEX SKIP SCAN | Buffers 101K → 33 |
| [02](#section-02) | INDEX ACCESS 패턴 | 적절한 INDEX 힌트 지정 | Buffers 357K → 20 |
| [03](#section-03) | JOIN | NL JOIN → HASH JOIN 변경 | 실행시간 67초 → 6초 |
| [04](#section-04) | JOIN (JPPD) | JPPD (JOIN PREDICATE PUSH DOWN) | I/O 2,129K → 1,155 |
| [05](#section-05) | 서브쿼리 | JOIN → 스칼라 서브쿼리 변환 | I/O 5,256 → 2,239 |
| [06](#section-06) | JOIN, 서브쿼리, 반복 ACCESS | EXISTS + JOIN 순서 변경 | I/O 1,809K → 7,668 |
| [07](#section-07) | 실행 계획 분리 | UNION ALL로 실행 계획 분리 | FULL SCAN 제거 |
| [08](#section-08) | JOIN, 실행 계획 분리 | JOIN 순서 변경 + 스칼라 서브쿼리 | I/O 대폭 감소 |
| [09](#section-09) | 서브쿼리, PGA 튜닝 | JPPD + NL JOIN 적용 | PGA 32M 제거 |
| [10](#section-10) | JOIN, 서브쿼리, PGA | WINDOW 함수 + EXISTS | 반복 ACCESS 제거 |
| [11](#section-11) | 동일 데이터 반복 ACCESS | UNION → CASE WHEN 통합 | 반복 SCAN 제거 |
| [12](#section-12) | INDEX ACCESS, 페이징 | INDEX FULL SCAN(MIN/MAX) 유도 | I/O 대폭 감소 |
| [13](#section-13) | 페이징 처리, 서브쿼리 | 페이징 후 JOIN + 스칼라 서브쿼리 | I/O 802K → 수십 |
| [14](#section-14) | JOIN | JOIN 순서/방법 최적화 | 불필요 필터링 제거 |
| [15](#section-15) | JOIN (JPPD) | JPPD로 인라인뷰 침투 | 전체 GROUP BY 제거 |
| [16](#section-16) | 서브쿼리 | JOIN 순서/방법 + 서브쿼리 최적화 | I/O 대폭 감소 |

---

## Section 01
### INDEX SKIP SCAN 활용

**관련 단원**: INDEX ACCESS 패턴

**문제점**: INDEX 컬럼 `[중앙회조합구분코드, 매입추심구분코드, 거래일자, 사무소코드]`에서 중간 컬럼 `매입추심구분코드` 조건 누락 → INDEX ACCESS가 아닌 FILTER로 동작 → 넓은 범위 SCAN (2,913건에 101K Block)

**튜닝**: `매입추심구분코드`의 DISTINCT 값이 **2개**뿐이므로 **INDEX SKIP SCAN** 적용

```sql
-- 튜닝 후: INDEX_SS 힌트 추가
SELECT /*+ INDEX_SS(T1 IX_외화수표일별_N1) */
       T1.사무소코드, T1.외화수표거래번호, ...
  FROM 외화수표일별 T1
 WHERE T1.중앙회조합구분코드 = '1'
   AND T1.거래일자 LIKE (:B0 || '%')
 GROUP BY ...
```

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| INDEX Buffers | 101K | **33** |
| 실행 시간 | 2분 17초 | **0.62초** |

---

## Section 02
### 적절한 INDEX 선택 (힌트)

**관련 단원**: INDEX ACCESS 패턴

**문제점**: 조회 조건 `작업일자`에 적합한 INDEX(`카드환불내역_IX1`)가 있으나, 옵티마이저가 ORDER BY를 피하기 위해 **부적절한 PK INDEX FULL SCAN** 선택 → 417K건 전체 SCAN 후 필터링

**튜닝**: 적절한 INDEX를 힌트로 지정

```sql
SELECT /*+ INDEX(카드환불내역 카드환불내역_IX1) */ *
  FROM 카드환불내역
 WHERE 작업일자 BETWEEN :시작일 AND :종료일
   AND ...
```

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| Buffers | 357K | **20** |
| 실행 시간 | 33.77초 | **0.06초** |

> 💡 A-Rows 427건, Buffers 20 → **CLUSTERING FACTOR 양호**

---

## Section 03
### NL JOIN → HASH JOIN 변경

**관련 단원**: JOIN

**문제점**: 선행 테이블에서 **42만 건**이 후행 테이블들과 NL JOIN → 41만 번 이상 Random Single Block I/O

**튜닝**: 테이블 사이즈가 작으므로(4MB~192MB) **FULL TABLE SCAN + HASH JOIN**으로 변경

```sql
SELECT /*+ USE_HASH(T1 T2) */ ...
  FROM (SELECT /*+ USE_HASH(A B C) */ ...
          FROM 접수처리기본 A, 신청기본 B, 여신고객기본 C
         WHERE ...) T1,
       개인사업자내역 T2
 WHERE T1.실명번호 = T2.신용조사기업식별번호(+);
```

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| Buffers | 2,095K | **51,736** |
| 실행 시간 | 1분 7초 | **6.17초** |

> ⚠️ JOIN 테이블이 수 GB 이상이면 상황 고려 필요

---

## Section 04
### JPPD (JOIN PREDICATE PUSH DOWN)

**관련 단원**: JOIN (JPPD)

**문제점**: 인라인뷰 결과 108건이 UNION ALL VIEW로 **침투하지 못함** → VIEW 전체 830만 건 SCAN 후 HASH JOIN

**튜닝**: NL JOIN으로 변경하여 **JPPD 발생** → 인라인뷰 결과가 VIEW로 침투

```sql
SELECT /*+ USE_NL(A B) */ ...
  FROM 메타기본 A,
       (SELECT /*+ NO_MERGE USE_NL(A B) */ ...
          FROM (SELECT 처리아이디 FROM BPM_이력전송
                 WHERE ... GROUP BY 처리아이디) A,
               V_처리내역 B
         WHERE A.처리아이디 = B.처리아이디
           AND B.설명 LIKE 'TLN%') B
 WHERE A.인덱스ID = B.고객아이디;
```

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| Buffers | 2,129K | **1,155** |
| 실행 시간 | 5분 26초 | **0.02초** |
| PGA | 1,217K | **0** |

> 💡 실행 계획에 **UNION ALL PUSHED PREDICATE** Operation 확인

---

## Section 05
### JOIN → 스칼라 서브쿼리 변환 (캐싱 효과)

**관련 단원**: 서브쿼리

**문제점**: JOIN되는 INPUT 값의 DISTINCT 종류가 매우 적은데 일반 JOIN으로 수행 → 불필요한 반복 I/O

**튜닝**: UNIQUE KEY OUTER JOIN + 값 종류 적음 → **스칼라 서브쿼리**로 변환 (캐싱 효과)

```sql
-- JOIN을 스칼라 서브쿼리로 변환
SELECT ...
     , (SELECT B.단순코드명 FROM 단순통합코드 B
         WHERE B.단순유형코드 = 'REP_NBNK_C'
           AND E.결제신은행코드 = B.단순코드) AS 은행명
     , (SELECT D.고객명 FROM 고객기본 D
         WHERE E.소지자카드고객번호 = D.카드고객번호) AS 고객명
  FROM ...
```

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| Buffers | 5,256 | **2,239** |
| 스칼라 서브쿼리 Starts | — | **1** (캐싱) |

> ⚠️ 값 종류가 **많으면** 캐싱 효과 없음 → 반대로 스칼라 서브쿼리를 FROM절 JOIN으로 변경해야 할 수도 있음

---

## Section 06
### EXISTS + JOIN 순서 변경 + 동일 데이터 반복 ACCESS 제거

**관련 단원**: JOIN, 서브쿼리, 동일 데이터 반복 ACCESS 튜닝

**문제점**:
1. 거래내역 테이블을 MAX() 서브쿼리로 **2번 반복 SCAN**
2. JOIN 순서 비효율 → 530K건이 JOIN 후 90% 버려짐
3. 소형 테이블이 NL JOIN 후행으로 53만 번 JOIN

**튜닝**: MAX() 서브쿼리를 **EXISTS**로 변환 + JOIN 순서 최적화 + 소형 테이블 HASH JOIN

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| Buffers | 1,809K | **7,668** |
| 실행 시간 | 2분 9초 | **대폭 개선** |

---

## Section 07
### 실행 계획 분리 (UNION ALL)

**관련 단원**: 실행 계획 분리

**문제점**: OPTIONAL 바인드 변수(NULL 가능)로 인해 옵티마이저가 **최적 INDEX를 선택하지 못함** → FULL TABLE SCAN

**튜닝**: 바인드 변수 NULL 여부에 따라 **UNION ALL로 실행 계획 분리**

> 💡 DECODE/NVL로 OPTIONAL 처리 시 INDEX 사용 불가 → 실행 계획 분리가 답

---

## Section 08
### JOIN 순서 변경 + 스칼라 서브쿼리

**관련 단원**: JOIN, 실행 계획 분리

**문제점**: 선행 테이블 결과 36,150건이 후행과 NL JOIN → 상품명 LIKE 조건에 의해 19건만 남고 대부분 필터링

**튜닝**: JOIN 순서 최적화 + 필터링 조건을 먼저 적용

---

## Section 09
### JPPD로 인라인뷰 침투

**관련 단원**: 서브쿼리, PGA 튜닝

**문제점**: 선행 결과 1건이 인라인뷰(UNION ALL)로 침투하지 못함 → 전체 SORT + PGA 32M 사용

**튜닝**: NL JOIN + JPPD 적용 → 1건만 VIEW로 침투

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| PGA 사용 | 32M | **0** |

---

## Section 10
### WINDOW 함수 + EXISTS

**관련 단원**: JOIN, 서브쿼리, PGA 튜닝

**문제점**: SELECT절 참조 컬럼만 다르게 하여 동일 테이블을 UNION 위아래에서 **반복 ACCESS**

**튜닝**: WINDOW 함수(분석 함수)로 통합 + EXISTS로 중복 제거

---

## Section 11
### UNION → CASE WHEN 통합

**관련 단원**: 동일 데이터 반복 ACCESS 튜닝

**문제점**: SELECT절 참조 컬럼만 다른데 UNION으로 동일 데이터 **반복 SCAN**

**튜닝**: CASE WHEN으로 한 번만 SCAN하도록 통합

---

## Section 12
### INDEX FULL SCAN (MIN/MAX) 유도

**관련 단원**: INDEX ACCESS 패턴, 페이징 처리

**문제점**: PK INDEX가 있지만 복합 조건(`기준일자 <= :B1 AND 요일구분 = '2'`)으로 INDEX FULL SCAN(MIN/MAX) 미발생 → 전체 범위 SCAN 후 MAX 값 도출

**튜닝**: INDEX FULL SCAN(MIN/MAX)이 발생할 수 있도록 SQL 구조 변경

---

## Section 13
### 페이징 후 JOIN + 스칼라 서브쿼리

**관련 단원**: 페이징 처리, 서브쿼리

**문제점**: 전체 결과 건수와 외부 테이블 **모두 JOIN 후** 페이징으로 20건 추출 → 불필요한 대량 JOIN

**튜닝**:
1. 메인 테이블만으로 **먼저 페이징** (20건 추출)
2. 줄어든 건수에 대해서만 외부 테이블 JOIN
3. UNIQUE KEY OUTER JOIN + 값 종류 적음 → **스칼라 서브쿼리** (캐싱)

| 지표 | 튜닝 전 | 튜닝 후 |
|------|---------|---------|
| PGA | 802K | **0** |
| JOIN 대상 건수 | 15,201건 | **20건** |

---

## Section 14
### JOIN 순서/방법 최적화

**관련 단원**: JOIN

**문제점**: JOIN 순서 비효율 → 많은 건수가 NL JOIN 후 마지막에 대부분 필터링

**튜닝**: LEADING 힌트로 최적 JOIN 순서 지정 + 대량 JOIN은 HASH JOIN 적용

```sql
/*+ LEADING(E D B A C) USE_NL(D B A) USE_HASH(C) */
```

---

## Section 15
### JPPD로 인라인뷰 GROUP BY 제거

**관련 단원**: JOIN (JPPD)

**문제점**: 선행 결과 276건인데 인라인뷰에서 **전체 데이터 GROUP BY** 발생 → 대부분 버림 + PGA 대량 사용

**튜닝**: JPPD로 선행 건수만 인라인뷰에 침투 → 전체 GROUP BY 제거

```sql
/*+ OPT_PARAM('_optimizer_cost_based_transformation' 'on')
    OPT_PARAM('_optimizer_push_pred_cost_based' 'true')
    NO_MERGE(MST) USE_NL(MST) */
```

---

## Section 16
### JOIN 순서/방법 + 서브쿼리 최적화

**관련 단원**: 서브쿼리

**문제점**: 메인 쿼리와 서브쿼리의 JOIN 순서/방법이 비효율적 → 대량 I/O 발생

**튜닝**: JOIN 순서 변경 + 서브쿼리 최적화로 I/O 대폭 감소

---

## 핵심 튜닝 패턴 총정리 ✅

### 1. INDEX 관련
| 패턴 | 상황 | 해법 |
|------|------|------|
| **INDEX SKIP SCAN** | 중간 컬럼 누락 + DISTINCT 값 적음 | `INDEX_SS` 힌트 |
| **적절한 INDEX 선택** | 옵티마이저가 잘못된 INDEX 선택 | `INDEX` 힌트로 지정 |
| **INDEX FULL SCAN(MIN/MAX)** | 복합 조건으로 MIN/MAX 미발생 | SQL 구조 변경 |

### 2. JOIN 관련
| 패턴 | 상황 | 해법 |
|------|------|------|
| **NL → HASH JOIN** | 많은 건수 NL JOIN + 테이블 사이즈 작음 | `USE_HASH` 힌트 |
| **JPPD** | 인라인뷰/UNION ALL VIEW 침투 안 됨 | `USE_NL` + `NO_MERGE` |
| **JOIN 순서 변경** | 비효율적 순서로 대량 필터링 | `LEADING` 힌트 |
| **JOIN → 스칼라 서브쿼리** | DISTINCT 값 적은 UNIQUE KEY JOIN | 스칼라 서브쿼리 캐싱 |

### 3. 서브쿼리/반복 ACCESS
| 패턴 | 상황 | 해법 |
|------|------|------|
| **MAX() 서브쿼리 → EXISTS** | 동일 테이블 반복 SCAN | EXISTS로 변환 |
| **UNION → CASE WHEN** | 동일 데이터 반복 ACCESS | CASE WHEN 통합 |
| **실행 계획 분리** | OPTIONAL 바인드로 INDEX 사용 불가 | UNION ALL 분리 |

### 4. 페이징
| 패턴 | 상황 | 해법 |
|------|------|------|
| **페이징 후 JOIN** | 전체 JOIN 후 페이징 | 먼저 페이징 → 줄어든 건수로 JOIN |
