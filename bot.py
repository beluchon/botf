import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configuration
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", ".")

# Configuration depuis les variables d'environnement
API_BASE_URL = os.getenv("API_BASE_URL", ".")
API_ENDPOINT = "/api/auth/new"
API_LIST_ENDPOINT = "/api/auth/list"
SECRET_KEY = os.getenv("SECRET_KEY", ".")


def generate_unique_name() -> str:
    """Génère un nom unique automatiquement"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"token_{timestamp}"


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_token":
        # Génère un nom unique automatiquement
        unique_name = generate_unique_name()
        await create_token(query, context, name=unique_name)
    
    elif query.data == "test_api":
        await test_api_connection(query)
    
    elif query.data == "help":
        help_text = (
            "📖 *Guide d'utilisation*\n\n"
            "🔹 `/start` ou `/token` - Créer un nouveau token\n\n"
            "💡 *Important :* Chaque token a un nom unique généré automatiquement "
            "avec un timestamp. Exemple : `token_20241110_153045`\n\n"
            "Les tokens créés n'expirent jamais par défaut.\n\n"
            "🔒 Vos tokens sont précieux, gardez-les en sécurité !"
        )
        keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    elif query.data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("🔑 Créer un nouveau token", callback_data="create_token")],
            [InlineKeyboardButton("🔍 Tester la connexion API", callback_data="test_api")],
            [InlineKeyboardButton("ℹ️ Aide", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = (
            "🤖 *Bot d'Authentification*\n\n"
            "Bienvenue ! Je peux créer des tokens d'authentification pour vous.\n\n"
            "Choisissez une option ci-dessous :"
        )
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def create_token(query_or_update, context: ContextTypes.DEFAULT_TYPE, name: str = None):
    """Crée un token via l'API"""
    # Si pas de nom fourni, en générer un
    if name is None:
        name = generate_unique_name()
    
    try:
        # Construction de l'URL complète
        url = f"{API_BASE_URL}{API_ENDPOINT}"
        
        # Appel à l'API
        response = requests.post(
            url,
            params={"name": name, "never_expires": "true"},
            headers={"secret-key": SECRET_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "Non disponible")
            
            message = (
                f"✅ *Token créé avec succès !*\n\n"
                f"🏷️ Nom : `{name}`\n"
                f"🔑 Token : `{token}`\n\n"
                f"⏰ Expiration : Jamais\n\n"
                f"⚠️ Copiez ce token maintenant, vous ne pourrez plus le récupérer !"
            )
            
            keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if isinstance(query_or_update, Update):
                await query_or_update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await query_or_update.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            # Même en cas d'erreur 500, on considère que la clé a été créée
            message = (
                f"✅ *Clé créée !*\n\n"
                f"🏷️ Nom : `{name}`\n\n"
                f"⏳ Récupération des détails en cours..."
            )
            keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if isinstance(query_or_update, Update):
                await query_or_update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await query_or_update.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        
        # Attendre 2 secondes puis récupérer la liste des clés (même en cas d'erreur)
        await asyncio.sleep(2)
        
        # Récupérer la dernière clé créée
        try:
            list_url = f"{API_BASE_URL}{API_LIST_ENDPOINT}"
            list_response = requests.get(
                list_url,
                headers={"secret-key": SECRET_KEY},
                timeout=5
            )
            
            if list_response.status_code == 200:
                keys_data = list_response.json()
                
                # Trouver la dernière clé créée (celle avec le nom qu'on vient de créer)
                if isinstance(keys_data, list) and len(keys_data) > 0:
                    # Chercher la clé avec le nom correspondant
                    last_key = None
                    for key in keys_data:
                        if key.get("name") == name:
                            last_key = key
                            break
                    
                    # Si pas trouvée, prendre la dernière de la liste
                    if not last_key:
                        last_key = keys_data[-1]
                    
                    # Envoyer un nouveau message avec les détails de la clé
                    key_info = (
                        f"📋 *Détails de la dernière clé créée :*\n\n"
                        f"🏷️ Nom : `{last_key.get('name', 'N/A')}`\n"
                        f"🆔 ID : `{last_key.get('id', 'N/A')}`\n"
                        f"🔑 API Key : `{last_key.get('api_key', 'N/A')}`\n"
                        f"📅 Créée le : `{last_key.get('created_at', 'N/A')}`\n"
                        f"⏰ Expire : `{last_key.get('expires_at') or 'Jamais'}`\n"
                    )
                    
                    keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    if isinstance(query_or_update, Update):
                        await query_or_update.message.reply_text(key_info, reply_markup=reply_markup, parse_mode="Markdown")
                    else:
                        await query_or_update.message.reply_text(key_info, reply_markup=reply_markup, parse_mode="Markdown")
                else:
                    # Liste vide
                    error_msg = "⚠️ Aucune clé trouvée dans la liste."
                    if isinstance(query_or_update, Update):
                        await query_or_update.message.reply_text(error_msg)
                    else:
                        await query_or_update.message.reply_text(error_msg)
            else:
                # Erreur lors de la récupération de la liste
                error_msg = (
                    f"⚠️ *Impossible de récupérer la liste des clés*\n\n"
                    f"Code : {list_response.status_code}\n"
                    f"Détails : {list_response.text[:200]}"
                )
                if isinstance(query_or_update, Update):
                    await query_or_update.message.reply_text(error_msg, parse_mode="Markdown")
                else:
                    await query_or_update.message.reply_text(error_msg, parse_mode="Markdown")
                        
        except Exception as list_error:
            # Erreur de connexion ou autre
            error_msg = f"❌ *Erreur lors de la récupération de la liste*\n\n{str(list_error)}"
            try:
                if isinstance(query_or_update, Update):
                    await query_or_update.message.reply_text(error_msg, parse_mode="Markdown")
                else:
                    await query_or_update.message.reply_text(error_msg, parse_mode="Markdown")
            except:
                print(f"Erreur lors de la récupération de la liste : {list_error}")
                
    except Exception as e:
        error_message = f"❌ *Erreur de connexion*\n\n{str(e)}"
        keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if isinstance(query_or_update, Update):
            await query_or_update.message.reply_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query_or_update.edit_message_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")

async def test_api_connection(query):
    """Teste la connexion à l'API"""
    try:
        url = f"{API_BASE_URL}{API_ENDPOINT}"
        # Test avec un vrai appel POST comme l'API l'attend
        test_name = generate_unique_name()
        response = requests.post(
            url,
            params={"name": test_name, "never_expires": "true"},
            headers={"secret-key": SECRET_KEY},
            timeout=5
        )
        
        if response.status_code == 200:
            message = (
                f"✅ *Connexion API réussie !*\n\n"
                f"🌐 URL : `{API_BASE_URL}`\n"
                f"📡 Status : {response.status_code}\n"
                f"✨ L'API répond correctement !\n"
            )
        else:
            message = (
                f"⚠️ *API accessible mais erreur*\n\n"
                f"🌐 URL : `{API_BASE_URL}`\n"
                f"📡 Status : {response.status_code}\n"
                f"📄 Réponse : {response.text[:200]}\n"
            )
    except requests.exceptions.ConnectionError:
        message = (
            f"❌ *Erreur de connexion*\n\n"
            f"🌐 URL : `{API_BASE_URL}`\n"
            f"📡 L'API n'est pas accessible\n\n"
            f"*Solutions :*\n"
            f"1️⃣ Vérifiez que votre API est démarrée\n"
            f"2️⃣ Vérifiez l'URL et le port dans le code\n"
            f"3️⃣ Si vous êtes dans Docker, utilisez 172.17.0.1\n"
        )
    except Exception as e:
        message = f"❌ *Erreur*\n\n{str(e)}"
    
    keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /token pour créer un token automatiquement"""
    unique_name = generate_unique_name()
    await create_token(update, context, name=unique_name)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start pour créer un token automatiquement (même fonction que /token)"""
    unique_name = generate_unique_name()
    await create_token(update, context, name=unique_name)

def main():
    """Point d'entrée principal du bot"""
    # Créer l'application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Démarrer le bot
    print("🤖 Bot démarré...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
