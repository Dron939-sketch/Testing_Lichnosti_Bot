# app.py - ПОЛНАЯ ВЕРСИЯ С ПАТЧЕМ ДЛЯ TELEGRAM-BOT
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

def safe_import_bot_module(bot_file_path):
    """Безопасный импорт модуля бота с обработкой синтаксических ошибок"""
    try:
        # Проверяем файл на синтаксические ошибки
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Очищаем файл от возможных незакрытых кавычек в начале
        lines = content.split('\n')
        cleaned_lines = []
        
        # Удаляем патч для telegram-bot если он есть (он уже в app.py)
        skip_lines = False
        for line in lines:
            # Пропускаем блок патча в bot_adaptive.py
            if '# ============ ПАТЧ ДЛЯ TELEGRAM-BOT ============' in line:
                skip_lines = True
                continue
            if skip_lines and '# ============ КОНЕЦ ПАТЧА ============' in line:
                skip_lines = False
                continue
            if not skip_lines:
                # Удаляем строки с незакрытыми кавычками
                if line.strip() in ['"""', "'''"] and len(line.strip()) == 3:
                    continue
                cleaned_lines.append(line)
        
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Создаем модуль
        import importlib.util
        spec = importlib.util.spec_from_file_location("bot_adaptive_module", bot_file_path)
        bot_module = importlib.util.module_from_spec(spec)
        
        # Выполняем очищенный код
        exec(cleaned_content, bot_module.__dict__)
        
        logger.info("✅ Модуль бота успешно загружен (с очисткой)")
        return bot_module
        
    except SyntaxError as e:
        logger.error(f"❌ Синтаксическая ошибка в bot_adaptive.py: {e}")
        
        # Пробуем прямой импорт как запасной вариант
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            # Переименовываем файл чтобы избежать конфликтов
            temp_file = os.path.join(current_dir, '_temp_bot.py')
            with open(bot_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Простая очистка - удаляем первые 40 строк если там проблема
            lines = content.split('\n')
            if len(lines) > 40:
                cleaned = '\n'.join(lines[40:])
            else:
                cleaned = content
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            
            # Импортируем
            import importlib.util
            spec = importlib.util.spec_from_file_location("_temp_bot", temp_file)
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            # Удаляем временный файл
            os.remove(temp_file)
            
            logger.info("✅ Модуль бота загружен через временный файл")
            return bot_module
            
        except Exception as e2:
            logger.error(f"❌ Не удалось загрузить бот: {e2}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки модуля бота: {e}")
        return None

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
            # Проверим другие возможные имена
            for filename in ['bot_adaptive_fixed.py', 'bot_adapter.py', 'bot.py']:
                alt_file = os.path.join(current_dir, filename)
                if os.path.exists(alt_file):
                    logger.info(f"✅ Найден альтернативный файл: {filename}")
                    bot_file = alt_file
                    break
            else:
                logger.error(f"📂 Файлы в директории: {[f for f in os.listdir('.') if f.endswith('.py')]}")
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
        
        # Загружаем модуль бота безопасным способом
        logger.info("📥 Загрузка модуля bot_adaptive...")
        bot_module = safe_import_bot_module(bot_file)
        
        if not bot_module:
            logger.error("❌ Не удалось загрузить модуль бота")
            return
        
        # Проверяем наличие функции main
        if not hasattr(bot_module, 'main'):
            logger.error("❌ Функция main() не найдена в модуле бота")
            
            # Проверяем другие возможные функции запуска
            for func_name in ['run_bot', 'start_bot', 'create_app']:
                if hasattr(bot_module, func_name):
                    logger.info(f"✅ Найдена функция {func_name}()")
                    bot_module.main = getattr(bot_module, func_name)
                    break
            else:
                logger.error("❌ Не найдено ни одной функции запуска бота")
                return
        
        logger.info("✅ Модуль bot_adaptive успешно загружен")
        
        # Запускаем main функцию
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
        finally:
            bot_running = False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в run_bot: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
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
        if not data:
            return jsonify({"error": "No JSON data"}), 400
            
        logger.info(f"📦 Webhook от ЮKassa: {data.get('event', 'unknown')}")
        
        # Базовая обработка
        event = data.get('event', 'unknown')
        payment_id = data.get('object', {}).get('id', 'unknown')
        
        logger.info(f"🔔 Событие: {event}, Платеж: {payment_id}")
        
        return jsonify({"status": "received", "event": event}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/start-bot', methods=['POST'])
def start_bot_manual():
    """Ручной запуск бота (для отладки)"""
    global bot_thread, bot_running
    
    if bot_running:
        return jsonify({"status": "already_running", "message": "Бот уже запущен"}), 200
    
    if bot_thread and bot_thread.is_alive():
        return jsonify({"status": "thread_alive", "message": "Поток бота активен"}), 200
    
    try:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Ждем немного чтобы бот успел запуститься
        time.sleep(2)
        
        return jsonify({
            "status": "started", 
            "thread_alive": bot_thread.is_alive(),
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
    
    # Проверяем запуск через 5 секунд
    time.sleep(5)
    if bot_thread.is_alive():
        logger.info("✅ Бот успешно запущен в фоновом режиме")
    else:
        logger.error("❌ Поток бота не запустился")

if __name__ == '__main__':
    # Логируем информацию о среде
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК ВАРИАТИКА БОТ v2.0")
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
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
