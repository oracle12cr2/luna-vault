#!/usr/bin/env python3
"""
동행복권 로또6/45 자동 구매 스크립트
- 매주 cron으로 실행
- 5세트 (번호 범위 5~40)
- 예치금 부족 시 메일 알림
- 구매 결과 메일 알림
"""

import sys
import time
import random
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === 설정 ===
USER_ID = "kto2004"
USER_PW = "kto8520!@#"
NUM_SETS = 5
NUM_MIN = 5
NUM_MAX = 40

# 메일 설정
SMTP_SERVER = "smtp.naver.com"
SMTP_PORT = 587
MAIL_FROM = "kto2004@naver.com"
MAIL_PW = "LX3Q4R5WQPSF"  # 네이버 앱 비밀번호
MAIL_TO = "kto2004@naver.com"

LOGIN_URL = "https://www.dhlottery.co.kr/login"
MAIN_URL = "https://www.dhlottery.co.kr/"
GAME_URL = "https://ol.dhlottery.co.kr/olotto/game_mobile/game645.do"

LOG_FILE = "/root/.openclaw/workspace/lotto/buy_log.txt"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def send_mail(subject, body):
    """네이버 SMTP로 메일 발송"""
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = MAIL_TO

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(MAIL_FROM, MAIL_PW)
            server.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
        log(f"메일 발송 완료: {subject}")
    except Exception as e:
        log(f"메일 발송 실패: {e}")


def generate_numbers():
    """5~40 범위에서 6개 번호 5세트 생성"""
    sets = []
    for _ in range(NUM_SETS):
        nums = sorted(random.sample(range(NUM_MIN, NUM_MAX + 1), 6))
        sets.append(nums)
    return sets


def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def login(driver):
    """로그인"""
    log("로그인 시도...")
    driver.get(LOGIN_URL)
    time.sleep(4)

    for i in range(10):
        if driver.execute_script("return rsa && rsa.n ? true : false;"):
            break
        time.sleep(1)
    else:
        log("RSA 키 로드 실패")
        return False

    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    driver.execute_script("login();")
    time.sleep(5)

    driver.get(MAIN_URL)
    time.sleep(3)

    if driver.execute_script("return isLoggedIn;"):
        log("로그인 성공")
        return True
    else:
        log("로그인 실패")
        return False


