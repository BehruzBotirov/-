
import sqlite3
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = "7606871879:AAFQ6ZNR2wj6MqOtfCtmziqpY3RwujErfSk"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

# Подключение к базе данных и создание таблицы пользователей
async def create_db():
    conn = sqlite3.connect('month5_sql/reg_users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        surname TEXT,
        phone TEXT,
        username TEXT,
        user_id INTEGER
    )
    ''')
    conn.commit()
    conn.close()

# Проверка, зарегистрирован ли пользователь
def check_user(user_id):
    conn = sqlite3.connect('month5_sql/reg_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Создание состояния для регистрации пользователя
class Register(StatesGroup):
    name = State()
    surname = State()
    phone = State()
    username = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def salom_ber(message: types.Message):
    if check_user(message.from_user.id):
        conn = sqlite3.connect('month5_sql/reg_users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, username FROM users WHERE user_id = ?", (message.from_user.id,))
        user_data = cursor.fetchone()
        conn.close()
        await message.answer(text=f"Assalomu aleykum, xush kelibsiz {user_data[0]} @{user_data[1]}")
    else:
        await message.answer(text="Assalomu aleykum, ro'yxatdan o'ting!\n\n/register")

# Обработчик команды /register
@dp.message_handler(commands=['register'])
async def royxatdan_otish(message: types.Message):
    if check_user(message.from_user.id):
        await message.answer(text="Siz ro'yxatdan o'tgansiz!")
    else:
        await message.answer(text="Ismingizni kiriting")
        await Register.name.set()

# Обработчик состояния для имени
@dp.message_handler(state=Register.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text="Familiyangizni kiriting")
    await Register.next()

# Обработчик состояния для фамилии
@dp.message_handler(state=Register.surname)
async def process_surname(message: types.Message, state: FSMContext):
    await state.update_data(surname=message.text)
    contact_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        types.KeyboardButton("Contact jo'natish", request_contact=True)
    )
    await message.answer(text="Telefon raqamingizni kiriting", reply_markup=contact_kb)
    await Register.next()

# Обработчик состояния для телефона
@dp.message_handler(content_types=types.ContentType.CONTACT, state=Register.phone)
async def process_phone(message: types.Message, state: FSMContext):
    contact = message.contact
    await state.update_data(phone=contact.phone_number)
    await message.answer(text="Telegram username kiriting (yoki boshqa narsani yozing):", reply_markup=types.ReplyKeyboardRemove())
    await Register.next()

# Обработчик состояния для username
@dp.message_handler(state=Register.username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.update_data(user_id=message.from_user.id)
    data = await state.get_data()

    conn = sqlite3.connect('month5_sql/reg_users.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO users (name, surname, phone, username, user_id) 
    VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], data['surname'], data['phone'], data['username'], data['user_id']))
    conn.commit()
    conn.close()

    await message.answer(text="Ro'yxatdan o'tdingiz!")
    await state.finish()

# Основная функция для запуска бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=create_db)
