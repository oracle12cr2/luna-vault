# 실습: DBMS_FILE_TRANSFER (ASM 환경)

> 📖 Oracle 19c RAC + ASM 환경 기준
> 🏗️ 소스: oracle19cogg RAC (50.31~37) / 타겟: oracle19c RAC (50.21~29)
> 📝 정리: 유나 (2026-03-24)

---

## 실습 목표

ASM 환경에서 DBMS_FILE_TRANSFER를 사용해 데이터파일을 DB Link로 전송하고,
TTS(Transportable Tablespace) 조합으로 테이블스페이스를 이관한다.

---

## 사전 환경 확인

### ASM 디스크그룹 확인

```sql
-- 양쪽 DB에서 실행
SELECT name, state, type, total_mb, free_mb,
       ROUND((1 - free_mb/total_mb) * 100, 1) AS used_pct
  FROM V$ASM_DISKGROUP;
```

### 현재 데이터파일 위치 확인

```sql
-- ASM 경로 확인
SELECT tablespace_name, file_name, bytes/1024/1024 AS mb
  FROM DBA_DATA_FILES
 ORDER BY tablespace_name;
```

---

## Part 1. COPY_FILE — 같은 서버 내 ASM 복사

> ASM ↔ ASM, ASM ↔ 파일시스템 간 복사 가능

### 1-1. 디렉토리 오브젝트 생성

```sql
-- ASM 디렉토리 오브젝트 (ASM 경로 직접 지정)
-- ⚠️ ASM 경로는 '+디스크그룹명/DB명/DATAFILE' 형태
CREATE OR REPLACE DIRECTORY ASM_DATA_DIR AS '+DATA';
GRANT READ, WRITE ON DIRECTORY ASM_DATA_DIR TO system;

-- 파일시스템 디렉토리 (백업/스테이징 용도)
CREATE OR REPLACE DIRECTORY FS_STAGE_DIR AS '/tmp/dbf_stage';
GRANT READ, WRITE ON DIRECTORY FS_STAGE_DIR TO system;
```

```bash
# OS에서 스테이징 디렉토리 생성 (oracle 유저)
mkdir -p /tmp/dbf_stage
chown oracle:oinstall /tmp/dbf_stage
```

### 1-2. 테스트용 테이블스페이스 생성

```sql
-- 테스트용 소규모 테이블스페이스 (ASM에 생성)
CREATE TABLESPACE TBS_XFER_TEST
  DATAFILE '+DATA' SIZE 50M
  AUTOEXTEND OFF;

-- 테스트 테이블 생성 & 데이터 입력
CREATE TABLE system.xfer_test_tbl TABLESPACE TBS_XFER_TEST AS
SELECT level AS id,
       'TEST_DATA_' || level AS name,
       SYSDATE - MOD(level, 365) AS created_dt,
       DBMS_RANDOM.STRING('A', 100) AS description
  FROM DUAL
CONNECT BY level <= 100000;

-- 건수 확인
SELECT COUNT(*) FROM system.xfer_test_tbl;
```

### 1-3. 데이터파일명 확인

```sql
-- ASM 내 실제 파일명 확인
SELECT file_name FROM DBA_DATA_FILES
 WHERE tablespace_name = 'TBS_XFER_TEST';
-- 예: +DATA/PROD/DATAFILE/tbs_xfer_test.280.1234567
```

### 1-4. ASM → 파일시스템 복사

```sql
-- ASM에서 파일시스템으로 복사
-- ⚠️ source_file_name에는 ASM 전체 경로에서 '+DATA/' 이후 부분 입력
BEGIN
  DBMS_FILE_TRANSFER.COPY_FILE(
    source_directory_object      => 'ASM_DATA_DIR',
    source_file_name             => 'PROD/DATAFILE/tbs_xfer_test.280.1234567',  -- 실제 경로로 변경
    destination_directory_object => 'FS_STAGE_DIR',
    destination_file_name        => 'tbs_xfer_test.dbf'
  );
END;
/
```

```bash
# 파일 복사 확인
ls -lh /tmp/dbf_stage/tbs_xfer_test.dbf
```

### 1-5. 파일시스템 → ASM 복사 (역방향)

