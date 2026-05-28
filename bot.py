import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import threading
import time
import requests
import json

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8996166045:AAEK0XqPv00eC91gFhcMvYcWZlgsGupOXVM"  # НОВЫЙ ТОКЕН
ADMIN_ID = 7738397444
TRC20_WALLET = "TSZ35HrnGnX631MPwiScxmPzvWb5QpAJUb"

# Токен Crypto Pay (от @CryptoBot)
CRYPTO_PAY_TOKEN = "588559:AAe1SxhACG2NYLrNd2WCXrt6kDiiGsWqcvd"

# API URL для Crypto Pay
CRYPTO_PAY_API = "https://pay.crypt.bot/api"

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

# ========== ФУНКЦИИ CRYPTO PAY ==========
def create_crypto_invoice(amount, asset="USDT"):
    """Создает счет в Crypto Pay"""
    url = f"{CRYPTO_PAY_API}/createInvoice"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "asset": asset,
        "amount": str(amount)
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if result.get("ok"):
            invoice = result["result"]
            return {
                "invoice_id": invoice["invoice_id"],
                "pay_url": invoice["pay_url"],
                "status": invoice["status"]
            }
        else:
            print(f"Ошибка: {result}")
            return None
    except Exception as e:
        print(f"Ошибка создания счета: {e}")
        return None

def check_invoice_status(invoice_id):
    """Проверяет статус счета"""
    url = f"{CRYPTO_PAY_API}/getInvoices"
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN,
        "Content-Type": "application/json"
    }
    params = {"invoice_ids": invoice_id}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        result = response.json()
        
        if result.get("ok") and result["result"]["items"]:
            return result["result"]["items"][0]["status"]
        return None
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        return None

# ========== ФОНОВАЯ ПРОВЕРКА ОПЛАТ ==========
def check_payments_background():
    """Фоновый поток для проверки оплат"""
    while True:
        try:
            for uid, order in list(orders.items()):
                if order.get('status') == 'waiting_payment' and order.get('invoice_id'):
                    status = check_invoice_status(order['invoice_id'])
                    
                    if status == "paid":
                        key = order['key']
                        service_info = SERVICE_TEXT.get(key, "✅ Услуга активирована!")
                        bot.send_message(uid, f"✅ **ПЛАТЕЖ ПОДТВЕРЖДЕН!**\n\n{service_info}")
                        bot.send_message(ADMIN_ID, f"✅ Оплата получена!\nПользователь: {uid}\nТовар: {order['name']}\nСумма: ${order['price']}")
                        del orders[uid]
                    elif status == "expired":
                        bot.send_message(uid, "❌ Время оплаты истекло. Повторите заказ /start")
                        del orders[uid]
        except Exception as e:
            print(f"Ошибка в фоновой проверке: {e}")
        
        time.sleep(10)

# ========== КЛАВИАТУРЫ ==========
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
        InlineKeyboardButton("✅ Я ОПЛАТИЛ (ЧЕК)", callback_data="paid_manual"),
        InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel")
    )
    return keyboard

def crypto_payment_keyboard(pay_url):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💎 ОПЛАТИТЬ ЧЕРЕЗ CRYPTO BOT", url=pay_url),
        InlineKeyboardButton("✅ Я ОПЛАТИЛ (ЧЕК)", callback_data="paid_manual"),
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

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    start_text = """🖤 **ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН!** 🖤

💎 **Оплата через CryptoBot** - мгновенно и без комиссии
💰 **Или напрямую на кошелек** USDT (TRC20)

👇 **Нажми КАТАЛОГ чтобы начать**"""
    bot.send_message(message.chat.id, start_text, parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "catalog")
def catalog_cmd(call):
    bot.edit_message_text("🛍 **ВЫБЕРИ ТОВАР:**", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=catalog_menu())

