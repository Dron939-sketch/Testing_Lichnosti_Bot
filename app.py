# app.py - ДЛЯ РАБОТЫ С ПЛАТЕЖАМИ
import os
import sys
import logging
import threading
from flask import Flask, jsonify, request

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def run_telegram_bot():
    """Запускает Telegram бота в отдельном потоке"""
    import time
    time.sleep(2)  # Даем Flask запуститься
    
    try:
        from bot_adaptive import main as bot_main
        logger.info("🤖 Запуск Telegram бота...")
        bot_main()
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")

# ============================================
# WEBHOOK ДЛЯ ЮKASSA
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Получаем уведомления о платежах от ЮKassa"""
    try:
        # Получаем данные
        data = request.get_json()
        event = data.get('event')
        payment_data = data.get('object', {})
        
        logger.info(f"💰 Webhook от ЮKassa: {event}")
        logger.info(f"📊 Платеж ID: {payment_data.get('id', 'unknown')}")
        
        # Проверяем подпись (если настроен SECRET)
        signature = request.headers.get('Yookassa-Signature')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if secret_key and signature:
            # Здесь должна быть проверка подписи
            logger.info("🔐 Подпись получена (нужно реализовать проверку)")
        
        # Обрабатываем успешный платеж
        if event == 'payment.succeeded':
            payment_id = payment_data.get('id')
            amount = payment_data.get('amount', {}).get('value')
            user_id = payment_data.get('metadata', {}).get('user_id')
            
            logger.info(f"✅ Платеж успешен: {payment_id}, сумма: {amount}, user: {user_id}")
            
            # TODO: Отправить файлы пользователю
            # Для этого нужен доступ к боту из этого контекста
            
            return jsonify({"status": "success"}), 200
        
        # Другие события
        elif event == 'payment.waiting_for_capture':
            logger.info(f"⏳ Платеж ожидает подтверждения")
            return jsonify({"status": "waiting"}), 200
            
        elif event == 'payment.canceled':
            logger.info(f"❌ Платеж отменен")
            return jsonify({"status": "canceled"}), 200
            
        else:
            logger.warning(f"⚠️ Неизвестное событие: {event}")
            return jsonify({"status": "unknown"}), 200
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# СТРАНИЦЫ ДЛЯ ПРОВЕРКИ
# ============================================

@app.route('/')
def home():
    """Главная страница для проверки работы"""
    return jsonify({
        "status": "online",
        "service": "Variatica Bot v2.0",
        "features": {
            "telegram_bot": "running",
            "yookassa_payments": "enabled",
            "webhook": "/yookassa-webhook"
        }
    })

@app.route('/health')
def health():
    """Проверка здоровья сервиса"""
    return jsonify({"status": "healthy"}), 200

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    logger.info("="*50)
    logger.info("🚀 ЗАПУСК ВАРИАТИКА v2.0 с ПЛАТЕЖАМИ")
    logger.info("="*50)
    
    # Проверяем необходимые переменные
    required_vars = ['TELEGRAM_BOT_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные: {missing}")
    else:
        logger.info("✅ Все необходимые переменные настроены")
    
    # Запускаем Telegram бота в фоновом потоке
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер (принимает webhook от ЮKassa)
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Flask запущен на порту {port}")
    logger.info(f"🔗 Webhook URL: https://ваш-домен.onrender.com/yookassa-webhook")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
