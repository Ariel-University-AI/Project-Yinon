import csv, json

CSV_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA.csv'
OUT_PATH  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\eda.html'

with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    raw = list(csv.reader(f))

numeric_cols = {
    'index_value':           'ערך מדד חברתי-כלכלי',
    'rank':                  'דירוג (1-1635)',
    'cluster':               'אשכול (1-10)',
    'median_age_val':        'חציון גיל',
    'dep_ratio_val':         'יחס תלות',
    'families4plus_val':     '% משפחות 4+ ילדים',
    'avg_schooling_val':     'ממוצע שנות לימוד',
    'academic_pct_val':      '% בעלי תואר אקדמי',
    'employed_pct_val':      '% בעלי הכנסה מעבודה',
    'above2x_wage_pct_val':  '% מעל פעמיים השכר הממוצע',
    'below_min_wage_pct_val':'% מתחת לשכר מינימום',
    'avg_monthly_income_val':'הכנסה חודשית ממוצעת לנפש',
    'vehicles_per100_val':   'כלי רכב ל-100 תושבים',
    'avg_days_abroad_val':   'ממוצע ימי שהות בחול',
}

records = []
for row in raw[9:]:
    if len(row) < 21:
        continue
    def get(i, r=row):
        v = r[i].strip().replace(',','').replace('"','')
        try: return float(v)
        except: return None
    rec = {
        'code_locality':         get(0),
        'locality_name':         row[1].strip(),
        'stat_area':             row[2].strip(),
        'population':            get(3),
        'index_value':           get(4),
        'rank':                  get(5),
        'cluster':               get(6),
        'median_age_val':        get(7),
        'dep_ratio_val':         get(10),
        'families4plus_val':     get(13),
        'avg_schooling_val':     get(16),
        'academic_pct_val':      get(19),
        'employed_pct_val':      get(22),
        'women_noincome_pct_val':get(25),
        'above2x_wage_pct_val':  get(28),
        'below_min_wage_pct_val':get(31),
        'income_support_pct_val':get(34),
        'avg_monthly_income_val':get(37),
        'vehicles_per100_val':   get(40),
        'avg_vehicle_fee_val':   get(43),
        'avg_days_abroad_val':   get(46),
    }
    if rec['index_value'] is not None:
        records.append(rec)

data_js   = json.dumps(records, ensure_ascii=False)
numeric_js = json.dumps(numeric_cols, ensure_ascii=False)
total      = len(records)

lines = []
lines.append('<!DOCTYPE html>')
lines.append('<html lang="he" dir="rtl">')
lines.append('<head>')
lines.append('<meta charset="UTF-8">')
lines.append('<title>EDA Dashboard</title>')
lines.append('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>')
lines.append('<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&display=swap" rel="stylesheet">')
lines.append('''<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Heebo',sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh}
header{background:linear-gradient(135deg,#1f2937,#111827);border-bottom:1px solid #21262d;padding:1.2rem 2rem;display:flex;align-items:center;gap:1rem}
header h1{font-size:1.4rem;color:#58a6ff;font-weight:700}
header span{color:#8b949e;font-size:.85rem;margin-right:.5rem}
.container{padding:1.5rem 2rem;max-width:1400px;margin:0 auto}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.8rem}
.metric-card{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1.3rem 1.6rem;position:relative;overflow:hidden}
.metric-card::before{content:'';position:absolute;top:0;right:0;width:4px;height:100%;background:var(--accent)}
.metric-card .val{font-size:2.2rem;font-weight:700;color:var(--accent);line-height:1}
.metric-card .lbl{font-size:.82rem;color:#8b949e;margin-top:.5rem}
.metric-card .sub{font-size:.75rem;color:#6e7681;margin-top:.3rem}
.controls{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1.2rem 1.6rem;margin-bottom:1.5rem;display:flex;flex-wrap:wrap;gap:1.2rem;align-items:flex-end}
.ctrl-group{display:flex;flex-direction:column;gap:.35rem}
label{font-size:.75rem;color:#8b949e;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
select{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:8px;padding:.45rem .85rem;font-family:inherit;font-size:.85rem;cursor:pointer;outline:none;min-width:200px}
select:focus{border-color:#58a6ff}
button.apply{background:#238636;color:#fff;border:none;border-radius:8px;padding:.52rem 1.5rem;font-size:.85rem;font-family:inherit;cursor:pointer;font-weight:600;transition:.2s;align-self:flex-end}
button.apply:hover{background:#2ea043}
.badge{background:#21262d;border-radius:20px;padding:.3rem 1rem;font-size:.82rem;color:#8b949e;align-self:flex-end}
.badge span{color:#58a6ff;font-weight:700}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem}
.chart-card{background:#161b22;border:1px solid #21262d;border-radius:14px;padding:1.3rem 1.5rem}
.chart-card h3{font-size:.9rem;color:#e6edf3;font-weight:600;margin-bottom:1.1rem;display:flex;align-items:center;gap:.5rem}
canvas{width:100%!important;max-height:280px}
@media(max-width:800px){.metrics,.charts{grid-template-columns:1fr}}
</style>''')
lines.append('</head>')
lines.append('<body>')
lines.append('<header>')
lines.append('<div>')
lines.append('<h1>&#128202; EDA &mdash; מדד חברתי-כלכלי</h1>')
lines.append('<span>למ"ס 2019 &bull; אזורים סטטיסטיים בתוך עיריות ומועצות מקומיות</span>')
lines.append('</div>')
lines.append('</header>')
lines.append('<div class="container">')

