import re
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import time as dtime

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

try:
    from nsepython import fnolist, nse_optionchain_scrapper
except Exception:
    fnolist = None
    nse_optionchain_scrapper = None

# =============================================================================
# PAGE
# =============================================================================
st.set_page_config(
    page_title="NSE Fast Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

IST = "Asia/Kolkata"

st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 10px;
        padding: 10px;
    }
    .live-strip {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 12px 0;}
    .live-card {border:1px solid rgba(128,128,128,.25);border-radius:12px;padding:10px 12px;min-height:78px;}
    .live-title {font-size:12px;opacity:.75;}
    .live-value {font-size:23px;font-weight:700;line-height:1.15;}
    .live-change {font-size:13px;font-weight:700;}
    .pos {color:#00a65a;} .neg {color:#d62728;} .neu {color:#888;}
    .sector-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;}
    .sector-card {border-radius:12px;padding:12px;border:1px solid rgba(128,128,128,.22);min-height:105px;}
    .sector-name {font-size:15px;font-weight:800;}
    .sector-pct {font-size:22px;font-weight:800;margin:2px 0 6px;}
    .sector-stocks {font-size:12px;opacity:.90;}
    @media (max-width:900px){.live-strip,.sector-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# FALLBACK SYMBOLS
# Dynamic F&O list is attempted first through nsepython.
# These are only fallbacks so the app can still open if that call fails.
# =============================================================================
NIFTY50_FALLBACK = [
    "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK",
    "BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL",
    "CIPLA","COALINDIA","DRREDDY","EICHERMOT","ETERNAL","GRASIM",
    "HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO",
    "HINDUNILVR","ICICIBANK","INDUSINDBK","INFY","ITC","JIOFIN",
    "JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NESTLEIND","NTPC",
    "ONGC","POWERGRID","RELIANCE","SBILIFE","SBIN","SHRIRAMFIN",
    "SUNPHARMA","TATACONSUM","TATAMOTORS","TATASTEEL","TCS","TECHM",
    "TRENT","ULTRACEMCO","WIPRO","BAJAJHLDNG"
]

FO_FALLBACK = list(dict.fromkeys(NIFTY50_FALLBACK + [
    "ABB","ABCAPITAL","ABFRL","ACC","ADANIENSOL","ALKEM","AMBUJACEM",
    "ANGELONE","APLAPOLLO","ASHOKLEY","ASTRAL","AUBANK","AUROPHARMA",
    "BANDHANBNK","BANKBARODA","BANKINDIA","BATAINDIA","BDL","BERGEPAINT",
    "BHEL","BIOCON","BOSCHLTD","BPCL","BRITANNIA","BSE","CANBK",
    "CANFINHOME","CGPOWER","CHAMBLFERT","CHOLAFIN","COFORGE","COLPAL",
    "CONCOR","CROMPTON","CUMMINSIND","DABUR","DALBHARAT","DELHIVERY",
    "DIVISLAB","DIXON","DLF","DMART","FEDERALBNK","GAIL","GLENMARK",
    "GMRAIRPORT","GODREJCP","GODREJPROP","GRANULES","HAL","HAVELLS",
    "HFCL","HINDCOPPER","HINDPETRO","HUDCO","ICICIGI","ICICIPRULI",
    "IDEA","IDFCFIRSTB","IEX","IGL","INDHOTEL","INDIANB","INDIGO",
    "INDUSTOWER","IOC","IRB","IRCTC","IREDA","IRFC","JINDALSTEL",
    "JUBLFOOD","KEI","KPITTECH","LICHSGFIN","LICI","LODHA","LTIM",
    "LUPIN","MANAPPURAM","MARICO","MAXHEALTH","MCX","MFSL","MOTHERSON",
    "MPHASIS","MRF","MUTHOOTFIN","NAUKRI","NBCC","NCC","NHPC","NMDC",
    "OBEROIRLTY","OFSS","OIL","PAGEIND","PAYTM","PEL","PERSISTENT",
    "PETRONET","PFC","PIDILITIND","PNB","POLYCAB","POONAWALLA","PRESTIGE",
    "RBLBANK","RECLTD","SAIL","SAMMAANCAP","SBICARD","SIEMENS","SONACOMS",
    "SRF","SUNTV","SUPREMEIND","SYNGENE","TATACHEM","TATACOMM",
    "TATAELXSI","TATAPOWER","TATATECH","TIINDIA","TITAN","TORNTPHARM",
    "TORNTPOWER","TVSMOTOR","UBL","UNIONBANK","UNITDSPR","UPL","VBL",
    "VEDL","VOLTAS","YESBANK","ZYDUSLIFE"
]))

SECTOR_MAP = {
    "HDFCBANK":"BANK","ICICIBANK":"BANK","SBIN":"BANK","AXISBANK":"BANK","KOTAKBANK":"BANK","INDUSINDBK":"BANK",
    "INFY":"IT","TCS":"IT","HCLTECH":"IT","TECHM":"IT","WIPRO":"IT",
    "MARUTI":"AUTO","M&M":"AUTO","TATAMOTORS":"AUTO","EICHERMOT":"AUTO","HEROMOTOCO":"AUTO","BAJAJ-AUTO":"AUTO",
    "SUNPHARMA":"PHARMA","DRREDDY":"PHARMA","CIPLA":"PHARMA","APOLLOHOSP":"HEALTHCARE",
    "ITC":"FMCG","HINDUNILVR":"FMCG","NESTLEIND":"FMCG","TATACONSUM":"FMCG",
    "TATASTEEL":"METAL","HINDALCO":"METAL","JSWSTEEL":"METAL","COALINDIA":"METAL",
    "RELIANCE":"ENERGY","ONGC":"ENERGY","NTPC":"POWER","POWERGRID":"POWER",
    "LT":"INFRA","ADANIPORTS":"INFRA","ADANIENT":"DIVERSIFIED","BEL":"DEFENCE",
    "BAJFINANCE":"FINANCIAL","BAJAJFINSV":"FINANCIAL","JIOFIN":"FINANCIAL","SHRIRAMFIN":"FINANCIAL",
    "HDFCLIFE":"INSURANCE","SBILIFE":"INSURANCE","GRASIM":"CEMENT","ULTRACEMCO":"CEMENT",
    "ASIANPAINT":"CONSUMER","TRENT":"RETAIL","BHARTIARTL":"TELECOM","ETERNAL":"INTERNET","BAJAJHLDNG":"FINANCIAL"
}

# =============================================================================
# SYMBOLS / MARKET STATUS
# =============================================================================
def clean_symbol(x):
    return str(x).strip().upper().replace(".NS", "")

@st.cache_data(ttl=6 * 3600, show_spinner=False)
def get_fo_symbols(limit=180):
    symbols = []
    if fnolist is not None:
        try:
            raw = fnolist()
            if isinstance(raw, (list, tuple, set)):
                symbols = [clean_symbol(x) for x in raw]
        except Exception:
            symbols = []

    if not symbols:
        symbols = FO_FALLBACK.copy()

    excluded = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}
    symbols = [s for s in dict.fromkeys(symbols) if s and s not in excluded]
    return symbols[:int(limit)]

