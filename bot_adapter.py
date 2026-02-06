# bot_adapter.py
"""
АДАПТЕР ДЛЯ ЗАПУСКА БОТА С АВТОИСПРАВЛЕНИЯМИ
Заменяет app.py как точку входа
"""

import os
import sys
import logging
import threading
import types
from flask import Flask, jsonify
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальные переменные
bot_thread = None
bot_running = False

def apply_telegram_patches():
    """
    Применяем все необходимые патчи для совместимости
    Вызывается ДО импорта оригинального бота
    """
    try:
        # 1. Подавляем warnings
        import warnings
        warnings.filterwarnings("ignore")
        
        # 2. Патч для urllib3.contrib.appengine (если старая версия telegram)
        sys.modules['urllib3.contrib.appengine'] = types.ModuleType('urllib3.contrib.appengine')
        sys.modules['urllib3.contrib.appengine'].__all__ = []
        sys.modules['urllib3.contrib.appengine'].AppEngineManager = None
        sys.modules['urllib3.contrib.appengine'].is_appengine_sandbox = lambda: False
        
        logger.info("✅ Применены базовые патчи")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка применения патчей: {e}")
        return False

def fix_telegram_imports():
    """
    Создает псевдонимы для обратной совместимости
    """
    try:
        import telegram.ext
        
        # Если есть Filters но нет filters, создаем псевдоним
        if hasattr(telegram.ext, 'Filters') and not hasattr(telegram.ext, 'filters'):
            telegram.ext.filters = telegram.ext.Filters
            logger.info("✅ Создан псевдоним: filters = Filters")
            
        # Если есть CallbackContext но нет ContextTypes
        if hasattr(telegram.ext, 'CallbackContext'):
            telegram.ext.ContextTypes = type('ContextTypes', (), {
                'DEFAULT_TYPE': telegram.ext.CallbackContext
            })
            logger.info("✅ Создан псевдоним: ContextTypes.DEFAULT_TYPE = CallbackContext")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания псевдонимов: {e}")
        return False

def run_original_bot():
    """Запускает оригинальный бота bot_adaptive.py"""
    global bot_running
    
    try:
        logger.info("🔧 Подготовка к запуску бота...")
        
        # 1. Применяем патчи
        apply_telegram_patches()
        
        # 2. Добавляем текущую директорию в путь
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # 3. Проверяем наличие файла
        if not os.path.exists('bot_adaptive.py'):
            logger.error("❌ Файл bot_adaptive.py не найден!")
            return
        
        # 4. Проверяем версию telegram
        import telegram
        logger.info(f"📦 Версия python-telegram-bot: {telegram.__version__}")
        
        # 5. Создаем псевдонимы для импортов
        fix_telegram_imports()
        
        # 6. Импортируем оригинальный модуль
        logger.info("📥 Импорт модуля bot_adaptive...")
        
        # Динамический импорт с обработкой ошибок
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot_adaptive", "bot_adaptive.py")
        bot_module = importlib.util.module_from_spec(spec)
        
        # Выполняем код модуля
        with open('bot_adaptive.py', 'r', encoding='utf-8') as f:
            module_code = f.read()
        
        # Выполняем код в контексте модуля
        exec(module_code, bot_module.__dict__)
        
        logger.info("✅ Модуль bot_adaptive успешно загружен")
        
        # 7. Запускаем main функцию
        if hasattr(bot_module, 'main'):
            logger.info("🚀 Запуск функции main()...")
            bot_running = True
            
            # Запускаем в try-except для перехвата ошибок
            try:
                bot_module.main()
            except KeyboardInterrupt:
                logger.info("⏹ Бот остановлен по сигналу")
            except Exception as e:
                logger.error(f"❌ Ошибка в работе бота: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.error("❌ Функция main() не найдена в bot_adaptive.py")
            
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        import traceback
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        bot_running = False

# Flask endpoints
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Variatica Bot Adapter",
        "bot": "running" if bot_running else "stopped",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "bot_status": "/bot-status"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot": "running" if bot_running else "stopped",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/bot-status')
def bot_status():
    global bot_thread
    return jsonify({
        "running": bot_running,
        "thread_alive": bot_thread.is_alive() if bot_thread else False
    }), 200

def start_bot_background():
    """Запуск бота в фоновом режиме"""
    global bot_thread
    
    import time
    time.sleep(2)  # Даем Flask запуститься
    
    # Проверяем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        logger.error("Добавьте в Environment Variables на Render")
        return
    
    logger.info(f"✅ Токен найден: {token[:10]}...")
    logger.info("🤖 Запуск Telegram бота в фоновом режиме...")
    
    bot_thread = threading.Thread(target=run_original_bot, daemon=True)
    bot_thread.start()

if __name__ == '__main__':
    # Логируем информацию о среде
    logger.info(f"🐍 Python версия: {sys.version.split()[0]}")
    logger.info(f"📁 Текущая директория: {os.getcwd()}")
    logger.info(f"📄 Файлы: {[f for f in os.listdir('.') if f.endswith('.py')]}")
    
    # Запускаем бота в фоне
    start_bot_background()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
