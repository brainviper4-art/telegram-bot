import logging
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import TelegramError

BOT_TOKEN = "8505622938:AAG0iuFpjtVC6p_PuTOHAA7Vmy8fz6qFPOk"
GROUP_ID = -1003966009327
WELCOME_MESSAGE = "✅ Message received! Please wait for our response."
START_MESSAGE = """Hello 👋

Send your MESSAGE now. I will reply ASAP.

Don't just say Hi or Hello, say your problem in one message to avoid extra waiting time and wait for my response.

⚠️Kindly don't delete or block the bot otherwise you will not get a response."""

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
user_topics = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.message.chat.type != "private":
        return
    user = update.effective_user
    message = update.message
    user_id = user.id
    try:
        if user_id not in user_topics:
            topic_name = f"👤 {user.full_name} | {user_id}"
            topic = await context.bot.create_forum_topic(chat_id=GROUP_ID, name=topic_name)
            user_topics[user_id] = topic.message_thread_id
            await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=user_topics[user_id], text=f"🆕 New User\n👤 {user.full_name}\n🆔 {user_id}\n@{user.username or 'N/A'}")
        tid = user_topics[user_id]
        if message.text:
            await context.bot.send_message(chat_id=GROUP_ID, message_thread_id=tid, text=f"💬 {message.text}")
        elif message.photo:
            await context.bot.send_photo(chat_id=GROUP_ID, message_thread_id=tid, photo=message.photo[-1].file_id, caption=message.caption or "")
        elif message.video:
            await context.bot.send_video(chat_id=GROUP_ID, message_thread_id=tid, video=message.video.file_id)
        elif message.document:
            await context.bot.send_document(chat_id=GROUP_ID, message_thread_id=tid, document=message.document.file_id)
        elif message.voice:
            await context.bot.send_voice(chat_id=GROUP_ID, message_thread_id=tid, voice=message.voice.file_id)
        await message.reply_text(WELCOME_MESSAGE)
    except TelegramError as e:
        logging.error(f"Error: {e}")

async def handle_group_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    if message.chat.id != GROUP_ID:
        return
    if not message.message_thread_id:
        return

    # Bot messages ignore karo
    if message.from_user and message.from_user.is_bot:
        return

    tid = message.message_thread_id
    logging.info(f"Group message received in thread: {tid}")
    logging.info(f"Current user_topics: {user_topics}")

    # Memory mein dhundo
    target = next((uid for uid, t in user_topics.items() if t == tid), None)

    # Agar memory mein nahi mila toh topic name se dhundo
    if not target:
        try:
            topic_info = await context.bot.get_forum_topic(GROUP_ID, tid)
            logging.info(f"Topic name: {topic_info.name}")
            match = re.search(r'\| (\d+)', topic_info.name)
            if match:
                target = int(match.group(1))
                user_topics[target] = tid
                logging.info(f"Found user from topic name: {target}")
        except Exception as e:
            logging.error(f"get_forum_topic error: {e}")

    if not target:
        logging.warning(f"No target found for thread {tid}")
        return

    try:
        if message.text:
            await context.bot.send_message(chat_id=target, text=f"📩 Reply:\n{message.text}")
        elif message.photo:
            await context.bot.send_photo(chat_id=target, photo=message.photo[-1].file_id, caption=message.caption or "")
        elif message.video:
            await context.bot.send_video(chat_id=target, video=message.video.file_id)
        elif message.voice:
            await context.bot.send_voice(chat_id=target, voice=message.voice.file_id)
        elif message.document:
            await context.bot.send_document(chat_id=target, document=message.document.file_id)
        logging.info(f"Reply sent to user: {target}")
    except TelegramError as e:
        logging.error(f"Send error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(~filters.ChatType.PRIVATE, handle_group_reply))
    logging.info("✅ Bot chalu ho gaya!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()            
