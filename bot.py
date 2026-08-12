import os
import tempfile
import requests
import json
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ----- КОНФИГУРАЦИЯ -----
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Личность Машкары (та же, что была)
SYSTEM_PROMPT = (
    "Ты — Машкара, добрая, ироничная и очень любопытная собеседница. "
    "Ты обожаешь задавать неожиданные вопросы (про суперсилы, странные истории, мечты) "
    "и делиться своими забавными мыслями. Отвечай ярко, с эмодзи, иногда чуть саркастично, "
    "но по-дружески. Ты всегда стремишься узнать о собеседнике что-то новое."
)

# URL OpenRouter API
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# -------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Машкара 👋 Задай мне вопрос, и я отвечу текстом, "
        "а потом пришлю голосовое сообщение!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # 1. Получаем ответ от OpenRouter (Gemini Flash бесплатно)
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "google/gemini-1.5-flash",  # бесплатная модель
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.9,
            "max_tokens": 300
        }
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        reply_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply_text = "Ой, у меня сейчас лапки... Попробуй ещё раз!"
        print(f"Ошибка OpenRouter: {e}")

    # 2. Отправляем текст
    await update.message.reply_text(reply_text)

    # 3. Отправляем голосовое через gTTS
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tts = gTTS(reply_text, lang="ru")
            tts.save(tmp_file.name)
            audio_path = tmp_file.name

        with open(audio_path, "rb") as audio:
            await update.message.reply_voice(audio)

        os.remove(audio_path)
    except Exception as e:
        await update.message.reply_text("Не смогла озвучить ответ 😅")
        print(f"Ошибка TTS: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот с OpenRouter запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
