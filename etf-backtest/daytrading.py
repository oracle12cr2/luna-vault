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


def send_kakao(content):
    """카카오톡으로 알림 전송 (유나 맥북 HTTP 릴레이)"""
    try:
        text = content.replace("**", "").replace("`", "")
        requests.post("http://192.168.50.192:18790",
                      json={"recipient": "김태완(메인)", "message": text},
                      timeout=15)
    except Exception as e:
        log.warning(f"카톡 전송 실패: {e}")


def send_discord(content):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": content}, timeout=10)
    except:
        pass
    send_kakao(content)


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
    """현재가 조회 — DB 실시간 체결 우선, 실패 시 KIS REST API 폴백"""
    try:
        conn = get_ora_conn()
        cur = conn.cursor()
        today = datetime.now().strftime("%Y%m%d")
        cur.execute("""
            SELECT CURRENT_PRICE FROM stock.TB_TICK_DATA
            WHERE STOCK_CODE = :1 AND TRADE_DT = :2
            ORDER BY TRADE_TM DESC FETCH FIRST 1 ROWS ONLY
        """, [stock_code, today])
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0] > 0:
            return int(row[0])
    except Exception as e:
        log.warning(f"DB 현재가 조회 실패 ({stock_code}): {e}")
    
    # 폴백: KIS REST API
    try:
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code}
        r = requests.get(f"{KIS_BASE}/uapi/domestic-stock/v1/quotations/inquire-price",
                         params=params, headers=kis_headers("FHKST01010100"))
        data = r.json()
        return int(data.get('output', {}).get('stck_prpr', 0))
    except Exception as e:
        log.error(f"KIS API 현재가 조회도 실패 ({stock_code}): {e}")
        return 0


