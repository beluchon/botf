import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import nest_asyncio
import sys
import time
from typing import Optional
import json

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
    def test_connection() -> dict:
        """Test la connexion à StreamFusion"""
        try:
            # Essayer différents endpoints possibles
            endpoints = [
                f"{API_CONFIG['base_url']}/health",
                f"{API_CONFIG['base_url']}/",
                f"{API_CONFIG['base_url']}/api/health"
            ]
            
            results = {}
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=5)
                    results[endpoint] = {
                        "status": response.status_code,
                        "reachable": True
                    }
                except Exception as e:
                    results[endpoint] = {
                        "status": None,
                        "reachable": False,
                        "error": str(e)
                    }
            
            return results
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def generate_key(username: str) -> Optional[dict]:
        """Génère une clé API via l'API StreamFusion"""
        try:
            # Essayer différents formats d'URL
            possible_urls = [
                f"{API_CONFIG['base_url']}/api/auth/new",
                f"{API_CONFIG['base_url']}/auth/new",
                f"{API_CONFIG['base_url']}/api/v1/auth/new"
            ]
            
            for url in possible_urls:
                try:
                    headers = {
                        "secret-key": API_CONFIG['secret_key'],
                        "Content-Type": "application/json"
                    }
                    
                    # Essayer avec params
                    params = {
                        "name": username,
                        "never_expires": "true"
                    }
                    response = requests.post(url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        return {"success": True, "data": response.json(), "url": url}
                    
                    # Essayer avec body JSON
                    data = {
                        "name": username,
                        "never_expires": True
                    }
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    
                    if response.status_code == 200:
                        return {"success": True, "data": response.json(), "url": url}
                    
                except Exception:
                    continue
            
            return {
                "success": False,
                "error": "Aucun endpoint ne fonctionne",
                "tried_urls": possible_urls
            }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def list_keys(username: str) -> Optional[list]:
        """Liste les clés d'un utilisateur via l'API StreamFusion"""
        try:
            possible_urls = [
                f"{API_CONFIG['base_url']}/api/auth/keys",
                f"{API_CONFIG['base_url']}/auth/keys",
                f"{API_CONFIG['base_url']}/api/v1/auth/keys"
            ]
            
            for url in possible_urls:
                try:
                    headers = {"secret-key": API_CONFIG['secret_key']}
                    params = {"name": username}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue
            
            return None
                
        except Exception:
            return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Message de bienvenue avec menu interactif"""
    keyboard = [
        [InlineKeyboardButton("🔑 Générer une clé", callback_data="generate")],
        [InlineKeyboardButton("📊 Mes clés", callback_data="list_keys")],
        [InlineKeyboardButton("🔧 Test connexion", callback_data="test")],
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
    
    elif query.data == "test":
        await test_connection(query)
    
    elif query.data == "help":
        await show_help(query)
    
    elif query.data == "back_menu":
        await show_main_menu(query)

async def test_connection(query) -> None:
    """Test la connexion à StreamFusion"""
    await query.edit_message_text("⏳ Test de connexion...")
    
    results = StreamFusionAPI.test_connection()
    
    message = "🔧 *Test de connexion StreamFusion*\n\n"
    message += f"URL configurée : `{API_CONFIG['base_url']}`\n"
    message += f"Secret Key : `{API_CONFIG['secret_key'][:10]}...`\n\n"
    
    if "error" in results:
        message += f"❌ Erreur : {results['error']}\n"
    else:
        message += "📡 Résultats des tests :\n\n"
        for endpoint, result in results.items():
            if result.get("reachable"):
                status = result.get("status")
                emoji = "✅" if status == 200 else "⚠️"
                message += f"{emoji} {endpoint}\n"
                message += f"   Status: {status}\n\n"
            else:
                message += f"❌ {endpoint}\n"
                message += f"   Erreur: {result.get('error', 'N/A')[:50]}\n\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Retour", callback_data="back_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def generate_key(query) -> None:
    """Génère une clé via l'API StreamFusion"""
    username = query.from_user.username or f"User_{query.from_user.id}"
    
    await query.edit_message_text("⏳ Génération en cours...")
    
    result = StreamFusionAPI.generate_key(username)
    
    if result and result.get('success'):
        keyboard = [[InlineKeyboardButton("◀️ Retour au menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        data = result.get('data', {})
        api_key = data.get('api_key') or data.get('key') or data.get('apiKey', 'N/A')
        created_at = data.get('created_at') or data.get('createdAt', 'N/A')
        
        message = (
            "✅ *Clé API générée avec succès !*\n\n"
            f"🔑 Clé : `{api_key}`\n"
            f"👤 Utilisateur : {username}\n"
            f"📊 Requêtes : Illimitées\n"
            f"⏰ Expiration : Jamais\n"
            f"📅 Créée le : {created_at}\n"
            f"🔗 Endpoint : {result.get('url', 'N/A')}\n\n"
            "⚠️ *Conservez cette clé en sécurité !*\n\n"
            "🔗 Utilisez cette clé pour configurer votre addon Stremio avec StreamFusion."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔧 Test connexion", callback_data="test")],
            [InlineKeyboardButton("🔄 Réessayer", callback_data="generate")],
            [InlineKeyboardButton("◀️ Retour", callback_data="back_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        error_msg = result.get('error', 'Erreur inconnue') if result else "Pas de réponse"
        tried_urls = result.get('tried_urls', []) if result else []
        
        message = (
            "❌ *Erreur lors de la génération*\n\n"
            f"Erreur : `{error_msg}`\n\n"
        )
        
        if tried_urls:
            message += "URLs testées :\n"
            for url in tried_urls:
                message += f"• {url}\n"
            message += "\n"
        
        message += (
            "Vérifiez :\n"
            "• StreamFusion est bien démarré\n"
            "• La SECRET_KEY est correcte\n"
            "• L'URL de l'API est valide\n\n"
            "Utilisez le bouton 'Test connexion' pour diagnostiquer."
        )
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
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
        
        for i, key_info in enumerate(keys[:5], 1):
            api_key = key_info.get('api_key') or key_info.get('key', 'N/A')
            created = key_info.get('created_at') or key_info.get('createdAt', 'N/A')
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
            "📭 Aucune clé trouvée ou erreur de connexion.\n\nGénérez-en une !",
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
        "• `/test` - Tester la connexion à StreamFusion\n"
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
        [InlineKeyboardButton("🔧 Test connexion", callback_data="test")],
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
    
    if result and result.get('success'):
        data = result.get('data', {})
        api_key = data.get('api_key') or data.get('key') or data.get('apiKey', 'N/A')
        await msg.edit_text(
            f"✅ *Clé générée !*\n\n🔑 `{api_key}`\n\n⚠️ Conservez-la en sécurité !",
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text(
            "❌ Erreur de génération.\n\nUtilisez /test pour diagnostiquer le problème."
        )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande de test de connexion"""
    msg = await update.message.reply_text("⏳ Test en cours...")
    
    results = StreamFusionAPI.test_connection()
    
    message = "🔧 *Test de connexion*\n\n"
    message += f"URL : `{API_CONFIG['base_url']}`\n\n"
    
    if "error" in results:
        message += f"❌ {results['error']}"
    else:
        working = sum(1 for r in results.values() if r.get('reachable'))
        message += f"Endpoints testés : {len(results)}\n"
        message += f"Fonctionnels : {working}\n"
    
    await msg.edit_text(message, parse_mode='Markdown')

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
            "📭 Aucune clé trouvée ou erreur de connexion.\n\nUtilisez /generate pour en créer une.",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande d'aide"""
    help_text = (
        "🆘 *Aide StreamFusion*\n\n"
        "Commandes :\n"
        "• /start - Menu principal\n"
        "• /generate - Créer une clé\n"
        "• /keys - Voir vos clés\n"
        "• /test - Test connexion\n"
        "• /help - Cette aide"
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
        application.add_handler(CommandHandler("test", test_command))
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
