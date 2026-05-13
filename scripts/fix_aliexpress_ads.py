import sys
import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.database import DatabaseEngine

def fix_ads():
    print("🚀 [FIX ADS] Scanning for wrongly grouped AliExpress Ads...")
    db = DatabaseEngine()
    conn = db._get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, full_text, subject, sender FROM emails WHERE manual_category = 'Ali express'")
    emails = cursor.fetchall()
    
    order_patterns = [
        r"חבילה מס'",
        r"הזמנה מס'",
        r"הזמנה \d+.*בהמתנה לאישור.*נשלחה"
    ]
    
    fixed_count = 0
    for email in emails:
        text = str(email['full_text']) + " " + str(email['subject']) + " " + str(email['sender'])
        
        is_order = False
        for pattern in order_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                is_order = True
                break
                
        # If it doesn't have the explicit Hebrew order strings, it's an ad!
        if not is_order:
            update_cursor = conn.cursor()
            update_cursor.execute(
                "UPDATE emails SET manual_category = %s WHERE id = %s", 
                ("Ali express ad", email['id'])
            )
            update_cursor.close()
            fixed_count += 1
            
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Successfully separated {fixed_count} promotional emails into 'Ali express ad'!")
    print("\nNext step: Run `python main.py --train` to retrain your model with the corrected ads vs orders.")

if __name__ == "__main__":
    fix_ads()