def market_status():
    now = pd.Timestamp.now(tz=IST)
    if now.weekday() >= 5:
        return "CLOSED"
    if dtime(9, 15) <= now.time() <= dtime(15, 30):
        return "OPEN"
    return "CLOSED"

# =============================================================================
# DATA FETCH
# =============================================================================
def chunks(items, n=35):
    for i in range(0, len(items), n):
        yield items[i:i+n]

@st.cache_data(ttl=45, show_spinner=False)
def fetch_intraday(symbols):
    """
    Uses Yahoo Finance 5-minute candles.

    Market OPEN:
        latest available intraday candles are scanned.

    Market CLOSED:
        latest available completed trading session is scanned automatically.
    """
    result = {}
    yahoo_symbols = [f"{s}.NS" for s in symbols]

    for batch in chunks(yahoo_symbols, 35):
        try:
            data = yf.download(
                tickers=batch,
                period="10d",
                interval="5m",
                group_by="ticker",
                auto_adjust=False,
                prepost=False,
                threads=True,
                progress=False,
            )
        except Exception:
            continue

        if data is None or len(data) == 0:
            continue

        for ys in batch:
            symbol = ys[:-3]
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if ys not in data.columns.get_level_values(0):
                        continue
                    df = data[ys].copy()
                else:
                    df = data.copy()

                df.columns = [str(c).lower() for c in df.columns]
                required = {"open", "high", "low", "close", "volume"}
                if not required.issubset(set(df.columns)):
                    continue

                df = df[["open","high","low","close","volume"]]
                df = df.dropna(subset=["close"])

                idx = pd.to_datetime(df.index)
                if idx.tz is None:
                    idx = idx.tz_localize("UTC")
                idx = idx.tz_convert(IST)
                df.index = idx

                if not df.empty:
                    result[symbol] = df.sort_index()

            except Exception:
                continue

    return result

