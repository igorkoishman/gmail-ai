# Usage Guide: Teaching, Training, & Prediction

This guide explains the three-stage workflow for the Gmail AI classification system.

## 1. Teaching (Bootstrapping)
The system needs "gold standard" labels to learn from. We use Gemini flash-lite to generate these efficiently.

```bash
python main.py --teach
```
- **What it does**: Fetches up to 2000 unread emails (defined in `main.py`). Sends batches to Gemini. Updates `ai_category` in MySQL.
- **Cost**: Uses minimal Gemini tokens.

## 2. Training (Offline Brain)
Once you have labels (from Gemini or your manual overrides), train the local Random Forest model.

```bash
python main.py --train
```
- **What it does**: Reads labeled emails from DB. Vectorizes text (TF-IDF). Trains a `RandomForestClassifier`. Saves models to `ml_models_pro/`.

## 3. Prediction (Daily Operations)
Use the local brain to categorize emails without any API costs.

### Manual Run
```bash
python main.py --predict
```

### Cron Job (Run & Exit)
```bash
python main.py --once
```
- **What it does**: Performs exactly one full sync cycle (Fetch -> Predict -> Label) and then shuts down. Ideal for Linux `crontab` or Kubernetes `CronJob`.

### Background Service (Persistent)
```bash
python main.py --service --interval 24
```
- **What it does**: Checks for new unread emails every 24 hours. Labels them locally. Updates Gmail using the API.

## 4. Bulk Recovery
If you have thousands of old emails to label at once:
```bash
python main.py --bulk-label
```
- **Resiliency**: This command is designed to be stopped and restarted; it will resume from where it left off.
