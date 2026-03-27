# MEMORY.md - 루나의 장기 기억

## 남궁건
- 한국어 선호, 반말 OK
- 효율적이고 똑똑한 비서 스타일 원함
- 첫 세션: 2026-02-13
- **애플 생태계 우선** — 모든 프로젝트에서 Apple 생태계 고려 (iCloud, CalDAV, Safari, PWA 등)
- 닉네임 "남궁건"으로 통일 (디스코드 포함)

## 설정
- 게이트웨이: local 모드, LAN 바인딩, 포트 18789
- 서버: 2690v4 (Linux, Rocky/RHEL 계열), IP: 192.168.50.56
- Grafana: 192.168.50.56:3000 (admin/rlaxodhks)
- SSH 외부 접속: oracle23cr2.asuscomm.com:3000 → 내부 22

## 인프라 IP (192.168.50.x)
- redis01/02/03: .3/.4/.5
- waserver01/02: .6/.7
- kafka: .9
- webserver01/02: .11/.12
- haproxy: .14
- postgres01: .16
- oracle19c RAC: .21~.29 (SCAN: .27~.29, system/oracle@50.27:1521/PROD)
- oracle19c OGG RAC: .31~.37 (SCAN: .35~.37, app_user/oracle@50.35:1521/PROD)
- oracle19c ADG: .41
- windows: .30
- 호스트 서버(루나): .56
- 맥북 에어(유나): .192

## 블로그
- 도메인: oracle23cr2.asuscomm.com
- 프론트: Next.js, webserver01/02 이중화, PM2 관리, 포트 3001
- API: Fastify, 포트 3000
- DB: Oracle 19c (app_user@50.35:1521/PROD)
- 디자인: velog/dev.to 스타일 적용 완료 (유나 작업, 2026-03-15)
- 관리자: admin/admin1234

## VM 접속 정보
- kto2005 계정 (SSH 키): redis01~03, waserver01~02, webserver01~02, kafka, haproxy
- oracle 계정 (SSH 키): oracle19c01~03, oracle19cogg01~02, oracle19cadg
- 50.56 보안: 비밀번호 인증 OFF, root 로그인 OFF, 키 인증만 허용
- oracle@192.168.50.56 직접 SSH 키 접속 가능 (sudo su 불필요)

## 로또
- 추천 규칙: 5~40 범위만 (1~4, 41~45 제외), 항상 5세트
- 데이터: Google Sheet doc_id 16tt7cSqdts3fObqfC2Q5eYIiwL-k2lFBMUasrzs2UE0
- 메일 발신자: kto2004@naver.com (luna@ 쓰면 네이버 SMTP 거부됨)
- 동행복권 계정: kto2004 / kto8520!@# (⚠️ kto2005 아님!)
- 자동 구매: Selenium + Chrome headless, 모바일 페이지(ol.dhlottery.co.kr) 사용
- 스크립트: /root/.openclaw/workspace/lotto/buy_lotto.py

## Oracle RAC/GI 패치 교훈
- OL9/RHEL9에서 Oracle 19c 패치 시 re-link 실패 주의:
  - shrept.lst 누락 → `touch $GRID_HOME/network/admin/shrept.lst`
  - config.o -fPIC 문제 → `gcc -fPIC -c -o config.o config.c`
  - CHAD(CHADDriver) 프로세스가 라이브러리 잡고 있으면 kill 필요
  - Event Manager 안 돌면 opatchauto가 CRS 인식 못함 → crsctl stop/start crs
- 패치 파일 소유권: `chown -R grid:oinstall /tmp/패치디렉토리` 필수
- zip bomb 오탐: `UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip`
- oracle19cogg01/02: 2노드 RAC, Grid Home: /grid/app/19.0.0/grid, DB Home: /oracle/app/oracle/product/19.0.0/dbhome_1

## Cloud Control 13c — 설치 완료! (2026-03-09)
- OEM 13.5 R5 설치 완료 (50.56, /cloud13cr5/oem)
- gc_inst: /cloud13cr5/gc_inst
- 접속: https://192.168.50.56:7803/em (sysman / Oracle2026_em)
- WLS Admin: https://2690v4:7102 (weblogic)
- DB 리포지토리: oracle19c01:1521/PROD (SYSMAN 스키마)
- 설치 기간: 3/4~3/9 (6일, silent 모드 ConfigureGC.sh)
- 핵심 교훈:
  - response 파일: EM_INSTALL_TYPE="NOSEED" 필수
  - emInstanceMapping.properties 있으면 "home already in use" 에러
  - MGMT_UPGRADEUTIL_TASK phase=8은 "incomplete upgrade" → 삭제 필요
  - SYSMAN122140_* 스키마는 RCU로 별도 생성 (OPSS, IAU, MDS, STB, WLS)
  - OUI 인벤토리 HOME_LIST, ConfigXML 상태도 체크 필요