# Metrics
lines.append('<div class="metrics">')
lines.append('<div class="metric-card" style="--accent:#58a6ff"><div class="val" id="m1">-</div><div class="lbl">&#128205; אזורים סטטיסטיים (לאחר סינון)</div><div class="sub" id="m1s">-</div></div>')
lines.append('<div class="metric-card" style="--accent:#3fb950"><div class="val" id="m2">-</div><div class="lbl">&#127919; ממוצע ערך מדד</div><div class="sub" id="m2s">-</div></div>')
lines.append('<div class="metric-card" style="--accent:#d29922"><div class="val" id="m3">-</div><div class="lbl">&#127941; חציון דירוג</div><div class="sub" id="m3s">מ-1 עד 1,635</div></div>')
lines.append('</div>')

# Controls
lines.append('<div class="controls">')
lines.append('<div class="ctrl-group"><label>&#128269; סינון לפי אשכול</label><select id="filterCluster"><option value="">כל האשכולות (1-10)</option><option value="1">אשכול 1 — הנמוך</option><option value="2">אשכול 2</option><option value="3">אשכול 3</option><option value="4">אשכול 4</option><option value="5">אשכול 5</option><option value="6">אשכול 6</option><option value="7">אשכול 7</option><option value="8">אשכול 8</option><option value="9">אשכול 9</option><option value="10">אשכול 10 — הגבוה</option></select></div>')
lines.append('<div class="ctrl-group"><label>&#128200; Histogram — עמודה מספרית</label><select id="histCol"></select></div>')
lines.append('<div class="ctrl-group"><label>&#128201; Bar — ממוצע</label><select id="barX"></select></div>')
lines.append('<div class="ctrl-group"><label>&#128200; Bar — לפי</label><select id="barY"><option value="cluster">אשכול</option></select></div>')
lines.append('<button class="apply" onclick="update()">&#128260; עדכן</button>')
lines.append('<div class="badge">מוצג: <span id="countBadge">-</span> רשומות</div>')
lines.append('</div>')

# Charts
lines.append('<div class="charts">')
lines.append('<div class="chart-card"><h3><span>&#128200;</span> Histogram — התפלגות</h3><canvas id="histChart"></canvas></div>')
lines.append('<div class="chart-card"><h3><span>&#128201;</span> Bar Chart — ממוצע לפי קבוצה</h3><canvas id="barChart"></canvas></div>')
lines.append('</div>')

lines.append('</div>') # container

