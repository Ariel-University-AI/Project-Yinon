import pandas as pd
import json, random

CSV  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\PART3\DATA_final.csv'
OUT  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\PART3\eda_app.html'

df = pd.read_csv(CSV, encoding='utf-8-sig', low_memory=False)
df.columns = [c.strip() for c in df.columns]

num_cols = df.select_dtypes(include='number').columns.tolist()

# Cluster column
CLUSTER_COL = 'CLUSTER*** (1 to 10) '
if CLUSTER_COL not in df.columns:
    CLUSTER_COL = [c for c in df.columns if 'CLUSTER' in c.upper()][0]

clusters = sorted(df[CLUSTER_COL].dropna().unique().astype(int).tolist())

# Build per-cluster data dict
random.seed(42)
cluster_data = {}
for cl in [0] + clusters:   # 0 = all
    sub = df if cl == 0 else df[df[CLUSTER_COL] == cl]
    n = len(sub)
    d = {'n': n, 'cols': {}}
    idx = list(range(n))
    if n > 400: idx = random.sample(idx, 400)
    for c in num_cols:
        vals = sub[c].iloc[idx].values.tolist()
        d['cols'][c] = [v if pd.notna(v) else None for v in vals]
    cluster_data[str(cl)] = d

# Correlation matrix (all data, top 12 numeric cols only for readability)
top_cols = num_cols[:12]
corr_df  = df[top_cols].dropna()
corr_mat = corr_df.corr().round(3)
corr_vals = corr_mat.values.tolist()
corr_lbls = [c[:18] for c in top_cols]

data_js   = json.dumps(cluster_data, ensure_ascii=False)
corr_v_js = json.dumps(corr_vals,    ensure_ascii=False)
corr_l_js = json.dumps(corr_lbls,    ensure_ascii=False)
num_js    = json.dumps(num_cols,     ensure_ascii=False)
rows_n, cols_n = df.shape
pct_miss  = round(df.isnull().sum().sum() / (rows_n * cols_n) * 100, 2)

