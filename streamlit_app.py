import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

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

        # 초기 자산 = 처음 자산 + 총 예치금
        initial_investment = initial_total_asset + total_deposit
        
        # 수익률 계산
        profit_rate = ((latest_total_asset - initial_investment) / initial_investment) * 100
        return profit_rate, latest_total_asset, initial_investment
    else:
        return None, None, None

# 경과 시간과 연환산 수익률 계산 함수
def calculate_annualized_return(df, profit_rate):
    if not df.empty:
        first_trade_date = datetime.strptime(df['timestamp'].min(), "%Y-%m-%d %H:%M:%S")  # 첫 거래일
        last_trade_date = datetime.strptime(df['timestamp'].max(), "%Y-%m-%d %H:%M:%S")   # 마지막 거래일
        elapsed_time = (last_trade_date - first_trade_date).total_seconds() / 3600  # 경과 시간(시간 단위)
        
        if elapsed_time > 0:
            # 연환산 수익률 = ((1 + 수익률/100) ^ (8760 / 경과 시간)) - 1
            annualized_return = ((1 + profit_rate / 100) ** (8760 / elapsed_time) - 1) * 100  # 1년은 8760시간
            return elapsed_time, annualized_return
        else:
            return elapsed_time, None
    else:
        return None, None

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
        st.header(f"현재 수익률: {profit_rate:.2f}%")
        st.header(f"현재 총 자산: {latest_total_asset:.2f} KRW")
        st.header(f"초기 자산: {initial_investment:.2f} KRW")
        
        if elapsed_time is not None:
            st.write(f"첫 거래일로부터 {elapsed_time:.2f} 시간 경과")
            if annualized_return is not None:
                st.write(f"1년 예상 수익률: {annualized_return:.2f}%")
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
