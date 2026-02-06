"""
app.py - Flask сервер для обработки webhook от ЮKassa и API для бота
Запускается на Render как второй сервис: gunicorn app:app
"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from contextlib import contextmanager
from dotenv import load_dotenv

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

# Путь к общей базе данных
DB_PATH = "shared_payments.db"

# ============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к SQLite БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Инициализация базы данных с таблицами"""
    logger.info("🗄️ Инициализация базы данных...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица платежей (основная)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT UNIQUE NOT NULL,           -- наш внутренний ID
            yookassa_id TEXT,                          -- ID платежа в ЮKassa
            user_id INTEGER NOT NULL,                  -- ID пользователя Telegram
            amount REAL NOT NULL DEFAULT 199.0,
            status TEXT NOT NULL DEFAULT 'pending',    -- pending, succeeded, canceled, waiting_for_capture
            email TEXT,
            description TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP,
            metadata TEXT                              -- Дополнительные данные в JSON
        )
        """)
        
        # Таблица уведомлений от ЮKassa
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yookassa_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            webhook_id TEXT NOT NULL,
            event TEXT NOT NULL,
            payment_id TEXT NOT NULL,
            status TEXT NOT NULL,
            received_at TIMESTAMP NOT NULL,
            payload TEXT NOT NULL                       -- Полный JSON от ЮKassa
        )
        """)
        
        # Таблица доставленных файлов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            delivered_at TIMESTAMP NOT NULL,
            files_sent TEXT,                           -- JSON список отправленных файлов
            FOREIGN KEY (payment_id) REFERENCES payments (payment_id)
        )
        """)
        
        conn.commit()
    
    logger.info("✅ База данных инициализирована")

def find_payment_by_yookassa_id(yookassa_id: str):
    """Находит платеж по ID из ЮKassa"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM payments WHERE yookassa_id = ? OR payment_id = ?", 
            (yookassa_id, yookassa_id)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

