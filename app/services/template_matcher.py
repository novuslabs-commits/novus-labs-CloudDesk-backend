from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from app.models.template import Template
import numpy as np

class TemplateMatcher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=5000,
                ngram_range=(1, 2)
            )
            cls._instance.templates = []
            cls._instance.matrix = None
            cls._instance.fitted = False
        return cls._instance

    def fit(self, db: Session):
        templates = db.query(Template).all()
        if not templates:
            self.fitted = False
            return

        self.templates = templates
        corpus = [f"{t.title} {t.body}" for t in templates]
        self.matrix = self.vectorizer.fit_transform(corpus)
        self.fitted = True
        print(f"Template matcher fitted on {len(templates)} templates")

    def match(self, text: str, intent: str, top_k: int = 3) -> list:
        if not self.fitted or not self.templates:
            return []

        query_vec = self.vectorizer.transform([text])
        similarities = cosine_similarity(query_vec, self.matrix)[0]

        # filter by intent first then rank by similarity
        intent_indices = [
            i for i, t in enumerate(self.templates)
            if t.intent == intent
        ]

        if not intent_indices:
            intent_indices = list(range(len(self.templates)))

        ranked = sorted(intent_indices, key=lambda i: similarities[i], reverse=True)[:top_k]

        return [
            {
                "template_id": self.templates[i].id,
                "title": self.templates[i].title,
                "body": self.templates[i].body,
                "similarity": round(float(similarities[i]), 4)
            }
            for i in ranked
        ]

template_matcher = TemplateMatcher()