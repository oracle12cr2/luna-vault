#!/usr/bin/env python3
"""
로또 당첨 결과 확인 및 메일 발송
매주 월요일 09시 실행용
"""

import sys
import time
import smtplib
import subprocess
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta

# 설정
USER_ID = "kto2004"
USER_PW = "kto8520!@#"

# 메일 설정
MAIL_FROM = "kto2004@naver.com"
MAIL_TO = "kto2004@naver.com"
MAIL_PW = "LX3Q4R5WQPSF"  # 네이버 앱 비밀번호 (naver_cafe/config.py에서 확인)
SMTP_SERVER = "smtp.naver.com"
SMTP_PORT = 587

LOGIN_URL = "https://www.dhlottery.co.kr/login"
HISTORY_URL = "https://ol.dhlottery.co.kr/olotto/game/gameResult.do"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def send_kakao(message, recipient="김태완"):
    """카카오톡으로 메시지 전송 (유나 맥북 경유)"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            [os.path.join(script_dir, "send_kakao.sh"), recipient, message],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            log(f"카톡 전송 성공 → {recipient}")
            return True
        else:
            log(f"카톡 전송 실패: {result.stderr}")
            return False
    except Exception as e:
        log(f"카톡 전송 에러: {e}")
        return False

def send_mail(subject, body):
    """메일 발송"""
    try:
        msg = MIMEMultipart()
        msg['From'] = MAIL_FROM
        msg['To'] = MAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(MAIL_FROM, MAIL_PW)
            server.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())
        log("메일 발송 성공")
        return True
    except Exception as e:
        log(f"메일 발송 실패: {e}")
        return False

def login(driver):
    """로그인 (buy_lotto.py와 동일한 방식)"""
    log("로그인 시도...")
    driver.get(LOGIN_URL)
    time.sleep(4)

    # RSA 키 로드 확인
    for i in range(10):
        if driver.execute_script("return rsa && rsa.n ? true : false;"):
            break
        time.sleep(1)
    else:
        log("RSA 키 로드 실패")
        return False

    try:
        driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
        driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
        driver.execute_script("login();")  # JavaScript login 함수 호출
        time.sleep(5)

        driver.get("https://www.dhlottery.co.kr/")
        time.sleep(3)

        # 로그인 성공 확인
        if driver.execute_script("return isLoggedIn;"):
            log("로그인 성공")
            return True
        else:
            log("로그인 실패")
            return False
    except Exception as e:
        log(f"로그인 실패: {e}")
        return False

def get_winning_history(driver):
    """최근 당첨 내역 조회"""
    log("당첨 내역 조회...")
    driver.get(HISTORY_URL)
    time.sleep(5)
    
    results = []
    
    try:
        # 최근 1달간의 당첨 내역 파싱
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
        
        for row in rows[1:]:  # 헤더 제외
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 6:
                round_num = cells[0].text.strip()
                buy_date = cells[1].text.strip()
                draw_date = cells[2].text.strip()
                numbers = cells[3].text.strip()
                result = cells[4].text.strip()
                amount = cells[5].text.strip()
                
                # 당첨이 있는 경우만
                if "당첨" in result or amount.replace(",", "").replace("원", "").isdigit():
                    results.append({
                        'round': round_num,
                        'buy_date': buy_date,
                        'draw_date': draw_date,
                        'numbers': numbers,
                        'result': result,
                        'amount': amount
                    })
        
        # 최근 1주일 내 당첨만 필터링
        week_ago = datetime.now() - timedelta(days=7)
        recent_wins = []
        
        for r in results:
            try:
                # 날짜 파싱 (YYYY-MM-DD 또는 YYYY.MM.DD 형태)
                draw_date = r['draw_date'].replace('.', '-')
                draw_dt = datetime.strptime(draw_date, '%Y-%m-%d')
                if draw_dt >= week_ago:
                    recent_wins.append(r)
            except:
                # 날짜 파싱 실패하면 일단 포함
                recent_wins.append(r)
                
        return recent_wins
        
    except Exception as e:
        log(f"당첨 내역 조회 실패: {e}")
        return []

def get_balance(driver):
    """예치금 조회 (buy_lotto.py와 동일한 방식)"""
    try:
        driver.get("https://ol.dhlottery.co.kr/olotto/game_mobile/game645.do")
        time.sleep(3)
        
        # buy_lotto.py와 동일한 방식
        deposit = driver.execute_script(
            "var el = document.getElementById('moneyBalance'); return el ? parseInt(el.value) : 0;"
        )
        return f"{deposit:,}원" if deposit > 0 else "0원"
    except Exception as e:
        log(f"예치금 조회 실패: {e}")
        return "조회 실패"

def main():
    log("=" * 50)
    log("🎰 로또 당첨 결과 확인")
    log("=" * 50)
    
    # Chrome 옵션
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 로그인
        if not login(driver):
            send_mail("[로또] 당첨 확인 실패", "동행복권 로그인에 실패했습니다.")
            return
        
        # 당첨 내역 조회
        wins = get_winning_history(driver)
        
        # 예치금 조회
        balance = get_balance(driver)
        
        # 메일 내용 작성
        if wins:
            subject = f"🎉 로또 당첨 알림 ({len(wins)}건)"
            body = "🎊 로또 당첨 결과를 알려드립니다!\n\n"
            
            total_amount = 0
            for w in wins:
                body += f"📍 {w['round']}회차 ({w['draw_date']})\n"
                body += f"   구매일: {w['buy_date']}\n"
                body += f"   번호: {w['numbers']}\n"
                body += f"   결과: {w['result']}\n"
                body += f"   당첨금: {w['amount']}\n\n"
                
                # 당첨금 합계 계산
                try:
                    amount_num = int(w['amount'].replace(',', '').replace('원', ''))
                    total_amount += amount_num
                except:
                    pass
            
            body += f"💰 총 당첨금: {total_amount:,}원\n"
            body += f"💳 현재 예치금: {balance}\n\n"
            body += "🔗 https://www.dhlottery.co.kr\n"
            body += f"확인시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        else:
            subject = "📋 로또 당첨 결과 (당첨 없음)"
            body = f"지난주 로또 당첨 내역이 없습니다.\n\n"
            body += f"💳 현재 예치금: {balance}\n\n"
            body += "🔗 https://www.dhlottery.co.kr\n"
            body += f"확인시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 메일 발송
        send_mail(subject, body)
        
        # 카톡 전송
        if wins:
            kakao_msg = f"🎉 로또 당첨! ({len(wins)}건)\n"
            for w in wins:
                kakao_msg += f"📍 {w['round']}회차: {w['result']} ({w['amount']})\n"
            kakao_msg += f"💳 예치금: {balance}"
        else:
            kakao_msg = f"📋 로또 당첨 결과: 이번 주 당첨 없음\n💳 예치금: {balance}"
        send_kakao(kakao_msg, "김태완(메인)")
        
        log(f"당첨 확인 완료: {len(wins)}건")
        
    except Exception as e:
        log(f"에러 발생: {e}")
        send_mail("[로또] 당첨 확인 에러", f"당첨 확인 중 오류가 발생했습니다.\n\n{e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()