"""
app.py - Flask сервер для обработки webhook от ЮKassa
Запускается как второй сервис на Render
"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from contextlib import contextmanager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)

# Путь к общей базе данных
DB_PATH = "shared_payments.db"

# ============================================
# ОБЩАЯ БАЗА ДАННЫХ (для обмена с Telegram ботом)
# ============================================

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Для доступа по именам колонок
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Инициализация базы данных"""
    logger.info("🗄️ Инициализация базы данных...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица платежей
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
        if result:
            return dict(result)
        return None

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

def create_test_payment():
    """Создает тестовый платеж для проверки (опционально)"""
    test_payment_id = f"test_{int(datetime.now().timestamp())}"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, amount, status, created_at, description)
        VALUES (?, 123456789, 199.0, 'succeeded', ?, 'Тестовый платеж для проверки')
        """, (test_payment_id, datetime.now().isoformat()))
        conn.commit()
    
    logger.info(f"🧪 Создан тестовый платеж: {test_payment_id}")
    return test_payment_id

# ============================================
# WEBHOOK ЭНДПОИНТЫ ДЛЯ ЮKASSA
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """
    Основной endpoint для получения webhook от ЮKassa
    Должен быть указан в настройках кабинета ЮKassa:
    https://ваш-домен.onrender.com/yookassa-webhook
    """
    try:
        # Получаем данные от ЮKassa
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
            
            # Ищем наш внутренний payment_id по yookassa_id
            # Обычно мы сохраняем соответствие при создании платежа в metadata
            payment = find_payment_by_yookassa_id(payment_id)
            
            if payment:
                # Обновляем статус в нашей БД
                update_payment_status(payment['payment_id'], 'succeeded', payment_id)
                logger.info(f"📊 Обновлен статус: {payment['payment_id']} -> succeeded")
            else:
                # Если не нашли, ищем по metadata в объекте платежа
                metadata = webhook_data.get('object', {}).get('metadata', {})
                our_payment_id = metadata.get('our_payment_id')
                
                if our_payment_id:
                    update_payment_status(our_payment_id, 'succeeded', payment_id)
                    logger.info(f"📊 Найден по metadata: {our_payment_id}")
                else:
                    logger.warning(f"⚠️ Не найден наш платеж для yookassa_id: {payment_id}")
        
        elif event == 'payment.waiting_for_capture':
            logger.info(f"⏳ Ожидание подтверждения: {payment_id}")
            # Можно обновить статус на 'waiting_for_capture'
            
        elif event == 'payment.canceled':
            logger.info(f"❌ Платеж отменен: {payment_id}")
            payment = find_payment_by_yookassa_id(payment_id)
            if payment:
                update_payment_status(payment['payment_id'], 'canceled', payment_id)
        
        elif event == 'refund.succeeded':
            logger.info(f"↩️ Успешный возврат для платежа: {payment_id}")
        
        else:
            logger.info(f"📨 Другое событие: {event}")
        
        # Всегда возвращаем 200 OK, чтобы ЮKassa не отправлял повторные запросы
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        logger.exception("Детали ошибки:")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/yookassa-webhook', methods=['GET'])
def yookassa_webhook_verify():
    """Метод для верификации webhook (нужен для некоторых настроек)"""
    return jsonify({
        "status": "webhook_ready",
        "service": "variatica_yookassa_webhook",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/yookassa-webhook (POST)",
            "health": "/health",
            "status": "/status",
            "test": "/test-webhook (POST для тестирования)"
        }
    }), 200

# ============================================
# ТЕСТОВЫЙ ЭНДПОИНТ
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

# ============================================
# HEALTH CHECK И СТАТУС
# ============================================

@app.route('/')
def index():
    """Главная страница - показывает статус сервиса"""
    return jsonify({
        "service": "Variatica YooKassa Webhook Server",
        "version": "2.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/yookassa-webhook (POST)",
            "webhook_verify": "/yookassa-webhook (GET)",
            "health": "/health",
            "status": "/status",
            "test": "/test-webhook (POST)",
            "payments": "/payments (GET)"
        },
        "database": {
            "path": DB_PATH,
            "initialized": os.path.exists(DB_PATH)
        }
    })

@app.route('/health')
def health_check():
    """Health check для Render"""
    return jsonify({
        "status": "healthy",
        "service": "yookassa_webhook",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/status')
def status_check():
    """Проверка статуса сервиса и статистика"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Статистика платежей
            cursor.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
            payments_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Статистика webhook
            cursor.execute("SELECT COUNT(*) FROM yookassa_webhooks")
            webhooks_count = cursor.fetchone()[0]
            
            # Последние webhook
            cursor.execute("""
            SELECT event, payment_id, status, received_at 
            FROM yookassa_webhooks 
            ORDER BY received_at DESC 
            LIMIT 5
            """)
            recent_webhooks = [
                dict(zip(['event', 'payment_id', 'status', 'received_at'], row)) 
                for row in cursor.fetchall()
            ]
        
        return jsonify({
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "payments": payments_stats,
                "webhooks_total": webhooks_count,
                "recent_webhooks": recent_webhooks
            },
            "service_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/payments')
def list_payments():
    """Список платежей (для админки)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT payment_id, yookassa_id, user_id, amount, status, created_at 
            FROM payments 
            ORDER BY created_at DESC 
            LIMIT 50
            """)
            
            payments = []
            for row in cursor.fetchall():
                payments.append({
                    'payment_id': row[0],
                    'yookassa_id': row[1],
                    'user_id': row[2],
                    'amount': row[3],
                    'status': row[4],
                    'created_at': row[5]
                })
        
        return jsonify({
            "count": len(payments),
            "payments": payments
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    # Инициализация базы данных
    init_database()
    
    # Создание тестового платежа (опционально)
    create_test_payment()
    
    # Запуск Flask сервера
    port = int(os.getenv('PORT', 10000))
    
    logger.info("="*50)
    logger.info("🌐 ЗАПУСК FLASK СЕРВЕРА ДЛЯ YOOKASSA WEBHOOK")
    logger.info("="*50)
    logger.info(f"Порт: {port}")
    logger.info(f"База данных: {DB_PATH}")
    logger.info(f"Webhook URL: https://ваш-домен.onrender.com/yookassa-webhook")
    logger.info("="*50)
    
    # Для разработки используем debug, для продакшена - нет
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False  # Отключаем reloader на Render
    )
