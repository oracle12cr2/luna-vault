#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-
"""
ETF 데이트레이딩 시스템
- 09:30 스냅샷 → 멀티팩터 스코어링 → 매수
- 14:50 전종목 일괄 청산 (15:00 장 마감 전)
- 자산의 70%를 예산으로 설정
- 스코어 70점 이상 종목만 매수, 다종목 분산

모드:
    --mode buy          매수 분석 → 승인 대기 → 실행
    --mode sell         청산 분석 → 승인 대기 → 실행
    --mode buy-exec     매수 실행 (승인 후 호출)
    --mode sell-exec    청산 실행 (승인 후 호출)
    --auto              승인 없이 즉시 실행 (기존 동작)

크론탭:
    30 9  * * 1-5  daytrading.py --mode buy
    50 14 * * 1-5  daytrading.py --mode sell
"""

import os
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"

import argparse
import json
import logging
import requests
import oracledb
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 경로 설정 (멀티팩터 모듈 import)
import sys
sys.path.insert(0, '/root/.openclaw/workspace/etf-backtest')
from strategies.multifactor import multifactor_score

# ============================================================
# 설정
# ============================================================
# KIS 모의투자
KIS_BASE = "https://openapivts.koreainvestment.com:29443"
KIS_APP_KEY = "PSn3EK6GBUcrb5pcAatX6qXr1Pa07laVUYUe"
KIS_APP_SECRET = "d3o9g5OfF55qwbM9CizR/nUDuNNgWhjOtnCn5fzOHCS5B9VM7mWFB2HsNFK5rJlHiQuts5vB4kxQiZS0w0+mAP9hP4L4OGW+aG8wW0PfI6HvU2JSqd7AHghIisAKuYxjzWMXjM5ctpXErzf/gpL/Y16BTQqzGogIYuIJ7gCGVB33VoHELhQ="
KIS_CANO = "50173951"
KIS_ACNT_PRDT = "01"
TOKEN_FILE = "/tmp/kis_daytrading_token.json"

# Oracle (주가/수급 데이터)
ORA_LIB = "/usr/lib/oracle/23/client64/lib"
ORA_USER = "stock"
ORA_PASS = "Oracle2026_em"
ORA_DSN = "PROD_OGG"

# Discord
DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1480884778768007259/_bqFiBBOXAv3n5seIVUogrnqTvadU6twHJQmx9e7sa1jWNEz7CDwSyXJ00Ar73VhpwlG"

# 전략 설정
BUDGET_RATIO = 0.70          # 자산의 70% 매수
SCORE_THRESHOLD = 70         # 매수 최소 스코어
MAX_STOCKS = 5               # 최대 종목 수
MIN_BUY_AMT = 100_000       # 최소 매수 금액

# 대상 종목 (일봉 수집 목록과 일치시킴)
TARGETS = [
    {"code": "122630", "name": "KODEX 레버리지"},
    {"code": "105190", "name": "ACE 200"},
    {"code": "279530", "name": "KODEX 고배당"},
    {"code": "091230", "name": "TIGER 반도체"},
    {"code": "305720", "name": "KODEX 2차전지산업"},
    {"code": "466940", "name": "TIGER 은행고배당플러스"},
    {"code": "132030", "name": "KODEX 골드선물"},
    {"code": "229200", "name": "KODEX 코스닥150"},
]

LOG_FILE = "/var/log/stock/daytrading.log"
PENDING_FILE = "/tmp/daytrading_pending.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def flog(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    log.info(msg)


def send_discord(content):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": content}, timeout=10)
    except:
        pass


# ============================================================
# KIS API
# ============================================================
def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            cached = json.load(f)
            if datetime.fromisoformat(cached['expires_at']) > datetime.now(tz=None):
                return cached['token']
    r = requests.post(f"{KIS_BASE}/oauth2/tokenP", json={
        "grant_type": "client_credentials", "appkey": KIS_APP_KEY, "appsecret": KIS_APP_SECRET,
    })
    token = r.json()['access_token']
    with open(TOKEN_FILE, 'w') as f:
        json.dump({"token": token, "expires_at": (datetime.now()+timedelta(hours=23)).isoformat()}, f)
    return token


def kis_headers(tr_id):
    return {
        "authorization": f"Bearer {get_token()}",
        "appkey": KIS_APP_KEY, "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id, "content-type": "application/json; charset=utf-8",
    }


def get_balance():
    """잔고 조회"""
    params = {
        "CANO": KIS_CANO, "ACNT_PRDT_CD": KIS_ACNT_PRDT,
        "AFHR_FLPR_YN": "N", "OFL_YN": "", "INQR_DVSN": "02",
        "UNPR_DVSN": "01", "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N", "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "", "CTX_AREA_NK100": "",
    }
    r = requests.get(f"{KIS_BASE}/uapi/domestic-stock/v1/trading/inquire-balance",
                     params=params, headers=kis_headers("VTTC8434R"))
    return r.json()


