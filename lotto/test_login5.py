#!/usr/bin/env python3
"""로그인 후 isLoggedIn 확인 + 구매 페이지 진입"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

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
    # 로그인
    print("[1] 로그인")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(3)
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    driver.execute_script("login();")
    time.sleep(5)
    
    # 핵심: 메인 페이지 새로 로드 (서버가 isLoggedIn = true 렌더링)
    print("[2] 메인 페이지 새로 로드")
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    
    is_logged = driver.execute_script("return isLoggedIn;")
    print(f"    isLoggedIn: {is_logged}")
    
    if not is_logged:
        # HTML 소스에서 직접 확인
        src = driver.page_source
        import re
        match = re.search(r'const isLoggedIn = (\w+);', src)
        print(f"    HTML에서: {match.group(0) if match else 'not found'}")
        
        # 로그아웃 텍스트 확인
        if '로그아웃' in src:
            print("    '로그아웃' 텍스트는 존재함")
        else:
            print("    '로그아웃' 텍스트도 없음 — 진짜 로그인 실패")
            driver.save_screenshot('/tmp/lotto_login5_fail.png')
            exit(1)
    
    if is_logged:
        print("    ✅ isLoggedIn = true!")
        
        # 구매 페이지 팝업 URL 가져오기
        print("\n[3] 구매 팝업 URL 가져오기")
        
        # window.open을 가로채서 URL 캡처
        driver.execute_script("""
            window.__popupUrls = [];
            window.__origOpen = window.open;
            window.open = function(url, name, features) {
                window.__popupUrls.push(url);
                return null;
            };
        """)
        
        # goGameClsf 호출
        try:
            driver.execute_script("gmUtil.goGameClsf('LO40','PRCHS');")
            time.sleep(3)
        except Exception as e:
            # alert 처리
            try:
                alert = driver.switch_to.alert
                print(f"    Alert: {alert.text}")
                alert.accept()
            except:
                print(f"    에러: {e}")
        
        popup_urls = driver.execute_script("return window.__popupUrls;")
        print(f"    캡처된 팝업 URL: {popup_urls}")
        
        if popup_urls:
            game_url = popup_urls[0]
            print(f"\n[4] 게임 페이지 접속: {game_url}")
            driver.get(game_url)
            time.sleep(5)
            print(f"    URL: {driver.current_url}")
            print(f"    Title: {driver.title}")
            
            body = driver.find_element(By.TAG_NAME, 'body').text[:500]
            print(f"    Body: {body[:300]}")
            
            # 페이지 구조 분석
            inputs = driver.find_elements(By.TAG_NAME, 'input')
            print(f"\n    Inputs: {len(inputs)}")
            for inp in inputs[:20]:
                print(f"      id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, type={inp.get_attribute('type')}")
            
            # 번호 선택 관련 요소
            num_elements = driver.execute_script("""
                var result = [];
                // 번호 버튼들 찾기
                var spans = document.querySelectorAll('span, div, label, td');
                for (var i = 0; i < spans.length; i++) {
                    var el = spans[i];
                    var text = el.textContent.trim();
                    var onclick = el.getAttribute('onclick') || '';
                    if (text.match(/^\\d{1,2}$/) && parseInt(text) >= 1 && parseInt(text) <= 45) {
                        result.push({tag: el.tagName, id: el.id, class: el.className, text: text, onclick: onclick});
                    }
                    if (result.length > 50) break;
                }
                return result;
            """)
            print(f"\n    번호 요소: {len(num_elements)}")
            for el in num_elements[:10]:
                print(f"      {el}")
            
            # 자동/수동 선택 버튼
            btns = driver.execute_script("""
                var btns = document.querySelectorAll('button, input[type=button], a');
                var result = [];
                for (var i = 0; i < btns.length; i++) {
                    var text = btns[i].textContent.trim();
                    if (text.match(/자동|수동|혼합|확인|구매|선택|초기화|삭제/)) {
                        result.push({tag: btns[i].tagName, id: btns[i].id, class: btns[i].className, text: text.substring(0,30)});
                    }
                }
                return result;
            """)
            print(f"\n    구매 관련 버튼: {len(btns)}")
            for b in btns:
                print(f"      {b}")
            
            driver.save_screenshot('/tmp/lotto_game_page5.png')
            
            # HTML 저장
            with open('/tmp/lotto_game_page5.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("\n    HTML 저장: /tmp/lotto_game_page5.html")
    else:
        print("    ❌ isLoggedIn 여전히 false — 로그인이 실제로 안 된 것")
        driver.save_screenshot('/tmp/lotto_login5_notlogged.png')

finally:
    driver.quit()
    print("\nDone!")
