import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(
    page_title="Pro Terminal 180+ F&O & Nifty 50", 
    layout="wide"
)

st.title("🦅 My Ultimate F&O + Nifty 50 Multi-Strategy Trading Terminal")

india_tz = pytz.timezone('Asia/Kolkata')
now_india = datetime.now(india_tz)
current_time_india = now_india.strftime('%d-%m-%Y %H:%M:%S')
st.write(f"Latest Terminal Scan Time (IST): **{current_time_india}**")

current_hour = now_india.hour
current_minute = now_india.minute
current_day = now_india.weekday()

market_closed = False

if current_day >= 5:
    market_closed = True
elif (current_hour < 9) or (current_hour == 9 and current_minute < 15):
    market_closed = True
elif (current_hour > 15) or (current_hour == 15 and current_minute > 30):
    market_closed = True

if market_closed:
    st.warning("⚠️ STARTUP REMARK: Live Market is CLOSED right now. System has automatically loaded the last available closing data for your analysis and off-market research.")
    data_period = "5d"
else:
    st.success("🟢 STARTUP REMARK: Live Market is OPEN! Scanning 180+ F&O & Nifty 50 stocks in real-time.")
    data_period = "1d"

FO_STOCKS = [
    'AARTIIND.NS', 'ABB.NS', 'ABBOTINDIA.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIPORTS.NS',
    'ADANIPOWER.NS', 'ALKEM.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 
    'ASTRAL.NS', 'ATUL.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 
    'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BATAINDIA.NS', 'BEL.NS', 'BERGEPAINT.NS', 
    'BHARATFORG.NS', 'BHARTIARTL.NS', 'BHEL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'BSOFT.NS', 
    'CANFINHOME.NS', 'CANBK.NS', 'CHAMBLFERT.NS', 'CHOLAMFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COCHINSHIP.NS', 'COFORGE.NS', 
    'COLPAL.NS', 'CONCOR.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'CUB.NS', 'CUMMINSIND.NS', 'DABUR.NS', 'DALBHARAT.NS', 
    'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 
    'EXIDEIND.NS', 'FEDERALBNK.NS', 'FORCEMOT.NS', 'GAIL.NS', 'GLENMARK.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GODFREYPHLP.NS', 
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRANULES.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HAVELLS.NS', 'HCLTECH.NS', 
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HYUNDAI.NS', 
    'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDEA.NS', 'IDFC.NS', 'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS', 
    'INDHOTEL.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS', 'INFY.NS', 'IOC.NS', 
    'IPCALAB.NS', 'IRCTC.NS', 'ITC.NS', 'JINDALSTEL.NS', 'JIOFIN.NS', 'JKCEMENT.NS', 'JSWSTEEL.NS', 'JUBLFOOD.NS', 
    'KOTAKBANK.NS', 'L&TFH.NS', 'LALPATHLAB.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LUPIN.NS', 
    'M&M.NS', 'M&MFIN.NS', 'MANAPPURAM.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MCDOWELL-N.NS', 'MCX.NS', 
    'METROPOLIS.NS', 'MFSL.NS', 'MGL.NS', 'MOTHERSON.NS', 'MOTILALOFS.NS', 'MPHASIS.NS', 'MRF.NS', 'MUTHOOTFIN.NS', 
    'NATIONALUM.NS', 'NAVINFLUOR.NS', 'NAUKRI.NS', 'NESTLEIND.NS', 'NIPPONLIFE.NS', 'NMDC.NS', 'NTPC.NS', 'OBEROIRLTY.NS', 
    'ONGC.NS', 'PAGEIND.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS', 
    'POLYCAB.NS', 'POWERGRID.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'RECCON.NS', 'RELIANCE.NS', 'SAIL.NS', 
    'SBICARD.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SRF.NS', 'SUNPHARMA.NS', 
    'SUNTV.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACHEMICAL.NS', 'TATACOMM.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 
    'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TVSMOTOR.NS', 
    'UBL.NS', 'ULTRACEMCO.NS', 'UPL.NS', 'VEDL.NS', 'VISHALMEGA.NS', 'VOLTAS.NS', 'WIPRO.NS', 'ZEEL.NS', 'ZYDUSLIFE.NS'
]

