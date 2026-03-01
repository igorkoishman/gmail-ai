#!/usr/bin/env python3
import os
import re
import json
import time
import argparse
import ssl
import certifi
import httplib2
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from config import Config

# CRITICAL: Must patch SSL BEFORE importing genai
# genai imports httpx which creates SSL contexts at import time
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
import warnings
warnings.filterwarnings('ignore')

# NOW import genai after SSL is patched
from google import genai


# -------------------------
# Helpers: OAuth + Gmail
# -------------------------
def gmail_service(disable_ssl_verify=False) -> Any:
    """Get authenticated Gmail service using config"""
    creds = None
    if os.path.exists(Config.TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(Config.TOKEN_PATH, Config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("❌ No valid credentials found!")
            print("   Run: python setup_credentials.py")
            raise SystemExit("Authentication required. Run setup_credentials.py first.")

        with open(Config.TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    # Build service with optional SSL verification disable
    if disable_ssl_verify:
        # Create custom HTTP with SSL verification disabled
        from google_auth_httplib2 import AuthorizedHttp
        http = httplib2.Http(disable_ssl_certificate_validation=True)
        authed_http = AuthorizedHttp(creds, http=http)
        return build("gmail", "v1", http=authed_http)
    else:
        return build("gmail", "v1", credentials=creds)


def list_threads_all(service: Any, query: str, max_results: int) -> List[Dict[str, Any]]:
    threads: List[Dict[str, Any]] = []
    page_token = None
    while len(threads) < max_results:
        res = service.users().threads().list(
            userId="me",
            q=query,
            maxResults=min(500, max_results - len(threads)),
            pageToken=page_token
        ).execute()
        threads.extend(res.get("threads", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return threads


def get_thread_metadata(service: Any, thread_id: str) -> Dict[str, Any]:
    t = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="metadata",
        metadataHeaders=Config.EXTRA_HEADERS
    ).execute()

    msg = t["messages"][0]
    hdrs = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

    return {
        "threadId": thread_id,
        "subject": hdrs.get("subject", ""),
        "from": hdrs.get("from", ""),
        "date": hdrs.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "list_unsubscribe": hdrs.get("list-unsubscribe", ""),
        "precedence": hdrs.get("precedence", ""),
        "reply_to": hdrs.get("reply-to", ""),
    }


# -------------------------
# Helpers: Gemini JSON parsing
# -------------------------
def extract_json(text: str) -> Any:
    if text is None:
        raise ValueError("Model returned None")
    t = text.strip()
    if not t:
        raise ValueError("Model returned empty text")

    # Strip code fences
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)

    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass

    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", t)
    if not m:
        raise ValueError("Could not find JSON in model output")

    return json.loads(m.group(1))


def gemini_json(client: genai.Client, model: str, prompt: str, max_retries: int = 1) -> Any:
    resp = client.models.generate_content(model=model, contents=prompt)
    raw = (resp.text or "")

    try:
        return extract_json(raw)
    except Exception:
        if max_retries <= 0:
            raise
        retry_prompt = prompt + "\n\nIMPORTANT: Output ONLY valid JSON. No markdown. No backticks. No commentary."
        resp2 = client.models.generate_content(model=model, contents=retry_prompt)
        raw2 = (resp2.text or "")
        return extract_json(raw2)


# -------------------------
# Rules
# -------------------------
FAMILY_SENDERS = [
    "alex koishman",
    "vladislav koishman",
    "marina@0020",
]

SYNLOGY_HINTS = [
    "synology",
    "active insight",
    "hyper backup",
    "quickconnect",
]

INSURANCE_HINTS = [
    "aig",
    "bituah yashir",
    "ביטוח ישיר",
]

CARRIERS_HINTS = [
    "dhl",
    "israel post",
    "דואר ישראל",
]

DELIVERY_KEYWORDS = [
    "tracking", "track", "shipment", "shipped", "out for delivery", "delivered",
    "customs", "clearance", "parcel", "waybill",
    "מעקב", "מספר מעקב", "משלוח", "חבילה", "דואר"
]

PROMO_KEYWORDS = [
    "discount", "sale", "deal", "coupon", "% off", "special offer",
    "unsubscribe",  # strong signal
    "הנחה", "מבצע", "קופון"
]

def norm(s: str) -> str:
    return (s or "").lower()

def rule_engine(row: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    fr = norm(row.get("from", ""))
    subj = norm(row.get("subject", ""))
    snip = norm(row.get("snippet", ""))
    lu = norm(row.get("list_unsubscribe", ""))
    prec = norm(row.get("precedence", ""))
    text = " ".join([fr, subj, snip, lu, prec])

    if any(x in text for x in [x.lower() for x in FAMILY_SENDERS]):
        return "People/Family", "family sender match"

    if any(x in text for x in [x.lower() for x in SYNLOGY_HINTS]):
        return "Home/Synology", "synology keyword match"

    if any(x.lower() in text for x in INSURANCE_HINTS):
        return "Insurance/Car & Home", "insurance keyword match"

    has_delivery_kw = any(k in text for k in [k.lower() for k in DELIVERY_KEYWORDS])
    has_carrier = any(c in text for c in [c.lower() for c in CARRIERS_HINTS])
    has_promo_kw = any(k in text for k in [k.lower() for k in PROMO_KEYWORDS])

    # Delivery should win over promotions when tracking exists
    if has_carrier or has_delivery_kw:
        return "Shopping/Delivery Updates", "tracking/carrier/shipping update"

    # Newsletter/promo signals
    if lu or ("bulk" in prec) or ("list" in prec) or has_promo_kw:
        return "Shopping/Promotions", "marketing/newsletter signal"

    return None, None


# -------------------------
# Classification
# -------------------------
def batch_iter(lst: List[Dict[str, Any]], n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


def classify_batch(client: genai.Client, model: str, payload: List[Dict[str, Any]]) -> pd.DataFrame:
    prompt = f"""
Classify each email into ONE category from this list:
{Config.REQUIRED_CATEGORIES}

Return ONLY valid JSON:
{{
  "results": [
    {{"threadId":"string", "category":"string", "confidence":0.0, "reason":"max 12 words"}}
  ]
}}

Notes:
- Delivery Updates = tracking/shipping/status changes (not discounts)
- Promotions = discounts, marketing, newsletters (often list_unsubscribe present)
- Synology/Insurance/Family may be handled by rules

Emails:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

    data = gemini_json(client, model, prompt, max_retries=1)
    df = pd.DataFrame(data["results"])
    df = df.rename(columns={"category":"ai_category","confidence":"ai_confidence","reason":"ai_reason"})
    return df


def decide_final(row: pd.Series, conf_threshold: float) -> Tuple[str, str, float, str]:
    if isinstance(row.get("rule_category"), str) and row["rule_category"]:
        return ("rule", row["rule_category"], 1.0, row.get("rule_reason") or "rule match")

    ai_conf = row.get("ai_confidence")
    if pd.notna(ai_conf) and float(ai_conf) >= conf_threshold:
        return ("ai", row.get("ai_category", "Other/Review"), float(ai_conf), row.get("ai_reason") or "ai")

    return ("review", "Other/Review", float(ai_conf or 0.0), "low confidence / no rule")


# -------------------------
# Main
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Gmail AI sorting preview (read-only) -> explainable CSV")
    parser.add_argument("--query", default=None, help=f"Gmail search query (default: {Config.DEFAULT_QUERY})")
    parser.add_argument("--max-threads", type=int, default=None, help=f"Number of threads to sample (default: {Config.MAX_THREADS})")
    parser.add_argument("--batch", type=int, default=None, help=f"Gemini batch size (default: {Config.BATCH_SIZE})")
    parser.add_argument("--model", default=None, help=f"Gemini model (default: {Config.GEMINI_MODEL})")
    parser.add_argument("--conf", type=float, default=None, help=f"Confidence threshold (default: {Config.CONFIDENCE_THRESHOLD})")
    parser.add_argument("--out", default=None, help=f"Output CSV filename (default: {Config.OUTPUT_FILE})")
    parser.add_argument("--disable-ssl-verify", action='store_true', help="Disable SSL verification (not recommended, use only if you have corporate proxy issues)")
    args = parser.parse_args()

    # Use config defaults if not provided
    query = args.query or Config.DEFAULT_QUERY
    max_threads = args.max_threads or Config.MAX_THREADS
    batch_size = args.batch or Config.BATCH_SIZE
    model = args.model or Config.GEMINI_MODEL
    conf_threshold = args.conf or Config.CONFIDENCE_THRESHOLD
    output_file = args.out or Config.OUTPUT_FILE

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error:\n{e}")
        print("\nMake sure you have:")
        print("1. Created .env file with GEMINI_API_KEY")
        print("2. Downloaded client_secret.json from Google Cloud Console")
        print("3. Run: python setup_credentials.py")
        raise SystemExit(1)

    # Always use SSL disabled for corporate proxy compatibility
    print("🔑 Using Gemini API Key from config")
    print("📧 Connecting to Gmail...")
    service = gmail_service(disable_ssl_verify=True)

    print(f"📬 Fetching up to {max_threads} threads with query: {query}")
    threads = list_threads_all(service, query, max_threads)
    print(f"✅ Threads fetched: {len(threads)}")

    print("📝 Fetching thread metadata (this may take a bit)...")
    rows = []
    for idx, th in enumerate(threads, 1):
        try:
            rows.append(get_thread_metadata(service, th["id"]))
        except HttpError as e:
            print(f"⚠️  Gmail error on thread {th['id']}: {e}")
        if idx % 100 == 0:
            print(f"   ... fetched {idx}/{len(threads)}")

    df = pd.DataFrame(rows)
    print(f"✅ Metadata rows: {len(df)}")

    # Apply rules
    print("🔍 Applying rule-based classification...")
    rule_pairs = df.apply(lambda r: rule_engine(r.to_dict()), axis=1, result_type="expand")
    rule_pairs.columns = ["rule_category", "rule_reason"]
    df = pd.concat([df, rule_pairs], axis=1)

    # Gemini for leftovers
    to_ai = df[df["rule_category"].isna() | (df["rule_category"]=="")].copy()
    print(f"🤖 Rows needing AI classification: {len(to_ai)}")

    # CRITICAL: Set SSL context immediately before creating Gemini client
    # genai.Client creates its httpx client when instantiated, so we must set this first
    ssl._create_default_https_context = ssl._create_unverified_context
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    ai_frames = []
    payload_all = to_ai[["threadId","from","subject","snippet","list_unsubscribe","precedence","reply_to"]].to_dict(orient="records")

    total_batches = (len(payload_all) + batch_size - 1) // batch_size
    for batch_idx, batch in enumerate(batch_iter(payload_all, batch_size), 1):
        print(f"   ... processing batch {batch_idx}/{total_batches}")
        ai_frames.append(classify_batch(client, model, batch))
        time.sleep(0.2)

    ai_df = pd.concat(ai_frames, ignore_index=True) if ai_frames else pd.DataFrame(columns=["threadId","ai_category","ai_confidence","ai_reason"])
    merged = df.merge(ai_df, on="threadId", how="left")

    # Final decision
    print("🎯 Making final category decisions...")
    final = merged.apply(lambda r: decide_final(r, conf_threshold), axis=1, result_type="expand")
    final.columns = ["decision_source","final_category","final_confidence","final_reason"]
    merged = pd.concat([merged, final], axis=1)

    merged.to_csv(output_file, index=False)
    print(f"\n✅ Results written to: {output_file}")
    print(f"\n📊 Top categories:")
    print(merged["final_category"].value_counts().head(15).to_string())

    # Summary stats
    print(f"\n📈 Classification Summary:")
    print(f"   Total emails: {len(merged)}")
    print(f"   Rule-based: {len(merged[merged['decision_source'] == 'rule'])}")
    print(f"   AI-based: {len(merged[merged['decision_source'] == 'ai'])}")
    print(f"   Needs review: {len(merged[merged['decision_source'] == 'review'])}")


if __name__ == "__main__":
    main()