

# bot.py
import os
import uuid
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import nest_asyncio
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# ✅ CRÉER LE DOSSIER DE LOGS AVANT TOUTE CHOSE
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
os.chmod(log_dir, 0o755)  # Donner les permissions

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        RotatingFileHandler(
            "/app/logs/telegram_bot.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Appliquer nest_asyncio
nest_asyncio.apply()

# Configuration de la base de données
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "streamfusion"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "host.docker.internal"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

def connect_db(max_retries=5, retry_delay=5):
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Connexion à la base de données établie avec succès")
            return conn
        except Exception as e:
            logger.error(f"Tentative {attempt + 1}/{max_retries} - Erreur de connexion: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Nouvelle tentative dans {retry_delay} secondes...")
                asyncio.sleep(retry_delay)
    return None

async def generate_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        conn = connect_db()
        if not conn:
            await update.message.reply_text("Impossible de se connecter à la base de données.")
            return

        api_key = str(uuid.uuid4())
        is_active = True
        never_expire = True
        total_queries = -1
        name = update.message.from_user.username or "Unknown"

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name)
                VALUES (uuid(%s), %s, %s, %s, %s)
                RETURNING api_key
                """,
                (api_key, is_active, never_expire, total_queries, name)
            )
            returned_key = cur.fetchone()[0]
            conn.commit()

            logger.info(f"Nouvelle clé API générée pour l'utilisateur: {name}")
            
            confirmation_message = (
                f"✅ Clé API générée avec succès !\n\n"
                f"🔑 Votre clé : {returned_key}\n"
                f"📊 Requêtes : Illimitées\n"
                f"⏰ Expiration : Jamais"
            )
            await update.message.reply_text(confirmation_message)
    except Exception as e:
        error_msg = f"Erreur lors de la génération de la clé API: {e}"
        logger.error(error_msg)
        await update.message.reply_text("Une erreur est survenue lors de la génération de la clé.")
    finally:
        if conn:
            conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "👋 Bienvenue sur le générateur de clés API !\n\n"
        "Pour obtenir une nouvelle clé API avec accès illimité, "
        "utilisez la commande /generate"
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"Nouvel utilisateur a démarré le bot: {update.message.from_user.username}")

async def main() -> None:
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("Token Telegram non trouvé dans les variables d'environnement")
            
        application = ApplicationBuilder().token(token).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("generate", generate_api_key))
        
        logger.info("Bot démarré avec succès")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Erreur critique lors du démarrage du bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Démarrage du service bot Telegram")
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logger.error(f"Erreur dans la boucle principale: {e}")
            logger.info("Redémarrage dans 60 secondes...")
            asyncio.sleep(60)
