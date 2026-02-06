# bot_adaptive_fixed.py
"""
АВТОМАТИЧЕСКИЙ ФИКС ДЛЯ bot_adaptive.py
Запускает оригинальный бот с автоматическими исправлениями для совместимости
"""

import sys
import os
import importlib.util
import re
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_bot_code(source_code: str) -> str:
    """
    Автоматически исправляет код bot_adaptive.py для совместимости с версией 20.7
    """
    fixes_applied = []
    
    # 1. Исправляем Filters -> filters (если есть)
    if 'Filters.' in source_code:
        source_code = re.sub(r'Filters\.', 'filters.', source_code)
        fixes_applied.append("Filters. → filters.")
    
    # 2. Исправляем CallbackContext -> ContextTypes.DEFAULT_TYPE
    if 'CallbackContext' in source_code:
        source_code = re.sub(
            r'context:\s*CallbackContext',
            'context: ContextTypes.DEFAULT_TYPE',
            source_code
        )
        fixes_applied.append("CallbackContext → ContextTypes.DEFAULT_TYPE")
    
    # 3. Добавляем недостающие async (простые случаи)
    async_patterns = [
        (r'def start\(', r'async def start('),
        (r'def help\(', r'async def help('),
        (r'def handle_', r'async def handle_'),
        (r'def (\w+)_handler\(', r'async def \1_handler('),
    ]
    
    for pattern, replacement in async_patterns:
        if re.search(pattern, source_code):
            source_code = re.sub(pattern, replacement, source_code)
            fixes_applied.append(f"Добавлен async для функций")
    
    # 4. Исправляем Updater -> Application
    if 'Updater(' in source_code:
        source_code = re.sub(
            r'updater\s*=\s*Updater\([^)]+\)',
            'application = Application.builder().token(TOKEN).build()',
            source_code
        )
        source_code = re.sub(r'updater\.', 'application.', source_code)
        source_code = re.sub(r'dp\.', 'application.', source_code)
        fixes_applied.append("Updater → Application")
    
    # 5. Исправляем start_polling -> run_polling
    if 'start_polling()' in source_code:
        source_code = source_code.replace('start_polling()', 'run_polling()')
        fixes_applied.append("start_polling → run_polling")
    
    # 6. Добавляем await к callback_query.answer()
    if 'callback_query.answer()' in source_code and 'await' not in source_code:
        source_code = re.sub(
            r'([^a-zA-Z0-9_])callback_query\.answer\(\)',
            r'\1await callback_query.answer()',
            source_code
        )
        fixes_applied.append("Добавлен await к callback_query.answer()")
    
    logger.info(f"✅ Применено исправлений: {len(fixes_applied)}")
    for fix in fixes_applied:
        logger.info(f"  • {fix}")
    
    return source_code

def load_and_fix_bot():
    """
    Загружает bot_adaptive.py, применяет исправления и возвращает модуль
    """
    try:
        # Путь к оригинальному файлу
        original_file = 'bot_adaptive.py'
        
        if not os.path.exists(original_file):
            logger.error(f"❌ Файл {original_file} не найден!")
            return None
        
        # Читаем оригинальный код
        with open(original_file, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        logger.info(f"📖 Загружен оригинальный код ({len(original_code)} символов)")
        
        # Применяем исправления
        fixed_code = fix_bot_code(original_code)
        
        # Создаем временный модуль
        spec = importlib.util.spec_from_loader('bot_fixed', loader=None)
        module = importlib.util.module_from_spec(spec)
        
        # Выполняем исправленный код в модуле
        exec(fixed_code, module.__dict__)
        
        logger.info("✅ Модуль успешно загружен и исправлен")
        return module
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки модуля: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """
    Главная функция - запускает исправленного бота
    """
    logger.info("="*50)
    logger.info("🤖 ЗАПУСК АВТОФИКС БОТА")
    logger.info("="*50)
    
    # Загружаем и исправляем модуль
    bot_module = load_and_fix_bot()
    
    if not bot_module:
        logger.error("❌ Не удалось загрузить модуль бота")
        return
    
    try:
        # Проверяем версию telegram
        import telegram
        logger.info(f"📦 python-telegram-bot версия: {telegram.__version__}")
        
        # Запускаем main функцию из модуля
        if hasattr(bot_module, 'main'):
            logger.info("🚀 Запуск исправленного бота...")
            bot_module.main()
        else:
            logger.error("❌ Функция main() не найдена в модуле")
            
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Попробуйте: pip install python-telegram-bot==20.7")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
