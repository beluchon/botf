FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

ENV TELEGRAM_TOKEN=your_telegram_token_here
ENV API_BASE_URL=http://localhost:8082
ENV SECRET_KEY=testuu
ENV POSTGRES_DB=streamfusion
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_HOST=host.docker.internal
ENV POSTGRES_PORT=5432

CMD ["python", "bot.py"]
