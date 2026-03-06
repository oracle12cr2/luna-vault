#!/usr/bin/env python3
"""올바른 계정으로 로그인 테스트"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

USER_ID = "kto2004"
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
    print("[1] 로그인")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(4)
    
    # RSA 키 로드 대기
    for i in range(5):
        if driver.execute_script("return rsa.n ? true : false;"):
            break
        time.sleep(1)
    
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    driver.execute_script("login();")
    time.sleep(5)
    
    # 메인 페이지
    print("[2] 메인 페이지")
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    
    is_logged = driver.execute_script("return isLoggedIn;")
    print(f"    isLoggedIn: {is_logged}")
    
    if is_logged:
        print("    ✅ 로그인 성공!")
        
        # 팝업 URL 캡처
        driver.execute_script("""
            window.__popupUrls = [];
            window.open = function(url, name, features) {
                window.__popupUrls.push(url);
                return null;
            };
        """)
        
        driver.execute_script("gmUtil.goGameClsf('LO40','PRCHS');")
        time.sleep(3)
        
        popup_urls = driver.execute_script("return window.__popupUrls;")
        print(f"    게임 팝업 URL: {popup_urls}")
        
        if popup_urls:
            print(f"\n[3] 게임 페이지: {popup_urls[0]}")
            driver.get(popup_urls[0])
            time.sleep(5)
            print(f"    URL: {driver.current_url}")
            print(f"    Title: {driver.title}")
            
            body = driver.find_element(By.TAG_NAME, 'body').text[:500]
            print(f"    Body: {body[:300]}")
            
            driver.save_screenshot('/tmp/lotto_game_success.png')
            
            with open('/tmp/lotto_game_success.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
    else:
        print("    ❌ 로그인 실패")
        import re
        match = re.search(r"const errorMessage = '([^']+)';", driver.page_source)
        if match:
            print(f"    에러: {match.group(1)}")

finally:
    driver.quit()
    print("\nDone!")
