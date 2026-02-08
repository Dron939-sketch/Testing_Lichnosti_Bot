#!/usr/bin/env python3
"""
app.py - Полный Flask API для платежной системы с мгновенными уведомлениями
Версия с системой восстановления при падении и отказоустойчивостью
ИСПРАВЛЕННАЯ ВЕРСИЯ - с безопасным созданием таблиц и поддержкой Invoices API
С ПОДДЕРЖКОЙ ВСЕХ СПОСОБОВ ОПЛАТЫ ЮKASSA И АВТОЗАПУСКОМ RECOVERY WORKER
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
import uuid
import functools
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

# Проверяем наличие YooKassa SDK
try:
    from yookassa import Configuration, Payment, Invoice
    YOOKASSA_SDK_AVAILABLE = True
    logger.info("✅ YooKassa SDK доступен (с поддержкой Invoice API)")
except ImportError as e:
    YOOKASSA_SDK_AVAILABLE = False
    logger.warning(f"⚠️ YooKassa SDK не установлен: {e}")

# Конфигурация
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"
YANDEX_DISK_BASE_URL = "https://disk.yandex.ru/d/ваша_ссылка"  # ЗАМЕНИТЕ НА РЕАЛЬНУЮ

# Создание Flask приложения
app = Flask(__name__)
CORS(app)

# ============================================
# АРХИТЕКТУРНЫЕ УТИЛИТЫ ДЛЯ РЕФАКТОРИНГА
# ============================================

def with_transaction(func):
    """Декоратор для коротких атомарных транзакций"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = get_db_connection()
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            logger.info(f"✅ Транзакция {func.__name__} успешно завершена")
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Транзакция {func.__name__} откачена: {e}")
            raise
        finally:
            conn.close()
    return wrapper

def async_task(func):
    """Декоратор для запуска функции в отдельном потоке"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(
            target=func,
            args=args,
            kwargs=kwargs,
            daemon=True,
            name=f"async_{func.__name__}_{int(time.time())}"
        )
        thread.start()
        logger.info(f"🚀 Запущена асинхронная задача: {func.__name__}")
        return thread
    return wrapper

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

# ============================================================================
# РЕШЕНИЕ ПРОБЛЕМЫ 1: Безопасное создание таблиц
# ============================================================================

def create_payments_table():
    """БЕЗОПАСНАЯ версия: создает/проверяет таблицу payments"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Шаг 1: Проверяем существование таблицы БЕЗ попытки создания
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'payments'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Шаг 2: Только если таблицы НЕТ - создаем с нуля
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
                confirmed_at TIMESTAMP,
                recovery_attempts INTEGER DEFAULT 0,
                last_recovery_attempt TIMESTAMP,
                payment_method VARCHAR(50) DEFAULT 'bank_card',
                payment_method_details TEXT DEFAULT '{}'
            )
            """)
            logger.info("✅ Таблица 'payments' создана с нуля")
        else:
            # Шаг 3: Таблица существует - БЕЗОПАСНО добавляем недостающие колонки
            logger.info("✅ Таблица 'payments' уже существует, проверяем структуру")
            
            # Проверяем существующие колонки
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'payments'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # Безопасное добавление payment_method
            if 'payment_method' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN payment_method VARCHAR(50) DEFAULT 'bank_card'")
                    logger.info("✅ Добавлена колонка payment_method")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить payment_method: {e}")
            
            # Безопасное добавление payment_method_details
            if 'payment_method_details' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN payment_method_details TEXT DEFAULT '{}'")
                    logger.info("✅ Добавлена колонка payment_method_details")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить payment_method_details: {e}")
            
            # Безопасное добавление recovery_attempts
            if 'recovery_attempts' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN recovery_attempts INTEGER DEFAULT 0")
                    logger.info("✅ Добавлена колонка recovery_attempts")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить recovery_attempts: {e}")
            
            # Безопасное добавление last_recovery_attempt
            if 'last_recovery_attempt' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE payments ADD COLUMN last_recovery_attempt TIMESTAMP")
                    logger.info("✅ Добавлена колонка last_recovery_attempt")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить last_recovery_attempt: {e}")
        
        # Шаг 4: Создаем индексы (если их нет)
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_yookassa_id ON payments(yookassa_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_payment_method ON payments(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_payments_recovery ON payments(status, created_at) WHERE status IN ('pending', 'waiting_for_capture')"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'payments' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в create_payments_table: {e}")
        return False

def create_user_access_table():
    """Безопасное создание таблицы user_access"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'user_access'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Создаем таблицу с нуля
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
                recovery_notified BOOLEAN DEFAULT FALSE,
                UNIQUE(user_id, payment_id)
            )
            """)
            logger.info("✅ Таблица 'user_access' создана с нуля")
        else:
            # Проверяем и добавляем недостающие колонки
            logger.info("✅ Таблица 'user_access' уже существует, проверяем структуру")
            
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'user_access'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # Безопасное добавление колонок
            columns_to_add = [
                ('recovery_notified', 'BOOLEAN DEFAULT FALSE'),
                ('access_token', 'VARCHAR(255)'),
                ('expires_at', 'TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL \'30 days\')')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE user_access ADD COLUMN {column_name} {column_type}")
                        logger.info(f"✅ Добавлена колонка {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось добавить {column_name}: {e}")
        
        # Создаем индексы
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_user_access_user_id ON user_access(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_access_has_access ON user_access(has_access)",
            "CREATE INDEX IF NOT EXISTS idx_user_access_token ON user_access(access_token)"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'user_access' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы user_access: {e}")
        return False

def create_yookassa_webhooks_table():
    """Безопасное создание таблицы webhooks"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'yookassa_webhooks'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
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
            logger.info("✅ Таблица 'yookassa_webhooks' создана")
        
        # Создаем индексы
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
        
        logger.info("✅ Таблица 'yookassa_webhooks' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы webhooks: {e}")
        return False

