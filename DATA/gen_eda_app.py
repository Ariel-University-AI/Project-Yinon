import pandas as pd
import json

FINAL_PATH  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA_final.csv'
OUT_PATH    = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\eda_app.html'

df = pd.read_csv(FINAL_PATH, encoding='utf-8-sig', low_memory=False)
rows, cols_n = df.shape
pct_missing  = round(df.isnull().sum().sum() / (rows * cols_n) * 100, 2)

# Identify numeric columns
num_cols = df.select_dtypes(include='number').columns.tolist()

# Build column→values dict (only numeric, downsample to 500 pts max)
import random
random.seed(42)
col_data = {}
for c in num_cols:
    vals = df[c].dropna().tolist()
    if len(vals) > 500:
        vals = random.sample(vals, 500)
    col_data[c] = vals

# Also build paired data for scatter (x,y) – store all numeric cols raw (sampled)
scatter_data = {}
idx_sample = random.sample(range(rows), min(400, rows))
for c in num_cols:
    scatter_data[c] = [df[c].iloc[i] if not pd.isna(df[c].iloc[i]) else None for i in idx_sample]

col_data_js    = json.dumps(col_data,    ensure_ascii=False)
scatter_data_js= json.dumps(scatter_data, ensure_ascii=False)
num_cols_js    = json.dumps(num_cols,    ensure_ascii=False)

