FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de l'application
WORKDIR /app

# Créer le répertoire pour les logs
RUN mkdir -p /app/logs

# Copier le fichier requirements.txt d'abord (pour mieux utiliser le cache Docker)
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer un utilisateur non-root pour plus de sécurité
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV POSTGRES_HOST=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=streamfusion
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Commande pour lancer le bot
CMD ["python", "bot.py"]
