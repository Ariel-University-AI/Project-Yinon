"""
יועץ נדל"ן חכם — FastAPI backend
Run locally:  uvicorn main:app --reload --port 8000
"""
import re
import json
import pathlib
import datetime
import difflib
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

BASE       = pathlib.Path(__file__).parent
MODEL_PATH = BASE.parent / "model.pkl"
ML_PATH    = BASE.parent / "DATA_FILES" / "apartments_ml_ready.csv"
DISP_PATH  = BASE.parent / "DATA_FILES" / "apartments_display.csv"
POI_PATH   = BASE.parent / "DATA_FILES" / "ISRAEL_POINTS_FILTERED_GEO.csv"

_DAILY_REFRESH_SECRET = "nadlanist_daily_2024"
_DAILY_CACHE_PATH     = pathlib.Path("/tmp/yad2_daily_cache.json")

app = FastAPI()

# ── Load model + data once at startup ────────────────────────────────────────
model  = joblib.load(MODEL_PATH)
df_ml  = pd.read_csv(ML_PATH,   encoding="utf-8-sig")
df_d   = pd.read_csv(DISP_PATH, encoding="utf-8-sig")

feat_cols   = [c for c in df_ml.columns if c != "dealAmount"]
settlements = sorted(df_d["settlementNameHeb"].dropna().unique().tolist())

_s_min = float(df_d["socio_index_avg"].min())
_s_max = float(df_d["socio_index_avg"].max())

# Load POI once (large file — load lazily on first use)
_poi_df:  Optional[pd.DataFrame] = None
_df_pred: Optional[pd.DataFrame] = None

# ── Load daily Yad2 cache from file if exists and from today ─────────────────
def _load_daily_cache():
    global _yad2_area_cache, _yad2_area_ts
    try:
        import datetime as _dt
        if _DAILY_CACHE_PATH.exists():
            data = json.loads(_DAILY_CACHE_PATH.read_text(encoding="utf-8"))
            if data.get("date") == _dt.date.today().isoformat():
                _yad2_area_cache = data.get("prices", {})
                _yad2_area_ts    = time.time()
                print(f"[daily_cache] loaded {len(_yad2_area_cache)} cities from file", flush=True)
    except Exception as e:
        print(f"[daily_cache] load failed: {e}", flush=True)

threading.Thread(target=_load_daily_cache, daemon=True).start()

# Yad2 live price cache for areas page
_yad2_area_cache: dict  = {}   # city_name -> avg_asking_price
_yad2_area_ts:    float = 0.0
_yad2_area_busy:  bool  = False

# Yad2 live rent cache for areas page
_yad2_rent_cache: dict  = {}   # city_name -> median monthly rent
_yad2_rent_ts:    float = 0.0
_yad2_rent_busy:  bool  = False
_yad2_rent_lock         = threading.Lock()


def _get_predictions() -> pd.DataFrame:
    global _df_pred
    if _df_pred is None:
        preds = model.predict(df_ml[feat_cols].values)
        df = df_d.copy()
        df["predicted"]       = preds.astype(float)
        safe_denom            = df["dealAmount"].replace(0, np.nan)
        df["gap_pct"]         = (df["predicted"] - df["dealAmount"]) / safe_denom * 100
        df["viability_score"] = (50 + df["gap_pct"].fillna(0) * 1.5).clip(0, 100).round(1)
        _df_pred = df
    return _df_pred


def _get_poi_df() -> pd.DataFrame:
    global _poi_df
    if _poi_df is None and POI_PATH.exists():
        _poi_df = pd.read_csv(POI_PATH, encoding="utf-8-sig", low_memory=False,
                              usecols=["lat", "lon", "name", "category"])
        _poi_df = _poi_df.dropna(subset=["lat", "lon", "category"]).reset_index(drop=True)
    return _poi_df if _poi_df is not None else pd.DataFrame()


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.get("/")
def landing():
    return FileResponse(BASE / "landing.html")

@app.get("/check")
def check():
    return FileResponse(BASE / "check.html")

@app.get("/areas")
def areas():
    return FileResponse(BASE / "areas.html")

@app.get("/browse")
def browse():
    return FileResponse(BASE / "browse.html")

@app.get("/profile")
def profile():
    return FileResponse(BASE / "profile.html")


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/cities")
def get_cities():
    return JSONResponse(settlements)


@app.get("/api/yad2-cities")
def get_yad2_cities():
    return JSONResponse(sorted([c for c in settlements if c in _YAD2_CITY_IDS]))


