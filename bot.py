import os
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

STREAMFUSION_URL = "http://stream-fusion:8080"  # Internal Docker network
SECRET_API_KEY = "testuu"

async def generate_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        name = update.message.from_user.username or f"user_{update.message.from_user.id}"
        
        print(f"🔄 Generating API key for: {name}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{STREAMFUSION_URL}/api/auth/new",
                params={"name": name, "never_expires": "true"},
                headers={"secret-key": SECRET_API_KEY},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"📡 Response status: {response.status}")
                
                if response.status == 200:
                    api_key = await response.text()
                    print(f"✅ Key generated: {api_key}")
                    
                    message = (
                        f"✅ Stream-fusion API Key Generated!\n\n"
                        f"🔑 `{api_key}`\n\n"
                        f"Use this key in your API requests with header:\n"
                        f"`X-API-Key: {api_key}`\n\n"
                        f"Example usage:\n"
                        f"```bash\n"
                        f"curl -H \"X-API-Key: {api_key}\" \\\n"
                        f"  http://localhost:8082/api/streaming/movies\n"
                        f"```"
                    )
                    await update.message.reply_text(message, parse_mode='Markdown')
                    
                else:
                    error_text = await response.text()
                    print(f"❌ API Error: {response.status} - {error_text}")
                    await update.message.reply_text(f"❌ API Error {response.status}: {error_text}")
                    
    except asyncio.TimeoutError:
        await update.message.reply_text("❌ Timeout: Stream-fusion API is not responding")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def my_keys(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        name = update.message.from_user.username or f"user_{update.message.from_user.id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{STREAMFUSION_URL}/api/auth/get_by_name/{name}",
                headers={"secret-key": SECRET_API_KEY},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    keys = await response.json()
                    
                    if keys:
                        message = f"🔑 Your API Keys ({len(keys)}):\n\n"
                        for i, key in enumerate(keys, 1):
                            api_key = key['api_key']
                            created = key.get('created_at', 'Unknown')
                            message += f"{i}. `{api_key}`\n"
                            if created != 'Unknown':
                                message += f"   Created: {created[:10]}\n\n"
                            else:
                                message += "\n"
                    else:
                        message = "❌ No API keys found. Use /generate to create one."
                        
                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    await update.message.reply_text("❌ Could not retrieve your keys")
                    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "👋 Stream-fusion API Key Bot\n\n"
        "Commands:\n"
        "/generate - Create new API key\n"
        "/mykeys - List your API keys\n"
        "/help - Show this message"
    )
    await update.message.reply_text(message)

async def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generate", generate_api_key))
    application.add_handler(CommandHandler("mykeys", my_keys))
    application.add_handler(CommandHandler("help", start))
    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
