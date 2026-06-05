"""
יועץ נדל"ן חכם — Real Estate Investment Advisor
Run:  streamlit run app.py
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

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE          = pathlib.Path(__file__).parent
MODEL_PATH    = BASE / "model.pkl"
APT_ML_PATH   = BASE / "DATA_FILES" / "apartments_ml_ready.csv"
APT_DISP_PATH = BASE / "DATA_FILES" / "apartments_display.csv"
POI_PATH      = BASE / "DATA_FILES" / "ISRAEL_POINTS_FILTERED_GEO.csv"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='יועץ נדל"ן חכם',
    layout="wide",
    page_icon="🏠",
)

st.markdown("""
<style>
  /* ── Metrics ─────────────────────────────────────────────────────────── */
  [data-testid="stMetricValue"]    { font-size: 1.65rem !important; font-weight: 800; }
  [data-testid="stMetricLabel"]    { font-size: .78rem; color: #555; }
  [data-testid="metric-container"] {
    background: #f7f9fc;
    border: 1px solid #dde3ea;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  }

  /* ── Layout ──────────────────────────────────────────────────────────── */
  .block-container { padding-top: 0.5rem; padding-bottom: 2rem; }
  hr               { margin: 1.2rem 0; border-color: #e5e7eb; }
  label            { font-weight: 600 !important; }

  /* ── GLOBAL RTL — set on the whole main section ──────────────────────── */
  /* This is the only reliable way to override Streamlit's Base Web styles  */
  section[data-testid="stMain"],
  section[data-testid="stMain"] * {
    direction: rtl !important;
    text-align: right !important;
  }

  /* ── LTR exceptions — things that must stay left-to-right ───────────── */
  /* Number / text inputs: digits should stay LTR                          */
  input, textarea,
  [data-baseweb="input"] input,
  [data-baseweb="textarea"] textarea {
    direction: ltr !important;
    text-align: left !important;
  }
  /* Plotly charts, iframes, maps: leave untouched                        */
  .js-plotly-plot,
  .js-plotly-plot *,
  iframe,
  [data-testid="stIFrame"] { direction: ltr !important; }

  /* Sliders: the track & thumb are visual — keep them LTR internally     */
  [data-baseweb="slider"] [role="slider"] { direction: ltr !important; }

  /* Progress bars inside dataframes                                      */
  [data-testid="stDataFrameContainer"] { direction: ltr !important; }
  [data-testid="stDataFrameContainer"] * { direction: ltr !important; text-align: left !important; }
</style>
""", unsafe_allow_html=True)

# ── Header banner ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  background: linear-gradient(135deg, #0f3460 0%, #1a5276 100%);
  color: white;
  padding: 22px 32px;
  border-radius: 12px;
  margin-bottom: 8px;
  direction: rtl;
">
  <h1 style="margin:0; font-size:1.85rem; font-weight:800;">🏠 יועץ נדל&quot;ן חכם</h1>
  <p style="margin:6px 0 0; opacity:0.82; font-size:0.95rem;">
    כלי ML לאיתור הזדמנויות השקעה · אזורים &nbsp;|&nbsp; נכסים &nbsp;|&nbsp; עסקאות
  </p>
</div>
""", unsafe_allow_html=True)


@st.cache_data
def compute_settlement_stats(ml_path: str, disp_path: str, mdl_path: str) -> pd.DataFrame:
    mdl   = joblib.load(mdl_path)
    df_ml = pd.read_csv(ml_path,   encoding="utf-8-sig")
    df_d  = pd.read_csv(disp_path, encoding="utf-8-sig")

    X             = df_ml.drop(columns=["dealAmount"])
    df_d          = df_d.copy()
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

    agg_dict = dict(
        avg_price  = ("dealAmount",      "mean"),
        avg_gap    = ("gap_pct",         "mean"),
        deal_count = ("dealAmount",      "count"),
        avg_socio  = ("socio_index_avg", "mean"),
    )
    if "N" in df_d.columns and "E" in df_d.columns:
        agg_dict["avg_lat"] = ("N", "mean")
        agg_dict["avg_lon"] = ("E", "mean")

    stats = df_d.groupby("settlementNameHeb").agg(**agg_dict).join(trend_s).reset_index()

    return stats


@st.cache_resource
def load_model_cached(mdl_path: str):
    return joblib.load(mdl_path)


@st.cache_data
def load_dataframes(ml_path: str, disp_path: str):
    df_ml = pd.read_csv(ml_path,   encoding="utf-8-sig")
    df_d  = pd.read_csv(disp_path, encoding="utf-8-sig")
    return df_ml, df_d


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


def _get_str(d: dict, *keys) -> str | None:
    for k in keys:
        v = d.get(k)
        if v and isinstance(v, str):
            return v.strip()
    return None


def _meta(html: str, prop: str) -> str | None:
    """Extract og/name meta tag content."""
    m = re.search(
        rf'<meta[^>]+(?:property|name)=["\'](?:og:)?{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    ) or re.search(
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:)?{re.escape(prop)}["\']',
        html, re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def _parse_yad2_html(html: str) -> dict:
    """Parse a Yad2 listing page HTML → data dict. Used by both scraper and manual paste."""
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        # Maybe user pasted just the raw JSON (not full HTML)
        raw = html.strip()
        if raw.startswith("{"):
            try:
                json.loads(raw)
                m = type("_M", (), {"group": lambda self, i: raw})()
            except json.JSONDecodeError:
                pass
    if not m:
        # ── Last resort: extract from meta tags ───────────────────────────────
        title = _meta(html, "title") or ""
        desc  = _meta(html, "description") or ""
        combined = title + " " + desc

        # Rooms from description
        rm = re.search(r'(\d+(?:\.\d)?)\s*חדרים', combined)
        rooms = float(rm.group(1)) if rm else None

        # City / neighborhood / street from title pattern:
        # "דירה, רחוב מספר, שכונה, עיר | ..."
        parts = [p.strip() for p in title.split(",")]
        city = hood = street = None
        if len(parts) >= 4:
            street_raw = parts[1]          # "עגנון 4"
            hood   = parts[2]
            city   = parts[3].split("|")[0].strip()
            sm = re.match(r'^(.+?)\s+(\d+)$', street_raw)
            street = sm.group(1) if sm else street_raw

        if rooms or city:
            return {
                "price": None, "rooms": rooms, "area": None, "floor": None,
                "city": city, "neighborhood": hood, "street": street,
                "lat": None, "lon": None,
                "error": "נמצאו פרטים חלקיים ממטא-טאגים — חסר מחיר. השלם ידנית.",
                "needs_manual": True,
            }
        return {"error": "לא נמצא __NEXT_DATA__ — ודא שהדבקת את קוד המקור המלא של הדף (Ctrl+U → Ctrl+A → Ctrl+C).", "needs_manual": True}

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"error": "שגיאה בפענוח JSON.", "needs_manual": True}

    pp      = data.get("props", {}).get("pageProps", {})
    listing = None

    # ── New YAD2 structure: dehydratedState > queries[0] > state > data ───────
    try:
        listing = pp["dehydratedState"]["queries"][0]["state"]["data"]
    except (KeyError, IndexError, TypeError):
        pass

    # ── Legacy fallback paths ──────────────────────────────────────────────────
    if not listing:
        for path in [["listing"], ["item"], ["itemData"], ["listingData"], ["ad"]]:
            try:
                obj = pp
                for k in path:
                    obj = obj[k]
                if isinstance(obj, dict) and ("price" in obj or "priceOnly" in obj):
                    listing = obj
                    break
            except (KeyError, TypeError):
                continue

    if not listing:
        return {"error": "מבנה הנתונים לא מוכר.", "needs_manual": True}

    # ── Extract fields ────────────────────────────────────────────────────────
    price = _get_num(listing, "price", "priceOnly", "priceFormatted")

    addr  = listing.get("address") or {}
    add_d = listing.get("additionalDetails") or {}
    inp   = listing.get("inProperty") or {}

    # New structure: address.city / .neighborhood / .street are dicts with "text"
    def _txt(d, *keys):
        for k in keys:
            v = d.get(k)
            if isinstance(v, dict):
                t = v.get("text") or v.get("textHeb")
                if t and isinstance(t, str):
                    return t.strip()
            if v and isinstance(v, str):
                return v.strip()
        return None

    city   = _txt(addr, "city")   or _get_str(listing, "city", "cityHeb")
    street = _txt(addr, "street") or _get_str(listing, "street", "streetHeb")
    hood   = _txt(addr, "neighborhood") or _get_str(listing, "neighborhood")

    # Floor: address.house.floor takes priority
    house = addr.get("house") or {}
    floor = (_get_num(house, "floor")
             or _get_num(add_d, "floor", "floorFormatted")
             or _get_num(listing, "floor"))

    # Rooms: additionalDetails.roomsCount
    rooms = (_get_num(add_d, "roomsCount", "rooms", "roomNum")
             or _get_num(inp, "rooms")
             or _get_num(listing, "rooms", "roomNum"))

    # Area: additionalDetails.squareMeter
    area  = (_get_num(add_d, "squareMeter", "area", "meter")
             or _get_num(inp, "squareMeter", "area")
             or _get_num(listing, "squareMeter", "area", "meter"))

    # Exact GPS coords from address.coords (WGS84) — use for map pin
    coords_d = addr.get("coords") or {}
    lat = coords_d.get("lat")
    lon = coords_d.get("lon")

    if not price:
        return {"error": "לא נמצא מחיר במודעה.", "needs_manual": True}

    return {
        "price": price, "rooms": rooms, "area": area, "floor": floor,
        "city": city, "neighborhood": hood, "street": street,
        "lat": lat, "lon": lon,
    }


def scrape_yad2_listing(url: str) -> dict:
    """Fetch a YAD2 item page and parse it. Returns data dict or {"error": ..., "needs_manual": bool}."""
    if not re.search(r"yad2\.co\.il/.*item/", url):
        return {"error": "הקישור אינו תקין — חייב להיות קישור לנכס ב-yad2.co.il", "needs_manual": False}

    import time as _time
    html = None
    _extra_headers = {
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        from curl_cffi import requests as _cr
        for _attempt, _ver in enumerate(["chrome133", "chrome131", "chrome124", "chrome120", "chrome116"]):
            try:
                if _attempt:
                    _time.sleep(1.5)
                s = _cr.Session(impersonate=_ver)
                s.headers.update(_extra_headers)
                resp = s.get(url, timeout=25)
                if resp.status_code == 200 and len(resp.text) > 5000:
                    html = resp.text
                    break
            except Exception:
                continue
    except ImportError:
        pass
    if html is None:
        try:
            resp = requests.get(url, headers={**_YAD2_HEADERS, **_extra_headers}, timeout=15)
            html = resp.text
        except Exception:
            return {"error": "שגיאת חיבור — בדוק חיבור לאינטרנט ונסה שוב.", "needs_manual": True}

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

    # Normalise typographic / Hebrew special characters to plain ASCII equivalents
    text = (text
        .replace("״", '"')   # ״ Hebrew gershayim  →  "
        .replace("׳", "'")   # ׳ Hebrew geresh     →  '
        .replace("’", "'")   # ' right single quote
        .replace("‘", "'")   # ' left  single quote
        .replace("“", '"')   # " left  double quote
        .replace("”", '"')   # " right double quote
        .replace(" ", " ")   # non-breaking space
        .replace("–", "-")   # en-dash
        .replace("—", "-")   # em-dash
    )

    # ── Price ──────────────────────────────────────────────────────────────────
    price = None
    for pat in [
        r'([\d]{1,3}(?:,[\d]{3})+)\s*₪',         # 1,800,000 ₪
        r'₪\s*([\d]{1,3}(?:,[\d]{3})+)',           # ₪ 1,800,000
        r'([\d]{4,7})\s*₪',                        # 1800000 ₪
        r'₪\s*([\d]{4,7})',                         # ₪ 1800000
        r'([\d]{1,3}(?:,[\d]{3})+)\s*שקל',        # 1,800,000 שקל
        r'מחיר[:\s]*([\d,]+)',                      # מחיר: 1,800,000
        r'(?:^|[-—|\s])([\d]{1,3}(?:,[\d]{3})+)(?=\s|$|[.,\-])',  # כותרת ללא ₪
    ]:
        m = re.search(pat, text, re.MULTILINE)
        if m:
            try:
                v = float(m.group(1).replace(",", ""))
                if v >= 50_000:
                    price = v
                    break
            except (ValueError, TypeError):
                pass
    if not price:
        m = re.search(r'([\d]+(?:[.,][\d]+)?)\s*מיליון', text)
        if m:
            try:
                price = float(m.group(1).replace(",", ".")) * 1_000_000
            except (ValueError, TypeError):
                pass

    # ── Rooms ──────────────────────────────────────────────────────────────────
    rooms = None
    for pat in [
        r'(\d+[.,]\d)\s*חדרים',       # "2,5 חדרים" or "2.5 חדרים" — explicit half-room first
        r'(\d+[.,]\d)\s*חד',           # "2,5 חד'"
        r'(\d+)\s*חדרים',              # "4 חדרים"
        r'(\d+)\s*חד\'',               # "4 חד'"
        r'חדרים[:\s]*(\d+[.,]?\d?)',
        r'rooms?[:\s]*(\d+(?:\.\d)?)',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                rooms = float(m.group(1).replace(",", "."))
                break
            except (ValueError, TypeError):
                pass

    # ── Area ───────────────────────────────────────────────────────────────────
    area = None
    for pat in [
        r'(\d+)\s*מ"ר',            # after normalisation ״→" this always works
        r"(\d+)\s*מ''",
        r"(\d+)\s*מ'",
        r'(\d+)\s*מטר\s*(?:רבוע)?',
        r'שטח[:\s]*(?:כ-?\s*)?(\d+)',
        r'(?:כ-?\s*)(\d+)\s*מ',   # "כ-53 מ..."
        r'(\d+)\s*sqm',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1))
                if 10 <= v <= 1000:
                    area = v
                    break
            except (ValueError, TypeError):
                pass

    # ── Floor ──────────────────────────────────────────────────────────────────
    floor = None
    for pat in [r'קומה\s*(\d+)', r'(\d+)\s*קומה', r'floor[:\s]*(\d+)']:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                floor = float(m.group(1))
                break
            except (ValueError, TypeError):
                pass
    if floor is None:
        for word, num in _HEB_FLOOR_ORDINALS.items():
            if re.search(rf'קומה\s+{word}', text):
                floor = float(num)
                break

    # ── City ───────────────────────────────────────────────────────────────────
    city = None
    for c in _HEB_CITIES:
        if c in text:
            city = c
            break

    return {
        "price": price, "rooms": rooms, "area": area, "floor": floor,
        "city": city, "neighborhood": None, "street": None,
        "lat": None, "lon": None,
    }


def scrape_facebook_listing(url: str) -> dict:
    """
    Attempt to scrape a Facebook Marketplace real-estate listing.
    Facebook almost always blocks unauthenticated access — when that happens,
    returns needs_paste=True to prompt the user to paste the description text.
    """
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
                if _attempt:
                    _time.sleep(1)
                resp = _cr.Session(impersonate=_ver).get(url, timeout=25)
                html = resp.text
                break
            except Exception:
                continue
    except ImportError:
        pass

    if html is None:
        try:
            resp = requests.get(url, headers=fb_headers, timeout=15)
            html = resp.text
        except Exception:
            return {
                "error": "לא ניתן להגיע ל-Facebook.",
                "needs_manual": True, "needs_paste": True,
            }

    _FB_BLOCKED_SIGNALS = [
        "log in to facebook", "create new account", "you must log in",
        "login_form", "sorry, something went wrong", "error facebook",
    ]
    if any(kw in html[:5000].lower() for kw in _FB_BLOCKED_SIGNALS):
        return {
            "error": "Facebook דורש התחברות לצפייה במודעה זו.",
            "needs_manual": True, "needs_paste": True,
        }

    # ── Try to extract text from OG meta tags ──────────────────────────────────
    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']', html)
    og_desc  = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']', html)

    # ── Try to extract description from embedded JSON ──────────────────────────
    json_desc = None
    for pat in [r'"body"\s*:\s*\{"text"\s*:\s*"([^"]{20,})"',
                r'"description"\s*:\s*"([^"]{20,})"',
                r'"listing_description"\s*:\s*"([^"]{20,})"']:
        jm = re.search(pat, html)
        if jm:
            json_desc = jm.group(1).encode().decode("unicode_escape", errors="ignore")
            break

    # ── Try structured price from JSON ─────────────────────────────────────────
    json_price = None
    for pat in [r'"listing_price"[^}]*"amount"\s*:\s*"?([\d.]+)"?',
                r'"price_value"\s*:\s*"?([\d,]+)"?',
                r'"formatted_amount"\s*:\s*"([\d,]+)"']:
        jm = re.search(pat, html)
        if jm:
            try:
                v = float(jm.group(1).replace(",", ""))
                if v >= 50_000:
                    json_price = v
            except (ValueError, TypeError):
                pass
            if json_price:
                break

    text = " ".join(filter(None, [
        og_title.group(1) if og_title else "",
        og_desc.group(1)  if og_desc  else "",
        json_desc or "",
    ]))

    if not text.strip() and not json_price:
        return {
            "error": "לא ניתן לחלץ פרטים מ-Facebook.",
            "needs_manual": True, "needs_paste": True,
        }

    result = _parse_realestate_text(text)
    if json_price:
        result["price"] = json_price

    if not result["price"]:
        return {
            "error": "לא נמצא מחיר במודעה.",
            "needs_manual": True, "needs_paste": True,
        }

    return result


def scrape_listing(url: str) -> dict:
    """Route to the correct scraper based on the listing URL."""
    if re.search(r"yad2\.co\.il/.*item/", url):
        return scrape_yad2_listing(url)
    if re.search(r"facebook\.com/marketplace/item/|fb\.com/marketplace/item/", url):
        return scrape_facebook_listing(url)
    return {
        "error": "הקישור אינו תקין — יש להזין קישור מ-yad2.co.il או Facebook Marketplace",
        "needs_manual": False,
    }


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
    "transport":  "תחבורה",
    "education":  "חינוך",
    "health":     "בריאות",
    "park":       "פארקים",
    "retail":     "קניות",
    "food":       "מזון",
    "service":    "שירותים",
    "leisure":    "פנאי",
    "tourism":    "תיירות",
    "community":  "קהילה",
    "nature":     "טבע",
    "historic":   "היסטוריה",
    "employment": "תעסוקה",
}

