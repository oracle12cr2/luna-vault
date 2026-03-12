"""
ETF 백테스트 대시보드
Streamlit 기반 웹 대시보드
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import yaml
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="ETF 백테스트 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #1f77b4;
}
.positive {
    color: #ff6b6b;
    font-weight: bold;
}
.negative {
    color: #4dabf7;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_config():
    """설정 파일 로드"""
    try:
        with open('/root/.openclaw/workspace/etf-backtest/config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"설정 파일 로드 오류: {e}")
        return None

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_data(symbols, start_date, end_date):
    """주식 데이터 다운로드"""
    try:
        with st.spinner('데이터 다운로드 중...'):
            data = {}
            for name, symbol in symbols.items():
                try:
                    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
                    # MultiIndex 컬럼 평탄화
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    if not df.empty:
                        data[name] = df
                        st.sidebar.success(f"✓ {name}")
                    else:
                        st.sidebar.warning(f"⚠ {name}: 데이터 없음")
                except Exception as e:
                    st.sidebar.error(f"✗ {name}: {str(e)}")
                    continue
            
            # 벤치마크 (코스피200)
            kospi = yf.download("^KS200", start=start_date, end=end_date, progress=False)
            if isinstance(kospi.columns, pd.MultiIndex):
                kospi.columns = kospi.columns.get_level_values(0)
            if not kospi.empty:
                data['코스피200'] = kospi
                
            return data
    except Exception as e:
        st.error(f"데이터 다운로드 오류: {e}")
        return {}

def calculate_moving_average_strategy(data, short_period=20, long_period=60):
    """이동평균 크로스 전략"""
    df = data.copy()
    df['MA_Short'] = df['Close'].rolling(window=short_period).mean()
    df['MA_Long'] = df['Close'].rolling(window=long_period).mean()
    
    # 신호 생성
    df['Signal'] = 0
    df.loc[df['MA_Short'] > df['MA_Long'], 'Signal'] = 1
    df.loc[df['MA_Short'] < df['MA_Long'], 'Signal'] = 0
    
    # 포지션 변화점
    df['Position'] = df['Signal'].diff()
    
    return df

def calculate_rsi_strategy(data, period=14, oversold=30, overbought=70):
    """RSI 전략"""
    df = data.copy()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 신호 생성
    df['Signal'] = 0
    df.loc[df['RSI'] < oversold, 'Signal'] = 1  # 매수
    df.loc[df['RSI'] > overbought, 'Signal'] = 0  # 매도
    
    return df

def calculate_dual_momentum_strategy(etf_data, benchmark_data, lookback=252):
    """듀얼 모멘텀 전략"""
    combined_data = {}
    
    for name, data in etf_data.items():
        if name == '코스피200':
            continue
            
        df = data.copy()
        df['ETF_Return'] = df['Close'].pct_change(periods=lookback)
        
        # 벤치마크와 비교 (코스피200)
        if '코스피200' in etf_data:
            benchmark = etf_data['코스피200']['Close'].reindex(df.index).pct_change(periods=lookback)
            df['Benchmark_Return'] = benchmark
            df['Relative_Momentum'] = df['ETF_Return'] - df['Benchmark_Return']
            
            # 절대 모멘텀과 상대 모멘텀 모두 양수일 때만 매수
            df['Signal'] = 0
            df.loc[(df['ETF_Return'] > 0) & (df['Relative_Momentum'] > 0), 'Signal'] = 1
        else:
            # 절대 모멘텀만 사용
            df['Signal'] = 0
            df.loc[df['ETF_Return'] > 0, 'Signal'] = 1
            
        combined_data[name] = df
        
    return combined_data

def calculate_grid_strategy(data, grid_pct=5, sell_pct=10, buy_pct=10, ma_period=20, initial_cash=10000000):
    """분할매매 전략 (오르면 일부 매도, 내리면 분할 매수)
    
    - 이동평균 대비 grid_pct% 이상 오르면 보유량의 sell_pct% 매도 (수익실현)
    - 이동평균 대비 grid_pct% 이상 내리면 현금의 buy_pct% 매수 (분할매수)
    - 자산을 조금씩 늘려가는 안정적 전략
    """
    df = data.copy()
    df['MA'] = df['Close'].rolling(window=ma_period).mean()
    df['Deviation'] = (df['Close'] - df['MA']) / df['MA'] * 100  # 이평선 대비 이격도(%)
    
    cash = initial_cash
    holdings = 0  # 보유 수량
    
    # 초기 매수 (50% 투자)
    initial_buy_amount = initial_cash * 0.5
    
    portfolio_values = []
    cash_values = []
    stock_values = []
    signals_list = []
    trade_log = []
    
    # 매수후보유 벤치마크
    bnh_shares = 0
    bnh_initialized = False
    bnh_values = []
    
    for i in range(len(df)):
        price = float(df['Close'].iloc[i])
        date = df.index[i]
        
        if pd.isna(df['MA'].iloc[i]):
            portfolio_values.append(cash + holdings * price)
            cash_values.append(cash)
            stock_values.append(holdings * price)
            signals_list.append(0)
            # 매수후보유: 아직 이평선 미형성
            bnh_values.append(initial_cash)
            continue
        
        # 매수후보유 벤치마크 초기화 (이평선 형성 시점에 전액 매수)
        if not bnh_initialized:
            bnh_shares = int(initial_cash / price)
            bnh_initialized = True
        bnh_values.append(bnh_shares * price + (initial_cash - bnh_shares * price))
        
        deviation = float(df['Deviation'].iloc[i])
        
        # 첫 매수 (이평선 형성 후)
        if holdings == 0 and cash > 0:
            buy_qty = int(initial_buy_amount / price)
            if buy_qty > 0:
                cost = buy_qty * price
                cash -= cost
                holdings += buy_qty
                trade_log.append({'date': date, 'action': '초기매수', 'price': price, 'qty': buy_qty, 'amount': cost, 'cash': cash, 'holdings': holdings})
        
        # 오름세: 이평선 대비 grid_pct% 이상 → 보유량의 sell_pct% 매도 (수익실현)
        elif deviation >= grid_pct and holdings > 0:
            sell_qty = max(1, int(holdings * sell_pct / 100))
            if sell_qty > 0:
                revenue = sell_qty * price * (1 - 0.0015)  # 수수료 차감
                cash += revenue
                holdings -= sell_qty
                trade_log.append({'date': date, 'action': '수익실현', 'price': price, 'qty': -sell_qty, 'amount': revenue, 'cash': cash, 'holdings': holdings})
        
        # 내림세: 이평선 대비 -grid_pct% 이하 → 현금의 buy_pct% 분할매수
        elif deviation <= -grid_pct and cash > 0:
            buy_amount = cash * buy_pct / 100
            buy_qty = int(buy_amount / price)
            if buy_qty > 0:
                cost = buy_qty * price * (1 + 0.0015)  # 수수료 포함
                if cost <= cash:
                    cash -= cost
                    holdings += buy_qty
                    trade_log.append({'date': date, 'action': '분할매수', 'price': price, 'qty': buy_qty, 'amount': cost, 'cash': cash, 'holdings': holdings})
        
        portfolio_value = cash + holdings * price
        portfolio_values.append(portfolio_value)
        cash_values.append(cash)
        stock_values.append(holdings * price)
        signals_list.append(1 if holdings > 0 else 0)
    
    df['Portfolio_Value'] = portfolio_values
    df['Cash_Value'] = cash_values
    df['Stock_Value'] = stock_values
    df['BnH_Value'] = bnh_values
    df['Signal'] = signals_list
    
    return df, trade_log, portfolio_values

def calculate_grid_metrics(portfolio_values, initial_cash, index, bnh_values=None):
    """분할매매 전략 지표 계산"""
    pv = pd.Series(portfolio_values, index=index)
    
    # 수익률
    total_return = float((pv.iloc[-1] / initial_cash) - 1)
    years = len(pv) / 252
    annual_return = float((1 + total_return) ** (1/years) - 1) if years > 0 else 0
    
    # 일별 수익률
    daily_returns = pv.pct_change().fillna(0)
    
    # 샤프비율
    portfolio_vol = float(daily_returns.std() * np.sqrt(252))
    sharpe_ratio = annual_return / portfolio_vol if portfolio_vol > 0 else 0
    
    # 드로다운
    peak = pv.cummax()
    drawdown = (pv - peak) / peak
    max_drawdown = float(drawdown.min())
    
    # 누적 수익률 (정규화)
    cumulative_returns = pv / initial_cash
    
    # 매수후보유 벤치마크
    if bnh_values is not None:
        bnh = pd.Series(bnh_values, index=index)
        benchmark_cumulative = bnh / initial_cash
        benchmark_total = float((bnh.iloc[-1] / initial_cash) - 1)
        benchmark_annual = float((1 + benchmark_total) ** (1/years) - 1) if years > 0 else 0
        # 벤치마크 드로다운
        bnh_peak = bnh.cummax()
        bnh_drawdown = (bnh - bnh_peak) / bnh_peak
    else:
        benchmark_cumulative = cumulative_returns.copy()
        benchmark_total = total_return
        benchmark_annual = annual_return
        bnh_drawdown = drawdown.copy()
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': float((daily_returns > 0).sum() / len(daily_returns) * 100),
        'cumulative_returns': cumulative_returns,
        'portfolio_returns': daily_returns,
        'drawdown': drawdown,
        'benchmark_total': benchmark_total,
        'benchmark_annual': benchmark_annual,
        'benchmark_cumulative': benchmark_cumulative,
        'benchmark_drawdown': bnh_drawdown,
        'final_value': float(pv.iloc[-1]),
        'profit': float(pv.iloc[-1] - initial_cash),
        'excess_return': total_return - benchmark_total if bnh_values is not None else 0,
    }

def calculate_backtest_metrics(price_data, signals, initial_cash=10000000, commission=0.0015):
    """백테스트 지표 계산"""
    if len(price_data) == 0 or len(signals) == 0:
        return {}
    
    # 신호에 따른 수익률 계산
    returns = price_data.pct_change().fillna(0)
    shifted_signals = signals.shift(1).fillna(0)
    portfolio_returns = shifted_signals * returns  # 전날 신호로 오늘 수익률
    portfolio_returns = portfolio_returns.fillna(0)
    
    # 다중 ETF인 경우 동일 가중 평균으로 합산
    if isinstance(portfolio_returns, pd.DataFrame):
        portfolio_returns = portfolio_returns.mean(axis=1)
    if isinstance(returns, pd.DataFrame):
        returns_avg = returns.mean(axis=1)
    else:
        returns_avg = returns
    
    trade_signals = shifted_signals.diff().abs().fillna(0)
    if isinstance(trade_signals, pd.DataFrame):
        trade_signals = trade_signals.mean(axis=1)
    
    # 수수료 적용
    transaction_costs = trade_signals * commission
    portfolio_returns = portfolio_returns - transaction_costs
    
    # 누적 수익률
    cumulative_returns = (1 + portfolio_returns).cumprod()
    
    # 벤치마크 (매수후보유)
    benchmark_returns = returns_avg
    benchmark_cumulative = (1 + benchmark_returns).cumprod()
    
    # 성과 지표 계산
    total_return = float(cumulative_returns.iloc[-1] - 1)
    benchmark_total = float(benchmark_cumulative.iloc[-1] - 1)
    
    # 연환산 수익률
    years = len(portfolio_returns) / 252  # 영업일 기준
    annual_return = float((1 + total_return) ** (1/years) - 1) if years > 0 else 0
    benchmark_annual = float((1 + benchmark_total) ** (1/years) - 1) if years > 0 else 0
    
    # 샤프 비율 (단순화)
    portfolio_vol = float(portfolio_returns.std() * np.sqrt(252))
    sharpe_ratio = annual_return / portfolio_vol if portfolio_vol > 0 else 0
    
    # 최대 드로다운
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = float(drawdown.min())
    
    # 승률
    winning_trades = int((portfolio_returns > 0).sum())
    total_trades = int((trade_signals > 0).sum())
    win_rate = winning_trades / len(portfolio_returns) * 100 if len(portfolio_returns) > 0 else 0
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'cumulative_returns': cumulative_returns,
        'portfolio_returns': portfolio_returns,
        'drawdown': drawdown,
        'benchmark_total': benchmark_total,
        'benchmark_annual': benchmark_annual,
        'benchmark_cumulative': benchmark_cumulative
    }

def create_portfolio_chart(metrics):
    """포트폴리오 성과 차트"""
    fig = go.Figure()
    
    # 포트폴리오 수익률
    fig.add_trace(go.Scatter(
        x=metrics['cumulative_returns'].index,
        y=(metrics['cumulative_returns'] - 1) * 100,
        name='포트폴리오',
        line=dict(color='blue', width=2)
    ))
    
    # 벤치마크
    fig.add_trace(go.Scatter(
        x=metrics['benchmark_cumulative'].index,
        y=(metrics['benchmark_cumulative'] - 1) * 100,
        name='벤치마크',
        line=dict(color='gray', width=1, dash='dash')
    ))
    
    fig.update_layout(
        title='포트폴리오 수익률 곡선',
        xaxis_title='날짜',
        yaxis_title='누적 수익률 (%)',
        hovermode='x unified'
    )
    
    return fig

def create_drawdown_chart(metrics):
    """드로다운 차트"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=metrics['drawdown'].index,
        y=metrics['drawdown'] * 100,
        fill='tonexty',
        name='드로다운',
        line=dict(color='red')
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title='드로다운 분석',
        xaxis_title='날짜',
        yaxis_title='드로다운 (%)',
        hovermode='x unified'
    )
    
    return fig

