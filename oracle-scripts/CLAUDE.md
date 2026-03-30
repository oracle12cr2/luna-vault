# Oracle 스크립트 디렉토리

## 목적
Oracle 19c RAC 관리, 모니터링, 튜닝 스크립트

## 접속 정보
- Oracle 19c RAC (메인): system/oracle@192.168.50.27:1521/PROD
- Oracle 19c OGG RAC: app_user/oracle@192.168.50.35:1521/PROD
- Oracle 19c ADG: 192.168.50.41

## 주의사항
- RAC 패치 시 shrept.lst 누락 주의 → touch $GRID_HOME/network/admin/shrept.lst
- OL9/RHEL9: crypto-policies가 ssh-rsa 차단 → ed25519 키 사용
- TFA는 RAM 많이 씀 → 필요시 tfactl stop

## Cloud Control 13c
- URL: https://192.168.50.56:7803/em (sysman / Oracle2026_em)
- DB 리포지토리: oracle19c01:1521/PROD
