# ETF 자동매매 디렉토리

## 목적
KIS 모의투자 API 기반 ETF 자동매매 시스템

## 주요 스크립트 (루나 서버 /usr/local/bin/)
- etf_signal.py — 매매 시그널 생성 (메인)
- kis_mock_trader.py — KIS 모의투자 주문 실행
- kis_candle.py — 일봉 데이터 수집
- kis_investor.py — 투자자 동향 수집

## 설정
- 모의투자 계좌: 50173951 (ACNT_PRDT_CD: 01)
- 총 자본: 1,000만원 (3종목 균등 배분)
- cron: 평일 08:30(open) / 16:00(close)
- 포지션 상태: /var/lib/stock/signal_positions.json

## 주요 로직 (etf_signal.py)
1. Bubble Detector (버블 리스크 0-12점)
2. Exposure Coach (공포지표 기반 투자 비중 ceiling)
3. Position Sizer (ATR 역변동성 가중 종목별 비중)
4. 외국인 필터 (5일 중 3일+ 순매도 시 보류)
5. Discord 웹훅 알림

## 주의
- 실제 매매 로직 변경 시 --dry-run으로 먼저 테스트
- cron shebang: #!/home/anaconda3/bin/python3 절대경로 필수
