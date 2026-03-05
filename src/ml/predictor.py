import pandas as pd
import numpy as np
import joblib
import time
from .base import BaseML
from ..core.gmail import GmailEngine

class ProPredictor(BaseML):
    def predict_all(self):
        """Categorize every email in the DB that doesn't have a manual label."""
        if not self.model_exists():
            print("🔮 No local model found. Please train first.")
            return

        conn = self.db._get_connection()
        df = pd.read_sql("SELECT threadId, sender, full_text FROM emails WHERE manual_category IS NULL", conn)
        conn.close()

        if df.empty:
            print("🔮 No emails need prediction.")
            return

        print(f"🔮 [PREDICTING] Applying Pro ML logic + Hard Rules to {len(df)} emails...")
        clf = joblib.load(self.model_file)
        vec = joblib.load(self.vec_file)
        enc = joblib.load(self.enc_file)

        X = vec.transform(df['full_text'].astype(str).str.lower())
        preds = clf.predict(X)
        probs = np.max(clf.predict_proba(X), axis=1)

        results = []
        for tid, cat, conf, sender in zip(df['threadId'], enc.inverse_transform(preds), probs, df['sender']):
            hard_cat = self._get_hard_rule(sender)
            if hard_cat:
                cat = hard_cat
                conf = 1.0
            else:
                if cat == "Me" and 'igorkoishman@gmail.com' not in sender.lower():
                    cat = "Other/Review"
                elif cat == "Marina" and 'marina0020@gmail.com' not in sender.lower():
                    cat = "Other/Review"
            results.append({'threadId': tid, 'category': cat, 'confidence': conf})
        
        self.db.update_ai_predictions(results)
        print("✅ DB updated with ML predictions.")

    def bulk_label_history(self, max_results=200):
        """Resilient loop to label all of Gmail."""
        if not self.model_exists():
            print("🔮 No local model found. Please train first.")
            return

        print("\n🚀 [BULK LABEL HISTORY] Starting resilient labeling...")
        gmail = GmailEngine()
        clf = joblib.load(self.model_file)
        vec = joblib.load(self.vec_file)
        enc = joblib.load(self.enc_file)

        while True:
            print(f"\n🔍 Fetching up to {max_results} threads...")
            emails = gmail.fetch_new_emails(max_results=max_results, query="-has:userlabels")
            
            if not emails:
                print("🎉 Bulk labeling complete.")
                break

            self.db.save_emails(emails)
            df = pd.DataFrame(emails)
            X = vec.transform(df['full_text'].astype(str).str.lower())
            preds = clf.predict(X)
            probs = np.max(clf.predict_proba(X), axis=1)

            results = []
            labeled_count = 0
            for tid, cat, conf, sender in zip(df['threadId'], enc.inverse_transform(preds), probs, df['sender']):
                hard_cat = self._get_hard_rule(sender)
                if hard_cat:
                    cat = hard_cat
                    conf = 1.0
                else:
                    if cat == "Me" and 'igorkoishman@gmail.com' not in sender.lower():
                        cat = "Other/Review"
                    elif cat == "Marina" and 'marina0020@gmail.com' not in sender.lower():
                        cat = "Other/Review"

                results.append({'threadId': tid, 'category': cat, 'confidence': conf})
                if pd.notna(cat) and str(cat).strip():
                    if gmail.apply_label_to_thread(tid, cat):
                        labeled_count += 1
                        print(f"  🏷️ Applied [{cat}] to {tid}")

            self.db.update_ai_predictions(results)
            print(f"✅ Batch complete: {labeled_count}/{len(emails)} labeled.")
            time.sleep(2)
