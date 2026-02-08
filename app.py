#!/usr/bin/env python3
"""
app.py - Полный Flask API для платежной системы с мгновенными уведомлениями
Версия с системой восстановления при падении и отказоустойчивостью
ИСПРАВЛЕННАЯ ВЕРСИЯ - устранены ошибки с recovery_attempts
"""

import os
import sys
import json
import logging
import hashlib
import hmac
import time
import signal
import threading
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

# Обработчики сигналов для graceful shutdown
def handle_exit(signum, frame):
    logger.info(f"📴 Получен сигнал {signum}, graceful shutdown...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Проверяем наличие psycopg3
try:
    import psycopg
    POSTGRES_AVAILABLE = True
    logger.info("✅ psycopg3 (версия 3.x) доступна")
except ImportError as e:
    POSTGRES_AVAILABLE = False
    logger.error(f"❌ psycopg3 не установлен: {e}")

# Конфигурация
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

def check_and_add_missing_columns():
    """Проверяет и добавляет отсутствующие колонки в существующую таблицу payments"""
    if not POSTGRES_AVAILABLE:
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование колонок
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments'
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Список необходимых колонок
        required_columns = [
            ('recovery_attempts', 'INTEGER DEFAULT 0'),
            ('last_recovery_attempt', 'TIMESTAMP')
        ]
        
        added_columns = []
        
        for column_name, column_type in required_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE payments ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    logger.info(f"✅ Добавлена колонка: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Ошибка добавления колонки {column_name}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if added_columns:
            logger.info(f"✅ Добавлены недостающие колонки: {', '.join(added_columns)}")
            return True
        else:
            logger.info("✅ Все необходимые колонки уже существуют в таблице payments")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки/добавления колонок: {e}")
        return False

def create_payments_table():
    """Создает таблицу payments с правильной структурой"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Сначала создаем таблицу БЕЗ дополнительных колонок
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
        
        # Создаем индексы если их нет
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_yookassa_id ON payments(yookassa_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_payments_recovery ON payments(status, created_at) 
        WHERE status IN ('pending', 'waiting_for_capture')
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Базовая таблица 'payments' создана/проверена")
        
        # Теперь добавляем недостающие колонки
        check_and_add_missing_columns()
        
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_access (
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
            recovery_notified BOOLEAN DEFAULT FALSE,
            UNIQUE(user_id, payment_id)
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_access_user_id ON user_access(user_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_access_has_access ON user_access(has_access)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_access_token ON user_access(access_token)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'user_access' создана/проверена")
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yookassa_webhooks (
            id SERIAL PRIMARY KEY,
            webhook_id VARCHAR(255) NOT NULL DEFAULT 'unknown_' || EXTRACT(EPOCH FROM NOW())::TEXT,
            event VARCHAR(100) NOT NULL,
            payment_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payload TEXT,
            processed BOOLEAN DEFAULT FALSE,
            retry_count INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhooks_payment_id ON yookassa_webhooks(payment_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhooks_event ON yookassa_webhooks(event)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhooks_webhook_id ON yookassa_webhooks(webhook_id)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'yookassa_webhooks' создана/проверена")
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications_log (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(100) NOT NULL,
            notification_type VARCHAR(50) DEFAULT 'payment_success',
            sent_via VARCHAR(50) DEFAULT 'telegram_api',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            auto_recovery BOOLEAN DEFAULT FALSE
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications_log(user_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_payment_id ON notifications_log(payment_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications_log(sent_at)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'notifications_log' создана/проверена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы notifications_log: {e}")
        return False

def create_recovery_log_table():
    """Создает таблицу для логов восстановления"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_log (
            id SERIAL PRIMARY KEY,
            recovery_type VARCHAR(50) NOT NULL,
            payment_id VARCHAR(100),
            user_id BIGINT,
            status_before VARCHAR(50),
            status_after VARCHAR(50),
            recovery_result VARCHAR(50) NOT NULL,
            error_message TEXT,
            recovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recovery_payment_id ON recovery_log(payment_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recovery_recovered_at ON recovery_log(recovered_at)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'recovery_log' создана/проверена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы recovery_log: {e}")
        return False

def create_all_tables():
    """Создает все таблицы с нуля"""
    logger.info("🗄️ Создание/проверка всех таблиц базы данных...")
    
    results = {
        "payments": create_payments_table(),
        "user_access": create_user_access_table(),
        "yookassa_webhooks": create_yookassa_webhooks_table(),
        "notifications_log": create_notifications_log_table(),
        "recovery_log": create_recovery_log_table()
    }
    
    success_count = sum(1 for result in results.values() if result)
    
    if success_count == len(results):
        logger.info("✅ Все таблицы созданы/проверены успешно")
        return True
    else:
        logger.error(f"❌ Успешно создано/проверено только {success_count}/{len(results)} таблиц")
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

def send_telegram_notification(user_id, payment_id, access_token=None, is_recovery=False):
    """Отправляет мгновенное уведомление в Telegram"""
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        # Форматируем сообщение в зависимости от типа
        if is_recovery:
            message = f"""
🔧 *ВОССТАНОВЛЕНИЕ ДОСТУПА*

✅ Ваш платеж `#{payment_id[:8]}` был восстановлен после сбоя системы!

📁 Для получения материалов нажмите кнопку ниже:
`/materials`

⏳ Доступ действителен 30 дней
            """
        else:
            message = f"""
✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*

🎉 Ваш платеж `#{payment_id[:8]}` успешно обработан!

📁 Для получения материалов нажмите кнопку ниже или используйте команду:
`/materials`

💰 Спасибо за покупку курса "ВАРИАТИКА"!
⏳ Доступ действителен 30 дней
            """
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
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
        
        notification_type = 'payment_success_recovery' if is_recovery else 'payment_success'
        
        if response.status_code == 200:
            logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
            
            if access_token:
                cursor.execute("""
                UPDATE user_access 
                SET access_token = %s, 
                    link_sent = TRUE,
                    materials_sent_at = CURRENT_TIMESTAMP,
                    recovery_notified = %s
                WHERE user_id = %s AND payment_id = %s
                """, (access_token, is_recovery, user_id, payment_id))
            
            cursor.execute("""
            INSERT INTO notifications_log 
            (user_id, payment_id, notification_type, success, auto_recovery)
            VALUES (%s, %s, %s, TRUE, %s)
            """, (user_id, payment_id, notification_type, is_recovery))
            
            conn.commit()
            return True
        else:
            error_msg = f"Telegram API: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            
            cursor.execute("""
            INSERT INTO notifications_log 
            (user_id, payment_id, notification_type, success, error_message, auto_recovery)
            VALUES (%s, %s, %s, FALSE, %s, %s)
            """, (user_id, payment_id, notification_type, error_msg, is_recovery))
            
            conn.commit()
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        return False
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def generate_yandex_disk_link(user_id, payment_id, token=None):
    """Генерирует защищенную ссылку на Яндекс.Диск"""
    try:
        if token:
            link = f"{YANDEX_DISK_BASE_URL}?access_token={token}&user_id={user_id}&ref=variatica"
        else:
            timestamp = int(time.time())
            link = f"{YANDEX_DISK_BASE_URL}?user={user_id}&payment={payment_id[:8]}&ts={timestamp}&ref=telegram_bot"
        
        logger.info(f"🔗 Сгенерирована ссылка Яндекс.Диск для user_id={user_id}")
        return link
    except Exception as e:
        logger.error(f"❌ Ошибка генерации ссылки: {e}")
        return YANDEX_DISK_BASE_URL

# ============================================
# СИСТЕМА ВОССТАНОВЛЕНИЯ ПРИ ПАДЕНИИ
# ============================================

def log_recovery_action(recovery_type, payment_id=None, user_id=None, 
                        status_before=None, status_after=None, 
                        result="success", error=None, details=None):
    """Логирует действия восстановления"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO recovery_log 
        (recovery_type, payment_id, user_id, status_before, status_after, 
         recovery_result, error_message, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (recovery_type, payment_id, user_id, status_before, 
              status_after, result, error, json.dumps(details) if details else None))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Ошибка логирования восстановления: {e}")

def check_yookassa_payment_status(yookassa_id):
    """Проверяет статус платежа в ЮKassa через API"""
    try:
        # Импортируем здесь, чтобы не создавать зависимость при старте
        from yookassa import Configuration, Payment
        
        shop_id = os.getenv('YOOKASSA_SHOP_ID')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if not shop_id or not secret_key:
            logger.error("❌ Не настроены ключи ЮKassa")
            return None
        
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        
        payment = Payment.find_one(yookassa_id)
        return {
            'id': payment.id,
            'status': payment.status,
            'paid': payment.paid,
            'amount': payment.amount.value if hasattr(payment, 'amount') else None
        }
    except Exception as e:
        logger.error(f"❌ Ошибка проверки платежа в ЮKassa {yookassa_id}: {e}")
        return None

def safe_update_recovery_attempts(payment_id, cursor):
    """Безопасное обновление recovery_attempts (если колонка существует)"""
    try:
        # Проверяем существование колонки
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'recovery_attempts'
        """)
        
        if cursor.fetchone():
            # Колонка существует - обновляем
            cursor.execute("""
            UPDATE payments 
            SET recovery_attempts = COALESCE(recovery_attempts, 0) + 1,
                last_recovery_attempt = CURRENT_TIMESTAMP
            WHERE payment_id = %s
            """, (payment_id,))
            return True
        else:
            # Колонка не существует - пропускаем
            logger.warning(f"⚠️ Колонка recovery_attempts не существует, пропускаем обновление для {payment_id}")
            return False
    except Exception as e:
        logger.error(f"⚠️ Ошибка при проверке/обновлении recovery_attempts: {e}")
        return False

def find_and_recover_lost_payments():
    """Находит и восстанавливает потерянные платежи"""
    try:
        logger.info("🔄 Запуск поиска потерянных платежей...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Используем безопасный запрос без recovery_attempts в WHERE
        cursor.execute("""
        SELECT p.payment_id, p.yookassa_id, p.user_id, p.status, p.created_at
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.status IN ('pending', 'waiting_for_capture')
        AND p.created_at < NOW() - INTERVAL '10 minutes'
        AND p.created_at > NOW() - INTERVAL '24 hours'
        AND (ua.id IS NULL OR ua.has_access = FALSE)
        ORDER BY p.created_at DESC
        LIMIT 20
        """)
        
        lost_payments = cursor.fetchall()
        recovered_count = 0
        
        logger.info(f"🔍 Найдено {len(lost_payments)} потенциально потерянных платежей")
        
        for payment in lost_payments:
            payment_id, yookassa_id, user_id, status_before, created_at = payment
            
            try:
                # Безопасное обновление счетчика попыток
                safe_update_recovery_attempts(payment_id, cursor)
                
                # Проверяем статус в ЮKassa если есть yookassa_id
                if yookassa_id:
                    yk_status = check_yookassa_payment_status(yookassa_id)
                    
                    if yk_status and yk_status.get('status') == 'succeeded':
                        # Платеж оплачен! Восстанавливаем
                        logger.info(f"🎉 Найден оплаченный платеж: {payment_id}")
                        
                        # Обновляем статус БЕЗ recovery_attempts
                        cursor.execute("""
                        UPDATE payments 
                        SET status = 'succeeded', 
                            confirmed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE payment_id = %s
                        """, (payment_id,))
                        
                        # Выдаем доступ
                        access_token = generate_access_token(user_id, payment_id)
                        cursor.execute("""
                        INSERT INTO user_access (user_id, payment_id, has_access, access_token, recovery_notified)
                        VALUES (%s, %s, TRUE, %s, FALSE)
                        ON CONFLICT (user_id, payment_id) DO UPDATE SET
                            has_access = TRUE,
                            access_token = EXCLUDED.access_token,
                            granted_at = CURRENT_TIMESTAMP
                        """, (user_id, payment_id, access_token))
                        
                        # Отправляем уведомление о восстановлении
                        send_telegram_notification(user_id, payment_id, access_token, is_recovery=True)
                        
                        # Логируем восстановление
                        log_recovery_action(
                            recovery_type="auto_recovery",
                            payment_id=payment_id,
                            user_id=user_id,
                            status_before=status_before,
                            status_after="succeeded",
                            result="success",
                            details={
                                "yookassa_id": yookassa_id,
                                "yk_status": yk_status
                            }
                        )
                        
                        recovered_count += 1
                        logger.info(f"✅ Восстановлен платеж: {payment_id}")
                        
                conn.commit()
                
            except Exception as e:
                logger.error(f"❌ Ошибка восстановления платежа {payment_id}: {e}")
                log_recovery_action(
                    recovery_type="auto_recovery",
                    payment_id=payment_id,
                    user_id=user_id,
                    status_before=status_before,
                    status_after=status_before,
                    result="error",
                    error=str(e)
                )
                conn.rollback()
                continue
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Автовосстановление завершено. Восстановлено: {recovered_count}/{len(lost_payments)}")
        return {
            "found": len(lost_payments),
            "recovered": recovered_count
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка в find_and_recover_lost_payments: {e}")
        return {"error": str(e)}

def recovery_worker():
    """Фоновый воркер для восстановления платежей"""
    while True:
        try:
            # Запускаем каждые 15 минут
            time.sleep(900)  # 15 минут
            
            # Проверяем, что приложение запущено
            with app.app_context():
                result = find_and_recover_lost_payments()
                if result.get('recovered', 0) > 0:
                    logger.info(f"🔄 Воркер восстановления обработал {result['recovered']} платежей")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка в recovery_worker: {e}")
            time.sleep(300)  # Ждем 5 минут при ошибке

# Запускаем воркер в отдельном потоке
def start_recovery_worker():
    """Запускает фоновый воркер восстановления"""
    try:
        thread = threading.Thread(target=recovery_worker, daemon=True)
        thread.start()
        logger.info("✅ Фоновый воркер восстановления запущен")
        return True
    except Exception as e:
        logger.error(f"❌ Не удалось запустить recovery worker: {e}")
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
        "version": "Payment System v5.0 (с системой восстановления)",
        "database": db_status,
        "telegram_bot": TELEGRAM_BOT_URL,
        "features": [
            "✅ Мгновенные уведомления в Telegram",
            "✅ Защищенные ссылки на Яндекс.Диск",
            "✅ Система автовосстановления при падении",
            "✅ Панель администратора",
            "✅ Логирование всех действий"
        ],
        "endpoints": {
            "admin": "/admin/dashboard (GET)",
            "recovery": "/recovery/** (см. /admin/dashboard)",
            "create_payment": "/api/create-payment (POST)",
            "yookassa_webhook": "/yookassa-webhook (POST)",
            "get_materials": "/api/get-materials/<payment_id> (GET)",
            "health": "/health (GET)",
            "check_db": "/check-db (GET)"
        }
    })

# ============================================
# 1. ЭНДПОИНТЫ ДЛЯ ПЛАТЕЖЕЙ (существующие)
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
        
        logger.info(f"✅ ЮKassa ID обновлен: {payment_id} -> {yookassa_id}")
        
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
        
        # Используем безопасный запрос - проверяем существование колонок
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name IN ('recovery_attempts', 'last_recovery_attempt')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        has_recovery_attempts = 'recovery_attempts' in existing_columns
        has_last_recovery_attempt = 'last_recovery_attempt' in existing_columns
        
        # Формируем безопасный запрос
        base_columns = """
            payment_id, yookassa_id, user_id, amount, status, email,
            description, created_at, updated_at, confirmed_at
        """
        
        if has_recovery_attempts and has_last_recovery_attempt:
            query = f"SELECT {base_columns}, recovery_attempts, last_recovery_attempt FROM payments WHERE payment_id = %s"
        elif has_recovery_attempts:
            query = f"SELECT {base_columns}, recovery_attempts, NULL as last_recovery_attempt FROM payments WHERE payment_id = %s"
        elif has_last_recovery_attempt:
            query = f"SELECT {base_columns}, NULL as recovery_attempts, last_recovery_attempt FROM payments WHERE payment_id = %s"
        else:
            query = f"SELECT {base_columns}, NULL as recovery_attempts, NULL as last_recovery_attempt FROM payments WHERE payment_id = %s"
        
        cursor.execute(query, (payment_id,))
        
        payment = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not payment:
            return jsonify({
                "success": False,
                "error": "Payment not found"
            }), 404
        
        # Формируем словарь с учетом доступности колонок
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
            "confirmed_at": payment[9].isoformat() if payment[9] else None,
        }
        
        # Добавляем дополнительные поля если они есть
        if len(payment) > 10:
            payment_dict["recovery_attempts"] = payment[10]
        if len(payment) > 11:
            payment_dict["last_recovery_attempt"] = payment[11].isoformat() if payment[11] else None
        
        return jsonify({
            "success": True,
            "payment": payment_dict,
            "metadata": {
                "has_recovery_attempts_column": has_recovery_attempts,
                "has_last_recovery_attempt_column": has_last_recovery_attempt
            }
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
        
        user_id, status = payment
        
        if status != 'succeeded':
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Cannot grant access for payment with status: {status}"
            }), 400
        
        access_token = generate_access_token(user_id, payment_id)
        
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
            ua.payment_id, ua.has_access, ua.granted_at, ua.expires_at,
            ua.access_token, ua.recovery_notified,
            p.description, p.amount, p.created_at, p.status
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
                "recovery_notified": access[5],
                "description": access[6],
                "amount": float(access[7]) if access[7] else None,
                "payment_date": access[8].isoformat() if access[8] else None,
                "payment_status": access[9],
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
        user_id = request.args.get('user_id')
        token = request.args.get('token')
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id parameter"}), 400
        
        user_id = int(user_id)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        has_access = False
        access_token = None
        
        if token:
            token_data = verify_access_token(token)
            if token_data and token_data['user_id'] == user_id and token_data['payment_id'] == payment_id:
                has_access = True
                access_token = token
        
        if not has_access:
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
        
        yandex_link = generate_yandex_disk_link(user_id, payment_id, access_token)
        
        cursor.execute("""
        UPDATE user_access 
        SET yandex_disk_link = %s,
            materials_sent_at = CURRENT_TIMESTAMP
        WHERE user_id = %s AND payment_id = %s
        """, (yandex_link, user_id, payment_id))
        
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

# ============================================
# 3. ВЕБХУК ЮKASSA С ВОССТАНОВЛЕНИЕМ (ИСПРАВЛЕННЫЙ)
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Обработчик вебхуков от ЮKassa с восстановлением"""
    try:
        event_json = request.get_json()
        if not event_json:
            logger.warning("❌ Пустой вебхук от ЮKassa")
            return jsonify({"status": "error", "message": "Empty webhook"}), 400
        
        logger.info(f"📥 Получен вебхук от ЮKassa: {json.dumps(event_json, ensure_ascii=False)[:200]}...")
        
        webhook_id = event_json.get('id')
        if not webhook_id:
            timestamp = int(time.time())
            data_hash = hashlib.md5(json.dumps(event_json).encode()).hexdigest()[:8]
            webhook_id = f"wh_{timestamp}_{data_hash}"
        
        event_type = event_json.get('event', 'unknown')
        payment_data = event_json.get('object', {})
        yookassa_id = payment_data.get('id', 'unknown')
        status = payment_data.get('status', 'unknown')
        metadata = payment_data.get('metadata', {})
        payment_id = metadata.get('payment_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Логируем вебхук
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
            
            if event_type == 'payment.succeeded' and yookassa_id != 'unknown':
                logger.info(f"🎉 Платеж успешен: {yookassa_id}")
                
                # ПРОВЕРЯЕМ: безопасный UPDATE БЕЗ recovery_attempts
                cursor.execute("""
                UPDATE payments 
                SET status = 'succeeded', 
                    confirmed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    metadata = %s
                WHERE yookassa_id = %s OR payment_id = %s
                RETURNING user_id, payment_id, status as old_status
                """, (json.dumps(metadata, ensure_ascii=False), yookassa_id, payment_id))
                
                result = cursor.fetchone()
                if result:
                    user_id, actual_payment_id, old_status = result
                    
                    # Логируем если это восстановление
                    if old_status != 'succeeded':
                        log_recovery_action(
                            recovery_type="webhook_recovery",
                            payment_id=actual_payment_id,
                            user_id=user_id,
                            status_before=old_status,
                            status_after="succeeded",
                            result="success",
                            details={"yookassa_id": yookassa_id}
                        )
                    
                    access_token = generate_access_token(user_id, actual_payment_id)
                    
                    cursor.execute("""
                    INSERT INTO user_access (user_id, payment_id, has_access, access_token)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (user_id, payment_id) DO UPDATE SET
                        has_access = TRUE,
                        access_token = EXCLUDED.access_token,
                        granted_at = CURRENT_TIMESTAMP,
                        recovery_notified = FALSE
                    """, (user_id, actual_payment_id, access_token))
                    
                    cursor.execute("""
                    INSERT INTO notifications_log (user_id, payment_id, notification_type, success)
                    VALUES (%s, %s, 'access_granted', TRUE)
                    """, (user_id, actual_payment_id))
                    
                    logger.info(f"✅ Доступ выдан пользователю {user_id}")
                    
                    try:
                        notification_sent = send_telegram_notification(user_id, actual_payment_id, access_token)
                        
                        if notification_sent:
                            logger.info(f"📲 Уведомление отправлено пользователю {user_id}")
                        else:
                            logger.error(f"❌ Не удалось отправить уведомление")
                            
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
            
            cursor.execute("UPDATE yookassa_webhooks SET processed = TRUE WHERE id = %s", (webhook_db_id,))
            
            conn.commit()
            logger.info(f"✅ Вебхук обработан: {webhook_id}")
            
            return jsonify({"status": "ok", "webhook_id": webhook_id}), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка обработки вебхука в БД: {e}")
            
            # Логируем ошибку вебхука
            log_recovery_action(
                recovery_type="webhook_error",
                payment_id=payment_id,
                status_before=status,
                status_after=status,
                result="error",
                error=str(e),
                details={"yookassa_id": yookassa_id, "event": event_type}
            )
            
            return jsonify({"status": "error", "message": str(e)}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================
# 4. СИСТЕМА ВОССТАНОВЛЕНИЯ И АДМИН ПАНЕЛЬ
# ============================================

@app.route('/recovery/find-lost-payments', methods=['GET'])
def recovery_find_lost_payments():
    """Находит и восстанавливает потерянные платежи вручную"""
    try:
        result = find_and_recover_lost_payments()
        return jsonify({
            "success": True,
            "message": "Восстановление запущено",
            "result": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recovery/force-process/<payment_id>', methods=['POST'])
def recovery_force_process(payment_id):
    """Принудительная обработка платежа"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT user_id, yookassa_id, status FROM payments WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            return jsonify({"success": False, "error": "Платеж не найден"}), 404
        
        user_id, yookassa_id, status_before = payment
        
        if yookassa_id:
            yk_status = check_yookassa_payment_status(yookassa_id)
            
            if yk_status and yk_status.get('status') == 'succeeded':
                cursor.execute("""
                UPDATE payments 
                SET status = 'succeeded', confirmed_at = CURRENT_TIMESTAMP
                WHERE payment_id = %s
                """, (payment_id,))
                
                access_token = generate_access_token(user_id, payment_id)
                
                cursor.execute("""
                INSERT INTO user_access (user_id, payment_id, has_access, access_token, recovery_notified)
                VALUES (%s, %s, TRUE, %s, TRUE)
                ON CONFLICT (user_id, payment_id) DO UPDATE SET
                    has_access = TRUE,
                    access_token = EXCLUDED.access_token
                """, (user_id, payment_id, access_token))
                
                send_telegram_notification(user_id, payment_id, access_token, is_recovery=True)
                
                log_recovery_action(
                    recovery_type="manual_force",
                    payment_id=payment_id,
                    user_id=user_id,
                    status_before=status_before,
                    status_after="succeeded",
                    result="success",
                    details={"yookassa_id": yookassa_id, "yk_status": yk_status}
                )
                
                conn.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Платеж успешно обработан",
                    "status": "succeeded",
                    "notified": True
                })
        
        return jsonify({
            "success": False,
            "error": "Платеж не найден в ЮKassa или не оплачен"
        }), 400
        
    except Exception as e:
        log_recovery_action(
            recovery_type="manual_force",
            payment_id=payment_id,
            status_before=None,
            status_after=None,
            result="error",
            error=str(e)
        )
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

