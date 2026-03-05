import argparse
import time

from mbox_engine import parse_mbox
from database_engine import DatabaseEngine
from config import Config

def main():
    parser = argparse.ArgumentParser(description="Import emails from an Mbox file into the database.")
    parser.add_argument("mbox_file", help="Path to the Mbox file.")
    args = parser.parse_args()

    print("--- Starting Mbox Import ---")
    start_time = time.time()

    # 1. Parse all emails from the Mbox file
    all_emails = parse_mbox(args.mbox_file)
    if not all_emails:
        print("No emails found in the Mbox file. Exiting.")
        return

    # 2. Check for existing emails in the database to avoid duplicates
    db = DatabaseEngine()
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT threadId FROM emails")
    existing_ids = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    new_emails = [e for e in all_emails if e['threadId'] not in existing_ids]
    
    print(f"✅ Found {len(all_emails)} total emails in Mbox.")
    print(f"✅ {len(existing_ids)} emails already exist in the database.")
    print(f"📥 {len(new_emails)} new emails will be imported.")

    if not new_emails:
        print("✅ Database is already up-to-date.")
        return

    # 3. Save new emails to the database in batches
    batch_size = Config.BATCH_SIZE
    for i in range(0, len(new_emails), batch_size):
        batch = new_emails[i:i+batch_size]
        try:
            db.save_emails(batch)
            print(f"   - Saved batch { (i // batch_size) + 1 }: {len(batch)} emails.")
        except Exception as e:
            print(f"   - ❌ ERROR saving batch { (i // batch_size) + 1 }: {e}")
            print(f"     - Skipping this batch. You can re-run the script to retry.")

    end_time = time.time()
    print("\n--- Mbox Import Complete ---")
    print(f"Total time taken: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
