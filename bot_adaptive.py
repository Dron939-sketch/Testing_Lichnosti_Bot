#!/usr/bin/env python3
"""
Telegram Bot для платежной системы ЮKassa
Оптимизированная версия с защитой от конфликтов
"""

import os
import sys
import time
import json
import base64
import logging
import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ApplicationBuilder
)

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Уменьшаем логирование библиотек
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# ========== ПРОВЕРКА КОНФИГУРАЦИИ ==========
def check_configuration():
    """Проверяет все настройки перед запуском"""
    print("=" * 60)
    print("🤖 ЗАПУСК ТЕЛЕГРАМ БОТА")
    print("=" * 60)
    
    errors = []
    
    # Проверка токена
    if not TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установлен")
    else:
        print(f"✅ Токен бота: установлен")
    
    # Проверка URL API
    if not API_URL:
        errors.append("⚠️ API_URL не установлен, используется по умолчанию")
    else:
        print(f"✅ API URL: {API_URL}")
    
    # Проверка ЮKassa
    if not YOOKASSA_SHOP_ID:
        errors.append("❌ YOOKASSA_SHOP_ID не установлен")
    else:
        print(f"✅ Shop ID: {'установлен' if YOOKASSA_SHOP_ID else 'НЕТ!'}")
    
    if not YOOKASSA_SECRET_KEY:
        errors.append("❌ YOOKASSA_SECRET_KEY не установлен")
    else:
        key_type = "ТЕСТОВЫЙ" if YOOKASSA_SECRET_KEY.startswith('test_') else "БОЕВОЙ"
        print(f"✅ Secret Key: {key_type}")
    
    print("=" * 60)
    
    if errors:
        for error in errors:
            print(error)
        return False
    
    return True

