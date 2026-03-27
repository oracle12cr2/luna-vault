#!/home/anaconda3/bin/python3
# -*- coding: utf-8 -*-
"""
매일 자동 손익 분석 리포트
- KIS 모의투자 API에서 잔고/손익 조회
- Oracle DB에 일별 스냅샷 저장
- Discord + 메일 리포트 발송

cron: 0 16 * * 1-5 (평일 16:00, 장 마감 후)
"""

import os
import requests
import json
import smtplib
import oracledb
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pathlib import Path

# KIS 모의투자 설정
KIS_BASE = "https://openapivts.koreainvestment.com:29443"
KIS_APP_KEY = "PSn3EK6GBUcrb5pcAatX6qXr1Pa07laVUYUe"
KIS_APP_SECRET = "d3o9g5OfF55qwbM9CizR/nUDuNNgWhjOtnCn5fzOHCS5B9VM7mWFB2HsNFK5rJlHiQuts5vB4kxQiZS0w0+mAP9hP4L4OGW+aG8wW0PfI6HvU2JSqd7AHghIisAKuYxjzWMXjM5ctpXErzf/gpL/Y16BTQqzGogIYuIJ7gCGVB33VoHELhQ="
KIS_CANO = "50173951"
KIS_ACNT_PRDT = "01"

# Oracle
ORACLE_USER = "app_user"
ORACLE_PASS = "oracle"
ORACLE_DSN = "192.168.50.35:1521/PROD"

# Discord
DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1480884778768007259/_bqFiBBOXAv3n5seIVUogrnqTvadU6twHJQmx9e7sa1jWNEz7CDwSyXJ00Ar73VhpwlG"

# 메일
SMTP_SERVER = "smtp.naver.com"
SMTP_PORT = 587
MAIL_FROM = "kto2004@naver.com"
MAIL_PW = "YM512KB4JEB8"
MAIL_TO = "kto2004@naver.com"

INITIAL_CAPITAL = 10_000_000
TOKEN_FILE = "/tmp/kis_mock_token_pnl.json"
LOG_FILE = "/var/log/stock/daily_pnl.log"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")


def get_kis_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            cached = json.load(f)
            if datetime.fromisoformat(cached['expires_at']) > datetime.utcnow():
                return cached['token']

    r = requests.post(f"{KIS_BASE}/oauth2/tokenP", json={
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
    })
    data = r.json()
    token = data['access_token']
    expires = (datetime.utcnow() + timedelta(hours=23)).isoformat()
    with open(TOKEN_FILE, 'w') as f:
        json.dump({"token": token, "expires_at": expires}, f)
    return token


def get_balance():
    token = get_kis_token()
    params = {
        "CANO": KIS_CANO, "ACNT_PRDT_CD": KIS_ACNT_PRDT,
        "AFHR_FLPR_YN": "N", "OFL_YN": "", "INQR_DVSN": "02",
        "UNPR_DVSN": "01", "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N", "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "", "CTX_AREA_NK100": "",
    }
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": "VTTC8434R",
        "content-type": "application/json; charset=utf-8",
    }
    r = requests.get(f"{KIS_BASE}/uapi/domestic-stock/v1/trading/inquire-balance",
                     params=params, headers=headers)
    return r.json()


def save_snapshot(conn, holdings, summary):
    """일별 스냅샷 DB 저장"""
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    # 기존 오늘 데이터 삭제 (중복 방지)
    cur.execute("DELETE FROM APP_USER.TB_PNL_DAILY WHERE SNAP_DATE = TO_DATE(:1, 'YYYY-MM-DD')", [today])

    cur.execute("""
        INSERT INTO APP_USER.TB_PNL_DAILY 
        (SNAP_DATE, DEPOSIT, PCHS_AMT, EVLU_AMT, EVLU_PNL, TOT_EVLU, DAILY_RETURN, TOTAL_RETURN, HOLDINGS_JSON)
        VALUES (TO_DATE(:1,'YYYY-MM-DD'), :2, :3, :4, :5, :6, :7, :8, :9)
    """, [
        today,
        summary['deposit'],
        summary['pchs_amt'],
        summary['evlu_amt'],
        summary['evlu_pnl'],
        summary['tot_evlu'],
        summary['daily_return'],
        summary['total_return'],
        json.dumps(holdings, ensure_ascii=False),
    ])
    conn.commit()
    cur.close()


