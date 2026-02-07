"""
app.py - Полный Flask API для платежной системы
Версия с исправленной структурой таблиц и ВСЕМИ эндпоинтами
"""

import os
import sys
import json
import logging
import hashlib
import hmac
from datetime import datetime
from decimal import Decimal
from flask import Flask, request, jsonify
from flask_cors import CORS

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Проверяем наличие psycopg3
try:
    import psycopg
    POSTGRES_AVAILABLE = True
    logger.info("✅ psycopg3 (версия 3.x) доступна")
except ImportError as e:
    POSTGRES_AVAILABLE = False
    logger.error(f"❌ psycopg3 не установлен: {e}")

# Создание Flask приложения
app = Flask(__name__)
CORS(app)

# Конфигурация для вебхуков
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ============================================

def get_db_connection():
    """Подключение к PostgreSQL через psycopg3"""
    if not POSTGRES_AVAILABLE:
        raise ImportError("psycopg3 не установлен")
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL не настроен в Render!")
    
    # Исправляем URL для Render
    if '.render.com' in DATABASE_URL and ':5432' not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('.render.com/', '.render.com:5432/')
    
    if 'sslmode=' not in DATABASE_URL:
        if '?' in DATABASE_URL:
            DATABASE_URL += '&sslmode=require'
        else:
            DATABASE_URL += '?sslmode=require'
    
    logger.info(f"🔗 Подключение к PostgreSQL через psycopg3...")
    return psycopg.connect(DATABASE_URL)

def create_payments_table():
    """Создает таблицу payments с правильной структурой"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Удаляем старую таблицу если есть
        cursor.execute("DROP TABLE IF EXISTS payments CASCADE")
        logger.info("🗑️ Старая таблица payments удалена")
        
        # Создаем новую таблицу с ВСЕМИ полями
        cursor.execute("""
        CREATE TABLE payments (
            id SERIAL PRIMARY KEY,
            payment_id VARCHAR(100) UNIQUE NOT NULL,
            yookassa_id VARCHAR(100),
            user_id BIGINT NOT NULL,
            amount DECIMAL(10,2) DEFAULT 690.00,
            status VARCHAR(50) DEFAULT 'pending',
            email VARCHAR(255),
            description TEXT DEFAULT 'Полный пакет ВАРИАТИКА',
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP
        )
        """)
        
        # Создаем индексы
        cursor.execute("CREATE INDEX idx_payments_payment_id ON payments(payment_id)")
        cursor.execute("CREATE INDEX idx_payments_user_id ON payments(user_id)")
        cursor.execute("CREATE INDEX idx_payments_status ON payments(status)")
        cursor.execute("CREATE INDEX idx_payments_yookassa_id ON payments(yookassa_id)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'payments' создана с правильной структурой")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы payments: {e}")
        return False

def create_user_access_table():
    """Создает таблицу для доступа пользователей"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS user_access CASCADE")
        
        cursor.execute("""
        CREATE TABLE user_access (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(100),
            has_access BOOLEAN DEFAULT FALSE,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            files_sent TEXT DEFAULT '[]',
            UNIQUE(user_id, payment_id)
        )
        """)
        
        cursor.execute("CREATE INDEX idx_user_access_user_id ON user_access(user_id)")
        cursor.execute("CREATE INDEX idx_user_access_has_access ON user_access(has_access)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'user_access' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы user_access: {e}")
        return False

