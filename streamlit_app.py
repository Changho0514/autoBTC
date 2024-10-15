import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

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

# 수익률 계산 함수
def calculate_profit_rate(df):
    # 첫 번째 거래와 마지막 거래의 자산을 비교하여 수익률을 계산
    if not df.empty:
        initial_total_asset = df.iloc[0]['total_asset']
        latest_total_asset = df.iloc[-1]['total_asset']
        profit_rate = ((latest_total_asset - initial_total_asset) / initial_total_asset) * 100
        return profit_rate
    else:
        return None

# 메인 함수
def main():
    st.title('Bitcoin Trades Viewer')

    # 데이터 로드
    df = load_data()

    profit_rate = calculate_profit_rate(df)
    if profit_rate is not None:
        st.header(f"Current Profit Rate: {profit_rate:.2f}%")
    else:
        st.header("No trades Yet.")
    # 기본 통계
    st.header('Basic Statistics')
    st.write(f"Total number of trades: {len(df)}")
    st.write(f"First trade date: {df['timestamp'].min()}")
    st.write(f"Last trade date: {df['timestamp'].max()}")

    # 거래 내역 표시
    st.header('Trade History')
    st.dataframe(df)

    # 거래 결정 분포
    st.header('Trade Decision Distribution')
    decision_counts = df['decision'].value_counts()
    fig = px.pie(values=decision_counts.values, names=decision_counts.index, title='Trade Decisions')
    st.plotly_chart(fig)

    # BTC 잔액 변화
    st.header('BTC Balance Over Time')
    fig = px.line(df, x='timestamp', y='btc_balance', title='BTC Balance')
    st.plotly_chart(fig)

    # KRW 잔액 변화
    st.header('KRW Balance Over Time')
    fig = px.line(df, x='timestamp', y='krw_balance', title='KRW Balance')
    st.plotly_chart(fig)

    # BTC 가격 변화
    st.header('BTC Price Over Time')
    fig = px.line(df, x='timestamp', y='btc_krw_price', title='BTC Price (KRW)')
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()