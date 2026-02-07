#!/usr/bin/env python3
"""
БОТ ДЛЯ RENDER - ФИНАЛЬНАЯ ВЕРСИЯ
Решает проблему с event loop в Python 3.13
"""

import os
import sys
import logging

# Настройка логирования ДО всех импортов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("="*60)
print("🚀 TELEGRAM БОТ ВАРИАТИКА - РАБОЧАЯ ВЕРСИЯ")
print("="*60)

def run_bot():
    """Запуск бота в отдельном процессе"""
    
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлен")
        sys.exit(1)
    
    logger.info(f"✅ Токен получен: {TOKEN[:10]}...")
    
    try:
        # Импортируем библиотеки
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
        
        # === ОПРЕДЕЛЯЕМ ФУНКЦИИ ===
        
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Команда /start"""
            logger.info(f"📨 /start от {update.effective_user.id}")
            
            keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="test")]]
            
            await update.message.reply_text(
                "🎴 <b>ВАРИАТИКА v2.0</b>\n\n"
                "✅ Бот успешно запущен на Render!\n\n"
                "Нажмите кнопку для проверки:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        
        async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Обработка кнопок"""
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "🎉 <b>ВСЁ РАБОТАЕТ!</b>\n\n"
                "✅ Кнопки работают\n"
                "✅ Команды работают\n"
                "✅ Render работает\n\n"
                "<i>Теперь можно переносить основной функционал</i>",
                parse_mode="HTML"
            )
        
        async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Команда /test"""
            await update.message.reply_text("✅ Тест пройден! Бот полностью работоспособен.")
        
        # === ЗАПУСК БОТА ===
        
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("test", test))
        app.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("🤖 Бот запущен и готов к работе")
        
        # ЗАПУСКАЕМ БЕЗ asyncio.run - используем низкоуровневый API
        import asyncio
        
        # Создаем новый event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Запускаем бота
            loop.run_until_complete(
                app.run_polling(
                    drop_pending_updates=True,
                    close_loop=False,
                    stop_signals=(),
                    allowed_updates=None,
                    timeout=30,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30,
                    pool_timeout=30
                )
            )
        except KeyboardInterrupt:
            logger.info("👋 Бот остановлен")
        finally:
            # Всегда закрываем loop
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Запускаем бота
    run_bot()
