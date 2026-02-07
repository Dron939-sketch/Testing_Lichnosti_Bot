"""
app.py - Полный Flask API для платежной системы
Версия с исправленной структурой таблиц
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
# API ЭНДПОИНТЫ
# ============================================

@app.route('/')
def home():
    """Главная страница"""
    db_status = "✅ psycopg3 доступен" if POSTGRES_AVAILABLE else "❌ Проблема с psycopg3"
    
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "Production v1.1",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_all_tables": "/create-all-tables (GET)",
            "drop_and_recreate": "/drop-and-recreate (GET) - полная пересборка",
            "check_db": "/check-db (GET)",
            "table_structure": "/table-structure (GET)",
            "create_payment": "/api/create-payment (POST)",
            "health": "/health (GET)"
        },
        "warning": "Если есть ошибки с description - используйте /drop-and-recreate"
    })

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
        
        # Проверяем таблицы
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Проверяем основные таблицы
        expected_tables = ['payments', 'user_access', 'yookassa_webhooks']
        table_status = {table: table in tables for table in expected_tables}
        
        # Проверяем структуру payments
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

@app.route('/api/create-payment', methods=['POST'])
def api_create_payment():
    """Создает платеж - УПРОЩЕННАЯ ВЕРСИЯ"""
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
        
        # Подключаемся к БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ПРОВЕРЯЕМ СТРУКТУРУ ТАБЛИЦЫ
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'description'
        """)
        
        has_description = cursor.fetchone() is not None
        
        if has_description:
            # Если есть description - используем полную версию
            cursor.execute("""
            INSERT INTO payments (payment_id, user_id, amount, email, description, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            ON CONFLICT (payment_id) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
            RETURNING payment_id, status, created_at
            """, (payment_id, user_id, amount, email, description))
        else:
            # Если нет description - используем упрощенную версию
            cursor.execute("""
            INSERT INTO payments (payment_id, user_id, amount, email, status)
            VALUES (%s, %s, %s, %s, 'pending')
            ON CONFLICT (payment_id) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
            RETURNING payment_id, status, created_at
            """, (payment_id, user_id, amount, email))
        
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
            "created_at": result[2].isoformat() if result and result[2] else None,
            "table_has_description": has_description
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        
        # Проверяем если ошибка из-за отсутствия колонки
        error_msg = str(e)
        if "description" in error_msg and "не существует" in error_msg:
            return jsonify({
                "success": False,
                "error": "В таблице payments отсутствует колонка 'description'",
                "solution": "Используйте /drop-and-recreate для пересоздания таблицы",
                "quick_fix": "Откройте: https://testing-lichnosti-bot-1.onrender.com/drop-and-recreate"
            }), 500
        
        return jsonify({
            "success": False,
            "error": f"Error: {error_msg}",
            "type": type(e).__name__
        }), 500

@app.route('/test-payment', methods=['GET'])
def test_payment():
    """Тестовый эндпоинт для создания платежа"""
    try:
        # Создаем тестовые данные
        test_id = f"test_{int(datetime.now().timestamp())}"
        test_data = {
            "payment_id": test_id,
            "user_id": 999999,
            "amount": 1.0,
            "email": "test@example.com",
            "description": "Тестовый платеж"
        }
        
        # Имитируем запрос
        from flask import make_response
        
        # Создаем фиктивный request
        class FakeRequest:
            def get_json(self):
                return test_data
        
        original_request = request._get_current_object()
        
        # Временно заменяем request
        import flask
        flask.request = FakeRequest()
        
        # Вызываем API функцию
        response = api_create_payment()
        
        # Восстанавливаем request
        flask.request = original_request
        
        # Если это уже ответ Flask, возвращаем его
        if isinstance(response, tuple):
            return response
        
        return jsonify({
            "test": "completed",
            "payment_id": test_id,
            "data": test_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Тест не удался"
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
    print("🚀 VARIATICA PAYMENT API - FIXED VERSION")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print("="*60)
    print("🔧 ПРОБЛЕМА: В таблице payments нет колонки 'description'")
    print("💡 РЕШЕНИЕ: Используйте /drop-and-recreate")
    print("="*60)
    print("📡 КЛЮЧЕВЫЕ ЭНДПОИНТЫ:")
    print("  /drop-and-recreate    - Пересоздает таблицу (РЕШАЕТ ПРОБЛЕМУ!)")
    print("  /table-structure      - Показывает структуру таблицы")
    print("  /api/create-payment   - Создает платеж")
    print("  /check-db             - Проверяет БД")
    print("="*60)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
