import pandas as pd
import numpy as np
import json, os

CSV_PATH     = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA.csv'
CLEAN_PATH   = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA_clean.csv'
REPORT_PATH  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\missing_report.html'

# ── 1. Load ──────────────────────────────────────────────────────────────────
# Header at row 6 (0-indexed), skip rows 7 and 8 (Hebrew header + nationwide)
df_raw = pd.read_csv(CSV_PATH, header=6, skiprows=[7, 8], encoding='utf-8-sig', low_memory=False)

# Fix column name for locality
cols = list(df_raw.columns)
if cols[1] == '' or pd.isna(cols[1]):
    cols[1] = 'LOCALITY_NAME'
df_raw.columns = cols

print(f"Loaded: {df_raw.shape[0]} rows x {df_raw.shape[1]} columns")

# ── 2. Mark ".." as NaN (CBS code for suppressed data) ───────────────────────
df = df_raw.replace('..', np.nan)
df = df.replace('', np.nan)

# Also strip whitespace from string columns
for c in df.select_dtypes(include='object').columns:
    df[c] = df[c].str.strip().replace('', np.nan)

# Drop entirely unnamed trailing columns (Unnamed: 50+)
named_cols = [c for c in df.columns if not str(c).startswith('Unnamed:') or df[c].notna().any()]
df = df[named_cols]

total_rows = len(df)

# ── 3. Before snapshot ───────────────────────────────────────────────────────
before_rows = df.shape[0]
before_cols = df.shape[1]
miss_before = df.isnull().sum()
pct_before  = (miss_before / total_rows * 100).round(1)

# ── 4. Drop columns with >50% missing ────────────────────────────────────────
drop_cols = pct_before[pct_before > 50].index.tolist()
df_clean  = df.drop(columns=drop_cols)
print(f"Dropped {len(drop_cols)} columns with >50% missing: {drop_cols[:5]}...")

# ── 5. Impute remaining missing values ───────────────────────────────────────
impute_log = {}
for col in df_clean.columns:
    n_miss = df_clean[col].isnull().sum()
    if n_miss == 0:
        continue
    # Try numeric conversion
    converted = pd.to_numeric(df_clean[col], errors='coerce')
    if converted.notna().sum() > converted.isna().sum():          # mostly numeric
        fill_val = converted.mean()
        df_clean[col] = converted.fillna(fill_val)
        impute_log[col] = {'method': 'mean', 'value': round(fill_val, 4), 'n_filled': int(n_miss)}
    else:                                                          # categorical
        mode_series = df_clean[col].mode()
        fill_val = mode_series.iloc[0] if len(mode_series) else 'UNKNOWN'
        df_clean[col] = df_clean[col].fillna(fill_val)
        impute_log[col] = {'method': 'mode', 'value': str(fill_val), 'n_filled': int(n_miss)}

# ── 6. After snapshot ────────────────────────────────────────────────────────
after_rows = df_clean.shape[0]
after_cols = df_clean.shape[1]
miss_after = df_clean.isnull().sum().sum()

# ── 7. Save clean CSV ────────────────────────────────────────────────────────
df_clean.to_csv(CLEAN_PATH, index=False, encoding='utf-8-sig')
print(f"Saved clean CSV: {after_rows} rows x {after_cols} cols, {miss_after} missing")

# ── 8. Build column report table rows ───────────────────────────────────────
table_rows = []
for col in df.columns:
    n = int(miss_before[col])
    p = float(pct_before[col])
    dropped = col in drop_cols
    imputed = col in impute_log

    if dropped:
        status = '<span style="background:#da3633;color:#fff;padding:2px 9px;border-radius:10px;font-size:.75em;">&#10006; נמחקה</span>'
        action = 'נמחקה (>50%)'
    elif imputed:
        info = impute_log[col]
        m = info['method']
        v = info['value']
        filled = info['n_filled']
        label = 'ממוצע' if m == 'mean' else 'ערך שכיח'
        status = '<span style="background:#1f6feb;color:#fff;padding:2px 9px;border-radius:10px;font-size:.75em;">&#8635; מולאה</span>'
        action = f'{label}: {v} ({filled} ערכים)'
    else:
        status = '<span style="background:#238636;color:#fff;padding:2px 9px;border-radius:10px;font-size:.75em;">&#10003; תקין</span>'
        action = 'אין פעולה'

    bar_w  = min(100, int(p))
    bar_col = '#da3633' if p > 50 else ('#1f6feb' if p > 10 else '#238636')

    table_rows.append(
        '<tr>'
        f'<td><code style="font-size:.78em">{col[:40]}</code></td>'
        f'<td style="text-align:center">{n:,}</td>'
        f'<td>'
        f'<div style="display:flex;align-items:center;gap:.5rem">'
        f'<div style="width:80px;background:#21262d;border-radius:4px;height:8px">'
        f'<div style="width:{bar_w}%;background:{bar_col};height:100%;border-radius:4px"></div>'
        f'</div>'
        f'<span style="font-size:.82em;color:{bar_col}">{p}%</span>'
        f'</div>'
        f'</td>'
        f'<td>{status}</td>'
        f'<td style="font-size:.8em;color:#8b949e">{action}</td>'
        '</tr>'
    )

