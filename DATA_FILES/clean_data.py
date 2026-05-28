import pandas as pd

df = pd.read_excel("ALL_DATA.xlsx")
print(f"לפני ניקוי: {len(df)} שורות")

# סינון מחיר חריג
df = df[df["dealAmount"] >= 100_000]
df = df[df["dealAmount"] <= 10_000_000]

# סינון שטח חריג
df = df[df["assetArea"] >= 20]
df = df[df["assetArea"] <= 500]

print(f"אחרי ניקוי: {len(df)} שורות")

df.to_csv("all_data_clean.csv", index=False, encoding="utf-8-sig")
print("נשמר: all_data_clean.csv")
