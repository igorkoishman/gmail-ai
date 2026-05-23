import sys
import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.gmail import GmailEngine
from src.core.database import DatabaseEngine

def run_aliexpress_fix():
    gmail = GmailEngine()
    db = DatabaseEngine()
    
    # 1. Fetch from Gmail using a query that finds these specific Hebrew phrases
    # Using OR to catch any of the variations
    query = 'from:aliexpress OR "חבילה מס" OR "הזמנה מס" OR "בהמתנה לאישור" OR "עדכון מסירה" OR "הודעה על משלוח שמספרו" OR "יצאה מאזור המוצא" OR "מוכנה למשלוח" OR "יצאה למסירה" OR "נשלחה" OR "במדינה/באזור שלכם" OR "אושרה"'
    print(f"🚀 [STEP 1] Fetching missing emails from Gmail with query: {query}")
    emails = gmail.fetch_new_emails(max_results=500, query=query)
    
    if emails:
        print(f"📥 Found {len(emails)} emails from Gmail. Saving to database...")
        db.save_emails(emails)
    else:
        print("📭 No new emails found in Gmail matching the query.")

    # 2. Update the database categories for BOTH old and new emails
    print("\n🧠 [STEP 2] Scanning database to forcefully apply 'Ali express' label...")
    conn = db._get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Select all emails (unmarked, and already marked)
    cursor.execute("SELECT id, threadId, full_text, subject, sender FROM emails")
    all_emails = cursor.fetchall()
    
    updated_count = 0
    for email in all_emails:
        sender_lower = str(email['sender']).lower()
        subject_lower = str(email['subject']).lower()
        
        # Only mark as Ali express if sender is aliexpress or subject contains explicit Hebrew tracking phrases
        is_aliexpress = 'aliexpress' in sender_lower or any(p in subject_lower for p in ["חבילה מס", "הזמנה מס", "בהמתנה לאישור", "עדכון מסירה", "הודעה על משלוח שמספרו"])
        
        if is_aliexpress:
            update_cursor = conn.cursor()
            # Forcefully set manual_category to 'Ali express'
            update_cursor.execute(
                "UPDATE emails SET manual_category = %s WHERE id = %s", 
                ("Ali express", email['id'])
            )
            update_cursor.close()
            updated_count += 1
            
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Successfully marked {updated_count} emails as 'Ali express' in the database!")
    print("\nNext step: Run `python main.py --train` to retrain your model with these fixed labels.")

if __name__ == "__main__":
    run_aliexpress_fix()
