from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
driver.get("https://www.dhlottery.co.kr/user.do?method=login&returnUrl=")
time.sleep(3)

# 페이지 소스에서 input 필드 찾기
page = driver.page_source
driver.save_screenshot('/tmp/dhlottery_login_page.png')

# input 태그 추출
from selenium.webdriver.common.by import By
inputs = driver.find_elements(By.TAG_NAME, 'input')
for inp in inputs:
    print(f"id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}")

# iframe 확인
iframes = driver.find_elements(By.TAG_NAME, 'iframe')
print(f"\nIframes found: {len(iframes)}")
for iframe in iframes:
    print(f"  iframe src={iframe.get_attribute('src')}, id={iframe.get_attribute('id')}")

driver.quit()
