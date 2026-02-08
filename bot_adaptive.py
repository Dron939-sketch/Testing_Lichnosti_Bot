#!/usr/bin/env python3
"""
Telegram Bot для платежной системы VARIATICA
ИСПРАВЛЕННАЯ ВЕРСИЯ с Invoices API (все способы оплаты)
"""

import os
import sys
import time
import json
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

# Ссылка на бота для возврата после оплаты
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

# ========== ИСПРАВЛЕННЫЕ ФУНКЦИИ ==========

def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 1.0, email: str = None, is_test: bool = False) -> dict:
    """Создает платеж через Invoices API (все способы оплаты)"""
    try:
        logger.info(f"📤 Создаю платеж через Invoices API: {payment_id}, сумма: {amount} руб")
        
        # Описание в зависимости от типа платежа
        description = f"Тестовый платеж {amount} руб" if is_test else f"Курс ВАРИАТИКА - {amount} руб"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "description": description,
            "email": email or f"user_{user_id}@telegram.org"
        }
        
        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: используем новый эндпоинт с Invoices API
        response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ API: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            if data.get('success'):
                # Проверяем, что это Invoices API
                invoice_type = data.get('invoice_type')
                available_methods = data.get('available_methods', 'unknown')
                
                if invoice_type == 'yookassa_invoice':
                    logger.info(f"✅ Счет создан через Invoices API: {payment_id}")
                    logger.info(f"📋 Доступные способы оплаты: {available_methods}")
                    
                    if available_methods == 'all':
                        logger.info("🎉 Пользователь увидит ВСЕ способы оплаты (СБП, ЮMoney, карты и др.)")
                    else:
                        logger.warning(f"⚠️ Доступные способы: {available_methods}")
                else:
                    logger.warning(f"⚠️ Используется старый API: {invoice_type}")
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "yookassa_id": data.get('yookassa_id'),
                    "confirmation_url": data.get('confirmation_url'),
                    "status": data.get('status', 'pending'),
                    "amount": amount,
                    "description": description,
                    "invoice_type": invoice_type,
                    "available_methods": available_methods
                }
            else:
                error_msg = data.get('error', 'Неизвестная ошибка')
                logger.error(f"❌ Ошибка API: {error_msg}")
                return {
                    "success": False,
                    "error": f"Ошибка API: {error_msg}"
                }
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка {response.status_code}: {error_text}")
            return {
                "success": False,
                "error": f"Ошибка {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'payment' in data:
                status = data['payment'].get('status', 'unknown')
                amount = data['payment'].get('amount', 0)
                user_id = data['payment'].get('user_id')
                payment_method = data['payment'].get('payment_method', 'unknown')
            else:
                status = data.get('status', 'unknown')
                amount = 0
                user_id = None
                payment_method = 'unknown'
                
            return {
                "success": True,
                "status": status,
                "amount": amount,
                "user_id": user_id,
                "payment_method": payment_method,
                "data": data
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": "Платеж не найден"
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка: {response.status_code}",
                "details": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_user_access(user_id: int) -> dict:
    try:
        response = requests.get(
            f"{API_URL}/api/check-access/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_materials_link(user_id: int, payment_id: str, token: str = None) -> dict:
    try:
        url = f"{API_URL}/api/get-materials/{payment_id}"
        params = {"user_id": user_id}
        
        if token:
            params["token"] = token
            
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========== ОБРАБОТЧИКИ КОМАНД (остаются без изменений) ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_690")],
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА (1 руб)", callback_data="test_buy")],
        [InlineKeyboardButton("📁 МОИ МАТЕРИАЛЫ", callback_data="my_materials")],
        [InlineKeyboardButton("🔍 ПРОВЕРИТЬ СТАТУС", callback_data="check_status_menu")]
    ]
    
    message_text = (
        f"🚀 *Добро пожаловать в VARIATICA!*\n\n"
        f"👋 *{user.first_name}*, выберите действие:\n\n"
        
        f"💎 *Полный курс:* 690 руб\n"
        f"• Полный доступ к материалам\n"
        f"• ВСЕ способы оплаты (СБП, ЮMoney, карты и др.)\n"
        f"• Мгновенная выдача после оплаты\n\n"
        
        f"🧪 *Тестовая оплата:* 1 руб\n"
        f"• Проверка платежной системы\n"
        f"• Тестовые материалы\n"
        f"• ВСЕ способы оплаты\n\n"
        
        f"⚙️ *Системная информация:*\n"
        f"• API: `{API_URL}`\n"
        f"• Бот: {TELEGRAM_BOT_URL}"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def test_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    await query.edit_message_text("📦 *Создаю тестовый платеж 1 рубль через Invoices API...*", parse_mode='Markdown')
    
    timestamp = int(time.time())
    payment_id = f"test_{user_id}_{timestamp}"
    
    payment_result = create_yookassa_payment(
        payment_id=payment_id,
        user_id=user_id,
        amount=1.0,
        email=f"user_{user_id}@telegram.org",
        is_test=True
    )
    
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    # Добавляем информацию о Invoices API
    invoice_info = ""
    if payment_result.get('invoice_type') == 'yookassa_invoice':
        invoice_info = "\n💡 *Invoices API активирован!* Вы увидите ВСЕ доступные способы оплаты."
    
    message_text = (
        f"✅ *ТЕСТОВЫЙ ПЛАТЕЖ 1 РУБЛЬ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID:* `{payment_id}`\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"🔄 *Тип:* Invoices API\n"
        f"💳 *Доступные способы:* {payment_result.get('available_methods', 'all')}"
        f"{invoice_info}\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты вы получите мгновенное уведомление."
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def buy_690_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    await query.edit_message_text("📦 *Создаю заказ на полный курс через Invoices API...*", parse_mode='Markdown')
    
    timestamp = int(time.time())
    payment_id = f"prod_{user_id}_{timestamp}"
    
    payment_result = create_yookassa_payment(
        payment_id=payment_id,
        user_id=user_id,
        amount=690.0,
        email=f"user_{user_id}@telegram.org",
        is_test=False
    )
    
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    # Добавляем информацию о Invoices API
    invoice_info = ""
    if payment_result.get('invoice_type') == 'yookassa_invoice':
        available_methods = payment_result.get('available_methods', 'all')
        if available_methods == 'all':
            invoice_info = "\n💡 *ВСЕ способы оплаты доступны:* СБП, ЮMoney, банковские карты, Тинькофф и другие!"
    
    message_text = (
        f"✅ *ЗАКАЗ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 руб\n"
        f"📚 *Продукт:* Полный курс ВАРИАТИКА\n"
        f"🔄 *Тип:* Invoices API\n"
        f"💳 *Доступные способы:* {payment_result.get('available_methods', 'all')}"
        f"{invoice_info}\n\n"
        f"*Что вы получите после оплаты:*\n"
        f"✅ Полный доступ ко всем материалам\n"
        f"✅ Мгновенное уведомление в Telegram\n"
        f"✅ Защищенную ссылку на Яндекс.Диск\n"
        f"✅ Техническую поддержку\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты вы получите доступ к материалам."
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 *Проверяю статус:*\n`{payment_id}`", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка:* {error_msg}", parse_mode='Markdown')
            return
        
        status = result.get("status", "unknown")
        amount = result.get("amount", 0)
        payment_method = result.get("payment_method", "unknown")
        
        # Информация о способе оплаты
        method_info = ""
        if payment_method != "unknown":
            method_info = f"\n💳 *Способ оплаты:* {payment_method}"
        
        if status == "succeeded":
            is_test = amount == 1.0
            
            if is_test:
                message = (
                    f"🎉 *ТЕСТОВЫЙ ПЛАТЕЖ ОПЛАЧЕН!*\n\n"
                    f"✅ Платеж `{payment_id}` успешно завершен!\n"
                    f"💰 Сумма: {amount} руб"
                    f"{method_info}\n\n"
                    f"*🔓 СИСТЕМА РАБОТАЕТ КОРРЕКТНО!*\n"
                    f"Для полного курса используйте /buy"
                )
            else:
                message = (
                    f"🎉 *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
                    f"✅ Ваш заказ `{payment_id}` успешно оплачен!\n"
                    f"💰 Сумма: {amount} руб"
                    f"{method_info}\n\n"
                    f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                    f"Вы получили доступ ко всем материалам курса ВАРИАТИКА!\n\n"
                    f"📁 Для получения материалов нажмите:\n"
                    f"`/materials`\n\n"
                    f"✅ Вы получите мгновенное уведомление с ссылкой."
                )
                
                # Проверяем доступ и показываем кнопку
                user_id = result.get("user_id", query.from_user.id)
                access_data = get_user_access(user_id)
                if access_data.get('has_access', False):
                    accesses = access_data.get('accesses', [])
                    for access in accesses:
                        if access.get('payment_id') == payment_id and access.get('access_token'):
                            keyboard = [[InlineKeyboardButton("📁 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data=f"get_materials_{payment_id}")]]
                            await query.edit_message_text(
                                message,
                                reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode='Markdown'
                            )
                            return
            
        elif status in ["pending", "waiting"]:
            message = (
                f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
                f"Заказ `{payment_id}` еще не оплачен.\n"
                f"💰 Сумма: {amount} руб"
                f"{method_info}\n\n"
                f"*Для оплаты используйте кнопку ниже:*"
            )
            keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", callback_data=f"retry_{payment_id}")]]
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            message = (
                f"📊 *Статус заказа:* `{status}`\n"
                f"💰 *Сумма:* {amount} руб"
                f"{method_info}"
            )
        
        await query.edit_message_text(message, parse_mode='Markdown')

# ... остальные функции остаются без изменений (materials_command, myaccess_command, check_command и т.д.)

async def retry_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("retry_"):
        payment_id = query.data[6:]
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text(
                f"❌ *Не удалось найти платеж* `{payment_id}`",
                parse_mode='Markdown'
            )
            return
        
        amount = result.get("amount", 1.0)
        user_id = result.get("user_id", query.from_user.id)
        
        is_test = amount == 1.0
        
        # Создаем новую ссылку через Invoices API
        new_payment_id = f"retry_{user_id}_{int(time.time())}"
        payment_result = create_yookassa_payment(
            payment_id=new_payment_id,
            user_id=user_id,
            amount=amount,
            email=f"user_{user_id}@telegram.org",
            is_test=is_test
        )
        
        if payment_result.get("success", False):
            keyboard = [[InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=payment_result["confirmation_url"])]]
            
            amount_text = "1 рубль" if is_test else "690 руб"
            
            # Информация о Invoices API
            invoice_info = ""
            if payment_result.get('invoice_type') == 'yookassa_invoice':
                invoice_info = "\n💡 *ВСЕ способы оплаты доступны!*"
            
            await query.edit_message_text(
                f"🔗 *НОВАЯ ССЫЛКА ДЛЯ ОПЛАТЫ*\n\n"
                f"📋 *ID:* `{new_payment_id}`\n"
                f"💰 *Сумма:* {amount_text}"
                f"{invoice_info}\n\n"
                f"Нажмите кнопку ниже для оплаты:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
        else:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(
                f"❌ *Не удалось создать ссылку оплаты*\n\n"
                f"`{error_msg}`\n\n"
                f"Попробуйте создать новый платеж.",
                parse_mode='Markdown'
            )

def check_configuration():
    print("=" * 70)
    print("🤖 VARIATICA PAYMENT BOT - Invoices API ВЕРСИЯ")
    print("=" * 70)
    
    errors = []
    warnings = []
    
    # Проверка токена
    if not TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установен")
        print("❌ Токен бота: НЕ УСТАНОВЛЕН!")
    else:
        print(f"✅ Токен бота: установлен")
    
    # Проверка URL API
    if not API_URL:
        errors.append("⚠️ API_URL не установлен, используется по умолчанию")
    print(f"✅ API URL: {API_URL}")
    
    # Проверка доступности API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API доступен: {response.status_code}")
            print(f"📊 Версия API: {data.get('version', 'unknown')}")
            print(f"📊 Статус: {data.get('status', 'unknown')}")
            
            # Проверяем поддержку Invoices API
            if 'invoices' in data.get('supported_payment_methods', '').lower():
                print("✅ Invoices API: ПОДДЕРЖИВАЕТСЯ")
            else:
                print("⚠️ Invoices API: проверьте конфигурацию")
                
        else:
            warnings.append(f"⚠️ API недоступен: код {response.status_code}")
            print(f"⚠️ API ответ: {response.status_code}")
    except Exception as e:
        errors.append(f"❌ API недоступен: {str(e)}")
        print(f"❌ API недоступен: {e}")
    
    print("=" * 70)
    
    if errors:
        print("❌ Критические ошибки конфигурации:")
        for error in errors:
            print(f"  {error}")
        return False
    
    if warnings:
        print("⚠️ Предупреждения конфигурации:")
        for warning in warnings:
            print(f"  {warning}")
    
    print("✅ Конфигурация проверена успешно!")
    print("=" * 70)
    print("🚀 Доступные команды:")
    print("  /start - Главное меню")
    print("  /materials - Получить материалы")
    print("  /myaccess - Мои доступы")
    print("  /buy - Купить доступ за 690 руб")
    print("  /check <id> - Проверить статус")
    print("=" * 70)
    print("💡 ОСОБЕННОСТИ НОВОЙ ВЕРСИИ:")
    print("  • Invoices API - ВСЕ способы оплаты")
    print("  • СБП, ЮMoney, банковские карты и др.")
    print("  • Чеки по 54-ФЗ создаются автоматически")
    print("=" * 70)
    return True

# ... остальной код (очистка конфликтов, обработчики ошибок, main) остается без изменений ...

def main():
    """Основная функция запуска"""
    print("=" * 80)
    print("🚀 VARIATICA PAYMENT BOT - Invoices API ВЕРСИЯ")
    print("=" * 80)
    
    if not check_configuration():
        print("❌ Конфигурация неполная, выход...")
        sys.exit(1)
    
    print("\n🛡️ Проверяю и очищаю возможные конфликты...")
    # ... очистка конфликтов ...
    
    print("⏳ Жду 3 секунды перед запуском...")
    time.sleep(3)
    
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Регистрация обработчиков
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", start))  # Алиас для /buy
        app.add_handler(CommandHandler("materials", materials_command))
        app.add_handler(CommandHandler("myaccess", myaccess_command))
        app.add_handler(CommandHandler("check", check_command))
        
        # Регистрация callback-обработчиков
        app.add_handler(CallbackQueryHandler(test_buy_callback, pattern="^test_buy$"))
        app.add_handler(CallbackQueryHandler(buy_690_callback, pattern="^buy_690$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(get_materials_callback, pattern="^get_materials_"))
        app.add_handler(CallbackQueryHandler(my_materials_callback, pattern="^my_materials$"))
        app.add_handler(CallbackQueryHandler(check_status_menu_callback, pattern="^check_status_menu$"))
        app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
        app.add_handler(CallbackQueryHandler(retry_payment_callback, pattern="^retry_"))
        
        print("✅ Бот запущен успешно!")
        print(f"📡 API: {API_URL}")
        print(f"🤖 Бот: {TELEGRAM_BOT_URL}")
        print(f"💡 Режим: Invoices API (все способы оплаты)")
        print(f"⏰ Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("📱 Используйте команду /start в Telegram")
        print("💎 Полный курс: 690 руб (Invoices API)")
        print("🧪 Тестовый платеж: 1 руб (Invoices API)")
        print("📁 Материалы: мгновенная выдача после оплаты")
        print("=" * 80)
        print("🎯 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ:")
        print("  • Бот теперь использует Invoices API")
        print("  • Пользователи видят ВСЕ способы оплаты")
        print("  • СБП, ЮMoney, карты и другие методы")
        print("=" * 80)
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=1.0,
            timeout=30
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"🔄 Автовосстановление через 10 секунд...")
        time.sleep(10)
        
        os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    main()