def create_grid_price_chart(grid_data, trade_log, etf_name):
    """분할매매 가격 차트 + 매매 마커 + 이동평균"""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.08,
                        row_heights=[0.7, 0.3],
                        subplot_titles=[f'{etf_name} 가격 & 매매 시점', '이격도 (%)'])
    
    # 가격 라인
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['Close'],
        name='종가', line=dict(color='#1f77b4', width=1.5)
    ), row=1, col=1)
    
    # 이동평균
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['MA'],
        name='이동평균', line=dict(color='orange', width=1, dash='dash')
    ), row=1, col=1)
    
    # 매수 마커
    buys = [t for t in trade_log if t['qty'] > 0]
    if buys:
        fig.add_trace(go.Scatter(
            x=[t['date'] for t in buys],
            y=[t['price'] for t in buys],
            mode='markers',
            name='매수',
            marker=dict(symbol='triangle-up', size=12, color='#2ca02c', line=dict(width=1, color='darkgreen')),
            text=[f"{t['action']}<br>{t['qty']}주 @ {t['price']:,.0f}" for t in buys],
            hovertemplate='%{text}<extra></extra>'
        ), row=1, col=1)
    
    # 매도 마커
    sells = [t for t in trade_log if t['qty'] < 0]
    if sells:
        fig.add_trace(go.Scatter(
            x=[t['date'] for t in sells],
            y=[t['price'] for t in sells],
            mode='markers',
            name='매도',
            marker=dict(symbol='triangle-down', size=12, color='#d62728', line=dict(width=1, color='darkred')),
            text=[f"{t['action']}<br>{abs(t['qty'])}주 @ {t['price']:,.0f}" for t in sells],
            hovertemplate='%{text}<extra></extra>'
        ), row=1, col=1)
    
    # 이격도 차트
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['Deviation'],
        name='이격도', line=dict(color='purple', width=1),
        fill='tozeroy', fillcolor='rgba(128,0,128,0.1)'
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    fig.update_layout(height=600, hovermode='x unified', legend=dict(orientation='h', y=1.05))
    return fig


