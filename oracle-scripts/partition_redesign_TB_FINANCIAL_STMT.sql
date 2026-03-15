-- ============================================================
-- TB_FINANCIAL_STMT 파티션 재설계
-- 현재: LIST(REPRT_CODE) 단일 파티션
-- 변경: RANGE(BSNS_YEAR) + HASH(STOCK_CODE) 복합 파티션
--
-- 목적:
--   - WHERE STOCK_CODE = :1 (7만회/일) → 1/8 서브파티션 스캔
--   - WHERE BSNS_YEAR = :1 → 1개 파티션 스캔
--   - DISTINCT STOCK_CODE → 파티션별 병렬 처리 가능
--
-- 실행 계정: STOCK (스키마 소유자) 또는 DBA
-- 예상 소요시간: 30~60분 (380만건 기준)
-- ============================================================

-- ============================================================
-- STEP 1. 신규 테이블 생성 (RANGE-HASH 복합 파티션)
-- ============================================================
CREATE TABLE STOCK.TB_FINANCIAL_STMT_NEW
(
    FS_SEQ             NUMBER DEFAULT STOCK.SEQ_FINANCIAL_STMT.NEXTVAL NOT NULL,
    CORP_CODE          VARCHAR2(8)   NOT NULL,
    STOCK_CODE         VARCHAR2(6),
    BSNS_YEAR          VARCHAR2(4)   NOT NULL,
    REPRT_CODE         VARCHAR2(5)   NOT NULL,
    FS_DIV             VARCHAR2(5)   NOT NULL,
    FS_NM              VARCHAR2(50),
    SJ_DIV             VARCHAR2(5),
    SJ_NM              VARCHAR2(100),
    ACCOUNT_ID         VARCHAR2(100),
    ACCOUNT_NM         VARCHAR2(200),
    ACCOUNT_DETAIL     VARCHAR2(200),
    THSTRM_NM          VARCHAR2(50),
    THSTRM_AMOUNT      NUMBER(20,0),
    THSTRM_ADD_AMOUNT  NUMBER(20,0),
    FRMTRM_NM          VARCHAR2(50),
    FRMTRM_AMOUNT      NUMBER(20,0),
    FRMTRM_Q_NM        VARCHAR2(50),
    FRMTRM_Q_AMOUNT    NUMBER(20,0),
    FRMTRM_ADD_AMOUNT  NUMBER(20,0),
    BFEFRMTRM_NM       VARCHAR2(50),
    BFEFRMTRM_AMOUNT   NUMBER(20,0),
    ORD                NUMBER(5,0),
    CURRENCY           VARCHAR2(5),
    LOAD_DT            DATE DEFAULT SYSDATE NOT NULL
)
TABLESPACE USERS
PARTITION BY RANGE (BSNS_YEAR)
SUBPARTITION BY HASH (STOCK_CODE) SUBPARTITIONS 8
(
    PARTITION P_2021 VALUES LESS THAN ('2022')
    (
        SUBPARTITION P_2021_H1,
        SUBPARTITION P_2021_H2,
        SUBPARTITION P_2021_H3,
        SUBPARTITION P_2021_H4,
        SUBPARTITION P_2021_H5,
        SUBPARTITION P_2021_H6,
        SUBPARTITION P_2021_H7,
        SUBPARTITION P_2021_H8
    ),
    PARTITION P_2022 VALUES LESS THAN ('2023')
    (
        SUBPARTITION P_2022_H1,
        SUBPARTITION P_2022_H2,
        SUBPARTITION P_2022_H3,
        SUBPARTITION P_2022_H4,
        SUBPARTITION P_2022_H5,
        SUBPARTITION P_2022_H6,
        SUBPARTITION P_2022_H7,
        SUBPARTITION P_2022_H8
    ),
    PARTITION P_2023 VALUES LESS THAN ('2024')
    (
        SUBPARTITION P_2023_H1,
        SUBPARTITION P_2023_H2,
        SUBPARTITION P_2023_H3,
        SUBPARTITION P_2023_H4,
        SUBPARTITION P_2023_H5,
        SUBPARTITION P_2023_H6,
        SUBPARTITION P_2023_H7,
        SUBPARTITION P_2023_H8
    ),
    PARTITION P_2024 VALUES LESS THAN ('2025')
    (
        SUBPARTITION P_2024_H1,
        SUBPARTITION P_2024_H2,
        SUBPARTITION P_2024_H3,
        SUBPARTITION P_2024_H4,
        SUBPARTITION P_2024_H5,
        SUBPARTITION P_2024_H6,
        SUBPARTITION P_2024_H7,
        SUBPARTITION P_2024_H8
    ),
    PARTITION P_2025 VALUES LESS THAN ('2026')
    (
        SUBPARTITION P_2025_H1,
        SUBPARTITION P_2025_H2,
        SUBPARTITION P_2025_H3,
        SUBPARTITION P_2025_H4,
        SUBPARTITION P_2025_H5,
        SUBPARTITION P_2025_H6,
        SUBPARTITION P_2025_H7,
        SUBPARTITION P_2025_H8
    ),
    PARTITION P_MAX VALUES LESS THAN (MAXVALUE)
    (
        SUBPARTITION P_MAX_H1,
        SUBPARTITION P_MAX_H2,
        SUBPARTITION P_MAX_H3,
        SUBPARTITION P_MAX_H4,
        SUBPARTITION P_MAX_H5,
        SUBPARTITION P_MAX_H6,
        SUBPARTITION P_MAX_H7,
        SUBPARTITION P_MAX_H8
    )
);

