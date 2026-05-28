import requests
import pandas as pd
import time
import random
import re
from pyproj import Transformer
from datetime import datetime, timedelta

transformer_to_mercator = Transformer.from_crs("EPSG:2039", "EPSG:3857")
transformer_to_itm = Transformer.from_crs("EPSG:3857", "EPSG:2039")

FIVE_YEARS_AGO = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
RECENT_FROM = "2025-01-01"

MAX_PER_CITY = 80
MAX_PER_BUILDING = 3
TARGET = 10000
STEP = 500

def get_polygon_at_point(x_itm, y_itm):
    x, y = transformer_to_mercator.transform(x_itm, y_itm)
    url = f"https://www.govmap.gov.il/api/real-estate/deals/{x},{y}/15.875"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data:
            return data[0]
    except:
        pass
    return None

def extract_centroid_itm(shape_str):
    try:
        coords = re.findall(r'([\d.]+) ([\d.]+)', shape_str)
        if coords:
            xs = [float(c[0]) for c in coords]
            ys = [float(c[1]) for c in coords]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            itm_x, itm_y = transformer_to_itm.transform(cx, cy)
            return round(itm_x, 2), round(itm_y, 2)
    except:
        pass
    return None, None

def get_all_recent_deals(polygon_id):
    all_deals = []
    offset = 0
    while True:
        url = f"https://www.govmap.gov.il/api/real-estate/street-deals/{polygon_id}"
        try:
            r = requests.get(url, params={"limit": 100, "offset": offset}, timeout=10)
            response = r.json()
            data = response.get("data", [])
        except:
            break
        if not data:
            break
        recent = [d for d in data if d.get("dealDate", "") >= FIVE_YEARS_AGO]
        all_deals.extend(recent)
        old = [d for d in data if d.get("dealDate", "") < FIVE_YEARS_AGO]
        if old or len(data) < 100:
            break
        offset += 100
        time.sleep(0.1)
    return all_deals

REGIONS = [
    {"x_min": 170000, "x_max": 200000, "y_min": 648000, "y_max": 672000},
    {"x_min": 205000, "x_max": 230000, "y_min": 624000, "y_max": 645000},
    {"x_min": 193000, "x_max": 215000, "y_min": 738000, "y_max": 758000},
    {"x_min": 172000, "x_max": 195000, "y_min": 568000, "y_max": 588000},
    {"x_min": 183000, "x_max": 200000, "y_min": 685000, "y_max": 705000},
    {"x_min": 155000, "x_max": 178000, "y_min": 612000, "y_max": 638000},
    {"x_min": 185000, "x_max": 205000, "y_min": 645000, "y_max": 665000},
    {"x_min": 210000, "x_max": 235000, "y_min": 725000, "y_max": 750000},
    {"x_min": 235000, "x_max": 258000, "y_min": 735000, "y_max": 765000},
    {"x_min": 185000, "x_max": 210000, "y_min": 630000, "y_max": 650000},
    {"x_min": 178000, "x_max": 193000, "y_min": 668000, "y_max": 682000},
    {"x_min": 170000, "x_max": 185000, "y_min": 638000, "y_max": 655000},
    {"x_min": 188000, "x_max": 202000, "y_min": 673000, "y_max": 685000},
    {"x_min": 183000, "x_max": 196000, "y_min": 353000, "y_max": 368000},
    {"x_min": 205000, "x_max": 220000, "y_min": 758000, "y_max": 775000},
    {"x_min": 198000, "x_max": 212000, "y_min": 622000, "y_max": 635000},
    {"x_min": 200000, "x_max": 218000, "y_min": 658000, "y_max": 675000},
    {"x_min": 172000, "x_max": 184000, "y_min": 602000, "y_max": 615000},
    {"x_min": 188000, "x_max": 205000, "y_min": 538000, "y_max": 558000},
    {"x_min": 155000, "x_max": 172000, "y_min": 578000, "y_max": 598000},
]

points = []
for region in REGIONS:
    for y in range(region["y_min"], region["y_max"], STEP):
        for x in range(region["x_min"], region["x_max"], STEP):
            points.append((x, y))

random.shuffle(points)
print(f"סהכ {len(points)} נקודות לסריקה")

seen_polygons = set()
all_deals = []
city_counts = {}
city_recent_counts = {}
city_exhausted = {}

for x, y in points:
    print(f"סורק {x},{y}...", end="\r")

    result = get_polygon_at_point(x, y)
    if not result:
        continue

    city = result.get("settlementNameHeb", "לא ידוע")
    current_count = city_counts.get(city, 0)
    current_recent = city_recent_counts.get(city, 0)
    min_recent = max(1, int(current_count * 0.25))

    # בדוק אם להמשיך לעיר זו
    if current_count >= MAX_PER_CITY:
        if current_recent >= min_recent:
            continue
        if city_exhausted.get(city, False):
            continue

    polygon_id = result["polygon_id"]
    if polygon_id in seen_polygons:
        continue
    seen_polygons.add(polygon_id)

    deals = get_all_recent_deals(polygon_id)
    if not deals:
        continue

    # חלץ קואורדינטות
    shape_str = deals[0].get("shape", "")
    itm_x, itm_y = extract_centroid_itm(shape_str)

    if current_count < MAX_PER_CITY:
        # לקח אקראי מ-5 שנים, מקסימום 3 לבניין
        remaining_city = MAX_PER_CITY - current_count
        random.shuffle(deals)
        selected = deals[:min(MAX_PER_BUILDING, remaining_city)]
    else:
        # הגיע ל-80 אבל חסר recent – לקח רק מ-2025-2026
        recent_deals = [d for d in deals if d.get("dealDate", "") >= RECENT_FROM]
        if not recent_deals:
            city_exhausted[city] = True
            continue
        remaining_recent = min_recent - current_recent
        random.shuffle(recent_deals)
        selected = recent_deals[:min(MAX_PER_BUILDING, remaining_recent)]

    # הוסף קואורדינטות
    for deal in selected:
        deal["itm_x"] = itm_x
        deal["itm_y"] = itm_y

    new_recent = len([d for d in selected if d.get("dealDate", "") >= RECENT_FROM])
    city_counts[city] = current_count + len(selected)
    city_recent_counts[city] = current_recent + new_recent
    all_deals.extend(selected)

    street = result.get("streetNameHeb", "")
    print(f"→ {city} {street} | {len(selected)} | עיר: {city_counts[city]} | 2025+: {city_recent_counts[city]} | סהכ: {len(all_deals)}")

    if len(all_deals) >= TARGET:
        print("\nהגענו ל-10,000!")
        break

    time.sleep(0.2)

df = pd.DataFrame(all_deals)
df.to_csv("nadlan_sample.csv", index=False, encoding="utf-8-sig")
print(f"\nסיום! {len(df)} עסקאות נשמרו ל-nadlan_sample.csv")
print("\nעסקאות לפי יישוב:")
for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
    recent = city_recent_counts.get(city, 0)
    print(f"  {city}: {count} סהכ | {recent} מ-2025+")