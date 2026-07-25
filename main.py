import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TELEGRAM_BOT_TOKEN = "8884394536:AAEfDaTV8rA5lje87PlecAmT6CGE5zNuhGk"

SEENSMS_API_URL = "https://seensms.uz/api/v2"
SEENSMS_API_TOKEN = "JQVUUMxTraOhMFXbukUAtjCkNY9VUBhK"
SERVICE_ID = 452

router = Router()


class OrderState(StatesGroup):
  waiting_for_link = State()
  waiting_for_quantity = State()


@router.callback_query(F.data == "order_insta")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "Iltimos, Instagram profilingiz havolasini yuboring:"
  )
  await state.set_state(OrderState.waiting_for_link)
  await callback.answer()


@router.message(OrderState.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
  await state.update_data(link=message.text)
  await message.answer("Nechta obunachi kerak? Faqat raqam kiriting:")
  await state.set_state(OrderState.waiting_for_quantity)


@router.message(OrderState.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
  if not message.text.isdigit():
    await message.answer("Iltimos, faqat raqam kiriting!")
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
          await message.answer(
              f"✅ Buyurtma qabul qilindi!\n🆔 ID: {result['order']}"
          )
        else:
          await message.answer(
              f"❌ Xatolik: {result.get('error', 'Nomaal')}"
          )
    except Exception as e:
      await message.answer(f"❌ Xatolik: {e}")

  await state.clear()


async def main():
  logging.basicConfig(level=logging.INFO)
  bot = Bot(token=TELEGRAM_BOT_TOKEN)
  dp = Dispatcher()
  dp.include_router(router)
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