-- ============================================================
-- STEP 2. 데이터 이관 (PARALLEL 4 사용, 약 30~60분)
-- ============================================================
-- 진행상황 확인: SELECT * FROM V$SESSION_LONGOPS WHERE OPNAME LIKE '%INSERT%';

INSERT /*+ PARALLEL(4) APPEND */ INTO STOCK.TB_FINANCIAL_STMT_NEW
SELECT /*+ PARALLEL(4) */
    FS_SEQ, CORP_CODE, STOCK_CODE, BSNS_YEAR, REPRT_CODE,
    FS_DIV, FS_NM, SJ_DIV, SJ_NM, ACCOUNT_ID, ACCOUNT_NM,
    ACCOUNT_DETAIL, THSTRM_NM, THSTRM_AMOUNT, THSTRM_ADD_AMOUNT,
    FRMTRM_NM, FRMTRM_AMOUNT, FRMTRM_Q_NM, FRMTRM_Q_AMOUNT,
    FRMTRM_ADD_AMOUNT, BFEFRMTRM_NM, BFEFRMTRM_AMOUNT,
    ORD, CURRENCY, LOAD_DT
FROM STOCK.TB_FINANCIAL_STMT;
COMMIT;

-- 건수 검증
SELECT COUNT(*) FROM STOCK.TB_FINANCIAL_STMT_NEW;
-- 기존과 동일해야 함 (3,802,835건)

-- ============================================================
-- STEP 3. 인덱스 생성
-- ============================================================

-- PK: FS_SEQ (GLOBAL 인덱스 - 파티션 키가 아니므로)
ALTER TABLE STOCK.TB_FINANCIAL_STMT_NEW
    ADD CONSTRAINT PK_FINANCIAL_STMT_NEW PRIMARY KEY (FS_SEQ)
    USING INDEX GLOBAL TABLESPACE USERS;

-- 핵심 조회 인덱스: STOCK_CODE + BSNS_YEAR (LOCAL)
-- WHERE STOCK_CODE = :1 쿼리에서 HASH 서브파티션 내 빠른 검색
CREATE INDEX STOCK.IDX_FS_STOCK_NEW
    ON STOCK.TB_FINANCIAL_STMT_NEW (STOCK_CODE, BSNS_YEAR)
    LOCAL TABLESPACE USERS;

-- CORP_CODE + BSNS_YEAR + REPRT_CODE 조회용 (LOCAL)
CREATE INDEX STOCK.IDX_FS_CORP_YEAR_NEW
    ON STOCK.TB_FINANCIAL_STMT_NEW (CORP_CODE, BSNS_YEAR, REPRT_CODE)
    LOCAL TABLESPACE USERS;

