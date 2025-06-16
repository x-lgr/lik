import os
import threading
import requests
import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# Flask App (Keep Alive)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Telegram Bot Config
BOT_TOKEN = os.getenv("TOKEN")  # Set in Render/Heroku env vars
PASTEBIN_RAW_URL = "https://pastebin.com/raw/MmbfWwcY"  # Your auth list
auto_like_tasks = {}  # Stores active auto-like jobs

# Check if user is authorized
async def check_auth(update: Update):
    user_id = str(update.effective_user.id)
    try:
        response = requests.get(PASTEBIN_RAW_URL)
        allowed_users = response.text.strip().splitlines()
        if user_id not in allowed_users:
            await update.message.reply_text("❌ MY SON BINA PAISE K KUCH NHI HOTA,\nDM @xlgr158 50 RUPPESS ONLY USE UNLIMITED TIME")
            return False
        return True
    except:
        await update.message.reply_text("⚠️ Error verifying authorization. Please try later.")
        return False

# Process Likes (With Your Original Messages)
async def process_like(uid: str):
    url = f"https://paid-api-xlgr.vercel.app/like?uid={uid}"
    try:
        res = requests.get(url).json()
        res.pop("credit", None)
        
        if res["status"] == 1:
            return f"""✅ Le Mad@rchod!
👤 Nickname: {res['nickname']}
🌍 Region: {res['region']}
👍 Likes Before: {res['likes_before']}
➕ Likes Added: {res['likes_added']}
🎯 Likes After: {res['likes_after']}
🆔 UID: {res['uid']}
MADE WITH ❤️ BY AAPKA APNA BHADWA DEVELOPER XLGR"""
        elif res["status"] == 2:
            return f"""⚠️ No Likes Added!
🍆Iss Se Jyada Lauda Le Le Mera
👤 Nickname: {res['nickname']}
🆔 UID: {res['uid']}"""
        else:
            return "❌ UID DEKH KR DAAL CHUTIYE!"
    except:
        return "❌ Error processing UID!"

# Auto-Like Daily at 4AM IST
def auto_like_job(context: CallbackContext):
    job = context.job
    uid = job.context['uid']
    chat_id = job.context['chat_id']
    result = process_like(uid)
    context.bot.send_message(chat_id=chat_id, text=f"🔁 AUTO LIKE UPDATE:\n{result}")

# Bot Commands (With Your Original Style)
async def start(update: Update, context: CallbackContext):
    if not await check_auth(update):
        return
    await update.message.reply_text("👋 Welcome! Send /like <uid> to process likes.\nJLDI UID DE KAL SUBH PANWEL NIKLNA HAI")

async def like(update: Update, context: CallbackContext):
    if not await check_auth(update):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a UID.\nUsage: /like <uid>")
        return
    result = await process_like(context.args[0])
    await update.message.reply_text(result)

async def auto_like(update: Update, context: CallbackContext):
    if not await check_auth(update):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a UID.\nUsage: /auto <uid>")
        return
    
    user_id = update.effective_user.id
    uid = context.args[0]
    
    # Remove old job if exists
    if str(user_id) in auto_like_tasks:
        auto_like_tasks[str(user_id)].schedule_removal()
    
    # Schedule new job (4AM Daily IST)
    job = context.job_queue.run_daily(
        auto_like_job,
        time=datetime.time(hour=4, minute=0, tzinfo=pytz.timezone('Asia/Kolkata')),
        days=(0, 1, 2, 3, 4, 5, 6),
        context={'uid': uid, 'chat_id': user_id}
    )
    
    auto_like_tasks[str(user_id)] = job
    await update.message.reply_text(f"""✅ Auto like setup successfully!
🆔 UID: {uid}
⏰ Will run daily at 4 AM IST
Use /stopauto to cancel""")

async def stop_auto(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in auto_like_tasks:
        auto_like_tasks[user_id].schedule_removal()
        del auto_like_tasks[user_id]
        await update.message.reply_text("✅ Auto likes stopped successfully!")
    else:
        await update.message.reply_text("ℹ️ You don't have any active auto like setup.")

# Start Bot
def main():
    # Start Flask in Thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram Bot
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("like", like))
    dp.add_handler(CommandHandler("auto", auto_like))
    dp.add_handler(CommandHandler("stopauto", stop_auto))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
