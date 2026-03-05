import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from .base import BaseML
from ..core.config import Config
from ..core.ai_gemini import gemini_classify

class ProTrainer(BaseML):
    def __init__(self, model_dir="ml_models_pro"):
        super().__init__(model_dir)
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 3))
        self.classifier = RandomForestClassifier(n_estimators=300, class_weight='balanced')
        self.encoder = LabelEncoder()

    def teach_with_gemini(self, target_count=2000):
        """Fetch emails from DB that need labels and ask Gemini."""
        current_ai_classified_count = self.db.get_ai_classified_count()
        needed_for_gemini = max(0, target_count - current_ai_classified_count)

        if needed_for_gemini == 0:
            print(f"✅ Already have {current_ai_classified_count} Gemini-classified emails. Target {target_count} reached.")
            return

        print(f"🎯 Need {needed_for_gemini} more emails to reach Gemini target. Fetching...")
        to_teach = self.db.get_emails_for_ai(limit=needed_for_gemini, reclassify_ai_labels=False)
        
        if not to_teach:
            print("✅ No emails found that need teaching.")
            return

        print(f"🤖 [TEACHING] Asking Gemini to label {len(to_teach)} emails...")
        
        all_results = []
        for i in range(0, len(to_teach), Config.GEMINI_BATCH_SIZE):
            batch = to_teach[i:i+Config.GEMINI_BATCH_SIZE]
            payload = [{
                "threadId": e['threadId'],
                "from": e['sender'],
                "subject": e['subject'],
                "snippet": e['snippet'],
                "full_text": e['full_text'][:2000] if e['full_text'] else ""
            } for e in batch]
            
            try:
                results = gemini_classify(payload, Config.GEMINI_API_KEY, Config.GEMINI_MODEL, Config.REQUIRED_CATEGORIES)
                if results:
                    self.db.update_ai_predictions(results)
                    all_results.extend(results)
                    print(f"   - ✅ Batch {i // Config.GEMINI_BATCH_SIZE + 1} processed.")
            except Exception as e:
                print(f"   - ❌ ERROR in Gemini batch: {e}")
                
        print(f"✅ DB updated with {len(all_results)} new Gemini labels.")

    def train_locally(self):
        """Learns from Manual and Gemini labels."""
        data = self.db.get_training_data()
        if len(data) < 5:
            print("❌ Not enough labels to train yet.")
            return

        df = pd.DataFrame(data)
        print(f"🧠 [TRAINING] Learning from {len(df)} examples...")
        
        X = self.vectorizer.fit_transform(df['full_text'].astype(str).str.lower())
        y = self.encoder.fit_transform(df['category'])
        
        self.classifier.fit(X, y)
        
        joblib.dump(self.classifier, self.model_file)
        joblib.dump(self.vectorizer, self.vec_file)
        joblib.dump(self.encoder, self.enc_file)
        print("✅ [OFFLINE PRO BRAIN] Trained and saved.")
