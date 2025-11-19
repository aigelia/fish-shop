import asyncio
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from environs import Env
from redis.asyncio import Redis


async def start(message: Message, state_data: dict):
    await message.answer(text='Привет!')
    return "ECHO"


async def echo(message: Message, state_data: dict):
    users_reply = message.text
    await message.answer(users_reply)
    return "ECHO"


async def handle_users_reply(message: Message, redis_conn: Redis):
    chat_id = message.chat.id
    user_reply = message.text

    if user_reply == '/start':
        user_state = 'START'
    else:
        stored_state = await redis_conn.get(str(chat_id))
        user_state = stored_state.decode("utf-8") if stored_state else 'START'

    states_functions = {
        'START': start,
        'ECHO': echo
    }

    state_handler = states_functions[user_state]

    try:
        next_state = await state_handler(message, {})
        await redis_conn.set(str(chat_id), next_state)
    except Exception as err:
        print(f"Error: {err}")


async def main():
    env = Env()
    env.read_env()

    tg_token = env.str("TG_TOKEN")
    redis_host = env.str("DATABASE_HOST", "localhost")
    redis_port = env.int("DATABASE_PORT", 6379)
    redis_password = env.str("DATABASE_PASSWORD", None)

    redis_conn = Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=False
    )

    bot = Bot(token=tg_token)
    storage = RedisStorage(redis=redis_conn)
    dp = Dispatcher(storage=storage)

    dp.message.register(partial(handle_users_reply, redis_conn=redis_conn))

    try:
        await dp.start_polling(bot)
    finally:
        await redis_conn.close()


if __name__ == '__main__':
    asyncio.run(main())