#!/usr/bin/env python3
"""
국내 주식 차트 자동 분석 프로그램 v2
- Mode 1 (기본): 수치 분석만 (API 비용 0원)
- Mode 2 (--vision): 수치 1차 필터 → BUY/SELL 후보만 Gemini Vision 확인
- 디스코드 알림 지원
"""

import asyncio
import json
import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import mplfinance as mpf
import numpy as np
import pandas as pd
import yfinance as yf

from dotenv import load_dotenv

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CHART_DIR = Path("charts_kr")
CHART_DIR.mkdir(exist_ok=True)
OUTPUT_CSV = "gemini_chart_analysis_kr.csv"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")

# macOS 한글 폰트
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams["font.family"] = "Apple SD Gothic Neo"
    plt.rcParams["axes.unicode_minus"] = False

# ──────────────────────────────────────────────
# 종목 리스트
# ──────────────────────────────────────────────
STOCKS = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "373220.KS": "LG에너지솔루션",
    "207940.KS": "삼성바이오로직스", "005380.KS": "현대차", "000270.KS": "기아",
    "006400.KS": "삼성SDI", "051910.KS": "LG화학", "035420.KS": "NAVER",
    "035720.KS": "카카오", "005490.KS": "POSCO홀딩스", "055550.KS": "신한지주",
    "105560.KS": "KB금융", "003670.KS": "포스코퓨처엠", "012330.KS": "현대모비스",
    "066570.KS": "LG전자", "003550.KS": "LG", "032830.KS": "삼성생명",
    "086790.KS": "하나금융지주", "034730.KS": "SK", "015760.KS": "한국전력",
    "096770.KS": "SK이노베이션", "017670.KS": "SK텔레콤", "030200.KS": "KT",
    "316140.KS": "우리금융지주", "009150.KS": "삼성전기", "010130.KS": "고려아연",
    "028260.KS": "삼성물산", "034020.KS": "두산에너빌리티", "011200.KS": "HMM",
    "018260.KS": "삼성에스디에스", "033780.KS": "KT&G", "000810.KS": "삼성화재",
    "010950.KS": "S-Oil", "009540.KS": "HD한국조선해양", "267250.KS": "HD현대",
    "003490.KS": "대한항공", "036570.KS": "엔씨소프트", "011170.KS": "롯데케미칼",
    "024110.KS": "기업은행", "000720.KS": "현대건설", "010140.KS": "삼성중공업",
    "047050.KS": "포스코인터내셔널", "090430.KS": "아모레퍼시픽",
    "051900.KS": "LG생활건강", "329180.KS": "HD현대중공업", "004020.KS": "현대제철",
    "000100.KS": "유한양행", "011780.KS": "금호석유", "016360.KS": "삼성증권",
    "006800.KS": "미래에셋증권", "138040.KS": "메리츠금융지주",
    "352820.KS": "하이브", "259960.KS": "크래프톤",
    "042660.KS": "한화오션", "402340.KS": "SK스퀘어", "361610.KS": "SK아이이테크놀로지",
    "001570.KS": "금양", "271560.KS": "오리온", "000080.KS": "하이트진로",
    "002790.KS": "아모레G", "088350.KS": "한화생명", "161390.KS": "한국타이어앤테크놀로지",
    "004170.KS": "신세계", "021240.KS": "코웨이", "006360.KS": "GS건설",
    "071050.KS": "한국금융지주", "139480.KS": "이마트", "326030.KS": "SK바이오팜",
    "180640.KS": "한진칼", "032640.KS": "LG유플러스", "078930.KS": "GS",
    "247540.KQ": "에코프로비엠", "086520.KQ": "에코프로", "377300.KQ": "카카오페이",
    "263750.KQ": "펄어비스", "068270.KQ": "셀트리온", "196170.KQ": "알테오젠",
    "145020.KQ": "휴젤", "041510.KQ": "에스엠", "293490.KQ": "카카오게임즈",
    "112040.KQ": "위메이드", "035900.KQ": "JYP Ent.", "357780.KQ": "솔브레인",
    "028300.KQ": "에이치엘비", "095340.KQ": "ISC", "039030.KQ": "이오테크닉스",
    "058470.KQ": "리노공업", "005290.KQ": "동진쎄미켐", "383220.KQ": "F&F",
    "454910.KQ": "에이피알", "322510.KQ": "제이엘케이", "236810.KQ": "엔비티",
    "403870.KQ": "HPSP", "067310.KQ": "하나마이크론", "218410.KQ": "RFHIC",
    "041920.KQ": "메디아나",
}


