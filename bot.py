import os
import requests
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# 🛠️ Configuration
TELEGRAM_TOKEN = os.environ.get("8367979038:AAEw7DuWFFK1mBTyHxc0XOh5Q19uq11FYD8")  # Remplacez par votre token
LOCAL_API_URL = "http://localhost:8082"

# ✅ Fonction pour créer un utilisateur
async def create_user(bot, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # URL pour créer l'utilisateur
    create_url = f"{LOCAL_API_URL}/api/auth/new?name=bot_user&never_expires=true"
    headers = {"secret-key": "testuu"}

    print("🚀 Création de l'utilisateur...")
    try:
        response = requests.post(create_url, headers=headers)
        response.raise_for_status()
        print("✅ Création réussie")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")
        return

    # 🔍 Récupérer la liste des clés
    list_url = f"{LOCAL_API_URL}/api/auth/list"
    list_headers = {"secret-key": "testuu"}

    try:
        list_response = requests.get(list_url, headers=list_headers)
        list_response.raise_for_status()
        data = list_response.json()

        # On suppose que la réponse est une liste d'objets avec un champ "key"
        if isinstance(data, list) and len(data) > 0:
            key = data[0].get("key", "KEY_NOT_FOUND")
            await update.message.reply_text(f"🔑 Clé récupérée : {key}")
        else:
            await update.message.reply_text("⚠️ Aucune clé trouvée.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur lors de la récupération : {e}")

# 📥 Commande /start
async def start_command(bot, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue !\n\n"
        "Cliquez sur le bouton ci-dessous pour obtenir une clé d'authentification.\n"
        "Je créerai un utilisateur et vous retournerai la clé automatiquement."
    )

# 📲 Bouton "Obtenir la clé"
async def get_key_button(bot, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Créer le bouton
    keyboard = [
        [InlineKeyboardButton("Obtenir la clé", callback_data='get_key')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Cliquez sur le bouton pour obtenir la clé.", reply_markup=reply_markup)

# 📦 Commande /key (pour les utilisateurs qui veulent lancer le processus)
async def key_command(bot, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_user(bot, update, context)

# 🧩 Commande /help
async def help_command(bot, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 Commandes disponibles :\n"
        "/start — Démarrer le bot\n"
        "/help — Afficher cette aide\n"
        "/key — Lancer la création de la clé (via commande)\n"
        "👉 Cliquez sur le bouton pour obtenir la clé."
    )

# 🧩 Gestion des messages (si l'utilisateur envoie un message, on l’interprète comme un clic sur le bouton)
# Mais pour simplifier, on va gérer les clics avec le bot

# 🚫 On n’écoute pas les messages, mais on utilise les boutons

# 🎯 On utilise le bot pour gérer les commandes et les clics
# On utilise un handler pour le bouton "Obtenir la clé"

# 🧠 On va ajouter un handler pour les clics sur le bouton
async def handle_callback_query(bot, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'get_key':
        await create_user(bot, update, context)
        await query.answer()  # Répondre au clic

# 🚀 Initialisation
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("key", key_command))

    # Gestion des clics sur les boutons
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Démarrer l'application
    application.run_polling()

if __name__ == "__main__":
    main()
