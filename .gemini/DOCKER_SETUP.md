# Deploying Gmail AI on a Clean Machine

Follow these steps to set up the entire classification stack on a new computer using Docker.

## Prerequisites
1.  **Google Cloud Console**:
    - Enable Gmail API.
    - Create OAuth 2.0 Client ID (Desktop App).
    - Download `client_secret.json` and place it in the project root.
2.  **Gemini API Key**:
    - Get a key from [Google AI Studio](https://aistudio.google.com/).

## 1. Environment Setup

```bash
# Clone the repository
git clone git@github.com:igorkoishman/gmail-ai.git
cd gmail-ai

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

## 2. Infrastructure (Database)

```bash
# Start MySQL and Adminer
docker-compose up -d db adminer
```
- **MySQL**: `localhost:3306` (User: `root`, Pass: `password`)
- **Adminer**: `http://localhost:8080`

## 3. Local Python Setup (One-time)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Authenticate with Gmail (Opens browser)
python scripts/setup_credentials.py
```

## 4. Bootstrapping the "Pro Brain"

Before running the background service, you must train the local model:

```bash
# 1. Ask Gemini to label your first 2000 emails
python main.py --teach

# 2. Train the local offline model
python main.py --train

# 3. Verify locally
python main.py --predict
```

## 5. Dockerized Service Deployment

Once the `ml_models_pro/` directory is populated with your trained models, you can run the classification service inside Docker:

```bash
# Start the background service
docker-compose up -d gmail-ai
```

The service will now check for new emails and update your Gmail labels automatically every 24 hours.
