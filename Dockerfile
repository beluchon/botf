FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Créer la structure de dossiers AVANT de changer d'utilisateur
WORKDIR /app
RUN mkdir -p logs && chmod 755 logs

# Copier les requirements d'abord
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer un utilisateur non-root et donner les permissions
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
