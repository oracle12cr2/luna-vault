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
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)

try:
    # 메인 페이지
    driver.get("https://www.dhlottery.co.kr/common.do?method=main")
    time.sleep(3)
    print("Main:", driver.title)
    
    # 로그인 링크 찾기
    links = driver.find_elements(By.TAG_NAME, 'a')
    for link in links:
        href = link.get_attribute('href') or ''
        text = link.text.strip()
        if '로그인' in text or 'login' in href.lower():
            print(f"Found: text='{text}', href='{href}'")
    
    # 로그인 페이지 직접 접근 시도 (다양한 URL)
    login_urls = [
        "https://www.dhlottery.co.kr/user.do?method=login",
        "https://dhlottery.co.kr/user.do?method=login",
        "https://www.dhlottery.co.kr/gameLogin.do?method=login",
    ]
    
    for url in login_urls:
        driver.get(url)
        time.sleep(2)
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        if len(inputs) > 0:
            print(f"\n✅ Found inputs at: {url}")
            for inp in inputs:
                print(f"  id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, type={inp.get_attribute('type')}")
            driver.save_screenshot('/tmp/dhlottery_login2.png')
            break
        else:
            print(f"❌ No inputs at: {url}")

finally:
    driver.quit()
