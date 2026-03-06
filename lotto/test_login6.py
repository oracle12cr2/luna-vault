#!/usr/bin/env python3
"""RSA 암호화 + 로그인 디버깅"""

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
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

try:
    print("[1] 로그인 페이지")
    driver.get("https://www.dhlottery.co.kr/login")
    time.sleep(4)
    
    # RSA 키 로드 확인
    rsa_check = driver.execute_script("""
        return {
            rsaExists: typeof rsa !== 'undefined',
            rsaType: typeof rsa,
            fnRSAencryptExists: typeof fnRSAencrypt !== 'undefined'
        };
    """)
    print(f"    RSA 체크: {rsa_check}")
    
    # RSA 모듈러스 가져오기 시도
    try:
        rsa_modulus = driver.execute_script("return rsa.n ? rsa.n.toString(16).substring(0, 40) + '...' : 'empty';")
        print(f"    RSA modulus: {rsa_modulus}")
    except Exception as e:
        print(f"    RSA modulus 에러: {e}")
    
    # selectRsaModulus 수동 호출
    print("\n[2] RSA 키 수동 로드")
    driver.execute_script("""
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/login/selectRsaModulus.do', false);
        xhr.send();
        var resp = JSON.parse(xhr.responseText);
        window.__rsaResp = resp;
        if (resp.data) {
            rsa.setPublic(resp.data.rsaModulus, resp.data.publicExponent);
        }
    """)
    rsa_resp = driver.execute_script("return window.__rsaResp;")
    print(f"    RSA response: {str(rsa_resp)[:200]}")
    
    rsa_modulus2 = driver.execute_script("return rsa.n ? rsa.n.toString(16).substring(0, 40) + '...' : 'empty';")
    print(f"    RSA modulus after: {rsa_modulus2}")
    
    # 입력
    print("\n[3] 입력 + 암호화 테스트")
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    
    # 수동으로 암호화 후 hidden 필드 설정
    encrypted_vals = driver.execute_script("""
        var encId = fnRSAencrypt(document.getElementById('inpUserId').value);
        var encPw = fnRSAencrypt(document.getElementById('inpUserPswdEncn').value);
        document.getElementById('userId').value = encId;
        document.getElementById('userPswdEncn').value = encPw;
        return {
            inpUserId: document.getElementById('inpUserId').value,
            encId: encId ? encId.substring(0, 40) + '...' : 'null',
            encPw: encPw ? encPw.substring(0, 40) + '...' : 'null',
            hiddenUserId: document.getElementById('userId').value.substring(0, 40) + '...',
            hiddenPw: document.getElementById('userPswdEncn').value.substring(0, 40) + '...',
            formAction: document.getElementById('loginForm').action
        };
    """)
    print(f"    암호화 결과: {encrypted_vals}")
    
    # 폼 액션 설정 + 제출
    print("\n[4] 폼 제출")
    driver.execute_script("""
        document.getElementById('loginForm').action = '/login/securityLoginCheck.do';
        document.getElementById('loginForm').submit();
    """)
    time.sleep(5)
    
    print(f"    URL after submit: {driver.current_url}")
    
    # 응답 확인
    body = driver.find_element(By.TAG_NAME, 'body').text[:300]
    print(f"    Body: {body[:200]}")
    
    # 쿠키 확인
    cookies = driver.get_cookies()
    print(f"    Cookies: {[(c['name'], c['value'][:20]) for c in cookies]}")
    
    # 메인 페이지로 이동
    print("\n[5] 메인 페이지")
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    
    is_logged = driver.execute_script("return isLoggedIn;")
    print(f"    isLoggedIn: {is_logged}")
    
    # HTML에서 isLoggedIn 직접 확인
    import re
    match = re.search(r'const isLoggedIn = (\w+);', driver.page_source)
    print(f"    HTML isLoggedIn: {match.group(1) if match else 'not found'}")
    
    # 사용자 정보 확인
    user_info = driver.execute_script("""
        var nameEl = document.querySelector('.user-name, .myinfo, #userNm, .name');
        var logoutEl = document.querySelector('a[href*="logout"], button[onclick*="logout"]');
        return {
            userName: nameEl ? nameEl.textContent.trim() : 'not found',
            logoutBtn: logoutEl ? logoutEl.outerHTML.substring(0, 100) : 'not found'
        };
    """)
    print(f"    사용자 정보: {user_info}")
    
    driver.save_screenshot('/tmp/lotto_login6.png')

finally:
    driver.quit()
    print("\nDone!")
