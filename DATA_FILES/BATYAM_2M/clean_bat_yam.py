import pandas as pd
import numpy as np
import json

CSV_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\nadlan_final.csv'
OUT_CSV  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\bat_yam_clean.csv'
OUT_HTML = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\bat_yam_clean.html'

# ── 1. Load & filter ─────────────────────────────────────────────────────────
df_all = pd.read_csv(CSV_PATH, encoding='utf-8-sig', low_memory=False)
df_all.columns = [c.strip() for c in df_all.columns]

df = df_all[df_all['settlementNameHeb'] == 'בת ים'].copy().reset_index(drop=True)
n_rows, n_cols = df.shape

# ── 2. Before snapshot ───────────────────────────────────────────────────────
before = []
for col in df.columns:
    null_n   = int(df[col].isnull().sum())
    null_pct = round(null_n / n_rows * 100, 1)
    dtype    = str(df[col].dtype)
    before.append({'col': col, 'dtype': dtype, 'null_n': null_n, 'null_pct': null_pct})

# ── 3. Drop columns with >50% missing ────────────────────────────────────────
drop_cols = [b['col'] for b in before if b['null_pct'] > 50]
df.drop(columns=drop_cols, inplace=True)

# ── 4. Impute remaining missing values ───────────────────────────────────────
fill_log = {}   # col -> (strategy, value_used)

for col in df.columns:
    if df[col].isnull().sum() == 0:
        continue
    if df[col].dtype in [np.float64, np.int64, 'float64', 'int64']:
        val = df[col].mean()
        df[col] = df[col].fillna(val)
        fill_log[col] = ('ממוצע', round(float(val), 4))
    else:
        mode_vals = df[col].mode()
        val = mode_vals.iloc[0] if len(mode_vals) > 0 else ''
        df[col] = df[col].fillna(val)
        fill_log[col] = ('ערך שכיח', str(val))

# ── 5. After snapshot ────────────────────────────────────────────────────────
after = {}
for col in df.columns:
    after[col] = int(df[col].isnull().sum())

# ── 6. Save cleaned CSV ──────────────────────────────────────────────────────
df.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')

# ── 7. Build HTML report ──────────────────────────────────────────────────────

# Color helpers
def pct_color(p):
    if p == 0:    return '#3fb950'   # green  – no missing
    if p <= 20:   return '#d29922'   # yellow – few missing
    if p <= 50:   return '#f97316'   # orange – moderate
    return '#f87171'                 # red    – dropped

def dtype_badge(dtype):
    if 'int' in dtype:   return ('#4ade80', 'int')
    if 'float' in dtype: return ('#60a5fa', 'float')
    return ('#f59e0b', 'text')

# Before table rows
before_rows = ''
for b in before:
    dropped = b['col'] in drop_cols
    dc, dl = dtype_badge(b['dtype'])
    pc = pct_color(b['null_pct'])
    row_bg = 'background:#2a1515' if dropped else ''
    tag = '<span style="background:#f87171;color:#111;padding:1px 7px;border-radius:8px;font-size:.75em;font-weight:700">מחוק</span>' if dropped else ''
    before_rows += (
        f'<tr style="{row_bg}">'
        f'<td><code>{b["col"]}</code> {tag}</td>'
        f'<td><span class="badge" style="background:{dc};color:#111">{dl}</span></td>'
        f'<td>{b["null_n"]:,}</td>'
        f'<td><span class="pct-pill" style="background:{pc}">{b["null_pct"]}%</span></td>'
        f'</tr>'
    )

# After table rows (only kept cols)
after_rows = ''
for col in df.columns:
    dc, dl = dtype_badge(str(df[col].dtype))
    strategy, fill_val = fill_log.get(col, ('—', ''))
    was_null = next((b['null_n'] for b in before if b['col'] == col), 0)
    was_pct  = next((b['null_pct'] for b in before if b['col'] == col), 0.0)
    note = f'<span style="color:#94a3b8;font-size:.78em">{strategy}: <code>{fill_val}</code></span>' if strategy != '—' else '<span style="color:#3fb950;font-size:.78em">✓ ללא חסרים</span>'
    after_rows += (
        f'<tr>'
        f'<td><code>{col}</code></td>'
        f'<td><span class="badge" style="background:{dc};color:#111">{dl}</span></td>'
        f'<td style="color:#94a3b8;font-size:.85em">{was_null:,} ({was_pct}%)</td>'
        f'<td>0</td>'
        f'<td>{note}</td>'
        f'</tr>'
    )

