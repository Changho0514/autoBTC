import requests
import pyupbit
import os
import time
import json
import base64
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from ta import add_all_ta_features
from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.trend import MACD

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 보조지표를 데이터프레임에 추가하는 함수
def add_indicators(df_day, df_hour):

    df_day = dropna(df_day)
    df_hour = dropna(df_hour)

    # Bollinger Bands (일봉)
    indicator_bb_day = BollingerBands(close=df_day["close"], window=20, window_dev=2)
    df_day['bb_bbm'] = indicator_bb_day.bollinger_mavg()
    df_day['bb_bbh'] = indicator_bb_day.bollinger_hband()
    df_day['bb_bbl'] = indicator_bb_day.bollinger_lband()

    # Bollinger Bands (시간봉)
    indicator_bb_hour = BollingerBands(close=df_hour["close"], window=20, window_dev=2)
    df_hour['bb_bbm'] = indicator_bb_hour.bollinger_mavg()
    df_hour['bb_bbh'] = indicator_bb_hour.bollinger_hband()
    df_hour['bb_bbl'] = indicator_bb_hour.bollinger_lband()

    # Simple Moving Average (SMA) 추가 (일봉)
    sma_indicator_day = SMAIndicator(close=df_day["close"], window=14)
    df_day['sma_14'] = sma_indicator_day.sma_indicator()

    # Exponential Moving Average (EMA) 추가 (일봉)
    ema_indicator_day = EMAIndicator(close=df_day["close"], window=14)
    df_day['ema_14'] = ema_indicator_day.ema_indicator()

    # RSI (일봉)
    rsi_day = RSIIndicator(close=df_day["close"], window=14)
    df_day['rsi_14'] = rsi_day.rsi()

    # MACD (일봉)
    macd_day = MACD(close=df_day["close"])
    df_day['macd'] = macd_day.macd()
    df_day['macd_signal'] = macd_day.macd_signal()
    df_day['macd_diff'] = macd_day.macd_diff()

    return df_day, df_hour

# 공포와 탐욕 지수 가져오기
def get_fear_and_greed_index():
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data'][0]
    else:
        print(f"Failed to fetch Fear and Greed Index. Status code: {response.status_code}")
        return None

# 최신 비트코인 뉴스 가져오기
def get_latest_news():
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_news",
        "q": "Bitcoin",
        "gl": "us",  # 미국 뉴스
        "hl": "en",  # 영어
        "api_key": SERP_API_KEY
    }
    
    response = requests.get(url, params=params)
    news_data = response.json()

    if "news_results" in news_data:
        headlines = [{"title": news["title"], "date": news["date"]} for news in news_data["news_results"][:5]]
        print("Latest Bitcoin News Headlines:", headlines)
        return headlines
    else:
        print("No news results found")
        return []

# ChromeDriver 초기화
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# 디버깅 메시지 출력 함수
def debug_message(message):
    print(f"[DEBUG] {message}")

# 클릭 시도 함수
def try_click_element(driver, by, value, element_name, wait_time=10):
    try:
        debug_message(f"Trying to click {element_name}...")
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        debug_message(f"Clicked {element_name} successfully!")
        time.sleep(1)
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

# 업비트 차트 페이지 열기
def open_upbit_chart(driver):
    debug_message("Opening the web page...")
    driver.get('https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC')
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    debug_message("Page loaded successfully.")

# 시간 주기 선택 (1시간)
def select_time_period(driver):
    if try_click_element(driver, By.CSS_SELECTOR, ".ciq-menu.ciq-period", "Time Period Menu"):
        time.sleep(1)
        if not try_click_element(driver, By.CSS_SELECTOR, 'cq-item[stxtap="Layout.setPeriodicity(1,60,\'minute\')"]', "1시간"):
            debug_message("Failed to click '1시간' option after opening menu.")

# 볼린저 밴드 추가
def select_bollinger_band(driver):
    if try_click_element(driver, By.CSS_SELECTOR, ".ciq-menu.ciq-studies", "Indicator Menu"):
        time.sleep(1)
        if not try_click_element(driver, By.CSS_SELECTOR, "#fullChartiq > div > div > div.ciq-nav > div > div > cq-menu.ciq-menu.ciq-studies.collapse.stxMenuActive > cq-menu-dropdown > cq-scroll > cq-studies > cq-studies-content > cq-item:nth-child(15)", "Bollinger Bands"):
            debug_message("Failed to select '볼린저 밴드' option.")

# 차트 스크린샷을 Base64로 변환하여 GPT-4 분석에 사용
def capture_screenshot(driver):
    debug_message("Capturing chart screenshot...")
    filename = "upbit_chart.png"
    driver.save_screenshot(filename)
    
    with open(filename, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
    debug_message("Screenshot captured and encoded in base64.")
    return base64_image

# GPT-4 Vision 모델로 차트 분석
def analyze_with_gpt(base64_image, indicators):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What’s in this image and what should be my trading decision?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Here are some technical indicators: {indicators}"
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

# 자동 매매 로직
def ai_trading():
    # 1. Selenium을 통해 웹 페이지에서 차트 설정
    driver = init_driver()
    open_upbit_chart(driver)
    select_time_period(driver)
    select_bollinger_band(driver)
    
    # 2. 차트 스크린샷 찍고 Base64 인코딩
    base64_image = capture_screenshot(driver)

    # 3. 업비트 차트 데이터 가져오기 (30일 일봉, 24시간 봉)
    df_day = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")  
    df_24h = pyupbit.get_ohlcv("KRW-BTC", count=24, interval="minute60")

    # 보조지표 추가
    df_day, df_24h = add_indicators(df_day, df_24h)

    # 4. 보조지표 데이터 GPT-4에 제공
    indicators = {
        "Bollinger Bands (Day)": df_day[["bb_bbm", "bb_bbh", "bb_bbl"]].tail(1).to_dict(),
        "RSI (Day)": df_day["rsi_14"].tail(1).values[0],
        "MACD (Day)": df_day["macd_diff"].tail(1).values[0]
    }
    
    result = analyze_with_gpt(base64_image, indicators)
    
    # 5. 결과 출력
    print("GPT-4 Trading Decision:")
    print(json.dumps(result, indent=4))

    # Selenium 브라우저 닫기
    driver.quit()

ai_trading()
