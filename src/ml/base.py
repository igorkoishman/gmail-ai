import os
import joblib
from ..core.database import DatabaseEngine

class BaseML:
    def __init__(self, model_dir="ml_models_pro"):
        self.db = DatabaseEngine()
        self.model_dir = model_dir
        self.model_file = os.path.join(model_dir, "pro_classifier.pkl")
        self.vec_file = os.path.join(model_dir, "pro_vectorizer.pkl")
        self.enc_file = os.path.join(model_dir, "pro_encoder.pkl")

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

    def _get_hard_rule(self, sender: str) -> str:
        """Override ML logic for specific critical senders."""
        sender = sender.lower()
        if 'igorkoishman@gmail.com' in sender:
            return "Me"
        if 'marina0020@gmail.com' in sender:
            return "Marina"
        if 'github' in sender or 'docker' in sender:
            return "Work/Professional"
        if 'ebay' in sender:
            return "Shopping/Promotions"
        if 'aliexpress' in sender:
            return "Ali express adds"
        return None

    def model_exists(self) -> bool:
        return os.path.exists(self.model_file)
