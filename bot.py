import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configuration
BOT_TOKEN = "TON_TOKEN_TELEGRAM_ICI"
API_URL_NEW = "http://localhost:8082/api/auth/new"
API_URL_LIST = "http://localhost:8082/api/auth/list"
API_SECRET_KEY = "testuu"

def create_api_key():
    headers = {"secret-key": API_SECRET_KEY}
    params = {"name": "bot_user", "never_expires": "true"}
    try:
        response = requests.post(API_URL_NEW, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("api_key", "Clé non trouvée dans la réponse")
    except Exception as e:
        return f"Erreur : {str(e)}"

def get_latest_api_key():
    headers = {"secret-key": API_SECRET_KEY}
    try:
        response = requests.get(API_URL_LIST, headers=headers)
        response.raise_for_status()
        data = response.json()
        keys = data.get("keys", [])
        if keys:
            latest = keys[-1]
            return latest.get("api_key", "Clé non trouvée")
        else:
            return "Aucune clé trouvée dans la liste."
    except Exception as e:
        return f"Erreur : {str(e)}"

def start(update: Update, context: CallbackContext):
    api_key = create_api_key()
    update.effective_message.reply_text(f"Voici ta nouvelle clé API :\n`{api_key}`", parse_mode="Markdown")

def latest(update: Update, context: CallbackContext):
    latest_key = get_latest_api_key()
    update.effective_message.reply_text(f"Dernière clé API :\n`{latest_key}`", parse_mode="Markdown")

def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("latest", latest))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
