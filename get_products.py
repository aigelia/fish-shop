from pprint import pprint

from environs import Env
import requests


def get_products(token, url):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    if response.status_code == 200:
        return response.json()
    else:
        return f'Ошибка: {response.status_code}, {response.text}'


def main():
    env = Env()
    env.read_env()
    strapi_token = env.str('STRAPI_TOKEN')
    strapi_url = env.str('STRAPI_URL')
    pprint(get_products(strapi_token, strapi_url))


if __name__ == '__main__':
    main()

