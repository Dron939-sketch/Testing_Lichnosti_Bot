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
    
    # 3. Добавляем недостающие async (только если еще нет async)
    # Более точные паттерны для поиска функций, которые нуждаются в async
    lines = source_code.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Проверяем, начинается ли строка с "def " и не содержит ли уже "async"
        if line.strip().startswith('def ') and 'async' not in line:
            # Проверяем, это ли обработчик телеграма по имени функции
            func_name = line.split('def ')[1].split('(')[0].strip()
            
            # Список функций, которые должны быть async (обработчики телеграма)
            telegram_handlers = [
                'start', 'help', 'test', 'handle_',
                'payment', 'gift', 'package', 'results',
                'stage', 'clarification', 'dilts', 'cancel'
            ]
            
            # Проверяем, является ли это обработчиком телеграма
            should_be_async = False
            for handler in telegram_handlers:
                if handler in func_name.lower():
                    should_be_async = True
                    break
            
            # Также проверяем по параметрам функции
            if 'Update' in line or 'context:' in line:
                should_be_async = True
            
            if should_be_async:
                line = line.replace('def ', 'async def ', 1)
                fixes_applied.append(f"Добавлен async для {func_name}")
        
        fixed_lines.append(line)
    
    source_code = '\n'.join(fixed_lines)
    
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
    
    # 6. Удаляем двойные async если есть
    source_code = re.sub(r'async async def', 'async def', source_code)
    if 'async async def' in source_code:
        source_code = source_code.replace('async async def', 'async def')
        fixes_applied.append("Удалены двойные async")
    
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        original_file = os.path.join(current_dir, 'bot_adaptive.py')
        
        if not os.path.exists(original_file):
            logger.error(f"❌ Файл {original_file} не найден!")
            
            # Проверяем другие возможные файлы
            for filename in ['bot_adaptive_fixed.py', 'bot.py', 'main.py']:
                alt_file = os.path.join(current_dir, filename)
                if os.path.exists(alt_file):
                    logger.info(f"🔍 Найден альтернативный файл: {filename}")
                    original_file = alt_file
                    break
            
            if not os.path.exists(original_file):
                logger.error(f"📂 Файлы в директории: {os.listdir('.')}")
                return None
        
        logger.info(f"📖 Загружаем файл: {original_file}")
        
        # Читаем оригинальный код
        with open(original_file, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        logger.info(f"📖 Загружен оригинальный код ({len(original_code)} символов)")
        
        # Применяем исправления
        fixed_code = fix_bot_code(original_code)
        
        # Проверяем на двойные async перед выполнением
        if 'async async' in fixed_code:
            logger.warning("⚠️  Обнаружены двойные async, исправляю...")
            fixed_code = fixed_code.replace('async async', 'async')
        
        # Создаем временный модуль
        spec = importlib.util.spec_from_loader('bot_fixed', loader=None)
        module = importlib.util.module_from_spec(spec)
        
        # Выполняем исправленный код в модуле
        exec(fixed_code, module.__dict__)
        
        logger.info("✅ Модуль успешно загружен и исправлен")
        return module
        
    except SyntaxError as e:
        logger.error(f"❌ Синтаксическая ошибка: {e}")
        
        # Попробуем найти и показать проблемную строку
        lines = original_code.split('\n')
        if e.lineno and e.lineno < len(lines):
            problem_line = lines[e.lineno - 1]
            logger.error(f"📝 Проблемная строка {e.lineno}: {problem_line}")
        
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки модуля: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
        return None

def simple_bot_fallback():
    """
    Простой запасной бот если основной не работает
    """
    try:
        import os
        import asyncio
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes
        
        TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not TOKEN:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не установлен!")
        
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "🤖 Бот работает!\n\n"
                "Тестовая версия.\n\n"
                "Нажми /help для помощи."
            )
        
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "🆘 Помощь:\n\n"
                "/start - Начать\n"
                "/help - Эта справка\n\n"
                "Основной бот временно недоступен."
            )
        
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        print("🤖 Запущен простой тестовый бот")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Ошибка в простом боте: {e}")
        import traceback
        print(f"Трассировка:\n{traceback.format_exc()}")

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
        logger.info("🔄 Запускаю простой тестовый бот...")
        simple_bot_fallback()
        return
    
    try:
        # Проверяем версию telegram
        import telegram
        logger.info(f"📦 python-telegram-bot версия: {telegram.__version__}")
        
        # Запускаем main функцию из модуля
        if hasattr(bot_module, 'main'):
            logger.info("🚀 Запуск исправленного бота...")
            bot_module.main()
        elif hasattr(bot_module, 'run_bot'):
            logger.info("🚀 Запуск через run_bot...")
            bot_module.run_bot()
        elif hasattr(bot_module, 'start_bot'):
            logger.info("🚀 Запуск через start_bot...")
            bot_module.start_bot()
        else:
            logger.error("❌ Функция запуска не найдена")
            logger.info("🔄 Запускаю простой тестовый бот...")
            simple_bot_fallback()
            
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.error("Попробуйте: pip install python-telegram-bot==20.7")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
        logger.info("🔄 Запускаю простой тестовый бот...")
        simple_bot_fallback()

if __name__ == '__main__':
    main()
