import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Ultimate Stock Scanner Suite", layout="wide")
st.title("🚀 My Personal 7-Strategy Stock Scanner Terminal")

india_tz = pytz.timezone('Asia/Kolkata')
current_time_india = datetime.now(india_tz).strftime('%d-%m-%Y %H:%M:%S')
st.write(f"Latest Terminal Scan Time (IST): **{current_time_india}**")

FO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 
    'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'TATASTEEL.NS', 'MARUTI.NS',
    'AXISBANK.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'ASIANPAINT.NS', 'M&M.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS',
    'ADANIENT.NS', 'ADANIPORTS.NS', 'POWERGRID.NS', 'NTPC.NS', 'INDUSINDBK.NS',
    'JSWSTEEL.NS', 'HINDALCO.NS', 'TATACONSUM.NS', 'ONGC.NS', 'COALINDIA.NS',
    'TATAMOTORS.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS', 'NESTLEIND.NS'
]

def scan_all_strategies(stocks):
    orb_list, open_low_list, open_high_list = [], [], []
    vol_up_list, vol_down_list, ema_cross_list, bb_squeeze_list = [], [], [], []
    for stock in stocks:
        try:
            data_5m = yf.download(stock, period="1d", interval="5m", progress=False)
            data_1d = yf.download(stock, period="10d", interval="1d", progress=False)
            if data_5m.empty or len(data_5m) < 21 or data_1d.empty or len(data_1d) < 6:
                continue
            data_5m.columns = [col if isinstance(col, tuple) else col for col in data_5m.columns]
            data_1d.columns = [col if isinstance(col, tuple) else col for col in data_1d.columns]
            current_price = float(data_5m['Close'].iloc[-1])
            prev_price = float(data_5m['Close'].iloc[-2])
            today_open = float(data_5m['Open'].iloc[0])
            today_high = float(data_5m['High'].max())
            today_low = float(data_5m['Low'].min())
            today_vol = float(data_1d['Volume'].iloc[-1])
            avg_vol_5d = float(data_1d['Volume'].iloc[-6:-1].mean())
            
            first_15m = data_5m.iloc[:3]
            orb_high = float(first_15m['High'].max())
            orb_low = float(first_15m['Low'].min())
            if len(data_5m) > 3:
                if current_price > orb_high:
                    orb_list.append({"Stock": stock.replace(".NS",""), "Signal": "🟢 Bullish Breakout", "Price": round(current_price,2), "15M High": round(orb_high,2)})
                elif current_price < orb_low:
                    orb_list.append({"Stock": stock.replace(".NS",""), "Signal": "🔴 Bearish Breakdown", "Price": round(current_price,2), "15M Low": round(orb_low,2)})
            
            if abs(today_open - today_low) <= (today_open * 0.0005):
                open_low_list.append({"Stock": stock.replace(".NS",""), "Price": round(current_price,2), "Open/Low": round(today_open,2)})
            if abs(today_open - today_high) <= (today_open * 0.0005):
                open_high_list.append({"Stock": stock.replace(".NS",""), "Price": round(current_price,2), "Open/High": round(today_open,2)})
                
            if today_vol > (avg_vol_5d * 2):
                change = ((current_price - today_open) / today_open) * 100
                if change > 1.5:
                    vol_up_list.append({"Stock": stock.replace(".NS",""), "Price": round(current_price,2), "Volume X": round(today_vol/avg_vol_5d,1)})
                elif change < -1.5:
                    vol_down_list.append({"Stock": stock.replace(".NS",""), "Price": round(current_price,2), "Volume X": round(today_vol/avg_vol_5d,1)})
            
            data_5m['EMA20'] = data_5m['Close'].ewm(span=20, adjust=False).mean()
            current_ema = float(data_5m['EMA20'].iloc[-1])
            prev_ema = float(data_5m['EMA20'].iloc[-2])
            if today_vol > (avg_vol_5d * 1.2):
                if prev_price <= prev_ema and current_price > current_ema:
                    ema_cross_list.append({"Stock": stock.replace(".NS",""), "Signal": "🟢 Bullish Cross (Above 20 EMA)", "Price": round(current_price,2), "EMA20": round(current_ema,2)})
                elif prev_price >= prev_ema and current_price < current_ema:
                    ema_cross_list.append({"Stock": stock.replace(".NS",""), "Signal": "🔴 Bearish Cross (Below 20 EMA)", "Price": round(current_price,2), "EMA20": round(current_ema,2)})

            data_5m['MA20_BB'] = data_5m['Close'].rolling(window=20).mean()
            data_5m['STD'] = data_5m['Close'].rolling(window=20).std()
            data_5m['Upper_BB'] = data_5m['MA20_BB'] + (2 * data_5m['STD'])
            data_5m['Lower_BB'] = data_5m['MA20_BB'] - (2 * data_5m['STD'])
            current_upper = float(data_5m['Upper_BB'].iloc[-1])
            current_lower = float(data_5m['Lower_BB'].iloc[-1])
            prev_upper = float(data_5m['Upper_BB'].iloc[-2])
            prev_lower = float(data_5m['Lower_BB'].iloc[-2])
            if prev_price <= prev_upper and current_price > current_upper:
                bb_squeeze_list.append({"Stock": stock.replace(".NS",""), "Signal": "🟢 BB Breakout (Upper Band)", "Price": round(current_price,2), "Upper Band": round(current_upper,2)})
            elif prev_price >= prev_lower and current_price < current_lower:
                bb_squeeze_list.append({"Stock": stock.replace(".NS",""), "Signal": "🔴 BB Breakdown (Lower Band)", "Price": round(current_price,2), "Lower Band": round(current_lower,2)})
        except Exception as e:
            pass
    return (pd.DataFrame(orb_list), pd.DataFrame(open_low_list), pd.DataFrame(open_high_list), 
            pd.DataFrame(vol_up_list), pd.DataFrame(vol_down_list), pd.DataFrame(ema_cross_list), pd.DataFrame(bb_squeeze_list))

