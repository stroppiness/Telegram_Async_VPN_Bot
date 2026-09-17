import asyncio
import logging
import os
import aiosqlite

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bd_init import init_db, DB_NAME

load_dotenv()
init_db()

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()


def create_inline_keyboard(buttons_dict):
    builder = InlineKeyboardBuilder()
    for text, callback in buttons_dict.items():
        builder.button(text=text, callback_data=callback)
    builder.adjust(1)
    return builder.as_markup()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Функция для обработки стартовой команды."""

    if not message.from_user:
        return

    tg_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (tg_id,)) as cursor:
            user_exists = await cursor.fetchone()

        if not user_exists:
            await db.execute(
                "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
                (tg_id, username, first_name)
            )
            await db.commit()

    kb = create_inline_keyboard({
        "🚀 Получить ключ AMNEZIAWG": "get_amneziawg_key",
        "🚀 Получить ключ XRAY": "get_xray_key"
    })

    await message.answer(
        f'Привет, {message.from_user.full_name}! '
        'Я выдаю конфигурации к твоему ВПН. Нажми на',
        reply_markup=kb
        )


@dp.callback_query(F.data == 'get_amneziawg_key')
async def get_amneziawg_key(callback: types.CallbackQuery):
    """
    Функция для обработки нажатия кнопки "Получить токен".
    """

    kb = create_inline_keyboard({
        "🚀 Получить ключ XRAY": "get_xray_key"
    })

    user_id = callback.from_user.id
    status_message = await bot.send_message(
        chat_id=user_id, text="⏳ Начинаю генерацию ключа..."
    )
    vpn_key = "vless://example-key-data-here..."

    await bot.send_message(
        chat_id=user_id,
        text=rf"✅ Ваш ключ готов:\n`{vpn_key}`\."
        "Скопируйте его и вставьте в AmneziaVPN",
        reply_markup=kb,
        parse_mode='MarkdownV2',
    )

    await bot.send_message(
        chat_id=user_id,
        text='Тест',
        parse_mode='MarkdownV2',
    )

    await bot.delete_message(
        chat_id=user_id, message_id=status_message.message_id
    )

    await callback.answer(
        text="Ключ успешно сгенерирован",
    )


@dp.callback_query(F.data == 'get_xray_key')
async def get_xray_key(callback: types.CallbackQuery):
    pass


async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