# =============================================================================
# LIVE TOP STRIP — ADD-ON ONLY
# =============================================================================
@st.cache_data(ttl=60, show_spinner=False)
def yahoo_live_quote(ticker):
    try:
        intr = yf.download(ticker, period="5d", interval="5m", auto_adjust=False, progress=False, threads=False)
        daily = yf.download(ticker, period="10d", interval="1d", auto_adjust=False, progress=False, threads=False)
        if intr is None or intr.empty:
            return None
        c = intr["Close"]
        if isinstance(c, pd.DataFrame): c = c.iloc[:,0]
        price = float(c.dropna().iloc[-1])
        prev = np.nan
        if daily is not None and not daily.empty:
            dc = daily["Close"]
            if isinstance(dc, pd.DataFrame): dc = dc.iloc[:,0]
            vals = dc.dropna().astype(float).tolist()
            if len(vals) >= 2: prev = vals[-2]
            elif len(vals) == 1: prev = vals[-1]
        change = price-prev if pd.notna(prev) else np.nan
        pct = change/prev*100 if pd.notna(prev) and prev else np.nan
        return {"price":price,"change":change,"pct":pct}
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def gift_nifty_live():
    # Best-effort third-party public quote. If blocked, UI shows N/A.
    try:
        url = "https://giftcitynifty.com/gift-nifty-intraday-price-data/"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
        m = re.search(r"Gift Nifty Live price is\s*([\d,]+(?:\.\d+)?)\s*(up|down)\s*by\s*([\d,]+(?:\.\d+)?)", text, re.I)
        if not m: return None
        price = float(m.group(1).replace(",",""))
        sign = 1 if m.group(2).lower()=="up" else -1
        change = sign*float(m.group(3).replace(",",""))
        prev = price-change
        pct = change/prev*100 if prev else np.nan
        return {"price":price,"change":change,"pct":pct}
    except Exception:
        return None

@st.cache_data(ttl=180, show_spinner=False)
def get_nifty_pcr():
    # No fake/synthetic PCR: only actual option-chain OI when available.
    if nse_optionchain_scrapper is None:
        return None
    try:
        oc = nse_optionchain_scrapper("NIFTY")
        data = oc.get("records",{}).get("data",[]) if isinstance(oc,dict) else []
        ce_oi = pe_oi = 0.0
        for item in data:
            ce = item.get("CE") or {}
            pe = item.get("PE") or {}
            ce_oi += float(ce.get("openInterest") or 0)
            pe_oi += float(pe.get("openInterest") or 0)
        return pe_oi/ce_oi if ce_oi > 0 else None
    except Exception:
        return None

# =============================================================================
# INDICATORS
# =============================================================================
def enrich(df):
    x = df.copy()

    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()

    x["vol_avg20"] = x["volume"].rolling(20).mean()
    x["rvol"] = x["volume"] / x["vol_avg20"].replace(0, np.nan)

    bb_mid = x["close"].rolling(20).mean()
    bb_std = x["close"].rolling(20).std(ddof=0)
    x["bb_upper"] = bb_mid + 2 * bb_std
    x["bb_lower"] = bb_mid - 2 * bb_std
    x["bb_width"] = (x["bb_upper"] - x["bb_lower"]) / bb_mid.replace(0, np.nan)
    x["bb_width_avg"] = x["bb_width"].rolling(20).mean()

    # Intraday VWAP, resetting each session.
    session = pd.Series(x.index.date, index=x.index)
    typical = (x["high"] + x["low"] + x["close"]) / 3.0
    pv = typical * x["volume"]
    cum_vol = x["volume"].groupby(session).cumsum().replace(0, np.nan)
    x["vwap"] = pv.groupby(session).cumsum() / cum_vol

    return x

def latest_session(df):
    if df.empty:
        return df
    last_date = df.index[-1].date()
    return df[df.index.date == last_date].copy()

def previous_session_close(df):
    dates = list(pd.Index(df.index.date).unique())
    if len(dates) < 2:
        return np.nan

    prev = df[df.index.date == dates[-2]]
    return float(prev["close"].iloc[-1]) if not prev.empty else np.nan

def cross_up(a, b):
    return (
        len(a) >= 2 and len(b) >= 2
        and a.iloc[-2] <= b.iloc[-2]
        and a.iloc[-1] > b.iloc[-1]
    )

def cross_down(a, b):
    return (
        len(a) >= 2 and len(b) >= 2
        and a.iloc[-2] >= b.iloc[-2]
        and a.iloc[-1] < b.iloc[-1]
    )

def rvol_score(rvol):
    if pd.isna(rvol): return "N/A"
    if rvol >= 5: return "🔥 Explosive"
    if rvol >= 3: return "🟢 Strong"
    if rvol >= 2: return "🟡 Good"
    if rvol >= 1.5: return "⚪ Watch"
    return "Low"

def resample_ohlcv(df, rule):
    return (df.resample(rule, origin="start_day", offset="15min")
              .agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
              .dropna(subset=["close"]))

def tf_bias(df, rule=None):
    x = df if rule is None else resample_ohlcv(df, rule)
    if len(x) < 20: return "N/A"
    e = x["close"].ewm(span=20, adjust=False).mean()
    c,ev = float(x["close"].iloc[-1]), float(e.iloc[-1])
    return "BULLISH" if c > ev else ("BEARISH" if c < ev else "NEUTRAL")

def mtf_alignment(raw):
    b5,b15,b60 = tf_bias(raw), tf_bias(raw,"15min"), tf_bias(raw,"60min")
    if all(v=="BULLISH" for v in [b5,b15,b60]): align="🟢 BULLISH"
    elif all(v=="BEARISH" for v in [b5,b15,b60]): align="🔴 BEARISH"
    else: align="⚠️ MIXED"
    return b5,b15,b60,align

