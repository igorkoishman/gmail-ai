import argparse
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.gmail import GmailEngine
from src.core.database import DatabaseEngine

def fetch_custom_emails(query: str, limit: int):
    print(f"🚀 [FETCH CUSTOM] Searching Gmail for: '{query}' (Max {limit} emails)")
    
    try:
        gmail = GmailEngine()
        db = DatabaseEngine()
    except Exception as e:
        print(f"❌ Error initializing engines: {e}")
        return
    
    # 1. Fetch emails using custom query
    emails = gmail.fetch_new_emails(max_results=limit, query=query)
    
    if not emails:
        print("📭 No emails found matching the query.")
        return
        
    print(f"✅ Found {len(emails)} emails. Saving to database...")
    
    # 2. Save emails to DB
    try:
        db.save_emails(emails)
        print("🎉 Successfully saved emails to the database!")
        print("\nNext steps to update your model:")
        print("1. Run `python main.py --teach` to have Gemini assign initial categories.")
        print("   (Or manually categorize them via your database UI at http://localhost:8080)")
        print("2. Run `python main.py --train` to retrain your local model with the new data + old data.")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch specific batch of emails from Gmail")
    parser.add_argument("--query", type=str, required=True, help="Gmail search query (e.g. 'from:boss@company.com' or 'after:2024-01-01')")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of emails to download")
    
    args = parser.parse_args()
    fetch_custom_emails(args.query, args.limit)