```sql
BEGIN
  DBMS_FILE_TRANSFER.COPY_FILE(
    source_directory_object      => 'FS_STAGE_DIR',
    source_file_name             => 'tbs_xfer_test.dbf',
    destination_directory_object => 'ASM_DATA_DIR',
    destination_file_name        => 'tbs_xfer_test_copy.dbf'
  );
END;
/
```

```bash
# ASM에서 확인 (grid 유저)
asmcmd ls -l +DATA/PROD/DATAFILE/tbs_xfer_test*
```

---

## Part 2. GET_FILE — 리모트 DB에서 데이터파일 가져오기

> DB Link를 통해 소스 DB의 ASM 데이터파일을 타겟 DB로 직접 전송

### 2-1. 소스 DB 준비 (oracle19cogg — 50.35)

```sql
-- 소스 DB에서 디렉토리 오브젝트 생성
CREATE OR REPLACE DIRECTORY SRC_ASM_DIR AS '+DATA';
GRANT READ, WRITE ON DIRECTORY SRC_ASM_DIR TO system;

-- 테스트 테이블스페이스가 없으면 생성 (Part 1과 동일)
-- (이미 있으면 스킵)
```

### 2-2. 타겟 DB 준비 (oracle19c — 50.27)

```sql
-- 타겟 DB에서 디렉토리 오브젝트 생성
CREATE OR REPLACE DIRECTORY TGT_ASM_DIR AS '+DATA';
GRANT READ, WRITE ON DIRECTORY TGT_ASM_DIR TO system;

-- 파일시스템 스테이징 (TTS 덤프파일 수신용)
CREATE OR REPLACE DIRECTORY TGT_STAGE_DIR AS '/tmp/dbf_stage';
GRANT READ, WRITE ON DIRECTORY TGT_STAGE_DIR TO system;

-- 소스 DB로의 DB Link 생성
CREATE DATABASE LINK ogg_link
  CONNECT TO system IDENTIFIED BY oracle
  USING '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.50.35)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=PROD)))';

-- DB Link 테스트
SELECT * FROM DUAL@ogg_link;
```

### 2-3. 소스에서 테이블스페이스 READ ONLY 전환

```sql
-- 소스 DB (50.35) 에서 실행
ALTER TABLESPACE TBS_XFER_TEST READ ONLY;

-- 상태 확인
SELECT tablespace_name, status FROM DBA_TABLESPACES
 WHERE tablespace_name = 'TBS_XFER_TEST';
```

### 2-4. 데이터파일 전송 (GET_FILE)

```sql
-- 타겟 DB (50.27) 에서 실행
-- 소스 ASM의 데이터파일을 타겟 ASM으로 직접 전송
BEGIN
  DBMS_FILE_TRANSFER.GET_FILE(
    source_directory_object      => 'SRC_ASM_DIR',
    source_file_name             => 'PROD/DATAFILE/tbs_xfer_test.280.1234567',  -- 소스 실제 경로
    source_database              => 'ogg_link',
    destination_directory_object => 'TGT_ASM_DIR',
    destination_file_name        => 'tbs_xfer_test.dbf'
  );
END;
/
```

### 2-5. 전송 모니터링

```sql
-- 타겟 DB에서 전송 진행률 확인
SELECT sid, serial#, opname, sofar, totalwork,
       ROUND(sofar/NULLIF(totalwork, 0) * 100, 2) AS pct_done,
       time_remaining AS remain_sec
  FROM V$SESSION_LONGOPS
 WHERE opname LIKE '%FILE_TRANSFER%'
   AND sofar < totalwork;
```

---

## Part 3. TTS + DBMS_FILE_TRANSFER 조합 — 전체 시나리오

> 대용량 테이블스페이스를 ASM 환경에서 완전 이관하는 실전 시나리오

### 3-1. 이관 가능 여부 사전 체크

```sql
-- 소스 DB에서 실행
-- Self-contained 검증 (다른 TS 의존성 없는지 확인)
EXEC DBMS_TTS.TRANSPORT_SET_CHECK('TBS_XFER_TEST', TRUE);

SELECT * FROM TRANSPORT_SET_VIOLATIONS;
-- 결과가 없으면 이관 가능
```

```sql
-- 플랫폼 호환성 확인 (양쪽 DB에서)
SELECT platform_id, platform_name, endian_format
  FROM V$TRANSPORTABLE_PLATFORM
 WHERE platform_name LIKE '%Linux%';
-- 같은 endian이면 변환 불필요
```

