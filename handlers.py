from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, BufferedInputFile

from strapi_helpers import download_image, get_or_create_cart, add_product_to_cart


class BotStates(StatesGroup):
    START = State()
    HANDLE_MENU = State()
    HANDLE_DESCRIPTION = State()


def get_keyboard(buttons: list, prefix: str = "option"):
    keyboard = []
    for idx, button in enumerate(buttons):
        keyboard.append([InlineKeyboardButton(
            text=button,
            callback_data=f"{prefix}_{idx}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_keyboard():
    keyboard = [
        [InlineKeyboardButton(
            text="Добавить в корзину",
            callback_data="add_to_cart"
        )],
        [InlineKeyboardButton(
            text="Назад",
            callback_data="back_to_menu"
        )]
    ]
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
    await state.set_state(BotStates.HANDLE_MENU)


async def main_menu_handler(
        callback: CallbackQuery,
        state: FSMContext,
        products: list,
        bot: Bot,
        strapi_base_url: str
):
    product_id = int(callback.data.split('_')[1])

    if 0 <= product_id < len(products):
        product = products[product_id]

        await state.update_data(current_product_document_id=product.get('documentId'))

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
                    caption=caption,
                    reply_markup=get_back_keyboard()
                )
            else:
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=caption,
                    reply_markup=get_back_keyboard()
                )
        else:
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=caption,
                reply_markup=get_back_keyboard()
            )

        await state.set_state(BotStates.HANDLE_DESCRIPTION)
    else:
        await callback.answer("Ошибка: товар не найден")


async def back_to_menu_handler(callback: CallbackQuery, state: FSMContext, products: list, bot: Bot):
    product_names = [product.get('title') for product in products]
    reply_markup = get_keyboard(product_names, prefix='product')

    await callback.answer()
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text='Выберите товар:',
        reply_markup=reply_markup
    )
    await state.set_state(BotStates.HANDLE_MENU)


async def add_to_cart_handler(callback: CallbackQuery, state: FSMContext, strapi_base_url: str, strapi_token: str):
    telegram_id = callback.from_user.id

    cart = get_or_create_cart(strapi_base_url, strapi_token, telegram_id)

    if not cart:
        await callback.answer("Ошибка при создании корзины", show_alert=True)
        return

    user_data = await state.get_data()
    product_document_id = user_data.get('current_product_document_id')

    if not product_document_id:
        await callback.answer("Ошибка: товар не выбран", show_alert=True)
        return

    cart_document_id = cart['documentId']
    cart_item = add_product_to_cart(strapi_base_url, strapi_token, cart_document_id, product_document_id, quantity=1.0)

    if cart_item:
        await callback.answer("Товар добавлен в корзину!")
    else:
        await callback.answer("Ошибка при добавлении товара в корзину", show_alert=True)
