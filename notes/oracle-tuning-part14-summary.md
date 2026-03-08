# 오라클 튜닝 나침반 — Part 14. 옵티마이저 정리

> 참고 도서: 오동규 저 "THE LOGICAL OPTIMIZER"

---

## Section 01. 옵티마이저란?

### 핵심 정의
- SQL 쿼리의 **최적 실행 계획을 결정**하는 Oracle DB의 핵심 구성 요소
- 모든 후보 실행 계획 중 **비용이 가장 낮은 것**을 선택
- 통계 정보 등을 활용하여 비용 계산

### 옵티마이저 구성 요소 (4단계)

```
Parsed Query → Query Transformer → Estimator → Plan Generator → Row Source Generator
```

| 구성 요소 | 역할 |
|-----------|------|
| **Query Transformer** | SQL을 재구성하여 효율성 향상 (서브쿼리 unnesting, 뷰 병합, 조건절 pushing 등) |
| **Estimator** | 통계 정보 기반으로 각 실행 계획의 비용(CPU, I/O, 메모리) 계산 |
| **Plan Generator** | 비용이 가장 낮은 실행 계획 선택 |
| **Row Source Generator** | 선택된 실행 계획을 DB 엔진이 수행 가능한 형태로 변환 |

### 옵티마이저에 영향을 미치는 요소

**1. 통계 정보 (가장 중요!)**
- 행 수, 고유 값 수, 데이터 분포, NULL 여부
- **카디널리티 추정**이 올바른 실행 계획 선택의 핵심
- **히스토그램**: 왜곡된 데이터 분포 시 선택성 정확도 향상
  - 예: 특정 값에 90% 데이터 집중 → 적은 건수 값은 INDEX, 많은 건수 값은 FULL SCAN
  - 단, 바인드 변수 사용 환경에서는 히스토그램 미수집이 일반적 (실행 계획 재사용 원칙)

**2. 시스템 리소스**
- 메모리 충분 → Hash Join 선호
- 메모리 제한 → Nested Loop 선택

**3. SQL 쿼리 구조 및 힌트**
- JOIN, 서브쿼리, 집계 복잡도 및 힌트 사용이 영향

**4. 옵티마이저 모드**
- `ALL_ROWS` — 전체 처리량 최적화
- `FIRST_ROWS` — 첫 몇 행 응답 시간 최소화

**5. 옵티마이저 파라미터**
- `OPTIMIZER_INDEX_COST_ADJ` — INDEX 비용 조정
- `OPTIMIZER_INDEX_CACHING` — INDEX 캐싱 비율

**6. 스키마 디자인**
- INDEX, 파티션 설계
- PK/FK 제약조건 → JOIN 최적화, 불필요한 작업 제거 정보 제공

### 핵심 메시지
> 옵티마이저가 최적 실행 계획을 생성하려면:
> 1. **정확한 통계 정보 유지**
> 2. **효율적인 스키마 설계**
> 3. **SQL 작성 능력**

---

## Section 02. 10053 TRACE

### 용도
- 옵티마이저가 **하드 파싱 과정에서 실행 계획을 생성하는 과정을 추적**

### 사용법

```sql
-- TRACE ON
ALTER SESSION SET EVENTS '10053 TRACE NAME CONTEXT FOREVER, LEVEL 1';

-- SQL 실행
SELECT ...;

-- TRACE OFF
ALTER SESSION SET EVENTS '10046 TRACE NAME CONTEXT OFF';
```

### Trace 파일 위치 확인

```sql
SELECT RTRIM(C.VALUE,'/')||'/'||D.INSTANCE_NAME||'_ora_'
       ||LTRIM(TO_CHAR(A.SPID))||'.trc'
  FROM V$PROCESS A, V$SESSION B, V$PARAMETER C, V$INSTANCE D
 WHERE A.ADDR = B.PADDR
   AND B.AUDSID = SYS_CONTEXT('USERENV','SESSIONID')
   AND C.NAME = 'user_dump_dest';
```

### 10053 TRACE 12단계

