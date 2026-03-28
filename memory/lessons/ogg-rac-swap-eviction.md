---
trigger: "Oracle RAC 노드에서 인스턴스가 갑자기 eviction"
domain: oracle
confidence: ✅
created: 2026-03-12
updated: 2026-03-12
---

# OGG RAC Heavy Swapping → 인스턴스 Eviction

## 문제
16GB RAM 서버에서 Oracle DB + ASM + CRS + TFA 동시 실행 → 메모리 부족 → 인스턴스 eviction

## 원인
- TFA 혼자 700MB+ RSS 차지
- 16GB에 DB+ASM+CRS+TFA는 과부하

## 해결
```bash
tfactl stop
systemctl disable oracle-tfa
```
UNDO 충돌 시: 인스턴스가 다른 노드에서 올라오면 `undo_tablespace` 재배정 필요

## 교훈
1. TFA는 메모리 부족 환경에서 반드시 비활성화
2. 16GB RAC 노드는 항상 스왑 모니터링 필수
3. DB 장기 다운 방치 금지 → 자동 모니터링/알림 설정
