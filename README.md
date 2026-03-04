# Gmail AI Pro Categorization

Automatically categorize Gmail emails using a hybrid approach of Google's Gemini AI (for teaching) and a secure, offline Machine Learning "Pro Brain" (for high-speed, cost-free daily execution).

## Key Features

1. **Human-in-the-Loop ML**: You teach Gemini on a small sample, manually correct any mistakes, and then a blazing fast Random Forest model learns *your* exact preferences.
2. **Offline Privacy**: Once trained, the ML model runs entirely on your local machine—no emails are sent to external APIs for daily labeling.
3. **Dual Automation Options**:
    - **Dockerized Background Service**: Runs continuously on a Linux server, fetching and applying labels every 10 minutes.
    - **"The Stupid Script" (Apps Script)**: Extracts your ML model's logic into a massive Javascript file that runs 100% free and native inside Gmail's cloud.

---

## 🏗️ Architecture

1. **`main_pro.py`**: The core orchestrator. Handles Teaching, Training, Predicting, and running the background Daemon.
2. **`database_engine.py`**: Manages the local MySQL database (stores email history, predictions, and manual overrides).
3. **`gmail_engine.py`**: Interacts directly with the Gmail API to list unread messages and apply label categorizations.
4. **`distill_rules.py`**: Extracts the most important keywords and senders from the ML model to generate a standalone Google Apps Script.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9+
- Docker & Docker Compose (for the database and service)
- A Google Cloud Project with the Gmail API enabled (Requires `modify` scope).

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_key_here
```
Place your `client_secret.json` from Google Cloud in the root directory.

### 3. Setup Credentials & Database
```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the MySQL Database
docker-compose up db adminer -d

# Authenticate with Google (This will open a browser window)
python setup_credentials.py
```

---

## 🧠 Workflows: How to Use

### Phase 1: Teaching & Training
Populate your database and train your unique ML model.
```bash
# 1. Ask Gemini to label a batch of emails to bootstrap the system
python main_pro.py --teach

# 2. Train your offline "Pro Brain" on those labels (and any manual overrides you made in the DB)
python main_pro.py --train

# 3. Apply the offline model to the rest of your database history
python main_pro.py --predict
```

### Phase 2: Live Automation
Choose **one** of the two automation methods below:

#### Option A: Dockerized Background Service (Recommended for Linux Servers)
Runs a continuous Python daemon that syncs with Gmail every 10 minutes. 
👉 **[Read the Linux Deployment Guide](.gemini/linux_deployment_guide.md)** for detailed instructions.
```bash
# Deploys the service alongside the database using docker-compose
docker-compose up -d
```

#### Option B: Google Apps Script ("The Stupid Script")
If you don't want to run a server 24/7, you can export your ML model's logic into a script that runs natively inside Gmail.
👉 **[Read the Apps Script Automation Guide](.gemini/apps_script_automation_guide.md)**.
```bash
# Generates a 'generated_rules.gs' file based on your trained model
python distill_rules.py
```

---

## 📚 Detailed Documentation
During development, the AI assistant recorded detailed walkthroughs, plans, and instructions. You can find all of these in the `.gemini/` directory:
- [Project Summary & Logs](.gemini/project_summary.md)
- [Linux Deployment Guide](.gemini/linux_deployment_guide.md)
- [Apps Script Automation Guide](.gemini/apps_script_automation_guide.md)
