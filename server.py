"""
Простой HTTP сервер для Render
"""

from flask import Flask, request, jsonify
import os
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "service": "Variatica Telegram Bot",
        "version": "2.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/webhook', methods=['POST'])
def webhook():
    # Если будете использовать webhook вместо polling
    return jsonify({"status": "ok"})

def run_bot():
    """Запуск Telegram бота в отдельном потоке"""
    import bot_adaptive
    # Запуск бота (будет использовать polling)
    print("🤖 Запускаю Telegram бота...")

if __name__ == "__main__":
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Запуск HTTP сервера на порту {port}")
    app.run(host='0.0.0.0', port=port)
