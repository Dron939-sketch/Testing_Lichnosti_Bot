# app.py - УПРОЩЕННАЯ ВЕРСИЯ
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Простой запуск бота"""
    logger.info("🚀 Запуск ВАРИАТИКА v2.0")
    logger.info(f"🐍 Python: {sys.version}")
    
    # Проверяем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
        return
    
    logger.info(f"✅ Токен: {token[:10]}...")
    
    try:
        # Простой импорт и запуск
        from bot_adaptive import main as bot_main
        bot_main()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
