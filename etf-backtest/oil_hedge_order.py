#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-
"""
원유 헤지 포트폴리오 C안 — 모의투자 주문 실행
포트: KODEX레버리지27% / ACE200 27% / KODEX고배당26% / WTI원유10% / 골드10%
"""

import sys
import json
import time
sys.path.insert(0, '/usr/local/bin')
from kis_mock_trader import (
    get_access_token, get_headers, buy_market, sell_market,
    get_balance, send_order_discord, MOCK_BASE_URL, MOCK_APP_KEY,
    MOCK_APP_SECRET, MOCK_CANO, MOCK_ACNT_PRDT
)
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# C안 목표 포트폴리오
# ============================================================
TOTAL_CAPITAL = 10_000_000  # 1000만원

TARGET_PORTFOLIO = {
    '122630': {'name': 'KODEX 레버리지',       'weight': 0.27},   # 270만
    '105190': {'name': 'ACE 200',              'weight': 0.27},   # 270만 (모의투자 종목코드)
    '279530': {'name': 'KODEX 고배당',         'weight': 0.26},   # 260만
    '261220': {'name': 'KODEX WTI원유선물',    'weight': 0.10},   # 100만 ← 신규
    '132030': {'name': 'KODEX 골드선물',       'weight': 0.10},   # 100만 ← 신규
}

def get_current_price(stock_code: str) -> float:
    """현재가 조회"""
    headers = get_headers("FHKST01010100")
    # 모의투자도 시세는 실전 API 사용
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }
    resp = requests.get(
        f"{MOCK_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
        headers=headers,
        params=params,
        timeout=10,
    )
    result = resp.json()
    if result.get("rt_cd") == "0":
        return float(result["output"]["stck_prpr"])
    else:
        log.warning(f"현재가 조회 실패 {stock_code}: {result.get('msg1', '')}")
        return 0


def get_current_holdings() -> dict:
    """현재 보유 종목 → {종목코드: 수량}"""
    holdings = get_balance()
    result = {}
    for h in holdings:
        code = h.get('pdno', '')
        qty = int(h.get('hldg_qty', 0))
        if qty > 0:
            result[code] = {
                'qty': qty,
                'name': h.get('prdt_name', ''),
                'avg_price': float(h.get('pchs_avg_pric', 0)),
                'eval_amt': int(h.get('evlu_amt', 0)),
            }
    return result


def calculate_orders(holdings: dict, prices: dict) -> list:
    """목표 vs 현재 비교하여 주문 목록 생성"""
    orders = []
    
    for code, target in TARGET_PORTFOLIO.items():
        target_amount = int(TOTAL_CAPITAL * target['weight'])
        price = prices.get(code, 0)
        if price <= 0:
            log.error(f"[{code}] {target['name']} 현재가 없음, 스킵")
            continue
        
        target_qty = int(target_amount / price)
        current_qty = holdings.get(code, {}).get('qty', 0)
        diff = target_qty - current_qty
        
        if diff > 0:
            orders.append({
                'action': 'BUY',
                'code': code,
                'name': target['name'],
                'qty': diff,
                'price': price,
                'amount': diff * price,
                'target_qty': target_qty,
                'current_qty': current_qty,
            })
        elif diff < 0:
            orders.append({
                'action': 'SELL',
                'code': code,
                'name': target['name'],
                'qty': abs(diff),
                'price': price,
                'amount': abs(diff) * price,
                'target_qty': target_qty,
                'current_qty': current_qty,
            })
        else:
            log.info(f"[{code}] {target['name']} 목표=현재={target_qty}주 → 주문 불필요")
    
    # 현재 보유 중이지만 목표에 없는 종목 → 전량 매도
    for code, info in holdings.items():
        if code not in TARGET_PORTFOLIO and info['qty'] > 0:
            orders.append({
                'action': 'SELL',
                'code': code,
                'name': info['name'],
                'qty': info['qty'],
                'price': prices.get(code, info['avg_price']),
                'amount': info['qty'] * prices.get(code, info['avg_price']),
                'target_qty': 0,
                'current_qty': info['qty'],
            })
    
    return orders


