import os
from dotenv import load_dotenv
import pyupbit
import pandas as pd
import json
import google.generativeai as genai
import ta
from ta.utils import dropna
import time
import requests
import base64
from PIL import Image
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException, NoSuchElementException
import logging
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import BaseModel
import sqlite3

class TradingDecision(BaseModel):
    decision: str
    percentage: int
    reason: str

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Gemini API 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def add_indicators(df):
    # 볼린저 밴드
    indicator_bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()
    df['bb_bbh'] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()
    
    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
    
    # MACD
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    # 이동평균선
    df['sma_20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()
    
    return df

def get_fear_and_greed_index():
    url = "https://api.alternative.me/fng/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data'][0]
    else:
        logger.error(f"Failed to fetch Fear and Greed Index. Status code: {response.status_code}")
        return None

def get_latest_news():
    """SerpApi를 이용하여 최신 비트코인 관련 뉴스 가져오기"""
    url = "https://serpapi.com/search"
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    params = {
        "engine": "google_news",
        "q": "Bitcoin",
        "gl": "us",  # 미국 뉴스
        "hl": "en",  # 영어
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # HTTP 에러 발생 시 예외

        news_data = response.json()

        if "news_results" not in news_data:
            print(f"⚠️ 'news_results'가 응답에 없음: {news_data}")
            return []

        news_results = news_data["news_results"][:5]
        all_stories = []

        for news in news_results:
            top_level_title = news.get("title", "No title available")
            all_stories.append({"title": top_level_title, "date": "No date (top-level)"})

            for story in news.get("stories", []):
                title = story.get("title", "No title available")
                date = story.get("date", "No date available")
                all_stories.append({"title": title, "date": date})

        return all_stories

    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 에러 발생: {e}")
    except ValueError as e:
        print(f"❌ JSON 파싱 에러: {e}")
    except KeyError as e:
        print(f"❌ 응답 데이터에 필요한 키가 없음: {e}")
    except Exception as e:
        print(f"❌ 알 수 없는 에러: {e}")

    return []  # 에러 발생 시 빈 리스트 반환

def setup_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")  # 디버깅을 위해 헤드리스 모드 비활성화
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return chrome_options

def create_driver():
    logger.info("ChromeDriver 설정 중...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=setup_chrome_options())
    return driver

def click_element_by_xpath(driver, xpath, element_name, wait_time=10):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        # 요소가 뷰포트에 보일 때까지 스크롤
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        # 요소가 클릭 가능할 때까지 대기
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        logger.info(f"{element_name} 클릭 완료")
        time.sleep(2)  # 클릭 후 잠시 대기
    except TimeoutException:
        logger.error(f"{element_name} 요소를 찾는 데 시간이 초과되었습니다.")
    except ElementClickInterceptedException:
        logger.error(f"{element_name} 요소를 클릭할 수 없습니다. 다른 요소에 가려져 있을 수 있습니다.")
    except NoSuchElementException:
        logger.error(f"{element_name} 요소를 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"{element_name} 클릭 중 오류 발생: {e}")

def perform_chart_actions(driver):
    # 시간 메뉴 클릭
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]",
        "시간 메뉴"
    )
    
    # 1시간 옵션 선택
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]",
        "1시간 옵션"
    )
    
    # 지표 메뉴 클릭
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]",
        "지표 메뉴"
    )
    
    # 볼린저 밴드 옵션 선택
    click_element_by_xpath(
        driver,
        "/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]",
        "볼린저 밴드 옵션"
    )

def capture_and_encode_screenshot(driver):
    try:
        # 스크린샷 캡처
        png = driver.get_screenshot_as_png()
        
        # PIL Image로 변환
        img = Image.open(io.BytesIO(png))
        
        # 이미지 리사이즈 (OpenAI API 제한에 맞춤)
        img.thumbnail((2000, 2000))
        
        # 현재 시간을 파일명에 포함
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upbit_chart_{current_time}.png"
        
        # 현재 스크립트의 경로를 가져옴
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 파일 저장 경로 설정
        file_path = os.path.join(script_dir, filename)
        
        # 이미지 파일로 저장
        img.save(file_path)
        logger.info(f"스크린샷이 저장되었습니다: {file_path}")
        
        # 이미지를 바이트로 변환
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        
        # base64로 인코딩
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return base64_image, file_path
    except Exception as e:
        logger.error(f"스크린샷 캡처 및 인코딩 중 오류 발생: {e}")
        return None, None

def get_combined_transcript(playlist):
    subscribes = []
    try:
        for video_id in playlist:
            sentences = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
            # 각 비디오의 텍스트를 하나의 문자열로 결합하여 리스트에 추가
            combined_text = " ".join([sentence['text'] for sentence in sentences])
            subscribes.append(combined_text)
    except Exception as e:
        print(f"Error fetching YouTube transcript for video {video_id}: {e}")
    
    return subscribes

