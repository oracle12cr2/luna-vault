#!/usr/bin/env python3
"""로그인 후 구매 페이지 진입 테스트 - 사이트 내부 흐름"""

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
    # === 로그인 ===
    print("[1] 로그인")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(3)
    
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    driver.execute_script("login();")
    time.sleep(5)
    
    # 메인으로 이동해서 로그인 확인
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    
    if '로그아웃' not in driver.page_source:
        print("    ❌ 로그인 실패")
        exit(1)
    print("    ✅ 로그인 성공")
    
    # isLoggedIn 확인
    is_logged = driver.execute_script("return typeof isLoggedIn !== 'undefined' ? isLoggedIn : 'N/A';")
    print(f"    isLoggedIn JS변수: {is_logged}")
    
    # === 구매 페이지 진입 시도 ===
    
    # 방법 1: goGameClsf 직접 호출 (사이트 내부 JS)
    print("\n[2] goGameClsf('LO40','PRCHS') 호출")
    
    # 새 창 열리는지 확인하기 위해 현재 핸들 기록
    main_window = driver.current_window_handle
    print(f"    현재 창: {main_window}")
    
    # popup 허용 설정
    driver.execute_script("window.open = function(url, name, features) { window.__lastPopupUrl = url; return window; };")
    
    # JS 호출
    try:
        driver.execute_script("gmUtil.goGameClsf('LO40','PRCHS');")
        time.sleep(3)
        popup_url = driver.execute_script("return window.__lastPopupUrl || 'none';")
        print(f"    팝업 URL: {popup_url}")
    except Exception as e:
        print(f"    goGameClsf 에러: {e}")
    
    # 방법 2: getServerProperties로 URL 확인 후 직접 이동
    print("\n[3] 서버 속성 확인")
    try:
        props = driver.execute_script("""
            return new Promise(function(resolve) {
                cmmUtil.getServerProperties(function(propInfo) {
                    resolve(propInfo);
                });
            });
        """)
        print(f"    elwasUrl: {props.get('serviceElwasUrl', 'N/A')}")
        print(f"    olwasUrl: {props.get('serviceOlwasUrl', 'N/A')}")
    except Exception as e:
        print(f"    getServerProperties 에러: {e}")
    
    # 방법 3: 현재 세션 쿠키 확인 후 el.dhlottery.co.kr에 수동 설정
    print("\n[4] 쿠키 목록")
    for c in driver.get_cookies():
        print(f"    {c['name']}={c['value'][:40]}... domain={c.get('domain','')}")
    
    # 방법 4: 새 창 핸들 확인
    all_windows = driver.window_handles
    print(f"\n[5] 창 핸들: {len(all_windows)}")
    for w in all_windows:
        driver.switch_to.window(w)
        print(f"    {w}: {driver.current_url}")
    
    # 방법 5: 로또 구매 페이지 직접 URL (다른 패턴 시도)
    print("\n[6] 직접 URL 접근 테스트")
    test_urls = [
        "https://el.dhlottery.co.kr/game/TotalGame.jsp?LottoId=LO40",
        "https://www.dhlottery.co.kr/gameResult.do?method=byWin",
        "https://ol.dhlottery.co.kr/olotto/game_mobile/game645.do",
    ]
    
    for url in test_urls:
        driver.get(url)
        time.sleep(3)
        print(f"    {url}")
        print(f"      → {driver.current_url}")
        print(f"      Title: {driver.title}")
        body = driver.find_element(By.TAG_NAME, 'body').text[:200]
        print(f"      Body: {body[:150]}")
        driver.save_screenshot(f'/tmp/lotto_url_test_{test_urls.index(url)}.png')

finally:
    driver.quit()
    print("\nDone!")
