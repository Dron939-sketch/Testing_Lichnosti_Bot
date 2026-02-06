#!/usr/bin/env python3
"""
Запуск бота ВАРИАТИКА v2.0
Отдельный процесс для бота
"""

import os
import sys
import logging
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_environment():
    """Проверка необходимых переменных окружения"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'YOOKASSA_SHOP_ID',
        'YOOKASSA_SECRET_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
        logger.error("Установите их в настройках Render.com")
        return False
    
    return True

async def main_async():
    """Асинхронный запуск бота"""
    try:
        # Импортируем основной модуль бота
        from bot_adaptive import main as bot_main
        
        logger.info("🤖 Запускаю бота ВАРИАТИКА v2.0...")
        
        # Запускаем бота
        await bot_main()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Проверьте наличие файла bot_adaptive.py")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

def main():
    """Точка входа"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА ВАРИАТИКА v2.0")
    logger.info("=" * 50)
    
    # Проверяем переменные окружения
    if not check_environment():
        sys.exit(1)
    
    # Запускаем асинхронно
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("⏹ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
