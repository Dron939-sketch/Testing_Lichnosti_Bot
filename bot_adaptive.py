#!/usr/bin/env python3
"""
Telegram Bot для платежной системы
ИСПРАВЛЕННАЯ ВЕРСИЯ без ошибок yookassa
"""

import os
import sys
import time
import atexit
import logging
import requests
import json
import urllib.parse
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
# Уменьшаем логирование
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('yookassa').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# ========== АЛЬТЕРНАТИВНАЯ РЕАЛИЗАЦИЯ ЮKASSA БЕЗ БИБЛИОТЕКИ ==========
def create_payment_yookassa_direct(payment_id: str, user_id: int) -> dict:
    """
    Создание платежа через прямое API ЮKassa
    БЕЗ использования библиотеки yookassa
    """
    try:
        import base64
        
        # Авторизация Basic Auth
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id  # Уникальный ключ
        }
        
        payload = {
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
        
        # Отправляем запрос к API ЮKassa
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"ЮKassa API ответ: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": data.get('id'),
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "status": data.get('status'),
                "method": "yookassa_api_direct"
            }
        else:
            logger.error(f"ЮKassa API ошибка: {response.text}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "details": response.text[:200]
            }
            
    except Exception as e:
        logger.error(f"Ошибка прямого API ЮKassa: {e}")
        return {
            "success": False,
            "error": str(e)[:100]
        }

def create_yoomoney_simple_link(payment_id: str, user_id: int) -> dict:
    """
    Простая ссылка на ЮMoney для быстрых платежей
    Используем формат: https://yoomoney.ru/transfer/quickpay/confirm.xml
    """
    try:
        # Если у нас есть номер кошелька ЮMoney (410011...)
        wallet_number = YOOKASSA_SHOP_ID
        
        # Формируем правильный URL
        params = {
            'receiver': wallet_number if wallet_number and wallet_number.startswith('4100') else '4100117740833021',
            'quickpay-form': 'shop',
            'targets': f'Оплата курса ВАРИАТИКА (ID: {payment_id})',
            'paymentType': 'AC',
            'sum': '690',
            'label': payment_id,
            'successURL': 'https://t.me/variatica_bot'
        }
        
        # Два варианта URL
        url_variant_1 = f"https://yoomoney.ru/transfer/quickpay/confirm.xml?{urllib.parse.urlencode(params)}"
        url_variant_2 = f"https://yoomoney.ru/quickpay/confirm.xml?{urllib.parse.urlencode(params)}"
        
        # Проверяем, какой URL рабочий
        for test_url in [url_variant_1, url_variant_2]:
            try:
                test_response = requests.head(test_url, timeout=5, allow_redirects=True)
                if test_response.status_code < 400:
                    logger.info(f"URL рабочий: {test_url[:50]}...")
                    return {
                        "success": True,
                        "payment_id": payment_id,
                        "confirmation_url": test_url,
                        "method": "yoomoney_simple"
                    }
            except:
                continue
        
        # Если ни один URL не сработал, используем самый простой
        final_url = f"https://yoomoney.ru/to/{params['receiver']}/690"
        
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": final_url,
            "method": "yoomoney_fallback"
        }
        
    except Exception as e:
        logger.error(f"Ошибка создания ссылки ЮMoney: {e}")
        
        # Аварийная ссылка
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": "https://yoomoney.ru/to/4100117740833021/690",
            "method": "emergency"
        }

def create_payment_link_smart(payment_id: str, user_id: int) -> dict:
    """
    Умное создание платежной ссылки
    Пробуем разные методы по очереди
    """
    logger.info(f"Создаем платежную ссылку для {payment_id}")
    
    # Метод 1: Прямой API ЮKassa (самый надежный)
    logger.info("Пробуем прямой API ЮKassa...")
    result = create_payment_yookassa_direct(payment_id, user_id)
    
    if result["success"]:
        logger.info("✅ Успешно через прямой API ЮKassa")
        return result
    
    # Метод 2: Простая ссылка ЮMoney
    logger.info("Пробуем простую ссылку ЮMoney...")
    result = create_yoomoney_simple_link(payment_id, user_id)
    
    if result["success"]:
        logger.info("✅ Успешно через ЮMoney")
        return result
    
    # Метод 3: Запасной вариант
    logger.warning("Использую запасную ссылку...")
    return {
        "success": True,
        "payment_id": payment_id,
        "confirmation_url": "https://yoomoney.ru/to/4100117740833021/690",
        "method": "fallback",
        "note": "Это тестовая ссылка. Замените на свою в настройках."
    }

