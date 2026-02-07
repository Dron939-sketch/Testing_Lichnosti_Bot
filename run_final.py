#!/usr/bin/env python3
"""
УПРОЩЕННЫЙ ЗАПУСК БОТА ДЛЯ RENDER
БЕЗ FLASK, ТОЛЬКО TELEGRAM БОТ
"""

import os
import sys
import asyncio
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("="*50)
print("🚀 ЗАПУСК TELEGRAM БОТА ВАРИАТИКА")
print("="*50)

async def main():
    """Основная асинхронная функция"""
    
    # Получаем токен
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return
    
    logger.info(f"✅ Токен получен: {TOKEN[:10]}...")
    
    try:
        # Импортируем библиотеки
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import (
            Application,
            CommandHandler,
            CallbackQueryHandler,
            ContextTypes,
            ConversationHandler
        )
        
        logger.info("📦 Библиотеки загружены")
        
        # === ОПРЕДЕЛЯЕМ ФУНКЦИИ ===
        
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Команда /start"""
            logger.info(f"📨 Команда /start от {update.effective_user.id}")
            
            keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
            
            await update.message.reply_text(
                "🎴 <b>Добро пожаловать в ВАРИАТИКА!</b>\n\n"
                "Нажмите кнопку чтобы начать тест:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        
        async def start_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработка кнопки начала теста"""
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "✅ Тест начался!\n\n"
                "<b>Эта демо-версия показывает:</b>\n"
                "1. Работа команды /start\n"
                "2. Работа кнопок\n"
                "3. Соединение с Telegram\n\n"
                "Полный тест в bot_adaptive.py",
                parse_mode="HTML"
            )
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Команда /help"""
            await update.message.reply_text(
                "📋 <b>Доступные команды:</b>\n\n"
                "/start - Начать тест\n"
                "/test - Проверка работы\n"
                "/help - Эта справка\n\n"
                "<i>Бот успешно запущен на Render!</i>",
                parse_mode="HTML"
            )
        
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Команда /test"""
            await update.message.reply_text("✅ Бот работает корректно на Render!")
        
        # === СОЗДАЕМ ПРИЛОЖЕНИЕ ===
        
        # Важно: создаем новый event loop
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test", test_command))
        
        # Добавляем обработчик кнопок
        application.add_handler(CallbackQueryHandler(start_test_callback, pattern="^start_test$"))
        
        logger.info("🤖 Бот запущен и готов к работе")
        
        # Запускаем polling с отдельным loop
        await application.run_polling(
            drop_pending_updates=True,
            close_loop=False,
            stop_signals=()  # ОТКЛЮЧАЕМ обработку сигналов
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise

def main_sync():
    """Синхронная обертка для запуска"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except RuntimeError as e:
        if "already running" in str(e):
            logger.error("⚠️ Event loop уже запущен. Используем альтернативный метод...")
            # Альтернативный запуск
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(main())
            finally:
                loop.close()
        else:
            raise

if __name__ == "__main__":
    main_sync()
