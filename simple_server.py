"""
Простой HTTP сервер для Render
"""

from flask import Flask, jsonify
import threading
import time
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Variatica Telegram Bot",
        "version": "2.0",
        "mode": "polling",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    # Заглушка для вебхука ЮKassa
    return jsonify({"status": "webhook_received", "mode": "polling_active"})

def run_bot():
    """Запуск Telegram бота"""
    import bot_adaptive
    bot_adaptive.main()

if __name__ == "__main__":
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 HTTP сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
