---
globs: ["**/*.py"]
---

# Python 스크립트 규칙

## 환경
- 인터프리터: /home/anaconda3/bin/python3
- shebang: #!/home/anaconda3/bin/python3 (cron 환경 대응)
- encoding: # -*- coding: utf-8 -*-

## 스타일
- logging 모듈 사용 (print 대신)
- requests 타임아웃 필수 (timeout=10)
- 파일 경로는 절대경로 또는 Path 객체

## KIS API (주식)
- 모의투자 모듈: /usr/local/bin/kis_mock_trader.py
- 실전 모듈: /usr/local/bin/kis_realtime.py
- 토큰 캐시: /tmp/kis_mock_token.json
- 디스코드 웹훅으로 알림 전송

## 데이터 파이프라인
- Redis: 192.168.50.9 (RedisCluster)
- Oracle DB: app_user@50.35:1521/PROD
