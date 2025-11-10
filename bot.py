import os
import secrets
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import nest_asyncio

DB_CONFIG = {
    "dbname": "zilean",
    "user": "stremio", 
    "password": "stremio",
    "host": "stremio-postgres",
    "port": "5432"
}

def generate_streamfusion_key():
    """Génère une clé au format Stream-fusion"""
    return f"sf_{secrets.token_hex(16)}"

def connect_db():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ DB error: {e}")
        return None

async def generate_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = None
    try:
        conn = connect_db()
        if not conn:
            await update.message.reply_text("❌ Database unavailable")
            return

        # Générer une clé au format Stream-fusion
        api_key = generate_streamfusion_key()
        name = update.message.from_user.username or "Unknown"

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name) VALUES (%s, true, true, -1, %s) RETURNING api_key",
                (api_key, name)
            )
            returned_key = cur.fetchone()[0]
            conn.commit()
            
            message = (
                f"✅ Stream-fusion API Key Generated!\n\n"
                f"🔑 `{returned_key}`\n\n"
                f"Use this key to authenticate with Stream-fusion API."
            )
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except psycopg2.IntegrityError:
        await update.message.reply_text("❌ Key already exists, try again")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if conn:
            conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Use /generate to create a Stream-fusion API key")

async def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate_api_key))
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