def get_realtime_indicators(stock_code):
    """실시간 지표 조회 — TB_TICK_DATA + TB_ORDERBOOK_SNAP에서 추출
    Returns:
        dict: {
            'price': 현재가,
            'trade_strength': 체결강도 (100 이상=매수우세),
            'vwap_5min': 최근 5분 VWAP,
            'vol_ratio': 5분 거래량 / 30분 평균 비율,
            'accum_vol': 당일 누적 거래량,
            'spread_pct': 호가 스프레드 %,
            'buy_sell_ratio': 매수잔량/매도잔량,
            'available': 데이터 존재 여부,
        }
    """
    today = datetime.now().strftime("%Y%m%d")
    result = {'available': False, 'price': 0}
    
    try:
        conn = get_ora_conn()
        cur = conn.cursor()
        
        # 1. 최근 체결 데이터 (최신 300건 ≈ 5~10분)
        cur.execute("""
            SELECT CURRENT_PRICE, TRADE_VOL, ACCUM_VOL, TRADE_STRENGTH, TRADE_TM
            FROM stock.TB_TICK_DATA
            WHERE STOCK_CODE = :1 AND TRADE_DT = :2
            ORDER BY TRADE_TM DESC FETCH FIRST 300 ROWS ONLY
        """, [stock_code, today])
        ticks = cur.fetchall()
        
        if not ticks:
            cur.close()
            conn.close()
            return result
        
        # 현재가 & 체결강도
        result['price'] = int(ticks[0][0])
        result['trade_strength'] = float(ticks[0][3] or 0)
        result['accum_vol'] = int(ticks[0][2] or 0)
        
        # VWAP (최근 5분 거래량 가중 평균)
        prices = [float(t[0]) for t in ticks[:60]]  # 약 5분
        vols = [float(t[1] or 1) for t in ticks[:60]]
        total_vol = sum(vols)
        if total_vol > 0:
            result['vwap_5min'] = round(sum(p*v for p, v in zip(prices, vols)) / total_vol, 0)
        else:
            result['vwap_5min'] = result['price']
        
        # 거래량 비율 (최근 5분 vs 30분 평균)
        vol_5min = sum(vols[:60])
        vol_30min = sum(float(t[1] or 0) for t in ticks)
        avg_30min = vol_30min / 6 if len(ticks) >= 60 else vol_30min  # 30분 = 5분 × 6
        result['vol_ratio'] = round(vol_5min / max(avg_30min, 1), 2)
        
        # 2. 호가 데이터 (최신 1건)
        cur.execute("""
            SELECT SELL_HOG1, BUY_HOG1, TOTAL_SELL_VOL, TOTAL_BUY_VOL
            FROM stock.TB_ORDERBOOK_SNAP
            WHERE STOCK_CODE = :1 AND SNAP_DT = :2
            ORDER BY SNAP_TM DESC FETCH FIRST 1 ROWS ONLY
        """, [stock_code, today])
        ob = cur.fetchone()
        
        if ob and ob[0] and ob[1]:
            sell_hog1 = int(ob[0])
            buy_hog1 = int(ob[1])
            total_sell = int(ob[2] or 0)
            total_buy = int(ob[3] or 0)
            
            # 스프레드 % 
            mid_price = (sell_hog1 + buy_hog1) / 2
            result['spread_pct'] = round((sell_hog1 - buy_hog1) / mid_price * 100, 3) if mid_price > 0 else 0
            
            # 매수/매도 잔량 비율
            result['buy_sell_ratio'] = round(total_buy / max(total_sell, 1), 2)
        else:
            result['spread_pct'] = 0
            result['buy_sell_ratio'] = 1.0
        
        result['available'] = True
        cur.close()
        conn.close()
        
    except Exception as e:
        log.warning(f"실시간 지표 조회 실패 ({stock_code}): {e}")
    
    return result


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
        # 펀더멘탈 데이터 조회 (TB_FINANCIAL_STMT)
        fundamental = None
        try:
            fund_df = pd.read_sql("""
                SELECT ACCOUNT_ID, THSTRM_AMOUNT FROM stock.TB_FINANCIAL_STMT
                WHERE STOCK_CODE = :1 AND BSNS_YEAR = '2024' AND REPRT_CODE = '11011'
                  AND FS_DIV = 'CFS'
            """, conn, params=[t['code']])
            if not fund_df.empty:
                fundamental = {}
                # PER는 재무제표에 직접 없으므로, 시가총액/순이익으로 추정 가능
                # ROE = 당기순이익/자본총계
                for _, row in fund_df.iterrows():
                    aid = str(row.get('account_id', ''))
                    amt = row.get('thstrm_amount', 0)
                    if amt is None:
                        continue
                    if 'NetIncome' in aid or 'ProfitLoss' in aid:
                        fundamental['net_income'] = float(amt)
                    elif 'Equity' in aid and 'Total' in aid.replace('total','Total'):
                        fundamental['equity'] = float(amt)
                    elif 'Revenue' in aid or 'Sales' in aid:
                        fundamental['revenue'] = float(amt)
                
                # ROE 계산
                if fundamental.get('net_income') and fundamental.get('equity') and fundamental['equity'] > 0:
                    fundamental['roe'] = fundamental['net_income'] / fundamental['equity'] * 100
                
                # PER는 ETF라 해당 없을 수 있음 → 기본값
                if 'per' not in fundamental:
                    fundamental['per'] = None
                if 'revenue_growth' not in fundamental:
                    fundamental['revenue_growth'] = None
        except Exception as e:
            log.warning(f"펀더멘탈 조회 실패 ({t['code']}): {e}")
        
        result = multifactor_score(price_df, investor_df, financial_df=fundamental)
        result['code'] = t['code']
        result['name'] = t['name']
        
        # 실시간 지표 조회 (DB 우선)
        rt = get_realtime_indicators(t['code'])
        result['price'] = rt['price'] if rt['available'] else get_current_price(t['code'])
        result['realtime'] = rt
        
        # 실시간 조건 반영: 체결강도/거래량/호가 기반 보정
        if rt['available']:
            bonus = 0
            penalty = 0
            reasons = []
            
            # 체결강도 > 110 → +5점 (매수세 강함)
            if rt['trade_strength'] > 110:
                bonus += 5
                reasons.append(f"체결강도↑{rt['trade_strength']:.0f}")
            # 체결강도 < 80 → -5점 (매도세 강함)
            elif rt['trade_strength'] < 80:
                penalty += 5
                reasons.append(f"체결강도↓{rt['trade_strength']:.0f}")
            
            # 5분 거래량 > 30분 평균 ×1.5 → +3점 (활발)
            if rt['vol_ratio'] > 1.5:
                bonus += 3
                reasons.append(f"거래량↑{rt['vol_ratio']}x")
            # 5분 거래량 < 30분 평균 ×0.5 → -3점 (한산)
            elif rt['vol_ratio'] < 0.5:
                penalty += 3
                reasons.append(f"거래량↓{rt['vol_ratio']}x")
            
            # 매수잔량/매도잔량 > 1.2 → +2점
            if rt['buy_sell_ratio'] > 1.2:
                bonus += 2
                reasons.append(f"매수잔량↑{rt['buy_sell_ratio']}")
            elif rt['buy_sell_ratio'] < 0.7:
                penalty += 2
                reasons.append(f"매도잔량↑{rt['buy_sell_ratio']}")
            
            # 스프레드 > 0.3% → -3점 (유동성 부족)
            if rt['spread_pct'] > 0.3:
                penalty += 3
                reasons.append(f"스프레드↑{rt['spread_pct']}%")
            
            result['total_score'] = round(min(100, max(0, result['total_score'] + bonus - penalty)), 1)
            result['rt_adjustment'] = bonus - penalty
            result['rt_reasons'] = reasons
            rt_log = f" RT[{bonus-penalty:+d}점: {', '.join(reasons)}]" if reasons else " RT[조건충족]"
        else:
            result['rt_adjustment'] = 0
            result['rt_reasons'] = []
            rt_log = " RT[데이터없음]"
        
        # 이평선 기반 시장 상태 판단
        market_state = "BULL"  # 기본 강세
        try:
            ma_df = get_price_df(conn, t['code'], days=120)
            if ma_df is not None and len(ma_df) >= 60:
                closes = ma_df['close'].values
                price_now = result['price']
                ma60_val = float(np.mean(closes[-60:]))
                ma120_val = float(np.mean(closes[-120:])) if len(closes) >= 120 else ma60_val
                ma15_val = float(np.mean(closes[-15:])) if len(closes) >= 15 else price_now
                ma3_val = float(np.mean(closes[-3:])) if len(closes) >= 3 else price_now
                
                result['ma_values'] = {
                    'ma3': round(ma3_val), 'ma15': round(ma15_val),
                    'ma60': round(ma60_val), 'ma120': round(ma120_val),
                }
                
                if price_now < ma60_val:
                    market_state = "BEAR"  # 약세장
                elif price_now < ma120_val:
                    market_state = "CORRECTION"  # 조정장
                
                # 추세 전환 감지: MA3 > MA15 골든크로스 + 현재가 > MA60
                ma3_today = (price_now + sum(closes[-2:])) / 3 if len(closes) >= 2 else price_now
                if market_state == "BEAR" and ma3_today > ma15_val and price_now > ma60_val * 0.98:
                    market_state = "REVERSAL"  # 추세 전환 (바닥 탈출)
                
        except Exception as e:
            log.warning(f"시장 상태 판단 실패 ({t['code']}): {e}")
        
        result['market_state'] = market_state
        
        scored.append(result)
        flog(f"  {t['name']}: {result['total_score']}점 ({result['signal']}) 현재가 {result['price']:,}원 [{market_state}]{rt_log}")
    conn.close()

    # 3. 매수 종목 선정 — 시장 상태별 기준 적용
    buy_candidates = []
    for s in scored:
        if s['price'] <= 0:
            continue
        state = s.get('market_state', 'BULL')
        score = s['total_score']
        
        if state == "BEAR":
            # 약세장: 매수 금지
            flog(f"  ❌ {s['name']}: 약세장(MA60 하회) 매수 금지 (스코어 {score})")
            continue
        elif state == "CORRECTION":
            # 조정장: 스코어 80 이상만 매수
            if score >= 80:
                buy_candidates.append(s)
            else:
                flog(f"  ⚠️ {s['name']}: 조정장 스코어 미달 {score}<80")
        elif state == "REVERSAL":
            # 추세 전환: 골든크로스 + MA60 근접 → 매수 허용 (스코어 70+)
            if score >= SCORE_THRESHOLD:
                buy_candidates.append(s)
                flog(f"  🔄 {s['name']}: 추세 전환 감지! 매수 허용 (스코어 {score})")
        else:
            # 강세장: 정상 기준
            if score >= SCORE_THRESHOLD:
                buy_candidates.append(s)
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
            # 실시간 지표 있으면 표시
            rt_info = ""
            matched = [s for s in scored if s['code'] == p['code']]
            if matched and matched[0].get('rt_reasons'):
                rt_info = f" | {', '.join(matched[0]['rt_reasons'])}"
            lines.append(f"  📊 **{p['name']}** {p['qty']}주 @ {p['price']:,}원 (스코어 {p['score']}{rt_info})")
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

