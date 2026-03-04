# How to Automate Your Gmail with "The Stupid Script"

I have successfully distilled your ML model's logic into a single Javascript file: [generated_rules.gs](file:///Users/igorkoishman/PycharmProjects/gmail-ai/generated_rules.gs).

This script will run **24/7 in Google's cloud**, automatically labeling new emails as they arrive, without needing your computer to be on.

## Steps to Setup

### 1. Open Google Apps Script
1.  Go to [script.google.com](https://script.google.com/).
2.  Click **"New Project"**.

### 2. Paste the Rules
1.  Open [generated_rules.gs](file:///Users/igorkoishman/PycharmProjects/gmail-ai/generated_rules.gs) on your computer.
2.  **Copy all the text** inside that file.
3.  In the Apps Script editor, delete any existing code and **Paste** your rules there.
4.  Click the **Save** icon (💾) and name the project "Gmail AI Classifier".

### 3. Test Run
1.  In the Apps Script editor, make sure `classifyIncomingEmails` is selected in the toolbar.
2.  Click **"Run"**.
3.  Google will ask for permissions. Click **"Review Permissions"**, select your account, then click **"Advanced"** > **"Go to Gmail AI Classifier (unsafe)"** > **"Allow"**.
4.  Check your Gmail! You should see new labels starting with `AI/` appearing on your unread emails.

### 4. Set it to Run Automatically (The Magic Part)
1.  On the left sidebar, click the **Triggers** icon (⏰).
2.  Click **"+ Add Trigger"** (bottom right).
3.  Set the following:
    -   **Function to run**: `classifyIncomingEmails`
    -   **Event source**: `Time-driven`
    -   **Type of time based trigger**: `Minutes timer`
    -   **Select minute interval**: `Every 10 minutes` (or `Every minute` for instant results).
4.  Click **Save**.

---

## What to expect
-   Every time the trigger runs, it scans your **Inbox** for **Unread** emails.
-   It checks the Sender and Keywords against the thousands of rules we distilled.
-   If it matches, it applies a label like `AI/Finance` or `AI/AliExpress`.
-   It works entirely in the cloud—you can turn off your laptop and it will keep labeling!

## How to Update
If you train your model again in the future and want to update these rules:
1.  Run `python distill_rules.py` again.
2.  Copy the new `generated_rules.gs` and paste it over the old code in script.google.com.
