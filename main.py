import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "8884394536:AAEfDaTV8rA5lje87PlecAmT6CGE5zNuhGk"

bot = Bot("8884394536:AAEfDaTV8rA5lje87PlecAmT6CGE5zNuhGk")
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, ?)', (user_id, 10))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_coins(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💰 Balans"), 
            KeyboardButton(text="➕ Tanga ishlash")
        ],
        [
            KeyboardButton(text="🚀 Buyurtma berish")
        ]
    ],
    resize_keyboard=True
)
)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        "Xush kelibsiz! Botimizga 10 coin bonus berildi.",
        reply_markup=main_menu
    )

@dp.message(F.text == "💰 Balans")
async def balance_cmd(message: types.Message):
    coins = get_balance(message.from_user.id)
    await message.answer(f"Sizning balansingiz: **{coins} coin**", parse_mode="Markdown")

@dp.message(F.text == "➕ Tanga ishlash")
async def earn_cmd(message: types.Message):
    task_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Kanalga o'tish", url="https://t.me/telegram")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ]
    )
    await message.answer("Kanalga obuna bo'ling va 2 coin oling:", reply_markup=task_kb)

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    add_coins(call.from_user.id, 2)
    await call.answer("Topshiriq bajarildi! +2 coin qo'shildi.", show_alert=True)
    
@dp.message(F.text == "🚀 Buyurtma berish")
async def order_cmd(message: types.Message):
    coins = get_balance(message.from_user.id)
    if coins < 10:
        await message.answer(f"Sizda coin yetarli emas. Balans: {coins} coin\nMinimum 10 coin kerak!")
    else:
        await message.answer("Buyurtma berish uchun kanalingiz havolasini yuboring (masalan: @kanal_nomi):")

async def main():
    init_db()
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
