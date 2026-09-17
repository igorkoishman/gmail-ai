from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from .predictor import ProPredictor
from ..core.gmail import GmailEngine
import sys

import time
import pandas as pd

class GmailAIService:
    def __init__(self):
        self.predictor = ProPredictor()
        self.lock_name = "gmail_sync_lock"

    def run_cycle(self, max_batches=10, batch_size=50):
        print("\n🔄 [SERVICE] Attempting to start sync cycle...")
        
        # Distributed Lock: Only one pod can run the cycle
        if not self.predictor.db.acquire_lock(self.lock_name):
            print("🔒 [SKIP] Another pod is already running the sync cycle. Skipping...")
            return

        try:
            gmail = GmailEngine()
            total_labeled = 0
            seen_thread_ids = set()
            
            for batch_num in range(max_batches):
                # Query all inbox emails without user labels (catches both unread and read emails)
                emails = gmail.fetch_new_emails(max_results=batch_size, query="in:inbox -has:userlabels")
                
                # Filter out threads already attempted in this cycle
                new_emails = [e for e in emails if e['threadId'] not in seen_thread_ids]
                
                if not new_emails:
                    if batch_num == 0:
                        print("📭 No unlabeled emails found in inbox.")
                    break
                
                print(f"📥 Processing batch {batch_num + 1} ({len(new_emails)} unlabeled emails)...")
                self.predictor.db.save_emails(new_emails)
                predictions = self.predictor.predict_batch(new_emails)
                
                batch_labeled = 0
                for pred in predictions:
                    tid = pred['threadId']
                    seen_thread_ids.add(tid)
                    cat = pred['category']
                    if pd.notna(cat) and str(cat).strip():
                        if gmail.apply_label_to_thread(tid, cat):
                            batch_labeled += 1
                            print(f"  🏷️ Applied [{cat}] to {tid}")
                
                total_labeled += batch_labeled
                print(f"✅ Batch {batch_num + 1} complete: {batch_labeled}/{len(new_emails)} labeled.")
                
                if len(emails) < batch_size:
                    break
                    
                time.sleep(1)
                
            print(f"✅ Cycle complete: Total {total_labeled} emails labeled.")
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
