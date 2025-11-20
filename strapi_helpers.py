import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10


def get_products(strapi_url: str, strapi_token: str) -> Optional[dict]:
    headers = {"Authorization": f"Bearer {strapi_token}"}
    params = {"populate": "*"}

    try:
        response = requests.get(
            strapi_url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении продуктов: {e}")
        return None


def get_image_url(product: dict, strapi_base_url: str) -> Optional[str]:
    try:
        if 'image' not in product:
            return None

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
        logger.error(f"Ошибка при извлечении URL изображения: {e}")
        return None


def download_image(image_url: str) -> Optional[bytes]:
    try:
        response = requests.get(image_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при скачивании изображения: {e}")
        return None


def get_or_create_cart(
        strapi_base_url: str,
        strapi_token: str,
        telegram_id: int
) -> Optional[dict]:
    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json"
    }
    carts_url = f"{strapi_base_url}/api/carts"

    try:
        params = {
            "filters[telegram_id][$eq]": telegram_id,
            "filters[order_status][$eq]": "active",
            "populate": "*"
        }
        response = requests.get(
            carts_url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data.get('data'):
            return data['data'][0]

        cart_data = {
            "data": {
                "telegram_id": str(telegram_id),
                "order_status": "active"
            }
        }
        response = requests.post(
            carts_url,
            headers=headers,
            json=cart_data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()['data']

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при работе с корзиной: {e}")
        return None


def add_product_to_cart(
        strapi_base_url: str,
        strapi_token: str,
        cart_document_id: str,
        product_document_id: str,
        quantity: float = 1.0
) -> Optional[dict]:
    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json"
    }
    cart_items_url = f"{strapi_base_url}/api/cart-items"

    try:
        cart_item_data = {
            "data": {
                "quantity": quantity,
                "cart": cart_document_id,
                "product": product_document_id
            }
        }
        response = requests.post(
            cart_items_url,
            headers=headers,
            json=cart_item_data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()['data']

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {e}")
        return None


def get_cart_with_items(
        strapi_base_url: str,
        strapi_token: str,
        telegram_id: int
) -> Optional[dict]:
    headers = {"Authorization": f"Bearer {strapi_token}"}
    carts_url = f"{strapi_base_url}/api/carts"

    try:
        params = {
            "filters[telegram_id][$eq]": telegram_id,
            "filters[order_status][$eq]": "active",
            "populate[items][populate][0]": "product"
        }
        response = requests.get(
            carts_url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data.get('data'):
            return data['data'][0]

        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении корзины: {e}")
        return None


def remove_cart_item(
        strapi_base_url: str,
        strapi_token: str,
        cart_item_document_id: str
) -> bool:
    headers = {"Authorization": f"Bearer {strapi_token}"}
    cart_item_url = f"{strapi_base_url}/api/cart-items/{cart_item_document_id}"

    try:
        response = requests.delete(cart_item_url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при удалении товара из корзины: {e}")
        return False


def create_customer(
        strapi_base_url: str,
        strapi_token: str,
        telegram_id: int,
        email: str,
        username: Optional[str] = None
) -> Optional[dict]:
    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json"
    }
    customers_url = f"{strapi_base_url}/api/customers"

    try:
        customer_data = {
            "data": {
                "telegram_id": str(telegram_id),
                "email": email,
                "username": username
            }
        }
        response = requests.post(
            customers_url,
            headers=headers,
            json=customer_data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"Клиент создан для telegram_id: {telegram_id}")
        return response.json()['data']

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при создании клиента: {e}")
        return None


def get_customer(strapi_base_url: str, strapi_token: str, telegram_id: int) -> Optional[dict]:
    headers = {"Authorization": f"Bearer {strapi_token}"}
    customers_url = f"{strapi_base_url}/api/customers"

    try:
        params = {"filters[telegram_id][$eq]": telegram_id}
        response = requests.get(
            customers_url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data.get('data'):
            return data['data'][0]

        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении клиента: {e}")
        return None


def link_cart_to_customer_and_complete(
        strapi_base_url: str,
        strapi_token: str,
        cart_document_id: str,
        customer_document_id: str
) -> Optional[dict]:
    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json"
    }
    cart_url = f"{strapi_base_url}/api/carts/{cart_document_id}"

    try:
        cart_data = {
            "data": {
                "customer": customer_document_id,
                "order_status": "completed"
            }
        }
        response = requests.put(
            cart_url,
            headers=headers,
            json=cart_data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"Заказ оформлен для корзины {cart_document_id}")
        return response.json()['data']

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при обновлении корзины: {e}")
        return None