def get_current_price(stock_code):
    """현재가 조회"""
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code}
    r = requests.get(f"{KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
                     params=params, headers=kis_headers("FHKST01010100"))
    data = r.json()
    return int(data.get('output', {}).get('stck_prpr', 0))


def place_order(stock_code, qty, order_type="buy"):
    """매수/매도 주문"""
    tr_id = "VTTC0802U" if order_type == "buy" else "VTTC0801U"
    body = {
        "CANO": KIS_CANO, "ACNT_PRDT_CD": KIS_ACNT_PRDT,
        "PDNO": stock_code, "ORD_DVSN": "01",  # 시장가
        "ORD_QTY": str(qty), "ORD_UNPR": "0",
    }
    r = requests.post(f"{KIS_BASE}/uapi/domestic-stock/v1/trading/order-cash",
                      headers=kis_headers(tr_id), json=body)
    result = r.json()
    return result.get('rt_cd') == '0', result.get('msg1', '')


# ============================================================
# Oracle 데이터
# ============================================================
def get_ora_conn():
    oracledb.init_oracle_client(lib_dir=ORA_LIB)
    return oracledb.connect(user=ORA_USER, password=ORA_PASS, dsn=ORA_DSN)


def get_price_df(conn, code, days=30):
    df = pd.read_sql("""
        SELECT CANDLE_DT, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, CLOSE_PRICE, TRADE_VOL
        FROM STOCK.TB_DAY_CANDLE WHERE STOCK_CODE = :1
        ORDER BY CANDLE_DT DESC FETCH FIRST :2 ROWS ONLY
    """, conn, params=[code, days])
    if df.empty:
        return None
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    return df.sort_values('date').reset_index(drop=True)


def get_investor_df(conn, code, days=10):
    df = pd.read_sql("""
        SELECT TRADE_DT, FRGN_NET_VOL, ORGN_NET_VOL, PRSN_NET_VOL
        FROM STOCK.TB_INVESTOR_TREND WHERE STOCK_CODE = :1
        ORDER BY TRADE_DT DESC FETCH FIRST :2 ROWS ONLY
    """, conn, params=[code, days])
    if df.empty:
        return None
    df.columns = ['trade_dt', 'frgn_net_vol', 'orgn_net_vol', 'prsn_net_vol']
    return df.sort_values('trade_dt').reset_index(drop=True)


# ============================================================
# 매수 모드
# ============================================================
def run_buy(auto_mode=False):
    flog("=" * 50)
    flog(f"🟢 데이트레이딩 매수 시작 (09:30) {'[자동]' if auto_mode else '[승인모드]'}")

    # 1. 잔고 확인
    bal = get_balance()
    summary = (bal.get('output2') or [{}])[0]
    tot_evlu = int(summary.get('tot_evlu_amt', 0))
    deposit = int(summary.get('prvs_rcdl_excc_amt', 0)) or int(summary.get('dnca_tot_amt', 0))
    budget = int(tot_evlu * BUDGET_RATIO)
    flog(f"총 평가: {tot_evlu:,}원, 예수금(D+2): {deposit:,}원, 매수 예산: {budget:,}원")

    if deposit < MIN_BUY_AMT:
        flog("예수금 부족, 매수 스킵")
        send_discord(f"⚠️ 데이트레이딩 매수 스킵 — 예수금 부족 ({deposit:,}원)")
        return

    # 2. 멀티팩터 스코어링
    conn = get_ora_conn()
    scored = []
    for t in TARGETS:
        price_df = get_price_df(conn, t['code'])
        investor_df = get_investor_df(conn, t['code'])
        if price_df is None or len(price_df) < 15:
            flog(f"  {t['name']}: 데이터 부족, 스킵")
            continue
        result = multifactor_score(price_df, investor_df)
        result['code'] = t['code']
        result['name'] = t['name']
        import time; time.sleep(0.3)  # API rate limit 방지
        result['price'] = get_current_price(t['code'])
        scored.append(result)
        flog(f"  {t['name']}: {result['total_score']}점 ({result['signal']}) 현재가 {result['price']:,}원")
    conn.close()

    # 3. 매수 종목 선정 (70점 이상, 상위 N개)
    buy_candidates = [s for s in scored if s['total_score'] >= SCORE_THRESHOLD and s['price'] > 0]
    buy_candidates.sort(key=lambda x: x['total_score'], reverse=True)
    buy_candidates = buy_candidates[:MAX_STOCKS]

    if not buy_candidates:
        flog("매수 조건 충족 종목 없음")
        send_discord("⚪ 데이트레이딩 — 매수 조건 충족 종목 없음")
        return

    # 4. 종목별 매수 금액 배분 (균등)
    per_stock_budget = min(budget, deposit) // len(buy_candidates)
    buy_plan = []
    for c in buy_candidates:
        qty = per_stock_budget // c['price']
        if qty > 0:
            buy_plan.append({"code": c['code'], "name": c['name'], "qty": qty, "price": c['price'], "score": c['total_score']})

    if not buy_plan:
        flog("매수 가능 종목 없음 (수량 0)")
        return

    # 승인 모드: 플랜 저장 후 알림만 전송
    if not auto_mode:
        pending = {"mode": "buy", "plan": buy_plan, "budget": per_stock_budget * len(buy_plan), "timestamp": datetime.now().isoformat()}
        with open(PENDING_FILE, 'w') as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)
        lines = [f"🟡 **데이트레이딩 매수 승인 요청** ({datetime.now().strftime('%H:%M')})",
                 f"예산: {pending['budget']:,}원", ""]
        for p in buy_plan:
            lines.append(f"  📊 **{p['name']}** {p['qty']}주 @ {p['price']:,}원 (스코어 {p['score']})")
        lines.append(f"\n✅ 승인: `daytrading.py --mode buy-exec`")
        lines.append(f"❌ 거부: `daytrading.py --mode cancel`")
        msg = "\n".join(lines)
        flog(msg)
        send_discord(msg)
        return

    # 자동 모드 또는 buy-exec: 즉시 실행
    execute_buy(buy_plan)


