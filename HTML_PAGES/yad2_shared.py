"""
Shared Yad2 constants and helpers — no heavy dependencies.
Imported by both main.py (Render) and local_updater.py (local machine).
"""
import re
import json

_YAD2_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_YAD2_CITY_IDS = {
    # מחוז תל אביב — CBS codes verified from data.gov.il
    "תל אביב יפו": 5000, "תל אביב-יפו": 5000, "תל אביב": 5000,
    "בת ים": 6200, "חולון": 6600, "בני ברק": 6100,
    "גבעתיים": 6300, "רמת גן": 8600,
    "אור יהודה": 6710, "גבעת שמואל": 6350,
    "קרית אונו": 7520, "יהוד מונוסון": 6850, "יהוד-מונוסון": 6850,
    "אלעד": 1309,
    # מחוז ירושלים
    "ירושלים": 3000,
    "בית שמש": 2610, "מעלה אדומים": 3616, "גבעת זאב": 3730,
    "ביתר עילית": 3780, "מודיעין עילית": 3797, "אפרת": 3650,
    "קרית ארבע": 1102, "מבשרת ציון": 1055,
    # מחוז המרכז
    "ראשון לציון": 8300, "פתח תקווה": 7900, "רחובות": 8400,
    "נס ציונה": 7200, "לוד": 7000, "רמלה": 8500,
    "מודיעין מכבים רעות": 1200, "מודיעין-מכבים-רעות": 1200, "מודיעין": 1200,
    "רעננה": 8700, "כפר סבא": 6900, "הוד השרון": 9700,
    "נתניה": 7400, "הרצליה": 6400, "רמת השרון": 2650,
    "ראש העין": 2640, "יבנה": 2660, "גדרה": 2550,
    "באר יעקב": 6010, "שוהם": 1304,
    # מחוז חיפה
    "חיפה": 4000,
    "קרית אתא": 6800, "קרית ביאליק": 9500, "קרית מוצקין": 8200, "קרית ים": 9600,
    "נשר": 7360, "טירת כרמל": 5160, "זכרון יעקב": 9300,
    "פרדס חנה כרכור": 7810, "פרדס חנה-כרכור": 7810,
    "חדרה": 6500, "אור עקיבא": 417, "עכו": 7600, "נהריה": 9100,
    # מחוז הצפון
    "נצרת": 7300, "נוף הגליל": 1061, "עפולה": 7700,
    "קרית שמונה": 2800, "צפת": 8000, "טבריה": 6700,
    "כרמיאל": 1139, "מגדל העמק": 874, "בית שאן": 9200,
    "מעלות תרשיחא": 1085, "מעלות-תרשיחא": 1085, "יוקנעם עילית": 1041,
    # מחוז הדרום
    "באר שבע": 9000, "אשדוד": 70, "אשקלון": 7100,
    "דימונה": 2200, "קרית מלאכי": 1034, "קריית גת": 7680, "קרית גת": 7680,
    "נתיבות": 246, "שדרות": 1031, "אופקים": 31,
    "מצפה רמון": 99, "גן יבנה": 166,
    "ירוחם": 831, "ערד": 2560, "אילת": 2600,
}


def _parse_yad2_search_html(html: str):
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None, "לא נמצאו נתונים — יד2 ייתכן וחסמה את הגישה."
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, "שגיאה בפענוח נתוני העמוד."
    pp = data.get("props", {}).get("pageProps", {})

    def _collect(feed_dict):
        result = []
        for key in ("private", "agency", "platinum", "trio", "booster"):
            bucket = feed_dict.get(key) or []
            if isinstance(bucket, list):
                result.extend(b for b in bucket if isinstance(b, dict) and b.get("price"))
        return result

    top_feed = pp.get("feed")
    if isinstance(top_feed, dict):
        items = _collect(top_feed)
        if items:
            return items, None
    for q in pp.get("dehydratedState", {}).get("queries", []):
        sd = q.get("state", {}).get("data", {})
        if isinstance(sd, dict):
            items = _collect(sd)
            if items:
                return items, None
    return None, "לא נמצאו מודעות בעמוד."
