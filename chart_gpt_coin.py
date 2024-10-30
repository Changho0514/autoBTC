import os
from dotenv import load_dotenv
import pandas as pd
import json
import jwt
import uuid
import time
import requests
from openai import OpenAI
import ta
from ta.utils import dropna
import logging
from datetime import datetime, timedelta
import sqlite3
from pydantic import BaseModel

class TradingDecision(BaseModel):
    decision: str
    percentage: int
    reason: str

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# JWT 인증 토큰 생성 함수
def generate_auth_token():
    access_key = os.getenv("BITHUMB_ACCESS_KEY")
    secret_key = os.getenv("BITHUMB_SECRET_KEY")
    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
        'timestamp': round(time.time() * 1000)
    }
    jwt_token = jwt.encode(payload, secret_key)
    authorization_token = f'Bearer {jwt_token}'
    headers = {'Authorization': authorization_token}
    logger.debug("Generated JWT token for authorization.")
    return headers

# 보조 지표 추가 함수
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

    # Stochastic
    stoch = ta.momentum.StochasticOscillator(close=df['close'], high=df['high'], low=df['low'], window=14, smooth_window=3)
    df['stoch_k'] = stoch.stoch()  # %K
    df['stoch_d'] = stoch.stoch_signal()  # %D
    
    return df

