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
                        "reachable": True,
                        "content": response.text[:100] if response.text else "No content"
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
                    print(f"🔧 Tentative avec l'URL: {url}")
                    
                    headers = {
                        "secret-key": API_CONFIG['secret_key'],
                        "Content-Type": "application/json"
                    }
                    
                    # Essayer avec body JSON
                    data = {
                        "name": username,
                        "never_expires": True
                    }
                    
                    print(f"📤 Envoi des données: {data}")
                    print(f"🔑 Secret key utilisée: {API_CONFIG['secret_key'][:10]}...")
                    
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    
                    print(f"📥 Réponse reçue - Status: {response.status_code}")
                    print(f"📄 Contenu de la réponse: {response.text[:200]}...")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            print(f"✅ JSON parsé: {response_data}")
                            return {
                                "success": True, 
                                "data": response_data, 
                                "url": url,
                                "raw_response": response.text
                            }
                        except json.JSONDecodeError as e:
                            print(f"❌ Erreur JSON: {e}")
                            return {
                                "success": False,
                                "error": f"Erreur JSON: {str(e)}",
                                "raw_response": response.text
                            }
                    
                    # Essayer avec params si JSON échoue
                    params = {
                        "name": username,
                        "never_expires": "true"
                    }
                    response = requests.post(url, headers=headers, params=params, timeout=10)
                    
                    print(f"📥 Réponse (params) - Status: {response.status_code}")
                    print(f"📄 Contenu (params): {response.text[:200]}...")
                    
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            return {
                                "success": True, 
                                "data": response_data, 
                                "url": url,
                                "raw_response": response.text
                            }
                        except json.JSONDecodeError as e:
                            return {
                                "success": False,
                                "error": f"Erreur JSON: {str(e)}",
                                "raw_response": response.text
                            }
                            
                except requests.exceptions.RequestException as e:
                    print(f"❌ Erreur requête pour {url}: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Erreur inattendue pour {url}: {e}")
                    continue
            
            return {
                "success": False,
                "error": "Aucun endpoint ne fonctionne",
                "tried_urls": possible_urls
            }
                
        except Exception as e:
            print(f"💥 Erreur globale: {e}")
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
                    
                    print(f"🔍 Liste des clés - URL: {url}, User: {username}")
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    
                    print(f"📥 Réponse liste - Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        keys_data = response.json()
                        print(f"✅ Clés trouvées: {keys_data}")
                        return keys_data
                except Exception as e:
                    print(f"❌ Erreur liste clés pour {url}: {e}")
                    continue
            
            return None
                
        except Exception as e:
            print(f"💥 Erreur globale liste clés: {e}")
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
                message += f"   Status: {status}\n"
                message += f"   Content: {result.get('content', 'N/A')}\n\n"
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
    
    print(f"🎯 Résultat de génération: {result}")
    
    if result and result.get('success'):
        keyboard = [[InlineKeyboardButton("◀️ Retour au menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        data = result.get('data', {})
        
        # Extraire la clé API de différentes manières possibles
        api_key = None
        possible_key_fields = ['api_key', 'key', 'apiKey', 'token', 'access_token', 'apikey']
        
        for field in possible_key_fields:
            if field in data:
                api_key = data[field]
                print(f"✅ Clé trouvée dans le champ '{field}': {api_key}")
                break
        
        if not api_key:
            # Si aucun champ standard ne contient la clé, afficher tout le JSON pour débogage
            print(f"🔍 Aucun champ standard trouvé. Données complètes: {data}")
            api_key = "NON_TROUVÉE - Voir les logs"
        
        created_at = data.get('created_at') or data.get('createdAt') or data.get('timestamp', 'N/A')
        
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
        
        # Ajouter des informations de débogage si nécessaire
        if api_key == "NON_TROUVÉE - Voir les logs":
            message += f"\n\n🔧 *Debug Info:*\n```{json.dumps(data, indent=2)}```"
        
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
        raw_response = result.get('raw_response', 'N/A')
        tried_urls = result.get('tried_urls', []) if result else []
        
        message = (
            "❌ *Erreur lors de la génération*\n\n"
            f"Erreur : `{error_msg}`\n\n"
        )
        
        if raw_response and raw_response != 'N/A':
            message += f"📄 Réponse brute : `{raw_response[:100]}...`\n\n"
        
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
    
    print(f"🔑 Clés récupérées pour {username}: {keys}")
    
    if keys and len(keys) > 0:
        message = f"📊 *Vos clés API StreamFusion*\n\n"
        message += f"Total : {len(keys)} clé(s)\n\n"
        
        keyboard = []
        
        for i, key_info in enumerate(keys[:5], 1):
            # Extraire la clé de différentes manières
            api_key = None
            possible_key_fields = ['api_key', 'key', 'apiKey', 'token', 'access_token', 'apikey']
            
            for field in possible_key_fields:
                if field in key_info:
                    api_key = key_info[field]
                    break
            
            if not api_key:
                api_key = "NON_TROUVÉE"
            
            created = key_info.get('created_at') or key_info.get('createdAt') or key_info.get('timestamp', 'N/A')
            is_active = key_info.get('is_active', True)
            
            status = "🟢" if is_active else "🔴"
            short_key = f"{api_key[:8]}...{api_key[-8:]}" if len(api_key) > 16 and api_key != "NON_TROUVÉE" else api_key
            
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
    
    print(f"🎯 Résultat de génération (commande): {result}")
    
    if result and result.get('success'):
        data = result.get('data', {})
        
        # Extraire la clé API de différentes manières possibles
        api_key = None
        possible_key_fields = ['api_key', 'key', 'apiKey', 'token', 'access_token', 'apikey']
        
        for field in possible_key_fields:
            if field in data:
                api_key = data[field]
                break
        
        if api_key:
            await msg.edit_text(
                f"✅ *Clé générée !*\n\n🔑 `{api_key}`\n\n⚠️ Conservez-la en sécurité !",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"❌ Clé générée mais format inattendu.\n\nDonnées reçues: ```{json.dumps(data, indent=2)}```",
                parse_mode='Markdown'
            )
    else:
        error_msg = result.get('error', 'Erreur inconnue') if result else "Pas de réponse"
        await msg.edit_text(
            f"❌ Erreur de génération: {error_msg}\n\nUtilisez /test pour diagnostiquer le problème."
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
        message += f"Fonctionnels : {working}\n\n"
        
        for endpoint, result in results.items():
            if result.get('reachable'):
                status = result.get('status')
                emoji = "✅" if status == 200 else "⚠️"
                message += f"{emoji} {endpoint}\n"
            else:
                message += f"❌ {endpoint}\n"
    
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
        
        print("🤖 Bot StreamFusion démarré...")
        print(f"🔗 URL API: {API_CONFIG['base_url']}")
        print(f"🔑 Secret Key: {API_CONFIG['secret_key'][:10]}...")
        
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except Exception as e:
        print(f"💥 Erreur critique: {e}")
        sys.exit(1)

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("👋 Arrêt du bot...")
            break
        except Exception as e:
            print(f"💥 Erreur redémarrage: {e}")
            time.sleep(60)