# Script
lines.append('<script>')
lines.append('const ALL_DATA = ' + data_js + ';')
lines.append('const NUMERIC  = ' + numeric_js + ';')
lines.append('''
const histEl = document.getElementById('histCol');
const barXEl = document.getElementById('barX');
Object.entries(NUMERIC).forEach(([k,v])=>{
  histEl.innerHTML += '<option value="'+k+'">'+v+'</option>';
  barXEl.innerHTML += '<option value="'+k+'">'+v+'</option>';
});
histEl.value='index_value'; barXEl.value='index_value';

let HC=null, BC=null;

function filtered(){
  const cl=document.getElementById('filterCluster').value;
  return cl ? ALL_DATA.filter(r=>r.cluster==+cl) : ALL_DATA;
}
function mean(a){return a.reduce((s,v)=>s+v,0)/a.length}
function median(a){const s=[...a].sort((x,y)=>x-y);const m=Math.floor(s.length/2);return s.length%2?s[m]:(s[m-1]+s[m])/2}
function stdev(a){const mu=mean(a);return Math.sqrt(mean(a.map(v=>(v-mu)**2)))}

function histogram(data,col,bins=20){
  const vals=data.map(r=>r[col]).filter(v=>v!=null);
  if(!vals.length) return {labels:[],counts:[]};
  const mn=Math.min(...vals),mx=Math.max(...vals);
  const w=(mx-mn)/bins||1;
  const counts=Array(bins).fill(0);
  const labels=[];
  for(let i=0;i<bins;i++) labels.push((mn+i*w).toFixed(2));
  vals.forEach(v=>{let idx=Math.min(bins-1,Math.floor((v-mn)/w));counts[idx]++;});
  return{labels,counts};
}

function barData(data,xCol,yCol){
  const g={};
  data.forEach(r=>{const k=r[yCol];if(k==null||r[xCol]==null)return;(g[k]=g[k]||[]).push(r[xCol]);});
  const keys=Object.keys(g).sort((a,b)=>+a-+b);
  return{labels:keys.map(k=>'אשכול '+k),avgs:keys.map(k=>+mean(g[k]).toFixed(3))};
}

const PAL=['#58a6ff','#3fb950','#d29922','#f78166','#a371f7','#39d353','#e3b341','#ffa657','#79c0ff','#56d364'];

function update(){
  const data=filtered();
  const col=histEl.value, xCol=barXEl.value;

  // Metrics
  const idxV=data.map(r=>r.index_value).filter(v=>v!=null);
  const rnkV=data.map(r=>r.rank).filter(v=>v!=null);
  document.getElementById('m1').textContent=data.length.toLocaleString();
  document.getElementById('m1s').textContent='מתוך '+ALL_DATA.length.toLocaleString()+' סה"כ';
  document.getElementById('m2').textContent=idxV.length?mean(idxV).toFixed(3):'-';
  document.getElementById('m2s').textContent=idxV.length?'סטיית תקן: '+stdev(idxV).toFixed(3):'';
  document.getElementById('m3').textContent=rnkV.length?Math.round(median(rnkV)):'-';
  document.getElementById('countBadge').textContent=data.length.toLocaleString();

  // Histogram
  const {labels:hL,counts}=histogram(data,col);
  if(HC)HC.destroy();
  HC=new Chart(document.getElementById('histChart'),{
    type:'bar',
    data:{labels:hL,datasets:[{label:NUMERIC[col]||col,data:counts,backgroundColor:'rgba(88,166,255,.65)',borderColor:'#58a6ff',borderWidth:1,borderRadius:4}]},
    options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#8b949e',maxRotation:45,font:{size:9}},grid:{color:'#21262d'}},y:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}}}}
  });

  // Bar
  const {labels:bL,avgs}=barData(data,xCol,'cluster');
  if(BC)BC.destroy();
  BC=new Chart(document.getElementById('barChart'),{
    type:'bar',
    data:{labels:bL,datasets:[{label:'ממוצע '+NUMERIC[xCol],data:avgs,backgroundColor:bL.map((_,i)=>PAL[i%PAL.length]+'99'),borderColor:bL.map((_,i)=>PAL[i%PAL.length]),borderWidth:1,borderRadius:6}]},
    options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}},y:{ticks:{color:'#8b949e'},grid:{color:'#21262d'}}}}
  });
}
update();
''')
lines.append('</script>')
lines.append('</body>')
lines.append('</html>')

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Done! Records:', total)
