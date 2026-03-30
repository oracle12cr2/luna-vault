# ETF 백테스트 디렉토리

## 목적
워크포워드 검증 기반 ETF 전략 백테스트 및 최적화

## 주요 파일
- daytrading.py — 데이트레이딩 전략
- optimize_report.html — 최적화 결과 리포트
- walkforward_report.html — 워크포워드 검증 리포트

## 규칙
- 전략 변경 시 반드시 워크포워드(OOS) 검증 후 적용
- 수익률보다 샤프 비율 우선
- 백테스트 파라미터: Oracle DB (stock.TB_DAY_CANDLE)에서 로드
- 결과 리포트는 reports/ 디렉토리에 저장

## 현재 전략 (워크포워드 PASS)
- KODEX 레버리지: MA(3/15)
- ACE 200: MA(3/15)
- TIGER 반도체TOP10: MA(3/15) (데이터 부족 이슈 있음)
