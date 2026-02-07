"""
Упрощенная версия бота с основными функциями
"""

import logging
import asyncio
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

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
START, TESTING, RESULTS = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в тест ВАРИАТИКА!</b>\n\n"
        f"Это упрощенная версия для тестирования.\n\n"
        f"Готов начать?"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    return START

async def start_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "✅ Тест начат!\n\n"
        "Это упрощенная версия.\n\n"
        "В полной версии будет:\n"
        "• 4 этапа тестирования\n"
        "• Анализ профиля\n"
        "• Персональные рекомендации",
        parse_mode="HTML"
    )
    
    return RESULTS

async def main():
    """Основная функция"""
    # Получаем токен
    import os
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            START: [
                CallbackQueryHandler(start_test_callback, pattern="^start_test$")
            ],
            RESULTS: []
        },
        fallbacks=[],
        per_message=True
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    
    # Запускаем
    logger.info("🤖 Упрощенный бот запущен")
    await application.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )

if __name__ == "__main__":
    asyncio.run(main())
