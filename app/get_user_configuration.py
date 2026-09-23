import asyncio
import aiohttp
import os

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

API_URL = os.getenv('API_URL')
API_KEY = os.getenv('FASTIFY_API_KEY')


async def create_user_config(telegram_id, username, protocol, endpoint='clients'):

    payload = {
        "clientName": username,
        "protocol": protocol,
        "expiresAt": None,
    }

    headers = {
       "x-api-key": API_KEY,
       "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.post(f'{API_URL}/{endpoint}', json=payload) as response:

                if response.status == 200:
                    data = await response.json()
                    vpn_config = data.get('client', {}).get('config')

                    return vpn_config

                else:
                    error_text = await response.text()
                    return (
                        f'Ошибка сервера:{HTTPStatus.INTERNAL_SERVER_ERROR}: '
                        f'{error_text}'
                    )

        except aiohttp.ClientError as e:
            return(f'Ошибка сетевого подключения: {e}')
