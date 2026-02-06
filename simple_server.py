import os
import sys
import logging
from flask import Flask, jsonify
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Variatica Telegram Bot",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "message": "Сервер работает. Бот запускается отдельно."
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Запуск бота (если нужно запускать через API)"""
    try:
        # Попробуйте запустить бота
        import subprocess
        import threading
        
        def run_bot():
            try:
                # Запускаем бота в отдельном процессе
                subprocess.run([sys.executable, "bot_adaptive.py"], 
                             check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Ошибка запуска бота: {e}")
                logger.error(f"STDOUT: {e.stdout}")
                logger.error(f"STDERR: {e.stderr}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")
        
        # Запускаем в отдельном потоке
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        return jsonify({
            "status": "bot_started",
            "message": "Бот запускается в фоновом режиме"
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Запуск Flask сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
