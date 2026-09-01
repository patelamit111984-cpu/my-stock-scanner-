import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dynamic F&O ORB Scanner", layout="wide")
st.title("📊 My Personal Dynamic ORB Scanner (Nifty F&O)")
st.write(f"Latest Market Scan Time: **{datetime.now().strftime('%H:%M:%S')}**")

FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
    'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'TATASTEEL.NS', 'MARUTI.NS'
]

def run_orb_scanner(stocks):
    breakout_list = []
    for stock in stocks:
        try:
            data = yf.download(stock, period="1d", interval="5m", progress=False)
            if data.empty or len(data) < 3:
                continue
            current_price = data['Close'].iloc[-1]
            opening_range_data = data.iloc[:-1] 
            range_high = opening_range_data['High'].max()
            range_low = opening_range_data['Low'].min()
            
            if current_price > range_high:
                breakout_list.append({
                    "Stock": stock.replace(".NS", ""),
                    "Signal": "🟢 BULLISH BREAKOUT (UP)",
                    "Current Price": round(current_price, 2),
                    "Range High": round(range_high, 2)
                })
            elif current_price < range_low:
                breakout_list.append({
                    "Stock": stock.replace(".NS", ""),
                    "Signal": "🔴 BEARISH BREAKOUT (DOWN)",
                    "Current Price": round(current_price, 2),
                    "Range Low": round(range_low, 2)
                })
        except Exception as e:
            pass
    return pd.DataFrame(breakout_list)

if st.button("🔄 Scan Market Right Now"):
    with st.spinner("Scanning latest F&O stocks data..."):
        df_result = run_orb_scanner(FO_STOCKS)
        if not df_result.empty:
            st.success(f"Found {len(df_result)} stocks breaking out right now!")
            st.dataframe(df_result, use_container_width=True)
        else:
            st.warning("Filhal kisi bhi F&O stock mein is exact time par breakout nahi hai.")

