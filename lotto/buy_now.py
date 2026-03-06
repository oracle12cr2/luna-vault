#!/usr/bin/env python3
"""로또6/45 실제 구매 - 1214회차"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

USER_ID = "kto2004"
USER_PW = "kto8520!@#"

# 번호 생성 (5~40 범위, 5세트)
random.seed()
number_sets = []
for _ in range(5):
    nums = sorted(random.sample(range(5, 41), 6))
    number_sets.append(nums)

print("=" * 50)
print("🎰 로또6/45 구매 - 1214회차")
print("=" * 50)
for i, nums in enumerate(number_sets):
    print(f"  세트 {chr(65+i)}: {nums}")
print()

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
    # === 로그인 ===
    print("[1] 로그인...")
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
    
    if not driver.execute_script("return isLoggedIn;"):
        print("    ❌ 로그인 실패!")
        exit(1)
    print("    ✅ 로그인 성공")
    
    # === 게임 페이지 ===
    print("\n[2] 게임 페이지...")
    driver.get("https://ol.dhlottery.co.kr/olotto/game_mobile/game645.do")
    time.sleep(5)
    
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    if '세션' in body_text[:100]:
        print("    ❌ 세션 만료!")
        exit(1)
    
    cur_round = driver.execute_script("return document.getElementById('curRound') ? document.getElementById('curRound').textContent.trim() : '?';")
    print(f"    ✅ {cur_round}회차 구매 페이지")
    
    # === 번호 선택 ===
    print("\n[3] 번호 선택...")
    for set_idx, nums in enumerate(number_sets):
        letter = chr(65 + set_idx)
        
        # 번호 선택하기 클릭
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
            driver.execute_script(f"""
                var nums = document.querySelectorAll('.lt-num');
                for (var i = 0; i < nums.length; i++) {{
                    if (nums[i].textContent.trim() === '{num}') {{
                        nums[i].click();
                        break;
                    }}
                }}
            """)
            time.sleep(0.2)
        
        # 선택 확인
        selected = driver.execute_script("""
            var on = document.querySelectorAll('.lt-num.on');
            var nums = [];
            on.forEach(function(el) { nums.push(el.textContent.trim()); });
            return nums;
        """)
        
        # 선택완료
        driver.execute_script("$('#btnSelectNum').click();")
        time.sleep(1)
        
        # alert 처리
        try:
            alert = driver.switch_to.alert
            print(f"    세트 {letter} Alert: {alert.text}")
            alert.accept()
            time.sleep(0.5)
        except:
            pass
        
        print(f"    세트 {letter}: {selected} ✅")
    
    # === 최종 확인 ===
    print("\n[4] 최종 선택 확인...")
    final = driver.execute_script("""
        var result = [];
        var alpha = ['A','B','C','D','E'];
        var wrap = document.getElementById('myNum-boxWrap01');
        if (!wrap) return [];
        for (var i = 0; i < 5; i++) {
            var balls = [];
            for (var j = 0; j < 6; j++) {
                var el = wrap.querySelector('.ball_' + alpha[i] + j);
                if (el && el.textContent.trim()) balls.push(el.textContent.trim());
            }
            if (balls.length > 0) result.push({set: alpha[i], balls: balls});
        }
        return result;
    """)
    
    for f in final:
        print(f"    {f['set']}: {f['balls']}")
    
    if len(final) != 5:
        print(f"    ❌ {len(final)}세트만 선택됨! 중단.")
        driver.save_screenshot('/tmp/lotto_buy_fail.png')
        exit(1)
    
    driver.save_screenshot('/tmp/lotto_before_buy.png')
    
    # === 구매하기 ===
    print("\n[5] 🎰 구매 진행!")
    driver.execute_script("$('#btnBuy').click();")
    time.sleep(2)
    
    # "구매하시겠습니까?" 확인
    print("    구매 확인 팝업 처리...")
    driver.execute_script("""
        var btns = document.querySelectorAll('.buttonOk');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].offsetParent !== null) {
                btns[i].click();
                break;
            }
        }
    """)
    time.sleep(8)
    
    # 대기열 처리 (접속자 많을 경우)
    for i in range(10):
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        if '접속' in page_text and '대기' in page_text:
            print(f"    접속 대기 중... ({i+1})")
            time.sleep(3)
        else:
            break
    
    # === 결과 확인 ===
    print("\n[6] 결과 확인...")
    driver.save_screenshot('/tmp/lotto_after_buy.png')
    
    result_text = driver.find_element(By.TAG_NAME, 'body').text
    
    # 구매 결과 파싱
    result_data = driver.execute_script("""
        var result = {};
        var issueDay = document.getElementById('issueDay');
        var drawDate = document.getElementById('drawDate');
        var payLimit = document.getElementById('payLimitDate');
        result.issueDay = issueDay ? issueDay.textContent.trim() : '';
        result.drawDate = drawDate ? drawDate.textContent.trim() : '';
        result.payLimit = payLimit ? payLimit.textContent.trim() : '';
        
        // 구매된 번호들
        result.tickets = [];
        for (var i = 0; i < 5; i++) {
            var line = document.getElementById('line' + i);
            if (line && line.style.display !== 'none') {
                var nums = [];
                line.querySelectorAll('.ticket-num').forEach(function(el) {
                    if (el.textContent.trim()) nums.push(el.textContent.trim());
                });
                var cate = document.getElementById('ticketCate' + i);
                var set = document.getElementById('ticketSet' + i);
                result.tickets.push({
                    game: cate ? cate.textContent.trim() : '',
                    type: set ? set.textContent.trim() : '',
                    nums: nums
                });
            }
        }
        return result;
    """)
    
    if result_data.get('tickets') and len(result_data['tickets']) > 0:
        print("\n    🎉🎉🎉 구매 성공! 🎉🎉🎉")
        print(f"    발행일: {result_data.get('issueDay', '')}")
        print(f"    추첨일: {result_data.get('drawDate', '')}")
        print(f"    지급기한: {result_data.get('payLimit', '')}")
        print(f"\n    구매 번호:")
        for t in result_data['tickets']:
            print(f"      {t['game']} [{t['type']}]: {t['nums']}")
    else:
        # alert 체크
        try:
            alert = driver.switch_to.alert
            print(f"    Alert: {alert.text}")
            alert.accept()
        except:
            pass
        
        print(f"\n    결과 텍스트: {result_text[:500]}")
        
        if '구매' in result_text and '완료' in result_text:
            print("    ✅ 구매 완료된 것 같음!")
        elif '세션' in result_text or '로그인' in result_text:
            print("    ❌ 세션 만료")
        elif '비정상' in result_text:
            print("    ❌ 비정상 접속 감지")
        else:
            print("    ⚠️ 결과 불명확 — 스크린샷 확인 필요")

finally:
    driver.quit()
    print("\nDone!")
