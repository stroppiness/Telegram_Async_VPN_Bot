import asyncio
import json
import logging
import os

import aio_pika
from aiogram import Bot
from aiogram.types import URLInputFile
from dotenv import load_dotenv

from .constants import RESPONSE_QUEUE, ZIP_RESPONSE_QUEUE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')

bot = Bot(token=TOKEN)


async def send_zapret_zip(message: aio_pika.IncomingMessage):
    """
    Функция для получения документа из rabbitMQ и отправки ответа пользователю.
    """
    logger.info(
        f'Получено сообщение из {ZIP_RESPONSE_QUEUE}, '
        f'delivery_tag={message.delivery_tag}'
    )

    async with message.process():
        payload = json.loads(message.body.decode())

        telegram_id = payload.get('telegram_id')
        download_url = payload.get('download_url')
        file_name = payload.get('file_name')
        version = payload.get('version')
        error = payload.get('error')

        if error:
            await bot.send_message(
                telegram_id,
                'Не смог получить архив. Попробуй позже!'
            )
            return

        archive = URLInputFile(
            download_url,
            filename=file_name
        )

        await bot.send_document(
            chat_id=telegram_id,
            document=archive,
            caption=(
                f'📂 Актуальная версия: '
                f'<b>{version}</b>'
            ),
            parse_mode='HTML'
        )


async def send_vpn_config(message: aio_pika.IncomingMessage):
    """
    Функция для получения конфигурации из rabbitMQ и
    отправки ответа пользователю.
    """
    logger.info(
        f'Получено сообщение из {RESPONSE_QUEUE}, '
        f'delivery_tag={message.delivery_tag}'
    )

    async with message.process():
        payload = json.loads(message.body.decode())

        telegram_id = payload.get('telegram_id')
        vpn_key = payload.get('vpn_key')
        error = payload.get('error')

        logger.info(
            f'Получен результат для telegram_id={telegram_id}'
        )

        logger.info(
            f'Отправляю VPN-конфигурацию пользователю '
            f'telegram_id={telegram_id}'
        )

        print('Отправляю в Telegram:', telegram_id)

        if error == 'cooldown':
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    'С момента последнего запроса ещё не прошло трёх дней! '
                    'Ты сможешь запросить ещё один ключ,'
                    'когда три дня истекут 🧐'
                )
            )
            return

        if vpn_key is None or error in ('delete_failed', 'create_failed'):
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    'Не смог получить ключик, но чуть попозже '
                    'всё обязательно получится!'
                )
            )
            return

        await bot.send_message(
            chat_id=telegram_id,
            text=vpn_key,
        )

        await bot.send_message(
            chat_id=telegram_id,
            text='Нажми "/start" или воспользуйся меню команд',
        )

        logger.info(
            f'VPN-конфигурация успешно отправлена пользователю '
            f'telegram_id={telegram_id}'
        )


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    queue = await channel.declare_queue(
        RESPONSE_QUEUE,
        durable=True,
    )

    zapret_queue = await channel.declare_queue(
        ZIP_RESPONSE_QUEUE,
        durable=True
    )

    await queue.consume(send_vpn_config)
    await zapret_queue.consume(send_zapret_zip)

    try:
        await asyncio.Future()
    finally:
        await connection.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