@app.get("/api/areas")
def get_areas(min_deals: int = 5):
    df = _get_predictions()

    def _trend(g):
        years = g["deal_year"].dropna()
        if years.nunique() < 2:
            return 0.0
        prices = g.loc[years.index, "dealAmount"].values
        slope  = np.polyfit(years.values.astype(float), prices, 1)[0]
        mean_p = float(g["dealAmount"].mean())
        return float(round(slope / mean_p * 100, 2)) if mean_p else 0.0

    try:
        trend_s = df.groupby("settlementNameHeb").apply(_trend, include_groups=False)
    except TypeError:
        trend_s = df.groupby("settlementNameHeb").apply(_trend)
    trend_s.name = "trend_pct_yr"

    # Use all data for viability/trend, but recent data (2022+) for avg_price
    df_recent = df[df["deal_year"] >= 2022] if "deal_year" in df.columns else df

    agg: dict = {
        "avg_gap":       ("gap_pct",         "mean"),
        "deal_count":    ("dealAmount",      "count"),
        "avg_viability": ("viability_score", "mean"),
    }
    if "socio_index_avg" in df.columns:
        agg["avg_socio"] = ("socio_index_avg", "mean")

    stats = df.groupby("settlementNameHeb").agg(**agg).join(trend_s).reset_index()

    # Recent price: prefer 2022+ avg; fall back to all-time if fewer than 3 recent deals
    recent_price = (df_recent.groupby("settlementNameHeb")["dealAmount"]
                    .agg(recent_mean="mean", recent_count="count").reset_index())
    alltime_price = df.groupby("settlementNameHeb")["dealAmount"].mean().reset_index(name="alltime_mean")
    price_df = recent_price.merge(alltime_price, on="settlementNameHeb", how="right")
    price_df["avg_price"] = price_df.apply(
        lambda r: r["recent_mean"] if r["recent_count"] >= 3 else r["alltime_mean"], axis=1
    )
    stats = stats.merge(price_df[["settlementNameHeb", "avg_price"]], on="settlementNameHeb", how="left")

    stats = stats[stats["deal_count"] >= min_deals].copy()
    stats["district"]     = stats["settlementNameHeb"].map(lambda c: _CITY_TO_DISTRICT.get(c, "אחר"))
    stats["avg_viability"] = stats["avg_viability"].round(1)
    stats["avg_price"]    = stats["avg_price"].round(0)
    stats["avg_gap"]      = stats["avg_gap"].round(1)
    stats["trend_pct_yr"] = stats["trend_pct_yr"].fillna(0).round(2)
    if "avg_socio" not in stats.columns:
        stats["avg_socio"] = None
    else:
        stats["avg_socio"] = stats["avg_socio"].round(1)

    def _est_yield(p):
        # Gross rental yield benchmarks (Israeli market 2024)
        if p is None or p <= 0: return 3.0
        if p >= 5_000_000: return 1.9   # Tel Aviv center
        if p >= 4_000_000: return 2.0
        if p >= 3_000_000: return 2.2   # Jerusalem, Herzliya
        if p >= 2_000_000: return 2.4   # Netanya, Ra'anana
        if p >= 1_500_000: return 2.7   # Beer Sheva, Ashdod
        if p >= 1_000_000: return 2.6   # Kiryat Gat, Kiryat Malachi
        return 3.5                       # Deep periphery (Ofakim etc.)

    stats["avg_rent_est"] = stats["avg_price"].apply(
        lambda p: round(p * _est_yield(p) / 100 / 12) if pd.notna(p) and p > 0 else None
    )
    stats = stats.sort_values("avg_viability", ascending=False)

    records = stats.rename(columns={"settlementNameHeb": "city"}).to_dict("records")
    for r in records:
        for k, v in list(r.items()):
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                r[k] = None
        city = r.get("city", "")
        yad2_rent = _yad2_rent_cache.get(city)
        r["avg_rent_yad2"] = int(yad2_rent) if yad2_rent else None
    return JSONResponse(records)


class PredictRequest(BaseModel):
    city: str
    rooms: float
    size_sqm: float
    floor: int
    asking_price: int

@app.post("/api/predict")
def predict(req: PredictRequest):
    city  = req.city
    price = float(req.asking_price)
    area  = float(req.size_sqm)
    rooms = float(req.rooms)
    floor = float(req.floor)

    mask   = df_d["settlementNameHeb"] == city
    sub_d  = df_d[mask]
    sub_ml = df_ml[mask]

    if sub_ml.empty:
        return JSONResponse({"error": f"לא נמצאו נתונים עבור '{city}'."}, status_code=422)

    today = datetime.date.today()
    fvec = sub_ml[feat_cols].median().copy()
    fvec["assetArea"]    = area
    fvec["assetRoomNum"] = rooms
    fvec["floor_num"]    = floor
    fvec["deal_year"]    = float(today.year)
    fvec["deal_month"]   = float(today.month)

    predicted  = float(model.predict(fvec[feat_cols].values.reshape(1, -1))[0])
    gap_pct    = (predicted - price) / price * 100
    gap_amount = predicted - price
    n_deals    = len(sub_d)

    s_avg        = float(sub_d["socio_index_avg"].mean()) if not sub_d.empty else (_s_min + _s_max) / 2
    socio_score  = (s_avg - _s_min) / (_s_max - _s_min) * 100 if _s_max > _s_min else 50.0
    price_score  = min(100.0, max(0.0, 50.0 + gap_pct * 2.5))
    liq_score    = min(100.0, n_deals / 50.0 * 100.0)
    viability    = round(0.60 * price_score + 0.25 * socio_score + 0.15 * liq_score, 1)

    return {
        "viability_score": viability,
        "predicted_price": round(predicted),
        "asking_price":    round(price),
        "gap_pct":         round(gap_pct, 1),
        "gap_amount":      round(gap_amount),
        "price_score":     round(price_score, 1),
        "socio_score":     round(socio_score, 1),
        "liq_score":       round(liq_score, 1),
        "deal_count":      n_deals,
        "city":            city,
    }


class ScrapeRequest(BaseModel):
    url: str

@app.post("/api/scrape")
def scrape(req: ScrapeRequest):
    url = req.url.strip()
    result = _scrape_listing(url)
    if result.get("city"):
        matched = _match_settlement(result["city"], settlements)
        result["city"] = matched or result["city"]
    return JSONResponse(result)


class ParseSourceRequest(BaseModel):
    html: str

