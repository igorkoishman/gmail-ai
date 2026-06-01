import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.database import DatabaseEngine
from src.core.gmail import GmailEngine
from src.ml.base import BaseML

def fix_ads():
    print("🚀 [FIX ADS] Scanning for wrongly grouped AliExpress Ads using BaseML hard rules...")
    db = DatabaseEngine()
    gmail = GmailEngine()
    base_ml = BaseML()
    
    conn = db._get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, threadId, full_text, subject, sender, manual_category, ai_category FROM emails WHERE manual_category = 'Ali express' OR sender LIKE '%aliexpress%'")
    emails = cursor.fetchall()
    
    fixed_count = 0
    for email in emails:
        sender = str(email['sender'])
        full_text = str(email['full_text'])
        current_manual = email['manual_category']
        current_ai = email['ai_category']
        
        correct_cat = base_ml._get_hard_rule(sender, full_text)
        
        # We demote to 'Ali express adds' if the hard rule explicitly determines it's an ad
        if correct_cat == "Ali express adds":
            if current_manual != "Ali express adds" or current_ai != "Ali express adds":
                update_cursor = conn.cursor()
                update_cursor.execute(
                    "UPDATE emails SET manual_category = %s, ai_category = %s WHERE id = %s", 
                    ("Ali express adds", "Ali express adds", email['id'])
                )
                update_cursor.close()
                
            # ALWAYS apply correct single label in Gmail
            gmail.apply_label_to_thread(email['threadId'], "Ali express adds")
            
            print(f"🔄 Thread {email['threadId']}: ensured label 'Ali express adds' is applied (was DB Manual: '{current_manual}', DB AI: '{current_ai}')")
            fixed_count += 1
                
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Successfully separated {fixed_count} promotional emails into 'Ali express adds'!")
    print("\nNext step: Run `python main.py --train` to retrain your model with the corrected ads vs orders.")

if __name__ == "__main__":
    fix_ads()
