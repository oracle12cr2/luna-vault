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
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)

try:
    # 1. 메인 페이지에서 로그인 관련 요소 탐색
    print("=== 메인 페이지 ===")
    driver.get("https://www.dhlottery.co.kr/common.do?method=main")
    time.sleep(3)
    print(f"Title: {driver.title}")
    print(f"URL: {driver.current_url}")
    
    # 로그인 관련 링크/버튼 찾기
    all_links = driver.find_elements(By.TAG_NAME, 'a')
    for link in all_links:
        href = link.get_attribute('href') or ''
        text = link.text.strip()
        onclick = link.get_attribute('onclick') or ''
        if any(k in (text + href + onclick).lower() for k in ['로그인', 'login', 'signin']):
            print(f"  Link: text='{text}', href='{href}', onclick='{onclick}'")
    
    # 2. 로그인 페이지 직접 접근
    login_urls = [
        "https://dhlottery.co.kr/user.do?method=login",
        "https://www.dhlottery.co.kr/user.do?method=login",
        "https://www.dhlottery.co.kr/user.do?method=login&returnUrl=",
        "https://www.dhlottery.co.kr/gameLogin.do?method=login",
    ]
    
    for url in login_urls:
        print(f"\n=== Trying: {url} ===")
        driver.get(url)
        time.sleep(3)
        print(f"Final URL: {driver.current_url}")
        print(f"Title: {driver.title}")
        
        # iframe 확인
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"Iframes: {len(iframes)}")
        for iframe in iframes:
            print(f"  iframe: id={iframe.get_attribute('id')}, name={iframe.get_attribute('name')}, src={iframe.get_attribute('src')}")
        
        # input 확인
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"Inputs: {len(inputs)}")
        for inp in inputs:
            itype = inp.get_attribute('type')
            iid = inp.get_attribute('id')
            iname = inp.get_attribute('name')
            iplaceholder = inp.get_attribute('placeholder')
            print(f"  input: id={iid}, name={iname}, type={itype}, placeholder={iplaceholder}")
        
        # form 확인
        forms = driver.find_elements(By.TAG_NAME, 'form')
        print(f"Forms: {len(forms)}")
        for form in forms:
            print(f"  form: id={form.get_attribute('id')}, action={form.get_attribute('action')}, method={form.get_attribute('method')}")
        
        # iframe 안으로 들어가서 확인
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                inputs2 = driver.find_elements(By.TAG_NAME, 'input')
                print(f"\n  Inside iframe '{iframe.get_attribute('id') or iframe.get_attribute('name') or iframe.get_attribute('src')}':")
                print(f"  Inputs inside iframe: {len(inputs2)}")
                for inp in inputs2:
                    print(f"    input: id={inp.get_attribute('id')}, name={inp.get_attribute('name')}, type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}")
                forms2 = driver.find_elements(By.TAG_NAME, 'form')
                for form in forms2:
                    print(f"    form: id={form.get_attribute('id')}, action={form.get_attribute('action')}, method={form.get_attribute('method')}")
                driver.switch_to.default_content()
            except Exception as e:
                print(f"  iframe switch error: {e}")
                driver.switch_to.default_content()
        
        # 스크린샷
        driver.save_screenshot(f'/tmp/dhlottery_explore_{login_urls.index(url)}.png')
        
        if len(inputs) > 2 or len(iframes) > 0:
            break

finally:
    driver.quit()
    print("\nDone!")
