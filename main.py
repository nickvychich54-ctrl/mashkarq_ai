import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from characterai import pycai

print("БОТ ЗАПУСКАЕТСЯ")

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHARACTER_ID = os.getenv("CHARACTER_ID")
CHARACTER_TOKEN = os.getenv("CHARACTER_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


client = pycai.Client(CHARACTER_TOKEN)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! 🤖 Я подключён к Character.AI")


@dp.message()
async def chat(message: Message):
    print("Получено:", message.text)

    try:
        chat = await client.new_chat(CHARACTER_ID)

        answer = await chat.send_message(
            text=message.text
        )

        print("Ответ:", answer)

        await message.answer(str(answer))

    except Exception as e:
        print("ОШИБКА:", repr(e))
        await message.answer(f"Ошибка: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())