# =============================================================================
# ONE-STOCK SCAN
# =============================================================================
def build_row(symbol, raw, high_vol_mult, strong_move_pct,
              open_near_extreme_pct, squeeze_factor):

    x = enrich(raw)
    day = latest_session(x)

    if day.empty or len(x) < 25:
        return None

    last = x.iloc[-1]

    o = float(day["open"].iloc[0])
    h = float(day["high"].max())
    l = float(day["low"].min())
    c = float(day["close"].iloc[-1])

    prev_close = previous_session_close(x)

    move_from_open = ((c / o) - 1) * 100 if o else np.nan
    change_pct = ((c / prev_close) - 1) * 100 if pd.notna(prev_close) and prev_close else np.nan

    rvol = float(last["rvol"]) if pd.notna(last["rvol"]) else np.nan
    ema20 = float(last["ema20"]) if pd.notna(last["ema20"]) else np.nan
    vwap = float(last["vwap"]) if pd.notna(last["vwap"]) else np.nan

    # -------------------------------------------------------------------------
    # 1) 15 MINUTE OPENING RANGE BREAKOUT
    # -------------------------------------------------------------------------
    first_15m = day.between_time("09:15", "09:29")
    if first_15m.empty:
        first_15m = day.iloc[:3]

    orb_high = float(first_15m["high"].max())
    orb_low = float(first_15m["low"].min())

    if c > orb_high:
        orb = "ORB UP"
    elif c < orb_low:
        orb = "ORB DOWN"
    else:
        orb = "INSIDE"

    # -------------------------------------------------------------------------
    # 2/3) OPEN BIAS
    # -------------------------------------------------------------------------
    if c > o and c > ema20:
        if move_from_open >= strong_move_pct and rvol >= high_vol_mult and (pd.isna(vwap) or c > vwap):
            open_bias = "STRONG BULLISH"
        else:
            open_bias = "BULLISH"

    elif c < o and c < ema20:
        if move_from_open <= -strong_move_pct and rvol >= high_vol_mult and (pd.isna(vwap) or c < vwap):
            open_bias = "STRONG BEARISH"
        else:
            open_bias = "BEARISH"

    else:
        open_bias = "NEUTRAL"

    # -------------------------------------------------------------------------
    # 4/5) OPEN LOW->HIGH / HIGH->LOW WITH HIGH VOLUME
    # -------------------------------------------------------------------------
    price_tol = o * (open_near_extreme_pct / 100.0)
    day_range = max(h - l, 1e-9)
    close_position = ((c - l) / day_range) * 100

    low_to_high = (
        abs(o - l) <= price_tol
        and close_position >= 70
        and c > o
        and rvol >= high_vol_mult
    )

    high_to_low = (
        abs(h - o) <= price_tol
        and close_position <= 30
        and c < o
        and rvol >= high_vol_mult
    )

    # -------------------------------------------------------------------------
    # 6) EMA20 CROSS + HIGH VOLUME
    # -------------------------------------------------------------------------
    ema_bull = cross_up(x["close"], x["ema20"]) and rvol >= high_vol_mult
    ema_bear = cross_down(x["close"], x["ema20"]) and rvol >= high_vol_mult

    # -------------------------------------------------------------------------
    # 7) BOLLINGER SQUEEZE -> EXPANSION
    # Previous bar must be squeezed; current bar must cross outside.
    # -------------------------------------------------------------------------
    previous_bar = x.iloc[-2]

    prior_squeeze = (
        pd.notna(previous_bar["bb_width"])
        and pd.notna(previous_bar["bb_width_avg"])
        and previous_bar["bb_width"]
            <= previous_bar["bb_width_avg"] * squeeze_factor
    )

    bb_bull = prior_squeeze and cross_up(x["close"], x["bb_upper"])
    bb_bear = prior_squeeze and cross_down(x["close"], x["bb_lower"])

    # NEW add-ons. Old formulas above are untouched.
    vwap_bias = "N/A" if pd.isna(vwap) else ("BULLISH" if c > vwap else ("BEARISH" if c < vwap else "NEUTRAL"))
    rv_score = rvol_score(rvol)
    b5,b15,b60,alignment = mtf_alignment(raw)

    bull_score = bear_score = 0
    if orb == "ORB UP": bull_score += 20
    if orb == "ORB DOWN": bear_score += 20
    if pd.notna(rvol) and rvol >= 2:
        if c >= o: bull_score += 20
        else: bear_score += 20
    if ema_bull: bull_score += 15
    if ema_bear: bear_score += 15
    if bb_bull: bull_score += 15
    if bb_bear: bear_score += 15
    if vwap_bias == "BULLISH": bull_score += 10
    if vwap_bias == "BEARISH": bear_score += 10
    if alignment == "🟢 BULLISH": bull_score += 20
    if alignment == "🔴 BEARISH": bear_score += 20
    scanner_score = max(bull_score,bear_score)
    score_bias = "🟢 BULLISH" if bull_score > bear_score else ("🔴 BEARISH" if bear_score > bull_score else "⚪ NEUTRAL")
    trend_strength = ((c/ema20)-1)*100 if pd.notna(ema20) and ema20 else np.nan

    return {
        "Symbol": symbol,
        "Session": str(day.index[-1].date()),
        "Open": o,
        "High": h,
        "Low": l,
        "Close": c,
        "Prev Close": prev_close,
        "Change %": change_pct,
        "From Open %": move_from_open,
        "RVOL": rvol,
        "RVOL Score": rv_score,
        "EMA20": ema20,
        "VWAP": vwap,
        "VWAP Bias": vwap_bias,
        "ORB High": orb_high,
        "ORB Low": orb_low,
        "ORB": orb,
        "Open Bias": open_bias,
        "Low→High HV": low_to_high,
        "High→Low HV": high_to_low,
        "EMA Bull": ema_bull,
        "EMA Bear": ema_bear,
        "BB Bull": bb_bull,
        "BB Bear": bb_bear,
        "5m": b5,
        "15m": b15,
        "1H": b60,
        "MTF Alignment": alignment,
        "Scanner Score": scanner_score,
        "Score Bias": score_bias,
        "Trend Strength %": trend_strength,
        "Session Volume": float(day["volume"].sum()),
    }

