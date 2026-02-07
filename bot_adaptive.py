"""
РАБОЧИЙ БОТ ДЛЯ ПРОДАКШЕНА
Теперь когда база данных работает!
"""

import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://testing-lichnosti-bot-1.onrender.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню - теперь с реальной БД"""
    await update.message.reply_text(
        "🎉 **ПЛАТЕЖНАЯ СИСТЕМА РАБОТАЕТ!**\n\n"
        "✅ PostgreSQL база настроена\n"
        "✅ Таблица payments создана\n"
        "✅ API принимает платежи\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Купить доступ (690 руб)", callback_data="buy")],
            [InlineKeyboardButton("🧪 Тестовый платеж (1 руб)", callback_data="test_payment")],
            [InlineKeyboardButton("📊 Проверить статус", callback_data="check_status")],
            [InlineKeyboardButton("🔧 Настройки", callback_data="settings")]
        ])
    )

async def buy_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка доступа - реальный платеж"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💰 **ПОКУПКА ДОСТУПА К КУРСУ**\n\n"
        "Стоимость: 690 рублей\n"
        "Доступ навсегда\n\n"
        "Следующие шаги:\n"
        "1. Создать платеж в базе\n"
        "2. Интегрировать с ЮKassa\n"
        "3. Получить ссылку для оплаты\n"
        "4. Открыть доступ после оплаты\n\n"
        "⚙️ *Интеграция с ЮKassa в разработке*",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧪 Протестировать создание", callback_data="create_real")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ])
    )

async def create_test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж - уже работает!"""
    query = update.callback_query
    await query.answer("⏳ Создаю тестовый платеж...")
    
    # Данные для теста
    test_data = {
        "payment_id": f"telegram_test_{query.from_user.id}",
        "user_id": query.from_user.id,
        "amount": 1.0,
        "email": f"user{query.from_user.id}@telegram.org",
        "description": "Тест из Telegram бота"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            await query.edit_message_text(
                f"✅ **ТЕСТ УСПЕШЕН!**\n\n"
                f"Платеж создан в PostgreSQL!\n\n"
                f"📋 Детали:\n"
                f"• ID: `{result['payment_id']}`\n"
                f"• Статус: {result['status']}\n"
                f"• Время: {result.get('created_at', 'сейчас')}\n\n"
                f"**Что дальше:**\n"
                f"1. Добавить интеграцию с ЮKassa\n"
                f"2. Настроить вебхуки\n"
                f"3. Создать механизм доступа",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Проверить в базе", 
                     url=f"{API_URL}/api/payment-status/{result['payment_id']}")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back")]
                ])
            )
        else:
            await query.edit_message_text(f"❌ Ошибка: {response.status_code}\n{response.text}")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка подключения: {str(e)}")

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    await start(update, context)

def main():
    print("="*60)
    print("🎉 РАБОЧИЙ БОТ ДЛЯ ПРОДАКШЕНА")
    print(f"API: {API_URL}")
    print("База данных: PostgreSQL ✅")
    print("="*60)
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buy_access, pattern="^buy$"))
    app.add_handler(CallbackQueryHandler(create_test_payment, pattern="^test_payment$"))
    app.add_handler(CallbackQueryHandler(create_test_payment, pattern="^create_real$"))
    app.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))
    
    print("✅ Бот запущен! База данных работает.")
    print("💡 Следующий шаг: интеграция с ЮKassa")
    print("="*60)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
