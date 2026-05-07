import pandas as pd
import numpy as np
import json

CSV_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\BATYAM_2M\bat_yam_clean.csv'
OUT_HTML = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\BATYAM_2M\bat_yam_eda.html'

df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', low_memory=False)
df.columns = [c.strip() for c in df.columns]

df['dealDate_ts'] = pd.to_datetime(df['dealDate'], errors='coerce').astype('int64') // 1_000_000

rows_total, cols_total = df.shape
missing_pct = round(df.isnull().sum().sum() / (rows_total * cols_total) * 100, 2)

num_cols  = df.select_dtypes(include='number').columns.tolist()
cat_cols  = df.select_dtypes(exclude='number').columns.tolist()
all_cols  = df.columns.tolist()
hist_cols = [c for c in all_cols if c != 'dealDate_ts']

deal_natures = sorted(df['dealNatureDescription'].dropna().unique().tolist())

df_clean = df.replace([np.inf, -np.inf], np.nan).where(pd.notnull(df), None)
records  = df_clean.to_dict(orient='records')

data_json          = json.dumps(records,       ensure_ascii=False, default=str)
hist_cols_json     = json.dumps(hist_cols,     ensure_ascii=False)
num_cols_json      = json.dumps(num_cols,      ensure_ascii=False)
cat_cols_json      = json.dumps(cat_cols,      ensure_ascii=False)
deal_natures_json  = json.dumps(deal_natures,  ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>EDA — בת ים</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0d1117; --surface:#161b22; --border:#21262d;
    --text:#c9d1d9; --muted:#8b949e;
    --blue:#58a6ff; --green:#3fb950; --yellow:#d29922; --purple:#c084fc;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Heebo',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }}

  nav {{
    background:linear-gradient(135deg,#161b22,#0d1117);
    border-bottom:1px solid var(--border);
    padding:.9rem 2rem; display:flex; justify-content:space-between; align-items:center;
    position:sticky; top:0; z-index:100;
  }}
  nav h1 {{ color:var(--blue); font-size:1.15rem; font-weight:700; }}
  nav span {{ color:var(--muted); font-size:.85rem; }}

  /* ── FILTER BAR ── */
  .filter-bar {{
    background:#0f1923; border-bottom:1px solid var(--border);
    padding:.75rem 2rem; display:flex; align-items:center; gap:.75rem;
    flex-wrap:wrap; position:sticky; top:49px; z-index:99;
  }}
  .filter-label {{ font-size:.75rem; color:var(--muted); font-weight:700;
    text-transform:uppercase; letter-spacing:.06em; white-space:nowrap; }}
  .filter-pill {{
    cursor:pointer; padding:.3rem .95rem; border-radius:20px; font-size:.82rem;
    font-weight:600; border:2px solid transparent; transition:.18s;
    background:#1e293b; color:var(--muted); user-select:none;
  }}
  .filter-pill.active {{ color:#111; border-color:transparent; }}
  .filter-pill.all-pill {{ background:var(--border); color:var(--text); }}
  .filter-pill.all-pill.active {{ background:var(--blue); color:#fff; }}
  .filter-count {{
    margin-right:auto; font-size:.8rem; color:var(--muted);
    background:#1e293b; border:1px solid var(--border);
    border-radius:20px; padding:3px 12px; white-space:nowrap;
  }}
  .filter-count b {{ color:var(--blue); }}

  .container {{ padding:1.5rem 2rem; max-width:1300px; margin:0 auto; }}

  .metrics {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1.2rem; margin-bottom:1.8rem; }}
  .metric-card {{
    background:var(--surface); border:1px solid var(--border);
    border-radius:14px; padding:1.4rem 1.5rem; text-align:center;
    position:relative; overflow:hidden; transition:.2s;
  }}
  .metric-card::before {{
    content:''; position:absolute; top:0; right:0; width:4px; height:100%; background:var(--color);
  }}
  .metric-card .val {{ font-size:2.4rem; font-weight:900; color:var(--color); line-height:1; }}
  .metric-card .lbl {{ font-size:.85rem; color:var(--muted); margin-top:.5rem; font-weight:600; }}

  .section {{
    background:var(--surface); border:1px solid var(--border);
    border-radius:14px; padding:1.5rem; margin-bottom:1.5rem;
  }}
  .section-title {{
    font-size:1rem; font-weight:700; color:#fff;
    border-bottom:1px solid var(--border); padding-bottom:.6rem; margin-bottom:1.2rem;
  }}

  .controls {{ display:flex; gap:1rem; flex-wrap:wrap; align-items:flex-end; margin-bottom:1.2rem; }}
  .ctrl-group {{ display:flex; flex-direction:column; gap:.35rem; min-width:220px; flex:1; }}
  .ctrl-group label {{ font-size:.75rem; color:var(--muted); font-weight:700;
    text-transform:uppercase; letter-spacing:.06em; }}
  select {{
    background:var(--bg); color:var(--text); border:1px solid var(--border);
    padding:.55rem .9rem; border-radius:9px; font-family:inherit; font-size:.9rem;
    outline:none; transition:.2s; cursor:pointer; width:100%;
  }}
  select:focus {{ border-color:var(--blue); box-shadow:0 0 0 2px rgba(88,166,255,.15); }}
  button {{
    background:var(--blue); color:#fff; border:none;
    padding:.55rem 1.6rem; border-radius:9px; font-family:inherit;
    font-weight:700; cursor:pointer; font-size:.9rem; transition:.2s;
    white-space:nowrap; align-self:flex-end;
  }}
  button:hover {{ filter:brightness(1.12); }}

  .chart-box {{
    background:var(--bg); border:1px solid var(--border);
    border-radius:12px; padding:1.2rem;
  }}
  .chart-info {{ display:flex; gap:.8rem; flex-wrap:wrap; margin-top:.8rem; }}
  .chip {{
    background:#1e293b; border:1px solid var(--border);
    border-radius:20px; padding:3px 12px; font-size:.78rem; color:var(--muted);
  }}
  .chip b {{ color:var(--text); }}

  .divider {{ border:none; border-top:1px solid var(--border); margin:0 0 1.5rem; }}
  @media(max-width:900px){{ .metrics {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>

<nav>
  <h1>&#128202; EDA Dashboard &mdash; בת ים</h1>
  <span>bat_yam_clean.csv &nbsp;|&nbsp; {rows_total:,} שורות &nbsp;|&nbsp; {cols_total - 1} עמודות</span>
</nav>

<!-- FILTER BAR -->
<div class="filter-bar">
  <span class="filter-label">&#128279; סוג עסקה:</span>
  <span class="filter-pill all-pill active" data-val="__all__" onclick="toggleFilter(this)">הכל</span>
  <span id="naturePills"></span>
  <span class="filter-count" id="filterCount">מציג <b>{rows_total:,}</b> עסקאות</span>
</div>

<div class="container">

  <!-- METRICS -->
  <div class="metrics">
    <div class="metric-card" style="--color:var(--blue)">
      <div class="val" id="metricRows">{rows_total:,}</div>
      <div class="lbl">&#128200; שורות מסוננות</div>
    </div>
    <div class="metric-card" style="--color:var(--green)">
      <div class="val">{cols_total - 1}</div>
      <div class="lbl">&#128203; עמודות</div>
    </div>
    <div class="metric-card" style="--color:var(--yellow)">
      <div class="val">{missing_pct}%</div>
      <div class="lbl">&#10060; ערכים חסרים</div>
    </div>
  </div>

  <!-- HISTOGRAM -->
  <div class="section">
    <div class="section-title">&#128200; Histogram &mdash; התפלגות עמודה</div>
    <div class="controls">
      <div class="ctrl-group">
        <label>בחר עמודה</label>
        <select id="histCol" onchange="drawHistogram()"></select>
      </div>
      <div class="ctrl-group">
        <label>מספר סלים (bins)</label>
        <select id="histBins" onchange="drawHistogram()">
          <option value="10">10</option>
          <option value="20" selected>20</option>
          <option value="30">30</option>
          <option value="50">50</option>
        </select>
      </div>
    </div>
    <div class="chart-box">
      <canvas id="histChart" height="90"></canvas>
    </div>
    <div class="chart-info" id="histInfo"></div>
  </div>

  <hr class="divider">

  <!-- SCATTER -->
  <div class="section">
    <div class="section-title">&#127775; Scatter Plot &mdash; קשר בין שתי עמודות</div>
    <div class="controls">
      <div class="ctrl-group">
        <label>ציר X</label>
        <select id="scatX"></select>
      </div>
      <div class="ctrl-group">
        <label>ציר Y</label>
        <select id="scatY"></select>
      </div>
      <button onclick="drawScatter()">&#9654; הצג</button>
    </div>
    <div class="chart-box">
      <canvas id="scatChart" height="90"></canvas>
    </div>
    <div class="chart-info" id="scatInfo"></div>
  </div>

</div>

<script>
const DATA         = {data_json};
const HIST_COLS    = {hist_cols_json};
const NUM_COLS     = {num_cols_json};
const CAT_COLS     = {cat_cols_json};
const DEAL_NATURES = {deal_natures_json};

const DATE_COLS = new Set(['dealDate_ts']);
const COL_LABEL = {{ dealDate_ts: 'dealDate' }};
function colLabel(c) {{ return COL_LABEL[c] || c; }}

// Colour palette — one per dealNatureDescription category
const PALETTE = [
  '#58a6ff','#3fb950','#f97316','#c084fc',
  '#f43f5e','#22d3ee','#a3e635','#fb923c','#e879f9','#34d399'
];
const NATURE_COLOR = {{}};
DEAL_NATURES.forEach((n, i) => {{ NATURE_COLOR[n] = PALETTE[i % PALETTE.length]; }});

// Active filter state: empty Set = show all
let activeFilters = new Set();

let histInst = null, scatInst = null;

const C = {{
  color:'#c9d1d9', grid:'#21262d',
  blue:'#58a6ff', green:'#3fb950', purple:'#c084fc', yellow:'#d29922'
}};

/* ── filter logic ── */
function getFilteredData() {{
  if (activeFilters.size === 0) return DATA;
  return DATA.filter(r => activeFilters.has(r['dealNatureDescription']));
}}

function toggleFilter(el) {{
  const val = el.dataset.val;

  if (val === '__all__') {{
    activeFilters.clear();
    // Deactivate all nature pills, activate "all"
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
  }} else {{
    // Toggle this category
    if (activeFilters.has(val)) {{
      activeFilters.delete(val);
      el.classList.remove('active');
    }} else {{
      activeFilters.add(val);
      el.classList.add('active');
    }}
    // Sync "all" pill
    const allPill = document.querySelector('.all-pill');
    allPill.classList.toggle('active', activeFilters.size === 0);
  }}

  refreshAll();
}}

function refreshAll() {{
  const fd = getFilteredData();
  const n  = fd.length;

  // Update metric + filter bar count
  document.getElementById('metricRows').textContent = n.toLocaleString();
  document.getElementById('filterCount').innerHTML  = `מציג <b>${{n.toLocaleString()}}</b> עסקאות`;

  drawHistogram();
  drawScatter();
}}

/* ── helpers ── */
function fmtDate(ms) {{
  return new Date(ms).toLocaleDateString('he-IL', {{year:'numeric', month:'short', day:'numeric'}});
}}
function fmtDateShort(ms) {{
  return new Date(ms).toLocaleDateString('he-IL', {{year:'numeric', month:'short'}});
}}
function chip(label, value) {{
  return `<span class="chip">${{label}}: <b>${{value}}</b></span>`;
}}
function numStats(vals) {{
  const cl = vals.filter(v => v !== null && !isNaN(v)).map(Number);
  if (!cl.length) return null;
  const mean = cl.reduce((a,b)=>a+b,0)/cl.length;
  const s = [...cl].sort((a,b)=>a-b);
  const med = s.length%2 ? s[Math.floor(s.length/2)] : (s[s.length/2-1]+s[s.length/2])/2;
  const std = Math.sqrt(cl.reduce((a,b)=>a+(b-mean)**2,0)/cl.length);
  return {{ n:cl.length, mean, med, std, min:s[0], max:s[s.length-1] }};
}}
function pearson(xs, ys) {{
  const n = xs.length;
  if (n < 2) return '—';
  const mx=xs.reduce((a,b)=>a+b,0)/n, my=ys.reduce((a,b)=>a+b,0)/n;
  let num=0, dx2=0, dy2=0;
  for(let i=0;i<n;i++) {{ num+=(xs[i]-mx)*(ys[i]-my); dx2+=(xs[i]-mx)**2; dy2+=(ys[i]-my)**2; }}
  return dx2 && dy2 ? (num/Math.sqrt(dx2*dy2)).toFixed(4) : '—';
}}
function regressionLine(xs, ys) {{
  const n=xs.length, mx=xs.reduce((a,b)=>a+b,0)/n, my=ys.reduce((a,b)=>a+b,0)/n;
  let num=0, den=0;
  xs.forEach((x,i)=>{{ num+=(x-mx)*(ys[i]-my); den+=(x-mx)**2; }});
  const slope = den ? num/den : 0, inter = my - slope*mx;
  const mnX=Math.min(...xs), mxX=Math.max(...xs);
  return {{ slope, inter, line:[{{x:mnX,y:slope*mnX+inter}},{{x:mxX,y:slope*mxX+inter}}] }};
}}

/* ── populate selects ── */
function populateSelects() {{
  const histCol = document.getElementById('histCol');
  const scatX   = document.getElementById('scatX');
  const scatY   = document.getElementById('scatY');

  HIST_COLS.forEach(c => {{
    histCol.innerHTML += `<option value="${{c}}">${{c}}</option>`;
  }});
  histCol.value = HIST_COLS.includes('dealAmount') ? 'dealAmount' : (NUM_COLS.find(c=>c!=='dealDate_ts')||NUM_COLS[0]);

  NUM_COLS.forEach(c => {{
    const lbl = colLabel(c);
    scatX.innerHTML += `<option value="${{c}}">${{lbl}}</option>`;
    scatY.innerHTML += `<option value="${{c}}">${{lbl}}</option>`;
  }});
  if (NUM_COLS.includes('dealDate_ts')) scatX.value = 'dealDate_ts';
  if (NUM_COLS.includes('dealAmount'))  scatY.value = 'dealAmount';

  // Build nature pills
  const container = document.getElementById('naturePills');
  DEAL_NATURES.forEach(n => {{
    const pill = document.createElement('span');
    pill.className   = 'filter-pill';
    pill.dataset.val = n;
    pill.textContent = n;
    pill.style.setProperty('--pill-color', NATURE_COLOR[n]);
    pill.onclick = () => toggleFilter(pill);
    container.appendChild(pill);
  }});

  // Style active pills with their category colour
  document.querySelectorAll('.filter-pill:not(.all-pill)').forEach(p => {{
    p.addEventListener('mouseenter', () => {{
      if (!p.classList.contains('active'))
        p.style.borderColor = NATURE_COLOR[p.dataset.val];
    }});
    p.addEventListener('mouseleave', () => {{
      if (!p.classList.contains('active'))
        p.style.borderColor = 'transparent';
    }});
  }});
}}

// Apply active colour to a pill when it becomes active
function stylePills() {{
  document.querySelectorAll('.filter-pill:not(.all-pill)').forEach(p => {{
    if (p.classList.contains('active')) {{
      p.style.background   = NATURE_COLOR[p.dataset.val];
      p.style.borderColor  = 'transparent';
    }} else {{
      p.style.background  = '';
      p.style.borderColor = 'transparent';
    }}
  }});
}}

/* ── histogram ── */
function drawHistogram() {{
  stylePills();
  const fd   = getFilteredData();
  const col  = document.getElementById('histCol').value;
  const bins = parseInt(document.getElementById('histBins').value);
  const isNum = NUM_COLS.includes(col);
  let labels, color;

  // When filtered to multiple natures: stack bars per category
  // When single nature / all same: single colour bar
  const naturesInData = [...new Set(fd.map(r => r['dealNatureDescription']))].filter(Boolean);
  const useStacked = naturesInData.length > 1;

  if (isNum) {{
    const allVals = fd.map(r=>r[col]).filter(v=>v!==null&&!isNaN(v)).map(Number);
    if (!allVals.length) return;
    const mn=Math.min(...allVals), mx=Math.max(...allVals);
    const step=(mx-mn)/bins||1;
    labels = Array.from({{length:bins}},(_,i)=>(mn+i*step).toFixed(1));

    let datasets;
    if (useStacked) {{
      datasets = naturesInData.map(nat => {{
        const vals = fd.filter(r=>r['dealNatureDescription']===nat).map(r=>r[col]).filter(v=>v!==null&&!isNaN(v)).map(Number);
        const counts = new Array(bins).fill(0);
        vals.forEach(v=>{{ let i=Math.floor((v-mn)/step); if(i>=bins)i=bins-1; counts[i]++; }});
        return {{ label:nat, data:counts,
          backgroundColor:NATURE_COLOR[nat]+'99', borderColor:NATURE_COLOR[nat], borderWidth:1, borderRadius:2 }};
      }});
    }} else {{
      const counts = new Array(bins).fill(0);
      allVals.forEach(v=>{{ let i=Math.floor((v-mn)/step); if(i>=bins)i=bins-1; counts[i]++; }});
      const singleColor = naturesInData.length===1 ? NATURE_COLOR[naturesInData[0]] : C.blue;
      datasets = [{{ label:col, data:counts,
        backgroundColor:singleColor+'bb', borderColor:singleColor, borderWidth:1, borderRadius:3 }}];
    }}

    const st = numStats(allVals);
    document.getElementById('histInfo').innerHTML =
      chip('n', st.n.toLocaleString()) +
      chip('ממוצע', Math.round(st.mean).toLocaleString()) +
      chip('חציון', Math.round(st.med).toLocaleString()) +
      chip('סטד', Math.round(st.std).toLocaleString()) +
      chip('מינ׳', Math.round(st.min).toLocaleString()) +
      chip('מקס׳', Math.round(st.max).toLocaleString());

    if (histInst) histInst.destroy();
    histInst = new Chart(document.getElementById('histChart').getContext('2d'), {{
      type:'bar',
      data:{{ labels, datasets }},
      options:{{
        responsive:true, animation:{{duration:200}},
        plugins:{{
          legend:{{ display:useStacked, labels:{{color:C.color, boxWidth:12}} }},
          tooltip:{{ callbacks:{{ title:c=>`[${{c[0].label}}…]`, label:c=>` ${{c.dataset.label}}: ${{c.parsed.y}}` }} }}
        }},
        scales:{{
          x:{{ stacked:useStacked, ticks:{{color:C.color,maxRotation:45,font:{{size:11}}}}, grid:{{color:C.grid}} }},
          y:{{ stacked:useStacked, ticks:{{color:C.color}}, grid:{{color:C.grid}} }}
        }}
      }}
    }});

  }} else {{
    // Categorical
    const freq={{}};
    fd.forEach(r=>{{ const v=r[col]??'(חסר)'; freq[v]=(freq[v]||0)+1; }});
    const sorted=Object.entries(freq).sort((a,b)=>b[1]-a[1]).slice(0,30);
    labels=sorted.map(e=>String(e[0]));
    const counts=sorted.map(e=>e[1]);
    const bgColors = labels.map(l => (NATURE_COLOR[l] || C.green) + 'bb');
    const bdColors = labels.map(l =>  NATURE_COLOR[l] || C.green);

    document.getElementById('histInfo').innerHTML =
      chip('ייחודיים', Object.keys(freq).length) +
      chip('שכיח', labels[0]) + chip('כמות', counts[0]);

    if (histInst) histInst.destroy();
    histInst = new Chart(document.getElementById('histChart').getContext('2d'), {{
      type:'bar',
      data:{{ labels, datasets:[{{ label:col, data:counts,
        backgroundColor:bgColors, borderColor:bdColors, borderWidth:1, borderRadius:3 }}] }},
      options:{{
        responsive:true, animation:{{duration:200}},
        plugins:{{ legend:{{display:false}},
          tooltip:{{ callbacks:{{ title:c=>c[0].label, label:c=>` ${{c.parsed.y}} רשומות` }} }} }},
        scales:{{
          x:{{ ticks:{{color:C.color,maxRotation:45,font:{{size:11}}}}, grid:{{color:C.grid}} }},
          y:{{ ticks:{{color:C.color}}, grid:{{color:C.grid}} }}
        }}
      }}
    }});
  }}
}}

/* ── scatter ── */
function drawScatter() {{
  const fd   = getFilteredData();
  const xCol = document.getElementById('scatX').value;
  const yCol = document.getElementById('scatY').value;
  const xIsDate = DATE_COLS.has(xCol);
  const yIsDate = DATE_COLS.has(yCol);

  const naturesInData = [...new Set(fd.map(r => r['dealNatureDescription']))].filter(Boolean).sort();
  const useColored    = naturesInData.length > 1;

  // Build per-category point datasets
  let datasets;
  let allXs = [], allYs = [];

  if (useColored) {{
    datasets = naturesInData.map(nat => {{
      const pts = fd
        .filter(r => r['dealNatureDescription'] === nat)
        .map(r => ({{ x: Number(r[xCol]), y: Number(r[yCol]) }}))
        .filter(p => !isNaN(p.x) && !isNaN(p.y));
      pts.forEach(p => {{ allXs.push(p.x); allYs.push(p.y); }});
      return {{
        label: nat, data: pts,
        backgroundColor: NATURE_COLOR[nat] + '88',
        borderColor:     NATURE_COLOR[nat],
        borderWidth: 0, pointRadius: 3.5, pointHoverRadius: 7
      }};
    }});
  }} else {{
    const pts = fd
      .map(r => ({{ x: Number(r[xCol]), y: Number(r[yCol]) }}))
      .filter(p => !isNaN(p.x) && !isNaN(p.y));
    pts.forEach(p => {{ allXs.push(p.x); allYs.push(p.y); }});
    const singleColor = naturesInData.length===1 ? NATURE_COLOR[naturesInData[0]] : C.purple;
    datasets = [{{
      label: naturesInData[0] || `${{colLabel(xCol)}} vs ${{colLabel(yCol)}}`,
      data: pts,
      backgroundColor: singleColor + '77', borderColor: singleColor,
      borderWidth: 0, pointRadius: 3, pointHoverRadius: 6
    }}];
  }}

  if (!allXs.length) return;

  // Regression line over all filtered data
  const r = pearson(allXs, allYs);
  const reg = regressionLine(allXs, allYs);
  datasets.push({{
    label: 'קו מגמה', data: reg.line, type: 'line',
    borderColor: C.yellow, borderWidth: 2, pointRadius: 0, tension: 0,
    order: -1
  }});

  if (scatInst) scatInst.destroy();
  scatInst = new Chart(document.getElementById('scatChart').getContext('2d'), {{
    type: 'scatter',
    data: {{ datasets }},
    options: {{
      responsive: true, animation: {{duration:200}},
      plugins: {{
        legend: {{ display: useColored, labels: {{color:C.color, boxWidth:12, padding:12}} }},
        tooltip: {{
          callbacks: {{
            label: ctx => {{
              if (ctx.dataset.label === 'קו מגמה') return null;
              const xStr = xIsDate ? fmtDate(ctx.parsed.x) : ctx.parsed.x.toLocaleString();
              const yStr = yIsDate ? fmtDate(ctx.parsed.y) : ctx.parsed.y.toLocaleString();
              return ` ${{ctx.dataset.label}}  |  ${{colLabel(xCol)}}: ${{xStr}}  ·  ${{colLabel(yCol)}}: ${{yStr}}`;
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          title: {{ display:true, text:colLabel(xCol), color:C.color }},
          ticks: {{ color:C.color, callback: val => xIsDate ? fmtDateShort(val) : val.toLocaleString() }},
          grid:  {{ color:C.grid }}
        }},
        y: {{
          title: {{ display:true, text:colLabel(yCol), color:C.color }},
          ticks: {{ color:C.color, callback: val => yIsDate ? fmtDateShort(val) : val.toLocaleString() }},
          grid:  {{ color:C.grid }}
        }}
      }}
    }}
  }});

  const rColor = isNaN(Number(r)) ? C.color : Math.abs(r)>0.7 ? C.green : Math.abs(r)>0.4 ? C.yellow : C.color;
  document.getElementById('scatInfo').innerHTML =
    chip('נקודות', allXs.length.toLocaleString()) +
    `<span class="chip">מתאם Pearson (r): <b style="color:${{rColor}}">${{r}}</b></span>` +
    (xIsDate ? '' : chip('שיפוע', reg.slope.toExponential(3)));
}}

/* ── init ── */
populateSelects();
drawHistogram();
drawScatter();
</script>
</body>
</html>"""

with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated: {OUT_HTML}")
print(f"Rows: {rows_total:,}  |  Columns: {cols_total-1}  |  Deal natures: {deal_natures}")
