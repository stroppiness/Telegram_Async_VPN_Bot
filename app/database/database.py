from tortoise import Tortoise

from app.database.config import TORTOISE_ORM


async def init_db():
    print('1. Начинаю Tortoise.init()')
    await Tortoise.init(config=TORTOISE_ORM)
    print('2. Tortoise.init() завершён')
    await Tortoise.generate_schemas()
    print('3. generate_schemas() завершён')


async def close_db():
    await Tortoise.close_connections()
