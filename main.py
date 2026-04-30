from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Intents
from telegram.ext import (
    ApplicationBuilder, ContextTypes, ChatJoinRequestHandler,
    CommandHandler, ChatMemberHandler
)
import json
import os
import requests
from datetime import datetime
import asyncio

BOT_TOKEN = os.environ.get("BOT_TOKEN")
APK_URL = os.environ.get("APK_URL") # GitHub ka RAW link dalna yaha
VIP_CHANNEL_URL = os.environ.get("VIP_CHANNEL_URL")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
LEAVE_MSG_URL = os.environ.get("LEAVE_MSG_URL")

USERS_FILE = "users.json"
APK_FILE = "jai_club_premium.apk"

WELCOME_IMAGE_URL = "https://kommodo.ai/i/lk66ZvAY1u3vzHXU9aLN"
LEAVE_IMAGE_URL = "https://kommodo.ai/i/UTlTK3RUQvuCGsM1aCLS"

# Yahan hum Telegram ka file_id save karenge taaki bandwidth na lage
APK_FILE_ID = None 

# ================= USERS =================
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_user(user, users):
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "joined_at": datetime.now().isoformat()
        })
        save_users(users)

# ================= APK CACHE (From GitHub) =================
def fetch_apk():
    # Render par jab bot start hoga, sirf 1 baar GitHub se download karega
    if os.path.exists(APK_FILE):
        print("APK already on disk ✅")
        return
        
    try:
        if APK_URL:
            print("Downloading APK from GitHub once...")
            res = requests.get(APK_URL, stream=True, timeout=120)
            res.raise_for_status()
            with open(APK_FILE, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("APK downloaded & saved locally ✅")
    except Exception as e:
        print("APK error:", e)

# ================= SEND APK (Bandwidth Saver) =================
async def send_apk(user_id, context):
    global APK_FILE_ID

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("GET SECRET APK ✅", url=f"https://t.me/{BOT_USERNAME}?start=apk")]
    ])

    caption_text = (
        "✅ 100% BEST APK IN WHOLE TELEGRAM 💥\n\n"
        "( ONLY FOR PREMIUM USERS ⚡️ )\n\n"
        "FOR HELP : @KD_HACK_MANAGER"
    )

    try:
        # MAGIC 🪄: Agar file_id already save hai, toh direct Telegram server se bhejo (0 MB Render Bandwidth used)
        if APK_FILE_ID:
            await context.bot.send_document(
                chat_id=user_id,
                document=APK_FILE_ID,
                caption=caption_text,
                reply_markup=btn
            )
            return

        # Agar bot restart hua hai aur file_id nahi hai, toh 1st user ke liye Render se upload karo
        if not os.path.exists(APK_FILE):
            print("APK File hi nahi mili!")
            return

        with open(APK_FILE, 'rb') as file:
            message = await context.bot.send_document(
                chat_id=user_id,
                document=file,
                filename="jai club premium.apk",
                caption=caption_text,
                reply_markup=btn
            )
            # Pehli baar upload hone par jo id mili, usko save kar lo sab aage aane wale users ke liye
            APK_FILE_ID = message.document.file_id
            print(f"File uploaded to Telegram successfully! Cached File ID: {APK_FILE_ID}")

    except Exception as e:
        print("Error sending APK:", e)

# ================= JOIN REQUEST =================
async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user

    try:
        users = load_users()
        add_user(user, users)

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 VIP CHANNEL LINK 🔥", url=VIP_CHANNEL_URL)]
        ])

        # Pehle DM send kro
        await context.bot.send_photo(
            chat_id=user.id,
            photo=WELCOME_IMAGE_URL,
            caption=" ✅ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗞𝗗 𝗧𝗥𝗔𝗗𝗘𝗥𝗦 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗕𝗢𝗧 ⚡️",
            reply_markup=btn
        )
        
        # Fir APK bhejo (Ye automatically file_id cache use karega)
        await send_apk(user.id, context)

        # Pending clear karne ke liye decline kar do
        await update.chat_join_request.decline()

    except Exception as e:
        print("Join error:", e)

# ================= LEAVE TRACK =================
async def track_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = update.chat_member
        if member.old_chat_member.status in ["member", "administrator"] and member.new_chat_member.status in ["left", "kicked"]:
            user = member.from_user

            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("JOIN CHANNEL 🔥", url=LEAVE_MSG_URL)]
            ])

            await context.bot.send_photo(
                chat_id=user.id,
                photo=LEAVE_IMAGE_URL,
                caption="🙌 CONGRATULATIONS 🎉 APKO AB YE SARE FREE MELNE WALA HAI ES CHANNEL ME 👇🏻",
                reply_markup=btn
            )

    except Exception as e:
        pass

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to message to broadcast")
        return

    users = load_users()
    msg = update.message.reply_to_message

    sent = 0
    for u in users:
        try:
            await msg.copy(chat_id=u["id"])
            sent += 1
            await asyncio.sleep(0.05)
        except:
            continue

    await update.message.reply_text(f"Broadcast sent to {sent} users ✅")

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    add_user(user, users)

    if context.args and context.args[0] == "apk":
        await send_apk(user.id, context)
    else:
        await update.message.reply_text("Click button to get APK 🔥")

# ================= MAIN =================
def main():
    fetch_apk()
    
    intents = Intents.default()
    intents.chat_member = True
    intents.message_content = True
    
    app = ApplicationBuilder().token(BOT_TOKEN).intents(intents).build()

    app.add_handler(ChatJoinRequestHandler(join_request))
    app.add_handler(ChatMemberHandler(track_leave, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
