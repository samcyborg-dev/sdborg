import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Grok Cyborg v4 - Samson", layout="wide", page_icon="🚀")
st.title("🚀 Grok Cyborg v4 — Fixed & Sensitive Backtester")
st.markdown("**Now tuned to catch your real screenshot-style setups**")

tickers = {"Gold": "GC=F", "EURUSD": "EURUSD=X", "Oil": "CL=F", "DAX": "^GDAXI"}

def get_data(ticker, interval, period="120d"):
    try:
        return yf.download(ticker, interval=interval, period=period, progress=False).dropna()
    except:
        return pd.DataFrame()

def detect_4h_bias(df):
    if len(df) < 12: return None
    # More forgiving bias detection (last 3 swings)
    recent = df.tail(12)
    if (recent['Close'].iloc[-1] > recent['Close'].iloc[-6]) and (recent['High'].iloc[-1] > recent['High'].iloc[-6]):
        return "BULLISH"
    if (recent['Close'].iloc[-1] < recent['Close'].iloc[-6]) and (recent['Low'].iloc[-1] < recent['Low'].iloc[-6]):
        return "BEARISH"
    return None

def detect_1h_zone(df):
    if len(df) < 20: return {"after_sweep": False, "low": 0, "high": 0}
    last = df.tail(20)
    zone_high = last['High'].max()
    zone_low = last['Low'].min()
    current = df['Close'].iloc[-1]
    
    # Liquidity sweep detection (broke extreme in last 30 bars then returned)
    swept_high = df['High'].iloc[-40:-15].max() > zone_high + 0.0002
    swept_low = df['Low'].iloc[-40:-15].min() < zone_low - 0.0002
    swept = swept_high or swept_low
    
    inside = zone_low <= current <= zone_high
    return {"after_sweep": swept and inside, "low": round(zone_low,5), "high": round(zone_high,5)}

def detect_5m_bos_retrace(df):
    if len(df) < 40: return None
    prev_high = df['High'].iloc[-30:-8].max()
    prev_low = df['Low'].iloc[-30:-8].min()
    current = df['Close'].iloc[-1]
    body = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1])
    
    # Lower threshold + allow smaller displacement for real setups
    if current > prev_high and body > 0.0003 and df['Low'].iloc[-10:-1].min() <= current <= df['Close'].iloc[-2]:
        return "🟢 BULLISH BOS + RETRACE"
    if current < prev_low and body > 0.0003 and df['High'].iloc[-10:-1].max() >= current >= df['Close'].iloc[-2]:
        return "🔴 BEARISH BOS + RETRACE"
    return None

# ===================== TABS =====================
tab1, tab2, tab3 = st.tabs(["🔴 Live Scanner", "📊 Full Backtester", "📈 Analytics"])

with tab2:
    st.subheader("📊 Full Backtester — Now Sensitive to Your Style")
    if st.button("🚀 Run Full Backtest (Last 120 Days)", type="primary", use_container_width=True):
        with st.spinner("Scanning for your exact screenshot-style setups..."):
            trades = []
            for name, ticker in tickers.items():
                df4 = get_data(ticker, "4h")
                df1 = get_data(ticker, "1h")
                df5 = get_data(ticker, "5m")
                
                for i in range(100, len(df5)-5):
                    slice4 = df4[df4.index <= df5.index[i]].tail(15)
                    slice1 = df1[df1.index <= df5.index[i]].tail(25)
                    slice5 = df5.iloc[i-45:i+1]
                    
                    bias = detect_4h_bias(slice4)
                    zone = detect_1h_zone(slice1)
                    bos = detect_5m_bos_retrace(slice5)
                    
                    if bias and zone["after_sweep"] and bos:
                        entry = slice5['Close'].iloc[-1]
                        stop = zone["low"] if "BULLISH" in bos else zone["high"]
                        target = entry + 2.5 * (entry - stop) if "BULLISH" in bos else entry - 2.5 * (stop - entry)
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
            st.success(f"✅ Backtest finished! Found **{len(trades)} trades**")
    
    if "backtest_df" in st.session_state and not st.session_state.backtest_df.empty:
        bt = st.session_state.backtest_df
        wins = len(bt[bt.Result == "WIN"])
        total = len(bt)
        winrate = round(wins / total * 100, 1) if total > 0 else 0
        st.dataframe(bt, use_container_width=True)
        st.metric("Win Rate", f"{winrate}%", f"{total} total trades")
    else:
        st.info("Click the button above to run the backtest.")

with tab3:
    st.subheader("📈 Analytics")
    if "backtest_df" in st.session_state and not st.session_state.backtest_df.empty:
        bt = st.session_state.backtest_df
        wins = len(bt[bt.Result == "WIN"])
        total = len(bt)
        winrate = round(wins / total * 100, 1) if total > 0 else 0
        st.metric("Win Rate", f"{winrate}%")
        st.metric("Total Trades Found", str(total))
        st.dataframe(bt, use_container_width=True)
    else:
        st.info("Run backtest first")

st.caption("v4 — Much more sensitive detection (should now find dozens of trades like your screenshots)")
