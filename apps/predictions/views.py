
from pathlib import Path
from .models import YieldPrediction
import joblib
import numpy as np
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from qiskit_machine_learning.kernels import FidelityQuantumKernel


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "apps" / "predictions" / "ml_models"

# Load both models and their saved preprocessing components.
classical_data = joblib.load(
    MODEL_DIR / "comparison_classical_model.joblib"
)
quantum_data = joblib.load(
    MODEL_DIR / "quantum_yield_model.joblib"
)

classical_model = classical_data["model"]
classical_preprocessor = classical_data["preprocessor"]

quantum_model = quantum_data["model"]
quantum_preprocessor = quantum_data["preprocessor"]
quantum_pca = quantum_data["pca"]
quantum_angle_scaler = quantum_data["angle_scaler"]
quantum_feature_map = quantum_data["feature_map"]
quantum_train_data = quantum_data["train_quantum"]

quantum_kernel = FidelityQuantumKernel(
    feature_map=quantum_feature_map
)


@login_required
def yield_prediction(request):
    result = None
    error = None

    if request.method == "POST":
        try:
            crop = request.POST.get("crop", "").strip()
            season = request.POST.get("season", "").strip()
            state = request.POST.get("state", "").strip()
            year = int(request.POST.get("year", "2026"))
            area = float(request.POST.get("area", "0"))
            rainfall = float(request.POST.get("rainfall", "0"))

            if not crop or not season or not state:
                raise ValueError(
                    "Please enter a crop, season, and state."
                )

            if area <= 0 or rainfall < 0:
                raise ValueError(
                    "Area must be positive and rainfall cannot be negative."
                )

            input_data = pd.DataFrame([{
                "Crop": crop,
                "Crop_Year": year,
                "Season": season,
                "State": state,
                "Area": area,
                "Annual_Rainfall": rainfall,
            }])

            # Classical prediction
            classical_input = classical_preprocessor.transform(
                input_data
            )
            classical_prediction = float(
                classical_model.predict(classical_input)[0]
            )

            # Quantum-kernel prediction
            quantum_input = quantum_preprocessor.transform(
                input_data
            )
            quantum_input = quantum_pca.transform(quantum_input)
            quantum_input = quantum_angle_scaler.transform(
                quantum_input
            )

            kernel_values = quantum_kernel.evaluate(
                x_vec=quantum_input,
                y_vec=quantum_train_data,
            )

            quantum_prediction = float(
                quantum_model.predict(kernel_values)[0]
            )
            
            YieldPrediction.objects.create(
                farmer=request.user,
                crop=crop,
                season=season,
                state=state,
                crop_year=year,
                area=area,
                annual_rainfall=rainfall,
                classical_yield=classical_prediction,
                quantum_yield=quantum_prediction,
            )

            result = {
                "crop": crop,
                "classical_yield": round(classical_prediction, 3),
                "quantum_yield": round(quantum_prediction, 3),
                "classical_name": "Classical Random Forest",
                "quantum_name": "Experimental Quantum Kernel SVR",
            }

        except (ValueError, TypeError) as exc:
            error = str(exc) or "Please enter valid values."
        except Exception:
            error = (
                "Prediction failed. Check the server terminal "
                "for the technical error."
            )

    return render(
        request,
        "predictions/yield_prediction.html",
        {
            "result": result,
            "error": error,
        },
    )



@login_required
def prediction_history(request):
    predictions = YieldPrediction.objects.filter(
        farmer=request.user
    )

    return render(
        request,
        "predictions/history.html",
        {"predictions": predictions},
    )
