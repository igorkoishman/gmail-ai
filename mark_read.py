import sys
import os
import time
from googleapiclient.errors import HttpError

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.core.gmail import GmailEngine

def mark_all_as_read():
    print("🧹 [MARK AS READ] Starting a deep clean of your inbox...")
    gmail = GmailEngine()
    
    query = "is:unread"
    total_marked = 0
    
    while True:
        try:
            # Fetch batch of unread threads
            results = gmail.service.users().threads().list(userId='me', q=query, maxResults=100).execute()
            threads = results.get('threads', [])
            
            if not threads:
                break

            print(f"📖 Found {len(threads)} unread threads in this batch. Processing...")
            
            for thread in threads:
                try:
                    body = {'removeLabelIds': ['UNREAD']}
                    gmail.service.users().threads().modify(userId='me', id=thread['id'], body=body).execute()
                    total_marked += 1
                except HttpError as error:
                    # If it's already read or changed, just continue
                    continue
            
            print(f"✅ Total marked so far: {total_marked}")
            # Brief sleep to respect rate limits
            time.sleep(1)
            
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            break
    
    print(f"\n🎉 Finished! Successfully marked {total_marked} threads as read.")

if __name__ == "__main__":
    mark_all_as_read()
