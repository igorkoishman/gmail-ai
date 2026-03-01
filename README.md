# Gmail AI Categorization

Automatically categorize Gmail emails using rule-based logic and Google's Gemini AI.

## Features

- OAuth authentication with Gmail API
- Rule-based categorization for known patterns (family, Synology, insurance, delivery, promotions)
- AI-powered categorization using Gemini for uncertain cases
- Explainable output with confidence scores and reasoning
- Read-only mode (no emails modified)

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Gmail API**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials JSON file
6. Save it as `client_secret.json` in this directory

### 4. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### Basic Run

```bash
python main.py
```

### Custom Parameters

```bash
python main.py \
  --query "in:inbox newer_than:30d" \
  --max-threads 500 \
  --batch 25 \
  --conf 0.8 \
  --out my_results.csv
```

### Parameters

- `--client-secret`: Path to OAuth credentials (default: `client_secret.json`)
- `--token`: Path to token cache (default: `token.json`)
- `--query`: Gmail search query (default: `in:inbox newer_than:365d`)
- `--max-threads`: Number of threads to fetch (default: `1000`)
- `--batch`: Gemini batch size (default: `50`)
- `--model`: Gemini model (default: `models/gemini-2.5-flash-lite`)
- `--conf`: AI confidence threshold (default: `0.75`)
- `--out`: Output CSV filename (default: `gmail_ai_explainable_preview.csv`)

## Categories

- People/Family
- Home/Synology
- Insurance/Car & Home
- Shopping/Delivery Updates
- Shopping/Orders & Receipts
- Shopping/Promotions
- Finance/Banking & Payments
- Security/Alerts
- Subscriptions/Services
- Work/Professional
- Travel/Transportation
- Surveys/Feedback
- Newsletters/Digests
- Other/Review

## Output

The script generates a CSV with:
- Email metadata (subject, from, date, snippet)
- Rule-based categorization (if matched)
- AI categorization (for remaining emails)
- Final decision with confidence score and reasoning

## Next Steps

- Review the output CSV
- Create Gmail filters/labels based on categorization
- Implement auto-labeling with Gmail API (requires write scopes)