def main(dry_run=True):
    print("=" * 60)
    print("🛢️  C안 포트폴리오 — 모의투자 주문")
    print(f"   모드: {'🔍 DRY-RUN (주문 안 넣음)' if dry_run else '🚀 실주문'}")
    print("=" * 60)
    
    # 1. 토큰 확인
    token = get_access_token()
    print(f"✅ 토큰 OK")
    
    # 2. 현재 잔고
    print("\n📊 현재 보유 현황:")
    holdings = get_current_holdings()
    for code, info in holdings.items():
        print(f"   {info['name']} ({code}): {info['qty']}주, 평가 {info['eval_amt']:,}원")
    if not holdings:
        print("   (보유 종목 없음)")
    
    # 3. 현재가 조회
    print("\n💰 현재가 조회:")
    prices = {}
    all_codes = set(TARGET_PORTFOLIO.keys()) | set(holdings.keys())
    for code in all_codes:
        price = get_current_price(code)
        prices[code] = price
        name = TARGET_PORTFOLIO.get(code, {}).get('name', holdings.get(code, {}).get('name', code))
        print(f"   {name} ({code}): {price:,.0f}원")
        time.sleep(1.0)  # API 속도 제한 (모의투자 초당 1건)
    
    # 4. 주문 계산
    print("\n📋 주문 계획:")
    orders = calculate_orders(holdings, prices)
    
    # 매도 먼저, 매수 나중에
    sell_orders = [o for o in orders if o['action'] == 'SELL']
    buy_orders = [o for o in orders if o['action'] == 'BUY']
    
    total_sell = sum(o['amount'] for o in sell_orders)
    total_buy = sum(o['amount'] for o in buy_orders)
    
    if sell_orders:
        print("\n  [매도]")
        for o in sell_orders:
            print(f"   🔴 {o['name']} ({o['code']}): {o['current_qty']}→{o['target_qty']}주 "
                  f"({o['qty']}주 매도, 약 {o['amount']:,.0f}원)")
    
    if buy_orders:
        print("\n  [매수]")
        for o in buy_orders:
            print(f"   🟢 {o['name']} ({o['code']}): {o['current_qty']}→{o['target_qty']}주 "
                  f"({o['qty']}주 매수, 약 {o['amount']:,.0f}원)")
    
    print(f"\n  매도 합계: {total_sell:,.0f}원")
    print(f"  매수 합계: {total_buy:,.0f}원")
    
    if not orders:
        print("  ✅ 주문 불필요 — 이미 목표 포트폴리오와 동일")
        return
    
    # 5. 주문 실행
    if dry_run:
        print("\n⚠️  DRY-RUN 모드: 실제 주문은 넣지 않았어")
        print("   실주문하려면: python3 oil_hedge_order.py --execute")
        return
    
    print("\n🚀 주문 실행 중...")
    
    # 매도 먼저
    for o in sell_orders:
        print(f"   매도: {o['name']} {o['qty']}주...")
        result = sell_market(o['code'], o['qty'])
        send_order_discord("SELL", o['code'], o['name'], o['qty'], o['price'], result)
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['msg']}")
        time.sleep(0.5)
    
    # 매수
    for o in buy_orders:
        print(f"   매수: {o['name']} {o['qty']}주...")
        result = buy_market(o['code'], o['qty'])
        send_order_discord("BUY", o['code'], o['name'], o['qty'], o['price'], result)
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['msg']}")
        time.sleep(0.5)
    
    print("\n✅ 주문 완료!")
    
    # 최종 잔고 확인
    print("\n📊 주문 후 잔고:")
    time.sleep(1)
    final_holdings = get_current_holdings()
    for code, info in final_holdings.items():
        print(f"   {info['name']} ({code}): {info['qty']}주, 평가 {info['eval_amt']:,}원")


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    main(dry_run=not execute)
