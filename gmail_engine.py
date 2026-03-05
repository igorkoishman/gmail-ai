import base64
import os
import re
import html
from datetime import datetime
from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config

class GmailEngine:
    def __init__(self):
        if not os.path.exists(Config.TOKEN_PATH):
            raise FileNotFoundError(f"Missing {Config.TOKEN_PATH}. Please run setup_credentials.py")
        
        self.creds = Credentials.from_authorized_user_file(Config.TOKEN_PATH, Config.SCOPES)
        self.service = build('gmail', 'v1', credentials=self.creds)
        self._label_cache = {}
        self._init_labels()

    def _init_labels(self):
        """Fetch all existing labels to cache their IDs."""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            for label in labels:
                self._label_cache[label['name']] = label['id']
        except HttpError as error:
            print(f"An error occurred fetching labels: {error}")

    def get_or_create_label(self, category_name: str) -> str:
        """Get the Gmail Label ID for a category, creating it if it doesn't exist."""
        label_name = category_name
        
        if label_name in self._label_cache:
            return self._label_cache[label_name]
            
        try:
            print(f"Creating new Gmail label: {label_name}")
            label_body = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            new_label = self.service.users().labels().create(userId='me', body=label_body).execute()
            self._label_cache[label_name] = new_label['id']
            return new_label['id']
        except HttpError as error:
            print(f"Error creating label {label_name}: {error}")
            return None

    def apply_label_to_thread(self, thread_id: str, category_name: str):
        """Apply a category label to a specific thread."""
        label_id = self.get_or_create_label(category_name)
        if not label_id:
            return False
            
        try:
            body = {
                'addLabelIds': [label_id],
                # 'removeLabelIds': ['UNREAD'] # Optional: remove inbox/unread if desired
            }
            self.service.users().threads().modify(userId='me', id=thread_id, body=body).execute()
            return True
        except HttpError as error:
            print(f"Error applying label to thread {thread_id}: {error}")
            return False

    def _get_body(self, payload):
        """Recursively extract text from email payload, preferring plain text."""
        parts_to_process = []
        if 'parts' in payload:
            parts_to_process = payload['parts']
        else:
            # Single part message
            parts_to_process = [payload]

        plain_text_parts = []
        html_parts = []

        def collect_parts(parts):
            for part in parts:
                mime = part.get('mimeType', '')
                if mime == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        plain_text_parts.append(base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'))
                elif mime == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        html_parts.append(base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore'))
                elif 'parts' in part:
                    collect_parts(part['parts'])

        collect_parts(parts_to_process)

        if plain_text_parts:
            return "\n".join(plain_text_parts)
        
        if html_parts:
            # Strip tags from all HTML parts and join them
            full_html = "\n".join(html_parts)
            # Use a slightly better regex or just strip tags
            text = re.sub('<[^<]+?>', ' ', full_html)
            text = html.unescape(text)
            return " ".join(text.split())

        return ""

    def fetch_new_emails(self, max_results=50, query="in:inbox is:unread"):
        """Fetch new emails matching the query and parse them for the database."""
        try:
            results = self.service.users().threads().list(userId='me', q=query, maxResults=max_results).execute()
            threads = results.get('threads', [])
            
            if not threads:
                return []
                
            parsed_emails = []
            print(f"📥 Fetching {len(threads)} new threads from Gmail...")
            
            for thread in threads:
                try:
                    t_data = self.service.users().threads().get(userId='me', id=thread['id'], format='full').execute()
                    # Just grab the first message in the thread for categorization
                    msg = t_data['messages'][0]
                    
                    headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
                    
                    # Core metadata
                    subject = headers.get('subject', 'No Subject')
                    sender = headers.get('from', 'Unknown Sender')
                    date_str = headers.get('date', '')
                    
                    try:
                        date_obj = parsedate_to_datetime(date_str)
                    except:
                        date_obj = datetime.now()
                        
                    # Improved recursive body parsing
                    body_data = self._get_body(msg['payload'])
                        
                    snippet = msg.get('snippet', '')
                    full_text = f"Subject: {subject}\nSender: {sender}\n\n{body_data}"
                    
                    parsed_emails.append({
                        'threadId': thread['id'],
                        'sender': sender,
                        'subject': subject,
                        'date': date_obj.strftime('%Y-%m-%d %H:%M:%S'),
                        'snippet': snippet,
                        'full_text': full_text,
                        'raw_body': body_data
                    })
                except Exception as e:
                    print(f"Error parsing thread {thread['id']}: {e}")
                    continue
                    
            return parsed_emails
            
        except HttpError as error:
            print(f"An error occurred fetching emails: {error}")
            return []
