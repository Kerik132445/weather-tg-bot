"""uvicorn main:app --reload"""

from fastapi import FastAPI, HTTPException, Depends
import httpx
from contextlib import asynccontextmanager
# импорт всех функций из бд
from database import init_db, add_favorite_cities, get_favorite_cities, delete_favorite_cities


@asynccontextmanager
async def lifespan(app: FastAPI):

    # хз для чего он, вроде нужен чтобы создать бд
    await init_db()

    yield

app = FastAPI(lifespan=lifespan)


def get_condition_emji(condition_text):
    # принимает текст погоды, и по клбчевому слову возвращает эмоджи
    text_lower = condition_text.lower()
    if 'ясно' in text_lower or 'солнечно' in text_lower:
        return ('☀️')
    elif 'облач' in text_lower or 'пасмур' in text_lower:
        return ('☁️')
    elif 'туман' in text_lower or 'дымка' in text_lower:
        return ('🌫')
    elif 'дождь' in text_lower or 'лив' in text_lower or 'морос' in text_lower:
        return ('🌧')
    elif 'снег' in text_lower or 'метел' in text_lower or 'град' in text_lower or 'крупа' in text_lower:
        return ('🌨')
    elif 'гроз' in text_lower:
        return ('⚡️')

    return ('✨')


def get_temp_emoji(temp_text):
    # все тоже самое что и с прошлой функцией, но ток тут градусы
    if temp_text <= -10:
        return ('❄️')
    elif temp_text > -10 and temp_text <= 10:
        return ('💨')
    elif temp_text > 10 and temp_text <= 20:
        return ('🍃')
    elif temp_text > 20 and temp_text <= 28:
        return ('☀️')
    elif temp_text > 28:
        return ('🔥')


@app.get("/weather")
# самый сок. бот сюда стучит, а он делает запрос в Weather api, забирает данные, упаковывает в json и отдает боту
async def get_city(city: str):
    API_KEY = "fd5562ea66f04ba1b82114340261406"

    url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&lang=ru"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        if response.status_code != 200:
            raise HTTPException(
                status_code=404, detail="Такой город не найден")

        data = response.json()
        temp = data["current"]["temp_c"]
        text = data["current"]["condition"]["text"]

        emoji_condition = get_condition_emji(text)
        emoji_temp = get_temp_emoji(temp)

        return {"temperature": f"{emoji_temp} {temp}", "condition": f"{emoji_condition} {text}"}


@app.post("/favorites")
async def adding_fav_cities(city: str):

    # эндпоинт для добавления города в избранное.
    # проверяет есть ли такой город, и если все норм, то то записывает в бд
    await get_city(city=city)

    await add_favorite_cities(city_name=city)

    return {"status": "success", "message": f"Город {city} сохранен!"}


@app.get("/favorites")
async def getting_fav_cities():
    raw_cities = await get_favorite_cities()
    clean_raw = [item[0] for item in raw_cities]
    weather_data = []

    for city in clean_raw:

        city_weather = await get_city(city=city)
        weather_data.append({
            "city": city,
            "temp": city_weather["temperature"],
            "condition": city_weather["condition"]
        })

    return {"favorites_cities": weather_data}


@app.delete("/favorites")
async def deliting_fav_cities(city: str):

    # эндпоинт для удаления города из избранного
    # просто удаляет городчерез бд и возвращает новый список оставшихся городов

    await delete_favorite_cities(city_name=city)
    raw_cities = await get_favorite_cities()

    clean_raw = [item[0] for item in raw_cities]

    return {"status": "success", "message": f"Город {city} удален!", "favorites_cities": clean_raw}
