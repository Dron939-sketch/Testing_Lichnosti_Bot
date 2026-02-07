"""
🚀 ПЛАТЕЖНЫЙ БОТ С ИНТЕГРАЦИЕЙ ЮKASSA
Только платежи, без лишнего функционала
"""

import os
import logging
import uuid
import json
from datetime import datetime

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
API_URL = "https://testing-lichnosti-bot-1.onrender.com"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Проверка переменных окружения
def check_env():
    """Проверяем наличие всех необходимых переменных"""
    missing = []
    
    if not TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not YOOKASSA_SHOP_ID:
        missing.append("YOOKASSA_SHOP_ID")
    if not YOOKASSA_SECRET_KEY:
        missing.append("YOOKASSA_SECRET_KEY")
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
        return False
    
    logger.info("✅ Все переменные окружения настроены")
    return True

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С API БАЗЫ ДАННЫХ
# ============================================

def create_payment_in_db(user_id: int, amount: float = 690.0) -> dict:
    """
    Создает платеж в базе данных
    Возвращает: {'success': bool, 'payment_id': str, 'error': str}
    """
    try:
        # Генерируем уникальный ID платежа
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
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            logger.info(f"✅ Платеж создан: {payment_id} для пользователя {user_id}")
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "pending",
                "data": data
            }
        else:
            logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": response.text
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка сети: {e}")
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return {
            "success": False,
            "error": f"Внутренняя ошибка: {str(e)}"
        }

def get_payment_status(payment_id: str) -> dict:
    """Получает статус платежа из базы данных"""
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
                "error": f"Статус {response.status_code}",
                "text": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ЮKASSA
# ============================================

def create_yookassa_payment(payment_id: str, amount: float = 690.0, user_id: int = None) -> dict:
    """
    Создает платеж в ЮKassa
    Возвращает ссылку для оплаты
    """
    try:
        # Используем официальную библиотеку yookassa
        from yookassa import Configuration, Payment
        
        # Настраиваем ЮKassa
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        
        # Создаем платеж
        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"  # Вернуться в бота после оплаты
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
        yookassa_response = requests.post(
            f"{API_URL}/api/update-yookassa-id",
            json={
                "payment_id": payment_id,
                "yookassa_id": payment.id
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if yookassa_response.status_code != 200:
            logger.warning(f"⚠️ Не удалось сохранить ID ЮKassa: {yookassa_response.text}")
        
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
        # Если библиотека yookassa не установлена
        logger.error("❌ Библиотека 'yookassa' не установлена")
        return {
            "success": False,
            "error": "Библиотека ЮKassa не установлена. Установите: pip install yookassa"
        }
    except Exception as e:
        logger.error(f"❌ Ошибка ЮKassa: {e}")
        return {
            "success": False,
            "error": f"Ошибка ЮKassa: {str(e)}"
        }

# ============================================
# ТЕЛЕГРАМ ХЕНДЛЕРЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главная команда бота"""
    user = update.effective_user
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "💳 Стоимость: 690 рублей\n"
        "🎁 Что входит: полный доступ к материалам\n\n"
        "Для покупки нажмите /buy",
        parse_mode='Markdown'
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда покупки"""
    user_id = update.effective_user.id
    
    # Создаем платеж в базе данных
    await update.message.reply_text("⏳ Создаю платеж в системе...")
    
    payment_result = create_payment_in_db(user_id)
    
    if not payment_result["success"]:
        await update.message.reply_text(
            f"❌ Ошибка при создании платежа:\n{payment_result.get('error', 'Неизвестная ошибка')}"
        )
        return
    
    payment_id = payment_result["payment_id"]
    
    # Создаем платеж в ЮKassa
    await update.message.reply_text("🔗 Создаю ссылку для оплаты...")
    
    yookassa_result = create_yookassa_payment(
        payment_id=payment_id,
        amount=690.0,
        user_id=user_id
    )
    
    if not yookassa_result["success"]:
        await update.message.reply_text(
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
        [InlineKeyboardButton("❌ Отменить платеж", callback_data=f"cancel_{payment_id}")]
    ])
    
    await update.message.reply_text(
        f"✅ Платеж создан!\n\n"
        f"📋 **Детали платежа:**\n"
        f"• ID: `{payment_id}`\n"
        f"• ЮKassa ID: `{yookassa_id}`\n"
        f"• Сумма: 690 руб.\n"
        f"• Статус: ожидание оплаты\n\n"
        f"💡 **Инструкция:**\n"
        f"1. Нажмите кнопку 'Оплатить' ниже\n"
        f"2. Оплатите на сайте ЮKassa\n"
        f"3. Вернитесь в бота и проверьте статус\n"
        f"4. Доступ откроется автоматически\n\n"
        f"После оплаты нажмите 'Проверить статус'",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа (команда)"""
    await update.message.reply_text(
        "📊 Для проверки статуса:\n"
        "1. Нажмите /buy и создайте платеж\n"
        "2. Используйте кнопку 'Проверить статус'\n\n"
        "Или отправьте мне ID платежа в формате:\n"
        "`status_ваш_id_платежа`",
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Проверка статуса
    if data.startswith("status_"):
        payment_id = data[7:]  # Убираем "status_"
        await check_payment_status(query, payment_id)
    
    # Отмена платежа
    elif data.startswith("cancel_"):
        payment_id = data[7:]  # Убираем "cancel_"
        await cancel_payment(query, payment_id)
    
    # Меню
    elif data == "menu":
        await start(update, context)

async def check_payment_status(query, payment_id: str):
    """Проверяет и показывает статус платежа"""
    await query.edit_message_text("⏳ Проверяю статус платежа...")
    
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
        "pending": "⏳ Ожидание оплаты",
        "processing": "🔄 Обработка платежа",
        "succeeded": "✅ Оплачено успешно!",
        "canceled": "❌ Платеж отменен",
        "waiting_for_capture": "⏳ Ожидает подтверждения"
    }
    
    message = status_messages.get(status, f"Статус: {status}")
    
    # Кнопки в зависимости от статуса
    keyboard_buttons = []
    
    if status == "pending":
        keyboard_buttons.append([InlineKeyboardButton("🔄 Проверить снова", callback_data=f"status_{payment_id}")])
    
    keyboard_buttons.append([InlineKeyboardButton("🏠 В меню", callback_data="menu")])
    
    await query.edit_message_text(
        f"📊 **Статус платежа**\n\n"
        f"• ID: `{payment_id}`\n"
        f"• Статус: {message}\n"
        f"• Сумма: {amount} руб.\n"
        f"• Обновлено: {payment.get('updated_at', 'неизвестно')}\n\n"
        f"💡 *Если статус 'succeeded' - доступ к курсу открыт автоматически*",
        reply_markup=InlineKeyboardMarkup(keyboard_buttons) if keyboard_buttons else None,
        parse_mode='Markdown'
    )

async def cancel_payment(query, payment_id: str):
    """Отмена платежа"""
    await query.edit_message_text(
        f"⚠️ **Отмена платежа**\n\n"
        f"Платеж `{payment_id}` будет отменен.\n\n"
        f"Это необратимое действие. Подтвердите?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_cancel_{payment_id}")],
            [InlineKeyboardButton("❌ Нет, вернуться", callback_data=f"status_{payment_id}")]
        ]),
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    # Если пользователь отправляет ID платежа
    if text.startswith("status_"):
        payment_id = text[7:]
        await check_payment_status_simple(update, payment_id)
    else:
        await update.message.reply_text(
            "Я понимаю команды:\n"
            "/start - начать работу\n"
            "/buy - купить доступ\n"
            "/check - проверить статус\n\n"
            "Или отправьте ID платежа в формате:\n"
            "`status_ваш_id_платежа`",
            parse_mode='Markdown'
        )

