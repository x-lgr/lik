import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Get token from environment variable
BOT_TOKEN = os.getenv("TOKEN")  # Will be set in Render's environment variables
PASTEBIN_RAW_URL = "https://pastebin.com/raw/MmbfWwcY"  # Replace with your actual Pastebin URL

async def check_authorization(update: Update):
    """Check if user is authorized via Pastebin list"""
    user_id = str(update.effective_user.id)
    
    try:
        response = requests.get(PASTEBIN_RAW_URL)
        response.raise_for_status()
        allowed_users = response.text.strip().splitlines()
        
        if user_id not in allowed_users:
            await update.message.reply_text("❌ MY SON BINA PAISE K KUCH NHI HOTA,\nDM @xlgr158 50 RUPPESS ONLY USE UNLIMITED TIME")
            return False
        return True
        
    except Exception as e:
        await update.message.reply_text("⚠ Error verifying authorization. Please try later.")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    await update.message.reply_text("👋 Welcome! Send /like <uid> to process likes.\nJLDI UID DE KAL SUBH PANWEL NIKLNA HAI")

async def process_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # First check authorization
    if not await check_authorization(update):
        return

    if not context.args:
        await update.message.reply_text("⚠ Please provide a UID.\nUsage: /like <uid>")
        return

    uid = context.args[0]
    url = f"https://paid-api-xlgr.vercel.app/like?uid={uid}"

    try:
        response = requests.get(url)
        data = response.json()

        # remove credit
        data.pop("credit", None)
        data.pop("credits", None)

        status = data.get("status")

        if status == 1:
            msg = (
                f"✅ Le Mad@rchod!\n"
                f"👤 Nickname: {data.get('nickname')}\n"
                f"🌍 Region: {data.get('region')}\n"
                f"👍 Likes Before: {data.get('likes_before')}\n"
                f"➕ Likes Added: {data.get('likes_added')}\n"
                f"🎯 Likes After: {data.get('likes_after')}\n"
                f"🆔 UID: {data.get('uid')}\n"
                f"MADE WITH ❤ BY AAPKA APNA BHADWA DEVELOPER XLGR"
            )
        elif status == 2:
            msg = (
                f"⚠ No Likes Added!\n"
                f"🍆Iss Se Jyada Lauda Le Le Mera\n"
                f"👤 Nickname: {data.get('nickname')}\n"
                f"🆔 UID: {data.get('uid')}"
            )
        elif status == 404:
            msg = (
                f"❌ UID DEKH KR DAAL CHUTIYE!\n"
            )
        else:
            msg = "❓ Unknown status received."

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n{str(e)}")

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Telegram bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("like", process_uid))
    bot_app.run_polling()

if _name_ == "_main_":
    main()
