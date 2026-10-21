import asyncio
import logging
import os

import aio_pika
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from dotenv import load_dotenv

from .constants import VPN_QUEUE, ZIP_QUEUE
from .gateway_services import (create_inline_keyboard, request_vpn_key,
                               request_zapret_zip)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq/')

gateway_router = Router()


@gateway_router.message(Command('start'))
async def cmd_start(message: types.Message):
    """Функция для обработки стартовой команды."""

    kb = create_inline_keyboard({
        '🚀 Получить ключ AMNEZIAWG': 'get_amneziawg_key',
        '🚀 Получить ключ XRAY': 'get_xray_key',
        '📲 Скачать последнюю версию Zapret': 'download_zapret',
    })

    await message.answer(
        f'Привет, {message.from_user.full_name}! '
        'Я выдаю конфигурации к твоему ВПН. Нажми на '
        'интересующую кнопку или воспользуйся меню!',
        reply_markup=kb
        )


@gateway_router.message(Command('zip'))
async def get_zapret_command(message, rabbit_channel: aio_pika.Channel):
    """
    Функция для обработки команды "/zip".
    """

    await message.answer('⏳Запрашиваю архив...')

    await request_zapret_zip(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        rabbit_channel=rabbit_channel
        )


@gateway_router.callback_query(F.data == 'download_zapret')
async def get_zapret_zip(
    callback: types.CallbackQuery,
    rabbit_channel: aio_pika.Channel
):
    """
    Функция для обработки нажатия кнопки "Скачать последнюю версию Zapret".
    """

    await callback.answer('⏳Запрашиваю архив...')

    await request_zapret_zip(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        rabbit_channel=rabbit_channel
        )

    await callback.answer()


@gateway_router.message(Command('amneziawg'))
async def get_amneziawg_command(message, rabbit_channel: aio_pika.Channel):
    """
    Функция для обработки команды "/amneziawg".
    """

    await message.answer('⏳ Начинаю генерацию ключа AMNEZIAWG...')

    await request_vpn_key(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        protocol='amneziawg3',
        rabbit_channel=rabbit_channel
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

    await request_vpn_key(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        protocol='amneziawg3',
        rabbit_channel=rabbit_channel
    )

    await callback.answer()


@gateway_router.message(Command('xray'))
async def get_xray_command(message, rabbit_channel: aio_pika.Channel):
    """
    Функция для обработки команды "/xray".
    """

    await message.answer('⏳ Начинаю генерацию ключа AMNEZIAWG...')

    await request_vpn_key(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        protocol='amneziawg3',
        rabbit_channel=rabbit_channel
    )


@gateway_router.callback_query(F.data == 'get_xray_key')
async def get_xray_key(
    callback: types.CallbackQuery,
    rabbit_channel: aio_pika.Channel
):
    """
    Функция для обработки нажатия кнопки "Получить ключ XRAY".
    """

    await callback.message.answer('⏳ Начинаю генерацию ключа XRAY...')

    await request_vpn_key(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        protocol='xray',
        rabbit_channel=rabbit_channel
    )

    await callback.answer()


async def main():
    bot = Bot(token=TOKEN)

    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    channel = await connection.channel()

    await channel.declare_queue(
        VPN_QUEUE,
        durable=True
    )

    await channel.declare_queue(
        ZIP_QUEUE,
        durable=True
    )

    dp = Dispatcher()
    dp['rabbit_channel'] = channel
    dp.include_router(gateway_router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
