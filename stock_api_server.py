#!/usr/bin/env python3
"""
주식 실시간 대시보드 FastAPI 서버
- Redis(192.168.50.3)에서 데이터 읽기
- /stocks, /health, /stock/{code} API
- stock_realtime.html 서빙
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
from datetime import datetime
from pathlib import Path

app = FastAPI(title="주식 실시간 대시보드")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_HOST = "192.168.50.3"
REDIS_PORT = 6379
REDIS_PASSWORD = "redis"

STOCK_CODES = {
    "005930": "삼성전자",
    "066570": "LG전자",
    "005380": "현대차",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "373220": "LG에너지솔루션",
    "105560": "KB금융",
    "000270": "기아",
    "207940": "삼성바이오로직스",
}


def get_redis():
    return redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
        decode_responses=True, socket_timeout=5
    )


def get_latest_data(r, stock_code: str) -> dict | None:
    """ts:stock:{code}:* 키 중 가장 최신 데이터 반환"""
    keys = sorted(r.keys(f"ts:stock:{stock_code}:*"))
    if not keys:
        return None
    raw = r.get(keys[-1])
    if not raw:
        return None
    return json.loads(raw)


@app.get("/health")
def health():
    try:
        r = get_redis()
        stock_keys = r.keys("ts:stock:*")
        return {"status": "ok", "keys": len(stock_keys), "redis": REDIS_HOST}
    except Exception as e:
        return {"status": "error", "message": str(e), "keys": 0}


@app.get("/stocks")
def stocks():
    try:
        r = get_redis()
        result = []
        for code, name in STOCK_CODES.items():
            data = get_latest_data(r, code)
            if not data:
                continue

            open_price_raw = r.get(f"open:stock:{code}")
            open_price = int(open_price_raw) if open_price_raw else None

            current_price = data.get("price", 0)
            change = (current_price - open_price) if open_price else 0
            change_rate = (change / open_price * 100) if open_price and open_price > 0 else 0

            result.append({
                "stockCode": code,
                "stockName": name,
                "currentPrice": current_price,
                "change": change,
                "changeRate": round(change_rate, 2),
                "volume": data.get("volume", 0),
                "lastUpdate": data.get("datetime", ""),
            })

        return {"stocks": result, "count": len(result), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"stocks": [], "count": 0, "error": str(e)}


@app.get("/stock/{code}")
def stock_detail(code: str):
    try:
        r = get_redis()
        data = get_latest_data(r, code)
        if not data:
            return {"error": "not found"}

        # history (최근 100개)
        history_raw = r.lrange(f"history:stock:{code}", 0, 99)
        history = []
        for item in history_raw:
            parts = item.split(":")
            if len(parts) == 2:
                history.append({"price": int(parts[0]), "timestamp": int(parts[1])})

        open_price_raw = r.get(f"open:stock:{code}")
        open_price = int(open_price_raw) if open_price_raw else None

        return {
            "current": data,
            "openPrice": open_price,
            "history": history,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/alerts")
def alerts():
    try:
        r = get_redis()
        alert_keys = r.keys("alert:stock:*")
        result = []
        for k in alert_keys:
            raw = r.get(k)
            if raw:
                result.append(json.loads(raw))
        return {"alerts": result, "count": len(result)}
    except Exception as e:
        return {"alerts": [], "error": str(e)}


@app.get("/stock_realtime.html", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path(__file__).parent / "stock_realtime.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>stock_realtime.html not found</h1>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