@app.post("/api/parse-source")
def parse_source(req: ParseSourceRequest):
    result = _parse_yad2_html(req.html.strip())
    if result.get("city"):
        matched = _match_settlement(result["city"], settlements)
        result["city"] = matched or result["city"]
    return JSONResponse(result)


class AreasRequest(BaseModel):
    budget: int
    goal: str   # "rent" | "appreciation"

@app.post("/api/areas")
def rank_areas(req: AreasRequest):
    # TODO: port investment area ranking from app_simple.py
    pass


@app.get("/api/properties")
def get_properties(
    city:      str   = "",
    district:  str   = "",
    min_price: float = 0,
    max_price: float = 1e12,
    min_rooms: float = 0,
    max_rooms: float = 20,
    min_area:  float = 0,
    max_area:  float = 9999,
    min_year:  int   = 1900,
    max_year:  int   = 2100,
    limit:     int   = 50,
):
    df = _get_predictions()
    if district:
        cities = _DISTRICT_MAP.get(district, [])
        sub = df[df["settlementNameHeb"].isin(cities)].copy()
    else:
        sub = df[df["settlementNameHeb"] == city].copy()
    if sub.empty:
        return JSONResponse({"records": [], "total": 0})

    price_mask = sub["dealAmount"].between(min_price, max_price)
    rooms_mask = sub["assetRoomNum"].isna() | sub["assetRoomNum"].between(min_rooms, max_rooms)
    area_mask  = sub["assetArea"].isna()    | sub["assetArea"].between(min_area, max_area)
    year_mask  = sub["deal_year"].isna()    | sub["deal_year"].between(float(min_year), float(max_year))
    sub = sub[price_mask & rooms_mask & area_mask & year_mask]

    if district:
        sub = (sub.sort_values("viability_score", ascending=False)
                  .groupby("settlementNameHeb", group_keys=False)
                  .head(5))
        sub = sub.sort_values("viability_score", ascending=False)
    else:
        sub = sub.sort_values("viability_score", ascending=False).head(limit)

    def _ss(v):
        return str(v) if pd.notna(v) else ""
    def _si(v):
        try:    return int(float(v)) if pd.notna(v) else None
        except: return None
    def _sf(v, d=1):
        try:    return round(float(v), d) if pd.notna(v) else None
        except: return None

    include_city = bool(district)
    records = []
    for _, row in sub.iterrows():
        rec = {
            "neighborhood":    _ss(row.get("neighborhood")),
            "street":          _ss(row.get("streetNameHeb")),
            "house_num":       _ss(row.get("houseNum")),
            "area":            _sf(row.get("assetArea")),
            "rooms":           _sf(row.get("assetRoomNum")),
            "floor":           _si(row.get("floor_num")),
            "deal_amount":     _si(row.get("dealAmount")),
            "predicted":       _si(row.get("predicted")),
            "viability_score": _sf(row.get("viability_score")),
            "deal_year":       _si(row.get("deal_year")),
        }
        if include_city:
            rec["city"] = _ss(row.get("settlementNameHeb"))
        records.append(rec)
    return {"records": records, "total": len(records)}


@app.get("/api/city-stats")
def city_stats(city: str):
    df  = _get_predictions()
    sub = df[df["settlementNameHeb"] == city]
    if sub.empty:
        return JSONResponse({"error": "עיר לא נמצאה"}, status_code=404)
    price_v = sub["dealAmount"].dropna()
    rooms_v = sub["assetRoomNum"].dropna()
    area_v  = sub["assetArea"].dropna()
    year_v  = sub["deal_year"].dropna()
    return {
        "deal_count":     int(len(sub)),
        "avg_price":      round(float(price_v.mean()))  if len(price_v) else 0,
        "avg_area":       round(float(area_v.mean()), 1) if len(area_v)  else 0,
        "avg_viability":  round(float(sub["viability_score"].mean()), 1),
        "min_price":      round(float(price_v.min()))   if len(price_v) else 0,
        "max_price":      round(float(price_v.max()))   if len(price_v) else 10_000_000,
        "min_rooms":      float(rooms_v.min())  if len(rooms_v) else 1.0,
        "max_rooms":      float(rooms_v.max())  if len(rooms_v) else 10.0,
        "min_area":       round(float(area_v.min()))    if len(area_v)  else 0,
        "max_area":       round(float(area_v.max()))    if len(area_v)  else 999,
        "min_year":       int(year_v.min()) if len(year_v) else 2000,
        "max_year":       int(year_v.max()) if len(year_v) else 2025,
        "yad2_supported": city in _YAD2_CITY_IDS,
    }


@app.get("/api/districts")
def get_districts():
    return JSONResponse(sorted(_DISTRICT_MAP.keys()))


@app.get("/api/district-stats")
def district_stats(district: str):
    cities = _DISTRICT_MAP.get(district, [])
    if not cities:
        return JSONResponse({"error": "מחוז לא נמצא"}, status_code=404)
    df  = _get_predictions()
    sub = df[df["settlementNameHeb"].isin(cities)]
    if sub.empty:
        return JSONResponse({"error": "לא נמצאו נתונים"}, status_code=404)
    price_v = sub["dealAmount"].dropna()
    rooms_v = sub["assetRoomNum"].dropna()
    area_v  = sub["assetArea"].dropna()
    year_v  = sub["deal_year"].dropna()
    return {
        "deal_count": int(len(sub)),
        "min_price":  round(float(price_v.min()))   if len(price_v) else 0,
        "max_price":  round(float(price_v.max()))   if len(price_v) else 10_000_000,
        "min_rooms":  float(rooms_v.min())  if len(rooms_v) else 1.0,
        "max_rooms":  float(rooms_v.max())  if len(rooms_v) else 10.0,
        "min_area":   round(float(area_v.min()))    if len(area_v)  else 0,
        "max_area":   round(float(area_v.max()))    if len(area_v)  else 999,
        "min_year":   int(year_v.min())  if len(year_v) else 2000,
        "max_year":   int(year_v.max())  if len(year_v) else 2025,
    }


