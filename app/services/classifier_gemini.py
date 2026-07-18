from google import genai
import json
from app.config import get_settings

settings = get_settings()

VALID_INTENTS = ["billing", "technical", "feature_request", "complaint", "refund", "account_access", "general"]

class GeminiClassifier:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        print("Gemini classifier initialized")

    def classify(self, text: str) -> dict:
        prompt = f"""Classify this customer support ticket into exactly one of these intents:
billing, technical, feature_request, complaint, refund, account_access, general

Ticket: "{text}"

Respond with ONLY a JSON object in this exact format, no other text:
{{"intent": "one_of_the_categories_above", "confidence": 0.85}}

confidence should be a realistic number between 0 and 1 reflecting how certain you are."""

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                raw = response.text.strip().replace('```json', '').replace('```', '').strip()
                result = json.loads(raw)

                intent = result.get("intent", "general")
                if intent not in VALID_INTENTS:
                    intent = "general"
                confidence = float(result.get("confidence", 0.7))

                return {
                    "intent": intent,
                    "confidence": confidence,
                    "all_scores": {i: (confidence if i == intent else (1 - confidence) / 6) for i in VALID_INTENTS},
                    "needs_review": confidence < settings.confidence_threshold
                }
            except Exception as e:
                if attempt < 2:
                    import time
                    time.sleep(2)
                else:
                    return {
                        "intent": "general",
                        "confidence": 0.5,
                        "all_scores": {i: 1/7 for i in VALID_INTENTS},
                        "needs_review": True
                    }

classifier = GeminiClassifier()