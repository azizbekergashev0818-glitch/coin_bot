import asyncio
import sqlite3
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = "8884394536:AAEfDaTV8rA5lje87PlecAmT6CGE5zNuhGk"  
ADMIN_ID = 6913959674

SEENSMS_API_URL = "https://seensms.uz/api/v2"
SEENSMS_API_TOKEN = "JQVUUMxTraOhMFXbukUAtjCkNY9VUBhK"
SERVICE_ID = 452

REQUIRED_CHANNEL = "@telegram"  # Majburiy obuna kanali (o'zingizning kanal username yozing)

bot = Bot(token=API_TOKEN)
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
        return 999999999  
    
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
    await message.answer(
        "Xush kelibsiz! Botimizga xush kelibsiz.",
        reply_markup=main_menu
    )

@dp.message(F.text == "💰 Balans")
async def balance_cmd(message: types.Message):
    coins = get_balance(message.from_user.id)
    if message.from_user.id == ADMIN_ID:
        await message.answer("Sizning balansingiz: ♾️ Cheksiz coin")
    else:
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

# "🚀 Buyurtma berish" tugmasi bosilganda avval obunani tekshiramiz
@dp.message(F.text == "🚀 Buyurtma berish")
async def order_cmd(message: types.Message):
    user_id = message.from_user.id
    
    # Admin uchun obuna tekshirilmaydi
    if user_id != ADMIN_ID:
        try:
            member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            if member.status in ["left", "kicked"]:
                sub_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")]
                    ]
                )
                await message.answer(f"❌ Botdan foydalanish uchun avval quyidagi kanalga obuna bo'ling:", reply_markup=sub_kb)
                return
        except Exception as e:
            print(f"Obunani tekshirishda xato (bot kanalda admin bo'lishi kerak): {e}")

    coins = get_balance(user_id)
    if coins < 10:
        await message.answer(f"Sizda coin yetarli emas. Balans: {coins} coin\nMinimum 10 coin kerak!")
    else:
        await message.answer("Buyurtma berish uchun kanal yoki instagram manzilingizni yozing (masalan: @kanal_nomi yoki link):")

@dp.message(F.text.startswith("@") | F.text.startswith("http"))
async def process_order(message: types.Message):
    user_id = message.from_user.id
    coins = get_balance(user_id)
    
    if coins >= 10:
        target_link = message.text
        
        payload = {
            "key": SEENSMS_API_TOKEN,
            "action": "add",
            "service": SERVICE_ID,
            "link": target_link,
            "quantity": 100
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(SEENSMS_API_URL, data=payload) as response:
                    result = await response.json()
                    if "order" in result:
                        add_coins(user_id, -10)  
                        await message.answer(f"🚀 Buyurtma qabul qilindi!\n🆔 ID: {result['order']}")
                    else:
                        await message.answer(f"❌ Xato: {result.get('error', 'Nomaʼlum')}")
            except Exception as e:
                await message.answer(f"❌ Server xatosi: {e}")
        
        try:
            await bot.send_message(
                ADMIN_ID, 
                f"📥 **Yangi buyurtma!**\n\nFoydalanuvchi: @{message.from_user.username} (ID: {user_id})\nManzil: {target_link}"
            )
        except Exception as e:
            print(f"Adminga xabar yuborishda xato: {e}")

async def handle(request):
    return web.Response(text="OK")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    init_db()
    asyncio.create_task(web_server())
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