def create_notifications_log_table():
    """Безопасное создание таблицы notifications_log"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'notifications_log'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
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
            logger.info("✅ Таблица 'notifications_log' создана")
        
        # Создаем индексы
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
        
        logger.info("✅ Таблица 'notifications_log' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы notifications_log: {e}")
        return False

def create_recovery_log_table():
    """Безопасное создание таблицы recovery_log"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'recovery_log'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
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
            logger.info("✅ Таблица 'recovery_log' создана")
        
        # Создаем индексы
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recovery_payment_id ON recovery_log(payment_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_recovery_recovered_at ON recovery_log(recovered_at)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'recovery_log' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы recovery_log: {e}")
        return False

def create_all_tables():
    """Создает все таблицы с нуля - БЕЗОПАСНАЯ ВЕРСИЯ"""
    logger.info("🗄️ Безопасное создание/проверка всех таблиц базы данных...")
    
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

def send_telegram_pure(user_id, payment_id, access_token=None, is_recovery=False):
    """ЧИСТАЯ функция отправки в Telegram (БЕЗ операций с БД!)"""
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
        
        if response.status_code == 200:
            logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
            return True
        else:
            error_msg = f"Telegram API: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        return False

@async_task
def log_notification_async(user_id, payment_id, success, is_recovery=False):
    """Асинхронное логирование уведомления"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        notification_type = 'payment_success_recovery' if is_recovery else 'payment_success'
        
        cursor.execute("""
        INSERT INTO notifications_log 
        (user_id, payment_id, notification_type, success, auto_recovery)
        VALUES (%s, %s, %s, %s, %s)
        """, (user_id, payment_id, notification_type, success, is_recovery))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"📝 Логирование уведомления завершено: success={success}")
    except Exception as e:
        logger.error(f"❌ Ошибка логирования уведомления: {e}")

@async_task
def send_notification_async(user_id, payment_id, access_token=None, is_recovery=False):
    """Асинхронная отправка уведомления"""
    try:
        logger.info(f"🔔 Начинаю отправку уведомления user_id={user_id}, payment_id={payment_id}")
        success = send_telegram_pure(user_id, payment_id, access_token, is_recovery)
        
        # После отправки логируем результат
        log_notification_async(user_id, payment_id, success, is_recovery)
        
        # Если успешно отправлено, обновляем access_token в БД
        if success and access_token:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE user_access 
                SET access_token = %s, 
                    link_sent = TRUE,
                    materials_sent_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND payment_id = %s
                """, (access_token, user_id, payment_id))
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"✅ Access token обновлен для user_id={user_id}")
            except Exception as db_e:
                logger.error(f"⚠️ Ошибка обновления access token: {db_e}")
        
        return success
    except Exception as e:
        logger.error(f"❌ Ошибка в асинхронной отправке уведомления: {e}")
        return False

# Оригинальная функция для обратной совместимости
def send_telegram_notification(user_id, payment_id, access_token=None, is_recovery=False):
    """Оригинальная функция для обратной совместимости"""
    # Запускаем асинхронно, но возвращаем True сразу
    send_notification_async(user_id, payment_id, access_token, is_recovery)
    return True  # Для совместимости со старым кодом

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

# ============================================================================
# РЕШЕНИЕ ПРОБЛЕМЫ 2: Переход на Invoices API
# ============================================================================

