#!/usr/bin/env python3
"""
Simple test script to verify Gmail and Gemini integrations
"""
import os
import ssl
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google import genai

# Load environment
load_dotenv()

print("=" * 60)
print("TESTING INTEGRATIONS")
print("=" * 60)

# Test 1: Check API Key
print("\n1️⃣  Testing Gemini API Key...")
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print(f"   ✅ API Key found: {api_key[:20]}...")
else:
    print("   ❌ No API key found in .env")
    exit(1)

# Test 2: Check Gmail Token
print("\n2️⃣  Testing Gmail Authentication...")
if os.path.exists('token.json'):
    print("   ✅ token.json found")
    try:
        creds = Credentials.from_authorized_user_file('token.json')
        print("   ✅ Credentials loaded")
    except Exception as e:
        print(f"   ❌ Error loading credentials: {e}")
        exit(1)
else:
    print("   ❌ token.json not found. Run: python setup_credentials.py")
    exit(1)

# Test 3: Test Gmail API
print("\n3️⃣  Testing Gmail API connection...")
try:
    # Disable SSL verification for corporate proxy
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp
    http = httplib2.Http(disable_ssl_certificate_validation=True)
    authed_http = AuthorizedHttp(creds, http=http)

    service = build('gmail', 'v1', http=authed_http)
    profile = service.users().getProfile(userId='me').execute()
    print(f"   ✅ Connected to Gmail: {profile.get('emailAddress')}")
    print(f"   📊 Total messages: {profile.get('messagesTotal')}")
except Exception as e:
    print(f"   ❌ Gmail API error: {e}")
    exit(1)

# Test 4: Test Gemini API
print("\n4️⃣  Testing Gemini API connection...")
try:
    # Disable SSL verification for Gemini too
    ssl._create_default_https_context = ssl._create_unverified_context

    client = genai.Client(api_key=api_key)

    # Simple test prompt
    response = client.models.generate_content(
        model='models/gemini-2.5-flash-lite',
        contents='Reply with just: OK'
    )

    result = response.text.strip()
    print(f"   ✅ Gemini API working: {result}")
except Exception as e:
    print(f"   ❌ Gemini API error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nYou can now run: python main.py --disable-ssl-verify")