# 매크로 급변 기준
MACRO_PANIC_RULES = {
    "vix_threshold": 35,       # VIX 35 이상 → 긴급
    "usdkrw_threshold": 1550,  # 환율 1550 이상 → 긴급
    "wti_spike_pct": 8.0,      # 유가 일일 +8% 이상 → 긴급
}


def check_macro_panic() -> dict:
    """매크로 급변 감지 — DB에서 최신 공포지표 조회"""
    result = {"panic": False, "reasons": [], "fear_level": "UNKNOWN"}
    try:
        conn = get_ora_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT VIX, VIX_CHG, WTI, WTI_CHG, USDKRW, USDKRW_CHG, FEAR_LEVEL
            FROM stock.TB_MARKET_FEAR
            ORDER BY TRADE_DT DESC FETCH FIRST 1 ROWS ONLY
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return result
        
        vix = float(row[0] or 0)
        wti_chg = float(row[3] or 0)
        usdkrw = float(row[4] or 0)
        usdkrw_chg = float(row[5] or 0)
        fear_level = row[6] or "UNKNOWN"
        
        result["fear_level"] = fear_level
        result["vix"] = vix
        result["usdkrw"] = usdkrw
        result["wti_chg"] = wti_chg
        
        # VIX 급등
        if vix >= MACRO_PANIC_RULES["vix_threshold"]:
            result["panic"] = True
            result["reasons"].append(f"VIX {vix:.1f} (기준 {MACRO_PANIC_RULES['vix_threshold']})")
        
        # 환율 급등
        if usdkrw >= MACRO_PANIC_RULES["usdkrw_threshold"]:
            result["panic"] = True
            result["reasons"].append(f"환율 {usdkrw:,.0f}원 (기준 {MACRO_PANIC_RULES['usdkrw_threshold']})")
        
        # 유가 급등
        if wti_chg >= MACRO_PANIC_RULES["wti_spike_pct"]:
            result["panic"] = True
            result["reasons"].append(f"유가 +{wti_chg:.1f}% (기준 +{MACRO_PANIC_RULES['wti_spike_pct']}%)")
        
    except Exception as e:
        log.warning(f"매크로 체크 실패: {e}")
    
    return result