# ========== ФУНКЦИИ ДЛЯ ЮKASSA ==========
def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 1.0) -> dict:
    """Создает платеж в ЮKassa (версия для yookassa==2.3.0)"""
    try:
        # Basic Auth для ЮKassa API v3
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id
        }
        
        # Используем версию без receipt для yookassa==2.3.0
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,
            "description": f"Тестовый платеж #{payment_id}",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id)
            }
        }
        
        logger.info(f"Создаю платеж в ЮKassa: {payment_id} на {amount} руб")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            yookassa_id = data.get('id')
            
            # Сохраняем ID ЮKassa в базе
            try:
                requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={
                        "payment_id": payment_id,
                        "yookassa_id": yookassa_id,
                        "status": "waiting"
                    },
                    timeout=10
                )
                logger.info(f"ID сохранен в БД: {yookassa_id}")
            except Exception as e:
                logger.error(f"Ошибка сохранения ID: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": yookassa_id,
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "status": data.get('status'),
                "amount": amount
            }
        else:
            error_text = response.text[:300]
            logger.error(f"Ошибка ЮKassa {response.status_code}: {error_text}")
            
            return {
                "success": False,
                "error": f"Код {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"Исключение: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ========== ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ==========
def create_payment_in_db(user_id: int, amount: float = 1.0) -> dict:
    """Создает запись о платеже в базе данных"""
    try:
        timestamp = int(time.time())
        payment_id = f"test_{user_id}_{timestamp}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": f"Тестовый платеж {amount} руб"
        }
        
        logger.info(f"Создаю платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Платеж создан в БД: {payment_id}")
            return {
                "success": True,
                "payment_id": payment_id
            }
        else:
            logger.error(f"Ошибка БД {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            return {
                "success": True,
                "status": status,
                "data": data
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
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА (1 рубль)", callback_data="test_buy")],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data="check_status_menu")]
    ]
    
    message_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "*Тестовая платежная система*\n\n"
        "💰 *Сумма:* 1 рубль\n"
        "🎯 *Цель:* Проверить работу платежей\n\n"
        "Нажмите кнопку ниже для создания тестового платежа:"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def test_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка тестовой покупки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Шаг 1: Создаем в БД
    await query.edit_message_text("📦 *Создаю платеж в базе данных...*", parse_mode='Markdown')
    
    db_result = create_payment_in_db(user_id)
    if not db_result["success"]:
        await query.edit_message_text(f"❌ *Ошибка базы:* {db_result.get('error')}", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    # Шаг 2: Создаем в ЮKassa
    await query.edit_message_text("💳 *Создаю платеж в ЮKassa...*", parse_mode='Markdown')
    
    payment_result = create_yookassa_payment(payment_id, user_id)
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка ЮKassa:* {error_msg}", parse_mode='Markdown')
        return
    
    # Шаг 3: Показываем ссылку
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")]
    ]
    
    message_text = (
        f"✅ *Платеж создан!*\n\n"
        f"*ID:* `{payment_id}`\n"
        f"*Сумма:* 1 рубль\n"
        f"*Статус:* ожидание оплаты\n\n"
        f"Нажмите кнопку для оплаты:"
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 Проверяю статус `{payment_id}`...", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text(f"❌ Не удалось проверить статус", parse_mode='Markdown')
            return
        
        status = result.get("status", "unknown")
        
        if status == "succeeded":
            message = f"🎉 *ОПЛАЧЕНО!*\n\nПлатеж `{payment_id}` успешно завершен!"
        elif status in ["pending", "waiting"]:
            message = f"⏳ *ОЖИДАНИЕ*\n\nПлатеж `{payment_id}` ожидает оплаты"
        else:
            message = f"📊 Статус: *{status}*"
        
        await query.edit_message_text(message, parse_mode='Markdown')

async def check_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню проверки статуса"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 *Проверка статуса*\n\n"
        "Используйте команду:\n"
        "`/check ID_платежа`\n\n"
        "Или создайте новый платеж:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧪 Новый тестовый платеж", callback_data="test_buy")]])
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check"""
    if not context.args:
        await update.message.reply_text(
            "Использование: `/check ID_платежа`\n"
            "Пример: `/check test_123456_1234567890`",
            parse_mode='Markdown'
        )
        return
    
    payment_id = context.args[0]
    result = check_payment_status_db(payment_id)
    
    if result["success"]:
        status = result.get("status", "unknown")
        await update.message.reply_text(f"Статус `{payment_id}`: *{status}*", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Ошибка проверки `{payment_id}`")

# ========== ОБРАБОТЧИК ОШИБОК ==========
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Упрощенный обработчик ошибок"""
    error_msg = str(context.error)
    
    # Логируем все ошибки
    logger.error(f"Ошибка: {error_msg}")
    
    # Конфликт с другим ботом
    if "Conflict" in error_msg and "getUpdates" in error_msg:
        logger.warning("⚠️ Конфликт с другим ботом!")
        # Просто логируем, не пытаемся исправить
        
    # Уведомляем пользователя только если есть update
    if update and isinstance(update, Update):
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text("⚠️ Произошла ошибка, попробуйте снова")
            elif update.message:
                await update.message.reply_text("⚠️ Произошла ошибка, попробуйте снова")
        except:
            pass

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска"""
    # Проверяем конфигурацию
    if not check_configuration():
        print("❌ Конфигурация неполная, выход...")
        sys.exit(1)
    
    try:
        # Создаем приложение
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("test", start))
        app.add_handler(CommandHandler("check", check_command))
        
        # Callback обработчики
        app.add_handler(CallbackQueryHandler(test_buy_callback, pattern="^test_buy$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(check_status_menu, pattern="^check_status_menu$"))
        
        # Обработчик ошибок
        app.add_error_handler(error_handler)
        
        print("✅ Бот запущен!")
        print("📱 Используйте /start")
        print("=" * 60)
        
        # Запускаем с защитой от конфликтов
        app.run_polling(
            drop_pending_updates=True,  # ВАЖНО: очищаем очередь обновлений
            allowed_updates=['message', 'callback_query'],
            close_loop=False
        )
        
    except Exception as e:
        logger.critical(f"Критическая ошибка запуска: {e}")
        
        # Простой перезапуск через 10 секунд
        print(f"🔄 Перезапуск через 10 секунд...")
        time.sleep(10)
        
        # Перезапускаем процесс
        os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    main()
