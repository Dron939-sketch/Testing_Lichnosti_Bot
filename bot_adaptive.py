"""
УПРОЩЕННЫЙ ТЕСТ ВАРИАТИКА + Flask API платежи
Минимальная версия с работающей системой оплаты
"""

import logging
import os
import asyncio
import time
import requests
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не установлен!")

# URL вашего Flask API
FLASK_API_URL = "https://testing-lichnosti-bot-1.onrender.com"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
STAGE_1, RESULTS, PAYMENT_SCREEN, PAYMENT_SUCCESS = range(4)

# Константы
BOT_LINK = "https://t.me/testing_lichnosti_bot"
AUTHOR_LINK = "@meysternlp"
PAYMENT_AMOUNT = 690

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def make_sync_request(method: str, url: str, **kwargs):
    """Синхронный HTTP-запрос"""
    try:
        if method.lower() == 'get':
            response = requests.get(url, **kwargs)
        elif method.lower() == 'post':
            response = requests.post(url, **kwargs)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {"success": False, "error": "Invalid JSON response"}

async def make_async_request(method: str, url: str, **kwargs):
    """Асинхронная обертка для requests"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, make_sync_request, method, url, **kwargs)

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = (
        "👋 Добро пожаловать в упрощенный тест ВАРИАТИКА!\n\n"
        "Это демо-версия с работающей платежной системой.\n\n"
        "Нажмите кнопку ниже, чтобы начать тест."
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    # Упрощенный тест - сразу переходим к результатам
    context.user_data["test_completed"] = True
    context.user_data["profile_type"] = "SA"  # Пример результата
    
    result_text = (
        "🎉 Тест завершен!\n\n"
        "🎯 Ваш профиль: SA_4_val\n\n"
        "• Тип: СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ\n"
        "• Уровень: 4 (КРИЗИСНЫЙ)\n"
        "• Точка роста: ЦЕННОСТИ\n\n"
        "Что дальше?"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup)
    return RESULTS

# ========== ФУНКЦИИ ПЛАТЕЖЕЙ ==========

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран полного пакета"""
    query = update.callback_query
    await query.answer()
    
    package_text = (
        "💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА\n\n"
        "Что входит:\n"
        "• Полный разбор вашего профиля (15+ страниц)\n"
        "• Терапевтическая сказка\n"
        "• Книга «ВАРИАТИКА» (PDF)\n"
        "• Персональные рекомендации\n"
        "• Карта сильных сторон\n\n"
        "Цена: 690 ₽\n\n"
        "🔒 Безопасная оплата через ЮKassa"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Купить за 690 ₽", callback_data="start_payment")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup)
    return PAYMENT_SCREEN

async def handle_payment_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса оплаты - через Flask API"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    payment_id = f"pay_{user_id}_{int(time.time())}"
    
    logger.info(f"Starting payment for user {user_id}, payment_id: {payment_id}")
    
    try:
        # Шаг 1: Создаем запись платежа в БД через Flask API
        create_payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": PAYMENT_AMOUNT,
            "email": f"user{user_id}@telegram.org"
        }
        
        db_result = await make_async_request(
            "POST", 
            f"{FLASK_API_URL}/api/create-payment",
            json=create_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if not db_result.get("success", False):
            error_msg = db_result.get("error", "Неизвестная ошибка")
            raise Exception(f"Ошибка создания платежа в БД: {error_msg}")
        
        logger.info(f"Payment created in DB: {db_result}")
        
        # Шаг 2: Создаем платеж в ЮKassa через Flask API
        yookassa_payload = {
            "payment_id": payment_id,
            "amount": PAYMENT_AMOUNT,
            "description": "Полный пакет ВАРИАТИКА",
            "return_url": BOT_LINK
        }
        
        yookassa_result = await make_async_request(
            "POST",
            f"{FLASK_API_URL}/api/create-yookassa-payment",
            json=yookassa_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if not yookassa_result.get("success", True):
            error_msg = yookassa_result.get("error", "Неизвестная ошибка")
            raise Exception(f"ЮKassa: {error_msg}")
        
        logger.info(f"YooKassa payment created: {yookassa_result}")
        
        # Сохраняем данные платежа
        context.user_data["current_payment"] = {
            "payment_id": payment_id,
            "payment_url": yookassa_result.get("payment_url", ""),
            "amount": PAYMENT_AMOUNT,
            "status": yookassa_result.get("status", "pending")
        }
        
        # Показываем экран оплаты
        payment_text = (
            f"💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА\n\n"
            f"ID заказа: {payment_id[:8]}...\n"
            f"Цена: 690 ₽\n\n"
            f"Инструкция:\n"
            f"1. Нажмите «Оплатить»\n"
            f"2. Оплатите в открывшемся окне\n"
            f"3. Вернитесь и нажмите «Проверить оплату»"
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить 690 ₽", url=yookassa_result.get("payment_url", ""))],
            [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(payment_text, reply_markup=reply_markup)
        return PAYMENT_SCREEN
        
    except Exception as e:
        logger.error(f"Payment creation error: {e}", exc_info=True)
        
        error_text = f"❌ Ошибка создания платежа: {str(e)}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="start_payment")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(error_text, reply_markup=reply_markup)
        return PAYMENT_SCREEN

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа через Flask API"""
    query = update.callback_query
    await query.answer("🔍 Проверяем оплату...")
    
    payment_id = query.data.replace("check_payment_", "")
    if not payment_id:
        payment_data = context.user_data.get("current_payment", {})
        payment_id = payment_data.get("payment_id")
    
    if not payment_id:
        await query.answer("❌ ID платежа не найден", show_alert=True)
        return PAYMENT_SCREEN
    
    logger.info(f"Checking payment status for: {payment_id}")
    
    try:
        status_result = await make_async_request(
            "GET",
            f"{FLASK_API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if not status_result.get("success", False):
            error_msg = status_result.get("error", "Неизвестная ошибка")
            raise Exception(f"Ошибка проверки статуса: {error_msg}")
        
        payment_status = status_result.get("status", "unknown")
        
        if payment_status == "succeeded":
            await query.answer("✅ Оплата прошла успешно!", show_alert=True)
            
            # Доставка продукта
            delivery_text = (
                "🎉 Оплата прошла успешно!\n\n"
                "📦 Ваши материалы готовы:\n"
                "1. Полный разбор профиля\n"
                "2. Терапевтическая сказка\n"
                "3. Книга ВАРИАТИКА\n"
                "4. Рекомендации\n\n"
                "Ссылка: https://disk.yandex.ru/d/variatica_package\n\n"
                "Спасибо за покупку! 🎁"
            )
            
            await query.edit_message_text(delivery_text)
            
            if "current_payment" in context.user_data:
                del context.user_data["current_payment"]
            
            return PAYMENT_SUCCESS
            
        elif payment_status == "pending":
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
            ]
            
            await query.edit_message_text(
                f"⏳ Ожидание оплаты\n\nID: {payment_id[:8]}...\n\nЕсли вы уже оплатили, подождите 1-2 минуты.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="start_payment")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
            ]
            
            await query.edit_message_text(
                f"❌ Платеж не оплачен\n\nСтатус: {payment_status}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
    except Exception as e:
        logger.error(f"Payment status check error: {e}")
        
        error_text = f"⚠️ Ошибка проверки: {str(e)}"
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"check_payment_{payment_id}")]]
        
        await query.edit_message_text(error_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return PAYMENT_SCREEN

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена платежа"""
    query = update.callback_query
    await query.answer()
    
    if "current_payment" in context.user_data:
        del context.user_data["current_payment"]
    
    return await back_to_results(update, context)

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    
    result_text = (
        "🎉 Тест завершен!\n\n"
        "🎯 Ваш профиль: SA_4_val\n\n"
        "Что дальше?"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup)
    return RESULTS

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    start_text = "🚀 Начинаем тест заново!"
    keyboard = [[InlineKeyboardButton("▶️ Начать", callback_data="start_test")]]
    
    await query.edit_message_text(start_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    await update.message.reply_text("Тест отменён. /start чтобы начать заново.")
    return ConversationHandler.END

# ========== ЗАПУСК БОТА ==========

def main():
    """Запуск бота"""
    print("="*50)
    print("🚀 УПРОЩЕННЫЙ БОТ ВАРИАТИКА")
    print(f"🔗 Flask API: {FLASK_API_URL}")
    print(f"🤖 Токен: {'Установлен' if TOKEN else '❌ Нет!'}")
    print("💰 Платежи: Flask API + ЮKassa")
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
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            RESULTS: [
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(handle_payment_start, pattern="^start_payment$"),
                CallbackQueryHandler(check_payment_status, pattern="^check_payment_"),
                CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PAYMENT_SUCCESS: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    print("\n🤖 Бот запускается...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
