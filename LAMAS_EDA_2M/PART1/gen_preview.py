
import csv
import os

file_path = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\DATA.csv'
out_path  = r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA\data_preview.html'

with open(file_path, 'r', encoding='utf-8-sig') as f:
    reader = list(csv.reader(f))

header = reader[6][:7]
header[1] = 'שם יישוב'
data = reader[9:14]
rows_data = [row[:7] for row in data]
total_rows = len(reader) - 9

dtypes = [
    ('CODE OF LOCALITY',               'סמל יישוב',              'float64',          '#4ade80'),
    ('שם יישוב',                        'שם יישוב',               'object (טקסט)',    '#60a5fa'),
    ('CODE OF STATISTICAL AREA',        'סמל אזור סטטיסטי',       'object (טקסט)',    '#60a5fa'),
    ('POPULATION*',                     'אוכלוסייה',               'object (טקסט)',    '#60a5fa'),
    ('INDEX VALUE**',                   'ערך מדד חברתי-כלכלי',    'float64',          '#4ade80'),
    ('RANK (1 to 1635)',                'דירוג',                   'float64',          '#4ade80'),
    ('CLUSTER*** (1 to 10)',            'אשכול',                   'float64 (קטגורי)', '#4ade80'),
    ('VALUE / STANDARDIZED VALUE / RANK x14', 'משתני המדד (14 אינדיקטורים)', 'object / float64', '#f59e0b'),
    ('Unnamed: 50-69',                  'עמודות ריקות',            'float64 (NaN)',    '#f87171'),
]

rows_html = ''
for row in rows_data:
    cells = ''.join('<td>{}</td>'.format(c.strip()) for c in row)
    rows_html += '<tr>{}</tr>'.format(cells)

dtype_rows = ''
for col, heb, dtype, color in dtypes:
    dtype_rows += (
        '<tr>'
        '<td><code>{}</code></td>'
        '<td>{}</td>'
        '<td><span style="background:{};color:#111;padding:2px 8px;border-radius:12px;font-size:0.85em;">{}</span></td>'
        '</tr>'
    ).format(col, heb, color, dtype)

header_cells = ''.join('<th>{}</th>'.format(h) for h in header)

html = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>DATA.csv Preview</title>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Heebo', 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
  h1 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: .5rem; font-size: 1.6rem; }}
  h2 {{ color: #94a3b8; margin-top: 2.5rem; font-size: 1rem; text-transform: uppercase; letter-spacing: .08em; }}
  .stats {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0; }}
  .stat-box {{ background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 1rem 2rem; text-align: center; min-width: 130px; }}
  .stat-box .val {{ font-size: 2rem; font-weight: 700; color: #38bdf8; }}
  .stat-box .label {{ font-size: .8rem; color: #94a3b8; margin-top: .2rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 14px; overflow: hidden; margin: 1rem 0; box-shadow: 0 4px 20px rgba(0,0,0,.4); }}
  th {{ background: linear-gradient(135deg, #0ea5e9, #2563eb); color: #fff; padding: 12px 14px; font-size: .85rem; text-align: right; font-weight: 600; }}
  td {{ padding: 10px 14px; font-size: .85rem; border-bottom: 1px solid #1e3a5f; text-align: right; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #1a3050; }}
  code {{ background: #0f2744; color: #93c5fd; padding: 2px 7px; border-radius: 5px; font-size: .78rem; direction: ltr; display: inline-block; }}
  .note {{ color: #475569; font-size: .8rem; margin-top: 2rem; padding: 1rem; background: #1e293b; border-radius: 10px; border-right: 3px solid #334155; }}
</style>
</head>
<body>
<h1>&#128202; DATA.csv &mdash; מדד חברתי-כלכלי (למ&quot;ס 2019)</h1>

<div class="stats">
  <div class="stat-box"><div class="val">{total_rows:,}</div><div class="label">שורות נתונים</div></div>
  <div class="stat-box"><div class="val">70</div><div class="label">עמודות</div></div>
  <div class="stat-box"><div class="val">14</div><div class="label">אינדיקטורים</div></div>
  <div class="stat-box"><div class="val">20</div><div class="label">עמודות ריקות</div></div>
</div>

<h2>5 השורות הראשונות (עמודות מרכזיות)</h2>
<table>
  <thead><tr>{header_cells}</tr></thead>
  <tbody>{rows_html}</tbody>
</table>

<h2>סוגי עמודות</h2>
<table>
  <thead><tr><th>שם עמודה</th><th>תיאור</th><th>סוג</th></tr></thead>
  <tbody>{dtype_rows}</tbody>
</table>

<div class="note">
  &#9432; שורות המכילות <code>..</code> מציינות נתונים חסרים (פחות מ-100 תושבים באזור הסטטיסטי).
  <br>עמודת אוכלוסייה מסוג object כי מכילה פסיקים (למשל 10,424) &mdash; יש להמיר לפני חישוב.
</div>

</body></html>""".format(
    total_rows=total_rows,
    header_cells=header_cells,
    rows_html=rows_html,
    dtype_rows=dtype_rows
)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print('Done:', out_path)
