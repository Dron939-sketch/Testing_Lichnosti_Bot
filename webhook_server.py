# webhook_server.py
"""
Flask сервер для получения webhook от ЮKassa
"""

import os
import json
import logging
import hmac
import hashlib
from flask import Flask, request, jsonify
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальный словарь для хранения статусов платежей
payments_status = {}

def verify_yookassa_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Проверяет подпись webhook от ЮKassa
    """
    if not secret:
        logger.warning("⚠️  YOOKASSA_WEBHOOK_SECRET не установлен, пропускаем проверку подписи")
        return True
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@app.route('/')
def home():
    """Главная страница"""
    return jsonify({
        "status": "running",
        "service": "Variatica Bot Webhook Server",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "yookassa_webhook": "/yookassa-webhook (POST)",
            "payment_status": "/payment/<payment_id>"
        }
    })

@app.route('/health')
def health():
    """Health check для Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "payments_processed": len(payments_status)
    }), 200

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """
    Webhook эндпоинт для ЮKassa
    Документация: https://yookassa.ru/developers/api#webhook
    """
    try:
        # Получаем данные
        body = request.get_data()
        signature = request.headers.get('YooKassa-Signature', '')
        
        # Проверяем подпись
        secret = os.getenv('YOOKASSA_WEBHOOK_SECRET', '')
        if not verify_yookassa_signature(body, signature, secret):
            logger.warning("❌ Неверная подпись webhook")
            return jsonify({"error": "Invalid signature"}), 400
        
        # Парсим JSON
        data = request.json
        event = data.get('event', 'unknown')
        payment_id = data.get('object', {}).get('id', 'unknown')
        
        logger.info(f"📦 Webhook от ЮKassa: {event} для payment {payment_id}")
        
        # Обрабатываем события
        if event == 'payment.succeeded':
            # Платеж успешно завершен
            amount = data['object']['amount']
            description = data['object'].get('description', '')
            metadata = data['object'].get('metadata', {})
            
            logger.info(f"✅ Платеж успешен: {payment_id}")
            logger.info(f"💰 Сумма: {amount['value']} {amount['currency']}")
            logger.info(f"📝 Описание: {description}")
            
            # Сохраняем статус
            payments_status[payment_id] = {
                'status': 'succeeded',
                'amount': amount,
                'description': description,
                'metadata': metadata,
                'updated_at': datetime.now().isoformat()
            }
            
            # Здесь можно:
            # 1. Отправить уведомление в Telegram
            # 2. Обновить БД
            # 3. Выдать доступ к продукту
            
        elif event == 'payment.waiting_for_capture':
            # Платеж ожидает подтверждения (для двухстадийных платежей)
            logger.info(f"⏳ Платеж ожидает подтверждения: {payment_id}")
            payments_status[payment_id] = {
                'status': 'waiting_for_capture',
                'updated_at': datetime.now().isoformat()
            }
            
        elif event == 'payment.canceled':
            # Платеж отменен
            logger.info(f"❌ Платеж отменен: {payment_id}")
            payments_status[payment_id] = {
                'status': 'canceled',
                'updated_at': datetime.now().isoformat()
            }
            
        else:
            logger.info(f"📄 Другое событие: {event} для {payment_id}")
        
        # Всегда возвращаем 200 OK
        return jsonify({
            "status": "received",
            "event": event,
            "payment_id": payment_id
        }), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/payment/<payment_id>', methods=['GET'])
def get_payment_status(payment_id):
    """Проверка статуса платежа"""
    if payment_id in payments_status:
        return jsonify(payments_status[payment_id]), 200
    else:
        return jsonify({"error": "Payment not found"}), 404

@app.route('/payments', methods=['GET'])
def list_payments():
    """Список всех обработанных платежей"""
    return jsonify({
        "count": len(payments_status),
        "payments": list(payments_status.keys())
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск webhook сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