# Write HTML
f = open(OUT, 'w', encoding='utf-8')
f.write(f'''<!DOCTYPE html>
<html lang="he" dir="rtl"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EDA Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0d1117;--surf:#161b22;--bdr:#21262d;--txt:#c9d1d9;--mut:#8b949e;--blu:#58a6ff;--grn:#3fb950;--yel:#d29922;--red:#f85149;--pur:#a371f7}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Heebo',sans-serif;background:var(--bg);color:var(--txt)}}
nav{{background:linear-gradient(135deg,#161b22,#0d1117);border-bottom:1px solid var(--bdr);padding:.9rem 2rem;display:flex;align-items:center;justify-content:space-between}}
nav h1{{font-size:1.1rem;color:var(--blu);font-weight:700}}
nav .info{{color:var(--mut);font-size:.8rem}}
.wrap{{padding:1.5rem 2rem;max-width:1400px;margin:0 auto}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.5rem}}
.met{{background:var(--surf);border:1px solid var(--bdr);border-radius:14px;padding:1.2rem 1.5rem;position:relative;overflow:hidden}}
.met::after{{content:'';position:absolute;top:0;right:0;width:4px;height:100%;background:var(--a)}}
.met .v{{font-size:2rem;font-weight:900;color:var(--a)}}
.met .l{{font-size:.8rem;color:var(--mut);margin-top:.3rem}}
/* FILTER BAR */
.fbar{{background:var(--surf);border:1px solid var(--bdr);border-radius:14px;padding:1rem 1.5rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:1rem;flex-wrap:wrap}}
.fbar label{{font-size:.75rem;color:var(--mut);font-weight:700;text-transform:uppercase}}
.chips{{display:flex;gap:.4rem;flex-wrap:wrap}}
.chip{{background:var(--bg);border:1px solid var(--bdr);border-radius:20px;padding:.3rem .9rem;font-size:.8rem;color:var(--mut);cursor:pointer;transition:.15s;font-family:inherit}}
.chip:hover,.chip.on{{background:var(--blu);border-color:var(--blu);color:#fff;font-weight:700}}
.chip.on{{box-shadow:0 0 10px rgba(88,166,255,.3)}}
.nbadge{{margin-right:auto;background:var(--bg);border:1px solid var(--bdr);border-radius:20px;padding:.3rem 1rem;font-size:.8rem;color:var(--mut)}}
.nbadge span{{color:var(--blu);font-weight:700}}
/* CHARTS */
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem}}
.card{{background:var(--surf);border:1px solid var(--bdr);border-radius:14px;padding:1.2rem}}
.card h3{{font-size:.9rem;font-weight:700;margin-bottom:.8rem;display:flex;align-items:center;gap:.4rem}}
.ctrls{{display:flex;gap:.7rem;margin-bottom:.8rem;flex-wrap:wrap;align-items:flex-end}}
.cg{{display:flex;flex-direction:column;gap:.3rem;flex:1;min-width:150px}}
.cg label{{font-size:.7rem;color:var(--mut);font-weight:700;text-transform:uppercase}}
select{{background:var(--bg);border:1px solid #30363d;color:var(--txt);border-radius:8px;padding:.42rem .8rem;font-family:inherit;font-size:.83rem;width:100%;outline:none}}
select:focus{{border-color:var(--blu)}}
button{{background:var(--blu);color:#fff;border:none;border-radius:8px;padding:.45rem 1.2rem;font-family:inherit;font-size:.83rem;cursor:pointer;font-weight:700}}
button:hover{{filter:brightness(1.15)}}
.sbar{{font-size:.75rem;color:var(--mut);margin-bottom:.7rem;display:flex;gap:1rem;flex-wrap:wrap}}
.sbar b{{color:var(--blu)}}
canvas{{width:100%!important}}
/* HEATMAP */
.hmwrap{{overflow-x:auto}}
#heatCanvas{{display:block}}
@media(max-width:720px){{.grid2,.metrics{{grid-template-columns:1fr}}}}
</style></head><body>

<nav>
  <h1>&#128202; EDA Dashboard &mdash; מדד חברתי-כלכלי (למ"ס)</h1>
  <span class="info">DATA_final.csv</span>
</nav>

<div class="wrap">

<!-- METRICS -->
<div class="metrics">
  <div class="met" style="--a:var(--blu)"><div class="v" id="m1">-</div><div class="l">&#128205; שורות (לאחר סינון)</div></div>
  <div class="met" style="--a:var(--grn)"><div class="v">{cols_n}</div><div class="l">&#128205; עמודות</div></div>
  <div class="met" style="--a:var(--yel)"><div class="v">{pct_miss}%</div><div class="l">&#128165; ערכים חסרים</div></div>
</div>

<!-- FILTER BAR -->
<div class="fbar">
  <label>&#128269; סינון לפי אשכול:</label>
  <div class="chips">
    <button class="chip on" data-cl="0" onclick="setCluster(0)">הכל</button>
''')
for cl in clusters:
    f.write(f'    <button class="chip" data-cl="{cl}" onclick="setCluster({cl})">{cl}</button>\n')