## 주식/ETF 투자 시스템
- 투자금: 1천만원 (변경: 1억→1천만)
- 한국투자증권 계좌: 화정PB센터에서 모바일 OTP 발급 (2026-03-10)
- KIS OpenAPI 키 발급 완료
- DART API 연동 완료
- 데이터 파이프라인: KIS/DART API → Redis (50.9) → Oracle DB (50.31)
- ETF 백테스트 대시보드: http://192.168.50.56:8501 (Streamlit)
- ETF 포트폴리오: ACE200, KOSDAQ150, TIGER IT, KODEX 고배당/2차전지/레버리지/골드/국고채, TIGER 반도체/은행
- 종목별 최적 전략 (워크포워드 검증 PASS):
  - ACE200 → MA(3/15): OOS +58.2%, 샤프 2.67
  - KODEX레버리지 → MA(3/15): OOS +135.4%, 샤프 2.57
  - TIGER반도체 → RSI(9/30/75): OOS +31.1%, 샤프 1.58
  - KODEX고배당 → MA(7/30): OOS +31.1%, 샤프 2.02
  - KODEX골드 → BB(15/1.5): OOS +11.2%, 샤프 1.73
- 분할매매 최적: MA10/이격5%/매도5%/매수15% (수익률 37.4%, 샤프 0.62)
- 디스코드 알림: #etf-signals 채널 (Luna 서버)
- 스크립트: /usr/local/bin/kis_realtime.py, kis_candle.py, dart_*.py, etf_redis_realtime.py
- 리포트: etf-backtest/reports/ (optimize_report.html, walkforward_report.html)
- 모의투자 API 키 발급 완료 (2026-03-11)
- 모의투자 계좌: 50173951 (ACNT_PRDT_CD: 01)
- 모의투자 자동매매 연동 완료: signal.py → kis_mock_trader.py → KIS 모의투자 API
- 포트폴리오 변경 (2026-03-12): 5종→3종 (KODEX레버리지/ACE200/KODEX고배당, 균등33%)
- 투자자별 매매동향: kis_investor.py (cron 평일 16:10), TB_INVESTOR_TREND
- signal.py 외국인 필터: 5일 중 3일+ 순매도 시 매수 보류
- KODEX 고배당 1차 분할매수: 47주 @ 17,545 (모의투자, 2026-03-12)
- etf_redis_realtime.py: 시뮬레이션→실제 KIS API 전환 완료, RedisCluster 클라이언트 적용
- crontab/shebang: 모든 stock 스크립트 /home/anaconda3/bin/python3 절대경로로 수정
- 교훈: cron 환경에서 #!/usr/bin/env python3은 PATH 문제로 실패 → 절대경로 필수

## 유나 (Yuna) — 동생 AI 비서
- 맥북 에어: 192.168.50.192, 계정 taeoankim
- 플랜: Gamestop $65 Max 5x (별도 계정)
- 구성: OpenClaw + Claude Code
- 역할: 루나 백업 + DB 학습 + 업무 자동화 서포트
- 성격: 따뜻하고 친근, 존댓말 (루나와 차별화)
- GitHub 공유 리포: oracle12cr2/luna-vault
- 로컬 clone: /root/.openclaw/workspace/luna-vault/

## 튜닝 파이프라인 (D:\oracle-sql-tuning, Windows PC)
- Python 기반 SQL 튜닝 자동화 (4단계)
- Phase 1: V$SQL 느린 SQL 감지 → Phase 2: 10046 트레이스 → Phase 3: tkprof 분석 → Phase 4: HTML/Excel 리포트
- 설정: settings.yaml (DB: 50.31 PROD, app_user)
- TODO: 10053 트레이스 수집/분석/엑셀 시트 추가

## 도구
- youtube-transcript-api로 유튜브 자막 추출 가능 (pip install youtube-transcript-api)

## 서버 프롬프트 컬러 (2026-03-11)
- kto2005=🟢초록, oracle=🟡노랑, grid=🔵시안, root=🔴빨강
- RHEL9/OL9: crypto-policies가 ssh-rsa(SHA1) 차단 → ed25519 키 필요

## webserver01/02
- blog-api(Fastify) + blog-front(Next.js): PM2 관리, systemd도 있음
- 2026-03-12: DB 다운 시 무한 재시작 폭주 → PM2 delete + systemd disable로 정리
- BLOG_POST 등 테이블 미존재 — 블로그 재개 시 먼저 생성 필요
- 재시작 폭주가 RAC CPU 상승 + ORA-609 원인이었음

## OGG RAC 교훈 (2026-03-12)
- Heavy swapping → 인스턴스 eviction: 16GB RAM에 DB+ASM+CRS+TFA 과부하
- TFA 혼자 700MB+ RSS: tfactl stop + systemctl disable 필요
- UNDO 충돌: 인스턴스가 다른 노드에서 올라오면 undo_tablespace 재배정 필요
- DB 다운 한 달+ 방치됨 → 자동 모니터링/알림 필수

## 교훈
- 게이트웨이 재시작 시 lock 파일(.gateway.lock) 충돌 주의 — pkill 후 lock 삭제 필요
- plugins.entries.telegram.enabled: false 확인 필요 — 텔레그램 채널과 별개 설정일 수 있음
- ORA-27366 `"".""`(빈 job 이름): scheduler 내부 유령 running 엔트리 → sys.scheduler$_job 직접 UPDATE로 정리
- RHEL9/OL9 SSH: crypto-policies가 ssh-rsa 차단, ed25519 키 사용
