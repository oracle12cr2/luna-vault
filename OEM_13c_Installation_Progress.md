# OEM 13c Release 5 Installation Progress

## 목표
Oracle Enterprise Manager Cloud Control 13c Release 5 설치
- 서버: 192.168.50.56 (hostname: 2690v4)
- OMS home: `/cloud13cr5/oem`
- Agent home: `/cloud13cr5/agent`
- DB: 3-node RAC (PROD service, oracle19c01/02/03)

## 현재 상태 (2026-03-07 23:00)

### ✅ 진행 중: SchemaManager로 SYSMAN 리포지토리 생성
**시작**: 2026-03-07 20:44
**상태**: 정상 진행 중 (Java 프로세스 2개 활성)
**로그 크기**: 590MB (활발한 SQL 실행 중)
**현재 단계**: RAC database post-creation SQL
**예상 완료**: 내일 오전 (원래 17시간 소요)

```bash
# 모니터링 명령어
ps -ef | grep "[j]ava.*EMSchema\|[p]erl.*schemamanager" | grep -v grep
tail -f /tmp/schemamanager_output5.log
tail -f /cloud13cr5/oem/sysman/log/schemamanager/m_030726_0844_PM/m_030726_0844_PM.CREATE/logs/em_repos_config.log
```

### 🔧 오늘 해결한 핵심 문제

#### 1. RepManager 버그 발견 및 패치
- `emrepmgr.pl`에서 `GRANT DBA TO $EM_REPOS_USER` 누락
- 1337라인에 grants 호출 추가로 해결

#### 2. OEM 13c R5 SQL 구조 변화
- 기존 monolithic `*_cre.sql` → 서브디렉토리별 개별 스크립트
- RepManager와 호환성 문제 발생

#### 3. 풀 인스톨러 silent 모드 버그
- **문제**: `-silent` 모드에서 소프트웨어 설치 단계 건너뜀
- **원인**: 3/4 원래 설치는 GUI 모드였음 (`s_silent=false`)
- **시도**: xvfb-run, DISPLAY 설정 등 모두 실패

#### 4. 최종 해결책: SchemaManager 직접 실행
- **도구**: `/cloud13cr5/oem/sysman/admin/emdrep/bin/schemamanager.pl`
- **핵심**: `COMMON_COMPONENTS_HOME=/cloud13cr5/oem/oracle_common` 환경변수 필수
- **방법**: RCU를 내부적으로 사용하여 SYSMAN 리포지토리 생성

## 이전 시도들 (실패)

### RepManager (emrepmgr.pl)
- **시도 #1-5**: 권한, 패스워드, 환경 문제들 해결
- **시도 #6**: SYSMAN 생성 성공하나 schema 생성 실패 (SQL 구조 변화)

### ConfigureGC.sh  
- **문제**: 기존 SYSMAN 리포지토리 필요 (재구성 도구일 뿐)
- **시도**: 수동 SYSMAN + RCU 스키마 생성 → PL/SQL 패키지 부족으로 실패

### 풀 인스톨러 (em13500_linux64.bin)
- **Silent 모드**: validation만 하고 설치 건너뜀
- **GUI 모드**: xvfb-run으로 시도하나 클릭 대기로 멈춤

## 환경 설정

### 필수 환경 변수 (SchemaManager)
```bash
export ORACLE_HOME=/cloud13cr5/oem
export MW_HOME=/cloud13cr5/oem
export COMMON_COMPONENTS_HOME=/cloud13cr5/oem/oracle_common  # 핵심!
export JAVA_HOME=$ORACLE_HOME/oracle_common/jdk
export PERL5LIB=$ORACLE_HOME/sysman/admin/emdrep/bin:$ORACLE_HOME/sysman/install:$ORACLE_HOME/perl/lib
```

### DB 연결
```
(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=oracle19c01)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=PROD)))
```

### 비밀번호
- SYS: `oracle`
- SYSMAN/weblogic/nodemanager/agent: `Oracle2026_em`

## 다음 단계

### 1. SchemaManager 완료 대기
- **모니터링**: 로그 크기 및 최신 타임스탬프 확인
- **완료 신호**: "Repository Creation Utility - Create - Success" 메시지

### 2. ConfigureGC.sh 실행
SchemaManager 완료 후 OMS 구성:
```bash
cd /cloud13cr5/oem
./sysman/install/ConfigureGC.sh
```

### 3. 검증
- OMS 상태 확인: `/cloud13cr5/oem/bin/emctl status oms`
- 웹 접속: https://2690v4:7802/em
- Agent 상태: `/cloud13cr5/agent/agent_13.5.0.0.0/bin/emctl status agent`

## 주요 로그 위치
- **SchemaManager 메인**: `/tmp/schemamanager_output5.log`
- **RCU 상세**: `/cloud13cr5/oem/sysman/log/schemamanager/m_030726_0844_PM/`
- **이전 시도들**: `/tmp/emrepmgr_create*.log`, `/tmp/configureGC_output*.log`

## 백업된 파일
- RepManager 백업: `/cloud13cr5/oem/sysman/admin/emdrep/bin/10.1/emrepmgr.pl.bak`
- 구 홈: `/cloud13cr5/oem_old`, `/cloud13cr5/agent_old` (필요시 복원용)

---
**마지막 업데이트**: 2026-03-07 23:00 KST
**작업자**: 루나 🌙