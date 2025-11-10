import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import json
from datetime import datetime

# Configuration
TELEGRAM_TOKEN = "8367979038:AAEw7DuWFFK1mBTyHxc0XOh5Q19uq11FYD8"
API_BASE_URL = "http://127.0.0.1:8082/api/auth"
SECRET_KEY = "testuu"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue"""
    await update.message.reply_text(
        "👋 Bot de gestion des clés API\n\n"
        "Commandes disponibles:\n"
        "/newkey <nom> - Créer une nouvelle clé API\n"
        "/latest - Récupérer la clé la plus récente"
    )

async def create_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Créer une nouvelle clé API"""
    try:
        # Récupérer le nom depuis les arguments
        if not context.args:
            await update.message.reply_text("❌ Usage: /newkey <nom_de_la_cle>")
            return
        
        key_name = " ".join(context.args)
        
        # Debug
        url = f"{API_BASE_URL}/new"
        print(f"🔍 Tentative connexion à: {url}")
        print(f"🔍 Paramètres: name={key_name}, never_expires=true")
        
        # Appel API pour créer la clé
        response = requests.post(
            f"{API_BASE_URL}/new",
            params={"name": key_name, "never_expires": "true"},
            headers={"secret-key": SECRET_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(
                f"✅ Clé créée avec succès!\n\n"
                f"🔑 Nom: {key_name}\n"
                f"🆔 Clé: `{data.get('key', 'N/A')}`\n\n"
                f"(Tap pour copier)",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ Erreur: {response.status_code} - {response.text}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def get_latest_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupérer la clé la plus récente"""
    try:
        # Appel API pour lister les clés
        response = requests.get(
            f"{API_BASE_URL}/list",
            headers={"secret-key": SECRET_KEY}
        )
        
        if response.status_code == 200:
            keys = response.json()
            
            if not keys or len(keys) == 0:
                await update.message.reply_text("ℹ️ Aucune clé trouvée")
                return
            
            # Trouver la clé la plus récente (dernière dans la liste)
            latest_key = keys[-1] if isinstance(keys, list) else keys
            
            await update.message.reply_text(
                f"🔑 Clé la plus récente:\n\n"
                f"📝 Nom: {latest_key.get('name', 'N/A')}\n"
                f"🆔 Clé: `{latest_key.get('key', 'N/A')}`\n"
                f"📅 Créée: {latest_key.get('created_at', 'N/A')}\n\n"
                f"(Tap pour copier)",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ Erreur: {response.status_code} - {response.text}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

def main():
    """Démarrer le bot"""
    # Créer l'application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newkey", create_key))
    application.add_handler(CommandHandler("latest", get_latest_key))
    
    # Démarrer le bot
    print("🤖 Bot démarré...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
