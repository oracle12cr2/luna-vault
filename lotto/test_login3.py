#!/usr/bin/env python3
"""로그인 디버깅 스크립트"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER_ID = "kto2005"
USER_PW = "kto8520!@#"

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

try:
    # 로그인 페이지
    print("[1] 로그인 페이지 접속")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(3)
    print(f"    URL: {driver.current_url}")
    
    # 쿠키 확인 (로그인 전)
    cookies_before = driver.get_cookies()
    print(f"    쿠키 (before): {[c['name'] for c in cookies_before]}")
    
    # 아이디/비밀번호 입력
    id_input = driver.find_element(By.ID, "inpUserId")
    id_input.clear()
    id_input.send_keys(USER_ID)
    
    pw_input = driver.find_element(By.ID, "inpUserPswdEncn")
    pw_input.clear()
    pw_input.send_keys(USER_PW)
    
    print("[2] 로그인 시도")
    
    # alert 미리 처리할 준비
    # login() JS 호출
    try:
        driver.execute_script("login();")
    except Exception as e:
        print(f"    JS login() 에러: {e}")
    
    # alert 체크
    time.sleep(2)
    try:
        alert = driver.switch_to.alert
        print(f"    ⚠️ Alert: {alert.text}")
        alert.accept()
        time.sleep(1)
    except:
        print("    Alert 없음")
    
    # 여러 번 URL 체크 (리다이렉트 대기)
    for i in range(10):
        time.sleep(1)
        url = driver.current_url
        print(f"    [{i+1}s] URL: {url}")
        if '/login' not in url.lower():
            break
    
    # 쿠키 확인 (로그인 후)
    cookies_after = driver.get_cookies()
    print(f"\n    쿠키 (after): {[c['name'] for c in cookies_after]}")
    for c in cookies_after:
        if c['name'] not in [x['name'] for x in cookies_before]:
            print(f"    새 쿠키: {c['name']}={c['value'][:30]}...")
    
    # 페이지 내용 확인
    page_text = driver.find_element(By.TAG_NAME, 'body').text[:500]
    print(f"\n    페이지 텍스트: {page_text[:300]}")
    
    # 로그인 상태 확인 - 메인 페이지로 이동
    print("\n[3] 메인 페이지로 이동해서 로그인 상태 확인")
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    
    # 로그아웃 버튼이 있으면 로그인 성공
    page_src = driver.page_source
    if '로그아웃' in page_src:
        print("    ✅ 로그인 확인됨 (로그아웃 버튼 존재)")
    elif '로그인' in page_src:
        print("    ❌ 로그인 안 됨 (로그인 버튼 존재)")
    
    # isLoggedIn 변수 체크
    try:
        is_logged = driver.execute_script("return typeof isLoggedIn !== 'undefined' ? isLoggedIn : 'undefined';")
        print(f"    isLoggedIn: {is_logged}")
    except:
        pass
    
    driver.save_screenshot('/tmp/lotto_login_test3.png')
    
    # 예치금 확인 시도
    try:
        deposit = driver.execute_script("""
            var el = document.querySelector('.deposit, #deposit, .money, #money, .balance');
            return el ? el.textContent : 'not found';
        """)
        print(f"    예치금: {deposit}")
    except:
        pass

    # 게임 페이지 접속 시도
    print("\n[4] 게임 페이지 접속 시도")
    driver.get("https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40")
    time.sleep(5)
    print(f"    URL: {driver.current_url}")
    print(f"    Title: {driver.title}")
    driver.save_screenshot('/tmp/lotto_game_test3.png')
    
    # 게임 페이지 구조
    body_text = driver.find_element(By.TAG_NAME, 'body').text[:500]
    print(f"    페이지 텍스트: {body_text[:300]}")

finally:
    driver.quit()
    print("\nDone!")
