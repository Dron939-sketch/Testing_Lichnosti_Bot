"""
bot.py - Telegram бот для платежной системы
Запускается как Worker Service на Render
"""

import os
import sys
import logging
import asyncio
import signal
import json
from datetime import datetime
from typing import Optional

import requests
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

# Проверка переменных окружения
def check_env():
    missing = []
    if not TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not YOOKASSA_SHOP_ID:
        missing.append("YOOKASSA_SHOP_ID")
    if not YOOKASSA_SECRET_KEY:
        missing.append("YOOKASSA_SECRET_KEY")
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные: {', '.join(missing)}")
        return False
    
    logger.info("✅ Все переменные окружения настроены")
    return True

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С API
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
            data = response.json()
            logger.info(f"✅ Платеж создан: {payment_id} для пользователя {user_id}")
            return {
                "success": True, 
                "payment_id": payment_id, 
                "data": data,
                "status": data.get("status", "pending")
            }
        else:
            logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {
            "success": False,
            "error": f"Ошибка: {str(e)}"
        }

def create_yookassa_payment(payment_id: str, user_id: int) -> dict:
    """Создает платеж в ЮKassa"""
    try:
        # Импортируем библиотеку ЮKassa
        from yookassa import Configuration, Payment
        
        # Настраиваем ЮKassa
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        
        # Создаем платеж
        payment = Payment.create({
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
                "bot": "variatica_bot"
            }
        })
        
        # Сохраняем ID ЮKassa в нашей базе
        response = requests.post(
            f"{API_URL}/api/update-yookassa-id",
            json={
                "payment_id": payment_id,
                "yookassa_id": payment.id
            },
            timeout=10
        )
        
        if response.status_code != 200:
            logger.warning(f"⚠️ Не удалось сохранить ID ЮKassa: {response.text}")
        
        # Получаем ссылку для оплаты
        confirmation_url = payment.confirmation.confirmation_url
        
        return {
            "success": True,
            "payment_id": payment_id,
            "yookassa_id": payment.id,
            "confirmation_url": confirmation_url,
            "status": payment.status
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "Библиотека 'yookassa' не установлена"
        }
    except Exception as e:
        logger.error(f"❌ Ошибка ЮKassa: {e}")
        return {
            "success": False,
            "error": f"Ошибка ЮKassa: {str(e)}"
        }

