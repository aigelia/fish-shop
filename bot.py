import asyncio
from functools import partial

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, BufferedInputFile
from environs import Env
from redis.asyncio import Redis

from get_products import get_products, download_image


class BotStates(StatesGroup):
    START = State()
    HANDLE_MENU = State()


def get_keyboard(buttons: list, prefix: str = "option"):
    keyboard = []
    for idx, button in enumerate(buttons):
        keyboard.append([InlineKeyboardButton(
            text=button,
            callback_data=f"{prefix}_{idx}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_image_url(product: dict, strapi_base_url: str) -> str:
    try:
        if 'image' in product:
            image_data = product['image']

            if isinstance(image_data, dict) and 'data' in image_data:
                url = image_data['data']['attributes']['url']
            elif isinstance(image_data, dict) and 'url' in image_data:
                url = image_data['url']
            else:
                return None

            if url.startswith('/'):
                return f"{strapi_base_url}{url}"
            return url
    except (KeyError, TypeError) as e:
        print(f"Ошибка при извлечении URL изображения: {e}")

    return None


async def cmd_start(message: Message, state: FSMContext, products: list):
    if not products:
        await message.answer("Извините, товары временно недоступны.")
        return

    product_names = [product.get('title') for product in products]
    reply_markup = get_keyboard(product_names, prefix='product')

    await message.answer(text='Привет! Выберите товар:', reply_markup=reply_markup)
    await state.set_state(BotStates.START)


async def button_handler(
        callback: CallbackQuery,
        state: FSMContext,
        products: list,
        bot: Bot,
        strapi_base_url: str
):
    product_id = int(callback.data.split('_')[1])

    if 0 <= product_id < len(products):
        product = products[product_id]

        caption = (
            f"{product.get('title')} "
            f"({product.get('price')} руб. за кг)\n\n"
            f"{product.get('description')}"
        )

        image_url = get_image_url(product, strapi_base_url)

        await callback.answer()
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        if image_url:
            image_data = download_image(image_url)

            if image_data:
                photo = BufferedInputFile(image_data, filename="product.jpg")

                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=photo,
                    caption=caption
                )
            else:
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=caption
                )
        else:
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=caption
            )

        await state.set_state(BotStates.HANDLE_MENU)
    else:
        await callback.answer("Ошибка: товар не найден")


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

    dp.message.register(
        partial(cmd_start, products=products),
        Command("start")
    )
    dp.callback_query.register(
        partial(button_handler, products=products, bot=bot, strapi_base_url=strapi_base_url),
        F.data.startswith('product_')
    )

    try:
        print("Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await redis_conn.close()


if __name__ == '__main__':
    asyncio.run(main())