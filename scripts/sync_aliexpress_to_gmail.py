import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.gmail import GmailEngine
from src.core.database import DatabaseEngine

from src.core.config import Config

def sync_labels_to_gmail():
    print("🚀 [SYNC] Correcting labels and enforcing EXACTLY ONE AI label per thread in Gmail...")
    
    try:
        gmail = GmailEngine()
        db = DatabaseEngine()
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        return
        
    conn = db._get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Select ALL emails that currently have or had Ali express / Ali express adds
    # We want to clean up both genuine AliExpress and the wrongly tagged non-AliExpress emails!
    cursor.execute("""
        SELECT threadId, sender, manual_category, ai_category 
        FROM emails 
        WHERE manual_category IN ('Ali express', 'Ali express adds')
           OR ai_category IN ('Ali express', 'Ali express adds')
           OR sender LIKE '%aliexpress%'
    """)
    emails = cursor.fetchall()
    conn.close()
    
    total = len(emails)
    print(f"📦 Found {total} emails to verify and clean in Gmail.")
    
    ali_express_id = gmail.get_or_create_label("Ali express")
    ali_express_ad_id = gmail.get_or_create_label("Ali express adds")
    
    # Gather ALL known AI label IDs to ensure we remove duplicates
    all_known_categories = [
        'Alex Koishman', 'Ali express', 'Ali express adds', 'Ali express ad', 'Etrade', 'LinkedIn', 
        'Marina', 'Me', 'Other', 'Survey', 'Synology', 'Finance/Banking & Payments', 
        'Home/Synology', 'Israel Post', 'Newsletters/Digests', 'Other/Review', 'People/Family', 
        'Security/Alerts', 'Shopping/Delivery Updates', 'Shopping/Orders & Receipts', 
        'Shopping/Promotions', 'Subscriptions/Services', 'Surveys/Feedback', 
        'Travel/Transportation', 'Work/Professional'
    ]
    ai_categories = set(Config.REQUIRED_CATEGORIES + all_known_categories)
    ai_label_ids = {gmail._label_cache[cat]: cat for cat in ai_categories if cat in gmail._label_cache}
    
    success_count = 0
    fixed_double_tags = 0
    cleaned_non_ali = 0
    
    for i, email in enumerate(emails):
        tid = email['threadId']
        sender = str(email['sender']).lower()
        manual_cat = email['manual_category']
        ai_cat = email['ai_category']
        
        is_aliexpress = 'aliexpress' in sender
        
        try:
            thread_data = gmail.service.users().threads().get(userId='me', id=tid, format='minimal').execute()
            current_labels = thread_data.get('messages', [{}])[0].get('labelIds', [])
            
            labels_to_add = []
            labels_to_remove = []
            
            if not is_aliexpress:
                # This is a non-AliExpress email (e.g. Brooks, Google, Israel Post) that was wrongly tagged!
                # 1. Remove Ali express and Ali express adds if present
                if ali_express_id in current_labels:
                    labels_to_remove.append(ali_express_id)
                if ali_express_ad_id in current_labels:
                    labels_to_remove.append(ali_express_ad_id)
                
                # 2. Ensure its correct ai_category or manual_category is attached!
                correct_cat = manual_cat or ai_cat
                if correct_cat and correct_cat in gmail._label_cache:
                    correct_id = gmail._label_cache[correct_cat]
                    if correct_id not in current_labels:
                        labels_to_add.append(correct_id)
                
                if labels_to_remove:
                    cleaned_non_ali += 1
            else:
                # This is a genuine AliExpress email.
                correct_cat = manual_cat or ai_cat or "Ali express adds"
                target_label_id = ali_express_id if correct_cat == 'Ali express' else ali_express_ad_id
                
                if target_label_id not in current_labels:
                    labels_to_add.append(target_label_id)
                
                # Remove ANY OTHER AI label (including the wrong ali express label and any duplicate AI labels)
                for lid in current_labels:
                    if lid in ai_label_ids and lid != target_label_id:
                        labels_to_remove.append(lid)
                        fixed_double_tags += 1
            
            if labels_to_add or labels_to_remove:
                body = {}
                if labels_to_add: body['addLabelIds'] = labels_to_add
                if labels_to_remove: body['removeLabelIds'] = labels_to_remove
                
                gmail.service.users().threads().modify(userId='me', id=tid, body=body).execute()
                success_count += 1
                
        except Exception as e:
            pass
            
        if i % 100 == 0 and i > 0:
            print(f"   ⏳ Synced {i}/{total} emails... (Cleaned {cleaned_non_ali} non-Ali, Fixed {fixed_double_tags} duplicate tags)")
            time.sleep(1)
            
    print(f"\n✅ Sync Complete! Updated {success_count} threads. Cleaned {cleaned_non_ali} non-AliExpress emails and stripped {fixed_double_tags} duplicate labels.")

if __name__ == "__main__":
    sync_labels_to_gmail()
