import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = "8367979038:AAEw7DuWFFK1mBTyHxc0XOh5Q19uq11FYD8"
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = create_api_key()
    await update.effective_message.reply_text(f"Voici ta nouvelle clé API :\n`{api_key}`", parse_mode="Markdown")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    latest_key = get_latest_api_key()
    await update.effective_message.reply_text(f"Dernière clé API :\n`{latest_key}`", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("latest", latest))

    app.run_polling()

if __name__ == "__main__":
    main()
