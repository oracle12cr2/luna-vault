#!/usr/bin/env python3
"""
Redis 데이터를 HTTP API로 제공하는 서버 (CORS 지원)
브라우저에서 Cross-Origin 요청 가능
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 모든 도메인에서 접근 허용

# Redis 연결
redis_client = redis.Redis(host='192.168.50.3', port=6379, password='redis', decode_responses=True)

@app.route('/health')
def health():
    try:
        redis_client.ping()
        return jsonify({
            "status": "ok",
            "redis": "connected",
            "keys": redis_client.dbsize(),
            "timestamp": datetime.now().isoformat(),
            "message": "API 서버 정상 작동!"
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stock/<stock_code>')
def get_stock(stock_code):
    try:
        data = redis_client.get(f'stats:stock:{stock_code}')
        if data:
            stock_data = json.loads(data)
            return jsonify({
                "stockCode": stock_code,
                "stockName": stock_data.get('stock_name', ''),
                "currentPrice": stock_data.get('current_price', 0),
                "changeRate": stock_data.get('change_rate', 0),
                "change": stock_data.get('change', 0),
                "volume": stock_data.get('volume', 0),
                "timestamp": stock_data.get('timestamp', 0),
                "lastUpdate": stock_data.get('last_update', ''),
                "success": True
            })
        else:
            return jsonify({
                "error": f"Stock {stock_code} not found",
                "success": False
            }), 404
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/stocks')
def get_all_stocks():
    try:
        stocks = []
        stock_keys = redis_client.keys('stats:stock:*')
        
        for key in stock_keys:
            data = redis_client.get(key)
            if data:
                try:
                    stock_data = json.loads(data)
                    stocks.append({
                        "stockCode": stock_data.get('stock_code', ''),
                        "stockName": stock_data.get('stock_name', ''),
                        "currentPrice": stock_data.get('current_price', 0),
                        "changeRate": round(stock_data.get('change_rate', 0), 2),
                        "change": stock_data.get('change', 0),
                        "volume": stock_data.get('volume', 0),
                        "lastUpdate": stock_data.get('last_update', '')
                    })
                except json.JSONDecodeError:
                    continue
        
        # 등락률 기준 정렬
        stocks.sort(key=lambda x: x['changeRate'], reverse=True)
        
        return jsonify({
            "stocks": stocks,
            "total": len(stocks),
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/ranking')
def get_ranking():
    try:
        ranking = redis_client.zrevrange('ranking:change_rate', 0, 9, withscores=True)
        result = []
        
        for member, score in ranking:
            if ':' in member:
                code, name = member.split(':', 1)
                result.append({
                    "rank": len(result) + 1,
                    "stockCode": code,
                    "stockName": name,
                    "changeRate": round(float(score), 2)
                })
        
        return jsonify({
            "ranking": result,
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/alerts')
def get_alerts():
    try:
        alert_keys = redis_client.keys('alert:stock:*')
        alerts = []
        
        for key in alert_keys:
            data = redis_client.get(key)
            if data:
                try:
                    alert_data = json.loads(data)
                    alerts.append(alert_data)
                except json.JSONDecodeError:
                    continue
        
        return jsonify({
            "alerts": alerts,
            "total": len(alerts),
            "timestamp": datetime.now().isoformat(),
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/test')
def test():
    """브라우저 연결 테스트용"""
    return jsonify({
        "message": "🎉 API 서버 연결 성공!",
        "timestamp": datetime.now().isoformat(),
        "cors": "enabled",
        "endpoints": [
            "/health",
            "/stocks", 
            "/stock/<code>",
            "/ranking",
            "/alerts",
            "/test"
        ]
    })

if __name__ == '__main__':
    print("🚀 Redis CORS API 서버 시작...")
    print("🌐 URL: http://192.168.50.56:5000")
    print("🔗 CORS: 모든 도메인 허용")
    print("📊 엔드포인트:")
    print("  /health - 서버 상태")
    print("  /test - 연결 테스트")
    print("  /stocks - 전체 종목")
    print("  /stock/<code> - 특정 종목")
    print("  /ranking - 변동률 순위")
    print("  /alerts - 급변동 알림")
    
    app.run(host='0.0.0.0', port=5000, debug=False)