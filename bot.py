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
from flask import Flask, request, jsonify
import threading

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
    "dbname": os.getenv("POSTGRES_DB", "zilean"),
    "user": os.getenv("POSTGRES_USER", "stremio"),
    "password": os.getenv("POSTGRES_PASSWORD", "stremio"),
    "host": os.getenv("POSTGRES_HOST", "stremio-postgres"),
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

# Fonctions du bot Telegram
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
                f"🔑 Votre clé : `{returned_key}`\n"
                f"📊 Requêtes : Illimitées\n"
                f"⏰ Expiration : Jamais\n\n"
                f"Utilisez cette clé dans vos requêtes API."
            )
            await update.message.reply_text(confirmation_message, parse_mode='Markdown')
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
        "Commandes disponibles:\n"
        "/start - Afficher ce message\n"
        "/generate - Générer une nouvelle clé API\n"
        "/mykeys - Afficher vos clés API"
    )
    await update.message.reply_text(welcome_message)
    logger.info(f"Nouvel utilisateur a démarré le bot: {update.message.from_user.username}")

async def my_keys(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        conn = connect_db()
        if not conn:
            await update.message.reply_text("Impossible de se connecter à la base de données.")
            return

        username = update.message.from_user.username or "Unknown"
        
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT api_key, is_active, created_at, total_queries 
                FROM api_keys 
                WHERE name = %s 
                ORDER BY created_at DESC
                """,
                (username,)
            )
            keys = cur.fetchall()

            if keys:
                message = f"🔑 Vos clés API ({len(keys)}):\n\n"
                for i, (api_key, is_active, created_at, total_queries) in enumerate(keys, 1):
                    status = "✅ Actif" if is_active else "❌ Inactif"
                    queries = "Illimité" if total_queries == -1 else f"{total_queries} requêtes"
                    message += f"{i}. `{api_key}`\n"
                    message += f"   Statut: {status}\n"
                    message += f"   Créé: {created_at.strftime('%Y-%m-%d')}\n"
                    message += f"   Quotas: {queries}\n\n"
            else:
                message = "❌ Aucune clé API trouvée. Utilisez /generate pour en créer une."

            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        error_msg = f"Erreur lors de la récupération des clés: {e}"
        logger.error(error_msg)
        await update.message.reply_text("Une erreur est survenue.")
    finally:
        if conn:
            conn.close()

# Application Flask pour l'API HTTP
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "API Key Manager Service",
        "version": "1.0",
        "endpoints": {
            "/health": "Health check",
            "/api/verify": "Verify API key (GET param: api_key)",
            "/api/stats": "Get API key statistics (GET param: api_key)"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    try:
        conn = connect_db()
        if conn:
            conn.close()
            return jsonify({"status": "healthy", "database": "connected"})
        else:
            return jsonify({"status": "unhealthy", "database": "disconnected"}), 503
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route('/api/verify', methods=['GET'])
def verify_api_key():
    api_key = request.args.get('api_key')
    if not api_key:
        return jsonify({"error": "API key required. Use ?api_key=YOUR_API_KEY"}), 400
    
    try:
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name, is_active, total_queries, never_expire, created_at 
                FROM api_keys 
                WHERE api_key = uuid(%s)
                """,
                (api_key,)
            )
            result = cur.fetchone()
            
            if result:
                name, is_active, total_queries, never_expire, created_at = result
                if is_active:
                    return jsonify({
                        "valid": True,
                        "name": name,
                        "total_queries": total_queries,
                        "never_expire": never_expire,
                        "created_at": created_at.isoformat(),
                        "message": "API key is valid"
                    })
                else:
                    return jsonify({"valid": False, "error": "API key is inactive"}), 403
            else:
                return jsonify({"valid": False, "error": "Invalid API key"}), 404
                
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    api_key = request.args.get('api_key')
    if not api_key:
        return jsonify({"error": "API key required"}), 400
    
    try:
        conn = connect_db()
        with conn.cursor() as cur:
            # Vérifier d'abord la clé
            cur.execute(
                "SELECT name FROM api_keys WHERE api_key = uuid(%s) AND is_active = true",
                (api_key,)
            )
            if not cur.fetchone():
                return jsonify({"error": "Invalid or inactive API key"}), 403
            
            # Statistiques globales
            cur.execute("SELECT COUNT(*) as total_keys FROM api_keys")
            total_keys = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) as active_keys FROM api_keys WHERE is_active = true")
            active_keys = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) as unlimited_keys FROM api_keys WHERE total_queries = -1")
            unlimited_keys = cur.fetchone()[0]
            
            return jsonify({
                "stats": {
                    "total_keys": total_keys,
                    "active_keys": active_keys,
                    "unlimited_keys": unlimited_keys
                }
            })
                
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Lancer Flask dans un thread séparé
def run_flask():
    logger.info("Démarrage du serveur Flask sur le port 52707")
    app.run(host='0.0.0.0', port=52707, debug=False, use_reloader=False)

# Bot Telegram
async def run_telegram_bot():
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("Token Telegram non trouvé dans les variables d'environnement")
            
        application = ApplicationBuilder().token(token).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("generate", generate_api_key))
        application.add_handler(CommandHandler("mykeys", my_keys))
        
        logger.info("Bot Telegram démarré avec succès")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Erreur critique lors du démarrage du bot Telegram: {e}")
        raise

# Fonction principale
def main():
    # Démarrer Flask dans un thread séparé
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("Service démarré - Bot Telegram + API HTTP")
    
    # Démarrer le bot Telegram dans le thread principal
    while True:
        try:
            asyncio.run(run_telegram_bot())
        except Exception as e:
            logger.error(f"Erreur dans la boucle principale du bot: {e}")
            logger.info("Redémarrage dans 30 secondes...")
            asyncio.sleep(30)

if __name__ == '__main__':
    main()