def scan_universe(symbols, data_map, high_vol_mult, strong_move_pct,
                  open_near_extreme_pct, squeeze_factor):

    rows = []

    for symbol in symbols:
        raw = data_map.get(symbol)

        if raw is None or raw.empty:
            continue

        try:
            row = build_row(
                symbol,
                raw,
                high_vol_mult,
                strong_move_pct,
                open_near_extreme_pct,
                squeeze_factor,
            )

            if row:
                rows.append(row)

        except Exception:
            continue

    return pd.DataFrame(rows)

# =============================================================================
# MARKET STRENGTH LAYER — TRIN + PCR + A/D + NIFTY BREADTH
# =============================================================================
def market_strength_layer(nifty_df):
    if nifty_df.empty:
        return {"adv":0,"dec":0,"unch":0,"ad_ratio":np.nan,"breadth_pct":np.nan,"trin":np.nan,"pcr":None,"label":"N/A"}
    adv_df=nifty_df[nifty_df["Change %"]>0]; dec_df=nifty_df[nifty_df["Change %"]<0]
    adv,dec=len(adv_df),len(dec_df); unch=int((nifty_df["Change %"]==0).sum())
    ad_ratio=np.inf if dec==0 and adv>0 else (adv/dec if dec>0 else np.nan)
    breadth_pct=adv/len(nifty_df)*100 if len(nifty_df) else np.nan
    adv_vol=float(adv_df["Session Volume"].sum()) if not adv_df.empty else 0.0
    dec_vol=float(dec_df["Session Volume"].sum()) if not dec_df.empty else 0.0
    trin=np.nan
    if adv>0 and dec>0 and adv_vol>0 and dec_vol>0:
        trin=(adv/dec)/(adv_vol/dec_vol)
    pcr=get_nifty_pcr()
    score=0
    if pd.notna(breadth_pct): score += 1 if breadth_pct>=60 else (-1 if breadth_pct<=40 else 0)
    if pd.notna(ad_ratio): score += 1 if ad_ratio>=1.2 else (-1 if ad_ratio<=0.8 else 0)
    if pd.notna(trin): score += 1 if trin<=0.90 else (-1 if trin>=1.10 else 0)
    if pcr is not None: score += 1 if pcr>=1.10 else (-1 if pcr<=0.80 else 0)
    label = "STRONG BULLISH" if score>=3 else ("BULLISH" if score>=1 else ("STRONG BEARISH" if score<=-3 else ("BEARISH" if score<=-1 else "NEUTRAL")))
    return {"adv":adv,"dec":dec,"unch":unch,"ad_ratio":ad_ratio,"breadth_pct":breadth_pct,"trin":trin,"pcr":pcr,"label":label}

def fmt_num(v): return "N/A" if v is None or pd.isna(v) else f"{v:,.2f}"
def fmt_pct(v): return "N/A" if v is None or pd.isna(v) else f"{v:+.2f}%"
def live_card(title, quote=None, text=None):
    if text is not None:
        cls="pos" if "BULL" in text else ("neg" if "BEAR" in text else "neu")
        return f'<div class="live-card"><div class="live-title">{title}</div><div class="live-value {cls}">{text}</div></div>'
    if quote is None:
        return f'<div class="live-card"><div class="live-title">{title}</div><div class="live-value neu">N/A</div><div class="live-change neu">feed unavailable</div></div>'
    pct=quote.get("pct",np.nan); cls="pos" if pd.notna(pct) and pct>0 else ("neg" if pd.notna(pct) and pct<0 else "neu")
    return f'<div class="live-card"><div class="live-title">{title}</div><div class="live-value {cls}">{fmt_num(quote.get("price"))}</div><div class="live-change {cls}">{fmt_num(quote.get("change"))} &nbsp; {fmt_pct(pct)}</div></div>'

