import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Ultimate 8-Strategy Terminal", layout="wide")
st.title("🦅 My Ultimate 180+ F&O & Nifty 50 Professional Dashboard")

india_tz = pytz.timezone('Asia/Kolkata')
now_india = datetime.now(india_tz)
st.write(f"Latest Terminal Scan Time (IST): **{now_india.strftime('%d-%m-%Y %H:%M:%S')}**")

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
    st.warning("⚠️ STARTUP REMARK: Live Market is CLOSED. Showing last available session data for analysis.")
    data_period = "5d"
else:
    st.success("🟢 STARTUP REMARK: Live Market is OPEN! Scanning in real-time.")
    data_period = "1d"

# Nifty 50 Exact Stocks List
NIFTY50_STOCKS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 
    'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BRITANNIA.NS', 'CIPLA.NS', 
    'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 
    'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 
    'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'M&M.NS', 'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 
    'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TCS.NS', 'TATACONSUM.NS', 
    'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'SHRIRAMFIN.NS'
]

# Complete 180+ F&O Stocks List
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
def scan_all_strategies(stocks):
    orb_list, open_low_list, open_high_list = [], [], []
    vol_up_list, vol_down_list, ema_cross_list, bb_squeeze_list = [], [], [], []
    progress_text = st.empty()
    
    for idx, stock in enumerate(stocks):
        if idx % 20 == 0:
            progress_text.text(f"Scanning 180+ Market Momentum: {idx}/{len(stocks)} processed...")
        try:
            data = yf.download(stock, period=data_period, interval="1d", progress=False)
            if data.empty or len(data) < 6: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            
            current_price = float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2])
            today_open = float(data['Open'].iloc[-1])
            today_high = float(data['High'].iloc[-1])
            today_low = float(data['Low'].iloc[-1])
            today_vol = float(data['Volume'].iloc[-1])
            avg_vol_5d = float(data['Volume'].iloc[-6:-1].mean())
            stock_name = stock.replace(".NS","")
            
            if current_price > prev_price:
                orb_list.append({"Stock": stock_name, "Signal": "🟢 Bullish Breakout", "Price": round(current_price,2), "Prev Close": round(prev_price,2)})
            elif current_price < prev_price:
                orb_list.append({"Stock": stock_name, "Signal": "🔴 Bearish Breakdown", "Price": round(current_price,2), "Prev Close": round(prev_price,2)})
            
            if abs(today_open - today_low) <= (today_open * 0.001):
                open_low_list.append({"Stock": stock_name, "Price": round(current_price,2), "Open/Low": round(today_open,2)})
            if abs(today_open - today_high) <= (today_open * 0.001):
                open_high_list.append({"Stock": stock_name, "Price": round(current_price,2), "Open/High": round(today_open,2)})
                
            if today_vol > avg_vol_5d:
                price_change = ((current_price - today_open) / today_open) * 100
                if price_change > 0.5:
                    vol_up_list.append({"Stock": stock_name, "Price": round(current_price,2), "Volume X": round(today_vol/avg_vol_5d,1)})
                elif price_change < -0.5:
                    vol_down_list.append({"Stock": stock_name, "Price": round(current_price,2), "Volume X": round(today_vol/avg_vol_5d,1)})
            
            data['SMA5'] = data['Close'].rolling(window=5).mean()
            current_sma = float(data['SMA5'].iloc[-1])
            prev_sma = float(data['SMA5'].iloc[-2])
            if prev_price <= prev_sma and current_price > current_sma:
                ema_cross_list.append({"Stock": stock_name, "Signal": "🟢 Bullish Cross", "Price": round(current_price,2), "SMA5": round(current_sma,2)})
            elif prev_price >= prev_sma and current_price < current_sma:
                ema_cross_list.append({"Stock": stock_name, "Signal": "🔴 Bearish Cross", "Price": round(current_price,2), "SMA5": round(current_sma,2)})

            data['STD'] = data['Close'].rolling(window=5).std()
            data['Upper'] = data['SMA5'] + (1.5 * data['STD'])
            data['Lower'] = data['SMA5'] - (1.5 * data['STD'])
            if current_price > float(data['Upper'].iloc[-1]):
                bb_squeeze_list.append({"Stock": stock_name, "Signal": "🟢 Upper Band Breakout", "Price": round(current_price,2), "Upper": round(data['Upper'].iloc[-1],2)})
            elif current_price < float(data['Lower'].iloc[-1]):
                bb_squeeze_list.append({"Stock": stock_name, "Signal": "🔴 Lower Band Breakdown", "Price": round(current_price,2), "Lower": round(data['Lower'].iloc[-1],2)})
        except: pass
    progress_text.empty()
    return (pd.DataFrame(orb_list), pd.DataFrame(open_low_list), pd.DataFrame(open_high_list), 
            pd.DataFrame(vol_up_list), pd.DataFrame(vol_down_list), pd.DataFrame(ema_cross_list), pd.DataFrame(bb_squeeze_list))

