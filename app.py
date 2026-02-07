"""
МИНИМАЛЬНЫЙ FLASK КОД ДЛЯ ИСПРАВЛЕНИЯ ОШИБКИ
Добавляем эндпоинты для создания таблицы и теста
"""

from flask import Flask, request, jsonify
import os
import psycopg2
import sys

app = Flask(__name__)

# ========== ДИАГНОСТИЧЕСКИЕ ЭНДПОИНТЫ ==========

@app.route('/')
def home():
    return jsonify({
        "status": "Flask API работает",
        "endpoints": {
            "create_table": "/create-table (GET)",
            "test_payment": "/test-payment (POST)",
            "check_db": "/check-db (GET)",
            "api_create_payment": "/api/create-payment (POST)"
        }
    })

@app.route('/create-table', methods=['GET'])
def create_table():
    """Создает таблицу payments если её нет"""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            return jsonify({"error": "DATABASE_URL not set"}), 500
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Создаем простую таблицу
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
        
        return jsonify({
            "success": True,
            "message": "Таблица 'payments' создана или уже существует"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/check-db', methods=['GET'])
def check_db():
    """Проверяет таблицы в базе"""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Проверяем payments
        payments_exists = 'payments' in tables
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "tables": tables,
            "payments_exists": payments_exists,
            "table_count": len(tables)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@app.route('/api/create-payment', methods=['POST'])
def api_create_payment():
    """Создает платеж - ПРОСТАЯ ВЕРСИЯ"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400
        
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        if not payment_id or not user_id:
            return jsonify({
                "success": False,
                "error": "Нужны payment_id и user_id"
            }), 400
        
        amount = data.get('amount', 1.0)
        email = data.get('email', '')
        
        DATABASE_URL = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Простая вставка
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, amount, email)
        VALUES (%s, %s, %s, %s)
        """, (payment_id, user_id, float(amount), email))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Платеж создан",
            "payment_id": payment_id,
            "status": "pending"
        })
        
    except psycopg2.Error as e:
        return jsonify({
            "success": False,
            "error": f"Ошибка PostgreSQL: {str(e)}",
            "error_code": e.pgcode if hasattr(e, 'pgcode') else None
        }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Ошибка сервера: {str(e)}"
        }), 500

@app.route('/test-payment', methods=['POST'])
def test_payment():
    """Тестовый эндпоинт для проверки"""
    test_data = {
        "payment_id": "test_123",
        "user_id": 123,
        "amount": 1.0,
        "email": "test@test.com"
    }
    
    # Имитируем запрос
    return api_create_payment(test_data)

@app.route('/test-api', methods=['GET'])
def test_api():
    return jsonify({
        "status": "ok",
        "service": "Минимальный Flask API",
        "endpoints": {
            "check_db": "/check-db",
            "create_table": "/create-table",
            "create_payment": "/api/create-payment",
            "test": "/test-payment"
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print("="*60)
    print("🚀 ЗАПУСК МИНИМАЛЬНОГО FLASK API")
    print(f"Порт: {port}")
    print(f"Python: {sys.version.split()[0]}")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