def get_balances():
    url = "https://api.bithumb.com/v1/accounts"
    headers = generate_auth_token()
    response = requests.get(url, headers=headers)
    
    try:
        # JSON 응답이 제대로 파싱되는지 확인
        data = response.json()
        
        # 응답 형식 확인 및 디버깅 로그 추가
        if not isinstance(data, list):
            logger.error("Expected list format for balance data, but got %s", type(data))
            return {'krw_balance': 0, 'btc_balance': 0, 'btc_avg_buy_price': 0}
        
        logger.debug("Balance data retrieved: %s", data)

        # KRW와 BTC 데이터 추출, 없을 경우 기본값 설정
        krw_data = next((item for item in data if item['currency'] == 'KRW'), {'balance': 0})
        btc_data = next((item for item in data if item['currency'] == 'BTC'), {'balance': 0, 'avg_buy_price': 0})
        
        # 잔액과 평균 매수 단가 추출
        krw_balance = float(krw_data.get('balance', 0))
        btc_balance = float(btc_data.get('balance', 0))
        btc_avg_buy_price = float(btc_data.get('avg_buy_price', 0))

        return {
            'krw_balance': krw_balance,
            'btc_balance': btc_balance,
            'btc_avg_buy_price': btc_avg_buy_price
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Error parsing balance data: %s", e)
        return {'krw_balance': 0, 'btc_balance': 0, 'btc_avg_buy_price': 0}


# 현재가 조회 함수
def get_current_price(market="KRW-BTC"):
    url = f"https://api.bithumb.com/v1/ticker?markets={market}"
    response = requests.get(url)
    logger.debug("현재가 가져오기 성공")

   
    if response.status_code != 200:
        logger.error("Error fetching current price: %s", response.status_code)
        return None
    
    try:
        data = response.json()
        logger.debug("현재가 가져오기 성공")
        return data
    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON response for current price: %s", e)
        return None
    
# 오더북 조회 함수
def get_orderbook(market="KRW-BTC"):
    url = f"https://api.bithumb.com/v1/orderbook?markets={market}"
    response = requests.get(url)
    
    try:
        data = response.json()
        logger.debug("오더북 가져오기 성공")

        # 데이터가 리스트 형식인 경우 첫 번째 요소를 사용
        if isinstance(data, list) and len(data) > 0:
            orderbook = data[0]  # 첫 번째 요소 선택
            orderbook_data = {
                "best_ask_price": orderbook["orderbook_units"][0]["ask_price"],
                "best_bid_price": orderbook["orderbook_units"][0]["bid_price"],
                "total_ask_size": orderbook["total_ask_size"],
                "total_bid_size": orderbook["total_bid_size"]
            }
            return orderbook_data
        else:
            logger.error("Unexpected data format for orderbook: %s", data)
            return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error("Error processing orderbook data: %s", e)
        return None

# SQLite DB 초기화
def init_db():
    conn = sqlite3.connect('trading_data1.db')
    cursor = conn.cursor()
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
    logger.debug("Database initialized and table created if not exists.")
    return conn

def get_db_connection():
    return sqlite3.connect('trading_data1.db')

def fetch_ohlcv_data(url):
    response = requests.get(url, headers={"accept": "application/json"})
    try:
        data = response.json()
        if isinstance(data, list):
            logger.debug("OHLCV data retrieved successfully.")
            df = pd.DataFrame(data)
            return df
        else:
            logger.error("Unexpected data format for OHLCV data: %s", type(data))
            return pd.DataFrame()
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Error parsing OHLCV data: %s", e)
        return pd.DataFrame()

def get_daily_ohlcv(market="KRW-BTC", count=30):
    url = f"https://api.bithumb.com/v1/candles/days?market={market}&count={count}"
    df_daily = fetch_ohlcv_data(url)

    if not df_daily.empty:
        df_daily = df_daily.rename(columns={
            'opening_price': 'open',
            'high_price': 'high',
            'low_price': 'low',
            'trade_price': 'close',
            'candle_acc_trade_volume': 'volume'
        })
        df_daily['candle_date_time_kst'] = pd.to_datetime(df_daily['candle_date_time_kst'])
        df_daily.set_index('candle_date_time_kst', inplace=True)
        
    return df_daily

def get_hourly_ohlcv(market="KRW-BTC", count=24):
    url = f"https://api.bithumb.com/v1/candles/minutes/60?market={market}&count={count}"
    df_hourly = fetch_ohlcv_data(url)

    if not df_hourly.empty:
        df_hourly = df_hourly.rename(columns={
            'opening_price': 'open',
            'high_price': 'high',
            'low_price': 'low',
            'trade_price': 'close',
            'candle_acc_trade_volume': 'volume'
        })
        df_hourly['candle_date_time_kst'] = pd.to_datetime(df_hourly['candle_date_time_kst'])
        df_hourly.set_index('candle_date_time_kst', inplace=True)
        
    return df_hourly


def get_recent_trades(conn, days=7):
    c = conn.cursor()
    seven_days_ago = (datetime.now() - timedelta(days=days)).isoformat()
    c.execute("SELECT * FROM trades WHERE timestamp > ? ORDER BY timestamp DESC", (seven_days_ago,))
    columns = [column[0] for column in c.description]
    return pd.DataFrame.from_records(data=c.fetchall(), columns=columns)

def calculate_performance(trades_df):
    if trades_df.empty or len(trades_df) < 2:
        return 0  # 데이터가 없거나 거래가 2건 미만인 경우 0 반환
    
    # 직전 거래와 비교
    previous_trade = trades_df.iloc[-2]
    current_trade = trades_df.iloc[-1]

    initial_balance = previous_trade['krw_balance'] + previous_trade['btc_balance'] * previous_trade['btc_krw_price']
    final_balance = current_trade['krw_balance'] + current_trade['btc_balance'] * current_trade['btc_krw_price']
    
    return (final_balance - initial_balance) / initial_balance * 100

def buy_order(amount):
    current_price_data = get_current_price("KRW-BTC")
    if current_price_data is None or not current_price_data:
        logger.error("Failed to fetch current price for buy order.")
        return None
    
    # 첫 번째 요소에서 'trade_price' 가져오기
    closing_price = current_price_data[0].get("trade_price")
    
    request_body = {
        'market': 'KRW-BTC',
        'side': 'bid',
        'volume': str(amount),  # 매수 수량
        'price': str(closing_price),  # 현재가 사용
        'ord_type': 'price',  # 시장가 매수
    }

    headers = {
        'Authorization': generate_auth_token()
    }

    response = requests.post("https://api.bithumb.com/v1/orders", headers=headers, data=request_body)

    if response.status_code == 201:
        return response.json()  # 주문 성공시 응답 반환
    else:
        logger.error("Buy order failed: %s", response.json())
        return None

def sell_order(amount):
    current_price_data = get_current_price("KRW-BTC")
    if current_price_data is None or not current_price_data:
        logger.error("Failed to fetch current price for sell order.")
        return None
    
    # 첫 번째 요소에서 'trade_price' 가져오기
    closing_price = current_price_data[0].get("trade_price")

    request_body = {
        'market': 'KRW-BTC',
        'side': 'ask',
        'volume': str(amount),  # 매도 수량
        'price': str(closing_price),  # 현재가 사용
        'ord_type': 'market',  # 시장가 매도
    }

    headers = {
        'Authorization': generate_auth_token()
    }

    response = requests.post("https://api.bithumb.com/v1/orders", headers=headers, data=request_body)

    if response.status_code == 201:
        return response.json()  # 주문 성공시 응답 반환
    else:
        logger.error("Sell order failed: %s", response.json())
        return None

def generate_reflection(trades_df, current_market_data):
    performance = calculate_performance(trades_df)
    
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are an AI trading assistant tasked with analyzing recent trading performance and current market conditions to generate insights and improvements for future trading decisions."
            },
            {
                "role": "user",
                "content": f"""
                Recent trading data:
                {trades_df.to_json(orient='records')}
                
                Current market data:
                {current_market_data}
                
                Overall performance during the last trading period: {performance:.2f}%
                
                Please analyze this data and provide:
                1. A brief reflection on the recent trading decisions
                2. What specific strategies or indicators were successful or unsuccessful?
                3. Suggestions for improvement in future trading decisions
                4. Any patterns or trends you notice in the market data
                
                Limit your response to 250 words or less.
                """
            }
        ]
    )
    
    return response.choices[0].message.content