# ========== ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ==========
def create_payment_in_db(user_id: int) -> dict:
    """Создает платеж в базе данных"""
    try:
        # Генерируем уникальный ID платежа
        timestamp = int(datetime.now().timestamp())
        payment_id = f"pay_{user_id}_{timestamp}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 690.00,
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
            logger.error(f"❌ Ошибка API БД: {response.status_code}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
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
                "yookassa_id": yookassa_id
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка обновления ID: {e}")
        return False

def check_payment_status(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========== TELEGRAM КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("💰 Купить доступ", callback_data="buy")],
        [InlineKeyboardButton("📊 Мой статус", callback_data="mystatus")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(
        f"👋 Добро пожаловать, {user.first_name}!\n\n"
        "Это бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "💎 **Что включено:**\n"
        "• Все видеоуроки и материалы\n"
        "• Доступ навсегда\n"
        "• Поддержка и обновления\n\n"
        "💰 **Цена:** 690 рублей\n\n"
        "Нажмите **Купить доступ** для оплаты:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy"""
    user = update.effective_user
    
    # Создаем платеж в БД
    result = create_payment_in_db(user.id)
    
    if not result["success"]:
        await update.message.reply_text(
            "❌ **Ошибка создания платежа**\n\n"
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    payment_id = result["payment_id"]
    
    # Создаем платежную ссылку
    payment_result = create_payment_link_smart(payment_id, user.id)
    
    if not payment_result.get("success", False):
        await update.message.reply_text(
            "❌ **Ошибка платежной системы**\n\n"
            "Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    # Отправляем пользователю ссылку
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"status_{payment_id}")]
    ]
    
    message_text = (
        f"✅ **Платеж создан!**\n\n"
        f"📋 ID: `{payment_id}`\n"
        f"👤 Пользователь: {user.first_name}\n"
        f"💰 Сумма: 690 рублей\n\n"
        f"**Нажмите кнопку ниже для оплаты:**\n"
        f"После оплаты нажмите 'Проверить оплату'"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    await update.message.reply_text(
        "📊 **Проверка статуса**\n\n"
        "1. После создания платежа используйте кнопку 'Проверить оплату'\n"
        "2. Или введите: `/check ID_платежа`\n"
        "3. ID платежа выглядит так: `pay_123456789_1234567890`\n\n"
        "Если платеж успешен, доступ откроется автоматически.",
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check [payment_id]"""
    if not context.args:
        await update.message.reply_text(
            "Укажите ID платежа:\n"
            "`/check pay_123456789_1234567890`",
            parse_mode='Markdown'
        )
        return
    
    payment_id = context.args[0]
    await process_payment_status(update, payment_id)

async def process_payment_status(update, payment_id: str):
    """Обрабатывает проверку статуса"""
    result = check_payment_status(payment_id)
    
    if not result["success"]:
        await update.message.reply_text(
            f"❌ Не удалось проверить статус платежа `{payment_id}`",
            parse_mode='Markdown'
        )
        return
    
    payment_data = result["data"].get("payment", {})
    status = payment_data.get("status", "unknown")
    
    # Форматируем ответ
    if status == "succeeded":
        response_text = (
            f"🎉 **ОПЛАЧЕНО!**\n\n"
            f"✅ Платеж `{payment_id}` успешно завершен!\n"
            f"💰 Сумма: {payment_data.get('amount', 690)} руб\n"
            f"📅 Оплачено: {payment_data.get('confirmed_at', 'только что')}\n\n"
            f"**Доступ к курсу открыт!**\n"
            f"Ожидайте письмо с инструкциями."
        )
    elif status in ["pending", "waiting"]:
        response_text = (
            f"⏳ **ОЖИДАЕТ ОПЛАТЫ**\n\n"
            f"Платеж `{payment_id}` еще не оплачен.\n\n"
            f"**Чтобы оплатить:**\n"
            f"1. Нажмите /buy для новой ссылки\n"
            f"2. Или используйте старую ссылку\n\n"
            f"После оплаты проверьте статус снова."
        )
    elif status == "canceled":
        response_text = (
            f"❌ **ОТМЕНЕНО**\n\n"
            f"Платеж `{payment_id}` был отменен.\n\n"
            f"Для нового платежа нажмите /buy"
        )
    else:
        response_text = (
            f"📊 **СТАТУС ПЛАТЕЖА**\n\n"
            f"ID: `{payment_id}`\n"
            f"Статус: {status}\n"
            f"Сумма: {payment_data.get('amount', 690)} руб"
        )
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

# ========== CALLBACK ОБРАБОТЧИКИ ==========
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "buy":
        await process_buy_callback(query)
    elif data.startswith("status_"):
        payment_id = data[7:]
        await process_status_callback(query, payment_id)
    elif data == "mystatus":
        await query.edit_message_text(
            "📊 **Мой статус**\n\n"
            "Чтобы проверить статус:\n"
            "1. Найдите ID платежа (он был при создании)\n"
            "2. Нажмите /check и введите ID\n"
            "3. Или создайте новый платеж: /buy",
            parse_mode='Markdown'
        )
    elif data == "help":
        await query.edit_message_text(
            "❓ **Помощь и поддержка**\n\n"
            "**Частые вопросы:**\n"
            "1. *Как оплатить?* - Нажмите /buy и следуйте инструкциям\n"
            "2. *Не пришел доступ?* - Проверьте статус /check\n"
            "3. *Ошибка платежа?* - Попробуйте снова через 5 минут\n"
            "4. *Возврат средств?* - Обратитесь в поддержку ЮMoney\n\n"
            "**Контакты поддержки:**\n"
            "Email: support@example.com\n"
            "Telegram: @support_bot\n\n"
            "Нажмите /buy для начала оплаты:",
            parse_mode='Markdown'
        )

async def process_buy_callback(query):
    """Обработка покупки из callback"""
    user = query.from_user
    
    # Создаем платеж в БД
    result = create_payment_in_db(user.id)
    
    if not result["success"]:
        await query.edit_message_text(
            "❌ **Ошибка создания платежа**\n\n"
            "Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    payment_id = result["payment_id"]
    
    # Создаем платежную ссылку
    payment_result = create_payment_link_smart(payment_id, user.id)
    
    if not payment_result.get("success", False):
        await query.edit_message_text(
            "❌ **Ошибка платежной системы**\n\n"
            "Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    # Показываем кнопку для оплаты
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"status_{payment_id}")]
    ]
    
    await query.edit_message_text(
        f"✅ **Готово к оплате!**\n\n"
        f"ID платежа: `{payment_id}`\n\n"
        f"**Нажмите кнопку ниже:**\n"
        f"После оплаты вернитесь и нажмите 'Проверить оплату'",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def process_status_callback(query, payment_id: str):
    """Проверка статуса из callback"""
    result = check_payment_status(payment_id)
    
    if not result["success"]:
        await query.edit_message_text(
            f"❌ Не удалось проверить статус `{payment_id}`",
            parse_mode='Markdown'
        )
        return
    
    payment_data = result["data"].get("payment", {})
    status = payment_data.get("status", "unknown")
    
    if status == "succeeded":
        message = (
            f"🎉 **ОПЛАЧЕНО!**\n\n"
            f"✅ Платеж завершен успешно!\n"
            f"Доступ к курсу открыт.\n\n"
            f"Ожидайте письмо с инструкциями."
        )
        keyboard = []
    else:
        message = (
            f"⏳ **Статус: {status.upper()}**\n\n"
            f"Платеж еще не завершен.\n\n"
            f"ID: `{payment_id}`\n"
            f"Для оплаты нажмите кнопку ниже:"
        )
        keyboard = [[InlineKeyboardButton("💳 Оплатить", callback_data="buy")]]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        parse_mode='Markdown'
    )

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота"""
    print("=" * 60)
    print("🤖 TELEGRAM БОТ ДЛЯ ПЛАТЕЖЕЙ")
    print("=" * 60)
    print(f"Версия: 2.0 (исправлена ошибка yookassa)")
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Проверка конфигурации
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        print("Добавьте в Render переменные окружения:")
        print("- TELEGRAM_BOT_TOKEN")
        print("- YOOKASSA_SHOP_ID")
        print("- YOOKASSA_SECRET_KEY")
        print("- API_URL")
        sys.exit(1)
    
    print(f"✅ Токен бота: {'установлен' if TOKEN else 'НЕТ!'}")
    print(f"🔗 API URL: {API_URL}")
    print(f"💰 ЮKassa Shop ID: {'установлен' if YOOKASSA_SHOP_ID else 'НЕТ!'}")
    print(f"🔑 ЮKassa Secret: {'установлен' if YOOKASSA_SECRET_KEY else 'НЕТ!'}")
    
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        print("⚠️  ВНИМАНИЕ: Данные ЮKassa неполные!")
        print("Платежи могут работать через простые ссылки ЮMoney")
    
    print("=" * 60)
    print("🔄 Запуск бота...")
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики команд
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", buy_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("check", check_command))
        
        # Добавляем callback обработчики
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        # Запускаем бота
        print("✅ Бот запущен успешно!")
        print("📱 Ищите бота в Telegram")
        print("🛑 Для остановки: Ctrl+C")
        print("=" * 60)
        
        # Ключевая настройка для избежания конфликтов
        app.run_polling(
            drop_pending_updates=True,  # Очищает очередь обновлений
            allowed_updates=Update.ALL_TYPES,
            pool_timeout=30,
            read_timeout=30,
            connect_timeout=30
        )
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Перезапуск через 10 секунд...")
        time.sleep(10)
        main()  # Рекурсивный перезапуск

if __name__ == "__main__":
    main()