class MapDataRequest(BaseModel):
    city: str
    rooms: float = 3.0
    lat: Optional[float] = None
    lon: Optional[float] = None
    street: Optional[str] = None

@app.post("/api/map-data")
def map_data(req: MapDataRequest):
    # ── Resolve center coordinates ─────────────────────────────────────────
    center_lat, center_lon, exact = req.lat, req.lon, True
    if not center_lat or not center_lon:
        exact = False
        query = ", ".join(filter(None, [req.street, req.city]))
        if query:
            center_lat, center_lon = _geocode(query)
        if not center_lat and req.city:
            center_lat, center_lon = _geocode(req.city)

    # ── Similar transactions (ITM → WGS84) ─────────────────────────────────
    similar = []
    mask    = df_d["settlementNameHeb"] == req.city
    sim_sub = df_d[mask & (df_d["assetRoomNum"] >= req.rooms - 0.5)
                        & (df_d["assetRoomNum"] <= req.rooms + 0.5)]
    valid = sim_sub.dropna(subset=["X", "Y"])
    if len(valid):
        lats, lons = _itm_to_wgs84(valid["X"], valid["Y"])
        street_col   = "streetNameHeb" if "streetNameHeb" in valid.columns else None
        house_col    = "houseNum"      if "houseNum"      in valid.columns else None
        year_col     = "deal_year"     if "deal_year"     in valid.columns else None
        for i, (lat, lon) in enumerate(zip(lats, lons)):
            if not (29 <= lat <= 34 and 34 <= lon <= 36):
                continue
            row = valid.iloc[i]
            street    = str(row[street_col]) if street_col and pd.notna(row[street_col]) else ""
            house_num = str(int(row[house_col])) if house_col and pd.notna(row[house_col]) else ""
            year      = int(row[year_col]) if year_col and pd.notna(row[year_col]) else None
            similar.append({
                "lat":       round(lat, 6),
                "lon":       round(lon, 6),
                "price":     int(row["dealAmount"]),
                "rooms":     float(row["assetRoomNum"]),
                "street":    street,
                "house_num": house_num,
                "year":      year,
            })

    # ── POI within 1 km ────────────────────────────────────────────────────
    pois = []
    poi_summary = []
    if center_lat and center_lon:
        poi_df = _get_poi_df()
        if len(poi_df):
            nearby = _get_local_pois(poi_df, center_lat, center_lon, radius_m=1000)
            if len(nearby):
                for _, row in nearby.iterrows():
                    pois.append({
                        "lat":      round(float(row["lat"]), 6),
                        "lon":      round(float(row["lon"]), 6),
                        "name":     str(row["name"]) if row["name"] else "",
                        "category": str(row["prefix"]),
                        "cat_heb":  str(row["cat_heb"]),
                        "dist_m":   int(row["dist_m"]),
                    })
                summary = (nearby.groupby(["prefix", "cat_heb"])
                           .agg(count=("dist_m", "count"), nearest=("dist_m", "min"))
                           .reset_index()
                           .sort_values("nearest"))
                for _, r in summary.iterrows():
                    poi_summary.append({
                        "cat":      r["prefix"],
                        "heb":      r["cat_heb"],
                        "emoji":    _CAT_EMOJI.get(r["prefix"], "📍"),
                        "color":    _FOLIUM_COLORS.get(r["prefix"], "#888"),
                        "count":    int(r["count"]),
                        "nearest":  int(r["nearest"]),
                    })

    return {
        "center":      {"lat": center_lat, "lon": center_lon, "exact": exact} if center_lat else None,
        "similar":     similar,
        "pois":        pois,
        "poi_summary": poi_summary,
    }


# ── Scraping helpers (ported from app_simple.py) ──────────────────────────────

_SCRAPERAPI_KEY = "0c71b8175708db5a86a7ff05805de670"


_YAD2_SEMAPHORE = threading.Semaphore(4)  # max 4 concurrent ScraperAPI requests


def _yad2_get(url: str, params: dict = None, timeout: int = 65) -> tuple:
    """Fetch a Yad2 URL via ScraperAPI (bypasses datacenter IP blocks)."""
    import requests as _req
    from urllib.parse import urlencode, quote_plus
    target = (url + "?" + urlencode(params)) if params else url
    api_url = f"http://api.scraperapi.com?api_key={_SCRAPERAPI_KEY}&country_code=il&url={quote_plus(target)}"
    for attempt in range(2):
        if attempt:
            time.sleep(3)
        with _YAD2_SEMAPHORE:
            try:
                r = _req.get(api_url, timeout=timeout)
                print(f"[yad2_get] {target[:80]} → status={r.status_code} len={len(r.text)}", flush=True)
                if r.status_code == 200 and len(r.text) > 3000:
                    return r.text, None
                return None, f"קוד שגיאה {r.status_code}"
            except Exception as exc:
                print(f"[yad2_get] attempt {attempt+1} ERROR → {exc}", flush=True)
                if attempt == 1:
                    return None, str(exc)
    return None, "failed"


