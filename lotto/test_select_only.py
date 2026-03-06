#!/usr/bin/env python3
"""번호 선택까지만 테스트 (구매 안 함)"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

USER_ID = "kto2004"
USER_PW = "kto8520!@#"
NUM_SETS = 5
NUM_MIN = 5
NUM_MAX = 40

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
    for i in range(10):
        if driver.execute_script("return rsa && rsa.n ? true : false;"):
            break
        time.sleep(1)
    driver.find_element(By.ID, "inpUserId").send_keys(USER_ID)
    driver.find_element(By.ID, "inpUserPswdEncn").send_keys(USER_PW)
    driver.execute_script("login();")
    time.sleep(5)
    driver.get("https://www.dhlottery.co.kr/")
    time.sleep(3)
    print(f"    isLoggedIn: {driver.execute_script('return isLoggedIn;')}")
    
    # 게임 페이지
    print("\n[2] 게임 페이지")
    driver.get("https://ol.dhlottery.co.kr/olotto/game_mobile/game645.do")
    time.sleep(5)
    print(f"    Title: {driver.title}")
    
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    if '세션' in body_text[:100]:
        print("    ❌ 세션 만료!")
        exit(1)
    
    # 현재 회차
    cur_round = driver.execute_script("var el = document.getElementById('curRound'); return el ? el.textContent.trim() : 'unknown';")
    print(f"    회차: {cur_round}")
    
    # 예치금
    deposit_info = driver.execute_script("""
        var text = document.body.innerText;
        var match = text.match(/예치금[\\s:]*([\\d,]+)/);
        return match ? match[1] : 'not found';
    """)
    print(f"    예치금: {deposit_info}")
    
    # 번호 생성
    number_sets = []
    for _ in range(NUM_SETS):
        nums = sorted(random.sample(range(NUM_MIN, NUM_MAX + 1), 6))
        number_sets.append(nums)
    
    print(f"\n[3] 번호 선택 ({NUM_SETS}세트)")
    for i, nums in enumerate(number_sets):
        print(f"    세트 {chr(65+i)}: {nums}")
    
    # 번호 선택 시작
    for set_idx, nums in enumerate(number_sets):
        letter = chr(65 + set_idx)
        print(f"\n    --- 세트 {letter} 선택 중 ---")
        
        # "번호 선택하기" 클릭
        driver.execute_script("""
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.trim() === '번호 선택하기') {
                    btns[i].click();
                    break;
                }
            }
        """)
        time.sleep(1)
        
        # 초기화
        driver.execute_script("$('#btnInit').click();")
        time.sleep(0.5)
        
        # 번호 클릭
        for num in nums:
            clicked = driver.execute_script(f"""
                var nums = document.querySelectorAll('.lt-num');
                for (var i = 0; i < nums.length; i++) {{
                    if (nums[i].textContent.trim() === '{num}') {{
                        nums[i].click();
                        return true;
                    }}
                }}
                return false;
            """)
            if not clicked:
                print(f"      ⚠️ {num} 클릭 실패")
            time.sleep(0.2)
        
        # 선택된 번호 확인
        selected = driver.execute_script("""
            var on = document.querySelectorAll('.lt-num.on');
            var nums = [];
            on.forEach(function(el) { nums.push(el.textContent.trim()); });
            return nums;
        """)
        print(f"      선택됨: {selected}")
        
        # 선택완료
        driver.execute_script("$('#btnSelectNum').click();")
        time.sleep(1)
        
        # alert 처리
        try:
            alert = driver.switch_to.alert
            print(f"      Alert: {alert.text}")
            alert.accept()
            time.sleep(0.5)
        except:
            pass
    
    # 최종 선택 확인
    print(f"\n[4] 최종 선택 확인")
    final_info = driver.execute_script("""
        var result = [];
        var alpabet = ['A','B','C','D','E'];
        var wrap = document.getElementById('myNum-boxWrap01');
        if (!wrap) return 'wrap not found';
        
        for (var i = 0; i < 5; i++) {
            var balls = [];
            for (var j = 0; j < 6; j++) {
                var el = wrap.querySelector('.ball_' + alpabet[i] + j);
                if (el && el.textContent.trim()) {
                    balls.push(el.textContent.trim());
                }
            }
            if (balls.length > 0) {
                result.push({set: alpabet[i], balls: balls});
            }
        }
        return result;
    """)
    print(f"    결과: {final_info}")
    
    driver.save_screenshot('/tmp/lotto_select_test.png')
    print("\n    📸 스크린샷: /tmp/lotto_select_test.png")
    print("\n    ⚠️ 구매는 하지 않음 (테스트 모드)")

finally:
    driver.quit()
    print("\nDone!")
