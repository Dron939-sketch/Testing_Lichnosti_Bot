"""
app.py - Основной файл для запуска на Render
Содержит Flask сервер для webhook и запускает Telegram бота в отдельном потоке
"""

import os
import sys
import logging
import threading
import asyncio
import traceback
from flask import Flask, request, jsonify
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)

# Импортируем конфигурацию для проверки
try:
    from config import Config
    config = Config()
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать конфигурацию: {e}")
    config = None

# ============================================
# WEBHOOK ДЛЯ ЮKASSA
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """
    Webhook для обработки уведомлений от ЮKassa
    Этот endpoint должен быть указан в настройках кабинета ЮKassa
    """
    try:
        # Получаем данные от ЮKassa
        event_json = request.get_json()
        
        if not event_json:
            logger.warning("⚠️ Получен пустой webhook от ЮKassa")
            return jsonify({"status": "error", "message": "Empty payload"}), 400
        
        logger.info(f"📨 Получен webhook от ЮKassa: {event_json.get('event', 'unknown')}")
        
        # Логируем основные данные
        event = event_json.get('event', '')
        payment_id = event_json.get('object', {}).get('id', '')
        status = event_json.get('object', {}).get('status', '')
        
        logger.info(f"💰 Событие: {event}, ID: {payment_id}, Статус: {status}")
        
        # Здесь должна быть логика обновления статуса платежа в вашей базе данных
        # Например, можно записать в файл или использовать базу данных
        
        # Простая логика логирования
        with open('payment_webhooks.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {event} - {payment_id} - {status}\n")
        
        # Всегда возвращаем 200 OK, чтобы ЮKassa не отправлял повторные запросы
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/yookassa-webhook', methods=['GET'])
def yookassa_webhook_verify():
    """Метод для верификации webhook (нужен для некоторых настроек)"""
    return jsonify({"status": "webhook_ready", "service": "variatica_bot"}), 200

# ============================================
# HEALTH CHECK И СТАТУС
# ============================================

@app.route('/')
def index():
    """Главная страница - показывает статус сервиса"""
    status = {
        "service": "Variatica Telegram Bot + YooKassa Webhook",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/yookassa-webhook (POST)",
            "health": "/health",
            "status": "/status"
        }
    }
    return jsonify(status)

@app.route('/health')
def health_check():
    """Health check для Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route('/status')
def status_check():
    """Проверка статуса сервиса"""
    try:
        # Проверяем конфигурацию
        config_status = "loaded" if config else "error"
        payment_enabled = config.is_payment_enabled if config else False
        
        status = {
            "service": "Variatica Bot",
            "status": "operational",
            "config": config_status,
            "payments_enabled": payment_enabled,
            "webhook_url": config.WEBHOOK_URL if config else "not_configured",
            "timestamp": datetime.now().isoformat(),
            "bot_thread": "running" if hasattr(app, 'bot_thread') and app.bot_thread.is_alive() else "stopped"
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================
# ЗАПУСК TELEGRAM БОТА
# ============================================

def run_bot():
    """Запуск Telegram бота в отдельном потоке"""
    try:
        logger.info("🤖 Запускаю Telegram бота в отдельном потоке...")
        
        # Создаем новый цикл событий для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Импортируем и запускаем бота
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from bot_adaptive import main as bot_main
        
        # Запускаем бота
        bot_main()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        logger.error(f"📋 Трассировка:\n{traceback.format_exc()}")

def start_bot_thread():
    """Запускает бота в отдельном потоке"""
    if hasattr(app, 'bot_thread') and app.bot_thread.is_alive():
        logger.info("🤖 Бот уже запущен")
        return
    
    logger.info("🚀 Создаю поток для Telegram бота...")
    app.bot_thread = threading.Thread(target=run_bot, name="telegram-bot")
    app.bot_thread.daemon = True  # Демонизированный поток (завершится с основным)
    app.bot_thread.start()
    logger.info("✅ Поток для бота создан и запущен")

# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    start_bot_thread()
    
    # Запускаем Flask сервер
    port = int(os.getenv('PORT', 10000))
    
    logger.info(f"🌐 Запускаю Flask сервер на порту {port}")
    logger.info(f"💰 Webhook URL: {config.WEBHOOK_URL if config else 'Не настроен'}/yookassa-webhook")
    logger.info(f"📊 Режим платежей: {'🟢 ВКЛЮЧЕН' if config and config.is_payment_enabled else '🔴 ВЫКЛЮЧЕН'}")
    
    # Для разработки используем debug, для продакшена - нет
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False  # Отключаем reloader, т.к. он создает дополнительные потоки
    )
