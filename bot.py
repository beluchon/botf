# bot.py
import os
import uuid
import psycopg2
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import nest_asyncio

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

# Configuration de l'API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8082")
SECRET_KEY = os.getenv("SECRET_KEY", "testuu")

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception:
        return None

async def generate_api_key_via_api(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Génère une clé API via l'endpoint API"""
    try:
        user_name = update.message.from_user.username or f"user_{update.message.from_user.id}"
        
        # Préparer les paramètres
        params = {
            "name": user_name,
            "never_expires": "true"
        }
        
        headers = {
            "secret-key": SECRET_KEY
        }
        
        # Faire l'appel API
        response = requests.post(
            f"{API_BASE_URL}/api/auth/new",
            params=params,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            api_key_data = response.json()
            api_key = api_key_data.get("api_key", "Clé non retournée")
            
            # Sauvegarder dans la base de données
            await save_api_key_to_db(api_key, user_name)
            
            confirmation_message = (
                f"✅ Clé API générée avec succès via l'API !\n\n"
                f"🔑 Votre clé : `{api_key}`\n"
                f"👤 Utilisateur : {user_name}\n"
                f"📊 Requêtes : Illimitées\n"
                f"⏰ Expiration : Jamais\n\n"
                f"⚠️ **Gardez cette clé secrète !**"
            )
            await update.message.reply_text(confirmation_message, parse_mode='Markdown')
            
        else:
            await update.message.reply_text("❌ Erreur lors de la génération via l'API. Utilisation de la méthode de secours...")
            await generate_api_key_fallback(update, context)
            
    except requests.exceptions.RequestException:
        await update.message.reply_text("❌ Impossible de contacter l'API. Utilisation de la méthode de secours...")
        await generate_api_key_fallback(update, context)
    except Exception:
        await update.message.reply_text("❌ Erreur lors de la génération de la clé API.")

async def generate_api_key_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Méthode de secours pour générer une clé API directement dans la base de données"""
    try:
        conn = connect_db()
        if not conn:
            await update.message.reply_text("❌ Impossible de se connecter à la base de données.")
            return

        api_key = str(uuid.uuid4())
        is_active = True
        never_expire = True
        total_queries = -1
        name = update.message.from_user.username or f"user_{update.message.from_user.id}"

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name, created_at)
                VALUES (uuid(%s), %s, %s, %s, %s, NOW())
                RETURNING api_key
                """,
                (api_key, is_active, never_expire, total_queries, name)
            )
            returned_key = cur.fetchone()[0]
            conn.commit()
            
            confirmation_message = (
                f"✅ Clé API générée avec succès (mode secours) !\n\n"
                f"🔑 Votre clé : `{returned_key}`\n"
                f"👤 Utilisateur : {name}\n"
                f"📊 Requêtes : Illimitées\n"
                f"⏰ Expiration : Jamais\n\n"
                f"⚠️ **Gardez cette clé secrète !**"
            )
            await update.message.reply_text(confirmation_message, parse_mode='Markdown')
            
    except Exception:
        await update.message.reply_text("❌ Échec de la génération de clé API.")
    finally:
        if conn:
            conn.close()

async def save_api_key_to_db(api_key: str, user_name: str) -> None:
    """Sauvegarde la clé API dans la base de données"""
    try:
        conn = connect_db()
        if not conn:
            return

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name, created_at, source)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                """,
                (api_key, True, True, -1, user_name, 'telegram_bot_api')
            )
            conn.commit()
            
    except Exception:
        pass
    finally:
        if conn:
            conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande de démarrage du bot"""
    welcome_message = (
        "👋 Bienvenue sur le générateur de clés API !\n\n"
        "Commandes disponibles:\n"
        "✅ /generate - Générer une nouvelle clé API\n"
        "ℹ️  /help - Afficher cette aide\n\n"
        "Votre clé API vous permettra d'accéder à l'API StreamFusion avec des requêtes illimitées et sans expiration."
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande d'aide"""
    help_message = (
        "🤖 **Générateur de Clés API**\n\n"
        "🔑 **Générer une clé:**\n"
        "Utilisez `/generate` pour créer une nouvelle clé API\n\n"
        "⚡ **Caractéristiques:**\n"
        "• Requêtes illimitées\n"
        "• Pas d'expiration\n"
        "• Accès complet à l'API\n\n"
        "🔒 **Sécurité:**\n"
        "• Gardez votre clé secrète\n"
        "• Ne la partagez pas\n"
        "• Stockez-la en sécurité"
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def main() -> None:
    """Fonction principale"""
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            return
            
        application = ApplicationBuilder().token(token).build()
        
        # Ajouter les handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("generate", generate_api_key_via_api))
        
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception:
        pass

if __name__ == '__main__':
    asyncio.run(main())