# =============================================================================
# TABLE HELPERS
# =============================================================================
def prepare_table(df, sort_by=None, ascending=False):
    if df.empty:
        return df

    x = df.copy()

    if sort_by and sort_by in x.columns:
        x = x.sort_values(sort_by, ascending=ascending)

    numeric_cols = [
        "Open","High","Low","Close","Prev Close",
        "Change %","From Open %","RVOL","EMA20","VWAP",
        "ORB High","ORB Low","Scanner Score","Trend Strength %"
    ]

    for col in numeric_cols:
        if col in x.columns:
            x[col] = pd.to_numeric(x[col], errors="coerce").round(2)

    return x

def show_table(df, columns=None, sort_by=None, ascending=False, height=610):
    if df.empty:
        st.info("Latest available session me koi matching stock nahi mila.")
        return

    x = df.copy()

    if columns:
        x = x[columns]

    x = prepare_table(x, sort_by, ascending)

    def paint(v):
        sv=str(v)
        if sv=="ORB UP" or "BULLISH" in sv: return "background-color:rgba(0,180,90,.16);color:#008f4c;font-weight:700"
        if sv=="ORB DOWN" or "BEARISH" in sv: return "background-color:rgba(220,60,60,.16);color:#c62828;font-weight:700"
        if "Explosive" in sv: return "background-color:rgba(255,90,0,.18);font-weight:800"
        if "Strong" in sv: return "background-color:rgba(0,180,90,.13);font-weight:700"
        if "Good" in sv: return "background-color:rgba(230,190,0,.17);font-weight:700"
        return ""
    styled=x.style
    for col in ["ORB","VWAP Bias","Open Bias","MTF Alignment","Score Bias","State","RVOL Score"]:
        if col in x.columns: styled=styled.map(paint, subset=[col])
    for col in ["Change %","From Open %","Trend Strength %"]:
        if col in x.columns:
            styled=styled.map(lambda v: "color:#008f4c;font-weight:700" if pd.notna(v) and float(v)>0 else ("color:#c62828;font-weight:700" if pd.notna(v) and float(v)<0 else ""), subset=[col])
    st.dataframe(styled,use_container_width=True,hide_index=True,height=height)

# =============================================================================
# SIDEBAR
# =============================================================================
st.title("📈 NSE Fast Scanner — 10 Tabs")

with st.sidebar:
    st.header("Scanner Settings")

    refresh_seconds = st.selectbox(
        "Auto refresh",
        [30, 45, 60, 120],
        index=1,
        format_func=lambda x: f"{x} sec",
    )

    fo_limit = st.number_input(
        "F&O stocks to scan",
        min_value=10,
        max_value=250,
        value=180,
        step=10,
    )

    high_vol_mult = st.number_input(
        "High Volume Multiplier",
        min_value=1.0,
        max_value=5.0,
        value=1.50,
        step=0.10,
    )

    strong_move_pct = st.number_input(
        "Strong Bull/Bear % from Open",
        min_value=0.10,
        max_value=5.0,
        value=0.75,
        step=0.05,
    )

    open_near_extreme_pct = st.number_input(
        "Open near High/Low tolerance %",
        min_value=0.05,
        max_value=2.0,
        value=0.25,
        step=0.05,
    )

    squeeze_factor = st.number_input(
        "BB Squeeze Factor",
        min_value=0.30,
        max_value=1.20,
        value=0.80,
        step=0.05,
    )

    nifty_fut_ticker = st.text_input(
        "Yahoo NIFTY Future ticker", value="NIFTY=F",
        help="If unavailable in your Yahoo region, card shows N/A. No fake fallback."
    )

    if st.button("Refresh Now", use_container_width=True):
        st.cache_data.clear()

    st.caption(
        "Market close hone ke baad scanner latest completed trading session use karega."
    )

if st_autorefresh is not None:
    st_autorefresh(
        interval=int(refresh_seconds * 1000),
        key="nse_scanner_autorefresh",
    )

# =============================================================================
# LOAD DATA
# =============================================================================
fo_symbols = get_fo_symbols(int(fo_limit))
nifty50_symbols = NIFTY50_FALLBACK.copy()

all_symbols = list(dict.fromkeys(fo_symbols + nifty50_symbols))

with st.spinner(f"{len(all_symbols)} symbols scan ho rahe hain..."):
    data_map = fetch_intraday(tuple(all_symbols))

fo_df = scan_universe(
    fo_symbols,
    data_map,
    high_vol_mult,
    strong_move_pct,
    open_near_extreme_pct,
    squeeze_factor,
)

nifty_df = scan_universe(
    nifty50_symbols,
    data_map,
    high_vol_mult,
    strong_move_pct,
    open_near_extreme_pct,
    squeeze_factor,
)

strength = market_strength_layer(nifty_df)
nifty_quote = yahoo_live_quote("^NSEI")
fut_quote = yahoo_live_quote(nifty_fut_ticker.strip()) if nifty_fut_ticker.strip() else None
gift_quote = gift_nifty_live()

