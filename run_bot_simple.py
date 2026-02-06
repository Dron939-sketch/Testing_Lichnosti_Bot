# run_bot_simple.py - ОБНОВЛЕННЫЙ
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_minimal_bot():
    """Запускает минимальную версию бота если основная не работает"""
    logger.info("🔄 Запуск минимальной версии бота...")
    
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ Токен не найден!")
            return
        
        async def start(update, context):
            await update.message.reply_text(
                "✅ Бот работает! (Минимальная версия)\n\n"
                "Основной бот временно недоступен.\n"
                "Администратор уже работает над исправлением.\n\n"
                "Команды:\n"
                "/help - помощь\n"
                "/test - тестовая команда"
            )
        
        async def help_command(update, context):
            await update.message.reply_text(
                "🤖 Минимальная версия бота ВАРИАТИКА\n\n"
                "Тест запущен успешно!\n\n"
                "Полная версия с платежами скоро будет восстановлена."
            )
        
        async def test(update, context):
            await update.message.reply_text("✅ Тестовая команда работает!")
        
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("test", test))
        
        logger.info("🤖 Минимальный бот запущен!")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в минимальном боте: {e}")

def main():
    print("="*50)
    print("🤖 ЗАПУСК БОТА ВАРИАТИКА v2.0 с ЮKassa")
    print("="*50)
    
    # Проверяем конфигурацию ЮKassa
    shop_id = os.getenv('YOOKASSA_SHOP_ID')
    secret_key = os.getenv('YOOKASSA_SECRET_KEY')
    
    if shop_id and secret_key:
        logger.info(f"✅ ЮKassa настроен: Shop ID: {shop_id[:10]}...")
        logger.info(f"🌐 Webhook URL: {os.getenv('WEBHOOK_URL', 'Не настроен')}/yookassa-webhook")
    else:
        logger.warning("⚠️  ЮKassa не настроен. Платежи не будут работать.")
    
    # Проверяем токен Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
        logger.error("Добавьте в Environment Variables на Render")
        return
    
    logger.info(f"✅ Токен Telegram: {token[:10]}...")
    
    # Импортируем и запускаем бота
    try:
        import telegram
        logger.info(f"📦 python-telegram-bot: {telegram.__version__}")
        
        # Добавляем путь для импорта
        sys.path.insert(0, os.path.dirname(__file__))
        
        # Пробуем разные варианты
        bot_files = ['bot_adaptive_fixed.py', 'bot_adaptive.py']
        
        for bot_file in bot_files:
            if os.path.exists(bot_file):
                try:
                    logger.info(f"🔄 Попытка импорта: {bot_file}")
                    
                    # Динамический импорт
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("bot_module", bot_file)
                    bot_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(bot_module)
                    
                    logger.info(f"✅ Файл {bot_file} загружен успешно!")
                    
                    if hasattr(bot_module, 'main'):
                        logger.info("🚀 Запуск основного бота...")
                        bot_module.main()
                        return  # Успех!
                    else:
                        logger.error(f"❌ Функция main() не найдена в {bot_file}")
                        
                except SyntaxError as e:
                    logger.error(f"❌ Синтаксическая ошибка в {bot_file}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Ошибка в {bot_file}: {e}")
                    continue
        
        # Если ни один файл не сработал
        logger.error("❌ Все файлы бота содержат ошибки!")
        logger.info("🔄 Переключаюсь на минимальную версию...")
        run_minimal_bot()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта модулей: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
