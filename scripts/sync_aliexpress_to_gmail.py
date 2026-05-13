import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.gmail import GmailEngine
from src.core.database import DatabaseEngine

def sync_labels_to_gmail():
    print("🚀 [SYNC] Pushing corrected 'Ali express' and 'Ali express ad' labels to Gmail...")
    
    try:
        gmail = GmailEngine()
        db = DatabaseEngine()
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        return
        
    conn = db._get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all the emails we just categorized
    cursor.execute("""
        SELECT threadId, manual_category 
        FROM emails 
        WHERE manual_category IN ('Ali express', 'Ali express ad')
    """)
    emails = cursor.fetchall()
    conn.close()
    
    total = len(emails)
    print(f"📦 Found {total} emails to sync to Gmail.")
    
    # Pre-fetch label IDs so we can also remove wrong labels
    ali_express_id = gmail.get_or_create_label("Ali express")
    ali_express_ad_id = gmail.get_or_create_label("Ali express ad")
    
    success_count = 0
    for i, email in enumerate(emails):
        tid = email['threadId']
        cat = email['manual_category']
        
        target_label_id = ali_express_id if cat == 'Ali express' else ali_express_ad_id
        remove_label_id = ali_express_id if cat == 'Ali express ad' else ali_express_ad_id
        
        try:
            body = {
                'addLabelIds': [target_label_id],
                'removeLabelIds': [remove_label_id]
            }
            gmail.service.users().threads().modify(userId='me', id=tid, body=body).execute()
            success_count += 1
        except Exception as e:
            # Some threads might be deleted in Gmail
            pass
            
        if i % 100 == 0 and i > 0:
            print(f"   ⏳ Synced {i}/{total} emails...")
            # Sleep slightly to respect Gmail API quotas
            time.sleep(1)
            
    print(f"\n✅ Sync Complete! Successfully pushed {success_count} correct labels to Gmail.")

if __name__ == "__main__":
    sync_labels_to_gmail()
