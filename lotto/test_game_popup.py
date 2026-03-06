#!/usr/bin/env python3
"""팝업으로 게임 페이지 열기"""

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
options.add_argument('--disable-popup-blocking')  # 팝업 허용
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
    
    # 메인 페이지
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    print(f"    isLoggedIn: {driver.execute_script('return isLoggedIn;')}")
    
    # window.open으로 팝업 열기 (실제 브라우저처럼)
    print("\n[2] 게임 페이지 팝업 열기")
    main_handle = driver.current_window_handle
    
    # 실제 gmUtil.goGameClsf 호출 (window.open 가로채지 않음)
    driver.execute_script("gmUtil.goGameClsf('LO40','PRCHS');")
    time.sleep(5)
    
    all_handles = driver.window_handles
    print(f"    윈도우 수: {len(all_handles)}")
    
    if len(all_handles) > 1:
        # 새 팝업으로 전환
        for handle in all_handles:
            if handle != main_handle:
                driver.switch_to.window(handle)
                break
        
        time.sleep(3)
        print(f"    팝업 URL: {driver.current_url}")
        print(f"    팝업 Title: {driver.title}")
        
        body = driver.find_element(By.TAG_NAME, 'body').text[:500]
        print(f"    Body: {body[:300]}")
        
        # 페이지 구조 분석
        print("\n[3] 번호 선택 UI 분석")
        
        # 번호판 찾기
        num_elements = driver.execute_script("""
            var result = [];
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                var text = el.textContent.trim();
                var onclick = el.getAttribute('onclick') || '';
                if (text.match(/^\\d{1,2}$/) && parseInt(text) >= 1 && parseInt(text) <= 45) {
                    if (el.children.length === 0) {
                        result.push({tag: el.tagName, id: el.id, class: el.className, text: text, onclick: onclick.substring(0,50)});
                    }
                }
                if (result.length > 60) break;
            }
            return result;
        """)
        print(f"    번호 요소: {len(num_elements)}")
        for el in num_elements[:15]:
            print(f"      {el}")
        
        # 버튼 찾기
        btns = driver.execute_script("""
            var btns = document.querySelectorAll('button, input[type=button], input[type=submit], a');
            var result = [];
            for (var i = 0; i < btns.length; i++) {
                var text = btns[i].textContent.trim();
                var id = btns[i].id;
                var cls = btns[i].className;
                var onclick = btns[i].getAttribute('onclick') || '';
                if (text.length > 0 && text.length < 30) {
                    result.push({tag: btns[i].tagName, id: id, class: cls.substring(0,50), text: text, onclick: onclick.substring(0,50)});
                }
            }
            return result;
        """)
        print(f"\n    버튼: {len(btns)}")
        for b in btns[:20]:
            print(f"      {b}")
        
        driver.save_screenshot('/tmp/lotto_game_popup.png')
        with open('/tmp/lotto_game_popup.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\n    HTML 저장됨")
    else:
        print("    ❌ 팝업이 안 열림")
        # 대안: window.open 직접 호출
        print("\n[2b] 대안: window.open 직접 호출")
        driver.execute_script("window.open('https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40', 'gamePop', 'width=1164,height=793');")
        time.sleep(5)
        
        all_handles = driver.window_handles
        print(f"    윈도우 수: {len(all_handles)}")
        
        if len(all_handles) > 1:
            for handle in all_handles:
                if handle != main_handle:
                    driver.switch_to.window(handle)
                    break
            time.sleep(3)
            print(f"    URL: {driver.current_url}")
            print(f"    Title: {driver.title}")
            body = driver.find_element(By.TAG_NAME, 'body').text[:300]
            print(f"    Body: {body[:200]}")
            driver.save_screenshot('/tmp/lotto_game_popup2.png')

finally:
    driver.quit()
    print("\nDone!")
