"""
app.py - Минимальный рабочий Flask API для платежей
Версия 5.0 - Создает таблицу при запуске
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

# Создание Flask приложения
app = Flask(__name__)
CORS(app)  # Разрешаем CORS для API запросов

# Импортируем PostgreSQL библиотеку
try:
    import psycopg2
    from psycopg2 import Error as PGError
    POSTGRES_AVAILABLE = True
    logger.info("✅ PostgreSQL библиотека доступна")
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("⚠️ PostgreSQL библиотека не установлена")

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ============================================

def get_db_connection():
    """Подключение к PostgreSQL на Render"""
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
    
    logger.info(f"🔗 Подключение к PostgreSQL: {DATABASE_URL[:60]}...")
    return psycopg2.connect(DATABASE_URL)

def create_payments_table():
    """Создает таблицу payments если её не существует"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            payment_id VARCHAR(255) UNIQUE NOT NULL,
            yookassa_id VARCHAR(255),
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
        
        # Создаем индексы для быстрого поиска
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'payments' создана или уже существует")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы: {e}")
        return False

def create_user_access_table():
    """Создает таблицу для доступа пользователей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_access (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(255),
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'user_access' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы user_access: {e}")
        return False

def create_webhooks_table():
    """Создает таблицу для логов webhook"""
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'yookassa_webhooks' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы webhooks: {e}")
        return False

def init_database():
    """Инициализация всех таблиц при запуске"""
    logger.info("🗄️ Инициализация базы данных...")
    
    if not POSTGRES_AVAILABLE:
        logger.error("❌ PostgreSQL библиотека не установлена!")
        return False
    
    try:
        # Создаем все таблицы
        payments_ok = create_payments_table()
        access_ok = create_user_access_table()
        webhooks_ok = create_webhooks_table()
        
        if payments_ok and access_ok and webhooks_ok:
            logger.info("✅ Все таблицы базы данных инициализированы")
            return True
        else:
            logger.error("❌ Не все таблицы созданы успешно")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False

# ============================================
# API ЭНДПОИНТЫ ДЛЯ TELEGRAM БОТА
# ============================================

@app.route('/')
def home():
    """Главная страница"""
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "5.0",
        "database": "PostgreSQL на Render",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_table": "/create-table (GET) - создает таблицу",
            "check_db": "/check-db (GET) - проверяет БД",
            "create_payment": "/api/create-payment (POST)",
            "payment_status": "/api/payment-status/<payment_id> (GET)",
            "test": "/test (GET) - тестовый платеж"
        },
        "message": "Используйте /create-table для создания таблицы"
    })

@app.route('/create-table', methods=['GET'])
def create_table_endpoint():
    """Создает таблицу payments"""
    try:
        success = create_payments_table()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Таблица 'payments' создана или уже существует!",
                "next_step": "Теперь можете тестировать создание платежа",
                "test_url": "/test (GET) для теста"
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
    """Проверяет состояние базы данных"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Проверяем таблицу payments
        payments_exists = 'payments' in tables
        
        # Проверяем сколько записей в payments
        record_count = 0
        if payments_exists:
            cursor.execute("SELECT COUNT(*) FROM payments")
            record_count = cursor.fetchone()[0]
        
        # Получаем версию PostgreSQL
        cursor.execute("SELECT version()")
        db_version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL",
            "version": db_version.split(',')[0],
            "tables": tables,
            "payments_exists": payments_exists,
            "payments_record_count": record_count,
            "health": "healthy" if payments_exists else "missing_payments_table"
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
    """
    Создает новую запись о платеже в БД
    Telegram бот вызывает этот endpoint при начале оплаты
    """
    try:
        # Получаем данные
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data"}), 400
        
        # Проверяем обязательные поля
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        if not payment_id:
            return jsonify({"success": False, "error": "Missing payment_id"}), 400
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"}), 400
        
        # Дополнительные поля
        amount = float(data.get('amount', 1.0))
        email = data.get('email', '')
        description = data.get('description', 'Тестовый платеж')
        
        # Подключаемся к БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Вставляем платеж
        cursor.execute("""
        INSERT INTO payments 
        (payment_id, user_id, amount, email, description, status, metadata)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s)
        ON CONFLICT (payment_id) DO UPDATE SET
        status = EXCLUDED.status,
        updated_at = CURRENT_TIMESTAMP
        RETURNING id, payment_id, status, created_at
        """, (
            payment_id,
            user_id,
            amount,
            email,
            description,
            json.dumps({
                'created_via': 'api_create_payment',
                'timestamp': datetime.now().isoformat(),
                'user_agent': request.headers.get('User-Agent', '')
            })
        ))
        
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Платеж создан: {payment_id} для пользователя {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment record created",
            "payment_id": payment_id,
            "status": "pending",
            "database_id": result[0] if result else None,
            "created_at": result[3].isoformat() if result and result[3] else None
        }), 201
        
    except PGError as e:
        logger.error(f"❌ PostgreSQL ошибка: {e}")
        return jsonify({
            "success": False,
            "error": f"Database error: {str(e)}",
            "pgcode": e.pgcode if hasattr(e, 'pgcode') else None
        }), 500
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/api/payment-status/<payment_id>', methods=['GET'])
def api_payment_status(payment_id):
    """Получает статус платежа"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT payment_id, user_id, amount, status, email, description,
               created_at, updated_at, yookassa_id
        FROM payments 
        WHERE payment_id = %s
        """, (payment_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return jsonify({
                "found": True,
                "payment_id": row[0],
                "user_id": row[1],
                "amount": float(row[2]) if row[2] else 0,
                "status": row[3],
                "email": row[4],
                "description": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None,
                "yookassa_id": row[8]
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

@app.route('/test', methods=['GET'])
def test_payment():
    """Тестовый endpoint - создает тестовый платеж"""
    try:
        # Создаем тестовые данные
        test_id = f"test_{int(datetime.now().timestamp())}"
        test_data = {
            "payment_id": test_id,
            "user_id": 999999,
            "amount": 1.0,
            "email": "test@example.com",
            "description": "Тестовый платеж для проверки"
        }
        
        # Имитируем запрос к нашему же API
        from flask import make_response
        request._cached_data = json.dumps(test_data)
        request._parsed_content_type = ('application/json', {})
        
        response = api_create_payment()
        
        # Если это уже ответ Flask, возвращаем его
        if isinstance(response, tuple):
            return response
        
        # Добавляем ссылки для тестирования
        response_data = response.get_json()
        if response_data.get('success'):
            response_data['test_links'] = {
                "check_status": f"/api/payment-status/{test_id}",
                "check_db": "/check-db",
                "home": "/"
            }
        
        return jsonify(response_data), response.status_code
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Тест не удался"
        }), 500

@app.route('/test-api', methods=['GET'])
def test_api():
    """Информация о API"""
    return jsonify({
        "status": "ok",
        "service": "Variatica Payment API",
        "version": "5.0",
        "database": "PostgreSQL on Render",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "home": "/",
            "create_table": "/create-table",
            "check_db": "/check-db",
            "create_payment": "/api/create-payment (POST)",
            "payment_status": "/api/payment-status/<payment_id> (GET)",
            "test": "/test (GET)"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check для Render"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "healthy",
            "service": "variatica_payment_api",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "variatica_payment_api",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    print("="*60)
    print("🚀 ЗАПУСК VARIATICA FLASK API v5.0")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"PostgreSQL доступен: {POSTGRES_AVAILABLE}")
    print("="*60)
    
    # Инициализируем базу данных
    if POSTGRES_AVAILABLE:
        db_initialized = init_database()
        if db_initialized:
            print("✅ База данных инициализирована")
        else:
            print("⚠️ Проблема с инициализацией БД")
    else:
        print("❌ PostgreSQL библиотека не установлена!")
        print("   Добавьте в requirements.txt: psycopg2-binary")
    
    print("="*60)
    print("📡 Доступные endpoints:")
    print("  /                 - Главная страница")
    print("  /create-table     - Создать таблицу payments")
    print("  /check-db         - Проверить состояние БД")
    print("  /api/create-payment - Создать платеж")
    print("  /test             - Тестовый платеж")
    print("  /health           - Health check")
    print("="*60)
    print("💡 Сначала откройте: /create-table")
    print("💡 Затем протестируйте: /test")
    print("="*60)
    
    # Запускаем сервер
    port = int(os.getenv('PORT', 10000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