| # | 단계 | 설명 |
|---|------|------|
| 1 | **환경 정보** | DBMS, OS, 하드웨어, Client 정보 |
| 2 | **Query Block** | QUERY BLOCK 정보 + 파싱된 SQL 출력 |
| 3 | **용어 정의** | 10053에서 사용되는 약어 목록 |
| 4 | **옵티마이저 파라미터** | 성능 관련 파라미터 (변경된 것 별도 표시) |
| 5 | **HQT** ⭐ | Heuristic Query Transformation (규칙 기반 쿼리 변환) |
| 6 | **Bind Peeking** | 바인드 변수의 실제 값 확인 (`_OPTIM_PEEK_USER_BINDS=TRUE`) |
| 7 | **CBQT** ⭐ | Cost Based Query Transformation (비용 기반 쿼리 변환) |
| 8 | **통계 정보** | 시스템/테이블/INDEX 통계 출력 |
| 9 | **Access Path** ⭐ | 테이블별 최적 ACCESS PATH와 COST 평가 |
| 10 | **JOIN 최적화** ⭐ | 최적 JOIN 방법 및 순서 결정 |
| 11 | **실행 계획** | SQL + 최종 실행 계획 출력 |
| 12 | **최종 파라미터** | 수행 당시 옵티마이저 파라미터 + 적용된 힌트 |

> **핵심 단계**: 5번/7번(쿼리 Transformation), 9번/10번(Physical Optimization)

### Query Block 개념
- SQL 문의 **기본 구성 단위**
- 옵티마이저가 Query Block 단위로 최적화 시도

```sql
-- 1개 Query Block
SELECT DEPARTMENT_ID, COUNT(*) FROM EMPLOYEES GROUP BY DEPARTMENT_ID;

-- 2개 Query Block (메인 + 서브쿼리)
SELECT EMPLOYEE_ID FROM EMPLOYEES
 WHERE DEPARTMENT_ID = (SELECT DEPARTMENT_ID FROM DEPARTMENTS
                         WHERE DEPARTMENT_NAME = 'SALES');

-- 2개 Query Block (메인 + 인라인뷰)
SELECT D.DEPARTMENT_NAME, E.EMPLOYEE_COUNT
  FROM DEPARTMENTS D,
       (SELECT DEPARTMENT_ID, COUNT(*) AS EMPLOYEE_COUNT
          FROM EMPLOYEES GROUP BY DEPARTMENT_ID) E
 WHERE D.DEPARTMENT_ID = E.DEPARTMENT_ID;
```

### 10053 약어 목록 (중요!)

| 약어 | 의미 |
|------|------|
| **CBQT** | Cost-Based Query Transformation |
| **JPPD** | Join Predicate Push-Down |
| **FPD** | Filter Push-Down |
| **PM** | Predicate Move-Around |
| **CVM** | Complex View Merging |
| **SPJ** | Select-Project-Join |
| **SU** | Subquery Unnesting |
| **OBYE** | Order By Elimination |
| **ST** | Star Transformation (new, CBQT) |
| **CNT** | COUNT(col) → COUNT(*) 변환 |
| **JE** | Join Elimination |
| **JF** | Join Factorization |
| **SLP** | Select List Pruning |
| **DP** | Distinct Placement |
| **CSE** | Common Subexpression Elimination |
| **TE** | Table Expansion |
| **SJC** | Set Join Conversion |

### 통계 정보 약어

| 약어 | 의미 |
|------|------|
| **LB** | Leaf Blocks |
| **DK** | Distinct Keys |
| **LB/K** | 키당 평균 Leaf Block 수 |
| **DB/K** | 키당 평균 Data Block 수 |
| **CLUF** | Clustering Factor |
| **NDV** | Number of Distinct Values |

### 10053 TRACE 예제 분석

**실행 SQL:**
```sql
SELECT ORDER_ID, ORDER_DATE, PRODUCT_ID, UNIT_PRICE, QUANTITY
  FROM ORDER_ITEMS A
 WHERE ORDER_DATE >= TO_DATE('20120101', 'YYYYMMDD')
   AND ORDER_DATE <  TO_DATE('20120121', 'YYYYMMDD')
   AND PRODUCT_ID IN (SELECT PRODUCT_ID FROM PRODUCTS B
                       WHERE PRODUCT_NAME = 'MB - S300');
```

