from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import time

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# ChromeDriver 자동 설치 및 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 디버깅용 함수
def debug_message(message):
    print(f"[DEBUG] {message}")

# 클릭 시도 함수
def try_click_element(by, value, element_name, wait_time=10):
    """
    일반 클릭 함수
    :param by: By 객체 (e.g., By.CSS_SELECTOR)
    :param value: 탐색할 셀렉터 또는 XPath 값
    :param element_name: 클릭할 요소의 이름 (디버깅용)
    :param wait_time: 대기 시간 (기본값 10초)
    """
    try:
        debug_message(f"Trying to click {element_name}...")
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        debug_message(f"Clicked {element_name} successfully!")
        time.sleep(1)  # 클릭 후 잠시 대기
        return True
    except TimeoutException:
        debug_message(f"Failed to click {element_name}: Timeout")
        return False
    except ElementClickInterceptedException:
        debug_message(f"Failed to click {element_name}: Element intercepted")
        return False
    except Exception as e:
        debug_message(f"Error clicking {element_name}: {e}")
        return False

# .ciq-menu.ciq-period 및 .ciq-menu.ciq-studies 메뉴 클릭 및 지표 선택
def main():
    # 웹 페이지 열기
    debug_message("Opening the web page...")
    driver.get('https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC')
    
    # 페이지가 로드될 시간을 기다림
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    debug_message("Page loaded successfully.")
    
    # 시간 선택 메뉴 클릭 후 '1시간' 옵션 선택
    if try_click_element(By.CSS_SELECTOR, ".ciq-menu.ciq-period", "Time Period Menu"):
        time.sleep(1)  # 메뉴 열림 대기
        if not try_click_element(By.CSS_SELECTOR, 'cq-item[stxtap="Layout.setPeriodicity(1,60,\'minute\')"]', "1시간"):
            debug_message("Failed to click '1시간' option after opening menu.")
    
    # 지표 메뉴 클릭 후 '볼린저 밴드' 선택
    if try_click_element(By.CSS_SELECTOR, ".ciq-menu.ciq-studies", "Indicator Menu"):
        time.sleep(1)  # 메뉴 열림 대기
        # 볼린저 밴드 클릭 (제공된 Selector 사용)
        if not try_click_element(By.CSS_SELECTOR, "#fullChartiq > div > div > div.ciq-nav > div > div > cq-menu.ciq-menu.ciq-studies.collapse.stxMenuActive > cq-menu-dropdown > cq-scroll > cq-studies > cq-studies-content > cq-item:nth-child(15)", "Bollinger Bands"):
            debug_message("Failed to select '볼린저 밴드' option.")

    # 차트가 업데이트되는 시간을 기다림
    time.sleep(3)

    # 스크린샷 찍기
    filename = "upbit_chart_only.png"
    driver.save_screenshot(filename)
    print(f"스크린샷 저장 완료: {filename}")


main()
