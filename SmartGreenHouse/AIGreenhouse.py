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




# ============================================================
# AI VERİ SETİNİN HAZIRLANMASI
# ============================================================

# Modelde kullanılacak giriş değişkenleri
features = [
    "Temperature",
    "Humidity",
    "SoilMoisture",
    "Light"
]

# X = Model girdileri
X = df[features]

# y = Modelin tahmin edeceği hedef
y = df["Irrigation"]


from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight='balanced',   
    random_state=42,
    n_jobs=-1                  
)

model.fit(X_train, y_train)

print("Model eğitimi tamamlandı.")
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nSınıflandırma Raporu:")
print(classification_report(y_test, y_pred, target_names=['Sulama=False', 'Sulama=True']))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\n================ FEATURE IMPORTANCE ================")

for feature, importance in zip(features, model.feature_importances_):
    print(f"{feature:15s}: {importance:.4f}")
    probabilities = model.predict_proba(X_test)

print("\nİlk 10 tahmin:")
for i in range(10):
    print(
        f"Gerçek: {y_test.iloc[i]} | "
        f"Tahmin: {y_pred[i]} | "
        f"Sulama Olasılığı: %{probabilities[i][1] * 100:.2f}"
    )
    from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score
)

# Tahmin
y_pred = model.predict(X_test)

# Sulama olasılığı
y_prob = model.predict_proba(X_test)[:, 1]

print("\n================ MODEL DEĞERLENDİRME ================")

print("Accuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["Sulama=False", "Sulama=True"]
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# ROC-AUC
auc = roc_auc_score(y_test, y_prob)

print("\nROC-AUC:", auc)
print("\n================ KARAR EŞİĞİ ANALİZİ ================")

thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]

for threshold in thresholds:

    y_threshold = (y_prob >= threshold).astype(int)

    precision = precision_score(y_test, y_threshold, zero_division=0)
    recall = recall_score(y_test, y_threshold, zero_division=0)
    f1 = f1_score(y_test, y_threshold, zero_division=0)
    accuracy = accuracy_score(y_test, y_threshold)

    print(
        f"Eşik: %{threshold * 100:.0f} | "
        f"Accuracy: %{accuracy * 100:.2f} | "
        f"Precision: %{precision * 100:.2f} | "
        f"Recall: %{recall * 100:.2f} | "
        f"F1: %{f1 * 100:.2f}"
    )
    import joblib

joblib.dump(model, "irrigation_model.pkl")

print("\nModel başarıyla kaydedildi.")
print("Dosya: irrigation_model.pkl")