f.write(f'''  </div>
  <div class="nbadge">מוצג: <span id="nbadge">-</span> רשומות</div>
</div>

<!-- CHARTS ROW -->
<div class="grid2">
  <div class="card">
    <h3>&#128200; Histogram</h3>
    <div class="ctrls">
      <div class="cg"><label>עמודה</label><select id="hcol"></select></div>
      <div class="cg"><label>Bins</label><select id="hbins"><option>10</option><option>15</option><option selected>20</option><option>30</option><option>50</option></select></div>
      <button onclick="drawH()">&#8635;</button>
    </div>
    <div class="sbar" id="hstats"></div>
    <canvas id="hchart" height="200"></canvas>
  </div>
  <div class="card">
    <h3>&#9899; Scatter Plot</h3>
    <div class="ctrls">
      <div class="cg"><label>ציר X</label><select id="sx"></select></div>
      <div class="cg"><label>ציר Y</label><select id="sy"></select></div>
      <button onclick="drawS()">&#8635;</button>
    </div>
    <div class="sbar" id="sstats"></div>
    <canvas id="schart" height="200"></canvas>
  </div>
</div>

<!-- HEATMAP -->
<div class="card" style="margin-bottom:1.5rem">
  <h3>&#128293; Heatmap — מטריצת קורלציות (12 עמודות מספריות)</h3>
  <div class="hmwrap"><canvas id="heatCanvas"></canvas></div>
</div>

</div><!-- wrap -->

<script>
const CD={clusterData};
const CV={corrVals};
const CL={corrLbls};
const NC={numJs};
const TOTAL={rows_n};

let curCl=0;
function getData(){{return CD[String(curCl)];}}

// Populate selects
const hcolEl=document.getElementById('hcol');
const sxEl=document.getElementById('sx');
const syEl=document.getElementById('sy');
NC.forEach((c,i)=>{{
  hcolEl.innerHTML+=`<option value="${{c}}">${{c}}</option>`;
  sxEl.innerHTML+=`<option value="${{c}}" ${{i===0?'selected':''}}>${{c}}</option>`;
  syEl.innerHTML+=`<option value="${{c}}" ${{i===1?'selected':''}}>${{c}}</option>`;
}});

function mean(a){{return a.reduce((s,v)=>s+v,0)/a.length;}}
function stdev(a){{const m=mean(a);return Math.sqrt(mean(a.map(v=>(v-m)**2)));}}
function median(a){{const s=[...a].sort((x,y)=>x-y);const m=Math.floor(s.length/2);return s.length%2?s[m]:(s[m-1]+s[m])/2;}}
function corr(x,y){{const mx=mean(x),my=mean(y),sx=stdev(x),sy=stdev(y);return mean(x.map((v,i)=>((v-mx)/sx)*((y[i]-my)/sy)));}}

function setCluster(cl){{
  curCl=cl;
  document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('on',+c.dataset.cl===cl));
  const d=getData();
  document.getElementById('m1').textContent=d.n.toLocaleString();
  document.getElementById('nbadge').textContent=d.n.toLocaleString();
  drawH(); drawS();
}}

let HC=null,SC=null;
function drawH(){{
  const col=hcolEl.value, bins=+document.getElementById('hbins').value;
  const d=getData(); if(!d)return;
  const vals=(d.cols[col]||[]).filter(v=>v!=null);
  if(!vals.length)return;
  const mn=Math.min(...vals),mx=Math.max(...vals),w=(mx-mn)/bins||1;
  const counts=Array(bins).fill(0),labels=[];
  for(let i=0;i<bins;i++)labels.push((mn+i*w).toFixed(2));
  vals.forEach(v=>{{let i=Math.min(bins-1,Math.floor((v-mn)/w));counts[i]++;}});
  const m=mean(vals),sd=stdev(vals);
  document.getElementById('hstats').innerHTML=
    `n=<b>${{vals.length.toLocaleString()}}</b> &bull; ממוצע <b>${{m.toFixed(2)}}</b> &bull; &#963; <b>${{sd.toFixed(2)}}</b> &bull; חציון <b>${{median(vals).toFixed(2)}}</b>`;
  if(HC)HC.destroy();
  HC=new Chart(document.getElementById('hchart'),{{
    type:'bar',data:{{labels,datasets:[{{data:counts,backgroundColor:'rgba(88,166,255,.6)',borderColor:'#58a6ff',borderWidth:1,borderRadius:3}}]}},
    options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#8b949e',font:{{size:9}},maxRotation:45}},grid:{{color:'#21262d'}}}},y:{{ticks:{{color:'#8b949e'}},grid:{{color:'#21262d'}}}}}}}}
  }});
}}
function drawS(){{
  const cx=sxEl.value,cy=syEl.value;
  const d=getData(); if(!d)return;
  const xa=d.cols[cx]||[],ya=d.cols[cy]||[];
  const pts=[],xc=[],yc=[];
  for(let i=0;i<xa.length;i++){{if(xa[i]!=null&&ya[i]!=null){{pts.push({{x:xa[i],y:ya[i]}});xc.push(xa[i]);yc.push(ya[i]);}}}}
  if(!pts.length)return;
  const r=corr(xc,yc);
  const rc=Math.abs(r)>.5?'#3fb950':Math.abs(r)>.3?'#d29922':'#f85149';
  document.getElementById('sstats').innerHTML=
    `n=<b>${{pts.length}}</b> &bull; Pearson r: <b style="color:${{rc}}">${{r.toFixed(4)}}</b> &bull; ${{Math.abs(r)>.7?'קורלציה חזקה':Math.abs(r)>.4?'קורלציה בינונית':'קורלציה חלשה'}} ${{r>0?'&#8593;חיובית':'&#8595;שלילית'}}`;
  if(SC)SC.destroy();
  SC=new Chart(document.getElementById('schart'),{{
    type:'scatter',
    data:{{datasets:[{{data:pts,backgroundColor:'rgba(163,113,247,.55)',borderColor:'#a371f7',borderWidth:1,pointRadius:4}}]}},
    options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#8b949e',font:{{size:9}}}},grid:{{color:'#21262d'}},title:{{display:true,text:cx.slice(0,20),color:'#8b949e'}}}},y:{{ticks:{{color:'#8b949e'}},grid:{{color:'#21262d'}},title:{{display:true,text:cy.slice(0,20),color:'#8b949e'}}}}}}}}
  }});
}}

// ── HEATMAP ──────────────────────────────────────────────────────────────────
function drawHeat(){{
  const canvas=document.getElementById('heatCanvas');
  const n=CL.length, cell=52, pad={{t:120,l:160,r:20,b:20}};
  canvas.width=pad.l+n*cell+pad.r;
  canvas.height=pad.t+n*cell+pad.b;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#161b22';ctx.fillRect(0,0,canvas.width,canvas.height);

  function lerp(a,b,t){{return a+(b-a)*t;}}
  function color(v){{
    // -1=red, 0=gray, 1=green
    if(v>0){{const t=v;return `rgb(${{Math.round(lerp(33,63,t))}},${{Math.round(lerp(185,179,t))}},${{Math.round(lerp(80,80,t))}})`}}
    else{{const t=-v;return `rgb(${{Math.round(lerp(33,248,t))}},${{Math.round(lerp(185,81,t))}},${{Math.round(lerp(80,73,t))}})`}}
  }}

  // Column labels (top, rotated)
  ctx.save();ctx.font='bold 10px Heebo,sans-serif';ctx.fillStyle='#8b949e';ctx.textAlign='right';
  CL.forEach((lbl,i)=>{{
    ctx.save();ctx.translate(pad.l+i*cell+cell/2,pad.t-6);ctx.rotate(-Math.PI/3);
    ctx.fillText(lbl,0,0);ctx.restore();
  }});ctx.restore();

  // Row labels (right side, RTL)
  ctx.font='bold 10px Heebo,sans-serif';ctx.fillStyle='#8b949e';ctx.textAlign='right';
  CL.forEach((lbl,i)=>{{ctx.fillText(lbl,pad.l-6,pad.t+i*cell+cell/2+4);}});

  // Cells
  CV.forEach((row,i)=>{{
    row.forEach((v,j)=>{{
      const x=pad.l+j*cell, y=pad.t+i*cell;
      ctx.fillStyle=color(v);
      ctx.fillRect(x+1,y+1,cell-2,cell-2);
      ctx.font=v===1?'bold 10px Heebo':'10px Heebo';
      ctx.fillStyle=Math.abs(v)>.5?'#fff':'#c9d1d9';
      ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(v.toFixed(2),x+cell/2,y+cell/2);
    }});
  }});
}}

// Init
setCluster(0);
drawHeat();
</script>
</body></html>
'''.replace('{clusterData}', data_js)
     .replace('{corrVals}',   corr_v_js)
     .replace('{corrLbls}',   corr_l_js)
     .replace('{numJs}',      num_js)
     .replace('{rows_n}',     str(rows_n)))
f.close()
print(f'Done! {rows_n} rows x {cols_n} cols -> {OUT}')
