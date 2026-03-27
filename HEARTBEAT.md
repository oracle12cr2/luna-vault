# HEARTBEAT.md

## OpenClaw 관리
- **다음 업데이트 체크**: 2026-04-04 (2주 주기)
- 명령어: `npm view openclaw version` vs 현재버전 비교

# Add tasks below when you want the agent to check something periodically.

## 2026-03-13 할 일
- [x] 블로그 복구: Oracle에 BLOG_POST 등 테이블 생성 → blog-api/blog-front 재시작 (webserver01/02) — 완료!
- [x] MCP Oracle 서버 디버깅: 코드/설정 모두 없음, 필요시 새로 구축 (스킵 2026-03-21)
- [ ] Oracle DBA 스크립트: oracle-base 388개 다운 완료, 18c 이상 + 공통 스크립트 정리 및 선별 필요
- [x] 미국장 마감 분석 스크립트: 07:00 KST 수집 (완료 2026-03-21, cron 07:00 실행 + 07:05 알림)

## 블로그 리디자인 (2분기 프로젝트: 4~6월)
- [ ] Next.js 프론트 리디자인: 사이드바 레이아웃 (프로필+검색+카테고리 트리)
- [ ] 카테고리 계층구조 + 게시글 수 표시
- [ ] 태그(해시태그) 시스템 추가 (DB 테이블 + API + UI)
- [ ] 본문 스타일: blockquote, 코드블록, 기술 블로그 느낌
- [ ] 레퍼런스: 박영민 Oracle DBA 블로그 (Tistory) 스타일

## 2026-03-31 (월) 할 일
- [ ] 기존 보유종목(ACE200 32주, TIGER 반도체 223주) 처리 방향 결정
- [ ] 예수금 확보 후 데이트레이딩 실전 모의투자 테스트 (09:30 매수 → 14:50 청산)

## Kafka 연동
- [x] Oracle OGG RAC → Kafka → 3Node RAC (Debezium + JDBC Sink, 정상 동작 확인 3/22)
- [ ] PostgreSQL Sink 커넥터 추가 (Oracle → Kafka → PostgreSQL 50.16)
  - Sink 커넥터 생성 완료 (RUNNING), PG 스키마/유저 준비 완료
  - **내일 해야 할 것**: Debezium Source LogMiner CDC 디버깅 (토픽 데이터 0건 문제)
  - Kafka 브로커 meta.properties 재생성으로 복구 완료 (3/23)

## 스터디
- [x] Part 16 파티셔닝 (3/22 완료)
- [ ] Part 18 Oracle 성능분석 기본방법론 (3/29 일요일 예정)
- [ ] Part 19 튜닝 실무 사례

## Exadata VM 시뮬레이션 (대기)
- [ ] VM 구성 (DB 서버 + 스토리지 서버 분리)
- [ ] HCC 압축 테스트, Zone Map, DBRM 등 가능한 기능 실습
- 남궁건 준비되면 시작

## 프로젝트 대기열
- [ ] Luna Dashboard: Jarvis 스타일 개인 AI 대시보드 (Next.js, 다크테마) — 인프라 미니맵 완료 (3/20), 에이전트 회의실 재설계 완료 (3/21)


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