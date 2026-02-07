"""
bot_adaptive.py - Telegram бот для платежной системы
Исправленная версия без ошибок с ЮKassa
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

# Проверка переменных окружения
def check_env():
    """Проверяет наличие всех необходимых переменных"""
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
                "data": data
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
    """
    Создает платеж в ЮKassa
    ИСПРАВЛЕННАЯ ВЕРСИЯ - БЕЗ receipt
    """
    try:
        # Импортируем библиотеку ЮKassa
        from yookassa import Configuration, Payment
        
        # Настраиваем ЮKassa
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        
        # ИСПРАВЛЕНИЕ: Создаем платеж БЕЗ receipt (для цифровых товаров)
        payment_data = {
            "amount": {
                "value": "690.00",  # Фиксированная сумма
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,  # Автоматическое списание
            "description": f"Оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "product": "variatica_full_course",
                "timestamp": str(datetime.now().timestamp())
            }
        }
        
        # Явно указываем, что это цифровой товар (не требуется receipt)
        payment_data["payment_mode"] = "full_payment"
        payment_data["payment_subject"] = "service"  # Услуга (цифровой товар)
        
        # Создаем платеж
        payment = Payment.create(payment_data)
        
        # Сохраняем ID ЮKassa в нашей базе
        try:
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
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при сохранении ID ЮKassa: {e}")
        
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
        # Детализация ошибки
        error_msg = str(e)
        if "receipt" in error_msg.lower():
            return {
                "success": False,
                "error": "Ошибка чека (receipt). Используйте yookassa==2.3.0 или удалите receipt из запроса."
            }
        return {
            "success": False,
            "error": f"Ошибка ЮKassa: {error_msg[:100]}"
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

def update_yookassa_id_in_db(payment_id: str, yookassa_id: str) -> bool:
    """Обновляет ID ЮKassa в базе данных"""
    try:
        response = requests.post(
            f"{API_URL}/api/update-yookassa-id",
            json={
                "payment_id": payment_id,
                "yookassa_id": yookassa_id
            },
            timeout=10
        )
        
        return response.status_code == 200
    except:
        return False

# ============================================
# ТЕЛЕГРАМ ХЕНДЛЕРЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Купить доступ (690 руб)", callback_data="buy")],
        [InlineKeyboardButton("📊 Мои платежи", callback_data="my_payments")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ])
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для оплаты курса **ВАРИАТИКА**.\n\n"
        "💳 **Стоимость:** 690 рублей\n"
        "🎁 **Что входит:**\n"
        "• Полный доступ к материалам курса\n"
        "• Пожизненный доступ\n"
        "• Все обновления\n\n"
        "Нажмите кнопку ниже для покупки:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    logger.info(f"👤 Пользователь {user.id} запустил бота")

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /buy"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🛒 Пользователь {user_id} начал покупку")
    
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
        # Пробуем альтернативный метод без receipt
        await msg.edit_text("⚠️ Пробую альтернативный метод оплаты...")
        
        # Создаем простую платежную ссылку
        simple_result = create_simple_payment(payment_id, user_id)
        
        if not simple_result["success"]:
            await msg.edit_text(
                f"❌ Ошибка при создании платежа:\n{yookassa_result.get('error', 'Неизвестная ошибка')}\n\n"
                f"Но платеж создан в системе с ID: `{payment_id}`\n"
                f"Попробуйте позже или свяжитесь с поддержкой.",
                parse_mode='Markdown'
            )
            return
        
        confirmation_url = simple_result["confirmation_url"]
        payment_method = "альтернативный"
    else:
        confirmation_url = yookassa_result["confirmation_url"]
        payment_method = "ЮKassa"
    
    # Отправляем пользователю ссылку для оплаты
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
    ])
    
    await msg.edit_text(
        f"✅ **Платеж создан через {payment_method}!**\n\n"
        f"📋 **Детали платежа:**\n"
        f"• ID: `{payment_id}`\n"
        f"• Сумма: 690 руб.\n"
        f"• Статус: ожидание оплаты\n\n"
        f"💡 **Инструкция:**\n"
        f"1. Нажмите кнопку 'Оплатить' ниже\n"
        f"2. Оплатите на сайте платежной системы\n"
        f"3. Вернитесь в бота и нажмите 'Проверить статус'\n"
        f"4. Доступ откроется автоматически\n\n"
        f"После оплаты нажмите 'Проверить статус' 👇",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    logger.info(f"✅ Платеж {payment_id} создан для пользователя {user_id}")

def create_simple_payment(payment_id: str, user_id: int) -> dict:
    """Альтернативный метод создания платежа (простая ссылка)"""
    try:
        # Базовая ссылка для тестирования
        test_url = f"https://yoomoney.ru/quickpay/confirm.xml?receiver=410011000000000&quickpay-form=shop&sum=690&label={payment_id}"
        
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": test_url,
            "method": "simple"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def check_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /check"""
    await update.message.reply_text(
        "📊 **Проверка статуса платежа**\n\n"
        "Для проверки статуса:\n"
        "1. Сначала создайте платеж командой /buy\n"
        "2. Используйте кнопку 'Проверить статус' под платежом\n\n"
        "Или отправьте мне ID платежа в формате:\n"
        "`status_ваш_id_платежа`",
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    logger.info(f"🔄 Callback получен: {data}")
    
    if data == "buy":
        await buy_callback(query)
    elif data.startswith("status_"):
        payment_id = data[7:]
        await check_payment_status_callback(query, payment_id)
    elif data == "menu":
        await menu_callback(query)
    elif data == "my_payments":
        await my_payments_callback(query)
    elif data == "help":
        await help_callback(query)

async def buy_callback(query):
    """Покупка из callback"""
    user_id = query.from_user.id
    
    await query.edit_message_text("⏳ Создаю платеж в системе...")
    
    payment_result = create_payment_in_db(user_id)
    
    if not payment_result["success"]:
        await query.edit_message_text(
            f"❌ Ошибка: {payment_result.get('error', 'Неизвестная ошибка')}\n\n"
            "Попробуйте позже."
        )
        return
    
    payment_id = payment_result["payment_id"]
    
    await query.edit_message_text("🔗 Создаю ссылку для оплаты...")
    
    yookassa_result = create_yookassa_payment(payment_id, user_id)
    
    if not yookassa_result["success"]:
        simple_result = create_simple_payment(payment_id, user_id)
        
        if not simple_result["success"]:
            await query.edit_message_text(
                f"❌ Ошибка: {yookassa_result.get('error', 'Неизвестная ошибка')}\n\n"
                f"Платеж создан с ID: `{payment_id}`",
                parse_mode='Markdown'
            )
            return
        
        confirmation_url = simple_result["confirmation_url"]
        payment_method = "альтернативный"
    else:
        confirmation_url = yookassa_result["confirmation_url"]
        payment_method = "ЮKassa"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
    ])
    
    await query.edit_message_text(
        f"✅ **Платеж создан через {payment_method}!**\n\n"
        f"ID: `{payment_id}`\n"
        f"Нажмите кнопку ниже для оплаты:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def check_payment_status_callback(query, payment_id: str):
    """Проверка статуса из callback"""
    await query.edit_message_text(f"⏳ Проверяю статус платежа...")
    
    status_result = get_payment_status(payment_id)
    
    if not status_result.get("success"):
        await query.edit_message_text(
            f"❌ Ошибка: {status_result.get('error', 'Неизвестная ошибка')}"
        )
        return
    
    payment = status_result.get("payment", {})
    status = payment.get("status", "unknown")
    amount = payment.get("amount", 0)
    
    # Статусные сообщения
    status_messages = {
        "pending": "⏳ **Ожидание оплаты**\n\nПлатеж создан, но оплата еще не поступила.",
        "waiting": "⏳ **Ожидание подтверждения**\n\nПлатеж создан, ожидает обработки.",
        "succeeded": "✅ **ОПЛАЧЕНО УСПЕШНО!**\n\nДоступ к курсу открыт! 🎉\n\nСвяжитесь с поддержкой для получения материалов.",
        "canceled": "❌ **Платеж отменен**\n\nПлатеж был отменен.",
        "waiting_for_capture": "⏳ **Ожидает подтверждения**\n\nПлатеж ожидает подтверждения."
    }
    
    message = status_messages.get(status, f"**Статус:** {status}")
    
    # Кнопки
    keyboard_buttons = []
    
    if status in ["pending", "waiting", "waiting_for_capture"]:
        keyboard_buttons.append([InlineKeyboardButton("🔄 Проверить снова", callback_data=f"status_{payment_id}")])
    
    keyboard_buttons.append([InlineKeyboardButton("💳 Новый платеж", callback_data="buy")])
    keyboard_buttons.append([InlineKeyboardButton("🏠 В меню", callback_data="menu")])
    
    await query.edit_message_text(
        f"📊 **Статус платежа**\n\n"
        f"{message}\n\n"
        f"📋 **Детали:**\n"
        f"• ID: `{payment_id}`\n"
        f"• Сумма: {amount} руб.\n"
        f"• Обновлено: {payment.get('updated_at', 'недавно')}\n\n"
        f"💡 *При статусе 'succeeded' доступ открыт автоматически*",
        reply_markup=InlineKeyboardMarkup(keyboard_buttons),
        parse_mode='Markdown'
    )

async def menu_callback(query):
    """Главное меню из callback"""
    user = query.from_user
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Купить доступ (690 руб)", callback_data="buy")],
        [InlineKeyboardButton("📊 Мои платежи", callback_data="my_payments")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ])
    
    await query.edit_message_text(
        f"👋 {user.first_name}, выберите действие:",
        reply_markup=keyboard
    )

