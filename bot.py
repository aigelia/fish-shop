import asyncio
from functools import partial

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from environs import Env
from redis.asyncio import Redis

from strapi_helpers import get_products
from handlers import *


def register_handlers(dp: Dispatcher, products: list, bot: Bot, strapi_base_url: str, strapi_token: str):
    dp.message.register(
        partial(cmd_start, products=products),
        Command("start")
    )
    dp.callback_query.register(
        partial(main_menu_handler, products=products, bot=bot, strapi_base_url=strapi_base_url),
        F.data.startswith('product_'),
        BotStates.HANDLE_MENU
    )
    dp.callback_query.register(
        partial(back_to_menu_handler, products=products, bot=bot),
        F.data == 'back_to_menu',
        BotStates.HANDLE_DESCRIPTION
    )
    dp.callback_query.register(
        partial(back_to_menu_handler, products=products, bot=bot),
        F.data == 'back_to_menu',
        BotStates.HANDLE_CART
    )
    dp.callback_query.register(
        partial(add_to_cart_handler, strapi_base_url=strapi_base_url, strapi_token=strapi_token),
        F.data == 'add_to_cart',
        BotStates.HANDLE_DESCRIPTION
    )
    dp.callback_query.register(
        partial(show_cart_handler, strapi_base_url=strapi_base_url, strapi_token=strapi_token, bot=bot),
        F.data == 'show_cart'
    )
    dp.callback_query.register(
        partial(remove_item_handler, strapi_base_url=strapi_base_url, strapi_token=strapi_token, bot=bot),
        F.data.startswith('remove_item_'),
        BotStates.HANDLE_CART
    )


async def main():
    env = Env()
    env.read_env()

    tg_token = env.str("TG_TOKEN")
    redis_host = env.str("DATABASE_HOST", "localhost")
    redis_port = env.int("DATABASE_PORT", 6379)
    redis_password = env.str("DATABASE_PASSWORD", None)
    strapi_url = env.str('STRAPI_URL')
    strapi_token = env.str('STRAPI_TOKEN')
    strapi_base_url = env.str('STRAPI_BASE_URL')

    print("Загрузка продуктов...")
    raw_products = get_products(strapi_url, strapi_token)

    if raw_products and 'data' in raw_products:
        products = raw_products['data']
        print(f"Загружено товаров: {len(products)}")
    else:
        print("Не удалось загрузить товары, бот не будет запущен.")
        return

    redis_conn = Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=False
    )

    bot = Bot(token=tg_token)
    storage = RedisStorage(redis=redis_conn)
    dp = Dispatcher(storage=storage)

    register_handlers(dp, products, bot, strapi_base_url, strapi_token)

    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await redis_conn.close()


if __name__ == '__main__':
    asyncio.run(main())
