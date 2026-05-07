import pandas as pd
import json
import numpy as np

CSV_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\nadlan_final.csv'
OUT_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\nadlan_preview.html'

df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', low_memory=False)
df.columns = [c.strip() for c in df.columns]

rows_total, cols_total = df.shape
missing_pct = round(df.isnull().sum().sum() / (rows_total * cols_total) * 100, 2)

# Column info
dtype_color = {
    'int64':   ('#4ade80', 'int64 (מספר שלם)'),
    'float64': ('#60a5fa', 'float64 (מספר עשרוני)'),
    'object':  ('#f59e0b', 'object (טקסט)'),
    'bool':    ('#c084fc', 'bool'),
    'datetime64[ns]': ('#f87171', 'datetime'),
}

col_info = []
for col in df.columns:
    dtype_str = str(df[col].dtype)
    color, label = dtype_color.get(dtype_str, ('#94a3b8', dtype_str))
    null_count = int(df[col].isnull().sum())
    null_pct = round(null_count / rows_total * 100, 1)
    sample = df[col].dropna().iloc[0] if df[col].dropna().shape[0] > 0 else ''
    col_info.append((col, label, color, null_count, null_pct, str(sample)[:40]))

# First 500 rows for the table
preview = df.head(500).replace([np.inf, -np.inf], np.nan).where(pd.notnull(df.head(500)), None)
records = preview.to_dict(orient='records')
columns = df.columns.tolist()

records_json = json.dumps(records, ensure_ascii=False, default=str)
columns_json = json.dumps(columns, ensure_ascii=False)

# Build dtype rows HTML
dtype_rows_html = ''
for col, label, color, null_count, null_pct, sample in col_info:
    dtype_rows_html += (
        f'<tr>'
        f'<td><code>{col}</code></td>'
        f'<td><span class="badge" style="background:{color};color:#111">{label}</span></td>'
        f'<td>{null_count:,} ({null_pct}%)</td>'
        f'<td style="color:#94a3b8;font-size:.8em">{sample}</td>'
        f'</tr>'
    )

