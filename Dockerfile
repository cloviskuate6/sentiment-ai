# Utilisation d'une version slim mise à jour
FROM python:3.11-slim-bookworm

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Étape 1 : Mise à jour du système d'exploitation et installation des dépendances système
# On nettoie le cache apt pour réduire la taille de l'image finale
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Étape 2 : copier le fichier de dépendances
COPY requirements.txt .

# Étape 3 : installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : copier le code source et les tests
COPY src/ ./src/
COPY tests/ ./tests/

# Documenter le port utilisé par l’application
EXPOSE 8085

# Commande de démarrage du serveur Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8085"]