# app.py - ПОЛНАЯ ВЕРСИЯ С ПАТЧЕМ ДЛЯ TELEGRAM-BOT
import os
import sys
import threading
import logging
import time
from flask import Flask, jsonify
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

def run_bot():
    """Запуск Telegram бота в отдельном потоке"""
    global bot_running
    
    try:
        logger.info("🔧 Подготовка к запуску бота...")
        
        # Добавляем текущую директорию в путь Python
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Проверяем наличие файла бота
        bot_file = os.path.join(current_dir, 'bot_adaptive.py')
        if not os.path.exists(bot_file):
            logger.error(f"❌ Файл bot_adaptive.py не найден в {current_dir}")
            logger.error(f"📂 Файлы в директории: {os.listdir('.')}")
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
        
        # Импортируем и запускаем бота
        logger.info("📥 Импорт модуля bot_adaptive...")
        
        # Динамический импорт с обработкой ошибок
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot_adaptive", bot_file)
        bot_module = importlib.util.module_from_spec(spec)
        
        # Выполняем код модуля
        with open(bot_file, 'r', encoding='utf-8') as f:
            module_code = f.read()
        
        # Выполняем код в контексте модуля
        exec(module_code, bot_module.__dict__)
        
        logger.info("✅ Модуль bot_adaptive успешно загружен")
        
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
            logger.error("❌ Функция main() не найдена в bot_adaptive.py")
            
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
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
            "yookassa_webhook": "/yookassa-webhook (POST)"
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

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Webhook для ЮKassa (упрощенный)"""
    try:
        import json
        data = request.json
        logger.info(f"📦 Webhook от ЮKassa: {data.get('event', 'unknown')}")
        
        # Базовая обработка
        event = data.get('event', 'unknown')
        payment_id = data.get('object', {}).get('id', 'unknown')
        
        logger.info(f"🔔 Событие: {event}, Платеж: {payment_id}")
        
        return jsonify({"status": "received", "event": event}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({"error": str(e)}), 500

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
    
    # Проверяем ЮKassa
    shop_id = os.getenv('YOOKASSA_SHOP_ID')
    secret_key = os.getenv('YOOKASSA_SECRET_KEY')
    
    if shop_id and secret_key:
        logger.info(f"✅ ЮKassa настроен: Shop ID: {shop_id[:10]}...")
    else:
        logger.warning("⚠️  ЮKassa не настроен. Платежи не будут работать.")
        logger.warning("   Добавьте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY")
    
    logger.info("🤖 Запуск Telegram бота в фоновом режиме...")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

if __name__ == '__main__':
    # Логируем информацию о среде
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК ВАРИАТИКА БОТ v2.0")
    logger.info("="*50)
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Текущая директория: {os.getcwd()}")
    logger.info(f"📄 Python файлы: {[f for f in os.listdir('.') if f.endswith('.py')]}")
    
    # Автозапуск бота
    start_bot_on_init()
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    logger.info(f"🔗 URL: https://testing-lichnosti-bot-qyra.onrender.com")
    logger.info(f"🏥 Health check: https://testing-lichnosti-bot-qyra.onrender.com/health")
    
    # Для webhook нужно импортировать request
    from flask import request
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