def buy_lotto(driver, number_sets):
    """번호 선택 + 구매"""
    log("구매 페이지 접속...")
    driver.get(GAME_URL)
    time.sleep(5)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    if '세션' in body_text[:100]:
        log("세션 만료!")
        return None

    cur_round = driver.execute_script(
        "return document.getElementById('curRound') ? document.getElementById('curRound').textContent.trim() : '?';"
    )
    log(f"{cur_round}회차 구매 페이지")

    # 예치금 확인
    deposit = driver.execute_script(
        "var el = document.getElementById('moneyBalance'); return el ? parseInt(el.value) : 0;"
    )
    log(f"예치금: {deposit:,}원")

    required = NUM_SETS * 1000
    if deposit < required:
        log(f"예치금 부족! (필요: {required:,}원, 현재: {deposit:,}원)")
        send_mail(
            f"[로또] 예치금 부족 - {cur_round}회차 구매 불가",
            f"동행복권 예치금이 부족하여 {cur_round}회차 로또를 구매하지 못했습니다.\n\n"
            f"현재 예치금: {deposit:,}원\n"
            f"필요 금액: {required:,}원\n"
            f"부족 금액: {required - deposit:,}원\n\n"
            f"동행복권 사이트에서 예치금을 충전해주세요.\n"
            f"https://www.dhlottery.co.kr"
        )
        return None

    # 번호 선택
    for set_idx, nums in enumerate(number_sets):
        letter = chr(65 + set_idx)

        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.trim() === '번호 선택하기') {
                    btns[i].click(); break;
                }
            }
        """)
        time.sleep(1)

        driver.execute_script("$('#btnInit').click();")
        time.sleep(0.5)

        for num in nums:
            driver.execute_script(f"""
                var nums = document.querySelectorAll('.lt-num');
                for (var i = 0; i < nums.length; i++) {{
                    if (nums[i].textContent.trim() === '{num}') {{
                        nums[i].click(); break;
                    }}
                }}
            """)
            time.sleep(0.2)

        driver.execute_script("$('#btnSelectNum').click();")
        time.sleep(1)

        try:
            alert = driver.switch_to.alert
            log(f"세트 {letter} Alert: {alert.text}")
            alert.accept()
            time.sleep(0.5)
        except:
            pass

        log(f"세트 {letter}: {nums} ✅")

    # 최종 확인
    final = driver.execute_script("""
        var result = []; var alpha = ['A','B','C','D','E'];
        var wrap = document.getElementById('myNum-boxWrap01');
        if (!wrap) return [];
        for (var i = 0; i < 5; i++) {
            var balls = [];
            for (var j = 0; j < 6; j++) {
                var el = wrap.querySelector('.ball_' + alpha[i] + j);
                if (el && el.textContent.trim()) balls.push(el.textContent.trim());
            }
            if (balls.length > 0) result.push({set: alpha[i], balls: balls});
        }
        return result;
    """)

    if len(final) != NUM_SETS:
        log(f"{len(final)}세트만 선택됨! 중단.")
        return None

    # 구매
    log("구매 진행!")
    driver.execute_script("$('#btnBuy').click();")
    time.sleep(2)

    driver.execute_script("""
        var btns = document.querySelectorAll('.buttonOk');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].offsetParent !== null) { btns[i].click(); break; }
        }
    """)
    time.sleep(8)

    # 대기열
    for i in range(10):
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        if '접속' in page_text and '대기' in page_text:
            log(f"접속 대기 중... ({i+1})")
            time.sleep(3)
        else:
            break

    time.sleep(3)
    driver.save_screenshot('/tmp/lotto_result.png')

    # 결과 파싱
    result_data = driver.execute_script("""
        var result = {};
        var issueDay = document.getElementById('issueDay');
        var drawDate = document.getElementById('drawDate');
        var payLimit = document.getElementById('payLimitDate');
        result.issueDay = issueDay ? issueDay.textContent.trim() : '';
        result.drawDate = drawDate ? drawDate.textContent.trim() : '';
        result.payLimit = payLimit ? payLimit.textContent.trim() : '';
        result.tickets = [];
        for (var i = 0; i < 5; i++) {
            var line = document.getElementById('line' + i);
            if (line && line.style.display !== 'none') {
                var nums = [];
                line.querySelectorAll('.ticket-num').forEach(function(el) {
                    if (el.textContent.trim()) nums.push(el.textContent.trim());
                });
                var cate = document.getElementById('ticketCate' + i);
                var set_type = document.getElementById('ticketSet' + i);
                result.tickets.push({
                    game: cate ? cate.textContent.trim() : '',
                    type: set_type ? set_type.textContent.trim() : '',
                    nums: nums
                });
            }
        }
        return result;
    """)

    return {
        'round': cur_round,
        'deposit_before': deposit,
        'deposit_after': deposit - required,
        'result': result_data
    }


def main():
    log("=" * 50)
    log("🎰 동행복권 로또6/45 자동 구매")
    log("=" * 50)

    number_sets = generate_numbers()
    for i, nums in enumerate(number_sets):
        log(f"세트 {chr(65+i)}: {nums}")

    driver = create_driver()
    try:
        if not login(driver):
            send_mail("[로또] 로그인 실패", "동행복권 로그인에 실패했습니다. 비밀번호를 확인해주세요.")
            sys.exit(1)

        result = buy_lotto(driver, number_sets)

        if result and result['result'].get('tickets'):
            tickets = result['result']['tickets']
            log("🎉 구매 성공!")

            # 결과 메일
            body_lines = [
                f"🎰 로또6/45 {result['round']}회차 구매 완료!\n",
                f"발행일: {result['result'].get('issueDay', '')}",
                f"추첨일: {result['result'].get('drawDate', '')}",
                f"지급기한: {result['result'].get('payLimit', '')}\n",
                "구매 번호:",
            ]
            for t in tickets:
                body_lines.append(f"  {t['game']} [{t['type']}]: {', '.join(t['nums'])}")

            body_lines.append(f"\n예치금 잔액: {result['deposit_after']:,}원")

            if result['deposit_after'] < 5000:
                body_lines.append(f"\n⚠️ 예치금이 부족합니다! 다음 주 구매를 위해 충전해주세요.")

            send_mail(
                f"[로또] {result['round']}회차 구매 완료 ✅",
                "\n".join(body_lines)
            )
        else:
            log("구매 실패 또는 예치금 부족")

    except Exception as e:
        log(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
        send_mail("[로또] 구매 스크립트 에러", f"에러: {e}")
        sys.exit(1)
    finally:
        driver.quit()
        log("완료")


if __name__ == "__main__":
    main()