@app.route('/recovery/resend-notifications/<int:user_id>', methods=['POST'])
def recovery_resend_notifications(user_id):
    """Повторная отправка уведомлений пользователю"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT p.payment_id, ua.access_token
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.user_id = %s 
        AND p.status = 'succeeded'
        AND ua.has_access = TRUE
        AND p.confirmed_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """, (user_id,))
        
        payments = cursor.fetchall()
        
        results = []
        for payment_id, access_token in payments:
            success = send_telegram_notification(user_id, payment_id, access_token, is_recovery=True)
            results.append({
                "payment_id": payment_id,
                "notification_sent": success
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "payments_found": len(payments),
            "notifications_resent": len([r for r in results if r["notification_sent"]]),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Панель администратора для мониторинга"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Статистика
        cursor.execute("SELECT COUNT(*) FROM payments")
        total_payments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'succeeded'")
        succeeded_payments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending' AND created_at > NOW() - INTERVAL '1 hour'")
        recent_pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_access WHERE has_access = TRUE")
        active_accesses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recovery_log WHERE recovered_at > NOW() - INTERVAL '24 hours'")
        recoveries_24h = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM recovery_log WHERE recovery_result = 'error' AND recovered_at > NOW() - INTERVAL '24 hours'")
        recovery_errors_24h = cursor.fetchone()[0]
        
        # Проблемные платежи (безопасный запрос)
        cursor.execute("""
        SELECT p.payment_id, p.user_id, p.status, p.created_at
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.status IN ('pending', 'waiting_for_capture')
        AND p.created_at > NOW() - INTERVAL '24 hours'
        AND (ua.id IS NULL OR ua.has_access = FALSE)
        ORDER BY p.created_at DESC
        LIMIT 20
        """)
        problem_payments = cursor.fetchall()
        
        # Последние восстановления
        cursor.execute("""
        SELECT recovery_type, payment_id, user_id, status_before, status_after, 
               recovery_result, recovered_at
        FROM recovery_log 
        ORDER BY recovered_at DESC 
        LIMIT 10
        """)
        recent_recoveries = cursor.fetchall()
        
        # Статистика уведомлений
        cursor.execute("""
        SELECT notification_type, 
               COUNT(*) as total,
               SUM(CASE WHEN success THEN 1 ELSE 0 END) as success,
               SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed
        FROM notifications_log 
        WHERE sent_at > NOW() - INTERVAL '24 hours'
        GROUP BY notification_type
        """)
        notifications_stats = cursor.fetchall()
        
        # Проверка структуры таблицы
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name IN ('recovery_attempts', 'last_recovery_attempt')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "total_payments": total_payments,
                "succeeded_payments": succeeded_payments,
                "recent_pending_payments": recent_pending,
                "active_accesses": active_accesses,
                "recoveries_last_24h": recoveries_24h,
                "recovery_errors_last_24h": recovery_errors_24h
            },
            "problem_payments": [
                {
                    "payment_id": p[0],
                    "user_id": p[1],
                    "status": p[2],
                    "created_at": p[3].isoformat() if p[3] else None,
                    "needs_recovery": True
                } for p in problem_payments
            ],
            "recent_recoveries": [
                {
                    "type": r[0],
                    "payment_id": r[1],
                    "user_id": r[2],
                    "status_before": r[3],
                    "status_after": r[4],
                    "result": r[5],
                    "recovered_at": r[6].isoformat() if r[6] else None
                } for r in recent_recoveries
            ],
            "notifications_stats": [
                {
                    "type": n[0],
                    "total": n[1],
                    "success": n[2],
                    "failed": n[3],
                    "success_rate": round((n[2] / n[1] * 100) if n[1] > 0 else 0, 1)
                } for n in notifications_stats
            ],
            "table_structure": {
                "has_recovery_attempts": 'recovery_attempts' in existing_columns,
                "has_last_recovery_attempt": 'last_recovery_attempt' in existing_columns,
                "status": "complete" if len(existing_columns) == 2 else "missing_columns"
            },
            "recovery_endpoints": {
                "find_lost_payments": "/recovery/find-lost-payments (GET)",
                "force_process": "/recovery/force-process/<payment_id> (POST)",
                "resend_notifications": "/recovery/resend-notifications/<user_id> (POST)",
                "fix_columns": "/fix-missing-columns (GET)"
            },
            "system": {
                "recovery_worker": "active" if 'recovery_thread' in globals() else "inactive",
                "postgres_available": POSTGRES_AVAILABLE,
                "telegram_configured": bool(os.getenv('TELEGRAM_BOT_TOKEN'))
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# 5. АДМИНИСТРАТИВНЫЕ И ТЕСТОВЫЕ ЭНДПОИНТЫ
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
                "message": "✅ Все таблицы созданы/проверены!",
                "tables": [
                    "payments - платежи (с recovery_attempts)",
                    "user_access - доступы пользователей",
                    "yookassa_webhooks - логи вебхуков",
                    "notifications_log - логи уведомлений",
                    "recovery_log - логи восстановления"
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
        
        expected_tables = ['payments', 'user_access', 'yookassa_webhooks', 'notifications_log', 'recovery_log']
        table_status = {table: table in tables for table in expected_tables}
        
        data_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            data_counts[table] = cursor.fetchone()[0]
        
        cursor.execute("""
        SELECT status, COUNT(*) 
        FROM payments 
        GROUP BY status 
        ORDER BY COUNT(*) DESC
        """)
        payments_by_status = cursor.fetchall()
        
        cursor.execute("""
        SELECT recovery_result, COUNT(*) 
        FROM recovery_log 
        WHERE recovered_at > NOW() - INTERVAL '24 hours'
        GROUP BY recovery_result
        """)
        recent_recoveries = cursor.fetchall()
        
        # Проверка структуры таблицы payments
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments'
        ORDER BY ordinal_position
        """)
        payment_columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "expected_tables_status": table_status,
            "data_counts": data_counts,
            "payments_by_status": {status: count for status, count in payments_by_status},
            "recent_recoveries": {result: count for result, count in recent_recoveries},
            "payments_table_columns": payment_columns,
            "has_recovery_columns": all(col in payment_columns for col in ['recovery_attempts', 'last_recovery_attempt']),
            "health": "healthy" if all(table_status.values()) else "issues"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/fix-missing-columns', methods=['GET'])
def fix_missing_columns():
    """Добавляет недостающие колонки в таблицу payments"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не доступен"}), 500
    
    try:
        success = check_and_add_missing_columns()
        if success:
            return jsonify({
                "success": True,
                "message": "✅ Проверка/добавление колонок выполнена успешно",
                "columns_added": ["recovery_attempts", "last_recovery_attempt"]
            })
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось добавить колонки"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/test-notification/<int:user_id>', methods=['GET'])
def test_notification(user_id):
    """Тестовая отправка уведомления"""
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
        
        telegram_token_set = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        
        return jsonify({
            "status": "healthy" if (POSTGRES_AVAILABLE and "connected" in db_status and telegram_token_set) else "degraded",
            "service": "variatica_payment_api",
            "version": "5.0 (с системой восстановления) - ИСПРАВЛЕННАЯ",
            "database": db_status,
            "telegram_token_configured": telegram_token_set,
            "telegram_bot_url": TELEGRAM_BOT_URL,
            "recovery_system": "active",
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": [
                "Исправлен вебхук ЮKassa (удален recovery_attempts = 0)",
                "Добавлена проверка структуры таблицы",
                "Безопасные SQL-запросы"
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)[:200],
            "timestamp": datetime.now().isoformat()
        }), 500

