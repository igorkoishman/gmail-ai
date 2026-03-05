import os
import pandas as pd
from database_engine import DatabaseEngine
from gmail_engine import GmailEngine
from config import Config

def enrich_database():
    print("🚀 [ENRICHMENT] Starting database text enrichment...")
    
    db = DatabaseEngine()
    gmail = GmailEngine()
    conn = db._get_connection()
    
    # Find emails with empty or very short text
    # We prioritize ones that have a manual category since they are our training anchor
    query = """
        SELECT threadId, sender, subject 
        FROM emails 
        WHERE (full_text IS NULL OR full_text = '' OR LENGTH(full_text) < 100)
    """
    df_to_enrich = pd.read_sql(query, conn)
    conn.close()
    
    if df_to_enrich.empty:
        print("✅ No records found that need enrichment.")
        return

    # Filter out invalid threadIds (Gmail IDs are hex strings, usually 16 chars)
    # Some records have Message-IDs like <... @outlook.com> which will 400.
    import re
    valid_hex_pattern = re.compile(r'^[0-9a-fA-F]{16,}$')
    
    initial_count = len(df_to_enrich)
    df_to_enrich = df_to_enrich[df_to_enrich['threadId'].apply(lambda x: bool(valid_hex_pattern.match(str(x))))]
    skipped = initial_count - len(df_to_enrich)
    
    if skipped > 0:
        print(f"⚠️ Skipped {skipped} records with invalid/Message-ID formats (only hex IDs are valid for Gmail API).")

    print(f"🧐 Found {len(df_to_enrich)} valid Gmail threads that need richer text extraction.")
    
    enriched_count = 0
    batch_size = 50
    
    for i in range(0, len(df_to_enrich), batch_size):
        batch = df_to_enrich.iloc[i:i+batch_size]
        updates = []
        
        for idx, row in batch.iterrows():
            tid = row['threadId']
            try:
                # Use the new improved parsing logic in fetch_new_emails (via get_body)
                # But we just want this one thread
                t_data = gmail.service.users().threads().get(userId='me', id=tid, format='full').execute()
                msg = t_data['messages'][0]
                
                body_data = gmail._get_body(msg['payload'])
                snippet = msg.get('snippet', '')
                full_text = f"Subject: {row['subject']}\nSender: {row['sender']}\n\n{body_data}"
                
                updates.append({
                    'threadId': tid,
                    'full_text': full_text,
                    'raw_body': body_data,
                    'snippet': snippet
                })
                enriched_count += 1
                if enriched_count % 10 == 0:
                    print(f"  ✨ Enriched {enriched_count} records...")
                    
            except Exception as e:
                print(f"  ❌ Error enriching thread {tid}: {e}")
                
        # Update DB in batches
        if updates:
            conn = db._get_connection()
            cursor = conn.cursor()
            sql = "UPDATE emails SET full_text = %s, raw_body = %s, snippet = %s WHERE threadId = %s"
            for u in updates:
                cursor.execute(sql, (u['full_text'], u['raw_body'], u['snippet'], u['threadId']))
            conn.commit()
            cursor.close()
            conn.close()

    print(f"\n🎉 Enrichment complete! {enriched_count} records updated with high-quality text.")

if __name__ == "__main__":
    enrich_database()
