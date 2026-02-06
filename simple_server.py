import os
import threading
import logging
from flask import Flask

# Импортируем и запускаем бота в отдельном потоке
def run_bot():
    from your_main_file import main  # импортируйте вашу main функцию
    main()

app = Flask(__name__)

@app.route('/')
def home():
    return "Variatica Bot is running! Bot is active in background."

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=5000)
