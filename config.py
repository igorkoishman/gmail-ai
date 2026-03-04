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
    GEMINI_BATCH_SIZE = int(os.getenv('GEMINI_BATCH_SIZE', '10'))

    # Gmail API
    CLIENT_SECRET_PATH = os.getenv('CLIENT_SECRET_PATH', 'client_secret.json')
    TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

    # Browserless (IMAP) Auth
    GMAIL_USER = os.getenv('GMAIL_USER', '')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

    # Application Settings
    DEFAULT_QUERY = os.getenv('DEFAULT_QUERY', 'in:inbox newer_than:365d')
    MAX_THREADS = int(os.getenv('MAX_THREADS', '2000'))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
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
        "Personal/Non-Promotional",
        "People/Family",
        "Finance/Banking",
        "Finance/Investments",
        "Insurance/General",
        "Insurance/Car & Home",
        "Shopping/Amazon",
        "Shopping/eBay",
        "Shopping/AliExpress",
        "Shopping/Delivery Updates",
        "Shopping/Orders & Receipts",
        "Shopping/Promotions & Ads",
        "Security/Alerts",
        "Subscriptions/Services",
        "Work/Professional",
        "Travel/Transportation",
        "Surveys/Feedback",
        "Newsletters/Digests",
        "Home/Utilities",
        "Other/Review",
    ]

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set in .env file")

        # Either OAuth (client_secret.json) or IMAP (GMAIL_APP_PASSWORD) must be provided
        has_oauth = Path(cls.CLIENT_SECRET_PATH).exists() or Path(cls.TOKEN_PATH).exists()
        has_imap = cls.GMAIL_USER and cls.GMAIL_APP_PASSWORD

        if not (has_oauth or has_imap):
            errors.append(
                "Gmail credentials missing. Provide either:\n"
                "  1. OAuth: 'client_secret.json' file (requires browser one-time setup)\n"
                "  2. IMAP: GMAIL_USER and GMAIL_APP_PASSWORD in .env (browserless setup)"
            )

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
