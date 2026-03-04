import os
import joblib
import pandas as pd
import numpy as np
from database_engine import DatabaseEngine
from config import Config

def distill():
    model_dir = "ml_models_pro"
    model_file = os.path.join(model_dir, "pro_classifier.pkl")
    vec_file = os.path.join(model_dir, "pro_vectorizer.pkl")
    enc_file = os.path.join(model_dir, "pro_encoder.pkl")

    if not all(os.path.exists(f) for f in [model_file, vec_file, enc_file]):
        print("❌ Model files not found. Please train the model first.")
        return

    print("🧠 Loading model and data...")
    clf = joblib.load(model_file)
    vec = joblib.load(vec_file)
    enc = joblib.load(enc_file)

    db = DatabaseEngine()
    # Get all labeled data to find sender associations
    data = db.get_training_data()
    df = pd.DataFrame(data)
    
    # We also need threadId and sender for better distillation
    conn = db._get_connection()
    raw_df = pd.read_sql("SELECT sender, full_text, COALESCE(manual_category, ai_category) as category FROM emails WHERE manual_category IS NOT NULL OR ai_category IS NOT NULL", conn)
    conn.close()

    categories = enc.classes_
    feature_names = vec.get_feature_names_out()

    # --- SENDER RULES ---
    print("📧 Extracting sender-based rules...")
    sender_rules = {}
    for cat in categories:
        cat_senders = raw_df[raw_df['category'] == cat]['sender'].value_counts()
        # Keep senders that appear at least 3 times and are > 80% associated with this category
        top_senders = []
        for sender, count in cat_senders.items():
            if count >= 3:
                total_sender_count = raw_df[raw_df['sender'] == sender].shape[0]
                if count / total_sender_count > 0.8:
                    top_senders.append(sender)
        sender_rules[cat] = top_senders[:20] # Limit to top 20 senders per category

    # --- KEYWORD RULES (Feature Importance) ---
    print("🔑 Extracting keyword-based rules...")
    keyword_rules = {}
    # For RandomForest, we can't easily get per-class importance like LogReg, 
    # but we can look at the average feature contribution or just use the global importance 
    # and check correlation with classes
    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    top_k = 500 # Look at top 500 global features
    top_features = [feature_names[i] for i in indices[:top_k]]
    
    # Filter features for each category
    for cat in categories:
        cat_keywords = []
        # Simple heuristic: what top words appear most in this category vs others
        # (This is a simplified distillation)
        cat_texts = raw_df[raw_df['category'] == cat]['full_text'].astype(str).str.lower()
        other_texts = raw_df[raw_df['category'] != cat]['full_text'].astype(str).str.lower()
        
        for word in top_features:
            cat_count = cat_texts.str.contains(word, regex=False).sum()
            if cat_count > 5:
                other_count = other_texts.str.contains(word, regex=False).sum()
                # If word is 3x more likely in this category
                if cat_count > (other_count * 3):
                    cat_keywords.append(word)
        
        keyword_rules[cat] = cat_keywords[:30] # Limit to top 30 keywords per category

    # --- GENERATE APPS SCRIPT ---
    print("📝 Generating Google Apps Script...")
    
    js_code = """
/**
 * STUPID SCRIPT: Distilled Rules from Gmail-AI
 * Paste this into Google Apps Script (script.google.com)
 */

function classifyIncomingEmails() {
  var threads = GmailApp.search('in:inbox is:unread', 0, 50);
  for (var i = 0; i < threads.length; i++) {
    var thread = threads[i];
    var message = thread.getMessages()[0];
    var sender = message.getFrom().toLowerCase();
    var subject = message.getSubject().toLowerCase();
    var body = message.getPlainBody().toLowerCase();
    
    var category = determineCategory(sender, subject, body);
    if (category) {
      applyLabel(thread, category);
    }
  }
}

function determineCategory(sender, subject, body) {
"""

    # Add Sender Rules
    for cat, senders in sender_rules.items():
        if not senders: continue
    # Add Sender Rules
    for cat, senders in sender_rules.items():
        if not senders: continue
        checks = []
        for s in senders:
            if not s: continue
            # Escape double quotes and remove newlines for Javascript
            safe_s = s.lower().replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            checks.append(f'sender.includes("{safe_s}")')
        sender_checks = " || ".join(checks)
        if sender_checks:
            js_code += f'  if ({sender_checks}) return "{cat}";\n'

    # Add Keyword Rules
    for cat, keywords in keyword_rules.items():
        if not keywords: continue
        # Filter out short or problematic keywords
        clean_keywords = [k for k in keywords if len(k) > 3]
        if not clean_keywords: continue
        
        checks = []
        for k in clean_keywords:
            # Escape double quotes and remove newlines for Javascript
            safe_k = k.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            checks.append(f'body.includes("{safe_k}")')
        keyword_checks = " || ".join(checks)
        if keyword_checks:
            js_code += f'  if ({keyword_checks}) return "{cat}";\n'

    js_code += """
  return null;
}

function applyLabel(thread, category) {
  var labelName = "AI/" + category;
  var label = GmailApp.getUserLabelByName(labelName);
  if (!label) {
    label = GmailApp.createLabel(labelName);
  }
  thread.addLabel(label);
  thread.markRead(); // Optional: remove if you want to keep as unread
  console.log("Categorized: " + thread.getFirstMessageSubject() + " as " + category);
}
"""

    output_file = "generated_rules.gs"
    with open(output_file, "w") as f:
        f.write(js_code)
    
    print(f"✅ Success! Distilled rules saved to {output_file}")
    print("👉 You can now copy the contents of this file to Google Apps Script.")

if __name__ == "__main__":
    distill()
