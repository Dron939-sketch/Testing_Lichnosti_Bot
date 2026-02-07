"""
app.py - Полный Flask API для платежной системы
Версия с psycopg3 и всеми таблицами
"""

import os
import sys
import json
import logging
from datetime import datetime
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
    from psycopg import errors as pg_errors
    POSTGRES_AVAILABLE = True
    logger.info("✅ psycopg3 (версия 3.x) доступна")
except ImportError as e:
    POSTGRES_AVAILABLE = False
    logger.error(f"❌ psycopg3 не установлен: {e}")
    # Создаем заглушку для PGError
    class pg_errors:
        class Error(Exception):
            pass

# Создание Flask приложения
app = Flask(__name__)
CORS(app)

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ (psycopg3)
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
    """Создает таблицу payments через psycopg3"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
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
        
        # Индексы для быстрого поиска
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_payment_id 
        ON payments(payment_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_user_id 
        ON payments(user_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_status 
        ON payments(status)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_yookassa_id 
        ON payments(yookassa_id)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'payments' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы payments: {e}")
        return False

def create_user_access_table():
    """Создает таблицу для доступа пользователей к курсу"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_access (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(100),
            has_access BOOLEAN DEFAULT FALSE,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            files_sent TEXT DEFAULT '[]',
            UNIQUE(user_id, payment_id)
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_access_user_id 
        ON user_access(user_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_access_has_access 
        ON user_access(has_access)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'user_access' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы user_access: {e}")
        return False

def create_yookassa_webhooks_table():
    """Создает таблицу для логов вебхуков от ЮKassa"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yookassa_webhooks (
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
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhooks_payment_id 
        ON yookassa_webhooks(payment_id)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhooks_event 
        ON yookassa_webhooks(event)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'yookassa_webhooks' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы webhooks: {e}")
        return False

def create_all_tables():
    """Создает все необходимые таблицы"""
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
        "version": "Production v1.0",
        "database": db_status,
        "psycopg_version": "3.x" if POSTGRES_AVAILABLE else "не установлен",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_all_tables": "/create-all-tables (GET)",
            "check_db": "/check-db (GET)",
            "create_payment": "/api/create-payment (POST)",
            "payment_status": "/api/payment-status/<id> (GET)",
            "test": "/test (GET)",
            "health": "/health (GET)"
        }
    })

@app.route('/create-all-tables', methods=['GET'])
def create_all_tables_endpoint():
    """Создает все таблицы сразу"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не доступен",
            "solution": "Убедитесь что psycopg[binary]==3.3.2 в requirements.txt"
        }), 500
    
    try:
        success = create_all_tables()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Все таблицы созданы!",
                "tables_created": [
                    "payments - платежи",
                    "user_access - доступы пользователей",
                    "yookassa_webhooks - логи вебхуков"
                ],
                "next_step": "Теперь можно настраивать ЮKassa"
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

@app.route('/create-table', methods=['GET'])
def create_table_endpoint():
    """Создает таблицу payments через psycopg3"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не доступен"
        }), 500
    
    try:
        success = create_payments_table()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Таблица 'payments' создана!",
                "next_step": "Используйте /create-all-tables для всех таблиц"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось создать таблицу"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/check-db', methods=['GET'])
def check_db():
    """Проверяет состояние базы данных через psycopg3"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не доступен"
        }), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Проверяем основные таблицы
        expected_tables = ['payments', 'user_access', 'yookassa_webhooks']
        table_status = {}
        
        for table in expected_tables:
            table_status[table] = table in tables
        
        # Получаем количество записей в каждой таблице
        record_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            record_counts[table] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "table_status": table_status,
            "record_counts": record_counts,
            "health": "healthy" if all(table_status.values()) else "missing_tables"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
            "database_url_set": bool(os.getenv('DATABASE_URL')),
            "health": "unhealthy"
        }), 500

