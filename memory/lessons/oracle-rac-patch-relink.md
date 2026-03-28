---
trigger: "OL9/RHEL9에서 Oracle 19c 패치 시 re-link 실패"
domain: oracle
confidence: ✅
created: 2026-03-08
updated: 2026-03-08
---

# Oracle RAC/GI 패치 re-link 실패 대응

## 문제
OL9/RHEL9 환경에서 Oracle 19c 패치 적용 시 re-link 단계에서 여러 에러 발생

## 원인
RHEL9 변경사항 (crypto-policies, gcc 기본 옵션 등)과 Oracle 19c 호환성 문제

## 해결
1. `shrept.lst` 누락 → `touch $GRID_HOME/network/admin/shrept.lst`
2. `config.o -fPIC` 문제 → `gcc -fPIC -c -o config.o config.c`
3. CHAD(CHADDriver) 프로세스가 라이브러리 잡고 있으면 → `kill` 필요
4. Event Manager 안 돌면 opatchauto가 CRS 인식 못함 → `crsctl stop/start crs`
5. 패치 파일 소유권: `chown -R grid:oinstall /tmp/패치디렉토리` 필수
6. zip bomb 오탐: `UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip`

## 교훈
RHEL9 계열에서 Oracle 패치는 항상 re-link 이슈 각오하고, 위 체크리스트 미리 준비
