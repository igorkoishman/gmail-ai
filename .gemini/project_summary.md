# Gmail AI Project Summary

This project is a sophisticated email categorization system that combines Google's Gemini AI with local Machine Learning (Random Forest) to classify Gmail messages into predefined categories.

## Architecture & Components

### 1. Configuration (`config.py`)
- **Environment Driven**: Uses `.env` for API keys, database credentials, and model settings.
- **Predefined Categories**: 22 categories spanning Personal, Finance, Shopping, Work, etc.
- **Flexible Auth**: Supports both OAuth (client secret/token) and IMAP (App Passwords).

### 2. Database Management (`database_engine.py`)
- **MySQL Backend**: Stores emails in an `emails` table including full text, snippets, and classification results.
- **Smart Upsert**: Avoids duplicates by using `threadId` as a unique key.
- **Indexing**: Optimized for performance on `manual_category` and `ai_category` lookups.

### 3. AI Classification Engine (`ai_engine.py`)
- **Gemini Integration**: Interfaces with Google's GenAI API (flash-lite model by default).
- **Robust Parsing**: Advanced regex-based JSON extraction to handle LLM response variations.
- **Batch Processing**: Configurable batch sizes to minimize API calls and handle rate limits.

### 4. Professional Classifier (`main_pro.py`)
The orchestrator of the two-stage classification workflow:
- **Phase 1: Gemini Teaching**: Fetches a target number of emails (default 2000) and uses Gemini to generate high-quality labels.
- **Phase 2: Local Training**: Trains a local `RandomForestClassifier` using `TfidfVectorizer` on the data labeled by Gemini and any manual labels provided by the user.
- **Phase 3: Bulk Prediction**: Applies the local model to all remaining uncategorized emails for efficient, offline classification of the entire database.

### 5. Data Ingestion (`mbox_engine.py`, `import_from_mbox.py`)
- Supports importing legacy email data from MBOX files directly into the MySQL database.

## Typical Workflow

1.  **Ingestion**: Import emails via Gmail API or MBOX file.
2.  **Gemini Bootstrapping**: Run `python main_pro.py --teach` to get the first 2000 emails classified by AI.
3.  **Human Feedback**: (Optional) Manually review and correct categories in the database (e.g., via Adminer).
4.  **Local Training**: Run `python main_pro.py --train` to build the local "brain" from manual and AI labels.
5.  **Offline Prediction**: The system uses the local brain to categorize the rest of your inbox without further API costs.

## Technical Stack
- **Languages**: Python
- **AI**: Google Gemini API
- **ML**: Scikit-learn (Random Forest, TF-IDF)
- **Database**: MySQL (Docker-ready)
- **Data Tools**: Pandas, Joblib
