-- ============================================================
-- TB_FINANCIAL_STMT 온라인 파티션 재설계
-- 방법: DBMS_REDEFINITION (서비스 중단 없음)
-- 실행 계정: STOCK 소유자 또는 DBA
-- 예상 소요시간: 30~60분 (데이터 이관 중 서비스 정상)
-- ============================================================

-- ============================================================
-- STEP 0. 사전 권한 확인 (DBA 계정으로 실행)
-- ============================================================
-- GRANT EXECUTE ON DBMS_REDEFINITION TO STOCK;
-- GRANT ALTER ANY TABLE TO STOCK;
-- GRANT DROP ANY TABLE TO STOCK;
-- GRANT LOCK ANY TABLE TO STOCK;
-- GRANT CREATE ANY TABLE TO STOCK;
-- GRANT CREATE ANY INDEX TO STOCK;
-- GRANT CREATE ANY TRIGGER TO STOCK;

-- ============================================================
-- STEP 1. 재정의 가능 여부 확인
-- ============================================================
EXEC DBMS_REDEFINITION.CAN_REDEF_TABLE('STOCK', 'TB_FINANCIAL_STMT', DBMS_REDEFINITION.CONS_USE_ROWID);

-- ============================================================
-- STEP 2. 중간 테이블 생성 (신규 파티션 구조)
-- ============================================================
CREATE TABLE STOCK.TB_FINANCIAL_STMT_INT
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
    PARTITION P_2021 VALUES LESS THAN ('2022'),
    PARTITION P_2022 VALUES LESS THAN ('2023'),
    PARTITION P_2023 VALUES LESS THAN ('2024'),
    PARTITION P_2024 VALUES LESS THAN ('2025'),
    PARTITION P_2025 VALUES LESS THAN ('2026'),
    PARTITION P_MAX  VALUES LESS THAN (MAXVALUE)
);

-- ============================================================
-- STEP 3. 온라인 재정의 시작 (이 동안 서비스 정상 운영)
-- ============================================================
-- 소요시간: 약 30~60분 (380만건 복사)
-- 진행 확인: SELECT * FROM V$SESSION_LONGOPS WHERE OPNAME LIKE '%REDEF%';

EXEC DBMS_REDEFINITION.START_REDEF_TABLE(
    uname       => 'STOCK',
    orig_table  => 'TB_FINANCIAL_STMT',
    int_table   => 'TB_FINANCIAL_STMT_INT',
    options_flag => DBMS_REDEFINITION.CONS_USE_ROWID
);

-- ============================================================
-- STEP 4. 중간 테이블에 인덱스 생성 (재정의 중 가능)
-- ============================================================

-- STOCK_CODE + BSNS_YEAR 인덱스 (LOCAL)
CREATE INDEX STOCK.IDX_FS_STOCK_INT
    ON STOCK.TB_FINANCIAL_STMT_INT (STOCK_CODE, BSNS_YEAR)
    LOCAL TABLESPACE USERS;

-- CORP_CODE + BSNS_YEAR + REPRT_CODE 인덱스 (LOCAL)
CREATE INDEX STOCK.IDX_FS_CORP_YEAR_INT
    ON STOCK.TB_FINANCIAL_STMT_INT (CORP_CODE, BSNS_YEAR, REPRT_CODE)
    LOCAL TABLESPACE USERS;

-- ============================================================
-- STEP 5. 중간 동기화 (선택사항 - 재정의 중 추가된 변경분 반영)
-- 재정의 시간이 길 경우 중간에 실행해서 최종 FINISH 시간 단축
-- ============================================================
EXEC DBMS_REDEFINITION.SYNC_INTERIM_TABLE('STOCK', 'TB_FINANCIAL_STMT', 'TB_FINANCIAL_STMT_INT');

-- ============================================================
-- STEP 6. 통계정보 수집 (중간 테이블)
-- ============================================================
EXEC DBMS_STATS.GATHER_TABLE_STATS('STOCK', 'TB_FINANCIAL_STMT_INT', CASCADE=>TRUE, DEGREE=>4);

-- ============================================================
-- STEP 7. 재정의 완료 (테이블 교체 - 수초 소요, 서비스 영향 거의 없음)
-- ============================================================
EXEC DBMS_REDEFINITION.FINISH_REDEF_TABLE('STOCK', 'TB_FINANCIAL_STMT', 'TB_FINANCIAL_STMT_INT');

-- ============================================================
-- STEP 8. 인덱스명 변경 (선택)
-- ============================================================
ALTER INDEX STOCK.IDX_FS_STOCK_INT      RENAME TO IDX_FS_STOCK;
ALTER INDEX STOCK.IDX_FS_CORP_YEAR_INT  RENAME TO IDX_FS_CORP_YEAR;

-- ============================================================
-- STEP 9. 중간 테이블 삭제 (이제 구 테이블이 INT로 바뀌어 있음)
-- ============================================================
DROP TABLE STOCK.TB_FINANCIAL_STMT_INT PURGE;

-- ============================================================
-- STEP 10. 검증
-- ============================================================

-- 건수 확인
SELECT COUNT(*) FROM STOCK.TB_FINANCIAL_STMT;

-- 파티션 현황
SELECT PARTITION_NAME, NUM_ROWS, BLOCKS
FROM ALL_TAB_PARTITIONS
WHERE TABLE_OWNER='STOCK' AND TABLE_NAME='TB_FINANCIAL_STMT'
ORDER BY PARTITION_POSITION;

-- 실행계획: STOCK_CODE 단건 조회 (HASH SINGLE 확인)
EXPLAIN PLAN FOR
SELECT ACCOUNT_ID, SJ_DIV, THSTRM_AMOUNT
FROM STOCK.TB_FINANCIAL_STMT
WHERE STOCK_CODE = '005930';
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- 실행계획: BSNS_YEAR + STOCK_CODE (RANGE SINGLE + HASH SINGLE)
EXPLAIN PLAN FOR
SELECT ACCOUNT_ID, SJ_DIV, THSTRM_AMOUNT
FROM STOCK.TB_FINANCIAL_STMT
WHERE BSNS_YEAR = '2024' AND STOCK_CODE = '005930';
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- 성능 확인: DISTINCT STOCK_CODE
SET TIMING ON
SELECT DISTINCT STOCK_CODE FROM STOCK.TB_FINANCIAL_STMT
WHERE STOCK_CODE IS NOT NULL ORDER BY STOCK_CODE;

-- ============================================================
-- 롤백 (FINISH 전에만 가능)
-- ============================================================
-- EXEC DBMS_REDEFINITION.ABORT_REDEF_TABLE('STOCK', 'TB_FINANCIAL_STMT', 'TB_FINANCIAL_STMT_INT');
-- DROP TABLE STOCK.TB_FINANCIAL_STMT_INT PURGE;