# SQLite DB 연결 및 테이블 생성 함수 (연결을 반환)
def init_db():
    conn = sqlite3.connect('trading_data.db')
    cursor = conn.cursor()
    
    # 테이블이 존재하지 않으면 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        decision TEXT,
        percentage INTEGER,
        reason TEXT,
        btc_balance REAL,
        krw_balance REAL,
        btc_avg_buy_price REAL,
        btc_krw_price REAL,
        total_asset REAL,
        reflection TEXT
    )
    ''')
    
    conn.commit()
    return conn  # 연결을 닫지 않고 반환하여 이후 트랜잭션에서 계속 사용할 수 있도록 함

def get_db_connection():
    return sqlite3.connect('trading_data.db')

# 매매 데이터를 DB에 저장하는 함수 (conn을 전달받아 사용)
def save_trade_data_with_reflection(conn, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection):
    cursor = conn.cursor()

    # 현재 시간을 가져옴
    current_time = datetime.now().isoformat()

    # 데이터를 테이블에 삽입
    cursor.execute('''
    INSERT INTO trades (timestamp, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_time, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection))
    
    conn.commit()

def get_recent_trades(conn, days=7):
    c = conn.cursor()
    seven_days_ago = (datetime.now() - timedelta(days=days)).isoformat()
    c.execute("SELECT * FROM trades WHERE timestamp > ? ORDER BY timestamp DESC", (seven_days_ago,))
    columns = [column[0] for column in c.description]
    return pd.DataFrame.from_records(data=c.fetchall(), columns=columns)


def calculate_performance(trades_df):
    if trades_df.empty:
        return 0
    
    initial_balance = trades_df.iloc[-1]['krw_balance'] + trades_df.iloc[-1]['btc_balance'] * trades_df.iloc[-1]['btc_krw_price']
    final_balance = trades_df.iloc[0]['krw_balance'] + trades_df.iloc[0]['btc_balance'] * trades_df.iloc[0]['btc_krw_price']
    
    return (final_balance - initial_balance) / initial_balance * 100

def generate_reflection(trades_df, current_market_data):
    performance = calculate_performance(trades_df)

    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""당신은 최근 트레이딩 성과와 현재 시장 상황을 분석하여 향후 트레이딩 결정에 대한 인사이트와 개선점을 제공하는 AI 트레이딩 어시스턴트입니다.

최근 거래 데이터:
{trades_df.to_json(orient='records')}

현재 시장 데이터:
{current_market_data}

최근 7일간 수익률: {performance:.2f}%

다음 내용을 분석하여 **반드시 한글로** 응답해주세요:
1. 최근 거래 결정에 대한 간략한 평가
2. 잘된 점과 개선이 필요한 점
3. 향후 거래 결정을 위한 제안
4. 시장 데이터에서 발견한 패턴이나 트렌드

