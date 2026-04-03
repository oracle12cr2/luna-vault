#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-
"""
멀티팩터 스코어링 리포트
- 포트폴리오 3종목에 대해 통합 스코어 계산
- Discord 알림 + 로그 저장

cron: 30 8 * * 1-5 /home/anaconda3/bin/python3 /root/.openclaw/workspace/etf-backtest/multifactor_report.py
"""

import os
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"

import oracledb
import pandas as pd
import requests
import json
from datetime import datetime
from strategies.multifactor import multifactor_score

# 설정
ORACLE_USER = "stock"
ORACLE_PASS = "Oracle2026_em"
ORACLE_DSN  = "PROD_OGG"
ORACLE_LIB  = "/usr/lib/oracle/23/client64/lib"

DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1480884778768007259/_bqFiBBOXAv3n5seIVUogrnqTvadU6twHJQmx9e7sa1jWNEz7CDwSyXJ00Ar73VhpwlG"

LOG_FILE = "/var/log/stock/multifactor.log"

TARGETS = [
    {"code": "122630", "name": "KODEX 레버리지"},
    {"code": "102110", "name": "ACE 200"},  
    {"code": "279530", "name": "KODEX 고배당"},
]


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")


def send_discord(content):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": content}, timeout=10)
    except Exception as e:
        log(f"Discord 전송 실패: {e}")


def get_price_data(conn, stock_code, days=30):
    """일봉 데이터 조회"""
    sql = """
        SELECT TRADE_DT, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, CLOSE_PRICE, VOLUME
        FROM STOCK.TB_DAY_CANDLE
        WHERE STOCK_CODE = :1
        ORDER BY TRADE_DT DESC
        FETCH FIRST :2 ROWS ONLY
    """
    df = pd.read_sql(sql, conn, params=[stock_code, days])
    if df.empty:
        return None
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df = df.sort_values('date').reset_index(drop=True)
    return df


def get_investor_data(conn, stock_code, days=10):
    """투자자별 매매동향 조회"""
    sql = """
        SELECT TRADE_DT, FRGN_NET_VOL, ORGN_NET_VOL, PRSN_NET_VOL
        FROM STOCK.TB_INVESTOR_TREND
        WHERE STOCK_CODE = :1
        ORDER BY TRADE_DT DESC
        FETCH FIRST :2 ROWS ONLY
    """
    df = pd.read_sql(sql, conn, params=[stock_code, days])
    if df.empty:
        return None
    df.columns = ['trade_dt', 'frgn_net_vol', 'orgn_net_vol', 'prsn_net_vol']
    df = df.sort_values('trade_dt').reset_index(drop=True)
    return df


def main():
    log("=" * 50)
    log("📊 멀티팩터 스코어링 리포트")
    log("=" * 50)

    oracledb.init_oracle_client(lib_dir=ORACLE_LIB)
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)

    results = []
    for t in TARGETS:
        price_df = get_price_data(conn, t['code'])
        investor_df = get_investor_data(conn, t['code'])

        if price_df is None or len(price_df) < 15:
            log(f"  {t['name']}: 데이터 부족")
            continue

        result = multifactor_score(price_df, investor_df)
        result['name'] = t['name']
        result['code'] = t['code']
        result['price'] = int(price_df['close'].iloc[-1])
        results.append(result)

        log(f"  {t['name']}: 총합={result['total_score']}  기술={result['technical_score']}  수급={result['supply_score']}  모멘텀={result['momentum_score']}  → {result['signal']} ({result['confidence']})")

    conn.close()

    # Discord 알림
    if results:
        signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}
        conf_emoji = {'HIGH': '🔥', 'MEDIUM': '⚡', 'LOW': '💤'}

        lines = [f"📊 **멀티팩터 스코어링** ({datetime.now().strftime('%m/%d %H:%M')})", ""]
        for r in results:
            sig = signal_emoji.get(r['signal'], '⚪')
            conf = conf_emoji.get(r['confidence'], '')
            lines.append(
                f"{sig} **{r['name']}** {r['price']:,}원  "
                f"총합 **{r['total_score']}** "
                f"(기술 {r['technical_score']} / 수급 {r['supply_score']} / 모멘텀 {r['momentum_score']}) "
                f"{r['signal']} {conf}"
            )

        # 매수 추천
        buys = [r for r in results if r['signal'] == 'BUY']
        if buys:
            lines.append(f"\n🎯 매수 추천: {', '.join(r['name'] for r in buys)}")

        send_discord("\n".join(lines))

    log("완료")


if __name__ == "__main__":
    main()
