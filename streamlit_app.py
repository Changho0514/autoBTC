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
    # 첫 자산과 예치금을 고려한 수익률 계산
    if not df.empty:
        initial_total_asset = df.iloc[0]['total_asset']  # 처음 자산
        total_deposit = df['deposit'].sum()  # 총 예치금
        latest_total_asset = df.iloc[-1]['total_asset']  # 현재 자산
        
        # 수익률 계산
        profit_rate = ((latest_total_asset - (initial_total_asset + total_deposit)) / (initial_total_asset + total_deposit)) * 100
        return profit_rate, latest_total_asset
    else:
        return None, None

# 메인 함수
def main():
    st.title('비트코인 거래 내역 조회')

    # 데이터 로드
    df = load_data()

    profit_rate, latest_total_asset = calculate_profit_rate(df)
    if profit_rate is not None:
        st.header(f"현재 수익률: {profit_rate:.2f}%")
        st.header(f"현재 총 자산: {latest_total_asset:.2f} KRW")  # 현재 총 자산 표시
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