#!/usr/bin/env python3
"""
app.py - Полный Flask API для платежной системы
Исправленная версия с работающими вебхуками и исправленными ошибками
"""

import os
import sys
import json
import logging
import hashlib
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
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
    """Создает таблицу для логов вебхуков - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
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
            webhook_id VARCHAR(255) NOT NULL DEFAULT 'unknown_' || EXTRACT(EPOCH FROM NOW())::TEXT,
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
        cursor.execute("CREATE INDEX idx_webhooks_webhook_id ON yookassa_webhooks(webhook_id)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'yookassa_webhooks' создана с DEFAULT значением")
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

# ============================================
# API ЭНДПОИНТЫ
# ============================================

@app.route('/')
def home():
    """Главная страница"""
    db_status = "✅ psycopg3 доступен" if POSTGRES_AVAILABLE else "❌ Проблема с psycopg3"
    
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "Payment System v3.0 (исправленная)",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_payment": "/api/create-payment (POST)",
            "update_yookassa_id": "/api/update-yookassa-id (POST)",
            "payment_status": "/api/payment-status/<payment_id> (GET)",
            "yookassa_webhook": "/yookassa-webhook (POST)",
            "grant_access": "/api/grant-access/<payment_id> (POST)",
            "check_access": "/api/check-access/<user_id> (GET)",
            "health": "/health (GET)",
            "check_db": "/check-db (GET)",
            "emergency_check": "/emergency-check (GET)",
            "create_tables": "/create-all-tables (GET)"
        },
        "note": "API принимает вебхуки от ЮKassa и обрабатывает платежи"
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
        new_status = data.get('status', 'waiting')
        
        if not payment_id or not yookassa_id:
            return jsonify({"success": False, "error": "Missing payment_id or yookassa_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE payments 
        SET yookassa_id = %s, status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE payment_id = %s
        RETURNING payment_id, status, yookassa_id, user_id
        """, (yookassa_id, new_status, payment_id))
        
        result = cursor.fetchone()
        
        if not result:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Payment not found"}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ ЮKassa ID обновлен: {payment_id} -> {yookassa_id} (статус: {new_status})")
        
        return jsonify({
            "success": True,
            "message": "Yookassa ID updated",
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "status": new_status,
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
# 3. ВЕБХУК ЮKASSA - ИСПРАВЛЕННАЯ ВЕРСИЯ
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Обработчик вебхуков от ЮKassa - ИСПРАВЛЕННАЯ ВЕРСИЯ (без webhook_id = null)"""
    try:
        # Получаем данные
        event_json = request.get_json()
        if not event_json:
            return jsonify({"status": "error", "message": "Empty webhook"}), 400
        
        logger.info(f"📥 Получен вебхук от ЮKassa: {json.dumps(event_json, ensure_ascii=False)[:200]}...")
        
        # Генерируем webhook_id если его нет
        webhook_id = event_json.get('id')
        if not webhook_id:
            # Создаем уникальный ID на основе времени и данных
            import time
            timestamp = int(time.time())
            data_hash = hashlib.md5(json.dumps(event_json).encode()).hexdigest()[:8]
            webhook_id = f"wh_{timestamp}_{data_hash}"
        
        # Извлекаем данные события
        event_type = event_json.get('event', 'unknown')
        payment_data = event_json.get('object', {})
        yookassa_id = payment_data.get('id', 'unknown')
        status = payment_data.get('status', 'unknown')
        metadata = payment_data.get('metadata', {})
        payment_id = metadata.get('payment_id')
        
        # Сохраняем вебхук в лог
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # ВСТАВЛЯЕМ с webhook_id (теперь всегда есть значение)
            cursor.execute("""
            INSERT INTO yookassa_webhooks (webhook_id, event, payment_id, status, payload)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """, (
                webhook_id,  # ← Теперь НЕ NULL!
                event_type,
                yookassa_id,
                status,
                json.dumps(event_json, ensure_ascii=False)
            ))
            
            webhook_db_id = cursor.fetchone()[0]
            
            # Обрабатываем события
            if event_type == 'payment.succeeded' and yookassa_id != 'unknown':
                # Обновляем статус платежа
                cursor.execute("""
                UPDATE payments 
                SET status = 'succeeded', 
                    confirmed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    metadata = %s
                WHERE yookassa_id = %s OR payment_id = %s
                RETURNING user_id
                """, (json.dumps(metadata, ensure_ascii=False), yookassa_id, payment_id))
                
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    # Выдаем доступ автоматически
                    cursor.execute("""
                    INSERT INTO user_access (user_id, payment_id, has_access)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (user_id, payment_id) DO UPDATE SET
                        has_access = TRUE,
                        granted_at = CURRENT_TIMESTAMP
                    """, (user_id, payment_id))
                    
                    logger.info(f"✅ Платеж успешен: {yookassa_id}, доступ выдан пользователю {user_id}")
            
            elif event_type == 'payment.canceled' and yookassa_id != 'unknown':
                cursor.execute("""
                UPDATE payments 
                SET status = 'canceled', 
                    updated_at = CURRENT_TIMESTAMP
                WHERE yookassa_id = %s
                """, (yookassa_id,))
                
                logger.info(f"❌ Платеж отменен: {yookassa_id}")
            
            elif event_type == 'payment.waiting_for_capture' and yookassa_id != 'unknown':
                cursor.execute("""
                UPDATE payments 
                SET status = 'waiting_for_capture', 
                    updated_at = CURRENT_TIMESTAMP
                WHERE yookassa_id = %s
                """, (yookassa_id,))
                
                logger.info(f"⏳ Платеж ожидает подтверждения: {yookassa_id}")
            
            # Помечаем как обработанный
            cursor.execute("UPDATE yookassa_webhooks SET processed = TRUE WHERE id = %s", (webhook_db_id,))
            
            conn.commit()
            logger.info(f"✅ Вебхук обработан: {webhook_id}")
            
            return jsonify({"status": "ok", "webhook_id": webhook_id}), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка обработки вебхука в БД: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# 4. АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ
# ============================================

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
                    "yookassa_webhooks - логи вебхуков (webhook_id с DEFAULT значением)"
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
    """Показывает структуру таблиц"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не доступен"}), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = ['payments', 'user_access', 'yookassa_webhooks']
        result = {}
        
        for table in tables:
            cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            result[table] = {
                "exists": len(columns) > 0,
                "columns": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns],
                "column_count": len(columns)
            }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "tables": result,
            "webhook_id_fixed": result.get('yookassa_webhooks', {}).get('exists', False)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
        
        # Проверяем данные
        data_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            data_counts[table] = cursor.fetchone()[0]
        
        # Проверяем webhook_id в yookassa_webhooks
        webhook_id_check = True
        if 'yookassa_webhooks' in tables:
            cursor.execute("""
            SELECT COUNT(*) FROM yookassa_webhooks WHERE webhook_id IS NULL
            """)
            null_webhooks = cursor.fetchone()[0]
            webhook_id_check = null_webhooks == 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "expected_tables_status": table_status,
            "data_counts": data_counts,
            "webhook_id_valid": webhook_id_check,
            "health": "healthy" if all(table_status.values()) and webhook_id_check else "issues"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/emergency-check', methods=['GET'])
