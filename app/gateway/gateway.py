import asyncio
import json
import logging
import os

import aio_pika

from dotenv import load_dotenv
from aiogram import Bot, Router, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
QUEUE_NAME = "vpn_tasks"

gateway_router = Router()


def create_inline_keyboard(buttons_dict):
    builder = InlineKeyboardBuilder()

    for text, callback in buttons_dict.items():
        builder.button(text=text, callback_data=callback)

    builder.adjust(1)
    return builder.as_markup()


@gateway_router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Функция для обработки стартовой команды."""

    kb = create_inline_keyboard({
        "🚀 Получить ключ AMNEZIAWG": "get_amneziawg_key",
        "🚀 Получить ключ XRAY": "get_xray_key",
        '🔙 Вскоре тут будет что-то новенькое...': 'pass',
    })

    await message.answer(
        f'Привет, {message.from_user.full_name}! '
        'Я выдаю конфигурации к твоему ВПН. Нажми на',
        reply_markup=kb
        )


@gateway_router.callback_query(F.data == 'get_amneziawg_key')
async def get_amneziawg_key(
    callback: types.CallbackQuery,
    rabbit_channel: aio_pika.Channel
):
    """
    Функция для обработки нажатия кнопки "Получить ключ AMNEZIAWG".
    """

    await callback.message.answer('⏳ Начинаю генерацию ключа AMNEZIAWG...')

    user_data = {
        'telegram_id': callback.from_user.id,
        'username': callback.from_user.username,
        'protocol': 'amneziawg3',
    }

    await rabbit_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(user_data).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=QUEUE_NAME,
    )

    await callback.answer()


@gateway_router.callback_query(F.data == 'get_xray_key')
async def get_xray_key(
    callback: types.CallbackQuery,
    rabbit_channel: aio_pika.Channel
):
    """
    Функция для обработки нажатия кнопки "Получить ключ XRAY".
    """

    await callback.message.answer('⏳ Начинаю генерацию ключа XRAY...')

    user_data = {
        'telegram_id': callback.from_user.id,
        'username': callback.from_user.username,
        'protocol': 'xray',
    }

    await rabbit_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(user_data).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=QUEUE_NAME,
    )

    await callback.answer()


async def main():
    bot = Bot(token=TOKEN)

    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    channel = await connection.channel()

    await channel.declare_queue(
        QUEUE_NAME,
        durable=True
    )

    dp = Dispatcher()
    dp['rabbit_channel'] = channel
    dp.include_router(gateway_router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
