
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "crop_yield.csv"
MODEL_DIR = BASE_DIR / "apps" / "predictions" / "ml_models"
MODEL_PATH = MODEL_DIR / "yield_model.joblib"

# Load dataset
df = pd.read_csv(DATA_PATH)

# Features available for our baseline model.
# Do not use Production, Yield, Fertilizer or Pesticide as inputs.
features = [
    "Crop",
    "Crop_Year",
    "Season",
    "State",
    "Area",
    "Annual_Rainfall",
]

target = "Yield"

X = df[features].copy()
y = df[target].copy()

# Treat crop, season, and state as categorical data.
categorical_features = ["Crop", "Season", "State"]
numeric_features = [
    "Crop_Year",
    "Area",
    "Annual_Rainfall",
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
        ("numeric", "passthrough", numeric_features),
    ]
)

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "regressor",
            RandomForestRegressor(
                n_estimators=150,
                random_state=42,
                n_jobs=-1,
                min_samples_leaf=2,
            ),
        ),
    ]
)

# Hold out data for evaluation
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training classical yield model...")
model.fit(X_train, y_train)

# Evaluate on unseen test rows
predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = mean_squared_error(y_test, predictions) ** 0.5
r2 = r2_score(y_test, predictions)

print("\n--- Classical Model Evaluation ---")
print(f"Training rows: {len(X_train)}")
print(f"Testing rows:  {len(X_test)}")
print(f"MAE:           {mae:.4f}")
print(f"RMSE:          {rmse:.4f}")
print(f"R² score:      {r2:.4f}")

# Save trained pipeline for Django
MODEL_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(
    {
        "model": model,
        "features": features,
        "target": target,
        "target_unit": "dataset-defined yield unit",
    },
    MODEL_PATH,
)

print(f"\nModel saved to: {MODEL_PATH}")
print("Training complete.")
