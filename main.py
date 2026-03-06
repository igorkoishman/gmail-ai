import argparse
import sys
import os

# Add src to path if needed (standard for some setups)
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.ml.trainer import ProTrainer
from src.ml.predictor import ProPredictor
from src.ml.service import GmailAIService

def main():
    parser = argparse.ArgumentParser(description="Gmail AI: Modular, Resilient Email Classification")
    parser.add_argument("--teach", action="store_true", help="Gemini-lite teaching (Bootstrap labels)")
    parser.add_argument("--train", action="store_true", help="Train the offline local brain")
    parser.add_argument("--predict", action="store_true", help="Run ML prediction on local database")
    parser.add_argument("--bulk-label", action="store_true", help="Resilient mass labeling of Gmail inbox")
    parser.add_argument("--service", action="store_true", help="Run as persistent background service")
    parser.add_argument("--cron", type=str, default="0 0 * * *", help="Cron expression for service sync (e.g. '0 0 * * *')")
    parser.add_argument("--once", action="store_true", help="Run a single sync cycle (Fetch, Predict, Label) and exit")
    
    args = parser.parse_args()

    if args.once:
        service = GmailAIService()
        service.run_cycle()

    elif args.teach:
        trainer = ProTrainer()
        trainer.teach_with_gemini()
        # Auto-predict after teaching
        predictor = ProPredictor()
        predictor.predict_all()

    elif args.train:
        trainer = ProTrainer()
        trainer.train_locally()

    elif args.predict:
        predictor = ProPredictor()
        predictor.predict_all()

    elif args.bulk_label:
        predictor = ProPredictor()
        predictor.bulk_label_history()

    elif args.service:
        service = GmailAIService()
        service.start(cron_expression=args.cron)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