_CAT_EMOJI = {
    "transport": "🚌", "education": "🎓", "health": "🏥",
    "park": "🌳", "retail": "🛒", "food": "🍽️",
    "service": "🏛️", "leisure": "🎭", "tourism": "🏛️",
    "community": "⛪", "nature": "🌿", "historic": "🏰",
    "employment": "🏢",
}


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


def _match_settlement(city: str | None, settlements: list) -> str | None:
    """Fuzzy-match a YAD2 city name against our settlement list.
    Handles Hebrew spelling variants (double yod/vav, geresh, whitespace)."""
    import difflib
    if not city:
        return None

    def _norm(s: str) -> str:
        s = s.strip().replace("\xa0", " ").replace("-", " ").replace("–", " ")
        return " ".join(s.split()).lower()

    def _norm_he(s: str) -> str:
        s = _norm(s)
        s = s.replace("יי", "י")   # double yod → single  (נהרייה → נהריה)
        s = s.replace("וו", "ו")   # double vav → single
        s = s.replace("'", "").replace('"', "")   # geresh / gershayim
        return s

    c_norm    = _norm(city)
    c_norm_he = _norm_he(city)

    # 1. Exact basic normalisation
    for s in settlements:
        if _norm(s) == c_norm:
            return s

    # 2. Hebrew spelling variants (yy/vv collapse)
    for s in settlements:
        if _norm_he(s) == c_norm_he:
            return s

    # 3. Substring
    for s in settlements:
        s_n = _norm(s)
        if c_norm in s_n or s_n in c_norm:
            return s

    # 4. Fuzzy — difflib on Hebrew-normalised strings (cutoff 0.82)
    norm_he_map = {_norm_he(s): s for s in settlements}
    close = difflib.get_close_matches(c_norm_he, norm_he_map.keys(), n=1, cutoff=0.82)
    if close:
        return norm_he_map[close[0]]

    return None