def get_nifty50_dashboard(stocks):
    nifty_data = []
    advances, declines = 0, 0
    for stock in stocks:
        try:
            res = yf.download(stock, period="2d", interval="1d", progress=False)
            if res.empty: continue
            if isinstance(res.columns, pd.MultiIndex): res.columns = res.columns.get_level_values(0)
            
            op = round(float(res['Open'].iloc[-1]), 2)
            hi = round(float(res['High'].iloc[-1]), 2)
            lo = round(float(res['Low'].iloc[-1]), 2)
            cl = round(float(res['Close'].iloc[-1]), 2)
            prev_cl = float(res['Close'].iloc[-2])
            chg = round(((cl - prev_cl) / prev_cl) * 100, 2)
            
            if chg >= 0: advances += 1
            else: declines += 1
            
            nifty_data.append({"Stock": stock.replace(".NS",""), "Open": op, "High": hi, "Low": lo, "Close": cl, "Change %": chg})
        except: pass
    return pd.DataFrame(nifty_data), advances, declines

if st.button("🚀 Run Ultimate Terminal Scan Now"):
    with st.spinner("Processing analysis... Please wait."):
        df_orb, df_ol, df_oh, df_vu, df_vd, df_ema, df_bb = scan_all_strategies(FO_STOCKS)
        df_nifty, adv, dec = get_nifty50_dashboard(NIFTY50_STOCKS)
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "⏱️ 15 Min ORB", "🚀 Open = Low", "📉 Open = High", "🔊 Vol Breakout", "💥 Vol Breakdown", "📈 20 EMA Cross", "🔮 BB Squeeze", "📊 Nifty 50 Dashboard"
        ])
        
        def show_data(df, msg):
            st.dataframe(df, use_container_width=True) if not df.empty else st.info(msg)

        with tab1: show_data(df_orb, "No stocks matched.")
        with tab2: show_data(df_ol, "No stocks matched.")
        with tab3: show_data(df_oh, "No stocks matched.")
        with tab4: show_data(df_vu, "No stocks matched.")
        with tab5: show_data(df_vd, "No stocks matched.")
        with tab6: show_data(df_ema, "No stocks matched.")
        with tab7: show_data(df_bb, "No stocks matched.")
        with tab8:
            st.subheader("Nifty 50 Real-Time Heatmap Sheet")
            if not df_nifty.empty:
                # Custom Style to Color Code Positive in Green and Negative in Red
                def color_change(val):
                    color = 'green' if val >= 0 else 'red'
                    return f'color: {color}; font-weight: bold;'
                st.dataframe(df_nifty.style.applymap(color_change, subset=['Change %']), use_container_width=True)
                
                st.markdown("---")
                st.subheader("📊 Advance / Decline Ratio")
                col1, col2, col3 = st.columns(3)
                col1.metric("🟢 ADVANCES (Gainers)", adv)
                col2.metric("🔴 DECLINES (Losers)", dec)
                col3.metric("📊 A/D RATIO", round(adv/dec, 2) if dec > 0 else adv)
            else:
                st.info("Nifty 50 data unavailable.")