def get_tv_link(symbol):
    clean_symbol = symbol.replace(".NS", "")
    base_url = "https://tradingview.com"
    params = f"?symbol=NSE%3A{clean_symbol}&interval=5&theme=dark&style=1&timezone=Asia%2FKolkata&studies=%5B%22RSI%40tv-basicstudies%22%2C%22Volume%40tv-basicstudies%22%5D"
    return f"{base_url}{params}"
def scan_all_strategies(stocks):
    orb_list = []
    open_low_list = []
    open_high_list = []
    vol_up_list = []
    vol_down_list = []
    ema_cross_list = []
    bb_squeeze_list = []
    
    progress_text = st.empty()
    
    for idx, stock in enumerate(stocks):
        if idx % 20 == 0:
            progress_text.text(f"Scanning momentum: {idx}/{len(stocks)} stocks processed...")
        try:
            data_5m = yf.download(stock, period=data_period, interval="5m", progress=False)
            data_1d = yf.download(stock, period="10d", interval="1d", progress=False)
            
            if data_5m.empty or len(data_5m) < 21 or data_1d.empty or len(data_1d) < 6:
                continue
                
            data_5m.columns = [col if isinstance(col, tuple) else col for col in data_5m.columns]
            data_1d.columns = [col if isinstance(col, tuple) else col for col in data_1d.columns]
            
            last_date = data_5m.index[-1].date()
            day_data = data_5m[data_5m.index.date == last_date]
            if day_data.empty: 
                continue
            
            current_price = float(day_data['Close'].iloc[-1])
            prev_price = float(day_data['Close'].iloc[-2]) if len(day_data) > 1 else current_price
            today_open = float(day_data['Open'].iloc)
            today_high = float(day_data['High'].max())
            today_low = float(day_data['Low'].min())
            today_vol = float(data_1d['Volume'].iloc[-1])
            avg_vol_5d = float(data_1d['Volume'].iloc[-6:-1].mean())
            tv_url = get_tv_link(stock)
            stock_name = stock.replace(".NS","")
            
            first_15m = day_data.iloc[:3]
            if len(first_15m) >= 3:
                orb_high = float(first_15m['High'].max())
                orb_low = float(first_15m['Low'].min())
                if len(day_data) > 3:
                    if current_price > orb_high:
                        orb_list.append({"Stock": stock_name, "Signal": "🟢 Bullish Breakout", "Price": round(current_price,2), "15M High": round(orb_high,2), "Chart": tv_url})
                    elif current_price < orb_low:
                        orb_list.append({"Stock": stock_name, "Signal": "🔴 Bearish Breakdown", "Price": round(current_price,2), "15M Low": round(orb_low,2), "Chart": tv_url})
            
            if abs(today_open - today_low) <= (today_open * 0.0005):
                open_low_list.append({"Stock": stock_name, "Price": round(current_price,2), "Open/Low": round(today_open,2), "Chart": tv_url})
            if abs(today_open - today_high) <= (today_open * 0.0005):
                open_high_list.append({"Stock": stock_name, "Price": round(current_price,2), "Open/High": round(today_open,2), "Chart": tv_url})
                
            if today_vol > (avg_vol_5d * 1.5):
                change = ((current_price - today_open) / today_open) * 100
                if change > 1.0:
                    vol_up_list.append({"Stock": stock_name, "Price": round(current_price,2), "Volume X": round(today_vol/avg_vol_5d,1), "Chart": tv_url})
                elif change < -1.0:
                    vol_down_list.append({"Stock": stock_name, "Price": round(current_price,2), "Volume X": round(today_vol/avg_vol_5d,1), "Chart": tv_url})
            
            day_data['EMA20'] = day_data['Close'].ewm(span=20, adjust=False).mean()
            current_ema = float(day_data['EMA20'].iloc[-1])
            prev_ema = float(day_data['EMA20'].iloc[-2]) if len(day_data) > 1 else current_ema
            
            if prev_price <= prev_ema and current_price > current_ema:
                ema_cross_list.append({"Stock": stock_name, "Signal": "🟢 Above 20 EMA", "Price": round(current_price,2), "EMA20": round(current_ema,2), "Chart": tv_url})
            elif prev_price >= prev_ema and current_price < current_ema:
                ema_cross_list.append({"Stock": stock_name, "Signal": "🔴 Below 20 EMA", "Price": round(current_price,2), "EMA20": round(current_ema,2), "Chart": tv_url})

            day_data['MA20_BB'] = day_data['Close'].rolling(window=20).mean()
            day_data['STD'] = day_data['Close'].rolling(window=20).std()
            data_5m['Upper_BB'] = day_data['MA20_BB'] + (2 * day_data['STD'])
            data_5m['Lower_BB'] = day_data['MA20_BB'] - (2 * day_data['STD'])
            
            if not data_5m['Upper_BB'].isna().iloc[-1]:
                current_upper = float(data_5m['Upper_BB'].iloc[-1])
                current_lower = float(data_5m['Lower_BB'].iloc[-1])
                prev_upper = float(data_5m['Upper_BB'].iloc[-2]) if len(day_data) > 1 else current_upper
                prev_lower = float(data_5m['Lower_BB'].iloc[-2]) if len(day_data) > 1 else current_lower
                
                if prev_price <= prev_upper and current_price > current_upper:
                    bb_squeeze_list.append({"Stock": stock_name, "Signal": "🟢 Upper Band Breakout", "Price": round(current_price,2), "Upper Band": round(current_upper,2), "Chart": tv_url})
                elif prev_price >= prev_lower and current_price < current_lower:
                    bb_squeeze_list.append({"Stock": stock_name, "Signal": "🔴 Lower Band Breakdown", "Price": round(current_price,2), "Lower Band": round(current_lower,2), "Chart": tv_url})
        except Exception as e:
            pass
            
    progress_text.empty()
    return (pd.DataFrame(orb_list), pd.DataFrame(open_low_list), pd.DataFrame(open_high_list), 
            pd.DataFrame(vol_up_list), pd.DataFrame(vol_down_list), pd.DataFrame(ema_cross_list), pd.DataFrame(bb_squeeze_list))