@app.route('/api/create-payment', methods=['POST'])
def api_create_payment():
    """Создает платеж через psycopg3"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не установлен"
        }), 500
    
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
        
        amount = float(data.get('amount', 1.0))
        email = data.get('email', '')
        description = data.get('description', 'Тестовый платеж')
        yookassa_id = data.get('yookassa_id')
        
        # Подключаемся к БД через psycopg3
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if yookassa_id:
            # Вставка с yookassa_id
            cursor.execute("""
            INSERT INTO payments 
            (payment_id, user_id, amount, email, description, yookassa_id, status, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
            ON CONFLICT (payment_id) DO UPDATE SET
            status = EXCLUDED.status,
            yookassa_id = EXCLUDED.yookassa_id,
            updated_at = CURRENT_TIMESTAMP
            RETURNING id, payment_id, status, created_at
            """, (
                payment_id, user_id, amount, email, description, yookassa_id,
                json.dumps({
                    'created_via': 'api_create_payment',
                    'timestamp': datetime.now().isoformat()
                })
            ))
        else:
            # Вставка без yookassa_id
            cursor.execute("""
            INSERT INTO payments 
            (payment_id, user_id, amount, email, description, status, metadata)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s)
            ON CONFLICT (payment_id) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
            RETURNING id, payment_id, status, created_at
            """, (
                payment_id, user_id, amount, email, description,
                json.dumps({
                    'created_via': 'api_create_payment',
                    'timestamp': datetime.now().isoformat()
                })
            ))
        
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Платеж создан: {payment_id} для пользователя {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment created",
            "payment_id": payment_id,
            "status": "pending",
            "database_id": result[0] if result else None,
            "created_at": result[3].isoformat() if result and result[3] else None
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/api/payment-status/<payment_id>', methods=['GET'])
def api_payment_status(payment_id):
    """Получает статус платежа"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не установлен"
        }), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT payment_id, user_id, amount, status, email, description,
               created_at, updated_at, yookassa_id, metadata
        FROM payments 
        WHERE payment_id = %s
        """, (payment_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return jsonify({
                "found": True,
                "payment": {
                    "payment_id": row[0],
                    "user_id": row[1],
                    "amount": float(row[2]) if row[2] else 0,
                    "status": row[3],
                    "email": row[4],
                    "description": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                    "yookassa_id": row[8],
                    "metadata": json.loads(row[9]) if row[9] else {}
                }
            }), 200
        else:
            return jsonify({
                "found": False,
                "payment_id": payment_id,
                "message": "Payment not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "found": False,
            "error": str(e),
            "payment_id": payment_id
        }), 500

@app.route('/api/update-yookassa-id', methods=['POST'])
def api_update_yookassa_id():
    """Обновляет yookassa_id для платежа"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не установлен"
        }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data"}), 400
        
        payment_id = data.get('payment_id')
        yookassa_id = data.get('yookassa_id')
        
        if not payment_id or not yookassa_id:
            return jsonify({"success": False, "error": "Missing payment_id or yookassa_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE payments 
        SET yookassa_id = %s, updated_at = CURRENT_TIMESTAMP
        WHERE payment_id = %s
        RETURNING payment_id, yookassa_id
        """, (yookassa_id, payment_id))
        
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"✅ Yookassa ID обновлен: {payment_id} -> {yookassa_id}")
            return jsonify({
                "success": True,
                "message": "Yookassa ID updated",
                "payment_id": payment_id,
                "yookassa_id": yookassa_id
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Payment not found",
                "payment_id": payment_id
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Ошибка обновления yookassa_id: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Тестовый эндпоинт"""
    return jsonify({
        "status": "API работает!",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_all_tables": "/create-all-tables",
            "create_payment": "/api/create-payment (POST)",
            "payment_status": "/api/payment-status/<id> (GET)",
            "update_yookassa": "/api/update-yookassa-id (POST)"
        },
        "database": "PostgreSQL с psycopg3"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check для мониторинга"""
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
    print("🚀 VARIATICA PAYMENT API - PRODUCTION READY")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print("="*60)
    print("📡 ДОСТУПНЫЕ ЭНДПОИНТЫ:")
    print("  /                 - Главная страница")
    print("  /create-all-tables - Создать все таблицы")
    print("  /check-db         - Проверить состояние БД")
    print("  /api/create-payment - Создать платеж")
    print("  /api/payment-status/<id> - Статус платежа")
    print("  /api/update-yookassa-id - Обновить ID ЮKassa")
    print("  /health           - Health check")
    print("="*60)
    print("💡 ПЕРВЫЙ ШАГ: Откройте /create-all-tables")
    print("="*60)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
