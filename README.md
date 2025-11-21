# Telegram-бот для интернет-магазина на базе Strapi CMS

Telegram-бот для продажи рыбы, который работает с CMS Strapi v5 в качестве бэкенда. Бот позволяет пользователям просматривать каталог товаров, добавлять их в корзину и оформлять заказы.

## Функционал

* Просмотр каталога товаров с изображениями и описаниями
* Добавление товаров в корзину
* Управление корзиной (просмотр, удаление товаров)
* Оформление заказа с указанием email
* Автоматическое создание новой корзины для следующего заказа после ввода email

## Установка

Клонируйте репозиторий и создайте виртуальное окружение с Python 3.12+. Проект использует UV в качестве пакетного менеджера, так что устанавливайте зависимости через него:

```bash
pip install uv
uv sync
```

Создайте файл `.env` и добавьте в него переменные окружения:

* `TG_TOKEN` - токен Telegram-бота
* `DATABASE_HOST` - хост базы данных Redis (по умолчанию `localhost`)
* `DATABASE_PORT` - порт базы данных Redis (по умолчанию `6379`)
* `DATABASE_PASSWORD` - пароль для базы данных Redis
* `STRAPI_URL` - URL для получения продуктов (например, `http://localhost:1337/api/products`)
* `STRAPI_TOKEN` - токен доступа к Strapi API
* `STRAPI_BASE_URL` - базовый URL Strapi (например, `http://localhost:1337`)

## Настройка Strapi

Для установки и настройки Strapi CMS воспользуйтесь [руководством на официальном сайте](https://docs.strapi.io/cms/intro). Когда всё будет настроено, в Strapi необходимо создать следующие модели и их поля:

### Product
* `title` - Text
* `description` - Text
* `price` - Number
* `image` - Media (single)

### Cart
* `telegram_id` - Text
* `order_status` - Enumeration (`active`, `completed`), default: `active`
* `items` - Relation: has many CartItem
* `customer` - Relation: belongs to one Customer

### CartItem
* `quantity` - Decimal
* `product` - Relation: many-to-one с Product
* `cart` - Relation: many-to-one с Cart

### Customer
* `telegram_id` - Text
* `email` - Email
* `username` - Text
* `carts` - Relation: has many Cart

## Запуск

Запустите бота:

```bash
python bot.py
```

## Цели проекта

Код написан в учебных целях — для курса по Python и веб-разработке на сайте [Devman](https://dvmn.org).