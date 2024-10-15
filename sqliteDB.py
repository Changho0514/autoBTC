import sqlite3
from datetime import datetime

# SQLite DB 연결 및 테이블 생성 함수
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
        total_asset REAL
    )
    ''')
    
    conn.commit()
    conn.close()

# 매매 데이터를 DB에 저장하는 함수
def save_trade_data(decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset):
    conn = sqlite3.connect('trading_data.db')
    cursor = conn.cursor()

    # 현재 시간을 가져옴
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 데이터를 테이블에 삽입
    cursor.execute('''
    INSERT INTO trades (timestamp, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_time, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, total_asset))
    
    conn.commit()
    conn.close()

