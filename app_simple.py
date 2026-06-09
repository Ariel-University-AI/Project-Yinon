"""
יועץ נדל"ן חכם — גרסה מפושטת
Run:  streamlit run app_simple.py
"""
import pathlib
import datetime
import re
import json
import requests
import numpy as np
import pandas as pd
import joblib
import plotly.express as px
import streamlit as st

BASE          = pathlib.Path(__file__).parent
MODEL_PATH    = BASE / "model.pkl"
APT_ML_PATH   = BASE / "DATA_FILES" / "apartments_ml_ready.csv"
APT_DISP_PATH = BASE / "DATA_FILES" / "apartments_display.csv"
POI_PATH      = BASE / "DATA_FILES" / "ISRAEL_POINTS_FILTERED_GEO.csv"

st.set_page_config(
    page_title='יועץ נדל"ן חכם',
    layout="wide",
    page_icon="🏠",
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Hebrew:wght@300;400;700;900&family=Rubik:wght@300;400;500;700;900&display=swap');

/* ── Design Tokens ───────────────────────────────────────────────────── */
:root {
  --brand-900: oklch(18% 0.09 155);
  --brand-700: oklch(27% 0.12 155);
  --brand-500: oklch(40% 0.14 155);
  --brand-400: oklch(50% 0.15 155);
  --brand-200: oklch(88% 0.06 155);
  --brand-100: oklch(96% 0.015 155);
  --ink-900:   oklch(13% 0.015 155);
  --ink-700:   oklch(28% 0.025 155);
  --ink-500:   oklch(45% 0.03 155);
  --ink-400:   oklch(56% 0.03 155);
  --ink-200:   oklch(82% 0.018 155);
  --ink-100:   oklch(95% 0.01 155);
  --good:      oklch(50% 0.16 148);
  --good-bg:   oklch(95% 0.04 148);
  --fair:      oklch(68% 0.14 78);
  --fair-bg:   oklch(96% 0.04 78);
  --bad:       oklch(52% 0.16 25);
  --bad-bg:    oklch(96% 0.04 25);
  --bg:        oklch(99.5% 0.003 155);
  --surface:   oklch(97% 0.008 155);
  --font-display: 'Noto Serif Hebrew', Georgia, serif;
  --font-body:    'Rubik', system-ui, sans-serif;
  --r-sm: 4px;
  --r-md: 8px;
  --r-lg: 14px;
}

/* ── Font & Base ─────────────────────────────────────────────────────── */
.stApp, body {
  background-color: var(--bg) !important;
  font-family: var(--font-body) !important;
  color: var(--ink-900) !important;
  -webkit-font-smoothing: antialiased;
}

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--ink-100); }
::-webkit-scrollbar-thumb { background: var(--brand-500); border-radius: 3px; }

/* ── Page container ──────────────────────────────────────────────────── */
.block-container { padding-top: 1rem; padding-bottom: 2rem; }

/* ── Display font for headings ───────────────────────────────────────── */
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
  font-family: var(--font-display) !important;
  font-weight: 300 !important;
  letter-spacing: -0.01em !important;
  line-height: 1.4 !important;
  overflow: visible !important;
  padding-bottom: 0.06em !important;
}
.stMarkdown { overflow: visible !important; }

/* ── Metrics ─────────────────────────────────────────────────────────── */
[data-testid="stMetricValue"] {
  font-size: 1.5rem !important;
  font-weight: 700 !important;
  color: var(--ink-900) !important;
}
[data-testid="stMetricLabel"] {
  font-size: .8rem !important;
  color: var(--ink-500) !important;
  font-weight: 500 !important;
}
[data-testid="metric-container"] {
  background: #fff;
  border: 1.5px solid var(--ink-200);
  border-radius: var(--r-md);
  padding: 16px 20px;
  box-shadow: 0 2px 8px oklch(13% 0.015 155 / 0.04);
  transition: box-shadow 0.22s ease, border-color 0.22s ease;
}
[data-testid="metric-container"]:hover {
  box-shadow: 0 4px 16px oklch(27% 0.12 155 / 0.10);
  border-color: var(--brand-400);
}

/* ── Labels ──────────────────────────────────────────────────────────── */
label { font-weight: 600 !important; color: var(--ink-700) !important; }

/* ── Verdict boxes ───────────────────────────────────────────────────── */
.verdict-good {
  background: var(--good-bg);
  border: 2px solid var(--good);
  border-radius: var(--r-lg);
  padding: 28px 32px;
  text-align: center;
  margin: 16px 0;
  box-shadow: 0 2px 8px oklch(50% 0.16 148 / 0.10);
}
.verdict-ok {
  background: var(--fair-bg);
  border: 2px solid var(--fair);
  border-radius: var(--r-lg);
  padding: 28px 32px;
  text-align: center;
  margin: 16px 0;
  box-shadow: 0 2px 8px oklch(68% 0.14 78 / 0.10);
}
.verdict-bad {
  background: var(--bad-bg);
  border: 2px solid var(--bad);
  border-radius: var(--r-lg);
  padding: 28px 32px;
  text-align: center;
  margin: 16px 0;
  box-shadow: 0 2px 8px oklch(52% 0.16 25 / 0.10);
}

/* ── Cards / bordered containers ─────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-radius: var(--r-md) !important;
  border-color: var(--ink-200) !important;
  box-shadow: 0 2px 8px oklch(13% 0.015 155 / 0.04) !important;
  background: #fff !important;
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  transition: box-shadow 0.25s ease, border-color 0.25s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
  box-shadow: 0 4px 20px oklch(27% 0.12 155 / 0.12) !important;
  border-color: var(--brand-400) !important;
}

/* ── Equal height + hover-expand for card rows ───────────────────────── */
[data-testid="stHorizontalBlock"] {
  align-items: stretch !important;
}
[data-testid="column"]:has([data-testid="stVerticalBlockBorderWrapper"]) {
  transition: flex-grow 0.35s ease !important;
  flex-grow: 1 !important;
}
[data-testid="column"]:has([data-testid="stVerticalBlockBorderWrapper"]):hover {
  flex-grow: 1.8 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
  height: 100% !important;
}
/* Push button to bottom of card */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"] {
  margin-top: auto !important;
  padding-top: 12px !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
  border-radius: var(--r-md) !important;
  font-weight: 500 !important;
  font-family: var(--font-body) !important;
  transition: background 0.18s, border-color 0.18s,
              transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {
  background-color: var(--brand-700) !important;
  border-color: var(--brand-700) !important;
  color: #fff !important;
  font-weight: 600 !important;
}
[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
  background-color: var(--brand-900) !important;
  border-color: var(--brand-900) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px oklch(18% 0.09 155 / 0.25) !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: #fff !important;
  border-left: 1.5px solid var(--ink-200) !important;
}

/* ── GLOBAL RTL ──────────────────────────────────────────────────────── */
section[data-testid="stMain"],
section[data-testid="stMain"] * {
  direction: rtl !important;
  text-align: right !important;
}

/* ── LTR exceptions ──────────────────────────────────────────────────── */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
  direction: ltr !important;
  text-align: left !important;
}
.js-plotly-plot, .js-plotly-plot *, iframe,
[data-testid="stIFrame"]          { direction: ltr !important; }
[data-baseweb="slider"] [role="slider"] { direction: ltr !important; }
[data-testid="stDataFrameContainer"],
[data-testid="stDataFrameContainer"] * { direction: ltr !important; text-align: left !important; }

/* ═══════════════════════════════════════════════════════════════════════
   MOTION SYSTEM
   Brand: honest, analytical, direct — motion earns trust through
   clarity, not decoration. 200–400ms ease-out-expo, no bounce.
   ═══════════════════════════════════════════════════════════════════════ */

