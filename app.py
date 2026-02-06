# app.py - ВЕРСИЯ С АВТОФИКСОМ
import os
import sys
import threading
import logging
import time
from flask import Flask, jsonify, request
from datetime import datetime

# ============ ПАТЧ ДЛЯ TELEGRAM-BOT 20.7 С PYTHON 3.13 ============
def apply_telegram_patch():
    """Применяет патч для исправления ошибки python-telegram-bot 20.7"""
    try:
        # Пробуем импортировать telegram.ext
        import telegram.ext._updater as updater_module
        
        # Сохраняем оригинальный конструктор
        original_init = updater_module.Updater.__init__
        
        def patched_init(self, *args, **kwargs):
            """
            Патченая версия конструктора Updater
            Удаляет проблемный приватный атрибут _Updater__polling_cleanup_cb
            который вызывает ошибку в Python 3.13
            """
            # Вызываем оригинальный конструктор
            result = original_init(self, *args, **kwargs)
            
            # Удаляем проблемные атрибуты
            problem_attrs = [
                '_Updater__polling_cleanup_cb',
                '__polling_cleanup_cb',
                '_polling_cleanup_cb'
            ]
            
            for attr_name in problem_attrs:
                try:
                    delattr(self, attr_name)
                except AttributeError:
                    pass
            
            return result
        
        # Заменяем оригинальный конструктор на патченый
        updater_module.Updater.__init__ = patched_init
        
        print("✅ Патч для telegram-bot 20.7 применен успешно")
        return True
        
    except ImportError as e:
        print(f"⚠️  Не удалось импортировать telegram.ext: {e}")
        print("⚠️  Попробуйте: pip install python-telegram-bot==20.7")
        return False
    except Exception as e:
        print(f"⚠️  Ошибка применения патча: {e}")
        return False

# Применяем патч сразу при запуске
apply_telegram_patch()
# ============ КОНЕЦ ПАТЧА ============

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

def run_fixed_bot():
    """Запуск бота через bot_adaptive_fixed.py"""
    global bot_running
    
    try:
        logger.info("🤖 Запуск бота через bot_adaptive_fixed.py...")
        
        # Добавляем текущую директорию в путь Python
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Проверяем наличие файла бота
        bot_file = os.path.join(current_dir, 'bot_adaptive_fixed.py')
        if not os.path.exists(bot_file):
            logger.error(f"❌ Файл bot_adaptive_fixed.py не найден в {current_dir}")
            return
        
        logger.info(f"✅ Файл бота найден: {bot_file}")
        
        # Проверяем версию telegram
        try:
            import telegram
            logger.info(f"📦 Версия python-telegram-bot: {telegram.__version__}")
        except ImportError as e:
            logger.error(f"❌ Не удалось импортировать telegram: {e}")
            logger.error("Установите: pip install python-telegram-bot==20.7")
            return
        
        # Импортируем исправленный бот
        logger.info("📥 Импорт модуля bot_adaptive_fixed...")
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot_fixed", bot_file)
        bot_module = importlib.util.module_from_spec(spec)
        
        # Выполняем код модуля
        with open(bot_file, 'r', encoding='utf-8') as f:
            module_code = f.read()
        
        exec(module_code, bot_module.__dict__)
        
        logger.info("✅ Модуль bot_adaptive_fixed успешно загружен")
        
        # Запускаем main функцию
        if hasattr(bot_module, 'main'):
            logger.info("🚀 Запуск функции main()...")
            bot_running = True
            
            try:
                bot_module.main()
            except KeyboardInterrupt:
                logger.info("⏹ Бот остановлен по сигналу")
            except Exception as e:
                logger.error(f"❌ Ошибка в работе бота: {e}")
                import traceback
                logger.error(f"Трассировка:\n{traceback.format_exc()}")
        else:
            logger.error("❌ Функция main() не найдена")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
    finally:
        bot_running = False

@app.route('/')
def home():
    """Главная страница"""
    return jsonify({
        "status": "running",
        "service": "Variatica Bot + Flask API",
        "version": "2.0",
        "bot_status": "running" if bot_running else "stopped",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "bot_status": "/bot-status",
            "start_bot": "/start-bot (POST)"
        }
    })

@app.route('/health')
def health():
    """Health check для Render"""
    return jsonify({
        "status": "healthy",
        "bot": "running" if bot_running else "stopped",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/bot-status')
def bot_status():
    """Статус бота"""
    global bot_thread
    return jsonify({
        "running": bot_running,
        "thread_alive": bot_thread.is_alive() if bot_thread else False
    }), 200

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Ручной запуск бота"""
    global bot_thread, bot_running
    
    if bot_running:
        return jsonify({"status": "already_running", "message": "Бот уже запущен"}), 200
    
    try:
        bot_thread = threading.Thread(target=run_fixed_bot, daemon=True)
        bot_thread.start()
        
        # Ждем немного чтобы бот успел запуститься
        time.sleep(3)
        
        return jsonify({
            "status": "started",
            "bot_running": bot_running
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

def start_bot_on_init():
    """Автозапуск бота при старте сервера"""
    global bot_thread
    
    # Ждем немного перед запуском бота
    logger.info("⏳ Ожидание перед запуском бота...")
    time.sleep(3)
    
    # Проверяем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        logger.error("Добавьте в Environment Variables на Render")
        logger.error("Инструкция: Dashboard → Environment → Add Environment Variable")
        return
    
    logger.info(f"✅ Токен найден: {token[:10]}...")
    
    logger.info("🤖 Запуск Telegram-бота через bot_adaptive_fixed.py...")
    
    bot_thread = threading.Thread(target=run_fixed_bot, daemon=True)
    bot_thread.start()
    
    # Проверяем запуск через 5 секунд
    time.sleep(5)
    if bot_thread.is_alive():
        logger.info("✅ Бот успешно запущен в фоновом режиме")
    else:
        logger.error("❌ Поток бота не запустился")

if __name__ == '__main__':
    # Логируем информацию о среде
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК ВАРИАТИКА БОТ v2.0 (с автофиксом)")
    logger.info("="*50)
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Текущая директория: {os.getcwd()}")
    
    # Список Python файлов
    py_files = [f for f in os.listdir('.') if f.endswith('.py')]
    logger.info(f"📄 Python файлы ({len(py_files)}): {py_files}")
    
    # Автозапуск бота
    start_bot_on_init()
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    logger.info(f"🔗 URL: https://testing-lichnosti-bot-qyra.onrender.com")
    logger.info(f"🏥 Health check: https://testing-lichnosti-bot-qyra.onrender.com/health")
    logger.info(f"🤖 Ручной запуск бота: POST /start-bot")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
