import schedule
import time
from .predictor import ProPredictor
from ..core.gmail import GmailEngine

class GmailAIService:
    def __init__(self):
        self.predictor = ProPredictor()

    def run_cycle(self):
        print("\n🔄 [SERVICE] Starting sync cycle...")
        try:
            gmail = GmailEngine()
            emails = gmail.fetch_new_emails(max_results=50, query="in:inbox is:unread")
            
            if emails:
                self.predictor.db.save_emails(emails)
                self.predictor.predict_all()
                
                # Apply labels to Gmail
                conn = self.predictor.db._get_connection()
                # Simplified fetch for the cycle
                for email in emails:
                    tid = email['threadId']
                    row = self.predictor.db.get_emails_for_ai(limit=1, reclassify_ai_labels=True) # or just query by ID
                    # Actually easier just to re-run the prediction for the loop
                    # but for now let's use the DB's latest prediction
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT ai_category FROM emails WHERE threadId = %s", (tid,))
                    res = cursor.fetchone()
                    if res and res['ai_category']:
                        gmail.apply_label_to_thread(tid, res['ai_category'])
                    cursor.close()
                conn.close()
                print(f"✅ Cycle complete for {len(emails)} emails.")
            else:
                print("📭 No new emails.")
        except Exception as e:
            print(f"❌ [SERVICE ERROR]: {e}")
        print("💤 Waiting for next run...")

    def start(self, interval_hours=24):
        print(f"🚀 Starting persistent service: Syncing every {interval_hours} hours.")
        self.run_cycle()
        schedule.every(interval_hours).hours.do(self.run_cycle)
        while True:
            schedule.run_pending()
            time.sleep(1)
