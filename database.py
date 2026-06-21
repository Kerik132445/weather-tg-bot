import aiosqlite

DB_NAME = "weather.db"

# Автоматический запуск при старте сервера.
# Создает таблицу favorite_cities, если её ещё нет в файле weather.db.
# UNIQUE NOT NULL гарантирует, что один и тот же город
# не запишется дважды.


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS favorite_cities (cities_id INTEGER PRIMARY KEY, city_name TEXT UNIQUE NOT NULL)""")

        await db.commit()


async def add_favorite_cities(city_name: str):

    # Принимает название города от FastAPI и записывает его в базу.
    # Знак '?' защищает от SQL-инъекций (чтобы хакеры не сломали базу).

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""INSERT INTO favorite_cities (city_name) VALUES (?)""", (city_name,))

        await db.commit()


async def get_favorite_cities():

    # Вытаскивает из базы ВСЕ сохраненные города.
    # Возвращает список кортежей, например: [('Москва',), ('Ковров',)]

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""SELECT city_name FROM favorite_cities""")
        rows = await cursor.fetchall()

        return rows


async def delete_favorite_cities(city_name: str):

    # Ищет город в базе по названию и полностью удаляет его из таблицы.

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""DELETE FROM favorite_cities WHERE city_name = ? """, (city_name,))

        await db.commit()
