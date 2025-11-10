import os
import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration du logging basique sans fichier
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Récupération des variables d'environnement
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')

# Validation des variables obligatoires
required_vars = {
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'API_BASE_URL': API_BASE_URL,
    'SECRET_KEY': SECRET_KEY
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
    exit(1)

print("🤖 FatherBot initialisation...")
print(f"📍 API Base URL: {API_BASE_URL}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande /start"""
    welcome_text = """
🤖 **FatherBot - Générateur d'API Key**

Commandes disponibles:
/start - Afficher ce message
/generate - Générer une nouvelle API key
/list - Lister les API keys existantes
/help - Aide

Envoyez "generate nom_utilisateur" pour créer une API key personnalisée.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande /help"""
    help_text = """
📖 **Aide FatherBot**

Ce bot permet de générer et gérer les API keys pour votre application.

**Commandes:**
- `/generate` - Génère une API key avec un nom par défaut
- `/generate <nom>` - Génère une API key avec un nom spécifique
- `/list` - Liste les API keys existantes
- `/help` - Affiche cette aide

**Exemples:**
`generate mon_app`
`generate utilisateur_test`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def generate_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE, username="telegram_user"):
    """Fonction pour générer une API key"""
    try:
        # Construction de l'URL complète
        api_url = f"{API_BASE_URL}/api/auth/new"
        
        # Paramètres de la requête
        params = {
            'name': username,
            'never_expires': 'true'
        }
        
        headers = {
            'secret-key': SECRET_KEY
        }
        
        print(f"🔑 Génération API key pour: {username}")
        
        # Envoi de la requête POST
        response = requests.post(api_url, params=params, headers=headers, timeout=30)
        
        print(f"📡 Réponse API: {response.status_code}")
        
        if response.status_code == 200:
            # Récupération de l'API key depuis la réponse
            api_data = response.json()
            api_key = api_data.get('key', 'Clé non trouvée dans la réponse')
            
            success_message = f"""
✅ **API Key générée avec succès!**

👤 **Utilisateur:** `{username}`
🔑 **API Key:** `{api_key}`

⚠️ **Important:** Gardez cette clé en sécurité et ne la partagez pas!
            """
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
            print(f"✅ API key générée pour {username}")
            
        elif response.status_code == 400:
            error_data = response.json()
            error_message = f"""
❌ **Erreur lors de la génération**

L'utilisateur `{username}` existe déjà ou la requête est invalide.

Détail: {error_data.get('error', 'Erreur inconnue')}
            """
            await update.message.reply_text(error_message, parse_mode='Markdown')
            
        else:
            error_message = f"""
❌ **Erreur API**

Code: {response.status_code}
Message: {response.text}

Vérifiez que l'API est accessible à: {API_BASE_URL}
            """
            await update.message.reply_text(error_message)
            print(f"❌ Erreur API: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        error_message = f"""
❌ **Erreur de connexion**

Impossible de se connecter à l'API à l'adresse:
`{API_BASE_URL}`

Vérifiez que:
• L'API est démarrée
• L'URL est correcte
• Le réseau est accessible
        """
        await update.message.reply_text(error_message, parse_mode='Markdown')
        print(f"❌ Connexion impossible à: {API_BASE_URL}")
        
    except requests.exceptions.Timeout:
        error_message = """
❌ **Timeout**

L'API n'a pas répondu dans le temps imparti.
Veuillez réessayer plus tard.
        """
        await update.message.reply_text(error_message)
        print("❌ Timeout de l'API")
        
    except Exception as e:
        error_message = f"""
❌ **Erreur inattendue**

{str(e)}
        """
        await update.message.reply_text(error_message)
        print(f"❌ Erreur inattendue: {e}")

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande /generate avec ou sans argument"""
    if context.args:
        username = ' '.join(context.args)
        await generate_api_key(update, context, username)
    else:
        await generate_api_key(update, context, "telegram_user")

async def list_keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la commande /list pour lister les clés existantes"""
    try:
        # Cette endpoint peut varier selon votre API
        list_url = f"{API_BASE_URL}/api/auth/keys"
        headers = {'secret-key': SECRET_KEY}
        
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            keys_data = response.json()
            if keys_data:
                keys_list = "\n".join([f"• {key.get('name', 'Sans nom')}: `{key.get('key', 'N/A')}`" 
                                     for key in keys_data])
                message = f"🔑 **Clés API existantes:**\n\n{keys_list}"
            else:
                message = "📭 Aucune clé API trouvée."
                
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Impossible de récupérer la liste des clés.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")
        print(f"❌ Erreur liste clés: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les messages texte"""
    text = update.message.text.strip()
    
    if text.lower().startswith('generate'):
        parts = text.split(' ', 1)
        username = parts[1] if len(parts) > 1 else "telegram_user"
        await generate_api_key(update, context, username)
    else:
        await update.message.reply_text(
            "Envoyez 'generate' pour créer une API key, ou /help pour l'aide."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les erreurs"""
    print(f"❌ Erreur: {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Une erreur s'est produite. Veuillez réessayer."
        )

def main():
    """Fonction principale"""
    try:
        # Création de l'application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Gestionnaires de commandes
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("generate", generate_command))
        application.add_handler(CommandHandler("list", list_keys_command))
        
        # Gestionnaire de messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Gestionnaire d'erreurs
        application.add_error_handler(error_handler)
        
        # Démarrage du bot
        print("🚀 FatherBot démarré avec succès!")
        print(f"📍 API Base: {API_BASE_URL}")
        print(f"🔐 Secret Key: {'*' * len(SECRET_KEY)}")
        
        print("=" * 50)
        print("🤖 FatherBot est opérationnel!")
        print("=" * 50)
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Erreur critique au démarrage: {e}")
        exit(1)

if __name__ == '__main__':
    main()
