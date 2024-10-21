import os
from dotenv import load_dotenv
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import pyupbit  # PyUpbit 추가

load_dotenv()
access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")
# 데이터베이스 연결 함수
def get_connection():
    return sqlite3.connect('trading_data.db')

# 데이터 로드 함수
def load_data():
    conn = get_connection()
    query = "SELECT * FROM trades"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# PyUpbit API를 이용한 현재 잔고 및 자산 조회 함수
def get_current_assets():
    upbit = pyupbit.Upbit(access, secret)  # 본인의 API 키로 교체 필요
    krw_balance = float(upbit.get_balance("KRW"))  # 현재 보유한 현금
    btc_balance = float(upbit.get_balance("KRW-BTC"))  # 보유한 BTC 수량
    btc_price = pyupbit.get_current_price("KRW-BTC")  # 현재 BTC 가격
    total_asset = krw_balance + btc_balance * btc_price  # 총 자산 계산
    return krw_balance, btc_balance, btc_price, total_asset

# 수익률 계산 함수 수정
def calculate_profit_rate(df):
    if not df.empty:
        # PyUpbit API에서 현재 자산 정보를 가져옴
        krw_balance, btc_balance, btc_price, latest_total_asset = get_current_assets()
        
        initial_total_asset = df.iloc[0]['total_asset'] + 1000000 # 처음 자산
        initial_investment = initial_total_asset  # 초기 자산
        
        # 수익률 계산
        profit_rate = ((latest_total_asset - initial_investment) / initial_investment) * 100
        return profit_rate, latest_total_asset, initial_investment
    else:
        return None, None, None

# 경과 시간과 연환산 수익률 계산 함수는 기존과 동일

def calculate_annualized_return(df, profit_rate):
    if not df.empty:
        try:
            first_trade_date = pd.to_datetime(df['timestamp'].min())  # pandas를 사용해 자동으로 처리
            last_trade_date = datetime.now()
        except Exception as e:
            st.write(f"날짜 형식 처리 오류: {e}")
            return None, None

        elapsed_time = (last_trade_date - first_trade_date).total_seconds() / 3600  # 경과 시간(시간 단위)
        
        if elapsed_time > 0:
            # 연환산 수익률 = ((1 + 수익률/100) ^ (8760 / 경과 시간)) - 1
            annualized_return = ((1 + profit_rate / 100) ** (8760 / elapsed_time) - 1) * 100  # 1년은 8760시간
            return elapsed_time, annualized_return
        else:
            return elapsed_time, None
    else:
        return None, None
    
# 경과 시간을 일과 시간 단위로 변환하는 함수
def format_elapsed_time(elapsed_hours):
    days = int(elapsed_hours // 24)  # 경과 일 수
    hours = int(elapsed_hours % 24)  # 남은 시간
    return days, hours

# 메인 함수
def main():
    st.title('비트코인 거래 내역 조회')

    # 데이터 로드
    df = load_data()

    # 수익률 및 초기 자산, 현재 자산 계산
    profit_rate, latest_total_asset, initial_investment = calculate_profit_rate(df)
    
    # 경과 시간 및 1년 예상 수익률 계산
    elapsed_time, annualized_return = calculate_annualized_return(df, profit_rate) if profit_rate is not None else (None, None)

    # 수익률과 자산 정보 표시
    if profit_rate is not None:
        st.subheader(f"💹 현재 수익률: **{profit_rate:.2f}%**")
        st.subheader(f"💰 현재 총 자산: **{latest_total_asset:.2f} KRW**")
        st.subheader(f"💼 초기 자산: **{initial_investment:.2f} KRW**")
        
        if elapsed_time is not None:
            days, hours = format_elapsed_time(elapsed_time)
            st.markdown(f"<span style='color:blue;'>🕒 첫 거래일로부터 **{days}일 {hours}시간** 경과</span>", unsafe_allow_html=True)
            if annualized_return is not None:
                st.markdown(f"<span style='color:green;'>📈 1년 예상 수익률: **{annualized_return:.2f}%**</span>", unsafe_allow_html=True)
    else:
        st.header("거래 내역이 없습니다.")

    # 기본 통계
    st.header('기본 통계')
    st.write(f"총 거래 횟수: {len(df)}")
    st.write(f"첫 거래 날짜: {df['timestamp'].min()}")
    st.write(f"마지막 거래 날짜: {df['timestamp'].max()}")

    # 거래 내역 표시
    st.header('거래 내역')
    st.dataframe(df)

    # 거래 결정 분포
    st.header('거래 결정 분포')
    decision_counts = df['decision'].value_counts()
    fig = px.pie(values=decision_counts.values, names=decision_counts.index, title='거래 결정 분포')
    st.plotly_chart(fig)

    # BTC 잔액 변화
    st.header('BTC 잔액 변화')
    fig = px.line(df, x='timestamp', y='btc_balance', title='BTC 잔액')
    st.plotly_chart(fig)

    # KRW 잔액 변화
    st.header('KRW 잔액 변화')
    fig = px.line(df, x='timestamp', y='krw_balance', title='KRW 잔액')
    st.plotly_chart(fig)

    # BTC 가격 변화
    st.header('BTC 가격 변화')
    fig = px.line(df, x='timestamp', y='btc_krw_price', title='BTC 가격 (KRW)')
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