def save_trade_data_with_reflection(conn, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection):
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO trades (timestamp, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_time, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection))
    conn.commit()
    logger.debug("Trade data saved to database.")

def ai_trading():
    # 1. 현재 투자 상태 조회
    balances = get_balances()

    # BTC와 KRW 잔액 조회
    btc_balance = balances['btc_balance']
    krw_balance = balances['krw_balance']
    btc_avg_buy_price = balances['btc_avg_buy_price']
    

    # 2. 오더북(호가 데이터) 조회
    orderbook = get_orderbook()
    

    # 3. 현재 BTC 가격 조회
    btc_krw_price_data = get_current_price("KRW-BTC")
    btc_krw_price = btc_krw_price_data[0]["trade_price"]  # 현재 가격 추출

    # 4. 차트 데이터 조회 및 보조지표 추가
    df_daily = get_daily_ohlcv("KRW-BTC", 30)
    df_daily = dropna(df_daily)
    df_daily = add_indicators(df_daily)

    df_hourly = get_hourly_ohlcv("KRW-BTC", 24)
    df_hourly = dropna(df_hourly)
    df_hourly = add_indicators(df_hourly)

    # OpenAI 요청 데이터 준비
    current_market_data = {
        "orderbook": orderbook,
        "recent_daily_ohlcv": df_daily,
        "recent_hourly_ohlcv": df_hourly
    }

    # 7. YouTube 자막 데이터 가져오기
    f = open("strategy1.txt", "r", encoding="UTF-8")
    youtube_transcript = f.read()
    f.close()

    # 최근 거래 내역 조회 및 reflection 생성
    conn = get_db_connection()
    recent_trades = get_recent_trades(conn)
    reflection = generate_reflection(recent_trades, current_market_data)

    # OpenAI API 호출로 거래 결정 요청
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
        {
            "role": "system",
            "content": """You are an expert in Bitcoin investing and must always incorporate the trading strategies in the provided YouTube video transcript. Analyze the provided data and give priority to YouTube's strategies when making your decision. Your analysis should include:
            - Technical indicators and market data
            - The strategies from the YouTube video
            - Recent trading performance and reflection

            Recent trading reflection:
            {reflection}

            Response format:
                1. Decision (buy, sell, or hold)
                2. If the decision is 'buy', provide a percentage (1-100) of available KRW to use for buying.
                If the decision is 'sell', provide a percentage (1-100) of held BTC to sell.
                If the decision is 'hold', set the percentage to 0.
                3. Reason for your decision

                Ensure that the percentage is an integer between 1 and 100 for buy/sell decisions, and exactly 0 for hold decisions.
                Your percentage should reflect the strength of your conviction in the decision based on the analyzed data.
        
            """
        },
        {
            "role": "user",
            "content": f"""Current investment status: {json.dumps(balances)}
            Orderbook: {json.dumps(orderbook)}
            Daily OHLCV with indicators (30 days): {df_daily.to_json()}
            Hourly OHLCV with indicators (24 hours): {df_hourly.to_json()}
            YouTube Video Transcript: {youtube_transcript}"""
        }
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "trading_decision",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string", "enum": ["buy", "sell", "hold"]},
                    "percentage": {
                        "type": "integer"
                    },
                    "reason": {"type": "string"}
                },
                "required": ["decision", "percentage", "reason"],
                "additionalProperties": False
            }
        }
    },
        max_tokens=4095
    )

     # 응답을 문자열로 가져오기
    response_content = response.choices[0].message.content.strip()
    
    try:
        # JSON 파싱
        result = TradingDecision.parse_raw(response_content)
        logger.debug("AI Decision: %s, Reason: %s", result.decision, result.reason)
    except Exception as e:
        logger.error("Error parsing TradingDecision: %s", e)
        logger.debug("Response content: %s", response_content)
        return

    print(f"### AI Decision: {result.decision.upper()} ###")
    print(f"### Reason: {result.reason} ###")

    # 총 자산 계산
    btc_balance = balances.get('btc_balance', 0) or 0
    krw_balance = balances.get('krw_balance', 0) or 0
    total_asset = (btc_balance * btc_krw_price) + krw_balance

    # 매매 후 저장할 데이터를 모은 후, 거래 실행 후 저장
    if result.decision == "buy":
        amount_to_buy = krw_balance * (result.percentage / 100) * 0.9995  # 지정된 비율만큼 매수
        if amount_to_buy > 5000:
            print(f"### Buy Order Executed: Buying {result.percentage}% of available KRW ###")
            order_result = buy_order(amount_to_buy)  # Bithumb에서 매수 주문 실행
            print(order_result)
        else:
            print("### Buy Order Failed: Insufficient KRW (less than 5000 KRW) ###")

    elif result.decision == "sell":
        amount_to_sell = btc_balance * (result.percentage / 100)  # 지정된 비율만큼 매도
        if amount_to_sell * btc_krw_price > 5000:
            print(f"### Sell Order Executed: Selling {result.percentage}% of available BTC ###")
            order_result = sell_order(amount_to_sell)  # Bithumb에서 매도 주문 실행
            print(order_result)
        else:
            print("### Sell Order Failed: Insufficient BTC (less than 5000 KRW worth) ###")
            
    elif result.decision == "hold":
        print("### Hold Position ###")

    # 거래 실행 여부와 관계없이 현재 잔고 조회
    time.sleep(1)  # API 호출 제한을 고려하여 잠시 대기
    balances = get_balances()  # Bithumb API를 통해 잔고 다시 조회
    btc_balance = balances['btc_balance']
    krw_balance = balances['krw_balance']
    btc_avg_buy_price = balances['btc_avg_buy_price']

    # 9. 반성 내용 생성 및 데이터 저장
    save_trade_data_with_reflection(conn, result.decision, result.percentage, result.reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset, reflection)

    # 데이터베이스 연결 종료
    conn.close()

# 메인 루프
while True:
    try:
        ai_trading()
        time.sleep(3600)  # 1시간마다 실행
    except Exception as e:
        logger.error("An error occurred in ai_trading: %s", e)
        time.sleep(300)  # 오류 발생 시 5분 후 재시도
