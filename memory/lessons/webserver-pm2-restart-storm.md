---
trigger: "PM2 관리 앱이 DB 다운 시 무한 재시작"
domain: infra
confidence: ✅
created: 2026-03-12
updated: 2026-03-12
---

# PM2 무한 재시작 폭주 → RAC CPU 상승

## 문제
webserver01/02의 blog-api(Fastify)가 Oracle DB 다운 상태에서 무한 재시작 반복
→ RAC CPU 상승 + ORA-609 에러 폭증

## 원인
PM2 기본 설정이 앱 크래시 시 즉시 재시작 → DB 연결 실패로 즉시 크래시 → 무한 루프

## 해결
```bash
pm2 delete blog-api blog-front
systemctl disable blog-api blog-front
```

## 교훈
1. PM2 앱에 `max_restarts`, `min_uptime` 설정 필수
2. DB 의존 앱은 healthcheck + backoff 로직 넣기
3. systemd + PM2 이중 관리 하지 말 것 (하나만 선택)
