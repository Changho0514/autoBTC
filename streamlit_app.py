import os
from dotenv import load_dotenv
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pyupbit

# 페이지 설정
st.set_page_config(
    page_title="AutoBTC 트레이딩 대시보드",
    page_icon="₿",
    layout="wide"
)

load_dotenv()
access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")

# 데이터베이스 연결 함수
def get_connection():
    return sqlite3.connect('trading_data.db')

# 데이터 로드 함수
def load_data():
    conn = get_connection()
    query = "SELECT * FROM trades ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# PyUpbit API를 이용한 현재 잔고 및 자산 조회 함수
def get_current_assets():
    try:
        upbit = pyupbit.Upbit(access, secret)
        krw_balance = float(upbit.get_balance("KRW") or 0)
        btc_balance = float(upbit.get_balance("KRW-BTC") or 0)
        btc_price = pyupbit.get_current_price("KRW-BTC") or 0
        total_asset = krw_balance + btc_balance * btc_price
        return krw_balance, btc_balance, btc_price, total_asset
    except Exception as e:
        st.error(f"자산 조회 오류: {e}")
        return 0, 0, 0, 0

# 수익률 계산 함수
def calculate_profit_rate(df):
    if not df.empty:
        krw_balance, btc_balance, btc_price, latest_total_asset = get_current_assets()
        initial_total_asset = df.iloc[-1]['total_asset']  # 첫 거래 시 자산

        if initial_total_asset > 0:
            profit_rate = ((latest_total_asset - initial_total_asset) / initial_total_asset) * 100
            return profit_rate, latest_total_asset, initial_total_asset
    return None, None, None

# 연환산 수익률 계산 함수
def calculate_annualized_return(df, profit_rate):
    if not df.empty and profit_rate is not None:
        try:
            first_trade_date = pd.to_datetime(df['timestamp'].min())
            last_trade_date = datetime.now()
            elapsed_time = (last_trade_date - first_trade_date).total_seconds() / 3600

            if elapsed_time > 0:
                annualized_return = ((1 + profit_rate / 100) ** (8760 / elapsed_time) - 1) * 100
                return elapsed_time, annualized_return
        except Exception as e:
            st.error(f"날짜 처리 오류: {e}")
    return None, None

# 경과 시간을 일/시간으로 변환
def format_elapsed_time(elapsed_hours):
    days = int(elapsed_hours // 24)
    hours = int(elapsed_hours % 24)
    return days, hours

# 메인 함수
def main():
    # 헤더
    st.title("₿ AutoBTC 트레이딩 대시보드")
    st.markdown("---")

    # 데이터 로드
    df = load_data()

    if df.empty:
        st.warning("아직 거래 내역이 없습니다. 트레이딩 봇이 실행되면 데이터가 표시됩니다.")
        return

    # 수익률 계산
    profit_rate, latest_total_asset, initial_investment = calculate_profit_rate(df)
    elapsed_time, annualized_return = calculate_annualized_return(df, profit_rate)

    # ========== 핵심 지표 카드 ==========
    st.header("📊 핵심 지표")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if profit_rate is not None:
            color = "green" if profit_rate >= 0 else "red"
            st.metric(
                label="현재 수익률",
                value=f"{profit_rate:.2f}%",
                delta=f"{'📈' if profit_rate >= 0 else '📉'}"
            )
        else:
            st.metric(label="현재 수익률", value="계산 중...")

    with col2:
        if latest_total_asset:
            st.metric(
                label="현재 총 자산",
                value=f"₩{latest_total_asset:,.0f}"
            )
        else:
            st.metric(label="현재 총 자산", value="조회 중...")

    with col3:
        if initial_investment:
            st.metric(
                label="초기 자산",
                value=f"₩{initial_investment:,.0f}"
            )
        else:
            st.metric(label="초기 자산", value="-")

    with col4:
        if elapsed_time:
            days, hours = format_elapsed_time(elapsed_time)
            st.metric(
                label="운영 기간",
                value=f"{days}일 {hours}시간"
            )
        else:
            st.metric(label="운영 기간", value="-")

    # 연환산 수익률
    if annualized_return is not None:
        st.info(f"📈 **연환산 예상 수익률: {annualized_return:.2f}%**")

    st.markdown("---")

    # ========== 차트 섹션 ==========
    st.header("📈 자산 변화 추이")

    # 총 자산 변화 그래프
    df_sorted = df.sort_values('timestamp')
    fig_total = go.Figure()
    fig_total.add_trace(go.Scatter(
        x=df_sorted['timestamp'],
        y=df_sorted['total_asset'],
        mode='lines+markers',
        name='총 자산',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    fig_total.update_layout(
        title='총 자산 변화',
        xaxis_title='시간',
        yaxis_title='자산 (KRW)',
        hovermode='x unified'
    )
    st.plotly_chart(fig_total, use_container_width=True)

    # 2열 차트
    col1, col2 = st.columns(2)

    with col1:
        # BTC 잔액 변화
        fig_btc = px.line(df_sorted, x='timestamp', y='btc_balance',
                         title='BTC 보유량 변화',
                         labels={'timestamp': '시간', 'btc_balance': 'BTC'})
        fig_btc.update_traces(line_color='#ff7f0e')
        st.plotly_chart(fig_btc, use_container_width=True)

    with col2:
        # KRW 잔액 변화
        fig_krw = px.line(df_sorted, x='timestamp', y='krw_balance',
                         title='KRW 보유량 변화',
                         labels={'timestamp': '시간', 'krw_balance': 'KRW'})
        fig_krw.update_traces(line_color='#2ca02c')
        st.plotly_chart(fig_krw, use_container_width=True)

    st.markdown("---")

    # ========== 거래 통계 ==========
    st.header("📋 거래 통계")

    col1, col2 = st.columns(2)

    with col1:
        # 거래 결정 분포
        decision_counts = df['decision'].value_counts()
        fig_pie = px.pie(
            values=decision_counts.values,
            names=decision_counts.index,
            title='거래 결정 분포',
            color_discrete_map={'buy': '#2ca02c', 'sell': '#d62728', 'hold': '#1f77b4'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # 기본 통계
        st.subheader("거래 요약")
        st.write(f"**총 거래 횟수:** {len(df)}회")
        st.write(f"**매수 횟수:** {len(df[df['decision'] == 'buy'])}회")
        st.write(f"**매도 횟수:** {len(df[df['decision'] == 'sell'])}회")
        st.write(f"**홀드 횟수:** {len(df[df['decision'] == 'hold'])}회")
        st.write(f"**첫 거래:** {df['timestamp'].min()}")
        st.write(f"**마지막 거래:** {df['timestamp'].max()}")

    st.markdown("---")

    # ========== 최근 거래 내역 ==========
    st.header("🕐 최근 거래 내역")

    # 최근 10개 거래
    recent_df = df.head(10)[['timestamp', 'decision', 'percentage', 'reason', 'total_asset']]
    recent_df.columns = ['시간', '결정', '비율(%)', '이유', '총자산']
    st.dataframe(recent_df, use_container_width=True)

    # 전체 데이터 보기 (접이식)
    with st.expander("📜 전체 거래 내역 보기"):
        st.dataframe(df, use_container_width=True)

    # ========== AI 분석 (Reflection) ==========
    if 'reflection' in df.columns and df['reflection'].iloc[0]:
        st.markdown("---")
        st.header("🤖 AI 최근 분석")
        with st.expander("AI의 최근 시장 분석 보기"):
            st.write(df['reflection'].iloc[0])

if __name__ == "__main__":
    main()