def create_yookassa_invoice(payment_id, amount, user_id, description="Оплата курса ВАРИАТИКА"):
    """Создает СЧЕТ в ЮKassa (дает пользователю выбор способа оплаты)"""
    if not YOOKASSA_SDK_AVAILABLE:
        logger.error("❌ YooKassa SDK не установлен")
        # Fallback для обратной совместимости
        return {
            "id": None,
            "status": "pending",
            "confirmation_url": None,
            "method": "invoice_fallback",
            "available_methods": ["bank_card"],
            "note": "YooKassa SDK недоступен"
        }
    
    try:
        shop_id = os.getenv('YOOKASSA_SHOP_ID')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if not shop_id or not secret_key:
            raise ValueError("YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY не настроены")
        
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        
        # Срок действия счета (24 часа)
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
        
        # Данные для создания СЧЕТА
        invoice_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id)
            },
            # КЛЮЧЕВОЕ: payment_data БЕЗ указания метода
            "payment_data": {
                # Пусто - ЮKassa сам предложит все доступные способы
            },
            # Корзина товаров (обязательно для счетов)
            "cart": [
                {
                    "description": description,
                    "quantity": "1.000",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB"
                    },
                    "vat_code": 1  # Без НДС
                }
            ],
            "expires_at": expires_at,
            "delivery_method_data": {
                "type": "self"  # Пользователь сам переходит по ссылку
            }
        }
        
        # Создаем СЧЕТ (не платеж!)
        invoice = Invoice.create(invoice_data)
        
        # Получаем URL для оплаты
        payment_url = invoice.delivery_method.url if hasattr(invoice.delivery_method, 'url') else None
        
        logger.info(f"✅ Счет создан: {payment_id} → {invoice.id}")
        
        return {
            "id": invoice.id,
            "status": invoice.status,
            "confirmation_url": payment_url,  # Страница выбора способа оплаты
            "invoice_url": payment_url,       # Алиас для совместимости
            "method": "invoice",              # Тип - счет
            "available_methods": "all",       # Все доступные способы в кабинете ЮKassa
            "expires_at": invoice.expires_at if hasattr(invoice, 'expires_at') else expires_at
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания счета: {e}")
        raise

def create_yookassa_payment_legacy(payment_id, amount, user_id, description="Оплата курса ВАРИАТИКА"):
    """Создает ПЛАТЕЖ в ЮKassa (старая функция для обратной совместимости)"""
    if not YOOKASSA_SDK_AVAILABLE:
        logger.error("❌ YooKassa SDK не установлен")
        return {
            "id": None,
            "status": "pending",
            "confirmation_url": None,
            "method": "bank_card"
        }
    
    try:
        shop_id = os.getenv('YOOKASSA_SHOP_ID')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if not shop_id or not secret_key:
            raise ValueError("YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY не настроены")
        
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        
        # Старая логика с фиксированным методом
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": os.getenv('RETURN_URL', 'https://your-site.com/success')
            },
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id)
            },
            "capture": True
        }
        
        payment = Payment.create(payment_data)
        
        confirmation_url = None
        if hasattr(payment.confirmation, 'confirmation_url'):
            confirmation_url = payment.confirmation.confirmation_url
        
        logger.info(f"✅ Платеж создан (старая версия): {payment_id} → {payment.id}")
        
        return {
            "id": payment.id,
            "status": payment.status,
            "confirmation_url": confirmation_url,
            "method": "bank_card"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа (старая версия): {e}")
        raise

# ============================================
# НОВЫЕ АРХИТЕКТУРНЫЕ ФУНКЦИИ ДЛЯ ВЕБХУКА
# ============================================

@with_transaction
def save_webhook_to_db_quick(conn, webhook_id, event_type, yookassa_id, status, event_json, payment_id="unknown"):
    """Быстрое сохранение вебхука в БД (отдельная транзакция)"""
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO yookassa_webhooks (webhook_id, event, payment_id, status, payload)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """, (webhook_id, event_type, yookassa_id, status, json.dumps(event_json, ensure_ascii=False)))
    webhook_db_id = cursor.fetchone()[0]
    cursor.execute("UPDATE yookassa_webhooks SET processed = TRUE WHERE id = %s", (webhook_db_id,))
    return webhook_db_id

@with_transaction
def update_payment_status_tx(conn, yookassa_id, payment_id, status="succeeded", metadata=None):
    """Обновление статуса платежа (отдельная транзакция)"""
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE payments 
    SET status = %s, 
        confirmed_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP,
        metadata = %s
    WHERE yookassa_id = %s OR payment_id = %s
    RETURNING user_id, payment_id, status as old_status
    """, (status, json.dumps(metadata or {}, ensure_ascii=False), yookassa_id, payment_id))
    result = cursor.fetchone()
    return result

@with_transaction
def grant_user_access_tx(conn, user_id, payment_id):
    """Выдача доступа пользователю (отдельная транзакция)"""
    cursor = conn.cursor()
    access_token = generate_access_token(user_id, payment_id)
    cursor.execute("""
    INSERT INTO user_access (user_id, payment_id, has_access, access_token)
    VALUES (%s, %s, TRUE, %s)
    ON CONFLICT (user_id, payment_id) DO UPDATE SET
        has_access = TRUE,
        access_token = EXCLUDED.access_token,
        granted_at = CURRENT_TIMESTAMP
    """, (user_id, payment_id, access_token))
    return access_token

