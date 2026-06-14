"""
local_updater.py — מושך מחירי יד2 מה-IP הביתי ושולח ל-Render.
רץ אוטומטית בכל התחברות למחשב, מתעדכן פעם בשבוע.

הפעלה ידנית:  python local_updater.py
"""
import sys
import json
import pathlib
import datetime
import time

# ── Config ────────────────────────────────────────────────────────────────────
RENDER_PRICES = "https://nadlanist.onrender.com/api/yad2-set-prices"
RENDER_RENTS  = "https://nadlanist.onrender.com/api/yad2-set-rents"
SECRET        = "nadlanist_daily_2024"
UPDATE_DAYS   = 7
STATE_FILE    = pathlib.Path.home() / ".nadlanist_last_update.json"

sys.path.insert(0, str(pathlib.Path(__file__).parent / "HTML_PAGES"))
from yad2_shared import _YAD2_CITY_IDS, _YAD2_HEADERS, _parse_yad2_search_html

# ── Check if already ran this week ───────────────────────────────────────────
def already_ran():
    if not STATE_FILE.exists():
        return False
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        last = datetime.date.fromisoformat(data.get("date", "2000-01-01"))
        return (datetime.date.today() - last).days < UPDATE_DAYS
    except Exception:
        return False

def mark_ran():
    STATE_FILE.write_text(
        json.dumps({"date": datetime.date.today().isoformat()}),
        encoding="utf-8",
    )

# ── Shared: fetch HTML from Yad2 ─────────────────────────────────────────────
def _fetch_html(url, params):
    html = None
    try:
        from curl_cffi import requests as _cr
        for ver in ["chrome124", "chrome120", "chrome116"]:
            try:
                s = _cr.Session(impersonate=ver)
                s.headers.update(_YAD2_HEADERS)
                r = s.get(url, params=params, timeout=15)
                if r.status_code == 200 and len(r.text) > 10_000:
                    html = r.text
                    break
            except Exception:
                continue
    except ImportError:
        pass

    if html is None:
        import requests as _req
        try:
            r = _req.get(url, params=params, headers=_YAD2_HEADERS, timeout=15)
            if r.status_code == 200 and len(r.text) > 10_000:
                html = r.text
        except Exception:
            pass
    return html

# ── Fetch sale price for one city ────────────────────────────────────────────
def fetch_city_price(city_id: int):
    html = _fetch_html(
        "https://www.yad2.co.il/realestate/forsale",
        {"propertyGroup": "apartments", "propertyType": "1", "page": "1", "city": city_id},
    )
    if not html:
        return None
    rows, _ = _parse_yad2_search_html(html)
    if not rows:
        return None
    filtered = [
        r["price"] for r in rows
        if r.get("price", 0) > 300_000
        and (r.get("rooms") is None or r["rooms"] >= 2.0)
        and (r.get("area")  is None or r["area"]  >= 40)
    ]
    prices = sorted(filtered) if filtered else sorted(
        [r["price"] for r in rows if r.get("price", 0) > 300_000]
    )
    if len(prices) >= 3:
        idx = int(len(prices) * 0.60)
        return prices[min(idx, len(prices) - 1)]
    return None

# ── Fetch rent price for one city ────────────────────────────────────────────
def fetch_city_rent(city_id: int):
    html = _fetch_html(
        "https://www.yad2.co.il/realestate/rent",
        {"propertyGroup": "apartments", "propertyType": "1", "page": "1", "city": city_id},
    )
    if not html:
        return None
    rows, _ = _parse_yad2_search_html(html)
    if not rows:
        return None
    rents = []
    for r in rows:
        try:
            price = float(r.get("price", 0))
        except (TypeError, ValueError):
            continue
        if price < 1_500 or price > 50_000:
            continue
        add_d = r.get("additionalDetails") or {}
        rooms = add_d.get("roomsCount") or add_d.get("rooms")
        area  = add_d.get("squareMeter") or add_d.get("squareMeters")
        rooms_f = float(rooms) if rooms is not None else None
        area_f  = float(area)  if area  is not None else None
        if rooms_f is not None and rooms_f < 1.5:
            continue
        if area_f is not None and area_f < 30:
            continue
        rents.append(int(price))
    rents.sort()
    if len(rents) >= 3:
        idx = int(len(rents) * 0.50)
        return rents[min(idx, len(rents) - 1)]
    return None

# ── Post to Render ────────────────────────────────────────────────────────────
def post_to_render(url, payload_key, data):
    import requests as _req
    r = _req.post(url, params={"secret": SECRET}, json={payload_key: data}, timeout=30)
    if r.ok:
        print(f"OK: {r.json()}")
    else:
        print(f"ERROR: {r.status_code} {r.text}")
    return r.ok

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if already_ran():
        print("כבר עודכן השבוע — דילוג.")
        return

    seen_ids = set()
    unique = []
    for city, city_id in _YAD2_CITY_IDS.items():
        if city_id not in seen_ids:
            seen_ids.add(city_id)
            unique.append((city, city_id))

    # ── מחירי מכירה ──────────────────────────────────────────────────────────
    print("מתחיל טעינת מחירי מכירה...")
    prices = {}
    for city, city_id in unique:
        price = fetch_city_price(city_id)
        if price:
            prices[city] = price
            print(f"  + {city}: {price:,}")
        else:
            print(f"  - {city}")
        time.sleep(0.5)

    print(f"\nנטענו {len(prices)} ערים (מכירה). שולח ל-Render...")
    post_to_render(RENDER_PRICES, "prices", prices)

    # ── מחירי שכירות ─────────────────────────────────────────────────────────
    print("\nמתחיל טעינת מחירי שכירות...")
    rents = {}
    for city, city_id in unique:
        rent = fetch_city_rent(city_id)
        if rent:
            rents[city] = rent
            print(f"  + {city}: {rent:,}")
        else:
            print(f"  - {city}")
        time.sleep(0.5)

    print(f"\nנטענו {len(rents)} ערים (שכירות). שולח ל-Render...")
    post_to_render(RENDER_RENTS, "rents", rents)

    mark_ran()

if __name__ == "__main__":
    main()
