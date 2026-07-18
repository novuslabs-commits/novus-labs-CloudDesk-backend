import re
from app.services.sentiment import analyze_sentiment

URGENT_KEYWORDS = [
    "urgent", "asap", "immediately", "critical", "emergency",
    "broken", "down", "outage", "can't access", "cannot access",
    "losing data", "data loss", "production", "blocked", "escalate"
]

def score_urgency(text: str) -> str:
    text_lower = text.lower()
    score = 0

    # keyword signals
    keyword_hits = sum(1 for kw in URGENT_KEYWORDS if kw in text_lower)
    score += keyword_hits * 2

    # punctuation signals
    score += text.count("!") 
    score += text.count("?") * 0.5

    # caps ratio
    words = text.split()
    if words:
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / len(words)
        score += caps_ratio * 5

    # sentiment signal — very negative = more urgent
    sentiment = analyze_sentiment(text)
    if sentiment["score"] < -0.5:
        score += 3
    elif sentiment["score"] < -0.2:
        score += 1

    # length signal — longer tickets often have more context = more serious
    if len(words) > 100:
        score += 1

    if score >= 6:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"