def create_yookassa_webhooks_table():
    """Создает таблицу для логов вебхуков"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS yookassa_webhooks CASCADE")
        
        cursor.execute("""
        CREATE TABLE yookassa_webhooks (
            id SERIAL PRIMARY KEY,
            webhook_id VARCHAR(255) NOT NULL,
            event VARCHAR(100) NOT NULL,
            payment_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payload TEXT,
            processed BOOLEAN DEFAULT FALSE
        )
        """)
        
        cursor.execute("CREATE INDEX idx_webhooks_payment_id ON yookassa_webhooks(payment_id)")
        cursor.execute("CREATE INDEX idx_webhooks_event ON yookassa_webhooks(event)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'yookassa_webhooks' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы webhooks: {e}")
        return False

def create_all_tables():
    """Создает все таблицы с нуля"""
    logger.info("🗄️ Создание всех таблиц базы данных...")
    
    results = {
        "payments": create_payments_table(),
        "user_access": create_user_access_table(),
        "yookassa_webhooks": create_yookassa_webhooks_table()
    }
    
    success_count = sum(1 for result in results.values() if result)
    
    if success_count == len(results):
        logger.info("✅ Все таблицы созданы успешно")
        return True
    else:
        logger.error(f"❌ Создано только {success_count}/{len(results)} таблиц")
        return False

def check_table_structure():
    """Проверяет структуру таблицы payments"""
    if not POSTGRES_AVAILABLE:
        return {"error": "psycopg3 не доступен"}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'payments'
        ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "table_exists": len(columns) > 0,
            "columns": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns],
            "column_count": len(columns)
        }
        
    except Exception as e:
        return {"error": str(e)}

# ============================================
# API ЭНДПОИНТЫ (НОВЫЕ - ДОБАВЛЯЕМ)
# ============================================

@app.route('/')
def home():
    """Главная страница"""
    db_status = "✅ psycopg3 доступен" if POSTGRES_AVAILABLE else "❌ Проблема с psycopg3"
    
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "Payment System v2.0",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_payment": "/api/create-payment (POST)",
            "update_yookassa_id": "/api/update-yookassa-id (POST)",
            "payment_status": "/api/payment-status/<payment_id> (GET)",
            "user_payments": "/api/user-payments/<user_id> (GET)",
            "yookassa_webhook": "/yookassa-webhook (POST)",
            "grant_access": "/api/grant-access/<payment_id> (POST)",
            "check_access": "/api/check-access/<user_id> (GET)",
            "admin": "/drop-and-recreate (GET) - для пересоздания таблиц"
        }
    })

# ============================================
# 1. ЭНДПОИНТЫ ДЛЯ ПЛАТЕЖЕЙ
# ============================================

@app.route('/api/create-payment', methods=['POST'])
def api_create_payment():
    """Создает платеж"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data"}), 400
        
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        if not payment_id:
            return jsonify({"success": False, "error": "Missing payment_id"}), 400
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"}), 400
        
        amount = float(data.get('amount', 690.0))
        email = data.get('email', f'user_{user_id}@telegram.org')
        description = data.get('description', 'Полный пакет ВАРИАТИКА')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, amount, email, description, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        ON CONFLICT (payment_id) DO UPDATE SET
            amount = EXCLUDED.amount,
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
        RETURNING payment_id, status, created_at, amount
        """, (payment_id, user_id, amount, email, description))
        
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Платеж создан: {payment_id} для пользователя {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment created",
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": float(result[3]) if result and result[3] else amount,
            "status": result[1] if result else "pending",
            "created_at": result[2].isoformat() if result and result[2] else datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/api/update-yookassa-id', methods=['POST'])
def api_update_yookassa_id():
    """Обновляет ID платежа ЮKassa"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        yookassa_id = data.get('yookassa_id')
        
        if not payment_id or not yookassa_id:
            return jsonify({"success": False, "error": "Missing payment_id or yookassa_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE payments 
        SET yookassa_id = %s, status = 'waiting', updated_at = CURRENT_TIMESTAMP
        WHERE payment_id = %s
        RETURNING payment_id, status, yookassa_id, user_id
        """, (yookassa_id, payment_id))
        
        result = cursor.fetchone()
        
        if not result:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Payment not found"}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ ЮKassa ID обновлен: {payment_id} -> {yookassa_id}")
        
        return jsonify({
            "success": True,
            "message": "Yookassa ID updated",
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "status": "waiting",
            "user_id": result[3]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления ЮKassa ID: {e}")
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}"
        }), 500

@app.route('/api/payment-status/<payment_id>', methods=['GET'])
def api_payment_status(payment_id):
    """Возвращает статус платежа"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            payment_id, 
            yookassa_id, 
            user_id, 
            amount, 
            status, 
            email,
            description,
            created_at,
            updated_at,
            confirmed_at
        FROM payments 
        WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not payment:
            return jsonify({
                "success": False,
                "error": "Payment not found"
            }), 404
        
        payment_dict = {
            "payment_id": payment[0],
            "yookassa_id": payment[1],
            "user_id": payment[2],
            "amount": float(payment[3]) if payment[3] else None,
            "status": payment[4],
            "email": payment[5],
            "description": payment[6],
            "created_at": payment[7].isoformat() if payment[7] else None,
            "updated_at": payment[8].isoformat() if payment[8] else None,
            "confirmed_at": payment[9].isoformat() if payment[9] else None
        }
        
        return jsonify({
            "success": True,
            "payment": payment_dict
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса платежа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user-payments/<int:user_id>', methods=['GET'])
def api_user_payments(user_id):
    """Возвращает все платежи пользователя"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            payment_id, 
            yookassa_id, 
            amount, 
            status,
            description,
            created_at,
            updated_at,
            confirmed_at
        FROM payments 
        WHERE user_id = %s
        ORDER BY created_at DESC
        """, (user_id,))
        
        payments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        payments_list = []
        for payment in payments:
            payments_list.append({
                "payment_id": payment[0],
                "yookassa_id": payment[1],
                "amount": float(payment[2]) if payment[2] else None,
                "status": payment[3],
                "description": payment[4],
                "created_at": payment[5].isoformat() if payment[5] else None,
                "updated_at": payment[6].isoformat() if payment[6] else None,
                "confirmed_at": payment[7].isoformat() if payment[7] else None
            })
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "payments_count": len(payments_list),
            "payments": payments_list
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения платежей пользователя: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# 2. ЭНДПОИНТЫ ДЛЯ ДОСТУПА
# ============================================

@app.route('/api/grant-access/<payment_id>', methods=['POST'])
def api_grant_access(payment_id):
    """Выдает доступ пользователю после успешной оплаты"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        # Получаем информацию о платеже
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT user_id, status FROM payments WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Payment not found"}), 404
        
        user_id = payment[0]
        status = payment[1]
        
        # Проверяем, что платеж успешен
        if status != 'succeeded':
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Cannot grant access for payment with status: {status}"
            }), 400
        
        # Выдаем доступ
        cursor.execute("""
        INSERT INTO user_access (user_id, payment_id, has_access)
        VALUES (%s, %s, TRUE)
        ON CONFLICT (user_id, payment_id) DO UPDATE SET
            has_access = TRUE,
            granted_at = CURRENT_TIMESTAMP
        RETURNING user_id, payment_id, has_access, granted_at
        """, (user_id, payment_id))
        
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Доступ выдан: user_id={user_id}, payment_id={payment_id}")
        
        return jsonify({
            "success": True,
            "message": "Access granted",
            "user_id": user_id,
            "payment_id": payment_id,
            "has_access": True,
            "granted_at": result[3].isoformat() if result and result[3] else datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка выдачи доступа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/check-access/<int:user_id>', methods=['GET'])
def api_check_access(user_id):
    """Проверяет, есть ли у пользователя доступ"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            ua.payment_id,
            ua.has_access,
            ua.granted_at,
            p.description,
            p.amount,
            p.created_at
        FROM user_access ua
        LEFT JOIN payments p ON ua.payment_id = p.payment_id
        WHERE ua.user_id = %s AND ua.has_access = TRUE
        ORDER BY ua.granted_at DESC
        """, (user_id,))
        
        accesses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        access_list = []
        for access in accesses:
            access_list.append({
                "payment_id": access[0],
                "has_access": access[1],
                "granted_at": access[2].isoformat() if access[2] else None,
                "description": access[3],
                "amount": float(access[4]) if access[4] else None,
                "payment_date": access[5].isoformat() if access[5] else None
            })
        
        has_access = len(access_list) > 0
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "has_access": has_access,
            "active_accesses_count": len(access_list),
            "accesses": access_list
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки доступа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# 3. ВЕБХУК ЮKASSA
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Обработчик вебхуков от ЮKassa"""
    try:
        # Логируем полученный вебхук
        event_json = request.get_json()
        logger.info(f"📥 Получен вебхук от ЮKassa: {json.dumps(event_json, ensure_ascii=False)}")
        
        # Проверяем подпись (опционально, но рекомендуется)
        if YOOKASSA_SECRET_KEY:
            signature = request.headers.get('Yookassa-Signature')
            if signature:
                # Проверка подписи
                body = request.get_data(as_text=True)
                expected_signature = hmac.new(
                    YOOKASSA_SECRET_KEY.encode('utf-8'),
                    body.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                if signature != expected_signature:
                    logger.warning(f"⚠️ Неверная подпись вебхука: {signature}")
                    return jsonify({"status": "error", "message": "Invalid signature"}), 400
        
        # Сохраняем вебхук в лог
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO yookassa_webhooks (webhook_id, event, payment_id, status, payload)
        VALUES (%s, %s, %s, %s, %s)
        """, (
            event_json.get('id'),
            event_json.get('event'),
            event_json.get('object', {}).get('id'),
            event_json.get('object', {}).get('status'),
            json.dumps(event_json, ensure_ascii=False)
        ))
        
        # Обрабатываем событие
        event_type = event_json.get('event')
        payment_data = event_json.get('object', {})
        yookassa_id = payment_data.get('id')
        status = payment_data.get('status')
        metadata = payment_data.get('metadata', {})
        payment_id = metadata.get('payment_id')
        
        if event_type == 'payment.succeeded' and yookassa_id:
            # Обновляем статус платежа
            cursor.execute("""
            UPDATE payments 
            SET status = 'succeeded', 
                confirmed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP,
                metadata = %s
            WHERE yookassa_id = %s
            RETURNING payment_id, user_id
            """, (json.dumps(metadata, ensure_ascii=False), yookassa_id))
            
            result = cursor.fetchone()
            
            if result:
                payment_id = result[0]
                user_id = result[1]
                
                # Выдаем доступ автоматически
                cursor.execute("""
                INSERT INTO user_access (user_id, payment_id, has_access)
                VALUES (%s, %s, TRUE)
                ON CONFLICT (user_id, payment_id) DO UPDATE SET
                    has_access = TRUE,
                    granted_at = CURRENT_TIMESTAMP
                """, (user_id, payment_id))
                
                logger.info(f"✅ Платеж успешен: {yookassa_id}, доступ выдан пользователю {user_id}")
        
        elif event_type == 'payment.canceled' and yookassa_id:
            cursor.execute("""
            UPDATE payments 
            SET status = 'canceled', 
                updated_at = CURRENT_TIMESTAMP
            WHERE yookassa_id = %s
            """, (yookassa_id,))
            
            logger.info(f"❌ Платеж отменен: {yookassa_id}")
        
        elif event_type == 'payment.waiting_for_capture' and yookassa_id:
            cursor.execute("""
            UPDATE payments 
            SET status = 'waiting_for_capture', 
                updated_at = CURRENT_TIMESTAMP
            WHERE yookassa_id = %s
            """, (yookassa_id,))
            
            logger.info(f"⏳ Платеж ожидает подтверждения: {yookassa_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Помечаем вебхук как обработанный
        cursor.execute("""
        UPDATE yookassa_webhooks 
        SET processed = TRUE 
        WHERE webhook_id = %s
        """, (event_json.get('id'),))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# 4. АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ
# ============================================

@app.route('/drop-and-recreate', methods=['GET'])
def drop_and_recreate():
    """Удаляет и пересоздает таблицу payments"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не доступен"}), 500
    
    try:
        success = create_payments_table()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Таблица payments пересоздана с правильной структурой!",
                "columns_added": [
                    "description (TEXT)",
                    "yookassa_id (VARCHAR)",
                    "metadata (TEXT)",
                    "updated_at (TIMESTAMP)"
                ]
            })
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось пересоздать таблицу"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/create-all-tables', methods=['GET'])
def create_all_tables_endpoint():
    """Создает все таблицы с нуля"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не доступен"
        }), 500
    
    try:
        success = create_all_tables()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Все таблицы созданы заново!",
                "tables": [
                    "payments - платежи (с description, yookassa_id, metadata)",
                    "user_access - доступы пользователей",
                    "yookassa_webhooks - логи вебхуков"
                ]
            })
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось создать все таблицы"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/table-structure', methods=['GET'])
def table_structure():
    """Показывает структуру таблицы payments"""
    structure = check_table_structure()
    
    if "error" in structure:
        return jsonify({"success": False, "error": structure["error"]}), 500
    
    return jsonify({
        "success": True,
        "table_exists": structure["table_exists"],
        "column_count": structure["column_count"],
        "columns": structure["columns"],
        "has_description": any(col["name"] == "description" for col in structure["columns"]),
        "has_yookassa_id": any(col["name"] == "yookassa_id" for col in structure["columns"]),
        "has_metadata": any(col["name"] == "metadata" for col in structure["columns"])
    })

@app.route('/check-db', methods=['GET'])
def check_db():
    """Проверяет состояние базы данных"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не доступен"
        }), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['payments', 'user_access', 'yookassa_webhooks']
        table_status = {table: table in tables for table in expected_tables}
        
        payments_structure = []
        if 'payments' in tables:
            cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'payments'
            ORDER BY ordinal_position
            """)
            payments_structure = [{"column": row[0], "type": row[1]} for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "table_status": table_status,
            "payments_structure": payments_structure,
            "health": "healthy" if all(table_status.values()) else "missing_tables"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    try:
        if POSTGRES_AVAILABLE:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            db_status = "connected"
        else:
            db_status = "psycopg3_not_available"
        
        return jsonify({
            "status": "healthy" if POSTGRES_AVAILABLE else "degraded",
            "service": "variatica_payment_api",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    print("="*60)
    print("🚀 VARIATICA PAYMENT API - COMPLETE v2.0")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print("="*60)
    print("📡 КЛЮЧЕВЫЕ ЭНДПОИНТЫ:")
    print("  /api/create-payment      - Создать платеж")
    print("  /api/update-yookassa-id  - Сохранить ID ЮKassa")
    print("  /api/payment-status/{id} - Статус платежа")
    print("  /yookassa-webhook        - Вебхук ЮKassa")
    print("  /api/grant-access/{id}   - Выдать доступ")
    print("  /api/check-access/{id}   - Проверить доступ")
    print("="*60)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
