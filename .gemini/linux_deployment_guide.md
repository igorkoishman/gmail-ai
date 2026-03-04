# Linux Deployment Guide

I have successfully implemented the Dockerized Background Service! It is now capable of fetching new emails, sorting them via your ML model, and labeling them directly in your Gmail automatically.

Because we are moving this to a Linux machine, there are a few manual steps you need to take to ensure the service has everything it needs to run.

## 1. Re-Authorize Your Gmail (Local Mac)
We upgraded the app's permissions from "readonly" to "modify". You **must** re-authorize your account to generate a new token.

1.  Open your terminal on your Mac.
2.  Delete the old token: `rm token.json`
3.  Run the setup: `./.venv/bin/python setup_credentials.py`
4.  A browser will open; go through the Google login process again.

## 2. Commit and Push Code
Once you have the new `token.json`, you should commit the amazing new code I wrote to your branch:

```bash
git add .
git commit -m "Add Dockerized background service and Gmail sync engine"
git push -u origin feature/service
```

## 3. Deploy to Linux Machine

You **do not** need to clone the entire project repository on your Linux machine anymore, because the code will be pulled automatically from Docker Hub! You just need a single folder with your configuration.

On your target Linux machine, do the following:

1.  **Create a folder**:
    ```bash
    mkdir ~/gmail-ai
    cd ~/gmail-ai
    ```
2.  **Add your configuration files**: 
    Copy the following 3 items from your Mac into this new folder on your Linux machine (you can use `scp` or a USB drive):
    - `docker-compose.yml`
    - `token.json`
    - `ml_models_pro/` (the entire folder containing your `.pkl` models)
    - `.env` 

    Your Linux folder should look exactly like this:
    ```text
    ~/gmail-ai/
    ├── .env
    ├── docker-compose.yml
    ├── token.json
    └── ml_models_pro/
        ├── pro_classifier.pkl
        ├── pro_encoder.pkl
        └── pro_vectorizer.pkl
    ```

3.  **Start the Service!**
    Simply run the compose command in that folder:
    ```bash
    docker-compose up -d
    ```

### To view logs:
If you want to watch the service sync emails every 10 minutes on your Linux server:
```bash
docker logs -f gmail-ai-service
```
