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


def download_image(image_url: str) -> bytes:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании изображения: {e}")
        return None
