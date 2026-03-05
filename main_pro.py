import os
import pandas as pd
import numpy as np
import joblib
import argparse
import time
import schedule
from typing import List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from config import Config
from ai_engine import gemini_classify
from database_engine import DatabaseEngine
from gmail_engine import GmailEngine

class ProClassifier:
    def __init__(self, model_dir="ml_models_pro"):
        self.db = DatabaseEngine()
        self.model_dir = model_dir
        self.model_file = os.path.join(model_dir, "pro_classifier.pkl")
        self.vec_file = os.path.join(model_dir, "pro_vectorizer.pkl")
        self.enc_file = os.path.join(model_dir, "pro_encoder.pkl")

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        # These are placeholders/defaults, they get overwritten during training
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 3))
        self.classifier = RandomForestClassifier(n_estimators=300, class_weight='balanced')
        self.encoder = LabelEncoder()

    # --- PHASE 3: GEMINI TEACHING ---
    def teach_with_gemini(self, limit=5000):
        """Fetch emails from DB that need labels and ask Gemini."""
        # Get current count of AI-classified emails (not manually overridden)
        current_ai_classified_count = self.db.get_ai_classified_count()
        target_gemini_count = 2000 # User-defined target for Gemini-classified emails
        
        # Calculate how many more emails Gemini needs to classify to reach the target
        needed_for_gemini = max(0, target_gemini_count - current_ai_classified_count)

        if needed_for_gemini == 0:
            print(f"✅ Already have {current_ai_classified_count} Gemini-classified emails. Target {target_gemini_count} reached. Skipping Gemini teaching.")
            return

        print(f"🎯 Need {needed_for_gemini} more emails to reach Gemini target of {target_gemini_count}. Fetching...")
        to_teach = self.db.get_emails_for_ai(limit=needed_for_gemini, reclassify_ai_labels=False)
        
        if not to_teach:
            print("✅ No emails found that need teaching (or re-teaching).")
            return

        print(f"🤖 [TEACHING] Asking Gemini to label {len(to_teach)} emails using Full Content with NEW Categories...")
        
        all_results = []
        for i in range(0, len(to_teach), Config.GEMINI_BATCH_SIZE):
            batch_to_teach = to_teach[i:i+Config.GEMINI_BATCH_SIZE]
            
            payload = []
            for e in batch_to_teach:
                payload.append({
                    "threadId": e['threadId'],
                    "from": e['sender'],
                    "subject": e['subject'],
                    "snippet": e['snippet'],
                    "full_text": e['full_text'][:2000] if e['full_text'] else ""
                })
            
            print(f"   - Sending batch {i // Config.GEMINI_BATCH_SIZE + 1} of {len(batch_to_teach)} emails to Gemini...")
            try:
                # Pass the REQUIRED_CATEGORIES to the gemini_classify function for context
                results = gemini_classify(payload, Config.GEMINI_API_KEY, Config.GEMINI_MODEL, Config.REQUIRED_CATEGORIES)
                if results:
                    self.db.update_ai_predictions(results)
                    all_results.extend(results)
                    print(f"   - ✅ Batch processed. {len(results)} emails labeled.")
                else:
                    print(f"   - ⚠️ Gemini returned no labels for batch {i // Config.GEMINI_BATCH_SIZE + 1}.")
            except Exception as e:
                print(f"   - ❌ ERROR processing Gemini batch {i // Config.GEMINI_BATCH_SIZE + 1}: {e}")
                # Continue to next batch even if one fails
                
        print(f"✅ DB updated with {len(all_results)} new Gemini labels.")

    # --- PHASE 4: THE BRAIN (LEARNING FROM YOU) ---
    def _extract_features(self, df):
        return (df['full_text'].astype(str).str.lower())

    def train_locally(self):
        """The 'Human-in-the-loop' training. Prioritizes YOUR manual_category."""
        data = self.db.get_training_data()
        if len(data) < 5:
            print("❌ Not enough labels (Manual or Gemini) to train yet.")
            return

        df = pd.DataFrame(data)
        print(f"🧠 [TRAINING] Learning from {len(df)} examples (Prioritizing YOUR labels)...")
        
        X = self.vectorizer.fit_transform(self._extract_features(df))
        y = self.encoder.fit_transform(df['category'])
        
        self.classifier.fit(X, y)
        
        joblib.dump(self.classifier, self.model_file)
        joblib.dump(self.vectorizer, self.vec_file)
        joblib.dump(self.encoder, self.enc_file)
        print("✅ [OFFLINE PRO BRAIN] Trained and saved.")

    def predict_all(self):
        """Categorize every email in the DB that doesn't have a manual label."""
        if not os.path.exists(self.model_file):
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
                # Fallback for personal categories
                if cat == "Me" and 'igorkoishman@gmail.com' not in sender.lower():
                    cat = "Other/Review"
                elif cat == "Marina" and 'marina0020@gmail.com' not in sender.lower():
                    cat = "Other/Review"
            results.append({'threadId': tid, 'category': cat, 'confidence': conf})
        
        self.db.update_ai_predictions(results)
        print("✅ DB updated with all local ML predictions.")

    def _get_hard_rule(self, sender: str) -> str:
        """Override ML logic for specific critical senders."""
        sender = sender.lower()
        if 'igorkoishman@gmail.com' in sender:
            return "Me"
        if 'marina0020@gmail.com' in sender:
            return "Marina"
        if 'github' in sender or 'docker' in sender:
            return "Work/Professional"
        if 'ebay' in sender:
            return "Shopping/Promotions"
        if 'aliexpress' in sender:
            return "Ali express adds"
        return None

    def bulk_label_history(self):
        """Massive resilient loop to grab uncategorized threads from Gmail, predict, and label them."""
        if not os.path.exists(self.model_file):
            print("🔮 No local model found. Please train first by running --train.")
            return

        print("\n🚀 [BULK LABEL HISTORY] Starting massive resilient relabeling process...")
        
        try:
            gmail = GmailEngine()
        except Exception as e:
            print(f"❌ [ERROR] Failed to initialize GmailEngine: {e}")
            return

        clf = joblib.load(self.model_file)
        vec = joblib.load(self.vec_file)
        enc = joblib.load(self.enc_file)

        # We query for threads that DO NOT have any custom labels yet.
        # This makes it naturally resilient—if it crashes, it just queries the remaining ones next time.
        # It's an approximation, but grabbing a large chunk ensures we keep moving.
        max_results = 200
        
        while True:
            print(f"\n🔍 Fetching up to {max_results} unlabeled threads from Gmail...")
            # We exclude our labels by searching for things without them.
            # A simpler resilient approach is just to fetch raw threads, predict, and apply. 
            # If the label the model predicts is already on it, the API just ignores the add request.
            emails = gmail.fetch_new_emails(max_results=max_results, query="-has:userlabels")
            
            if not emails:
                print("🎉 No more unlabeled threads found! Bulk labeling is complete.")
                break

            print(f"🧠 Predicting categories for {len(emails)} threads...")
            # Quickly save to DB for history
            self.db.save_emails(emails)
            
            # Predict
            df = pd.DataFrame(emails)
            X = vec.transform(df['full_text'].astype(str).str.lower())
            preds = clf.predict(X)
            probs = np.max(clf.predict_proba(X), axis=1)

            results = []
            labeled_count = 0
            
            for tid, cat, conf, sender in zip(df['threadId'], enc.inverse_transform(preds), probs, df['sender']):
                # Hard rules override ML
                hard_cat = self._get_hard_rule(sender)
                if hard_cat:
                    cat = hard_cat
                    conf = 1.0
                else:
                    # Enforce strict personal categories: Only forced by sender rules above
                    # If ML predicted Me/Marina for someone else, fall back to Other/Review
                    if cat == "Me" and 'igorkoishman@gmail.com' not in sender.lower():
                        cat = "Other/Review"
                    elif cat == "Marina" and 'marina0020@gmail.com' not in sender.lower():
                        cat = "Other/Review"

                results.append({'threadId': tid, 'category': cat, 'confidence': conf})
                
                # Apply to Gmail directly (gmail engine creates the label without AI/ now)
                if pd.notna(cat) and str(cat).strip():
                    if gmail.apply_label_to_thread(tid, cat):
                        labeled_count += 1
                        print(f"  🏷️ Applied [{cat}] to thread {tid}")

            self.db.update_ai_predictions(results)
            print(f"✅ Batch complete: Applied labels to {labeled_count}/{len(emails)} threads.")
            
            # Brief pause to avoid hammering the Google API limits too hard
            time.sleep(2)

    # --- PHASE 5: BACKGROUND SERVICE ---
    def run_service_cycle(self):
        print("\n🔄 [SERVICE] Starting sync cycle...")
        try:
            gmail = GmailEngine()
        except Exception as e:
            print(f"❌ [SERVICE ERROR] Failed to initialize GmailEngine: {e}")
            return
            
        emails = gmail.fetch_new_emails(max_results=50, query="in:inbox is:unread")
        
        if emails:
            self.db.save_emails(emails)
            print(f"✅ Saved {len(emails)} new emails to DB.")
            
            # Run prediction on these new emails to generate labels
            print("🧠 Running predictions on new emails...")
            self.predict_all()
            
            # Apply labels back to Gmail
            conn = self.db._get_connection()
            df = pd.read_sql("SELECT threadId, ai_category FROM emails WHERE ai_category IS NOT NULL", conn)
            conn.close()
            
            label_dict = df.set_index('threadId')['ai_category'].to_dict()
            labeled_count = 0
            
            for email in emails:
                tid = email['threadId']
                if tid in label_dict:
                    cat = label_dict[tid]
                    # Don't apply 'None' or empty categories
                    if pd.notna(cat) and cat.strip():
                        if gmail.apply_label_to_thread(tid, cat):
                            labeled_count += 1
                            
            print(f"✅ Applied labels to {labeled_count} threads in Gmail.")
        else:
            print("📭 No new unread emails.")
            
        print("💤 [SERVICE] Sync cycle complete. Waiting for next run...")

    def run_background_service(self, interval_hours=6):
        print(f"🚀 [SERVICE] Starting Gmail AI background service. Syncing every {interval_hours} hours.")
        
        # Run first cycle immediately
        self.run_service_cycle()
        
        # Schedule subsequent cycles
        schedule.every(interval_hours).hours.do(self.run_service_cycle)
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Service stopped by user.")
                break
            except Exception as e:
                print(f"❌ Unexpected error in service loop: {e}")
                time.sleep(60) # Wait a minute before retrying on crash


