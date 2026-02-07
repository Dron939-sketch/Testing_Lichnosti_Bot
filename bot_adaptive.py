#!/usr/bin/env python3
"""
Telegram Bot для тестирования платежей (1 рубль)
Версия 4.0 - тестовая оплата для проверки всей цепочки
"""

import os
import sys
import time
import json
import base64
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

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")  # 1262862
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")  # live_...

# ========== ТЕСТОВЫЕ НАСТРОЙКИ ==========
TEST_MODE = True  # Режим тестирования (1 рубль)
TEST_AMOUNT = "1.00"  # Тестовая сумма
PROD_AMOUNT = "690.00"  # Боевая сумма

# ========== ФУНКЦИИ ДЛЯ ЮKASSA API ==========
def create_yookassa_payment(payment_id: str, user_id: int, email: str = None) -> dict:
    """
    Создание платежа в ЮKassa (тестовый режим - 1 рубль)
    """
    try:
        # Используем тестовую сумму
        amount_value = TEST_AMOUNT if TEST_MODE else PROD_AMOUNT
        
        # Формируем email
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Basic Auth
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id,
            'User-Agent': 'TestBot/1.0'
        }
        
        # ПРОСТОЙ payload без receipt (чтобы избежать ошибок)
        payload = {
            "amount": {
                "value": amount_value,
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
            "description": f"Тестовая оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id),
                "test_mode": str(TEST_MODE)
            }
        }
        
        logger.info(f"🔄 Отправляю платеж {payment_id} на сумму {amount_value} руб")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Сохраняем yookassa_id в БД
            try:
                requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={
                        "payment_id": payment_id,
                        "yookassa_id": data.get('id'),
                        "status": "waiting"
                    },
                    timeout=5
                )
                logger.info(f"✅ ID сохранен в БД: {data.get('id')}")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения ID: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": data.get('id'),
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "status": data.get('status'),
                "amount": amount_value
            }
            
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            
            # Пробуем вариант без payment_method_data
            return create_yookassa_payment_simple(payment_id, user_id, amount_value)
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {
            "success": False,
            "error": str(e)[:200]
        }

