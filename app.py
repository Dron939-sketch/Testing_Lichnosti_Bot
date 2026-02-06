# app.py - УПРОЩЕННАЯ ВЕРСИЯ
import os
import sys
import threading
import logging
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

def run_bot():
    """Запуск Telegram бота в отдельном потоке"""
    global bot_running
    
    try:
        # Добавляем текущую директорию в путь Python
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Импортируем и запускаем бота
        from bot_adaptive import main as bot_main
        
        logger.info("🚀 Запуск Telegram бота ВАРИАТИКА v2.0...")
        bot_running = True
        
        # Запускаем бота
        bot_main()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта бота: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        import traceback
        logger.error(f"Трассировка:\n{traceback.format_exc()}")
    finally:
        bot_running = False

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Variatica Bot + Flask API",
        "bot_status": "running" if bot_running else "stopped",
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
    return jsonify({
        "running": bot_running,
        "thread_alive": bot_thread.is_alive() if bot_thread else False
    }), 200

def start_bot_on_init():
    """Автозапуск бота при старте сервера"""
    global bot_thread
    
    # Ждем немного перед запуском бота
    import time
    time.sleep(3)
    
    # Проверяем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        logger.error("Добавьте в Environment Variables на Render")
        return
    
    logger.info(f"✅ Токен найден: {token[:10]}...")
    logger.info("🤖 Запуск Telegram бота в фоновом режиме...")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

if __name__ == '__main__':
    # Автозапуск бота
    start_bot_on_init()
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
