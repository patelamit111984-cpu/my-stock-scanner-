import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from datetime import time as dtime

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

try:
    from nsepython import fnolist
except Exception:
    fnolist = None

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
        "EMA20": ema20,
        "VWAP": vwap,
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
        "ORB High","ORB Low"
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

    st.dataframe(
        x,
        use_container_width=True,
        hide_index=True,
        height=height,
    )

# =============================================================================
# SIDEBAR
# =============================================================================
st.title("📈 NSE Fast Scanner — 8 Tabs")

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
        ["Symbol","Session","ORB","Close","ORB High","ORB Low","Change %","RVOL"],
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
    st.subheader("NIFTY 50 — OHLC + Bullish/Bearish + Advance/Decline")

    if nifty_df.empty:
        st.info("NIFTY50 data abhi load nahi hua.")
    else:
        breadth = nifty_df[
            ["Symbol","Session","Open","High","Low","Close","Prev Close","Change %"]
        ].copy()

        breadth["State"] = np.where(
            breadth["Change %"] > 0,
            "BULLISH",
            np.where(
                breadth["Change %"] < 0,
                "BEARISH",
                "UNCHANGED"
            ),
        )

        advances = int((breadth["Change %"] > 0).sum())
        declines = int((breadth["Change %"] < 0).sum())
        unchanged = int((breadth["Change %"] == 0).sum())

        ad_ratio = np.inf if declines == 0 else advances / declines

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Advances", advances)
        b2.metric("Declines", declines)
        b3.metric("Unchanged", unchanged)
        b4.metric(
            "A/D Ratio",
            "∞" if np.isinf(ad_ratio) else f"{ad_ratio:.2f}"
        )

        if np.isinf(ad_ratio) or ad_ratio >= 2:
            breadth_text = "STRONG BULLISH"
        elif ad_ratio > 1:
            breadth_text = "BULLISH"
        elif ad_ratio == 1:
            breadth_text = "NEUTRAL"
        elif ad_ratio >= 0.5:
            breadth_text = "BEARISH"
        else:
            breadth_text = "STRONG BEARISH"

        st.markdown(f"### Market Breadth: **{breadth_text}**")

        breadth = prepare_table(
            breadth.sort_values("Change %", ascending=False)
        )

        def row_colour(row):
            val = row.get("Change %", np.nan)

            if pd.isna(val):
                return [""] * len(row)

            if val > 0:
                return ["background-color: rgba(0,180,90,0.16)"] * len(row)

            if val < 0:
                return ["background-color: rgba(220,60,60,0.16)"] * len(row)

            return [""] * len(row)

        st.dataframe(
            breadth.style.apply(row_colour, axis=1),
            use_container_width=True,
            hide_index=True,
            height=720,
        )

# =============================================================================
# FOOTER
# =============================================================================
st.caption(
    "Free data layer: Yahoo Finance (yfinance). It is useful for a free scanner, "
    "but it is not an official guaranteed real-time NSE exchange feed. "
    "Later, broker/vendor WebSocket can replace only the fetch layer without "
    "changing these scanner formulas."
)