def create_grid_portfolio_chart(grid_data, initial_cash):
    """분할매매 포트폴리오 가치 vs 매수후보유 비교"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['Portfolio_Value'],
        name='분할매매 포트폴리오',
        line=dict(color='#2ca02c', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['BnH_Value'],
        name='매수후보유 (벤치마크)',
        line=dict(color='gray', width=1.5, dash='dash')
    ))
    
    fig.add_hline(y=initial_cash, line_dash="dot", line_color="red",
                  annotation_text=f"초기 투자금 {initial_cash/10000:,.0f}만원")
    
    fig.update_layout(
        title='포트폴리오 가치 비교',
        xaxis_title='날짜', yaxis_title='평가금액 (원)',
        hovermode='x unified', height=400,
        yaxis_tickformat=',',
        legend=dict(orientation='h', y=1.05)
    )
    return fig


def create_grid_allocation_chart(grid_data):
    """현금 vs 주식 자산 구성 변화 (영역 차트)"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['Stock_Value'],
        name='주식 평가액', stackgroup='one',
        line=dict(width=0), fillcolor='rgba(31,119,180,0.6)'
    ))
    
    fig.add_trace(go.Scatter(
        x=grid_data.index, y=grid_data['Cash_Value'],
        name='현금', stackgroup='one',
        line=dict(width=0), fillcolor='rgba(44,160,44,0.4)'
    ))
    
    fig.update_layout(
        title='자산 구성 변화 (현금 vs 주식)',
        xaxis_title='날짜', yaxis_title='금액 (원)',
        hovermode='x unified', height=400,
        yaxis_tickformat=',',
        legend=dict(orientation='h', y=1.05)
    )
    return fig


