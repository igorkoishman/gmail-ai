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

    def _get_hard_rule(self, sender: str, full_text: str = "") -> str:
        """Override ML logic for specific critical senders."""
        sender = sender.lower()
        full_text_lower = full_text.lower() if full_text else ""
        if 'igorkoishman@gmail.com' in sender:
            return "Me"
        if 'marina0020@gmail.com' in sender:
            return "Marina"
        if 'github' in sender or 'docker' in sender:
            return "Work/Professional"
        if 'ebay' in sender:
            return "Shopping/Promotions"
        if 'aliexpress' in sender:
            # If the email explicitly contains 'פרסומת' (advertisement), it is definitely an ad!
            if 'פרסומת' in full_text_lower:
                return "Ali express adds"

            import re
            
            # Catch known promo phrases
            ad_patterns = [
                r"זה כמעט שלך",
                r"מבחר חבילות\s*=\s*מקסימום הנחות",
                r"עדיין בעניין\?",
                r"הגיע הזמן להוסיף עוד",
                r"לכו בגדול על חסכונות",
                r"meanwhile",
                r"לקחת הפסקה\?\s*זה הזמן לחזור לקנות אצלנו",
                r"קנו בכמויות כדי לחסוך"
            ]
            for pattern in ad_patterns:
                if re.search(pattern, full_text_lower, re.IGNORECASE):
                    return "Ali express adds"

            # Catch known order tracking patterns
            order_patterns = [
                r"חבילה מס'?\s+[A-Z0-9]+",
                r"הזמנה מס'?\s+[0-9]+",
                r"הזמנה\s+[0-9]+",
                r"הזמנתכם\s+מס'?\s+[0-9]+",
                r"הזמנתכם\s+[0-9]+",
                r"חבילה מס'",
                r"הזמנה מס'",
                r"הזמנה\s*\d+[:\s]*בהמתנה לאישור",
                r"הזמנה \d+.*בהמתנה לאישור",
                r"עדכונים לגבי המשלוח של \d+ החבילות שלכם",
                r"הזמ'.*\d+.*עדכון מסירה",
                r"הודעה על משלוח שמספרו",
                r"יצאה מאזור המוצא",
                r"מוכנה למשלוח",
                r"יצאה למסירה",
                r"נשלחה",
                r"במדינה/באזור שלכם",
                r"אושרה",
                r"נמסרה",
                r"נאספה על ידי חברת המשלוחים",
                r"עם חברת המשלוחים המקומית",
                r"שוחררה מהמכס"
            ]
            for pattern in order_patterns:
                if re.search(pattern, full_text_lower, re.IGNORECASE | re.DOTALL):
                    return "Ali express"
                    
            return "Ali express adds"
        return None

    def model_exists(self) -> bool:
        return os.path.exists(self.model_file)
