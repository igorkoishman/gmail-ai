from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from .predictor import ProPredictor
from ..core.gmail import GmailEngine
import sys

class GmailAIService:
    def __init__(self):
        self.predictor = ProPredictor()
        self.lock_name = "gmail_sync_lock"

    def run_cycle(self):
        print("\n🔄 [SERVICE] Attempting to start sync cycle...")
        
        # Distributed Lock: Only one pod can run the cycle
        if not self.predictor.db.acquire_lock(self.lock_name):
            print("🔒 [SKIP] Another pod is already running the sync cycle. Skipping...")
            return

        try:
            gmail = GmailEngine()
            emails = gmail.fetch_new_emails(max_results=50, query="in:inbox is:unread")
            
            if emails:
                self.predictor.db.save_emails(emails)
                self.predictor.predict_all()
                
                conn = self.predictor.db._get_connection()
                for email in emails:
                    tid = email['threadId']
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
        finally:
            # Always release the lock so the next scheduled run can happen
            self.predictor.db.release_lock(self.lock_name)
            
        print("💤 Waiting for next scheduled run...")

    def start(self, cron_expression="0 0 * * *"):
        print(f"🚀 Starting persistent service with Cron schedule: '{cron_expression}'")
        
        # Initial run on startup
        self.run_cycle()
        
        scheduler = BlockingScheduler()
        try:
            scheduler.add_job(self.run_cycle, CronTrigger.from_crontab(cron_expression))
            scheduler.start()
        except Exception as e:
            print(f"❌ [SCHEDULER ERROR]: {e}")
            sys.exit(1)