@with_transaction
def log_recovery_action_tx(conn, recovery_type, payment_id, user_id, status_before, 
                          status_after, result="success", error=None, details=None):
    """Логирование действий восстановления (отдельная транзакция)"""
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO recovery_log 
    (recovery_type, payment_id, user_id, status_before, status_after, 
     recovery_result, error_message, details)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (recovery_type, payment_id, user_id, status_before, 
          status_after, result, error, json.dumps(details) if details else None))
    return True

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
        SELECT p.payment_id, p.yookassa_id, p.user_id, p.status, p.created_at, p.payment_method
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
            payment_id, yookassa_id, user_id, status_before, created_at, payment_method = payment
            
            try:
                # Безопасное обновление счетчика попыток
                safe_update_recovery_attempts(payment_id, cursor)
                
                # Проверяем статус в ЮKassa если есть yookassa_id
                if yookassa_id:
                    yk_status = check_yookassa_payment_status(yookassa_id)
                    
                    if yk_status and yk_status.get('status') == 'succeeded':
                        # Платеж оплачен! Восстанавливаем
                        logger.info(f"🎉 Найден оплаченный платеж: {payment_id}")
                        
                        # Безопасный UPDATE
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
                        INSERT INTO user_access (user_id, payment_id, has_access, access_token)
                        VALUES (%s, %s, TRUE, %s)
                        ON CONFLICT (user_id, payment_id) DO UPDATE SET
                            has_access = TRUE,
                            access_token = EXCLUDED.access_token,
                            granted_at = CURRENT_TIMESTAMP
                        """, (user_id, payment_id, access_token))
                        
                        # Пытаемся обновить recovery_notified отдельно если колонка существует
                        try:
                            cursor.execute("""
                            UPDATE user_access 
                            SET recovery_notified = TRUE 
                            WHERE user_id = %s AND payment_id = %s
                            """, (user_id, payment_id))
                        except Exception as e:
                            # Колонка может не существовать - игнорируем ошибку
                            pass
                        
                        # Отправляем уведомление о восстановлении асинхронно
                        send_notification_async(user_id, payment_id, access_token, is_recovery=True)
                        
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
                                "yk_status": yk_status,
                                "payment_method": payment_method
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
    logger.info("🔄 Recovery worker начал работу")
    
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
        thread = threading.Thread(
            target=recovery_worker, 
            daemon=True,
            name="RecoveryWorker"
        )
        thread.start()
        logger.info("✅ Фоновый воркер восстановления запущен")
        return thread
    except Exception as e:
        logger.error(f"❌ Не удалось запустить recovery worker: {e}")
        return None

def ensure_recovery_worker():
    """Гарантирует, что recovery worker запущен"""
    global recovery_thread
    
    # 1. Проверить не запущен ли уже
    for thread in threading.enumerate():
        if thread.name and "recovery" in thread.name.lower() and thread.is_alive():
            logger.info("✅ Recovery worker уже запущен")
            return thread
    
    # 2. Запустить через существующую функцию
    if POSTGRES_AVAILABLE:
        recovery_thread = start_recovery_worker()
        if recovery_thread:
            logger.info("✅ Recovery worker запущен автоматически")
        return recovery_thread
    
    return None

# ============================================
# API ЭНДПОИНТЫ
# ============================================

@app.route('/')
def home():
    """Главная страница"""
    db_status = "✅ psycopg3 доступен" if POSTGRES_AVAILABLE else "❌ Проблема с psycopg3"
    yookassa_status = "✅ YooKassa SDK доступен" if YOOKASSA_SDK_AVAILABLE else "⚠️ YooKassa SDK не установлен"
    
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "Payment System v6.0 (с поддержкой Invoices API и безопасным созданием таблиц)",
        "database": db_status,
        "yookassa": yookassa_status,
        "telegram_bot": TELEGRAM_BOT_URL,
        "features": [
            "✅ Мгновенные уведомления в Telegram",
            "✅ Защищенные ссылки на Яндекс.Диск",
            "✅ Система автовосстановления при падении",
            "✅ Панель администратора",
            "✅ Логирование всех действий",
            "✅ Invoices API ЮKassa (все способы оплаты)",
            "✅ Безопасное создание таблиц",
            "✅ Автозапуск recovery worker"
        ],
        "supported_payment_methods": [
            "💳 bank_card - Банковские карты",
            "📱 sbp - СБП",
            "🏦 yoo_money - ЮMoney",
            "🔵 tinkoff_bank - Тинькофф",
            "🧡 alfabank - Альфа-Клик",
            "🟣 qiwi - QIWI",
            "🏛️ sberbank - Сбербанк Онлайн"
        ],
        "endpoints": {
            "admin": "/admin/dashboard (GET)",
            "recovery": "/recovery/** (см. /admin/dashboard)",
            "create_payment": "/api/create-payment (POST) - СТАРЫЙ",
            "create_payment_advanced": "/api/create-payment-advanced (POST) - НОВЫЙ (Invoices API)",
            "yookassa_webhook": "/yookassa-webhook (POST) - обновленный",
            "get_materials": "/api/get-materials/<payment_id> (GET)",
            "health": "/health (GET)",
            "check_db": "/check-db (GET)",
            "create_tables": "/create-all-tables (GET) - безопасный"
        }
    })

# ============================================
# 1. ЭНДПОИНТЫ ДЛЯ ПЛАТЕЖЕЙ (существующие с обновлениями)
# ============================================

@app.route('/api/create-payment', methods=['POST'])
def api_create_payment():
    """Создает платеж (старый эндпоинт для обратной совместимости) - НЕ МЕНЯТЬ!"""
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
        
        # Создаем платеж в БД без ЮKassa (для обратной совместимости)
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
        
        logger.info(f"✅ Платеж создан (совместимость): {payment_id} для пользователя {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment created (legacy mode)",
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": float(result[3]) if result and result[3] else amount,
            "status": result[1] if result else "pending",
            "created_at": result[2].isoformat() if result and result[2] else datetime.now().isoformat(),
            "note": "Используйте /api/create-payment-advanced для поддержки всех способов оплаты (Invoices API)"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}",
            "type": type(e).__name__
        }), 500

@app.route('/api/create-payment-advanced', methods=['POST'])
def api_create_payment_advanced():
    """Создает платеж через СЧЕТА ЮKassa (Invoices API) - ОБНОВЛЕННЫЙ"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        if not payment_id or not user_id:
            return jsonify({"success": False, "error": "Отсутствуют обязательные параметры"}), 400
        
        amount = float(data.get('amount', 690.0))
        
        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Используем INVOICE вместо PAYMENT
        yookassa_data = create_yookassa_invoice(
            payment_id=payment_id,
            amount=amount,
            user_id=user_id
        )
        
        # Сохраняем в БД (совместимая структура)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO payments (
            payment_id, user_id, amount, yookassa_id, status, 
            payment_method, payment_method_details
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (payment_id) DO UPDATE SET
            yookassa_id = EXCLUDED.yookassa_id,
            status = EXCLUDED.status,
            payment_method = EXCLUDED.payment_method,
            payment_method_details = EXCLUDED.payment_method_details,
            updated_at = CURRENT_TIMESTAMP
        """, (
            payment_id, user_id, amount, 
            yookassa_data.get('id'), 
            yookassa_data.get('status', 'pending'),
            yookassa_data.get('method', 'invoice'),
            json.dumps({
                "type": "invoice", 
                "url": yookassa_data.get('confirmation_url'),
                "expires_at": yookassa_data.get('expires_at')
            })
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Платеж создан через счет: {payment_id}")
        
        # Совместимый ответ с новыми полями
        return jsonify({
            "success": True,
            "message": "Payment invoice created",
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "yookassa_id": yookassa_data.get('id'),
            "confirmation_url": yookassa_data.get('confirmation_url'),
            "payment_method": yookassa_data.get('method'),
            "available_methods": yookassa_data.get('available_methods'),
            "invoice_type": "yookassa_invoice",  # Новое поле
            "expires_at": yookassa_data.get('expires_at'),
            "status": "pending"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
        RETURNING payment_id, status, yookassa_id, user_id, payment_method
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
        
        logger.info(f"✅ ЮKassa ID обновлен: {payment_id} -> {yookassa_id}, метод: {result[4]}")
        
        return jsonify({
            "success": True,
            "message": "Yookassa ID updated",
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "status": new_status,
            "user_id": result[3],
            "payment_method": result[4]
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
        
        # Получаем все колонки
        cursor.execute("""
        SELECT 
            payment_id, yookassa_id, user_id, amount, status, email,
            description, created_at, updated_at, confirmed_at,
            payment_method, payment_method_details
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
            "confirmed_at": payment[9].isoformat() if payment[9] else None,
            "payment_method": payment[10],
            "payment_method_details": json.loads(payment[11]) if payment[11] else {}
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT user_id, status, payment_method FROM payments WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Payment not found"}), 404
        
        user_id, status, payment_method = payment
        
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
        
        # Отправляем уведомление асинхронно
        send_notification_async(user_id, payment_id, access_token)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Доступ выдан: user_id={user_id}, payment_id={payment_id}, метод: {payment_method}")
        
        return jsonify({
            "success": True,
            "message": "Access granted and notification sent",
            "user_id": user_id,
            "payment_id": payment_id,
            "has_access": True,
            "payment_method": payment_method,
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
            ua.access_token, ua.link_sent,
            p.description, p.amount, p.created_at, p.status, p.payment_method
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
                "link_sent": access[5],
                "description": access[6],
                "amount": float(access[7]) if access[7] else None,
                "payment_date": access[8].isoformat() if access[8] else None,
                "payment_status": access[9],
                "payment_method": access[10],
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
                p.status,
                p.payment_method
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
# 3. ИСПРАВЛЕННЫЙ ВЕБХУК ЮKASSA С ПОДДЕРЖКОЙ INVOICES API
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Обработчик вебхуков - ДОПОЛНЕН ДЛЯ INVOICES"""
    try:
        event_json = request.get_json()
        if not event_json:
            logger.warning("❌ Пустой вебхук от ЮKassa")
            return jsonify({"status": "error", "message": "Empty webhook"}), 400
        
        logger.info(f"📥 Получен вебхук от ЮKassa")
        
        webhook_id = event_json.get('id')
        if not webhook_id:
            timestamp = int(time.time())
            data_hash = hashlib.md5(json.dumps(event_json).encode()).hexdigest()[:8]
            webhook_id = f"wh_{timestamp}_{data_hash}"
        
        event_type = event_json.get('event', 'unknown')
        
        # КЛЮЧЕВОЕ: Обрабатываем оба типа событий
        if event_type == 'payment.succeeded':
            # Существующая логика для платежей
            payment_data = event_json.get('object', {})
            yookassa_id = payment_data.get('id')
            status = payment_data.get('status')
            metadata = payment_data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            user_id = metadata.get('user_id')
            
            logger.info(f"✅ Вебхук payment.succeeded: {yookassa_id}")
            
        elif event_type == 'invoice.paid':
            # НОВОЕ: Обработка оплаченных счетов
            invoice_data = event_json.get('object', {})
            
            # Извлекаем данные из счета
            yookassa_id = invoice_data.get('id')
            status = 'succeeded'  # invoice.paid всегда означает успешную оплату
            metadata = invoice_data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            user_id = metadata.get('user_id')
            
            logger.info(f"✅ Вебхук invoice.paid: счет {invoice_data.get('id')}")
            
            # Получаем информацию о способе оплаты из payment_data
            payment_data = invoice_data.get('payment_data', {})
            payment_method = payment_data.get('payment_method', {}) if payment_data else {}
            method_type = payment_method.get('type', 'invoice_paid') if payment_method else 'invoice_paid'
            method_details = json.dumps(payment_method, ensure_ascii=False) if payment_method else '{}'
            
            logger.info(f"💰 Способ оплаты из invoice: {method_type}")
            
        else:
            # Игнорируем другие события
            logger.info(f"📭 Вебхук проигнорирован: {event_type}")
            return jsonify({"status": "ignored"}), 200
        
        try:
            # 1. Сначала быстро сохраняем вебхук в БД
            webhook_db_id = save_webhook_to_db_quick(
                webhook_id, event_type, yookassa_id, status, event_json, payment_id
            )
            logger.info(f"✅ Вебхук сохранен: {webhook_id}")
        except Exception as e:
            logger.error(f"⚠️ Не удалось сохранить вебхук: {e}")
        
        # 2. НЕМЕДЛЕННО отвечаем ЮKassa
        response_data = {"status": "accepted", "webhook_id": webhook_id}
        logger.info(f"📤 Отправляю ответ ЮKassa: {response_data}")
        
        # 3. Запускаем асинхронную обработку в отдельном потоке
        @async_task
        def process_webhook_async():
            """Асинхронная обработка вебхука"""
            try:
                logger.info(f"🔧 Начинаю асинхронную обработку вебхука {webhook_id}")
                
                if event_type in ['payment.succeeded', 'invoice.paid'] and yookassa_id != 'unknown':
                    # Короткая транзакция 1: Обновляем статус платежа
                    try:
                        result = update_payment_status_tx(yookassa_id, payment_id, "succeeded", metadata)
                        if result:
                            user_id, actual_payment_id, old_status = result
                            logger.info(f"✅ Статус платежа обновлен: {actual_payment_id}")
                            
                            # ОБНОВЛЯЕМ СПОСОБ ОПЛАТЫ ДЛЯ invoice.paid
                            if event_type == 'invoice.paid':
                                try:
                                    conn = get_db_connection()
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                    UPDATE payments 
                                    SET payment_method = %s,
                                        payment_method_details = %s
                                    WHERE payment_id = %s
                                    """, (method_type, method_details, actual_payment_id))
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    logger.info(f"✅ Способ оплаты сохранен из invoice: {method_type}")
                                except Exception as method_e:
                                    logger.error(f"⚠️ Ошибка сохранения способа оплаты: {method_e}")
                            
                            # Короткая транзакция 2: Выдаем доступ
                            try:
                                access_token = grant_user_access_tx(user_id, actual_payment_id)
                                logger.info(f"✅ Доступ выдан пользователю {user_id}")
                                
                                # Логируем восстановление если нужно
                                if old_status != 'succeeded':
                                    try:
                                        log_recovery_action_tx(
                                            "webhook_recovery", actual_payment_id, user_id, 
                                            old_status, "succeeded", "success",
                                            details={
                                                "yookassa_id": yookassa_id,
                                                "event_type": event_type,
                                                "payment_method": method_type if event_type == 'invoice.paid' else 'unknown'
                                            }
                                        )
                                    except Exception as log_e:
                                        logger.error(f"⚠️ Ошибка логирования восстановления: {log_e}")
                                
                                # ОПЕРАЦИЯ ВНЕ ТРАНЗАКЦИИ: Отправляем уведомление
                                send_notification_async(user_id, actual_payment_id, access_token)
                                
                            except Exception as access_e:
                                logger.error(f"❌ Ошибка выдачи доступа: {access_e}")
                        else:
                            logger.warning(f"⚠️ Платеж не найден для yookassa_id={yookassa_id}")
                    except Exception as update_e:
                        logger.error(f"❌ Ошибка обновления статуса платежа: {update_e}")
                
                logger.info(f"✅ Асинхронная обработка вебхука {webhook_id} завершена")
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в асинхронной обработке: {e}")
        
        # Запускаем обработку
        process_webhook_async()
        
        # 4. Возвращаем ответ немедленно
        return jsonify(response_data), 202
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в вебхуке: {e}")
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
        SELECT user_id, yookassa_id, status, payment_method FROM payments WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            return jsonify({"success": False, "error": "Платеж не найден"}), 404
        
        user_id, yookassa_id, status_before, payment_method = payment
        
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
                INSERT INTO user_access (user_id, payment_id, has_access, access_token)
                VALUES (%s, %s, TRUE, %s)
                ON CONFLICT (user_id, payment_id) DO UPDATE SET
                    has_access = TRUE,
                    access_token = EXCLUDED.access_token
                """, (user_id, payment_id, access_token))
                
                # Отправляем уведомление асинхронно
                send_notification_async(user_id, payment_id, access_token, is_recovery=True)
                
                log_recovery_action(
                    recovery_type="manual_force",
                    payment_id=payment_id,
                    user_id=user_id,
                    status_before=status_before,
                    status_after="succeeded",
                    result="success",
                    details={
                        "yookassa_id": yookassa_id, 
                        "yk_status": yk_status,
                        "payment_method": payment_method
                    }
                )
                
                conn.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Платеж успешно обработан",
                    "status": "succeeded",
                    "payment_method": payment_method,
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
        SELECT p.payment_id, ua.access_token, p.payment_method
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.user_id = %s 
        AND p.status = 'succeeded'
        AND ua.has_access = TRUE
        AND p.confirmed_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """, (user_id,))
        
        payments = cursor.fetchall()
        
        results = []
        for payment_id, access_token, payment_method in payments:
            # Отправляем асинхронно
            send_notification_async(user_id, payment_id, access_token, is_recovery=True)
            results.append({
                "payment_id": payment_id,
                "payment_method": payment_method,
                "notification_sent": True
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "payments_found": len(payments),
            "notifications_resent": len(payments),
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
        
        # НОВАЯ СТАТИСТИКА: способы оплаты
        try:
            cursor.execute("""
            SELECT 
                COALESCE(payment_method, 'unknown') as method,
                COUNT(*) as count,
                SUM(amount) as total
            FROM payments 
            WHERE status = 'succeeded'
            GROUP BY COALESCE(payment_method, 'unknown')
            ORDER BY count DESC
            """)
            payment_methods_stats = cursor.fetchall()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения статистики по методам оплаты: {e}")
            payment_methods_stats = []
        
        # Проблемные платежи
        cursor.execute("""
        SELECT p.payment_id, p.user_id, p.status, p.created_at, p.payment_method
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
        WHERE table_name = 'payments' AND column_name IN ('recovery_attempts', 'last_recovery_attempt', 'payment_method', 'payment_method_details')
        """)
        existing_columns_payments = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user_access' AND column_name = 'recovery_notified'
        """)
        existing_columns_user_access = [row[0] for row in cursor.fetchall()]
        
        # Статистика по способам оплаты за последние 7 дней
        cursor.execute("""
        SELECT 
            COALESCE(payment_method, 'unknown') as method,
            DATE(created_at) as date,
            COUNT(*) as count,
            SUM(amount) as total
        FROM payments 
        WHERE status = 'succeeded'
        AND created_at > NOW() - INTERVAL '7 days'
        GROUP BY COALESCE(payment_method, 'unknown'), DATE(created_at)
        ORDER BY date DESC, count DESC
        """)
        payment_methods_daily_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Проверяем статус recovery worker
        recovery_status = "inactive"
        for thread in threading.enumerate():
            if thread.name and "recovery" in thread.name.lower() and thread.is_alive():
                recovery_status = "active"
                break
        
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
            "payment_methods_stats": [
                {
                    "method": row[0],
                    "count": row[1],
                    "total": float(row[2]) if row[2] else 0,
                    "percentage": round((row[1] / succeeded_payments * 100) if succeeded_payments > 0 else 0, 1)
                } for row in payment_methods_stats
            ],
            "payment_methods_daily_stats": [
                {
                    "method": row[0],
                    "date": row[1].isoformat() if row[1] else None,
                    "count": row[2],
                    "total": float(row[3]) if row[3] else 0
                } for row in payment_methods_daily_stats
            ],
            "problem_payments": [
                {
                    "payment_id": p[0],
                    "user_id": p[1],
                    "status": p[2],
                    "created_at": p[3].isoformat() if p[3] else None,
                    "payment_method": p[4],
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
                "payments_has_recovery_attempts": 'recovery_attempts' in existing_columns_payments,
                "payments_has_last_recovery_attempt": 'last_recovery_attempt' in existing_columns_payments,
                "payments_has_payment_method": 'payment_method' in existing_columns_payments,
                "payments_has_payment_method_details": 'payment_method_details' in existing_columns_payments,
                "user_access_has_recovery_notified": 'recovery_notified' in existing_columns_user_access,
                "status": "complete" if all([
                    'recovery_attempts' in existing_columns_payments,
                    'last_recovery_attempt' in existing_columns_payments,
                    'payment_method' in existing_columns_payments,
                    'payment_method_details' in existing_columns_payments,
                    'recovery_notified' in existing_columns_user_access
                ]) else "missing_columns"
            },
            "recovery_endpoints": {
                "find_lost_payments": "/recovery/find-lost-payments (GET)",
                "force_process": "/recovery/force-process/<payment_id> (POST)",
                "resend_notifications": "/recovery/resend-notifications/<user_id> (POST)",
                "fix_columns": "/create-all-tables (GET) - используйте этот эндпоинт"
            },
            "system": {
                "recovery_worker": recovery_status,
                "postgres_available": POSTGRES_AVAILABLE,
                "yookassa_sdk_available": YOOKASSA_SDK_AVAILABLE,
                "telegram_configured": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
                "yookassa_configured": bool(os.getenv('YOOKASSA_SHOP_ID') and os.getenv('YOOKASSA_SECRET_KEY')),
                "architecture_version": "6.0 (Invoices API + безопасные таблицы)"
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# 5. АДМИНИСТРАТИВНЫЕ И ТЕСТОВЫЕ ЭНДПОИНТЫ
# ============================================

@app.route('/create-all-tables', methods=['GET'])
def create_all_tables_endpoint():
    """Создает все таблицы с нуля - БЕЗОПАСНАЯ ВЕРСИЯ"""
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
                "message": "✅ Все таблицы созданы/проверены безопасно!",
                "tables": [
                    "payments - платежи (с payment_method и payment_method_details)",
                    "user_access - доступы пользователей",
                    "yookassa_webhooks - логи вебхуков",
                    "notifications_log - логи уведомлений",
                    "recovery_log - логи восстановления"
                ],
                "method": "безопасная проверка и добавление колонок"
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
        SELECT payment_method, COUNT(*) 
        FROM payments 
        WHERE status = 'succeeded'
        GROUP BY payment_method 
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """)
        payments_by_method = cursor.fetchall()
        
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
        
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user_access'
        ORDER BY ordinal_position
        """)
        user_access_columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "database": "PostgreSQL через psycopg3",
            "tables": tables,
            "expected_tables_status": table_status,
            "data_counts": data_counts,
            "payments_by_status": {status: count for status, count in payments_by_status},
            "payments_by_method": {method: count for method, count in payments_by_method},
            "recent_recoveries": {result: count for result, count in recent_recoveries},
            "payments_table_columns": payment_columns,
            "user_access_table_columns": user_access_columns,
            "has_required_columns": {
                "payments_recovery_attempts": 'recovery_attempts' in payment_columns,
                "payments_last_recovery_attempt": 'last_recovery_attempt' in payment_columns,
                "payments_payment_method": 'payment_method' in payment_columns,
                "payments_payment_method_details": 'payment_method_details' in payment_columns,
                "user_access_recovery_notified": 'recovery_notified' in user_access_columns
            },
            "health": "healthy" if all(table_status.values()) else "issues",
            "recommendation": "Запустите /create-all-tables для безопасного исправления" if not all(table_status.values()) else "OK"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/test-notification/<int:user_id>', methods=['GET'])
def test_notification(user_id):
    """Тестовая отправка уведомления"""
    try:
        payment_id = f"test_{int(time.time())}"
        success = send_telegram_pure(user_id, payment_id)
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "payment_id": payment_id,
            "telegram_bot_url": TELEGRAM_BOT_URL,
            "message": "Тестовое уведомление отправлено" if success else "Ошибка отправки"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-invoice-api', methods=['POST'])
def test_invoice_api():
    """Тестирование Invoices API"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id', f"test_invoice_{int(time.time())}")
        user_id = data.get('user_id', 123456)
        amount = float(data.get('amount', 690.0))
        
        # Тестируем создание счета
        result = create_yookassa_invoice(payment_id, amount, user_id)
        
        return jsonify({
            "success": True,
            "test": "Invoices API",
            "payment_id": payment_id,
            "result": result,
            "note": "Если available_methods = 'all', значит Invoices API работает и пользователь увидит все способы оплаты"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "test": "Invoices API",
            "error": str(e)
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
        
        telegram_token_set = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        yookassa_configured = bool(os.getenv('YOOKASSA_SHOP_ID') and os.getenv('YOOKASSA_SECRET_KEY'))
        
        # Проверяем статус recovery worker
        recovery_status = "inactive"
        for thread in threading.enumerate():
            if thread.name and "recovery" in thread.name.lower() and thread.is_alive():
                recovery_status = "active"
                break
        
        return jsonify({
            "status": "healthy" if (POSTGRES_AVAILABLE and "connected" in db_status and telegram_token_set) else "degraded",
            "service": "variatica_payment_api",
            "version": "6.0 (с Invoices API и безопасным созданием таблиц)",
            "database": db_status,
            "yookassa_sdk": "available" if YOOKASSA_SDK_AVAILABLE else "not_available",
            "yookassa_configured": yookassa_configured,
            "telegram_token_configured": telegram_token_set,
            "telegram_bot_url": TELEGRAM_BOT_URL,
            "recovery_worker": recovery_status,
            "supported_payment_methods": "all (через Invoices API)",
            "architecture": "исправленная (Invoices API + безопасные таблицы)",
            "timestamp": datetime.now().isoformat(),
            "critical_fixes": [
                "✅ Безопасное создание таблиц (без ошибок 'столбец не существует')",
                "✅ Invoices API (все способы оплаты ЮKassa)",
                "✅ Обработка вебхуков invoice.paid",
                "✅ 100% обратная совместимость",
                "✅ Сохранение логики оповещений"
            ],
            "recommended_actions": [
                "1. Запустите /create-all-tables для безопасной проверки структуры",
                "2. Используйте /admin/dashboard для мониторинга",
                "3. Проверьте /check-db для диагностики БД",
                "4. Используйте /api/create-payment-advanced для создания счетов (Invoices API)",
                "5. Для теста Invoices API: /test-invoice-api (POST)"
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
        "recovery_suggestion": "Используйте /create-all-tables для безопасного исправления структуры БД"
    }), 500

@app.errorhandler(404)
def handle_404(error):
    """Обработчик 404 ошибок"""
    return jsonify({
        "success": False,
        "error": "Эндпоинт не найден",
        "available_endpoints": [
            "/", "/health", "/admin/dashboard", "/api/**", "/recovery/**",
            "/api/create-payment-advanced - новый эндпоинт с Invoices API",
            "/create-all-tables - безопасное создание таблиц",
            "/test-invoice-api - тест Invoices API"
        ]
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
    print("🚀 VARIATICA PAYMENT API v6.0 - С INVOICES API И БЕЗОПАСНЫМИ ТАБЛИЦАМИ")
    print("="*80)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print(f"YooKassa SDK доступен: {YOOKASSA_SDK_AVAILABLE}")
    print(f"Telegram Bot URL: {TELEGRAM_BOT_URL}")
    print(f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("🎯 ИСПРАВЛЕННЫЕ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
    print("  ✅ ПРОБЛЕМА 1: Безопасное создание таблиц")
    print("     - Нет ошибок 'столбец не существует'")
    print("     - Проверка перед созданием")
    print("     - Добавление только отсутствующих колонок")
    print("  ✅ ПРОБЛЕМА 2: Invoices API вместо Payments API")
    print("     - Пользователь видит ВСЕ способы оплаты")
    print("     - СБП, ЮMoney, Тинькофф и другие доступны")
    print("     - Сохранена логика оповещений")
    print("="*80)
    print("💳 INVOICES API (ВСЕ СПОСОБЫ ОПЛАТЫ):")
    print("  • ЮKassa сам предлагает все доступные способы")
    print("  • Пользователь выбирает на странице ЮKassa")
    print("  • Счет действует 24 часа")
    print("  • Вебхук обрабатывает invoice.paid события")
    print("="*80)
    print("📡 КЛЮЧЕВЫЕ ЭНДПОИНТЫ:")
    print("  /                              - Главная страница")
    print("  /health                        - Проверка здоровья")
    print("  /admin/dashboard               - Панель администратора")
    print("  /check-db                      - Проверка базы данных")
    print("  /create-all-tables             - Безопасное создание/проверка таблиц (ФИКС!)")
    print("  /api/create-payment            - Старый эндпоинт (обратная совместимость)")
    print("  /api/create-payment-advanced   - НОВЫЙ эндпоинт с Invoices API")
    print("  /test-invoice-api              - Тест Invoices API")
    print("  /recovery/find-lost-payments   - Восстановление платежей")
    print("  /yookassa-webhook              - Вебхук ЮKassa (обновлен для invoices)")
    print("="*80)
    print("🛡️  КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ:")
    print("  1. create_payments_table() - безопасная версия")
    print("  2. create_yookassa_invoice() - Invoices API")
    print("  3. /api/create-payment-advanced - обновлен для счетов")
    print("  4. /yookassa-webhook - обработка invoice.paid")
    print("  5. Все остальные функции сохранены без изменений")
    print("="*80)
    print("✅ ПРОВЕРКА ПОСЛЕ ЗАПУСКА:")
    print("  1. Откройте /create-all-tables - должна вернуть success")
    print("  2. Откройте /check-db - проверьте структуру таблиц")
    print("  3. Используйте /api/create-payment-advanced - создание счета")
    print("  4. В ответе должно быть: 'invoice_type': 'yookassa_invoice'")
    print("  5. confirmation_url ведет на страницу выбора способа оплаты")
    print("="*80)
    
    # Создаем таблицы при старте безопасным методом
    try:
        logger.info("🗄️ Безопасная проверка и создание таблиц при запуске...")
        success = create_all_tables()
        if success:
            print("✅ Таблицы проверены/созданы безопасно")
        else:
            print("⚠️ Возникли проблемы с таблицами, но приложение запускается")
    except Exception as e:
        logger.error(f"⚠️ Ошибка создания таблиц при старте: {e}")
        print(f"⚠️ Ошибка создания таблиц: {e}")
    
    # ЗАПУСК ВОРКЕРА ВОССТАНОВЛЕНИЯ С АВТОПРОВЕРКОЙ
    recovery_thread = ensure_recovery_worker()
    
    if recovery_thread and recovery_thread.is_alive():
        logger.info("✅ Recovery worker запущен автоматически")
        print("✅ Recovery worker запущен автоматически")
    else:
        logger.warning("⚠️ Recovery worker не удалось запустить")
        print("⚠️ Recovery worker не удалось запустить")
    
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🚀 Запуск сервера на порту {port}")
    print(f"🚀 Сервер запущен на порту {port}")
    print("="*80)
    app.run(host='0.0.0.0', port=port, debug=False)