# Обработчики ошибок
@app.errorhandler(500)
def handle_500(error):
    """Обработчик 500 ошибок"""
    logger.error(f"🔥 500 ошибка: {error}")
    return jsonify({
        "success": False,
        "error": "Внутренняя ошибка сервера",
        "recovery_suggestion": "Используйте /admin/dashboard для диагностики"
    }), 500

@app.errorhandler(404)
def handle_404(error):
    """Обработчик 404 ошибок"""
    return jsonify({
        "success": False,
        "error": "Эндпоинт не найден",
        "available_endpoints": ["/", "/health", "/admin/dashboard", "/api/**"]
    }), 404

@app.errorhandler(Exception)
def handle_exception(e):
    """Глобальный обработчик исключений"""
    logger.error(f"🔥 Необработанное исключение: {e}")
    return jsonify({
        "success": False,
        "error": "Внутренняя ошибка",
        "type": type(e).__name__
    }), 500

# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    print("="*80)
    print("🚀 VARIATICA PAYMENT API v5.0 - ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("="*80)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print(f"Telegram Bot URL: {TELEGRAM_BOT_URL}")
    print(f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("📡 КЛЮЧЕВЫЕ ЭНДПОИНТЫ:")
    print("  /                        - Главная страница")
    print("  /health                  - Проверка здоровья")
    print("  /admin/dashboard         - Панель администратора")
    print("  /check-db                - Проверка базы данных")
    print("  /create-all-tables       - Создать/проверить таблицы")
    print("  /fix-missing-columns     - Исправить структуру таблицы")
    print("  /recovery/find-lost-payments - Восстановление платежей")
    print("  /yookassa-webhook        - Вебхук ЮKassa (ИСПРАВЛЕННЫЙ)")
    print("="*80)
    print("🛠️  ВНЕСЕННЫЕ ИСПРАВЛЕНИЯ:")
    print("  • Удален recovery_attempts = 0 из вебхука ЮKassa")
    print("  • Добавлена безопасная проверка структуры таблицы")
    print("  • Безопасные SQL-запросы в find_and_recover_lost_payments")
    print("  • Автоматическое добавление недостающих колонок")
    print("="*80)
    print("🛡️  СИСТЕМА ВОССТАНОВЛЕНИЯ:")
    print("  • Автоматическое восстановление каждые 15 минут")
    print("  • Панель администратора для мониторинга")
    print("  • Ручное восстановление потерянных платежей")
    print("  • Логирование всех действий восстановления")
    print("="*80)
    print("💡 Инструкция:")
    print("  1. Сначала запустите /fix-missing-columns")
    print("  2. Используйте /admin/dashboard для мониторинга")
    print("  3. При падении система автоматически восстановит платежи")
    print("="*80)
    
    # Создаем таблицы при старте
    try:
        create_all_tables()
    except Exception as e:
        logger.error(f"⚠️ Ошибка создания таблиц при старте: {e}")
    
    # Запускаем воркер восстановления
    global recovery_thread
    recovery_thread = start_recovery_worker()
    
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