:root {
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes ag-fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes ag-fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes ag-reveal {
  from { opacity: 0; transform: translateY(8px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Page entrance: the whole content area fades in ────────────────── */
.block-container {
  animation: ag-fade-in 300ms var(--ease-out-expo) both;
}

/* ── Headings: gentle slide-down entrance ───────────────────────────── */
h1, .stMarkdown h1 {
  animation: ag-fade-up 360ms var(--ease-out-expo) 30ms both;
}
h2, .stMarkdown h2 {
  animation: ag-fade-up 300ms var(--ease-out-expo) 40ms both;
}

/* ── Feature / nav cards: staggered entrance ────────────────────────── */
[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"])
  [data-testid="column"]:nth-child(1) [data-testid="stVerticalBlockBorderWrapper"] {
  animation: ag-fade-up 420ms var(--ease-out-expo) 60ms both;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"])
  [data-testid="column"]:nth-child(2) [data-testid="stVerticalBlockBorderWrapper"] {
  animation: ag-fade-up 420ms var(--ease-out-expo) 130ms both;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"])
  [data-testid="column"]:nth-child(3) [data-testid="stVerticalBlockBorderWrapper"] {
  animation: ag-fade-up 420ms var(--ease-out-expo) 200ms both;
}

/* ── Metric cards: staggered entrance per row ───────────────────────── */
[data-testid="stHorizontalBlock"]:has([data-testid="metric-container"])
  [data-testid="column"]:nth-child(1) [data-testid="metric-container"] {
  animation: ag-fade-up 280ms var(--ease-out-expo) 0ms both;
}
[data-testid="stHorizontalBlock"]:has([data-testid="metric-container"])
  [data-testid="column"]:nth-child(2) [data-testid="metric-container"] {
  animation: ag-fade-up 280ms var(--ease-out-expo) 55ms both;
}
[data-testid="stHorizontalBlock"]:has([data-testid="metric-container"])
  [data-testid="column"]:nth-child(3) [data-testid="metric-container"] {
  animation: ag-fade-up 280ms var(--ease-out-expo) 110ms both;
}

/* ── Verdict box: the hero reveal — the moment that matters most ─────── */
.verdict-good, .verdict-ok, .verdict-bad {
  animation: ag-reveal 400ms var(--ease-out-expo) both;
}

/* ── Alert / info / warning boxes ──────────────────────────────────── */
[data-testid="stAlert"] {
  animation: ag-fade-up 260ms var(--ease-out-expo) 80ms both;
}

/* ── Expander content: fade up when opened ──────────────────────────── */
[data-testid="stExpanderDetails"] {
  animation: ag-fade-up 220ms var(--ease-out-quart) both;
}

/* ── Sidebar: fade in on first load ─────────────────────────────────── */
[data-testid="stSidebar"] {
  animation: ag-fade-in 450ms var(--ease-out-quart) both;
}

/* ── Button press: tactile feedback ─────────────────────────────────── */
.stButton > button:active {
  transform: translateY(0) scale(0.96) !important;
  transition: transform 80ms ease !important;
}

/* ── Reduced motion: WCAG 2.1 AA compliance ─────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)


# ── helper: render a block of Hebrew HTML right-to-left ───────────────────────
def rtl(html: str, extra_style: str = "") -> None:
    st.markdown(
        f'<div dir="rtl" style="text-align:right;line-height:1.8;font-size:0.95rem;{extra_style}">'
        f'{html}</div>',
        unsafe_allow_html=True,
    )


# ─── Cached loaders ────────────────────────────────────────────────────────────

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_data():
    df_ml = pd.read_csv(APT_ML_PATH,   encoding="utf-8-sig")
    df_d  = pd.read_csv(APT_DISP_PATH, encoding="utf-8-sig")
    return df_ml, df_d


@st.cache_data
def compute_predictions():
    mdl   = joblib.load(str(MODEL_PATH))
    df_ml = pd.read_csv(str(APT_ML_PATH),   encoding="utf-8-sig")
    df_d  = pd.read_csv(str(APT_DISP_PATH), encoding="utf-8-sig")
    X     = df_ml.drop(columns=["dealAmount"])
    df_d  = df_d.copy()
    df_d["predicted"]       = mdl.predict(X)
    df_d["gap_pct"]         = (df_d["predicted"] - df_d["dealAmount"]) / df_d["dealAmount"] * 100
    df_d["viability_score"] = (50 + df_d["gap_pct"] * 1.5).clip(0, 100).round(1)
    return df_d


@st.cache_data
def compute_area_stats():
    mdl   = joblib.load(str(MODEL_PATH))
    df_ml = pd.read_csv(str(APT_ML_PATH),   encoding="utf-8-sig")
    df_d  = pd.read_csv(str(APT_DISP_PATH), encoding="utf-8-sig")
    X     = df_ml.drop(columns=["dealAmount"])
    df_d  = df_d.copy()
    df_d["predicted"] = mdl.predict(X)
    df_d["gap_pct"]   = (df_d["predicted"] - df_d["dealAmount"]) / df_d["dealAmount"] * 100

    def _trend(g):
        if g["deal_year"].nunique() < 2:
            return 0.0
        slope = np.polyfit(g["deal_year"].values, g["dealAmount"].values, 1)[0]
        return float(round(slope / g["dealAmount"].mean() * 100, 2))

    try:
        trend_s = df_d.groupby("settlementNameHeb").apply(_trend, include_groups=False)
    except TypeError:
        trend_s = df_d.groupby("settlementNameHeb").apply(_trend)
    trend_s = trend_s.rename("trend_pct_yr")

    stats = df_d.groupby("settlementNameHeb").agg(
        avg_price  = ("dealAmount",      "mean"),
        avg_gap    = ("gap_pct",         "mean"),
        deal_count = ("dealAmount",      "count"),
        avg_socio  = ("socio_index_avg", "mean"),
    ).join(trend_s).reset_index()
    return stats


@st.cache_data
def get_baselines():
    df_ml = pd.read_csv(str(APT_ML_PATH),   encoding="utf-8-sig")
    df_d  = pd.read_csv(str(APT_DISP_PATH), encoding="utf-8-sig")
    df_ml = df_ml.copy()
    df_ml["settlementNameHeb"] = df_d["settlementNameHeb"]
    return df_ml.groupby("settlementNameHeb").median()


# ─── URL scraping helpers (ported from app.py) ────────────────────────────────

_YAD2_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _get_num(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None:
            try:
                return float(str(v).replace(",", "").replace(" ", "").replace("\xa0", ""))
            except (ValueError, TypeError):
                pass
    return None


def _get_str(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v and isinstance(v, str):
            return v.strip()
    return None


def _meta(html: str, prop: str):
    m = re.search(
        rf'<meta[^>]+(?:property|name)=["\'](?:og:)?{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    ) or re.search(
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:)?{re.escape(prop)}["\']',
        html, re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def _parse_yad2_html(html: str) -> dict:
    """Parse Yad2 listing HTML → data dict (used by scraper + manual paste)."""
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        raw = html.strip()
        if raw.startswith("{"):
            try:
                json.loads(raw)
                m = type("_M", (), {"group": lambda self, i: raw})()
            except json.JSONDecodeError:
                pass
    if not m:
        # Fallback: extract from meta tags
        title = _meta(html, "title") or ""
        desc  = _meta(html, "description") or ""
        combined = title + " " + desc
        rm = re.search(r'(\d+(?:\.\d)?)\s*חדרים', combined)
        rooms = float(rm.group(1)) if rm else None
        parts = [p.strip() for p in title.split(",")]
        city = hood = street = house_num = None
        if len(parts) >= 5:
            street_raw = parts[1]
            hood = parts[3]
            city = parts[4].split("|")[0].strip()
            sm = re.match(r'^(.+?)\s+(\d+)$', street_raw)
            street   = sm.group(1).strip() if sm else street_raw.strip()
            house_num = sm.group(2) if sm else None
        elif len(parts) >= 4:
            street_raw = parts[1]
            hood = parts[2]
            city = parts[3].split("|")[0].strip()
            sm = re.match(r'^(.+?)\s+(\d+)$', street_raw)
            street   = sm.group(1).strip() if sm else street_raw.strip()
            house_num = sm.group(2) if sm else None
        if rooms or city:
            return {"price": None, "rooms": rooms, "area": None, "floor": None,
                    "city": city, "neighborhood": hood, "street": street,
                    "house_num": house_num, "lat": None, "lon": None,
                    "error": "נמצאו פרטים חלקיים — חסר מחיר, השלם ידנית.", "needs_manual": True}
        return {"error": "לא נמצא __NEXT_DATA__ — ודא שהדבקת את קוד המקור המלא (Ctrl+U → Ctrl+A → Ctrl+C).", "needs_manual": True}

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"error": "שגיאה בפענוח JSON.", "needs_manual": True}

    pp      = data.get("props", {}).get("pageProps", {})
    listing = None
    try:
        listing = pp["dehydratedState"]["queries"][0]["state"]["data"]
    except (KeyError, IndexError, TypeError):
        pass
    if not listing:
        for path in [["listing"], ["item"], ["itemData"], ["listingData"], ["ad"]]:
            try:
                obj = pp
                for k in path:
                    obj = obj[k]
                if isinstance(obj, dict) and ("price" in obj or "priceOnly" in obj):
                    listing = obj; break
            except (KeyError, TypeError):
                continue
    if not listing:
        return {"error": "מבנה הנתונים לא מוכר.", "needs_manual": True}

    price = _get_num(listing, "price", "priceOnly", "priceFormatted")
    addr  = listing.get("address") or {}
    add_d = listing.get("additionalDetails") or {}
    inp   = listing.get("inProperty") or {}

    def _txt(d, *keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, dict):
                t = v.get("text") or v.get("textHeb")
                if t and isinstance(t, str): return t.strip()
            if v and isinstance(v, str): return v.strip()
        return None

    city   = _txt(addr, "city")   or _get_str(listing, "city", "cityHeb")
    street = _txt(addr, "street") or _get_str(listing, "street", "streetHeb")
    hood   = _txt(addr, "neighborhood") or _get_str(listing, "neighborhood")
    house  = addr.get("house") or {}
    floor  = (_get_num(house, "floor") or _get_num(add_d, "floor", "floorFormatted") or _get_num(listing, "floor"))
    rooms  = (_get_num(add_d, "roomsCount", "rooms", "roomNum") or _get_num(inp, "rooms") or _get_num(listing, "rooms", "roomNum"))
    area   = (_get_num(add_d, "squareMeter", "area", "meter") or _get_num(inp, "squareMeter", "area") or _get_num(listing, "squareMeter", "area", "meter"))
    coords_d = addr.get("coords") or {}
    lat = coords_d.get("lat")
    lon = coords_d.get("lon")
    # House number — try address.house.number / address.houseNum / listing.houseNum
    _hn = (_get_num(house, "number") or _get_num(addr, "houseNum", "houseNumber")
           or _get_num(listing, "houseNum", "houseNumber"))
    house_num = str(int(_hn)) if _hn is not None else (_get_str(house, "number") or _get_str(addr, "houseNum"))
    if not price:
        return {"error": "לא נמצא מחיר במודעה.", "needs_manual": True}
    return {"price": price, "rooms": rooms, "area": area, "floor": floor,
            "city": city, "neighborhood": hood, "street": street,
            "house_num": house_num, "lat": lat, "lon": lon}


def scrape_yad2_listing(url: str) -> dict:
    """Fetch a YAD2 item page using curl_cffi Chrome impersonation."""
    if not re.search(r"yad2\.co\.il/.*item/", url):
        return {"error": "הקישור אינו תקין — חייב להיות קישור לנכס ב-yad2.co.il", "needs_manual": False}
    import time as _time
    _extra = {
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site", "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    html = None
    try:
        from curl_cffi import requests as _cr
        for _attempt, _ver in enumerate(["chrome133", "chrome131", "chrome124", "chrome120", "chrome116"]):
            try:
                if _attempt: _time.sleep(1.5)
                s = _cr.Session(impersonate=_ver)
                s.headers.update(_extra)
                resp = s.get(url, timeout=25)
                if resp.status_code == 200 and len(resp.text) > 5000:
                    html = resp.text; break
            except Exception:
                continue
    except ImportError:
        pass
    if html is None:
        try:
            resp = requests.get(url, headers={**_YAD2_HEADERS, **_extra}, timeout=15)
            html = resp.text
        except Exception:
            return {"error": "שגיאת חיבור — בדוק חיבור לאינטרנט.", "needs_manual": True}
    return _parse_yad2_html(html)


_HEB_FLOOR_ORDINALS = {
    "ראשונה": 1, "ראשון": 1, "שנייה": 2, "שני": 2, "שלישית": 3, "שלישי": 3,
    "רביעית": 4, "רביעי": 4, "חמישית": 5, "חמישי": 5, "שישית": 6, "שישי": 6,
    "שביעית": 7, "שביעי": 7, "שמינית": 8, "שמיני": 8, "קרקע": 0,
}

_HEB_CITIES = [
    "תל אביב", "ירושלים", "חיפה", "ראשון לציון", "פתח תקווה", "אשדוד",
    "נתניה", "באר שבע", "בני ברק", "רמת גן", "בת ים", "חולון", "אשקלון",
    "רחובות", "הרצליה", "כפר סבא", "מודיעין", "לוד", "רמלה", "נהריה",
    "רעננה", "גבעתיים", "עכו", "אילת", "טבריה", "צפת", "חדרה",
    "יהוד", "אור יהודה", "גבעת שמואל", "רמת השרון", "הוד השרון", "גדרה",
    "ראש העין", "קריית גת", "קריית שמונה", "אריאל", "מעלה אדומים",
]


def _parse_realestate_text(text: str) -> dict:
    """Extract price/rooms/area/floor/city from free-text Israeli real-estate description."""
    text = (text
        .replace("״", '"').replace("׳", "'").replace("’", "'").replace("‘", "'")
        .replace("“", '"').replace("”", '"').replace(" ", " ")
        .replace("–", "-").replace("—", "-")
    )
    price = None
    for pat in [
        r'([\d]{1,3}(?:,[\d]{3})+)\s*₪', r'₪\s*([\d]{1,3}(?:,[\d]{3})+)',
        r'([\d]{4,7})\s*₪',               r'₪\s*([\d]{4,7})',
        r'([\d]{1,3}(?:,[\d]{3})+)\s*שקל', r'מחיר[:\s]*([\d,]+)',
        r'(?:^|[-—|\s])([\d]{1,3}(?:,[\d]{3})+)(?=\s|$|[.,\-])',
    ]:
        mm = re.search(pat, text, re.MULTILINE)
        if mm:
            try:
                v = float(mm.group(1).replace(",", ""))
                if v >= 50_000:
                    price = v
                    break
            except (ValueError, TypeError):
                pass
    if not price:
        mm = re.search(r'([\d]+(?:[.,][\d]+)?)\s*מיליון', text)
        if mm:
            try: price = float(mm.group(1).replace(",", ".")) * 1_000_000
            except (ValueError, TypeError): pass

    rooms = None
    for pat in [r'(\d+[.,]\d)\s*חדרים', r'(\d+[.,]\d)\s*חד', r'(\d+)\s*חדרים',
                r"(\d+)\s*חד\'", r'חדרים[:\s]*(\d+[.,]?\d?)', r'rooms?[:\s]*(\d+(?:\.\d)?)']:
        mm = re.search(pat, text, re.IGNORECASE)
        if mm:
            try: rooms = float(mm.group(1).replace(",", ".")); break
            except (ValueError, TypeError): pass

    area = None
    for pat in [r'(\d+)\s*מ"ר', r"(\d+)\s*מ''", r"(\d+)\s*מ'",
                r'(\d+)\s*מטר\s*(?:רבוע)?', r'שטח[:\s]*(?:כ-?\s*)?(\d+)',
                r'(?:כ-?\s*)(\d+)\s*מ', r'(\d+)\s*sqm']:
        mm = re.search(pat, text, re.IGNORECASE)
        if mm:
            try:
                v = float(mm.group(1))
                if 10 <= v <= 1000:
                    area = v; break
            except (ValueError, TypeError): pass

    floor = None
    for pat in [r'קומה\s*(\d+)', r'(\d+)\s*קומה', r'floor[:\s]*(\d+)']:
        mm = re.search(pat, text, re.IGNORECASE)
        if mm:
            try: floor = float(mm.group(1)); break
            except (ValueError, TypeError): pass
    if floor is None:
        for word, num in _HEB_FLOOR_ORDINALS.items():
            if re.search(rf'קומה\s+{word}', text):
                floor = float(num); break

    city = None
    for c in _HEB_CITIES:
        if c in text:
            city = c; break

    return {"price": price, "rooms": rooms, "area": area, "floor": floor,
            "city": city, "neighborhood": None, "street": None, "lat": None, "lon": None}


def scrape_facebook_listing(url: str) -> dict:
    """Attempt to scrape a Facebook Marketplace real-estate listing."""
    import time as _time
    html = None
    fb_headers = {
        **_YAD2_HEADERS,
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Mobile Safari/537.36"
        ),
        "Accept-Language": "he-IL,he;q=0.9",
    }
    try:
        from curl_cffi import requests as _cr
        for _attempt, _ver in enumerate(["chrome133", "chrome124", "chrome120"]):
            try:
                if _attempt: _time.sleep(1)
                resp = _cr.Session(impersonate=_ver).get(url, timeout=25)
                html = resp.text; break
            except Exception: continue
    except ImportError:
        pass
    if html is None:
        try:
            resp = requests.get(url, headers=fb_headers, timeout=15)
            html = resp.text
        except Exception:
            return {"error": "לא ניתן להגיע ל-Facebook.", "needs_manual": True, "needs_paste": True}

    _FB_BLOCKED = ["log in to facebook", "create new account", "you must log in",
                   "login_form", "sorry, something went wrong", "error facebook"]
    if any(kw in html[:5000].lower() for kw in _FB_BLOCKED):
        return {"error": "Facebook דורש התחברות לצפייה במודעה זו.", "needs_manual": True, "needs_paste": True}

    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']', html)
    og_desc  = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']', html)
    json_desc = None
    for pat in [r'"body"\s*:\s*\{"text"\s*:\s*"([^"]{20,})"',
                r'"description"\s*:\s*"([^"]{20,})"',
                r'"listing_description"\s*:\s*"([^"]{20,})"']:
        jm = re.search(pat, html)
        if jm:
            json_desc = jm.group(1).encode().decode("unicode_escape", errors="ignore"); break
    json_price = None
    for pat in [r'"listing_price"[^}]*"amount"\s*:\s*"?([\d.]+)"?',
                r'"price_value"\s*:\s*"?([\d,]+)"?', r'"formatted_amount"\s*:\s*"([\d,]+)"']:
        jm = re.search(pat, html)
        if jm:
            try:
                v = float(jm.group(1).replace(",", ""))
                if v >= 50_000: json_price = v
            except (ValueError, TypeError): pass
            if json_price: break

    text = " ".join(filter(None, [
        og_title.group(1) if og_title else "",
        og_desc.group(1)  if og_desc  else "",
        json_desc or "",
    ]))
    if not text.strip() and not json_price:
        return {"error": "לא ניתן לחלץ פרטים מ-Facebook.", "needs_manual": True, "needs_paste": True}

    result = _parse_realestate_text(text)
    if json_price:
        result["price"] = json_price
    if not result["price"]:
        return {"error": "לא נמצא מחיר במודעה.", "needs_manual": True, "needs_paste": True}
    return result


def scrape_listing(url: str) -> dict:
    """Route to the correct scraper based on the listing URL."""
    if re.search(r"yad2\.co\.il/.*item/", url):
        return scrape_yad2_listing(url)
    if re.search(r"facebook\.com/marketplace/item/|fb\.com/marketplace/item/", url):
        return scrape_facebook_listing(url)
    return {"error": "הקישור אינו תקין — יש להזין קישור מ-yad2.co.il או Facebook Marketplace", "needs_manual": False}


def _match_settlement(city, settlements: list):
    """Fuzzy-match a YAD2 city name against our settlement list."""
    import difflib
    if not city:
        return None

    def _norm(s):
        s = s.strip().replace("\xa0", " ").replace("-", " ").replace("–", " ")
        return " ".join(s.split()).lower()

    def _norm_he(s):
        s = _norm(s)
        s = s.replace("יי", "י").replace("וו", "ו").replace("'", "").replace('"', "")
        return s

    c_norm    = _norm(city)
    c_norm_he = _norm_he(city)
    for s in settlements:
        if _norm(s) == c_norm: return s
    for s in settlements:
        if _norm_he(s) == c_norm_he: return s
    for s in settlements:
        s_n = _norm(s)
        if c_norm in s_n or s_n in c_norm: return s
    norm_he_map = {_norm_he(s): s for s in settlements}
    close = difflib.get_close_matches(c_norm_he, norm_he_map.keys(), n=1, cutoff=0.82)
    if close:
        return norm_he_map[close[0]]
    return None


# ─── Yad2 real-time city listing scraper ─────────────────────────────────────

# Yad2 city codes — verified by probing www.yad2.co.il/realestate/forsale?city=<id>
# and checking the fullTitleText / city.text returned in __NEXT_DATA__.
_YAD2_CITY_IDS = {
    # ── Confirmed correct ─────────────────────────────────────────────────────
    "תל אביב יפו": 5000, "תל אביב": 5000,
    "ירושלים": 3000,
    "נתניה": 7400,
    "פתח תקווה": 7900,
    "ראשון לציון": 8300,
    "בת ים": 6200,
    "רחובות": 8400,
    "הרצליה": 6400,
    "כפר סבא": 6900,
    "בני ברק": 6100,
    "רעננה": 8700,
    "מודיעין-מכבים-רעות": 4400, "מודיעין": 4400,
    "עכו": 7600,
    "נצרת": 7300,
    "אילת": 2600,
    "רמת השרון": 800,
    # ── Likely correct (not blocked during testing, but verified via listing city) ─
    "לוד": 7000,
    "רמלה": 8800,
    "קריית גת": 7680,
}


def _fetch_yad2_search_page(city_id, page=1, timeout=20):
    """Fetch one page of Yad2 forsale search results as HTML. Returns (html, error)."""
    url = "https://www.yad2.co.il/realestate/forsale"
    params = {
        "city": city_id,
        "propertyGroup": "apartments",
        "propertyType": "1",
        "page": page,
    }
    page_hdrs = {
        **_YAD2_HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.yad2.co.il/realestate/forsale",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }
    try:
        from curl_cffi import requests as _cr
        import time as _t
        # chrome116 consistently works; try it first, then older fallbacks
        for i, ver in enumerate(["chrome116", "chrome110", "chrome120", "chrome124"]):
            try:
                if i:
                    _t.sleep(1.0)
                s = _cr.Session(impersonate=ver)
                s.headers.update(page_hdrs)
                r = s.get(url, params=params, timeout=timeout)
                if r.status_code == 200 and len(r.text) > 3000:
                    return r.text, None
            except Exception:
                continue
    except ImportError:
        pass
    try:
        r = requests.get(url, params=params, headers=page_hdrs, timeout=timeout)
        if r.status_code == 200:
            return r.text, None
        return None, f"קוד שגיאה {r.status_code}"
    except Exception as exc:
        return None, str(exc)


def _parse_yad2_search_html(html):
    """Extract listing dicts from __NEXT_DATA__ in a Yad2 forsale search page.
    Returns (items_list, error_str).  As of mid-2026, listings live in
    pageProps.feed.{private,agency,platinum,trio}.
    """
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None, "לא נמצאו נתונים בעמוד — יד2 ייתכן שחסמה את הגישה."
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, "שגיאה בפענוח נתוני העמוד."

    pp = data.get("props", {}).get("pageProps", {})

    def _collect_from_feed(feed_dict):
        """Collect all real listings from a feed dict keyed by listing type."""
        result = []
        for key in ("private", "agency", "platinum", "trio", "booster"):
            bucket = feed_dict.get(key) or []
            if isinstance(bucket, list):
                result.extend(b for b in bucket if isinstance(b, dict) and b.get("price"))
        return result

    # Primary path: feed is a direct pageProps key (current Yad2 structure)
    top_feed = pp.get("feed")
    if isinstance(top_feed, dict):
        items = _collect_from_feed(top_feed)
        if items:
            return items, None

    # Fallback: buried inside dehydratedState queries
    for q in pp.get("dehydratedState", {}).get("queries", []):
        sd = q.get("state", {}).get("data", {})
        if not isinstance(sd, dict):
            continue
        items = _collect_from_feed(sd)
        if items:
            return items, None
        # Older feed_items structure
        for key in ("feed", "feedData"):
            sub = sd.get(key) or {}
            if isinstance(sub, dict):
                fi = sub.get("feed_items") or sub.get("feedItems") or []
                if fi:
                    return fi, None

    return None, "לא נמצאו מודעות בעמוד. ייתכן שיד2 שינתה את מבנה הנתונים."


def fetch_yad2_city_listings(city_heb, max_pages=3):
    """Fetch real-time apartment listings from Yad2 for a Hebrew city name.
    Returns (DataFrame, error_str). On success, error_str == ''.
    Scrapes www.yad2.co.il/realestate/forsale?city=<id> and parses __NEXT_DATA__.
    """
    import difflib

    # ── 1. Resolve city name → Yad2 city ID ──────────────────────────────────
    city_id = _YAD2_CITY_IDS.get(city_heb)
    if city_id is None:
        norm = city_heb.strip().replace("-", " ").replace("–", " ")
        close = difflib.get_close_matches(norm, list(_YAD2_CITY_IDS.keys()), n=1, cutoff=0.78)
        if close:
            city_id = _YAD2_CITY_IDS[close[0]]
        else:
            return pd.DataFrame(), (
                f"עיר '{city_heb}' אינה ברשימת הערים הנתמכות לחיפוש יד2 כרגע. "
                "נסה עיר גדולה יותר, או השתמש בנתונים ההיסטוריים."
            )

    # ── 2. Fetch and parse pages ──────────────────────────────────────────────
    all_items = []
    for page in range(1, max_pages + 1):
        html, err = _fetch_yad2_search_page(city_id, page=page)
        if err or not html:
            if page == 1:
                return pd.DataFrame(), (
                    f"שגיאת חיבור ליד2: {err or 'תגובה ריקה'}. "
                    "בדוק חיבור לאינטרנט או נסה שוב מאוחר יותר."
                )
            break

        items, parse_err = _parse_yad2_search_html(html)
        if parse_err:
            if page == 1:
                return pd.DataFrame(), parse_err
            break

        real_ads = [
            i for i in items
            if isinstance(i, dict)
            and i.get("type") not in {
                "commercial_promoted", "promoted_native",
                "banner", "promoted", "lead_gen",
            }
        ]
        all_items.extend(real_ads)
        if len(items) < 25:
            break

    if not all_items:
        return pd.DataFrame(), (
            "לא נמצאו מודעות. יד2 ייתכן וחסמה את הגישה — נסה שוב בעוד מספר דקות."
        )

    # ── 3. Parse into DataFrame ───────────────────────────────────────────────
    # Field paths confirmed from live __NEXT_DATA__ (June 2026):
    #   address.area.text        → neighborhood / area label
    #   address.street.text      → street name (may be absent)
    #   address.house.number     → house number
    #   address.house.floor      → floor
    #   additionalDetails.squareMeter → area m²
    #   additionalDetails.roomsCount  → rooms
    #   price                    → asking price (int)
    #   token                    → listing ID for URL /item/<token>
    rows = []
    for item in all_items:
        price = item.get("price")
        try:
            price = float(price)
        except (TypeError, ValueError):
            continue
        if price < 100_000:
            continue

        addr  = item.get("address") or {}
        add_d = item.get("additionalDetails") or {}
        house = addr.get("house") or {}

        def _txt_field(d, key):
            v = d.get(key)
            if isinstance(v, dict):
                return (v.get("text") or v.get("textHeb") or "").strip()
            return (v or "").strip() if isinstance(v, str) else ""

        hood    = _txt_field(addr, "area") or _txt_field(addr, "neighborhood")
        street  = _txt_field(addr, "street")
        hn      = house.get("number")
        house_n = str(int(hn)) if hn is not None else ""
        floor_v = house.get("floor")
        area    = add_d.get("squareMeter") or add_d.get("squareMeters")
        rooms   = add_d.get("roomsCount")  or add_d.get("rooms")
        item_id = str(item.get("token") or item.get("orderId") or item.get("id") or "")

        rows.append({
            "שכונה":           hood,
            "רחוב":            street,
            "מס' בית":         house_n,
            'שטח (מ"ר)':       float(area)    if area    is not None else np.nan,
            "חדרים":           float(rooms)   if rooms   is not None else np.nan,
            "קומה":            float(floor_v) if floor_v is not None else np.nan,
            "מחיר מבוקש (₪)": int(price),
            "_yad2_id":        item_id,
        })

    if not rows:
        return pd.DataFrame(), "לא נמצאו מודעות עם פרטים מלאים."

    return pd.DataFrame(rows), ""


# ─── POI / Map helpers ────────────────────────────────────────────────────────

_CAT_COLORS = {
    "transport":  [255, 140,   0, 160],
    "education":  [138,  43, 226, 160],
    "health":     [  0, 180,  60, 160],
    "park":       [ 34, 139,  34, 160],
    "retail":     [220, 180,   0, 160],
    "food":       [220,  20,  60, 160],
    "service":    [ 70, 130, 180, 160],
    "leisure":    [255, 105, 180, 160],
    "tourism":    [  0, 190, 200, 160],
    "community":  [200, 120,  30, 160],
    "nature":     [ 34, 100,  34, 160],
    "historic":   [139,  90,  43, 160],
    "employment": [110, 110, 110, 160],
}

_CAT_HEB = {
    "transport": "תחבורה", "education": "חינוך", "health": "בריאות",
    "park": "פארקים", "retail": "קניות", "food": "מזון",
    "service": "שירותים", "leisure": "פנאי", "tourism": "תיירות",
    "community": "קהילה", "nature": "טבע", "historic": "היסטוריה",
    "employment": "תעסוקה",
}

_CAT_EMOJI = {
    "transport": "🚌", "education": "🎓", "health": "🏥",
    "park": "🌳", "retail": "🛒", "food": "🍽️",
    "service": "🏛️", "leisure": "🎭", "tourism": "🏛️",
    "community": "⛪", "nature": "🌿", "historic": "🏰",
    "employment": "🏢",
}

_FOLIUM_COLORS = {
    "transport": "#FF8C00", "education": "#8A2BE2",
    "health":    "#00B43C", "park":      "#228B22",
    "retail":    "#DAA520", "food":      "#DC143C",
    "service":   "#4682B4", "leisure":   "#FF69B4",
    "tourism":   "#00CED1", "community": "#FFA500",
    "nature":    "#2E6B2E", "historic":  "#8B5A2B",
    "employment": "#696969",
}


def itm_to_wgs84(x_ser: pd.Series, y_ser: pd.Series):
    """Convert ITM (EPSG:2039) easting/northing to WGS84 lat/lon arrays."""
    a   = 6_378_137.0
    f   = 1.0 / 298.257_222_101
    e2  = 2*f - f**2
    k0  = 1.000_006_7
    lam0 = np.radians(35.204_516_944)
    phi0 = np.radians(31.734_393_611)
    FE, FN = 219_529.584, 626_907.390

    x0 = x_ser.values - FE
    y0 = y_ser.values - FN

    A0 = 1 - e2/4 - 3*e2**2/64 - 5*e2**3/256
    B0 = 3/8   * (e2 + e2**2/4  + 15*e2**3/128)
    C0 = 15/256 * (e2**2 + 3*e2**3/4)
    D0 = 35*e2**3/3072
    M0 = a * (A0*phi0 - B0*np.sin(2*phi0) + C0*np.sin(4*phi0) - D0*np.sin(6*phi0))

    M1  = M0 + y0 / k0
    mu1 = M1 / (a * A0)
    e1  = (1 - np.sqrt(1-e2)) / (1 + np.sqrt(1-e2))

    phi1 = (mu1
            + (3*e1/2   - 27*e1**3/32) * np.sin(2*mu1)
            + (21*e1**2/16)             * np.sin(4*mu1)
            + (151*e1**3/96)            * np.sin(6*mu1))

    N1 = a / np.sqrt(1 - e2 * np.sin(phi1)**2)
    T1 = np.tan(phi1)**2
    C1 = e2 * np.cos(phi1)**2 / (1 - e2)
    R1 = a * (1-e2) / (1 - e2*np.sin(phi1)**2)**1.5
    D1 = x0 / (N1 * k0)

    lat = phi1 - (N1*np.tan(phi1)/R1) * (
        D1**2/2 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e2/(1-e2)) * D1**4/24
    )
    lon = lam0 + (D1 - (1 + 2*T1 + C1)*D1**3/6) / np.cos(phi1)
    return np.degrees(lat), np.degrees(lon)


@st.cache_data
def load_poi_data(poi_path: str) -> pd.DataFrame:
    df = pd.read_csv(poi_path, encoding="utf-8-sig", low_memory=False,
                     usecols=["lat", "lon", "name", "category"])
    return df.dropna(subset=["lat", "lon", "category"]).reset_index(drop=True)


def get_local_pois(poi_df: pd.DataFrame, lat: float, lon: float,
                   radius_m: float = 1000) -> pd.DataFrame:
    """Return rows from poi_df within radius_m metres of (lat, lon), with distance."""
    dlat = radius_m / 111_000
    dlon = radius_m / (111_000 * np.cos(np.radians(lat)))
    nearby = poi_df[
        poi_df["lat"].between(lat - dlat, lat + dlat) &
        poi_df["lon"].between(lon - dlon, lon + dlon)
    ].copy()
    if nearby.empty:
        return nearby
    R = 6_371_000.0
    dlat_r = np.radians(nearby["lat"].values - lat)
    dlon_r = np.radians(nearby["lon"].values - lon)
    a = (np.sin(dlat_r / 2) ** 2
         + np.cos(np.radians(lat)) * np.cos(np.radians(nearby["lat"].values))
         * np.sin(dlon_r / 2) ** 2)
    dist = R * 2 * np.arcsin(np.sqrt(a))
    mask = dist <= radius_m
    nearby = nearby[mask].copy()
    nearby["dist_m"]  = dist[mask].round(0).astype(int)
    nearby["prefix"]  = nearby["category"].apply(lambda c: c.split("_")[0])
    nearby["cat_heb"] = nearby["prefix"].map(_CAT_HEB).fillna(nearby["prefix"])
    nearby["color"]   = nearby["prefix"].apply(
        lambda p: _CAT_COLORS.get(p, [128, 128, 128, 160])
    )
    return nearby.sort_values("dist_m").reset_index(drop=True)


@st.cache_data(ttl=86_400, show_spinner=False)
def geocode_address(query: str) -> tuple:
    """Geocode an Israeli address/city via Nominatim. Results cached 24 h."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{query}, ישראל", "format": "json", "limit": 1,
                    "accept-language": "he"},
            headers={"User-Agent": "AG_RealEstate_Advisor/1.0 (academic)"},
            timeout=6,
        )
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


# ─── Sidebar navigation ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div dir="rtl" style="text-align:center; padding:16px 0 12px;">
      <span style="font-size:2.2rem;">🏠</span><br>
      <b style="font-size:1.1rem; color:oklch(27% 0.12 155);">יועץ נדל"ן חכם</b>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "ניווט:",
        [
            "🔍 מצא אזור להשקעה",
            "🏡 בדוק נכס ספציפי",
            "📊 עיין בנכסים ביישוב",
        ],
        key="nav_page",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
    <div dir="rtl" style="font-size:0.8rem; color:#696969; text-align:right; line-height:1.5;">
    המודל אומן על 6,609 עסקאות נדל"ן אמיתיות בישראל.<br><br>
    הכלי מיועד לסיוע בקבלת החלטות בלבד — אינו תחליף לייעוץ מקצועי.
    </div>
    """, unsafe_allow_html=True)





# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — FIND AREA
# ══════════════════════════════════════════════════════════════════════════════
if page == "🔍 מצא אזור להשקעה":

    rtl('<h1>🔍 מצא אזור להשקעה</h1>')

    # ── Explanation bar ───────────────────────────────────────────────────────
    with st.expander("📖 הסבר על הכלי — לחץ לפתיחה / סגירה", expanded=True):
        about_col, inputs_col = st.columns(2)

        with about_col:
            rtl("""
            <h4>🗺️ מה הכלי הזה עושה?</h4>
            <p>הכלי עוזר לך למצוא <strong>אזורים מומלצים להשקעה</strong>
            מבלי שתצטרך לדעת נדל"ן מראש.</p>
            <p>הוא סורק אלפי עסקאות אמיתיות מרשות המיסים, ומחשב לכל אזור
            <strong>ציון כדאיות</strong> (0–100) לפי שלושה גורמים: כמה זול נמכרו
            נכסים שם, האם המחירים עולים, וכמה פעיל השוק.</p>
            <p><strong>מה תקבל בסוף?</strong><br>
            רשימה של אזורים ממוינת מהמומלץ ביותר לפחות — עם מחיר ממוצע,
            מגמה שנתית וציון.</p>
            """)

        with inputs_col:
            rtl("""
            <h4>📥 מה למלא?</h4>
            <p>🔹 <strong>תקציב מקסימלי (₪)</strong><br>
            הסכום המרבי שאתה מוכן לשלם עבור דירה.
            אזורים שהמחיר הממוצע שלהם גבוה מסכום זה יסוננו אוטומטית —
            כי סביר שלא תמצא שם דירה בתקציב.</p>
            <p>🔹 <strong>מטרת ההשקעה</strong></p>
            <ul>
              <li><em>תשואה שוטפת (שכ"ד)</em> — אתה רוצה לקנות ולהשכיר, ולקבל כסף כל חודש.
              הכלי יחפש אזורים עם ביקוש גבוה לשכירות.</li>
              <li><em>עליית ערך (מכירה ברווח)</em> — אתה רוצה לקנות בזול, לחכות שהנכס
              יתייקר, ולמכור. הכלי יחפש אזורים עם מגמת עלייה חזקה.</li>
            </ul>
            """)

    # ── Inputs ────────────────────────────────────────────────────────────────
    with st.container(border=True):
        col_a, col_b = st.columns(2)
        with col_a:
            budget = st.number_input(
                "💰 תקציב מקסימלי (₪)",
                min_value=300_000, max_value=10_000_000,
                value=2_000_000, step=100_000, format="%d",
                help="המחיר המקסימלי שאתה מוכן לשלם. אזורים שמחירם הממוצע גבוה יותר יסוננו.",
            )
        with col_b:
            goal = st.radio(
                "🎯 מה המטרה שלך?",
                ["💵 תשואה שוטפת (השכרה)", "📈 עליית ערך (מכירה ברווח)"],
                help="תשואה שוטפת = שכ\"ד חודשי. עליית ערך = קנה בזול, מכור ביוקר.",
            )

    # ── Compute ───────────────────────────────────────────────────────────────
    stats    = compute_area_stats()
    filtered = stats[(stats["avg_price"] <= budget) & (stats["deal_count"] >= 10)].copy()

    if filtered.empty:
        st.warning("לא נמצאו אזורים בתקציב זה עם מספיק נתונים. נסה להגדיל את התקציב.")
    else:
        def _minmax(s: pd.Series) -> pd.Series:
            lo, hi = s.min(), s.max()
            return pd.Series(50.0, index=s.index) if hi == lo else (s - lo) / (hi - lo) * 100

        gap_sc, trend_sc, liq_sc = _minmax(filtered["avg_gap"]), _minmax(filtered["trend_pct_yr"]), _minmax(filtered["deal_count"])

        if "עליית ערך" in goal:
            filtered["score"] = (0.30 * gap_sc + 0.50 * trend_sc + 0.20 * liq_sc).round(1)
            weight_desc = "פער מחיר 30% + מגמה 50% + נזילות 20%"
        else:
            filtered["score"] = (0.60 * gap_sc + 0.20 * trend_sc + 0.20 * liq_sc).round(1)
            weight_desc = "פער מחיר 60% + מגמה 20% + נזילות 20%"

        filtered = filtered.sort_values("score", ascending=False)
        top, best = filtered.head(15), filtered.iloc[0]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("אזורים בתקציב",    len(filtered))
        m2.metric("האזור המוביל",     best["settlementNameHeb"])
        m3.metric("ציון מוביל",       f"{best['score']:.0f} / 100")
        m4.metric("מחיר ממוצע מוביל", f"{best['avg_price']:,.0f} ₪")

        with m1:
            with st.popover("❓"):
                rtl("<p>כמה אזורים נמצאו בתוך התקציב שהגדרת (עם לפחות 10 עסקאות בנתונים).</p>")
        with m2:
            with st.popover("❓"):
                rtl("<p>האזור עם ציון הכדאיות הגבוה ביותר עבורך.</p>")
        with m3:
            with st.popover("❓"):
                rtl("<p>ציון בין 0–100. ירוק = מומלץ מאוד, אדום = פחות מומלץ.</p>")
        with m4:
            with st.popover("❓"):
                rtl("<p>מחיר ממוצע של דירות באזור המוביל לפי עסקאות אמיתיות.</p>")

        st.markdown("---")
        rtl('<h3>🏆 האזורים המומלצים ביותר עבורך</h3>')

        rows = []
        for _, row in top.iterrows():
            rows.append({
                "יישוב":            row["settlementNameHeb"],
                "ציון כדאיות":      row["score"],
                "מחיר ממוצע (₪)":  int(row["avg_price"]),
                "פער ממחיר שוק":   round(float(row["avg_gap"]), 1),
                "מגמת מחירים/שנה": round(float(row["trend_pct_yr"]), 1),
                "כמות עסקאות":     int(row["deal_count"]),
                "מדד סוציו":       round(row["avg_socio"], 2),
            })
        df_show = pd.DataFrame(rows)

        st.dataframe(
            df_show,
            column_config={
                "ציון כדאיות": st.column_config.ProgressColumn(
                    "ציון כדאיות (0-100)", min_value=0, max_value=100, format="%.0f",
                ),
                "מחיר ממוצע (₪)": st.column_config.NumberColumn(format="₪%,d"),
                "פער ממחיר שוק": st.column_config.NumberColumn(
                    "פער ממחיר שוק (%)",
                    format="%+.1f%%",
                    help="ההפרש בין מחיר השוק החזוי ע\"י המודל לבין המחיר שנמכר בפועל. חיובי (+) = נכסים נמכרו מתחת לשווי השוק — הזדמנות! שלילי (−) = נמכרו מעל השוק.",
                ),
                "מגמת מחירים/שנה": st.column_config.NumberColumn(
                    "מגמת מחירים/שנה (%)",
                    format="%+.1f%%",
                    help="שינוי אחוזי ממוצע במחירי הדירות מדי שנה (נגזר מרגרסיה על עסקאות היסטוריות). חיובי = מחירים עולים — מתאים להשקעה לעליית ערך. שלילי = מחירים יורדים.",
                ),
                "מדד סוציו": st.column_config.NumberColumn(
                    "מדד סוציו-אקונומי",
                    help="מדד הלשכה המרכזית לסטטיסטיקה (למ\"ס) המשקף את רמת החיים ביישוב: הכנסות ממוצעות, השכלה, תעסוקה ועוד. ערך גבוה = אזור חזק כלכלית → יציבות מחירים וסיכון נמוך יותר. ערך נמוך = פוטנציאל עלייה גבוה יותר, אך גם סיכון גבוה יותר.",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        with st.expander("📖 איך לקרוא את הטבלה?"):
            rtl("""
            <table style="width:100%;border-collapse:collapse;">
              <tr style="background:#F5F5F5;">
                <th style="padding:8px;border:1px solid #E0E0E0;text-align:right;">עמודה</th>
                <th style="padding:8px;border:1px solid #E0E0E0;text-align:right;">הסבר</th>
              </tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>ציון כדאיות</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">0–100. ירוק = מומלץ, אדום = פחות</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מחיר ממוצע</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">ממוצע עסקאות בפועל באזור</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>פער ממחיר שוק (%)</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">חיובי (+) = נמכר מתחת לשוק = הזדמנות · שלילי (−) = נמכר מעל השוק</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מגמת מחירים/שנה (%)</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">כמה % עלו / ירדו המחירים בשנה בממוצע</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>כמות עסקאות</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">יותר עסקאות = נתון אמין יותר</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מדד סוציו-אקונומי</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">מדד למ"ס לרמת החיים ביישוב. גבוה = אזור חזק → יציבות. נמוך = פוטנציאל עלייה + סיכון</td></tr>
            </table>
            """)

        rtl(f'<p style="color:#555;font-size:0.85rem;">ציון כדאיות חושב לפי: {weight_desc}</p>')

        rtl('<h3>📊 השוואה ויזואלית — ציון כדאיות לפי אזור</h3>')
        fig = px.bar(
            df_show.head(12), x="יישוב", y="ציון כדאיות",
            color="ציון כדאיות", color_continuous_scale="RdYlGn",
            range_color=[0, 100], height=370, text="ציון כדאיות",
        )
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-30, margin=dict(t=20, b=60))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📈 גרף — מחיר ממוצע מול מגמת מחירים"):
            fig2 = px.scatter(
                filtered.head(30), x="avg_price", y="trend_pct_yr",
                size="deal_count", color="score",
                color_continuous_scale="RdYlGn", range_color=[0, 100],
                hover_name="settlementNameHeb",
                labels={"avg_price": "מחיר ממוצע (₪)", "trend_pct_yr": "מגמה (%/שנה)",
                        "deal_count": "עסקאות", "score": "ציון כדאיות"},
                title="מחיר מול מגמה — גודל הנקודה = כמות עסקאות", height=400,
            )
            fig2.update_layout(margin=dict(t=40, b=20))
            st.plotly_chart(fig2, use_container_width=True)
            rtl('<p style="color:#555;font-size:0.85rem;">ציר X = מחיר ממוצע · ציר Y = מגמה שנתית · גודל = נזילות · צבע = ציון כדאיות</p>')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CHECK PROPERTY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏡 בדוק נכס ספציפי":

    rtl('<h1>🏡 בדוק נכס ספציפי</h1>')

    # ── Explanation bar ───────────────────────────────────────────────────────
    with st.expander("📖 הסבר על הכלי — לחץ לפתיחה / סגירה", expanded=True):
        about_col, inputs_col = st.columns(2)

        with about_col:
            rtl("""
            <h4>🏡 מה הכלי הזה עושה?</h4>
            <p>הכלי בודק אם <strong>מחיר נכס ספציפי</strong> שמצאת הוא הוגן —
            או שיקר / זול מהשוק.</p>
            <p>לאחר שתכניס את הפרטים, המודל יחפש עסקאות דומות שכבר נמכרו
            בעיר הזו, ויחשב מה הנכס "שווה" לפי השוק. לאחר מכן הוא ישווה את
            הסכום הזה למחיר שנדרש ממך — וייתן לך:</p>
            <ul>
              <li><strong>ציון כדאיות</strong> (0–100) — האם כדאי לקנות?</li>
              <li><strong>פירוט</strong> — למה הנכס קיבל את הציון הזה</li>
              <li><strong>עסקאות דומות</strong> — מה שילמו אחרים על נכסים דומים</li>
            </ul>
            """)

        with inputs_col:
            rtl("""
            <h4>📥 מה למלא?</h4>
            <p>🔹 <strong>עיר / יישוב</strong><br>
            העיר שבה הנכס נמצא. הכלי ישווה לעסקאות מאותה עיר בלבד.</p>
            <p>🔹 <strong>מחיר מבוקש (₪)</strong><br>
            הסכום שהמוכר דורש. זה הסכום שנשווה מול מחיר השוק.</p>
            <p>🔹 <strong>שטח (מ"ר)</strong><br>
            גודל הדירה במטרים רבועים כפי שמופיע במודעה.
            דירת 3 חדרים ממוצעת = 70–90 מ"ר.</p>
            <p>🔹 <strong>מספר חדרים</strong><br>
            בישראל נהוג לספור גם את הסלון.
            דירת 3 חדרים = 2 חדרי שינה + סלון. ניתן להכניס חצי חדר (לדוגמה: 2.5).</p>
            <p>🔹 <strong>קומה</strong><br>
            קומת קרקע = 0, קומה ראשונה = 1 וכן הלאה.
            קומות גבוהות נוטות להיות יקרות יותר — המודל לוקח זאת בחשבון.</p>
            """)

    mdl         = load_model()
    df_ml, df_d = load_data()
    feat_cols   = [c for c in df_ml.columns if c != "dealAmount"]
    settlements = sorted(df_d["settlementNameHeb"].dropna().unique().tolist())

    # ── URL auto-fill ─────────────────────────────────────────────────────────
    _FIELD_LABELS = {
        "price":     "💰 מחיר",
        "city":      "🏙️ עיר",
        "street":    "📍 רחוב",
        "house_num": "🔢 מס׳",
        "area":      "📐 שטח",
        "rooms":     "🛏️ חדרים",
        "floor":     "🏢 קומה",
    }

    with st.container(border=True):
        rtl('<h4>📎 יבוא אוטומטי מקישור — יד2</h4>')
        rtl('<p style="color:#555;font-size:0.88rem;">הדבק קישור למודעה ולחץ "חילוץ מידע" — הכלי ינסה למלא את הפרטים אוטומטית. אם לא הצליח, מלא ידנית בטופס למטה.</p>')

        col_url, col_btn = st.columns([5, 1])
        with col_url:
            paste_url = st.text_input(
                "🔗 קישור למודעה",
                key="cp_url",
                placeholder="https://www.yad2.co.il/item/...",
                label_visibility="collapsed",
            )
        with col_btn:
            st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
            fetch_btn = st.button("📥 חילוץ מידע", key="cp_fetch_btn", use_container_width=True, type="primary")

        if fetch_btn:
            if not paste_url or not paste_url.strip():
                st.warning("הדבק קישור תחילה.")
            else:
                _inp = paste_url.strip()
                _is_html = _inp.startswith("<!") or _inp.lower().startswith("<html")
                if _is_html:
                    result = _parse_yad2_html(_inp)
                    # Restore canonical URL from og:url if present
                    _og = re.search(r'property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']', _inp) \
                       or re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']', _inp)
                    if _og:
                        st.session_state["cp_url"] = _og.group(1)
                else:
                    with st.spinner("מחלץ נתונים מהקישור..."):
                        result = scrape_listing(_inp)

                # Apply whatever fields were found (works for full scrape AND partial HTML)
                filled = []
                if result.get("price"):
                    st.session_state["cp_price"] = max(100_000, min(20_000_000, int(result["price"])))
                    filled.append("price")
                if result.get("area"):
                    st.session_state["cp_area"]  = max(20, min(500, int(result["area"])))
                    filled.append("area")
                if result.get("rooms"):
                    st.session_state["cp_rooms"] = max(1.0, min(10.0, float(result["rooms"])))
                    filled.append("rooms")
                if result.get("floor") is not None:
                    st.session_state["cp_floor"] = max(0, min(50, int(result["floor"])))
                    filled.append("floor")
                if result.get("city"):
                    matched = _match_settlement(result["city"], settlements)
                    if matched:
                        st.session_state["cp_city"] = matched
                        filled.append("city")
                if result.get("lat") is not None:
                    st.session_state["cp_lat"] = result["lat"]
                if result.get("lon") is not None:
                    st.session_state["cp_lon"] = result["lon"]
                if result.get("street"):
                    st.session_state["cp_street"]       = result["street"]
                    st.session_state["cp_street_input"] = result["street"]
                    filled.append("street")
                if result.get("house_num"):
                    st.session_state["cp_house_num"] = str(result["house_num"])
                    filled.append("house_num")

                if filled:
                    st.session_state["cp_auto_fields"] = filled
                    if result.get("error"):
                        # Partial extraction — show what was found + what's missing
                        missing = [_FIELD_LABELS[f] for f in _FIELD_LABELS if f not in filled]
                        st.warning(f"⚠️ חולץ חלקית: {', '.join(_FIELD_LABELS[f] for f in filled if f in _FIELD_LABELS)}"
                                   + (f" | חסר: {', '.join(missing)} — השלם ידנית." if missing else ""))
                    st.rerun()
                else:
                    # Nothing found at all
                    if result.get("needs_paste"):
                        st.warning(f"⚠️ {result['error']} — הדבק את תיאור המודעה ידנית בטופס למטה.")
                    elif result.get("needs_manual"):
                        st.warning(
                            f"⚠️ {result.get('error','')}  \n"
                            "**פתרון:** פתח המודעה בדפדפן → **Ctrl+U** → **Ctrl+A** → **Ctrl+C** → הדבק כאן ולחץ שוב."
                        )
                    else:
                        st.error(f"❌ {result.get('error','שגיאה לא ידועה')}")

        # ── Auto-fill checklist ───────────────────────────────────────────────
        auto_fields = st.session_state.get("cp_auto_fields", [])
        if auto_fields:
            n_total  = len(_FIELD_LABELS)
            n_filled = sum(1 for f in _FIELD_LABELS if f in auto_fields)
            bar_color = "#1A9E3F" if n_filled == n_total else ("#F5A623" if n_filled >= 3 else "#D9534F")
            items_html = "".join(
                f'<span style="display:inline-flex;align-items:center;gap:4px;margin:3px 6px;font-size:0.88rem;">'
                f'{"✅" if f in auto_fields else "❌"} '
                f'<span style="color:{"#1A9E3F" if f in auto_fields else "#D9534F"};font-weight:{"600" if f in auto_fields else "400"};">'
                f'{lbl}</span></span>'
                for f, lbl in _FIELD_LABELS.items()
            )
            st.markdown(
                f'<div dir="rtl" style="background:#F8F9FA;border:1px solid #E0E0E0;border-radius:8px;padding:10px 14px;margin:8px 0;">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
                f'<strong style="font-size:0.92rem;">אחזור אוטומטי:</strong>'
                f'<span style="background:{bar_color};color:white;border-radius:20px;padding:2px 10px;font-size:0.85rem;font-weight:700;">'
                f'{n_filled}/{n_total}</span></div>'
                f'<div style="display:flex;flex-wrap:wrap;">{items_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("🗑️ נקה נתונים שאוחזרו", key="cp_clear_auto"):
                for k in ["cp_auto_fields", "cp_lat", "cp_lon", "cp_street", "cp_street_input"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # ── Form ──────────────────────────────────────────────────────────────────
    with st.container(border=True):
        rtl('<h4>פרטי הנכס</h4>')
        # Row 1 — Address
        r1c1, r1c2, r1c3 = st.columns([2, 2, 1])
        with r1c1:
            city = st.selectbox(
                "🏙️ עיר / יישוב", settlements,
                index=settlements.index("בת ים") if "בת ים" in settlements else 0,
                key="cp_city",
                help="בחר את העיר שבה הנכס נמצא.",
            )
        with r1c2:
            if "cp_street_input" not in st.session_state:
                st.session_state["cp_street_input"] = st.session_state.get("cp_street", "")
            street_input = st.text_input(
                "📍 שם רחוב",
                placeholder="לדוגמה: הרצל",
                key="cp_street_input",
                help="שם הרחוב של הנכס.",
            )
        with r1c3:
            house_num = st.text_input(
                "🔢 מס׳", value=st.session_state.get("cp_house_num", ""),
                placeholder="12",
                key="cp_house_num",
                help="מספר הבית.",
            )
        # Row 2 — Price + Area
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            price = st.number_input(
                "💰 מחיר מבוקש (₪)", min_value=100_000, max_value=20_000_000,
                value=1_500_000, step=50_000, format="%d", key="cp_price",
                help="הסכום שהמוכר דורש. זהו הסכום שנשווה מול מחיר השוק.",
            )
        with r2c2:
            area = st.number_input(
                '📐 שטח (מ"ר)', min_value=20, max_value=500, value=80, step=5, key="cp_area",
                help="שטח הדירה במ\"ר. דירת 3 חדרים ממוצעת = 70–90 מ\"ר.",
            )
        # Row 3 — Rooms + Floor
        r3c1, r3c2, _ = st.columns(3)
        with r3c1:
            rooms = st.number_input(
                "🛏️ מספר חדרים", min_value=1.0, max_value=10.0, value=3.0, step=0.5, key="cp_rooms",
                help="בישראל נהוג לספור גם את הסלון. דירת 3 חדרים = 2 שינות + סלון.",
            )
        with r3c2:
            floor = st.number_input(
                "🏢 קומה", min_value=0, max_value=50, value=2, step=1, key="cp_floor",
                help="קומת קרקע = 0. קומה ראשונה = 1. קומות גבוהות = בדרך כלל יקרות יותר.",
            )

    calc_btn = st.button("🔍 בדוק את הנכס", type="primary", use_container_width=True)

    if calc_btn:
        _full_addr = " ".join(filter(None, [street_input.strip(), house_num.strip()]))
        st.session_state["cp_result"] = {
            "city": city, "price": price, "area": area, "rooms": rooms, "floor": floor,
            "lat":    st.session_state.get("cp_lat"),
            "lon":    st.session_state.get("cp_lon"),
            "street": _full_addr or st.session_state.get("cp_street", ""),
        }
        st.session_state.pop("cp_show_map", None)

    if st.session_state.get("cp_result"):
        r     = st.session_state["cp_result"]
        city  = r["city"]
        price = r["price"]
        area  = r["area"]
        rooms = r["rooms"]
        floor = r["floor"]

        mask   = df_d["settlementNameHeb"] == city
        sub_d  = df_d[mask]
        sub_ml = df_ml[mask]

        fvec = sub_ml[feat_cols].median().copy()
        fvec["assetArea"]    = float(area)
        fvec["assetRoomNum"] = float(rooms)
        fvec["floor_num"]    = float(floor)
        today = datetime.date.today()
        fvec["deal_year"]    = float(today.year)
        fvec["deal_month"]   = float(today.month)

        predicted  = float(mdl.predict(fvec[feat_cols].values.reshape(1, -1))[0])
        gap_pct    = (predicted - price) / price * 100
        gap_amount = predicted - price

        avg_area  = float(sub_d["dealAmount"].mean()) if not sub_d.empty else price
        n_deals   = len(sub_d)

        s_min = float(df_d["socio_index_avg"].min())
        s_max = float(df_d["socio_index_avg"].max())
        s_avg = float(sub_d["socio_index_avg"].mean()) if not sub_d.empty else (s_min + s_max) / 2
        socio_score  = (s_avg - s_min) / (s_max - s_min) * 100 if s_max > s_min else 50.0
        price_score  = min(100.0, max(0.0, 50.0 + gap_pct * 2.5))
        liq_score    = min(100.0, n_deals / 50.0 * 100.0)
        viability    = round(0.60 * price_score + 0.25 * socio_score + 0.15 * liq_score, 1)

        st.markdown("---")
        rtl('<h2>📊 תוצאות הניתוח</h2>')

        if viability >= 70:
            verdict_class, verdict_icon, verdict_text = "verdict-good", "🟢", "עסקה טובה!"
            verdict_detail = "המחיר נראה הוגן או אפילו נמוך מהשוק."
        elif viability >= 45:
            verdict_class, verdict_icon, verdict_text = "verdict-ok", "🟡", "עסקה סבירה"
            verdict_detail = "המחיר קרוב לשוק. בדוק לעומק לפני החלטה."
        else:
            verdict_class, verdict_icon, verdict_text = "verdict-bad", "🔴", "מחיר גבוה"
            verdict_detail = "המחיר נראה גבוה מהשוק. נסה להתמקח."

        st.markdown(
            f'<div class="{verdict_class}">'
            f'<div style="font-size:3rem;">{verdict_icon} {viability:.0f} / 100</div>'
            f'<div dir="rtl" style="font-size:1.5rem;font-weight:800;margin-top:8px;">{verdict_text}</div>'
            f'<div dir="rtl" style="font-size:1rem;color:#555;margin-top:4px;">{verdict_detail}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        rtl('<h3>💰 השוואת מחירים</h3>')
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("מחיר חזוי (שוק הוגן)", f"{predicted:,.0f} ₪",
                   help="מה המודל חושב שהנכס שווה לפי עסקאות דומות.")
        mc2.metric("מחיר מבוקש", f"{price:,.0f} ₪",
                   help="הסכום שהמוכר דורש.")
        mc3.metric("הפרש", f"{gap_pct:+.1f}%",
                   delta=f"{gap_amount:+,.0f} ₪",
                   delta_color="normal" if gap_pct >= 0 else "inverse",
                   help="פלוס (+) = הנכס שווה יותר ממה שנדרש = טוב לך!")

        mc4, mc5, mc6 = st.columns(3)
        mc4.metric("מחיר ממוצע בעיר",  f"{avg_area:,.0f} ₪",
                   help="ממוצע כל העסקאות בעיר זו בנתונים.")
        mc5.metric("עסקאות בנתונים",   f"{n_deals}",
                   help="יותר עסקאות = ניתוח אמין יותר.")
        mc6.metric("איכות אזור",        f"{socio_score:.0f} / 100",
                   help="ציון המדד הסוציו-אקונומי (0 נמוך, 100 גבוה).")

        rtl('<h3>🔍 פירוט הציון — למה קיבלת את הציון הזה?</h3>')
        with st.container(border=True):
            reasons = []
            if gap_pct > 15:
                reasons.append(("✅", "מחיר זול משמעותית",
                    f"המודל מעריך שהנכס שווה {gap_pct:.1f}% יותר ממה שנדרש ממך. זו הזדמנות טובה."))
            elif gap_pct > 3:
                reasons.append(("✅", "מחיר מתחת לשוק",
                    f"הנכס מתומחר {gap_pct:.1f}% מתחת להערכת המודל. מרחב מיקוח טוב."))
            elif gap_pct > -5:
                reasons.append(("⚠️", "מחיר בשוק",
                    f"המחיר קרוב לשווי ההוגן (פער {gap_pct:+.1f}%). אין הזדמנות גדולה, אבל גם לא יקר."))
            elif gap_pct > -15:
                reasons.append(("⚠️", "מחיר מעל השוק",
                    f"הנכס מתומחר {abs(gap_pct):.1f}% מעל הערכת המודל. שקול להתמקח."))
            else:
                reasons.append(("❌", "מחיר גבוה מהשוק",
                    f"הנכס מתומחר {abs(gap_pct):.1f}% מעל המודל. ודא שיש סיבה מוצדקת."))

            if socio_score >= 70:
                reasons.append(("✅", f"אזור איכותי — {city}",
                    f"{city} מדורגת גבוה במדד הסוציו-אקונומי. זה מוסיף ביטחון להשקעה."))
            elif socio_score >= 40:
                reasons.append(("⚠️", f"אזור בינוני — {city}",
                    f"{city} במדד סוציו-אקונומי בינוני."))
            else:
                reasons.append(("⚠️", f"אזור עם מדד נמוך — {city}",
                    f"{city} מתחת לממוצע הארצי. סיכון גבוה יותר, אבל גם פוטנציאל עלייה."))

            if n_deals >= 30:
                reasons.append(("✅", "שוק נזיל",
                    f"יש {n_deals} עסקאות — שוק פעיל, קל יותר למכור בעתיד."))
            elif n_deals >= 10:
                reasons.append(("⚠️", "נזילות בינונית",
                    f"יש {n_deals} עסקאות — מספיק לניתוח, אבל לא שוק מאוד פעיל."))
            else:
                reasons.append(("⚠️", "מעט נתונים",
                    f"רק {n_deals} עסקאות. הניתוח פחות אמין — מומלץ לקבל חוות דעת שמאי."))

            for icon, title, desc in reasons:
                rtl(f'<p><strong>{icon} {title}</strong><br>{desc}</p>')

        rtl('<h3>🏘️ עסקאות דומות לאחרונה</h3>')
        rtl(f'<p style="color:#555">עסקאות ב{city} עם שטח דומה (±25%) וחדרים דומים (±0.5)</p>')

        df_all_pred = compute_predictions()
        similar = df_all_pred[
            (df_all_pred["settlementNameHeb"] == city) &
            (df_all_pred["assetArea"].between(area * 0.75, area * 1.25)) &
            (df_all_pred["assetRoomNum"].between(rooms - 0.5, rooms + 0.5))
        ].sort_values("deal_year", ascending=False).head(10)

        if similar.empty:
            st.info("לא נמצאו עסקאות דומות בנתונים. נסה לשנות את הפרמטרים.")
        else:
            avg_similar = similar["dealAmount"].mean()
            diff_vs_avg = price - avg_similar
            direction   = "גבוה" if diff_vs_avg > 0 else "נמוך"
            rtl(f'<p><strong>{len(similar)} עסקאות נמצאו</strong> · מחיר ממוצע: <strong>{avg_similar:,.0f} ₪</strong> · המחיר המבוקש {direction} ב-{abs(diff_vs_avg):,.0f} ₪ מהממוצע</p>')

            show_sim = similar.rename(columns={
                "streetNameHeb": "רחוב", "houseNum": "מס'",
                "assetArea": 'שטח (מ"ר)', "assetRoomNum": "חדרים",
                "floor_num": "קומה", "dealAmount": "מחיר שנמכר (₪)",
                "predicted": "מחיר חזוי (₪)", "viability_score": "ציון כדאיות",
                "deal_year": "שנה",
            }).copy()
            show_sim["מחיר שנמכר (₪)"] = show_sim["מחיר שנמכר (₪)"].round(0).astype(int)
            show_sim["מחיר חזוי (₪)"]  = show_sim["מחיר חזוי (₪)"].round(0).astype(int)
            cols_sim = [c for c in ["רחוב", "מס'", 'שטח (מ"ר)', "חדרים", "קומה",
                                    "מחיר שנמכר (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "שנה"]
                        if c in show_sim.columns]
            st.dataframe(
                show_sim[cols_sim],
                column_config={
                    "ציון כדאיות": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                    "מחיר שנמכר (₪)": st.column_config.NumberColumn(format="₪%,d"),
                    "מחיר חזוי (₪)":  st.column_config.NumberColumn(format="₪%,d"),
                },
                hide_index=True, use_container_width=True,
            )

        # ── Map & POI ─────────────────────────────────────────────────────────
        st.markdown("---")
        _map_open = st.session_state.get("cp_show_map", False)
        _map_label = "🗺️ הסתר מפה ונקודות עניין" if _map_open else "🗺️ הצג מפה ונקודות עניין"
        if st.button(_map_label, key="toggle_map_btn"):
            st.session_state["cp_show_map"] = not _map_open
            st.rerun()

        if st.session_state.get("cp_show_map"):
            has_pin = bool(r.get("lat") and r.get("lon"))
            map_lat = float(r["lat"]) if has_pin else None
            map_lon = float(r["lon"]) if has_pin else None
            geocoded = False
            if not has_pin:
                _gc_q = ", ".join(filter(None, [r.get("street"), r.get("city")]))
                if _gc_q:
                    with st.spinner("מאתר מיקום…"):
                        _gc_lat, _gc_lon = geocode_address(_gc_q)
                    if _gc_lat:
                        map_lat, map_lon = _gc_lat, _gc_lon
                        geocoded = True
            has_map_center = bool(map_lat and map_lon)

            try:
                from streamlit_folium import st_folium
                import folium

                # Similar transactions layer
                sim_df = pd.DataFrame(columns=["lat", "lon", "price", "rooms"])
                sim_sub = sub_d[
                    (sub_d["assetRoomNum"] >= rooms - 0.5) &
                    (sub_d["assetRoomNum"] <= rooms + 0.5)
                ]
                valid_s = sim_sub.dropna(subset=["X", "Y"])
                if len(valid_s):
                    s_lats, s_lons = itm_to_wgs84(valid_s["X"], valid_s["Y"])
                    sim_df = pd.DataFrame({
                        "lat": s_lats, "lon": s_lons,
                        "price": valid_s["dealAmount"].values,
                        "rooms": valid_s["assetRoomNum"].values,
                    })
                    sim_df = sim_df[sim_df["lat"].between(29, 34) & sim_df["lon"].between(34, 36)]

                # Centre + zoom
                if has_map_center:
                    c_lat, c_lon, zoom = map_lat, map_lon, 15 if has_pin else 14
                elif len(sim_df):
                    c_lat, c_lon, zoom = float(sim_df["lat"].mean()), float(sim_df["lon"].mean()), 14
                else:
                    c_lat, c_lon, zoom = 32.0, 34.8, 12

                fmap = folium.Map(location=[c_lat, c_lon], zoom_start=zoom, tiles="OpenStreetMap")

                if len(sim_df):
                    sim_group = folium.FeatureGroup(name=f"נכסים דומים ({len(sim_df)})", show=True)
                    for _, row_m in sim_df.iterrows():
                        folium.CircleMarker(
                            location=[row_m.lat, row_m.lon],
                            radius=6, color="#6495ED", fill=True,
                            fill_color="#6495ED", fill_opacity=0.65, weight=1,
                            tooltip=f"{int(row_m.price):,} ₪ | {row_m.rooms:.1f} חדרים",
                        ).add_to(sim_group)
                    sim_group.add_to(fmap)

                # POI layer
                poi_cache_key = None
                if has_map_center and POI_PATH.exists():
                    poi_cache_key = f"pois_{map_lat:.4f}_{map_lon:.4f}"
                    if poi_cache_key not in st.session_state:
                        all_pois = load_poi_data(str(POI_PATH))
                        st.session_state[poi_cache_key] = get_local_pois(all_pois, map_lat, map_lon)
                    poi_df = st.session_state[poi_cache_key]

                    if len(poi_df):
                        summary = (
                            poi_df.groupby(["prefix", "cat_heb"])
                            .agg(כמות=("dist_m", "count"), קרוב_ביותר=("dist_m", "min"))
                            .reset_index()
                            .sort_values("קרוב_ביותר")
                        )
                        summary["סמל"]    = summary["prefix"].map(_CAT_EMOJI).fillna("📍")
                        summary["קטגוריה"] = summary["סמל"] + " " + summary["cat_heb"]
                        summary["קרוב ביותר (מ')"] = summary["קרוב_ביותר"]
                        with st.expander(f"📊 סיכום נקודות עניין — {len(poi_df)} נקודות ב-1 ק\"מ", expanded=False):
                            st.dataframe(
                                summary[["קטגוריה", "כמות", "קרוב ביותר (מ')"]],
                                hide_index=True, use_container_width=True,
                            )

                        all_prefixes = summary["prefix"].tolist()
                        prefix_labels = {
                            row_s["prefix"]: f"{row_s['סמל']} {row_s['cat_heb']} ({row_s['כמות']})"
                            for _, row_s in summary.iterrows()
                        }
                        selected_prefixes = st.multiselect(
                            "סנן קטגוריות POI",
                            options=all_prefixes,
                            default=all_prefixes,
                            format_func=lambda p: prefix_labels.get(p, p),
                            key="poi_cat_filter_simple",
                        )
                        poi_filtered = poi_df[poi_df["prefix"].isin(selected_prefixes)]

                        for prefix in selected_prefixes:
                            grp_df = poi_filtered[poi_filtered["prefix"] == prefix]
                            clr    = _FOLIUM_COLORS.get(prefix, "#888888")
                            grp    = folium.FeatureGroup(name=f"{prefix_labels[prefix]}", show=True)
                            for _, row_p in grp_df.iterrows():
                                name_str = row_p["name"] if row_p["name"] else row_p["cat_heb"]
                                folium.CircleMarker(
                                    location=[row_p.lat, row_p.lon],
                                    radius=5, color=clr, fill=True,
                                    fill_color=clr, fill_opacity=0.65, weight=1,
                                    tooltip=f"{name_str} | {int(row_p.dist_m)} מ'",
                                ).add_to(grp)
                            grp.add_to(fmap)

                # Property pin
                if has_map_center:
                    addr_parts = [p for p in [r.get("street"), r.get("city")] if p]
                    addr_label = ", ".join(addr_parts) if addr_parts else r.get("city", "הנכס")
                    approx_note = " (מיקום משוער)" if geocoded else ""
                    popup_html = (
                        f"<div dir='rtl' style='font-family:Arial;min-width:180px'>"
                        f"<b>{addr_label}{approx_note}</b><br>"
                        f"{int(r['price']):,} ₪ | {r['rooms']:.1f} חדרים"
                        f"</div>"
                    )
                    folium.Marker(
                        location=[map_lat, map_lon],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=addr_label + approx_note,
                        icon=folium.Icon(color="orange" if geocoded else "red", icon="home", prefix="fa"),
                    ).add_to(fmap)

                folium.LayerControl(position="topright").add_to(fmap)
                st_folium(fmap, use_container_width=True, height=420, returned_objects=[])

                legend = []
                if has_pin:
                    legend.append("🔴 הנכס (מדויק)")
                elif geocoded:
                    legend.append("🟠 הנכס (מיקום משוער)")
                if len(sim_df):
                    legend.append(f"🔵 נכסים דומים ({len(sim_df)})")
                if poi_cache_key and len(st.session_state.get(poi_cache_key, pd.DataFrame())):
                    legend.append("🟠 תחבורה · 🟣 חינוך · 🟢 בריאות/פארקים · 🟡 קניות · 🔴 מזון")
                if legend:
                    st.caption(" · ".join(legend))

            except Exception as _map_exc:
                st.caption(f"שגיאת מפה: {_map_exc}")
                try:
                    lats, lons = itm_to_wgs84(sub_d["X"].dropna(), sub_d["Y"].dropna())
                    fb = pd.DataFrame({"lat": lats, "lon": lons})
                    fb = fb[fb["lat"].between(29, 34) & fb["lon"].between(34, 36)]
                    if has_pin:
                        fb = pd.concat([pd.DataFrame({"lat": [r["lat"]], "lon": [r["lon"]]}), fb], ignore_index=True)
                    if len(fb):
                        st.map(fb, zoom=14, use_container_width=True)
                except Exception:
                    pass

        if st.button("🔄 בדיקה חדשה", key="reset_cp"):
            for k in ["cp_result", "cp_show_map", "cp_auto_fields",
                      "cp_lat", "cp_lon", "cp_street"]:
                st.session_state.pop(k, None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — BROWSE CITY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 עיין בנכסים ביישוב":

    rtl('<h1>📊 עיין בנכסים ביישוב</h1>')

    # ── Explanation bar ───────────────────────────────────────────────────────
    with st.expander("📖 הסבר על הכלי — לחץ לפתיחה / סגירה", expanded=True):
        about_col, inputs_col = st.columns(2)

        with about_col:
            rtl("""
            <h4>📊 מה הכלי הזה עושה?</h4>
            <p>הכלי מציג רשימת נכסים לעיר שתבחר —
            מנתונים היסטוריים (<strong>רשות המיסים</strong>) או מודעות
            <strong>בזמן אמת מיד2</strong>.</p>
            <p>כל עסקה/מודעה מקבלת <strong>ציון כדאיות</strong> לפי מודל הבינה המלאכותית שלנו,
            כדי שתוכל להשוות ולמצוא הזדמנויות.</p>
            """)

        with inputs_col:
            rtl("""
            <h4>📥 מה לבחור?</h4>
            <p>🔹 <strong>מקור נתונים</strong><br>
            <em>נתונים היסטוריים</em> — עסקאות שבוצעו בפועל (מחיר שנמכר).<br>
            <em>מחירים בזמן אמת</em> — מודעות פעילות כעת ביד2 (מחיר מבוקש).</p>
            <p>🔹 <strong>עיר / יישוב</strong><br>
            בחר את העיר שמעניינת אותך.</p>
            <p>🔹 <strong>סינון</strong><br>
            גרור את הסרגלים לפי שטח, חדרים ושנה (בנתונים היסטוריים).</p>
            """)

    # ── Mode selector ─────────────────────────────────────────────────────────
    mode = st.radio(
        "📡 מקור נתונים:",
        ["📂 נתונים היסטוריים (רשות המיסים)", "🔴 מחירים בזמן אמת (יד2)"],
        horizontal=True,
        key="browse_mode",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # HISTORICAL MODE
    # ══════════════════════════════════════════════════════════════════════════
    if mode.startswith("📂"):

        df_all = compute_predictions()
        cities = sorted(df_all["settlementNameHeb"].dropna().unique().tolist())
        default_city = "בת ים" if "בת ים" in cities else cities[0]

        selected_city = st.selectbox(
            "🏙️ בחר עיר / יישוב", cities,
            index=cities.index(default_city), key="browse_city",
            help="בחר את העיר שמעניינת אותך לבדיקה.",
        )

        df_city = df_all[df_all["settlementNameHeb"] == selected_city].copy()

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("סה\"כ עסקאות",      len(df_city),
                   help="כמה עסקאות יש בבסיס הנתונים עבור עיר זו.")
        sm2.metric("מחיר ממוצע",        f"{df_city['dealAmount'].mean():,.0f} ₪",
                   help="ממוצע מחירי המכירה בפועל — לא מחיר מבוקש!")
        sm3.metric("שטח ממוצע",         f"{df_city['assetArea'].mean():.0f} מ\"ר",
                   help="שטח ממוצע של דירה שנמכרה בעיר.")
        sm4.metric("ציון כדאיות ממוצע", f"{df_city['viability_score'].mean():.1f} / 100",
                   help="מעל 50 = בממוצע נמכרו מתחת לשוק.")

        st.markdown("---")
        rtl('<h3>סינון עסקאות</h3>')

        area_vals  = df_city["assetArea"].dropna()
        rooms_vals = df_city["assetRoomNum"].dropna()
        year_vals  = df_city["deal_year"].dropna()

        # Row 1 — price (₪M min/max) + rooms (min/max)
        hc1, hc2, hc3, hc4 = st.columns(4)
        _prices = df_city["dealAmount"].dropna()
        with hc1:
            h_p_from = st.number_input(
                "💰 מחיר מינימום (₪ מ')",
                min_value=0.0, max_value=200.0,
                value=round(float(_prices.min()) / 1e6, 1) if len(_prices) else 0.0,
                step=0.1, format="%.1f", key="browse_p_from",
            )
        with hc2:
            h_p_to = st.number_input(
                "מחיר מקסימום (₪ מ')",
                min_value=0.0, max_value=200.0,
                value=round(float(_prices.max()) / 1e6 + 0.1, 1) if len(_prices) else 200.0,
                step=0.1, format="%.1f", key="browse_p_to",
            )
        _rv = rooms_vals[rooms_vals.between(1, 10)]
        with hc3:
            h_r_from = st.number_input(
                "🛏️ חדרים מינימום",
                min_value=1.0, max_value=10.0,
                value=float(_rv.min()) if len(_rv) else 1.0,
                step=0.5, format="%.1f", key="browse_r_from",
            )
        with hc4:
            h_r_to = st.number_input(
                "חדרים מקסימום",
                min_value=1.0, max_value=10.0,
                value=float(_rv.max()) if len(_rv) else 10.0,
                step=0.5, format="%.1f", key="browse_r_to",
            )

        # Row 2 — area (min/max) + year (min/max)
        ha1, ha2, ha3, ha4 = st.columns(4)
        _av = area_vals[(area_vals >= 20) & (area_vals <= 600)]
        with ha1:
            h_a_from = st.number_input(
                '📐 שטח מינימום (מ"ר)',
                min_value=0, max_value=1000,
                value=int(_av.min()) if len(_av) else 0,
                step=5, key="browse_a_from",
            )
        with ha2:
            h_a_to = st.number_input(
                'שטח מקסימום (מ"ר)',
                min_value=0, max_value=1000,
                value=int(_av.max()) + 5 if len(_av) else 1000,
                step=5, key="browse_a_to",
            )
        with ha3:
            h_y_from = st.number_input(
                "📅 שנה מינימום",
                min_value=int(year_vals.min()) if len(year_vals) else 2000,
                max_value=int(year_vals.max()) if len(year_vals) else 2030,
                value=int(year_vals.min()) if len(year_vals) else 2000,
                step=1, key="browse_y_from",
            )
        with ha4:
            h_y_to = st.number_input(
                "שנה מקסימום",
                min_value=int(year_vals.min()) if len(year_vals) else 2000,
                max_value=int(year_vals.max()) if len(year_vals) else 2030,
                value=int(year_vals.max()) if len(year_vals) else 2030,
                step=1, key="browse_y_to",
            )

        mask = (
            df_city["dealAmount"].between(h_p_from * 1e6, h_p_to * 1e6) &
            df_city["assetArea"].between(h_a_from, h_a_to) &
            df_city["assetRoomNum"].between(h_r_from, h_r_to) &
            df_city["deal_year"].between(h_y_from, h_y_to)
        )
        df_filtered = df_city[mask].sort_values("viability_score", ascending=False).copy()

        rtl(f'<p><strong>{len(df_filtered)} עסקאות</strong> מוצגות — מדורגות מהכדאית ביותר</p>')

        show = df_filtered.rename(columns={
            "neighborhood": "שכונה", "streetNameHeb": "רחוב", "houseNum": "מס' בית",
            "assetArea": 'שטח (מ"ר)', "assetRoomNum": "חדרים", "floor_num": "קומה",
            "dealAmount": "מחיר שנמכר (₪)", "predicted": "מחיר חזוי (₪)",
            "viability_score": "ציון כדאיות", "deal_year": "שנה",
        }).copy()

        show["מחיר שנמכר (₪)"] = show["מחיר שנמכר (₪)"].round(0).astype(int)
        show["מחיר חזוי (₪)"]  = show["מחיר חזוי (₪)"].round(0).astype(int)
        show['שטח (מ"ר)']       = show['שטח (מ"ר)'].round(1)
        if "קומה" in show.columns:
            try:
                show["קומה"] = show["קומה"].round(0).astype(int)
            except Exception:
                pass

        disp_cols = [c for c in
            ["שכונה", "רחוב", "מס' בית", 'שטח (מ"ר)', "חדרים", "קומה",
             "מחיר שנמכר (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "שנה"]
            if c in show.columns]

        st.dataframe(
            show[disp_cols].head(30),
            column_config={
                "ציון כדאיות": st.column_config.ProgressColumn(
                    "ציון כדאיות (0-100)", min_value=0, max_value=100, format="%.0f",
                ),
                "מחיר שנמכר (₪)": st.column_config.NumberColumn(format="₪%,d"),
                "מחיר חזוי (₪)":  st.column_config.NumberColumn(format="₪%,d"),
            },
            hide_index=True, use_container_width=True,
        )

        with st.expander("📖 איך לקרוא את הטבלה?"):
            rtl("""
            <table style="width:100%;border-collapse:collapse;">
              <tr style="background:#F5F5F5;">
                <th style="padding:8px;border:1px solid #E0E0E0;text-align:right;">עמודה</th>
                <th style="padding:8px;border:1px solid #E0E0E0;text-align:right;">הסבר</th>
              </tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>ציון כדאיות</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">0–100. עמודה ירוקה = נמכר מתחת לשוק</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מחיר שנמכר</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">הסכום שהקונה שילם בפועל (לא מחיר מבוקש)</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מחיר חזוי</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">מה המודל חשב שהנכס שווה</td></tr>
              <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>שנה</strong></td>
                  <td style="padding:8px;border:1px solid #E0E0E0;">מתי בוצעה העסקה</td></tr>
            </table>
            <p>הטבלה ממוינת מציון כדאיות גבוה לנמוך — העסקאות הכי "טובות" מוצגות ראשונות.</p>
            """)

        with st.expander("📊 גרף התפלגות מחירים"):
            if len(df_filtered) >= 5:
                fig3 = px.histogram(
                    df_filtered, x="dealAmount", nbins=30,
                    title=f"התפלגות מחירים — {selected_city}",
                    labels={"dealAmount": "מחיר (₪)", "count": "כמות עסקאות"},
                    height=350, color_discrete_sequence=["#2A5C21"],
                )
                fig3.update_layout(margin=dict(t=40, b=20), bargap=0.05)
                st.plotly_chart(fig3, use_container_width=True)
                rtl(f"""
                <p style="color:#555;font-size:0.85rem;">
                מחיר מינימום: {df_filtered['dealAmount'].min():,.0f} ₪ &nbsp;|&nbsp;
                חציון: {df_filtered['dealAmount'].median():,.0f} ₪ &nbsp;|&nbsp;
                מחיר מקסימום: {df_filtered['dealAmount'].max():,.0f} ₪
                </p>
                """)
            else:
                st.info("אין מספיק נתונים להצגת גרף עם הפילטרים הנוכחיים.")

    # ══════════════════════════════════════════════════════════════════════════
    # REAL-TIME YAD2 MODE
    # ══════════════════════════════════════════════════════════════════════════
    else:
        df_all_ref  = compute_predictions()
        _all_cities = df_all_ref["settlementNameHeb"].dropna().unique().tolist()
        # Only show cities that have a confirmed Yad2 city ID
        cities_rt   = sorted(c for c in _all_cities if c in _YAD2_CITY_IDS)
        default_rt  = "בת ים" if "בת ים" in cities_rt else (cities_rt[0] if cities_rt else "")

        selected_city_rt = st.selectbox(
            "🏙️ בחר עיר / יישוב", cities_rt,
            index=cities_rt.index(default_rt) if default_rt in cities_rt else 0,
            key="browse_city_rt",
            help="מציג רק ערים הנתמכות בחיפוש יד2.",
        )

        # Invalidate cached data when city changes
        if st.session_state.get("_rt_loaded_city") != selected_city_rt:
            st.session_state.pop("_rt_df", None)
            st.session_state.pop("_rt_error", None)

        col_btn, col_hint = st.columns([1, 4])
        with col_btn:
            load_btn = st.button(
                "🔄 טען נתונים מיד2", type="primary",
                use_container_width=True, key="rt_load_btn",
            )
        with col_hint:
            rtl(
                '<p style="color:#696969;font-size:0.85rem;margin-top:8px;">'
                'הנתונים נשלפים בזמן אמת מיד2. '
                'ציון הכדאיות מחושב ע"י מודל הבינה המלאכותית שלנו מול המחיר המבוקש.'
                '</p>'
            )

        if load_btn:
            with st.spinner(f"טוען מודעות ב{selected_city_rt} מיד2..."):
                df_rt_raw, rt_err = fetch_yad2_city_listings(selected_city_rt)

            if rt_err:
                st.session_state["_rt_error"] = rt_err
                st.session_state.pop("_rt_df", None)
            else:
                # Apply ML model to compute predicted price & viability score
                mdl_rt       = load_model()
                df_ml_rt, _  = load_data()
                feat_cols_rt = [c for c in df_ml_rt.columns if c != "dealAmount"]

                city_mask_rt = df_all_ref["settlementNameHeb"] == selected_city_rt
                sub_ml_rt    = df_ml_rt[city_mask_rt]
                fvec_base_rt = (
                    sub_ml_rt[feat_cols_rt].median()
                    if not sub_ml_rt.empty
                    else df_ml_rt[feat_cols_rt].median()
                )

                today_rt = datetime.date.today()
                preds_rt = []
                for _, row_rt in df_rt_raw.iterrows():
                    fv = fvec_base_rt.copy()
                    if not pd.isna(row_rt.get('שטח (מ"ר)', np.nan)):
                        fv["assetArea"]    = float(row_rt['שטח (מ"ר)'])
                    if not pd.isna(row_rt.get("חדרים", np.nan)):
                        fv["assetRoomNum"] = float(row_rt["חדרים"])
                    if not pd.isna(row_rt.get("קומה", np.nan)):
                        fv["floor_num"]    = float(row_rt["קומה"])
                    fv["deal_year"]  = float(today_rt.year)
                    fv["deal_month"] = float(today_rt.month)
                    try:
                        preds_rt.append(
                            float(mdl_rt.predict(fv[feat_cols_rt].values.reshape(1, -1))[0])
                        )
                    except Exception:
                        preds_rt.append(np.nan)

                df_rt_raw["מחיר חזוי (₪)"] = preds_rt

                def _viab_rt(row):
                    p, pred = row["מחיר מבוקש (₪)"], row["מחיר חזוי (₪)"]
                    if pd.isna(pred) or p <= 0:
                        return 50.0
                    return float(np.clip(50.0 + (pred - p) / p * 100 * 1.5, 0, 100))

                df_rt_raw["ציון כדאיות"]   = df_rt_raw.apply(_viab_rt, axis=1).round(1)
                df_rt_raw["מחיר חזוי (₪)"] = df_rt_raw["מחיר חזוי (₪)"].round(0)
                df_rt_raw                   = df_rt_raw.sort_values("ציון כדאיות", ascending=False)

                st.session_state["_rt_df"]          = df_rt_raw
                st.session_state["_rt_loaded_city"]  = selected_city_rt
                st.session_state.pop("_rt_error", None)

        # ── Error state ───────────────────────────────────────────────────────
        if st.session_state.get("_rt_error"):
            st.warning(f"⚠️ {st.session_state['_rt_error']}")
            rtl(
                '<p style="color:#696969;font-size:0.85rem;">'
                'טיפ: נסה שוב בעוד כמה דקות, או השתמש ב<strong>נתונים היסטוריים</strong> שתמיד זמינים.'
                '</p>'
            )

        # ── Data loaded — show results ────────────────────────────────────────
        elif "_rt_df" in st.session_state and st.session_state.get("_rt_loaded_city") == selected_city_rt:
            df_rt = st.session_state["_rt_df"].copy()

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric("מודעות פעילות", len(df_rt),
                       help="כמה מודעות יד2 פעילות נמצאו בעיר זו.")
            _avg_p = df_rt["מחיר מבוקש (₪)"].mean()
            sm2.metric("מחיר ממוצע מבוקש", f"{_avg_p:,.0f} ₪",
                       help="ממוצע המחירים המבוקשים — טרם עסקה סגורה.")
            _avg_s = df_rt['שטח (מ"ר)'].dropna().mean() if 'שטח (מ"ר)' in df_rt.columns else np.nan
            sm3.metric("שטח ממוצע",
                       f"{_avg_s:.0f} מ\"ר" if not pd.isna(_avg_s) else "—",
                       help="שטח ממוצע של הדירות המוצעות.")
            _avg_v = df_rt["ציון כדאיות"].mean()
            sm4.metric("ציון כדאיות ממוצע", f"{_avg_v:.1f} / 100",
                       help="מעל 50 = בממוצע המחיר מתחת להערכת המודל.")

            # ── Filters ───────────────────────────────────────────────────────
            st.markdown("---")
            rtl('<h3>סינון מודעות</h3>')

            _price_col = "מחיר מבוקש (₪)"
            _area_col  = 'שטח (מ"ר)'
            _rooms_col = "חדרים"
            df_rt_filtered = df_rt.copy()

            _pv = df_rt[_price_col].dropna()
            _rv = df_rt[_rooms_col].dropna()
            _rv = _rv[(_rv >= 1) & (_rv <= 10)]
            _av = df_rt[_area_col].dropna()
            _av = _av[(_av >= 20) & (_av <= 600)]

            # Row 1 — price (min / max) + rooms (min / max)
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                p_from = st.number_input(
                    "💰 מחיר מינימום (₪ מ')",
                    min_value=0.0, max_value=200.0,
                    value=round(float(_pv.min()) / 1e6, 1) if len(_pv) else 0.0,
                    step=0.1, format="%.1f", key="rt_p_from",
                )
            with fc2:
                p_to = st.number_input(
                    "מחיר מקסימום (₪ מ')",
                    min_value=0.0, max_value=200.0,
                    value=round(float(_pv.max()) / 1e6 + 0.1, 1) if len(_pv) else 200.0,
                    step=0.1, format="%.1f", key="rt_p_to",
                )
            with fc3:
                r_from = st.number_input(
                    "🛏️ חדרים מינימום",
                    min_value=1.0, max_value=10.0,
                    value=float(_rv.min()) if len(_rv) else 1.0,
                    step=0.5, format="%.1f", key="rt_r_from",
                )
            with fc4:
                r_to = st.number_input(
                    "חדרים מקסימום",
                    min_value=1.0, max_value=10.0,
                    value=float(_rv.max()) if len(_rv) else 10.0,
                    step=0.5, format="%.1f", key="rt_r_to",
                )

            # Row 2 — area (min / max)
            fa1, fa2, _, _ = st.columns(4)
            with fa1:
                a_from = st.number_input(
                    '📐 שטח מינימום (מ"ר)',
                    min_value=0, max_value=1000,
                    value=int(_av.min()) if len(_av) else 0,
                    step=5, key="rt_a_from",
                )
            with fa2:
                a_to = st.number_input(
                    'שטח מקסימום (מ"ר)',
                    min_value=0, max_value=1000,
                    value=int(_av.max()) + 5 if len(_av) else 1000,
                    step=5, key="rt_a_to",
                )

            # Apply all filters
            if len(_pv):
                df_rt_filtered = df_rt_filtered[
                    df_rt_filtered[_price_col].between(p_from * 1e6, p_to * 1e6)
                ]
            if len(_rv):
                df_rt_filtered = df_rt_filtered[
                    df_rt_filtered[_rooms_col].isna() |
                    df_rt_filtered[_rooms_col].between(r_from, r_to)
                ]
            if len(_av):
                df_rt_filtered = df_rt_filtered[
                    df_rt_filtered[_area_col].isna() |
                    df_rt_filtered[_area_col].between(a_from, a_to)
                ]

            df_rt_filtered = df_rt_filtered.sort_values("ציון כדאיות", ascending=False)
            rtl(f'<p><strong>{len(df_rt_filtered)} מודעות</strong> מוצגות — מדורגות מהכדאית ביותר</p>')

            # Build display table — drop שכונה (Yad2 returns regional area name, same for all rows)
            show_rt = df_rt_filtered.copy()
            if "מחיר חזוי (₪)" in show_rt.columns:
                show_rt["מחיר חזוי (₪)"] = show_rt["מחיר חזוי (₪)"].round(0).astype("Int64")
            if _area_col in show_rt.columns:
                show_rt[_area_col] = show_rt[_area_col].round(0).astype("Int64")
            if "קומה" in show_rt.columns:
                try:
                    show_rt["קומה"] = show_rt["קומה"].round(0).astype("Int64")
                except Exception:
                    pass
            if "_yad2_id" in show_rt.columns:
                show_rt["🔗 קישור"] = show_rt["_yad2_id"].apply(
                    lambda i: f"https://www.yad2.co.il/item/{i}" if i else ""
                )

            rt_disp_cols = [c for c in [
                "רחוב", "מס' בית", 'שטח (מ"ר)', "חדרים", "קומה",
                "מחיר מבוקש (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "🔗 קישור",
            ] if c in show_rt.columns]

            st.dataframe(
                show_rt[rt_disp_cols].head(50),
                column_config={
                    "ציון כדאיות": st.column_config.ProgressColumn(
                        "ציון כדאיות (0-100)", min_value=0, max_value=100, format="%.0f",
                    ),
                    "מחיר מבוקש (₪)": st.column_config.NumberColumn(format="₪%,d"),
                    "מחיר חזוי (₪)":  st.column_config.NumberColumn(format="₪%,d"),
                    "🔗 קישור": st.column_config.LinkColumn("🔗 יד2", display_text="פתח מודעה"),
                },
                hide_index=True, use_container_width=True,
            )

            with st.expander("📖 איך לקרוא את הטבלה?"):
                rtl("""
                <table style="width:100%;border-collapse:collapse;">
                  <tr style="background:#F5F5F5;">
                    <th style="padding:8px;border:1px solid #E0E0E0;text-align:right;">עמודה</th>
                    <th style="padding:8px;border:1px solid #E0E0E0;text-align:right;">הסבר</th>
                  </tr>
                  <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>ציון כדאיות</strong></td>
                      <td style="padding:8px;border:1px solid #E0E0E0;">0–100. ירוק = מחיר מתחת להערכת המודל = הזדמנות</td></tr>
                  <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מחיר מבוקש</strong></td>
                      <td style="padding:8px;border:1px solid #E0E0E0;">מה המוכר דורש — עדיין לא עסקה סגורה</td></tr>
                  <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>מחיר חזוי</strong></td>
                      <td style="padding:8px;border:1px solid #E0E0E0;">מה המודל מעריך שהנכס שווה לפי עסקאות היסטוריות</td></tr>
                  <tr><td style="padding:8px;border:1px solid #E0E0E0;"><strong>קישור</strong></td>
                      <td style="padding:8px;border:1px solid #E0E0E0;">לחץ לפתיחת המודעה המלאה ביד2</td></tr>
                </table>
                <p>הטבלה ממוינת מציון כדאיות גבוה לנמוך. שים לב: מחיר מבוקש ≠ מחיר עסקה סופי.</p>
                """)

            with st.expander("📊 גרף התפלגות מחירים"):
                if len(df_rt_filtered) >= 5:
                    fig_rt = px.histogram(
                        df_rt_filtered, x="מחיר מבוקש (₪)", nbins=25,
                        title=f"התפלגות מחירים מבוקשים — {selected_city_rt}",
                        labels={"מחיר מבוקש (₪)": "מחיר מבוקש (₪)", "count": "כמות מודעות"},
                        height=350, color_discrete_sequence=["#E25252"],
                    )
                    fig_rt.update_layout(margin=dict(t=40, b=20), bargap=0.05)
                    st.plotly_chart(fig_rt, use_container_width=True)
                    rtl(f"""
                    <p style="color:#555;font-size:0.85rem;">
                    מחיר מינימום: {df_rt_filtered['מחיר מבוקש (₪)'].min():,.0f} ₪ &nbsp;|&nbsp;
                    חציון: {int(df_rt_filtered['מחיר מבוקש (₪)'].median()):,.0f} ₪ &nbsp;|&nbsp;
                    מחיר מקסימום: {df_rt_filtered['מחיר מבוקש (₪)'].max():,.0f} ₪
                    </p>
                    """)
                else:
                    st.info("אין מספיק נתונים להצגת גרף עם הפילטרים הנוכחיים.")

        # ── Empty state — waiting for user to press the load button ──────────
        else:
            rtl("""
            <div dir="rtl" style="background:oklch(96% 0.015 155);border:1px solid oklch(27% 0.12 155);border-radius:10px;
                 padding:20px 24px;text-align:right;margin:16px 0;">
              <p style="font-size:1.1rem;font-weight:700;color:oklch(27% 0.12 155);">📡 מצב בזמן אמת</p>
              <p>לחץ <strong>טען נתונים מיד2</strong> כדי לשלוף את המודעות הפעילות כעת בעיר שבחרת.</p>
              <p style="color:#555;font-size:0.88rem;">
                הנתונים נשלפים ישירות מאתר יד2 ועשויים להשתנות בכל רגע.<br>
                ציון הכדאיות מחושב ע"י מודל הבינה המלאכותית שלנו מול המחיר המבוקש.
              </p>
            </div>
            """)
