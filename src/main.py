# Fichier principal de l'API Sentiment-AI
from fastapi import FastAPI
from src.schemas import PredictionRequest, PredictionResponse
from src.model import SentimentModel


# 1. Création de l'instance de l'API
app = FastAPI(title="SentimentAI API")


# 2. Chargement du modèle au démarrage
model = SentimentModel()


# Endpoint de Healthcheck
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Endpoint de prédiction
@app.post("/predict", response_model=PredictionResponse)
def predict_sentiment(payload: PredictionRequest):
    # Appeler la méthode predict du modèle avec le texte validé par Pydantic
    result = model.predict(payload.text)
    return result