# 주식 데이터 수집 디렉토리

## 목적
KIS API / DART API 기반 주식 데이터 수집 및 분석

## 데이터 파이프라인
KIS API → Redis (192.168.50.9) → Oracle DB (192.168.50.31)

## 주요 스크립트 (루나 서버)
- kis_realtime.py — 실시간 시세 수집
- kis_candle.py — 일봉 수집
- dart_*.py — DART 공시 데이터
- etf_redis_realtime.py — ETF 실시간 Redis 저장
- kis_investor.py — 투자자 동향 (cron 평일 16:10)

## DB 스키마
- stock.TB_DAY_CANDLE — 일봉
- stock.TB_INVESTOR_TREND — 투자자 동향
- stock.TB_MARKET_FEAR — 공포지표 (VIX, WTI, 환율, 금)
- stock.TB_FINANCIAL_STMT — 재무제표 (380만건)

## KIS API
- 실투자 + 모의투자 API 키 모두 발급 완료
- RedisCluster 클라이언트 사용 (redis01~03: 192.168.50.3~5)
