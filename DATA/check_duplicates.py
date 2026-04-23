import pandas as pd
import json

CLEAN_PATH  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA_clean.csv'
DEDUP_PATH  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA_final.csv'
REPORT_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\duplicates_report.html'

# ── Load ─────────────────────────────────────────────────────────────────────
df = pd.read_csv(CLEAN_PATH, encoding='utf-8-sig', low_memory=False)
total_before = len(df)
print(f"Loaded: {total_before} rows x {df.shape[1]} cols")

# ── Find duplicates ───────────────────────────────────────────────────────────
dup_mask     = df.duplicated(keep='first')         # True for every copy AFTER the first
dup_all_mask = df.duplicated(keep=False)           # True for ALL occurrences

n_dup_rows   = dup_mask.sum()                      # rows that will be removed
n_dup_groups = df[dup_all_mask].groupby(list(df.columns)).ngroups  # unique duplicate groups

print(f"Duplicate rows (to remove): {n_dup_rows}")
print(f"Unique duplicate groups:    {n_dup_groups}")

# ── Grab duplicates for display (show original + copies) ─────────────────────
dup_display = df[dup_all_mask].copy()
dup_display['__status__'] = 'COPY'
# Mark the first occurrence
first_idx = df[dup_all_mask].drop_duplicates(keep='first').index
dup_display.loc[first_idx, '__status__'] = 'ORIGINAL'
dup_display = dup_display.sort_values(list(df.columns[:4]))

# Build display table (first 8 columns only for readability)
display_cols = [c for c in df.columns[:8]]
table_rows = []
prev_vals = None
for _, row in dup_display.iterrows():
    status = row['__status__']
    cur_vals = tuple(str(row[c]) for c in display_cols)
    is_new_group = (cur_vals != prev_vals)
    prev_vals = cur_vals

    color = '#1c2128' if status == 'ORIGINAL' else '#2d1b1b'
    badge_bg = '#238636' if status == 'ORIGINAL' else '#da3633'
    badge_txt = 'ראשונה ✓' if status == 'ORIGINAL' else 'כפילות ✗'

    cells = ''.join(f'<td style="font-size:.78em">{str(row[c])[:30]}</td>' for c in display_cols)
    sep = '<tr><td colspan="10" style="height:2px;background:#21262d;padding:0"></td></tr>' if is_new_group and status == 'ORIGINAL' else ''
    table_rows.append(
        sep +
        f'<tr style="background:{color}">'
        f'<td><span style="background:{badge_bg};color:#fff;padding:1px 8px;border-radius:10px;font-size:.72em;white-space:nowrap">{badge_txt}</span></td>'
        + cells +
        '</tr>'
    )

table_html = '\n'.join(table_rows) if table_rows else '<tr><td colspan="10" style="text-align:center;color:#3fb950;padding:2rem">&#10003; אין שורות כפולות!</td></tr>'
header_cells = ''.join(f'<th>{c[:25]}</th>' for c in display_cols)

# ── De-duplicate ──────────────────────────────────────────────────────────────
df_dedup = df.drop_duplicates(keep='first').reset_index(drop=True)
total_after = len(df_dedup)
df_dedup.to_csv(DEDUP_PATH, index=False, encoding='utf-8-sig')
print(f"Saved: {DEDUP_PATH}  ({total_after} rows)")

# ── HTML Report ───────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Duplicates Report</title>
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
.before-after{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:2rem}}
.ba{{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1.2rem 1.5rem}}
.ba h3{{font-size:.85rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:1rem}}
.ba .row{{display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid #21262d;font-size:.85rem}}
.ba .row:last-child{{border-bottom:none}}
.ba .row span{{color:#58a6ff;font-weight:600}}
.section{{background:#161b22;border:1px solid #21262d;border-radius:14px;overflow:hidden}}
.section-head{{padding:1rem 1.5rem;border-bottom:1px solid #21262d;font-weight:600;display:flex;align-items:center;gap:.5rem}}
table{{width:100%;border-collapse:collapse;font-size:.82em}}
th{{background:#0d1117;color:#8b949e;padding:.65rem .8rem;text-align:right;font-weight:600;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid #21262d;font-size:.72em;white-space:nowrap}}
td{{padding:.55rem .8rem;border-bottom:1px solid #0d1117}}
.note{{color:#8b949e;font-size:.8rem;margin-top:1rem;padding:.8rem 1rem;background:#161b22;border-radius:10px;border-right:3px solid #238636}}
</style>
</head>
<body>

<h1>&#128203; Duplicates Report &mdash; DATA_clean.csv</h1>
<div class="sub">בדיקת שורות כפולות, הצגה ומחיקה</div>

<div class="cards">
  <div class="card" style="--c:#58a6ff">
    <div class="val">{total_before:,}</div>
    <div class="lbl">שורות לפני</div>
  </div>
  <div class="card" style="--c:#da3633">
    <div class="val">{n_dup_rows}</div>
    <div class="lbl">שורות כפולות (הוסרו)</div>
  </div>
  <div class="card" style="--c:#d29922">
    <div class="val">{n_dup_groups}</div>
    <div class="lbl">קבוצות כפילויות</div>
  </div>
  <div class="card" style="--c:#3fb950">
    <div class="val">{total_after:,}</div>
    <div class="lbl">שורות אחרי</div>
  </div>
</div>

<div class="before-after">
  <div class="ba">
    <h3>&#128204; לפני</h3>
    <div class="row">שורות <span>{total_before:,}</span></div>
    <div class="row">שורות כפולות <span style="color:#da3633">{n_dup_rows}</span></div>
    <div class="row">% כפילויות <span style="color:#da3633">{n_dup_rows/total_before*100:.2f}%</span></div>
  </div>
  <div class="ba">
    <h3>&#10003; אחרי</h3>
    <div class="row">שורות <span>{total_after:,}</span></div>
    <div class="row">שורות כפולות <span style="color:#3fb950">0</span></div>
    <div class="row">% כפילויות <span style="color:#3fb950">0.00%</span></div>
  </div>
</div>

<div class="section">
  <div class="section-head">
    &#128270; שורות כפולות שנמצאו ({n_dup_rows} הוסרו &mdash; מוצגות 8 עמודות ראשונות)
  </div>
  <div style="overflow-x:auto">
  <table>
    <thead><tr><th>סטטוס</th>{header_cells}</tr></thead>
    <tbody>{table_html}</tbody>
  </table>
  </div>
</div>

<div class="note">
  &#128190; קובץ סופי נשמר: <strong>DATA_final.csv</strong> &mdash;
  {total_after:,} שורות &times; {df_dedup.shape[1]} עמודות &bull; 0 כפילויות &bull; 0 חסרים
</div>

</body>
</html>"""

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n=== SUMMARY ===")
print(f"Before:  {total_before:,} rows")
print(f"Removed: {n_dup_rows} duplicate rows")
print(f"After:   {total_after:,} rows")
print(f"Report:  {REPORT_PATH}")
