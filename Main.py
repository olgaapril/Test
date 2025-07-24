import os
import json
import time
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)

# Загрузка токена и URL из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLIT_URL = os.getenv("REPLIT_URL")

# Резервное значение, если переменные окружения не заданы
if not BOT_TOKEN:
    BOT_TOKEN = "8446903855:AAGJiyssk62cQFtV6zGZ6cRYoNfUhVJXZuI"
if not REPLIT_URL:
    REPLIT_URL = "https://6d40ee08-bff3-4696-8f5a-1c915a35fd6d-00-1e91i4nybwh9i.riker.replit.dev/"

PROGRESS_FILE = "progress.json"

messages = [
    "1️⃣ Шаг 1: Начинаем проект! Подготовься.",
    "2️⃣ Шаг 2: Проверь документы и инструкции.",
    "3️⃣ Шаг 3: Заполни первую форму обратной связи.",
    "4️⃣ Шаг 4: Отметь прогресс в таблице.",
    "5️⃣ Шаг 5: Обсуди вопросы с командой.",
    "6️⃣ Шаг 6: Заверши этап и подготовь отчет."
]

# Flask-сервер для UptimeRobot
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Бот работает и жив!"

# Фоновый автопинг
def keep_alive():
    def ping():
        while True:
            try:
                print("⏱️ Пингуем себя...")
                requests.get(REPLIT_URL)
            except Exception as e:
                print(f"Ошибка при пинге: {e}")
            time.sleep(300)  # каждые 5 минут

    thread = threading.Thread(target=ping)
    thread.daemon = True
    thread.start()

# Работа с прогрессом
def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return {}
    try:
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

def build_keyboard():
    keyboard = [[InlineKeyboardButton("Дальше ▶️", callback_data='next')]]
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext):
    chat = update.effective_chat
    if not chat:
        return
    chat_id = str(chat.id)

    progress = load_progress()
    progress[chat_id] = 0
    save_progress(progress)

    update.message.reply_text(messages[0], reply_markup=build_keyboard())

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    query.answer()

    chat_id = str(query.message.chat.id)
    progress = load_progress()

    if chat_id not in progress:
        query.message.reply_text("Напиши /start чтобы начать рассылку.")
        return

    step = progress[chat_id] + 1

    if step >= len(messages):
        query.message.reply_text("Цепочка сообщений завершена. Спасибо!")
        progress.pop(chat_id)
    else:
        query.message.reply_text(messages[step], reply_markup=build_keyboard())
        progress[chat_id] = step

    save_progress(progress)

def main():
    # Запускаем Flask-сервер в фоне
    threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 8080}, daemon=True).start()

    # Запускаем авто-пинг
    keep_alive()

    # Запускаем Telegram-бота
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler, pattern='next'))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