@st.cache_data(ttl=86_400, show_spinner=False)
def geocode_address(query: str) -> tuple:
    """Geocode an Israeli address/city via Nominatim (free, no API key).
    Returns (lat, lon) or (None, None). Results are cached for 24 h."""
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


@st.cache_data
def load_display_data(disp_path: str) -> pd.DataFrame:
    return pd.read_csv(disp_path, encoding="utf-8-sig")


@st.cache_data
def compute_all_predictions(ml_path: str, disp_path: str, mdl_path: str) -> pd.DataFrame:
    mdl   = joblib.load(mdl_path)
    df_ml = pd.read_csv(ml_path,   encoding="utf-8-sig")
    df_d  = pd.read_csv(disp_path, encoding="utf-8-sig")

    X             = df_ml.drop(columns=["dealAmount"])
    df_d          = df_d.copy()
    df_d["predicted"] = mdl.predict(X)
    df_d["gap_pct"]   = (df_d["predicted"] - df_d["dealAmount"]) / df_d["dealAmount"] * 100

    # Score anchored at 50 (gap=0% → 50, every +1% gap → +1.5 pts), clipped to [0,100]
    df_d["viability_score"] = (50 + df_d["gap_pct"] * 1.5).clip(0, 100).round(1)

    return df_d


@st.cache_data
def get_settlement_baselines(ml_path: str, disp_path: str) -> pd.DataFrame:
    df_ml = pd.read_csv(ml_path,   encoding="utf-8-sig")
    df_d  = pd.read_csv(disp_path, encoding="utf-8-sig")
    df_ml = df_ml.copy()
    df_ml["settlementNameHeb"] = df_d["settlementNameHeb"]
    return df_ml.groupby("settlementNameHeb").median()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_profile, tab_mode_a, tab_mode_b_settle, tab_mode_b, tab_mode_c, tab_explain = st.tabs([
    "פרופיל 👤",
    "מצב א׳ — המלצת אזורים 🗺️",
    "מצב ב׳ — נכסים ביישוב 🏘️",
    "מצב ג׳ — הערכת נכס ספציפי 💡",
    "מצב ד׳ — בדיקת עסקה 🔍",
    "הסברים 📖",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — INVESTOR PROFILE
# ══════════════════════════════════════════════════════════════════════════════
with tab_profile:
    st.markdown("## 👤 פרופיל משקיע")
    st.caption("הגדר את פרופיל ההשקעה שלך — הוא ישמש בכל המצבים.")

    with st.container(border=True):
        r1c1, r1c2, r1c3 = st.columns(3)
        r2c1, r2c2, r2c3 = st.columns(3)

        with r1c1:
            st.number_input(
                "תקציב מקסימום (₪)",
                min_value=300_000, max_value=10_000_000,
                value=2_000_000, step=100_000, format="%d",
                key="budget_max",
            )
        with r1c2:
            st.selectbox("מטרת השקעה", ["תשואה שוטפת", "עליית ערך"], key="investment_goal")
        with r1c3:
            st.selectbox("רמת סיכון מועדפת", ["שוק מבוסס", "שוק מתפתח"], key="risk_level")
        with r2c1:
            st.selectbox("אופק השקעה", ["קצר (1-3 שנה)", "ארוך (5+ שנה)"], key="horizon")
        with r2c2:
            st.slider(
                "תשואה שנתית מינימלית (%)",
                min_value=0, max_value=20, value=5, key="min_yield",
                help="מסנן יישובים שהתשואה השנתית המשוערת שלהם נמוכה מהסף",
            )
        with r2c3:
            st.slider(
                "מינ' עסקאות ביישוב",
                min_value=5, max_value=50, value=10, key="min_deals",
                help="מינימום עסקאות ביישוב — אינדיקטור לנזילות השוק",
            )

    st.divider()
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("תקציב",        f"{st.session_state.get('budget_max', 2_000_000):,.0f} ₪")
    s2.metric("מטרה",         st.session_state.get("investment_goal", "תשואה שוטפת"))
    s3.metric("סיכון",        st.session_state.get("risk_level",      "שוק מבוסס"))
    s4.metric("אופק",         st.session_state.get("horizon",         "קצר (1-3 שנה)"))
    s5.metric("תשואה מינ'",   f"{st.session_state.get('min_yield', 5)}%")
    s6.metric("מינ' עסקאות",  st.session_state.get("min_deals", 10))

    st.info("עבור למצב א׳ כדי לראות המלצות אזורים לפי הפרופיל.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MODE A: AREA RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_a:
    st.markdown("## 🗺️ מצב א׳ — המלצת אזורים")

    stats = compute_settlement_stats(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # ── Read profile from session_state ──────────────────────────────────────
    budget_max      = st.session_state.get("budget_max",      2_000_000)
    investment_goal = st.session_state.get("investment_goal", "תשואה שוטפת")
    risk_level      = st.session_state.get("risk_level",      "שוק מבוסס")
    horizon         = st.session_state.get("horizon",         "קצר (1-3 שנה)")
    min_yield       = st.session_state.get("min_yield",       5)
    min_deals       = st.session_state.get("min_deals",       10)

    st.caption(
        f"פרופיל פעיל: תקציב {budget_max:,.0f} ₪ · {investment_goal} · {risk_level} · {horizon}"
    )
    st.divider()

    # ── Filter by profile ─────────────────────────────────────────────────────
    HORIZON_YEARS = {"קצר (1-3 שנה)": 2, "ארוך (5+ שנה)": 7}
    h_yrs = HORIZON_YEARS.get(horizon, 2)

    filtered = stats[stats["avg_price"] <= budget_max].copy()

    socio_med = stats["avg_socio"].median()
    if risk_level == "שוק מבוסס":
        filtered = filtered[filtered["avg_socio"] >= socio_med]
    else:
        filtered = filtered[filtered["avg_socio"] < socio_med]

    filtered = filtered[filtered["deal_count"] >= min_deals].copy()

    # Estimated annual yield = gap spread over horizon + annual price trend
    filtered["est_yield_pct"] = (filtered["avg_gap"] / h_yrs + filtered["trend_pct_yr"]).round(1)
    filtered = filtered[filtered["est_yield_pct"] >= min_yield].copy()

    if filtered.empty:
        st.warning("לא נמצאו יישובים התואמים לפרופיל. נסה להרחיב את הפרמטרים.")
    else:
        # ── Compute viability score ───────────────────────────────────────────
        def _minmax(s: pd.Series) -> pd.Series:
            lo, hi = s.min(), s.max()
            return pd.Series(50.0, index=s.index) if hi == lo else (s - lo) / (hi - lo) * 100

        gap_sc   = _minmax(filtered["avg_gap"])
        trend_sc = _minmax(filtered["trend_pct_yr"])
        liq_sc   = _minmax(filtered["deal_count"])

        if investment_goal == "תשואה שוטפת":
            w_gap, w_trend, w_liq = 0.6, 0.2, 0.2
        else:
            w_gap, w_trend, w_liq = 0.3, 0.5, 0.2

        filtered["viability_score"] = (
            w_gap * gap_sc + w_trend * trend_sc + w_liq * liq_sc
        ).round(1)

        filtered = filtered.sort_values("viability_score", ascending=False)

        # ── Metrics row ───────────────────────────────────────────────────────
        top = filtered.iloc[0]
        ma1, ma2, ma3, ma4, ma5 = st.columns(5)
        ma1.metric("יישובים שנמצאו",        len(filtered))
        ma2.metric("ציון מקסימלי",           f"{top['viability_score']:.0f} / 100")
        ma3.metric("מחיר ממוצע — מוביל",     f"{top['avg_price']:,.0f} ILS")
        ma4.metric("פער ממוצע — מוביל",      f"{top['avg_gap']:+.1f}%")
        ma5.metric("תשואה משוערת — מוביל",   f"{top['est_yield_pct']:+.1f}%/שנה")

        # ── Table ─────────────────────────────────────────────────────────────
        show = filtered.rename(columns={
            "settlementNameHeb": "יישוב",
            "viability_score":   "ציון כדאיות",
            "avg_price":         "מחיר ממוצע (₪)",
            "avg_gap":           "פער ממוצע (%)",
            "est_yield_pct":     "תשואה משוערת (%/שנה)",
            "trend_pct_yr":      "מגמה (%/שנה)",
            "deal_count":        "עסקאות",
            "avg_socio":         "מדד סוציו",
        }).copy()

        show["מחיר ממוצע (₪)"]      = show["מחיר ממוצע (₪)"].round(0).astype(int)
        show["פער ממוצע (%)"]        = show["פער ממוצע (%)"].round(1)
        show["תשואה משוערת (%/שנה)"] = show["תשואה משוערת (%/שנה)"].round(1)
        show["מגמה (%/שנה)"]         = show["מגמה (%/שנה)"].round(1)
        show["מדד סוציו"]             = show["מדד סוציו"].round(2)

        st.dataframe(
            show[["יישוב", "ציון כדאיות", "מחיר ממוצע (₪)", "תשואה משוערת (%/שנה)",
                  "פער ממוצע (%)", "מגמה (%/שנה)", "עסקאות", "מדד סוציו"]].head(15),
            column_config={
                "ציון כדאיות": st.column_config.ProgressColumn(
                    "ציון כדאיות", min_value=0, max_value=100, format="%.0f",
                ),
                "מחיר ממוצע (₪)": st.column_config.NumberColumn(format="₪%,d"),
                "תשואה משוערת (%/שנה)": st.column_config.NumberColumn(format="%+.1f%%"),
                "פער ממוצע (%)": st.column_config.NumberColumn(format="%+.1f%%"),
            },
            hide_index=True,
            use_container_width=True,
        )

        # ── Score legend ──────────────────────────────────────────────────────
        st.info(
            f"**ציון כדאיות** ({investment_goal}): "
            f"פער מחיר {int(w_gap*100)}% + מגמה {int(w_trend*100)}% + נזילות {int(w_liq*100)}%  |  "
            f"**פער חיובי** = נמכרו מתחת למחיר השוק (הזדמנות)"
        )

        st.divider()

        # ── Heatmap ───────────────────────────────────────────────────────────
        st.markdown("### מפת אזורי חום — פוטנציאל השקעה")

        df_d_map = load_display_data(str(APT_DISP_PATH))
        if "N" in df_d_map.columns and "E" in df_d_map.columns:
            map_pts = (
                df_d_map[df_d_map["settlementNameHeb"].isin(filtered["settlementNameHeb"])]
                .merge(filtered[["settlementNameHeb", "viability_score"]], on="settlementNameHeb", how="left")
                .rename(columns={"N": "lat", "E": "lon"})
                .dropna(subset=["lat", "lon"])
            )

            fig_map = px.density_mapbox(
                map_pts,
                lat="lat", lon="lon",
                z="viability_score",
                radius=18,
                center={"lat": 31.8, "lon": 34.9},
                zoom=7,
                mapbox_style="open-street-map",
                color_continuous_scale="YlOrRd",
                height=550,
            )
            fig_map.update_layout(
                margin=dict(t=20, b=10, l=10, r=10),
                coloraxis_colorbar=dict(title="ציון"),
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("עמודות קואורדינטות (N/E) לא נמצאו בנתונים — מפת החום אינה זמינה.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MODE B: PROPERTY RANKING IN SETTLEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_b_settle:
    st.markdown("## 🏘️ מצב ב׳ — נכסים ביישוב")

    df_all = compute_all_predictions(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # ── Settlement selector ───────────────────────────────────────────────────
    settlements_list = sorted(df_all["settlementNameHeb"].dropna().unique().tolist())
    default_idx_b = settlements_list.index("בת ים") if "בת ים" in settlements_list else 0
    selected_settlement = st.selectbox("בחר יישוב", settlements_list, index=default_idx_b, key="settle_b_sel")

    df_settle = df_all[df_all["settlementNameHeb"] == selected_settlement].copy()

    # ── Settlement summary ────────────────────────────────────────────────────
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("עסקאות ביישוב",     len(df_settle))
    sm2.metric("מחיר ממוצע",        f"{df_settle['dealAmount'].mean():,.0f} ILS")
    sm3.metric("שטח ממוצע",         f"{df_settle['assetArea'].mean():.0f} מ\"ר")
    sm4.metric("ציון כדאיות ממוצע", f"{df_settle['viability_score'].mean():.1f} / 100")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("### פילטרים")
    fb1, fb2, fb3 = st.columns(3)

    area_vals_b  = df_settle["assetArea"].dropna()
    rooms_vals_b = df_settle["assetRoomNum"].dropna()
    year_vals_b  = df_settle["deal_year"].dropna()

    with fb1:
        area_range_b = st.slider(
            'שטח (מ"ר)', float(area_vals_b.min()), float(area_vals_b.max()),
            (float(area_vals_b.min()), float(area_vals_b.max())), key="b_area_range",
        )
    with fb2:
        rooms_range_b = st.slider(
            "חדרים", float(rooms_vals_b.min()), float(rooms_vals_b.max()),
            (float(rooms_vals_b.min()), float(rooms_vals_b.max())), step=0.5, key="b_rooms_range",
        )
    with fb3:
        year_range_b = st.slider(
            "שנת עסקה", int(year_vals_b.min()), int(year_vals_b.max()),
            (int(year_vals_b.min()), int(year_vals_b.max())), key="b_year_range",
        )

    # ── Apply filters & rank ──────────────────────────────────────────────────
    mask_b = (
        df_settle["assetArea"].between(area_range_b[0], area_range_b[1]) &
        df_settle["assetRoomNum"].between(rooms_range_b[0], rooms_range_b[1]) &
        df_settle["deal_year"].between(year_range_b[0], year_range_b[1])
    )
    df_ranked = df_settle[mask_b].sort_values("viability_score", ascending=False).copy()

    st.markdown(f"**{len(df_ranked)} נכסים** אחרי פילטור — מדורגים לפי ציון כדאיות (מהגבוה לנמוך):")

    show_b = df_ranked.rename(columns={
        "neighborhood":    "שכונה",
        "streetNameHeb":   "רחוב",
        "houseNum":        "מס' בית",
        "assetArea":       'שטח (מ"ר)',
        "assetRoomNum":    "חדרים",
        "floor_num":       "קומה",
        "dealAmount":      "מחיר בפועל (₪)",
        "predicted":       "מחיר חזוי (₪)",
        "viability_score": "ציון כדאיות",
        "deal_year":       "שנה",
    }).copy()

    show_b["מחיר בפועל (₪)"] = show_b["מחיר בפועל (₪)"].round(0).astype(int)
    show_b["מחיר חזוי (₪)"]  = show_b["מחיר חזוי (₪)"].round(0).astype(int)
    show_b["ציון כדאיות"]     = show_b["ציון כדאיות"].round(1)
    show_b['שטח (מ"ר)']       = show_b['שטח (מ"ר)'].round(1)
    if "קומה" in show_b.columns:
        show_b["קומה"] = show_b["קומה"].round(0).astype(int)

    disp_cols_b = [c for c in
        ["שכונה", "רחוב", "מס' בית", 'שטח (מ"ר)', "חדרים", "קומה",
         "מחיר בפועל (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "שנה"]
        if c in show_b.columns]

    st.dataframe(
        show_b[disp_cols_b],
        column_config={
            "ציון כדאיות": st.column_config.ProgressColumn(
                "ציון כדאיות", min_value=0, max_value=100, format="%.0f",
            ),
            "מחיר בפועל (₪)": st.column_config.NumberColumn(format="₪%,d"),
            "מחיר חזוי (₪)":  st.column_config.NumberColumn(format="₪%,d"),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.info("**ציון כדאיות חיובי** = נמכר מתחת למחיר השוק — ככל שהציון גבוה יותר, כך העסקה טובה יותר.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MODE C (prev B): YAD2 PROPERTY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
for _k, _v in [
    ("b_url", ""), ("b_autofill", None), ("b_autofill_msg", ""),
    ("b_result", None),
    ("b_f_city_idx", 0), ("b_f_price", 1_500_000),
    ("b_f_area", 70), ("b_f_rooms", 3.0), ("b_f_floor", 2),
    ("b_fb_paste_text", ""), ("b_fb_show_paste", False),
    ("b_yad2_show_paste", False), ("b_yad2_paste_text", ""),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

with tab_mode_b:
    st.markdown("## 💡 מצב ג׳ — הערכת נכס ספציפי")

    mdl_b           = load_model_cached(str(MODEL_PATH))
    df_ml_b, df_d_b = load_dataframes(str(APT_ML_PATH), str(APT_DISP_PATH))
    feat_cols       = [c for c in df_ml_b.columns if c != "dealAmount"]
    settlements_b   = sorted(df_d_b["settlementNameHeb"].dropna().unique().tolist())

    # ── Step 1: optional YAD2 URL for auto-fill ───────────────────────────────
    st.markdown("#### שלב 1 — מלא מהמודעה אוטומטית — YAD2 או Facebook Marketplace (אופציונלי)")
    uc, bc = st.columns([6, 1])
    with uc:
        yad2_input = st.text_input(
            "קישור למודעה",
            placeholder="https://www.yad2.co.il/realestate/item/...  או  https://www.facebook.com/marketplace/item/...",
            label_visibility="collapsed", key="yad2_main_url",
        )
    with bc:
        fetch_btn = st.button("⬇️ חלץ", key="fetch_yad2")

    if fetch_btn and yad2_input:
        _inp = yad2_input.strip()
        # ── Detect HTML pasted directly into the URL field ─────────────────────
        _looks_like_html = _inp.startswith("<!") or _inp.lower().startswith("<html")
        if _looks_like_html:
            af = _parse_yad2_html(_inp)
            _og = re.search(r'property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']', _inp) \
               or re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']', _inp)
            st.session_state.b_url = _og.group(1) if _og else ""

            # Apply whatever fields were found (price may be missing)
            _found_h, _missing_h = [], []
            if af.get("price"):
                _p = max(100_000, min(20_000_000, int(af["price"])))
                st.session_state.b_f_price = _p; st.session_state["f_price"] = _p
                _found_h.append(f"מחיר {_p:,} ₪")
            else:
                _missing_h.append("מחיר")
            if af.get("area"):
                st.session_state.b_f_area  = int(af["area"]); st.session_state["f_area"]  = int(af["area"])
                _found_h.append(f"שטח {int(af['area'])} מ\"ר")
            if af.get("rooms"):
                st.session_state.b_f_rooms = float(af["rooms"]); st.session_state["f_rooms"] = float(af["rooms"])
                _found_h.append(f"{af['rooms']:.1f} חדרים")
            if af.get("floor") is not None:
                st.session_state.b_f_floor = int(af["floor"]); st.session_state["f_floor"] = int(af["floor"])
                _found_h.append(f"קומה {int(af['floor'])}")
            _cm = _match_settlement(af.get("city"), settlements_b)
            if _cm:
                st.session_state.b_f_city_idx = settlements_b.index(_cm)
                st.session_state["f_city"] = _cm
                _found_h.append(_cm)
            elif af.get("city"):
                st.session_state["b_city_debug"] = af.get("city")

            if _found_h:
                st.session_state.b_autofill = af
                _msg_h = "✅ חולץ מ-HTML: " + " · ".join(_found_h)
                if _missing_h:
                    _msg_h += f"  \n⚠️ חסר: {', '.join(_missing_h)} — השלם ידנית בטופס."
                st.session_state.b_autofill_msg = _msg_h
            else:
                st.session_state.b_autofill_msg = (
                    "⚠️ לא נמצאו פרטים ב-HTML שהודבק.  \n"
                    "ודא שהדבקת את קוד המקור **המלא** (Ctrl+U → Ctrl+A → Ctrl+C)."
                )
            st.rerun()
        else:
            st.session_state.b_url = yad2_input
            is_fb = bool(re.search(r"facebook\.com/marketplace|fb\.com/marketplace", yad2_input))
            spinner_msg = "מנסה לחלץ פרטים מ-Facebook Marketplace..." if is_fb else "מנסה לחלץ פרטים מ-YAD2..."
            with st.spinner(spinner_msg):
                af = scrape_listing(yad2_input)
        if not af.get("error") and af.get("price"):
            # Auto-fill session state with scraped values
            st.session_state.b_autofill = af
            _p = max(100_000, min(20_000_000, int(af["price"])))
            st.session_state.b_f_price = _p
            st.session_state["f_price"] = _p
            if af.get("area"):
                st.session_state.b_f_area   = int(af["area"])
                st.session_state["f_area"]  = int(af["area"])
            if af.get("rooms"):
                st.session_state.b_f_rooms  = float(af["rooms"])
                st.session_state["f_rooms"] = float(af["rooms"])
            if af.get("floor") is not None:
                st.session_state.b_f_floor  = int(af["floor"])
                st.session_state["f_floor"] = int(af["floor"])
            city_match = _match_settlement(af.get("city"), settlements_b)
            if city_match and city_match in settlements_b:
                st.session_state.b_f_city_idx = settlements_b.index(city_match)
                st.session_state["f_city"]    = city_match
            else:
                st.session_state["b_city_debug"] = af.get("city")

            # For Facebook: if key fields are missing → open paste box automatically
            _fb_url = bool(re.search(r"facebook\.com/marketplace|fb\.com/marketplace",
                                     st.session_state.b_url))
            _missing = [f for f, v in [("חדרים", af.get("rooms")),
                                        ("שטח", af.get("area"))] if not v]
            if _fb_url and _missing:
                st.session_state.b_fb_show_paste = True
                st.session_state.b_autofill_msg  = (
                    f"⚠️ נמצא מחיר ({_p:,} ₪), אך **{', '.join(_missing)}** לא חולצו אוטומטית.  \n"
                    "הדבק את כותרת ותיאור המודעה למטה — הפרטים החסרים יתמלאו."
                )
            else:
                st.session_state.b_autofill_msg = "✅ פרטים חולצו בהצלחה מהמודעה — ערכי הטופס עודכנו."
            st.rerun()
        else:
            is_yad2_url = bool(re.search(r"yad2\.co\.il/.*item/", yad2_input))
            if af.get("needs_paste"):
                st.session_state.b_fb_show_paste = True
                st.session_state.b_autofill_msg  = f"⚠️ {af.get('error','לא ניתן לחלץ')}"
            elif is_yad2_url and af.get("needs_manual"):
                st.session_state.b_yad2_show_paste = True
                st.session_state.b_autofill_msg = (
                    "⚠️ YAD2 חוסמת גישה אוטומטית.  \n"
                    "**פתרון:** פתח את המודעה בדפדפן → לחץ **Ctrl+U** → **Ctrl+A** → **Ctrl+C**  \n"
                    "ואז **הדבק את קוד המקור בשדה הקישור למעלה** ולחץ שוב על חלץ."
                )
            else:
                st.session_state.b_autofill_msg = (
                    f"⚠️ {af.get('error','לא ניתן לחלץ')} — "
                    "מלא את הפרטים ידנית מהמודעה הפתוחה."
                )
            st.rerun()

    if st.session_state.b_autofill_msg:
        _msg = st.session_state.b_autofill_msg
        if "⚠️" in _msg:
            st.warning(_msg)          # partial or blocked
        elif _msg.startswith("✅"):
            st.success(_msg)          # fully successful
        else:
            st.warning(_msg)

    if st.session_state.get("b_city_debug") is not None:
        st.info(f"🔍 עיר שחולצה מ-YAD2: `{st.session_state['b_city_debug']}` — לא נמצאה התאמה ברשימה. בחר ידנית.")

    # ── Facebook paste-description fallback ───────────────────────────────────
    if st.session_state.b_fb_show_paste:
        st.info(
            "**📋 הדבק את כותרת ותיאור המודעה מ-Facebook לחילוץ אוטומטי**  \n"
            "פתח את המודעה בדפדפן (עם חשבון מחובר), העתק את **הכותרת + התיאור המלא** ולחץ **חלץ מתיאור**.  \n"
            "💡 המחיר יכול להופיע בכותרת או בתיאור — הדבק את שניהם יחד."
        )
        fb_paste_input = st.text_area(
            "כותרת + תיאור המודעה מ-Facebook",
            value=st.session_state.b_fb_paste_text,
            placeholder="הדבק כאן את כותרת המודעה ואת התיאור המלא, לדוגמה:\n3 חדרים ברמת גן — 1,800,000 ₪\nדירת 3 חדרים, קומה 2, 75 מ\"ר\nרחוב הרצל 12, שכונת...",
            height=180,
            key="fb_paste_area",
        )
        parse_col, clear_col = st.columns([2, 1])
        parse_fb_btn = parse_col.button("🔍 חלץ מתיאור", type="primary", key="parse_fb_desc")
        clear_fb_btn = clear_col.button("✖ סגור", key="close_fb_paste")

        if clear_fb_btn:
            st.session_state.b_fb_show_paste = False
            st.session_state.b_fb_paste_text = ""
            st.rerun()

        if parse_fb_btn and fb_paste_input.strip():
            st.session_state.b_fb_paste_text = fb_paste_input
            parsed = _parse_realestate_text(fb_paste_input)

            # Always update fields that were found, regardless of whether price exists
            _found, _missing = [], []
            if parsed.get("price"):
                _p = max(100_000, min(20_000_000, int(parsed["price"])))
                st.session_state.b_f_price = _p
                st.session_state["f_price"] = _p
                _found.append(f"מחיר {_p:,} ₪")
            if parsed.get("area"):
                st.session_state.b_f_area   = int(parsed["area"])
                st.session_state["f_area"]  = int(parsed["area"])
                _found.append(f"שטח {int(parsed['area'])} מ\"ר")
            else:
                _missing.append("שטח")
            if parsed.get("rooms"):
                st.session_state.b_f_rooms  = float(parsed["rooms"])
                st.session_state["f_rooms"] = float(parsed["rooms"])
                _found.append(f"{parsed['rooms']:.1f} חדרים")
            else:
                _missing.append("חדרים")
            if parsed.get("floor") is not None:
                st.session_state.b_f_floor  = int(parsed["floor"])
                st.session_state["f_floor"] = int(parsed["floor"])
                _found.append(f"קומה {int(parsed['floor'])}")

            # City matching
            city_matched = False
            if parsed.get("city"):
                city_match = _match_settlement(parsed["city"], settlements_b)
                if city_match and city_match in settlements_b:
                    st.session_state.b_f_city_idx = settlements_b.index(city_match)
                    st.session_state["f_city"]    = city_match
                    _found.append(city_match)
                    city_matched = True
                else:
                    st.session_state["b_city_debug"] = parsed["city"]

            if _found:
                still_open = _missing and not parsed.get("price")
                st.session_state.b_autofill = parsed
                st.session_state.b_fb_show_paste = bool(_missing)
                msg_parts = ["✅ חולץ: " + " · ".join(_found)]
                if _missing:
                    msg_parts.append(f"⚠️ לא נמצא: {', '.join(_missing)} — השלם ידנית.")
                if not city_matched and parsed.get("city"):
                    msg_parts.append(f"🔍 עיר '{parsed['city']}' לא נמצאה ברשימה — בחר ידנית.")
                st.session_state.b_autofill_msg = "  \n".join(msg_parts)
                st.rerun()
            else:
                st.warning(
                    "לא נמצאו פרטים בטקסט. "
                    "ודא שהדבקת את כותרת וגם את תיאור המודעה המלא."
                )

    # ── YAD2 HTML paste fallback ──────────────────────────────────────────────
    if st.session_state.b_yad2_show_paste:
        st.info(
            "**📋 הדבק את קוד המקור של דף YAD2 לחילוץ אוטומטי**  \n"
            "1. פתח את המודעה ב-YAD2 בדפדפן  \n"
            "2. לחץ **Ctrl+U** (או לחצן-ימני → \"הצג מקור דף\")  \n"
            "3. לחץ **Ctrl+A** ואז **Ctrl+C** להעתקת כל הקוד  \n"
            "4. הדבק כאן ולחץ **חלץ מ-HTML**"
        )
        yad2_html_input = st.text_area(
            "קוד מקור של דף YAD2",
            value=st.session_state.b_yad2_paste_text,
            placeholder="הדבק כאן את קוד המקור של הדף (Ctrl+U → Ctrl+A → Ctrl+C)...",
            height=130,
            key="yad2_html_area",
        )
        _pc, _cc = st.columns([2, 1])
        parse_yad2_html_btn = _pc.button("🔍 חלץ מ-HTML", type="primary", key="parse_yad2_html")
        close_yad2_btn      = _cc.button("✖ סגור", key="close_yad2_paste")

        if close_yad2_btn:
            st.session_state.b_yad2_show_paste = False
            st.session_state.b_yad2_paste_text = ""
            st.rerun()

        if parse_yad2_html_btn and yad2_html_input.strip():
            st.session_state.b_yad2_paste_text = yad2_html_input
            af = _parse_yad2_html(yad2_html_input)
            # Apply whatever fields were found (price optional for partial meta extraction)
            _found, _missing = [], []
            if af.get("price"):
                _p = max(100_000, min(20_000_000, int(af["price"])))
                st.session_state.b_f_price = _p; st.session_state["f_price"] = _p
                _found.append(f"מחיר {_p:,} ₪")
            else:
                _missing.append("מחיר")
            if af.get("area"):
                st.session_state.b_f_area  = int(af["area"]); st.session_state["f_area"]  = int(af["area"])
                _found.append(f"שטח {int(af['area'])} מ\"ר")
            if af.get("rooms"):
                st.session_state.b_f_rooms = float(af["rooms"]); st.session_state["f_rooms"] = float(af["rooms"])
                _found.append(f"{af['rooms']:.1f} חדרים")
            if af.get("floor") is not None:
                st.session_state.b_f_floor = int(af["floor"]); st.session_state["f_floor"] = int(af["floor"])
                _found.append(f"קומה {int(af['floor'])}")
            city_match = _match_settlement(af.get("city"), settlements_b)
            if city_match:
                st.session_state.b_f_city_idx = settlements_b.index(city_match)
                st.session_state["f_city"]    = city_match
                _found.append(city_match)
            elif af.get("city"):
                st.session_state["b_city_debug"] = af.get("city")

            if _found:
                st.session_state.b_autofill = af
                msg = "✅ חולץ: " + " · ".join(_found)
                if _missing:
                    msg += f"  \n⚠️ חסר: {', '.join(_missing)} — השלם ידנית."
                    # keep paste open if price is still missing
                    st.session_state.b_yad2_show_paste = "מחיר" in _missing
                else:
                    st.session_state.b_yad2_show_paste = False
                    st.session_state.b_yad2_paste_text = ""
                st.session_state.b_autofill_msg = msg
                st.rerun()
            else:
                st.warning(f"⚠️ {af.get('error','לא ניתן לחלץ מה-HTML שהודבק.')}")

    # ── Step 2: property details form (always visible) ────────────────────────
    st.markdown("#### שלב 2 — פרטי הנכס")
    f1, f2, f3 = st.columns(3)
    with f1:
        if "f_city" not in st.session_state:
            st.session_state["f_city"] = settlements_b[st.session_state.b_f_city_idx]
        f_city = st.selectbox(
            "עיר / יישוב", options=settlements_b,
            key="f_city",
        )
    with f2:
        f_price = st.number_input(
            "מחיר מבוקש (₪)", min_value=100_000, max_value=20_000_000,
            value=st.session_state.b_f_price, step=10_000, format="%d", key="f_price",
        )
    with f3:
        f_area = st.number_input(
            'שטח (מ"ר)', min_value=20, max_value=500,
            value=st.session_state.b_f_area, step=5, key="f_area",
        )
    f4, f5 = st.columns(2)
    with f4:
        f_rooms = st.number_input(
            "חדרים", min_value=1.0, max_value=10.0,
            value=float(st.session_state.b_f_rooms), step=0.5, key="f_rooms",
        )
    with f5:
        f_floor = st.number_input(
            "קומה", min_value=0, max_value=50,
            value=st.session_state.b_f_floor, step=1, key="f_floor",
        )

    calc_btn = st.button("🔍 חשב ציון כדאיות", type="primary", key="calc_b")

    if calc_btn:
        af_data = st.session_state.b_autofill or {}
        st.session_state.b_result = {
            "price": float(f_price), "rooms": float(f_rooms),
            "area":  float(f_area),  "floor": float(f_floor),
            "city":  f_city,
            "lat":   af_data.get("lat"), "lon": af_data.get("lon"),
            "street": af_data.get("street"), "neighborhood": af_data.get("neighborhood"),
            "yad2_url": st.session_state.b_url or "",
        }

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.b_result:
        res = st.session_state.b_result

        matched_city = _match_settlement(res["city"], settlements_b)
        mask   = (df_d_b["settlementNameHeb"] == matched_city
                  if matched_city else pd.Series(True, index=df_d_b.index))
        sub_ml = df_ml_b[mask]
        sub_d  = df_d_b[mask]

        fvec = sub_ml[feat_cols].median().copy()
        fvec["assetArea"]    = res["area"]
        fvec["assetRoomNum"] = res["rooms"]
        fvec["floor_num"]    = res["floor"]
        today = datetime.date.today()
        fvec["deal_year"]  = float(today.year)
        fvec["deal_month"] = float(today.month)

        predicted_price = float(mdl_b.predict(fvec[feat_cols].values.reshape(1, -1))[0])
        asking_price    = res["price"]
        avg_area_price  = float(sub_d["dealAmount"].mean())
        gap_pct         = (predicted_price - asking_price) / asking_price * 100

        price_score = min(100.0, max(0.0, 50.0 + gap_pct * 2.5))
        s_min = float(df_d_b["socio_index_avg"].min())
        s_max = float(df_d_b["socio_index_avg"].max())
        s_avg = float(sub_d["socio_index_avg"].mean())
        socio_score = (s_avg - s_min) / (s_max - s_min) * 100 if s_max > s_min else 50.0
        n_deals   = len(sub_d)
        liq_score = min(100.0, n_deals / 50.0 * 100.0)
        viability = round(0.60 * price_score + 0.25 * socio_score + 0.15 * liq_score, 1)

        st.divider()
        dc = st.columns(5)
        dc[0].metric("עיר",        res["city"])
        dc[1].metric('שטח (מ"ר)',  f"{res['area']:.0f}")
        dc[2].metric("חדרים",      f"{res['rooms']:.1f}")
        dc[3].metric("קומה",       f"{int(res['floor'])}")
        dc[4].metric("מחיר מבוקש", f"{asking_price:,.0f} ₪")

        st.markdown("### 📊 ניתוח מחיר")
        m1, m2, m3 = st.columns(3)
        m1.metric("מחיר חזוי (מודל)", f"{predicted_price:,.0f} ₪")
        m2.metric("פער מהמחיר המבוקש", f"{gap_pct:+.1f}%",
                  delta=f"{predicted_price - asking_price:+,.0f} ₪",
                  delta_color="normal" if gap_pct >= 0 else "inverse")
        m3.metric("מחיר ממוצע באזור", f"{avg_area_price:,.0f} ₪")

        if viability >= 70:
            bg, icon, txt = "#d4edda", "🟢", "כדאי להשקיע"
        elif viability >= 45:
            bg, icon, txt = "#fff3cd", "🟡", "דורש בחינה נוספת"
        else:
            bg, icon, txt = "#f8d7da", "🔴", "לא מומלץ"
        st.markdown(
            f'<div style="text-align:center;padding:24px 0;border-radius:14px;background:{bg};'
            f'direction:rtl;margin:16px 0;">'
            f'<div style="font-size:3.5rem;line-height:1;">{icon} {viability:.0f}</div>'
            f'<div style="font-size:1.4rem;font-weight:700;margin-top:6px;">ציון כדאיות — {txt}</div>'
            f'<div style="font-size:.85rem;color:#555;margin-top:4px;">'
            f'פער מחיר 60% · איכות אזור 25% · נזילות שוק 15%</div></div>',
            unsafe_allow_html=True,
        )

        with st.expander("📋 פירוט הציון", expanded=True):
            reasons = []
            if gap_pct > 15:
                reasons.append(f"✅ **הנכס זול משמעותית** — המודל מעריך שהוא שווה {gap_pct:.1f}% יותר מהמחיר המבוקש.")
            elif gap_pct > 3:
                reasons.append(f"✅ **מחיר מתחת לשוק** — הנכס מתומחר {gap_pct:.1f}% מתחת להערכת המודל.")
            elif gap_pct > -5:
                reasons.append(f"⚠️ **מחיר בשוק** — קרוב לשווי ההוגן (פער {gap_pct:+.1f}%). מרחב מיקוח מוגבל.")
            elif gap_pct > -15:
                reasons.append(f"⚠️ **מחיר מעל שוק** — גבוה ב-{abs(gap_pct):.1f}% מהמודל. נסה להתמקח.")
            else:
                reasons.append(f"❌ **מחיר גבוה מהשוק** — {abs(gap_pct):.1f}% מעל המודל. בדוק אם יש הצדקה.")
            loc = matched_city or res["city"]
            if socio_score >= 70:
                reasons.append(f"✅ **אזור איכותי** — {loc} מדורג גבוה במדד הסוציו-אקונומי.")
            elif socio_score >= 40:
                reasons.append(f"⚠️ **אזור בינוני** — {loc} במדד סוציו-אקונומי בינוני.")
            else:
                reasons.append(f"⚠️ **מדד סוציו-אקונומי נמוך** — {loc} מתחת לממוצע.")
            if n_deals >= 30:
                reasons.append(f"✅ **שוק נזיל** — {n_deals} עסקאות בבסיס הנתונים.")
            elif n_deals >= 10:
                reasons.append(f"⚠️ **נזילות בינונית** — {n_deals} עסקאות לאזור זה.")
            else:
                reasons.append(f"⚠️ **מעט נתונים** — {n_deals} עסקאות. מומלץ לקבל חוות דעת שמאי.")
            for r in reasons:
                st.markdown(f"- {r}")

        if res.get("yad2_url"):
            st.markdown(f"[🔗 חזור למודעה ב-YAD2]({res['yad2_url']})")

        st.markdown("### 🗺️ מפת קרבה — עסקאות דומות באזור")
        has_pin = bool(res.get("lat") and res.get("lon"))

        # Resolve coordinates for POI/map even when no exact address was scraped
        map_lat = float(res["lat"]) if has_pin else None
        map_lon = float(res["lon"]) if has_pin else None
        geocoded = False
        if not has_pin:
            _gc_q = ", ".join(filter(None, [res.get("street"), res.get("city")]))
            if _gc_q:
                with st.spinner("מאתר מיקום…"):
                    _gc_lat, _gc_lon = geocode_address(_gc_q)
                if _gc_lat:
                    map_lat, map_lon = _gc_lat, _gc_lon
                    geocoded = True
        has_map_center = bool(map_lat and map_lon)

        mc1, mc2, mc3, mc4 = st.columns([1.5, 1.5, 1, 1])
        show_similar = mc1.checkbox(
            f"🏠 נכסים דומים ({res['rooms']:.1f} חדרים)",
            value=True, key="map_show_similar",
        )
        show_all = mc2.checkbox(
            "🏙️ כל הנכסים שנמכרו בעיר",
            value=False, key="map_show_all",
        )
        _pois_help = ("מיקום משוער (גיאוקודינג לפי עיר)" if geocoded
                      else "" if has_pin
                      else "לא ניתן לקבוע מיקום — הזן כתובת")
        show_pois  = mc3.checkbox("נקודות עניין (OSM)", value=has_map_center, key="map_pois",
                                   disabled=not has_map_center, help=_pois_help)
        focus_prop = mc4.checkbox("התמקד בנכס", value=has_map_center, key="map_focus",
                                   disabled=not has_map_center)

        try:
            from streamlit_folium import st_folium
            import folium

            _FOLIUM_COLORS = {
                "transport": "#FF8C00", "education": "#8A2BE2",
                "health":    "#00B43C", "park":      "#228B22",
                "retail":    "#DAA520", "food":      "#DC143C",
                "service":   "#4682B4", "leisure":   "#FF69B4",
                "tourism":   "#00CED1", "community": "#FFA500",
                "nature":    "#2E6B2E", "historic":  "#8B5A2B",
                "employment":"#696969",
            }

            # ── Build similar-transactions layer ───────────────────────────────
            sim_df = pd.DataFrame(columns=["lat", "lon", "price", "rooms"])
            if show_similar:
                sim_sub = sub_d[
                    (sub_d["assetRoomNum"] >= res["rooms"] - 0.5) &
                    (sub_d["assetRoomNum"] <= res["rooms"] + 0.5)
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

            # ── Build all-transactions layer ───────────────────────────────────
            all_df = pd.DataFrame(columns=["lat", "lon", "price", "rooms"])
            if show_all:
                valid_a = sub_d.dropna(subset=["X", "Y"])
                if len(valid_a):
                    a_lats, a_lons = itm_to_wgs84(valid_a["X"], valid_a["Y"])
                    all_df = pd.DataFrame({
                        "lat": a_lats, "lon": a_lons,
                        "price": valid_a["dealAmount"].values,
                        "rooms": valid_a["assetRoomNum"].values,
                    })
                    all_df = all_df[all_df["lat"].between(29, 34) & all_df["lon"].between(34, 36)]

            # ── Centre + zoom ──────────────────────────────────────────────────
            if has_map_center and focus_prop:
                c_lat, c_lon, zoom = map_lat, map_lon, 15 if has_pin else 14
            elif len(sim_df):
                c_lat, c_lon, zoom = float(sim_df["lat"].mean()), float(sim_df["lon"].mean()), 14
            elif len(all_df):
                c_lat, c_lon, zoom = float(all_df["lat"].mean()), float(all_df["lon"].mean()), 14
            else:
                c_lat, c_lon, zoom = 32.0, 34.8, 12

            # ── Build folium map ───────────────────────────────────────────────
            fmap = folium.Map(location=[c_lat, c_lon], zoom_start=zoom,
                              tiles="OpenStreetMap")

            # All-transactions layer (rendered first so similar appears on top)
            if show_all and len(all_df):
                all_group = folium.FeatureGroup(name=f"כל הנכסים בעיר ({len(all_df)})", show=True)
                for _, row in all_df.iterrows():
                    folium.CircleMarker(
                        location=[row.lat, row.lon],
                        radius=5, color="#A0A0C0", fill=True,
                        fill_color="#A0A0C0", fill_opacity=0.45, weight=1,
                        tooltip=f"{int(row.price):,} ₪ | {row.rooms:.1f} חדרים",
                    ).add_to(all_group)
                all_group.add_to(fmap)

            # Similar-transactions layer
            if show_similar and len(sim_df):
                sim_group = folium.FeatureGroup(name=f"נכסים דומים ({len(sim_df)})", show=True)
                for _, row in sim_df.iterrows():
                    folium.CircleMarker(
                        location=[row.lat, row.lon],
                        radius=6, color="#6495ED", fill=True,
                        fill_color="#6495ED", fill_opacity=0.65, weight=1,
                        tooltip=f"{int(row.price):,} ₪ | {row.rooms:.1f} חדרים",
                    ).add_to(sim_group)
                sim_group.add_to(fmap)

            # ── POI — load, summarise, filter, render ─────────────────────────
            cache_key = None
            if show_pois and has_map_center and POI_PATH.exists():
                cache_key = f"pois_{map_lat:.4f}_{map_lon:.4f}"
                if cache_key not in st.session_state:
                    all_pois = load_poi_data(str(POI_PATH))
                    st.session_state[cache_key] = get_local_pois(
                        all_pois, map_lat, map_lon
                    )
                poi_df = st.session_state[cache_key]

                if len(poi_df):
                    # ── Summary table ──────────────────────────────────────────
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

                    # ── Category filter ────────────────────────────────────────
                    all_prefixes = summary["prefix"].tolist()
                    prefix_labels = {
                        row["prefix"]: f"{row['סמל']} {row['cat_heb']} ({row['כמות']})"
                        for _, row in summary.iterrows()
                    }
                    selected_prefixes = st.multiselect(
                        "סנן קטגוריות POI",
                        options=all_prefixes,
                        default=all_prefixes,
                        format_func=lambda p: prefix_labels.get(p, p),
                        key="poi_cat_filter",
                    )
                    poi_filtered = poi_df[poi_df["prefix"].isin(selected_prefixes)]

                    # ── Add to map ─────────────────────────────────────────────
                    for prefix in selected_prefixes:
                        grp_df = poi_filtered[poi_filtered["prefix"] == prefix]
                        clr    = _FOLIUM_COLORS.get(prefix, "#888888")
                        grp    = folium.FeatureGroup(
                            name=f"{prefix_labels[prefix]}", show=True
                        )
                        for _, row in grp_df.iterrows():
                            name_str = row["name"] if row["name"] else row["cat_heb"]
                            folium.CircleMarker(
                                location=[row.lat, row.lon],
                                radius=5, color=clr, fill=True,
                                fill_color=clr, fill_opacity=0.65, weight=1,
                                tooltip=f"{name_str} | {int(row.dist_m)} מ'",
                            ).add_to(grp)
                        grp.add_to(fmap)

            # Property pin — always shown when we have any coordinates
            if has_map_center:
                addr_parts = [p for p in [res.get("street"), res.get("city")] if p]
                addr_label = ", ".join(addr_parts) if addr_parts else res.get("city", "הנכס")
                approx_note = " (מיקום משוער)" if geocoded else ""
                popup_html = (
                    f"<div dir='rtl' style='font-family:Arial;min-width:180px'>"
                    f"<b>{addr_label}{approx_note}</b><br>"
                    f"{int(res['price']):,} ₪ | {res['rooms']:.1f} חדרים"
                    f"</div>"
                )
                folium.Marker(
                    location=[map_lat, map_lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=addr_label + approx_note,
                    icon=folium.Icon(
                        color="orange" if geocoded else "red",
                        icon="home", prefix="fa",
                    ),
                ).add_to(fmap)

            folium.LayerControl(position="topright").add_to(fmap)
            st_folium(fmap, use_container_width=True, height=420, returned_objects=[])

            legend = []
            if has_pin:
                legend.append("🔴 הנכס (מדויק)")
            elif geocoded:
                legend.append("🟠 הנכס (מיקום משוער לפי עיר)")
            if show_similar and len(sim_df):
                legend.append(f"🔵 נכסים דומים ({len(sim_df)})")
            if show_all and len(all_df):
                legend.append(f"⚫ כל הנכסים בעיר ({len(all_df)})")
            if show_pois and has_map_center and cache_key:
                _pl = st.session_state.get(cache_key, pd.DataFrame())
                legend.append(
                    f"🟠 תחבורה · 🟣 חינוך · 🟢 בריאות/פארקים · 🟡 קניות · 🔴 מזון ({len(_pl)} POI)"
                    if len(_pl) else "⚠️ לא נמצאו POI ברדיוס 1 ק\"מ"
                )
            st.caption(" · ".join(legend))

        except Exception as _map_exc:
            st.caption(f"שגיאת מפה: {_map_exc}")
            try:
                lats, lons = itm_to_wgs84(sub_d["X"].dropna(), sub_d["Y"].dropna())
                fb = pd.DataFrame({"lat": lats, "lon": lons})
                fb = fb[fb["lat"].between(29, 34) & fb["lon"].between(34, 36)]
                if has_pin:
                    fb = pd.concat([pd.DataFrame({"lat":[res["lat"]],"lon":[res["lon"]]}), fb], ignore_index=True)
                if len(fb):
                    st.map(fb, zoom=14, use_container_width=True)
            except Exception:
                pass

        st.markdown("### 🏘️ עסקאות דומות באזור")
        sim_preds = mdl_b.predict(sub_ml[feat_cols])
        sim = sub_d.copy().reset_index(drop=True)
        sim["מחיר חזוי (₪)"] = np.round(sim_preds).astype(int)
        sim["פער (%)"]        = ((sim_preds - sim["dealAmount"]) / sim["dealAmount"] * 100).round(1)
        sim = sim.rename(columns={
            "streetNameHeb": "רחוב", "houseNum": "מס׳",
            "dealAmount": "מחיר בפועל (₪)", "assetArea": 'שטח (מ"ר)',
            "assetRoomNum": "חדרים", "floor_num": "קומה", "deal_year": "שנה",
        })
        avail = [c for c in
            ["רחוב", "מס׳", "מחיר בפועל (₪)", "מחיר חזוי (₪)", "פער (%)", 'שטח (מ"ר)', "חדרים", "קומה", "שנה"]
            if c in sim.columns]
        sim["מחיר בפועל (₪)"] = sim["מחיר בפועל (₪)"].astype(int)
        st.dataframe(sim[avail].sort_values("שנה", ascending=False).head(20),
                     hide_index=True, use_container_width=True)

        if st.button("🔄 ניתוח נכס חדש", key="reset_b"):
            for k in ["b_url","b_autofill","b_autofill_msg","b_result",
                      "b_f_price","b_f_area","b_f_rooms","b_f_floor","b_f_city_idx",
                      "b_fb_paste_text","b_fb_show_paste"]:
                st.session_state.pop(k, None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MODE D: SINGLE DEAL ANALYSIS (quick manual check)
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_c:
    st.markdown("## 🔍 מצב ד׳ — בדיקת עסקה ספציפית")

    baselines_c = get_settlement_baselines(str(APT_ML_PATH), str(APT_DISP_PATH))
    df_all_c    = compute_all_predictions(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # ── Inputs ────────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### פרטי הנכס")
        ic1, ic2, ic3, ic4 = st.columns(4)

        settlements_c = sorted(baselines_c.index.tolist())
        default_c_idx = settlements_c.index("בת ים") if "בת ים" in settlements_c else 0

        with ic1:
            settlement_c = st.selectbox("יישוב", settlements_c, index=default_c_idx, key="c_settlement")
        with ic2:
            area_c  = st.number_input('שטח (מ"ר)', min_value=20, max_value=500, value=80, step=5, key="c_area")
        with ic3:
            rooms_c = st.number_input("חדרים", min_value=1.0, max_value=10.0, value=3.0, step=0.5, key="c_rooms")
        with ic4:
            floor_c = st.number_input("קומה", min_value=0, max_value=50, value=2, step=1, key="c_floor")

        pc1, _ = st.columns([1, 2])
        with pc1:
            asking_price_c = st.number_input(
                "מחיר מבוקש (₪)",
                min_value=100_000, max_value=20_000_000,
                value=1_500_000, step=50_000, format="%d", key="c_price",
            )

    st.divider()

    # ── Predict ───────────────────────────────────────────────────────────────
    mdl_c   = load_model_cached(str(MODEL_PATH))
    feat_cols_c = [c for c in baselines_c.columns if c != "dealAmount"]
    row_c   = baselines_c.loc[settlement_c].copy()
    row_c["assetArea"]    = float(area_c)
    row_c["assetRoomNum"] = float(rooms_c)
    row_c["floor_num"]    = float(floor_c)

    predicted_c  = float(mdl_c.predict(pd.DataFrame([row_c[feat_cols_c]]))[0])
    price_diff_c = predicted_c - asking_price_c
    gap_pct_c    = price_diff_c / asking_price_c * 100
    viability_c  = float(np.clip(50 + gap_pct_c * 1.5, 0, 100))

    # ── Metrics ───────────────────────────────────────────────────────────────
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric('מחיר חזוי ע"י המודל', f"{predicted_c:,.0f} ILS")
    rc2.metric("מחיר מבוקש",           f"{asking_price_c:,.0f} ILS")
    rc3.metric("הפרש",                  f"{price_diff_c:+,.0f} ILS")
    rc4.metric("ציון כדאיות",           f"{viability_c:.0f} / 100")

    # ── Verdict ───────────────────────────────────────────────────────────────
    if viability_c >= 65:
        st.success(f"עסקה טובה — המודל מעריך שהנכס שווה {price_diff_c:+,.0f} ILS יותר מהמחיר המבוקש.")
    elif viability_c >= 40:
        st.warning(f"עסקה סבירה — פער של {price_diff_c:+,.0f} ILS ביחס לשוק.")
    else:
        st.error(f"מחיר גבוה — המודל מעריך שהנכס שווה {abs(price_diff_c):,.0f} ILS פחות מהמחיר המבוקש.")

    st.divider()

    # ── Similar properties ────────────────────────────────────────────────────
    st.markdown("### השוואה לעסקאות דומות ביישוב")

    similar_c = df_all_c[
        (df_all_c["settlementNameHeb"] == settlement_c) &
        (df_all_c["assetArea"].between(area_c * 0.75, area_c * 1.25)) &
        (df_all_c["assetRoomNum"].between(rooms_c - 0.5, rooms_c + 0.5))
    ].sort_values("viability_score", ascending=False).copy()

    if similar_c.empty:
        st.info("לא נמצאו עסקאות דומות. נסה להרחיב את טווח השטח או החדרים.")
    else:
        avg_actual_c  = similar_c["dealAmount"].mean()
        diff_vs_avg_c = asking_price_c - avg_actual_c
        st.caption(f"{len(similar_c)} עסקאות דומות נמצאו · מחיר ממוצע: {avg_actual_c:,.0f} ILS")

        show_c = similar_c.rename(columns={
            "neighborhood":    "שכונה",
            "streetNameHeb":   "רחוב",
            "assetArea":       'שטח (מ"ר)',
            "assetRoomNum":    "חדרים",
            "floor_num":       "קומה",
            "dealAmount":      "מחיר בפועל (₪)",
            "predicted":       "מחיר חזוי (₪)",
            "viability_score": "ציון כדאיות",
            "deal_year":       "שנה",
        }).copy()

        show_c["מחיר בפועל (₪)"] = show_c["מחיר בפועל (₪)"].round(0).astype(int)
        show_c["מחיר חזוי (₪)"]  = show_c["מחיר חזוי (₪)"].round(0).astype(int)
        show_c['שטח (מ"ר)']       = show_c['שטח (מ"ר)'].round(1)
        if "קומה" in show_c.columns:
            show_c["קומה"] = show_c["קומה"].round(0).astype(int)

        disp_cols_c = [c for c in
            ["שכונה", "רחוב", 'שטח (מ"ר)', "חדרים", "קומה",
             "מחיר בפועל (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "שנה"]
            if c in show_c.columns]

        st.dataframe(
            show_c[disp_cols_c].head(10),
            column_config={
                "ציון כדאיות": st.column_config.ProgressColumn(
                    min_value=0, max_value=100, format="%.0f",
                ),
                "מחיר בפועל (₪)": st.column_config.NumberColumn(format="₪%,d"),
                "מחיר חזוי (₪)":  st.column_config.NumberColumn(format="₪%,d"),
            },
            hide_index=True,
            use_container_width=True,
        )

        direction_c = "גבוה" if diff_vs_avg_c > 0 else "נמוך"
        st.info(
            f"המחיר המבוקש **{direction_c}** ב-{abs(diff_vs_avg_c):,.0f} ILS "
            f"ביחס לממוצע עסקאות דומות ({avg_actual_c:,.0f} ILS)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — EXPLANATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_explain:
    st.markdown("## 📖 הסברים")

    with st.expander("🗺️ מצב א׳ — איך עובד ציון הכדאיות?", expanded=True):
        st.markdown("""
### ציון כדאיות — מה זה?

המודל אומן על 6,609 עסקאות דירות ולמד לחזות מחיר "הוגן" לכל דירה.

**פער** = מחיר חזוי − מחיר ששולם בפועל

| פער | משמעות |
|-----|--------|
| **חיובי** | נמכר מתחת למחיר השוק — הזדמנות |
| **שלילי** | נמכר מעל מחיר השוק — יקר |

### ציון כדאיות per יישוב

| מרכיב | תשואה שוטפת | עליית ערך |
|--------|-------------|-----------|
| פער מחיר ממוצע | 60% | 30% |
| מגמת מחיר (%/שנה) | 20% | 50% |
| נזילות (כמות עסקאות) | 20% | 20% |

### פרמטרי הפרופיל

- **תקציב מקסימום** — מסנן יישובים שמחירם הממוצע מעל התקציב
- **שוק מבוסס** — מדד סוציו-אקונומי מעל החציון (סיכון נמוך יותר)
- **שוק מתפתח** — מדד סוציו-אקונומי מתחת לחציון (פוטנציאל גבוה, סיכון גבוה)
- **מינ' עסקאות** — נזילות שוק — פחות עסקאות = קשה יותר להיכנס ולצאת
        """)

    with st.expander("🤖 על המודל", expanded=False):
        st.markdown("""
### XGBoost — מודל חיזוי מחירים

**מקור נתונים:** רשות המיסים — 6,609 עסקאות דירות

**Features עיקריות:** שטח, חדרים, קומה, יישוב, שכונה, רחוב, מדד סוציו, קרבה ל-POI

**ביצועים:**
- R² = 0.741 — המודל מסביר 74.1% מהשונות במחיר
- RMSE = 607,000 ILS (35% מהמחיר הממוצע)
        """)