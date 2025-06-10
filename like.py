import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8119205692:AAGGEp8DMGHFNLXP8Gu1fe0oUP7GZQD_A8g"
PASTEBIN_RAW_URL = "https://pastebin.com/raw/MmbfWwcY"  # Replace with your actual Pastebin URL

async def check_authorization(update: Update):
    """Check if user is authorized via Pastebin list"""
    user_id = str(update.effective_user.id)
    
    try:
        response = requests.get(PASTEBIN_RAW_URL)
        response.raise_for_status()
        allowed_users = response.text.strip().splitlines()
        
        if user_id not in allowed_users:
            await update.message.reply_text("❌ MY SON BINA PAISE K KUCH NHI HOTA.")
            return False
        return True
        
    except Exception as e:
        await update.message.reply_text("⚠️ Error verifying authorization. Please try later.")
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
        await update.message.reply_text("⚠️ Please provide a UID.\nUsage: /like <uid>")
        return

    uid = context.args[0]
    url = f"https://fake-like-api.onrender.com/like?uid={uid}"

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

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("like", process_uid))

    app.run_polling()

if __name__ == "__main__":
    main()