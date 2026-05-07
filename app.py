"""
Streamlit EDA Dashboard — Real Estate Bat Yam
Run:  streamlit run app.py
"""
import pathlib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE     = pathlib.Path(__file__).parent
CSV_PATH = BASE / "DATA_FILES" / "BATYAM_2M" / "bat_yam_clean.csv"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='EDA — בת ים | יועץ נדל"ן',
    layout="wide",
    page_icon="📊",
)

st.markdown("""
<style>
  [data-testid="stMetricValue"]  { font-size: 2rem !important; font-weight: 800; }
  [data-testid="stMetricLabel"]  { font-size: .85rem; }
  .block-container               { padding-top: 1.2rem; padding-bottom: 2rem; }
  h2, h3                         { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig", low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df["dealDate"] = pd.to_datetime(df["dealDate"], errors="coerce")
    return df


df_raw   = load_data()
num_cols = df_raw.select_dtypes(include="number").columns.tolist()
PALETTE  = px.colors.qualitative.Plotly

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_eda, tab_explain = st.tabs(["📊 EDA Dashboard", "📖 הסברים על הגרפים"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EDA
# ══════════════════════════════════════════════════════════════════════════════
with tab_eda:
    st.markdown("## 📊 EDA Dashboard — בת ים")

    # ── Filter bar ────────────────────────────────────────────────────────────
    deal_natures = sorted(df_raw["dealNatureDescription"].dropna().unique().tolist())
    selected = st.multiselect(
        "🔗 סנן לפי סוג עסקה (dealNatureDescription):",
        options=deal_natures,
        default=[],
        placeholder="הכל — ללא סינון",
    )
    df = (
        df_raw[df_raw["dealNatureDescription"].isin(selected)].copy()
        if selected
        else df_raw.copy()
    )

    # ── Metrics ───────────────────────────────────────────────────────────────
    missing_pct = round(df_raw.isnull().sum().sum() / df_raw.size * 100, 2)
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "📈 שורות מסוננות",
        f"{len(df):,}",
        delta=f"{len(df) - len(df_raw):+,}" if selected else None,
    )
    m2.metric("📋 עמודות", df_raw.shape[1])
    m3.metric("❌ ערכים חסרים (מקור)", f"{missing_pct}%")

    st.divider()

    # ── Histogram ─────────────────────────────────────────────────────────────
    st.markdown("### 📊 Histogram — התפלגות עמודה")

    all_hist_cols = [c for c in df_raw.columns if c != "dealDate"]
    hc1, hc2 = st.columns([3, 1])
    with hc1:
        default_h = "dealAmount" if "dealAmount" in all_hist_cols else all_hist_cols[0]
        hist_col = st.selectbox(
            "בחר עמודה:", all_hist_cols, index=all_hist_cols.index(default_h)
        )
    with hc2:
        hist_bins = st.select_slider("Bins:", options=[10, 20, 30, 50], value=20)

    is_num    = hist_col in num_cols
    use_stack = len(selected) > 1

    if is_num:
        h_df = df.dropna(subset=[hist_col])
        fig_hist = px.histogram(
            h_df,
            x=hist_col,
            color="dealNatureDescription" if use_stack else None,
            nbins=hist_bins,
            barmode="stack" if use_stack else "overlay",
            template="plotly_dark",
            color_discrete_sequence=PALETTE,
        )
        fig_hist.update_layout(
            showlegend=use_stack,
            bargap=0.05,
            height=370,
            margin=dict(t=30, b=30, l=40, r=20),
            xaxis_title=hist_col,
            yaxis_title="כמות",
        )
        st.plotly_chart(fig_hist, width="stretch")

        v = h_df[hist_col]
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("n",          f"{len(v):,}")
        s2.metric("ממוצע",      f"{v.mean():,.0f}")
        s3.metric("חציון",      f"{v.median():,.0f}")
        s4.metric("סטיית תקן",  f"{v.std():,.0f}")
        s5.metric("מינימום",    f"{v.min():,.0f}")
        s6.metric("מקסימום",    f"{v.max():,.0f}")

    else:
        freq = df[hist_col].fillna("(חסר)").value_counts().head(30)
        fig_hist = px.bar(
            x=freq.values,
            y=freq.index,
            orientation="h",
            template="plotly_dark",
            color=freq.values,
            color_continuous_scale="Blues",
        )
        fig_hist.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            height=max(300, len(freq) * 28),
            margin=dict(t=30, b=30, l=40, r=20),
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="כמות",
        )
        st.plotly_chart(fig_hist, width="stretch")

        u1, u2, u3 = st.columns(3)
        u1.metric("ייחודיים",     df[hist_col].nunique())
        u2.metric("הנפוץ ביותר", str(freq.index[0]))
        u3.metric("כמות הנפוץ",  f"{freq.iloc[0]:,}")

    st.divider()

    # ── Scatter ───────────────────────────────────────────────────────────────
    st.markdown("### ✨ Scatter Plot — קשר בין שתי עמודות")

    x_opts = ["dealDate"] + num_cols
    sc1, sc2 = st.columns(2)
    with sc1:
        scat_x = st.selectbox("ציר X:", x_opts, index=0)
    with sc2:
        default_y = "dealAmount" if "dealAmount" in num_cols else num_cols[0]
        scat_y = st.selectbox("ציר Y:", num_cols, index=num_cols.index(default_y))

    x_is_date = scat_x == "dealDate"
    drop_on   = (["dealDate"] if x_is_date else [scat_x]) + [scat_y]
    scat_df   = df.dropna(subset=drop_on).copy()

    if scat_df.empty:
        st.warning("אין נתונים להצגה עבור הבחירה הנוכחית.")
    else:
        # Build one trace per deal-nature category
        nat_colors = {n: PALETTE[i % len(PALETTE)] for i, n in enumerate(deal_natures)}
        fig_scat   = go.Figure()

        nats_present = scat_df["dealNatureDescription"].dropna().unique().tolist()
        for nat in nats_present:
            sub = scat_df[scat_df["dealNatureDescription"] == nat]
            x_vals = sub["dealDate"] if x_is_date else sub[scat_x]
            y_vals = sub[scat_y]

            x_hover = "%{x|%d/%m/%Y}" if x_is_date else "%{x:,.0f}"
            fig_scat.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers",
                name=nat,
                marker=dict(color=nat_colors.get(nat, "#58a6ff"), opacity=0.65, size=6),
                hovertemplate=(
                    f"<b>{nat}</b><br>"
                    f"{'תאריך' if x_is_date else scat_x}: {x_hover}<br>"
                    f"{scat_y}: %{{y:,.0f}}<extra></extra>"
                ),
            ))

        # Regression line — numeric x only
        r_val = None
        if not x_is_date:
            xa = scat_df[scat_x].values.astype(float)
            ya = scat_df[scat_y].values.astype(float)
            ok = ~(np.isnan(xa) | np.isnan(ya))
            if ok.sum() >= 2:
                slope, intercept = np.polyfit(xa[ok], ya[ok], 1)
                xline = np.array([xa[ok].min(), xa[ok].max()])
                fig_scat.add_trace(go.Scatter(
                    x=xline,
                    y=slope * xline + intercept,
                    mode="lines",
                    name="קו מגמה",
                    line=dict(color="#d29922", width=2, dash="dash"),
                ))
                r_val = float(np.corrcoef(xa[ok], ya[ok])[0, 1])

        fig_scat.update_layout(
            template="plotly_dark",
            height=430,
            margin=dict(t=30, b=30, l=40, r=20),
            xaxis_title="תאריך עסקה" if x_is_date else scat_x,
            yaxis_title=scat_y,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_scat, width="stretch")

        # Stats row
        if r_val is not None:
            p1, p2, p3 = st.columns(3)
            p1.metric("נקודות",            f"{ok.sum():,}")
            p2.metric("מתאם Pearson (r)",  f"{r_val:.4f}")
            p3.metric("שיפוע",             f"{slope:.4e}")
        else:
            st.caption(f"נקודות: {len(scat_df):,}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EXPLANATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_explain:
    st.markdown("## 📖 הסברים על הגרפים")

    # ── 1. Histogram ──────────────────────────────────────────────────────────
    with st.expander("📊 Histogram — מה הוא מראה?", expanded=True):
        st.markdown("""
**Histogram (היסטוגרמה)** מחלק את טווח הערכים של עמודה ל-*bins* (סלים) שווים,
ומציג את **כמות הרשומות** שנופלות בכל סל.

#### כיצד לקרוא:
| אלמנט | משמעות |
|-------|--------|
| **ציר X** | טווח ערכים (מחיר, שטח, חדרים…) |
| **ציר Y** | כמות עסקאות באותו טווח |
| **סל גבוה** | ריכוז גבוה של עסקאות |
| **זנב ימני ארוך** | ערכים גבוהים נדירים שמושכים את הממוצע למעלה |
| **Bins** | יותר סלים = רזולוציה גבוהה יותר, אבל רועש יותר |

#### תוצאות בנתוני בת ים:
- **`dealAmount`** — skewed ימינה: רוב העסקאות ₪500K–₪2M, עם מעט עסקאות יקרות מאוד
- **`assetArea`** — שיא ב-70–100 מ"ר (דירות 3–4 חדרים טיפוסיות)
- **`assetRoomNum`** — שיא ב-3 חדרים (שוק האמצע של בת ים)

#### סינון ו-Stacked:
כשבוחרים מספר סוגי עסקה, הסלים הופכים ל**מחסנות** (stacked) — כל צבע מייצג קטגוריה אחת.
זה מאפשר לראות האם הפיזור שונה בין סוגי נכסים שונים.
        """)

    # ── 2. Scatter ────────────────────────────────────────────────────────────
    with st.expander("✨ Scatter Plot — מה הוא מראה?", expanded=True):
        st.markdown(r"""
**Scatter Plot (גרף פיזור)** מציג כל עסקה כנקודה אחת, כדי לחשוף קשרים בין שתי עמודות.

#### קו המגמה (רגרסיה ליניארית):
$$y = a \cdot x + b$$

- **שיפוע חיובי** → ככל ש-X עולה, Y נוטה לעלות
- **שיפוע שלילי** → קשר הפוך
- **ברירת מחדל:** `dealDate` (תאריך) מול `dealAmount` (מחיר) — מראה מגמת מחירים לאורך זמן

#### מתאם Pearson (r):
| טווח \|r\| | פירוש |
|------------|-------|
| 0.7 – 1.0 | קשר חזק ✅ |
| 0.4 – 0.7 | קשר בינוני 🟡 |
| 0.0 – 0.4 | קשר חלש / אין קשר ⚪ |
| שלילי | קשר הפוך |

#### תוצאות בנתוני בת ים (שורות `assetArea > 20`):
| עמודה | r עם dealAmount | הערה |
|-------|----------------|-------|
| `assetArea` | **0.296** | חלש-בינוני — בגלל ערבוב סוגי נכסים |
| `assetRoomNum` | **0.026** | מזוהם — 60 ערכים חסרים הוחלפו בממוצע |
| `X` (קואורדינטה) | **-0.092** | חלש |
| `Y` (קואורדינטה) | **0.021** | חלש |

> 💡 **המסקנה:** `dealNatureDescription` ו-`neighborhood` הם המנבאים החזקים ביותר —
> לא ניתן לכידתם על ידי Pearson r פשוט כי הם **קטגוריאליים**.
        """)

    # ── 3. Filter bar ─────────────────────────────────────────────────────────
    with st.expander("🔗 סינון לפי סוג עסקה — למה זה חשוב?", expanded=False):
        st.markdown("""
#### סוגי העסקאות בנתוני בת ים:
        """)
        deal_stats = pd.DataFrame({
            "סוג עסקה": ["דירה בבית קומות", "דירת גן", "קרקע", "מחסן", "בניין", "אחר"],
            "ממוצע מחיר (₪)": ["1,220,000", "2,160,000", "1,180,000", "714,000", "27,000,000", "—"],
            "כמות עסקאות": ["1,083", "30", "13", "10", "5", "~28"],
        })
        st.dataframe(deal_stats, width="stretch", hide_index=True)

        st.markdown("""
#### למה לסנן?

- **ערבוב כל הסוגים** מדלל מתאמים — מחסן ב-₪714K ובניין ב-₪27M על אותו גרף מוסיפים רעש
- **לאימון ML** מומלץ לפלטר ל-`דירה בבית קומות` בלבד (1,083 עסקאות עם הגיון מחיר אחיד)
- **הפרדה ויזואלית בצבעים** מאפשרת לגלות שדפוס `dealDate` שונה בין סוגי נכסים
        """)

    # ── 4. Column influence ───────────────────────────────────────────────────
    with st.expander("📋 אילו עמודות משפיעות על המחיר? — סיכום ניתוח", expanded=True):
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("""
#### ✅ משפיעים חזק:
1. **`dealNatureDescription`** — טווח x37 בין מחסן לבניין
2. **`neighborhood`** — פקטור x4.2 (חוף ים vs. פנים עיר)
3. **`assetArea`** — r=0.296 ישירות; אחרי סינון לדירות בלבד צפוי r~0.6+

#### ⚠️ משפיעים — צריכים ניקוי:
4. **`assetRoomNum`** — r=0.026 כרגע (זיהום), לאחר ניקוי צפוי r~0.5+
5. **`floorNo`** — טקסט עברי ("ראשונה", "שנייה") → NaN; צריך מיפוי למספרים

#### ❌ מתאם נמוך ישיר:
6. **`X, Y`** — r~0; כנראה יועילו כ-Feature Engineering (מרחק מהים/רכבת)
            """)

        with col_r:
            st.markdown("""
#### 🛠️ המלצות לפני אימון ML:

**1. סנן לדירות בלבד**
```python
df = df[df['dealNatureDescription'] == 'דירה בבית קומות']
```

**2. קודד קומות לעברית→מספר**
```python
floor_map = {'קרקע': 0, 'ראשונה': 1,
             'שנייה': 2, 'שלישית': 3, ...}
df['floor_num'] = df['floorNo'].map(floor_map)
```

**3. סמן שורות עם מספר חדרים מולא**
```python
df['rooms_imputed'] = df['assetRoomNum'].isna().astype(int)
```

**4. Feature Engineering גיאוגרפי**
```python
# מרחק מהים (נקודה קבועה)
from math import dist
df['dist_sea'] = df.apply(
    lambda r: dist((r['X'], r['Y']), (SEA_X, SEA_Y)), axis=1
)
```
            """)

    # ── 5. Dataset info ───────────────────────────────────────────────────────
    with st.expander("📁 על הנתונים — מקור ועיבוד", expanded=False):
        info_l, info_r = st.columns(2)

        with info_l:
            st.markdown(f"""
**מקור:** רשות המיסים — nadlan.gov.il
**עיר:** בת ים
**שורות לאחר ניקוי:** {len(df_raw):,}
**עמודות:** {df_raw.shape[1]}

#### שלבי עיבוד:
1. סינון מ-`nadlan_final.csv` לעסקאות בת ים
2. עמודות עם >50% חסרים — **נמחקו** (אף עמודה לא עמדה בקריטריון)
3. חסרים מספריים → **ממוצע**
   חסרים קטגוריאליים → **ערך שכיח (mode)**
4. `assetArea > 20` — מסיר חניות ומחסנות קטנים
            """)

        with info_r:
            col_info = pd.DataFrame([
                ("dealDate",              "תאריך העסקה"),
                ("dealAmount",            "מחיר העסקה (₪)"),
                ("assetArea",             'שטח הנכס (מ"ר)'),
                ("assetRoomNum",          "מספר חדרים"),
                ("floorNo",               "קומה (טקסט עברי)"),
                ("dealNatureDescription", "סוג הנכס"),
                ("neighborhood",          "שכונה"),
                ("streetName",            "שם הרחוב"),
                ("X",                     "קואורדינטת X (Israel TM)"),
                ("Y",                     "קואורדינטת Y (Israel TM)"),
                ("settlementNameHeb",     "שם היישוב"),
            ], columns=["עמודה", "תיאור"])
            st.dataframe(col_info, width="stretch", hide_index=True)