# ──────────────────────────────────────────────
# 기술적 지표 계산
# ──────────────────────────────────────────────
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def analyze_stock(df):
    """종합 수치 분석 → 시그널 + 점수"""
    if df is None or len(df) < 200:
        return None

    close = df["Close"]
    volume = df["Volume"]
    score = 0  # -100 ~ +100
    reasons = []

    # ── 이동평균선 분석 ──
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma60 = close.rolling(60).mean()
    ma120 = close.rolling(120).mean()
    ma200 = close.rolling(200).mean()

    last = close.iloc[-1]
    prev = close.iloc[-2]

    l_ma5 = ma5.iloc[-1]
    l_ma20 = ma20.iloc[-1]
    l_ma50 = ma50.iloc[-1]
    l_ma60 = ma60.iloc[-1]
    l_ma120 = ma120.iloc[-1]
    l_ma200 = ma200.iloc[-1]

    # 정배열/역배열
    if l_ma20 > l_ma50 > l_ma200:
        ma_status = "정배열"
        score += 15
        reasons.append("MA 정배열(강세 구조)")
    elif l_ma20 < l_ma50 < l_ma200:
        ma_status = "역배열"
        score -= 15
        reasons.append("MA 역배열(약세 구조)")
    else:
        ma_status = "혼조"

    # 골든크로스 / 데드크로스 (최근 5일 이내)
    for i in range(1, 6):
        if ma20.iloc[-i-1] < ma60.iloc[-i-1] and ma20.iloc[-i] >= ma60.iloc[-i]:
            score += 20
            reasons.append(f"골든크로스(20/60) {i}일전 발생")
            break
        if ma20.iloc[-i-1] > ma60.iloc[-i-1] and ma20.iloc[-i] <= ma60.iloc[-i]:
            score -= 20
            reasons.append(f"데드크로스(20/60) {i}일전 발생")
            break

    # 가격 vs 이평선 위치
    price_vs_ma20 = ((last - l_ma20) / l_ma20) * 100
    price_vs_ma200 = ((last - l_ma200) / l_ma200) * 100

    if last > l_ma20 > l_ma60 > l_ma120:
        score += 10
    if last < l_ma20 and last < l_ma60:
        score -= 10

    # MA20 지지/저항
    if abs(price_vs_ma20) < 1.5 and last > l_ma20:
        score += 5
        reasons.append(f"MA20 지지 반등 (이격 {price_vs_ma20:+.1f}%)")

    # ── RSI ──
    rsi = calc_rsi(close).iloc[-1]
    rsi_prev = calc_rsi(close).iloc[-2]

    if np.isnan(rsi):
        rsi = 50.0
        rsi_zone = "계산불가"
    elif rsi < 30:
        rsi_zone = "과매도"
        score += 20
        reasons.append(f"RSI {rsi:.1f} 과매도 진입 → 반등 기대")
    elif rsi < 40:
        rsi_zone = "약세"
        score += 8
        reasons.append(f"RSI {rsi:.1f} 약세권 (반등 가능)")
    elif rsi > 70:
        rsi_zone = "과매수"
        score -= 15
        reasons.append(f"RSI {rsi:.1f} 과매수 → 조정 가능")
    elif rsi > 60:
        rsi_zone = "강세"
        score += 5
    else:
        rsi_zone = "중립"

    # RSI 다이버전스 (간이)
    if rsi > rsi_prev and close.iloc[-1] < close.iloc[-2]:
        score += 5
        reasons.append("RSI 상승 다이버전스(가격↓ RSI↑)")
    elif rsi < rsi_prev and close.iloc[-1] > close.iloc[-2]:
        score -= 5

    # ── MACD ──
    macd_line, signal_line, histogram = calc_macd(close)
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    hist_val = histogram.iloc[-1]
    hist_prev = histogram.iloc[-2]

    if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_val >= signal_val:
        score += 15
        reasons.append("MACD 골든크로스")
    elif macd_line.iloc[-2] > signal_line.iloc[-2] and macd_val <= signal_val:
        score -= 15
        reasons.append("MACD 데드크로스")

    if hist_val > 0 and hist_val > hist_prev:
        score += 5
    elif hist_val < 0 and hist_val < hist_prev:
        score -= 5

    # ── 거래량 ──
    vol_avg_20 = volume.rolling(20).mean().iloc[-1]
    vol_recent_5 = volume.iloc[-5:].mean()
    vol_today = volume.iloc[-1]
    vol_ratio = vol_today / vol_avg_20 if vol_avg_20 > 0 else 1.0

    if vol_ratio > 3.0 and last > prev:
        volume_trend = "폭증+상승"
        score += 15
        reasons.append(f"거래량 폭증(x{vol_ratio:.1f}) + 양봉")
    elif vol_ratio > 2.0 and last > prev:
        volume_trend = "급증+상승"
        score += 10
        reasons.append(f"거래량 급증(x{vol_ratio:.1f})")
    elif vol_ratio > 1.5:
        volume_trend = "증가"
        score += 3
    elif vol_ratio < 0.5:
        volume_trend = "급감"
        score -= 3
    else:
        volume_trend = "보통"

    # ── 볼린저밴드 ──
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_width = ((bb_upper - bb_lower) / bb_mid * 100).iloc[-1]

    if last <= bb_lower.iloc[-1]:
        bb_status = "하단터치"
        score += 10
        reasons.append(f"볼린저밴드 하단 터치 (반등 기대)")
    elif last >= bb_upper.iloc[-1]:
        bb_status = "상단돌파"
        score -= 5
        reasons.append("볼린저밴드 상단 돌파 (과열)")
    elif bb_width < 5:
        bb_status = "스퀴즈"
        reasons.append("볼린저밴드 스퀴즈 (변동성 확대 임박)")
    else:
        bb_status = "밴드내"

    # ── 추세 강도 (최근 20일 수익률) ──
    ret_20d = ((last - close.iloc[-20]) / close.iloc[-20]) * 100
    ret_5d = ((last - close.iloc[-5]) / close.iloc[-5]) * 100

    if ret_20d > 15:
        score -= 5  # 급등 후 과열
    elif ret_20d < -15:
        score += 5  # 급락 후 반등

    # ── 최종 시그널 결정 ──
    score = max(-100, min(100, score))

    if score >= 30:
        signal = "BUY"
    elif score <= -20:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = min(95, abs(score) + 40)

    # 단기 전망
    if signal == "BUY":
        if rsi < 35:
            short_view = f"과매도 반등 구간. 단기 {abs(price_vs_ma20):.0f}%+ 반등 기대"
        elif "골든크로스" in str(reasons):
            short_view = "골든크로스 발생, 추세 전환 초기 단계"
        else:
            short_view = "기술적 매수 조건 충족, 단기 상승 모멘텀 확인"
    elif signal == "SELL":
        if rsi > 70:
            short_view = "과매수 조정 임박, 단기 차익실현 권장"
        elif "데드크로스" in str(reasons):
            short_view = "하락 추세 전환, 추가 하락 가능성"
        else:
            short_view = "약세 지표 다수, 관망 또는 포지션 축소 권장"
    else:
        short_view = "뚜렷한 방향성 없음, 추세 확인 후 진입 권장"

    return {
        "price": round(last, 0),
        "ma_status": ma_status,
        "rsi": round(rsi, 1),
        "rsi_zone": rsi_zone,
        "volume_trend": volume_trend,
        "bb_status": bb_status,
        "macd": "상승" if hist_val > 0 else "하락",
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "reasons": reasons[:5],
        "short_term_view": short_view,
        "price_vs_ma20": round(price_vs_ma20, 1),
        "price_vs_ma200": round(price_vs_ma200, 1),
        "ret_5d": round(ret_5d, 1),
        "ret_20d": round(ret_20d, 1),
    }


