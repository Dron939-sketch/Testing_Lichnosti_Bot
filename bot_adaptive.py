#!/usr/bin/env python3
"""
Telegram Bot для боевого режима ЮKassa
Версия 3.0 - с поддержкой receipt и фискализацией
"""

import os
import sys
import time
import json
import base64
import logging
import requests
import urllib.parse
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
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
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")  # Боевой Shop ID
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")  # Боевой Secret Key

# ========== ВАЛИДАЦИЯ КОНФИГУРАЦИИ ==========
def validate_config():
    """Проверяем настройки для боевого режима"""
    errors = []
    
    if not TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установлен")
    
    if not YOOKASSA_SHOP_ID:
        errors.append("❌ YOOKASSA_SHOP_ID не установлен")
    elif not str(YOOKASSA_SHOP_ID).startswith(('126', '127', '128')):
        logger.warning(f"⚠️  Shop ID '{YOOKASSA_SHOP_ID}' не похож на боевой (должен начинаться с 126, 127, 128)")
    
    if not YOOKASSA_SECRET_KEY:
        errors.append("❌ YOOKASSA_SECRET_KEY не установлен")
    elif not YOOKASSA_SECRET_KEY.startswith('live_'):
        logger.warning(f"⚠️  Secret Key не начинается с 'live_' - возможно это тестовый ключ")
    
    if errors:
        logger.error("\n".join(errors))
        return False
    
    return True

# ========== ФУНКЦИИ ДЛЯ ЮKASSA API ==========
def create_yookassa_payment_battle(payment_id: str, user_id: int, user_email: str = None) -> dict:
    """
    Создание платежа в БОЕВОМ режиме ЮKassa с receipt
    """
    try:
        # Формируем email
        if not user_email:
            user_email = f"user_{user_id}@telegram.org"
        
        # Подготавливаем заголовки
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id,
            'User-Agent': 'VariaticaBot/1.0'
        }
        
        # Формируем payload для боевого режима
        payload = {
            "amount": {
                "value": "690.00",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/variatica_bot?start=payment_{payment_id}"
            },
            "capture": True,
            "description": f"Оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_user_id": str(user_id),
                "product": "variatica_full_course"
            },
            # ВАЖНО: receipt для 54-ФЗ
            "receipt": {
                "customer": {
                    "email": user_email
                },
                "items": [
                    {
                        "description": "Полный пакет курса ВАРИАТИКА (электронный товар)",
                        "quantity": "1.00",
                        "amount": {
                            "value": "690.00",
                            "currency": "RUB"
                        },
                        "vat_code": 1,  # НДС 20%
                        "payment_subject": "service",  # Услуга
                        "payment_mode": "full_payment",
                        "product_code": "variatica_course_001"
                    }
                ]
            }
        }
        
        logger.info(f"Отправляем запрос в ЮKassa для платежа {payment_id}")
        
        # Отправляем запрос
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"Ответ ЮKassa: {response.status_code}")
        
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
            except Exception as e:
                logger.error(f"Ошибка сохранения yookassa_id: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": data.get('id'),
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "status": data.get('status'),
                "method": "yookassa_battle"
            }
            
        else:
            error_text = response.text[:500]
            logger.error(f"Ошибка ЮKassa {response.status_code}: {error_text}")
            
            # Пробуем альтернативный метод без receipt (если включена настройка)
            if "receipt" in error_text.lower():
                logger.info("Пробуем создать платеж без receipt...")
                return create_yookassa_payment_no_receipt(payment_id, user_id)
            
            return {
                "success": False,
                "error": f"ЮKassa error {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return {
            "success": False,
            "error": str(e)[:200]
        }

