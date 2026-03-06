-- ============================================================
-- RAC Memory Sizing Script (ASMM Mode)
-- Target: PROD RAC 3-Node (VM Memory 16GB)
-- Author: Luna
-- ============================================================

SET SERVEROUTPUT ON

DECLARE
  PS_MEMORY            NUMBER := 16;  -- VM 물리 메모리 (GB)
  SGA                  NUMBER;
  PGA                  NUMBER;
  SGA_MAX_SIZE         NUMBER;
  DB_CACHE_SIZE        NUMBER;
  PGA_AGGREGATE_TARGET NUMBER;
  SHARED_POOL_SIZE     NUMBER;
  JAVA_POOL_SIZE       NUMBER;
  LARGE_POOL_SIZE      NUMBER;
  SHARED_POOL_RESERVED_SIZE NUMBER;
  v_name  VARCHAR2(30);
  v_value VARCHAR2(512);

  CURSOR SGA_VALUE_CUR IS
    SELECT NAME, VALUE
    FROM   v$parameter
    WHERE  NAME IN (
      'memory_target', 'memory_max_target',
      'sga_max_size', 'sga_target',
      'shared_pool_size', 'large_pool_size',
      'java_pool_size', 'streams_pool_size',
      'lock_sga', 'shared_pool_reserved_size',
      'db_cache_size', 'pga_aggregate_target'
    )
    ORDER BY NAME;
BEGIN
  -- ======================== Calculation ==============================
  SGA := ROUND(PS_MEMORY * 0.35 * 1024);  -- 5734M

  IF PS_MEMORY <= 12 THEN
    PGA := ROUND(PS_MEMORY * 0.1 * 1024);
    DB_CACHE_SIZE := ROUND(SGA * 0.55);
    SHARED_POOL_SIZE := ROUND(SGA * 0.3);
  ELSIF PS_MEMORY > 12 AND PS_MEMORY <= 20 THEN
    PGA := ROUND(PS_MEMORY * 0.15 * 1024);
    DB_CACHE_SIZE := ROUND(SGA * 0.6);
    SHARED_POOL_SIZE := ROUND(SGA * 0.3);
  ELSIF PS_MEMORY > 20 AND PS_MEMORY <= 48 THEN
    PGA := ROUND(PS_MEMORY * 0.2 * 1024);
    DB_CACHE_SIZE := ROUND(SGA * 0.65);
    SHARED_POOL_SIZE := ROUND(SGA * 0.25);
  ELSIF PS_MEMORY > 48 AND PS_MEMORY <= 96 THEN
    PGA := ROUND(PS_MEMORY * 0.2 * 1024);
    DB_CACHE_SIZE := ROUND(SGA * 0.65);
    SHARED_POOL_SIZE := ROUND(SGA * 0.25);
  ELSIF PS_MEMORY > 96 THEN
    PGA := ROUND(PS_MEMORY * 0.2 * 1024);
    DB_CACHE_SIZE := ROUND(SGA * 0.7);
    SHARED_POOL_SIZE := ROUND(SGA * 0.2);
  END IF;

  SGA_MAX_SIZE := SGA;
  PGA_AGGREGATE_TARGET := PGA;
  JAVA_POOL_SIZE := ROUND(SGA * 0.015);
  LARGE_POOL_SIZE := ROUND(SGA * 0.035);
  SHARED_POOL_RESERVED_SIZE := ROUND(SGA * 0.025);

  -- ======================== 현재 설정 확인 ==============================
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');
  DBMS_OUTPUT.PUT_LINE('-- Current Settings (Before Change)');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');

  OPEN SGA_VALUE_CUR;
  LOOP
    FETCH SGA_VALUE_CUR INTO v_name, v_value;
    EXIT WHEN SGA_VALUE_CUR%NOTFOUND;
    DBMS_OUTPUT.PUT_LINE('-- ' || RPAD(v_name, 35) || ' = ' || v_value);
  END LOOP;
  CLOSE SGA_VALUE_CUR;

  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');
  DBMS_OUTPUT.PUT_LINE('-- Calculated Values (PS_MEMORY = ' || PS_MEMORY || 'GB)');
  DBMS_OUTPUT.PUT_LINE('-- SGA Total  : ' || SGA_MAX_SIZE || 'M');
  DBMS_OUTPUT.PUT_LINE('-- PGA Target : ' || PGA_AGGREGATE_TARGET || 'M');
  DBMS_OUTPUT.PUT_LINE('-- DB Cache   : ' || DB_CACHE_SIZE || 'M');
  DBMS_OUTPUT.PUT_LINE('-- Shared Pool: ' || SHARED_POOL_SIZE || 'M');
  DBMS_OUTPUT.PUT_LINE('-- Java Pool  : ' || JAVA_POOL_SIZE || 'M');
  DBMS_OUTPUT.PUT_LINE('-- Large Pool : ' || LARGE_POOL_SIZE || 'M');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');

  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');
  DBMS_OUTPUT.PUT_LINE('-- ALTER SYSTEM Commands (SPFILE - Restart Required)');
  DBMS_OUTPUT.PUT_LINE('-- RAC: AMM(memory_target) OFF -> ASMM(sga_target) ON');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');

  -- Disable AMM (ASMM recommended for RAC)
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET memory_target = 0 SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET memory_max_target = 0 SCOPE=SPFILE;');

  -- ASMM Settings
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET sga_max_size = ' || SGA_MAX_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET sga_target = ' || SGA_MAX_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET db_cache_size = ' || DB_CACHE_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET shared_pool_size = ' || SHARED_POOL_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET java_pool_size = ' || JAVA_POOL_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET large_pool_size = ' || LARGE_POOL_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET shared_pool_reserved_size = ' || SHARED_POOL_RESERVED_SIZE || 'M SCOPE=SPFILE;');
  DBMS_OUTPUT.PUT_LINE('ALTER SYSTEM SET pga_aggregate_target = ' || PGA_AGGREGATE_TARGET || 'M SCOPE=SPFILE;');

  DBMS_OUTPUT.PUT_LINE('');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');
  DBMS_OUTPUT.PUT_LINE('-- RAC Rolling Restart After Apply');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');
  DBMS_OUTPUT.PUT_LINE('-- srvctl stop instance -d PROD -i PROD3 -o immediate');
  DBMS_OUTPUT.PUT_LINE('-- srvctl start instance -d PROD -i PROD3');
  DBMS_OUTPUT.PUT_LINE('-- srvctl stop instance -d PROD -i PROD2 -o immediate');
  DBMS_OUTPUT.PUT_LINE('-- srvctl start instance -d PROD -i PROD2');
  DBMS_OUTPUT.PUT_LINE('-- srvctl stop instance -d PROD -i PROD1 -o immediate');
  DBMS_OUTPUT.PUT_LINE('-- srvctl start instance -d PROD -i PROD1');
  DBMS_OUTPUT.PUT_LINE('-- ============================================================');

END;
/