# Preview table (first 20 rows of cleaned df)
preview_cols = df.columns.tolist()
preview_records = df.head(20).replace([np.inf, -np.inf], np.nan).where(pd.notnull(df.head(20)), None)
preview_records = preview_records.to_dict(orient='records')
preview_json = json.dumps(preview_records, ensure_ascii=False, default=str)
preview_cols_json = json.dumps(preview_cols, ensure_ascii=False)

n_kept   = len(df.columns)
n_dropped = len(drop_cols)
n_filled  = len(fill_log)

html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>בת ים — ניקוי נתונים</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0d1117; --surface:#161b22; --border:#21262d;
    --text:#c9d1d9; --muted:#8b949e; --blue:#58a6ff;
    --green:#3fb950; --yellow:#d29922; --red:#f87171;
  }}
  *{{ box-sizing:border-box; margin:0; padding:0; }}
  body{{ font-family:'Heebo',sans-serif; background:var(--bg); color:var(--text); }}
  nav{{
    background:linear-gradient(135deg,#161b22,#0d1117);
    border-bottom:1px solid var(--border);
    padding:1rem 2rem; display:flex; justify-content:space-between; align-items:center;
  }}
  nav h1{{ color:var(--blue); font-size:1.2rem; font-weight:700; }}
  .container{{ padding:1.5rem 2rem; max-width:1200px; margin:0 auto; }}
  .metrics{{
    display:grid; grid-template-columns:repeat(5,1fr);
    gap:1rem; margin-bottom:1.5rem;
  }}
  .metric-card{{
    background:var(--surface); border:1px solid var(--border);
    border-radius:12px; padding:1.2rem; text-align:center;
    position:relative; overflow:hidden;
  }}
  .metric-card::before{{
    content:''; position:absolute; top:0; right:0;
    width:4px; height:100%; background:var(--color);
  }}
  .metric-card .val{{ font-size:1.9rem; font-weight:900; color:var(--color); line-height:1; }}
  .metric-card .lbl{{ font-size:.82rem; color:var(--muted); margin-top:.4rem; font-weight:600; }}
  .section{{
    background:var(--surface); border:1px solid var(--border);
    border-radius:12px; padding:1.5rem; margin-bottom:1.5rem;
  }}
  .section-title{{
    font-size:1rem; font-weight:700; color:#fff;
    margin-bottom:1rem; border-bottom:1px solid var(--border); padding-bottom:.5rem;
    display:flex; align-items:center; gap:.6rem;
  }}
  .table-wrap{{ overflow-x:auto; max-height:420px; border-radius:8px; border:1px solid var(--border); }}
  table{{ width:100%; border-collapse:collapse; font-size:.82rem; }}
  thead th{{
    background:linear-gradient(135deg,#0ea5e9,#2563eb);
    color:#fff; padding:9px 12px; text-align:right; font-weight:600;
    white-space:nowrap; position:sticky; top:0; z-index:5;
  }}
  tbody td{{ padding:7px 12px; border-bottom:1px solid var(--border); text-align:right; white-space:nowrap; }}
  tbody tr:hover td{{ background:#1a2a3a; }}
  tbody tr:last-child td{{ border-bottom:none; }}
  code{{
    background:#0f2744; color:#93c5fd; padding:2px 7px;
    border-radius:5px; font-size:.77rem; direction:ltr; display:inline-block;
  }}
  .badge{{
    display:inline-block; padding:2px 9px; border-radius:10px;
    font-size:.76rem; font-weight:700;
  }}
  .pct-pill{{
    display:inline-block; padding:2px 10px; border-radius:20px;
    font-size:.78rem; font-weight:700; color:#111;
  }}
  .arrow{{
    display:flex; align-items:center; justify-content:center;
    font-size:2rem; color:var(--blue); margin:1rem 0;
  }}
  .cols-grid{{
    display:flex; gap:.5rem; flex-wrap:wrap; margin-top:.5rem;
  }}
  .col-chip{{
    background:#2a1515; border:1px solid #f87171; color:#f87171;
    padding:3px 10px; border-radius:20px; font-size:.78rem;
  }}
</style>
</head>
<body>

<nav>
  <h1>&#128205; בת ים &mdash; ניקוי נתונים</h1>
  <div style="color:var(--muted);font-size:.9rem">bat_yam_clean.csv</div>
</nav>

<div class="container">

  <!-- METRICS -->
  <div class="metrics">
    <div class="metric-card" style="--color:var(--blue)">
      <div class="val">{n_rows:,}</div>
      <div class="lbl">שורות (בת ים)</div>
    </div>
    <div class="metric-card" style="--color:#94a3b8">
      <div class="val">{n_cols}</div>
      <div class="lbl">עמודות לפני</div>
    </div>
    <div class="metric-card" style="--color:var(--red)">
      <div class="val">{n_dropped}</div>
      <div class="lbl">עמודות נמחקו (&gt;50%)</div>
    </div>
    <div class="metric-card" style="--color:var(--green)">
      <div class="val">{n_kept}</div>
      <div class="lbl">עמודות אחרי</div>
    </div>
    <div class="metric-card" style="--color:var(--yellow)">
      <div class="val">{n_filled}</div>
      <div class="lbl">עמודות שמולאו</div>
    </div>
  </div>

  <!-- DROPPED COLUMNS -->
  <div class="section">
    <div class="section-title">&#128683; עמודות שנמחקו (מעל 50% חסרים)</div>
    <div class="cols-grid">
      {''.join(f'<span class="col-chip">{c}</span>' for c in drop_cols) if drop_cols else '<span style="color:var(--green)">אין עמודות למחיקה</span>'}
    </div>
  </div>

  <!-- BEFORE TABLE -->
  <div class="section">
    <div class="section-title">&#128203; לפני הניקוי &mdash; כל {n_cols} העמודות</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>עמודה</th><th>סוג</th><th>חסרים (מספר)</th><th>חסרים (%)</th></tr></thead>
        <tbody>{before_rows}</tbody>
      </table>
    </div>
  </div>

  <div class="arrow">&#8595; ניקוי &#8595;</div>

  <!-- AFTER TABLE -->
  <div class="section">
    <div class="section-title">&#9989; אחרי הניקוי &mdash; {n_kept} עמודות שנשארו</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>עמודה</th><th>סוג</th><th>חסרים לפני</th><th>חסרים אחרי</th><th>אסטרטגיית מילוי</th></tr></thead>
        <tbody>{after_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- DATA PREVIEW -->
  <div class="section">
    <div class="section-title">&#128202; תצוגה מקדימה &mdash; 20 שורות ראשונות (נתונים נקיים)</div>
    <div class="table-wrap">
      <table id="previewTable">
        <thead id="previewHead"></thead>
        <tbody id="previewBody"></tbody>
      </table>
    </div>
  </div>

</div>

<script>
const COLS = {preview_cols_json};
const ROWS = {preview_json};

const thead = document.getElementById('previewHead');
const tbody = document.getElementById('previewBody');

const tr = document.createElement('tr');
COLS.forEach(c => {{ const th = document.createElement('th'); th.textContent = c; tr.appendChild(th); }});
thead.appendChild(tr);

ROWS.forEach(row => {{
  const tr = document.createElement('tr');
  COLS.forEach(col => {{
    const td = document.createElement('td');
    const v = row[col];
    td.textContent = v === null || v === undefined ? '' : v;
    tr.appendChild(td);
  }});
  tbody.appendChild(tr);
}});
</script>
</body>
</html>"""

with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML  => {OUT_HTML}")
print(f"CSV   => {OUT_CSV}")
print(f"Rows: {n_rows} | Before: {n_cols} cols | Dropped: {n_dropped} | Kept: {n_kept} | Filled: {n_filled}")
print(f"\nDropped columns: {drop_cols}")
print(f"\nFill log:")
for col, (strategy, val) in fill_log.items():
    print(f"  {col}: {strategy} = {val}")
