import os
import json
import requests
import asyncio
from datetime import datetime
from io import BytesIO

# Latest Library Imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    ChatJoinRequestHandler,
    CommandHandler, 
    ChatMemberHandler
)

# Bandwidth aur Error fix ke liye zaroori import
from telegram.constants import ChatMemberStatus

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
APK_URL = os.environ.get("APK_URL")
VIP_CHANNEL_URL = os.environ.get("VIP_CHANNEL_URL")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
LEAVE_MSG_URL = os.environ.get("LEAVE_MSG_URL")

USERS_FILE = "users.json"
APK_FILE = "jai_club_premium.apk"
WELCOME_IMAGE_URL = "https://kommodo.ai/i/lk66ZvAY1u3vzHXU9aLN"
LEAVE_IMAGE_URL = "https://kommodo.ai/i/UTlTK3RUQvuCGsM1aCLS"

# Global Cache for File ID (Bandwidth Saver)
APK_FILE_ID = None 

# ================= USERS DATA =================
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except Exception:
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

# ================= APK DOWNLOAD (Once) =================
def fetch_apk():
    if os.path.exists(APK_FILE):
        print("APK local storage mein pehle se hai ✅")
        return
    try:
        if APK_URL:
            print("GitHub se APK download ho raha hai...")
            res = requests.get(APK_URL, stream=True, timeout=120)
            res.raise_for_status()
            with open(APK_FILE, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("APK successfully download ho gaya ✅")
    except Exception as e:
        print(f"Download Error: {e}")

# ================= SEND APK LOGIC =================
async def send_apk(user_id, context):
    global APK_FILE_ID
    
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("GET SECRET APK ✅", url=f"https://t.me/{BOT_USERNAME}?start=apk")]
    ])
    
    caption = (
        "✅ 100% BEST APK IN WHOLE TELEGRAM 💥\n\n"
        "( ONLY FOR PREMIUM USERS ⚡️ )\n\n"
        "FOR HELP : @KD_HACK_MANAGER"
    )

    try:
        # File ID use karein (0 MB Render Bandwidth)
        if APK_FILE_ID:
            await context.bot.send_document(chat_id=user_id, document=APK_FILE_ID, caption=caption, reply_markup=btn)
            return

        # Pehli baar upload karein aur ID save karein
        if os.path.exists(APK_FILE):
            with open(APK_FILE, 'rb') as f:
                msg = await context.bot.send_document(
                    chat_id=user_id, 
                    document=f, 
                    filename="jai club premium.apk", 
                    caption=caption, 
                    reply_markup=btn
                )
                APK_FILE_ID = msg.document.file_id
                print(f"New File ID Cached: {APK_FILE_ID}")
    except Exception as e:
        print(f"Send APK Error: {e}")

# ================= HANDLERS =================
async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    try:
        users = load_users()
        add_user(user, users)
        
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 VIP CHANNEL LINK 🔥", url=VIP_CHANNEL_URL)]])
        
        await context.bot.send_photo(
            chat_id=user.id, 
            photo=WELCOME_IMAGE_URL, 
            caption=" ✅ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗞𝗗 𝗧𝗥𝗔𝗗𝗘𝗥𝗦 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗕𝗢𝗧 ⚡️", 
            reply_markup=btn
        )
        await send_apk(user.id, context)
        await update.chat_join_request.decline()
    except Exception as e:
        print(f"Join Handler Error: {e}")

async def track_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        m = update.chat_member
        if m.old_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] and \
           m.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            
            user = m.from_user
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("JOIN CHANNEL 🔥", url=LEAVE_MSG_URL)]])
            
            await context.bot.send_photo(
                chat_id=user.id, 
                photo=LEAVE_IMAGE_URL, 
                caption="🙌 CONGRATULATIONS 🎉 APKO AB YE SARE FREE MELNE WALA HAI ES CHANNEL ME 👇🏻", 
                reply_markup=btn
            )
    except Exception:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    add_user(user, users)
    
    if context.args and context.args[0] == "apk":
        await send_apk(user.id, context)
    else:
        await update.message.reply_text("Click button to get APK 🔥")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to broadcast!")
        return
    
    users = load_users()
    msg = update.message.reply_to_message
    count = 0
    
    for u in users:
        try:
            await msg.copy(chat_id=u["id"])
            count += 1
            await asyncio.sleep(0.05)
        except:
            continue
    await update.message.reply_text(f"Broadcast sent to {count} users ✅")

# ================= MAIN RUNNER =================
def main():
    fetch_apk()
    
    # Intents fix: v20+ me aise likhte hain
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatJoinRequestHandler(join_request))
    app.add_handler(ChatMemberHandler(track_leave, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
