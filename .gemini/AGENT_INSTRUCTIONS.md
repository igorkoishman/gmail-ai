# Agent Instructions: Managing & Deploying Gmail AI

This workspace is designed to be managed by AI Agents (like Gemini CLI). Follow these rules to maintain the system.

## 🤖 DevOps Workflow

### 1. Environment Management
- **Verification**: Always run `./.venv/bin/python main.py --help` to ensure the environment is sound.
- **Database**: Use `src/core/database.py` logic to inspect schemas if needed.

### 2. Service Deployment (Docker/K3s)
- **Status Check**: `docker-compose ps` to verify the classifier is running.
- **Scheduling**: The classification interval is controlled by `main.py --interval X`. Do not change this unless requested.
- **K3s Entrypoint**: For Kubernetes deployments, use the `Dockerfile` with the entrypoint set to `python main.py --service --interval 24`.

### 3. Troubleshooting
- **Logs**: Always check `bulk_label.log` and container logs (`docker logs gmail-ai`).
- **Mailing List Parsing**: If text extraction fails, use `diagnostics/dump_mime.py` to inspect the email structure.

## 🧠 Model Maintenance
- **Retraining**: If the user provides manual labels in the database (Table: `emails`, Column: `manual_category`), the agent should trigger a retrain:
  ```bash
  python main.py --train
  ```
- **Bootstrap**: If the `ml_models_pro/` folder is empty, the agent must run `--teach` then `--train`.

## 📂 Directory Map
- `src/core/`: Foundation (Gmail, DB, AI API).
- `src/ml/`: "The Brain" (Trainer, Predictor, Service).
- `scripts/`: Operational tools.
- `diagnostics/`: Deep-dive debugging.
- `k8s/`: Infrastructure manifests.
