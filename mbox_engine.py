import mailbox
import email
import re
from typing import List, Dict, Any

def _decode_safe(header_value: str) -> str:
    """Safely decodes email headers."""
    try:
        decoded_parts = email.header.decode_header(header_value)
        return "".join(part.decode(charset or "utf-8", "ignore") if isinstance(part, bytes) else part for part, charset in decoded_parts)
    except Exception:
        return str(header_value)

def _get_body(msg: email.message.Message) -> (str, str):
    """Extracts text and HTML bodies from an email message."""
    text_body, html_body = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            if "attachment" in str(part.get("Content-Disposition")):
                continue
            try:
                payload = part.get_payload(decode=True).decode('utf-8', 'ignore')
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    text_body += payload
                elif content_type == "text/html":
                    html_body += payload
            except Exception:
                continue
    else:
        try:
            payload = msg.get_payload(decode=True).decode('utf-8', 'ignore')
            if msg.get_content_type() == "text/plain":
                text_body = payload
            else:
                html_body = payload
        except Exception:
            pass
    return text_body, html_body

def parse_mbox(mbox_path: str) -> List[Dict[str, Any]]:
    """
    Parses an Mbox file and returns a list of email dictionaries.
    """
    print(f"📦 Opening Mbox file at: {mbox_path}")
    mbox = mailbox.mbox(mbox_path)
    emails = []

    for i, message in enumerate(mbox):
        try:
            # --- Use Message-ID as the primary unique identifier ---
            thread_id = message['Message-ID']
            if not thread_id:
                print(f"   - Warning: Skipping message {i} due to missing Message-ID.")
                continue

            subject = _decode_safe(message['Subject'])
            sender = _decode_safe(message['From'])
            date_str = message['Date']
            dt_object = parsedate_to_datetime(date_str) if date_str else None

            text_body, html_body = _get_body(message)
            
            # Prefer HTML body for more content, fallback to text.
            content = html_body if html_body else text_body
            clean_text = re.sub(r'<[^>]+>', ' ', content)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            emails.append({
                "threadId": thread_id,
                "subject": subject,
                "sender": sender,
                "date": dt_object,
                "snippet": clean_text[:250],
                "full_text": clean_text[:30000],
                "raw_body": html_body[:50000]
            })
        except Exception as e:
            print(f"   - Error processing message {i}: {e}")
            continue
            
    print(f"✅ Mbox parsing complete. Found {len(emails)} valid emails.")
    return emails
