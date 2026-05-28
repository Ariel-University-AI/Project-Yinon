"""
יועץ נדל"ן חכם — Real Estate Investment Advisor
Run:  streamlit run app.py
"""
import pathlib
import numpy as np
import pandas as pd
import joblib
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE          = pathlib.Path(__file__).parent
MODEL_PATH    = BASE / "model.pkl"
APT_ML_PATH   = BASE / "DATA_FILES" / "apartments_ml_ready.csv"
APT_DISP_PATH = BASE / "DATA_FILES" / "apartments_display.csv"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='יועץ נדל"ן חכם',
    layout="wide",
    page_icon="🏠",
)

st.markdown("""
<style>
  [data-testid="stMetricValue"]  { font-size: 2rem !important; font-weight: 800; }
  [data-testid="stMetricLabel"]  { font-size: .85rem; }
  .block-container               { padding-top: 1.2rem; padding-bottom: 2rem; }
  h2, h3                         { direction: rtl; }
</style>
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

    stats = df_d.groupby("settlementNameHeb").agg(
        avg_price  = ("dealAmount",      "mean"),
        avg_gap    = ("gap_pct",         "mean"),
        deal_count = ("dealAmount",      "count"),
        avg_socio  = ("socio_index_avg", "mean"),
    ).join(trend_s).reset_index()

    return stats


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_mode_a, tab_explain = st.tabs(["🗺️ מצב א׳ — המלצת אזורים", "📖 הסברים"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MODE A: AREA RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_a:
    st.markdown("## 🗺️ מצב א׳ — המלצת אזורים")

    stats = compute_settlement_stats(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # ── Profile inputs ────────────────────────────────────────────────────────
    st.markdown("### הגדר פרופיל השקעה")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        budget_max = st.number_input(
            "תקציב מקסימום (₪)",
            min_value=300_000, max_value=10_000_000,
            value=2_000_000, step=100_000, format="%d",
        )
    with p2:
        investment_goal = st.selectbox(
            "מטרת השקעה",
            ["תשואה שוטפת", "עליית ערך"],
        )
    with p3:
        risk_level = st.selectbox(
            "רמת סיכון מועדפת",
            ["שוק מבוסס", "שוק מתפתח"],
        )
    with p4:
        min_deals = st.slider(
            "מינ' עסקאות ביישוב",
            min_value=5, max_value=50, value=10,
            help="מינימום עסקאות ביישוב — אינדיקטור לנזילות השוק",
        )

    st.divider()

    # ── Filter by profile ─────────────────────────────────────────────────────
    filtered = stats[stats["avg_price"] <= budget_max].copy()

    socio_med = stats["avg_socio"].median()
    if risk_level == "שוק מבוסס":
        filtered = filtered[filtered["avg_socio"] >= socio_med]
    else:
        filtered = filtered[filtered["avg_socio"] < socio_med]

    filtered = filtered[filtered["deal_count"] >= min_deals].copy()

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
        ma1, ma2, ma3, ma4 = st.columns(4)
        ma1.metric("יישובים שנמצאו",     len(filtered))
        ma2.metric("ציון מקסימלי",        f"{top['viability_score']:.0f} / 100")
        ma3.metric("מחיר ממוצע — מוביל",  f"{top['avg_price']:,.0f} ILS")
        ma4.metric("פער ממוצע — מוביל",   f"{top['avg_gap']:+.1f}%")

        # ── Table ─────────────────────────────────────────────────────────────
        show = filtered.rename(columns={
            "settlementNameHeb": "יישוב",
            "viability_score":   "ציון כדאיות",
            "avg_price":         "מחיר ממוצע (₪)",
            "avg_gap":           "פער ממוצע (%)",
            "trend_pct_yr":      "מגמה (%/שנה)",
            "deal_count":        "עסקאות",
            "avg_socio":         "מדד סוציו",
        }).copy()

        show["מחיר ממוצע (₪)"] = show["מחיר ממוצע (₪)"].round(0).astype(int)
        show["פער ממוצע (%)"]  = show["פער ממוצע (%)"].round(1)
        show["מגמה (%/שנה)"]   = show["מגמה (%/שנה)"].round(1)
        show["מדד סוציו"]       = show["מדד סוציו"].round(2)

        st.dataframe(
            show[["יישוב", "ציון כדאיות", "מחיר ממוצע (₪)", "פער ממוצע (%)",
                  "מגמה (%/שנה)", "עסקאות", "מדד סוציו"]].head(15),
            hide_index=True,
            use_container_width=True,
        )

        # ── Score legend ──────────────────────────────────────────────────────
        st.info(
            f"**ציון כדאיות** ({investment_goal}): "
            f"פער מחיר {int(w_gap*100)}% + מגמה {int(w_trend*100)}% + נזילות {int(w_liq*100)}%  |  "
            f"**פער חיובי** = נמכרו מתחת למחיר השוק (הזדמנות)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EXPLANATIONS
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