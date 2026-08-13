import os
import tempfile
import requests
import json
import asyncio
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ----- КОНФИГУРАЦИЯ -----
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "Ты — Машкара, добрая, ироничная и очень любопытная собеседница. "
    "Ты обожаешь задавать неожиданные вопросы (про суперсилы, странные истории, мечты) "
    "и делиться своими забавными мыслями. Отвечай ярко, с эмодзи, иногда чуть саркастично, "
    "но по-дружески. Ты всегда стремишься узнать о собеседнике что-то новое."
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# -------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Машкара 👋 Задай мне вопрос, и я отвечу текстом, "
        "а потом пришлю голосовое сообщение!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "mistralai/mistral-7b-instruct:free",  # проверенная бесплатная модель
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.9,
            "max_tokens": 300
        }
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
        
        # Детальная диагностика при ошибке
        if response.status_code != 200:
            error_body = response.text
            raise Exception(f"HTTP {response.status_code}: {error_body}")
        
        reply_text = response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        # Отправляем в Telegram подробную ошибку
        error_detail = f"❌ Ошибка: {str(e)}"
        await update.message.reply_text(error_detail)
        print(f"Полная ошибка: {e}")
        return

    await update.message.reply_text(reply_text)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tts = gTTS(reply_text, lang="ru")
            tts.save(tmp_file.name)
            audio_path = tmp_file.name

        with open(audio_path, "rb") as audio:
            await update.message.reply_voice(audio)

        os.remove(audio_path)
    except Exception as e:
        await update.message.reply_text("Не смогла озвучить ответ, но текст я отправила 😅")
        print(f"Ошибка TTS: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот с OpenRouter запущен...")

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(app.run_polling())

if __name__ == "__main__":
    main()