# ──────────────────────────────────────────────
# 차트 생성
# ──────────────────────────────────────────────
def generate_chart(ticker, name, df):
    if df is None or len(df) < 50:
        return None

    filepath = CHART_DIR / f"{ticker.replace('.', '_')}_{name}.png"

    mc = mpf.make_marketcolors(up="r", down="b", inherit=True)
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle="-", gridcolor="#e0e0e0")

    add_plots = [
        mpf.make_addplot(df["Close"].rolling(20).mean(), color="cyan", width=1),
        mpf.make_addplot(df["Close"].rolling(50).mean(), color="orange", width=1),
        mpf.make_addplot(df["Close"].rolling(200).mean(), color="red", width=1),
    ]

    fig, axes = mpf.plot(
        df, type="candle", style=style, volume=True,
        addplot=add_plots, title=f"\n{name} ({ticker})",
        figsize=(12, 7), returnfig=True,
    )
    fig.savefig(str(filepath), dpi=100, bbox_inches="tight")
    plt.close("all")
    return str(filepath)


# ──────────────────────────────────────────────
# Gemini Vision (선택 모드, BUY/SELL만)
# ──────────────────────────────────────────────
def analyze_with_gemini(client, ticker, name, chart_path, tech):
    """Gemini Vision 확인 분석 (BUY/SELL 후보만)"""
    from google.genai import types

    tech_text = f"""
[수치 데이터] {name}({ticker})
- 현재가: {tech['price']:,.0f}원 (5일 {tech['ret_5d']:+.1f}%, 20일 {tech['ret_20d']:+.1f}%)
- MA: {tech['ma_status']} | 가격 vs MA20: {tech['price_vs_ma20']:+.1f}%
- RSI: {tech['rsi']} ({tech['rsi_zone']}) | MACD: {tech['macd']}
- 거래량: {tech['volume_trend']} | 볼린저: {tech['bb_status']}
- 수치분석 시그널: {tech['signal']} (score: {tech['score']})
- 사유: {', '.join(tech['reasons'][:3])}
"""

    prompt = f"""당신은 25년 경력의 기술적 분석 전문가입니다.

{tech_text}

위 수치 분석 결과와 차트 이미지를 종합해서, 이 시그널이 맞는지 검증해주세요.

JSON 응답:
{{"verified": true/false, "adjusted_signal": "BUY/HOLD/SELL", "confidence": 0-100, "comment": "한줄 코멘트"}}
"""

    with open(chart_path, "rb") as f:
        image_data = f.read()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Content(role="user", parts=[
                types.Part.from_bytes(data=image_data, mime_type="image/png"),
                types.Part.from_text(text=prompt),
            ])
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json", temperature=0.3,
        ),
    )

    result = json.loads(response.text)
    if isinstance(result, list):
        result = result[0]
    return result


