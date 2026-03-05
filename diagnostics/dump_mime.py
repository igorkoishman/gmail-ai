import base64
import json
from gmail_engine import GmailEngine

gmail = GmailEngine()
thread_id = '19c9e7718323c17b'

def dump_parts(parts, indent=0):
    for i, part in enumerate(parts):
        mime = part.get('mimeType', 'unknown')
        body = part.get('body', {})
        data_size = len(body.get('data', ''))
        attach_id = body.get('attachmentId', 'None')
        print("  " * indent + f"Part {i}: {mime} [Data: {data_size} bytes, AttachID: {attach_id}]")
        if 'parts' in part:
            dump_parts(part['parts'], indent + 1)

try:
    t_data = gmail.service.users().threads().get(userId='me', id=thread_id, format='full').execute()
    msg = t_data['messages'][0]
    payload = msg['payload']
    
    print(f"Thread: {thread_id}")
    print(f"Main MimeType: {payload['mimeType']}")
    if 'parts' in payload:
        dump_parts(payload['parts'])
    else:
        print("No parts in payload.")

except Exception as e:
    print(f"Error: {e}")
