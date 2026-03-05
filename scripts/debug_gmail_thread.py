import base64
from email.utils import parsedate_to_datetime
from datetime import datetime
from gmail_engine import GmailEngine
import joblib
import pandas as pd
import numpy as np

gmail = GmailEngine()
thread_id = '19c9e7718323c17b'

try:
    t_data = gmail.service.users().threads().get(userId='me', id=thread_id, format='full').execute()
    msg = t_data['messages'][0]
    headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}
    subject = headers.get('subject', 'No Subject')
    sender = headers.get('from', 'Unknown Sender')

    body_data = gmail._get_body(msg['payload'])
    snippet = msg.get('snippet', '')
    full_text = f"Subject: {subject}\nSender: {sender}\n\n{body_data}"

    print(f"--- THREAD {thread_id} ---")
    print(f"Sender: {sender}")
    print(f"Subject: {subject}")
    print(f"Snippet: {snippet}")
    print(f"Full Text length: {len(full_text)}")
    print(f"Full Text preview:\n{full_text[:300]}...")

    # Predict
    clf = joblib.load('ml_models_pro/pro_classifier.pkl')
    vec = joblib.load('ml_models_pro/pro_vectorizer.pkl')
    enc = joblib.load('ml_models_pro/pro_encoder.pkl')

    df = pd.DataFrame([{'full_text': full_text}])
    X = vec.transform(df['full_text'].astype(str).str.lower())
    preds = clf.predict(X)
    probs = clf.predict_proba(X)
    
    print("\n--- PREDICTION ---")
    print(f"Predicted Category: {enc.inverse_transform(preds)[0]}")
    
    top_3_idx = np.argsort(probs[0])[-3:][::-1]
    for idx in top_3_idx:
        print(f"{enc.classes_[idx]}: {probs[0][idx]:.4f}")

except Exception as e:
    print(f"Error: {e}")
