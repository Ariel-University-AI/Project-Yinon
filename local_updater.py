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
RENDER_URL  = "https://nadlanist.onrender.com/api/yad2-set-prices"
SECRET      = "nadlanist_daily_2024"
UPDATE_DAYS = 7  # עדכן פעם בשבוע
STATE_FILE  = pathlib.Path.home() / ".nadlanist_last_update.json"

sys.path.insert(0, str(pathlib.Path(__file__).parent / "HTML_PAGES"))
from yad2_shared import _YAD2_CITY_IDS, _YAD2_HEADERS, _parse_yad2_search_html

# ── Check if already ran this week ───────────────────────────────────────────
def already_ran():
    if not STATE_FILE.exists():
        return False
    try:
        data  = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        last  = datetime.date.fromisoformat(data.get("date", "2000-01-01"))
        return (datetime.date.today() - last).days < UPDATE_DAYS
    except Exception:
        return False

def mark_ran():
    STATE_FILE.write_text(
        json.dumps({"date": datetime.date.today().isoformat()}),
        encoding="utf-8",
    )

# ── Fetch one city directly (no proxy) ───────────────────────────────────────
def fetch_city_price(city_heb: str, city_id: int):
    url    = "https://www.yad2.co.il/realestate/forsale"
    params = {"propertyGroup": "apartments", "propertyType": "1", "page": "1", "city": city_id}
    html   = None
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
            return None

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

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if already_ran():
        print("כבר עודכן השבוע — דילוג.")
        return

    print("מתחיל טעינת מחירי יד2...")
    prices = {}
    seen_ids = set()

    for city, city_id in _YAD2_CITY_IDS.items():
        if city_id in seen_ids:
            continue
        seen_ids.add(city_id)
        price = fetch_city_price(city, city_id)
        if price:
            prices[city] = price
            print(f"  + {city}: {price:,}")
        else:
            print(f"  - {city}")
        time.sleep(0.5)

    print(f"\nנטענו {len(prices)} ערים. שולח ל-Render...")

    import requests as _req
    r = _req.post(
        RENDER_URL,
        params={"secret": SECRET},
        json={"prices": prices},
        timeout=30,
    )
    if r.ok:
        print(f"OK: {r.json()}")
        mark_ran()
    else:
        print(f"ERROR: {r.status_code} {r.text}")

if __name__ == "__main__":
    main()