@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_cmd(call):
    info_text = """ℹ️ **ИНФОРМАЦИЯ**

👨‍💻 **Админ:** @StealShoper
💰 **Кошелек USDT (TRC20):** `TSZ35HrnGnX631MPwiScxmPzvWb5QpAJUb`
💎 **Crypto Bot:** @CryptoBot"""
    bot.edit_message_text(info_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_cmd(call):
    help_text = """❓ **ПОМОЩЬ**

📌 **Способы оплаты:**
1️⃣ Через Crypto Bot (мгновенно)
2️⃣ Напрямую на кошелек USDT TRC20

⚠️ **Проблемы:** @StealShoper"""
    bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_cmd(call):
    start_text = """🖤 **ДОБРО ПОЖАЛОВАТЬ В МАГАЗИН!** 🖤
👇 **Нажми КАТАЛОГ чтобы начать**"""
    bot.edit_message_text(start_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_cmd(call):
    key = call.data[4:]
    if key not in PRODUCTS:
        bot.answer_callback_query(call.id, "Ошибка")
        return
    
    p = PRODUCTS[key]
    uid = call.from_user.id
    
    invoice = create_crypto_invoice(p['price'])
    
    if invoice:
        orders[uid] = {
            'key': key,
            'name': p['name'],
            'price': p['price'],
            'status': 'waiting_payment',
            'invoice_id': invoice['invoice_id']
        }
        
        text = f"""💎 **{p['name']}**
💰 **Сумма:** ${p['price']} USDT

🔗 **Оплатить через Crypto Bot:** [НАЖМИ ДЛЯ ОПЛАТЫ]({invoice['pay_url']})

💳 **Или переведите напрямую на кошелек:** `TSZ35HrnGnX631MPwiScxmPzvWb5QpAJUb`

⏱ **Счет действителен 1 час**

❗️ **После оплаты нажмите кнопку «Я ОПЛАТИЛ» и отправьте чек (если оплачивали вручную)**"""
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=crypto_payment_keyboard(invoice['pay_url']))
    else:
        orders[uid] = {
            'key': key,
            'name': p['name'],
            'price': p['price'],
            'status': 'waiting_payment'
        }
        
        text = f"""💎 **{p['name']}**
💰 **Сумма:** ${p['price']} USDT

💳 **Переведите на кошелек:** `TSZ35HrnGnX631MPwiScxmPzvWb5QpAJUb`

❗️ **После оплаты нажмите кнопку «Я ОПЛАТИЛ» и отправьте чек**"""
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=payment_keyboard())
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "paid_manual")
def paid_manual_cmd(call):
    uid = call.from_user.id
    if uid not in orders:
        bot.send_message(uid, "❌ Нет активного заказа")
        bot.answer_callback_query(call.id)
        return
    
    orders[uid]['status'] = 'waiting_receipt'
    bot.send_message(uid, "📎 **Отправьте скриншот/фото чека об оплате**")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_cmd(call):
    uid = call.from_user.id
    if uid in orders:
        del orders[uid]
    bot.send_message(uid, "❌ Заказ отменен", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    uid = msg.from_user.id
    if uid not in orders or orders[uid]['status'] != 'waiting_receipt':
        bot.reply_to(msg, "❌ Нет активного заказа на проверке")
        return
    
    p = orders[uid]
    cap = f"📩 **ЧЕК НА ПРОВЕРКУ**\n👤 {msg.from_user.full_name}\n🆔 {uid}\n💎 {p['name']}\n💰 ${p['price']}"
    bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, cap, parse_mode="Markdown", reply_markup=admin_keyboard(uid))
    bot.reply_to(msg, "✅ **Чек отправлен!** Ожидайте подтверждения")
    orders[uid]['status'] = 'waiting_confirm'

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Только для админа")
        return
    
    uid = int(call.data.split("_")[1])
    if uid not in orders:
        bot.answer_callback_query(call.id, "⚠️ Заказ не найден")
        return
    
    key = orders[uid]['key']
    text = SERVICE_TEXT.get(key, "✅ Услуга активирована!")
    bot.send_message(uid, f"✅ **ПЛАТЕЖ ПОДТВЕРЖДЕН!**\n\n{text}")
    bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"✅ ПОДТВЕРЖДЕН\n{call.message.caption}")
    del orders[uid]
    bot.answer_callback_query(call.id, "✅ Готово")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Только для админа")
        return
    
    uid = int(call.data.split("_")[1])
    if uid in orders:
        bot.send_message(uid, "❌ **ЧЕК ОТКЛОНЕН**\n\nПишите @StealShoper")
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"❌ ОТКЛОНЕН\n{call.message.caption}")
        del orders[uid]
    bot.answer_callback_query(call.id, "❌ Отклонено")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    payment_thread = threading.Thread(target=check_payments_background, daemon=True)
    payment_thread.start()
    
    print("🤖 БОТ ЗАПУЩЕН!")
    print("💎 Криптоплатежи через Crypto Bot активны!")
    bot.infinity_polling()