-- ============================================================
-- STEP 4. 통계정보 수집
-- ============================================================
EXEC DBMS_STATS.GATHER_TABLE_STATS('STOCK', 'TB_FINANCIAL_STMT_NEW', CASCADE=>TRUE, DEGREE=>4, METHOD_OPT=>'FOR ALL COLUMNS SIZE AUTO');

-- ============================================================
-- STEP 5. 테이블 교체 (서비스 중단 최소화)
-- ============================================================
-- ⚠️ 서비스 점검 시간에 실행할 것!

-- 기존 테이블 백업용 이름으로 변경
ALTER TABLE STOCK.TB_FINANCIAL_STMT    RENAME TO TB_FINANCIAL_STMT_OLD;

-- 신규 테이블을 원래 이름으로 변경
ALTER TABLE STOCK.TB_FINANCIAL_STMT_NEW RENAME TO TB_FINANCIAL_STMT;

-- 인덱스명 변경
ALTER INDEX STOCK.PK_FINANCIAL_STMT_NEW    RENAME TO PK_FINANCIAL_STMT;
ALTER INDEX STOCK.IDX_FS_STOCK_NEW         RENAME TO IDX_FS_STOCK;
ALTER INDEX STOCK.IDX_FS_CORP_YEAR_NEW     RENAME TO IDX_FS_CORP_YEAR;

-- ============================================================
-- STEP 6. 검증
-- ============================================================

-- 파티션 현황
SELECT PARTITION_NAME, SUBPARTITION_COUNT, NUM_ROWS, BLOCKS
FROM ALL_TAB_PARTITIONS
WHERE TABLE_OWNER='STOCK' AND TABLE_NAME='TB_FINANCIAL_STMT'
ORDER BY PARTITION_POSITION;

-- 실행계획 검증 (STOCK_CODE 조회 → 서브파티션 Pruning 확인)
EXPLAIN PLAN FOR
SELECT ACCOUNT_ID, SJ_DIV, THSTRM_AMOUNT
FROM STOCK.TB_FINANCIAL_STMT
WHERE STOCK_CODE = '005930';
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
-- 기대값: PARTITION RANGE ALL + PARTITION HASH SINGLE (1/8 서브파티션)

-- 실행계획 검증 (BSNS_YEAR 조회 → RANGE Pruning 확인)
EXPLAIN PLAN FOR
SELECT ACCOUNT_ID, SJ_DIV, THSTRM_AMOUNT
FROM STOCK.TB_FINANCIAL_STMT
WHERE BSNS_YEAR = '2024' AND STOCK_CODE = '005930';
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
-- 기대값: PARTITION RANGE SINGLE + PARTITION HASH SINGLE (1개 서브파티션)

-- DISTINCT STOCK_CODE 성능 확인
SET TIMING ON
SELECT DISTINCT STOCK_CODE FROM STOCK.TB_FINANCIAL_STMT
WHERE STOCK_CODE IS NOT NULL ORDER BY STOCK_CODE;

-- ============================================================
-- STEP 7. 롤백 (문제 발생 시)
-- ============================================================
-- ALTER TABLE STOCK.TB_FINANCIAL_STMT     RENAME TO TB_FINANCIAL_STMT_NEW;
-- ALTER TABLE STOCK.TB_FINANCIAL_STMT_OLD RENAME TO TB_FINANCIAL_STMT;

-- ============================================================
-- STEP 8. 안정화 후 OLD 테이블 삭제 (1주일 후)
-- ============================================================
-- DROP TABLE STOCK.TB_FINANCIAL_STMT_OLD PURGE;

-- ============================================================
-- 파티션별 REPRT_CODE 분포 (선택사항: 추가 서브파티션 분석)
-- ============================================================
-- 향후 REPRT_CODE도 조회 조건이 자주 쓰인다면
-- RANGE(BSNS_YEAR) + LIST(REPRT_CODE) + HASH(STOCK_CODE) 3단계 검토
