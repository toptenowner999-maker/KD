import os
import json
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    ChatJoinRequestHandler,
    CommandHandler, 
    ChatMemberHandler
)
from telegram.constants import ChatMemberStatus

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
LEAVE_MSG_URL = os.environ.get("LEAVE_MSG_URL")

# OWNER CONFIG
ADMIN_ID = 7303219901  

# Direct Video URL aur Caption
WELCOME_VIDEO_URL = "https://kommodo.ai/i/TWuoP7QT7CBfjDFN5Dtd" 
WELCOME_VIDEO_CAPTION = (
    "💰How To Activate Vip Hack💰\n"
    "Pls Video Ko Pura Dekhna\n"
    "      💯 Setup Video 💯"
)

# APK File ID (Screenshot ke hisaab se 4658)
APK_FILE_ID = "4658" 

USERS_FILE = "users.json"
LEAVE_IMAGE_URL = "https://kommodo.ai/i/UTlTK3RUQvuCGsM1aCLS"
VIDEO_FILE_ID_CACHE = None 

# ================= DATA MANAGEMENT =================
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
    except: pass
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_user(user):
    users = load_users()
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id, 
            "username": user.username, 
            "first_name": user.first_name, 
            "joined_at": datetime.now().isoformat()
        })
        save_users(users)

# ================= HANDLERS =================
async def send_apk(user_id, context):
    apk_caption = "✅ 100% BEST APK IN WHOLE TELEGRAM 💥\n\n( ONLY FOR PREMIUM USERS ⚡️ )\n\nFOR HELP : @KD_HACK_MANAGER"
    
    try:
        await context.bot.send_document(
            chat_id=user_id, 
            document=APK_FILE_ID, 
            caption=apk_caption
        )
    except Exception as e:
        print(f"APK ID Error: {e}. Please check if the Message ID {APK_FILE_ID} is correct.")

async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global VIDEO_FILE_ID_CACHE
    request = update.chat_join_request
    user = request.from_user
    
    try:
        # --- NO AUTO APPROVE ---
        # Request pending rahegi, bot sirf user ko DM bhejega
        add_user(user)
        
        # Welcome Video bhejna
        if VIDEO_FILE_ID_CACHE:
            await context.bot.send_video(chat_id=user.id, video=VIDEO_FILE_ID_CACHE, caption=WELCOME_VIDEO_CAPTION)
        else:
            msg = await context.bot.send_video(chat_id=user.id, video=WELCOME_VIDEO_URL, caption=WELCOME_VIDEO_CAPTION)
            VIDEO_FILE_ID_CACHE = msg.video.file_id
        
        # APK bhejna
        await send_apk(user.id, context)
        
    except Exception as e:
        print(f"Join Handler Error: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return 
    users = load_users()
    await update.message.reply_text(f"📊 **BOT STATISTICS** 📊\n\nTotal Users: {len(users)}\nStatus: Running 24/7 ✅")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message:
        await update.message.reply_text("Kisi message ko reply karke /broadcast likho!")
        return
    
    users = load_users()
    msg = update.message.reply_to_message
    sent = 0
    status_msg = await update.message.reply_text("🚀 Broadcasting...")

    for u in users:
        try:
            await msg.copy(chat_id=u["id"])
            sent += 1
            await asyncio.sleep(0.05)
        except: continue
    
    await status_msg.edit_text(f"✅ Broadcast complete! Sent to {sent} users.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)
    await update.message.reply_text(f"Hello {user.first_name}! Your request is pending. Check below for setup video and APK.")
    await send_apk(user.id, context)

async def track_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        m = update.chat_member
        if m.old_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] and \
           m.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            user = m.from_user
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("JOIN CHANNEL 🔥", url=LEAVE_MSG_URL)]])
            await context.bot.send_photo(chat_id=user.id, photo=LEAVE_IMAGE_URL, caption="🙌 CONGRATULATIONS 🎉 APKO AB YE SARE FREE MELNE WALA HAI ES CHANNEL ME 👇🏻", reply_markup=btn)
    except: pass

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(ChatJoinRequestHandler(join_request))
    app.add_handler(ChatMemberHandler(track_leave, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    print(f"Bot Active - Requests will stay PENDING")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