table_html = '\n'.join(table_rows)

html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Missing Values Report</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Heebo',sans-serif;background:#0d1117;color:#c9d1d9;padding:2rem}}
h1{{color:#58a6ff;font-size:1.5rem;margin-bottom:.3rem}}
.sub{{color:#8b949e;font-size:.85rem;margin-bottom:2rem}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1.2rem 1.5rem;position:relative;overflow:hidden}}
.card::before{{content:'';position:absolute;top:0;right:0;width:4px;height:100%;background:var(--c)}}
.card .val{{font-size:1.9rem;font-weight:700;color:var(--c)}}
.card .lbl{{font-size:.8rem;color:#8b949e;margin-top:.3rem}}
.section{{background:#161b22;border:1px solid #21262d;border-radius:14px;overflow:hidden;margin-bottom:1.5rem}}
.section-head{{padding:1rem 1.5rem;border-bottom:1px solid #21262d;display:flex;align-items:center;gap:.5rem;font-weight:600}}
table{{width:100%;border-collapse:collapse}}
th{{background:#0d1117;color:#8b949e;padding:.7rem 1rem;font-size:.78rem;text-align:right;font-weight:600;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #21262d}}
td{{padding:.65rem 1rem;font-size:.85rem;border-bottom:1px solid #161b22}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#1c2128}}
code{{background:#21262d;padding:2px 6px;border-radius:4px;font-size:.78rem;direction:ltr;display:inline-block}}
.before-after{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:2rem}}
.ba{{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1.2rem 1.5rem}}
.ba h3{{font-size:.85rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:1rem}}
.ba .row{{display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid #21262d;font-size:.85rem}}
.ba .row:last-child{{border-bottom:none}}
.ba .row span{{color:#58a6ff;font-weight:600}}
</style>
</head>
<body>

<h1>&#128202; Missing Values Report &mdash; DATA.csv</h1>
<div class="sub">ניתוח ערכים חסרים, מחיקת עמודות וטיפול בחסרים</div>

<!-- Summary Cards -->
<div class="cards">
  <div class="card" style="--c:#58a6ff">
    <div class="val">{before_cols}</div>
    <div class="lbl">עמודות מקוריות</div>
  </div>
  <div class="card" style="--c:#da3633">
    <div class="val">{len(drop_cols)}</div>
    <div class="lbl">נמחקו (&gt;50% חסרים)</div>
  </div>
  <div class="card" style="--c:#1f6feb">
    <div class="val">{len(impute_log)}</div>
    <div class="lbl">עמודות מולאו</div>
  </div>
  <div class="card" style="--c:#3fb950">
    <div class="val">{after_cols}</div>
    <div class="lbl">עמודות לאחר ניקוי</div>
  </div>
</div>

<!-- Before / After -->
<div class="before-after">
  <div class="ba">
    <h3>&#128204; לפני ניקוי</h3>
    <div class="row">שורות <span>{before_rows:,}</span></div>
    <div class="row">עמודות <span>{before_cols}</span></div>
    <div class="row">סה"כ ערכים חסרים <span>{int(miss_before.sum()):,}</span></div>
    <div class="row">% חסרים מסה"כ תאים <span>{miss_before.sum()/(before_rows*before_cols)*100:.1f}%</span></div>
  </div>
  <div class="ba">
    <h3>&#10003; אחרי ניקוי</h3>
    <div class="row">שורות <span>{after_rows:,}</span></div>
    <div class="row">עמודות <span>{after_cols}</span></div>
    <div class="row">סה"כ ערכים חסרים <span>{miss_after:,}</span></div>
    <div class="row">% חסרים מסה"כ תאים <span>{miss_after/(after_rows*after_cols)*100:.2f}%</span></div>
  </div>
</div>

<!-- Detail Table -->
<div class="section">
  <div class="section-head">&#128203; פירוט לפי עמודה ({before_cols} עמודות)</div>
  <table>
    <thead><tr><th>שם עמודה</th><th>חסרים (#)</th><th>% חסרים</th><th>סטטוס</th><th>פעולה</th></tr></thead>
    <tbody>{table_html}</tbody>
  </table>
</div>

<p style="color:#30363d;font-size:.75rem;margin-top:1rem">
  &#128190; קובץ נקי נשמר: DATA_clean.csv &bull; {after_rows:,} שורות &times; {after_cols} עמודות
</p>
</body>
</html>"""

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nReport saved to: {REPORT_PATH}")
print(f"\n=== SUMMARY ===")
print(f"Before: {before_rows} rows x {before_cols} cols | {int(miss_before.sum()):,} missing")
print(f"After:  {after_rows} rows x {after_cols} cols  | {miss_after} missing")
print(f"Dropped cols: {len(drop_cols)}")
print(f"Imputed cols: {len(impute_log)}")
