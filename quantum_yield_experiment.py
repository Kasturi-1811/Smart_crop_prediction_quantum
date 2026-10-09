
from sklearn.ensemble import RandomForestRegressor

import joblib

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from sklearn.svm import SVR

from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.kernels import FidelityQuantumKernel


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "crop_yield.csv"

# Use a small sample because quantum kernel calculations
# can become expensive as the dataset grows.
df = pd.read_csv(DATA_PATH)
df = df.dropna(
    subset=[
        "Crop", "Crop_Year", "Season", "State",
        "Area", "Annual_Rainfall", "Yield"
    ]
)

df = df.sample(n=min(60, len(df)), random_state=42)

features = [
    "Crop", "Crop_Year", "Season",
    "State", "Area", "Annual_Rainfall"
]

X = df[features]
y = df["Yield"]

categorical_features = ["Crop", "Season", "State"]
numeric_features = ["Crop_Year", "Area", "Annual_Rainfall"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

# Convert categorical fields and scale numeric fields.
preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
        ("numeric", StandardScaler(), numeric_features),
    ]
)

X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# Reduce the encoded data to four features for four qubits.
pca = PCA(n_components=4)
X_train_reduced = pca.fit_transform(X_train_processed)
X_test_reduced = pca.transform(X_test_processed)

# Convert values into a range suitable for angle encoding.
angle_scaler = MinMaxScaler(feature_range=(0, np.pi))
X_train_quantum = angle_scaler.fit_transform(X_train_reduced)
X_test_quantum = angle_scaler.transform(X_test_reduced)

# Build the quantum feature map.
feature_map = zz_feature_map(
    feature_dimension=4,
    reps=1,
    entanglement="linear",
)

quantum_kernel = FidelityQuantumKernel(feature_map=feature_map)

# Classical baseline on the SAME training and test samples
classical_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    min_samples_leaf=2,
    n_jobs=-1,
)

classical_model.fit(X_train_processed, y_train)

joblib.dump(
    {
        "model": classical_model,
        "preprocessor": preprocessor,
        "features": features,
    },
    BASE_DIR / "apps" / "predictions" / "ml_models"
    / "comparison_classical_model.joblib",
)

classical_predictions = classical_model.predict(X_test_processed)

print("\n--- Classical Random Forest (same test samples) ---")
print(f"MAE:  {mean_absolute_error(y_test, classical_predictions):.4f}")
print(
    f"RMSE: "
    f"{np.sqrt(mean_squared_error(y_test, classical_predictions)):.4f}"
)
print(f"R²:   {r2_score(y_test, classical_predictions):.4f}")

print("Calculating training quantum kernel...")
K_train = quantum_kernel.evaluate(x_vec=X_train_quantum)

print("Calculating test quantum kernel...")
K_test = quantum_kernel.evaluate(
    x_vec=X_test_quantum,
    y_vec=X_train_quantum,
)

# Train SVR using the quantum kernel matrices.
model = SVR(kernel="precomputed")
model.fit(K_train, y_train)

predictions = model.predict(K_test)

print("\n--- Quantum Kernel Regression Results ---")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples:  {len(X_test)}")
print(f"MAE:              {mean_absolute_error(y_test, predictions):.4f}")
print(
    f"RMSE:             "
    f"{np.sqrt(mean_squared_error(y_test, predictions)):.4f}"
)
print(f"R² score:         {r2_score(y_test, predictions):.4f}")
print("\nQuantum kernel experiment completed.")

# Save the quantum model and preprocessing components
MODEL_DIR = BASE_DIR / "apps" / "predictions" / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "quantum_yield_model.joblib"

joblib.dump(
    {
        "model": model,
        "preprocessor": preprocessor,
        "pca": pca,
        "angle_scaler": angle_scaler,
        "feature_map": feature_map,
        "train_quantum": X_train_quantum,
        "features": features,
    },
    MODEL_PATH,
)

print(f"Quantum model saved to: {MODEL_PATH}")