def run_stoploss():
    """장��� 손절 체크 — DB 실시간 체결가 기반 + 매크로 패닉 체크"""
    
    # 매크로 패닉 체크 (VIX/환율/유가 급변)
    macro = check_macro_panic()
    if macro["panic"]:
        reason_str = ", ".join(macro["reasons"])
        flog(f"🚨 매크로 패닉 감지: {reason_str}")
        
        # 전량 매도
        bal = get_balance()
        panic_sold = []
        for h in bal.get('output1', []):
            qty = int(h.get('hldg_qty', 0))
            if qty <= 0:
                continue
            code = h.get('pdno', '')
            name = h.get('prdt_name', '?')
            ok, msg = place_order(code, qty, "sell")
            status = "✅" if ok else "❌"
            pnl = int(h.get('evlu_pfls_amt', 0))
            flog(f"🚨 매크로 긴급매도 {status} {name} {qty}주 | {pnl:+,}원")
            panic_sold.append({"name": name, "qty": qty, "pnl": pnl, "ok": ok})
        
        if panic_sold:
            lines = [f"🚨 **매크로 패닉 → 전량 매도** ({datetime.now().strftime('%H:%M')})", ""]
            lines.append(f"⚠️ 원인: {reason_str}")
            lines.append("")
            for s in panic_sold:
                icon = "✅" if s['ok'] else "❌"
                lines.append(f"{icon} **{s['name']}** {s['qty']}주 | {s['pnl']:+,}원")
            send_discord("\n".join(lines))
        return  # 매크로 패닉이면 개별 손절 불필요
    
    bal = get_balance()
    sold = []

    for h in bal.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        name = h.get('prdt_name', '?')
        code = h.get('pdno', '')
        avg_price = float(h.get('pchs_avg_pric', 0))
        
        # DB에서 실시간 현재가 조회 (더 최신)
        rt = get_realtime_indicators(code)
        if rt['available'] and rt['price'] > 0:
            cur_price = rt['price']
            pnl_pct = (cur_price - avg_price) / avg_price * 100 if avg_price > 0 else 0
            pnl = int((cur_price - avg_price) * qty)
            source = "RT"
        else:
            # KIS 잔고 기반 (폴백)
            pnl_pct = float(h.get('evlu_pfls_rt', 0))
            pnl = int(h.get('evlu_pfls_amt', 0))
            source = "API"

        if pnl_pct <= STOP_LOSS_PCT:
            ok, msg = place_order(code, qty, "sell")
            status = "✅" if ok else "❌"
            flog(f"🛑 손절 {status} {name} {qty}주 | {pnl:+,}원 ({pnl_pct:+.1f}%) [{source}]")
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


# ============================================================
# 단계적 익절 상태 파일
# ============================================================
PROFIT_STATE_FILE = "/var/lib/stock/profit_take_state.json"

def load_profit_state() -> dict:
    try:
        if Path(PROFIT_STATE_FILE).exists():
            with open(PROFIT_STATE_FILE) as f:
                return json.load(f)
    except:
        pass
    return {}

