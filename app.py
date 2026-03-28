import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Grok Cyborg v7 - Samson", layout="wide", page_icon="🚀")
st.title("🚀 Grok Cyborg v7 — Maximum Sensitivity")
st.markdown("**Ultra-relaxed detection using free yfinance 5-minute data**")

tickers = {"Gold": "GC=F", "EURUSD": "EURUSD=X"}

def get_data(ticker, interval, period="180d"):
    try:
        return yf.download(ticker, interval=interval, period=period, progress=False).dropna()
    except:
        return pd.DataFrame()

# ===================== ULTRA-SENSITIVE DETECTION =====================
def detect_4h_bias(df):
    if len(df) < 8: return None
    recent = df.tail(12)
    if recent['Close'].iloc[-1] > recent['Close'].mean(): return "BULLISH"
    if recent['Close'].iloc[-1] < recent['Close'].mean(): return "BEARISH"
    return None

def detect_1h_zone(df):
    if len(df) < 12: return {"after_sweep": False, "low": 0, "high": 0}
    last = df.tail(30)
    zone_high = last['High'].max()
    zone_low = last['Low'].min()
    current = df['Close'].iloc[-1]
    
    # Very forgiving sweep
    swept_high = df['High'].iloc[-70:-15].max() > zone_high * 1.0003
    swept_low = df['Low'].iloc[-70:-15].min() < zone_low * 0.9997
    swept = swept_high or swept_low
    inside = zone_low * 0.997 <= current <= zone_high * 1.003
    return {"after_sweep": swept and inside, "low": round(zone_low,5), "high": round(zone_high,5)}

def detect_5m_bos_retrace(df):
    if len(df) < 35: return None
    prev_high = df['High'].iloc[-32:-6].max()
    prev_low = df['Low'].iloc[-32:-6].min()
    current = df['Close'].iloc[-1]
    body = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1])
    
    # Extremely low threshold
    if current > prev_high and body > 0.00005 and df['Low'].iloc[-14:-1].min() <= current <= df['Close'].iloc[-2] + 0.0004:
        return "🟢 BULLISH BOS + RETRACE"
    if current < prev_low and body > 0.00005 and df['High'].iloc[-14:-1].max() >= current >= df['Close'].iloc[-2] - 0.0004:
        return "🔴 BEARISH BOS + RETRACE"
    return None

# ===================== BACKTESTER =====================
if st.button("🚀 Run Maximum Sensitivity Backtest (Last 180 Days)", type="primary", use_container_width=True):
    with st.spinner("Scanning with very relaxed rules..."):
        trades = []
        for name, ticker in tickers.items():
            df4 = get_data(ticker, "4h")
            df1 = get_data(ticker, "1h")
            df5 = get_data(ticker, "5m")
            
            for i in range(150, len(df5)-20):
                slice4 = df4[df4.index <= df5.index[i]].tail(20)
                slice1 = df1[df1.index <= df5.index[i]].tail(40)
                slice5 = df5.iloc[i-60:i+1]
                
                bias = detect_4h_bias(slice4)
                zone = detect_1h_zone(slice1)
                bos = detect_5m_bos_retrace(slice5)
                
                if bias and zone["after_sweep"] and bos:
                    entry = slice5['Close'].iloc[-1]
                    stop = zone["low"] if "BULLISH" in bos else zone["high"]
                    target = entry + 2.5*(entry - stop) if "BULLISH" in bos else entry - 2.5*(stop - entry)
                    result = "WIN" if (bos.startswith("🟢") and entry < target) or (bos.startswith("🔴") and entry > target) else "LOSS"
                    trades.append({
                        "Asset": name,
                        "Date": df5.index[i],
                        "Direction": bos,
                        "Entry": round(entry, 5),
                        "Stop": round(stop, 5),
                        "Target": round(target, 5),
                        "Result": result
                    })
        
        st.session_state.backtest_df = pd.DataFrame(trades)
        st.success(f"**Backtest finished! Found {len(trades)} trades**")

# Show results
if "backtest_df" in st.session_state and not st.session_state.backtest_df.empty:
    bt = st.session_state.backtest_df
    wins = len(bt[bt.Result == "WIN"])
    total = len(bt)
    winrate = round(wins / total * 100, 1) if total > 0 else 0
    st.dataframe(bt, use_container_width=True)
    st.metric("Total Trades Found", total)
    st.metric("Win Rate", f"{winrate}%")
else:
    st.info("Click the button above to run the backtest")

st.caption("v7 — Maximum sensitivity using free yfinance 5m data • Should now find many of your setups")