async def check_payment_status_simple(update: Update, payment_id: str):
    """Простая проверка статуса из сообщения"""
    await update.message.reply_text(f"⏳ Проверяю статус платежа `{payment_id}`...")
    
    status_result = get_payment_status(payment_id)
    
    if not status_result.get("success"):
        await update.message.reply_text(
            f"❌ Ошибка: {status_result.get('error', 'Неизвестная ошибка')}"
        )
        return
    
    payment = status_result.get("payment", {})
    status = payment.get("status", "unknown")
    
    status_messages = {
        "pending": "⏳ Ожидание оплаты",
        "succeeded": "✅ **ОПЛАЧЕНО!** Доступ открыт!",
        "canceled": "❌ Платеж отменен"
    }
    
    message = status_messages.get(status, f"Статус: {status}")
    
    await update.message.reply_text(
        f"Статус платежа `{payment_id}`:\n\n"
        f"{message}\n\n"
        f"Для деталей нажмите /buy и используйте кнопки",
        parse_mode='Markdown'
    )

# ============================================
# ЗАПУСК БОТА
# ============================================

def main():
    """Запуск бота"""
    print("="*60)
    print("🚀 ПЛАТЕЖНЫЙ БОТ С ЮKASSA")
    print("="*60)
    
    # Проверяем переменные окружения
    if not check_env():
        print("❌ Ошибка: не все переменные окружения установлены")
        print("Установите в Render:")
        print("1. TELEGRAM_BOT_TOKEN")
        print("2. YOOKASSA_SHOP_ID")
        print("3. YOOKASSA_SECRET_KEY")
        return
    
    print(f"API URL: {API_URL}")
    print(f"Bot Token: {TOKEN[:10]}...")
    print(f"ЮKassa Shop ID: {YOOKASSA_SHOP_ID[:10]}...")
    print("="*60)
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("check", check_status))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен и готов к работе!")
    print("💳 Доступные команды:")
    print("  /start - начать работу")
    print("  /buy - создать платеж (690 руб)")
    print("  /check - проверить статус")
    print("="*60)
    
    # Запускаем бота
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