if st.button("🔄 Scan All 7 Terminal Strategies Now"):
    with st.spinner("All 7 Strategies scanning in progress..."):
        df_orb, df_ol, df_oh, df_vu, df_vd, df_ema, df_bb = scan_all_strategies(FO_STOCKS)
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "⏱️ 15 Min ORB", "🚀 Open = Low (Bullish)", "📉 Open = High (Bearish)", 
            "🔊 Vol Breakout (Low-High)", "💥 Vol Breakdown (High-Low)", "📈 20 EMA Cross (Volume)", "🔮 Bollinger Bands Squeeze"
        ])
        with tab1:
            st.subheader("15 Minute Opening Range Breakout / Breakdown")
            st.dataframe(df_orb, use_container_width=True) if not df_orb.empty else st.info("Filhal kisi stock me 15M breakout nahi hai.")
        with tab2:
            st.subheader("Strong Bullish Stocks (Open = Low)")
            st.dataframe(df_ol, use_container_width=True) if not df_ol.empty else st.info("Filhal koi Open=Low stock nahi mila.")
        with tab3:
            st.subheader("Strong Bearish Stocks (Open = High)")
            st.dataframe(df_oh, use_container_width=True) if not df_oh.empty else st.info("Filhal koi Open=High stock nahi mila.")
        with tab4:
            st.subheader("High Volume Price Breakout (Low to High)")
            st.dataframe(df_vu, use_container_width=True) if not df_vu.empty else st.info("Filhal 2x volume ke sath koi breakout nahi mila.")
        with tab5:
            st.subheader("High Volume Price Breakdown (High to Low)")
            st.dataframe(df_vd, use_container_width=True) if not df_vd.empty else st.info("Filhal 2x volume ke sath koi breakdown nahi mila.")
        with tab6:
            st.subheader("Trend Following: 20 EMA Crossover with High Volume")
            st.dataframe(df_ema, use_container_width=True) if not df_ema.empty else st.info("Filhal 20 EMA ko high volume ke sath kisi stock ne cross nahi kiya.")
        with tab7:
            st.subheader("Volatility Expansion: Bollinger Bands Squeeze Breakout")
            st.dataframe(df_bb, use_container_width=True) if not df_bb.empty else st.info("Filhal Bollinger Bands ke bahar koi pricing breakout nahi hai.")
