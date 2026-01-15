import os
from dotenv import load_dotenv
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pyupbit

# 페이지 설정
st.set_page_config(
    page_title="AutoBTC Trading Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모던 다크 테마 CSS
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    }

    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* 헤더 스타일 */
    .main-header {
        background: linear-gradient(90deg, #f7931a 0%, #ffb347 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: glow 2s ease-in-out infinite alternate;
    }

    @keyframes glow {
        from { filter: drop-shadow(0 0 5px #f7931a); }
        to { filter: drop-shadow(0 0 20px #f7931a); }
    }

    .sub-header {
        color: #8b949e;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* 글래스모피즘 카드 */
    .glass-card {
        background: rgba(22, 27, 34, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(247, 147, 26, 0.15);
    }

    /* 메트릭 카드 */
    .metric-card {
        background: linear-gradient(145deg, rgba(22, 27, 34, 0.9), rgba(13, 17, 23, 0.9));
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #f7931a, #ffb347);
    }

    .metric-card.profit::before {
        background: linear-gradient(90deg, #238636, #3fb950);
    }

    .metric-card.loss::before {
        background: linear-gradient(90deg, #da3633, #f85149);
    }

    .metric-label {
        color: #8b949e;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        color: #f0f6fc;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .metric-value.profit {
        color: #3fb950;
    }

    .metric-value.loss {
        color: #f85149;
    }

    .metric-delta {
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* 거래 카드 */
    .trade-card {
        background: rgba(22, 27, 34, 0.9);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid #8b949e;
        transition: all 0.3s ease;
    }

    .trade-card:hover {
        background: rgba(30, 37, 46, 0.9);
    }

    .trade-card.buy {
        border-left-color: #3fb950;
        box-shadow: -4px 0 20px rgba(63, 185, 80, 0.1);
    }

    .trade-card.sell {
        border-left-color: #f85149;
        box-shadow: -4px 0 20px rgba(248, 81, 73, 0.1);
    }

    .trade-card.hold {
        border-left-color: #58a6ff;
        box-shadow: -4px 0 20px rgba(88, 166, 255, 0.1);
    }

    .trade-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .trade-decision {
        font-size: 0.85rem;
        font-weight: 700;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .trade-decision.buy {
        background: rgba(63, 185, 80, 0.15);
        color: #3fb950;
    }

    .trade-decision.sell {
        background: rgba(248, 81, 73, 0.15);
        color: #f85149;
    }

    .trade-decision.hold {
        background: rgba(88, 166, 255, 0.15);
        color: #58a6ff;
    }

    .trade-time {
        color: #8b949e;
        font-size: 0.85rem;
    }

    .trade-reason {
        color: #c9d1d9;
        font-size: 0.95rem;
        line-height: 1.6;
        padding: 1rem;
        background: rgba(13, 17, 23, 0.5);
        border-radius: 12px;
        margin-top: 0.75rem;
    }

    .trade-stats {
        display: flex;
        gap: 1.5rem;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .trade-stat {
        color: #8b949e;
        font-size: 0.85rem;
    }

    .trade-stat span {
        color: #f0f6fc;
        font-weight: 600;
    }

    /* AI 분석 카드 */
    .ai-analysis-card {
        background: linear-gradient(145deg, rgba(88, 166, 255, 0.1), rgba(22, 27, 34, 0.9));
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(88, 166, 255, 0.2);
    }

    .ai-analysis-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        color: #58a6ff;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .ai-analysis-content {
        color: #c9d1d9;
        font-size: 0.95rem;
        line-height: 1.8;
    }

    /* 섹션 헤더 */
    .section-header {
        color: #f0f6fc;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(247, 147, 26, 0.5), transparent);
    }

    /* 통계 바 */
    .stats-bar {
        display: flex;
        justify-content: space-around;
        background: rgba(22, 27, 34, 0.8);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-item {
        text-align: center;
    }

    .stat-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f0f6fc;
    }

    .stat-label {
        font-size: 0.8rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0d1117;
    }

    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }

    /* Streamlit 기본 요소 오버라이드 */
    .stMetric {
        background: transparent !important;
    }

    .stMetric label {
        color: #8b949e !important;
    }

    .stMetric .metric-value {
        color: #f0f6fc !important;
    }

    div[data-testid="stMetricValue"] {
        color: #f0f6fc;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(22, 27, 34, 0.8);
        border-radius: 12px;
        padding: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #8b949e;
        padding: 0.75rem 1.5rem;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(247, 147, 26, 0.2) !important;
        color: #f7931a !important;
    }

    /* expander 스타일 */
    .streamlit-expanderHeader {
        background: rgba(22, 27, 34, 0.8) !important;
        border-radius: 12px !important;
        color: #f0f6fc !important;
    }

    /* 데이터프레임 스타일 */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* 실시간 표시 */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(63, 185, 80, 0.15);
        color: #3fb950;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .live-dot {
        width: 8px;
        height: 8px;
        background: #3fb950;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }
</style>
""", unsafe_allow_html=True)

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
        initial_total_asset = df.iloc[-1]['total_asset']

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
            pass
    return None, None

# 경과 시간을 일/시간으로 변환
def format_elapsed_time(elapsed_hours):
    days = int(elapsed_hours // 24)
    hours = int(elapsed_hours % 24)
    return days, hours

# 거래 결정에 따른 이모지
def get_decision_emoji(decision):
    return {"buy": "📈", "sell": "📉", "hold": "⏸️"}.get(decision, "❓")

# 숫자 포맷팅
def format_krw(value):
    if value >= 100000000:
        return f"₩{value/100000000:.2f}억"
    elif value >= 10000:
        return f"₩{value/10000:.1f}만"
    else:
        return f"₩{value:,.0f}"

# 메인 함수
def main():
    # 헤더
    st.markdown('<h1 class="main-header">₿ AutoBTC</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Bitcoin Trading Dashboard</p>', unsafe_allow_html=True)

    # 실시간 표시
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f'''
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <span class="live-indicator">
                <span class="live-dot"></span>
                LIVE
            </span>
            <span style="color: #8b949e; margin-left: 1rem; font-size: 0.9rem;">{current_time}</span>
        </div>
        ''', unsafe_allow_html=True)

    # 데이터 로드
    df = load_data()

    if df.empty:
        st.markdown('''
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <h2 style="color: #f7931a; margin-bottom: 1rem;">🚀 대기 중</h2>
            <p style="color: #8b949e;">아직 거래 내역이 없습니다. 트레이딩 봇이 실행되면 데이터가 표시됩니다.</p>
        </div>
        ''', unsafe_allow_html=True)
        return

    # 수익률 계산
    profit_rate, latest_total_asset, initial_investment = calculate_profit_rate(df)
    elapsed_time, annualized_return = calculate_annualized_return(df, profit_rate)
    krw_balance, btc_balance, btc_price, _ = get_current_assets()

    # ========== 핵심 지표 카드 ==========
    st.markdown('<div class="section-header">📊 핵심 지표</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profit_class = "profit" if profit_rate and profit_rate >= 0 else "loss"
        profit_sign = "+" if profit_rate and profit_rate >= 0 else ""
        st.markdown(f'''
        <div class="metric-card {profit_class}">
            <div class="metric-label">현재 수익률</div>
            <div class="metric-value {profit_class}">{profit_sign}{profit_rate:.2f}%</div>
            <div class="metric-delta" style="color: {'#3fb950' if profit_rate >= 0 else '#f85149'}">
                {get_decision_emoji('buy') if profit_rate >= 0 else get_decision_emoji('sell')} 누적 수익률
            </div>
        </div>
        ''', unsafe_allow_html=True) if profit_rate else st.markdown('''
        <div class="metric-card">
            <div class="metric-label">현재 수익률</div>
            <div class="metric-value">계산 중...</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">현재 총 자산</div>
            <div class="metric-value">{format_krw(latest_total_asset)}</div>
            <div class="metric-delta" style="color: #8b949e;">₩{latest_total_asset:,.0f}</div>
        </div>
        ''', unsafe_allow_html=True) if latest_total_asset else st.markdown('''
        <div class="metric-card">
            <div class="metric-label">현재 총 자산</div>
            <div class="metric-value">조회 중...</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">초기 자산</div>
            <div class="metric-value">{format_krw(initial_investment)}</div>
            <div class="metric-delta" style="color: #8b949e;">₩{initial_investment:,.0f}</div>
        </div>
        ''', unsafe_allow_html=True) if initial_investment else st.markdown('''
        <div class="metric-card">
            <div class="metric-label">초기 자산</div>
            <div class="metric-value">-</div>
        </div>
        ''', unsafe_allow_html=True)

    with col4:
        if elapsed_time:
            days, hours = format_elapsed_time(elapsed_time)
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">운영 기간</div>
                <div class="metric-value">{days}일</div>
                <div class="metric-delta" style="color: #8b949e;">{hours}시간 경과</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div class="metric-card">
                <div class="metric-label">운영 기간</div>
                <div class="metric-value">-</div>
            </div>
            ''', unsafe_allow_html=True)

    # 연환산 수익률 배너
    if annualized_return is not None:
        ann_class = "profit" if annualized_return >= 0 else "loss"
        ann_sign = "+" if annualized_return >= 0 else ""
        st.markdown(f'''
        <div class="glass-card" style="text-align: center; margin-top: 1rem; margin-bottom: 2rem;">
            <span style="color: #8b949e; font-size: 0.9rem;">📈 연환산 예상 수익률</span>
            <span style="color: {'#3fb950' if annualized_return >= 0 else '#f85149'}; font-size: 1.5rem; font-weight: 700; margin-left: 1rem;">
                {ann_sign}{annualized_return:.2f}%
            </span>
        </div>
        ''', unsafe_allow_html=True)

    # ========== 보유 현황 ==========
    st.markdown('<div class="section-header">💰 보유 현황</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'''
        <div class="glass-card">
            <div style="color: #8b949e; font-size: 0.85rem; margin-bottom: 0.5rem;">보유 KRW</div>
            <div style="color: #f0f6fc; font-size: 1.4rem; font-weight: 600;">{format_krw(krw_balance)}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="glass-card">
            <div style="color: #8b949e; font-size: 0.85rem; margin-bottom: 0.5rem;">보유 BTC</div>
            <div style="color: #f7931a; font-size: 1.4rem; font-weight: 600;">{btc_balance:.8f} BTC</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''
        <div class="glass-card">
            <div style="color: #8b949e; font-size: 0.85rem; margin-bottom: 0.5rem;">현재 BTC 가격</div>
            <div style="color: #f0f6fc; font-size: 1.4rem; font-weight: 600;">{format_krw(btc_price)}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ========== 탭 구성 ==========
    tab1, tab2, tab3 = st.tabs(["📈 차트", "📋 거래 내역", "🤖 AI 분석"])

    with tab1:
        # 총 자산 변화 그래프
        st.markdown('<div class="section-header" style="margin-top: 1rem;">자산 추이</div>', unsafe_allow_html=True)

        df_sorted = df.sort_values('timestamp')

        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(
            x=df_sorted['timestamp'],
            y=df_sorted['total_asset'],
            mode='lines',
            name='총 자산',
            line=dict(color='#f7931a', width=3),
            fill='tozeroy',
            fillcolor='rgba(247, 147, 26, 0.1)'
        ))

        # 거래 포인트 표시
        buy_df = df_sorted[df_sorted['decision'] == 'buy']
        sell_df = df_sorted[df_sorted['decision'] == 'sell']

        fig_total.add_trace(go.Scatter(
            x=buy_df['timestamp'],
            y=buy_df['total_asset'],
            mode='markers',
            name='매수',
            marker=dict(color='#3fb950', size=10, symbol='triangle-up')
        ))

        fig_total.add_trace(go.Scatter(
            x=sell_df['timestamp'],
            y=sell_df['total_asset'],
            mode='markers',
            name='매도',
            marker=dict(color='#f85149', size=10, symbol='triangle-down')
        ))

        fig_total.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                title='',
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                title='자산 (KRW)',
            ),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=400
        )
        st.plotly_chart(fig_total, use_container_width=True)

        # 2열 차트
        col1, col2 = st.columns(2)

        with col1:
            fig_btc = go.Figure()
            fig_btc.add_trace(go.Scatter(
                x=df_sorted['timestamp'],
                y=df_sorted['btc_balance'],
                mode='lines+markers',
                name='BTC',
                line=dict(color='#f7931a', width=2),
                marker=dict(size=4)
            ))
            fig_btc.update_layout(
                title=dict(text='BTC 보유량', font=dict(size=14, color='#f0f6fc')),
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                margin=dict(l=0, r=0, t=40, b=0),
                height=300
            )
            st.plotly_chart(fig_btc, use_container_width=True)

        with col2:
            fig_krw = go.Figure()
            fig_krw.add_trace(go.Scatter(
                x=df_sorted['timestamp'],
                y=df_sorted['krw_balance'],
                mode='lines+markers',
                name='KRW',
                line=dict(color='#3fb950', width=2),
                marker=dict(size=4)
            ))
            fig_krw.update_layout(
                title=dict(text='KRW 보유량', font=dict(size=14, color='#f0f6fc')),
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                margin=dict(l=0, r=0, t=40, b=0),
                height=300
            )
            st.plotly_chart(fig_krw, use_container_width=True)

        # 거래 통계
        st.markdown('<div class="section-header" style="margin-top: 1.5rem;">거래 통계</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            decision_counts = df['decision'].value_counts()
            colors = {'buy': '#3fb950', 'sell': '#f85149', 'hold': '#58a6ff'}

            fig_pie = go.Figure(data=[go.Pie(
                labels=decision_counts.index,
                values=decision_counts.values,
                hole=.6,
                marker_colors=[colors.get(d, '#8b949e') for d in decision_counts.index]
            )])
            fig_pie.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                margin=dict(l=0, r=0, t=20, b=0),
                height=300,
                annotations=[dict(text='거래<br>분포', x=0.5, y=0.5, font_size=14, font_color='#f0f6fc', showarrow=False)]
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            total_trades = len(df)
            buy_count = len(df[df['decision'] == 'buy'])
            sell_count = len(df[df['decision'] == 'sell'])
            hold_count = len(df[df['decision'] == 'hold'])

            st.markdown(f'''
            <div class="glass-card">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                    <div>
                        <div style="color: #8b949e; font-size: 0.85rem;">총 거래</div>
                        <div style="color: #f0f6fc; font-size: 1.8rem; font-weight: 700;">{total_trades}회</div>
                    </div>
                    <div>
                        <div style="color: #3fb950; font-size: 0.85rem;">매수</div>
                        <div style="color: #3fb950; font-size: 1.8rem; font-weight: 700;">{buy_count}회</div>
                    </div>
                    <div>
                        <div style="color: #f85149; font-size: 0.85rem;">매도</div>
                        <div style="color: #f85149; font-size: 1.8rem; font-weight: 700;">{sell_count}회</div>
                    </div>
                    <div>
                        <div style="color: #58a6ff; font-size: 0.85rem;">홀드</div>
                        <div style="color: #58a6ff; font-size: 1.8rem; font-weight: 700;">{hold_count}회</div>
                    </div>
                </div>
                <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <div style="color: #8b949e; font-size: 0.85rem;">첫 거래</div>
                    <div style="color: #f0f6fc; font-size: 0.95rem;">{df['timestamp'].min()}</div>
                    <div style="color: #8b949e; font-size: 0.85rem; margin-top: 0.75rem;">마지막 거래</div>
                    <div style="color: #f0f6fc; font-size: 0.95rem;">{df['timestamp'].max()}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header" style="margin-top: 1rem;">최근 거래 내역</div>', unsafe_allow_html=True)

        # 필터 옵션
        filter_col1, filter_col2 = st.columns([1, 3])
        with filter_col1:
            filter_decision = st.selectbox(
                "거래 유형",
                ["전체", "매수 (Buy)", "매도 (Sell)", "홀드 (Hold)"],
                label_visibility="collapsed"
            )

        # 필터 적용
        filtered_df = df.copy()
        if filter_decision == "매수 (Buy)":
            filtered_df = df[df['decision'] == 'buy']
        elif filter_decision == "매도 (Sell)":
            filtered_df = df[df['decision'] == 'sell']
        elif filter_decision == "홀드 (Hold)":
            filtered_df = df[df['decision'] == 'hold']

        # 거래 카드 표시
        for idx, row in filtered_df.head(20).iterrows():
            decision = row['decision']
            timestamp = row['timestamp']
            reason = row.get('reason', '정보 없음')
            percentage = row.get('percentage', 0)
            total_asset = row.get('total_asset', 0)
            btc_bal = row.get('btc_balance', 0)
            krw_bal = row.get('krw_balance', 0)

            decision_kr = {"buy": "매수", "sell": "매도", "hold": "홀드"}.get(decision, decision)

            st.markdown(f'''
            <div class="trade-card {decision}">
                <div class="trade-header">
                    <span class="trade-decision {decision}">{get_decision_emoji(decision)} {decision_kr}</span>
                    <span class="trade-time">{timestamp}</span>
                </div>
                <div class="trade-reason">
                    <strong style="color: #f7931a;">💡 거래 근거:</strong><br>
                    {reason}
                </div>
                <div class="trade-stats">
                    <div class="trade-stat">비율: <span>{percentage}%</span></div>
                    <div class="trade-stat">총자산: <span>{format_krw(total_asset)}</span></div>
                    <div class="trade-stat">BTC: <span>{btc_bal:.6f}</span></div>
                    <div class="trade-stat">KRW: <span>{format_krw(krw_bal)}</span></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # 전체 데이터 보기
        with st.expander("📜 전체 거래 내역 (테이블)"):
            display_df = df[['timestamp', 'decision', 'percentage', 'reason', 'total_asset', 'btc_balance', 'krw_balance']].copy()
            display_df.columns = ['시간', '결정', '비율(%)', '거래 근거', '총자산', 'BTC', 'KRW']
            st.dataframe(display_df, use_container_width=True, height=400)

    with tab3:
        st.markdown('<div class="section-header" style="margin-top: 1rem;">AI 시장 분석</div>', unsafe_allow_html=True)

        # 최신 AI 분석
        if 'reflection' in df.columns:
            latest_reflection = df['reflection'].iloc[0] if pd.notna(df['reflection'].iloc[0]) else None

            if latest_reflection:
                st.markdown(f'''
                <div class="ai-analysis-card">
                    <div class="ai-analysis-header">
                        🤖 최신 AI 분석 리포트
                    </div>
                    <div class="ai-analysis-content">
                        {latest_reflection}
                    </div>
                    <div style="margin-top: 1rem; color: #8b949e; font-size: 0.85rem;">
                        분석 시점: {df['timestamp'].iloc[0]}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown('''
                <div class="glass-card" style="text-align: center; padding: 2rem;">
                    <p style="color: #8b949e;">아직 AI 분석 데이터가 없습니다.</p>
                </div>
                ''', unsafe_allow_html=True)

        # 최근 분석 히스토리
        st.markdown('<div class="section-header" style="margin-top: 2rem;">분석 히스토리</div>', unsafe_allow_html=True)

        if 'reflection' in df.columns:
            reflections_df = df[df['reflection'].notna()][['timestamp', 'reflection', 'decision']].head(5)

            for idx, row in reflections_df.iterrows():
                with st.expander(f"📊 {row['timestamp']} - {row['decision'].upper()}"):
                    st.markdown(f'''
                    <div style="color: #c9d1d9; line-height: 1.8;">
                        {row['reflection']}
                    </div>
                    ''', unsafe_allow_html=True)

    # 푸터
    st.markdown('''
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; color: #8b949e; font-size: 0.85rem;">
        <p>AutoBTC Trading Bot • AI-Powered by Gemini</p>
        <p style="font-size: 0.75rem; margin-top: 0.5rem;">⚠️ 투자의 책임은 본인에게 있습니다</p>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