def create_yookassa_payment_simple(payment_id: str, user_id: int, amount: str) -> dict:
    """
    Упрощенный запрос без payment_method_data
    """
    try:
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': f"{payment_id}_simple"
        }
        
        payload = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,
            "description": "Тестовая оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id
            }
        }
        
        logger.info(f"🔄 Пробую упрощенный запрос для {payment_id}")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "payment_id": payment_id
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка {response.status_code}: {response.text[:200]}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========== ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ==========
def create_payment_in_db(user_id: int, email: str = None) -> dict:
    """Создает платеж в базе данных"""
    try:
        timestamp = int(datetime.now().timestamp())
        payment_id = f"test_{user_id}_{timestamp}"
        
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Используем тестовую сумму
        amount = 1.00 if TEST_MODE else 690.00
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": email,
            "description": "Тестовая оплата курса ВАРИАТИКА"
        }
        
        logger.info(f"📦 Создаю платеж в БД: {payment_id} на {amount} руб")
        
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
                "email": email
            }
        else:
            logger.error(f"❌ Ошибка БД {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа в БД"""
    try:
        logger.info(f"🔍 Проверяю статус платежа: {payment_id}")
        
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            logger.info(f"📊 Статус платежа {payment_id}: {status}")
            return {
                "success": True,
                "data": data,
                "status": status
            }
        else:
            logger.error(f"❌ Ошибка проверки статуса: {response.status_code}")
            return {
                "success": False,
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"❌ Ошибка проверки статуса: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ========== TELEGRAM КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    amount_text = "1 рубль" if TEST_MODE else "690 рублей"
    description = "ТЕСТОВАЯ оплата" if TEST_MODE else "Оплата"
    
    keyboard = [
        [InlineKeyboardButton(f"💰 {description} ({amount_text})", callback_data="buy")],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data="check_status")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"🤖 **Бот для {'тестирования' if TEST_MODE else 'оплаты'} курса ВАРИАТИКА**\n\n"
        f"💳 **Сумма:** {amount_text}\n"
        f"🎯 **Цель:** Проверить всю цепочку платежей\n"
        f"📊 **Статус:** {'Тестовый режим' if TEST_MODE else 'Боевой режим'}\n\n"
        f"Нажмите кнопку для оплаты:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def quick_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая покупка"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    await query.edit_message_text("⏳ Создаю тестовый платеж...")
    
    # Создаем платеж в БД
    db_result = create_payment_in_db(user_id)
    
    if not db_result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка создания платежа:\n{db_result.get('error', 'Неизвестная ошибка')}"
        )
        return
    
    payment_id = db_result["payment_id"]
    
    # Создаем платеж в ЮKassa
    await query.edit_message_text("🔗 Генерирую ссылку для оплаты...")
    
    payment_result = create_yookassa_payment(payment_id, user_id)
    
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(
            f"❌ Ошибка платежной системы:\n{error_msg}\n\n"
            "Попробуйте позже."
        )
        return
    
    # Формируем сообщение
    amount_text = "1 рубль" if TEST_MODE else "690 рублей"
    
    keyboard = [
        [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {amount_text.upper()}", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("📋 Инструкция по оплате", callback_data="payment_help")]
    ]
    
    message_text = (
        f"✅ **Платеж создан!**\n\n"
        f"📋 ID платежа: `{payment_id}`\n"
        f"👤 Пользователь: {user.first_name}\n"
        f"💰 Сумма: {amount_text}\n"
        f"🎯 Режим: {'ТЕСТОВЫЙ (1 рубль)' if TEST_MODE else 'БОЕВОЙ'}\n\n"
        f"**Нажмите кнопку для оплаты:**\n"
        f"После оплаты нажмите 'Проверить статус'"
    )
    
    if TEST_MODE:
        message_text += "\n\n⚠️ **ТЕСТОВЫЙ РЕЖИМ**\nИспользуйте тестовые данные карты"
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса из callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 Проверяю статус платежа `{payment_id}`...")
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text(
                f"❌ Не удалось проверить статус платежа `{payment_id}`"
            )
            return
        
        status = result.get("status", "unknown")
        payment_data = result.get("data", {}).get("payment", {})
        
        if status == "succeeded":
            message = (
                f"🎉 **ОПЛАЧЕНО!**\n\n"
                f"✅ Платеж `{payment_id}` успешно завершен!\n"
                f"💰 Сумма: {payment_data.get('amount', 1)} руб\n"
                f"⏰ Время: {payment_data.get('confirmed_at', 'только что')}\n\n"
                f"**🔓 ДОСТУП ОТКРЫТ!**\n"
                f"Доступ к курсу предоставлен автоматически.\n\n"
                f"📧 Чек отправлен на email"
            )
            keyboard = []
        elif status in ["pending", "waiting"]:
            message = (
                f"⏳ **ОЖИДАЕТ ОПЛАТЫ**\n\n"
                f"Платеж `{payment_id}` еще не оплачен.\n"
                f"💰 Сумма: {payment_data.get('amount', 1)} руб\n\n"
                f"**Для оплаты:**\n"
                f"1. Используйте полученную ранее ссылку\n"
                f"2. Или создайте новый платеж\n\n"
                f"После оплаты проверьте статус снова."
            )
            keyboard = [[InlineKeyboardButton("💰 Создать новый платеж", callback_data="buy")]]
        elif status == "canceled":
            message = (
                f"❌ **ОТМЕНЕНО**\n\n"
                f"Платеж `{payment_id}` был отменен.\n\n"
                f"Для нового платежа нажмите кнопку:"
            )
            keyboard = [[InlineKeyboardButton("💰 Создать новый платеж", callback_data="buy")]]
        else:
            message = (
                f"📊 **СТАТУС ПЛАТЕЖА**\n\n"
                f"ID: `{payment_id}`\n"
                f"Статус: **{status}**\n"
                f"Сумма: {payment_data.get('amount', 1)} руб"
            )
            keyboard = []
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
            parse_mode='Markdown'
        )

async def payment_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь по оплате"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "💳 **ИНСТРУКЦИЯ ПО ТЕСТОВОЙ ОПЛАТЕ**\n\n"
        
        "**Для теста (1 рубль):**\n"
        "1. Нажмите 'Оплатить'\n"
        "2. На странице ЮKassa введите:\n"
        "   - Номер карты: `5555 5555 5555 4444`\n"
        "   - Срок: любая будущая дата\n"
        "   - CVV: `123`\n"
        "3. Подтвердите платеж\n\n"
        
        "**Что произойдет:**\n"
        "1. Банк спишет 1 рубль (тест)\n"
        "2. ЮKassa отправит нам уведомление\n"
        "3. Мы обновим статус в БД\n"
        "4. Вам откроется доступ к курсу\n\n"
        
        "**После оплаты:**\n"
        "1. Нажмите 'Проверить статус'\n"
        "2. Увидите статус 'ОПЛАЧЕНО'\n"
        "3. Получите доступ к материалам\n\n"
        
        "**Проблемы:**\n"
        "• Не приходит уведомление? Подождите 1-2 минуты\n"
        "• Ошибка платежа? Попробуйте еще раз\n"
        "• Вопросы? Пишите: @support"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к платежу", callback_data="buy")]]
    
    await query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "❓ **Помощь по тестированию**\n\n"
        "**Цель:** Проверить всю цепочку платежей\n\n"
        "**Шаги тестирования:**\n"
        "1. /start - начать тест\n"
        "2. Нажать 'ТЕСТОВАЯ оплата'\n"
        "3. Оплатить 1 рубль (тестовые данные)\n"
        "4. Проверить статус оплаты\n"
        "5. Убедиться, что доступ открылся\n\n"
        "**Тестовые данные карты:**\n"
        "• Номер: 5555 5555 5555 4444\n"
        "• Срок: любая будущая дата\n"
        "• CVV: 123\n\n"
        "**После успешного теста:**\n"
        "Мы переключимся на боевой режим (690 руб)",
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check [payment_id]"""
    if not context.args:
        await update.message.reply_text(
            "📋 **Проверка статуса платежа**\n\n"
            "Использование: `/check ID_платежа`\n\n"
            "Пример: `/check test_123456789_1234567890`\n\n"
            "ID платежа вы получаете при создании платежа.",
            parse_mode='Markdown'
        )
        return
    
    payment_id = context.args[0]
    
    await update.message.reply_text(f"🔍 Проверяю статус `{payment_id}`...")
    
    result = check_payment_status_db(payment_id)
    
    if not result["success"]:
        await update.message.reply_text(f"❌ Не удалось проверить платеж `{payment_id}`")
        return
    
    status = result.get("status", "unknown")
    payment_data = result.get("data", {}).get("payment", {})
    
    status_text = {
        "succeeded": "✅ **ОПЛАЧЕНО**",
        "pending": "⏳ **ОЖИДАЕТ ОПЛАТЫ**",
        "waiting": "⏳ **ОЖИДАЕТ ПОДТВЕРЖДЕНИЯ**",
        "canceled": "❌ **ОТМЕНЕНО**"
    }.get(status, f"📊 **{status.upper()}**")
    
    message = (
        f"📊 **СТАТУС ПЛАТЕЖА**\n\n"
        f"ID: `{payment_id}`\n"
        f"Статус: {status_text}\n"
        f"Сумма: {payment_data.get('amount', 1)} руб\n"
        f"Создан: {payment_data.get('created_at', 'неизвестно')}"
    )
    
    if status == "succeeded":
        message += f"\nОплачен: {payment_data.get('confirmed_at', 'неизвестно')}"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск тестового бота"""
    print("=" * 70)
    print("🤖 TELEGRAM БОТ ДЛЯ ТЕСТИРОВАНИЯ ПЛАТЕЖЕЙ")
    print("=" * 70)
    print(f"🎯 РЕЖИМ: {'ТЕСТОВЫЙ (1 рубль)' if TEST_MODE else 'БОЕВОЙ (690 руб)'}")
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Проверка конфигурации
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        sys.exit(1)
    
    print(f"✅ Токен бота: {'установлен' if TOKEN else 'НЕТ!'}")
    print(f"🔗 API URL: {API_URL}")
    print(f"💰 ЮKassa Shop ID: {'установлен' if YOOKASSA_SHOP_ID else 'НЕТ!'}")
    
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        print("⚠️  ВНИМАНИЕ: Данные ЮKassa неполные!")
        print("Платежи могут не работать")
    
    print("=" * 70)
    print("🔄 Запуск бота...")
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("check", check_command))
        
        # Callback обработчики
        app.add_handler(CallbackQueryHandler(quick_buy, pattern="^buy$"))
        app.add_handler(CallbackQueryHandler(check_status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(payment_help_callback, pattern="^payment_help$"))
        app.add_handler(CallbackQueryHandler(lambda u, c: help_command(u, c), pattern="^help$"))
        app.add_handler(CallbackQueryHandler(lambda u, c: start(u, c), pattern="^check_status$"))
        
        print("✅ Бот запущен успешно!")
        print("📱 Ищите бота в Telegram")
        print("💳 Для теста используйте команду /start")
        print("=" * 70)
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПУСКА: {e}")
        print("Перезапуск через 10 секунд...")
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