### 3-2. 메타데이터 Export (소스)

```bash
# 소스 DB 서버 (50.35) 에서 실행
# 테이블스페이스가 READ ONLY 상태인지 확인 후 진행

expdp system/oracle \
  TRANSPORT_TABLESPACES=TBS_XFER_TEST \
  DIRECTORY=SRC_ASM_DIR \
  DUMPFILE=tts_xfer_test.dmp \
  LOGFILE=tts_xfer_test_exp.log
```

> ⚠️ DIRECTORY가 ASM이면 덤프파일도 ASM에 생성됨.
> 파일시스템에 생성하고 싶으면 별도 디렉토리 오브젝트 사용:

```bash
# 파일시스템 디렉토리 사용 버전
expdp system/oracle \
  TRANSPORT_TABLESPACES=TBS_XFER_TEST \
  DIRECTORY=FS_STAGE_DIR \
  DUMPFILE=tts_xfer_test.dmp \
  LOGFILE=tts_xfer_test_exp.log
```

### 3-3. 데이터파일 + 덤프파일 전송 (타겟에서 GET_FILE)

```sql
-- 타겟 DB (50.27) 에서 실행

-- ① 데이터파일 전송 (ASM → ASM)
BEGIN
  DBMS_FILE_TRANSFER.GET_FILE(
    source_directory_object      => 'SRC_ASM_DIR',
    source_file_name             => 'PROD/DATAFILE/tbs_xfer_test.280.1234567',
    source_database              => 'ogg_link',
    destination_directory_object => 'TGT_ASM_DIR',
    destination_file_name        => 'tbs_xfer_test.dbf'
  );
END;
/

-- ② 덤프파일 전송 (파일시스템 → 파일시스템)
-- 소스에 FS 디렉토리 오브젝트가 있어야 함
BEGIN
  DBMS_FILE_TRANSFER.GET_FILE(
    source_directory_object      => 'FS_STAGE_DIR',     -- 소스의 파일시스템 디렉토리
    source_file_name             => 'tts_xfer_test.dmp',
    source_database              => 'ogg_link',
    destination_directory_object => 'TGT_STAGE_DIR',
    destination_file_name        => 'tts_xfer_test.dmp'
  );
END;
/
```

### 3-4. 메타데이터 Import (타겟)

```bash
# 타겟 DB 서버 (50.27) 에서 실행
# ASM 내 데이터파일 경로 확인 후 진행

impdp system/oracle \
  TRANSPORT_DATAFILES='+DATA/tbs_xfer_test.dbf' \
  DIRECTORY=TGT_STAGE_DIR \
  DUMPFILE=tts_xfer_test.dmp \
  LOGFILE=tts_xfer_test_imp.log
```

### 3-5. 이관 완료 확인

```sql
-- 타겟 DB에서 실행

-- 테이블스페이스 확인
SELECT tablespace_name, status FROM DBA_TABLESPACES
 WHERE tablespace_name = 'TBS_XFER_TEST';

-- READ WRITE로 전환
ALTER TABLESPACE TBS_XFER_TEST READ WRITE;

-- 데이터 검증
SELECT COUNT(*) FROM system.xfer_test_tbl;
-- 소스와 동일한 건수(100,000) 확인

-- 데이터 무결성 체크 (샘플)
SELECT * FROM system.xfer_test_tbl WHERE ROWNUM <= 5;
```

### 3-6. 소스 DB 원복

```sql
-- 소스 DB에서 READ WRITE로 복원
ALTER TABLESPACE TBS_XFER_TEST READ WRITE;
```

---

## Part 4. 병렬 전송 (여러 데이터파일)

> 대용량 테이블스페이스에 데이터파일이 여러 개일 때

### DBMS_SCHEDULER로 병렬 GET_FILE