def main():
    parser = argparse.ArgumentParser(description="Gmail AI Pro: MySQL + Full Content + Human-in-the-loop")
    parser.add_argument("--teach", action="store_true", help="Initiate Gemini teaching (targets 5000 AI-classified emails)")
    parser.add_argument("--train", action="store_true", help="Retrain the local brain")
    parser.add_argument("--predict", action="store_true", help="Run local predictions")
    parser.add_argument("--bulk-label", action="store_true", help="Run the resilient massive bulk relabeling process on all of Gmail")
    parser.add_argument("--service", action="store_true", help="Run as a background daemon (fetches, predicts, labels every 6 hours)")
    args = parser.parse_args()

    pro = ProClassifier()
    
    # Background Service
    if args.service:
        pro.run_background_service(interval_hours=6)
        return

    # Massive Bulk Relabeling
    if args.bulk_label:
        pro.bulk_label_history()
        return

    # 1. Teach (Gemini)
    if args.teach:
        pro.teach_with_gemini()
        # After Gemini teaching, apply local ML to any remaining uncategorized emails
        pro.predict_all()

    # 2. Train (Human + Gemini)
    if args.train:
        pro.train_locally()

    # 3. Predict
    if args.predict:
        pro.predict_all()

    if not any([args.teach, args.train, args.predict, args.bulk_label, args.service]):
        print("Please specify an action: --teach, --train, --predict, --bulk-label, or --service.")
        parser.print_help()
        return

    print("\n✅ Pro Cycle Complete.")
    print("👉 Open localhost:8080 (Adminer) to see/edit your emails.")
    print("👉 User: root | Pass: password | DB: gmail")

if __name__ == "__main__":
    main()
