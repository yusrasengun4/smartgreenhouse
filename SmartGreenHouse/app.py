from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)


# ============================================================
# MODELLERİ YÜKLE
# ============================================================

irrigation_model = joblib.load("irrigation_model.pkl")
fan_model = joblib.load("fan_model.pkl")


# ============================================================
# ORTAK KARAR EŞİĞİ
# ============================================================

IRRIGATION_THRESHOLD = 0.50
FAN_THRESHOLD = 0.50


# ============================================================
# SULAMA MODELİ
# ============================================================

IRRIGATION_FEATURES = [
    "Temperature",
    "Humidity",
    "SoilMoisture",
    "Light"
]


IRRIGATION_RANGES = {
    "Temperature": (15.0, 35.0),
    "Humidity": (40.0, 75.0),
    "SoilMoisture": (35.0, 90.0),
    "Light": (50.0, 950.0)
}


# ============================================================
# FAN MODELİ
# ============================================================

FAN_FEATURES = [
    "Temperature",
    "Humidity",
    "Light"
]


FAN_RANGES = {
    "Temperature": (15.0, 35.0),
    "Humidity": (40.0, 75.0),
    "Light": (50.0, 950.0)
}


# ============================================================
# YARDIMCI FONKSİYON
# ============================================================

def validate_input(data, features, ranges):

    if not data:
        return None, ["JSON verisi gönderilmedi."]

    missing = [
        f for f in features
        if f not in data
    ]

    if missing:
        return None, [
            f"Eksik alan(lar): {', '.join(missing)}"
        ]

    values = {}

    # Sayısal değer kontrolü
    for f in features:

        try:
            values[f] = float(data[f])

        except (TypeError, ValueError):

            return None, [
                f"{f} değeri sayısal olmalıdır."
            ]

    # Eğitim aralığı kontrolü
    warnings = []

    for f in features:

        lo, hi = ranges[f]

        if not (lo <= values[f] <= hi):

            warnings.append(
                f"{f} değeri ({values[f]}) "
                f"beklenen aralığın dışında "
                f"({lo}-{hi}). "
                f"Tahmin güvenilir olmayabilir."
            )

    return values, warnings


# ============================================================
# SULAMA TAHMİNİ
# ============================================================

@app.route("/predict/irrigation", methods=["POST"])
def predict_irrigation():

    try:

        data = request.get_json()

        values, warnings = validate_input(
            data,
            IRRIGATION_FEATURES,
            IRRIGATION_RANGES
        )

        if values is None:

            return jsonify({
                "error": warnings[0]
            }), 400

        # Model girişini oluştur
        X = np.array([
            [
                values[f]
                for f in IRRIGATION_FEATURES
            ]
        ])

        # Sulama olasılığı
        probability = (
            irrigation_model
            .predict_proba(X)[0][1]
        )

        # Karar
        prediction = (
            probability >= IRRIGATION_THRESHOLD
        )

        response = {

            "irrigation_needed":
                bool(prediction),

            "probability":
                round(float(probability), 4),

            "probability_percent":
                round(
                    float(probability * 100),
                    2
                ),

            "threshold_used":
                IRRIGATION_THRESHOLD,

            "reliable":
                len(warnings) == 0
        }

        if warnings:
            response["warnings"] = warnings

        return jsonify(response)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# FAN TAHMİNİ
# ============================================================

@app.route("/predict/fan", methods=["POST"])
def predict_fan():

    try:

        data = request.get_json()

        values, warnings = validate_input(
            data,
            FAN_FEATURES,
            FAN_RANGES
        )

        if values is None:

            return jsonify({
                "error": warnings[0]
            }), 400

        # Fan modelinin beklediği girişler
        X = np.array([
            [
                values[f]
                for f in FAN_FEATURES
            ]
        ])

        # Fan çalışma olasılığı
        probability = (
            fan_model
            .predict_proba(X)[0][1]
        )

        # Karar
        prediction = (
            probability >= FAN_THRESHOLD
        )

        response = {

            "fan_needed":
                bool(prediction),

            "probability":
                round(float(probability), 4),

            "probability_percent":
                round(
                    float(probability * 100),
                    2
                ),

            "threshold_used":
                FAN_THRESHOLD,

            "reliable":
                len(warnings) == 0
        }

        if warnings:
            response["warnings"] = warnings

        return jsonify(response)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# API SAĞLIK KONTROLÜ
# ============================================================

@app.route("/health", methods=["GET"])
def health_check():

    return jsonify({

        "status": "ok",

        "irrigation_model_loaded":
            irrigation_model is not None,

        "fan_model_loaded":
            fan_model is not None

    })


# ============================================================
# FLASK BAŞLAT
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )