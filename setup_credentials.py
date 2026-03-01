#!/usr/bin/env python3
"""
One-time Gmail OAuth setup script
Run this once to authorize the application, then token.json will be reused automatically
"""
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import Config


def setup_gmail_auth(headless=False):
    """
    Perform Gmail OAuth authorization

    Args:
        headless: If True, prints auth URL instead of opening browser
    """
    creds = None

    # Check if token already exists
    if Path(Config.TOKEN_PATH).exists():
        print(f"✅ Token file already exists: {Config.TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(Config.TOKEN_PATH, Config.SCOPES)

        if creds and creds.valid:
            print("✅ Existing credentials are valid!")
            return creds

        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
            with open(Config.TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
            print("✅ Credentials refreshed!")
            return creds

    # Need new authorization
    print(f"🔐 Starting OAuth flow for Gmail API...")
    print(f"   Using client secret: {Config.CLIENT_SECRET_PATH}")

    if not Path(Config.CLIENT_SECRET_PATH).exists():
        raise FileNotFoundError(
            f"Client secret file not found: {Config.CLIENT_SECRET_PATH}\n"
            f"Please download it from Google Cloud Console:\n"
            f"1. Go to: https://console.cloud.google.com/\n"
            f"2. Select your project\n"
            f"3. APIs & Services > Credentials\n"
            f"4. Create OAuth 2.0 Client ID (Desktop app)\n"
            f"5. Download JSON and save as '{Config.CLIENT_SECRET_PATH}'"
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        Config.CLIENT_SECRET_PATH,
        Config.SCOPES
    )

    if headless:
        # For remote/headless servers
        creds = flow.run_console()
    else:
        # For local machines with browser
        creds = flow.run_local_server(port=0)

    # Save credentials
    with open(Config.TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())

    print(f"✅ Credentials saved to: {Config.TOKEN_PATH}")
    print(f"   You won't need to authorize again until token expires!")

    return creds


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup Gmail OAuth credentials")
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Use console-based auth (for remote servers without browser)'
    )
    args = parser.parse_args()

    try:
        setup_gmail_auth(headless=args.headless)
        print("\n✅ Gmail authentication setup complete!")
        print("   You can now run: python main.py")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        exit(1)
