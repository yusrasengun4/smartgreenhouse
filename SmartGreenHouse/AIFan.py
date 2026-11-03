import pandas as pd
from sqlalchemy import create_engine

# SQL Server bağlantısı
connection_string = (
    
)

engine = create_engine(connection_string)

# SQL tablosunu Python'a aktar
query = """
SELECT
    Timestamp,
    Temperature,
    Humidity,
    SoilMoisture,
    Light,
    Heater,
    Fan,
    Irrigation,
    AutoMode,
    EmergencyStop,
    Scenario
FROM GreenhouseData
"""

df = pd.read_sql(query, engine)

from sklearn.model_selection import train_test_split

features_fan = [
    "Temperature",
    "Humidity",
    "Light"
]

X_fan = df[features_fan]
y_fan = df["Fan"]

print("\n================ FAN AI DATASET ================")

print("X boyutu:")
print(X_fan.shape)

print("\ny boyutu:")
print(y_fan.shape)

print("\nFan sınıf dağılımı:")
print(y_fan.value_counts())

print("\nFan sınıf yüzdeleri:")
print(y_fan.value_counts(normalize=True) * 100)

X_train_fan, X_test_fan, y_train_fan, y_test_fan = train_test_split(
    X_fan,
    y_fan,
    test_size=0.20,
    random_state=42,
    stratify=y_fan
)

print("\n================ FAN TRAIN / TEST ================")


from sklearn.ensemble import RandomForestClassifier

fan_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

fan_model.fit(X_train_fan, y_train_fan)

print("\nFan modeli eğitimi tamamlandı.")
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)

y_pred_fan = fan_model.predict(X_test_fan)
y_prob_fan = fan_model.predict_proba(X_test_fan)[:, 1]

print("\n================ FAN MODEL DEĞERLENDİRME ================")

print("Accuracy:",
      accuracy_score(y_test_fan, y_pred_fan))

print("\nClassification Report:")
print(
    classification_report(
        y_test_fan,
        y_pred_fan,
        target_names=["Fan=False", "Fan=True"],
        zero_division=0
    )
)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test_fan,
        y_pred_fan
    )
)

print("\nROC-AUC:")
print(
    roc_auc_score(
        y_test_fan,
        y_prob_fan
    )
)
print("\n================ FAN FEATURE IMPORTANCE ================")

for feature, importance in zip(
    features_fan,
    fan_model.feature_importances_
):
    print(f"{feature:15}: {importance:.4f}")
    import joblib

joblib.dump(fan_model, "fan_model.pkl")

print("Fan modeli kaydedildi: fan_model.pkl")