250단어 이내로 작성해주세요.
"""

    response = model.generate_content(prompt)
    return response.text

# 처음에 없다면 db를 만들어줘야한다.
init_db()

# 매매 판단 및 실행 함수
def ai_trading():
    # Upbit 객체 생성
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    upbit = pyupbit.Upbit(access, secret)

    # 1. 현재 투자 상태 조회
    all_balances = upbit.get_balances()

    # BTC와 KRW 잔액 조회
    btc_balance = upbit.get_balance("BTC")
    krw_balance = upbit.get_balance("KRW")
    btc_avg_buy_price = None
    for balance in all_balances:
        if balance['currency'] == 'BTC':
            btc_avg_buy_price = float(balance['avg_buy_price'])
            break

    # 2. 오더북(호가 데이터) 조회
    orderbook = pyupbit.get_orderbook("KRW-BTC")
    
    # 3. 현재 BTC 가격 조회
    btc_krw_price = pyupbit.get_current_price("KRW-BTC")

    # 4. 차트 데이터 조회 및 보조지표 추가
    df_daily = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=30)
    df_daily = dropna(df_daily)
    df_daily = add_indicators(df_daily)
    
    df_hourly = pyupbit.get_ohlcv("KRW-BTC", interval="minute60", count=24)
    df_hourly = dropna(df_hourly)
    df_hourly = add_indicators(df_hourly)

    # 5. 공포 탐욕 지수 가져오기
    fear_greed_index = get_fear_and_greed_index()

    # 6. 뉴스 헤드라인 가져오기
    news_headlines = get_latest_news()

    # 7. YouTube 자막 데이터 가져오기
    # playlist = ['6itriowPhhM', 'Ln2PevCHEuU', 'Li3EV0YVuSg', '3XbtEX3jUv4']
    # youtube_transcript = get_combined_transcript(playlist)
    # # 리스트를 문자열로 변환 (각 항목을 줄바꿈으로 구분)
    # youtube_transcript_str = "\n".join(youtube_transcript)

    # # 파일에 저장
    # with open("strategy.txt", "w", encoding="UTF-8") as f:
    #     f.write(youtube_transcript_str)
    # f.close()

    # 파일에서 YouTube 자막 데이터를 읽어오기
    f = open("strategy.txt", "r", encoding="UTF-8")
    youtube_transcript = f.read()
    f.close()

    # 8. 과거 거래 조회 및 성과 계산
    # 데이터베이스 연결
    conn = get_db_connection()
    
    # 최근 거래 내역 가져오기
    recent_trades = get_recent_trades(conn)
    
    # 현재 시장 데이터 수집 (기존 코드에서 가져온 데이터 사용)
    current_market_data = {
        "fear_greed_index": fear_greed_index,
        "news_headlines": news_headlines,
        "orderbook": orderbook,
        "daily_ohlcv": df_daily.to_dict(),
        "hourly_ohlcv": df_hourly.to_dict()
    }
    # 반성 및 개선 내용 생성
    reflection = generate_reflection(recent_trades, current_market_data)

    # Gemini 모델로 거래 결정
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""당신은 비트코인 투자 전문가이며, 제공된 유튜브 영상 자막(한국어)에 설명된 전설적인 한국 투자자 '원요티'의 트레이딩 전략을 항상 참고해야 합니다. 제공된 데이터를 분석하고 원요티의 전략을 우선적으로 고려하여 결정을 내려주세요.

분석에 포함할 내용:
- 기술적 지표 및 시장 데이터
- 최근 뉴스 헤드라인과 비트코인 가격에 미칠 영향
- 공포탐욕지수와 그 의미
- 전반적인 시장 심리
- 유튜브 영상의 전략
- 최근 거래 성과 및 반성

최근 거래 분석:
{reflection}

현재 투자 상태: {json.dumps(all_balances)}
호가창: {json.dumps(orderbook)}
일봉 OHLCV 및 지표 (30일): {df_daily.to_json()}
시간봉 OHLCV 및 지표 (24시간): {df_hourly.to_json()}
최근 뉴스 헤드라인: {json.dumps(news_headlines)}
공포탐욕지수: {json.dumps(fear_greed_index)}
유튜브 영상 자막: {youtube_transcript}

중요: 반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{{"decision": "buy" 또는 "sell" 또는 "hold", "percentage": 0-100 사이의 정수, "reason": "한글로 작성된 거래 근거"}}

규칙:
- decision은 반드시 "buy", "sell", "hold" 중 하나여야 합니다
- "buy"인 경우: percentage는 1-100 (사용할 KRW의 비율)
- "sell"인 경우: percentage는 1-100 (매도할 BTC의 비율)
- "hold"인 경우: percentage는 반드시 0
- reason은 **반드시 한글로** 거래 결정의 근거를 설명해주세요
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        )
    )

    # Gemini 응답 파싱
    result = TradingDecision.model_validate_json(response.text)

    print(f"### AI Decision: {result.decision.upper()} ###")
    print(f"### Reason: {result.reason} ###")

    # 총 자산 계산
    total_asset = (btc_balance * btc_krw_price) + krw_balance

    # 매매 후 저장할 데이터를 모은 후, 거래 실행 후 저장
    if result.decision == "buy":
        amount_to_buy = krw_balance * (result.percentage / 100) * 0.9995  # 지정된 비율만큼 매수
        if amount_to_buy > 5000:
            print(f"### Buy Order Executed: Buying {result.percentage}% of available KRW ###")
            order_result = upbit.buy_market_order("KRW-BTC", amount_to_buy)
            print(order_result)
        else:
            print("### Buy Order Failed: Insufficient KRW (less than 5000 KRW) ###")

    elif result.decision == "sell":
        amount_to_sell = btc_balance * (result.percentage / 100)  # 지정된 비율만큼 매도
        if amount_to_sell * btc_krw_price > 5000:
            print(f"### Sell Order Executed: Selling {result.percentage}% of available BTC ###")
            order_result = upbit.sell_market_order("KRW-BTC", amount_to_sell)
            print(order_result)
        else:
            print("### Sell Order Failed: Insufficient BTC (less than 5000 KRW worth) ###")
            
    elif result.decision == "hold":
        print("### Hold Position ###")

    # 거래 실행 여부와 관계없이 현재 잔고 조회
    time.sleep(1)  # API 호출 제한을 고려하여 잠시 대기
    balances = upbit.get_balances()
    btc_balance = next((float(balance['balance']) for balance in balances if balance['currency'] == 'BTC'), 0)
    krw_balance = next((float(balance['balance']) for balance in balances if balance['currency'] == 'KRW'), 0)
    btc_avg_buy_price = next((float(balance['avg_buy_price']) for balance in balances if balance['currency'] == 'BTC'), 0)
    current_btc_price = pyupbit.get_current_price("KRW-BTC")

    # 9. 반성 내용 생성 및 데이터 저장
    save_trade_data_with_reflection(conn, result.decision, result.percentage, result.reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection)

    # 데이터베이스 연결 종료
    conn.close()


# GitHub Actions에서 스케줄링하므로 단일 실행
if __name__ == "__main__":
    try:
        ai_trading()
        logger.info("Trading completed successfully")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e  # GitHub Actions에서 실패를 감지할 수 있도록
