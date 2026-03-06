from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    # 로그인 페이지
    driver.get("https://www.dhlottery.co.kr/user.do?method=login&returnUrl=")
    time.sleep(2)
    print("Login page:", driver.title)
    
    # 로그인
    driver.find_element(By.ID, 'userId').send_keys('kto2005')
    driver.find_element(By.ID, 'article').send_keys('kto8520!@#')
    time.sleep(0.5)
    
    # 로그인 버튼
    driver.find_element(By.CSS_SELECTOR, '.btn_common.lrg.blu').click()
    time.sleep(3)
    
    print("After login URL:", driver.current_url)
    
    # 로그인 확인
    page_source = driver.page_source
    if '로그아웃' in page_source or 'logout' in page_source.lower():
        print("✅ LOGIN SUCCESS!")
        
        # 예치금 확인
        driver.get("https://www.dhlottery.co.kr/userSsl.do?method=myPage")
        time.sleep(2)
        driver.save_screenshot('/tmp/dhlottery_mypage.png')
        print("MyPage screenshot saved")
    else:
        print("❌ LOGIN FAILED")
        driver.save_screenshot('/tmp/dhlottery_fail.png')
        
finally:
    driver.quit()
    print("DONE")
