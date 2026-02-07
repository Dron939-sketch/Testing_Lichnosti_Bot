#!/usr/bin/env python3
"""
Простой HTTP-сервер для health check Render
Запускается в отдельном потоке
"""

from flask import Flask, jsonify
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "variatica-telegram-bot",
        "bot": "running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/ping')
def ping():
    return "pong"

def run_server():
    """Запуск сервера в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Запускаем в фоне
threading.Thread(target=run_server, daemon=True).start()