**8단계 — 통계 정보 확인:**
```
ORDER_ITEMS: 9,828,860 rows / 47,104 blocks / AvgRowLen 29
  IX_ORDER_ITEMS_N1: Col#3, LVLS=2, #LB=25818, #DK=990464, CLUF=8698383
  IX_ORDER_ITEMS_N2: Col#2,3, LVLS=2, #LB=32700, #DK=9776360, CLUF=9705905

PRODUCTS: 288 rows / 13 blocks / AvgRowLen 220
  IX_PRODUCTS_PK: Col#1, LVLS=0, #LB=1, #DK=288, CLUF=10
```

**9단계 — Access Path 분석:**
- PRODUCTS: Table Scan 선택 (Cost=5.01, Card=1)
- ORDER_ITEMS: Table Scan (Cost=12954.68, Card=89689.63)
- Skip Scan 거부됨 (비용이 Table Scan보다 높음)

**10단계 — JOIN 최적화:**
- **Nested Loop**: PRODUCTS(드라이빙) → ORDER_ITEMS
- NL Join + Index Range Scan(IX_ORDER_ITEMS_N2) 최종 선택
- **Best NL Cost: 318.18**

**11단계 — 최종 실행 계획:**
```
SELECT STATEMENT                           (Cost=318)
  NESTED LOOPS
    NESTED LOOPS                    313 rows, 15K bytes
      TABLE ACCESS FULL   PRODUCTS    1 row,  21 bytes  (Cost=5)
      INDEX RANGE SCAN     IX_ORDER_ITEMS_N2  311 rows  (Cost=313)
    TABLE ACCESS BY INDEX ROWID ORDER_ITEMS 311 rows, 9019 bytes
```
- PRODUCTS를 FULL SCAN → 1건 ('MB - S300')
- 해당 PRODUCT_ID로 ORDER_ITEMS의 복합 INDEX(ORDER_DATE, PRODUCT_ID) Range Scan

---

## Section 03. Heuristic Query Transformation

### HQT란?
- Costing(비용 계산) 없이 **특정 RULE을 적용해서 SQL을 변환**하는 최적화
- 비용 계산 자체도 자원을 소모하므로, 명백히 유리한 변환은 비용 계산 없이 수행
- 예: COUNT(*)에 ORDER BY → ORDER BY 제거 (정렬 자체를 안 하는 게 최선)

---

### 1. CSE (Common Subexpression Elimination)
> OR 조건에서 중복된 하위 조건을 제거

```sql
-- 변환 전
WHERE (DEPARTMENT_ID = 'D02' AND SALARY = 34800)
   OR DEPARTMENT_ID = 'D02'

-- 변환 후
WHERE DEPARTMENT_ID = 'D02'
```
- CSE 적용 → INDEX RANGE SCAN (Buffers: 9)
- CSE 미적용 → FULL TABLE SCAN (Buffers: 10, OR 조건 때문)

---

### 2. JE (Join Elimination)
> SELECT/WHERE에서 사용하지 않는 테이블의 JOIN을 제거

```sql
-- CUSTOMERS C는 SELECT절에서 미사용
SELECT B.JOB_ID, SUM(A.ORDER_TOTAL)
  FROM ORDERS A, EMPLOYEES B, CUSTOMERS C
 WHERE A.EMPLOYEE_ID = B.EMPLOYEE_ID
   AND A.CUSTOMER_ID = C.CUSTOMER_ID  -- C는 불필요
```

**조건**: JOIN 대상 테이블에 **FK(Foreign Key)**가 있어야 JE 발생!
- FK 없음 → CUSTOMERS와 NL JOIN 수행 (Buffers: 709)
- FK 생성 후 → CUSTOMERS JOIN 완전 제거 (Buffers: 298)

힌트: `ELIMINATE_JOIN(@"SEL$1" "C"@"SEL$1")`

---