def create_yookassa_payment_no_receipt(payment_id: str, user_id: int) -> dict:
    """
    Альтернативный метод без receipt (если магазин настроен)
    """
    try:
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': f"{payment_id}_noreceipt"
        }
        
        payload = {
            "amount": {
                "value": "690.00",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/variatica_bot"
            },
            "capture": True,
            "description": f"Оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id
            }
            # НЕТ receipt!
        }
        
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
                "payment_id": payment_id,
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "method": "yookassa_no_receipt"
            }
        else:
            return {
                "success": False,
                "error": f"Fallback error: {response.status_code}"
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
        payment_id = f"pay_{user_id}_{timestamp}"
        
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 690.00,
            "email": email,
            "description": "Полный пакет ВАРИАТИКА"
        }
        
        logger.info(f"Создаем платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            return {
                "success": True,
                "payment_id": payment_id,
                "email": email
            }
        else:
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
    """Проверяет статус платежа в БД"""
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
        [InlineKeyboardButton("💰 Купить доступ (690 руб)", callback_data="buy")],
        [InlineKeyboardButton("📧 Ввести email", callback_data="enter_email")]
    ]
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "🎓 **Что вы получите:**\n"
        "• Полный доступ к курсу\n"
        "• Все материалы и обновления\n"
        "• Поддержку 24/7\n\n"
        "💳 **Стоимость:** 690 рублей\n"
        "⏱ **Доступ:** Навсегда\n\n"
        "Нажмите кнопку для оплаты:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy"""
    user = update.effective_user
    
    # Шаг 1: Запрашиваем email
    await update.message.reply_text(
        "📧 **Для оформления платежа нужен ваш email**\n\n"
        "Это необходимо для:\n"
        "1. Отправки чека (по закону 54-ФЗ)\n"
        "2. Доступа к курсу\n\n"
        "Пожалуйста, введите ваш email:",
        parse_mode='Markdown'
    )
    
    # Сохраняем состояние для следующего шага
    context.user_data['awaiting_email'] = True
    context.user_data['user_id'] = user.id

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений (для email)"""
    if context.user_data.get('awaiting_email'):
        email = update.message.text.strip()
        
        # Простая валидация email
        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ Пожалуйста, введите корректный email.\n"
                "Пример: ivanov@gmail.com"
            )
            return
        
        user_id = context.user_data['user_id']
        
        # Создаем платеж в БД
        await update.message.reply_text("⏳ Создаю платеж...")
        
        db_result = create_payment_in_db(user_id, email)
        
        if not db_result["success"]:
            await update.message.reply_text(
                "❌ Ошибка создания платежа. Попробуйте позже."
            )
            context.user_data.clear()
            return
        
        payment_id = db_result["payment_id"]
        
        # Создаем платеж в ЮKassa
        await update.message.reply_text("🔗 Создаю ссылку для оплаты...")
        
        payment_result = create_yookassa_payment_battle(payment_id, user_id, email)
        
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await update.message.reply_text(
                f"❌ Ошибка платежной системы:\n{error_msg}\n\n"
                "Попробуйте позже или обратитесь в поддержку."
            )
            context.user_data.clear()
            return
        
        # Показываем кнопку оплаты
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=payment_result["confirmation_url"])],
            [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")]
        ]
        
        await update.message.reply_text(
            f"✅ **Платеж готов!**\n\n"
            f"📧 Email: {email}\n"
            f"📋 ID: `{payment_id}`\n"
            f"💰 Сумма: 690 рублей\n\n"
            f"**Нажмите кнопку для оплаты:**\n"
            f"После оплаты чек придет на указанный email.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        context.user_data.clear()

async def quick_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая покупка (без email - будет запрос)"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    await query.edit_message_text(
        f"📧 **{user.first_name}, для оплаты нужен ваш email**\n\n"
        "Введите ваш email для получения чека:",
        parse_mode='Markdown'
    )
    
    # Устанавливаем состояние в контексте
    context.user_data['awaiting_email'] = True
    context.user_data['user_id'] = user.id
    context.user_data['message_id'] = query.message.message_id

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса из callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text("❌ Не удалось проверить статус")
            return
        
        payment_data = result["data"].get("payment", {})
        status = payment_data.get("status", "unknown")
        
        if status == "succeeded":
            message = (
                "🎉 **ОПЛАЧЕНО!**\n\n"
                "✅ Платеж успешно завершен!\n"
                "📧 Чек отправлен на ваш email\n"
                "🔓 Доступ к курсу открыт!\n\n"
                "Ожидайте письмо с инструкциями."
            )
        else:
            message = (
                f"⏳ **Статус: {status.upper()}**\n\n"
                f"Платеж еще не завершен.\n\n"
                f"ID: `{payment_id}`\n"
                f"Для оплаты нажмите кнопку:"
            )
            keyboard = [[InlineKeyboardButton("💳 Оплатить", callback_data="buy")]]
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        await query.edit_message_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "❓ **Помощь**\n\n"
        "**Как оплатить:**\n"
        "1. Нажмите /buy\n"
        "2. Введите ваш email\n"
        "3. Нажмите кнопку оплаты\n"
        "4. Завершите платеж на сайте ЮKassa\n\n"
        "**После оплаты:**\n"
        "• Чек придет на email\n"
        "• Доступ откроется автоматически\n"
        "• Проверить статус: /check ID_платежа\n\n"
        "**Поддержка:**\n"
        "По вопросам оплаты: support@variatica.ru\n"
        "Технические проблемы: @tech_support",
        parse_mode='Markdown'
    )

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота для боевого режима"""
    print("=" * 60)
    print("🚀 TELEGRAM БОТ ДЛЯ БОЕВОГО РЕЖИМА")
    print("=" * 60)
    
    # Проверяем конфигурацию
    if not validate_config():
        print("❌ Конфигурация не прошла проверку")
        print("Проверьте переменные окружения в Render")
        sys.exit(1)
    
    print("✅ Конфигурация проверена успешно")
    print(f"⏰ Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Создаем приложение
        from telegram.ext import MessageHandler, filters
        
        app = Application.builder().token(TOKEN).build()
        
        # Команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", buy_command))
        app.add_handler(CommandHandler("help", help_command))
        
        # Обработчик сообщений (для email)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Callback обработчики
        app.add_handler(CallbackQueryHandler(quick_buy_callback, pattern="^buy$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        
        # Команда проверки статуса
        async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if context.args:
                payment_id = context.args[0]
                result = check_payment_status_db(payment_id)
                
                if result["success"]:
                    status = result["data"].get("payment", {}).get("status", "unknown")
                    await update.message.reply_text(f"Статус платежа `{payment_id}`: **{status}**", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"Не удалось проверить платеж `{payment_id}`", parse_mode='Markdown')
            else:
                await update.message.reply_text("Использование: `/check ID_платежа`", parse_mode='Markdown')
        
        app.add_handler(CommandHandler("check", check_command))
        
        # Запускаем бота
        print("🤖 Бот запускается...")
        print("📱 Найдите бота в Telegram и начните с /start")
        print("=" * 60)
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        time.sleep(10)
        main()  # Перезапуск

if __name__ == "__main__":
    main()