html_lines = []
html_lines.append('<!DOCTYPE html>')
html_lines.append('<html lang="he" dir="rtl">')
html_lines.append('<head>')
html_lines.append('<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
html_lines.append('<title>EDA Dashboard</title>')
html_lines.append('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>')
html_lines.append('<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">')
html_lines.append('''<style>
:root{--bg:#0d1117;--surface:#161b22;--border:#21262d;--text:#c9d1d9;--muted:#8b949e;--blue:#58a6ff;--green:#3fb950;--yellow:#d29922;--red:#f85149;--purple:#a371f7}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Heebo',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}

/* NAV */
nav{background:linear-gradient(135deg,#161b22,#0d1117);border-bottom:1px solid var(--border);padding:.9rem 2rem;display:flex;align-items:center;justify-content:space-between}
nav .brand{display:flex;align-items:center;gap:.7rem}
nav .brand .icon{font-size:1.4rem}
nav .brand h1{font-size:1.1rem;color:var(--blue);font-weight:700}
nav .badge{background:#1f2937;border:1px solid var(--border);border-radius:20px;padding:.3rem 1rem;font-size:.78rem;color:var(--muted)}
nav .badge span{color:var(--green);font-weight:700}

/* LAYOUT */
.container{padding:1.5rem 2rem;max-width:1400px;margin:0 auto}

/* METRICS */
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2rem;margin-bottom:2rem}
.metric{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:1.4rem 1.6rem;position:relative;overflow:hidden;cursor:default;transition:.2s}
.metric:hover{border-color:var(--blue);transform:translateY(-2px)}
.metric::after{content:'';position:absolute;top:0;right:0;width:4px;height:100%;background:var(--accent);border-radius:0 16px 16px 0}
.metric .icon{font-size:1.6rem;margin-bottom:.5rem}
.metric .val{font-size:2.4rem;font-weight:900;color:var(--accent);line-height:1;letter-spacing:-1px}
.metric .lbl{font-size:.82rem;color:var(--muted);margin-top:.4rem;font-weight:600}
.metric .sub{font-size:.75rem;color:var(--muted);margin-top:.2rem;opacity:.7}

/* SECTION */
.section{background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden;margin-bottom:1.5rem}
.section-head{padding:1rem 1.5rem;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap}
.section-head h2{font-size:.95rem;font-weight:700;display:flex;align-items:center;gap:.5rem}
.section-body{padding:1.5rem}

/* CONTROLS */
.ctrl-row{display:flex;gap:1rem;flex-wrap:wrap;align-items:flex-end}
.ctrl-group{display:flex;flex-direction:column;gap:.4rem;min-width:220px;flex:1}
label{font-size:.73rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.06em}
select{background:#0d1117;border:1px solid #30363d;color:var(--text);border-radius:10px;padding:.5rem 1rem;font-family:inherit;font-size:.88rem;cursor:pointer;outline:none;width:100%;transition:.2s}
select:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(88,166,255,.15)}
button{background:linear-gradient(135deg,#1f6feb,#388bfd);color:#fff;border:none;border-radius:10px;padding:.55rem 1.6rem;font-size:.88rem;font-family:inherit;cursor:pointer;font-weight:700;transition:.2s;white-space:nowrap}
button:hover{filter:brightness(1.15);transform:translateY(-1px)}

/* CHART GRID */
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem}
.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:1.3rem 1.5rem}
.chart-card h3{font-size:.88rem;font-weight:700;color:var(--text);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem}
.chart-card h3 small{font-size:.75rem;color:var(--muted);font-weight:400;margin-right:.3rem}
canvas{width:100%!important}

/* STATS BAR */
.stats-bar{display:flex;gap:1.5rem;flex-wrap:wrap;font-size:.8rem;color:var(--muted);margin-bottom:1rem}
.stats-bar b{color:var(--blue)}

@media(max-width:700px){.chart-grid,.metrics{grid-template-columns:1fr}}
</style>''')
html_lines.append('</head>')
html_lines.append('<body>')

# NAV
html_lines.append('<nav>')
html_lines.append('<div class="brand"><span class="icon">&#128202;</span><h1>EDA Dashboard &mdash; מדד חברתי-כלכלי</h1></div>')
html_lines.append(f'<div class="badge">DATA_final.csv &bull; <span>{rows:,}</span> רשומות</div>')
html_lines.append('</nav>')

html_lines.append('<div class="container">')

# METRICS
html_lines.append('<div class="metrics">')
html_lines.append(f'<div class="metric" style="--accent:var(--blue)"><div class="icon">&#128205;</div><div class="val">{rows:,}</div><div class="lbl">שורות</div><div class="sub">רשומות אחרי ניקוי</div></div>')
html_lines.append(f'<div class="metric" style="--accent:var(--green)"><div class="icon">&#128205;</div><div class="val">{cols_n}</div><div class="lbl">עמודות</div><div class="sub">לאחר הסרת עמודות ריקות</div></div>')
html_lines.append(f'<div class="metric" style="--accent:var(--yellow)"><div class="icon">&#128165;</div><div class="val">{pct_missing}%</div><div class="lbl">ערכים חסרים</div><div class="sub">מסה"כ התאים לאחר ניקוי</div></div>')
html_lines.append('</div>')

# HISTOGRAM section
html_lines.append('<div class="section">')
html_lines.append('<div class="section-head"><h2>&#128200; Histogram &mdash; התפלגות עמודה</h2></div>')
html_lines.append('<div class="section-body">')
html_lines.append('<div class="ctrl-row" style="margin-bottom:1rem">')
html_lines.append('<div class="ctrl-group"><label>&#128270; בחר עמודה מספרית</label><select id="histCol"></select></div>')
html_lines.append('<div class="ctrl-group"><label>&#8680; מספר סלים (Bins)</label><select id="histBins"><option value="10">10</option><option value="15">15</option><option value="20" selected>20</option><option value="30">30</option><option value="50">50</option></select></div>')
html_lines.append('<button onclick="drawHist()">&#128260; עדכן</button>')
html_lines.append('</div>')
html_lines.append('<div class="stats-bar" id="histStats"></div>')
html_lines.append('<canvas id="histChart" height="200"></canvas>')
html_lines.append('</div></div>')

# SCATTER section
html_lines.append('<div class="section">')
html_lines.append('<div class="section-head"><h2>&#9899; Scatter Plot &mdash; קורלציה בין שתי עמודות</h2></div>')
html_lines.append('<div class="section-body">')
html_lines.append('<div class="ctrl-row" style="margin-bottom:1rem">')
html_lines.append('<div class="ctrl-group"><label>&#8660; ציר X</label><select id="scatX"></select></div>')
html_lines.append('<div class="ctrl-group"><label>&#8661; ציר Y</label><select id="scatY"></select></div>')
html_lines.append('<button onclick="drawScatter()">&#128260; עדכן</button>')
html_lines.append('</div>')
html_lines.append('<div class="stats-bar" id="scatStats"></div>')
html_lines.append('<canvas id="scatChart" height="240"></canvas>')
html_lines.append('</div></div>')

html_lines.append('</div>') # container

# SCRIPT
html_lines.append('<script>')
html_lines.append('const COL_DATA    = ' + col_data_js    + ';')
html_lines.append('const SCAT_DATA   = ' + scatter_data_js + ';')
html_lines.append('const NUM_COLS    = ' + num_cols_js    + ';')
html_lines.append(f'const TOTAL_ROWS  = {rows};')
html_lines.append(f'const TOTAL_COLS  = {cols_n};')

html_lines.append('''
// ── Populate selects ──────────────────────────────────────────────────────────
const histColEl = document.getElementById('histCol');
const scatXEl   = document.getElementById('scatX');
const scatYEl   = document.getElementById('scatY');

NUM_COLS.forEach((c,i) => {
  histColEl.innerHTML += `<option value="${c}">${c}</option>`;
  scatXEl.innerHTML   += `<option value="${c}" ${i===0?'selected':''}>${c}</option>`;
  scatYEl.innerHTML   += `<option value="${c}" ${i===1?'selected':''}>${c}</option>`;
});

// ── Math helpers ──────────────────────────────────────────────────────────────
const mean   = a => a.reduce((s,v)=>s+v,0)/a.length;
const stdev  = a => {const m=mean(a); return Math.sqrt(mean(a.map(v=>(v-m)**2)));}
const median = a => {const s=[...a].sort((x,y)=>x-y); const m=Math.floor(s.length/2); return s.length%2?s[m]:(s[m-1]+s[m])/2;}
const corr   = (x,y) => {
  const mx=mean(x),my=mean(y),sx=stdev(x),sy=stdev(y);
  return mean(x.map((v,i)=>((v-mx)/sx)*((y[i]-my)/sy)));
};

// ── Histogram builder ─────────────────────────────────────────────────────────
let HC = null;
function drawHist() {
  const col  = histColEl.value;
  const bins = +document.getElementById('histBins').value;
  const vals = (COL_DATA[col]||[]).filter(v=>v!=null);
  if (!vals.length) return;

  const mn=Math.min(...vals), mx=Math.max(...vals), w=(mx-mn)/bins||1;
  const counts=Array(bins).fill(0);
  const labels=[];
  for(let i=0;i<bins;i++) labels.push((mn+i*w).toFixed(2));
  vals.forEach(v=>{ let idx=Math.min(bins-1,Math.floor((v-mn)/w)); counts[idx]++; });

  // Stats bar
  const m=mean(vals), sd=stdev(vals), med=median(vals);
  document.getElementById('histStats').innerHTML =
    `<span>n=<b>${vals.length.toLocaleString()}</b></span>` +
    `<span>&#x2205; ממוצע: <b>${m.toFixed(3)}</b></span>` +
    `<span>&#963; סטיית תקן: <b>${sd.toFixed(3)}</b></span>` +
    `<span>&#771; חציון: <b>${med.toFixed(3)}</b></span>` +
    `<span>Min: <b>${mn.toFixed(3)}</b></span>` +
    `<span>Max: <b>${mx.toFixed(3)}</b></span>`;

  if (HC) HC.destroy();
  HC = new Chart(document.getElementById('histChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: col,
        data: counts,
        backgroundColor: 'rgba(88,166,255,.6)',
        borderColor: '#58a6ff',
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { title: t => 'מ '+t[0].label, label: t => 'תדירות: '+t.raw } }
      },
      scales: {
        x: { ticks:{color:'#8b949e',maxRotation:45,font:{size:9}}, grid:{color:'#21262d'} },
        y: { ticks:{color:'#8b949e'}, grid:{color:'#21262d'}, title:{display:true,text:'תדירות',color:'#8b949e'} }
      }
    }
  });
}

// ── Scatter builder ───────────────────────────────────────────────────────────
let SC = null;
function drawScatter() {
  const cx = scatXEl.value, cy = scatYEl.value;
  const xArr = SCAT_DATA[cx]||[], yArr = SCAT_DATA[cy]||[];
  const pts = [];
  const xClean=[], yClean=[];
  for (let i=0;i<xArr.length;i++) {
    if (xArr[i]!=null && yArr[i]!=null) {
      pts.push({x:xArr[i], y:yArr[i]});
      xClean.push(xArr[i]); yClean.push(yArr[i]);
    }
  }
  if (!pts.length) return;

  const r = corr(xClean, yClean);
  document.getElementById('scatStats').innerHTML =
    `<span>n=<b>${pts.length.toLocaleString()}</b></span>` +
    `<span>Pearson r: <b style="color:${Math.abs(r)>.5?'#3fb950':Math.abs(r)>.3?'#d29922':'#f85149'}">${r.toFixed(4)}</b></span>` +
    `<span>עוצמת קורלציה: <b>${Math.abs(r)>.7?'חזקה':Math.abs(r)>.4?'בינונית':'חלשה'}</b></span>` +
    `<span>כיוון: <b>${r>0?'חיובי':'שלילי'}</b></span>`;

  if (SC) SC.destroy();
  SC = new Chart(document.getElementById('scatChart'), {
    type: 'scatter',
    data: {
      datasets: [{
        label: cx+' vs '+cy,
        data: pts,
        backgroundColor: 'rgba(163,113,247,.55)',
        borderColor: 'rgba(163,113,247,.8)',
        borderWidth: 1,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: t => `(${t.parsed.x.toFixed(2)}, ${t.parsed.y.toFixed(2)})` } }
      },
      scales: {
        x: { ticks:{color:'#8b949e',font:{size:9}}, grid:{color:'#21262d'}, title:{display:true,text:cx,color:'#8b949e'} },
        y: { ticks:{color:'#8b949e'}, grid:{color:'#21262d'}, title:{display:true,text:cy,color:'#8b949e'} }
      }
    }
  });
}

// Init
drawHist();
drawScatter();
''')
html_lines.append('</script>')
html_lines.append('</body></html>')

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(html_lines))

print(f'Done! {rows} rows x {cols_n} cols | {pct_missing}% missing')
print(f'Saved: {OUT_PATH}')
