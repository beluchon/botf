import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configuration
TELEGRAM_BOT_TOKEN = "VOTRE_TOKEN_BOT_TELEGRAM"

# Configuration pour Docker (le bot accède à l'API sur l'hôte)
API_BASE_URL = "http://172.17.0.1:8082"  # IP du Docker bridge pour accéder à l'hôte Linux
API_ENDPOINT = "/api/auth/new"
SECRET_KEY = "testuu"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start - Affiche le menu principal"""
    keyboard = [
        [InlineKeyboardButton("🔑 Créer un nouveau token", callback_data="create_token")],
        [InlineKeyboardButton("📋 Créer token personnalisé", callback_data="create_custom")],
        [InlineKeyboardButton("🔍 Tester la connexion API", callback_data="test_api")],
        [InlineKeyboardButton("ℹ️ Aide", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🤖 *Bot d'Authentification*\n\n"
        "Bienvenue ! Je peux créer des tokens d'authentification pour vous.\n\n"
        "Choisissez une option ci-dessous :"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_token":
        await create_token(query, context, name="token_auto")
    
    elif query.data == "create_custom":
        await query.edit_message_text(
            "📝 Pour créer un token personnalisé, utilisez la commande :\n\n"
            "`/token <nom>`\n\n"
            "Exemple : `/token mon_application`",
            parse_mode="Markdown"
        )
    
    elif query.data == "test_api":
        await test_api_connection(query)
    
    elif query.data == "help":
        help_text = (
            "📖 *Guide d'utilisation*\n\n"
            "🔹 `/start` - Afficher le menu principal\n"
            "🔹 `/token <nom>` - Créer un token avec un nom personnalisé\n\n"
            "Les tokens créés n'expirent jamais par défaut.\n\n"
            "🔒 Vos tokens sont précieux, gardez-les en sécurité !"
        )
        keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    elif query.data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("🔑 Créer un nouveau token", callback_data="create_token")],
            [InlineKeyboardButton("📋 Créer token personnalisé", callback_data="create_custom")],
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

async def create_token(query_or_update, context: ContextTypes.DEFAULT_TYPE, name: str = "test"):
    """Crée un token via l'API"""
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
                f"📝 Nom : `{name}`\n"
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
            error_message = (
                f"❌ *Erreur lors de la création*\n\n"
                f"Code : {response.status_code}\n"
                f"Détails : {response.text}"
            )
            keyboard = [[InlineKeyboardButton("« Retour au menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if isinstance(query_or_update, Update):
                await query_or_update.message.reply_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await query_or_update.edit_message_text(error_message, reply_markup=reply_markup, parse_mode="Markdown")
                
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
        response = requests.post(
            url,
            params={"name": "test_connection", "never_expires": "true"},
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
    """Commande /token <nom> pour créer un token personnalisé"""
    if not context.args:
        await update.message.reply_text(
            "❌ Veuillez spécifier un nom pour le token.\n\n"
            "Exemple : `/token mon_application`",
            parse_mode="Markdown"
        )
        return
    
    token_name = " ".join(context.args)
    await create_token(update, context, name=token_name)

def main():
    """Point d'entrée principal du bot"""
    # Créer l'application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Démarrer le bot
    print("🤖 Bot démarré...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
