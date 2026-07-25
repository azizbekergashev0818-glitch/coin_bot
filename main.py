import asyncio
import logging
from aiohttp import web
import aiohttp
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart

TELEGRAM_BOT_TOKEN = "8884394536:AAEfDaTV8rA5lje87PlecAmT6CGE5zNuhGk"

SEENSMS_API_URL = "https://seensms.uz/api/v2"
SEENSMS_API_TOKEN = "JQVUUMxTraOhMFXbukUAtjCkNY9VUBhK"
SERVICE_ID = 452

router = Router()


class OrderState(StatesGroup):
  waiting_for_link = State()
  waiting_for_quantity = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "Salom! Bot ishga tushdi.\nBuyurtma berish uchun quyidagi tugmani bosing:",
      reply_markup=types.ReplyKeyboardMarkup(
          keyboard=[[types.KeyboardButton(text="🚀 Buyurtma berish")]],
          resize_keyboard=True,
      ),
  )


@router.message(F.text == "🚀 Buyurtma berish")
async def start_order_btn(message: types.Message, state: FSMContext):
  await message.answer("Link yuboring:")
  await state.set_state(OrderState.waiting_for_link)


@router.message(OrderState.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
  await state.update_data(link=message.text)
  await message.answer("Soni (faqat raqam):")
  await state.set_state(OrderState.waiting_for_quantity)


@router.message(OrderState.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
  if not message.text.isdigit():
    await message.answer("Faqat raqam kiriting!")
    return

  quantity = int(message.text)
  data = await state.get_data()
  link = data.get("link")

  payload = {
      "key": SEENSMS_API_TOKEN,
      "action": "add",
      "service": SERVICE_ID,
      "link": link,
      "quantity": quantity,
  }

  async with aiohttp.ClientSession() as session:
    try:
      async with session.post(SEENSMS_API_URL, data=payload) as response:
        result = await response.json()
        if "order" in result:
          await message.answer(f"✅ ID: {result['order']}")
        else:
          await message.answer(f"❌ Xato: {result.get('error', 'Nomaʼlum')}")
    except Exception as e:
      await message.answer(f"❌ Xato: {e}")

  await state.clear()


@router.message(F.text)
async def catch_all_other_messages(message: types.Message):
  pass


@router.callback_query(F.data)
async def catch_all_other_callbacks(callback: types.CallbackQuery):
  await callback.answer()


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
  logging.basicConfig(level=logging.INFO)
  bot = Bot(token=TELEGRAM_BOT_TOKEN)
  dp = Dispatcher()
  dp.include_router(router)
  asyncio.create_task(web_server())
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
