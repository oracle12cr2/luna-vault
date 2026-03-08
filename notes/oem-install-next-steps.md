# OEM 설치 - 내일 할 일

## 현재 상황 (2026-03-08 14:02)
- **상태**: Repository 손상으로 설치 실패
- **에러**: "The referenced database doesn't contain a valid Management Repository"
- **Oracle Home**: /cloud13cr5/oem (정상, 재사용 가능)

## 내일 계획

### 1단계: Repository 완전 재생성 (30분)
```bash
# RCU로 기존 스키마 삭제
/cloud13cr5/oem/bin/rcu -silent -dropRepository \
  -databaseType ORACLE -connectString oracle19c01:1521/PROD \
  -dbUser sys -dbRole sysdba -useSamePasswordForAllSchemaUsers true \
  -schemaPassword Oracle123! -component SYSMAN

# 새 스키마 생성
/cloud13cr5/oem/bin/rcu -silent -createRepository \
  -databaseType ORACLE -connectString oracle19c01:1521/PROD \
  -dbUser sys -dbRole sysdba -useSamePasswordForAllSchemaUsers true \
  -schemaPassword Oracle123! -component SYSMAN
```

### 2단계: Response 파일 수정
- EM_INSTALL_TYPE="NOSEED" → "INSTALL"
- 깨끗한 설치로 변경

### 3단계: 새로운 설치
```bash
/cloud13cr5/oem/sysman/install/ConfigureGC.sh -silent -responseFile /cloud13cr5/em13500.rsp
```

## 예상 소요시간
- 총 1.5-2시간
- Repository 재생성: 30분
- OMS 설치: 60-90분

## 백업된 파일들
- /cloud13cr5/em13500.rsp (Response 파일)
- /cloud13cr5/oem/ (Oracle Home)
- 패치된 omsca 스크립트: /tmp/patch_omsca.sh

## 성공 확률
- **높음** (90%+)
- Repository 문제만 해결하면 나머지는 검증됨