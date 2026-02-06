"""
Основной файл приложения для Render
"""

import os
import logging
from threading import Thread
from flask import Flask, request, jsonify
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Variatica Bot</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🤖 Variatica Bot</h1>
        <p>Бот психодиагностического теста ВАРИАТИКА</p>
        <p class="status">✅ Сервер работает</p>
        <p>Telegram: <a href="https://t.me/variatica_bot">@variatica_bot</a></p>
    </body>
    </html>
    '''

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """
    Обработчик webhook от ЮKassa
    """
    try:
        # Получаем данные из запроса
        data = request.get_json(silent=True)
        
        if not data:
            logger.error("❌ Webhook: Нет данных в запросе")
            return jsonify({'success': False, 'error': 'No data'}), 400
        
        # Логируем полученные данные
        logger.info("🔄 Webhook получен от ЮKassa")
        
        # Извлекаем информацию
        event = data.get('event')
        payment_data = data.get('object', {})
        
        payment_id = payment_data.get('id', 'N/A')[:8]
        logger.info(f"📋 Событие: {event}, Payment ID: {payment_id}...")
        logger.info(f"📋 Статус: {payment_data.get('status')}")
        
        # Проверяем событие
        if event == 'payment.succeeded':
            metadata = payment_data.get('metadata', {})
            user_id = metadata.get('user_id')
            
            if not user_id:
                logger.error("❌ Webhook: Не найден user_id в metadata")
                return jsonify({'success': False, 'error': 'No user_id'}), 400
            
            logger.info(f"✅ Платеж успешен! User ID: {user_id}")
            
            # Запись в лог файл
            with open('payments.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} | SUCCESS | User: {user_id} | Payment: {payment_data.get('id')} | Amount: {payment_data.get('amount', {}).get('value')} RUB\n")
        
        elif event == 'payment.canceled':
            logger.info(f"❌ Платеж отменен: {payment_id}...")
        
        elif event == 'payment.waiting_for_capture':
            logger.info(f"⏳ Платеж ожидает захвата: {payment_id}...")
        
        else:
            logger.info(f"ℹ️  Необрабатываемое событие: {event}")
        
        # ВСЕГДА возвращаем 200 OK
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"🔥 Критическая ошибка обработки webhook: {e}")
        import traceback
        logger.error(f"📋 Трассировка:\n{traceback.format_exc()}")
        
        # ВСЕГДА возвращаем 200, чтобы ЮKassa не повторял запросы
        return jsonify({'success': False, 'error': str(e)}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервера"""
    return jsonify({
        'status': 'healthy',
        'service': 'variatica-bot',
        'timestamp': datetime.now().isoformat()
    }), 200

def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    try:
        # Импорт должен быть внутри функции
        from bot_adaptive import main as run_bot
        
        logger.info("🤖 Запускаю Telegram бота...")
        run_bot()
        
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")
        import traceback
        logger.error(f"📋 Трассировка:\n{traceback.format_exc()}")

if __name__ == "__main__":
    # Запускаем Telegram бот в отдельном потоке
    bot_thread = Thread(target=run_telegram_bot, daemon=True, name="telegram-bot-thread")
    bot_thread.start()
    
    # Запускаем Flask (основной поток для Render)
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🌐 Запускаю Flask сервер на порту {port}")
    logger.info(f"🔗 Webhook URL: https://testing-lichnosti-bot-qyra.onrender.com/yookassa-webhook")
    
    app.run(host='0.0.0.0', port=port, debug=False)
