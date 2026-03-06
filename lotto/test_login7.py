#!/usr/bin/env python3
"""login() JS 호출 + securityLoginCheck 응답 분석"""

import time
import re
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
    print("[1] 로그인 페이지")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(4)
    
    # RSA 키 로드 대기
    for i in range(5):
        has_rsa = driver.execute_script("return rsa.n ? true : false;")
        if has_rsa:
            print(f"    RSA 키 로드 완료 ({i+1}s)")
            break
        time.sleep(1)
    
    # 입력
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    print("    입력 완료")
    
    # login() 호출
    print("\n[2] login() 호출")
    driver.execute_script("login();")
    
    # securityLoginCheck.do 응답 확인
    time.sleep(3)
    print(f"    URL: {driver.current_url}")
    
    # 이 페이지의 전체 HTML 확인 (리다이렉트 JS가 있을 수 있음)
    page_src = driver.page_source
    
    # script 태그에서 redirect/location 찾기
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', page_src, re.DOTALL)
    for i, script in enumerate(scripts):
        if 'location' in script or 'redirect' in script.lower() or 'href' in script:
            print(f"\n    Script #{i} (redirect 관련):")
            print(f"    {script.strip()[:300]}")
    
    # alert 체크
    try:
        alert = driver.switch_to.alert
        print(f"\n    Alert: {alert.text}")
        alert.accept()
        time.sleep(1)
    except:
        pass
    
    # 에러 메시지 확인
    err_msgs = driver.execute_script("""
        var msgs = [];
        var els = document.querySelectorAll('.error, .err, .alert, .msg, .message, [class*=error], [class*=fail]');
        els.forEach(function(el) {
            var text = el.textContent.trim();
            if (text) msgs.push({class: el.className, text: text.substring(0, 100)});
        });
        return msgs;
    """)
    if err_msgs:
        print(f"\n    에러 메시지: {err_msgs}")
    
    # 전체 페이지 텍스트
    body = driver.find_element(By.TAG_NAME, 'body').text
    print(f"\n    Body text: {body[:500]}")
    
    # HTML 저장
    with open('/tmp/lotto_security_check.html', 'w', encoding='utf-8') as f:
        f.write(page_src)
    print("    HTML 저장: /tmp/lotto_security_check.html")
    
    # 쿠키
    print(f"\n    Cookies: {[(c['name'], c['value'][:30], c['domain']) for c in driver.get_cookies()]}")
    
    # 10초 더 대기하면서 URL 변화 관찰
    print("\n[3] URL 변화 관찰 (10초)")
    for i in range(10):
        time.sleep(1)
        url = driver.current_url
        title = driver.title
        if i == 0 or (i > 0 and url != prev_url):
            print(f"    [{i+1}s] URL: {url}, Title: {title}")
        prev_url = url
    
    # 메인 페이지로 이동
    print("\n[4] 메인 페이지")
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    
    is_logged = driver.execute_script("return isLoggedIn;")
    print(f"    isLoggedIn: {is_logged}")
    
    # 로그아웃 관련 요소 정확히 찾기
    logout_elements = driver.execute_script("""
        var result = [];
        var all = document.querySelectorAll('a, button, span');
        for (var i = 0; i < all.length; i++) {
            var text = all[i].textContent.trim();
            if (text.includes('로그아웃') || text.includes('logout')) {
                result.push({
                    tag: all[i].tagName,
                    text: text.substring(0, 50),
                    href: all[i].getAttribute('href') || '',
                    display: window.getComputedStyle(all[i]).display,
                    visibility: window.getComputedStyle(all[i]).visibility,
                    hidden: all[i].hidden
                });
            }
        }
        return result;
    """)
    print(f"    로그아웃 요소: {logout_elements}")
    
    driver.save_screenshot('/tmp/lotto_login7.png')
    
finally:
    driver.quit()
    print("\nDone!")
