---
trigger: "Cloud Control 13c 설치 시 반복 실패"
domain: oracle
confidence: ✅
created: 2026-03-09
updated: 2026-03-09
---

# OEM 13c Silent 설치 핵심 체크리스트

## 문제
OEM 13.5 R5 설치가 여러 이유로 반복 실패 (6일 소요)

## 해결 & 체크리스트
1. response 파일: `EM_INSTALL_TYPE="NOSEED"` 필수
2. `emInstanceMapping.properties` 있으면 "home already in use" 에러 → 삭제
3. `MGMT_UPGRADEUTIL_TASK phase=8`은 "incomplete upgrade" → 관련 스키마 삭제 필요
4. `SYSMAN122140_*` 스키마는 RCU로 별도 생성 (OPSS, IAU, MDS, STB, WLS)
5. OUI 인벤토리 HOME_LIST, ConfigXML 상태 체크

## 교훈
OEM 설치는 한 번에 안 된다고 가정하고, 각 phase별 롤백 포인트 확보해둘 것.
