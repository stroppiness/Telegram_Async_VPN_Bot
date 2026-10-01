import asyncio
import json
import os
import logging

import aio_pika
from aiogram import Bot
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
RABBITMQ_URL = os.getenv(
    'RABBITMQ_URL',
    'amqp://guest:guest@rabbitmq/'
)

RESPONSE_QUEUE = 'vpn_responses'


bot = Bot(token=TOKEN)


async def send_vpn_config(message: aio_pika.IncomingMessage):
    logger.info(
        f"Получено сообщение из {RESPONSE_QUEUE}, "
        f"delivery_tag={message.delivery_tag}"
    )

    async with message.process():
        payload = json.loads(message.body.decode())

        telegram_id = payload.get('telegram_id')
        vpn_key = payload.get('vpn_key')
        error = payload.get('error')

        logger.info(
            f"Получен результат для telegram_id={telegram_id}"
        )

        logger.info(
            f"Отправляю VPN-конфигурацию пользователю "
            f"telegram_id={telegram_id}"
        )

        print('Отправляю в Telegram:', telegram_id)

        if error == 'cooldown':
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    'С момена последнего запроса ещё не прошло трёх дней! '
                    'Ты сможешь запросить ещё один ключ,'
                    'когда три дня истекут 🧐'
                )
            )
            return

        if error in ('delete_failed', 'create_failed'):
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    'Не смог получить ключик, но чуть попозже '
                    'всё обязательно получится!'
                )
            )

        await bot.send_message(
            chat_id=telegram_id,
            text=vpn_key,
        )

        await bot.send_message(
            chat_id=telegram_id,
            text='Нажми "/start" или воспользуйся меню команд',
        )

        logger.info(
            f"VPN-конфигурация успешно отправлена пользователю "
            f"telegram_id={telegram_id}"
        )


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    queue = await channel.declare_queue(
        RESPONSE_QUEUE,
        durable=True,
    )

    await queue.consume(send_vpn_config)

    try:
        await asyncio.Future()
    finally:
        await connection.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
