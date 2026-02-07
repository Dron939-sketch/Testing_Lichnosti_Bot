"""
app.py - Flask сервер для обработки webhook от ЮKassa и API для бота
ОБНОВЛЕННАЯ ВЕРСИЯ: использует единый database.py
Запускается на Render как: gunicorn app:app
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from database import db  # Используем единую БД

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)
CORS(app)  # Разрешаем CORS для API запросов

# ============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (используем единую БД)
# ============================================

def init_app_database():
    """Инициализация базы данных при запуске приложения"""
    try:
        db.init_database()
        logger.info("✅ База данных приложения инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД приложения: {e}")
        raise

# ============================================
# API ЭНДПОИНТЫ ДЛЯ TELEGRAM БОТА
# ============================================

@app.route('/api/payment-status/<payment_id>', methods=['GET'])
def api_payment_status(payment_id):
    """
    GET /api/payment-status/<payment_id>
    Возвращает статус платежа для Telegram бота
    """
    try:
        # Ищем платеж по нашему payment_id
        payment = db.get_payment_by_id(payment_id)
        
        # Если не нашли, пробуем поискать как yookassa_id
        if not payment:
            payment = db.get_payment_by_yookassa_id(payment_id)
        
        if payment:
            return jsonify({
                "found": True,
                "payment_id": payment.get('payment_id'),
                "yookassa_id": payment.get('yookassa_id'),
                "user_id": payment.get('user_id'),
                "status": payment.get('status'),
                "amount": float(payment.get('amount', 0)) if payment.get('amount') else 0,
                "email": payment.get('email', ''),
                "created_at": payment.get('created_at'),
                "updated_at": payment.get('updated_at')
            }), 200
        
        # Если платеж не найден
        return jsonify({
            "found": False,
            "message": "Payment not found",
            "payment_id": payment_id
        }), 404
        
    except Exception as e:
        logger.error(f"❌ API error: {e}")
        return jsonify({
            "found": False,
            "error": str(e),
            "payment_id": payment_id
        }), 500

@app.route('/api/create-payment', methods=['POST'])
def api_create_payment():
    """
    POST /api/create-payment
    Создает новую запись о платеже в БД
    Telegram бот вызывает этот endpoint при начале оплаты
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data"}), 400
        
        # Обязательные поля
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        if not payment_id or not user_id:
            return jsonify({
                "success": False, 
                "error": "Missing required fields: payment_id, user_id"
            }), 400
        
        # Дополнительные поля
        amount = data.get('amount', 690.00)
        email = data.get('email', '')
        description = data.get('description', 'Полный пакет ВАРИАТИКА')
        yookassa_id = data.get('yookassa_id')
        
        payment_data = {
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'email': email,
            'description': description,
            'yookassa_id': yookassa_id,
            'metadata': json.dumps({
                'created_via': 'api_create_payment',
                'timestamp': datetime.now().isoformat()
            })
        }
        
        if db.create_payment(payment_data):
            return jsonify({
                "success": True,
                "message": "Payment record created",
                "payment_id": payment_id,
                "status": "pending"
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create payment record"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ API create error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-yookassa-id', methods=['POST'])
def api_update_yookassa_id():
    """
    POST /api/update-yookassa-id
    Обновляет yookassa_id для существующего платежа
    Бот вызывает после успешного создания платежа в ЮKassa
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data"}), 400
        
        payment_id = data.get('payment_id')
        yookassa_id = data.get('yookassa_id')
        
        if not payment_id or not yookassa_id:
            return jsonify({
                "success": False, 
                "error": "Missing required fields: payment_id, yookassa_id"
            }), 400
        
        if db.update_payment_status(payment_id, 'pending', yookassa_id):
            return jsonify({
                "success": True,
                "message": "Yookassa ID updated",
                "payment_id": payment_id,
                "yookassa_id": yookassa_id
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update payment"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ API update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user-payments/<int:user_id>', methods=['GET'])
def api_user_payments(user_id):
    """
    GET /api/user-payments/<user_id>
    Возвращает все платежи пользователя
    """
    try:
        payments = []
        
        # Используем низкоуровневый доступ для сложных запросов
        with db.db_cursor() as cursor:
            if db.is_postgres:
                cursor.execute("""
                SELECT payment_id, yookassa_id, amount, status, created_at, description, email
                FROM payments 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                SELECT payment_id, yookassa_id, amount, status, created_at, description, email
                FROM payments 
                WHERE user_id = ? 
                ORDER BY created_at DESC
                """, (user_id,))
            
            rows = cursor.fetchall()
            for row in rows:
                if isinstance(row, dict):
                    payments.append({
                        'payment_id': row.get('payment_id'),
                        'yookassa_id': row.get('yookassa_id'),
                        'amount': float(row.get('amount', 0)) if row.get('amount') else 0,
                        'status': row.get('status'),
                        'created_at': row.get('created_at'),
                        'description': row.get('description'),
                        'email': row.get('email', '')
                    })
                else:
                    columns = [desc[0] for desc in cursor.description]
                    row_dict = dict(zip(columns, row))
                    payments.append({
                        'payment_id': row_dict.get('payment_id'),
                        'yookassa_id': row_dict.get('yookassa_id'),
                        'amount': float(row_dict.get('amount', 0)) if row_dict.get('amount') else 0,
                        'status': row_dict.get('status'),
                        'created_at': row_dict.get('created_at'),
                        'description': row_dict.get('description'),
                        'email': row_dict.get('email', '')
                    })
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "count": len(payments),
            "payments": payments
        }), 200
        
    except Exception as e:
        logger.error(f"❌ API user payments error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/grant-access', methods=['POST'])
def api_grant_access():
    """
    POST /api/grant-access
    Отмечает, что доступ пользователю предоставлен
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data"}), 400
        
        user_id = data.get('user_id')
        payment_id = data.get('payment_id')
        files_sent = data.get('files_sent')
        
        if not user_id or not payment_id:
            return jsonify({
                "success": False, 
                "error": "Missing required fields: user_id, payment_id"
            }), 400
        
        if db.mark_access_granted(user_id, payment_id, files_sent):
            return jsonify({
                "success": True,
                "message": "Access granted",
                "user_id": user_id,
                "payment_id": payment_id
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to grant access"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ API grant access error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/check-access/<int:user_id>', methods=['GET'])
def api_check_access(user_id):
    """
    GET /api/check-access/<user_id>
    Проверяет, есть ли у пользователя доступ
    """
    try:
        has_access = db.user_has_access(user_id)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "has_access": has_access
        }), 200
        
    except Exception as e:
        logger.error(f"❌ API check access error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# WEBHOOK ЭНДПОИНТЫ ДЛЯ ЮKASSA
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """
    Основной endpoint для получения webhook от ЮKassa
    Должен быть указан в настройках кабинета ЮKassa
    """
    try:
        # Проверяем JSON
        if not request.is_json:
            logger.warning("⚠️ Получен не JSON запрос от ЮKassa")
            return jsonify({"status": "error", "message": "Expected JSON"}), 400
        
        webhook_data = request.get_json()
        
        # Сохраняем уведомление в БД
        db.save_webhook_notification(webhook_data)
        
        # Логируем основные данные
        event = webhook_data.get('event', 'unknown')
        yookassa_id = webhook_data.get('object', {}).get('id', 'unknown')
        status = webhook_data.get('object', {}).get('status', 'unknown')
        
        logger.info(f"💰 Получен webhook: {event} | Платеж: {yookassa_id} | Статус: {status}")
        
        # Обрабатываем события платежа
        if event == 'payment.succeeded':
            logger.info(f"✅ Успешный платеж: {yookassa_id}")
            
            # Находим наш внутренний платеж
            payment = db.get_payment_by_yookassa_id(yookassa_id)
            
            if payment:
                # Обновляем статус
                db.update_payment_status(payment['payment_id'], 'succeeded', yookassa_id)
                logger.info(f"📊 Обновлен статус: {payment['payment_id']} -> succeeded")
                
                # Также обновляем в таблице deliveries для совместимости
                with db.db_cursor() as cursor:
                    if db.is_postgres:
                        cursor.execute("""
                        INSERT INTO deliveries (payment_id, user_id, files_sent)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (payment_id) DO NOTHING
                        """, (payment['payment_id'], payment['user_id'], '[]'))
                    else:
                        cursor.execute("""
                        INSERT OR IGNORE INTO deliveries (payment_id, user_id, files_sent)
                        VALUES (?, ?, ?)
                        """, (payment['payment_id'], payment['user_id'], '[]'))
                
            else:
                # Пробуем найти в metadata
                metadata = webhook_data.get('object', {}).get('metadata', {})
                our_payment_id = metadata.get('our_payment_id') or metadata.get('payment_id')
                
                if our_payment_id:
                    db.update_payment_status(our_payment_id, 'succeeded', yookassa_id)
                    logger.info(f"📊 Найден по metadata: {our_payment_id}")
                else:
                    logger.warning(f"⚠️ Не найден наш платеж для yookassa_id: {yookassa_id}")
                    
                    # Создаем новую запись если нет
                    user_id = metadata.get('user_id')
                    if user_id:
                        payment_data = {
                            'payment_id': f"auto_{yookassa_id}",
                            'user_id': user_id,
                            'amount': webhook_data.get('object', {}).get('amount', {}).get('value', 690.00),
                            'description': 'Автоматически созданный платеж',
                            'yookassa_id': yookassa_id,
                            'status': 'succeeded',
                            'metadata': json.dumps(metadata)
                        }
                        db.create_payment(payment_data)
                        logger.info(f"📝 Автосоздан платеж для yookassa_id: {yookassa_id}")
        
        elif event == 'payment.waiting_for_capture':
            logger.info(f"⏳ Ожидание подтверждения: {yookassa_id}")
            payment = db.get_payment_by_yookassa_id(yookassa_id)
            if payment:
                db.update_payment_status(payment['payment_id'], 'waiting_for_capture', yookassa_id)
        
        elif event == 'payment.canceled':
            logger.info(f"❌ Платеж отменен: {yookassa_id}")
            payment = db.get_payment_by_yookassa_id(yookassa_id)
            if payment:
                db.update_payment_status(payment['payment_id'], 'canceled', yookassa_id)
        
        elif event == 'refund.succeeded':
            logger.info(f"↩️ Успешный возврат для платежа: {yookassa_id}")
        
        else:
            logger.info(f"📨 Другое событие: {event}")
        
        # Всегда возвращаем 200 OK
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/yookassa-webhook', methods=['GET'])
def yookassa_webhook_verify():
    """Метод для верификации webhook"""
    return jsonify({
        "status": "webhook_ready",
        "service": "variatica_yookassa_webhook",
        "timestamp": datetime.now().isoformat(),
        "message": "Webhook endpoint is ready to receive notifications"
    }), 200

# ============================================
# ТЕСТОВЫЕ И ВСПОМОГАТЕЛЬНЫЕ ЭНДПОИНТЫ
# ============================================

@app.route('/test-webhook', methods=['POST'])
def test_webhook():
    """Тестовый endpoint для имитации webhook от ЮKassa"""
    try:
        test_data = request.get_json() or {
            "event": "payment.succeeded",
            "object": {
                "id": f"test_{int(datetime.now().timestamp())}",
                "status": "succeeded",
                "amount": {"value": "690.00", "currency": "RUB"},
                "metadata": {
                    "user_id": 123456789,
                    "payment_id": "test_payment_123",
                    "our_payment_id": "test_payment_123"
                }
            }
        }
        
        # Сохраняем тестовый webhook
        db.save_webhook_notification(test_data)
        
        # Имитируем обработку
        yookassa_id = test_data.get('object', {}).get('id')
        metadata = test_data.get('object', {}).get('metadata', {})
        our_payment_id = metadata.get('our_payment_id')
        
        if our_payment_id:
            db.update_payment_status(our_payment_id, 'succeeded', yookassa_id)
        
        logger.info(f"🧪 Тестовый webhook обработан: {test_data.get('event')}")
        
        return jsonify({
            "status": "test_ok",
            "message": "Тестовый webhook обработан",
            "data": test_data
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test-api', methods=['GET'])
def test_api():
    """Тестовый endpoint для проверки API"""
    return jsonify({
        "status": "ok",
        "service": "Variatica API",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "payment_status": "/api/payment-status/<payment_id>",
            "create_payment": "/api/create-payment",
            "update_yookassa": "/api/update-yookassa-id",
            "user_payments": "/api/user-payments/<user_id>",
            "grant_access": "/api/grant-access",
            "check_access": "/api/check-access/<user_id>",
            "webhook": "/yookassa-webhook"
        }
    }), 200

# ============================================
# HEALTH CHECK И СТАТУС
# ============================================

@app.route('/')
def index():
    """Главная страница - показывает статус сервиса"""
    db_type = "PostgreSQL" if db.is_postgres else "SQLite"
    
    return jsonify({
        "service": "Variatica YooKassa Webhook & API Server",
        "version": "4.0",
        "status": "running",
        "database": db_type,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/yookassa-webhook (POST)",
            "webhook_verify": "/yookassa-webhook (GET)",
            "health": "/health",
            "status": "/status",
            "test": "/test-webhook (POST)",
            "test_api": "/test-api (GET)",
            "api": {
                "payment_status": "/api/payment-status/<payment_id> (GET)",
                "create_payment": "/api/create-payment (POST)",
                "update_yookassa": "/api/update-yookassa-id (POST)",
                "user_payments": "/api/user-payments/<user_id> (GET)",
                "grant_access": "/api/grant-access (POST)",
                "check_access": "/api/check-access/<user_id> (GET)"
            }
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check для Render и мониторинга"""
    try:
        # Проверяем подключение к БД
        with db.db_cursor() as cursor:
            if db.is_postgres:
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1")
            db_ok = cursor.fetchone() is not None
        
        return jsonify({
            "status": "healthy",
            "service": "variatica_webhook_api",
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "variatica_webhook_api",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def status_check():
    """Детальный статус сервиса и статистика"""
    try:
        stats = {}
        
        with db.db_cursor() as cursor:
            # Статистика платежей
            cursor.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
            rows = cursor.fetchall()
            
            payments_stats = {}
            for row in rows:
                if isinstance(row, dict):
                    payments_stats[row['status']] = row['count']
                else:
                    payments_stats[row[0]] = row[1]
            
            # Статистика webhook
            cursor.execute("SELECT COUNT(*) FROM yookassa_webhooks")
            webhooks_result = cursor.fetchone()
            webhooks_count = webhooks_result[0] if webhooks_result else 0
            
            # Количество пользователей
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM payments")
            users_result = cursor.fetchone()
            users_count = users_result[0] if users_result else 0
            
            # Количество предоставленных доступов
            cursor.execute("SELECT COUNT(*) FROM user_access WHERE has_access = TRUE")
            access_result = cursor.fetchone()
            access_count = access_result[0] if access_result else 0
        
        db_type = "PostgreSQL" if db.is_postgres else "SQLite"
        
        return jsonify({
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "database": db_type,
            "statistics": {
                "payments": payments_stats,
                "webhooks_total": webhooks_count,
                "unique_users": users_count,
                "access_granted": access_count
            },
            "service_info": {
                "python_version": sys.version.split()[0],
                "flask_version": "2.3.2"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    # Инициализация базы данных
    init_app_database()
    
    # Запуск Flask сервера
    port = int(os.getenv('PORT', 10000))
    
    logger.info("="*60)
    logger.info("🚀 ЗАПУСК VARIATICA FLASK SERVER v4.0")
    logger.info("="*60)
    logger.info(f"Порт: {port}")
    logger.info(f"База данных: {'PostgreSQL' if db.is_postgres else 'SQLite'}")
    logger.info("="*60)
    logger.info("📡 Основные endpoints:")
    logger.info("  /yookassa-webhook    - Webhook от ЮKassa")
    logger.info("  /api/payment-status  - Статус платежа для бота")
    logger.info("  /api/create-payment  - Создание платежа")
    logger.info("  /health              - Health check для Render")
    logger.info("="*60)
    
    # Для разработки используем debug, для продакшена - нет
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False
    )