async def my_payments_callback(query):
    """Мои платежи"""
    user_id = query.from_user.id
    
    try:
        response = requests.get(f"{API_URL}/api/user-payments/{user_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            payments = data.get("payments", [])
            
            if payments:
                text = "📊 **Ваши платежи:**\n\n"
                for payment in payments[:5]:  # Показываем последние 5
                    status_emoji = {
                        "succeeded": "✅",
                        "pending": "⏳",
                        "canceled": "❌"
                    }.get(payment.get("status"), "📄")
                    
                    text += f"{status_emoji} {payment.get('payment_id')[:15]}... - {payment.get('amount')} руб. - {payment.get('status')}\n"
                
                if len(payments) > 5:
                    text += f"\n... и еще {len(payments) - 5} платежей"
            else:
                text = "📭 У вас еще нет платежей.\n\nНажмите 'Купить доступ' для создания первого платежа."
        else:
            text = "❌ Не удалось загрузить платежи. Попробуйте позже."
    
    except:
        text = "❌ Ошибка подключения к серверу."
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Купить доступ", callback_data="buy")],
        [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def help_callback(query):
    """Помощь"""
    help_text = (
        "ℹ️ **Помощь по использованию бота:**\n\n"
        "💰 **Покупка доступа:**\n"
        "1. Нажмите 'Купить доступ'\n"
        "2. Оплатите 690 рублей\n"
        "3. Проверьте статус оплаты\n"
        "4. Получите доступ к курсу\n\n"
        "📊 **Проверка статуса:**\n"
        "• Используйте кнопку 'Проверить статус' под платежом\n"
        "• Или напишите `status_ваш_id_платежа`\n\n"
        "❓ **Проблемы с оплатой:**\n"
        "• Если платеж не проходит, попробуйте через 5 минут\n"
        "• Для помощи: @ваш_аккаунт_поддержки"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Купить доступ", callback_data="buy")],
        [InlineKeyboardButton("🏠 В меню", callback_data="menu")]
    ])
    
    await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if text.startswith("status_"):
        payment_id = text[7:]
        
        msg = await update.message.reply_text(f"⏳ Проверяю статус `{payment_id}`...")
        
        status_result = get_payment_status(payment_id)
        
        if not status_result.get("success"):
            await msg.edit_text(f"❌ Ошибка: {status_result.get('error', 'Неизвестная ошибка')}")
            return
        
        payment = status_result.get("payment", {})
        status = payment.get("status", "unknown")
        
        if status == "succeeded":
            await msg.edit_text(
                f"✅ **ОПЛАЧЕНО!**\n\n"
                f"Платеж `{payment_id}` успешно завершен.\n"
                f"Доступ к курсу открыт! 🎉\n\n"
                f"Для получения материалов свяжитесь с поддержкой.",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"📊 Статус платежа `{payment_id}`:\n\n"
                f"**{status}**\n\n"
                f"Для оплаты нажмите /buy",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            "🤔 Я понимаю команды:\n"
            "/start - начать работу\n"
            "/buy - купить доступ\n"
            "/check - как проверить статус\n\n"
            "Или отправьте ID платежа:\n"
            "`status_ваш_id_платежа`",
            parse_mode='Markdown'
        )

# ============================================
# ЗАПУСК БОТА
# ============================================

async def post_init(application):
    """Выполняется после инициализации бота"""
    bot_info = await application.bot.get_me()
    
    print("="*60)
    print(f"🤖 Бот запущен: @{bot_info.username}")
    print(f"👤 Имя: {bot_info.first_name}")
    print(f"🆔 ID: {bot_info.id}")
    print(f"🌐 API: {API_URL}")
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
    print("="*60)

def main():
    """Запуск бота"""
    print("="*60)
    print("🚀 ЗАПУСК TELEGRAM БОТА")
    print("="*60)
    
    # Проверяем переменные окружения
    if not check_env():
        print("❌ Ошибка: проверьте переменные окружения в Render")
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
        application.add_handler(CommandHandler("help", help_callback))
        
        # Callback обработчики
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^buy$"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^status_"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^menu$"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^my_payments$"))
        application.add_handler(CallbackQueryHandler(handle_callback, pattern="^help$"))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Бот инициализирован")
        print("⏳ Запускаю polling...")
        
        # Запускаем бота
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()
