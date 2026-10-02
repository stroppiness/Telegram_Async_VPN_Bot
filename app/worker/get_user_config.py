import asyncio
import json
import logging
import os
from datetime import timedelta

import aio_pika
import aiohttp
from dotenv import load_dotenv
from tortoise.timezone import now

from .database.database import close_db, init_db
from .database.models import User, VPNKeys
from .constants import (VPN_QUEUE, ZIP_QUEUE, RESPONSE_QUEUE,
                        ZIP_RESPONSE_QUEUE, CLIENT_ENDPOINT)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_URL = os.getenv('API_URL')
API_KEY = os.getenv('FASTIFY_API_KEY')
RABBITMQ_URL = os.getenv('RABBITMQ_URL')


async def get_zapret_release(
    message: aio_pika.IncomingMessage,
    channel: aio_pika.Channel
):
    async with message.process():
        try:
            payload = json.loads(message.body.decode())

            username = payload.get('username')

            telegram_id = payload.get('telegram_id')

            user = await User.get_or_none(
                telegram_id=telegram_id,
            )

            if user is None:
                user = await User.create(
                    telegram_id=telegram_id,
                    username=username,
                )

            response_data = {
                'telegram_id': telegram_id,
                'action': 'download_zapret',
                'version': None,
                'download_url': None,
                'file_name': None,
                'error': None,
            }

            api_url = (
                'https://api.github.com/'
                'repos/Flowseal/zapret-discord-youtube/releases/latest'
            )

            headers = {'User-Agent': 'Telegram-Bot-App'}

            async with aiohttp.ClientSession(
                headers=headers
            ) as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        logger.error(
                            f'GitHub API вернул статус {response.status}'
                        )
                        response_data['error'] = 'github_error'

                    else:
                        release_data = await response.json()

                        assets = release_data.get('assets', [])

                        for asset in assets:
                            if asset.get(
                                'name', ''
                            ).endswith('.zip'):
                                response_data['version'] = (
                                    release_data.get('tag_name')
                                )
                                response_data['download_url'] = (
                                    asset.get('browser_download_url')
                                )
                                response_data['file_name'] = (
                                    asset.get('name')
                                )
                                break

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response_data).encode(),
                    delivery_mode=(
                        aio_pika.DeliveryMode.PERSISTENT
                    )
                ),
                routing_key=ZIP_RESPONSE_QUEUE
            )

        except Exception as e:
            logger.error(
                f'Ошибка при получении релиза Zapret: {e}'
            )
            logger.exception(
                'Ошибка при получении релиза Zapret'
            )


async def create_user_config(
    message: aio_pika.IncomingMessage,
    channel: aio_pika.Channel
):
    async with message.process():
        try:

            payload = json.loads(message.body.decode())

            telegram_id = payload.get('telegram_id')
            username = payload.get('username')
            protocol = payload.get('protocol')

            user = await User.get_or_none(
                telegram_id=telegram_id,
            )

            create_payload = {
                'clientName': username,
                'protocol': protocol,
                'expiresAt': None,
            }

            delete_payload = {
                'clientId': None,
                'protocol': protocol,
            }

            headers = {
               'x-api-key': API_KEY,
               'Content-Type': 'application/json'
            }

            response_data = {
                'telegram_id': telegram_id,
                'vpn_key': None,
                'error': None
            }

            can_create = True

            if user is None:
                user = await User.create(
                    telegram_id=telegram_id,
                    username=username,
                )

            if user is not None:
                last_key = await VPNKeys.filter(
                    user_id=telegram_id,
                    protocol=protocol,
                ).order_by('-created_at').first()

                if last_key:
                    elapsed = now() - last_key.created_at

                    if elapsed < timedelta(days=3):
                        response_data['error'] = 'cooldown'
                        can_create = False

            if can_create:

                async with aiohttp.ClientSession(headers=headers) as session:
                    try:

                        async with session.get(
                            f'{API_URL}/{CLIENT_ENDPOINT}',
                        ) as response:
                            data = await response.json()

                            client_id = None

                            for client in data['items']:
                                if client['username'] == username:
                                    client_id = client['peers'][0]['id']
                                    break

                            delete_payload['clientId'] = client_id

                        async with session.delete(
                            f'{API_URL}/{CLIENT_ENDPOINT}',
                            json=delete_payload,
                        ) as response:

                            delete_success = True

                            if response.status not in (200, 400, 404):
                                error_text = await response.text()
                                logger.error(
                                    f'Ошибка сервера:{
                                        response.status
                                    }: '
                                    f'{error_text}'
                                )
                                response_data['error'] = 'delete_failed'

                                delete_success = False

                        if delete_success is True:

                            async with session.post(
                                f'{API_URL}/{CLIENT_ENDPOINT}',
                                json=create_payload,
                            ) as response:

                                if response.status == 200:
                                    data = await response.json()
                                    vpn_key = data.get(
                                        'client', {}
                                    ).get('config')

                                    response_data['vpn_key'] = vpn_key

                                    if vpn_key is not None:
                                        user = await User.get(
                                            telegram_id=telegram_id
                                        )
                                        await VPNKeys.create(
                                            key_text=vpn_key,
                                            user_id=user,
                                            protocol=protocol
                                        )

                                else:
                                    error_text = await response.text()
                                    logger.error(
                                        f'Ошибка сервера:{
                                            response.status
                                        }: '
                                        f'{error_text}'
                                    )
                                    response_data['error'] = 'create_failed'

                    except aiohttp.ClientError as e:
                        logger.error(f'Ошибка сетевого подключения: {e}')
                        return

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(response_data).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=RESPONSE_QUEUE
            )

        except Exception as e:
            logger.error(f'Критическая ошибка в воркере: {e}')
            logger.exception('Критическая ошибка в воркере')
            return


async def main():
    await init_db()

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    await channel.declare_queue(
        RESPONSE_QUEUE,
        durable=True
    )

    await channel.declare_queue(
        ZIP_RESPONSE_QUEUE,
        durable=True
    )

    queue = await channel.declare_queue(
        VPN_QUEUE,
        durable=True
    )

    zapret_queue = await channel.declare_queue(
        ZIP_QUEUE,
        durable=True
    )

    await queue.consume(lambda message: create_user_config(message, channel))

    await zapret_queue.consume(
        lambda message: get_zapret_release(message, channel)
    )

    try:
        await asyncio.Future()
    finally:
        await connection.close()
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())
