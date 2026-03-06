#!/usr/bin/env python3
"""모바일 구매 페이지 접근 테스트"""

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
options.add_argument('--disable-popup-blocking')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

try:
    # 로그인
    print("[1] 로그인")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(4)
    for i in range(5):
        if driver.execute_script("return rsa.n ? true : false;"):
            break
        time.sleep(1)
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    driver.execute_script("login();")
    time.sleep(5)
    
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    print(f"    isLoggedIn: {driver.execute_script('return isLoggedIn;')}")
    
    # 쿠키 확인
    print("\n    모든 쿠키:")
    for c in driver.get_cookies():
        print(f"      {c['name']}={c['value'][:30]}... domain={c['domain']}")
    
    # 방법 1: 같은 탭에서 모바일 게임 페이지로 이동
    print("\n[2] 모바일 게임 페이지 (같은 탭)")
    driver.get("https://ol.dhlottery.co.kr/olotto/game_mobile/game645.do")
    time.sleep(5)
    print(f"    URL: {driver.current_url}")
    print(f"    Title: {driver.title}")
    body = driver.find_element(By.TAG_NAME, 'body').text[:500]
    print(f"    Body: {body[:300]}")
    driver.save_screenshot('/tmp/lotto_mobile_game.png')
    
    if '세션' in body or '로그인' in body[:50]:
        print("    ❌ 세션 없음 — 쿠키 수동 복사 시도")
        
        # 방법 2: 쿠키를 el/ol 도메인에 수동 설정
        # 먼저 www에서 쿠키 가져오기
        driver.get("https://www.dhlottery.co.kr/")
        time.sleep(2)
        www_cookies = driver.get_cookies()
        
        # el.dhlottery.co.kr로 이동해서 쿠키 설정
        print("\n[3] el.dhlottery.co.kr에 쿠키 수동 설정")
        driver.get("https://el.dhlottery.co.kr/")
        time.sleep(2)
        
        for c in www_cookies:
            try:
                cookie = {
                    'name': c['name'],
                    'value': c['value'],
                    'domain': '.dhlottery.co.kr',
                }
                driver.add_cookie(cookie)
            except Exception as e:
                pass
        
        driver.get("https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40")
        time.sleep(5)
        print(f"    URL: {driver.current_url}")
        print(f"    Title: {driver.title}")
        body = driver.find_element(By.TAG_NAME, 'body').text[:300]
        print(f"    Body: {body[:200]}")
        driver.save_screenshot('/tmp/lotto_el_cookie.png')
    
    else:
        print("    ✅ 게임 페이지 로드됨!")
        
        # 구조 분석
        print("\n[3] 구매 UI 분석")
        all_elements = driver.execute_script("""
            var result = {nums: [], btns: [], selects: []};
            // 번호판
            document.querySelectorAll('*').forEach(function(el) {
                var text = el.textContent.trim();
                var onclick = el.getAttribute('onclick') || '';
                if (text.match(/^\\d{1,2}$/) && parseInt(text) >= 1 && parseInt(text) <= 45 && el.children.length === 0) {
                    result.nums.push({tag: el.tagName, id: el.id, class: el.className.substring(0,50), text: text, onclick: onclick.substring(0,80)});
                }
            });
            // 버튼
            document.querySelectorAll('button, input[type=button], a.btn, a[class*=btn]').forEach(function(el) {
                var text = el.textContent.trim();
                if (text.length > 0 && text.length < 50) {
                    result.btns.push({tag: el.tagName, id: el.id, class: el.className.substring(0,50), text: text.substring(0,30)});
                }
            });
            // select
            document.querySelectorAll('select').forEach(function(el) {
                var opts = [];
                el.querySelectorAll('option').forEach(function(o) { opts.push(o.text); });
                result.selects.push({id: el.id, name: el.name, options: opts});
            });
            return result;
        """)
        
        print(f"    번호: {len(all_elements['nums'])}")
        for n in all_elements['nums'][:10]:
            print(f"      {n}")
        print(f"    버튼: {len(all_elements['btns'])}")
        for b in all_elements['btns']:
            print(f"      {b}")
        print(f"    Select: {len(all_elements['selects'])}")
        for s in all_elements['selects']:
            print(f"      {s}")
        
        with open('/tmp/lotto_mobile_game.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

finally:
    driver.quit()
    print("\nDone!")
