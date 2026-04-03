#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-
"""
KODEX 코스닥150 레버리지 (233740) 모니터링 + 자동 매매
전략:
  1) 매입가 -3% → 보유수량 30% 시장가 매도
  2) 1차 매도 체결가 -2% → 잔여수량 30% 시장가 매도
  3) 매입가 -1% → 예수금으로 추가 매수
"""

import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/usr/local/bin')
from kis_mock_trader import (
    get_access_token, get_headers, buy_market, sell_market,
    get_balance, send_order_discord, MOCK_BASE_URL,
    MOCK_CANO, MOCK_ACNT_PRDT
)
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/root/.openclaw/workspace/etf-backtest/kosdaq_lev_monitor.log"),
    ]
)
log = logging.getLogger(__name__)

# ============================================================
# 설정
# ============================================================
STOCK_CODE = "233740"
STOCK_NAME = "KODEX 코스닥150레버리지"
STATE_FILE = "/root/.openclaw/workspace/etf-backtest/kosdaq_lev_state.json"

# 폴링 간격 (초)
POLL_INTERVAL = 30


def get_current_price(stock_code: str) -> float:
    """현재가 조회"""
    headers = get_headers("FHKST01010100")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }
    resp = requests.get(
        f"{MOCK_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
        headers=headers, params=params, timeout=10,
    )
    result = resp.json()
    if result.get("rt_cd") == "0":
        return float(result["output"]["stck_prpr"])
    log.warning(f"현재가 조회 실패: {result.get('msg1', '')}")
    return 0


def get_available_cash() -> int:
    """주문 가능 예수금"""
    headers = get_headers("VTTC8434R")
    params = {
        'CANO': MOCK_CANO, 'ACNT_PRDT_CD': MOCK_ACNT_PRDT,
        'AFHR_FLPR_YN': 'N', 'OFL_YN': '', 'INQR_DVSN': '02',
        'UNPR_DVSN': '01', 'FUND_STTL_ICLD_YN': 'N',
        'FNCG_AMT_AUTO_RDPT_YN': 'N', 'PRCS_DVSN': '01',
        'CTX_AREA_FK100': '', 'CTX_AREA_NK100': '',
    }
    resp = requests.get(
        f"{MOCK_BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance",
        headers=headers, params=params, timeout=10,
    )
    data = resp.json()
    output2 = data.get("output2", [{}])
    if output2:
        return int(output2[0].get("dnca_tot_amt", 0))
    return 0


def get_holding_qty() -> tuple:
    """보유수량, 매입평균가 조회"""
    bal = get_balance()
    for h in bal:
        if h.get("pdno") == STOCK_CODE:
            return int(h.get("hldg_qty", 0)), float(h.get("pchs_avg_pric", 0))
    return 0, 0


def load_state() -> dict:
    """상태 파일 로드"""
    p = Path(STATE_FILE)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_state(state: dict):
    """상태 파일 저장"""
    Path(STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=2))


DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1480884778768007259/_bqFiBBOXAv3n5seIVUogrnqTvadU6twHJQmx9e7sa1jWNEz7CDwSyXJ00Ar73VhpwlG"

def send_discord(msg: str):
    """디스코드 웹훅 알림"""
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=5)
    except Exception as e:
        log.warning(f"디스코드 알림 실패: {e}")