# ──────────────────────────────────────────────
# 디스코드 알림
# ──────────────────────────────────────────────
def send_discord_alert(df):
    if not DISCORD_WEBHOOK:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(df)
    buy_count = len(df[df["signal"] == "BUY"])
    sell_count = len(df[df["signal"] == "SELL"])
    hold_count = len(df[df["signal"] == "HOLD"])

    lines = [
        f"# 📊 주식 차트 AI 분석 리포트",
        f"**{now}** | {total}종목 분석",
        f"🟢 BUY: {buy_count}  🟡 HOLD: {hold_count}  🔴 SELL: {sell_count}",
        "",
    ]

    # BUY
    buys = df[df["signal"] == "BUY"].sort_values("score", ascending=False)
    if not buys.empty:
        lines.append("## 🟢 BUY 시그널")
        for _, r in buys.head(10).iterrows():
            reasons = r.get("reasons", "")
            if isinstance(reasons, list):
                reasons = " / ".join(reasons[:2])
            elif isinstance(reasons, str) and reasons.startswith("["):
                try:
                    reasons = " / ".join(eval(reasons)[:2])
                except:
                    pass
            lines.append(
                f"**{r['name']}** ({r['ticker']}) "
                f"score:{r['score']} | {r.get('ma_status','')} | "
                f"RSI:{r.get('rsi','')} | {r.get('volume_trend','')}\n"
                f"> {r.get('short_term_view', '')}"
            )
        lines.append("")

    # SELL
    sells = df[df["signal"] == "SELL"].sort_values("score")
    if not sells.empty:
        lines.append("## 🔴 SELL 시그널")
        for _, r in sells.head(5).iterrows():
            lines.append(
                f"**{r['name']}** ({r['ticker']}) "
                f"score:{r['score']}\n"
                f"> {r.get('short_term_view', '')}"
            )

    message = "\n".join(lines)
    if len(message) > 1900:
        message = message[:1900] + "\n... (생략)"

    try:
        resp = requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        if resp.status_code in (200, 204):
            print("📨 디스코드 알림 전송 완료!")
        else:
            print(f"⚠️  디스코드 {resp.status_code}")
    except Exception as e:
        print(f"⚠️  디스코드 실패: {e}")


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    use_vision = "--vision" in sys.argv
    no_discord = "--no-discord" in sys.argv
    chart_mode = "--chart" in sys.argv or use_vision

    print("=" * 60)
    print("  📊 국내 주식 기술적 분석 시스템 v2")
    print("=" * 60)
    print(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📈 종목: {len(STOCKS)}개")
    print(f"🔍 모드: {'수치+Vision' if use_vision else '수치 분석 전용 (비용 0원)'}")
    if chart_mode:
        print(f"📸 차트: 생성함")
    print()

    # ── Step 1: 데이터 다운로드 + 분석 ──
    print("Step 1: 데이터 다운로드 & 기술적 분석")
    print("-" * 50)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)  # 200일선 위해 넉넉히

    results = []
    chart_paths = {}

    for i, (ticker, name) in enumerate(STOCKS.items(), 1):
        market = "코스닥" if ".KQ" in ticker else "코스피"
        print(f"  [{i:2d}/{len(STOCKS)}] {name:12s}({ticker:12s})", end=" ", flush=True)

        try:
            data = yf.download(
                ticker, start=start_date, end=end_date,
                progress=False, auto_adjust=True,
            )
            if data.empty:
                print("❌ 데이터없음")
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel("Ticker")

            analysis = analyze_stock(data)
            if analysis is None:
                print("❌ 데이터부족")
                continue

            analysis["ticker"] = ticker
            analysis["name"] = name
            analysis["market"] = market

            # 차트 생성 (옵션)
            if chart_mode:
                cp = generate_chart(ticker, name, data)
                if cp:
                    chart_paths[ticker] = cp

            sig = analysis["signal"]
            emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[sig]
            print(f"{emoji} {sig:4s} score:{analysis['score']:+3d} RSI:{analysis['rsi']:5.1f} MA:{analysis['ma_status']}")

            results.append(analysis)

        except Exception as e:
            print(f"❌ {str(e)[:50]}")

    if not results:
        print("❌ 분석 결과 없음")
        return

    df = pd.DataFrame(results)

    # ── Step 2: (옵션) Gemini Vision 검증 ──
    if use_vision and API_KEY:
        buysell = df[df["signal"].isin(["BUY", "SELL"])]
        if not buysell.empty:
            print(f"\nStep 2: Gemini Vision 검증 ({len(buysell)}종목)")
            print("-" * 50)

            from google import genai
            client = genai.Client(api_key=API_KEY)
            call_count = 0

            for _, row in buysell.iterrows():
                ticker = row["ticker"]
                if ticker not in chart_paths:
                    continue
                if call_count >= 15:  # 일일 쿼터 안전장치
                    print("  ⚠️  일일 쿼터 보호 (15회 도달)")
                    break

                print(f"  🔍 {row['name']}... ", end="", flush=True)
                try:
                    result = analyze_with_gemini(
                        client, ticker, row["name"],
                        chart_paths[ticker], row.to_dict()
                    )
                    verified = result.get("verified", True)
                    adj = result.get("adjusted_signal", row["signal"])
                    comment = result.get("comment", "")
                    print(f"{'✅' if verified else '❌'} {adj} — {comment[:50]}")

                    if not verified:
                        idx = df[df["ticker"] == ticker].index[0]
                        df.at[idx, "signal"] = adj
                        df.at[idx, "short_term_view"] = comment

                    call_count += 1
                    time.sleep(5)
                except Exception as e:
                    if "429" in str(e):
                        print("⏳ 쿼터 소진, Vision 중단")
                        break
                    print(f"❌ {str(e)[:40]}")

    # ── Step 3: 결과 종합 ──
    print(f"\n{'=' * 60}")
    print("  📊 분석 결과 요약")
    print("=" * 60)

    df = df.sort_values("score", ascending=False)

    # 시그널 통계
    for sig in ["BUY", "HOLD", "SELL"]:
        cnt = len(df[df["signal"] == sig])
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}[sig]
        print(f"  {emoji} {sig}: {cnt}건")

    # BUY
    buys = df[df["signal"] == "BUY"].copy()
    if not buys.empty:
        print(f"\n{'─' * 60}")
        print(f"  🟢 BUY 시그널 ({len(buys)}건)")
        print(f"{'─' * 60}")
        for _, r in buys.iterrows():
            reasons = r.get("reasons", [])
            if isinstance(reasons, str):
                try:
                    reasons = eval(reasons)
                except:
                    reasons = [reasons]
            reasons_str = " / ".join(reasons[:3])
            print(f"\n  ★ {r['name']} ({r['ticker']}) [{r['market']}]")
            print(f"    현재가: {r['price']:>12,.0f}원  score: {r['score']:+d}")
            print(f"    MA: {r['ma_status']}  RSI: {r['rsi']}({r['rsi_zone']})  MACD: {r.get('macd','')}")
            print(f"    거래량: {r['volume_trend']}  볼린저: {r['bb_status']}")
            print(f"    5일: {r.get('ret_5d',0):+.1f}%  20일: {r.get('ret_20d',0):+.1f}%")
            print(f"    사유: {reasons_str}")
            print(f"    전망: {r['short_term_view']}")
    else:
        print("\n  🟡 BUY 시그널 없음 — 전체 관망")

    # SELL
    sells = df[df["signal"] == "SELL"].copy()
    if not sells.empty:
        print(f"\n{'─' * 60}")
        print(f"  🔴 SELL 시그널 ({len(sells)}건)")
        print(f"{'─' * 60}")
        for _, r in sells.iterrows():
            reasons = r.get("reasons", [])
            if isinstance(reasons, str):
                try:
                    reasons = eval(reasons)
                except:
                    reasons = [reasons]
            reasons_str = " / ".join(reasons[:3])
            print(f"\n  ▼ {r['name']} ({r['ticker']}) score: {r['score']:+d}")
            print(f"    RSI: {r['rsi']}({r['rsi_zone']})  {reasons_str}")
            print(f"    전망: {r['short_term_view']}")

    # CSV 저장
    cols = ["ticker", "name", "market", "signal", "score", "confidence", "price",
            "ma_status", "rsi", "rsi_zone", "macd", "volume_trend", "bb_status",
            "ret_5d", "ret_20d", "price_vs_ma20", "price_vs_ma200",
            "short_term_view", "reasons"]
    save_cols = [c for c in cols if c in df.columns]
    df[save_cols].to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n💾 저장: {OUTPUT_CSV}")

    # 디스코드 알림
    if not no_discord and DISCORD_WEBHOOK:
        send_discord_alert(df)

    print(f"\n✅ 분석 완료! ({len(results)}종목)")


if __name__ == "__main__":
    main()
