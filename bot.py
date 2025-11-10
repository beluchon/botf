import os
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

# Configuration API StreamFusion
API_CONFIG = {
    "base_url": os.getenv("API_BASE_URL", "http://stream-fusion:8080"),
    "secret_key": os.getenv("API_SECRET_KEY", "testuu")
}

class StreamFusionAPI:
    """Classe pour interagir avec l'API StreamFusion"""
    
    @staticmethod
    def generate_key(username: str) -> Optional[dict]:
        """Génère une clé API via l'API StreamFusion"""
        try:
            url = f"{API_CONFIG['base_url']}/api/auth/new"
            headers = {"secret-key": API_CONFIG['secret_key']}
            params = {
                "name": username,
                "never_expires": "true"
            }
            
            response = requests.post(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    @staticmethod
    def list_keys(username: str) -> Optional[list]:
        """Liste les clés d'un utilisateur via l'API StreamFusion"""
        try:
            url = f"{API_CONFIG['base_url']}/api/auth/keys"
            headers = {"secret-key": API_CONFIG['secret_key']}
            params = {"name": username}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    @staticmethod
    def delete_key(api_key: str) -> bool:
        """Supprime une clé API"""
        try:
            url = f"{API_CONFIG['base_url']}/api/auth/delete"
            headers = {"secret-key": API_CONFIG['secret_key']}
            params = {"api_key": api_key}
            
            response = requests.delete(url, headers=headers, params=params, timeout=10)
            
            return response.status_code == 200
                
        except Exception:
            return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Message de bienvenue avec menu interactif"""
    keyboard = [
        [InlineKeyboardButton("🔑 Générer une clé", callback_data="generate")],
        [InlineKeyboardButton("📊 Mes clés", callback_data="list_keys")],
        [InlineKeyboardButton("❓ Aide", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "👋 *Bienvenue sur le bot StreamFusion !*\n\n"
        "🎬 Générez vos clés API pour accéder à StreamFusion.\n\n"
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
    
    if query.data == "generate":
        await generate_key(query)
    
    elif query.data == "list_keys":
        await list_user_keys(query)
    
    elif query.data == "help":
        await show_help(query)
    
    elif query.data == "back_menu":
        await show_main_menu(query)
    
    elif query.data.startswith("delete_"):
        api_key = query.data.replace("delete_", "")
        await confirm_delete(query, api_key)
    
    elif query.data.startswith("confirm_delete_"):
        api_key = query.data.replace("confirm_delete_", "")
        await delete_key(query, api_key)

async def generate_key(query) -> None:
    """Génère une clé via l'API StreamFusion"""
    username = query.from_user.username or f"User_{query.from_user.id}"
    
    await query.edit_message_text("⏳ Génération en cours...")
    
    result = StreamFusionAPI.generate_key(username)
    
    if result and 'api_key' in result:
        keyboard = [[InlineKeyboardButton("◀️ Retour au menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Extraire les informations de la réponse
        api_key = result.get('api_key', 'N/A')
        created_at = result.get('created_at', 'N/A')
        
        message = (
            "✅ *Clé API générée avec succès !*\n\n"
            f"🔑 Clé : `{api_key}`\n"
            f"👤 Utilisateur : {username}\n"
            f"📊 Requêtes : Illimitées\n"
            f"⏰ Expiration : Jamais\n"
            f"📅 Créée le : {created_at}\n\n"
            "⚠️ *Conservez cette clé en sécurité !*\n\n"
            "🔗 Utilisez cette clé pour configurer votre addon Stremio avec StreamFusion."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        keyboard = [[InlineKeyboardButton("🔄 Réessayer", callback_data="generate")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Erreur lors de la génération.\n\n"
            "Vérifiez que StreamFusion est bien démarré.",
            reply_markup=reply_markup
        )

async def list_user_keys(query) -> None:
    """Liste les clés de l'utilisateur"""
    username = query.from_user.username or f"User_{query.from_user.id}"
    
    await query.edit_message_text("⏳ Récupération des clés...")
    
    keys = StreamFusionAPI.list_keys(username)
    
    if keys and len(keys) > 0:
        message = f"📊 *Vos clés API StreamFusion*\n\n"
        message += f"Total : {len(keys)} clé(s)\n\n"
        
        keyboard = []
        
        for i, key_info in enumerate(keys[:5], 1):  # Limite à 5 clés
            api_key = key_info.get('api_key', 'N/A')
            created = key_info.get('created_at', 'N/A')
            is_active = key_info.get('is_active', True)
            
            status = "🟢" if is_active else "🔴"
            short_key = f"{api_key[:8]}...{api_key[-8:]}" if len(api_key) > 16 else api_key
            
            message += f"{i}. {status} `{short_key}`\n"
            message += f"   📅 {created}\n\n"
        
        keyboard.append([InlineKeyboardButton("◀️ Retour", callback_data="back_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔑 Générer une clé", callback_data="generate")],
            [InlineKeyboardButton("◀️ Retour", callback_data="back_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📭 Vous n'avez pas encore de clés API.\nGénérez-en une !",
            reply_markup=reply_markup
        )

async def confirm_delete(query, api_key: str) -> None:
    """Demande confirmation avant de supprimer une clé"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmer", callback_data=f"confirm_delete_{api_key}"),
            InlineKeyboardButton("❌ Annuler", callback_data="list_keys")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    short_key = f"{api_key[:8]}...{api_key[-8:]}"
    
    await query.edit_message_text(
        f"⚠️ *Confirmer la suppression ?*\n\n"
        f"Clé : `{short_key}`\n\n"
        f"Cette action est irréversible.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def delete_key(query, api_key: str) -> None:
    """Supprime une clé API"""
    await query.edit_message_text("⏳ Suppression en cours...")
    
    success = StreamFusionAPI.delete_key(api_key)
    
    keyboard = [[InlineKeyboardButton("◀️ Retour", callback_data="list_keys")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if success:
        await query.edit_message_text(
            "✅ Clé supprimée avec succès !",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            "❌ Erreur lors de la suppression.",
            reply_markup=reply_markup
        )

async def show_help(query) -> None:
    """Affiche l'aide"""
    help_text = (
        "🆘 *Aide du bot StreamFusion*\n\n"
        "📋 *Commandes disponibles :*\n"
        "• `/start` - Menu principal\n"
        "• `/generate` - Générer une clé rapidement\n"
        "• `/keys` - Voir vos clés\n"
        "• `/help` - Afficher cette aide\n\n"
        "🔑 *Utilisation des clés :*\n"
        "1. Générez une clé API\n"
        "2. Copiez la clé fournie\n"
        "3. Utilisez-la dans votre configuration Stremio\n\n"
        "💡 *Caractéristiques :*\n"
        "✓ Requêtes illimitées\n"
        "✓ Pas d'expiration\n"
        "✓ Accès complet à StreamFusion\n\n"
        "⚠️ Ne partagez jamais vos clés API !"
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
        [InlineKeyboardButton("🔑 Générer une clé", callback_data="generate")],
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
    """Commande rapide de génération"""
    username = update.message.from_user.username or f"User_{update.message.from_user.id}"
    
    msg = await update.message.reply_text("⏳ Génération en cours...")
    
    result = StreamFusionAPI.generate_key(username)
    
    if result and 'api_key' in result:
        api_key = result.get('api_key')
        await msg.edit_text(
            f"✅ *Clé générée !*\n\n🔑 `{api_key}`\n\n⚠️ Conservez-la en sécurité !",
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text("❌ Erreur de génération. Utilisez /start pour réessayer.")

async def keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande pour compter les clés"""
    username = update.message.from_user.username or f"User_{update.message.from_user.id}"
    
    keys = StreamFusionAPI.list_keys(username)
    
    if keys:
        count = len(keys)
        await update.message.reply_text(
            f"📊 Vous avez *{count}* clé(s) API.\n\nUtilisez /start pour plus de détails.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "📭 Vous n'avez pas encore de clés API.\n\nUtilisez /generate pour en créer une.",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande d'aide"""
    help_text = (
        "🆘 *Aide StreamFusion*\n\n"
        "Utilisez /start pour le menu principal.\n"
        "Utilisez /generate pour créer une clé.\n"
        "Utilisez /keys pour voir vos clés."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

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
        application.add_handler(CommandHandler("help", help_command))
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
