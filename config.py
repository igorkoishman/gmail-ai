#!/usr/bin/env python3
"""
Configuration management using environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""

    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash-lite')

    # Gmail API
    CLIENT_SECRET_PATH = os.getenv('CLIENT_SECRET_PATH', 'client_secret.json')
    TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    # Application Settings
    DEFAULT_QUERY = os.getenv('DEFAULT_QUERY', 'in:inbox newer_than:365d')
    MAX_THREADS = int(os.getenv('MAX_THREADS', '1000'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.75'))
    OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'gmail_ai_results.csv')

    # Email Headers to fetch
    EXTRA_HEADERS = [
        "Subject", "From", "To", "Date",
        "List-Unsubscribe", "Precedence", "Reply-To"
    ]

    # Categories
    REQUIRED_CATEGORIES = [
        "People/Family",
        "Home/Synology",
        "Insurance/Car & Home",
        "Shopping/Delivery Updates",
        "Shopping/Orders & Receipts",
        "Shopping/Promotions",
        "Finance/Banking & Payments",
        "Security/Alerts",
        "Subscriptions/Services",
        "Work/Professional",
        "Travel/Transportation",
        "Surveys/Feedback",
        "Newsletters/Digests",
        "Other/Review",
    ]

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set in .env file")

        if not Path(cls.CLIENT_SECRET_PATH).exists():
            errors.append(f"Gmail credentials file not found: {cls.CLIENT_SECRET_PATH}")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True


if __name__ == "__main__":
    # Test configuration
    try:
        Config.validate()
        print("✅ Configuration is valid!")
        print(f"   Gemini API Key: {Config.GEMINI_API_KEY[:20]}...")
        print(f"   Client Secret: {Config.CLIENT_SECRET_PATH}")
        print(f"   Token Path: {Config.TOKEN_PATH}")
    except ValueError as e:
        print(f"❌ {e}")