def get_yesterday_evlu(conn):
    """전일 총평가 조회"""
    cur = conn.cursor()
    cur.execute("""
        SELECT TOT_EVLU FROM APP_USER.TB_PNL_DAILY 
        WHERE SNAP_DATE < TRUNC(SYSDATE) 
        ORDER BY SNAP_DATE DESC FETCH FIRST 1 ROW ONLY
    """)
    row = cur.fetchone()
    cur.close()
    return row[0] if row else INITIAL_CAPITAL


def send_discord(content):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": content}, timeout=10)
    except Exception as e:
        log(f"Discord 실패: {e}")


def send_mail(subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = MAIL_TO
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(MAIL_FROM, MAIL_PW)
            s.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
    except Exception as e:
        log(f"메일 실패: {e}")


def main():
    log("=" * 50)
    log("📈 일일 손익 분석 리포트")
    log("=" * 50)

    # 1. KIS API 잔고 조회
    result = get_balance()
    if result.get('rt_cd') != '0':
        log(f"API 에러: {result.get('msg1')}")
        return

    # 보유 종목
    holdings = []
    for h in result.get('output1', []):
        qty = int(h.get('hldg_qty', 0))
        if qty <= 0:
            continue
        holdings.append({
            'name': h.get('prdt_name', ''),
            'code': h.get('pdno', ''),
            'qty': qty,
            'avg_price': round(float(h.get('pchs_avg_pric', 0))),
            'cur_price': int(h.get('prpr', 0)),
            'pnl': int(h.get('evlu_pfls_amt', 0)),
            'pnl_pct': float(h.get('evlu_pfls_rt', 0)),
            'evlu_amt': int(h.get('evlu_amt', 0)),
        })

    s = (result.get('output2') or [{}])[0]
    deposit = int(s.get('dnca_tot_amt', 0))
    pchs_amt = int(s.get('pchs_amt_smtl_amt', 0))
    evlu_amt = int(s.get('evlu_amt_smtl_amt', 0))
    evlu_pnl = int(s.get('evlu_pfls_smtl_amt', 0))
    tot_evlu = int(s.get('tot_evlu_amt', 0))

    # 2. DB 연결 + 전일 대비 수익률
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
    yesterday_evlu = get_yesterday_evlu(conn)
    daily_return = round((tot_evlu - yesterday_evlu) / yesterday_evlu * 100, 2) if yesterday_evlu else 0
    total_return = round((tot_evlu - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100, 2)

    summary = {
        'deposit': deposit,
        'pchs_amt': pchs_amt,
        'evlu_amt': evlu_amt,
        'evlu_pnl': evlu_pnl,
        'tot_evlu': tot_evlu,
        'daily_return': daily_return,
        'total_return': total_return,
    }

    # 3. DB 저장
    save_snapshot(conn, holdings, summary)
    conn.close()

    # 4. 리포트 생성
    daily_emoji = '📈' if daily_return >= 0 else '📉'
    total_emoji = '🟢' if total_return >= 0 else '🔴'

    lines = [
        f"{daily_emoji} **일일 손익 리포트** ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "",
        f"💰 총 평가: **{tot_evlu:,}원**",
        f"📊 전일 대비: **{daily_return:+.2f}%** ({tot_evlu - yesterday_evlu:+,}원)",
        f"{total_emoji} 총 수익률: **{total_return:+.2f}%** ({tot_evlu - INITIAL_CAPITAL:+,}원)",
        f"💵 예수금: {deposit:,}원",
        "",
        "**보유 종목:**",
    ]

    for h in holdings:
        pnl_icon = '🟢' if h['pnl'] >= 0 else '🔴'
        lines.append(
            f"  {pnl_icon} {h['name']} | {h['qty']}주 | "
            f"{h['cur_price']:,}원 | {h['pnl']:+,}원 ({h['pnl_pct']:+.1f}%)"
        )

    if not holdings:
        lines.append("  (보유 종목 없음)")

    report = "\n".join(lines)
    log(report)

    # 5. Discord + 메일
    send_discord(report)
    send_mail(
        f"[투자] 일일 리포트 {daily_return:+.2f}% ({datetime.now().strftime('%m/%d')})",
        report.replace('**', '').replace('`', '')
    )

    log("완료")


if __name__ == "__main__":
    main()
