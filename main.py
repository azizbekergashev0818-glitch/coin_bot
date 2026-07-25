import asyncio
import sqlite3
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = "8884394536:AAEfDaTV8ra5Ije87PIecA"
ADMIN_ID = 6913959674

SMM_API_KEY = "ad085aabb8ca0d38c4d908dd8e0b7ced"
SMM_SERVICE_ID = 71
SMM_API_URL = "https://smmmain.com/api/v2"

bot = Bot("8884394536:AAEfDaTV8rA5lje87PlecAmT6CGE5zNuhGk")
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_link = State()

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id INTEGER,
            task_id TEXT,
            PRIMARY KEY (user_id, task_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, 10)', (user_id,))
    conn.commit()
    conn.close()

def get_balance(user_id):
    if user_id == ADMIN_ID:
        return 9999999
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_coins(user_id, amount):
    if user_id == ADMIN_ID:
        return
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def is_task_completed(user_id, task_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?', (user_id, task_id))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def mark_task_completed(user_id, task_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO completed_tasks (user_id, task_id) VALUES (?, ?)', (user_id, task_id))
    conn.commit()
    conn.close()

async def send_smm_order(link: str, quantity: int):
    payload = {
        'key': SMM_API_KEY,
        'action': 'add',
        'service': SMM_SERVICE_ID,
        'link': link,
        'quantity': quantity
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(SMM_API_URL, data=payload) as response:
            return await response.json()

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

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    add_user(message.from_user.id)
    await message.answer("Xush kelibsiz! Botimizga 10 coin bonus berildi.", reply_markup=main_menu)

@dp.message(F.text == "💰 Balans")
async def balance_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("Siz Adminsiz! Sizning balansingiz: ♾️ Cheksiz coin")
    else:
        coins = get_balance(user_id)
        await message.answer(f"Sizning balansingiz: {coins} coin")

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
    task_id = "channel_1"
    
    if is_task_completed(call.from_user.id, task_id):
        await call.answer("Siz bu topshiriq uchun allaqachon coin olgansiz!", show_alert=True)
        return

    add_coins(call.from_user.id, 2)
    mark_task_completed(call.from_user.id, task_id)
    await call.answer("Topshiriq bajarildi! +2 coin berildi 🎉", show_alert=True)

@dp.message(F.text == "🚀 Buyurtma berish")
async def order_cmd(message: types.Message):
    order_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 10 ta obunachi (10 coin)", callback_data="pack_10_10")],
            [InlineKeyboardButton(text="👤 25 ta obunachi (20 coin)", callback_data="pack_25_20")],
            [InlineKeyboardButton(text="👤 70 ta obunachi (50 coin)", callback_data="pack_70_50")]
        ]
    )
    await message.answer("Nechta obunachi buyurtma qilmoqchisiz? Tarifni tanlang:", reply_markup=order_kb)

@dp.callback_query(F.data.startswith("pack_"))
async def select_pack(call: types.CallbackQuery, state: FSMContext):
    _, count, price = call.data.split("_")
    count, price = int(count), int(price)
    
    user_coins = get_balance(call.from_user.id)
    if user_coins < price:
        await call.answer(f"Sizda yetarli coin yo'q! Kerak: {price} coin, sizda: {user_coins} coin.", show_alert=True)
        return

    await state.update_data(sub_count=count, coin_price=price)
    await state.set_state(OrderState.waiting_for_link)
    await call.message.answer(f"Siz {count} ta obunachi paketini tanladingiz ({price} coin).\n\nEndi Telegram kanalingiz havolasini yuboring:")
    await call.answer()

@dp.message(OrderState.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    count = data.get("sub_count")
    price = data.get("coin_price")
    
    user_id = message.from_user.id
    target_link = message.text
    
    add_coins(user_id, -price)
    
    try:
        res = await send_smm_order(target_link, count)
        order_id = res.get("order", "Noma'lum")
        
        await message.answer(f"🚀 Buyurtmangiz qabul qilindi!\n\nManzil: {target_link}\nObunachilar: {count} ta\nBuyurtma ID: #{order_id}")
        
        await bot.send_message(
            ADMIN_ID, 
            f"📥 Yangi Avto-Buyurtma!\n\nFoydalanuvchi: @{message.from_user.username} (ID: {user_id})\nManzil: {target_link}\nSoni: {count} ta\nSMM Order ID: #{order_id}"
        )
    except Exception:
        await message.answer(f"🚀 Buyurtmangiz qabul qilindi!\n\nManzil: {target_link}\nObunachilar: {count} ta.")
        await bot.send_message(
            ADMIN_ID, 
            f"⚠️ Buyurtma tushdi:\nFoydalanuvchi: ID {user_id}\nManzil: {target_link}\nSoni: {count} ta"
        )
        
    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