def main():
    log.info(f"=== {STOCK_NAME} 모니터링 시작 ===")

    state = load_state()

    # 초기 상태 설정
    if not state:
        qty, avg_price = get_holding_qty()
        state = {
            "entry_price": avg_price,         # 매입평균가
            "initial_qty": qty,               # 초기 수량
            "stop1_triggered": False,         # -3% 1차 손절 실행 여부
            "stop1_sell_price": None,         # 1차 매도 체결가
            "stop2_triggered": False,         # -2% 2차 손절 실행 여부
            "dip_buy_triggered": False,       # -1% 추가매수 실행 여부
            "created_at": datetime.now().isoformat(),
        }
        save_state(state)
        log.info(f"초기 상태: 매입가 {avg_price:,.0f}원, 보유 {qty}주")
        send_discord(
            f"📊 **{STOCK_NAME} 모니터링 시작**\n"
            f"매입가: {avg_price:,.0f}원 | 보유: {qty}주\n"
            f"손절1: {avg_price * 0.97:,.0f}원(-3%) → 30%매도\n"
            f"손절2: 1차매도가 -2% → 30%매도\n"
            f"추가매수: {avg_price * 0.99:,.0f}원(-1%)"
        )

    entry_price = state["entry_price"]

    # 손절/매수 기준가
    stop1_price = entry_price * 0.97   # -3%
    dip_buy_price = entry_price * 0.99  # -1%

    log.info(f"기준가: 매입 {entry_price:,.0f} | 손절1 {stop1_price:,.0f} | 추가매수 {dip_buy_price:,.0f}")

    while True:
        now = datetime.now()

        # 장 시간 체크 (09:00 ~ 15:30)
        market_hour = now.hour * 100 + now.minute
        if market_hour < 900 or market_hour > 1530:
            log.info("장외 시간 — 대기")
            time.sleep(60)
            continue

        try:
            price = get_current_price(STOCK_CODE)
            if price == 0:
                time.sleep(POLL_INTERVAL)
                continue

            qty, avg_price = get_holding_qty()
            log.info(f"현재가: {price:,.0f}원 | 보유: {qty}주 | 손익: {(price/entry_price - 1)*100:+.2f}%")

            # === 1차 손절: -3% ===
            if not state["stop1_triggered"] and price <= stop1_price and qty > 0:
                sell_qty = max(1, int(qty * 0.3))
                log.info(f"🔴 1차 손절 발동! {price:,.0f}원 <= {stop1_price:,.0f}원 → {sell_qty}주 매도")
                result = sell_market(STOCK_CODE, sell_qty)
                if result.get("success"):
                    state["stop1_triggered"] = True
                    state["stop1_sell_price"] = price
                    state["stop2_price"] = price * 0.98  # 매도가 -2%
                    save_state(state)
                    send_discord(
                        f"🔴 **1차 손절 실행** {STOCK_NAME}\n"
                        f"매도: {sell_qty}주 @ {price:,.0f}원\n"
                        f"2차 손절 기준: {price * 0.98:,.0f}원 (-2%)\n"
                        f"주문번호: {result.get('order_no')}"
                    )
                else:
                    log.error(f"1차 손절 주문 실패: {result}")

            # === 2차 손절: 1차 매도가 -2% ===
            if (state["stop1_triggered"] and not state["stop2_triggered"]
                    and state.get("stop2_price") and price <= state["stop2_price"] and qty > 0):
                sell_qty = max(1, int(qty * 0.3))
                log.info(f"🔴 2차 손절 발동! {price:,.0f}원 <= {state['stop2_price']:,.0f}원 → {sell_qty}주 매도")
                result = sell_market(STOCK_CODE, sell_qty)
                if result.get("success"):
                    state["stop2_triggered"] = True
                    save_state(state)
                    send_discord(
                        f"🔴 **2차 손절 실행** {STOCK_NAME}\n"
                        f"매도: {sell_qty}주 @ {price:,.0f}원\n"
                        f"주문번호: {result.get('order_no')}"
                    )
                else:
                    log.error(f"2차 손절 주문 실패: {result}")

            # === 추가 매수: -1% ===
            if not state["dip_buy_triggered"] and price <= dip_buy_price and qty > 0:
                cash = get_available_cash()
                if cash > price:
                    buy_qty = int(cash / price)
                    log.info(f"🟢 추가매수 발동! {price:,.0f}원 <= {dip_buy_price:,.0f}원 → {buy_qty}주 매수")
                    result = buy_market(STOCK_CODE, buy_qty)
                    if result.get("success"):
                        state["dip_buy_triggered"] = True
                        save_state(state)
                        send_discord(
                            f"🟢 **추가매수 실행** {STOCK_NAME}\n"
                            f"매수: {buy_qty}주 @ {price:,.0f}원\n"
                            f"예수금: {cash:,}원 사용\n"
                            f"주문번호: {result.get('order_no')}"
                        )
                    else:
                        log.error(f"추가매수 주문 실패: {result}")
                else:
                    log.info(f"추가매수 조건이나 예수금 부족: {cash:,}원")

        except Exception as e:
            log.error(f"에러: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
