import asyncio
import logging
import os
import aiosqlite

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database import init_db, close_db
from app.models import User, VPNKeys

from app.get_user_configuration import create_user_config

load_dotenv()

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

    user = await User.get_or_none(
        telegram_id=message.from_user.id,
    )

    if user is None:
        user = await User.create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

    kb = create_inline_keyboard({
        "🚀 Получить ключ AMNEZIAWG": "get_amneziawg_key",
        "🚀 Получить ключ XRAY": "get_xray_key",
        '🔙 Обновить ключ AMNEZIAWG': 'restore_amneziawg_key',
        '🔙 Обновить ключ XRAY': 'restore_xray_key',
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
        '🚀 Получить ключ XRAY': 'get_xray_key',
        '🔙 Обновить ключ AMNEZIAWG': 'restore_amneziawg_key',
        '🔙 Обновить ключ XRAY': 'restore_xray_key',
    })

    username = callback.from_user.username
    telegram_id = callback.from_user.id

    status_message = await bot.send_message(
        chat_id=telegram_id, text="⏳ Начинаю генерацию ключа..."
    )
    vpn_key = await create_user_config(
        telegram_id,
        username,
        protocol='amneziawg3',
    )

    if vpn_key is None:
        await bot.send_message(
            chat_id=telegram_id,
            text='Создание ключа не удалось. Попробуйте позже.'
        )

    else:

        user = await User.get(
            telegram_id=telegram_id
        )
        await VPNKeys.create(
            key_text=vpn_key,
            user_id=user,
        )

        await bot.send_message(
            chat_id=telegram_id,
            text=rf"✅ Ваш ключ готов:\n`{vpn_key}`\."
            "Скопируйте его и вставьте в AmneziaVPN",
            reply_markup=kb,
            parse_mode='MarkdownV2',
        )

        await bot.delete_message(
            chat_id=telegram_id, message_id=status_message.message_id
        )

        await callback.answer(
            text="Ключ успешно сгенерирован",
        )


@dp.callback_query(F.data == 'get_xray_key')
async def get_xray_key(callback: types.CallbackQuery):
    pass


@dp.callback_query(F.data == 'restore_amneziawg_key')
async def restore_amneziawg_key(callback: types.CallbackQuery):
    pass


@dp.callback_query(F.data == 'restore_xray_key')
async def restore_xray_key(callback: types.CallbackQuery):
    pass


async def main():
    await init_db()

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())
