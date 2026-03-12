# HEARTBEAT.md

## OpenClaw 관리
- **다음 업데이트 체크**: 2026-03-16 (2주 주기)
- 명령어: `npm view openclaw version` vs 현재버전 비교

# Add tasks below when you want the agent to check something periodically.

## 2026-03-13 할 일
- [ ] 블로그 복구: Oracle에 BLOG_POST 등 테이블 생성 → blog-api/blog-front 재시작 (webserver01/02)
- [ ] MCP Oracle 서버 디버깅: Claude Desktop 핸드셰이크 disconnected 문제 해결
- [ ] Oracle DBA 스크립트 채워넣기 (oracle-scripts/)

## TODO
- [x] 동행복권 자동 구매 스크립트 개발 (완료 2026-03-05)
- [x] 동행복권 매주 자동 구매 cron 등록 (완료: `0 10 * * 5`, 매주 금요일 10시)
- [x] grid@oracle19c01 SSH 접속 (완료 2026-03-11, 원인: crypto-policies SHA1 disabled → ed25519 키로 해결)

## 2026-03-06 할 일 (내일 아침 알림) - 완료
- [x] 옵시디언 연동: /root/.openclaw/workspace/ 를 옵시디언 Vault로 열기 - 완료 2026-03-07 (GitHub 동기화)
- [x] oracle19cogg02 DB 패치 마무리 (19.23 → 19.30) - 완료 2026-03-08
- [x] RepManager 리포지토리 생성 결과 확인 - 완료 2026-03-08 (Repository 손상됨, 재생성 필요)

## 2026-03-11 할 일
- [x] 모의투자 API 키 발급 (완료 2026-03-11)
- [x] DART 공시 데이터 수집 (완료 2026-03-12, 한도 정상 복구)
- [x] 분봉 자동 수집 crontab 정상 동작 확인 (15:35 분봉 / 16:00 일봉, 정상)
- [x] ETF 백테스트 대시보드 분할매매 전략 차트 보완 (완료 2026-03-12)