### 3. OE (Outer Join Table Elimination)
> OUTER JOIN에서 불필요한 쪽 테이블을 제거

```sql
-- B 컬럼이 SELECT에 없고 OUTER JOIN → B 제거
SELECT A.ORDER_DATE, A.ORDER_STATUS, A.ORDER_TOTAL
  FROM ORDERS A, EMPLOYEES B
 WHERE A.EMPLOYEE_ID = B.EMPLOYEE_ID(+)
```

- INNER JOIN + FK 없음 → JOIN 제거 안 됨 (Buffers: 692)
- **OUTER JOIN** → EMPLOYEES 테이블 제거됨 (Buffers: 296)
  - OUTER TABLE 기준으로 모든 데이터가 나와야 하므로 B 테이블 불필요

힌트: `ELIMINATE_JOIN(@"SEL$1" "B"@"SEL$1")`

---

### 4. OJE (Outer Join Elimination)
> 의미 없는 OUTER JOIN을 INNER JOIN으로 변환

```sql
SELECT A.ORDER_DATE, A.ORDER_STATUS, A.ORDER_TOTAL
  FROM ORDERS A, EMPLOYEES B
 WHERE A.EMPLOYEE_ID = B.EMPLOYEE_ID(+)
   AND B.DEPARTMENT_ID = 'D17'    -- (+) 없음!
```

- JOIN절은 OUTER JOIN이지만 `B.DEPARTMENT_ID = 'D17'`에 `(+)`가 없음
- → OUTER JOIN → **INNER JOIN으로 변환**
- → 선행 테이블이 EMPLOYEES로 바뀌어 최적화됨

---

### 5. OBYE (Order By Elimination)
> 불필요한 ORDER BY를 제거

```sql
SELECT B.JOB_ID, SUM(A.ORDER_TOTAL)
  FROM ORDERS A,
       (SELECT EMPLOYEE_ID, JOB_ID
          FROM EMPLOYEES ORDER BY EMPLOYEE_ID) B  -- 불필요한 ORDER BY
 WHERE A.EMPLOYEE_ID = B.EMPLOYEE_ID
 GROUP BY B.JOB_ID
```

- 인라인 뷰의 ORDER BY는 메인 쿼리 GROUP BY에 영향 없음
- → ORDER BY 제거 (불필요한 정렬 방지)

힌트: `ELIMINATE_OBY(@"SEL$2")`

---

### 6. DE (Distinct Elimination)
> PK 컬럼만 SELECT 시 불필요한 DISTINCT 제거

```sql
SELECT DISTINCT B.EMPLOYEE_ID, C.DEPARTMENT_ID  -- 둘 다 PK
  FROM EMPLOYEES B, DEPARTMENTS C
 WHERE B.DEPARTMENT_ID = C.DEPARTMENT_ID
```

- PK 컬럼만 사용 → DISTINCT 제거 → NESTED LOOPS만 수행
- PK가 아닌 컬럼 포함 시 → HASH UNIQUE 발생 (추가 부하)

---

### 7. CNT (COUNT(column) → COUNT(*))
> NOT NULL 컬럼의 COUNT(컬럼)을 COUNT(*)로 변환

```sql
SELECT DEPARTMENT_ID, COUNT(LAST_NAME) AS CNT  -- LAST_NAME은 NOT NULL
  FROM EMPLOYEES WHERE JOB_ID = 'J01'
 GROUP BY DEPARTMENT_ID
```

- NOT NULL 컬럼 → COUNT(*) 변환 → **INDEX만 SCAN** (Buffers: 3)
- NULLABLE 컬럼 → 테이블 액세스 필요 (Buffers: 5)

---

### 8. FPD (Filter Push Down)
> 메인 쿼리 조건을 인라인 뷰 안으로 이동

```sql
SELECT A.EMPLOYEE_ID, A.FIRST_NAME, A.EMAIL
  FROM (SELECT /*+ NO_MERGE */
               EMPLOYEE_ID, FIRST_NAME, EMAIL, DEPARTMENT_ID, JOB_ID
          FROM EMPLOYEES) A,
       DEPARTMENTS B
 WHERE A.DEPARTMENT_ID = B.DEPARTMENT_ID
   AND A.JOB_ID = 'J01'  -- 이 조건이 뷰 안으로 이동!
```

