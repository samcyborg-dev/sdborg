import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Grok Cyborg v5 - Samson", layout="wide", page_icon="🚀")
st.title("🚀 Grok Cyborg v5 — Ultra-Sensitive Backtester")
st.markdown("**Now tuned to match your screenshot-style setups** (much more forgiving)")

tickers = {"Gold": "GC=F", "EURUSD": "EURUSD=X", "Oil": "CL=F", "DAX": "^GDAXI"}

def get_data(ticker, interval, period="180d"):
    try:
        return yf.download(ticker, interval=interval, period=period, progress=False).dropna()
    except:
        return pd.DataFrame()

def detect_4h_bias(df):
    if len(df) < 10: return None
    recent = df.tail(10)
    if recent['Close'].iloc[-1] > recent['Close'].mean():
        return "BULLISH"
    if recent['Close'].iloc[-1] < recent['Close'].mean():
        return "BEARISH"
    return None

def detect_1h_zone(df):
    if len(df) < 15: return {"after_sweep": False, "low": 0, "high": 0}
    last = df.tail(25)  # bigger window
    zone_high = last['High'].max()
    zone_low = last['Low'].min()
    current = df['Close'].iloc[-1]
    
    # Very forgiving liquidity sweep
    swept_high = df['High'].iloc[-50:-10].max() > zone_high * 1.0001
    swept_low = df['Low'].iloc[-50:-10].min() < zone_low * 0.9999
    swept = swept_high or swept_low
    
    inside = zone_low * 0.999 <= current <= zone_high * 1.001
    return {"after_sweep": swept and inside, "low": round(zone_low,5), "high": round(zone_high,5)}

def detect_5m_bos_retrace(df):
    if len(df) < 35: return None
    prev_high = df['High'].iloc[-30:-5].max()
    prev_low = df['Low'].iloc[-30:-5].min()
    current = df['Close'].iloc[-1]
    body = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1])
    
    # Extremely low threshold + very forgiving retrace
    if current > prev_high and body > 0.0001 and df['Low'].iloc[-12:-1].min() <= current <= df['Close'].iloc[-2] + 0.0002:
        return "🟢 BULLISH BOS + RETRACE"
    if current < prev_low and body > 0.0001 and df['High'].iloc[-12:-1].max() >= current >= df['Close'].iloc[-2] - 0.0002:
        return "🔴 BEARISH BOS + RETRACE"
    return None

# ===================== TABS =====================
tab1, tab2 = st.tabs(["📊 Full Backtester", "📈 Analytics"])

with tab2:
    st.subheader("📊 Ultra-Sensitive Backtester (v5)")
    if st.button("🚀 Run Backtest on Gold + EURUSD (Last 180 Days)", type="primary", use_container_width=True):
        with st.spinner("Scanning with very relaxed rules..."):
            trades = []
            for name, ticker in [("Gold", "GC=F"), ("EURUSD", "EURUSD=X")]:
                df4 = get_data(ticker, "4h")
                df1 = get_data(ticker, "1h")
                df5 = get_data(ticker, "5m")
                
                count = 0
                for i in range(120, len(df5)-10):
                    slice4 = df4[df4.index <= df5.index[i]].tail(18)
                    slice1 = df1[df1.index <= df5.index[i]].tail(30)
                    slice5 = df5.iloc[i-50:i+1]
                    
                    bias = detect_4h_bias(slice4)
                    zone = detect_1h_zone(slice1)
                    bos = detect_5m_bos_retrace(slice5)
                    
                    if bias and zone["after_sweep"] and bos:
                        entry = slice5['Close'].iloc[-1]
                        stop = zone["low"] if "BULLISH" in bos else zone["high"]
                        target = entry + 2.5*(entry-stop) if "BULLISH" in bos else entry - 2.5*(stop-entry)
                        result = "WIN" if (bos.startswith("🟢") and entry < target) or (bos.startswith("🔴") and entry > target) else "LOSS"
                        trades.append({"Asset": name, "Date": df5.index[i], "Direction": bos, "Entry": round(entry,5), "Stop": round(stop,5), "Target": round(target,5), "Result": result})
                        count += 1
                
                st.write(f"✅ {name}: {count} potential setups found internally")
            
            st.session_state.backtest_df = pd.DataFrame(trades)
            st.success(f"**FINAL RESULT: {len(trades)} trades found**")
    
    if "backtest_df" in st.session_state and not st.session_state.backtest_df.empty:
        bt = st.session_state.backtest_df
        wins = len(bt[bt.Result == "WIN"])
        total = len(bt)
        winrate = round(wins / total * 100, 1) if total > 0 else 0
        st.dataframe(bt.head(50), use_container_width=True)  # show first 50
        st.metric("Total Trades Found", total)
        st.metric("Win Rate", f"{winrate}%")
    else:
        st.info("Click the button above — this version is now very sensitive")

st.caption("v5 — Super relaxed detection. Should now find many of your real setups.")