def update_payment_status(payment_id: str, status: str, yookassa_id: str = None):
    """Обновляет статус платежа"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if yookassa_id:
            cursor.execute("""
            UPDATE payments 
            SET status = ?, updated_at = ?, yookassa_id = ?
            WHERE payment_id = ?
            """, (status, datetime.now().isoformat(), yookassa_id, payment_id))
        else:
            cursor.execute("""
            UPDATE payments 
            SET status = ?, updated_at = ?
            WHERE payment_id = ?
            """, (status, datetime.now().isoformat(), payment_id))
        
        conn.commit()
    
    logger.info(f"📊 Обновлен статус платежа {payment_id}: {status}")
    return True

def save_webhook_notification(webhook_data: dict):
    """Сохраняет уведомление от ЮKassa в БД"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        event = webhook_data.get('event', 'unknown')
        payment_id = webhook_data.get('object', {}).get('id', 'unknown')
        status = webhook_data.get('object', {}).get('status', 'unknown')
        webhook_id = webhook_data.get('id', f"webhook_{datetime.now().timestamp()}")
        
        cursor.execute("""
        INSERT INTO yookassa_webhooks 
        (webhook_id, event, payment_id, status, received_at, payload)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            webhook_id,
            event,
            payment_id,
            status,
            datetime.now().isoformat(),
            json.dumps(webhook_data, ensure_ascii=False)
        ))
        
        conn.commit()
    
    logger.info(f"📨 Сохранено webhook уведомление: {event} для {payment_id}")
    return True

def create_payment_record(payment_data: dict):
    """Создает новую запись о платеже в БД"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            payment_id = payment_data.get('payment_id')
            user_id = payment_data.get('user_id')
            amount = payment_data.get('amount', 199.0)
            email = payment_data.get('email', '')
            description = payment_data.get('description', 'Оплата подписки')
            yookassa_id = payment_data.get('yookassa_id')
            
            cursor.execute("""
            INSERT INTO payments 
            (payment_id, user_id, amount, email, description, created_at, status, yookassa_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(payment_id) DO UPDATE SET
                updated_at = ?,
                yookassa_id = ?
            """, (
                payment_id,
                user_id,
                amount,
                email,
                description,
                datetime.now().isoformat(),
                'pending',
                yookassa_id,
                datetime.now().isoformat(),
                yookassa_id
            ))
            
            conn.commit()
        
        logger.info(f"📝 Создана запись платежа: {payment_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return False

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
        payment = find_payment_by_yookassa_id(payment_id)
        
        if payment:
            return jsonify({
                "found": True,
                "payment_id": payment['payment_id'],
                "yookassa_id": payment.get('yookassa_id'),
                "user_id": payment['user_id'],
                "status": payment['status'],
                "amount": payment['amount'],
                "email": payment.get('email', ''),
                "created_at": payment['created_at'],
                "updated_at": payment.get('updated_at')
            }), 200
        else:
            # Пробуем найти по нашему внутреннему payment_id
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
                result = cursor.fetchone()
                
                if result:
                    payment = dict(result)
                    return jsonify({
                        "found": True,
                        "payment_id": payment['payment_id'],
                        "yookassa_id": payment.get('yookassa_id'),
                        "user_id": payment['user_id'],
                        "status": payment['status'],
                        "amount": payment['amount'],
                        "email": payment.get('email', ''),
                        "created_at": payment['created_at'],
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
        amount = data.get('amount', 199.00)
        email = data.get('email', '')
        description = data.get('description', 'Оплата подписки')
        yookassa_id = data.get('yookassa_id')
        
        payment_data = {
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'email': email,
            'description': description,
            'yookassa_id': yookassa_id
        }
        
        if create_payment_record(payment_data):
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
        
        if update_payment_status(payment_id, 'pending', yookassa_id):
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
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT payment_id, yookassa_id, amount, status, created_at, description
            FROM payments 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            """, (user_id,))
            
            payments = []
            for row in cursor.fetchall():
                payments.append({
                    'payment_id': row[0],
                    'yookassa_id': row[1],
                    'amount': row[2],
                    'status': row[3],
                    'created_at': row[4],
                    'description': row[5]
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
        save_webhook_notification(webhook_data)
        
        # Логируем основные данные
        event = webhook_data.get('event', 'unknown')
        payment_id = webhook_data.get('object', {}).get('id', 'unknown')
        status = webhook_data.get('object', {}).get('status', 'unknown')
        
        logger.info(f"💰 Получен webhook: {event} | Платеж: {payment_id} | Статус: {status}")
        
        # Обрабатываем события платежа
        if event == 'payment.succeeded':
            logger.info(f"✅ Успешный платеж: {payment_id}")
            
            # Находим наш внутренний платеж
            payment = find_payment_by_yookassa_id(payment_id)
            
            if payment:
                # Обновляем статус
                update_payment_status(payment['payment_id'], 'succeeded', payment_id)
                logger.info(f"📊 Обновлен статус: {payment['payment_id']} -> succeeded")
                
                # Можно здесь вызвать функцию доставки файлов
                # deliver_files_to_user(payment['user_id'])
                
            else:
                # Пробуем найти в metadata
                metadata = webhook_data.get('object', {}).get('metadata', {})
                our_payment_id = metadata.get('our_payment_id')
                
                if our_payment_id:
                    update_payment_status(our_payment_id, 'succeeded', payment_id)
                    logger.info(f"📊 Найден по metadata: {our_payment_id}")
                else:
                    logger.warning(f"⚠️ Не найден наш платеж для yookassa_id: {payment_id}")
        
        elif event == 'payment.waiting_for_capture':
            logger.info(f"⏳ Ожидание подтверждения: {payment_id}")
            payment = find_payment_by_yookassa_id(payment_id)
            if payment:
                update_payment_status(payment['payment_id'], 'waiting_for_capture', payment_id)
        
        elif event == 'payment.canceled':
            logger.info(f"❌ Платеж отменен: {payment_id}")
            payment = find_payment_by_yookassa_id(payment_id)
            if payment:
                update_payment_status(payment['payment_id'], 'canceled', payment_id)
        
        elif event == 'refund.succeeded':
            logger.info(f"↩️ Успешный возврат для платежа: {payment_id}")
        
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
                "amount": {"value": "199.00", "currency": "RUB"},
                "metadata": {"our_payment_id": "test_payment_123"}
            }
        }
        
        # Сохраняем тестовый webhook
        save_webhook_notification(test_data)
        
        logger.info(f"🧪 Тестовый webhook получен: {test_data.get('event')}")
        
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
            "webhook": "/yookassa-webhook"
        }
    }), 200

# ============================================
# HEALTH CHECK И СТАТУС
# ============================================

@app.route('/')
def index():
    """Главная страница - показывает статус сервиса"""
    return jsonify({
        "service": "Variatica YooKassa Webhook & API Server",
        "version": "2.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/yookassa-webhook (POST)",
            "webhook_verify": "/yookassa-webhook (GET)",
            "health": "/health",
            "status": "/status",
            "test": "/test-webhook (POST)",
            "test_api": "/test-api (GET)",
            "payments": "/payments (GET)",
            "api": {
                "payment_status": "/api/payment-status/<payment_id> (GET)",
                "create_payment": "/api/create-payment (POST)",
                "update_yookassa": "/api/update-yookassa-id (POST)",
                "user_payments": "/api/user-payments/<user_id> (GET)"
            }
        },
        "database": {
            "path": DB_PATH,
            "initialized": os.path.exists(DB_PATH)
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check для Render и мониторинга"""
    try:
        # Проверяем подключение к БД
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            db_ok = cursor.fetchone() is not None
        
        return jsonify({
            "status": "healthy",
            "service": "yookassa_webhook_api",
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "yookassa_webhook_api",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def status_check():
    """Детальный статус сервиса и статистика"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Статистика платежей
            cursor.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
            payments_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Статистика webhook
            cursor.execute("SELECT COUNT(*) FROM yookassa_webhooks")
            webhooks_count = cursor.fetchone()[0]
            
            # Количество пользователей
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM payments")
            users_count = cursor.fetchone()[0]
        
        return jsonify({
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "payments": payments_stats,
                "webhooks_total": webhooks_count,
                "unique_users": users_count
            },
            "service_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "database_path": DB_PATH
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/payments', methods=['GET'])
def list_payments():
    """Список платежей (для админки)"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT payment_id, yookassa_id, user_id, amount, status, created_at, description 
            FROM payments 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
            """, (limit, offset))
            
            payments = []
            for row in cursor.fetchall():
                payments.append({
                    'payment_id': row[0],
                    'yookassa_id': row[1],
                    'user_id': row[2],
                    'amount': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'description': row[6]
                })
            
            # Общее количество
            cursor.execute("SELECT COUNT(*) FROM payments")
            total = cursor.fetchone()[0]
        
        return jsonify({
            "success": True,
            "count": len(payments),
            "total": total,
            "limit": limit,
            "offset": offset,
            "payments": payments
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    # Инициализация базы данных
    init_database()
    
    # Запуск Flask сервера
    port = int(os.getenv('PORT', 10001))  # Render использует 10001 для второго сервиса
    
    logger.info("="*60)
    logger.info("🚀 ЗАПУСК VARIATICA FLASK SERVER")
    logger.info("="*60)
    logger.info(f"Порт: {port}")
    logger.info(f"База данных: {DB_PATH}")
    logger.info(f"Webhook URL: https://variatica-webhook-server.onrender.com/yookassa-webhook")
    logger.info(f"API URL: https://variatica-webhook-server.onrender.com/api/")
    logger.info("="*60)
    logger.info("📡 Доступные endpoints:")
    logger.info("  /                    - Главная страница")
    logger.info("  /health              - Health check")
    logger.info("  /status              - Статус и статистика")
    logger.info("  /yookassa-webhook    - Webhook от ЮKassa")
    logger.info("  /api/payment-status  - API для бота")
    logger.info("  /api/create-payment  - API для создания платежей")
    logger.info("="*60)
    
    # Для разработки используем debug, для продакшена - нет
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False  # Отключаем reloader на Render
    )
