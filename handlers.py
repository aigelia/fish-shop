from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    BufferedInputFile
)

from strapi_helpers import *


class BotStates(StatesGroup):
    START = State()
    HANDLE_MENU = State()
    HANDLE_DESCRIPTION = State()
    HANDLE_CART = State()
    WAITING_EMAIL = State()


def get_keyboard(buttons: list, prefix: str = "option"):
    keyboard = []
    for idx, button in enumerate(buttons):
        keyboard.append([InlineKeyboardButton(
            text=button,
            callback_data=f"{prefix}_{idx}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="Моя корзина",
        callback_data="show_cart"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_keyboard():
    keyboard = [
        [InlineKeyboardButton(
            text="Добавить в корзину",
            callback_data="add_to_cart"
        )],
        [InlineKeyboardButton(
            text="Моя корзина",
            callback_data="show_cart"
        )],
        [InlineKeyboardButton(
            text="Назад",
            callback_data="back_to_menu"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cart_keyboard(cart_items: list):
    keyboard = []
    for item in cart_items:
        product = item.get('product')
        if product:
            title = product.get('title', 'Товар')
            item_document_id = item.get('documentId')
            keyboard.append([InlineKeyboardButton(
                text=f"Удалить {title}",
                callback_data=f"remove_item_{item_document_id}"
            )])

    keyboard.append([InlineKeyboardButton(
        text="Оплатить",
        callback_data="pay"
    )])
    keyboard.append([InlineKeyboardButton(
        text="В меню",
        callback_data="back_to_menu"
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_empty_cart_keyboard():
    keyboard = [[InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_menu"
    )]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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


async def back_to_menu_handler(
        callback: CallbackQuery,
        state: FSMContext,
        products: list,
        bot: Bot
):
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


async def add_to_cart_handler(
        callback: CallbackQuery,
        state: FSMContext,
        strapi_base_url: str,
        strapi_token: str
):
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
    cart_item = add_product_to_cart(
        strapi_base_url,
        strapi_token,
        cart_document_id,
        product_document_id,
        quantity=1.0
    )

    if cart_item:
        await callback.answer("Товар добавлен в корзину!")
    else:
        await callback.answer("Ошибка при добавлении товара в корзину", show_alert=True)


async def show_cart_handler(
        callback: CallbackQuery,
        state: FSMContext,
        strapi_base_url: str,
        strapi_token: str,
        bot: Bot
):
    telegram_id = callback.from_user.id

    cart = get_cart_with_items(strapi_base_url, strapi_token, telegram_id)

    await callback.answer()
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )

    if not cart or not cart.get('items'):
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="Ваша корзина пуста",
            reply_markup=get_empty_cart_keyboard()
        )
        await state.set_state(BotStates.HANDLE_CART)
        return

    cart_text = "Ваша корзина:\n\n"
    total_price = 0

    for item in cart['items']:
        product = item.get('product')
        quantity = item.get('quantity', 0)

        if product:
            title = product.get('title', 'Неизвестный товар')
            price = product.get('price', 0)
            item_total = price * quantity
            total_price += item_total

            cart_text += f"{title}\n"
            cart_text += f"{quantity} кг × {price} руб. = {item_total} руб.\n\n"

    cart_text += f"Итого: {total_price} руб."

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=cart_text,
        reply_markup=get_cart_keyboard(cart['items'])
    )

    await state.set_state(BotStates.HANDLE_CART)


async def remove_item_handler(
        callback: CallbackQuery,
        state: FSMContext,
        strapi_base_url: str,
        strapi_token: str,
        bot: Bot
):
    item_document_id = callback.data.split('_')[2]

    success = remove_cart_item(strapi_base_url, strapi_token, item_document_id)

    if success:
        telegram_id = callback.from_user.id
        cart = get_cart_with_items(strapi_base_url, strapi_token, telegram_id)

        await callback.answer("Товар удален из корзины")
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        if not cart or not cart.get('items'):
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text="Ваша корзина пуста",
                reply_markup=get_empty_cart_keyboard()
            )
            await state.set_state(BotStates.HANDLE_CART)
            return

        cart_text = "Ваша корзина:\n\n"
        total_price = 0

        for item in cart['items']:
            product = item.get('product')
            quantity = item.get('quantity', 0)

            if product:
                title = product.get('title', 'Неизвестный товар')
                price = product.get('price', 0)
                item_total = price * quantity
                total_price += item_total

                cart_text += f"{title}\n"
                cart_text += f"{quantity} кг × {price} руб. = {item_total} руб.\n\n"

        cart_text += f"Итого: {total_price} руб."

        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=cart_text,
            reply_markup=get_cart_keyboard(cart['items'])
        )
    else:
        await callback.answer("Ошибка при удалении товара", show_alert=True)


async def pay_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Для оформления заказа, пожалуйста, отправьте вашу электронную почту:"
    )
    await state.set_state(BotStates.WAITING_EMAIL)


async def email_handler(
        message: Message,
        state: FSMContext,
        strapi_base_url: str,
        strapi_token: str
):
    email = message.text
    telegram_id = message.from_user.id
    username = message.from_user.username

    customer = create_customer(strapi_base_url, strapi_token, telegram_id, email, username)

    if customer:
        cart = get_cart_with_items(strapi_base_url, strapi_token, telegram_id)
        if cart:
            link_cart_to_customer_and_complete(
                strapi_base_url,
                strapi_token,
                cart['documentId'],
                customer['documentId']
            )
    await message.answer(
        f"Спасибо! Ваш заказ оформлен.\n"
        f"Мы свяжемся с вами по адресу: {email}"
    )

    await state.set_state(BotStates.HANDLE_MENU)