def save_profit_state(state: dict):
    try:
        os.makedirs(os.path.dirname(PROFIT_STATE_FILE), exist_ok=True)
        with open(PROFIT_STATE_FILE, "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"익절 상태 저장 실패: {e}")


def run_profit_take():
    """단계적 익절 — 수익 구간별 30%씩 분할 매도
    
    1차: +5% → 보유량의 30% 매도
    2차: 전일 대비 갭상승 or 추가 +3% → 잔여의 30% 매도  
    3차: 또 갭상승 or 추가 +3% → 잔여의 30% 매도
    4차: 나머지 10%는 시그널/손절/매도세로 처리
    """
    bal = get_balance()
    state = load_profit_state()
    today = datetime.now().strftime("%Y-%m-%d")
    sold = []

    for h in bal.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        code = h.get('pdno', '')
        name = h.get('prdt_name', '?')
        avg_price = float(h.get('pchs_avg_pric', 0))
        if avg_price <= 0:
            continue

        # 실시간 현재가
        rt = get_realtime_indicators(code)
        if rt['available'] and rt['price'] > 0:
            cur_price = rt['price']
        else:
            cur_price = int(h.get('prpr', 0))
        if cur_price <= 0:
            continue

        pnl_pct = (cur_price - avg_price) / avg_price * 100

        # 이 종목의 익절 상태
        cs = state.get(code, {
            "phase": 0,           # 0=미익절, 1=1차완료, 2=2차완료, 3=3차완료
            "original_qty": qty,  # 최초 보유량
            "last_take_date": None,
            "last_take_price": None,
            "peak_pnl_pct": 0,    # 최고 수익률 기록
        })
        
        # 최초 보유량 업데이트 (phase 0일 때만)
        if cs["phase"] == 0 and qty > cs.get("original_qty", 0):
            cs["original_qty"] = qty
        
        # 최고 수익률 갱신
        cs["peak_pnl_pct"] = max(cs.get("peak_pnl_pct", 0), pnl_pct)
        
        # 매도 수량 계산 (잔여의 30%, 최소 1주)
        sell_qty = max(1, int(qty * 0.3))
        if sell_qty >= qty:
            sell_qty = max(1, qty - 1)  # 최소 1주는 남기기
        
        should_sell = False
        take_reason = ""
        
        # ── 1차 익절: +5% 도달 ──
        if cs["phase"] == 0 and pnl_pct >= 5.0:
            should_sell = True
            take_reason = f"1차 익절 +{pnl_pct:.1f}% (기준 +5%)"
            cs["phase"] = 1
        
        # ── 2차 익절: 전일 대비 갭상승 or 추가 +3% ──
        elif cs["phase"] == 1:
            last_price = cs.get("last_take_price", avg_price)
            gain_since_last = (cur_price - last_price) / last_price * 100
            
            # 갭상승: 오늘 첫 체결(시가)이 전일 종가보다 +1% 이상
            gap_up = False
            try:
                conn = get_ora_conn()
                cur_db = conn.cursor()
                cur_db.execute("""
                    SELECT OPEN_PRICE FROM stock.TB_TICK_DATA
                    WHERE STOCK_CODE = :1 AND TRADE_DT = :2
                    ORDER BY TRADE_TM ASC FETCH FIRST 1 ROWS ONLY
                """, [code, datetime.now().strftime("%Y%m%d")])
                row = cur_db.fetchone()
                if row and last_price > 0:
                    open_gap = (float(row[0]) - last_price) / last_price * 100
                    if open_gap >= 1.0:
                        gap_up = True
                        take_reason = f"2차 익절: 갭상승 +{open_gap:.1f}%"
                cur_db.close()
                conn.close()
            except:
                pass
            
            if gap_up or gain_since_last >= 3.0:
                should_sell = True
                if not take_reason:
                    take_reason = f"2차 익절: 추가 +{gain_since_last:.1f}% (기준 +3%)"
                cs["phase"] = 2
        
        # ── 3차 익절: 또 갭상승 or 추가 +3% ──
        elif cs["phase"] == 2:
            last_price = cs.get("last_take_price", avg_price)
            gain_since_last = (cur_price - last_price) / last_price * 100
            
            gap_up = False
            try:
                conn = get_ora_conn()
                cur_db = conn.cursor()
                cur_db.execute("""
                    SELECT OPEN_PRICE FROM stock.TB_TICK_DATA
                    WHERE STOCK_CODE = :1 AND TRADE_DT = :2
                    ORDER BY TRADE_TM ASC FETCH FIRST 1 ROWS ONLY
                """, [code, datetime.now().strftime("%Y%m%d")])
                row = cur_db.fetchone()
                if row and last_price > 0:
                    open_gap = (float(row[0]) - last_price) / last_price * 100
                    if open_gap >= 1.0:
                        gap_up = True
                        take_reason = f"3차 익절: 갭상승 +{open_gap:.1f}%"
                cur_db.close()
                conn.close()
            except:
                pass
            
            if gap_up or gain_since_last >= 3.0:
                should_sell = True
                if not take_reason:
                    take_reason = f"3차 익절: 추가 +{gain_since_last:.1f}% (기준 +3%)"
                cs["phase"] = 3
        
        # ── 매도 실행 ──
        if should_sell and cs.get("last_take_date") != today:
            ok, msg = place_order(code, sell_qty, "sell")
            status = "✅" if ok else "❌"
            pnl_amt = int((cur_price - avg_price) * sell_qty)
            flog(f"🎯 {take_reason} {status} {name} {sell_qty}주/{qty}주 @ {cur_price:,}원 | +{pnl_amt:,}원")
            
            cs["last_take_date"] = today
            cs["last_take_price"] = cur_price
            
            sold.append({
                "name": name, "code": code, "sell_qty": sell_qty, "total_qty": qty,
                "price": cur_price, "pnl_pct": pnl_pct, "pnl_amt": pnl_amt,
                "reason": take_reason, "phase": cs["phase"], "ok": ok,
            })
        
        state[code] = cs

    save_profit_state(state)

    # 디스코드 알림
    if sold:
        lines = [f"🎯 **단계적 익절 실행** ({datetime.now().strftime('%H:%M')})", ""]
        for s in sold:
            icon = "✅" if s['ok'] else "❌"
            remaining = s['total_qty'] - s['sell_qty']
            lines.append(f"{icon} **{s['name']}** {s['sell_qty']}주 매도 (잔여 {remaining}주)")
            lines.append(f"  └ {s['reason']} | +{s['pnl_amt']:,}원 ({s['pnl_pct']:+.1f}%)")
        send_discord("\n".join(lines))


def run_sellpressure():
    """매도세 감지 — -3% 되기 전에 선제 매도
    
    TB_TICK_DATA + TB_ORDERBOOK_SNAP에서 매도세 시그널 복합 판단:
    - 경고(WARN) 2개 이상 → 디스코드 알림
    - 위험(DANGER) 1개 + 경고 1개 → 즉시 매도
    - 위험(DANGER) 2개 이상 → 긴급 전량 매도
    """
    bal = get_balance()
    today = datetime.now().strftime("%Y%m%d")
    alerts = []
    sells = []

    for h in bal.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        code = h.get('pdno', '')
        name = h.get('prdt_name', '?')
        avg_price = float(h.get('pchs_avg_pric', 0))

        warnings = []   # 경고
        dangers = []     # 위험

        try:
            conn = get_ora_conn()
            cur = conn.cursor()

            # ── 1. 체결 데이터 분석 ──
            cur.execute("""
                SELECT CURRENT_PRICE, TRADE_VOL, TRADE_STRENGTH, TRADE_TM,
                       SELL_ACCUM_VOL, BUY_ACCUM_VOL, NET_BUY_VOL
                FROM stock.TB_TICK_DATA
                WHERE STOCK_CODE = :1 AND TRADE_DT = :2
                ORDER BY TRADE_TM DESC FETCH FIRST 100 ROWS ONLY
            """, [code, today])
            ticks = cur.fetchall()

            if len(ticks) >= 20:
                prices = [float(t[0]) for t in ticks]
                vols = [float(t[1] or 0) for t in ticks]
                strengths = [float(t[2] or 100) for t in ticks]
                cur_price = prices[0]
                pnl_pct = (cur_price - avg_price) / avg_price * 100 if avg_price > 0 else 0

                # (1) 체결강도 급락: 최근 5분 평균 vs 전체
                avg_strength_30 = sum(strengths) / len(strengths)
                avg_strength_5 = sum(strengths[:20]) / 20
                if avg_strength_5 < 80:
                    dangers.append(f"체결강도↓{avg_strength_5:.0f}")
                elif avg_strength_5 < 90 and avg_strength_30 > 100:
                    warnings.append(f"체결강도하락 {avg_strength_30:.0f}→{avg_strength_5:.0f}")

                # (2) 연속 하락 틱: 최근 20틱 중 하락 비율
                down_ticks = sum(1 for i in range(1, min(20, len(prices))) if prices[i-1] < prices[i])
                if down_ticks >= 15:
                    dangers.append(f"연속하락 {down_ticks}/20틱")
                elif down_ticks >= 12:
                    warnings.append(f"하락추세 {down_ticks}/20틱")

                # (3) 대량 매도 체결: 최근 틱 중 평소 대비 10배 이상 거래량
                avg_vol = sum(vols) / len(vols) if vols else 1
                for i, v in enumerate(vols[:10]):
                    if v > avg_vol * 10 and prices[i] < prices[min(i+1, len(prices)-1)]:
                        dangers.append(f"대량매도 {int(v):,}주(평균{int(avg_vol):,})")
                        break

                # (4) VWAP 이탈: 현재가 < 5분 VWAP × 0.99
                total_val = sum(p * v for p, v in zip(prices[:20], vols[:20]))
                total_vol = sum(vols[:20])
                vwap = total_val / max(total_vol, 1)
                if cur_price < vwap * 0.99:
                    warnings.append(f"VWAP이탈 현재{cur_price:,.0f}<VWAP{vwap:,.0f}")

                # (5) 장중 이평선 이탈 체크 (일봉 MA + 실시간 현재가)
                try:
                    conn2 = get_ora_conn()
                    cur2 = conn2.cursor()
                    cur2.execute("""
                        SELECT CLOSE_PRICE FROM stock.TB_DAY_CANDLE
                        WHERE STOCK_CODE = :1
                        ORDER BY CANDLE_DT DESC FETCH FIRST 120 ROWS ONLY
                    """, [code])
                    ma_rows = [float(r[0]) for r in cur2.fetchall()]
                    cur2.close()
                    conn2.close()
                    
                    ma_values = {}
                    for period in [3, 15, 30, 60, 120]:
                        if len(ma_rows) >= period:
                            ma_values[period] = sum(ma_rows[:period]) / period
                    
                    if 15 in ma_values:
                        ma15 = ma_values[15]
                        ma3 = ma_values.get(3, cur_price)
                        
                        # MA15 이탈: 현재가 < 15일선 × 0.99
                        if cur_price < ma15 * 0.99:
                            dangers.append(f"MA15이탈 현재{cur_price:,.0f}<MA15({ma15:,.0f})")
                        elif cur_price < ma15:
                            warnings.append(f"MA15하회 현재{cur_price:,.0f}<MA15({ma15:,.0f})")
                        
                        # 데드크로스 임박 (오늘 종가를 현재가로 가정)
                        ma3_today = (cur_price + sum(ma_rows[:2])) / 3
                        if ma3 > ma15 and ma3_today < ma15:
                            dangers.append(f"데드크로스임박 MA3({ma3_today:,.0f})<MA15({ma15:,.0f})")
                    
                    if 30 in ma_values:
                        ma30 = ma_values[30]
                        # MA30 이탈: 중기 추세 전환
                        if cur_price < ma30 * 0.98:
                            dangers.append(f"MA30이탈 현재{cur_price:,.0f}<MA30({ma30:,.0f})×0.98")
                        elif cur_price < ma30:
                            warnings.append(f"MA30하회 현재{cur_price:,.0f}<MA30({ma30:,.0f})")
                    
                    if 60 in ma_values:
                        ma60 = ma_values[60]
                        # MA60 이탈: 중장기 하락 신호
                        if cur_price < ma60:
                            dangers.append(f"MA60하회 현재{cur_price:,.0f}<MA60({ma60:,.0f})")
                    
                    if 120 in ma_values:
                        ma120 = ma_values[120]
                        # MA120 이탈: 약세장 진입
                        if cur_price < ma120:
                            dangers.append(f"MA120하회(약세장) 현재{cur_price:,.0f}<MA120({ma120:,.0f})")
                    
                except Exception as e:
                    log.warning(f"이평선 체크 실패 ({code}): {e}")

                # (6) 매도/매수 체결량 비율 (실시간 누적)  
                sell_accum = int(ticks[0][4] or 0)
                buy_accum = int(ticks[0][5] or 0)
                net_buy = int(ticks[0][6] or 0)
                
                if sell_accum > 0 and buy_accum > 0:
                    sell_buy_vol_ratio = sell_accum / buy_accum
                    # 매도체결 > 매수체결 × 1.5 → 위험
                    if sell_buy_vol_ratio > 1.5:
                        dangers.append(f"매도체결우세 {sell_buy_vol_ratio:.1f}x(매도{sell_accum:,}/매수{buy_accum:,})")
                    elif sell_buy_vol_ratio > 1.2:
                        warnings.append(f"매도체결↑ {sell_buy_vol_ratio:.1f}x")
                
                # (6) 순매수체결량 급감
                if net_buy is not None and net_buy < 0 and abs(net_buy) > buy_accum * 0.3:
                    warnings.append(f"순매도{net_buy:,}주")

            # ── 2. 호가 데이터 분석 ──
            cur.execute("""
                SELECT SELL_HOG1, BUY_HOG1, TOTAL_SELL_VOL, TOTAL_BUY_VOL,
                       BUY_VOL1, BUY_VOL2, BUY_VOL3
                FROM stock.TB_ORDERBOOK_SNAP
                WHERE STOCK_CODE = :1 AND SNAP_DT = :2
                ORDER BY SNAP_TM DESC FETCH FIRST 2 ROWS ONLY
            """, [code, today])
            obs = cur.fetchall()

            if obs:
                ob = obs[0]
                total_sell = int(ob[2] or 0)
                total_buy = int(ob[3] or 0)
                buy_vol1 = int(ob[4] or 0)

                # (5) 매도잔량 폭증
                sell_buy_ratio = total_sell / max(total_buy, 1)
                if sell_buy_ratio > 2.0:
                    dangers.append(f"매도잔량폭증 {sell_buy_ratio:.1f}x")
                elif sell_buy_ratio > 1.5:
                    warnings.append(f"매도잔량↑ {sell_buy_ratio:.1f}x")

                # (6) 매수벽 붕괴 (이전 스냅샷 대비)
                if len(obs) >= 2:
                    prev_buy_vol1 = int(obs[1][4] or 0)
                    if prev_buy_vol1 > 0 and buy_vol1 < prev_buy_vol1 * 0.5:
                        dangers.append(f"매수벽붕괴 {prev_buy_vol1:,}→{buy_vol1:,}")

            cur.close()
            conn.close()

        except Exception as e:
            log.warning(f"매도세 분석 실패 ({code}): {e}")
            continue

        # ── 3. 복합 판단 ──
        danger_cnt = len(dangers)
        warn_cnt = len(warnings)
        all_signals = dangers + warnings

        if danger_cnt >= 2:
            # 🚨 긴급 전량 매도
            ok, msg = place_order(code, qty, "sell")
            status = "✅" if ok else "❌"
            reason = f"위험×{danger_cnt}: {', '.join(dangers)}"
            flog(f"🚨 선제매도 {status} {name} {qty}주 | {reason}")
            sells.append({"name": name, "qty": qty, "code": code, "ok": ok,
                          "level": "CRITICAL", "reason": reason, "pnl_pct": pnl_pct})
        elif danger_cnt >= 1 and warn_cnt >= 1:
            # 🛑 즉시 매도
            ok, msg = place_order(code, qty, "sell")
            status = "✅" if ok else "❌"
            reason = f"위험×{danger_cnt}+경고×{warn_cnt}: {', '.join(all_signals)}"
            flog(f"🛑 선제매도 {status} {name} {qty}주 | {reason}")
            sells.append({"name": name, "qty": qty, "code": code, "ok": ok,
                          "level": "HIGH", "reason": reason, "pnl_pct": pnl_pct})
        elif warn_cnt >= 2:
            # ⚠️ 경고 알림만 (매도는 안 함)
            reason = f"경고×{warn_cnt}: {', '.join(warnings)}"
            flog(f"⚠️ 매도세 감지 {name} | {reason}")
            alerts.append({"name": name, "code": code, "level": "WARN", "reason": reason, "pnl_pct": pnl_pct})

    # ── 4. 디스코드 알림 ──
    if sells:
        lines = [f"🚨 **매도세 감지 → 선제 매도** ({datetime.now().strftime('%H:%M')})", ""]
        for s in sells:
            icon = "✅" if s['ok'] else "❌"
            lvl = "🚨" if s['level'] == "CRITICAL" else "🛑"
            lines.append(f"{lvl}{icon} **{s['name']}** {s['qty']}주 ({s['pnl_pct']:+.1f}%)")
            lines.append(f"  └ {s['reason']}")
        send_discord("\n".join(lines))

    if alerts:
        lines = [f"⚠️ **매도세 경고** ({datetime.now().strftime('%H:%M')})", ""]
        for a in alerts:
            lines.append(f"⚠️ **{a['name']}** ({a['pnl_pct']:+.1f}%)")
            lines.append(f"  └ {a['reason']}")
        send_discord("\n".join(lines))


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
    parser.add_argument("--mode", choices=["buy", "sell", "buy-exec", "sell-exec", "cancel", "stoploss", "sellpressure", "profit"], required=True)
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
    elif args.mode == "sellpressure":
        run_sellpressure()
    elif args.mode == "profit":
        run_profit_take()


if __name__ == "__main__":
    main()
