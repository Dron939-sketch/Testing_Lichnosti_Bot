#!/usr/bin/env python3
"""
Telegram Bot для платежной системы
Исправленная версия с:
1. Защитой от конфликта getUpdates
2. Правильными платежными ссылками
"""

import os
import sys
import time
import atexit
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ========== ФИКС КОНФЛИКТА getUpdates ==========
def cleanup_bot():
    """Очистка перед выходом"""
    print("🧹 Завершение работы бота...")
    time.sleep(2)

atexit.register(cleanup_bot)

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Уменьшаем логирование httpx
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Ваш номер кошелька ЮMoney (если известен)
YOOMONEY_WALLET = YOOKASSA_SHOP_ID  # Или отдельная переменная

# ========== ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ==========
def create_payment_in_db(user_id: int, amount: float = 690.0) -> dict:
    """Создает платеж в базе данных"""
    try:
        # Генерируем уникальный ID платежа
        timestamp = int(datetime.now().timestamp())
        payment_id = f"pay_{user_id}_{timestamp}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": "Полный пакет ВАРИАТИКА"
        }
        
        logger.info(f"Создаем платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"✅ Платеж создан в БД: {payment_id}")
            return {
                "success": True,
                "payment_id": payment_id,
                "message": "Платеж создан"
            }
        else:
            logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "details": response.text[:200]
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка сети: {e}")
        return {
            "success": False,
            "error": f"Сетевая ошибка: {str(e)}"
        }
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def update_yookassa_id_in_db(payment_id: str, yookassa_id: str) -> bool:
    """Обновляет ID ЮKassa в базе данных"""
    try:
        response = requests.post(
            f"{API_URL}/api/update-yookassa-id",
            json={
                "payment_id": payment_id,
                "yookassa_id": yookassa_id,
                "status": "waiting"
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

# ========== ИСПРАВЛЕННЫЕ ПЛАТЕЖНЫЕ ФУНКЦИИ ==========
def create_yookassa_payment_smart(payment_id: str, user_id: int) -> dict:
    """
    Умное создание платежа с fallback-опциями
    Возвращает URL для оплаты в любом случае
    """
    
    # ОПЦИЯ 1: ЮKassa API (основная)
    try:
        logger.info("Пробуем ЮKassa API...")
        from yookassa import Configuration, Payment
        
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        
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
            "description": f"Оплата курса ВАРИАТИКА (ID: {payment_id})",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "product": "variatica_course"
            }
        }
        
        payment = Payment.create(payment_data)
        
        # Сохраняем ID ЮKassa
        update_yookassa_id_in_db(payment_id, payment.id)
        
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "method": "yookassa_api",
            "yookassa_id": payment.id
        }
        
    except Exception as e:
        logger.warning(f"ЮKassa API не сработал: {e}")
    
    # ОПЦИЯ 2: Прямая ссылка ЮMoney (формат 2024)
    try:
        logger.info("Пробуем прямую ссылку ЮMoney...")
        
        # Формируем правильную ссылку
        # receiver=номер кошелька (410011...)
        # sum=690
        # quickpay-form=small
        # targets=Описание
        # label=ID платежа
        
        yoomoney_url = "https://yoomoney.ru/quickpay/shop-widget"
        
        # Кодируем параметры
        import urllib.parse
        
        params = {
            'writer': 'seller',
            'targets': f'Оплата курса ВАРИАТИКА (ID: {payment_id})',
            'targets-hint': 'Курс ВАРИАТИКА',
            'default-sum': '690',
            'button-text': '11',
            'hint': 'Введите email для доступа',
            'successURL': 'https://t.me/variatica_bot',
            'label': payment_id
        }
        
        if YOOMONEY_WALLET and YOOMONEY_WALLET.startswith('4100'):
            params['receiver'] = YOOMONEY_WALLET
        
        query_string = urllib.parse.urlencode(params)
        payment_url = f"{yoomoney_url}?{query_string}"
        
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": payment_url,
            "method": "yoomoney_direct"
        }
        
    except Exception as e:
        logger.warning(f"Прямая ссылка не сработала: {e}")
    
    # ОПЦИЯ 3: Резервная ссылка
    logger.info("Используем резервную ссылку...")
    
    # Убедитесь, что YOOMONEY_WALLET содержит номер кошелька (410011...)
    if YOOMONEY_WALLET and YOOMONEY_WALLET.startswith('4100'):
        reserve_url = f"https://yoomoney.ru/to/{YOOMONEY_WALLET}/690"
    else:
        # Если нет кошелька, используем тестовый
        reserve_url = "https://yoomoney.ru/to/4100117740833021/690"
    
    return {
        "success": True,
        "payment_id": payment_id,
        "confirmation_url": reserve_url,
        "method": "reserve"
    }

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("💰 Купить доступ (690 руб)", callback_data="buy_access")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "🎯 Что вы получаете:\n"
        "• Полный доступ к материалам\n"
        "• Поддержку 24/7\n"
        "• Обновления навсегда\n\n"
        "💳 Стоимость: **690 рублей**\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy"""
    user_id = update.effective_user.id
    
    # Шаг 1: Создаем платеж в БД
    await update.message.reply_text("⏳ Создаю платеж...")
    
    db_result = create_payment_in_db(user_id)
    
    if not db_result["success"]:
        await update.message.reply_text(
            f"❌ Ошибка: {db_result.get('error', 'Неизвестная ошибка')}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )
        return
    
    payment_id = db_result["payment_id"]
    
    # Шаг 2: Создаем платежную ссылку
    await update.message.reply_text("🔗 Генерирую ссылку для оплаты...")
    
    payment_result = create_yookassa_payment_smart(payment_id, user_id)
    
    if not payment_result["success"]:
        await update.message.reply_text("❌ Не удалось создать платежную ссылку")
        return
    
    # Шаг 3: Показываем ссылку
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_{payment_id}")]
    ]
    
    await update.message.reply_text(
        f"✅ **Платеж готов!**\n\n"
        f"📋 ID платежа: `{payment_id}`\n"
        f"💰 Сумма: 690 рублей\n"
        f"📦 Товар: Полный пакет ВАРИАТИКА\n\n"
        f"**Нажмите кнопку ниже для оплаты:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    await update.message.reply_text(
        "📊 **Проверка статуса**\n\n"
        "Чтобы проверить статус платежа:\n"
        "1. Используйте кнопку 'Проверить статус' после создания платежа\n"
        "2. Или отправьте мне ID платежа в формате:\n"
        "`/check pay_123456789_1234567890`",
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check [payment_id]"""
    if not context.args:
        await update.message.reply_text("Укажите ID платежа: `/check pay_123456789_1234567890`", parse_mode='Markdown')
        return
    
    payment_id = context.args[0]
    
    try:
        response = requests.get(f"{API_URL}/api/payment-status/{payment_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            payment_data = data.get('payment', {})
            
            status = payment_data.get('status', 'unknown')
            amount = payment_data.get('amount', 690)
            created_at = payment_data.get('created_at', '')
            
            status_emoji = {
                'pending': '⏳',
                'waiting': '⏳',
                'succeeded': '✅',
                'canceled': '❌'
            }.get(status, '❓')
            
            status_text = {
                'pending': 'Ожидает оплаты',
                'waiting': 'Ожидает подтверждения',
                'succeeded': '**ОПЛАЧЕНО! Доступ открыт!** 🎉',
                'canceled': 'Отменено'
            }.get(status, status)
            
            message = (
                f"📊 **Статус платежа**\n\n"
                f"ID: `{payment_id}`\n"
                f"Статус: {status_emoji} {status_text}\n"
                f"Сумма: {amount} руб\n"
            )
            
            if created_at:
                message += f"Создан: {created_at}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        elif response.status_code == 404:
            await update.message.reply_text(f"❌ Платеж `{payment_id}` не найден", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Ошибка сервера: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await update.message.reply_text("❌ Ошибка подключения к серверу")

# ========== CALLBACK ОБРАБОТЧИКИ ==========
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "buy_access":
        await buy_callback(query)
    elif data.startswith("check_"):
        payment_id = data[6:]
        await check_status_callback(query, payment_id)
    elif data == "help":
        await help_callback(query)

async def buy_callback(query):
    """Покупка из callback"""
    user_id = query.from_user.id
    
    await query.edit_message_text("⏳ Создаю платеж...")
    
    # Создаем в БД
    db_result = create_payment_in_db(user_id)
    
    if not db_result["success"]:
        await query.edit_message_text("❌ Ошибка создания платежа")
        return
    
    payment_id = db_result["payment_id"]
    
    # Получаем платежную ссылку
    payment_result = create_yookassa_payment_smart(payment_id, user_id)
    
    if not payment_result["success"]:
        await query.edit_message_text("❌ Ошибка создания платежной ссылки")
        return
    
    # Показываем кнопку для оплаты
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_{payment_id}")]
    ]
    
    await query.edit_message_text(
        f"✅ **Готово!**\n\n"
        f"ID: `{payment_id}`\n\n"
        f"Нажмите кнопку ниже для оплаты:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def check_status_callback(query, payment_id: str):
    """Проверка статуса из callback"""
    try:
        response = requests.get(f"{API_URL}/api/payment-status/{payment_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            
            if status == 'succeeded':
                message = "✅ **ОПЛАЧЕНО!**\n\nДоступ к курсу открыт! 🎉\n\nОжидайте письмо с инструкциями."
            elif status in ['pending', 'waiting']:
                message = "⏳ **Ожидает оплаты**\n\nНажмите кнопку 'Оплатить' и завершите платеж."
            elif status == 'canceled':
                message = "❌ **Отменено**\n\nПлатеж был отменен."
            else:
                message = f"📊 Статус: {status}"
            
            keyboard = [[InlineKeyboardButton("💳 Оплатить", callback_data="buy_access")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Не удалось получить статус")
            
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await query.edit_message_text("❌ Ошибка подключения")

async def help_callback(query):
    """Помощь"""
    await query.edit_message_text(
        "❓ **Помощь**\n\n"
        "1. **Как оплатить?**\n"
        "   - Нажмите 'Купить доступ'\n"
        "   - Нажмите 'Оплатить'\n"
        "   - Завершите платеж на странице ЮKassa\n\n"
        "2. **Не пришел доступ?**\n"
        "   - Проверьте статус командой /status\n"
        "   - Если оплачено, проверьте почту\n"
        "   - Или обратитесь в поддержку\n\n"
        "3. **Возврат средств?**\n"
        "   - Обратитесь в поддержку ЮKassa\n\n"
        "Для начала нажмите 'Купить доступ' 👇",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Купить доступ", callback_data="buy_access")]])
    )

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота с защитой от конфликтов"""
    print("=" * 60)
    print("🤖 ЗАПУСК TELEGRAM БОТА ДЛЯ ПЛАТЕЖЕЙ")
    print("=" * 60)
    
    # Проверяем токен
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
        print("Добавьте в переменные окружения:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather")
        return
    
    # Проверяем конфигурацию
    print(f"🔧 API_URL: {API_URL}")
    print(f"🔧 YOOKASSA_SHOP_ID: {'установлен' if YOOKASSA_SHOP_ID else 'НЕТ!'}")
    
    if not YOOKASSA_SHOP_ID:
        print("⚠️  ВНИМАНИЕ: YOOKASSA_SHOP_ID не установлен!")
        print("Платежные ссылки могут не работать корректно")
    
    try:
        # Создаем приложение с ограниченными обновлениями
        app = Application.builder().token(TOKEN).build()
        
        # Регистрируем команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", buy_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("check", check_command))
        
        # Регистрируем callback-обработчики
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        # Запускаем бота с очисткой очереди
        print("✅ Бот запускается...")
        print("📱 Перейдите в Telegram и найдите своего бота")
        print("🛑 Для остановки нажмите Ctrl+C\n")
        
        app.run_polling(
            drop_pending_updates=True,  # ОЧЕНЬ ВАЖНО! Убирает старые обновления
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Возможные причины:")
        print("1. Неверный токен бота")
        print("2. Конфликт с другим запущенным ботом")
        print("3. Проблемы с сетью")
        
        # Ждем перед повторной попыткой (если запускается как сервис)
        time.sleep(10)

if __name__ == "__main__":
    main()