def create_grid_drawdown_chart(metrics):
    """분할매매 vs 매수후보유 드로다운 비교"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=metrics['drawdown'].index, y=metrics['drawdown'] * 100,
        name='분할매매 드로다운',
        fill='tozeroy', fillcolor='rgba(214,39,40,0.2)',
        line=dict(color='#d62728', width=1.5)
    ))
    
    if 'benchmark_drawdown' in metrics:
        fig.add_trace(go.Scatter(
            x=metrics['benchmark_drawdown'].index, y=metrics['benchmark_drawdown'] * 100,
            name='매수후보유 드로다운',
            line=dict(color='gray', width=1, dash='dash')
        ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title='드로다운 비교 (분할매매 vs 매수후보유)',
        xaxis_title='날짜', yaxis_title='드로다운 (%)',
        hovermode='x unified', height=350,
        legend=dict(orientation='h', y=1.05)
    )
    return fig


def create_price_charts(data_dict, selected_etfs):
    """ETF 가격 차트"""
    fig = make_subplots(
        rows=len(selected_etfs), 
        cols=1,
        subplot_titles=[f"{etf} 가격 추이" for etf in selected_etfs],
        vertical_spacing=0.1
    )
    
    colors = px.colors.qualitative.Set1
    
    for i, etf in enumerate(selected_etfs):
        if etf in data_dict:
            data = data_dict[etf]
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    name=etf,
                    line=dict(color=colors[i % len(colors)])
                ),
                row=i+1, col=1
            )
    
    fig.update_layout(
        height=300 * len(selected_etfs),
        title_text="선택된 ETF 가격 차트"
    )
    
    return fig

# 메인 앱
def main():
    st.title("📈 ETF 백테스트 대시보드")
    st.markdown("---")
    
    # 설정 로드
    config = load_config()
    if not config:
        st.stop()
    
    # 사이드바 설정
    st.sidebar.header("🔧 백테스트 설정")
    
    # ETF 선택
    st.sidebar.subheader("📊 ETF 종목 선택")
    etf_options = list(config['data']['etfs'].keys())
    etf_names = {
        'ace200': 'ACE 200 ETF',
        'kosdaq150': 'KOSDAQ150 ETF', 
        'tiger_it': 'TIGER IT ETF',
        'kodex_dividend': 'KODEX 고배당',
        'kodex_battery': 'KODEX 2차전지',
        'tiger_semi': 'TIGER 반도체',
        'kodex_leverage': 'KODEX 레버리지',
        'tiger_bank': 'TIGER 은행',
        'kodex_gold': 'KODEX 골드',
        'kodex_bond': 'KODEX 국고채10년'
    }
    
    selected_etfs = st.sidebar.multiselect(
        "ETF 선택",
        options=etf_options,
        default=etf_options,  # 전체 선택 (config에 있는 종목만)
        format_func=lambda x: etf_names.get(x, x)
    )
    
    # 전략 선택
    st.sidebar.subheader("🎯 전략 선택")
    strategy = st.sidebar.selectbox(
        "백테스트 전략",
        ["분할매매 (추천)", "이동평균 크로스", "RSI", "듀얼 모멘텀", "매수후보유"]
    )
    
    # 기간 설정
    st.sidebar.subheader("📅 백테스트 기간")
    start_date = st.sidebar.date_input(
        "시작일",
        value=datetime.strptime(config['data']['start_date'], '%Y-%m-%d'),
        min_value=datetime(2010, 1, 1),
        max_value=datetime.now()
    )
    
    end_date = st.sidebar.date_input(
        "종료일", 
        value=datetime.strptime(config['data']['end_date'], '%Y-%m-%d'),
        min_value=start_date,
        max_value=datetime.now()
    )
    
    # 전략 파라미터
    st.sidebar.subheader("⚙️ 전략 파라미터")
    if strategy == "분할매매 (추천)":
        grid_ma = st.sidebar.slider("이동평균 기간", 5, 60, 20)
        grid_pct = st.sidebar.slider("매매 기준 이격도 (%)", 1, 15, 5)
        grid_sell_pct = st.sidebar.slider("수익실현 비율 (보유량의 %)", 5, 30, 10)
        grid_buy_pct = st.sidebar.slider("분할매수 비율 (현금의 %)", 5, 30, 10)
    elif strategy == "이동평균 크로스":
        short_ma = st.sidebar.slider("단기 이동평균", 5, 50, 20)
        long_ma = st.sidebar.slider("장기 이동평균", 20, 100, 60)
    elif strategy == "RSI":
        rsi_period = st.sidebar.slider("RSI 기간", 5, 30, 14)
        oversold = st.sidebar.slider("과매도 임계값", 20, 40, 30)
        overbought = st.sidebar.slider("과매수 임계값", 60, 80, 70)
    elif strategy == "듀얼 모멘텀":
        momentum_period = st.sidebar.slider("모멘텀 기간 (일)", 60, 365, 252)
    
    # 초기 투자금
    initial_cash = st.sidebar.number_input(
        "초기 투자금 (원)",
        min_value=1000000,
        max_value=1000000000,
        value=config['backtest']['initial_cash'],
        step=1000000,
        format="%d"
    )
    
    # 실행 버튼
    if st.sidebar.button("🚀 백테스트 실행", type="primary"):
        if not selected_etfs:
            st.error("최소 하나의 ETF를 선택해주세요.")
            return
            
        # 데이터 로드
        etf_symbols = {etf: config['data']['etfs'][etf] for etf in selected_etfs}
        data_dict = get_data(etf_symbols, start_date, end_date)
        
        if not data_dict:
            st.error("데이터를 불러올 수 없습니다.")
            return
            
        st.success("✅ 데이터 로드 완료!")
        
        # 백테스트 실행
        results = {}
        
        for etf_name, etf_data in data_dict.items():
            if etf_name == '코스피200':
                continue
                
            # 전략별 신호 생성
            if strategy == "분할매매 (추천)":
                grid_data, trade_log, pv = calculate_grid_strategy(
                    etf_data, grid_pct, grid_sell_pct, grid_buy_pct, grid_ma, initial_cash
                )
                bnh_values = grid_data['BnH_Value'].tolist()
                metrics = calculate_grid_metrics(pv, initial_cash, etf_data.index, bnh_values)
                metrics['trade_log'] = trade_log
                metrics['grid_data'] = grid_data
                results[etf_name] = metrics
                continue
            elif strategy == "이동평균 크로스":
                strategy_data = calculate_moving_average_strategy(etf_data, short_ma, long_ma)
                signals = strategy_data['Signal']
            elif strategy == "RSI":
                strategy_data = calculate_rsi_strategy(etf_data, rsi_period, oversold, overbought)
                signals = strategy_data['Signal']
            elif strategy == "듀얼 모멘텀":
                momentum_results = calculate_dual_momentum_strategy(
                    {etf_name: etf_data}, data_dict, momentum_period
                )
                if etf_name in momentum_results:
                    signals = momentum_results[etf_name]['Signal']
                else:
                    signals = pd.Series(1, index=etf_data.index)
            else:  # 매수후보유
                signals = pd.Series(1, index=etf_data.index)
            
            # 백테스트 지표 계산
            metrics = calculate_backtest_metrics(
                etf_data['Close'], signals, initial_cash, config['backtest']['commission']
            )
            results[etf_name] = metrics
        
        # 결과 표시
        st.markdown("## 📊 백테스트 결과")
        
        if not results:
            st.warning("결과가 없습니다.")
            return
        
        # ========== 분할매매 전용 UI ==========
        if strategy == "분할매매 (추천)":
            for etf_name, metrics in results.items():
                st.markdown(f"### 🏷️ {etf_names.get(etf_name, etf_name)}")
                
                # 핵심 지표 카드 (6개)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1:
                    st.metric("최종 평가금",
                              f"{metrics['final_value']/10000:,.0f}만원")
                with c2:
                    color = "🔴" if metrics['profit'] < 0 else "🟢"
                    st.metric("수익금",
                              f"{color} {metrics['profit']/10000:,.0f}만원")
                with c3:
                    st.metric("총 수익률",
                              f"{metrics['total_return']*100:.1f}%",
                              delta=f"BnH 대비 {metrics.get('excess_return',0)*100:+.1f}%")
                with c4:
                    st.metric("연환산 수익률",
                              f"{metrics['annual_return']*100:.1f}%")
                with c5:
                    st.metric("샤프 비율", f"{metrics['sharpe_ratio']:.2f}")
                with c6:
                    st.metric("최대 드로다운",
                              f"{metrics['max_drawdown']*100:.1f}%")
                
                st.markdown("---")
                grid_data = metrics.get('grid_data')
                trade_log = metrics.get('trade_log', [])
                
                if grid_data is not None:
                    # 1) 가격 차트 + 매매 마커
                    st.plotly_chart(
                        create_grid_price_chart(grid_data, trade_log, etf_names.get(etf_name, etf_name)),
                        use_container_width=True
                    )
                    
                    # 2) 포트폴리오 가치 vs 매수후보유
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(
                            create_grid_portfolio_chart(grid_data, initial_cash),
                            use_container_width=True
                        )
                    with col2:
                        st.plotly_chart(
                            create_grid_allocation_chart(grid_data),
                            use_container_width=True
                        )
                    
                    # 3) 드로다운 비교
                    st.plotly_chart(
                        create_grid_drawdown_chart(metrics),
                        use_container_width=True
                    )
                
                # 4) 거래 내역 테이블
                if trade_log:
                    st.markdown("#### 📋 거래 내역")
                    trade_df = pd.DataFrame(trade_log)
                    trade_df['date'] = pd.to_datetime(trade_df['date']).dt.strftime('%Y-%m-%d')
                    trade_df['price'] = trade_df['price'].apply(lambda x: f"{x:,.0f}")
                    trade_df['amount'] = trade_df['amount'].apply(lambda x: f"{x:,.0f}")
                    trade_df['cash'] = trade_df['cash'].apply(lambda x: f"{x:,.0f}")
                    trade_df.columns = ['날짜', '구분', '가격', '수량', '금액', '잔여현금', '보유수량']
                    st.dataframe(trade_df, use_container_width=True, height=min(400, 35 * len(trade_df) + 38))
                    st.caption(f"총 거래 횟수: {len(trade_log)}회 (매수 {len([t for t in trade_log if t['qty'] > 0])}회, 매도 {len([t for t in trade_log if t['qty'] < 0])}회)")
                
                st.markdown("---")
        
        # ========== 기타 전략 UI (기존 코드) ==========
        else:
            # 핵심 지표 카드
            total_returns = [r['total_return'] for r in results.values()]
            annual_returns = [r['annual_return'] for r in results.values()]
            sharpe_ratios = [r['sharpe_ratio'] for r in results.values()]
            max_drawdowns = [r['max_drawdown'] for r in results.values()]
            win_rates = [r['win_rate'] for r in results.values()]
            
            avg_total_return = np.mean(total_returns) * 100
            avg_annual_return = np.mean(annual_returns) * 100
            avg_sharpe = np.mean(sharpe_ratios)
            avg_max_dd = np.mean(max_drawdowns) * 100
            avg_win_rate = np.mean(win_rates)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("총 수익률", f"{avg_total_return:.1f}%", delta=f"{avg_total_return:.1f}%")
            with col2:
                st.metric("연환산 수익률", f"{avg_annual_return:.1f}%", delta=f"{avg_annual_return:.1f}%")
            with col3:
                st.metric("샤프 비율", f"{avg_sharpe:.2f}", delta=f"{avg_sharpe:.2f}")
            with col4:
                st.metric("최대 드로다운", f"{avg_max_dd:.1f}%", delta=f"{avg_max_dd:.1f}%")
            with col5:
                st.metric("승률", f"{avg_win_rate:.1f}%", delta=f"{avg_win_rate:.1f}%")
            
            # 차트 섹션
            first_etf = next(iter(results.keys()))
            first_metrics = results[first_etf]
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_portfolio_chart(first_metrics), use_container_width=True)
            with col2:
                st.plotly_chart(create_drawdown_chart(first_metrics), use_container_width=True)
            
            # ETF별 상세 결과
            st.markdown("### 📈 ETF별 상세 결과")
            for etf_name, metrics in results.items():
                with st.expander(f"🔍 {etf_names.get(etf_name, etf_name)} 상세 분석"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 수익률", f"{metrics['total_return']*100:.1f}%")
                        st.metric("샤프 비율", f"{metrics['sharpe_ratio']:.2f}")
                    with col2:
                        st.metric("연환산 수익률", f"{metrics['annual_return']*100:.1f}%")
                        st.metric("최대 드로다운", f"{metrics['max_drawdown']*100:.1f}%")
                    with col3:
                        st.metric("벤치마크 대비", f"{(metrics['total_return'] - metrics['benchmark_total'])*100:.1f}%")
                        st.metric("승률", f"{metrics['win_rate']:.1f}%")
            
            # ETF 가격 차트
            st.markdown("### 💹 ETF 가격 차트")
            if len(selected_etfs) <= 3:
                price_fig = create_price_charts(data_dict, selected_etfs)
                st.plotly_chart(price_fig, use_container_width=True)
            else:
                st.info("선택된 ETF가 너무 많아 차트를 생략했습니다. (3개 이하 권장)")
    
    else:
        st.info("👈 사이드바에서 설정을 조정하고 '백테스트 실행' 버튼을 클릭하세요.")
        
        # 기본 정보 표시
        st.markdown("## 📋 사용 가능한 ETF")
        etf_df = pd.DataFrame([
            {"ETF명": etf_names.get(k, k), "종목코드": v} 
            for k, v in config['data']['etfs'].items()
        ])
        st.dataframe(etf_df, use_container_width=True)

if __name__ == "__main__":
    main()