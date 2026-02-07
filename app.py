#!/usr/bin/env python3
"""
app.py - Полный Flask API для платежной системы с мгновенными уведомлениями
Версия с полной интеграцией Telegram и защищенными материалами
"""

import os
import sys
import json
import logging
import hashlib
import hmac
import time
import requests
from datetime import datetime, timedelta
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

# Ссылка на бота для возврата после оплаты
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"
YANDEX_DISK_BASE_URL = "https://disk.yandex.ru/d/ваша_ссылка"  # ЗАМЕНИТЕ НА РЕАЛЬНУЮ

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
        
        cursor.execute("DROP TABLE IF EXISTS payments CASCADE")
        logger.info("🗑️ Старая таблица payments удалена")
        
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
    """Создает таблицу для доступа пользователей с защищенными ссылками"""
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
            link_sent BOOLEAN DEFAULT FALSE,
            materials_sent_at TIMESTAMP,
            yandex_disk_link TEXT,
            access_token VARCHAR(255),
            expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
            UNIQUE(user_id, payment_id)
        )
        """)
        
        cursor.execute("CREATE INDEX idx_user_access_user_id ON user_access(user_id)")
        cursor.execute("CREATE INDEX idx_user_access_has_access ON user_access(has_access)")
        cursor.execute("CREATE INDEX idx_user_access_token ON user_access(access_token)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'user_access' создана с токенами доступа")
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
        
        logger.info("✅ Таблица 'yookassa_webhooks' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы webhooks: {e}")
        return False

def create_notifications_log_table():
    """Создает таблицу для логов уведомлений"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS notifications_log CASCADE")
        
        cursor.execute("""
        CREATE TABLE notifications_log (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(100) NOT NULL,
            notification_type VARCHAR(50) DEFAULT 'payment_success',
            sent_via VARCHAR(50) DEFAULT 'telegram_api',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("CREATE INDEX idx_notifications_user_id ON notifications_log(user_id)")
        cursor.execute("CREATE INDEX idx_notifications_payment_id ON notifications_log(payment_id)")
        cursor.execute("CREATE INDEX idx_notifications_sent_at ON notifications_log(sent_at)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'notifications_log' создана")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы notifications_log: {e}")
        return False

def create_all_tables():
    """Создает все таблицы с нуля"""
    logger.info("🗄️ Создание всех таблиц базы данных...")
    
    results = {
        "payments": create_payments_table(),
        "user_access": create_user_access_table(),
        "yookassa_webhooks": create_yookassa_webhooks_table(),
        "notifications_log": create_notifications_log_table()
    }
    
    success_count = sum(1 for result in results.values() if result)
    
    if success_count == len(results):
        logger.info("✅ Все таблицы созданы успешно")
        return True
    else:
        logger.error(f"❌ Создано только {success_count}/{len(results)} таблиц")
        return False

# ============================================
# ФУНКЦИИ ДЛЯ УВЕДОМЛЕНИЙ И ЗАЩИЩЕННЫХ ССЫЛОК
# ============================================

def generate_access_token(user_id, payment_id):
    """Генерация защищенного токена доступа с подписью"""
    try:
        secret = os.getenv('YOOKASSA_SECRET_KEY', 'default_secret_key')
        expires_at = int(time.time()) + (30 * 24 * 3600)  # 30 дней
        
        data = f"{user_id}:{payment_id}:{expires_at}"
        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:20]
        
        token = f"{data}:{signature}"
        logger.info(f"🔐 Сгенерирован токен для user_id={user_id}, payment_id={payment_id[:8]}")
        return token
    except Exception as e:
        logger.error(f"❌ Ошибка генерации токена: {e}")
        return f"token_{user_id}_{payment_id}_{int(time.time())}"

def verify_access_token(token):
    """Проверка защищенного токена доступа"""
    try:
        parts = token.split(':')
        if len(parts) != 4:
            return False
            
        user_id, payment_id, expires_at_str, signature = parts
        
        # Проверяем срок действия
        expires_at = int(expires_at_str)
        if time.time() > expires_at:
            logger.warning(f"⏰ Токен просрочен: expires_at={expires_at}")
            return False
        
        # Проверяем подпись
        secret = os.getenv('YOOKASSA_SECRET_KEY', 'default_secret_key')
        data = f"{user_id}:{payment_id}:{expires_at}"
        expected_signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:20]
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(f"⚠️ Неверная подпись токена")
            return False
            
        return {
            'user_id': int(user_id),
            'payment_id': payment_id,
            'expires_at': expires_at
        }
    except Exception as e:
        logger.error(f"❌ Ошибка проверки токена: {e}")
        return False

def send_telegram_notification(user_id, payment_id, access_token=None):
    """Отправляет мгновенное уведомление в Telegram после успешной оплаты"""
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не настроен в переменных окружения")
            return False
        
        # Форматируем сообщение
        message = f"""
✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*

🎉 Ваш платеж `#{payment_id[:8]}` успешно обработан!

📁 Для получения материалов нажмите кнопку ниже или используйте команду:
`/materials`

💰 Спасибо за покупку курса "ВАРИАТИКА"!
⏳ Доступ действителен 30 дней
        """
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        # Создаем inline-клавиатуру
        keyboard = [[
            {
                "text": "📁 ПОЛУЧИТЬ МАТЕРИАЛЫ",
                "callback_data": f"get_materials_{payment_id}"
            }
        ]]
        
        response = requests.post(url, json={
            "chat_id": user_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }, timeout=10)
        
        # Логируем результат
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if response.status_code == 200:
            logger.info(f"✅ Уведомление отправлено пользователю {user_id} для платежа {payment_id}")
            
            # Сохраняем токен доступа если передан
            if access_token:
                cursor.execute("""
                UPDATE user_access 
                SET access_token = %s, 
                    link_sent = TRUE,
                    materials_sent_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND payment_id = %s
                """, (access_token, user_id, payment_id))
            
            cursor.execute("""
            INSERT INTO notifications_log (user_id, payment_id, notification_type, success)
            VALUES (%s, %s, 'payment_success', TRUE)
            """, (user_id, payment_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        else:
            error_msg = f"Ошибка Telegram API: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            
            cursor.execute("""
            INSERT INTO notifications_log (user_id, payment_id, notification_type, success, error_message)
            VALUES (%s, %s, 'payment_success', FALSE, %s)
            """, (user_id, payment_id, error_msg))
            
            conn.commit()
            cursor.close()
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка в send_telegram_notification: {e}")
        return False

def generate_yandex_disk_link(user_id, payment_id, token=None):
    """Генерирует защищенную ссылку на Яндекс.Диск"""
    try:
        # Если есть токен, используем его для подписи
        if token:
            link = f"{YANDEX_DISK_BASE_URL}?access_token={token}&user_id={user_id}&ref=variatica"
        else:
            # Или создаем простую ссылку с параметрами для отслеживания
            timestamp = int(time.time())
            link = f"{YANDEX_DISK_BASE_URL}?user={user_id}&payment={payment_id[:8]}&ts={timestamp}&ref=telegram_bot"
        
        logger.info(f"🔗 Сгенерирована ссылка Яндекс.Диск для user_id={user_id}")
        return link
    except Exception as e:
        logger.error(f"❌ Ошибка генерации ссылки: {e}")
        return YANDEX_DISK_BASE_URL

# ============================================
# API ЭНДПОИНТЫ
# ============================================

@app.route('/')
def home():
    """Главная страница"""
    db_status = "✅ psycopg3 доступен" if POSTGRES_AVAILABLE else "❌ Проблема с psycopg3"
    
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "Payment System v4.0 (с мгновенными уведомлениями)",
        "database": db_status,
        "telegram_bot": TELEGRAM_BOT_URL,
        "features": [
            "✅ Мгновенные уведомления в Telegram",
            "✅ Защищенные ссылки на Яндекс.Диск",
            "✅ Верификация токенов доступа",
            "✅ Логирование всех действий"
        ],
        "endpoints": {
            "create_payment": "/api/create-payment (POST)",
            "update_yookassa_id": "/api/update-yookassa-id (POST)",
            "payment_status": "/api/payment-status/<payment_id> (GET)",
            "yookassa_webhook": "/yookassa-webhook (POST)",
            "grant_access": "/api/grant-access/<payment_id> (POST)",
            "check_access": "/api/check-access/<user_id> (GET)",
            "get_materials": "/api/get-materials/<payment_id> (GET)",
            "verify_token": "/api/verify-token (POST)",
            "health": "/health (GET)",
            "check_db": "/check-db (GET)",
            "create_tables": "/create-all-tables (GET)",
            "test_notification": "/test-notification/<user_id> (GET)"
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

# ============================================
# 2. ЭНДПОИНТЫ ДЛЯ ДОСТУПА И МАТЕРИАЛОВ
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
        
        # Генерируем токен доступа
        access_token = generate_access_token(user_id, payment_id)
        
        # Выдаем доступ
        cursor.execute("""
        INSERT INTO user_access (user_id, payment_id, has_access, access_token)
        VALUES (%s, %s, TRUE, %s)
        ON CONFLICT (user_id, payment_id) DO UPDATE SET
            has_access = TRUE,
            access_token = EXCLUDED.access_token,
            granted_at = CURRENT_TIMESTAMP
        RETURNING user_id, payment_id, has_access, granted_at
        """, (user_id, payment_id, access_token))
        
        result = cursor.fetchone()
        
        # Отправляем уведомление
        send_telegram_notification(user_id, payment_id, access_token)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Доступ выдан: user_id={user_id}, payment_id={payment_id}")
        
        return jsonify({
            "success": True,
            "message": "Access granted and notification sent",
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
            ua.expires_at,
            ua.access_token,
            p.description,
            p.amount,
            p.created_at,
            p.status
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
            expires_at = access[3]
            is_active = True
            if expires_at:
                is_active = expires_at > datetime.now()
            
            access_list.append({
                "payment_id": access[0],
                "has_access": access[1] and is_active,
                "granted_at": access[2].isoformat() if access[2] else None,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "access_token": access[4],
                "description": access[5],
                "amount": float(access[6]) if access[6] else None,
                "payment_date": access[7].isoformat() if access[7] else None,
                "payment_status": access[8],
                "is_active": is_active
            })
        
        has_active_access = any(access["has_access"] for access in access_list)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "has_access": has_active_access,
            "active_accesses_count": sum(1 for a in access_list if a["has_access"]),
            "total_accesses_count": len(access_list),
            "accesses": access_list
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки доступа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-materials/<payment_id>', methods=['GET'])
def api_get_materials(payment_id):
    """Возвращает защищенные материалы для платежа"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        # Получаем параметры
        user_id = request.args.get('user_id')
        token = request.args.get('token')
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id parameter"}), 400
        
        user_id = int(user_id)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем доступ через токен или напрямую
        has_access = False
        access_token = None
        
        if token:
            # Проверяем токен
            token_data = verify_access_token(token)
            if token_data and token_data['user_id'] == user_id and token_data['payment_id'] == payment_id:
                has_access = True
                access_token = token
        
        if not has_access:
            # Проверяем доступ через БД
            cursor.execute("""
            SELECT 
                ua.has_access,
                ua.expires_at > CURRENT_TIMESTAMP as is_active,
                ua.access_token,
                p.status
            FROM user_access ua
            LEFT JOIN payments p ON ua.payment_id = p.payment_id
            WHERE ua.user_id = %s AND ua.payment_id = %s
            """, (user_id, payment_id))
            
            result = cursor.fetchone()
            
            if not result or not result[0] or not result[1] or result[3] != 'succeeded':
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False, 
                    "error": "Доступ запрещен. Платеж не подтвержден или доступ истек.",
                    "code": "ACCESS_DENIED"
                }), 403
            
            has_access = True
            access_token = result[2]
        
        if not has_access:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Доступ не найден"}), 403
        
        # Генерируем защищенную ссылку
        yandex_link = generate_yandex_disk_link(user_id, payment_id, access_token)
        
        # Обновляем запись в БД
        cursor.execute("""
        UPDATE user_access 
        SET yandex_disk_link = %s,
            materials_sent_at = CURRENT_TIMESTAMP
        WHERE user_id = %s AND payment_id = %s
        """, (yandex_link, user_id, payment_id))
        
        # Логируем доступ к материалам
        cursor.execute("""
        INSERT INTO notifications_log (user_id, payment_id, notification_type, success)
        VALUES (%s, %s, 'materials_accessed', TRUE)
        """, (user_id, payment_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"📁 Материалы выданы: user_id={user_id}, payment_id={payment_id}")
        
        return jsonify({
            "success": True,
            "message": "Доступ к материалам подтвержден",
            "materials_link": yandex_link,
            "payment_id": payment_id,
            "user_id": user_id,
            "access_method": "token" if token else "direct",
            "note": "Ссылка действительна 30 дней с момента оплаты"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка выдачи материалов: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/verify-token', methods=['POST'])
def api_verify_token():
    """Проверяет токен доступа"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({"valid": False, "error": "Token is required"}), 400
        
        # Проверяем токен
        token_data = verify_access_token(token)
        if not token_data:
            return jsonify({"valid": False, "error": "Invalid or expired token"}), 200
        
        # Дополнительная проверка в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            ua.has_access,
            ua.expires_at > CURRENT_TIMESTAMP as is_active,
            p.status = 'succeeded' as payment_ok
        FROM user_access ua
        JOIN payments p ON ua.payment_id = p.payment_id
        WHERE ua.user_id = %s AND ua.payment_id = %s
        """, (token_data['user_id'], token_data['payment_id']))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and all(result):
            return jsonify({
                "valid": True,
                "user_id": token_data['user_id'],
                "payment_id": token_data['payment_id'],
                "expires_at": token_data['expires_at'],
                "expires_at_human": datetime.fromtimestamp(token_data['expires_at']).isoformat()
            }), 200
        
        return jsonify({"valid": False, "error": "Access not found in database"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки токена: {e}")
        return jsonify({"valid": False, "error": str(e)}), 500

# ============================================
# 3. ВЕБХУК ЮKASSA С МГНОВЕННЫМИ УВЕДОМЛЕНИЯМИ
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Обработчик вебхуков от ЮKassa с мгновенными уведомлениями"""
    try:
        # Получаем данные
        event_json = request.get_json()
        if not event_json:
            logger.warning("❌ Пустой вебхук от ЮKassa")
            return jsonify({"status": "error", "message": "Empty webhook"}), 400
        
        logger.info(f"📥 Получен вебхук от ЮKassa: {json.dumps(event_json, ensure_ascii=False)[:200]}...")
        
        # Генерируем webhook_id если его нет
        webhook_id = event_json.get('id')
        if not webhook_id:
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Сохраняем вебхук в лог
            cursor.execute("""
            INSERT INTO yookassa_webhooks (webhook_id, event, payment_id, status, payload)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """, (
                webhook_id,
                event_type,
                yookassa_id,
                status,
                json.dumps(event_json, ensure_ascii=False)
            ))
            
            webhook_db_id = cursor.fetchone()[0]
            
            # Обрабатываем события
            if event_type == 'payment.succeeded' and yookassa_id != 'unknown':
                logger.info(f"🎉 Платеж успешен: {yookassa_id}")
                
                # Обновляем статус платежа
                cursor.execute("""
                UPDATE payments 
                SET status = 'succeeded', 
                    confirmed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    metadata = %s
                WHERE yookassa_id = %s OR payment_id = %s
                RETURNING user_id, payment_id
                """, (json.dumps(metadata, ensure_ascii=False), yookassa_id, payment_id))
                
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    actual_payment_id = result[1]
                    
                    # Генерируем токен доступа
                    access_token = generate_access_token(user_id, actual_payment_id)
                    
                    # Выдаем доступ автоматически
                    cursor.execute("""
                    INSERT INTO user_access (user_id, payment_id, has_access, access_token)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (user_id, payment_id) DO UPDATE SET
                        has_access = TRUE,
                        access_token = EXCLUDED.access_token,
                        granted_at = CURRENT_TIMESTAMP
                    """, (user_id, actual_payment_id, access_token))
                    
                    # Логируем факт выдачи доступа
                    cursor.execute("""
                    INSERT INTO notifications_log (user_id, payment_id, notification_type, success)
                    VALUES (%s, %s, 'access_granted', TRUE)
                    """, (user_id, actual_payment_id))
                    
                    logger.info(f"✅ Доступ выдан пользователю {user_id} для платежа {actual_payment_id}")
                    
                    # 🔥 ВАЖНО: Отправляем мгновенное уведомление
                    try:
                        notification_sent = send_telegram_notification(user_id, actual_payment_id, access_token)
                        
                        if notification_sent:
                            logger.info(f"📲 Уведомление отправлено пользователю {user_id}")
                        else:
                            logger.error(f"❌ Не удалось отправить уведомление пользователю {user_id}")
                            
                    except Exception as notify_error:
                        logger.error(f"❌ Ошибка отправки уведомления: {notify_error}")
            
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
# 4. АДМИНИСТРАТИВНЫЕ И ТЕСТОВЫЕ ЭНДПОИНТЫ
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
                    "user_access - доступы пользователей с токенами",
                    "yookassa_webhooks - логи вебхуков",
                    "notifications_log - логи уведомлений"
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
        
        expected_tables = ['payments', 'user_access', 'yookassa_webhooks', 'notifications_log']
        table_status = {table: table in tables for table in expected_tables}
        
        # Проверяем данные
        data_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            data_counts[table] = cursor.fetchone()[0]
        
        # Проверяем последние уведомления
        notifications_status = "N/A"
        if 'notifications_log' in tables:
            cursor.execute("""
            SELECT notification_type, COUNT(*) 
            FROM notifications_log 
            GROUP BY notification_type 
            ORDER BY COUNT(*) DESC
            """)
            notifications_stats = cursor.fetchall()
            notifications_status = {ntype: count for ntype, count in notifications_stats}
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "expected_tables_status": table_status,
            "data_counts": data_counts,
            "notifications_stats": notifications_status,
            "health": "healthy" if all(table_status.values()) else "issues"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/test-notification/<int:user_id>', methods=['GET'])
def test_notification(user_id):
    """Тестовая отправка уведомления (админ)"""
    try:
        payment_id = f"test_{int(time.time())}"
        success = send_telegram_notification(user_id, payment_id)
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "payment_id": payment_id,
            "telegram_bot_url": TELEGRAM_BOT_URL,
            "message": "Тестовое уведомление отправлено" if success else "Ошибка отправки"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
        
        # Проверяем токен бота
        telegram_token_set = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        
        return jsonify({
            "status": "healthy" if (POSTGRES_AVAILABLE and "connected" in db_status and telegram_token_set) else "degraded",
            "service": "variatica_payment_api",
            "version": "4.0 (с уведомлениями)",
            "database": db_status,
            "telegram_token_configured": telegram_token_set,
            "telegram_bot_url": TELEGRAM_BOT_URL,
            "timestamp": datetime.now().isoformat(),
            "features": [
                "Мгновенные уведомления",
                "Защищенные ссылки",
                "Верификация токенов",
                "Логирование"
            ]
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
    print("="*80)
    print("🚀 VARIATICA PAYMENT API v4.0 - С МГНОВЕННЫМИ УВЕДОМЛЕНИЯМИ")
    print("="*80)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print(f"Telegram Bot URL: {TELEGRAM_BOT_URL}")
    print(f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("📡 КЛЮЧЕВЫЕ ЭНДПОИНТЫ:")
    print("  /                        - Главная страница")
    print("  /health                  - Проверка здоровья")
    print("  /check-db                - Проверка базы данных")
    print("  /create-all-tables       - Создать таблицы заново")
    print("  /test-notification/<id>  - Тест уведомления")
    print("  /api/create-payment      - Создать платеж")
    print("  /api/get-materials/{id}  - Получить материалы")
    print("  /yookassa-webhook        - Вебхук ЮKassa (МГНОВЕННЫЕ УВЕДОМЛЕНИЯ!)")
    print("="*80)
    print("💡 Инструкция:")
    print("  1. Используйте /create-all-tables для создания таблиц")
    print("  2. Убедитесь, что TELEGRAM_BOT_TOKEN установлен в окружении")
    print("  3. Настройте вебхук в ЮKassa на /yookassa-webhook")
    print("  4. Замените YANDEX_DISK_BASE_URL на реальную ссылку")
    print("="*80)
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
