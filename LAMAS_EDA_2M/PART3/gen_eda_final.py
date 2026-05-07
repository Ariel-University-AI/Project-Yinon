import pandas as pd
import json
import math

CSV_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\PART3\DATA_final.csv'
OUT_PATH = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\PART3\eda_final.html'

df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', low_memory=False)
df.columns = [c.strip() for c in df.columns]

# Deduplicate column names
cols = pd.Series(df.columns)
for dup in cols[cols.duplicated()].unique(): 
    cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
df.columns = cols


# Basic metrics
rows_total, cols_total = df.shape
missing_pct = round(df.isnull().sum().sum() / (rows_total * cols_total) * 100, 2)

# Column types
num_cols = df.select_dtypes(include=['number']).columns.tolist()
cat_cols = [c for c in df.columns if df[c].nunique() > 1 and df[c].nunique() <= 50] # Low cardinality for categorical

# Clean data for JSON (handle NaN, Inf)
import numpy as np
df = df.replace([np.inf, -np.inf], np.nan)
df = df.where(pd.notnull(df), None)

records = df.to_dict(orient='records')

data_json = json.dumps(records, ensure_ascii=False)
num_cols_json = json.dumps(num_cols, ensure_ascii=False)
cat_cols_json = json.dumps(cat_cols, ensure_ascii=False)

