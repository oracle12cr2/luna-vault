#!/home/anaconda3/bin/python3
"""
로또 당첨 확인 스크립트
- 최신 당첨번호를 동행복권 API → DB 저장
- 구매 이력과 매칭하여 당첨 여부/등수/금액 업데이트
- 결과 메일 발송
"""

import requests
import smtplib
import cx_Oracle
from email.mime.text import MIMEText
from datetime import datetime

# === 설정 ===
DB_DSN_STR = "192.168.50.35:1521/PROD"
DB_USER = "app_user"
DB_PASS = "oracle"

SMTP_SERVER = "smtp.naver.com"
SMTP_PORT = 587
MAIL_FROM = "kto2004@naver.com"
MAIL_PW = "YM512KB4JEB8"
MAIL_TO = "kto2004@naver.com"

GOOGLE_SHEET_ID = "16tt7cSqdts3fObqfC2Q5eYIiwL-k2lFBMUasrzs2UE0"

LOG_FILE = "/root/.openclaw/workspace/lotto/check_log.txt"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def send_mail(subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = MAIL_TO
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(MAIL_FROM, MAIL_PW)
            server.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
        log(f"메일 발송: {subject}")
    except Exception as e:
        log(f"메일 실패: {e}")


def get_db_conn():
    dsn = cx_Oracle.makedsn("192.168.50.35", 1521, service_name="PROD")
    return cx_Oracle.connect(DB_USER, DB_PASS, dsn)


def fetch_draw_from_sheet(draw_no):
    """Google Sheet에서 특정 회차 당첨번호 가져오기"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=로또당첨번호"
        r = requests.get(url, timeout=15)
        for line in r.text.strip().split('\n'):
            parts = line.replace('"', '').split(',')
            if len(parts) >= 8 and parts[0].strip() == str(draw_no) and parts[2].strip():
                nums = [int(parts[i]) for i in range(2, 8)]
                return nums
    except Exception as e:
        log(f"Sheet 조회 실패: {e}")
    return None


def update_draw_results():
    """미확인 회차의 당첨번호를 Google Sheet에서 가져와 DB 업데이트"""
    conn = get_db_conn()
    cur = conn.cursor()

    # 구매했는데 아직 당첨 확인 안 된 회차
    cur.execute("""
        SELECT DISTINCT p.DRAW_NO
        FROM TB_LOTTO_PURCHASE p
        WHERE p.MATCH_COUNT IS NULL
        AND NOT EXISTS (SELECT 1 FROM TB_LOTTO_DRAW d WHERE d.DRAW_NO = p.DRAW_NO AND d.NUM1 IS NOT NULL)
        ORDER BY p.DRAW_NO
    """)
    unchecked = [row[0] for row in cur.fetchall()]

    # DB에 없는 최신 회차도 체크
    cur.execute("SELECT MAX(DRAW_NO) FROM TB_LOTTO_DRAW")
    max_draw = cur.fetchone()[0] or 0

    for draw_no in range(max_draw + 1, max_draw + 5):
        if draw_no not in unchecked:
            unchecked.append(draw_no)

    added = 0
    for draw_no in unchecked:
        nums = fetch_draw_from_sheet(draw_no)
        if nums:
            try:
                cur.execute("""
                    MERGE INTO TB_LOTTO_DRAW d
                    USING DUAL ON (d.DRAW_NO = :1)
                    WHEN NOT MATCHED THEN
                        INSERT (DRAW_NO, NUM1, NUM2, NUM3, NUM4, NUM5, NUM6)
                        VALUES (:1, :2, :3, :4, :5, :6, :7)
                    WHEN MATCHED THEN
                        UPDATE SET NUM1=:2, NUM2=:3, NUM3=:4, NUM4=:5, NUM5=:6, NUM6=:7
                """, (draw_no, *nums))
                added += 1
                log(f"{draw_no}회차 당첨번호 업데이트: {nums}")
            except Exception as e:
                log(f"{draw_no}회차 업데이트 실패: {e}")

    conn.commit()
    cur.close()
    conn.close()
    return added


def check_matches():
    """구매 번호와 당첨 번호 매칭"""
    conn = get_db_conn()
    cur = conn.cursor()

    # 매칭 안 된 구매 이력 조회
    cur.execute("""
        SELECT p.PURCHASE_ID, p.DRAW_NO, p.SET_SEQ,
               p.NUM1, p.NUM2, p.NUM3, p.NUM4, p.NUM5, p.NUM6,
               d.NUM1, d.NUM2, d.NUM3, d.NUM4, d.NUM5, d.NUM6, d.BONUS_NO,
               d.FIRST_WIN_AMT
        FROM TB_LOTTO_PURCHASE p
        JOIN TB_LOTTO_DRAW d ON p.DRAW_NO = d.DRAW_NO
        WHERE p.MATCH_COUNT IS NULL
        AND d.NUM1 IS NOT NULL
    """)

    results = []
    for row in cur.fetchall():
        pid, draw_no, set_seq = row[0], row[1], row[2]
        my_nums = set(row[3:9])
        win_nums = set(row[9:15])
        bonus = row[15]
        first_amt = row[16] or 0

        match_count = len(my_nums & win_nums)
        bonus_match = 'Y' if bonus in my_nums else 'N'

        # 등수 판정
        prize_rank = None
        prize_amt = 0
        if match_count == 6:
            prize_rank = 1
            prize_amt = first_amt
        elif match_count == 5 and bonus_match == 'Y':
            prize_rank = 2
        elif match_count == 5:
            prize_rank = 3
        elif match_count == 4:
            prize_rank = 4
            prize_amt = 50000
        elif match_count == 3:
            prize_rank = 5
            prize_amt = 5000

        cur.execute("""
            UPDATE TB_LOTTO_PURCHASE
            SET MATCH_COUNT = :1, BONUS_MATCH = :2, PRIZE_RANK = :3, PRIZE_AMT = :4
            WHERE PURCHASE_ID = :5
        """, (match_count, bonus_match, prize_rank, prize_amt, pid))

        results.append({
            'draw_no': draw_no,
            'set_seq': set_seq,
            'my_nums': sorted(my_nums),
            'win_nums': sorted(win_nums),
            'match_count': match_count,
            'bonus_match': bonus_match,
            'prize_rank': prize_rank,
            'prize_amt': prize_amt,
        })

    conn.commit()
    cur.close()
    conn.close()
    return results


def main():
    log("=" * 50)
    log("🎰 로또 당첨 확인")
    log("=" * 50)

    # 1. 최신 당첨번호 업데이트
    added = update_draw_results()
    log(f"당첨번호 {added}개 업데이트")

    # 2. 구매 이력 매칭
    results = check_matches()

    if not results:
        log("확인할 구매 이력 없음")
        return

    # 3. 결과 정리
    total_prize = sum(r['prize_amt'] for r in results)
    winners = [r for r in results if r['prize_rank']]

    body_lines = ["🎰 로또 당첨 확인 결과\n"]

    draw_groups = {}
    for r in results:
        draw_groups.setdefault(r['draw_no'], []).append(r)

    for draw_no, items in sorted(draw_groups.items()):
        body_lines.append(f"\n📋 {draw_no}회차")
        body_lines.append(f"   당첨번호: {items[0]['win_nums']}")
        for item in items:
            rank_str = f"🏆 {item['prize_rank']}등! ({item['prize_amt']:,}원)" if item['prize_rank'] else "❌ 미당첨"
            body_lines.append(f"   세트{item['set_seq']}: {item['my_nums']} → {item['match_count']}개 일치 {rank_str}")

    body_lines.append(f"\n💰 총 당첨금: {total_prize:,}원")

    if winners:
        body_lines.append(f"🎉 당첨 {len(winners)}건!")

    result_text = "\n".join(body_lines)
    log(result_text)

    # 4. 메일 발송
    if winners:
        send_mail(f"[로또] 🎉 당첨! 총 {total_prize:,}원", result_text)
    else:
        send_mail(f"[로또] 당첨 확인 완료 (미당첨)", result_text)


if __name__ == "__main__":
    main()