from yad2_shared import _YAD2_HEADERS, _YAD2_CITY_IDS, _parse_yad2_search_html


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
            street    = sm.group(1).strip() if sm else street_raw.strip()
            house_num = sm.group(2) if sm else None
        elif len(parts) >= 4:
            street_raw = parts[1]
            hood = parts[2]
            city = parts[3].split("|")[0].strip()
            sm = re.match(r'^(.+?)\s+(\d+)$', street_raw)
            street    = sm.group(1).strip() if sm else street_raw.strip()
            house_num = sm.group(2) if sm else None
        if rooms or city:
            return {"price": None, "rooms": rooms, "area": None, "floor": None,
                    "city": city, "street": street, "house_num": house_num,
                    "error": "נמצאו פרטים חלקיים — חסר מחיר, השלם ידנית."}
        return {"error": "לא נמצא __NEXT_DATA__ — ודא שהדבקת את קוד המקור המלא."}

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"error": "שגיאה בפענוח JSON."}

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
        return {"error": "מבנה הנתונים לא מוכר."}

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

    city      = _txt(addr, "city")   or _get_str(listing, "city", "cityHeb")
    street    = _txt(addr, "street") or _get_str(listing, "street", "streetHeb")
    house     = addr.get("house") or {}
    floor     = (_get_num(house, "floor") or _get_num(add_d, "floor", "floorFormatted") or _get_num(listing, "floor"))
    rooms     = (_get_num(add_d, "roomsCount", "rooms", "roomNum") or _get_num(inp, "rooms") or _get_num(listing, "rooms", "roomNum"))
    area      = (_get_num(add_d, "squareMeter", "area", "meter") or _get_num(inp, "squareMeter", "area") or _get_num(listing, "squareMeter", "area", "meter"))
    coords_d  = addr.get("coords") or {}
    lat       = coords_d.get("lat")
    lon       = coords_d.get("lon")
    _hn       = (_get_num(house, "number") or _get_num(addr, "houseNum", "houseNumber") or _get_num(listing, "houseNum", "houseNumber"))
    house_num = str(int(_hn)) if _hn is not None else (_get_str(house, "number") or _get_str(addr, "houseNum"))

    if not price:
        return {"error": "לא נמצא מחיר במודעה."}
    return {"price": price, "rooms": rooms, "area": area, "floor": floor,
            "city": city, "street": street, "house_num": house_num, "lat": lat, "lon": lon}


def _scrape_yad2(url: str) -> dict:
    if not re.search(r"yad2\.co\.il/.*item/", url):
        return {"error": "הקישור אינו תקין — חייב להיות קישור לנכס ב-yad2.co.il"}
    html, err = _yad2_get(url, timeout=35)
    if html is None:
        return {"error": err or "שגיאת חיבור — בדוק חיבור לאינטרנט."}
    return _parse_yad2_html(html)


def _scrape_listing(url: str) -> dict:
    if re.search(r"yad2\.co\.il/.*item/", url):
        return _scrape_yad2(url)
    return {"error": "הקישור אינו תקין — יש להזין קישור מ-yad2.co.il"}


# ── POI / map helpers ─────────────────────────────────────────────────────────

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


def _itm_to_wgs84(x_ser: pd.Series, y_ser: pd.Series):
    """Convert ITM (EPSG:2039) easting/northing to WGS84 lat/lon arrays."""
    a   = 6_378_137.0
    f   = 1.0 / 298.257_222_101
    e2  = 2*f - f**2
    k0  = 1.000_006_7
    lam0 = np.radians(35.204_516_944)
    phi0 = np.radians(31.734_393_611)
    FE, FN = 219_529.584, 626_907.390

    x0 = x_ser.values.astype(float) - FE
    y0 = y_ser.values.astype(float) - FN

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


def _get_local_pois(poi_df: pd.DataFrame, lat: float, lon: float,
                    radius_m: float = 1000) -> pd.DataFrame:
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
    return nearby.sort_values("dist_m").reset_index(drop=True)


