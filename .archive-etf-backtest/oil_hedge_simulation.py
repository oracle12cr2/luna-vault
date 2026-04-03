"""
원유가 상승 시나리오별 포트폴리오 헤지 시뮬레이션
- 현재 포트폴리오 vs 에너지 헤지 포트폴리오 비교
- 3가지 시나리오: 단기해소 / 중기장기화 / 전면확전
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 데이터 수집
# ============================================================

# 현재 포트폴리오 + 헤지 후보 ETF
TICKERS = {
    # 현재 보유
    'KODEX레버리지': '122630.KS',
    'ACE200': '102110.KS',
    'KODEX고배당': '279530.KS',
    # 에너지/원유 헤지 후보
    'KODEX WTI원유선물': '261220.KS',      # WTI 원유선물 ETF
    'TIGER원유선물Enhanced': '130680.KS',   # 원유선물
    'KODEX골드선물': '132030.KS',           # 금 (인플레 헤지)
    'TIGER미국S&P500에너지': '218420.KS',   # 미국 에너지섹터
}

# 비교용 벤치마크
BENCHMARK = {
    'KOSPI200': '069500.KS',
    'WTI원유': 'CL=F',
}

print("=" * 70)
print("🛢️  원유가 상승 포트폴리오 헤지 시뮬레이션")
print("=" * 70)

# 최근 1년 데이터 수집
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"\n📊 데이터 수집 중... ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})")

prices = {}
current_prices = {}
failed = []

for name, ticker in {**TICKERS, **BENCHMARK}.items():
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if len(df) > 0:
            prices[name] = df['Close'].squeeze()
            current_prices[name] = float(df['Close'].iloc[-1].squeeze())
            print(f"  ✅ {name}: {current_prices[name]:,.0f}원" if '.KS' in ticker else f"  ✅ {name}: ${current_prices[name]:,.2f}")
        else:
            failed.append(name)
    except Exception as e:
        failed.append(name)
        print(f"  ❌ {name}: {e}")

if failed:
    print(f"\n⚠️  데이터 수집 실패: {', '.join(failed)}")

# ============================================================
# 2. 최근 수익률/변동성 분석
# ============================================================

print("\n" + "=" * 70)
print("📈 최근 수익률 & 변동성 분석")
print("=" * 70)

returns_data = {}
for name in prices:
    series = prices[name].dropna()
    if len(series) < 20:
        continue
    daily_ret = series.pct_change().dropna()
    
    # 기간별 수익률
    ret_1m = (series.iloc[-1] / series.iloc[-22] - 1) * 100 if len(series) > 22 else np.nan
    ret_3m = (series.iloc[-1] / series.iloc[-66] - 1) * 100 if len(series) > 66 else np.nan
    ret_6m = (series.iloc[-1] / series.iloc[-132] - 1) * 100 if len(series) > 132 else np.nan
    vol = daily_ret.std() * np.sqrt(252) * 100
    
    # 유가와의 상관계수
    if 'WTI원유' in prices and name != 'WTI원유':
        common_idx = series.index.intersection(prices['WTI원유'].index)
        if len(common_idx) > 20:
            corr = series.loc[common_idx].pct_change().corr(prices['WTI원유'].loc[common_idx].pct_change())
        else:
            corr = np.nan
    else:
        corr = np.nan
    
    returns_data[name] = {
        '1개월': ret_1m,
        '3개월': ret_3m,
        '6개월': ret_6m,
        '연변동성': vol,
        'WTI상관계수': corr
    }

df_returns = pd.DataFrame(returns_data).T
print(df_returns.to_string(float_format=lambda x: f"{x:.1f}" if not np.isnan(x) else "N/A"))

# ============================================================
# 3. 시나리오별 시뮬레이션
# ============================================================

print("\n" + "=" * 70)
print("🎯 시나리오별 포트폴리오 시뮬레이션 (향후 3개월)")
print("=" * 70)

# 시나리오 정의 (월간 수익률 가정)
scenarios = {
    '시나리오1: 단기해소\n(WTI $90~100 안착)': {
        'KODEX레버리지': [-3, 2, 3],      # KOSPI 소폭 조정 후 회복
        'ACE200': [-1.5, 1, 1.5],
        'KODEX고배당': [-0.5, 0.5, 1],
        'KODEX WTI원유선물': [5, -8, -5],  # 유가 하락 전환
        'TIGER원유선물Enhanced': [4, -7, -4],
        'KODEX골드선물': [2, 0, -1],        # 금 소폭 강세 후 안정
        'TIGER미국S&P500에너지': [3, -2, -1],
        'description': '호르무즈 2~4주 내 재개, 유가 하향 안정'
    },
    '시나리오2: 중기장기화\n(WTI $110~130)': {
        'KODEX레버리지': [-8, -5, -3],     # KOSPI 하락
        'ACE200': [-4, -2.5, -1.5],
        'KODEX고배당': [-2, -1, 0],
        'KODEX WTI원유선물': [12, 8, 5],   # 유가 지속 상승
        'TIGER원유선물Enhanced': [10, 7, 4],
        'KODEX골드선물': [5, 4, 3],         # 안전자산 선호
        'TIGER미국S&P500에너지': [8, 5, 3],
        'description': '호르무즈 1~3개월 교란, 비축유 소진 시작'
    },
    '시나리오3: 전면확전\n(WTI $150~200)': {
        'KODEX레버리지': [-15, -12, -8],   # KOSPI 급락
        'ACE200': [-7, -6, -4],
        'KODEX고배당': [-5, -3, -2],
        'KODEX WTI원유선물': [20, 15, 10],  # 유가 폭등
        'TIGER원유선물Enhanced': [18, 13, 9],
        'KODEX골드선물': [8, 6, 5],          # 금 급등
        'TIGER미국S&P500에너지': [12, 8, 5],
        'description': '호르무즈 장기 봉쇄, 오일쇼크급'
    }
}

INITIAL_CASH = 10_000_000  # 1000만원

# 포트폴리오 구성안들
portfolios = {
    'A. 현재 포트폴리오\n(변경 없음)': {
        'KODEX레버리지': 0.333,
        'ACE200': 0.333,
        'KODEX고배당': 0.334,
    },
    'B. 원유 헤지 10%\n(보수적)': {
        'KODEX레버리지': 0.30,
        'ACE200': 0.30,
        'KODEX고배당': 0.30,
        'KODEX WTI원유선물': 0.10,
    },
    'C. 원유+금 헤지 20%\n(균형)': {
        'KODEX레버리지': 0.27,
        'ACE200': 0.27,
        'KODEX고배당': 0.26,
        'KODEX WTI원유선물': 0.10,
        'KODEX골드선물': 0.10,
    },
    'D. 에너지 올인 30%\n(공격적)': {
        'KODEX레버리지': 0.25,
        'ACE200': 0.25,
        'KODEX고배당': 0.20,
        'KODEX WTI원유선물': 0.10,
        'KODEX골드선물': 0.10,
        'TIGER미국S&P500에너지': 0.10,
    },
}

for scenario_name, scenario in scenarios.items():
    if scenario_name == 'description':
        continue
    print(f"\n{'─' * 70}")
    print(f"📌 {scenario_name}")
    print(f"   {scenario.get('description', '')}")
    print(f"{'─' * 70}")
    
    results = []
    for port_name, weights in portfolios.items():
        total_return = 0
        monthly_values = [INITIAL_CASH]
        current_value = INITIAL_CASH
        
        for month in range(3):
            month_return = 0
            for etf, weight in weights.items():
                if etf in scenario:
                    month_return += weight * scenario[etf][month] / 100
            current_value *= (1 + month_return)
            monthly_values.append(current_value)
        
        total_return = (current_value / INITIAL_CASH - 1) * 100
        pnl = current_value - INITIAL_CASH
        
        # MDD 계산
        peak = monthly_values[0]
        max_dd = 0
        for v in monthly_values:
            if v > peak:
                peak = v
            dd = (v - peak) / peak
            if dd < max_dd:
                max_dd = dd
        
        results.append({
            'portfolio': port_name,
            'final_value': current_value,
            'total_return': total_return,
            'pnl': pnl,
            'mdd': max_dd * 100,
        })
    
    print(f"\n  {'포트폴리오':<28} {'최종 가치':>14} {'수익률':>10} {'손익':>14} {'MDD':>8}")
    print(f"  {'─'*28} {'─'*14} {'─'*10} {'─'*14} {'─'*8}")
    for r in results:
        emoji = '🟢' if r['total_return'] > 0 else '🔴'
        print(f"  {emoji} {r['portfolio']:<26} {r['final_value']:>12,.0f}원 {r['total_return']:>+8.1f}% {r['pnl']:>+12,.0f}원 {r['mdd']:>+6.1f}%")

# ============================================================
# 4. 추천
# ============================================================

print("\n" + "=" * 70)
print("💡 포트폴리오 추천")
print("=" * 70)

print("""
┌─────────────────────────────────────────────────────────────────┐
│ 현재 상황: 시나리오 1~2 사이 (단기해소~중기장기화)              │
│                                                                 │
│ 📌 추천: C안 (원유+금 헤지 20%)                                 │
│                                                                 │
│   • KODEX레버리지  27% (333→270만)                              │
│   • ACE200         27% (333→270만)                              │
│   • KODEX고배당    26% (334→260만)                              │
│   • KODEX WTI원유선물 10% (신규 100만)                          │
│   • KODEX골드선물    10% (신규 100만)                            │
│                                                                 │
│ 이유:                                                           │
│   1. 시나리오1이면 원유/금 손실 제한적 (-10% 내외)              │
│   2. 시나리오2이면 원유/금이 본 포트 손실 상당부분 상쇄          │
│   3. 시나리오3이면 원유/금이 방어벽 역할                        │
│   4. 정부 비축유+유류세 대책으로 시나리오3 확률 낮음             │
│                                                                 │
│ ⚠️ 주의: 원유선물 ETF는 롤오버 비용(콘탱고) 있음                │
│   → 장기 보유보다 단기 헤지용, 상황 해소 시 즉시 정리           │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================================
# 5. 실행 계획
# ============================================================

print("=" * 70)
print("📋 실행 계획 (C안 기준)")
print("=" * 70)
print("""
  [매도] KODEX레버리지  63만원 어치 (333→270만)
  [매도] ACE200         63만원 어치 (333→270만)  
  [매도] KODEX고배당    74만원 어치 (334→260만)
  ─────────────────────────────────────
  매도 합계: 약 200만원
  
  [매수] KODEX WTI원유선물(261220)  100만원
  [매수] KODEX골드선물(132030)      100만원
  ─────────────────────────────────────
  매수 합계: 약 200만원
  
  ⏰ 타이밍: 
    - 원유선물 ETF → 오늘~내일 중 (유가 모멘텀 아직 유효)
    - 금 ETF → 분할 진입 (이미 고점 근처, 2~3일 나눠서)
    
  🔄 리밸런싱 트리거:
    - 호르무즈 정상화 뉴스 → 원유 ETF 즉시 정리
    - WTI $120 돌파 → D안(30%)으로 확대 검토
    - WTI $85 이하 복귀 → 원유/금 전량 정리, 원래 포트 복귀
""")
