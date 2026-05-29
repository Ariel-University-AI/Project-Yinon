"""
יועץ נדל"ן חכם — Real Estate Investment Advisor
Run:  streamlit run app.py
"""
import pathlib
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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='יועץ נדל"ן חכם',
    layout="wide",
    page_icon="🏠",
)

st.markdown("""
<style>
  /* Metrics */
  [data-testid="stMetricValue"]    { font-size: 1.65rem !important; font-weight: 800; }
  [data-testid="stMetricLabel"]    { font-size: .78rem; color: #555; }
  [data-testid="metric-container"] {
    background: #f7f9fc;
    border: 1px solid #dde3ea;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  }

  /* Layout */
  .block-container { padding-top: 0.5rem; padding-bottom: 2rem; }
  h2, h3, h4       { direction: rtl; }
  hr                { margin: 1.2rem 0; border-color: #e5e7eb; }

  /* Tabs */
  .stTabs [data-baseweb="tab"] {
    font-size: 1rem;
    font-weight: 600;
    padding: 8px 28px;
  }

  /* Selectbox / inputs labels */
  label { font-weight: 600 !important; }
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

    stats = df_d.groupby("settlementNameHeb").agg(
        avg_price  = ("dealAmount",      "mean"),
        avg_gap    = ("gap_pct",         "mean"),
        deal_count = ("dealAmount",      "count"),
        avg_socio  = ("socio_index_avg", "mean"),
        avg_lat    = ("N",               "mean"),
        avg_lon    = ("E",               "mean"),
    ).join(trend_s).reset_index()

    return stats


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


@st.cache_resource
def load_model(mdl_path: str):
    return joblib.load(mdl_path)


@st.cache_data
def get_settlement_baselines(ml_path: str, disp_path: str) -> pd.DataFrame:
    df_ml = pd.read_csv(ml_path,   encoding="utf-8-sig")
    df_d  = pd.read_csv(disp_path, encoding="utf-8-sig")
    df_ml = df_ml.copy()
    df_ml["settlementNameHeb"] = df_d["settlementNameHeb"]
    return df_ml.groupby("settlementNameHeb").median()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_profile, tab_mode_a, tab_mode_b, tab_mode_c, tab_explain = st.tabs([
    "👤 פרופיל",
    "🗺️ מצב א׳",
    "🏘️ מצב ב׳",
    "🔍 מצב ג׳",
    "📖 הסברים",
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

    # Summary card
    st.divider()
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("תקציב", f"{st.session_state.get('budget_max', 2_000_000):,.0f} ₪")
    s2.metric("מטרה", st.session_state.get("investment_goal", "תשואה שוטפת"))
    s3.metric("סיכון", st.session_state.get("risk_level", "שוק מבוסס"))
    s4.metric("אופק", st.session_state.get("horizon", "קצר (1-3 שנה)"))
    s5.metric("תשואה מינ'", f"{st.session_state.get('min_yield', 5)}%")
    s6.metric("מינ' עסקאות", st.session_state.get("min_deals", 10))

    st.info("עבור למצב א׳ כדי לראות המלצות אזורים לפי הפרופיל.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MODE A: AREA RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_a:
    st.markdown("## 🗺️ מצב א׳ — המלצת אזורים")

    stats = compute_settlement_stats(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # Read profile from session_state
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
    h_yrs = HORIZON_YEARS[horizon]

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
        ma1.metric("יישובים שנמצאו",       len(filtered))
        ma2.metric("ציון מקסימלי",          f"{top['viability_score']:.0f} / 100")
        ma3.metric("מחיר ממוצע — מוביל",    f"{top['avg_price']:,.0f} ILS")
        ma4.metric("פער ממוצע — מוביל",     f"{top['avg_gap']:+.1f}%")
        ma5.metric("תשואה משוערת — מוביל",  f"{top['est_yield_pct']:+.1f}%/שנה")

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

        show["מחיר ממוצע (₪)"]        = show["מחיר ממוצע (₪)"].round(0).astype(int)
        show["פער ממוצע (%)"]          = show["פער ממוצע (%)"].round(1)
        show["תשואה משוערת (%/שנה)"]   = show["תשואה משוערת (%/שנה)"].round(1)
        show["מגמה (%/שנה)"]           = show["מגמה (%/שנה)"].round(1)
        show["מדד סוציו"]               = show["מדד סוציו"].round(2)

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

        df_d = load_display_data(str(APT_DISP_PATH))
        map_pts = (
            df_d[df_d["settlementNameHeb"].isin(filtered["settlementNameHeb"])]
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


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MODE B: PROPERTY RANKING IN SETTLEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_b:
    st.markdown("## 🏘️ מצב ב׳ — נכסים ביישוב")

    df_all = compute_all_predictions(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # ── Settlement selector ───────────────────────────────────────────────────
    settlements_list = sorted(df_all["settlementNameHeb"].dropna().unique().tolist())
    default_idx = settlements_list.index("בת ים") if "בת ים" in settlements_list else 0
    selected_settlement = st.selectbox("בחר יישוב", settlements_list, index=default_idx)

    df_settle = df_all[df_all["settlementNameHeb"] == selected_settlement].copy()

    # ── Settlement summary ────────────────────────────────────────────────────
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("עסקאות ביישוב",    len(df_settle))
    sm2.metric("מחיר ממוצע",       f"{df_settle['dealAmount'].mean():,.0f} ILS")
    sm3.metric("שטח ממוצע",        f"{df_settle['assetArea'].mean():.0f} מ\"ר")
    sm4.metric("ציון כדאיות ממוצע", f"{df_settle['viability_score'].mean():.1f} / 100")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("### פילטרים")
    f1, f2, f3 = st.columns(3)

    area_vals  = df_settle["assetArea"].dropna()
    rooms_vals = df_settle["assetRoomNum"].dropna()
    year_vals  = df_settle["deal_year"].dropna()

    with f1:
        area_range = st.slider(
            'שטח (מ"ר)',
            float(area_vals.min()), float(area_vals.max()),
            (float(area_vals.min()), float(area_vals.max())),
        )
    with f2:
        rooms_range = st.slider(
            "חדרים",
            float(rooms_vals.min()), float(rooms_vals.max()),
            (float(rooms_vals.min()), float(rooms_vals.max())),
            step=0.5,
        )
    with f3:
        year_range = st.slider(
            "שנת עסקה",
            int(year_vals.min()), int(year_vals.max()),
            (int(year_vals.min()), int(year_vals.max())),
        )

    # ── Apply filters & rank ──────────────────────────────────────────────────
    mask = (
        df_settle["assetArea"].between(area_range[0], area_range[1]) &
        df_settle["assetRoomNum"].between(rooms_range[0], rooms_range[1]) &
        df_settle["deal_year"].between(year_range[0], year_range[1])
    )
    df_ranked = df_settle[mask].sort_values("viability_score", ascending=False).copy()

    st.markdown(f"**{len(df_ranked)} נכסים** אחרי פילטור — מדורגים לפי ציון כדאיות (מהגבוה לנמוך):")

    # ── Table ─────────────────────────────────────────────────────────────────
    show_b = df_ranked.rename(columns={
        "neighborhood":  "שכונה",
        "streetNameHeb": "רחוב",
        "houseNum":      "מס' בית",
        "assetArea":     'שטח (מ"ר)',
        "assetRoomNum":  "חדרים",
        "floor_num":     "קומה",
        "dealAmount":    "מחיר בפועל (₪)",
        "predicted":     "מחיר חזוי (₪)",
        "viability_score": "ציון כדאיות",
        "deal_year":     "שנה",
    }).copy()

    show_b["מחיר בפועל (₪)"] = show_b["מחיר בפועל (₪)"].round(0).astype(int)
    show_b["מחיר חזוי (₪)"]  = show_b["מחיר חזוי (₪)"].round(0).astype(int)
    show_b["ציון כדאיות"]     = show_b["ציון כדאיות"].round(1)
    show_b['שטח (מ"ר)']       = show_b['שטח (מ"ר)'].round(1)
    show_b["קומה"]             = show_b["קומה"].round(0).astype(int)

    st.dataframe(
        show_b[["שכונה", "רחוב", "מס' בית", 'שטח (מ"ר)', "חדרים", "קומה",
                "מחיר בפועל (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "שנה"]],
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
# TAB 3 — MODE C: SINGLE DEAL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_mode_c:
    st.markdown("## 🔍 מצב ג׳ — בדיקת עסקה ספציפית")

    baselines = get_settlement_baselines(str(APT_ML_PATH), str(APT_DISP_PATH))
    df_all_c  = compute_all_predictions(str(APT_ML_PATH), str(APT_DISP_PATH), str(MODEL_PATH))

    # ── Inputs ────────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### פרטי הנכס")
        ic1, ic2, ic3, ic4 = st.columns(4)

        settlements_c = sorted(baselines.index.tolist())
        default_c = settlements_c.index("בת ים") if "בת ים" in settlements_c else 0

        with ic1:
            settlement_c = st.selectbox("יישוב", settlements_c, index=default_c, key="c_settlement")
        with ic2:
            area_c  = st.number_input('שטח (מ"ר)', min_value=20, max_value=500, value=80, step=5, key="c_area")
        with ic3:
            rooms_c = st.number_input("חדרים", min_value=1.0, max_value=10.0, value=3.0, step=0.5, key="c_rooms")
        with ic4:
            floor_c = st.number_input("קומה", min_value=0, max_value=50, value=2, step=1, key="c_floor")

        pc1, _ = st.columns([1, 2])
        with pc1:
            asking_price = st.number_input(
                "מחיר מבוקש (₪)",
                min_value=100_000, max_value=20_000_000,
                value=1_500_000, step=50_000, format="%d", key="c_price",
            )

    st.divider()

    # ── Predict ───────────────────────────────────────────────────────────────
    mdl = load_model(str(MODEL_PATH))
    row = baselines.loc[settlement_c].copy()
    row["assetArea"]    = float(area_c)
    row["assetRoomNum"] = float(rooms_c)
    row["floor_num"]    = float(floor_c)

    predicted  = float(mdl.predict(pd.DataFrame([row.drop("dealAmount")]))[0])
    price_diff = predicted - asking_price
    gap_pct    = price_diff / asking_price * 100

    viability = float(np.clip(50 + gap_pct * 1.5, 0, 100))

    # ── Metrics ───────────────────────────────────────────────────────────────
    rc1, rc2, rc3, rc4 = st.columns(4)
    rc1.metric("מחיר חזוי ע\"י המודל", f"{predicted:,.0f} ILS")
    rc2.metric("מחיר מבוקש",           f"{asking_price:,.0f} ILS")
    rc3.metric("הפרש",                  f"{price_diff:+,.0f} ILS")
    rc4.metric("ציון כדאיות",           f"{viability:.0f} / 100")

    # ── Verdict ───────────────────────────────────────────────────────────────
    if viability >= 65:
        st.success(f"עסקה טובה — המודל מעריך שהנכס שווה {price_diff:+,.0f} ILS יותר מהמחיר המבוקש.")
    elif viability >= 40:
        st.warning(f"עסקה סבירה — פער של {price_diff:+,.0f} ILS ביחס לשוק.")
    else:
        st.error(f"מחיר גבוה — המודל מעריך שהנכס שווה {abs(price_diff):,.0f} ILS פחות מהמחיר המבוקש.")

    st.divider()

    # ── Similar properties ────────────────────────────────────────────────────
    st.markdown("### השוואה לעסקאות דומות ביישוב")

    similar = df_all_c[
        (df_all_c["settlementNameHeb"] == settlement_c) &
        (df_all_c["assetArea"].between(area_c * 0.75, area_c * 1.25)) &
        (df_all_c["assetRoomNum"].between(rooms_c - 0.5, rooms_c + 0.5))
    ].sort_values("viability_score", ascending=False).copy()

    if similar.empty:
        st.info("לא נמצאו עסקאות דומות. נסה להרחיב את טווח השטח או החדרים.")
    else:
        avg_actual = similar["dealAmount"].mean()
        diff_vs_avg = asking_price - avg_actual
        st.caption(f"{len(similar)} עסקאות דומות נמצאו · מחיר ממוצע: {avg_actual:,.0f} ILS")

        show_c = similar.rename(columns={
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
        show_c["קומה"]             = show_c["קומה"].round(0).astype(int)

        st.dataframe(
            show_c[["שכונה", "רחוב", 'שטח (מ"ר)', "חדרים", "קומה",
                     "מחיר בפועל (₪)", "מחיר חזוי (₪)", "ציון כדאיות", "שנה"]].head(10),
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

        direction = "גבוה" if diff_vs_avg > 0 else "נמוך"
        st.info(
            f"המחיר המבוקש **{direction}** ב-{abs(diff_vs_avg):,.0f} ILS "
            f"ביחס לממוצע עסקאות דומות ({avg_actual:,.0f} ILS)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EXPLANATIONS
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