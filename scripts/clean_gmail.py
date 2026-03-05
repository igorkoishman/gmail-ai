import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from config import Config

def clean_gmail():
    if not os.path.exists(Config.TOKEN_PATH):
        print(f"Missing {Config.TOKEN_PATH}. Please authenticate first.")
        return

    creds = Credentials.from_authorized_user_file(Config.TOKEN_PATH, Config.SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    print("🧹 Starting Gmail Cleanup Sequence...")

    # 1. Delete matching labels
    print("\n1️⃣ Detecting and deleting all custom category labels...")
    
    # We want to delete ANY label that we created (e.g., anything that is a category in our DB)
    from database_engine import DatabaseEngine
    import pandas as pd
    
    db = DatabaseEngine()
    conn = db._get_connection()
    df_cats = pd.read_sql("SELECT DISTINCT COALESCE(manual_category, ai_category) as category FROM emails WHERE manual_category IS NOT NULL OR ai_category IS NOT NULL", conn)
    conn.close()
    
    db_categories = df_cats['category'].dropna().unique().tolist()
    # Add the old AI/ ones just in case any are lingering
    prefixes_to_delete = [
        "AI/", "People/", "Home/", "Insurance/", "Shopping/", 
        "Finance/", "Security/", "Subscriptions/", "Work/", 
        "Travel/", "Surveys/", "Newsletters/", "Other/"
    ]
    
    exact_names_to_delete = [str(c).strip() for c in db_categories]

    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        deleted_count = 0
        for label in labels:
            name = label['name']
            
            # Delete if it matches an exact DB category OR starts with an old prefix
            should_delete = label['type'] == 'user' and (
                name in exact_names_to_delete or 
                any(name.startswith(p) for p in prefixes_to_delete)
            )
            
            if should_delete:
                try:
                    service.users().labels().delete(userId='me', id=label['id']).execute()
                    print(f"  🗑️ Deleted label: {name}")
                    deleted_count += 1
                except HttpError as e:
                    print(f"  ❌ Failed to delete {name}: {e}")
        
        print(f"✅ Successfully deleted {deleted_count} category labels. (This strips them from all emails)")
        
    except HttpError as error:
        print(f"❌ Error fetching labels: {error}")

    # 2. Mark all as read
    print("\n2️⃣ Marking all unread emails as read. This might take a few minutes...")
    next_page_token = None
    processed = 0

    while True:
        try:
            # Fetch up to 500 unread messages safely
            results = service.users().messages().list(userId='me', q="is:unread", maxResults=500, pageToken=next_page_token).execute()
            messages = results.get('messages', [])
            
            if not messages:
                break

            message_ids = [msg['id'] for msg in messages]

            # Use batchModify to update them massively
            service.users().messages().batchModify(
                userId='me', 
                body={
                    'ids': message_ids, 
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            
            processed += len(messages)
            print(f"  📩 Marked {processed} messages as read...")

            next_page_token = results.get('nextPageToken')
            if not next_page_token:
                break
        except HttpError as error:
            print(f"❌ Error marking messages as read: {error}")
            break

    print("\n🎉 Gmail cleaning complete! You now have a perfectly clean slate.")

if __name__ == "__main__":
    clean_gmail()
