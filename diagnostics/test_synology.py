import joblib
import pandas as pd
from database_engine import DatabaseEngine

db = DatabaseEngine()
conn = db._get_connection()
# Grab a synology email from DB
df = pd.read_sql("SELECT sender, subject, full_text FROM emails WHERE sender LIKE '%synology%' LIMIT 1", conn)
conn.close()

if not df.empty:
    row = df.iloc[0]
    print(f"Testing on: {row['subject']}")
    
    clf = joblib.load('ml_models_pro/pro_classifier.pkl')
    vec = joblib.load('ml_models_pro/pro_vectorizer.pkl')
    enc = joblib.load('ml_models_pro/pro_encoder.pkl')
    
    X = vec.transform([row['full_text'].lower()])
    pred = clf.predict(X)
    print(f"Prediction: {enc.inverse_transform(pred)[0]}")
else:
    print("No Synology email found in DB.")