st.markdown(
    '<div class="live-strip">'
    + live_card("MARKET STRENGTH", text=strength["label"])
    + live_card("NIFTY 50", quote=nifty_quote)
    + live_card("NIFTY FUTURE", quote=fut_quote)
    + live_card("GIFT NIFTY*", quote=gift_quote)
    + '</div>',
    unsafe_allow_html=True,
)

pcr_txt = "N/A" if strength["pcr"] is None else f'{strength["pcr"]:.2f}'
trin_txt = "N/A" if pd.isna(strength["trin"]) else f'{strength["trin"]:.2f}'
ad_txt = "∞" if np.isinf(strength["ad_ratio"]) else ("N/A" if pd.isna(strength["ad_ratio"]) else f'{strength["ad_ratio"]:.2f}')
breadth_txt = "N/A" if pd.isna(strength["breadth_pct"]) else f'{strength["breadth_pct"]:.1f}%'
st.caption(f'Market Strength Layer → TRIN: {trin_txt} | PCR: {pcr_txt} | A/D: {ad_txt} | NIFTY Breadth: {breadth_txt} | Adv {strength["adv"]} / Dec {strength["dec"]}')

# =============================================================================
# TOP STATUS
# =============================================================================
status = market_status()

latest_session_name = (
    fo_df["Session"].max()
    if not fo_df.empty and "Session" in fo_df.columns
    else "-"
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Market", status)
m2.metric("Latest Session", latest_session_name)
m3.metric("F&O Loaded", f"{len(fo_df)} / {len(fo_symbols)}")
m4.metric("NIFTY50 Loaded", f"{len(nifty_df)} / 50")

if status == "CLOSED":
    st.info(
        "NSE market CLOSED hai. Scanner band nahi hoga — latest available completed-session data dikha raha hai."
    )

# =============================================================================
# 8 TABS
# =============================================================================
tabs = st.tabs([
    "1️⃣ ORB 15m",
    "2️⃣ Bullish Open",
    "3️⃣ Bearish Open",
    "4️⃣ Low → High HV",
    "5️⃣ High → Low HV",
    "6️⃣ EMA20 + Volume",
    "7️⃣ BB Squeeze",
    "8️⃣ NIFTY50 Breadth",
    "9️⃣ MTF + Score",
    "🔟 Sector Heatmap",
])

# -----------------------------------------------------------------------------
# TAB 1
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("15-Minute Opening Range Breakout")

    if not fo_df.empty:
        x = fo_df[fo_df["ORB"].isin(["ORB UP", "ORB DOWN"])]
    else:
        x = fo_df

    show_table(
        x,
        ["Symbol","Session","ORB","Close","ORB High","ORB Low","Change %","RVOL","RVOL Score","VWAP","VWAP Bias"],
        "RVOL",
        False,
    )

# -----------------------------------------------------------------------------
# TAB 2
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Bullish / Strong Bullish")

    if not fo_df.empty:
        x = fo_df[
            fo_df["Open Bias"].isin(["BULLISH", "STRONG BULLISH"])
        ]
    else:
        x = fo_df

    show_table(
        x,
        ["Symbol","Session","Open Bias","Open","High","Low","Close",
         "From Open %","Change %","RVOL","EMA20","VWAP"],
        "From Open %",
        False,
    )

# -----------------------------------------------------------------------------
# TAB 3
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Bearish / Strong Bearish")

    if not fo_df.empty:
        x = fo_df[
            fo_df["Open Bias"].isin(["BEARISH", "STRONG BEARISH"])
        ]
    else:
        x = fo_df

    show_table(
        x,
        ["Symbol","Session","Open Bias","Open","High","Low","Close",
         "From Open %","Change %","RVOL","EMA20","VWAP"],
        "From Open %",
        True,
    )

# -----------------------------------------------------------------------------
# TAB 4
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Open Near Low → High + High Volume")

    x = fo_df[fo_df["Low→High HV"]] if not fo_df.empty else fo_df

    show_table(
        x,
        ["Symbol","Session","Open","Low","High","Close",
         "From Open %","Change %","RVOL"],
        "RVOL",
        False,
    )

# -----------------------------------------------------------------------------
# TAB 5
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Open Near High → Low + High Volume")

    x = fo_df[fo_df["High→Low HV"]] if not fo_df.empty else fo_df

    show_table(
        x,
        ["Symbol","Session","Open","High","Low","Close",
         "From Open %","Change %","RVOL"],
        "RVOL",
        False,
    )

# -----------------------------------------------------------------------------
# TAB 6
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("EMA20 Cross + High Volume")

    left, right = st.columns(2)

    with left:
        st.markdown("### 🟢 Bullish")
        st.caption("Close crosses ABOVE EMA20 + High Volume")

        x = fo_df[fo_df["EMA Bull"]] if not fo_df.empty else fo_df

        show_table(
            x,
            ["Symbol","Session","Close","EMA20","RVOL",
             "Change %","From Open %"],
            "RVOL",
            False,
            500,
        )

    with right:
        st.markdown("### 🔴 Bearish")
        st.caption("Close crosses BELOW EMA20 + High Volume")

        x = fo_df[fo_df["EMA Bear"]] if not fo_df.empty else fo_df

        show_table(
            x,
            ["Symbol","Session","Close","EMA20","RVOL",
             "Change %","From Open %"],
            "RVOL",
            False,
            500,
        )

# -----------------------------------------------------------------------------
# TAB 7
# -----------------------------------------------------------------------------
with tabs[6]:
    st.subheader("Bollinger Band Squeeze → Volatility Expansion")

    left, right = st.columns(2)

    with left:
        st.markdown("### 🟢 Bullish")
        st.caption("Previous bar squeeze + Current price crosses Upper Band")

        x = fo_df[fo_df["BB Bull"]] if not fo_df.empty else fo_df

        show_table(
            x,
            ["Symbol","Session","Close","RVOL","Change %","From Open %"],
            "RVOL",
            False,
            500,
        )

    with right:
        st.markdown("### 🔴 Bearish")
        st.caption("Previous bar squeeze + Current price crosses Lower Band")

        x = fo_df[fo_df["BB Bear"]] if not fo_df.empty else fo_df

        show_table(
            x,
            ["Symbol","Session","Close","RVOL","Change %","From Open %"],
            "RVOL",
            False,
            500,
        )

# -----------------------------------------------------------------------------
# TAB 8
# -----------------------------------------------------------------------------
with tabs[7]:
    st.subheader("NIFTY 50 — OHLC + Breadth + Trend Strength")
    if nifty_df.empty:
        st.info("NIFTY50 data abhi load nahi hua.")
    else:
        breadth=nifty_df[["Symbol","Session","Open","High","Low","Close","Prev Close","Change %","Trend Strength %"]].copy()
        breadth["State"]=np.where(breadth["Change %"]>0,"BULLISH",np.where(breadth["Change %"]<0,"BEARISH","UNCHANGED"))
        b1,b2,b3,b4=st.columns(4)
        b1.metric("Advances",strength["adv"]); b2.metric("Declines",strength["dec"]); b3.metric("TRIN",trin_txt); b4.metric("A/D Ratio",ad_txt)
        st.markdown(f'### Market Breadth: **{strength["label"]}**')
        show_table(breadth,["Symbol","Session","State","Open","High","Low","Close","Prev Close","Change %","Trend Strength %"],"Change %",False,720)

# -----------------------------------------------------------------------------
# TAB 9
# -----------------------------------------------------------------------------
with tabs[8]:
    st.subheader("MTF Alignment + Scanner Score Engine")
    st.caption("5m / 15m / 1H alignment. Score 0–100. Old scanner signals unchanged.")
    if fo_df.empty:
        st.info("Data unavailable.")
    else:
        x=fo_df[["Symbol","Session","5m","15m","1H","MTF Alignment","Scanner Score","Score Bias","RVOL","RVOL Score","VWAP Bias","ORB","Change %"]].copy()
        show_table(x,None,"Scanner Score",False,720)

# -----------------------------------------------------------------------------
# TAB 10
# -----------------------------------------------------------------------------
with tabs[9]:
    st.subheader("Sector Heatmap — NIFTY 50")
    st.caption("Sector % = simple average Change % of loaded members. Two stocks = top 2 movers by absolute % in that sector.")
    if nifty_df.empty:
        st.info("NIFTY50 data unavailable.")
    else:
        sec=nifty_df[["Symbol","Change %"]].copy(); sec["Sector"]=sec["Symbol"].map(SECTOR_MAP).fillna("OTHER")
        cards=[]
        for sector,grp in sec.groupby("Sector"):
            avg=float(grp["Change %"].mean())
            movers=grp.assign(abs_move=grp["Change %"].abs()).sort_values("abs_move",ascending=False).head(2)
            stocks=" | ".join(f'{r["Symbol"]} {r["Change %"]:+.2f}%' for _,r in movers.iterrows())
            if avg>0: bg,cls="rgba(0,180,90,.16)","pos"
            elif avg<0: bg,cls="rgba(220,60,60,.16)","neg"
            else: bg,cls="rgba(150,150,150,.10)","neu"
            cards.append(f'<div class="sector-card" style="background:{bg}"><div class="sector-name">{sector}</div><div class="sector-pct {cls}">{avg:+.2f}%</div><div class="sector-stocks">{stocks}</div></div>')
        st.markdown('<div class="sector-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.caption(
    "Free stock/NIFTY data layer: Yahoo Finance (may be delayed). "
    "GIFT NIFTY is best-effort from a third-party public page and may show N/A if blocked. "
    "PCR is shown only when actual NSE option-chain OI is available through nsepython; no synthetic PCR is invented. "
    "Old scanner formulas are preserved; new modules are add-ons."
)