# ============================================================
# 매수 실행 (승인 후)
# ============================================================
def execute_buy(buy_plan):
    orders = []
    for p in buy_plan:
        ok, msg = place_order(p['code'], p['qty'], "buy")
        status = "✅" if ok else "❌"
        flog(f"  매수 {status} {p['name']} {p['qty']}주 @ {p['price']:,}원 (스코어: {p['score']})")
        orders.append({**p, "ok": ok})

    lines = [f"🟢 **데이트레이딩 매수 완료** ({datetime.now().strftime('%H:%M')})", ""]
    for o in orders:
        icon = "✅" if o['ok'] else "❌"
        lines.append(f"{icon} **{o['name']}** {o['qty']}주 @ {o['price']:,}원 (스코어 {o['score']})")
    send_discord("\n".join(lines))


def run_buy_exec():
    """승인된 매수 플랜 실행"""
    if not os.path.exists(PENDING_FILE):
        flog("승인 대기 중인 매수 플랜 없음")
        return
    with open(PENDING_FILE) as f:
        pending = json.load(f)
    if pending.get('mode') != 'buy':
        flog("대기 중인 플랜이 매수가 아님")
        return
    flog("✅ 매수 승인 — 실행 시작")
    execute_buy(pending['plan'])
    os.remove(PENDING_FILE)


# ============================================================
# 매도 모드 (일괄 청산)
# ============================================================
def run_sell(auto_mode=False):
    flog("=" * 50)
    flog("🔴 데이트레이딩 일괄 청산 시작 (14:50)")

    bal = get_balance()
    holdings = []
    for h in bal.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        holdings.append({
            'code': h.get('pdno', ''),
            'name': h.get('prdt_name', ''),
            'qty': qty,
            'avg_price': round(float(h.get('pchs_avg_pric', 0))),
            'cur_price': int(h.get('prpr', 0)),
            'pnl': int(h.get('evlu_pfls_amt', 0)),
            'pnl_pct': float(h.get('evlu_pfls_rt', 0)),
        })

    if not holdings:
        flog("보유 종목 없음, 청산 스킵")
        send_discord("⚪ 데이트레이딩 청산 — 보유 종목 없음")
        return

    # 승인 모드: 플랜 저장 후 알림만 전송
    if not auto_mode:
        sell_plan = [{"code": h['code'], "name": h['name'], "qty": h['qty'], "pnl": h['pnl'], "pnl_pct": h['pnl_pct']} for h in holdings]
        pending = {"mode": "sell", "plan": sell_plan, "timestamp": datetime.now().isoformat()}
        with open(PENDING_FILE, 'w') as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)

        total_pnl = sum(h['pnl'] for h in holdings)
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        lines = [f"🟡 **데이트레이딩 청산 승인 요청** ({datetime.now().strftime('%H:%M')})", ""]
        for h in holdings:
            pnl_icon = "🟢" if h['pnl'] >= 0 else "🔴"
            lines.append(f"  {pnl_icon} **{h['name']}** {h['qty']}주 | {h['pnl']:+,}원 ({h['pnl_pct']:+.1f}%)")
        lines.append(f"\n{pnl_emoji} **예상 손익: {total_pnl:+,}원**")
        lines.append(f"\n✅ 승인: `daytrading.py --mode sell-exec`")
        lines.append(f"❌ 거부 (홀드): `daytrading.py --mode cancel`")
        msg = "\n".join(lines)
        flog(msg)
        send_discord(msg)
        return

    # 자동 모드: 즉시 청산
    execute_sell(holdings)


