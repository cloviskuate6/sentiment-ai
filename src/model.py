class SentimentModel:
    def __init__(self):
        # Ce message sera visible dans "docker logs sentiment"
        print("[SentimentModel] Modèle chargé")

    def predict(self, text: str) -> dict:
        text_lower = text.lower()

        # Listes de mots-clés nettoyées des espaces superflus
        positive_words = [
            "bien",
            "super",
            "excellent",
            "parfait",
            "bon",
            "aime",
            "adore"]
        negative_words = [
            "mal",
            "nul",
            "horrible",
            "mauvais",
            "déteste",
            "pire"]

        # Compter les occurrences de mots positifs et négatifs
        pos = sum(1 for w in positive_words if w in text_lower)
        neg = sum(1 for w in negative_words if w in text_lower)

        if pos > neg:
            # Calcule un score dynamique plafonné à 1.0 max
            score = min(round(0.6 + 0.1 * pos, 2), 1.0)
            return {"label": "POSITIVE", "score": score, "text": text}

        elif neg > pos:
            # Calcule un score dynamique plafonné à 1.0 max
            score = min(round(0.6 + 0.1 * neg, 2), 1.0)
            return {"label": "NEGATIVE", "score": score, "text": text}

        return {"label": "NEUTRAL", "score": 0.5, "text": text}
