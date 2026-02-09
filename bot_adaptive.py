"""
БОТ ВАРИАТИКА - ТОЛЬКО ПЛАТЕЖИ И ВЫДАЧА МАТЕРИАЛОВ
Короткая версия с полным логированием
"""

import os
import logging
import asyncio
import base64
import uuid
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ============================================
# НАСТРОЙКА ЛОГГИРОВАНИЯ
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('payment_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# КОНФИГУРАЦИЯ
# ============================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8311564413:AAE5iu5n0VNFA_8cd9HT0BeD4776IKGsvtE")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "381864")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "test_1pIOqTgbYqCRm2yWLgrk9MhB1acMhH8bRBrYGgvQd_c")
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

logger.info(f"🔧 Конфигурация загружена:")
logger.info(f"   API_URL: {API_URL}")
logger.info(f"   YOOKASSA_SHOP_ID: {YOOKASSA_SHOP_ID[:10]}...")
logger.info(f"   YOOKASSA_SECRET_KEY: {YOOKASSA_SECRET_KEY[:10]}...")

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С API
# ============================================

def log_api_call(endpoint: str, response):
    """Логирование API вызовов"""
    logger.info(f"📡 API CALL: {endpoint}")
    logger.info(f"   Status: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"   Error: {response.text}")

def get_user_access(user_id: int) -> dict:
    """Получает информацию о доступах пользователя"""
    try:
        url = f"{API_URL}/api/check-access/{user_id}"
        logger.info(f"🔍 Проверка доступа: GET {url}")
        
        response = requests.get(url, timeout=10)
        log_api_call(f"GET {url}", response)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Доступ проверен: has_access={data.get('has_access')}")
            return data
        else:
            logger.error(f"❌ Ошибка API: {response.status_code}")
            return {"success": False, "error": f"API error {response.status_code}"}
            
    except Exception as e:
        logger.error(f"💥 Исключение в get_user_access: {e}")
        return {"success": False, "error": str(e)}

def get_materials_link(user_id: int, payment_id: str, token: str = None) -> dict:
    """Получает ссылку на материалы"""
    try:
        url = f"{API_URL}/api/get-materials/{payment_id}"
        params = {"user_id": user_id}
        
        if token:
            params["token"] = token
            
        logger.info(f"🔗 Получение материалов: GET {url}")
        logger.info(f"   Params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        log_api_call(f"GET {url}", response)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Материалы получены: success={data.get('success')}")
            return data
        else:
            logger.error(f"❌ Ошибка получения материалов: {response.status_code}")
            return {"success": False, "error": f"API error {response.status_code}"}
            
    except Exception as e:
        logger.error(f"💥 Исключение в get_materials_link: {e}")
        return {"success": False, "error": str(e)}

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        url = f"{API_URL}/api/payment-status/{payment_id}"
        logger.info(f"📊 Проверка статуса платежа: GET {url}")
        
        response = requests.get(url, timeout=10)
        log_api_call(f"GET {url}", response)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            logger.info(f"✅ Статус платежа {payment_id}: {status}")
            return {"success": True, "status": status}
        else:
            logger.error(f"❌ Ошибка проверки статуса: {response.status_code}")
            return {"success": False, "error": f"API error {response.status_code}"}
            
    except Exception as e:
        logger.error(f"💥 Исключение в check_payment_status_db: {e}")
        return {"success": False, "error": str(e)}

def create_payment_in_db(user_id: int, amount: float = 690.0, 
                         is_test: bool = False, profile_data: dict = None) -> dict:
    """Создает запись о платеже в БД"""
    try:
        timestamp = int(time.time())
        payment_id = f"test_{user_id}_{timestamp}" if is_test else f"variatica_{user_id}_{timestamp}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "description": f"Тестовый платеж {amount} руб" if is_test else "Полный пакет ВАРИАТИКА - 690 руб",
            "email": f"user_{user_id}@telegram.org"
        }
        
        if profile_data:
            simplified_profile = {
                "profile_key": profile_data.get("display_name", ""),
                "type_code": profile_data.get("type_code", ""),
                "level": profile_data.get("level", 1),
                "dilts_code": profile_data.get("dilts_code", "")
            }
            payload["profile_data"] = simplified_profile
        
        logger.info(f"💳 Создание платежа в БД: POST {API_URL}/api/create-payment-advanced")
        logger.info(f"   Payment ID: {payment_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Amount: {amount}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=payload,
            timeout=10
        )
        
        log_api_call(f"POST {API_URL}/api/create-payment-advanced", response)
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            logger.info(f"✅ Платеж создан в БД: {payment_id}")
            logger.info(f"   Confirmation URL: {'Есть' if response_data.get('confirmation_url') else 'Нет'}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "confirmation_url": response_data.get('confirmation_url'),
                "yookassa_id": response_data.get('yookassa_id')
            }
        else:
            logger.error(f"❌ Ошибка создания платежа в БД: {response.status_code}")
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"💥 Исключение в create_payment_in_db: {e}")
        return {"success": False, "error": str(e)}

