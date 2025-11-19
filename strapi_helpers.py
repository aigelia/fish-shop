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