html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>nadlan_final.csv — תצוגה מקדימה</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --border: #21262d;
    --text: #c9d1d9; --muted: #8b949e; --blue: #58a6ff;
    --green: #3fb950; --yellow: #d29922;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Heebo', sans-serif; background: var(--bg); color: var(--text); }}

  nav {{
    background: linear-gradient(135deg, #161b22, #0d1117);
    border-bottom: 1px solid var(--border);
    padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;
  }}
  nav h1 {{ color: var(--blue); font-size: 1.2rem; font-weight: 700; }}

  .container {{ padding: 1.5rem 2rem; max-width: 100%; }}

  .metrics {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-bottom: 1.5rem;
  }}
  .metric-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.2rem; text-align: center;
    position: relative; overflow: hidden;
  }}
  .metric-card::before {{
    content: ''; position: absolute; top: 0; right: 0;
    width: 4px; height: 100%; background: var(--color);
  }}
  .metric-card .val {{ font-size: 2rem; font-weight: 900; color: var(--color); line-height: 1; }}
  .metric-card .lbl {{ font-size: .85rem; color: var(--muted); margin-top: .4rem; font-weight: 600; }}

  .section {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
  }}
  .section-title {{
    font-size: 1rem; font-weight: 700; color: #fff;
    margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: .5rem;
  }}

  /* Search bar */
  .search-bar {{
    display: flex; gap: .8rem; margin-bottom: 1rem; align-items: center;
  }}
  .search-bar input {{
    background: var(--bg); color: var(--text); border: 1px solid var(--border);
    padding: .5rem 1rem; border-radius: 8px; font-family: inherit;
    font-size: .9rem; width: 300px; outline: none; transition: .2s;
  }}
  .search-bar input:focus {{ border-color: var(--blue); }}
  .search-bar span {{ color: var(--muted); font-size: .85rem; }}

  /* Data Table */
  .table-wrap {{ overflow-x: auto; max-height: 65vh; border-radius: 10px; border: 1px solid var(--border); }}
  table {{ width: 100%; border-collapse: collapse; font-size: .8rem; }}
  thead th {{
    background: linear-gradient(135deg, #0ea5e9, #2563eb);
    color: #fff; padding: 10px 12px; text-align: right;
    font-weight: 600; white-space: nowrap;
    position: sticky; top: 0; z-index: 10;
    cursor: pointer; user-select: none;
  }}
  thead th:hover {{ filter: brightness(1.15); }}
  thead th .sort-icon {{ margin-right: 4px; font-size: .7em; opacity: .7; }}
  tbody td {{
    padding: 7px 12px; border-bottom: 1px solid var(--border);
    text-align: right; white-space: nowrap; max-width: 200px;
    overflow: hidden; text-overflow: ellipsis;
  }}
  tbody tr:hover td {{ background: #1a2a3a; }}
  tbody tr:last-child td {{ border-bottom: none; }}

  /* Dtype Table */
  .dtype-table table {{ font-size: .85rem; }}
  .dtype-table th {{
    background: #1e293b; color: #94a3b8; padding: 9px 12px;
    text-align: right; font-weight: 600; text-transform: uppercase;
    font-size: .75rem; letter-spacing: .05em; position: sticky; top: 0;
  }}
  .dtype-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: right; }}
  .dtype-table tr:last-child td {{ border-bottom: none; }}
  code {{
    background: #0f2744; color: #93c5fd; padding: 2px 7px;
    border-radius: 5px; font-size: .78rem; direction: ltr; display: inline-block;
  }}
  .badge {{
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-size: .78rem; font-weight: 700;
  }}

  @media (max-width: 900px) {{ .metrics {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
</head>
<body>

<nav>
  <h1>&#128202; nadlan_final.csv &mdash; תצוגה מקדימה</h1>
  <div style="color:var(--muted);font-size:.9rem">נדל&quot;ן &mdash; ישראל</div>
</nav>

<div class="container">

  <!-- METRICS -->
  <div class="metrics">
    <div class="metric-card" style="--color:var(--blue)">
      <div class="val">{rows_total:,}</div>
      <div class="lbl">סה&quot;כ שורות</div>
    </div>
    <div class="metric-card" style="--color:var(--green)">
      <div class="val">{cols_total}</div>
      <div class="lbl">עמודות</div>
    </div>
    <div class="metric-card" style="--color:var(--yellow)">
      <div class="val">{missing_pct}%</div>
      <div class="lbl">ערכים חסרים</div>
    </div>
    <div class="metric-card" style="--color:#f87171">
      <div class="val">500</div>
      <div class="lbl">שורות מוצגות</div>
    </div>
  </div>

  <!-- DATA TABLE -->
  <div class="section">
    <div class="section-title">&#128203; 500 השורות הראשונות</div>
    <div class="search-bar">
      <input type="text" id="searchInput" placeholder="&#128269; חיפוש חופשי בטבלה..." oninput="filterTable()">
      <span id="rowCount">מציג <b>500</b> שורות</span>
    </div>
    <div class="table-wrap">
      <table id="dataTable">
        <thead id="tableHead"></thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>

  <!-- COLUMN TYPES -->
  <div class="section dtype-table">
    <div class="section-title">&#128196; סוגי עמודות ונתונים חסרים</div>
    <div class="table-wrap" style="max-height:none">
      <table>
        <thead>
          <tr>
            <th>שם עמודה</th>
            <th>סוג נתון</th>
            <th>ערכים חסרים</th>
            <th>דוגמה</th>
          </tr>
        </thead>
        <tbody>{dtype_rows_html}</tbody>
      </table>
    </div>
  </div>

</div>

<script>
const COLUMNS = {columns_json};
const RECORDS = {records_json};

let allRows = RECORDS;
let filteredRows = [...allRows];
let sortCol = null;
let sortAsc = true;

// Build header
function buildHeader() {{
  const tr = document.createElement('tr');
  COLUMNS.forEach((col, i) => {{
    const th = document.createElement('th');
    th.innerHTML = `<span class="sort-icon">&#8597;</span>${{col}}`;
    th.title = col;
    th.onclick = () => sortBy(i, col);
    tr.appendChild(th);
  }});
  document.getElementById('tableHead').appendChild(tr);
}}

// Render rows
function renderRows(rows) {{
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';
  rows.forEach(row => {{
    const tr = document.createElement('tr');
    COLUMNS.forEach(col => {{
      const td = document.createElement('td');
      const val = row[col];
      td.textContent = val === null || val === undefined ? '' : val;
      td.title = val === null || val === undefined ? '' : String(val);
      tr.appendChild(td);
    }});
    tbody.appendChild(tr);
  }});
  document.getElementById('rowCount').innerHTML = `מציג <b>${{rows.length}}</b> שורות`;
}}

// Filter
function filterTable() {{
  const q = document.getElementById('searchInput').value.toLowerCase();
  if (!q) {{
    filteredRows = [...allRows];
  }} else {{
    filteredRows = allRows.filter(row =>
      COLUMNS.some(col => {{
        const v = row[col];
        return v !== null && v !== undefined && String(v).toLowerCase().includes(q);
      }})
    );
  }}
  renderRows(filteredRows);
}}

// Sort
function sortBy(idx, col) {{
  if (sortCol === col) {{
    sortAsc = !sortAsc;
  }} else {{
    sortCol = col;
    sortAsc = true;
  }}
  filteredRows.sort((a, b) => {{
    const va = a[col], vb = b[col];
    if (va === null || va === undefined) return 1;
    if (vb === null || vb === undefined) return -1;
    const na = Number(va), nb = Number(vb);
    if (!isNaN(na) && !isNaN(nb)) return sortAsc ? na - nb : nb - na;
    return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
  }});

  // Update sort icons
  document.querySelectorAll('thead th .sort-icon').forEach((el, i) => {{
    el.innerHTML = i === idx ? (sortAsc ? '&#8593;' : '&#8595;') : '&#8597;';
  }});

  renderRows(filteredRows);
}}

buildHeader();
renderRows(allRows);
</script>
</body>
</html>"""

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated: {OUT_PATH}")
print(f"Rows: {rows_total:,}  |  Columns: {cols_total}  |  Missing: {missing_pct}%")
