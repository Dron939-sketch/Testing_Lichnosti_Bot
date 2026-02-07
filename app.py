"""
app.py - Flask API с поддержкой psycopg3
Версия для psycopg[binary]==3.3.2
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
    logger.error("У вас в requirements.txt: psycopg[binary]==3.3.2")
    logger.error("Это psycopg3, а не psycopg2!")

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
            payment_id VARCHAR(100) PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount DECIMAL(10,2),
            email VARCHAR(255),
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'payments' создана через psycopg3")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы (psycopg3): {e}")
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
        "version": "psycopg3 Edition",
        "database": db_status,
        "psycopg_version": "3.x" if POSTGRES_AVAILABLE else "не установлен",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "create_table": "/create-table (GET)",
            "check_db": "/check-db (GET)",
            "create_payment": "/api/create-payment (POST)",
            "test": "/test (GET)"
        }
    })

@app.route('/create-table', methods=['GET'])
def create_table_endpoint():
    """Создает таблицу payments через psycopg3"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не доступен",
            "your_requirements": "psycopg[binary]==3.3.2",
            "note": "Используйте psycopg3 API, не psycopg2!"
        }), 500
    
    try:
        success = create_payments_table()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Таблица 'payments' создана через psycopg3!",
                "next_step": "Теперь тестируйте: /test"
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
            "error": "psycopg3 не доступен",
            "solution": "Обновите код для работы с psycopg3"
        }), 500
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем таблицы (синтаксис psycopg3)
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        
        payments_exists = 'payments' in tables
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "payments_exists": payments_exists,
            "table_count": len(tables),
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
    """Создает платеж через psycopg3"""
    if not POSTGRES_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "psycopg3 не установлен",
            "your_requirements": "psycopg[binary]==3.3.2",
            "note": "Обновите код для psycopg3 API"
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
        
        # Подключаемся к БД через psycopg3
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Вставляем платеж (синтаксис psycopg3)
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, amount, email, status)
        VALUES (%s, %s, %s, %s, 'pending')
        ON CONFLICT (payment_id) DO UPDATE SET
        status = EXCLUDED.status,
        created_at = CURRENT_TIMESTAMP
        RETURNING payment_id, status, created_at
        """, (payment_id, user_id, amount, email))
        
        result = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Платеж создан через psycopg3: {payment_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment created via psycopg3",
            "payment_id": payment_id,
            "status": "pending",
            "psycopg_version": "3.x",
            "created_at": result[2].isoformat() if result and result[2] else None
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка psycopg3: {e}")
        return jsonify({
            "success": False,
            "error": f"psycopg3 error: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Тестовый эндпоинт"""
    return jsonify({
        "status": "Тестовый эндпоинт работает!",
        "psycopg_version": "3.x (ожидается)",
        "your_requirements": "psycopg[binary]==3.3.2",
        "note": "Используйте /create-table для создания таблицы",
        "endpoints": {
            "create_table": "/create-table",
            "check_db": "/check-db",
            "create_payment": "/api/create-payment (POST)"
        }
    })

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
            "psycopg_version": "3.x" if POSTGRES_AVAILABLE else "missing",
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
    print("🚀 FLASK API С ПОДДЕРЖКОЙ PSYCOPG3")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print(f"Ваш requirements.txt: psycopg[binary]==3.3.2")
    print("="*60)
    print("📡 Доступные endpoints:")
    print("  /create-table     - Создать таблицу")
    print("  /check-db         - Проверить БД")
    print("  /api/create-payment - Создать платеж")
    print("="*60)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
