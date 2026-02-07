#!/usr/bin/env python3
"""
Минимальный запуск бота для Render
"""

import asyncio
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Минимальный запуск"""
    try:
        # Проверка токена
        TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
            sys.exit(1)
        
        logger.info("🚀 Запуск минимального бота...")
        
        # Импорт здесь, чтобы избежать циклических импортов
        from telegram.ext import Application
        
        # Создаем простое приложение
        application = Application.builder().token(TOKEN).build()
        
        # Простая команда /start
        from telegram import Update
        from telegram.ext import CommandHandler, ContextTypes
        
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("✅ Бот работает! Используйте /test для проверки.")
        
        async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("✅ Тест пройден! Бот работает корректно.")
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("test", test))
        
        # Запускаем
        logger.info("🤖 Бот запущен и готов к работе")
        await application.run_polling(
            drop_pending_updates=True,
            close_loop=False  # Важно для Render
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