def emergency_check():
    """Аварийная проверка системы"""
    try:
        # Проверяем базовые вещи
        db_available = POSTGRES_AVAILABLE
        port = os.getenv('PORT', '10000')
        
        result = {
            "status": "checking",
            "timestamp": datetime.now().isoformat(),
            "port": port,
            "postgres_available": db_available,
            "environment_variables": {
                "DATABASE_URL": bool(os.getenv('DATABASE_URL')),
                "YOOKASSA_SHOP_ID": bool(os.getenv('YOOKASSA_SHOP_ID')),
                "YOOKASSA_SECRET_KEY": bool(os.getenv('YOOKASSA_SECRET_KEY'))
            }
        }
        
        # Пробуем подключиться к базе
        if db_available:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT NOW(), version()")
                db_info = cursor.fetchone()
                cursor.close()
                conn.close()
                
                result["database"] = {
                    "connected": True,
                    "time": str(db_info[0]),
                    "version": db_info[1][:50]
                }
            except Exception as db_error:
                result["database"] = {
                    "connected": False,
                    "error": str(db_error)
                }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    try:
        if POSTGRES_AVAILABLE:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)[:100]}"
        else:
            db_status = "psycopg3_not_available"
        
        return jsonify({
            "status": "healthy" if POSTGRES_AVAILABLE and "connected" in db_status else "degraded",
            "service": "variatica_payment_api",
            "version": "3.0",
            "database": db_status,
            "timestamp": datetime.now().isoformat(),
            "endpoints_working": True
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)[:200],
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    print("="*70)
    print("🚀 VARIATICA PAYMENT API - COMPLETE v3.0 (ИСПРАВЛЕННЫЙ)")
    print("="*70)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print(f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print("📡 КЛЮЧЕВЫЕ ЭНДПОИНТЫ:")
    print("  /                        - Главная страница")
    print("  /health                  - Проверка здоровья")
    print("  /check-db                - Проверка базы данных")
    print("  /emergency-check         - Аварийная проверка")
    print("  /create-all-tables       - Создать таблицы заново")
    print("  /api/create-payment      - Создать платеж")
    print("  /api/payment-status/{id} - Статус платежа")
    print("  /yookassa-webhook        - Вебхук ЮKassa (ИСПРАВЛЕН!)")
    print("="*70)
    print("💡 Используйте /create-all-tables если есть ошибки с таблицами")
    print("💡 Вебхук теперь корректно обрабатывает webhook_id = null")
    print("="*70)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
