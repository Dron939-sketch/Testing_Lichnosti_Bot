"""
ТЕСТОВЫЙ БОТ - Проверка платежной системы
"""

import logging
import os
import asyncio
import time
import requests
import json
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не установлен!")
    sys.exit(1)

# URL вашего Flask API
FLASK_API_URL = "https://testing-lichnosti-bot-1.onrender.com"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить Flask API", callback_data="check_api")],
        [InlineKeyboardButton("💰 Тест платежа", callback_data="test_payment")],
        [InlineKeyboardButton("📊 Проверить статус", callback_data="check_status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 Тестовый бот для проверки платежной системы\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def check_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка доступности Flask API"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Пытаемся подключиться к Flask API
        response = requests.get(f"{FLASK_API_URL}/", timeout=5)
        
        if response.status_code == 200:
            message = f"✅ Flask API доступен\nКод: {response.status_code}\nURL: {FLASK_API_URL}"
        else:
            message = f"⚠️ Flask API отвечает с кодом: {response.status_code}"
            
    except requests.exceptions.Timeout:
        message = "❌ Таймаут подключения к Flask API"
    except requests.exceptions.ConnectionError:
        message = "❌ Ошибка подключения к Flask API"
    except Exception as e:
        message = f"❌ Ошибка: {str(e)}"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест создания платежа"""
    query = update.callback_query
    await query.answer("⏳ Создаю тестовый платеж...")
    
    user_id = query.from_user.id
    payment_id = f"test_{user_id}_{int(time.time())}"
    
    try:
        # Тест 1: Проверяем доступность API
        await query.edit_message_text("🔍 Проверяю доступность API...")
        
        test_response = requests.get(f"{FLASK_API_URL}/api/test", timeout=5)
        if test_response.status_code != 200:
            raise Exception(f"API недоступен. Код: {test_response.status_code}")
        
        # Тест 2: Создаем платеж в БД
        await query.edit_message_text("📝 Создаю запись в БД...")
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 1,  # Минимальная сумма для теста
            "email": f"test{user_id}@test.com"
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{FLASK_API_URL}/api/create-payment",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Ошибка создания платежа: {response.text}")
        
        result = response.json()
        
        if not result.get("success", False):
            raise Exception(f"Ошибка в ответе: {result.get('error', 'Unknown')}")
        
        # Тест 3: Создаем платеж ЮKassa
        await query.edit_message_text("💳 Создаю платеж ЮKassa...")
        
        yookassa_payload = {
            "payment_id": payment_id,
            "amount": 1,
            "description": "Тестовый платеж",
            "return_url": "https://t.me/testing_lichnosti_bot"
        }
        
        yookassa_response = requests.post(
            f"{FLASK_API_URL}/api/create-yookassa-payment",
            json=yookassa_payload,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"YooKassa response status: {yookassa_response.status_code}")
        logger.info(f"YooKassa response text: {yookassa_response.text}")
        
        if yookassa_response.status_code != 200:
            raise Exception(f"Ошибка ЮKassa: {yookassa_response.text}")
        
        yookassa_result = yookassa_response.json()
        
        if not yookassa_result.get("success", True):
            raise Exception(f"ЮKassa ошибка: {yookassa_result.get('error', 'Unknown')}")
        
        # Сохраняем ID платежа для проверки
        context.user_data["test_payment_id"] = payment_id
        
        # Показываем результат
        message = (
            "✅ Тест пройден успешно!\n\n"
            f"📋 ID платежа: {payment_id}\n"
            f"🔗 Ссылка для оплаты: {yookassa_result.get('payment_url', 'Не получена')}\n"
            f"📊 Статус: {yookassa_result.get('status', 'unknown')}\n\n"
            f"🔄 Для проверки статуса используйте кнопку ниже."
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Проверить статус", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except requests.exceptions.Timeout:
        error_msg = "❌ Таймаут при запросе к API"
        await show_error(query, error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Ошибка подключения к API"
        await show_error(query, error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"❌ Ошибка парсинга JSON: {str(e)}"
        await show_error(query, error_msg)
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        await show_error(query, error_msg)

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    await query.answer("🔍 Проверяю статус...")
    
    payment_id = query.data.replace("check_payment_", "")
    if not payment_id:
        payment_id = context.user_data.get("test_payment_id")
    
    if not payment_id:
        await query.edit_message_text("❌ ID платежа не найден")
        return
    
    try:
        response = requests.get(
            f"{FLASK_API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        logger.info(f"Status check response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            
            message = f"📊 Статус платежа {payment_id[:8]}...: {status}"
            
            if status == "succeeded":
                message += "\n\n✅ Оплата прошла успешно!"
            elif status == "pending":
                message += "\n\n⏳ Ожидание оплаты..."
            elif status == "canceled":
                message += "\n\n❌ Платеж отменен"
            else:
                message += f"\n\nℹ️ Детали: {result}"
        else:
            message = f"❌ Ошибка проверки статуса: {response.text}"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка при проверке статуса: {str(e)}")

async def show_error(query, error_msg):
    """Показывает сообщение об ошибке"""
    logger.error(error_msg)
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(error_msg, reply_markup=reply_markup)

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к началу"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить Flask API", callback_data="check_api")],
        [InlineKeyboardButton("💰 Тест платежа", callback_data="test_payment")],
        [InlineKeyboardButton("📊 Проверить статус", callback_data="check_status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 Тестовый бот для проверки платежной системы\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса тестового платежа"""
    query = update.callback_query
    await query.answer()
    
    payment_id = context.user_data.get("test_payment_id")
    
    if not payment_id:
        message = "❌ Тестовый платеж не создан. Сначала создайте платеж."
    else:
        message = f"📋 ID тестового платежа: {payment_id}\n\nНажмите кнопку ниже для проверки статуса."
    
    keyboard = [
        [InlineKeyboardButton("📊 Проверить статус", callback_data=f"check_payment_{payment_id}")] if payment_id else [],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

# ========== ЗАПУСК БОТА ==========

def main():
    """Запуск бота"""
    print("="*50)
    print("🔧 ТЕСТОВЫЙ БОТ - Проверка платежной системы")
    print(f"🔗 Flask API: {FLASK_API_URL}")
    print(f"🤖 Токен: {'Установлен' if TOKEN else '❌ Нет!'}")
    print("="*50)
    
    # Проверка Flask API
    try:
        response = requests.get(f"{FLASK_API_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Flask API доступен")
        else:
            print(f"⚠️ Flask API: код {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка Flask API: {e}")
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_api, pattern="^check_api$"))
    application.add_handler(CallbackQueryHandler(test_payment, pattern="^test_payment$"))
    application.add_handler(CallbackQueryHandler(check_status, pattern="^check_status$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    application.add_handler(CallbackQueryHandler(check_payment_status, pattern="^check_payment_"))
    
    print("\n🤖 Бот запускается...")
    
    # Запуск с обработкой ошибки Conflict
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Важно! Сбрасывает старые обновления
        )
    except Conflict:
        print("⚠️ Обнаружен конфликт: другой экземпляр бота уже запущен")
        print("✅ Этот экземпляр завершает работу...")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