- `A.JOB_ID = 'J01'` 조건이 인라인 뷰 내부로 push → INDEX 사용 가능
- **NO_MERGE 힌트**: 뷰가 해체되는 것을 방지 (FPD 효과 확인용)
- **Simple View**: GROUP 함수나 분석 함수 없는 단순 인라인 뷰

---

### 9. TP (Transitive Predicate)
> JOIN 조건을 통해 다른 테이블에 상수 조건을 자동 생성

```sql
SELECT B.EMPLOYEE_ID, B.FIRST_NAME, C.DEPARTMENT_NAME
  FROM EMPLOYEES B, DEPARTMENTS C
 WHERE B.DEPARTMENT_ID = C.DEPARTMENT_ID
   AND B.DEPARTMENT_ID = 'D01'
```

- `B.DEPARTMENT_ID = C.DEPARTMENT_ID` + `B.DEPARTMENT_ID = 'D01'`
- → 옵티마이저가 `C.DEPARTMENT_ID = 'D01'` 조건 자동 추가!
- → DEPARTMENTS도 INDEX UNIQUE SCAN 가능

---

### 10. SVM (Simple View Merging)
> Simple View를 해체하여 메인 쿼리와 통합

```sql
SELECT A.EMPLOYEE_ID, A.FIRST_NAME, A.EMAIL, B.DEPARTMENT_NAME
  FROM (SELECT EMPLOYEE_ID, FIRST_NAME, EMAIL, DEPARTMENT_ID, JOB_ID
          FROM EMPLOYEES
         WHERE DEPARTMENT_ID = 'D01') A,
       DEPARTMENTS B
 WHERE A.DEPARTMENT_ID = B.DEPARTMENT_ID
```

- 인라인 뷰가 해체되어 메인 쿼리와 합쳐짐
- 단순 인라인 뷰(GROUP BY, 분석함수 없음) → View Merging 발생

---

## HQT 변환 종류 요약

| 약어 | 변환명 | 핵심 동작 |
|------|--------|-----------|
| **CSE** | Common Subexpression Elimination | OR 조건 중복 제거 |
| **JE** | Join Elimination | 미사용 테이블 JOIN 제거 (FK 필요) |
| **OE** | Outer Join Table Elimination | 불필요한 OUTER JOIN쪽 제거 |
| **OJE** | Outer Join Elimination | 의미 없는 OUTER→INNER 변환 |
| **OBYE** | Order By Elimination | 불필요한 ORDER BY 제거 |
| **DE** | Distinct Elimination | PK만 SELECT 시 DISTINCT 제거 |
| **CNT** | COUNT(col)→COUNT(*) | NOT NULL 컬럼 COUNT 최적화 |
| **FPD** | Filter Push Down | 조건절을 뷰 안으로 이동 |
| **TP** | Transitive Predicate | JOIN 조건으로 상수 조건 자동 생성 |
| **SVM** | Simple View Merging | 단순 뷰 해체 후 메인 쿼리 통합 |

---

## 핵심 정리

1. **옵티마이저 = DB의 두뇌** — SQL의 최적 실행 경로를 결정
2. **정확한 통계 정보가 가장 중요** — 부정확하면 잘못된 실행 계획 생성
3. **10053 TRACE로 옵티마이저 의사결정 과정을 투명하게 확인** 가능
4. **쿼리 변환(HQT/CBQT) → Access Path 선택 → JOIN 최적화** 순서로 진행
5. 바인드 변수 환경에서는 **Bind Peeking**이 하드 파싱 시 실제 값 확인
6. **HQT는 비용 계산 없이 RULE 기반** — 명백히 유리한 변환을 즉시 적용
7. **FK 제약조건이 JE에 필수** — 스키마 설계가 옵티마이저 성능에 직결
8. **NOT NULL 제약조건이 CNT 변환에 영향** — 제약조건 설계의 중요성
