import os
import uuid
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import nest_asyncio

# Configuration de la base de données
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "zilean"),
    "user": os.getenv("POSTGRES_USER", "stremio"),
    "password": os.getenv("POSTGRES_PASSWORD", "stremio"),
    "host": os.getenv("POSTGRES_HOST", "stremio-postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

def connect_db():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception:
        return None

async def generate_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        conn = connect_db()
        if not conn:
            await update.message.reply_text("❌ Base de données indisponible")
            return

        api_key = str(uuid.uuid4())
        name = update.message.from_user.username or "Unknown"

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name) VALUES (uuid(%s), true, true, -1, %s) RETURNING api_key",
                (api_key, name)
            )
            returned_key = cur.fetchone()[0]
            conn.commit()
            
            message = f"✅ Clé API : `{returned_key}`"
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text("❌ Erreur")
    finally:
        if conn:
            conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Utilisez /generate pour une clé API")

async def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate_api_key))
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
