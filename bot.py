import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8898263139:AAFBY3MoW4NKvOGBJgtWKBus1e8aKuFvyu4"
ADMIN_ID = 7738397444
TRC20_WALLET = "TSZ35HrnGnX631MPwiScxmPzvWb5QpAJUb"

PRODUCTS = {
    "snos": {"name": "Сносер TG/INST", "price": 30},
    "ddos": {"name": "DDOS СОФТ", "price": 40},
    "stroki": {"name": "Строки MM (10шт)", "price": 70},
    "max1": {"name": "MAX (с панели)", "price": 4},
    "max2": {"name": "MAX (Взросляк 18+)", "price": 6},
    "podpis": {"name": "Подпись ГК (Билайн,Т2)", "price": 4},
    "panel": {"name": "Панель MAX под ключ", "price": 90},
    "manual": {"name": "Мануал вбив банки/МФО с наставником", "price": 200},
    "cc": {"name": "СС FULL GEO", "price": 14},
    "spamer": {"name": "Cпамер MAX", "price": 20},
    "bruter": {"name": "Брутер Тинь/Сбер/ВТБ", "price": 150}
}

SERVICE_TEXT = {
    "snos": "✅ Сносер TG/INST активирован!\nЛогин: your_login\nПароль: your_password",
    "ddos": "✅ DDOS СОФТ:\nСсылка: https://ссылка_на_софт",
    "stroki": "✅ Строки MM:\nВаши строки здесь",
    "max1": "✅ MAX (с панели):\nДоступ выдан",
    "max2": "✅ MAX 18+:\nДоступ выдан",
    "podpis": "✅ Подпись ГК:\nФайл готов",
    "panel": "✅ Панель MAX под ключ:\nДоступ выдан",
    "manual": "✅ Мануал:\nСсылка и наставник",
    "cc": "✅ CC FULL GEO:\nСписок готов",
    "spamer": "✅ Спамер MAX:\nСофт выдан",
    "bruter": "✅ Брутер:\nСофт + базы выданы"
}

orders = {}
bot = telebot.TeleBot(BOT_TOKEN)

def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🛍 КАТАЛОГ", callback_data="catalog"),
        InlineKeyboardButton("ℹ️ ИНФО", callback_data="info"),
        InlineKeyboardButton("❓ ПОМОЩЬ", callback_data="help")
    )
    return keyboard

def catalog_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for key, product in PRODUCTS.items():
        btn = InlineKeyboardButton(f"{product['name']} - ${product['price']}", callback_data=f"buy_{key}")
        keyboard.add(btn)
    keyboard.add(InlineKeyboardButton("◀️ НАЗАД", callback_data="back"))
    return keyboard

def payment_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✅ Я ОПЛАТИЛ", callback_data="paid"),
        InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel")
    )
    return keyboard

def admin_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ ПОДТВЕРДИТЬ", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_{user_id}")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "🖤 ДОБРО ПОЖАЛОВАТЬ!\nНажми КАТАЛОГ", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "catalog")
def catalog_cmd(call):
    bot.edit_message_text("🛍 ВЫБЕРИ ТОВАР:", call.message.chat.id, call.message.message_id, reply_markup=catalog_menu())

@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_cmd(call):
    bot.edit_message_text("👨‍💻 Админ: @StealShoper", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_cmd(call):
    bot.edit_message_text("❓ Проблемы: @StealShoper", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_cmd(call):
    bot.edit_message_text("🖤 ГЛАВНОЕ МЕНЮ:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_cmd(call):
    key = call.data[4:]
    if key not in PRODUCTS:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    p = PRODUCTS[key]
    uid = call.from_user.id
    orders[uid] = {'key': key, 'name': p['name'], 'price': p['price'], 'status': 'waiting'}
    text = f"💎 {p['name']}\n💰 ${p['price']} USDT\n📤 Адрес: `{TRC20_WALLET}`"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=payment_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "paid")
def paid_cmd(call):
    uid = call.from_user.id
    if uid not in orders:
        bot.send_message(uid, "❌ Нет заказа")
        bot.answer_callback_query(call.id)
        return
    orders[uid]['status'] = 'waiting_receipt'
    bot.send_message(uid, "📎 Отправь скриншот чека")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_cmd(call):
    uid = call.from_user.id
    if uid in orders:
        del orders[uid]
    bot.send_message(uid, "❌ Отменено", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    uid = msg.from_user.id
    if uid not in orders or orders[uid]['status'] != 'waiting_receipt':
        bot.reply_to(msg, "❌ Нет заказа")
        return
    p = orders[uid]
    cap = f"📩 ЧЕК\n👤 {msg.from_user.full_name}\n🆔 {uid}\n💎 {p['name']}\n💰 ${p['price']}"
    bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, cap, reply_markup=admin_keyboard(uid))
    bot.reply_to(msg, "✅ Отправлено!")
    orders[uid]['status'] = 'waiting_confirm'

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Не админ")
        return
    uid = int(call.data.split("_")[1])
    if uid not in orders:
        bot.answer_callback_query(call.id, "⚠️ Нет заказа")
        return
    key = orders[uid]['key']
    text = SERVICE_TEXT.get(key, "✅ Активировано!")
    bot.send_message(uid, f"✅ ПЛАТЕЖ ПОДТВЕРЖДЕН!\n\n{text}")
    del orders[uid]
    bot.answer_callback_query(call.id, "✅ Готово")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Не админ")
        return
    uid = int(call.data.split("_")[1])
    if uid in orders:
        bot.send_message(uid, "❌ ЧЕК ОТКЛОНЕН\nПиши @StealShoper")
        del orders[uid]
    bot.answer_callback_query(call.id, "❌ Отклонено")

print("🤖 БОТ ЗАПУЩЕН!")
bot.infinity_polling()
