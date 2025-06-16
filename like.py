import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
from flask import Flask
import threading
import schedule
import time
from datetime import datetime, time as dtime
import pytz
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Get token from environment variable
BOT_TOKEN = os.getenv("TOKEN")
PASTEBIN_RAW_URL = "https://pastebin.com/raw/MmbfWwcY"

# Dictionary to store auto-like tasks {user_id: {uid: uid, job: job}}
auto_like_tasks = {}

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
        await update.message.reply_text("⚠️ Error verifying authorization. Please try later.")
        return False

async def process_like(uid: str, context: CallbackContext):
    """Process like for a given UID and return result message"""
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
                f"✅ [AUTO LIKE] Le Mad@rchod!\n"
                f"👤 Nickname: {data.get('nickname')}\n"
                f"🌍 Region: {data.get('region')}\n"
                f"👍 Likes Before: {data.get('likes_before')}\n"
                f"➕ Likes Added: {data.get('likes_added')}\n"
                f"🎯 Likes After: {data.get('likes_after')}\n"
                f"🆔 UID: {data.get('uid')}\n"
                f"MADE WITH ❤️ BY AAPKA APNA BHADWA DEVELOPER XLGR"
            )
        elif status == 2:
            msg = (
                f"⚠️ [AUTO LIKE] No Likes Added!\n"
                f"🍆Iss Se Jyada Lauda Le Le Mera\n"
                f"👤 Nickname: {data.get('nickname')}\n"
                f"🆔 UID: {data.get('uid')}"
            )
        elif status == 404:
            msg = (
                f"❌ [AUTO LIKE] UID DEKH KR DAAL CHUTIYE!\n"
            )
        else:
            msg = "❓ [AUTO LIKE] Unknown status received."

        return msg

    except Exception as e:
        return f"❌ [AUTO LIKE] Error:\n{str(e)}"

async def auto_like_job(context: CallbackContext):
    """Job that runs daily to process auto likes"""
    job = context.job
    user_id = job.user_id
    uid = job.uid
    
    try:
        result = await process_like(uid, context)
        await context.bot.send_message(chat_id=user_id, text=result)
    except Exception as e:
        logger.error(f"Error in auto_like_job: {e}")
        await context.bot.send_message(chat_id=user_id, text=f"⚠️ Error processing auto like for UID {uid}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return
    await update.message.reply_text("👋 Welcome! Send /like <uid> to process likes.\nSend /auto <uid> to setup daily auto likes at 4 AM\nJLDI UID DE KAL SUBH PANWEL NIKLNA HAI")

async def process_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_authorization(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please provide a UID.\nUsage: /like <uid>")
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
                f"MADE WITH ❤️ BY AAPKA APNA BHADWA DEVELOPER XLGR"
            )
        elif status == 2:
            msg = (
                f"⚠️ No Likes Added!\n"
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

async def auto_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup daily auto likes at 4 AM"""
    if not await check_authorization(update):
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please provide a UID.\nUsage: /auto <uid>")
        return

    user_id = update.effective_user.id
    uid = context.args[0]

    # Remove any existing job for this user
    if str(user_id) in auto_like_tasks:
        old_job = auto_like_tasks[str(user_id)]['job']
        old_job.schedule_removal()
        del auto_like_tasks[str(user_id)]

    # Schedule new job
    job = context.job_queue.run_daily(
        auto_like_job,
        time=dtime(hour=4, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')),
        days=(0, 1, 2, 3, 4, 5, 6),
        data={'uid': uid},
        user_id=user_id
    )

    # Store the job reference
    auto_like_tasks[str(user_id)] = {'uid': uid, 'job': job}

    await update.message.reply_text(
        f"✅ Auto like setup successfully!\n"
        f"🆔 UID: {uid}\n"
        f"⏰ Will run daily at 4 AM IST\n\n"
        f"Use /stopauto to cancel auto likes"
    )

async def stop_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop auto likes for a user"""
    if not await check_authorization(update):
        return

    user_id = str(update.effective_user.id)

    if user_id in auto_like_tasks:
        job = auto_like_tasks[user_id]['job']
        job.schedule_removal()
        del auto_like_tasks[user_id]
        await update.message.reply_text("✅ Auto likes stopped successfully!")
    else:
        await update.message.reply_text("ℹ️ You don't have any active auto like setup.")

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Telegram bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("like", process_uid))
    bot_app.add_handler(CommandHandler("auto", auto_like))
    bot_app.add_handler(CommandHandler("stopauto", stop_auto))
    
    bot_app.run_polling()

if __name__ == "__main__":
    main()
