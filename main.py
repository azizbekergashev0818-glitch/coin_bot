import aiohttp
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

SEENSMS_API_URL = "https://seensms.uz/api/v2"
SEENSMS_API_TOKEN = "JQVUUMxTraOhMFXbukUAtjCkNY9VUBhK"
SERVICE_ID = 452


class OrderState(StatesGroup):
  waiting_for_link = State()
  waiting_for_quantity = State()


@router.callback_query(F.data == "order_insta")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "Iltimos, Instagram profilingiz havolasini (linkini) yuboring:"
  )
  await state.set_state(OrderState.waiting_for_link)
  await callback.answer()


@router.message(OrderState.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
  await state.update_data(link=message.text)
  await message.answer(
      "Nechta obunachi kerak? (Min: 100, Max: 5000000):\n"
      "Faqat raqam yozib yuboring (masalan: 500)"
  )
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
          order_id = result["order"]
          await message.answer(
              f"✅ **Buyurtma muvaffaqiyatli qabul qilindi!**\n\n"
              f"🆔 Buyurtma raqami: {order_id}\n"
              f"🔗 Havola: {link}\n"
              f"👥 Soni: {quantity} ta"
          )
        else:
          error_msg = result.get("error", "Noma'lum xatolik")
          await message.answer(f"❌ Xatolik yuz berdi: {error_msg}")
    except Exception as e:
      await message.answer(f"❌ Server bilan bog'lanishda xatolik: {e}")

  await state.clear()