```sql
-- 타겟 DB에서 실행
-- 소스의 데이터파일 목록 조회 후 병렬 전송

DECLARE
  v_job_name VARCHAR2(30);
  v_idx      NUMBER := 0;
BEGIN
  FOR rec IN (
    SELECT file_name
      FROM DBA_DATA_FILES@ogg_link
     WHERE tablespace_name = 'TBS_XFER_TEST'
  ) LOOP
    v_idx := v_idx + 1;
    v_job_name := 'XFER_JOB_' || v_idx;

    -- ASM 경로에서 +DATA/ 이후 부분 추출
    -- 예: +DATA/PROD/DATAFILE/file.123.456 → PROD/DATAFILE/file.123.456
    DBMS_SCHEDULER.CREATE_JOB(
      job_name   => v_job_name,
      job_type   => 'PLSQL_BLOCK',
      job_action => 'BEGIN DBMS_FILE_TRANSFER.GET_FILE(' ||
                    '''SRC_ASM_DIR'', ' ||
                    '''' || SUBSTR(rec.file_name, INSTR(rec.file_name, '/', 1, 1) + 1) || ''', ' ||
                    '''ogg_link'', ' ||
                    '''TGT_ASM_DIR'', ' ||
                    '''xfer_' || v_idx || '.dbf''); ' ||
                    'END;',
      enabled    => TRUE
    );

    DBMS_OUTPUT.PUT_LINE('Submitted: ' || v_job_name || ' → ' || rec.file_name);
  END LOOP;
END;
/
```

```sql
-- 병렬 전송 진행 모니터링
SELECT job_name, state, run_duration, additional_info
  FROM DBA_SCHEDULER_JOB_RUN_DETAILS
 WHERE job_name LIKE 'XFER_JOB_%'
 ORDER BY actual_start_date DESC;
```

---

## Part 5. 정리 (실습 후 클린업)

```sql
-- 타겟 DB
DROP TABLE system.xfer_test_tbl PURGE;
DROP TABLESPACE TBS_XFER_TEST INCLUDING CONTENTS AND DATAFILES;
DROP DIRECTORY TGT_ASM_DIR;
DROP DIRECTORY TGT_STAGE_DIR;
DROP DATABASE LINK ogg_link;

-- 소스 DB
DROP TABLE system.xfer_test_tbl PURGE;
DROP TABLESPACE TBS_XFER_TEST INCLUDING CONTENTS AND DATAFILES;
DROP DIRECTORY SRC_ASM_DIR;
DROP DIRECTORY FS_STAGE_DIR;
```

```bash
# 파일시스템 스테이징 정리
rm -rf /tmp/dbf_stage
```

---

## 트러블슈팅

| 에러 | 원인 | 해결 |
|------|------|------|
| ORA-19505: failed to identify file | ASM 파일명 잘못 지정 | `asmcmd ls -l +DATA/PROD/DATAFILE/` 로 정확한 경로 확인 |
| ORA-19563: header validation failed | 소스 파일이 사용 중 | 테이블스페이스 READ ONLY 전환 후 재시도 |
| ORA-17628: Oracle error 19505 | 디렉토리 오브젝트 경로 불일치 | ASM은 `+DATA`, 파일시스템은 실제 OS 경로 |
| ORA-02085: database link connects to target | 자기 자신에게 DB Link | 타겟 → 소스 방향으로 DB Link 생성 확인 |
| ORA-15001: diskgroup not found | ASM 디렉토리 경로 오류 | `+DATA` 형태로 디스크그룹명만 지정 |
| 전송 속도 느림 | SQL*Net 대역폭 | SDU 파라미터 조정 (tnsnames.ora에 `SDU=65535`) |

### SDU 튜닝 (전송 속도 개선)

```
# tnsnames.ora — 양쪽 모두 설정
SOURCE_TNS =
  (DESCRIPTION=
    (SDU=65535)
    (ADDRESS=(PROTOCOL=TCP)(HOST=192.168.50.35)(PORT=1521))
    (CONNECT_DATA=(SERVICE_NAME=PROD))
  )
```

---

## 핵심 정리

| 항목 | 내용 |
|------|------|
| **ASM 디렉토리** | `CREATE DIRECTORY xxx AS '+DATA'` (디스크그룹명만) |
| **ASM 파일명** | `+DATA/` 이후 부분만 source_file_name에 지정 |
| **ASM → 파일시스템** | COPY_FILE로 가능 (백업/스테이징 용도) |
| **ASM → 리모트 ASM** | GET_FILE/PUT_FILE + DB Link |
| **TTS 조합** | READ ONLY → expdp → GET_FILE → impdp → READ WRITE |
| **병렬 전송** | DBMS_SCHEDULER로 여러 데이터파일 동시 전송 |
| **속도 튜닝** | SDU=65535 설정으로 SQL*Net 패킷 크기 증가 |