def get_payment_status(payment_id: str) -> dict:
    """Получает статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"Ошибка: {response.status_code}",
                "text": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# ТЕЛЕГРАМ ХЕНДЛЕРЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Приветственное сообщение
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "💳 Стоимость: 690 рублей\n"
        "🎁 Что входит: полный доступ ко всем материалам курса\n\n"
        "Для покупки нажмите /buy",
        parse_mode='Markdown'
    )
    logger.info(f"👤 Пользователь {user.id} ({user.first_name}) запустил бота")

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /buy"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🛒 Пользователь {user_id} ({user_name}) начал покупку")
    
    # Создаем платеж в базе данных
    msg = await update.message.reply_text("⏳ Создаю платеж в системе...")
    
    payment_result = create_payment_in_db(user_id)
    
    if not payment_result["success"]:
        await msg.edit_text(
            f"❌ Ошибка при создании платежа:\n{payment_result.get('error', 'Неизвестная ошибка')}\n\n"
            "Попробуйте позже или свяжитесь с поддержкой."
        )
        return
    
    payment_id = payment_result["payment_id"]
    
    # Создаем платеж в ЮKassa
    await msg.edit_text("🔗 Создаю ссылку для оплаты в ЮKassa...")
    
    yookassa_result = create_yookassa_payment(payment_id, user_id)
    
    if not yookassa_result["success"]:
        await msg.edit_text(
            f"❌ Ошибка при создании платежа ЮKassa:\n{yookassa_result.get('error', 'Неизвестная ошибка')}\n\n"
            f"Но платеж создан в системе с ID: `{payment_id}`\n"
            f"Попробуйте позже или свяжитесь с поддержкой.",
            parse_mode='Markdown'
        )
        return
    
    # Отправляем пользователю ссылку для оплаты
    confirmation_url = yookassa_result["confirmation_url"]
    yookassa_id = yookassa_result["yookassa_id"]
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{payment_id}")]
    ])
    
    await msg.edit_text(
        f"✅ **Платеж создан!**\n\n"
        f"📋 **Детали:**\n"
        f"• ID платежа: `{payment_id}`\n"
        f"• ID ЮKassa: `{yookassa_id}`\n"
        f"• Сумма: 690 руб.\n"
        f"• Статус: ожидание оплаты\n\n"
        f"💡 **Инструкция:**\n"
        f"1. Нажмите кнопку 'Оплатить' ниже\n"
        f"2. Оплатите на сайте ЮKassa\n"
        f"3. Вернитесь в бота и нажмите 'Проверить статус'\n"
        f"4. Доступ откроется автоматически\n\n"
        f"После оплаты нажмите 'Проверить статус' 👇",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    logger.info(f"✅ Платеж {payment_id} создан для пользователя {user_id}")

async def check_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /check"""
    await update.message.reply_text(
        "📊 **Проверка статуса платежа**\n\n"
        "Для проверки статуса:\n"
        "1. Сначала создайте платеж командой /buy\n"
        "2. Используйте кнопку 'Проверить статус' под платежом\n\n"
        "Или отправьте мне ID платежа в формате:\n"
        "`status_ваш_id_платежа`\n\n"
        "Например: `status_pay_123456_7890`",
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()  # Важно: подтверждаем получение callback
    
    data = query.data
    
    logger.info(f"🔄 Callback получен: {data} от пользователя {query.from_user.id}")
    
    # Проверка статуса
    if data.startswith("status_"):
        payment_id = data[7:]  # Убираем "status_"
        await check_payment_status(query, payment_id)
    
    # Отмена платежа
    elif data.startswith("cancel_"):
        payment_id = data[7:]  # Убираем "cancel_"
        await cancel_payment(query, payment_id)
    
    # Главное меню
    elif data == "menu":
        await start_from_callback(query)

async def check_payment_status(query, payment_id: str):
    """Проверяет и показывает статус платежа"""
    await query.edit_message_text(f"⏳ Проверяю статус платежа `{payment_id}`...")
    
    status_result = get_payment_status(payment_id)
    
    if not status_result.get("success"):
        await query.edit_message_text(
            f"❌ Не удалось проверить статус:\n{status_result.get('error', 'Неизвестная ошибка')}\n\n"
            f"ID платежа: `{payment_id}`",
            parse_mode='Markdown'
        )
        return
    
    payment = status_result.get("payment", {})
    status = payment.get("status", "unknown")
    amount = payment.get("amount", 0)
    
    # Форматируем сообщение в зависимости от статуса
    status_messages = {
        "pending": "⏳ **Ожидание оплаты**\n\nПлатеж создан, но оплата еще не поступила.",
        "waiting": "⏳ **Ожидание подтверждения**\n\nПлатеж создан в ЮKassa.",
        "succeeded": "✅ **ОПЛАЧЕНО УСПЕШНО!**\n\nДоступ к курсу открыт! 🎉",
        "canceled": "❌ **Платеж отменен**\n\nПлатеж был отменен.",
        "waiting_for_capture": "⏳ **Ожидает подтверждения**\n\nПлатеж ожидает подтверждения в ЮKassa."
    }
    
    message = status_messages.get(status, f"**Статус:** {status}")
    
    # Кнопки в зависимости от статуса
    keyboard_buttons = []
    
    if status in ["pending", "waiting", "waiting_for_capture"]:
        keyboard_buttons.append([InlineKeyboardButton("🔄 Проверить снова", callback_data=f"status_{payment_id}")])
    
    keyboard_buttons.append([InlineKeyboardButton("💳 Создать новый платеж", callback_data="new_payment")])
    keyboard_buttons.append([InlineKeyboardButton("🏠 В меню", callback_data="menu")])
    
    await query.edit_message_text(
        f"📊 **Статус платежа**\n\n"
        f"{message}\n\n"
        f"📋 **Детали:**\n"
        f"• ID: `{payment_id}`\n"
        f"• Сумма: {amount} руб.\n"
        f"• Обновлено: {payment.get('updated_at', 'неизвестно')}\n\n"
        f"💡 *Если статус 'succeeded' - доступ к курсу открыт автоматически*",
        reply_markup=InlineKeyboardMarkup(keyboard_buttons),
        parse_mode='Markdown'
    )
    
    logger.info(f"📊 Проверен статус платежа {payment_id}: {status}")

async def cancel_payment(query, payment_id: str):
    """Отмена платежа"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_cancel_{payment_id}")],
        [InlineKeyboardButton("❌ Нет, вернуться", callback_data=f"status_{payment_id}")]
    ])
    
    await query.edit_message_text(
        f"⚠️ **Отмена платежа**\n\n"
        f"Платеж `{payment_id}` будет отменен.\n\n"
        f"Это действие нельзя отменить. Подтверждаете?",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    logger.info(f"📨 Сообщение от {update.effective_user.id}: {text}")
    
    # Если пользователь отправляет ID платежа
    if text.startswith("status_"):
        payment_id = text[7:]
        
        # Создаем временное сообщение
        msg = await update.message.reply_text(f"⏳ Проверяю статус платежа `{payment_id}`...")
        
        # Проверяем статус
        status_result = get_payment_status(payment_id)
        
        if not status_result.get("success"):
            await msg.edit_text(
                f"❌ Ошибка: {status_result.get('error', 'Неизвестная ошибка')}"
            )
            return
        
        payment = status_result.get("payment", {})
        status = payment.get("status", "unknown")
        
        if status == "succeeded":
            await msg.edit_text(
                f"✅ **ОПЛАЧЕНО!**\n\n"
                f"Платеж `{payment_id}` успешно завершен.\n"
                f"Доступ к курсу открыт! 🎉\n\n"
                f"Для получения материалов напишите /start",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"📊 Статус платежа `{payment_id}`:\n\n"
                f"**{status}**\n\n"
                f"Для деталей создайте новый платеж командой /buy",
                parse_mode='Markdown'
            )
    else:
        # Если сообщение не распознано
        await update.message.reply_text(
            "🤔 Я не понял ваше сообщение.\n\n"
            "Доступные команды:\n"
            "/start - начать работу\n"
            "/buy - купить доступ (690 руб)\n"
            "/check - как проверить статус\n\n"
            "Или отправьте ID платежа в формате:\n"
            "`status_ваш_id_платежа`",
            parse_mode='Markdown'
        )

async def start_from_callback(query):
    """Старт из callback"""
    user = query.from_user
    
    await query.edit_message_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "💳 Стоимость: 690 рублей\n"
        "🎁 Что входит: полный доступ ко всем материалам курса\n\n"
        "Для покупки нажмите кнопку ниже:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Купить доступ", callback_data="new_payment")],
            [InlineKeyboardButton("📊 Мои платежи", callback_data="my_payments")]
        ])
    )

async def new_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание нового платежа из callback"""
    query = update.callback_query
    await query.answer()
    await buy_command_from_callback(query)

async def buy_command_from_callback(query):
    """Команда /buy из callback"""
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"🛒 Callback: пользователь {user_id} начал покупку")
    
    await query.edit_message_text("⏳ Создаю платеж в системе...")
    
    payment_result = create_payment_in_db(user_id)
    
    if not payment_result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка при создании платежа:\n{payment_result.get('error', 'Неизвестная ошибка')}\n\n"
            "Попробуйте позже или свяжитесь с поддержкой."
        )
        return
    
    payment_id = payment_result["payment_id"]
    
    await query.edit_message_text("🔗 Создаю ссылку для оплаты в ЮKassa...")
    
    yookassa_result = create_yookassa_payment(payment_id, user_id)
    
    if not yookassa_result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка при создании платежа ЮKassa:\n{yookassa_result.get('error', 'Неизвестная ошибка')}\n\n"
            f"Но платеж создан в системе с ID: `{payment_id}`\n"
            f"Попробуйте позже или свяжитесь с поддержкой.",
            parse_mode='Markdown'
        )
        return
    
    confirmation_url = yookassa_result["confirmation_url"]
    yookassa_id = yookassa_result["yookassa_id"]
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
    ])
    
    await query.edit_message_text(
        f"✅ **Платеж создан!**\n\n"
        f"📋 **Детали:**\n"
        f"• ID платежа: `{payment_id}`\n"
        f"• ID ЮKassa: `{yookassa_id}`\n"
        f"• Сумма: 690 руб.\n"
        f"• Статус: ожидание оплаты\n\n"
        f"💡 **Нажмите кнопку ниже для оплаты:**",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ============================================
# ИНИЦИАЛИЗАЦИЯ И ЗАПУСК
# ============================================

async def post_init(application: Application):
    """Выполняется после инициализации бота"""
    bot_info = await application.bot.get_me()
    
    print("="*60)
    print(f"🤖 Бот запущен: @{bot_info.username}")
    print(f"👤 Имя: {bot_info.first_name}")
    print(f"🆔 ID: {bot_info.id}")
    print(f"🌐 API URL: {API_URL}")
    print("="*60)
    
    # Проверяем API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"📡 API статус: {response.status_code}")
        if response.status_code == 200:
            print("✅ API доступен")
        else:
            print(f"⚠️ API недоступен: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
    
    print("="*60)
    print("📱 Бот готов к работе!")
    print("Попробуйте команды:")
    print("  /start - начать работу")
    print("  /buy - создать платеж")
    print("  /check - как проверить статус")
    print("="*60)

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print(f"\n⚠️ Получен сигнал {signum}. Завершение бота...")
    sys.exit(0)

def main():
    """Запуск бота"""
    print("="*60)
    print("🚀 ЗАПУСК ПЛАТЕЖНОГО БОТА")
    print("="*60)
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Проверяем переменные окружения
    if not check_env():
        print("❌ Ошибка: не все переменные окружения установлены")
        print("Установите в Render:")
        print("1. TELEGRAM_BOT_TOKEN")
        print("2. YOOKASSA_SHOP_ID")
        print("3. YOOKASSA_SECRET_KEY")
        print("4. API_URL (опционально)")
        return
    
    try:
        # Создаем приложение
        application = Application.builder().token(TOKEN).post_init(post_init).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("buy", buy_command))
        application.add_handler(CommandHandler("check", check_status_command))
        application.add_handler(CommandHandler("status", check_status_command))
        
        # Обработчики callback кнопок
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^status_"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^cancel_"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^confirm_cancel_"))
        application.add_handler(CallbackQueryHandler(new_payment_callback, pattern="^new_payment$"))
        application.add_handler(CallbackQueryHandler(start_from_callback, pattern="^menu$"))
        application.add_handler(CallbackQueryHandler(start_from_callback, pattern="^my_payments$"))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Бот инициализирован")
        print("⏳ Запускаю polling...")
        
        # Запускаем бота
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()
