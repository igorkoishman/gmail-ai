import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.core.gmail import GmailEngine

def delete_obsolete_label():
    gmail = GmailEngine()
    label_name = "Ali express ad"
    
    if label_name in gmail._label_cache:
        label_id = gmail._label_cache[label_name]
        try:
            gmail.service.users().labels().delete(userId='me', id=label_id).execute()
            print(f"✅ Successfully deleted the '{label_name}' label from your Gmail account entirely!")
        except Exception as e:
            print(f"❌ Error deleting label: {e}")
    else:
        print(f"📭 The label '{label_name}' doesn't exist in your Gmail account anymore.")

if __name__ == "__main__":
    delete_obsolete_label()