# ============================================
# ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ МАТЕРИАЛОВ
# ============================================

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials для получения материалов"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🚀 ПОЛЬЗОВАТЕЛЬ ЗАПРОСИЛ МАТЕРИАЛЫ: {user_id} ({user_name})")
    
    # Шаг 1: Проверяем доступ
    logger.info(f"🔍 Шаг 1: Проверка доступа для user_id={user_id}")
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        error_msg = access_data.get('error', 'Unknown error')
        logger.error(f"❌ ОШИБКА ПРОВЕРКИ ДОСТУПА: {error_msg}")
        
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"📊 Результат проверки доступа: has_access={access_data.get('has_access')}")
    
    # Шаг 2: Если нет доступа - предлагаем купить
    if not access_data.get('has_access', False):
        logger.info(f"❌ У пользователя {user_id} нет доступа")
        
        keyboard = [
            [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП 690 РУБ", callback_data="buy_variatica_package")],
            [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")]
        ]
        
        await update.message.reply_text(
            f"📭 *У ВАС НЕТ ДОСТУПА*\n\n"
            f"👤 *{user_name}*, для получения материалов необходимо оплатить доступ.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Шаг 3: Ищем активный доступ
    accesses = access_data.get('accesses', [])
    logger.info(f"🔍 Найдено {len(accesses)} доступов для пользователя {user_id}")
    
    if not accesses:
        logger.error(f"❌ Нет данных о доступах для user_id={user_id}")
        await update.message.reply_text(
            "❌ *Ошибка данных доступа*\n\nОбратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    # Шаг 4: Ищем активный доступ
    for idx, access in enumerate(accesses):
        logger.info(f"🔍 Проверяем доступ #{idx+1}:")
        logger.info(f"   Payment ID: {access.get('payment_id')}")
        logger.info(f"   Has Access: {access.get('has_access')}")
        logger.info(f"   Is Active: {access.get('is_active')}")
        logger.info(f"   Profile Key: {access.get('profile_key')}")
        
        if access.get('has_access', False) and access.get('is_active', False):
            payment_id = access.get('payment_id')
            access_token = access.get('access_token')
            profile_key = access.get('profile_key')
            
            logger.info(f"✅ НАЙДЕН АКТИВНЫЙ ДОСТУП!")
            logger.info(f"   Payment ID: {payment_id}")
            logger.info(f"   Profile Key: {profile_key}")
            
            # Шаг 5: Получаем ссылку на материалы
            logger.info(f"🔗 Получаем ссылку на материалы для payment_id={payment_id}")
            materials_data = get_materials_link(user_id, payment_id, access_token)
            
            if materials_data.get('success', False):
                materials_link = materials_data.get('materials_link')
                if materials_link:
                    logger.info(f"✅ Ссылка получена через API: {materials_link[:50]}...")
                    
                    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                    
                    await update.message.reply_text(
                        f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                        f"🎯 Профиль: `{profile_key}`\n"
                        f"🔗 Ссылка на Яндекс.Диск\n\n"
                        f"Нажмите кнопку ниже для скачивания:",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return
                else:
                    logger.warning(f"⚠️ API вернул success=True, но нет ссылки на материалы")
            else:
                logger.warning(f"⚠️ Не удалось получить материалы через API: {materials_data.get('error')}")
    
    # Если дошли сюда - что-то пошло не так
    logger.error(f"❌ НЕ УДАЛОСЬ НАЙТИ АКТИВНЫЙ ДОСТУП С МАТЕРИАЛАМИ")
    await update.message.reply_text(
        "❌ *Не удалось получить материалы*\n\n"
        "Попробуйте:\n"
        "1. Проверить статус доступа (/myaccess)\n"
        "2. Обратиться в поддержку",
        parse_mode='Markdown'
    )

# ============================================
# КОМАНДА /MYACCESS
# ============================================

async def myaccess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /myaccess для проверки статуса"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🔍 ПОЛЬЗОВАТЕЛЬ ПРОВЕРЯЕТ ДОСТУП: {user_id} ({user_name})")
    
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        logger.error(f"❌ Ошибка при проверке доступа для user_id={user_id}")
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*",
            parse_mode='Markdown'
        )
        return
    
    if access_data.get('has_access'):
        accesses = access_data.get('accesses', [])
        logger.info(f"✅ У пользователя ЕСТЬ доступ: {len(accesses)} записей")
        
        for access in accesses:
            if access.get('has_access') and access.get('is_active'):
                payment_id = access.get('payment_id')
                profile_key = access.get('profile_key')
                
                logger.info(f"📋 Активный доступ найден:")
                logger.info(f"   Payment ID: {payment_id}")
                logger.info(f"   Profile Key: {profile_key}")
                
                message = (
                    f"✅ *ДОСТУП АКТИВЕН!*\n\n"
                    f"👤 *Пользователь:* {user_name}\n"
                    f"🎯 *Профиль:* `{profile_key or 'Не указан'}`\n"
                    f"📋 *ID платежа:* `{payment_id}`\n\n"
                    f"Используйте команду /materials для получения материалов"
                )
                
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown'
                )
                return
    else:
        logger.info(f"❌ У пользователя НЕТ доступа")
        await update.message.reply_text(
            f"❌ *ДОСТУП НЕ АКТИВЕН*\n\n"
            f"👤 *Пользователь:* {user_name}\n"
            f"📦 *Статус:* Доступ не оплачен\n\n"
            f"Используйте команду /start для покупки доступа",
            parse_mode='Markdown'
        )

# ============================================
# ОБРАБОТЧИК КНОПКИ "ПОЛУЧИТЬ МАТЕРИАЛЫ"
# ============================================

async def get_materials_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Получить материалы'"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        user_id = query.from_user.id
        user_name = query.from_user.first_name
        
        logger.info(f"🔄 НАЖАТА КНОПКА 'ПОЛУЧИТЬ МАТЕРИАЛЫ'")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   User Name: {user_name}")
        
        # Обновляем сообщение
        await query.edit_message_text(
            "🔍 *Ищу ваши материалы...*",
            parse_mode='Markdown'
        )
        
        # Создаем фейковое обновление для вызова команды materials
        fake_update = Update(
            update_id=update.update_id,
            message=query.message
        )
        
        # Вызываем команду materials
        await materials_command(fake_update, context)
        
    except Exception as e:
        logger.error(f"💥 ОШИБКА В ОБРАБОТЧИКЕ КНОПКИ: {e}")
        await query.edit_message_text(
            "❌ *Произошла ошибка*\n\n"
            "Попробуйте использовать команду /materials",
            parse_mode='Markdown'
        )

# ============================================
# ТЕСТОВЫЙ ПЛАТЕЖ
# ============================================

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж 1 рубль"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        user_id = query.from_user.id
        user_name = query.from_user.first_name
        
        logger.info(f"🧪 СОЗДАНИЕ ТЕСТОВОГО ПЛАТЕЖА")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   User Name: {user_name}")
        
        await query.edit_message_text("🧪 *Создаю тестовый платеж 1 рубль...*", parse_mode='Markdown')
        
        # Создаем платеж в БД
        db_result = create_payment_in_db(user_id, amount=1.0, is_test=True)
        
        if not db_result["success"]:
            error_msg = db_result.get('error', 'Неизвестная ошибка')
            logger.error(f"❌ ОШИБКА СОЗДАНИЯ ПЛАТЕЖА: {error_msg}")
            await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
            return
        
        payment_id = db_result["payment_id"]
        logger.info(f"✅ Платеж создан: {payment_id}")
        
        # Если API вернул ссылку - используем ее
        if db_result.get("confirmation_url"):
            confirmation_url = db_result["confirmation_url"]
            logger.info(f"🔗 Использую URL от API: {confirmation_url[:50]}...")
        else:
            # Иначе показываем сообщение
            logger.warning(f"⚠️ API не вернул confirmation_url")
            await query.edit_message_text(
                f"🧪 *ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН*\n\n"
                f"📋 *ID платежа:* `{payment_id}`\n\n"
                f"*Для оплаты свяжитесь с поддержкой:*\n"
                f"👉 @meysternlp",
                parse_mode='Markdown'
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=confirmation_url)],
            [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")]
        ]
        
        await query.edit_message_text(
            f"🧪 *ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН*\n\n"
            f"👤 *Пользователь:* {user_name}\n"
            f"💰 *Сумма:* 1 рубль\n"
            f"📋 *ID:* `{payment_id}`\n\n"
            f"*Для проверки платежной системы:*\n"
            f"1. Нажмите кнопку оплаты\n"
            f"2. Выберите любой способ оплаты\n"
            f"3. После успешной оплаты используйте /materials",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"💥 ОШИБКА В ТЕСТОВОМ ПЛАТЕЖЕ: {e}")
        await query.edit_message_text(
            "❌ *Произошла ошибка*\n\nПопробуйте позже.",
            parse_mode='Markdown'
        )

# ============================================
# ПРОВЕРКА СТАТУСА ПЛАТЕЖА
# ============================================

async def status_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        payment_id = query.data.replace("status_", "")
        logger.info(f"📊 ПРОВЕРКА СТАТУСА ПЛАТЕЖА: {payment_id}")
        
        await query.edit_message_text(f"🔍 *Проверяю статус:* `{payment_id}`", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ ОШИБКА ПРОВЕРКИ СТАТУСА: {error_msg}")
            await query.edit_message_text(f"❌ *Ошибка:* {error_msg}", parse_mode='Markdown')
            return
        
        status = result.get("status", "unknown")
        logger.info(f"📊 Статус платежа {payment_id}: {status}")
        
        if status == "succeeded":
            logger.info(f"✅ Платеж {payment_id} ОПЛАЧЕН!")
            
            keyboard = [[InlineKeyboardButton("📥 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data="get_materials")]]
            
            await query.edit_message_text(
                f"🎉 *ПЛАТЕЖ ОПЛАЧЕН!*\n\n"
                f"✅ Платеж `{payment_id}` успешно завершен!\n\n"
                f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                f"Нажмите кнопку ниже для получения материалов:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif status in ["pending", "waiting"]:
            logger.info(f"⏳ Платеж {payment_id} ожидает оплаты")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить статус", callback_data=f"status_{payment_id}")],
                [InlineKeyboardButton("🧪 Создать новый платеж", callback_data="test_payment")]
            ]
            
            await query.edit_message_text(
                f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
                f"Заказ `{payment_id}` еще не оплачен.\n\n"
                f"Если вы уже оплатили, подождите несколько минут и обновите статус.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            logger.warning(f"⚠️ Неизвестный статус платежа {payment_id}: {status}")
            await query.edit_message_text(f"📊 *Статус:* `{status}`", parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"💥 ОШИБКА ПРОВЕРКИ СТАТУСА: {e}")
        await query.edit_message_text(
            "❌ *Произошла ошибка*\n\nПопробуйте позже.",
            parse_mode='Markdown'
        )

# ============================================
# СТАРТОВАЯ КОМАНДА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    logger.info(f"🚀 НОВЫЙ ПОЛЬЗОВАТЕЛЬ: {user.id} ({user.first_name})")
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 *Добро пожаловать в тестовый бот платежей ВАРИАТИКА!*\n\n"
        f"*Доступные команды:*\n"
        f"/materials - Получить материалы после оплаты\n"
        f"/myaccess - Проверить статус доступа\n\n"
        f"*Тестовый платеж:* 1 рубль\n"
        f"*Полный пакет:* 690 рублей\n\n"
        f"Для начала тестирования нажмите кнопку ниже:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")],
        [InlineKeyboardButton("📦 ПРОВЕРИТЬ ДОСТУП", callback_data="check_access")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================
# КНОПКА ПРОВЕРКИ ДОСТУПА
# ============================================

async def check_access_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка проверки доступа"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        user_id = query.from_user.id
        logger.info(f"🔍 НАЖАТА КНОПКА ПРОВЕРКИ ДОСТУПА: user_id={user_id}")
        
        # Создаем фейковое обновление для вызова команды myaccess
        fake_update = Update(
            update_id=update.update_id,
            message=query.message
        )
        
        # Вызываем команду myaccess
        await myaccess_command(fake_update, context)
        
    except Exception as e:
        logger.error(f"💥 ОШИБКА ПРОВЕРКИ ДОСТУПА: {e}")
        await query.edit_message_text(
            "❌ *Произошла ошибка*\n\nПопробуйте команду /myaccess",
            parse_mode='Markdown'
        )

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК БОТА ПЛАТЕЖЕЙ ВАРИАТИКА")
    logger.info("="*50)
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("myaccess", myaccess_command))
    
    # Добавляем обработчики кнопок
    application.add_handler(CallbackQueryHandler(test_payment, pattern="^test_payment$"))
    application.add_handler(CallbackQueryHandler(status_payment, pattern="^status_"))
    application.add_handler(CallbackQueryHandler(get_materials_button, pattern="^get_materials$"))
    application.add_handler(CallbackQueryHandler(check_access_button, pattern="^check_access$"))
    
    logger.info("✅ Обработчики зарегистрированы")
    logger.info("🤖 Бот запущен!")
    
    # Запускаем бота
    application.run_polling(allowed_updates=None)

if __name__ == "__main__":
    main()
