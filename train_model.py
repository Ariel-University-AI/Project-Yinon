# -*- coding: utf-8 -*-
"""
Train XGBoost model to predict real estate prices.
Run once: python train_model.py
Output: model.pkl
"""
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor

DATA_PATH  = "DATA_FILES/apartments_ml_ready.csv"
MODEL_PATH = "model.pkl"
TARGET     = "dealAmount"
RANDOM_STATE = 42

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
print(f"Loaded: {len(df):,} rows, {df.shape[1]} columns")

X = df.drop(columns=[TARGET])
y = df[TARGET]

# ── Train / Test split ────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE
)
print(f"Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")

# ── Train XGBoost ─────────────────────────────────────────────────────────────
model = XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
model.fit(X_train, y_train)
print("Training complete.")

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2   = r2_score(y_test, y_pred)

print(f"\n=== Results ===")
print(f"RMSE : {rmse:,.0f} ILS")
print(f"R2   : {r2:.4f}")
print(f"Mean deal price : {y_test.mean():,.0f} ILS")
print(f"RMSE as pct mean: {rmse / y_test.mean() * 100:.1f}%")

# Top 10 important features
importances = pd.Series(model.feature_importances_, index=X.columns)
print(f"\n=== Top 10 Features ===")
print(importances.sort_values(ascending=False).head(10).to_string())

# Save model
joblib.dump(model, MODEL_PATH)
print(f"\nModel saved: {MODEL_PATH}")