if st.button("🚀 Scan All Active F&O + Nifty 50 Market Now"):
    with st.spinner("Processing advanced mathematical analysis for all stocks... Please wait."):
        df_orb, df_ol, df_oh, df_vu, df_vd, df_ema, df_bb = scan_all_strategies(FO_STOCKS)
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "⏱️ 15 Min ORB", "🚀 Open = Low (Bullish)", "📉 Open = High (Bearish)", 
            "🔊 Vol Breakout (Low-High)", "💥 Vol Breakdown (High-Low)", "📈 20 EMA Cross", "🔮 Bollinger Bands Squeeze"
        ])
        
        def show_data(df, empty_msg):
            if not df.empty:
                st.dataframe(df, use_container_width=True, column_config={"Chart": st.column_config.LinkColumn("TradingView Chart")})
            else:
                st.info(empty_msg)
                
        with tab1:
            st.subheader("15 Minute Opening Range Breakout / Breakdown")
            show_data(df_orb, "No breakout found in current session data.")
        with tab2:
            st.subheader("Strong Bullish Stocks (Open = Low)")
            show_data(df_ol, "No Open=Low stock found in current session.")
        with tab3:
            st.subheader("Strong Bearish Stocks (Open = High)")
            show_data(df_oh, "No Open=High stock found in current session.")
        with tab4:
            st.subheader("High Volume Price Breakout (Low to High)")
            show_data(df_vu, "No heavy volume breakout found.")
        with tab5:
            st.subheader("High Volume Price Breakdown (High to Low)")
            show_data(df_vd, "No heavy volume breakdown found.")
        with tab6:
            st.subheader("Trend Following: 20 EMA Crossover with High Volume")
            show_data(df_ema, "No recent 20 EMA crossover found in this session.")
        with tab7:
            st.subheader("Volatility Expansion: Bollinger Bands Squeeze Breakout")
            show_data(df_bb, "No Bollinger Bands squeeze expansion found.")
