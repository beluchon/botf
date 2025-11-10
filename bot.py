import os
import uuid
import psycopg2
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import nest_asyncio
import sys
import time
from typing import Optional

# Appliquer nest_asyncio
nest_asyncio.apply()

# Configuration
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "streamfusion"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "host.docker.internal"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

API_CONFIG = {
    "base_url": os.getenv("API_BASE_URL", "http://localhost:8082"),
    "secret_key": os.getenv("API_SECRET_KEY", "testuu")
}

class APIKeyGenerator:
    """Classe pour gérer la génération de clés API via DB ou API"""
    
    @staticmethod
    def connect_db(max_retries=5, retry_delay=5) -> Optional[psycopg2.extensions.connection]:
        """Établit une connexion à la base de données avec retry automatique"""
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                return conn
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        return None

    @staticmethod
    def generate_via_db(username: str) -> Optional[str]:
        """Génère une clé API directement via la base de données"""
        conn = None
        try:
            conn = APIKeyGenerator.connect_db()
            if not conn:
                return None

            api_key = str(uuid.uuid4())
            
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO api_keys (api_key, is_active, never_expire, total_queries, name)
                    VALUES (%s::uuid, %s, %s, %s, %s)
                    RETURNING api_key
                    """,
                    (api_key, True, True, -1, username)
                )
                returned_key = cur.fetchone()[0]
                conn.commit()
                return str(returned_key)
                
        except Exception:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def generate_via_api(username: str) -> Optional[dict]:
        """Génère une clé API via l'API REST"""
        try:
            url = f"{API_CONFIG['base_url']}/api/auth/new"
            headers = {"secret-key": API_CONFIG['secret_key']}
            params = {"name": username, "never_expires": "true"}
            
            response = requests.post(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return None
                
        except Exception:
            return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Message de bienvenue avec menu interactif"""
    keyboard = [
        [InlineKeyboardButton("🔑 Générer une clé", callback_data="generate_menu")],
        [InlineKeyboardButton("📊 Mes clés", callback_data="list_keys")],
        [InlineKeyboardButton("❓ Aide", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "👋 *Bienvenue sur le générateur de clés API StreamFusion !*\n\n"
        "Ce bot vous permet de gérer vos clés API pour accéder à nos services.\n\n"
        "Que souhaitez-vous faire ?"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestionnaire des boutons inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "generate_menu":
        keyboard = [
            [InlineKeyboardButton("⚡ Méthode rapide (DB)", callback_data="gen_db")],
            [InlineKeyboardButton("🌐 Méthode API", callback_data="gen_api")],
            [InlineKeyboardButton("◀️ Retour", callback_data="back_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔑 *Choisissez une méthode de génération :*\n\n"
            "• *Méthode rapide* : Génération directe en base\n"
            "• *Méthode API* : Via le service REST\n\n"
            "Les deux méthodes créent des clés illimitées.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "gen_db":
        await generate_key_db(query)
    
    elif query.data == "gen_api":
        await generate_key_api(query)
    
    elif query.data == "list_keys":
        await list_user_keys(query)
    
    elif query.data == "help":
        await show_help(query)
    
    elif query.data == "back_menu":
        await show_main_menu(query)

async def generate_key_db(query) -> None:
    """Génère une clé via la base de données"""
    username = query.from_user.username or f"User_{query.from_user.id}"
    
    await query.edit_message_text("⏳ Génération en cours...")
    
    api_key = APIKeyGenerator.generate_via_db(username)
    
    if api_key:
        keyboard = [[InlineKeyboardButton("◀️ Retour au menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "✅ *Clé API générée avec succès !*\n\n"
            f"🔑 Clé : `{api_key}`\n"
            f"👤 Utilisateur : {username}\n"
            f"📊 Requêtes : Illimitées\n"
            f"⏰ Expiration : Jamais\n"
            f"🔧 Méthode : Base de données\n\n"
            "⚠️ *Conservez cette clé en sécurité !*"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        keyboard = [[InlineKeyboardButton("🔄 Réessayer", callback_data="gen_db")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Erreur lors de la génération.\nVeuillez réessayer.",
            reply_markup=reply_markup
        )

async def generate_key_api(query) -> None:
    """Génère une clé via l'API REST"""
    username = query.from_user.username or f"User_{query.from_user.id}"
    
    await query.edit_message_text("⏳ Génération via API en cours...")
    
    result = APIKeyGenerator.generate_via_api(username)
    
    if result and 'api_key' in result:
        keyboard = [[InlineKeyboardButton("◀️ Retour au menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "✅ *Clé API générée avec succès !*\n\n"
            f"🔑 Clé : `{result['api_key']}`\n"
            f"👤 Utilisateur : {username}\n"
            f"📊 Requêtes : Illimitées\n"
            f"⏰ Expiration : Jamais\n"
            f"🔧 Méthode : API REST\n\n"
            "⚠️ *Conservez cette clé en sécurité !*"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        keyboard = [[InlineKeyboardButton("🔄 Réessayer", callback_data="gen_api")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Erreur lors de la génération via API.\nVeuillez réessayer.",
            reply_markup=reply_markup
        )

async def list_user_keys(query) -> None:
    """Liste les clés de l'utilisateur"""
    username = query.from_user.username or f"User_{query.from_user.id}"
    
    conn = None
    try:
        conn = APIKeyGenerator.connect_db()
        if not conn:
            await query.edit_message_text("❌ Impossible de récupérer les clés.")
            return
        
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT api_key, created_at, is_active, total_queries
                FROM api_keys
                WHERE name = %s
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (username,)
            )
            keys = cur.fetchall()
        
        if keys:
            message = f"📊 *Vos clés API* (5 dernières)\n\n"
            for i, (key, created, active, queries) in enumerate(keys, 1):
                status = "🟢 Active" if active else "🔴 Inactive"
                q_text = "Illimitées" if queries == -1 else str(queries)
                message += f"{i}. `{key}`\n   {status} • {q_text} • {created.strftime('%d/%m/%Y')}\n\n"
        else:
            message = "📭 Vous n'avez pas encore de clés API.\nGénérez-en une !"
        
        keyboard = [[InlineKeyboardButton("◀️ Retour", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception:
        await query.edit_message_text("❌ Erreur lors de la récupération des clés.")
    finally:
        if conn:
            conn.close()

async def show_help(query) -> None:
    """Affiche l'aide"""
    help_text = (
        "🆘 *Aide du bot StreamFusion*\n\n"
        "📋 *Commandes disponibles :*\n"
        "• `/start` - Menu principal\n"
        "• `/generate` - Générer une clé rapidement\n"
        "• `/keys` - Voir vos clés\n"
        "• `/help` - Afficher cette aide\n\n"
        "🔑 *Méthodes de génération :*\n"
        "• *Base de données* : Rapide et fiable\n"
        "• *API REST* : Via le service web\n\n"
        "💡 *Toutes les clés sont :*\n"
        "✓ Illimitées en requêtes\n"
        "✓ Sans expiration\n"
        "✓ Activées par défaut\n\n"
        "❓ Questions ? Contactez @support"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Retour", callback_data="back_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_main_menu(query) -> None:
    """Affiche le menu principal"""
    keyboard = [
        [InlineKeyboardButton("🔑 Générer une clé", callback_data="generate_menu")],
        [InlineKeyboardButton("📊 Mes clés", callback_data="list_keys")],
        [InlineKeyboardButton("❓ Aide", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "👋 *Menu principal*\n\nQue souhaitez-vous faire ?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande rapide de génération (par défaut via DB)"""
    username = update.message.from_user.username or f"User_{update.message.from_user.id}"
    
    msg = await update.message.reply_text("⏳ Génération en cours...")
    
    api_key = APIKeyGenerator.generate_via_db(username)
    
    if api_key:
        await msg.edit_text(
            f"✅ *Clé générée !*\n\n🔑 `{api_key}`\n\n⚠️ Conservez-la en sécurité !",
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text("❌ Erreur de génération. Utilisez /start pour réessayer.")

async def keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande pour lister les clés"""
    username = update.message.from_user.username or f"User_{update.message.from_user.id}"
    
    conn = None
    try:
        conn = APIKeyGenerator.connect_db()
        if not conn:
            await update.message.reply_text("❌ Erreur de connexion.")
            return
        
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM api_keys WHERE name = %s
                """,
                (username,)
            )
            count = cur.fetchone()[0]
        
        await update.message.reply_text(
            f"📊 Vous avez *{count}* clé(s) API.\n\nUtilisez /start pour plus de détails.",
            parse_mode='Markdown'
        )
        
    except Exception:
        await update.message.reply_text("❌ Erreur.")
    finally:
        if conn:
            conn.close()

async def main() -> None:
    """Fonction principale du bot"""
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_TOKEN non trouvé")
        
        application = ApplicationBuilder().token(token).build()
        
        # Enregistrement des handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("generate", generate_command))
        application.add_handler(CommandHandler("keys", keys_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except Exception:
        sys.exit(1)

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(60)
