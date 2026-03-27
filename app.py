import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Grok Cyborg Scanner - Samson", layout="wide", page_icon="🚀")
st.title("🚀 Grok Cyborg Scanner")
st.markdown("**Your exact 4H → 1H entered → 5M BOS + Retrace strategy** | Live • Free • No subscriptions")

# ================== TICKERS ==================
tickers = {
    "Gold": "GC=F",
    "EURUSD": "EURUSD=X",
    "Oil": "CL=F",
    "DAX": "^GDAXI",
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Eurodollar": "GE=F"
}

# ================== HELPER FUNCTIONS ==================
def get_data(ticker, interval, period="5d"):
    data = yf.download(ticker, interval=interval, period=period, progress=False)
    return data.dropna()

def detect_4h_bias(df):
    if len(df) < 10:
        return "NEUTRAL"
    highs = df['High'].tail(8)
    lows = df['Low'].tail(8)
    if highs.is_monotonic_increasing and lows.is_monotonic_increasing:
        return "🟢 BULLISH"
    if highs.is_monotonic_decreasing and lows.is_monotonic_decreasing:
        return "🔴 BEARISH"
    return "⚪ CHOP"

def detect_1h_zone(df_1h):
    last_12 = df_1h.tail(12)
    zone_high = last_12['High'].max()
    zone_low = last_12['Low'].min()
    current = df_1h['Close'].iloc[-1]
    
    # Liquidity sweep detection
    swept = False
    if df_1h['High'].iloc[-20:-8].max() > zone_high + 0.0001:
        swept = True
    if df_1h['Low'].iloc[-20:-8].min() < zone_low - 0.0001:
        swept = True
    
    inside = zone_low <= current <= zone_high
    return {
        "inside": inside,
        "after_sweep": swept and inside,
        "zone_low": round(zone_low, 5),
        "zone_high": round(zone_high, 5)
    }

def detect_5m_bos_retrace(df_5m):
    if len(df_5m) < 25:
        return None
    last_20 = df_5m.tail(20)
    prev_high = last_20['High'].iloc[-15:-3].max()
    prev_low = last_20['Low'].iloc[-15:-3].min()
    
    current = df_5m['Close'].iloc[-1]
    body = abs(df_5m['Close'].iloc[-1] - df_5m['Open'].iloc[-1])
    
    # Bullish BOS + retrace
    if current > prev_high and body > 0.0003:
        retrace_zone = df_5m['Low'].iloc[-5:-1].min()
        if retrace_zone <= current <= df_5m['Close'].iloc[-2]:
            return "🟢 BULLISH BOS + RETRACE"
    # Bearish BOS + retrace
    if current < prev_low and body > 0.0003:
        retrace_zone = df_5m['High'].iloc[-5:-1].max()
        if retrace_zone >= current >= df_5m['Close'].iloc[-2]:
            return "🔴 BEARISH BOS + RETRACE"
    return None

def plot_mini_chart(df, title, signal_color):
    fig = go.Figure()
    fig.add_candlestick(open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                        increasing_line_color='lime', decreasing_line_color='red')
    fig.update_layout(title=title, height=180, margin=dict(l=0,r=0,t=30,b=0),
                      template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
    if signal_color:
        fig.add_hline(y=df['Close'].iloc[-1], line_dash="dash", line_color=signal_color)
    return fig

# ================== LIVE SCANNER ==================
if st.button("🔴 START LIVE SCANNER", type="primary", use_container_width=True):
    st.session_state.running = True

placeholder = st.empty()

while st.session_state.get("running", False):
    with placeholder.container():
        st.markdown(f"**Last scan:** {datetime.now().strftime('%H:%M:%S')} UTC+3")
        
        cols = st.columns(len(tickers))
        signals = []
        
        for idx, (name, ticker) in enumerate(tickers.items()):
            try:
                df4 = get_data(ticker, "4h")
                df1 = get_data(ticker, "1h")
                df5 = get_data(ticker, "5m")
                
                bias = detect_4h_bias(df4)
                zone = detect_1h_zone(df1)
                bos = detect_5m_bos_retrace(df5)
                
                if bias != "⚪ CHOP" and zone["after_sweep"] and bos:
                    signal = {
                        "Ticker": name,
                        "Time": datetime.now().strftime("%H:%M"),
                        "Bias": bias,
                        "Zone": f"{zone['zone_low']} - {zone['zone_high']}",
                        "5M Signal": bos,
                        "Price": round(df5['Close'].iloc[-1], 5)
                    }
                    signals.append(signal)
                    
                    # Show mini charts
                    with cols[idx]:
                        st.subheader(name)
                        st.plotly_chart(plot_mini_chart(df4.tail(30), "4H", "lime" if "BULLISH" in bias else "red"), use_container_width=True)
                        st.plotly_chart(plot_mini_chart(df1.tail(30), "1H", None), use_container_width=True)
                        st.plotly_chart(plot_mini_chart(df5.tail(40), "5M", "lime" if "BULLISH" in bos else "red"), use_container_width=True)
                        st.success(f"**{bos}**")
                
            except:
                pass  # skip temporary errors
        
        if signals:
            st.dataframe(pd.DataFrame(signals), use_container_width=True)
        else:
            st.info("No setups right now. Scanner is still running...")
        
        st.caption("Auto-refresh every 60 seconds • Built for Samson’s exact strategy")
        time.sleep(60)
        st.rerun()
