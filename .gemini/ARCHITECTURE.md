# Architecture: The "Pro Brain"

Gmail AI is built on a modular, two-stage classification architecture.

## 🏗️ Components

### 1. Core Engines (`src/core/`)
- **`gmail.py`**: High-level Gmail API wrapper. Handles thread fetching and label application.
- **`database.py`**: MySQL manager. Handles persistent storage and deduplication.
- **`ai_gemini.py`**: Gemini API interface. Optimized for batch-labeling history.
- **`config.py`**: Centralized configuration and category definitions.

### 2. ML Subsystem (`src/ml/`)
- **`trainer.py`**: Bridge between Gemini labels and the local Scikit-Learn model.
- **`predictor.py`**: High-speed, offline classification using the trained brain.
- **`service.py`**: Continuous scheduling logic using the `schedule` library.

### 3. Data Flow
1.  **Ingest**: Emails fetched -> DB.
2.  **Bootstrap**: Emails -> Gemini -> Labels -> DB.
3.  **Train**: DB Labels -> TF-IDF Vectorizer -> Random Forest Model -> Disk (`ml_models_pro/`).
4.  **Operate**: New Inbox Email -> Disk Model -> Local Label -> Gmail Update.

## 🛡️ Privacy & Heuristics
- **Offline First**: Once trained, personal emails never leave your machine for classification.
- **Heuristic Layer**: Hard-coded rules (in `src/ml/base.py`) override ML for critical senders (e.g., AliExpress, GitHub, personal emails).
- **Privacy Protectors**: Prevents personal categories (Me, Marina) from leaking into other emails by verifying sender identity.
