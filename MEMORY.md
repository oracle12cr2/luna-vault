# MEMORY.md - 루나의 장기 기억

## 남궁건
- 한국어 선호, 반말 OK
- 효율적이고 똑똑한 비서 스타일 원함
- 첫 세션: 2026-02-13

## 설정
- 텔레그램 봇: @ora19cbot
- 게이트웨이: local 모드, LAN 바인딩, 포트 18789
- 서버: 2690v4 (Linux, Rocky/RHEL 계열), IP: 192.168.50.56
- Grafana: 192.168.50.56:3000 (admin/rlaxodhks)
- SSH 외부 접속: oracle23cr2.asuscomm.com:3000 → 내부 22

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
- RSI 최적 파라미터: 기간12, 과매도11, 과매수55 (수익률 11.4%, DD -1.7%)
- 분할매매 전략 추가: 이평선 기준 오르면 일부 매도(수익실현), 내리면 분할매수
- 스크립트: /usr/local/bin/kis_realtime.py, kis_candle.py, dart_*.py, etf_redis_realtime.py
- 다음 단계: 자동매매 로직 연결, 디스코드 매매신호 알림

## 도구
- youtube-transcript-api로 유튜브 자막 추출 가능 (pip install youtube-transcript-api)

## 교훈
- 게이트웨이 재시작 시 lock 파일(.gateway.lock) 충돌 주의 — pkill 후 lock 삭제 필요
- plugins.entries.telegram.enabled: false 확인 필요 — 텔레그램 채널과 별개 설정일 수 있음