# Build HTML
html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>EDA Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #0d1117; --surface: #161b22; --border: #21262d; --text: #c9d1d9; --muted: #8b949e; --blue: #58a6ff; --green: #3fb950; --yellow: #d29922; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Heebo', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
        
        nav {{ background: linear-gradient(135deg, #161b22, #0d1117); border-bottom: 1px solid var(--border); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        nav h1 {{ color: var(--blue); font-size: 1.2rem; font-weight: 700; margin: 0; }}
        
        .container {{ padding: 1.5rem 2rem; max-width: 1400px; margin: 0 auto; }}
        
        .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 1.5rem; }}
        .metric-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; text-align: center; position: relative; overflow: hidden; }}
        .metric-card::before {{ content: ''; position: absolute; top: 0; right: 0; width: 4px; height: 100%; background: var(--color); }}
        .metric-card .val {{ font-size: 2.5rem; font-weight: 900; color: var(--color); line-height: 1; }}
        .metric-card .lbl {{ font-size: 0.9rem; color: var(--muted); margin-top: 0.5rem; font-weight: 600; }}
        
        .section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .section-title {{ font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
        
        .controls {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; align-items: flex-end; }}
        .control-group {{ display: flex; flex-direction: column; gap: 0.4rem; flex: 1; min-width: 200px; }}
        .control-group label {{ font-size: 0.8rem; color: var(--muted); font-weight: 600; text-transform: uppercase; }}
        select {{ background: var(--bg); color: var(--text); border: 1px solid var(--border); padding: 0.6rem; border-radius: 8px; font-family: inherit; outline: none; transition: 0.2s; }}
        select:focus {{ border-color: var(--blue); }}
        button {{ background: var(--blue); color: #fff; border: none; padding: 0.6rem 1.5rem; border-radius: 8px; font-family: inherit; font-weight: 700; cursor: pointer; transition: 0.2s; }}
        button:hover {{ filter: brightness(1.1); }}
        
        .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
        .chart-container {{ background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 1rem; }}
        
        @media (max-width: 900px) {{ .metrics, .charts-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>

<nav>
    <h1>&#128202; EDA Dashboard &mdash; מדד חברתי-כלכלי</h1>
    <div style="color: var(--muted); font-size: 0.9rem;">DATA_final.csv</div>
</nav>

<div class="container">

    <!-- METRICS -->
    <div class="metrics">
        <div class="metric-card" style="--color: var(--blue);">
            <div class="val" id="metric-rows">{rows_total}</div>
            <div class="lbl">שורות (לאחר סינון)</div>
        </div>
        <div class="metric-card" style="--color: var(--green);">
            <div class="val">{cols_total}</div>
            <div class="lbl">עמודות</div>
        </div>
        <div class="metric-card" style="--color: var(--yellow);">
            <div class="val">{missing_pct}%</div>
            <div class="lbl">אחוז חסרים</div>
        </div>
    </div>

    <!-- GLOBAL FILTER -->
    <div class="section">
        <div class="section-title">&#128269; סינון נתונים גלובלי</div>
        <div class="controls">
            <div class="control-group">
                <label>סנן לפי עמודה קטגורית:</label>
                <select id="filter-col" onchange="updateFilterValues()"></select>
            </div>
            <div class="control-group">
                <label>בחר ערך:</label>
                <select id="filter-val"></select>
            </div>
            <button onclick="applyFilter()">החל סינון</button>
        </div>
    </div>

    <div class="charts-grid">
        <!-- HISTOGRAM -->
        <div class="section" style="margin-bottom: 0;">
            <div class="section-title">&#128200; Histogram</div>
            <div class="controls">
                <div class="control-group">
                    <label>עמודה מספרית:</label>
                    <select id="hist-col"></select>
                </div>
                <button onclick="drawHistogram()">עדכן גרף</button>
            </div>
            <div class="chart-container">
                <canvas id="histChart"></canvas>
            </div>
        </div>

        <!-- BAR CHART -->
        <div class="section" style="margin-bottom: 0;">
            <div class="section-title">&#128201; Bar Chart (ממוצע)</div>
            <div class="controls">
                <div class="control-group">
                    <label>ציר X (ערך לממוצע):</label>
                    <select id="bar-x"></select>
                </div>
                <div class="control-group">
                    <label>ציר Y (קיבוץ קטגורי):</label>
                    <select id="bar-y"></select>
                </div>
                <button onclick="drawBarChart()">עדכן גרף</button>
            </div>
            <div class="chart-container">
                <canvas id="barChart"></canvas>
            </div>
        </div>
    </div>

</div>

<script>
    const ALL_DATA = {data_json};
    const NUM_COLS = {num_cols_json};
    const CAT_COLS = {cat_cols_json};
    
    let currentData = ALL_DATA;
    let histChartInstance = null;
    let barChartInstance = null;

    // Initialize Selects
    function init() {{
        const filterCol = document.getElementById('filter-col');
        const histCol = document.getElementById('hist-col');
        const barX = document.getElementById('bar-x');
        const barY = document.getElementById('bar-y');

        filterCol.innerHTML = '<option value="">ללא סינון</option>';
        CAT_COLS.forEach(c => {{
            filterCol.innerHTML += `<option value="${{c}}">${{c}}</option>`;
            barY.innerHTML += `<option value="${{c}}">${{c}}</option>`;
        }});

        NUM_COLS.forEach((c, i) => {{
            histCol.innerHTML += `<option value="${{c}}" ${{i===0?'selected':''}}>${{c}}</option>`;
            barX.innerHTML += `<option value="${{c}}" ${{i===0?'selected':''}}>${{c}}</option>`;
        }});
        
        // Set defaults if available
        const defaultCluster = CAT_COLS.find(c => c.includes('CLUSTER'));
        if (defaultCluster) {{
            barY.value = defaultCluster;
        }}

        updateFilterValues();
        applyFilter();
    }}

    function updateFilterValues() {{
        const col = document.getElementById('filter-col').value;
        const valSelect = document.getElementById('filter-val');
        
        if (!col) {{
            valSelect.innerHTML = '<option value="">הכל</option>';
            valSelect.disabled = true;
            return;
        }}
        
        valSelect.disabled = false;
        const uniqueVals = [...new Set(ALL_DATA.map(r => r[col]))].filter(v => v !== null && v !== undefined).sort();
        
        valSelect.innerHTML = '<option value="">הכל</option>';
        uniqueVals.forEach(v => {{
            valSelect.innerHTML += `<option value="${{v}}">${{v}}</option>`;
        }});
    }}

    function applyFilter() {{
        const col = document.getElementById('filter-col').value;
        const val = document.getElementById('filter-val').value;
        
        if (col && val) {{
            currentData = ALL_DATA.filter(r => String(r[col]) === String(val));
        }} else {{
            currentData = ALL_DATA;
        }}
        
        document.getElementById('metric-rows').innerText = currentData.length;
        
        drawHistogram();
        drawBarChart();
    }}

    function drawHistogram() {{
        const col = document.getElementById('hist-col').value;
        if (!col) return;
        
        const vals = currentData.map(r => r[col]).filter(v => v !== null && !isNaN(v));
        if (vals.length === 0) return;
        
        const bins = 20;
        const min = Math.min(...vals);
        const max = Math.max(...vals);
        const step = (max - min) / bins || 1;
        
        const counts = new Array(bins).fill(0);
        const labels = [];
        for (let i = 0; i < bins; i++) labels.push((min + i * step).toFixed(2));
        
        vals.forEach(v => {{
            let idx = Math.floor((v - min) / step);
            if (idx >= bins) idx = bins - 1;
            counts[idx]++;
        }});
        
        if (histChartInstance) histChartInstance.destroy();
        
        const ctx = document.getElementById('histChart').getContext('2d');
        histChartInstance = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: col,
                    data: counts,
                    backgroundColor: '#58a6ff',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#8b949e', maxRotation: 45 }}, grid: {{ color: '#21262d' }} }},
                    y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }}
                }}
            }}
        }});
    }}

    function drawBarChart() {{
        const xCol = document.getElementById('bar-x').value; // numeric to average
        const yCol = document.getElementById('bar-y').value; // categorical group
        if (!xCol || !yCol) return;
        
        const groups = {{}};
        currentData.forEach(r => {{
            const grp = r[yCol];
            const val = r[xCol];
            if (grp !== null && val !== null && !isNaN(val)) {{
                if (!groups[grp]) groups[grp] = [];
                groups[grp].push(val);
            }}
        }});
        
        const labels = Object.keys(groups).sort((a,b) => a.localeCompare(b, undefined, {{numeric: true}}));
        const data = labels.map(l => {{
            const arr = groups[l];
            return arr.reduce((a,b) => a+b, 0) / arr.length;
        }});
        
        if (barChartInstance) barChartInstance.destroy();
        
        const ctx = document.getElementById('barChart').getContext('2d');
        barChartInstance = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: `ממוצע ${{xCol}}`,
                    data: data,
                    backgroundColor: '#3fb950',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
                    y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }}
                }}
            }}
        }});
    }}

    // Run
    init();

</script>
</body>
</html>"""

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Generated successfully: {OUT_PATH}")
