import time
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Gauge, Histogram

# Import de vos modules locaux
from src.schemas import PredictionRequest, PredictionResponse
from src.model import SentimentModel

# 1. Initialisation unique de l'application
app = FastAPI(title="SentimentAI", version="0.1.0")

# 2. Initialisation de l'instrumentateur Prometheus
# On attache l'instrumentation à l'application 'app' ici
instrumentator = Instrumentator().instrument(app)

# 3. Chargement du modèle
model = SentimentModel()

# 4. Définition des métriques métier
predictions_total = Counter(
    "sentiment_predictions_total",
    "Nombre total de prédictions",
    ["label", "status"]
)

confidence_gauge = Gauge(
    "sentiment_confidence_score",
    "Score de confiance de la dernière prédiction",
    ["label"]
)

prediction_duration = Histogram(
    "sentiment_prediction_duration_seconds",
    "Durée des prédictions en secondes",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

# 5. Exposition explicite de la route /metrics
instrumentator.expose(app)

# 6. Endpoints
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    start = time.time()
    try:
        result = model.predict(request.text)
        duration = time.time() - start
        
        # Mise à jour des métriques métier
        predictions_total.labels(label=result["label"], status="ok").inc()
        confidence_gauge.labels(label=result["label"]).set(result["score"])
        prediction_duration.observe(duration)
        
        return result
    except Exception:
        predictions_total.labels(label="UNKNOWN", status="error").inc()
        raise