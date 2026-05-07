import pandas as pd
import numpy as np

df = pd.read_csv(
    r'c:\Users\yinon\OneDrive\שולחן העבודה\לימודים\שנה ה\גיאודזיה מתמטית אלי ספרא\AG_Project\DATA_FILES\BATYAM_2M\bat_yam_clean.csv',
    encoding='utf-8-sig'
)

before  = len(df)
removed = int((df['assetArea'] <= 20).sum())
df_f    = df[df['assetArea'] > 20].copy()
after   = len(df_f)

print(f"לפני: {before} | הוסרו: {removed} | אחרי: {after}")
print(f"assetArea  min={df_f['assetArea'].min():.1f}  max={df_f['assetArea'].max():.1f}  mean={df_f['assetArea'].mean():.1f}")
print(f"dealAmount mean={df_f['dealAmount'].mean():,.0f}  median={df_f['dealAmount'].median():,.0f}")

# Pearson correlations with dealAmount
print("\n--- מתאם פירסון עם dealAmount ---")
df_f['floorNo_num'] = pd.to_numeric(df_f['floorNo'], errors='coerce')
for col in ['assetArea', 'assetRoomNum', 'floorNo_num', 'X', 'Y']:
    r = df_f[col].corr(df_f['dealAmount'])
    print(f"  {col:<18}: {r:.4f}")

# Price per sqm
df_f['price_per_sqm'] = df_f['dealAmount'] / df_f['assetArea']
print(f"\nמחיר למ\"ר: mean={df_f['price_per_sqm'].mean():,.0f}  median={df_f['price_per_sqm'].median():,.0f}")

# dealNatureDescription
print("\n--- dealNatureDescription ---")
g = df_f.groupby('dealNatureDescription')['dealAmount'].agg(['count','mean','median']).sort_values('mean', ascending=False)
for idx, row in g.iterrows():
    print(f"  {idx:<30} n={int(row['count']):>4}  mean={row['mean']:>12,.0f}  median={row['median']:>12,.0f}")

# neighborhood (min 5 deals)
print("\n--- neighborhood: mean dealAmount (top 10, min 5 עסקאות) ---")
nb = df_f.groupby('neighborhood')['dealAmount'].agg(['mean','count'])
nb = nb[nb['count'] >= 5].sort_values('mean', ascending=False).head(10)
for idx, row in nb.iterrows():
    print(f"  {str(idx):<25} mean={row['mean']:>12,.0f}  n={int(row['count'])}")

# assetArea bins
print("\n--- טווחי שטח vs ממוצע מחיר ---")
df_f['area_bin'] = pd.cut(df_f['assetArea'], bins=[20,50,80,100,120,150,200,500], right=True)
ab = df_f.groupby('area_bin', observed=True)['dealAmount'].agg(['mean','count'])
for idx, row in ab.iterrows():
    print(f"  {str(idx):<15}  mean={row['mean']:>12,.0f}  n={int(row['count'])}")

# assetRoomNum distribution
print("\n--- assetRoomNum vs mean dealAmount ---")
rm = df_f.groupby('assetRoomNum')['dealAmount'].agg(['mean','count']).sort_index()
for idx, row in rm.iterrows():
    print(f"  {idx} חדרים: mean={row['mean']:>12,.0f}  n={int(row['count'])}")
