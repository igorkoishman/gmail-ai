import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.database import DatabaseEngine
from src.core.gmail import GmailEngine
from src.ml.base import BaseML

def fix_all_aliexpress():
    print("🚀 [FIX ALL ALIEXPRESS] Aligning DB and Gmail with src.ml.base hard rules...")
    db = DatabaseEngine()
    gmail = GmailEngine()
    base_ml = BaseML()
    
    conn = db._get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all emails from AliExpress
    cursor.execute("SELECT id, threadId, sender, full_text, manual_category, ai_category FROM emails WHERE sender LIKE '%aliexpress%'")
    emails = cursor.fetchall()
    
    fixed_count = 0
    for e in emails:
        sender = str(e['sender'])
        full_text = str(e['full_text'])
        current_manual = e['manual_category']
        current_ai = e['ai_category']
        
        # Get the definitive hard rule
        correct_cat = base_ml._get_hard_rule(sender, full_text)
        
        if not correct_cat:
            continue
            
        # Check if the DB is misaligned (either manual or AI category)
        if current_manual != correct_cat or current_ai != correct_cat:
            update_cursor = conn.cursor()
            update_cursor.execute(
                "UPDATE emails SET manual_category = %s, ai_category = %s WHERE id = %s", 
                (correct_cat, correct_cat, e['id'])
            )
            update_cursor.close()
            
            # Update Gmail to ensure single-label policy applies
            # The apply_label_to_thread function already strips out other AI labels
            gmail.apply_label_to_thread(e['threadId'], correct_cat)
            
            print(f"🔄 Thread {e['threadId']}: changed to '{correct_cat}' (was Manual: '{current_manual}', AI: '{current_ai}')")
            fixed_count += 1
            
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Successfully corrected {fixed_count} AliExpress emails based on new hard rules!")

if __name__ == "__main__":
    fix_all_aliexpress()
