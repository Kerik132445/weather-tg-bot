import os
import asyncio
import logging
import sys
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


class WeatherCallback(CallbackData, prefix='weather_click'):
    action: str
    city: str


class Form(StatesGroup):
    waiting_for_city = State()


user_kb = [
    [types.KeyboardButton(text='⭐️ Избранное')],
    [types.KeyboardButton(text='📊 Погода')]
]
user_keyboard = types.ReplyKeyboardMarkup(
    keyboard=user_kb,
    resize_keyboard=True
)


@dp.callback_query(WeatherCallback.filter())
async def hendle_weather_clicks(callback: CallbackQuery, callback_data: WeatherCallback):

    action = callback_data.action
    city = callback_data.city

    if action == "favorite":

        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://127.0.0.1:8000/favorites?city={city}")

        if response.status_code in [200, 201]:
            await callback.answer(text=f"Город {city} добавлен в избранное!")

        else:
            await callback.answer(text="Что-то пошло не так...")

    if action == "delete":
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"http://127.0.0.1:8000/favorites?city={city}")

            if response.status_code == 200:
                await callback.answer(text=f"🗑 Город {city} был успешно удален!")
                await callback.message.delete()
            else:
                await callback.answer(text="❌ Упс.. Что-то пошло не так")


@dp.message(Command("start"))
async def start_message(message: Message):
    # ловит /start, выдает кнопки и скидывает текст приветствия
    await message.answer('Йо! Я ну типо погоду могу показывать. Тыкай на кнопки и дальше уже разберешься!', reply_markup=user_keyboard)


@dp.message(Command("add"))
async def add_favorites_city(message: Message, command: CommandObject):
    # ловит команду / add на добавления города, отправляет post запрос в бэкенд
    city_args = command.args
    if not city_args:
        await message.answer("❌ Ты забыл указать город! Напиши, например: /add Москва")
        return

    async with httpx.AsyncClient() as client:
        response = await client.post(f"http://127.0.0.1:8000/favorites?city={city_args}")

        if response.status_code == 200 or response.status_code == 201:
            await message.answer(f"⭐️ Город {city_args} успешно добавлен!")

        else:
            await message.answer(f"❌ Упс.. Что-то пошло не так")


@dp.message(Command("delete"))
async def delete_cities(message: Message, command: CommandObject):
    # ловит команду /delete на удаление города из избранного.отправляет delete запрос в бэкенд
    city_args = command.args
    if not city_args:
        await message.answer("❌ Ты забыл указать город! Напиши, например: /delete Москва")
        return

    async with httpx.AsyncClient() as client:
        response = await client.delete(f"http://127.0.0.1:8000/favorites?city={city_args}")

        if response.status_code == 200:
            await message.answer(f"🗑 Город {city_args} был успешно удален!")

        else:
            await message.answer(f"❌  Упс.. Что-то пошло не так")


@dp.message(F.text == "📊 Погода")
async def user_need_weather(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_for_city)
    await message.answer("Напиши название города для которого хочешь узнать погоду:")


@dp.message(or_f(Command("favorites"), F.text == "⭐️ Избранное"))
async def show_favorites_cities(message: Message):

    # ловит кнопку или команду /favorites. Стучит /get в бэкенд, получакет список городов с погодой, собирает их через цикл и выводит одним большим текстом

    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8000/favorites")
        data = response.json()
        city_list = data["favorites_cities"]

        if not city_list:
            await message.answer("⭐️ Твой список избранного пока пуст!")
            return

        for item in city_list:
            city_info = f"📍Погода в г. *{item['city'].title()}*: \nТемпература: {item['temp']} \nСостояние: {item['condition']}"

            delete_button = InlineKeyboardButton(
                text="🗑 Удалить из избранного", callback_data=WeatherCallback(action='delete', city=item['city']).pack())
            fav_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[delete_button]])

            await message.answer(text=city_info, reply_markup=fav_keyboard, parse_mode="Markdown")


@dp.message(Form.waiting_for_city)
async def get_any_city_weather(message: Message, state: FSMContext):
    # ловит команду /weather. стучит в get /weather на бэкенде, забирает темп и описание и выовдит погоду
    city_args = message.text

    await state.clear()

    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://127.0.0.1:8000/weather?city={city_args}")

        if response.status_code == 200:
            data = response.json()

            temp = data["temperature"]
            text = data["condition"]

            add_favorite_button = InlineKeyboardButton(
                text="⭐️ Добавить в избранное", callback_data=WeatherCallback(action='favorite', city=city_args).pack())

            delete_favorite_button = InlineKeyboardButton(
                text="🗑 Удалить из избранного", callback_data=WeatherCallback(action='delete', city=city_args).pack())

            get_weather_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[add_favorite_button, delete_favorite_button]])

            await message.answer(f"📍Погода в г. *{city_args.title()}*:\nТемпература: {temp}°C\nСостояние: {text}", reply_markup=get_weather_keyboard, parse_mode="Markdown")

        elif response.status_code == 404:
            await message.answer(f"❌ Город {city_args} не найден. Проверь, есть ли такой город")

        else:
            await message.answer(f"❌ Упс.. Что-то пошло не так")


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