def execute_sell(holdings):
    total_pnl = 0
    lines = [f"🔴 **데이트레이딩 일괄 청산 완료** ({datetime.now().strftime('%H:%M')})", ""]

    for h in holdings:
        ok, msg = place_order(h['code'], h['qty'], "sell")
        status = "✅" if ok else "❌"
        total_pnl += h['pnl']
        pnl_icon = "🟢" if h['pnl'] >= 0 else "🔴"
        flog(f"  매도 {status} {h['name']} {h['qty']}주 | {h['pnl']:+,}원 ({h['pnl_pct']:+.1f}%)")
        lines.append(f"{pnl_icon} **{h['name']}** {h['qty']}주 | {h['pnl']:+,}원 ({h['pnl_pct']:+.1f}%)")

    pnl_emoji = "📈" if total_pnl >= 0 else "📉"
    lines.append(f"\n{pnl_emoji} **오늘 손익: {total_pnl:+,}원**")
    send_discord("\n".join(lines))
    flog(f"청산 완료 — 오늘 손익: {total_pnl:+,}원")


def run_sell_exec():
    """승인된 청산 플랜 실행"""
    if not os.path.exists(PENDING_FILE):
        flog("승인 대기 중인 청산 플랜 없음")
        return
    with open(PENDING_FILE) as f:
        pending = json.load(f)
    if pending.get('mode') != 'sell':
        flog("대기 중인 플랜이 청산이 아님")
        return
    flog("✅ 청산 승인 — 실행 시작")
    # 다시 잔고 조회해서 최신 정보로 실행
    bal = get_balance()
    holdings = []
    for h in bal.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        holdings.append({
            'code': h.get('pdno', ''),
            'name': h.get('prdt_name', ''),
            'qty': qty,
            'avg_price': round(float(h.get('pchs_avg_pric', 0))),
            'cur_price': int(h.get('prpr', 0)),
            'pnl': int(h.get('evlu_pfls_amt', 0)),
            'pnl_pct': float(h.get('evlu_pfls_rt', 0)),
        })
    execute_sell(holdings)
    os.remove(PENDING_FILE)


# ============================================================
# 손절 모드 (-3% 자동 청산)
# ============================================================
STOP_LOSS_PCT = -3.0  # 손절 기준

def run_stoploss():
    """장중 손절 체크 — -3% 이하 종목 즉시 매도"""
    bal = get_balance()
    sold = []

    for h in bal.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        name = h.get('prdt_name', '?')
        pnl_pct = float(h.get('evlu_pfls_rt', 0))
        pnl = int(h.get('evlu_pfls_amt', 0))
        code = h.get('pdno', '')

        if pnl_pct <= STOP_LOSS_PCT:
            ok, msg = place_order(code, qty, "sell")
            status = "✅" if ok else "❌"
            flog(f"🛑 손절 {status} {name} {qty}주 | {pnl:+,}원 ({pnl_pct:+.1f}%)")
            sold.append({"name": name, "qty": qty, "pnl": pnl, "pnl_pct": pnl_pct, "ok": ok})

    if sold:
        lines = [f"🛑 **손절 자동 실행** ({datetime.now().strftime('%H:%M')})", ""]
        for s in sold:
            icon = "✅" if s['ok'] else "❌"
            lines.append(f"{icon} **{s['name']}** {s['qty']}주 | {s['pnl']:+,}원 ({s['pnl_pct']:+.1f}%)")
        lines.append(f"\n⚠️ 손절 기준: {STOP_LOSS_PCT}%")
        msg = "\n".join(lines)
        send_discord(msg)
        flog(msg)


def run_cancel():
    """승인 대기 취소"""
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE) as f:
            pending = json.load(f)
        os.remove(PENDING_FILE)
        flog(f"❌ {pending.get('mode', '?')} 플랜 취소")
        send_discord(f"❌ 데이트레이딩 {pending.get('mode', '?')} 취소됨")
    else:
        flog("취소할 플랜 없음")


# ============================================================
# 메인
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["buy", "sell", "buy-exec", "sell-exec", "cancel", "stoploss"], required=True)
    parser.add_argument("--auto", action="store_true", help="승인 없이 즉시 실행")
    args = parser.parse_args()

    if args.mode == "buy":
        run_buy(auto_mode=args.auto)
    elif args.mode == "sell":
        run_sell(auto_mode=args.auto)
    elif args.mode == "buy-exec":
        run_buy_exec()
    elif args.mode == "sell-exec":
        run_sell_exec()
    elif args.mode == "cancel":
        run_cancel()
    elif args.mode == "stoploss":
        run_stoploss()


if __name__ == "__main__":
    main()
