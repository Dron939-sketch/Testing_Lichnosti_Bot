import os
import threading
import logging
from flask import Flask, jsonify, request
from datetime import datetime
import asyncio
import sys

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        
        logger.info("🚀 Запуск Telegram бота...")
        bot_running = True
        
        # Запускаем бота
        bot_main()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта бота: {e}")
        logger.error("Убедитесь что файл bot_adaptive.py существует")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
            "bot_status": "/bot-status",
            "start_bot": "/start-bot (POST)"
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

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Запуск бота через API"""
    global bot_thread
    
    if bot_thread and bot_thread.is_alive():
        return jsonify({"status": "already_running"}), 200
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    return jsonify({"status": "bot_started"}), 200

# ЮKassa webhook endpoint (если нужно)
@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Webhook для уведомлений от ЮKassa"""
    try:
        data = request.json
        logger.info(f"📦 Webhook от ЮKassa: {data.get('event', 'unknown')}")
        
        # Обработка уведомлений
        # Здесь можно обновлять статусы платежей
        
        return jsonify({"status": "received"}), 200
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return jsonify({"error": str(e)}), 500

def start_bot_on_init():
    """Автозапуск бота при старте сервера"""
    global bot_thread
    
    # Ждем немного перед запуском бота
    import time
    time.sleep(2)
    
    logger.info("⏳ Автозапуск Telegram бота...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

if __name__ == '__main__':
    # Запускаем бота при старте
    start_bot_on_init()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
