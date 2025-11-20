import requests


def get_products(strapi_url: str, strapi_token: str):
    headers = {
        "Authorization": f"Bearer {strapi_token}"
    }
    params = {
        "populate": "*"
    }
    try:
        response = requests.get(strapi_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении продуктов: {e}")
        return None


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


def download_image(image_url: str) -> bytes:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании изображения: {e}")
        return None


def get_or_create_cart(strapi_base_url: str, strapi_token: str, telegram_id: int):
    headers = {
        "Authorization": f"Bearer {strapi_token}",
        "Content-Type": "application/json"
    }

    carts_url = f"{strapi_base_url}/api/carts"

    try:
        params = {
            "filters[telegram_id][$eq]": telegram_id,
            "populate": "*"
        }
        response = requests.get(carts_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('data') and len(data['data']) > 0:
            return data['data'][0]

        cart_data = {
            "data": {
                "telegram_id": str(telegram_id)
            }
        }
        response = requests.post(carts_url, headers=headers, json=cart_data, timeout=10)
        response.raise_for_status()
        return response.json()['data']

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при работе с корзиной: {e}")
        return None


def add_product_to_cart(strapi_base_url: str, strapi_token: str, cart_document_id: str, product_document_id: str,
                        quantity: float = 1.0):
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

        print(f"Отправка данных: {cart_item_data}")
        response = requests.post(cart_items_url, headers=headers, json=cart_item_data, timeout=10)
        print(f"Статус ответа: {response.status_code}")
        print(f"Ответ: {response.text}")
        response.raise_for_status()
        return response.json()['data']

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при добавлении товара в корзину: {e}")
        return None


def get_cart_with_items(strapi_base_url: str, strapi_token: str, telegram_id: int):
    headers = {
        "Authorization": f"Bearer {strapi_token}"
    }

    carts_url = f"{strapi_base_url}/api/carts"

    try:
        params = {
            "filters[telegram_id][$eq]": telegram_id,
            "populate[items][populate][0]": "product"
        }
        response = requests.get(carts_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('data') and len(data['data']) > 0:
            return data['data'][0]

        return None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении корзины: {e}")
        return None


def remove_cart_item(strapi_base_url: str, strapi_token: str, cart_item_document_id: str):
    headers = {
        "Authorization": f"Bearer {strapi_token}"
    }

    cart_item_url = f"{strapi_base_url}/api/cart-items/{cart_item_document_id}"

    try:
        response = requests.delete(cart_item_url, headers=headers, timeout=10)
        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при удалении товара из корзины: {e}")
        return False
