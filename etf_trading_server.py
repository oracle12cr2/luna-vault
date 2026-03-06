#!/usr/bin/env python3
"""
ETF 가상매매 시스템
- FastAPI + SQLite + 네이버 실시간 데이터
- 포트 8889
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import threading
import time
import json

app = FastAPI(title="ETF 가상매매")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = Path(__file__).parent / "etf_trading.db"
FEE_RATE = 0.00015  # 0.015%

ETF_LIST = {
    "069500": "KODEX 200",
    "122630": "KODEX 레버리지",
    "114800": "KODEX 인버스",
    "252670": "KODEX 2X인버스",
    "102110": "TIGER 200",
    "102780": "KODEX 삼성그룹",
    "133690": "TIGER 나스닥100",
    "229200": "KODEX 코스닥150",
    "091160": "KODEX 반도체",
    "305540": "TIGER 2차전지테마",
}

# 실시간 가격 캐시
price_cache = {}
price_lock = threading.Lock()


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY,
            initial_balance REAL DEFAULT 200000000,
            cash_balance REAL DEFAULT 200000000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL UNIQUE,
            stock_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            avg_price REAL DEFAULT 0,
            total_cost REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            fee REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 계좌 초기화
    row = conn.execute("SELECT COUNT(*) as cnt FROM account").fetchone()
    if row["cnt"] == 0:
        conn.execute("INSERT INTO account (id, initial_balance, cash_balance) VALUES (1, 200000000, 200000000)")
    conn.commit()
    conn.close()


def fetch_price(stock_code: str) -> dict | None:
    """네이버에서 현재가 + 일봉 OHLCV 가져오기"""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://fchart.stock.naver.com/sise.naver"
    try:
        # 일봉에서 당일 시가/고가/저가/종가/거래량
        resp = requests.get(url, params={"timeframe": "day", "count": 1, "requestType": 0, "symbol": stock_code},
                          timeout=5, headers=headers)
        resp.encoding = "euc-kr"
        root = ET.fromstring(resp.text)
        chartdata = root.find("chartdata")
        if chartdata is None:
            return None
        items = chartdata.findall("item")
        if not items:
            return None
        parts = items[-1].get("data", "").split("|")
        if len(parts) < 6:
            return None
        day_open = int(parts[1]) if parts[1] != "null" else 0
        day_high = int(parts[2]) if parts[2] != "null" else 0
        day_low = int(parts[3]) if parts[3] != "null" else 0
        price = int(parts[4]) if parts[4] != "null" else 0
        volume = int(parts[5]) if parts[5] != "null" else 0
        if price == 0:
            return None
        return {
            "code": stock_code,
            "name": ETF_LIST.get(stock_code, chartdata.get("name", "")),
            "price": price,
            "volume": volume,
            "open": day_open,
            "high": day_high,
            "low": day_low,
        }
    except Exception:
        return None


def fetch_all_prices():
    """모든 ETF 가격 갱신"""
    global price_cache
    new_cache = {}
    for code, name in ETF_LIST.items():
        data = fetch_price(code)
        if data:
            data["updated"] = datetime.now().isoformat()
            new_cache[code] = data
        time.sleep(0.2)
    with price_lock:
        price_cache.update(new_cache)


def price_updater():
    """백그라운드 가격 갱신 스레드"""
    while True:
        try:
            fetch_all_prices()
        except Exception:
            pass
        time.sleep(60)


class TradeRequest(BaseModel):
    code: str
    quantity: int


@app.on_event("startup")
def startup():
    init_db()
    fetch_all_prices()
    t = threading.Thread(target=price_updater, daemon=True)
    t.start()


@app.get("/api/prices")
def get_prices():
    with price_lock:
        return {"prices": list(price_cache.values()), "timestamp": datetime.now().isoformat()}


@app.get("/api/account")
def get_account():
    conn = get_db()
    acc = conn.execute("SELECT * FROM account WHERE id=1").fetchone()
    portfolio = conn.execute("SELECT * FROM portfolio WHERE quantity > 0").fetchall()

    total_eval = 0
    holdings = []
    for p in portfolio:
        with price_lock:
            current = price_cache.get(p["stock_code"], {}).get("price", p["avg_price"])
        eval_amount = current * p["quantity"]
        profit = eval_amount - p["total_cost"]
        profit_rate = (profit / p["total_cost"] * 100) if p["total_cost"] > 0 else 0
        total_eval += eval_amount
        holdings.append({
            "code": p["stock_code"],
            "name": p["stock_name"],
            "quantity": p["quantity"],
            "avgPrice": p["avg_price"],
            "currentPrice": current,
            "totalCost": p["total_cost"],
            "evalAmount": eval_amount,
            "profit": profit,
            "profitRate": round(profit_rate, 2),
        })

    cash = acc["cash_balance"]
    total_assets = cash + total_eval
    total_profit = total_assets - acc["initial_balance"]
    total_profit_rate = (total_profit / acc["initial_balance"] * 100)

    conn.close()
    return {
        "initialBalance": acc["initial_balance"],
        "cashBalance": cash,
        "totalEval": total_eval,
        "totalAssets": total_assets,
        "totalProfit": total_profit,
        "totalProfitRate": round(total_profit_rate, 2),
        "holdings": holdings,
    }


@app.get("/api/portfolio")
def get_portfolio():
    return get_account()["holdings"]


@app.post("/api/buy")
def buy(req: TradeRequest):
    if req.code not in ETF_LIST:
        raise HTTPException(400, "잘못된 종목코드")
    if req.quantity <= 0:
        raise HTTPException(400, "수량은 1 이상")

    with price_lock:
        pdata = price_cache.get(req.code)
    if not pdata:
        raise HTTPException(400, "시세 정보 없음")

    price = pdata["price"]
    total = price * req.quantity
    fee = round(total * FEE_RATE)
    required = total + fee

    conn = get_db()
    acc = conn.execute("SELECT cash_balance FROM account WHERE id=1").fetchone()
    if acc["cash_balance"] < required:
        conn.close()
        raise HTTPException(400, f"잔고 부족 (필요: {required:,.0f}원, 보유: {acc['cash_balance']:,.0f}원)")

    # 잔고 차감
    conn.execute("UPDATE account SET cash_balance = cash_balance - ? WHERE id=1", (required,))

    # 포트폴리오 업데이트
    existing = conn.execute("SELECT * FROM portfolio WHERE stock_code=?", (req.code,)).fetchone()
    if existing:
        new_qty = existing["quantity"] + req.quantity
        new_cost = existing["total_cost"] + total
        new_avg = new_cost / new_qty
        conn.execute("UPDATE portfolio SET quantity=?, avg_price=?, total_cost=? WHERE stock_code=?",
                     (new_qty, round(new_avg), new_cost, req.code))
    else:
        conn.execute("INSERT INTO portfolio (stock_code, stock_name, quantity, avg_price, total_cost) VALUES (?,?,?,?,?)",
                     (req.code, ETF_LIST[req.code], req.quantity, price, total))

    # 거래 기록
    conn.execute("INSERT INTO trades (stock_code, stock_name, trade_type, quantity, price, total_amount, fee) VALUES (?,?,?,?,?,?,?)",
                 (req.code, ETF_LIST[req.code], "BUY", req.quantity, price, total, fee))
    conn.commit()
    conn.close()

    return {"status": "ok", "type": "BUY", "code": req.code, "name": ETF_LIST[req.code],
            "quantity": req.quantity, "price": price, "total": total, "fee": fee}


@app.post("/api/sell")
def sell(req: TradeRequest):
    if req.code not in ETF_LIST:
        raise HTTPException(400, "잘못된 종목코드")
    if req.quantity <= 0:
        raise HTTPException(400, "수량은 1 이상")

    with price_lock:
        pdata = price_cache.get(req.code)
    if not pdata:
        raise HTTPException(400, "시세 정보 없음")

    price = pdata["price"]
    total = price * req.quantity
    fee = round(total * FEE_RATE)
    proceeds = total - fee

    conn = get_db()
    existing = conn.execute("SELECT * FROM portfolio WHERE stock_code=?", (req.code,)).fetchone()
    if not existing or existing["quantity"] < req.quantity:
        conn.close()
        hold = existing["quantity"] if existing else 0
        raise HTTPException(400, f"보유 수량 부족 (보유: {hold}주)")

    new_qty = existing["quantity"] - req.quantity
    # 매도 비율에 따른 원가 차감
    sell_ratio = req.quantity / existing["quantity"]
    cost_reduction = existing["total_cost"] * sell_ratio

    if new_qty == 0:
        conn.execute("DELETE FROM portfolio WHERE stock_code=?", (req.code,))
    else:
        new_cost = existing["total_cost"] - cost_reduction
        new_avg = new_cost / new_qty
        conn.execute("UPDATE portfolio SET quantity=?, avg_price=?, total_cost=? WHERE stock_code=?",
                     (new_qty, round(new_avg), new_cost, req.code))

    # 잔고 추가
    conn.execute("UPDATE account SET cash_balance = cash_balance + ? WHERE id=1", (proceeds,))

    # 거래 기록
    conn.execute("INSERT INTO trades (stock_code, stock_name, trade_type, quantity, price, total_amount, fee) VALUES (?,?,?,?,?,?,?)",
                 (req.code, ETF_LIST[req.code], "SELL", req.quantity, price, total, fee))
    conn.commit()
    conn.close()

    return {"status": "ok", "type": "SELL", "code": req.code, "name": ETF_LIST[req.code],
            "quantity": req.quantity, "price": price, "total": total, "fee": fee}


@app.get("/api/trades")
def get_trades(limit: int = 50):
    conn = get_db()
    rows = conn.execute("SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return {"trades": [dict(r) for r in rows]}


@app.post("/api/reset")
def reset_account():
    """계좌 초기화"""
    conn = get_db()
    conn.execute("UPDATE account SET cash_balance = 200000000 WHERE id=1")
    conn.execute("DELETE FROM portfolio")
    conn.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "계좌가 초기화되었습니다"}


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_PAGE)


HTML_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>💹 ETF 가상매매</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',Tahoma,sans-serif; background:#0f0f23; color:#e0e0e0; min-height:100vh; }
.container { max-width:1400px; margin:0 auto; padding:20px; }
h1 { text-align:center; font-size:2rem; margin-bottom:20px; color:#00d4ff; }
.subtitle { text-align:center; color:#888; margin-bottom:25px; font-size:0.9rem; }

/* 계좌 요약 */
.account-summary {
    display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
    gap:15px; margin-bottom:25px;
}
.stat-card {
    background:#1a1a2e; border-radius:12px; padding:20px;
    border:1px solid #2a2a4a; text-align:center;
}
.stat-card .label { color:#888; font-size:0.85rem; margin-bottom:8px; }
.stat-card .value { font-size:1.5rem; font-weight:bold; }
.stat-card .value.positive { color:#00e676; }
.stat-card .value.negative { color:#ff5252; }

/* ETF 시세 테이블 */
.section { background:#1a1a2e; border-radius:12px; padding:20px; margin-bottom:20px; border:1px solid #2a2a4a; }
.section h2 { color:#00d4ff; margin-bottom:15px; font-size:1.2rem; }
table { width:100%; border-collapse:collapse; }
th { background:#16213e; color:#00d4ff; padding:12px 8px; text-align:right; font-size:0.85rem; }
th:first-child, td:first-child { text-align:left; }
td { padding:10px 8px; border-bottom:1px solid #2a2a4a; text-align:right; font-size:0.9rem; }
tr:hover { background:#16213e; }
.positive { color:#00e676; }
.negative { color:#ff5252; }

/* 매매 버튼 */
.btn { padding:6px 14px; border:none; border-radius:6px; cursor:pointer; font-size:0.8rem; font-weight:bold; transition:0.2s; }
.btn-buy { background:#00e676; color:#000; }
.btn-buy:hover { background:#00c853; }
.btn-sell { background:#ff5252; color:#fff; }
.btn-sell:hover { background:#d32f2f; }
.btn-reset { background:#ff9800; color:#000; padding:8px 20px; font-size:0.9rem; }
.btn-reset:hover { background:#f57c00; }

/* 모달 */
.modal-overlay {
    display:none; position:fixed; top:0; left:0; width:100%; height:100%;
    background:rgba(0,0,0,0.7); z-index:1000; align-items:center; justify-content:center;
}
.modal-overlay.active { display:flex; }
.modal {
    background:#1a1a2e; border-radius:16px; padding:30px; width:400px; max-width:90%;
    border:1px solid #2a2a4a;
}
.modal h3 { color:#00d4ff; margin-bottom:20px; text-align:center; }
.modal .info { color:#888; margin-bottom:15px; text-align:center; }
.modal input {
    width:100%; padding:12px; background:#0f0f23; border:1px solid #2a2a4a;
    border-radius:8px; color:#fff; font-size:1.1rem; text-align:center; margin-bottom:10px;
}
.modal .price-info { text-align:center; margin-bottom:15px; font-size:1.3rem; font-weight:bold; }
.modal .total-info { text-align:center; margin-bottom:20px; color:#888; }
.modal .modal-buttons { display:flex; gap:10px; }
.modal .modal-buttons .btn { flex:1; padding:12px; font-size:1rem; }
.btn-cancel { background:#333; color:#fff; }

/* 그리드 레이아웃 */
.bottom-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
@media (max-width:900px) { .bottom-grid { grid-template-columns:1fr; } }

/* 거래내역 */
.trade-buy { color:#00e676; }
.trade-sell { color:#ff5252; }

/* 상태바 */
.status-bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; }
.status-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#00e676; margin-right:6px; animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
.last-update { color:#666; font-size:0.8rem; }

/* 알림 토스트 */
.toast {
    position:fixed; top:20px; right:20px; padding:15px 25px; border-radius:10px;
    color:#fff; font-weight:bold; z-index:2000; transform:translateX(120%);
    transition:transform 0.3s ease;
}
.toast.show { transform:translateX(0); }
.toast.success { background:#00c853; }
.toast.error { background:#d32f2f; }
</style>
</head>
<body>
<div class="container">
    <h1>💹 ETF 가상매매 시스템</h1>
    <div class="subtitle">실시간 데이터 기반 모의투자 | 초기자본 2억원 | 수수료 0.015%</div>

    <div class="account-summary" id="account-summary"></div>

    <div class="section">
        <div class="status-bar">
            <h2>📊 ETF 실시간 시세</h2>
            <div>
                <span class="status-dot"></span>
                <span class="last-update" id="last-update">갱신 중...</span>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="text-align:left">종목명</th>
                    <th>현재가</th>
                    <th>시가</th>
                    <th>고가</th>
                    <th>저가</th>
                    <th>거래량</th>
                    <th>등락</th>
                    <th>매매</th>
                </tr>
            </thead>
            <tbody id="price-table"></tbody>
        </table>
    </div>

    <div class="bottom-grid">
        <div class="section">
            <h2>💼 보유 종목</h2>
            <table>
                <thead>
                    <tr><th style="text-align:left">종목</th><th>수량</th><th>평균단가</th><th>현재가</th><th>평가손익</th><th>수익률</th></tr>
                </thead>
                <tbody id="portfolio-table"></tbody>
            </table>
            <div id="no-holdings" style="text-align:center;color:#666;padding:30px;">보유 종목 없음</div>
        </div>

        <div class="section">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                <h2>📜 거래 내역</h2>
                <button class="btn btn-reset" onclick="resetAccount()">🔄 계좌 초기화</button>
            </div>
            <div id="trades-list" style="max-height:400px;overflow-y:auto;"></div>
        </div>
    </div>
</div>

<!-- 매매 모달 -->
<div class="modal-overlay" id="trade-modal">
    <div class="modal">
        <h3 id="modal-title">매수</h3>
        <div class="info" id="modal-stock-name"></div>
        <div class="price-info" id="modal-price"></div>
        <input type="number" id="modal-quantity" placeholder="수량 입력" min="1" oninput="updateTotal()">
        <div class="total-info" id="modal-total">총 금액: 0원</div>
        <div class="modal-buttons">
            <button class="btn btn-cancel" onclick="closeModal()">취소</button>
            <button class="btn" id="modal-confirm" onclick="confirmTrade()">확인</button>
        </div>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
const API = window.location.origin;
let currentTrade = { type:'', code:'', price:0 };

function fmt(n) { return n != null ? Number(n).toLocaleString('ko-KR') : '-'; }

function showToast(msg, type='success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast ' + type + ' show';
    setTimeout(() => t.classList.remove('show'), 3000);
}

function openModal(type, code, name, price) {
    currentTrade = { type, code, price };
    document.getElementById('modal-title').textContent = type === 'BUY' ? '📈 매수' : '📉 매도';
    document.getElementById('modal-stock-name').textContent = `${name} (${code})`;
    document.getElementById('modal-price').textContent = fmt(price) + '원';
    document.getElementById('modal-quantity').value = '';
    document.getElementById('modal-total').textContent = '총 금액: 0원';
    const btn = document.getElementById('modal-confirm');
    btn.className = type === 'BUY' ? 'btn btn-buy' : 'btn btn-sell';
    btn.textContent = type === 'BUY' ? '매수' : '매도';
    document.getElementById('trade-modal').classList.add('active');
    document.getElementById('modal-quantity').focus();
}

function closeModal() { document.getElementById('trade-modal').classList.remove('active'); }

function updateTotal() {
    const qty = parseInt(document.getElementById('modal-quantity').value) || 0;
    const total = qty * currentTrade.price;
    const fee = Math.round(total * 0.00015);
    document.getElementById('modal-total').textContent =
        `총 금액: ${fmt(total)}원 (수수료: ${fmt(fee)}원)`;
}

async function confirmTrade() {
    const qty = parseInt(document.getElementById('modal-quantity').value);
    if (!qty || qty <= 0) { showToast('수량을 입력하세요', 'error'); return; }
    try {
        const url = currentTrade.type === 'BUY' ? '/api/buy' : '/api/sell';
        const resp = await fetch(API + url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ code: currentTrade.code, quantity: qty })
        });
        const data = await resp.json();
        if (!resp.ok) { showToast(data.detail || '오류 발생', 'error'); return; }
        const typeStr = data.type === 'BUY' ? '매수' : '매도';
        showToast(`${typeStr} 완료: ${data.name} ${data.quantity}주 @ ${fmt(data.price)}원`);
        closeModal();
        refreshAll();
    } catch (e) { showToast('네트워크 오류', 'error'); }
}

async function resetAccount() {
    if (!confirm('정말 계좌를 초기화할까요? 모든 거래 내역이 삭제됩니다.')) return;
    await fetch(API + '/api/reset', { method: 'POST' });
    showToast('계좌가 초기화되었습니다');
    refreshAll();
}

async function loadPrices() {
    try {
        const resp = await fetch(API + '/api/prices');
        const data = await resp.json();
        const tbody = document.getElementById('price-table');
        tbody.innerHTML = data.prices.map(p => {
            const change = p.price - p.open;
            const changeRate = p.open > 0 ? (change / p.open * 100) : 0;
            const cls = change > 0 ? 'positive' : change < 0 ? 'negative' : '';
            const sign = change > 0 ? '+' : '';
            return `<tr>
                <td style="text-align:left;font-weight:bold">${p.name}<br><span style="color:#666;font-size:0.75rem">${p.code}</span></td>
                <td class="${cls}" style="font-weight:bold">${fmt(p.price)}</td>
                <td>${fmt(p.open)}</td>
                <td class="positive">${fmt(p.high)}</td>
                <td class="negative">${fmt(p.low)}</td>
                <td>${fmt(p.volume)}</td>
                <td class="${cls}">${sign}${fmt(change)} (${sign}${changeRate.toFixed(2)}%)</td>
                <td>
                    <button class="btn btn-buy" onclick="openModal('BUY','${p.code}','${p.name}',${p.price})">매수</button>
                    <button class="btn btn-sell" onclick="openModal('SELL','${p.code}','${p.name}',${p.price})">매도</button>
                </td>
            </tr>`;
        }).join('');
        document.getElementById('last-update').textContent = '갱신: ' + new Date().toLocaleTimeString('ko-KR');
    } catch (e) { console.error(e); }
}

async function loadAccount() {
    try {
        const resp = await fetch(API + '/api/account');
        const data = await resp.json();
        const cls = data.totalProfit >= 0 ? 'positive' : 'negative';
        const sign = data.totalProfit >= 0 ? '+' : '';
        document.getElementById('account-summary').innerHTML = `
            <div class="stat-card"><div class="label">💰 총 자산</div><div class="value">${fmt(Math.round(data.totalAssets))}원</div></div>
            <div class="stat-card"><div class="label">💵 현금</div><div class="value">${fmt(Math.round(data.cashBalance))}원</div></div>
            <div class="stat-card"><div class="label">📊 평가금액</div><div class="value">${fmt(Math.round(data.totalEval))}원</div></div>
            <div class="stat-card"><div class="label">📈 총 수익</div><div class="value ${cls}">${sign}${fmt(Math.round(data.totalProfit))}원 (${sign}${data.totalProfitRate}%)</div></div>
        `;
        // 포트폴리오
        const ptbody = document.getElementById('portfolio-table');
        const nohold = document.getElementById('no-holdings');
        if (data.holdings.length === 0) {
            ptbody.innerHTML = '';
            nohold.style.display = 'block';
        } else {
            nohold.style.display = 'none';
            ptbody.innerHTML = data.holdings.map(h => {
                const cls = h.profit >= 0 ? 'positive' : 'negative';
                const sign = h.profit >= 0 ? '+' : '';
                return `<tr>
                    <td style="text-align:left">${h.name}<br><span style="color:#666;font-size:0.75rem">${h.code}</span></td>
                    <td>${fmt(h.quantity)}</td>
                    <td>${fmt(Math.round(h.avgPrice))}</td>
                    <td>${fmt(h.currentPrice)}</td>
                    <td class="${cls}">${sign}${fmt(Math.round(h.profit))}</td>
                    <td class="${cls}">${sign}${h.profitRate}%</td>
                </tr>`;
            }).join('');
        }
    } catch (e) { console.error(e); }
}

async function loadTrades() {
    try {
        const resp = await fetch(API + '/api/trades');
        const data = await resp.json();
        const div = document.getElementById('trades-list');
        if (data.trades.length === 0) {
            div.innerHTML = '<div style="text-align:center;color:#666;padding:30px;">거래 내역 없음</div>';
            return;
        }
        div.innerHTML = '<table style="width:100%"><thead><tr><th style="text-align:left">시간</th><th>구분</th><th style="text-align:left">종목</th><th>수량</th><th>단가</th><th>금액</th></tr></thead><tbody>' +
            data.trades.map(t => {
                const cls = t.trade_type === 'BUY' ? 'trade-buy' : 'trade-sell';
                const label = t.trade_type === 'BUY' ? '매수' : '매도';
                const time = new Date(t.created_at).toLocaleString('ko-KR', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
                return `<tr>
                    <td style="text-align:left;color:#888;font-size:0.8rem">${time}</td>
                    <td class="${cls}" style="font-weight:bold">${label}</td>
                    <td style="text-align:left">${t.stock_name}</td>
                    <td>${fmt(t.quantity)}</td>
                    <td>${fmt(t.price)}</td>
                    <td>${fmt(Math.round(t.total_amount))}</td>
                </tr>`;
            }).join('') + '</tbody></table>';
    } catch (e) { console.error(e); }
}

function refreshAll() { loadPrices(); loadAccount(); loadTrades(); }

// 모달에서 엔터키
document.getElementById('modal-quantity').addEventListener('keydown', e => {
    if (e.key === 'Enter') confirmTrade();
});

// 초기 로드 + 30초 갱신
refreshAll();
setInterval(refreshAll, 60000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8889)
