#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ИСПРАВЛЕННЫЙ ЗАПУСК
"""

import asyncio
import os
import sys

# Добавляем путь
sys.path.append(os.path.dirname(__file__))

# Устанавливаем правильную версию
os.system("pip install python-telegram-bot==20.3 > /dev/null 2>&1")

async def main_fixed():
    """Исправленная версия"""
    
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен")
        return
    
    # Импортируем после установки
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        ContextTypes,
        ConversationHandler
    )
    
    # Определяем функцию start_command
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎴 <b>Добро пожаловать в ВАРИАТИКА!</b>\n\n"
            "Нажмите кнопку чтобы начать тест:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]
            ]),
            parse_mode="HTML"
        )
        return "START_MENU"
    
    async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("✅ Тест начался!")
        return "TESTING"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            "START_MENU": [],
            "TESTING": []
        },
        fallbacks=[],
        per_message=True
    )
    
    application.add_handler(conv_handler)
    
    print("🤖 Бот запущен и готов к работе!")
    await application.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )

if __name__ == "__main__":
    asyncio.run(main_fixed())
