# app.py - МИНИМАЛЬНАЯ ВЕРСИЯ ДЛЯ ЗАПУСКА ОСНОВНОГО БОТА
import os
import sys
import threading
import logging
import time
from flask import Flask, jsonify

# НАСТРОЙКА ЛОГИРОВАНИЯ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_thread = None
bot_running = False

def run_original_bot():
    """Запуск ОРИГИНАЛЬНОГО bot_adaptive.py"""
    global bot_running
    
    try:
        logger.info("🚀 ЗАПУСК ОСНОВНОГО БОТА bot_adaptive.py")
        
        # Проверяем токен
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
            return
        
        logger.info(f"✅ Токен найден: {token[:10]}...")
        
        # Добавляем текущую директорию в путь Python
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Импортируем ОРИГИНАЛЬНЫЙ бот напрямую
        logger.info("📥 Импорт ОРИГИНАЛЬНОГО bot_adaptive...")
        from bot_adaptive import main
        
        # Запускаем
        bot_running = True
        logger.info("▶️ Запуск функции main() из bot_adaptive.py")
        main()
        
    except SyntaxError as e:
        logger.error(f"❌ СИНТАКСИЧЕСКАЯ ОШИБКА в bot_adaptive.py: {e}")
        
        # Показываем где ошибка
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Подробности:\n{error_details}")
        
        # Если ошибка на строке 839
        if "line 839" in str(e) or "line 839" in error_details:
            logger.error("⚠️  ОШИБКА НА СТРОКЕ 839!")
            logger.error("Найдите файл bot_adaptive.py и исправьте строку 839")
            logger.error("Вероятно, там незакрытые тройные кавычки: \"\"\"")
            
    except ImportError as e:
        logger.error(f"❌ ОШИБКА ИМПОРТА: {e}")
        logger.error("Проверьте зависимости: pip install python-telegram-bot==20.7")
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА ЗАПУСКА БОТА: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
        
    finally:
        bot_running = False

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Variatica Bot",
        "bot": "running" if bot_running else "stopped",
        "version": "2.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def start_bot_on_init():
    """Автозапуск бота при старте"""
    global bot_thread
    
    # Ждем 3 секунды
    time.sleep(3)
    logger.info("🤖 АВТОЗАПУСК ОСНОВНОГО БОТА...")
    
    bot_thread = threading.Thread(target=run_original_bot, daemon=True)
    bot_thread.start()
    
    # Проверяем через 5 секунд
    time.sleep(5)
    if bot_thread.is_alive():
        logger.info("✅ ОСНОВНОЙ БОТ УСПЕШНО ЗАПУЩЕН!")
    else:
        logger.error("❌ ОСНОВНОЙ БОТ НЕ ЗАПУСТИЛСЯ")

if __name__ == '__main__':
    # Информация о запуске
    logger.info("="*60)
    logger.info("🚀 ЗАПУСК ОСНОВНОГО ВАРИАТИКА БОТА v2.0")
    logger.info("="*60)
    logger.info(f"🐍 Python: {sys.version}")
    logger.info(f"📁 Директория: {os.getcwd()}")
    
    # Список файлов
    files = [f for f in os.listdir('.') if f.endswith('.py')]
    logger.info(f"📄 Python файлы: {files}")
    
    # Автозапуск бота
    start_bot_on_init()
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Flask запущен на порту {port}")
    logger.info(f"🔗 Ваш URL: https://testing-lichnosti-bot-qyra.onrender.com")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
