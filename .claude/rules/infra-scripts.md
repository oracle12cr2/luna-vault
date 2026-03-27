---
globs: ["scripts/**/*.sh", "scripts/**", "**/*.sh"]
---

# 인프라 스크립트 규칙

## 서버 정보
- 호스트: 192.168.50.56 (Rocky Linux 9)
- SSH 키 인증만 허용 (비밀번호 OFF)
- kto2005 계정: redis, waserver, webserver, kafka, haproxy
- oracle 계정: oracle19c01~03, oracle19cogg01~02, oracle19cadg

## 쉘 스크립트 규칙
- bash 사용 (#!/bin/bash)
- set -euo pipefail 권장
- 로그 출력 포함
- 파괴적 명령(rm, drop 등)은 확인 후 실행

## 모니터링
- Grafana: 192.168.50.56:3000
- OEM 13.5: https://192.168.50.56:7803/em
- TFA 주의: RSS 700MB+ 먹으므로 필요시만 활성화

## VM 관리
- RAC 노드: 메모리 16GB 한계, TFA/불필요 서비스 OFF 유지
- DB 다운 감지 → 자동 알림 필수