def _geocode(query: str):
    """Geocode an Israeli address via Nominatim. Returns (lat, lon) or (None, None)."""
    try:
        import requests as _req
        resp = _req.get(
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


# ── Yad2 city-listing scraper ─────────────────────────────────────────────────

_DISTRICT_MAP = {
    "מחוז ירושלים": [
        "ירושלים", "בית שמש", "מעלה אדומים", "גבעת זאב", "ביתר עילית",
        "מודיעין עילית", "אפרת", "קרית ארבע", "מבשרת ציון",
    ],
    "מחוז תל אביב": [
        "תל אביב יפו", "תל אביב-יפו", "תל אביב", "בת ים", "חולון", "בני ברק",
        "גבעתיים", "רמת גן", "אור יהודה", "גבעת שמואל", "קרית אונו",
        "יהוד מונוסון", "יהוד-מונוסון", "אלעד",
    ],
    "מחוז המרכז": [
        "ראשון לציון", "פתח תקווה", "רחובות", "נס ציונה", "לוד", "רמלה",
        "מודיעין מכבים רעות", "מודיעין-מכבים-רעות", "רעננה", "כפר סבא",
        "הוד השרון", "נתניה", "הרצליה", "רמת השרון", "ראש העין", "יבנה",
        "גדרה", "באר יעקב", "שוהם",
    ],
    "מחוז חיפה": [
        "חיפה", "קרית אתא", "קרית ביאליק", "קרית מוצקין", "קרית ים",
        "נשר", "טירת כרמל", "זכרון יעקב", "פרדס חנה כרכור", "פרדס חנה-כרכור",
        "חדרה", "אור עקיבא", "עכו", "נהריה",
    ],
    "מחוז הצפון": [
        "נצרת", "נוף הגליל", "עפולה", "קרית שמונה", "צפת",
        "טבריה", "כרמיאל", "מגדל העמק", "בית שאן",
        "מעלות תרשיחא", "מעלות-תרשיחא", "יוקנעם עילית",
    ],
    "מחוז הדרום": [
        "באר שבע", "אשדוד", "אשקלון", "דימונה", "קרית מלאכי",
        "נתיבות", "שדרות", "אופקים", "מצפה רמון", "רהט",
        "קריית גת", "קרית גת", "גן יבנה", "ירוחם", "ערד", "אילת",
    ],
}
_CITY_TO_DISTRICT = {c: d for d, cities in _DISTRICT_MAP.items() for c in cities}


_dynamic_city_ids: dict = {}  # city_name -> id (discovered via Yad2 API, None if not found)


def _lookup_yad2_city_id_api(city: str) -> Optional[int]:
    """Try to discover a Yad2 city ID via the GW API (best-effort)."""
    if city in _dynamic_city_ids:
        return _dynamic_city_ids[city]
    try:
        html, _ = _yad2_get(
            "https://gw.yad2.co.il/general/locations",
            params={"text": city, "lang": "he", "type": "0"},
            timeout=15,
        )
        if html:
            d = json.loads(html)
            items = (d.get("data", {}).get("cities") or d.get("cities") or
                     d.get("data") or [])
            if isinstance(items, dict):
                items = list(items.values())
            norm = city.strip().replace("-", " ").replace("–", " ")
            for item in (items if isinstance(items, list) else []):
                if not isinstance(item, dict):
                    continue
                name = (item.get("text") or item.get("name") or
                        item.get("cityName") or "").strip()
                if name == city or name.replace("-", " ") == norm:
                    cid = (item.get("id") or item.get("cityId") or
                           item.get("value") or item.get("code"))
                    if cid:
                        _dynamic_city_ids[city] = int(cid)
                        return int(cid)
    except Exception:
        pass
    _dynamic_city_ids[city] = None
    return None


def _fetch_yad2_search_page(city_id: Optional[int] = None, city_name: Optional[str] = None,
                            page: int = 1, timeout: int = 35):
    url = "https://www.yad2.co.il/realestate/forsale"
    params: dict = {"propertyGroup": "apartments", "propertyType": "1", "page": page}
    if city_id is not None:
        params["city"] = city_id
    elif city_name:
        params["cityText"] = city_name
    else:
        return None, "לא סופק מזהה עיר."
    return _yad2_get(url, params, timeout=timeout)



def _txt_field(d: dict, key: str) -> str:
    v = d.get(key)
    if isinstance(v, dict):
        return (v.get("text") or v.get("textHeb") or "").strip()
    return (v or "").strip() if isinstance(v, str) else ""


def _fetch_yad2_city_listings(city_heb: str, max_pages: int = 3):
    import difflib as _dl
    city_id = _YAD2_CITY_IDS.get(city_heb)
    if city_id is None:
        norm  = city_heb.strip().replace("-", " ").replace("–", " ")
        # Fuzzy match against expanded dict
        candidates = {k.replace("-", " ").replace("–", " "): v for k, v in _YAD2_CITY_IDS.items()}
        close = _dl.get_close_matches(norm, list(candidates.keys()), n=1, cutoff=0.75)
        if close:
            city_id = candidates[close[0]]
    if city_id is None:
        # Last resort: try Yad2 GW API
        city_id = _lookup_yad2_city_id_api(city_heb)

    all_items = []
    for page in range(1, max_pages + 1):
        if city_id is not None:
            html, err = _fetch_yad2_search_page(city_id=city_id, page=page)
        else:
            html, err = _fetch_yad2_search_page(city_name=city_heb, page=page)
        if err or not html:
            if page == 1:
                return [], f"שגיאת חיבור ליד2: {err or 'תגובה ריקה'}."
            break
        items, parse_err = _parse_yad2_search_html(html)
        if parse_err:
            if page == 1:
                return [], parse_err
            break
        real_ads = [i for i in items if isinstance(i, dict)
                    and i.get("type") not in {"commercial_promoted", "promoted_native",
                                               "banner", "promoted", "lead_gen"}]
        all_items.extend(real_ads)
        if len(items) < 25:
            break

    if not all_items:
        return [], "לא נמצאו מודעות. יד2 ייתכן וחסמה את הגישה."

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
        hood    = _txt_field(addr, "area") or _txt_field(addr, "neighborhood")
        street  = _txt_field(addr, "street")
        hn      = house.get("number")
        house_n = str(int(hn)) if hn is not None else ""
        floor_v = house.get("floor")
        area    = add_d.get("squareMeter") or add_d.get("squareMeters")
        rooms   = add_d.get("roomsCount")  or add_d.get("rooms")
        item_id = str(item.get("token") or item.get("orderId") or item.get("id") or "")
        rows.append({
            "neighborhood": hood,
            "street":       street,
            "house_num":    house_n,
            "area":         float(area)    if area    is not None else None,
            "rooms":        float(rooms)   if rooms   is not None else None,
            "floor":        int(floor_v)   if floor_v is not None else None,
            "asking_price": int(price),
            "yad2_id":      item_id,
        })
    return rows, ""


class Yad2BrowseRequest(BaseModel):
    city:      str
    max_pages: int = 3


@app.post("/api/yad2-browse")
def yad2_browse(req: Yad2BrowseRequest):
    rows, err = _fetch_yad2_city_listings(req.city, req.max_pages)
    if err or not rows:
        return JSONResponse({"error": err or "לא נמצאו מודעות"}, status_code=422)

    today      = datetime.date.today()
    city_mask  = df_d["settlementNameHeb"] == req.city
    sub_ml     = df_ml[city_mask]
    fvec_base  = sub_ml[feat_cols].median() if not sub_ml.empty else df_ml[feat_cols].median()

    records = []
    for row in rows:
        fv = fvec_base.copy()
        if row["area"]  is not None: fv["assetArea"]    = row["area"]
        if row["rooms"] is not None: fv["assetRoomNum"] = row["rooms"]
        if row["floor"] is not None: fv["floor_num"]    = float(row["floor"])
        fv["deal_year"]  = float(today.year)
        fv["deal_month"] = float(today.month)
        try:
            predicted = float(model.predict(fv[feat_cols].values.reshape(1, -1))[0])
        except Exception:
            predicted = None
        p    = float(row["asking_price"])
        viab = round(min(100.0, max(0.0, 50.0 + (predicted - p) / p * 100 * 1.5)), 1) \
               if predicted and p > 0 else 50.0
        records.append({
            "neighborhood":    row["neighborhood"],
            "street":          row["street"],
            "house_num":       row["house_num"],
            "area":            row["area"],
            "rooms":           row["rooms"],
            "floor":           row["floor"],
            "asking_price":    row["asking_price"],
            "predicted":       round(predicted) if predicted else None,
            "viability_score": viab,
            "yad2_id":         row["yad2_id"],
        })
    records.sort(key=lambda r: r["viability_score"], reverse=True)
    return {"records": records, "total": len(records)}


class Yad2BrowseDistrictRequest(BaseModel):
    district:  str
    max_pages: int = 2

@app.post("/api/yad2-browse-district")
def yad2_browse_district(req: Yad2BrowseDistrictRequest):
    cities    = _DISTRICT_MAP.get(req.district, [])
    supported = [c for c in cities if c in _YAD2_CITY_IDS]
    if not supported:
        return JSONResponse({"error": "אין ערים נתמכות ביד2 במחוז זה"}, status_code=422)

    today = datetime.date.today()

    def fetch_city(city):
        rows, err = _fetch_yad2_city_listings(city, req.max_pages)
        if err or not rows:
            return []
        city_mask = df_d["settlementNameHeb"] == city
        sub_ml    = df_ml[city_mask]
        fvec_base = sub_ml[feat_cols].median() if not sub_ml.empty else df_ml[feat_cols].median()
        city_recs = []
        for row in rows:
            fv = fvec_base.copy()
            if row["area"]  is not None: fv["assetArea"]    = row["area"]
            if row["rooms"] is not None: fv["assetRoomNum"] = row["rooms"]
            if row["floor"] is not None: fv["floor_num"]    = float(row["floor"])
            fv["deal_year"]  = float(today.year)
            fv["deal_month"] = float(today.month)
            try:
                predicted = float(model.predict(fv[feat_cols].values.reshape(1, -1))[0])
            except Exception:
                predicted = None
            p    = float(row["asking_price"])
            viab = round(min(100.0, max(0.0, 50.0 + (predicted - p) / p * 100 * 1.5)), 1) \
                   if predicted and p > 0 else 50.0
            city_recs.append({
                "city":            city,
                "neighborhood":    row["neighborhood"],
                "street":          row["street"],
                "house_num":       row["house_num"],
                "area":            row["area"],
                "rooms":           row["rooms"],
                "floor":           row["floor"],
                "asking_price":    row["asking_price"],
                "predicted":       round(predicted) if predicted else None,
                "viability_score": viab,
                "yad2_id":         row["yad2_id"],
            })
        city_recs.sort(key=lambda r: r["viability_score"], reverse=True)
        return city_recs[:5]

    all_records = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for city_recs in ex.map(fetch_city, supported):
            all_records.extend(city_recs)

    all_records.sort(key=lambda r: r["viability_score"], reverse=True)
    return {"records": all_records, "total": len(all_records)}



@app.get("/api/yad2-area-prices/status")
def yad2_area_status():
    return JSONResponse({
        "fetching": _yad2_area_busy,
        "prices":   _yad2_area_cache,
        "count":    len(_yad2_area_cache),
    })


class SetPricesRequest(BaseModel):
    prices: dict

@app.post("/api/yad2-set-prices")
def yad2_set_prices(req: SetPricesRequest, secret: str = ""):
    if secret != _DAILY_REFRESH_SECRET:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    global _yad2_area_cache, _yad2_area_ts
    _yad2_area_cache = {k: int(v) for k, v in req.prices.items()}
    _yad2_area_ts    = time.time()
    try:
        import datetime as _dt
        _DAILY_CACHE_PATH.write_text(
            json.dumps({"date": _dt.date.today().isoformat(), "prices": _yad2_area_cache}),
            encoding="utf-8",
        )
    except Exception:
        pass
    return JSONResponse({"status": "ok", "count": len(_yad2_area_cache)})



def _fetch_yad2_rent_page(city_id: Optional[int] = None, city_name: Optional[str] = None,
                          page: int = 1, timeout: int = 35):
    url = "https://www.yad2.co.il/realestate/rent"
    params: dict = {"propertyGroup": "apartments", "propertyType": "1", "page": page}
    if city_id is not None:
        params["city"] = city_id
    elif city_name:
        params["cityText"] = city_name
    else:
        return None, "לא סופק מזהה עיר."
    return _yad2_get(url, params, timeout=timeout)


def _fetch_yad2_city_rent_listings(city_heb: str, max_pages: int = 2):
    import difflib as _dl
    city_id = _YAD2_CITY_IDS.get(city_heb)
    if city_id is None:
        norm = city_heb.strip().replace("-", " ").replace("–", " ")
        candidates = {k.replace("-", " ").replace("–", " "): v for k, v in _YAD2_CITY_IDS.items()}
        close = _dl.get_close_matches(norm, list(candidates.keys()), n=1, cutoff=0.75)
        if close:
            city_id = candidates[close[0]]
    if city_id is None:
        city_id = _lookup_yad2_city_id_api(city_heb)

    all_items = []
    for page in range(1, max_pages + 1):
        if city_id is not None:
            html, err = _fetch_yad2_rent_page(city_id=city_id, page=page)
        else:
            html, err = _fetch_yad2_rent_page(city_name=city_heb, page=page)
        if err or not html:
            break
        items, parse_err = _parse_yad2_search_html(html)
        if parse_err or not items:
            break
        real_ads = [i for i in items if isinstance(i, dict)
                    and i.get("type") not in {"commercial_promoted", "promoted_native",
                                               "banner", "promoted", "lead_gen"}]
        all_items.extend(real_ads)
        if len(items) < 20:
            break

    rents = []
    for item in all_items:
        price = item.get("price")
        try:
            price = float(price)
        except (TypeError, ValueError):
            continue
        if price < 1_500 or price > 50_000:
            continue
        add_d = item.get("additionalDetails") or {}
        rooms = add_d.get("roomsCount") or add_d.get("rooms")
        area  = add_d.get("squareMeter") or add_d.get("squareMeters")
        rooms_f = float(rooms) if rooms is not None else None
        area_f  = float(area)  if area  is not None else None
        if rooms_f is not None and rooms_f < 1.5:
            continue
        if area_f is not None and area_f < 30:
            continue
        rents.append(int(price))

    return sorted(rents)


@app.post("/api/yad2-rent-prices/start")
def yad2_rent_start():
    global _yad2_rent_busy
    now = time.time()
    with _yad2_rent_lock:
        if _yad2_rent_busy:
            return JSONResponse({"status": "running", "rents": _yad2_rent_cache, "count": len(_yad2_rent_cache)})
        if now - _yad2_rent_ts < 1800 and _yad2_rent_cache:
            return JSONResponse({"status": "cached", "rents": _yad2_rent_cache, "count": len(_yad2_rent_cache)})
        _yad2_rent_busy = True

    def _run():
        global _yad2_rent_cache, _yad2_rent_ts, _yad2_rent_busy
        counts = df_d["settlementNameHeb"].value_counts()
        cities_to_fetch = [c for c in counts[counts >= 5].index.tolist() if isinstance(c, str)]

        seen_ids: set = set()
        unique_cities: list = []
        for city in cities_to_fetch:
            cid = _YAD2_CITY_IDS.get(city)
            if cid is None:
                unique_cities.append(city)
            elif cid not in seen_ids:
                seen_ids.add(cid)
                unique_cities.append(city)

        def _fetch_one(city):
            try:
                rents = _fetch_yad2_city_rent_listings(city, max_pages=2)
                if len(rents) >= 3:
                    idx = int(len(rents) * 0.50)  # median
                    return city, rents[min(idx, len(rents) - 1)]
            except Exception:
                pass
            return city, None

        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = {ex.submit(_fetch_one, c): c for c in unique_cities}
            for fut in as_completed(futs):
                city, rent = fut.result()
                if rent is None:
                    continue
                with _yad2_rent_lock:
                    _yad2_rent_cache[city] = rent
                    cid = _YAD2_CITY_IDS.get(city)
                    if cid:
                        for alt, aid in _YAD2_CITY_IDS.items():
                            if aid == cid:
                                _yad2_rent_cache[alt] = rent

        with _yad2_rent_lock:
            _yad2_rent_ts   = time.time()
            _yad2_rent_busy = False

    threading.Thread(target=_run, daemon=True).start()
    return JSONResponse({"status": "started", "rents": {}, "count": 0})


@app.get("/api/yad2-rent-prices/status")
def yad2_rent_status():
    return JSONResponse({
        "fetching": _yad2_rent_busy,
        "rents":    _yad2_rent_cache,
        "count":    len(_yad2_rent_cache),
    })


def _match_settlement(city: str, settlement_list: list):
    if not city:
        return None

    def _norm(s):
        s = s.strip().replace("\xa0", " ").replace("-", " ").replace("–", " ")
        return " ".join(s.split()).lower()

    def _norm_he(s):
        s = _norm(s)
        return s.replace("יי", "י").replace("וו", "ו").replace("'", "").replace('"', "")

    c_norm    = _norm(city)
    c_norm_he = _norm_he(city)
    for s in settlement_list:
        if _norm(s) == c_norm: return s
    for s in settlement_list:
        if _norm_he(s) == c_norm_he: return s
    for s in settlement_list:
        s_n = _norm(s)
        if c_norm in s_n or s_n in c_norm: return s
    norm_he_map = {_norm_he(s): s for s in settlement_list}
    close = difflib.get_close_matches(c_norm_he, norm_he_map.keys(), n=1, cutoff=0.82)
    if close:
        return norm_he_map[close[0]]
    return None
