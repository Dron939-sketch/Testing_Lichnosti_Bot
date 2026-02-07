"""
bot_adaptive.py - Telegram бот с исправленной ошибкой receipt
"""

import os
import sys
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# ============================================
# ИСПРАВЛЕННАЯ ФУНКЦИЯ ЮKASSA
# ============================================

def create_yookassa_payment_fixed(payment_id: str, user_id: int) -> dict:
    """
    Создает платеж в ЮKassa БЕЗ receipt
    ИСПРАВЛЕННАЯ ВЕРСИЯ - работает с yookassa==2.3.0
    """
    try:
        from yookassa import Configuration, Payment
        
        # Настраиваем ЮKassa
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        
        # ПРОСТОЙ платеж БЕЗ receipt
        payment_data = {
            "amount": {
                "value": "690.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,
            "description": "Оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "product": "variatica_course"
            }
        }
        
        # Создаем платеж
        payment = Payment.create(payment_data)
        
        # Сохраняем ID ЮKassa
        try:
            requests.post(
                f"{API_URL}/api/update-yookassa-id",
                json={"payment_id": payment_id, "yookassa_id": payment.id},
                timeout=5
            )
        except:
            pass
        
        return {
            "success": True,
            "payment_id": payment_id,
            "yookassa_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка ЮKassa (fixed): {e}")
        return {
            "success": False,
            "error": f"ЮKassa: {str(e)[:100]}"
        }

def create_yookassa_payment_simple(payment_id: str, user_id: int) -> dict:
    """Альтернативный метод - простой URL"""
    try:
        # Генерируем прямую ссылку на ЮMoney
        yoomoney_url = f"https://yoomoney.ru/quickpay/confirm.xml"
        params = {
            "receiver": YOOKASSA_SHOP_ID,  # Номер кошелька
            "quickpay-form": "shop",
            "targets": f"Оплата курса ВАРИАТИКА (ID: {payment_id})",
            "sum": "690",
            "paymentType": "AC",
            "label": payment_id
        }
        
        # Формируем URL
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        payment_url = f"{yoomoney_url}?{query_string}"
        
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": payment_url,
            "method": "yoomoney_direct"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# ОСНОВНЫЕ ФУНКЦИИ (остаются как были)
# ============================================

def create_payment_in_db(user_id: int, amount: float = 690.0) -> dict:
    """Создает платеж в базе данных"""
    try:
        payment_id = f"pay_{user_id}_{int(datetime.now().timestamp())}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": "Полный пакет ВАРИАТИКА"
        }
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"✅ Платеж создан: {payment_id}")
            return {"success": True, "payment_id": payment_id}
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# УПРОЩЕННЫЕ ХЕНДЛЕРЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Простой старт"""
    user = update.effective_user
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Купить доступ (690 руб)", callback_data="buy")],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data="check_status")]
    ])
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса ВАРИАТИКА.\n\n"
        "💳 Стоимость: 690 рублей\n"
        "🎁 Доступ навсегда\n\n"
        "Нажмите кнопку ниже:",
        reply_markup=keyboard
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упрощенная покупка"""
    user_id = update.effective_user.id
    
    # Создаем платеж в БД
    payment_result = create_payment_in_db(user_id)
    
    if not payment_result["success"]:
        await update.message.reply_text("❌ Ошибка создания платежа. Попробуйте позже.")
        return
    
    payment_id = payment_result["payment_id"]
    
    # Пробуем метод 1: yookassa==2.3.0
    payment_result = create_yookassa_payment_fixed(payment_id, user_id)
    
    if not payment_result["success"]:
        # Метод 2: прямая ссылка ЮMoney
        payment_result = create_yookassa_payment_simple(payment_id, user_id)
    
    if not payment_result["success"]:
        # Метод 3: простая ссылка для теста
        test_url = f"https://yoomoney.ru/to/410011000000000/690"
        payment_result = {
            "success": True,
            "confirmation_url": test_url
        }
    
    # Отправляем ссылку
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")]
    ])
    
    await update.message.reply_text(
        f"✅ Платеж создан!\n\n"
        f"ID: `{payment_id}`\n"
        f"Нажмите кнопку для оплаты:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def check_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса"""
    await update.message.reply_text(
        "📊 Для проверки статуса:\n"
        "1. Создайте платеж командой /buy\n"
        "2. Используйте кнопку 'Проверить статус'\n\n"
        "Или отправьте: `status_ваш_id`",
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "buy":
        await buy_callback_simple(query)
    elif data.startswith("status_"):
        payment_id = data[7:]
        await check_status_simple(query, payment_id)
    elif data == "check_status":
        await query.edit_message_text("Для проверки статуса создайте платеж командой /buy")

async def buy_callback_simple(query):
    """Покупка из callback"""
    user_id = query.from_user.id
    
    await query.edit_message_text("⏳ Создаю платеж...")
    
    payment_result = create_payment_in_db(user_id)
    
    if not payment_result["success"]:
        await query.edit_message_text("❌ Ошибка. Попробуйте позже.")
        return
    
    payment_id = payment_result["payment_id"]
    
    # Пробуем разные методы оплаты
    payment_link = None
    
    # Метод 1
    result1 = create_yookassa_payment_fixed(payment_id, user_id)
    if result1["success"]:
        payment_link = result1["confirmation_url"]
    
    # Метод 2
    if not payment_link:
        result2 = create_yookassa_payment_simple(payment_id, user_id)
        if result2["success"]:
            payment_link = result2["confirmation_url"]
    
    # Метод 3 (fallback)
    if not payment_link:
        payment_link = f"https://yoomoney.ru/to/{YOOKASSA_SHOP_ID}/690"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 690 руб", url=payment_link)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")]
    ])
    
    await query.edit_message_text(
        f"✅ Готово! ID: `{payment_id}`\n\n"
        f"Нажмите для оплаты:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def check_status_simple(query, payment_id: str):
    """Простая проверка статуса"""
    try:
        response = requests.get(f"{API_URL}/api/payment-status/{payment_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            
            status_text = {
                'pending': '⏳ Ожидает оплаты',
                'succeeded': '✅ Оплачено! Доступ открыт! 🎉',
                'canceled': '❌ Отменено'
            }.get(status, status)
            
            await query.edit_message_text(
                f"📊 Статус `{payment_id}`:\n\n{status_text}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Не удалось проверить статус")
    except:
        await query.edit_message_text("❌ Ошибка подключения")

# ============================================
# ЗАПУСК БОТА
# ============================================

def main():
    """Запуск упрощенного бота"""
    print("="*60)
    print("🤖 ЗАПУСК УПРОЩЕННОГО БОТА")
    print("="*60)
    
    if not TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен")
        return
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", buy_command))
        app.add_handler(CommandHandler("check", check_status_command))
        
        # Callback
        app.add_handler(CallbackQueryHandler(handle_callback, pattern="^buy$"))
        app.add_handler(CallbackQueryHandler(handle_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(handle_callback, pattern="^check_status$"))
        
        print("✅ Бот запущен")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
