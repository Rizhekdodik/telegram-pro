import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8898263139:AAFBY3MoW4NKvOGBJgtWKBus1e8aKuFvyu4"   # Твой токен
ADMIN_ID = 123456789                    # ⚠️ СВОЙ TELEGRAM ID (число)
TRC20_WALLET = "TXxxxxxxxxxxxxxxx"      # ⚠️ СВОЙ TRC20 КОШЕЛЕК

# Прайс-лист (название: цена в $)
PRODUCTS = {
    "Сносер TG/INST": 30,
    "DDOS СОФТ": 40,
    "Строки MM (10шт)": 70,
    "MAX (с панели)": 4,
    "MAX (Взросляк 18+)": 6,
    "Подпись ГК (Билайн,Т2)": 4,
    "Панель MAX под ключ": 90,
    "Мануал вбив банки/МФО с наставником": 200,
    "СС FULL GEO": 14,
    "Cпамер MAX": 20,
    "Брутер Тинь/Сбер/ВТБ": 150
}

# Твои услуги
SERVICE_TEXT = {
    "Сносер TG/INST": "✅ Ваш доступ: логин: user123, пароль: pass456\nСайт: https://example.com",
    "DDOS СОФТ": "✅ Ссылка на софт: https://disk.yandex.ru/...",
    "Строки MM (10шт)": "✅ Ваши строки:\n1. ...\n2. ...",
    "MAX (с панели)": "✅ Доступ к панели: ip:8080, логин: admin, пароль: qwerty",
    "MAX (Взросляк 18+)": "✅ Ссылка на приват канал: https://t.me/+...",
    "Подпись ГК (Билайн,Т2)": "✅ Инструкция и файл подписи: ...",
    "Панель MAX под ключ": "✅ Готовая панель: доступ по ssh root@...",
    "Мануал вбив банки/МФО с наставником": "✅ Мануал (PDF) и контакт наставника: @mentor",
    "СС FULL GEO": "✅ СС список: приложен файлом.",
    "Cпамер MAX": "✅ Софт спамер + инструкция.",
    "Брутер Тинь/Сбер/ВТБ": "✅ Брутер + базы в комплекте."
}

orders = {}
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ========== FSM ==========
class OrderState(StatesGroup):
    waiting_for_receipt = State()

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for name in PRODUCTS.keys():
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"{name} - ${PRODUCTS[name]}", callback_data=f"buy_{name}")])
    return keyboard

def payment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard

# ========== ХЕНДЛЕРЫ ==========
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("🛍 Добро пожаловать в магазин!\nВыберите товар из списка:", reply_markup=main_menu())

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    product_name = callback.data[4:]
    price = PRODUCTS[product_name]
    user_id = callback.from_user.id

    orders[user_id] = {
        'product': product_name,
        'price': price,
        'status': 'waiting_payment'
    }

    text = f"""💎 Товар: {product_name}
💰 Сумма: ${price} (TRC20)

📤 Переведите ровно {price} USDT (TRC20) на адрес:
`{TRC20_WALLET}`

❗️ После оплаты нажмите кнопку «✅ Я оплатил» и отправьте чек (скриншот перевода).
"""
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=payment_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "paid")
async def paid_click(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in orders or orders[user_id]['status'] != 'waiting_payment':
        await callback.message.answer("❌ У вас нет активного заказа или вы уже отправили чек.")
        await callback.answer()
        return

    await callback.message.answer("📎 Пожалуйста, отправьте скриншот/фото чека об оплате.")
    await state.set_state(OrderState.waiting_for_receipt)
    await callback.answer()

@dp.message(OrderState.waiting_for_receipt, F.photo)
async def handle_receipt_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in orders:
        await message.answer("❌ Заказ не найден. Начните заново /start")
        await state.clear()
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    product = orders[user_id]['product']
    price = orders[user_id]['price']

    admin_text = f"📩 **Новый чек на проверку**\n👤 Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n🆔 ID: {user_id}\n💎 Товар: {product}\n💰 Сумма: ${price}\n\n✅ Подтвердить / ❌ Отклонить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_{user_id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")]
    ])
    await bot.send_photo(ADMIN_ID, photo, caption=admin_text, parse_mode="Markdown", reply_markup=keyboard)

    await message.answer("✅ Чек отправлен администратору. Ожидайте подтверждения (обычно 1-5 минут).")
    await state.clear()

@dp.message(OrderState.waiting_for_receipt)
async def wrong_receipt(message: types.Message):
    await message.answer("❌ Пожалуйста, отправьте **фото или скриншот** чека об оплате.")

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    if user_id not in orders:
        await callback.message.answer("⚠️ Заказ уже неактивен.")
        await callback.answer()
        return

    product = orders[user_id]['product']
    service_info = SERVICE_TEXT.get(product, "✅ Услуга активирована. Спасибо за покупку!")

    await bot.send_message(user_id, f"✅ **Ваш платеж подтвержден!**\n\n{service_info}")

    await callback.message.edit_caption(caption=f"✅ Платеж ПОДТВЕРЖДЕН. Пользователю {user_id} выдано.\n{callback.message.caption}")
    del orders[user_id]
    await callback.answer("Подтверждено, услуга отправлена.")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    if user_id in orders:
        await bot.send_message(user_id, "❌ Ваш чек **отклонен** администратором. Возможно, неверная сумма, скриншот или адрес.\nПовторите оплату через /start")
        del orders[user_id]

    await callback.message.edit_caption(caption=f"❌ Платеж ОТКЛОНЕН.\n{callback.message.caption}")
    await callback.answer("Отклонено, пользователь уведомлен.")

@dp.callback_query(F.data == "cancel")
async def cancel_order(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in orders:
        del orders[user_id]
    await callback.message.answer("❌ Заказ отменен. Возврат в меню.", reply_markup=main_menu())
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())