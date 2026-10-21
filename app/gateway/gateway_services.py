import json

import aio_pika
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .constants import VPN_QUEUE, ZIP_QUEUE


def create_inline_keyboard(buttons_dict):
    builder = InlineKeyboardBuilder()

    for text, callback in buttons_dict.items():
        builder.button(text=text, callback_data=callback)

    builder.adjust(1)
    return builder.as_markup()


async def request_vpn_key(
    telegram_id,
    username,
    protocol,
    rabbit_channel: aio_pika.Channel
):
    await rabbit_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                'telegram_id': telegram_id,
                'username': username,
                'protocol': protocol,
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=VPN_QUEUE,
    )


async def request_zapret_zip(
    telegram_id,
    rabbit_channel: aio_pika.Channel
):
    await rabbit_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps({
                'telegram_id': telegram_id,
                'username': username,
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key=ZIP_QUEUE,
    )
