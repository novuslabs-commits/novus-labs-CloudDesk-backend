from app.config import get_settings

settings = get_settings()

if settings.use_gemini_classifier:
    from app.services.classifier_gemini import classifier
else:
    # existing DistilBERT code stays here for local dev
    from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
    import torch
    import torch.nn.functional as F

    ID2LABEL = {
        0: "billing", 1: "technical", 2: "feature_request", 3: "complaint",
        4: "refund", 5: "account_access", 6: "general"
    }

    class TicketClassifier:
        _instance = None
        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._load()
            return cls._instance

        def _load(self):
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.tokenizer = DistilBertTokenizer.from_pretrained(settings.model_path)
            self.model = DistilBertForSequenceClassification.from_pretrained(settings.model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"Classifier loaded on {self.device}")

        def classify(self, text: str) -> dict:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)[0]
            predicted_id = torch.argmax(probs).item()
            confidence = round(probs[predicted_id].item(), 4)
            return {
                "intent": ID2LABEL[predicted_id],
                "confidence": confidence,
                "all_scores": {ID2LABEL[i]: round(probs[i].item(), 4) for i in range(7)},
                "needs_review": confidence < settings.confidence_threshold
            }

    classifier = TicketClassifier()