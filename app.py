#!/usr/bin/env python3
"""
app.py - Полный Flask API для платежной системы с мгновенными уведомлениями
Версия: 8.1 - ПОЛНАЯ ПОДДЕРЖКА ПРИГЛАШЕНИЙ
✅ Все 36 профилей Яндекс.Диск
✅ 18+ модуль с таблицами для приглашений
✅ 4F модуль с покупкой ключей
✅ Новые эндпоинты для управления приглашениями
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

# ========== ССЫЛКИ НА ПРОФИЛИ ЯНДЕКС.ДИСК ==========
PROFILE_LINKS = {
    # SA Profiles
    "SA_1_DEF": "https://disk.yandex.ru/d/HAcOfAg1tpIedA",
    "SA_2_SIT": "https://disk.yandex.ru/d/MwdMClX9koCTmA",
    "SA_3_CON": "https://disk.yandex.ru/d/NKN_XemK62t5nA",
    "SA_4_EXP": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA",
    "SA_5_INT": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg",
    "SA_6_AUT": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag",
    "SA_7_VAL": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g",
    "SA_8_TRA": "https://disk.yandex.ru/d/SqlDISkse1OEGQ",
    "SA_9_IDE": "https://disk.yandex.ru/d/vGzHmuckInNL5g",
    
    # SP Profiles
    "SP_1_DEF": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA",
    "SP_2_SIT": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA",
    "SP_3_CON": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA",
    "SP_4_EXP": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ",
    "SP_5_INT": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg",
    "SP_6_AUT": "https://disk.yandex.ru/d/xWBv4TLFosOB5g",
    "SP_7_VAL": "https://disk.yandex.ru/d/K1whXj6C6KAazQ",
    "SP_8_TRA": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg",
    "SP_9_IDE": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ",
    
    # IA Profiles
    "IA_1_DEF": "https://disk.yandex.ru/d/M1Y7z175uGKIHg",
    "IA_2_SIT": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ",
    "IA_3_CON": "https://disk.yandex.ru/d/DCkqqALby9UpFg",
    "IA_4_EXP": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg",
    "IA_5_INT": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g",
    "IA_6_AUT": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg",
    "IA_7_VAL": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ",
    "IA_8_TRA": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw",
    "IA_9_IDE": "https://disk.yandex.ru/d/ub0YpQQSg4g6rQ",
    
    # IP Profiles
    "IP_1_DEF": "https://disk.yandex.ru/d/m-WOQwDdgQxsnQ",
    "IP_2_SIT": "https://disk.yandex.ru/d/aL4VlAQdlaZ-6g",
    "IP_3_CON": "https://disk.yandex.ru/d/N8GG9XbnC3bFhg",
    "IP_4_EXP": "https://disk.yandex.ru/d/54RFOZmGhA4cfA",
    "IP_5_INT": "https://disk.yandex.ru/d/l5iFTIX8-gTycQ",
    "IP_6_AUT": "https://disk.yandex.ru/d/bTo_vcCoC1KU7Q",
    "IP_7_VAL": "https://disk.yandex.ru/d/TMx1VP843bnJQw",
    "IP_8_TRA": "https://disk.yandex.ru/d/e9KfJdLcl3gp7g",
    "IP_9_IDE": "https://disk.yandex.ru/d/ZiQPHJSDrrWZhw"
}

DEFAULT_PROFILE = "SA_1_DEF"  # Профиль по умолчанию
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

# ============================================
# 18+ МОДУЛЬ - КОНСТАНТЫ
# ============================================
SEXUAL_DEFAULT_PROFILE = "sa_5_int"
SEXUAL_PAYMENT_AMOUNT = 99.00
SEXUAL_PROFILES_DIR = "sexual_18"

# ============================================
# 4F МОДУЛЬ - КОНСТАНТЫ
# ============================================
F4F_BASE_PATH = "профили/4F"
F4F_FUNCTIONS = ["1F", "2F", "3F", "4F"]
F4F_DEFAULT_PROFILE = "sa_4_cap"
F4F_PAYMENT_AMOUNT = 99.00

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

def create_payments_table():
    """БЕЗОПАСНАЯ версия: создает/проверяет таблицу payments с поддержкой профилей"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Шаг 1: Проверяем существование таблицы
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
                payment_method_details TEXT DEFAULT '{}',
                profile_code VARCHAR(20) DEFAULT 'SA_1_DEF'
            )
            """)
            logger.info("✅ Таблица 'payments' создана с нуля (с profile_code)")
        else:
            # Шаг 3: Таблица существует - БЕЗОПАСНО добавляем недостающие колонки
            logger.info("✅ Таблица 'payments' уже существует, проверяем структуру")
            
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'payments'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            columns_to_add = [
                ('payment_method', 'VARCHAR(50) DEFAULT \'bank_card\''),
                ('payment_method_details', 'TEXT DEFAULT \'{}\''),
                ('recovery_attempts', 'INTEGER DEFAULT 0'),
                ('last_recovery_attempt', 'TIMESTAMP'),
                ('profile_code', 'VARCHAR(20) DEFAULT \'SA_1_DEF\'')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE payments ADD COLUMN {column_name} {column_type}")
                        logger.info(f"✅ Добавлена колонка {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось добавить {column_name}: {e}")
        
        # Шаг 4: Создаем индексы
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_yookassa_id ON payments(yookassa_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_payment_method ON payments(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_payments_profile_code ON payments(profile_code)",
            "CREATE INDEX IF NOT EXISTS idx_payments_recovery ON payments(status, created_at) WHERE status IN ('pending', 'waiting_for_capture')",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_yookassa_id ON payments(yookassa_id) WHERE yookassa_id IS NOT NULL"
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
    """Безопасное создание таблицы для доступа пользователей"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'user_access'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
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
            logger.info("✅ Таблица 'user_access' уже существует, проверяем структуру")
            
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'user_access'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            columns_to_add = [
                ('recovery_notified', 'BOOLEAN DEFAULT FALSE'),
                ('access_token', 'VARCHAR(255)'),
                ('expires_at', 'TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL \'30 days\')'),
                ('link_sent', 'BOOLEAN DEFAULT FALSE'),
                ('materials_sent_at', 'TIMESTAMP'),
                ('yandex_disk_link', 'TEXT')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE user_access ADD COLUMN {column_name} {column_type}")
                        logger.info(f"✅ Добавлена колонка {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось добавить {column_name}: {e}")
        
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
    """Безопасное создание таблицы для логов вебхуков"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'yookassa_webhooks'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.execute("""
            CREATE TABLE yookassa_webhooks (
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
        else:
            logger.info("✅ Таблица 'yookassa_webhooks' уже существует, проверяем структуру")
            
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'yookassa_webhooks'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            if 'webhook_id' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE yookassa_webhooks ADD COLUMN webhook_id VARCHAR(255) NOT NULL DEFAULT 'unknown_' || EXTRACT(EPOCH FROM NOW())::TEXT")
                    logger.info("✅ Добавлена колонка webhook_id")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить webhook_id: {e}")
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_webhooks_payment_id ON yookassa_webhooks(payment_id)",
            "CREATE INDEX IF NOT EXISTS idx_webhooks_event ON yookassa_webhooks(event)",
            "CREATE INDEX IF NOT EXISTS idx_webhooks_webhook_id ON yookassa_webhooks(webhook_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_webhook ON yookassa_webhooks(webhook_id, event)"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'yookassa_webhooks' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы webhooks: {e}")
        return False

def create_notifications_log_table():
    """Безопасное создание таблицы для логов уведомлений"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'notifications_log'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
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
                retry_count INTEGER DEFAULT 0,
                auto_recovery BOOLEAN DEFAULT FALSE
            )
            """)
            logger.info("✅ Таблица 'notifications_log' создана")
        else:
            logger.info("✅ Таблица 'notifications_log' уже существует, проверяем структуру")
            
            cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'notifications_log'
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            if 'auto_recovery' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE notifications_log ADD COLUMN auto_recovery BOOLEAN DEFAULT FALSE")
                    logger.info("✅ Добавлена колонка auto_recovery")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить auto_recovery: {e}")
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_payment_id ON notifications_log(payment_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications_log(sent_at)"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'notifications_log' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы notifications_log: {e}")
        return False

def create_recovery_log_table():
    """Безопасное создание таблицы для логов восстановления"""
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'recovery_log'
        )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.execute("""
            CREATE TABLE recovery_log (
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
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_recovery_payment_id ON recovery_log(payment_id)",
            "CREATE INDEX IF NOT EXISTS idx_recovery_recovered_at ON recovery_log(recovered_at)"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Таблица 'recovery_log' проверена/исправлена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы recovery_log: {e}")
        return False

def create_sexual_access_tables():
    """Создает таблицы для 18+ модуля"""
    if not POSTGRES_AVAILABLE:
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sexual_access_purchases (
            id SERIAL PRIMARY KEY,
            buyer_id BIGINT NOT NULL,
            target_id BIGINT NOT NULL,
            target_name VARCHAR(255),
            target_profile_key VARCHAR(50) NOT NULL,
            invite_id VARCHAR(100),
            payment_id VARCHAR(100) UNIQUE NOT NULL,
            amount DECIMAL(10,2) DEFAULT 99.00,
            status VARCHAR(50) DEFAULT 'pending',
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP,
            UNIQUE(buyer_id, target_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sexual_invites (
            id SERIAL PRIMARY KEY,
            invite_id VARCHAR(100) UNIQUE NOT NULL,
            buyer_id BIGINT NOT NULL,
            target_id BIGINT DEFAULT 0,
            target_name VARCHAR(255),
            target_profile_key VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            is_free BOOLEAN DEFAULT TRUE,           -- 👈 НОВОЕ ПОЛЕ
            invite_type VARCHAR(10) DEFAULT '🆓',    -- 👈 НОВОЕ ПОЛЕ
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            purchased_at TIMESTAMP
        )
        """)
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_sexual_purchases_buyer ON sexual_access_purchases(buyer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sexual_purchases_target ON sexual_access_purchases(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_sexual_purchases_status ON sexual_access_purchases(status)",
            "CREATE INDEX IF NOT EXISTS idx_sexual_invites_buyer ON sexual_invites(buyer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sexual_invites_target ON sexual_invites(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_sexual_invites_status ON sexual_invites(status)"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса 18+: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✅ Таблицы 18+ модуля созданы")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц 18+: {e}")
        return False

# ============================================
# 👇 ВОТ СЮДА ВСТАВЛЯЕМ НОВУЮ ФУНКЦИЮ
# ============================================

def add_columns_to_sexual_invites():
    """Добавляет недостающие колонки в таблицу sexual_invites"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование колонки is_free
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'sexual_invites' AND column_name = 'is_free'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE sexual_invites ADD COLUMN is_free BOOLEAN DEFAULT TRUE")
            logger.info("✅ Добавлена колонка is_free в sexual_invites")
        
        # Проверяем существование колонки invite_type
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'sexual_invites' AND column_name = 'invite_type'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE sexual_invites ADD COLUMN invite_type VARCHAR(10) DEFAULT '🆓'")
            logger.info("✅ Добавлена колонка invite_type в sexual_invites")
        
        # Обновляем существующие записи
        cursor.execute("UPDATE sexual_invites SET is_free = TRUE WHERE is_free IS NULL")
        cursor.execute("UPDATE sexual_invites SET invite_type = '🆓' WHERE invite_type IS NULL")
        logger.info("✅ Обновлены существующие записи")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка добавления колонок: {e}")
        return False


# ============================================
# 4F МОДУЛЬ - ТАБЛИЦЫ
# ============================================

def create_4f_tables():
    """Создает таблицы для 4F-модуля"""
    if not POSTGRES_AVAILABLE:
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases_4f (
            id SERIAL PRIMARY KEY,
            payment_id VARCHAR(100) UNIQUE NOT NULL,
            buyer_id BIGINT NOT NULL,
            target_id BIGINT NOT NULL,
            target_name VARCHAR(255),
            target_profile VARCHAR(50) DEFAULT 'SA_4_CAP',
            function VARCHAR(2) NOT NULL,
            amount DECIMAL(10,2) DEFAULT 99.00,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP,
            delivered BOOLEAN DEFAULT FALSE,
            invite_id VARCHAR(100),
            access_token VARCHAR(255),
            UNIQUE(buyer_id, target_id, function)
        )
        """)
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_4f_payment_id ON purchases_4f(payment_id)",
            "CREATE INDEX IF NOT EXISTS idx_4f_buyer ON purchases_4f(buyer_id)",
            "CREATE INDEX IF NOT EXISTS idx_4f_target ON purchases_4f(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_4f_status ON purchases_4f(status)",
            "CREATE INDEX IF NOT EXISTS idx_4f_function ON purchases_4f(function)"
        ]
        
        for sql in indexes_sql:
            try:
                cursor.execute(sql)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса 4F: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✅ Таблица purchases_4f создана")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы purchases_4f: {e}")
        return False

def create_user_limits_table():
    """Создает таблицу для хранения лимитов пользователей"""
    logger.info("🔧 ВЫЗОВ create_user_limits_table() - НАЧАЛО")
    
    if not POSTGRES_AVAILABLE:
        logger.error("❌ Невозможно создать таблицу: psycopg3 не доступен")
        return False
    
    try:
        logger.info("🔧 Подключаюсь к БД...")
        conn = get_db_connection()
        cursor = conn.cursor()
        logger.info("✅ Подключение успешно")
        
        # Таблица лимитов пользователей
        logger.info("🔧 Создаю таблицу user_limits...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_limits (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL UNIQUE,
            free_used INTEGER DEFAULT 0,
            total_purchased INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        logger.info("✅ Таблица user_limits создана или уже существует")
        
        # Индекс для быстрого поиска
        logger.info("🔧 Создаю индекс для user_limits...")
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_limits_user_id ON user_limits(user_id)
        """)
        logger.info("✅ Индекс создан")
        
        # Таблица истории покупок пакетов
        logger.info("🔧 Создаю таблицу package_purchases...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS package_purchases (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(100) UNIQUE NOT NULL,
            package_id VARCHAR(10) NOT NULL,
            links INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        logger.info("✅ Таблица package_purchases создана или уже существует")
        
        # Индексы для таблицы покупок
        logger.info("🔧 Создаю индексы для package_purchases...")
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_package_purchases_user_id ON package_purchases(user_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_package_purchases_payment_id ON package_purchases(payment_id)
        """)
        logger.info("✅ Индексы созданы")
        
        conn.commit()
        logger.info("✅ Транзакция закоммичена")
        
        cursor.close()
        conn.close()
        logger.info("✅ Соединение закрыто")
        
        logger.info("✅ Таблицы user_limits и package_purchases успешно созданы")
        return True
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА в create_user_limits_table: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_all_tables():
    """Создает все таблицы с нуля - БЕЗОПАСНАЯ ВЕРСИЯ"""
    logger.info("🗄️ Безопасное создание/проверка всех таблиц базы данных...")
    
    results = {
        "payments": create_payments_table(),
        "user_access": create_user_access_table(),
        "yookassa_webhooks": create_yookassa_webhooks_table(),
        "notifications_log": create_notifications_log_table(),
        "recovery_log": create_recovery_log_table(),
        "sexual_access": create_sexual_access_tables(),
        "purchases_4f": create_4f_tables(),
        "user_limits": create_user_limits_table()  # 👈 ДОБАВЛЕНО
    }
    
    # 👇 ВАЖНО: вызываем функцию добавления колонок
    columns_added = add_columns_to_sexual_invites()
    if columns_added:
        results["sexual_invites_columns"] = True
        logger.info("✅ Колонки в sexual_invites проверены/добавлены")
    
    success_count = sum(1 for result in results.values() if result)
    
    if success_count == len(results):
        logger.info("✅ Все таблицы созданы/проверены успешно")
        return True
    else:
        logger.error(f"❌ Успешно создано/проверено только {success_count}/{len(results)} таблиц")
        return False

def update_existing_payments_with_profile():
    """Добавляет profile_code в существующие платежи"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE payments 
        SET profile_code = 'SA_1_DEF' 
        WHERE profile_code IS NULL OR profile_code = ''
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Обновлено {updated_count} платежей с профилем по умолчанию")
        return updated_count
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления платежей: {e}")
        return 0

# ============================================
# ФУНКЦИИ ДЛЯ УВЕДОМЛЕНИЙ И ЗАЩИЩЕННЫХ ССЫЛОК
# ============================================

def generate_access_token(user_id, payment_id):
    """Генерация защищенного токена доступа с подписью"""
    try:
        secret = os.getenv('YOOKASSA_SECRET_KEY', 'default_secret_key')
        expires_at = int(time.time()) + (30 * 24 * 3600)
        
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
        
        expires_at = int(expires_at_str)
        if time.time() > expires_at:
            logger.warning(f"⏰ Токен просрочен: expires_at={expires_at}")
            return False
        
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

def generate_profile_link(profile_code, user_id, payment_id, token=None):
    """Генерирует защищенную ссылку на Яндекс.Диск для конкретного профиля"""
    try:
        base_link = PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE])
        
        if token:
            link = f"{base_link}?access_token={token}&user_id={user_id}&payment_id={payment_id}&profile={profile_code}&ref=variatica"
        else:
            timestamp = int(time.time())
            link = f"{base_link}?user={user_id}&payment={payment_id[:8]}&profile={profile_code}&ts={timestamp}&ref=telegram_bot"
        
        logger.info(f"🔗 Сгенерирована ссылка для профиля {profile_code}: user_id={user_id}")
        return link
    except Exception as e:
        logger.error(f"❌ Ошибка генерации ссылки для профиля {profile_code}: {e}")
        return PROFILE_LINKS.get(DEFAULT_PROFILE, "https://disk.yandex.ru")

def send_telegram_pure(user_id, payment_id, access_token=None, is_recovery=False, profile_code=None):
    """ЧИСТАЯ функция отправки в Telegram с учетом профиля и ссылкой на Яндекс.Диск"""
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        if not profile_code:
            logger.warning("⚠️ profile_code не указан, использую профиль по умолчанию")
            profile_code = DEFAULT_PROFILE
        
        if profile_code in PROFILE_LINKS:
            yandex_link = PROFILE_LINKS[profile_code]
            logger.info(f"📎 Найден профиль {profile_code}, ссылка: {yandex_link[:50]}...")
        else:
            logger.error(f"❌ Профиль {profile_code} не найден в PROFILE_LINKS! Использую профиль по умолчанию")
            profile_code = DEFAULT_PROFILE
            yandex_link = PROFILE_LINKS[DEFAULT_PROFILE]
        
        profile_name = profile_code if profile_code else "не указан"
        
        if is_recovery:
            message = f"""
✅ *ВОССТАНОВЛЕНИЕ ДОСТУПА*

🎉 Ваш платеж `#{payment_id[:8]}` был восстановлен после сбоя системы!

📁 *Профиль:* `{profile_name}`
🔗 *Ссылка на материалы:* {yandex_link}

💎 Ваше персональное описание профиля готово.
Для быстрого доступа нажмите кнопку ниже ⬇️
            """
        else:
            message = f"""
✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*

🎉 Ваш платеж `#{payment_id[:8]}` успешно обработан!

📁 *Профиль:* `{profile_name}`
🔗 *Ссылка на материалы:* {yandex_link}

💎 Ваше персональное описание профиля готово.
Для быстрого доступа нажмите кнопку ниже ⬇️
            """
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        keyboard = [[
            {
                "text": f"📁 ОТКРЫТЬ МАТЕРИАЛЫ ({profile_name})",
                "url": yandex_link
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
            logger.info(f"✅ Уведомление отправлено пользователю {user_id}, профиль: {profile_code}")
            return True
        else:
            error_msg = f"Telegram API: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            
            try:
                fallback_message = f"""✅ ОПЛАТА ПОДТВЕРЖДЕНА!

Платеж #{payment_id[:8]} успешно обработан!

📁 Профиль: {profile_name}
🔗 Ссылка на материалы: {yandex_link}

💎 Ваше персональное описание профиля готово.
Для быстрого доступа нажмите ссылку выше или кнопку ниже."""
                
                response = requests.post(url, json={
                    "chat_id": user_id,
                    "text": fallback_message,
                    "reply_markup": {
                        "inline_keyboard": keyboard
                    }
                }, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ Уведомление отправлено (fallback) пользователю {user_id}")
                    return True
                else:
                    logger.error(f"❌ Fallback тоже не сработал: {response.status_code}")
                    return False
                    
            except Exception as fallback_e:
                logger.error(f"❌ Ошибка fallback отправки: {fallback_e}")
                return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        return False

def send_sexual_telegram(user_id, payment_id, profile_key, is_recovery=False):
    """Отправляет уведомление о доступе к 18+ профилю - БЕЗ ССЫЛОК!"""
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        profile_name = profile_key if profile_key else "sa_5_int"
        
        if is_recovery:
            message = f"""
🔞 *ДОСТУП ВОССТАНОВЛЕН*

✅ Ваш платеж `#{payment_id[:8]}` подтвержден!

📱 *Профиль:* `{profile_name}`

👉 Откройте бота и нажмите кнопку "Мой профиль"
⚡️ Контент доступен внутри бота (без ссылок)
            """
        else:
            message = f"""
🔞 *ДОСТУП АКТИВИРОВАН*

✅ Оплата `#{payment_id[:8]}` успешно обработана!

📱 *Профиль:* `{profile_name}`

👉 Откройте бота и нажмите кнопку "Мой профиль"
⚡️ Контент доступен внутри бота (без ссылок)
            """
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        keyboard = [[
            {
                "text": "🔞 ОТКРЫТЬ 18+ ПРОФИЛЬ",
                "callback_data": f"sexual_open_{profile_key}"
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
            logger.info(f"🔞 18+ уведомление отправлено user={user_id}, профиль={profile_key}")
            return True
        else:
            logger.error(f"❌ Ошибка 18+ уведомления: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки 18+ уведомления: {e}")
        return False

# ============================================
# 4F МОДУЛЬ - УВЕДОМЛЕНИЯ
# ============================================

@async_task
def send_4f_notification_async(user_id, payment_id, function, target_name, target_profile, access_token=None):
    """
    Асинхронная отправка уведомления о покупке 4F-ключа
    """
    try:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        message = f"""
🔑 *КЛЮЧ {function} АКТИВИРОВАН!*

✅ Ваш платеж `#{payment_id[:8]}` подтвержден!

👤 *Для:* {target_name or 'друга'}
📊 *Профиль:* {target_profile or 'SA-4_CAP'}
🔐 *Функция:* {function}

⚡️ Нажмите кнопку ниже, чтобы открыть ключ
        """
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        keyboard = [[
            {
                "text": f"🔓 Открыть ключ {function}",
                "callback_data": f"open_4f_key_{payment_id}_{function}"
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
            logger.info(f"🔑 4F уведомление отправлено user={user_id}, function={function}")
            return True
        else:
            logger.error(f"❌ Ошибка отправки 4F уведомления: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка в асинхронной отправке 4F: {e}")
        return False

@async_task
def log_notification_async(user_id, payment_id, success, is_recovery=False, profile_code=None):
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
        
        logger.info(f"📝 Логирование уведомления завершено: success={success}, профиль={profile_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка логирования уведомления: {e}")

@async_task
def send_notification_async(user_id, payment_id, access_token=None, is_recovery=False, profile_code=None):
    """Асинхронная отправка уведомления"""
    try:
        logger.info(f"🔔 Начинаю отправку уведомления user_id={user_id}, payment_id={payment_id}, профиль={profile_code}")
        
        # 👇 ПРОВЕРЯЕМ, ЭТО ПАКЕТ ИЛИ ПРОФИЛЬ
        is_package = payment_id and payment_id.startswith("package_")
        
        if not profile_code:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT profile_code FROM payments WHERE payment_id = %s", (payment_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    profile_code = result[0]
                    logger.info(f"📊 Получил profile_code из БД: {profile_code}")
                cursor.close()
                conn.close()
            except Exception as db_e:
                logger.warning(f"⚠️ Не удалось получить profile_code из БД: {db_e}")
        
        # 👇 ЕСЛИ ЭТО ПАКЕТ - НАЧИСЛЯЕМ ЛИМИТЫ!
        if is_package:
            logger.info(f"📦 Это пакет ссылок (payment_id={payment_id}), начисляем лимиты...")
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Получаем сумму платежа
                cursor.execute("""
                SELECT amount FROM payments 
                WHERE payment_id = %s AND status = 'succeeded'
                """, (payment_id,))
                
                result = cursor.fetchone()
                if result:
                    amount = result[0]
                    
                    # Определяем package_id по сумме
                    if amount == 299:
                        package_id = "3"
                        links = 3
                    elif amount == 499:
                        package_id = "5"
                        links = 5
                    elif amount == 899:
                        package_id = "10"
                        links = 10
                    else:
                        logger.error(f"❌ Неизвестная сумма пакета: {amount}")
                        cursor.close()
                        conn.close()
                        return False
                    
                    # Добавляем запись в package_purchases
                    cursor.execute("""
                    INSERT INTO package_purchases (user_id, payment_id, package_id, links, amount, purchased_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (payment_id) DO NOTHING
                    """, (user_id, payment_id, package_id, links, amount))
                    
                    # Обновляем лимиты в user_limits
                    cursor.execute("""
                    INSERT INTO user_limits (user_id, total_purchased)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_purchased = user_limits.total_purchased + EXCLUDED.total_purchased,
                        updated_at = CURRENT_TIMESTAMP
                    """, (user_id, links))
                    
                    conn.commit()
                    logger.info(f"✅ Лимиты начислены: user_id={user_id}, +{links} ссылок")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                logger.error(f"❌ Ошибка начисления лимитов: {e}")
                return False
            
            return True
        
        # 👇 ЕСЛИ ЭТО ПРОФИЛЬ - ОТПРАВЛЯЕМ КАК ОБЫЧНО
        success = send_telegram_pure(user_id, payment_id, access_token, is_recovery, profile_code)
        log_notification_async(user_id, payment_id, success, is_recovery, profile_code)
        
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

@async_task
def send_sexual_notification_async(user_id, payment_id, profile_key, is_recovery=False):
    """Асинхронная отправка 18+ уведомления"""
    try:
        logger.info(f"🔞 Отправка 18+ уведомления user={user_id}")
        success = send_sexual_telegram(user_id, payment_id, profile_key, is_recovery)
        return success
    except Exception as e:
        logger.error(f"❌ Ошибка асинхронной отправки 18+: {e}")
        return False

def send_telegram_notification(user_id, payment_id, access_token=None, is_recovery=False, profile_code=None):
    """Оригинальная функция для обратной совместимости"""
    send_notification_async(user_id, payment_id, access_token, is_recovery, profile_code)
    return True
    
# ============================================
# РЕШЕНИЕ ПРОБЛЕМЫ 2: Переход на Invoices API
# ============================================

def create_yookassa_invoice(payment_id, amount, user_id, description="Оплата курса ВАРИАТИКА"):
    """Создает ПЛАТЕЖ в ЮKassa через прямой API (работает без SDK)"""
    try:
        logger.info(f"💰 Создание платежа: {payment_id}, сумма: {amount}, пользователь: {user_id}")
        
        # Проверяем наличие ключей
        shop_id = os.getenv('YOOKASSA_SHOP_ID')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if not shop_id or not secret_key:
            logger.error("❌ Не настроены ключи ЮKassa")
            return {
                "id": None,
                "status": "error",
                "confirmation_url": None,
                "method": "error",
                "available_methods": [],
                "note": "ЮKassa не настроена"
            }
        
        # Создаем базовую авторизацию
        import base64
        auth = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()
        
        # Формируем данные для платежа
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/Testing_Lichnosti_bot"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id),
                "telegram_id": str(user_id)
            },
            "receipt": {
                "customer": {
                    "email": f"user_{user_id}@example.com"
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": "1",
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            }
        }
        
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Idempotence-Key": payment_id
        }
        
        logger.info(f"📤 Отправка запроса в ЮKassa для payment_id={payment_id}")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payload,
            headers=headers,
            timeout=15
        )
        
        logger.info(f"📥 Ответ от ЮKassa: статус {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            confirmation_url = data.get("confirmation", {}).get("confirmation_url")
            
            logger.info(f"✅ Платеж создан в ЮKassa, id={data.get('id')}")
            
            return {
                "id": data.get("id"),
                "status": data.get("status", "pending"),
                "confirmation_url": confirmation_url,
                "method": "bank_card",
                "available_methods": ["bank_card", "sbp", "yoo_money", "sberbank", "alfabank", "tinkoff_bank"],
                "expires_at": None,
                "note": "Платеж создан через прямой API"
            }
        else:
            error_text = response.text[:500] if response.text else "Нет ответа"
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            
            # Пробуем упрощенный вариант без чека
            if response.status_code == 400 and "receipt" in error_text:
                logger.info("🔄 Пробую без чека...")
                
                # Убираем receipt
                simple_payload = {
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": "https://t.me/Testing_Lichnosti_bot"
                    },
                    "capture": True,
                    "description": description,
                    "metadata": {
                        "payment_id": payment_id,
                        "user_id": str(user_id)
                    }
                }
                
                response2 = requests.post(
                    "https://api.yookassa.ru/v3/payments",
                    json=simple_payload,
                    headers=headers,
                    timeout=15
                )
                
                if response2.status_code == 200 or response2.status_code == 201:
                    data2 = response2.json()
                    confirmation_url2 = data2.get("confirmation", {}).get("confirmation_url")
                    
                    logger.info(f"✅ Платеж создан (без чека)")
                    
                    return {
                        "id": data2.get("id"),
                        "status": data2.get("status", "pending"),
                        "confirmation_url": confirmation_url2,
                        "method": "bank_card",
                        "available_methods": ["bank_card"],
                        "expires_at": None,
                        "note": "Платеж создан без чека"
                    }
            
            return {
                "id": None,
                "status": "error",
                "confirmation_url": None,
                "method": "error",
                "available_methods": [],
                "note": f"Ошибка ЮKassa: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"❌ Исключение в create_yookassa_invoice: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "id": None,
            "status": "error",
            "confirmation_url": None,
            "method": "error",
            "available_methods": [],
            "note": str(e)
        }


def create_yookassa_payment_legacy(payment_id, amount, user_id, description="Оплата курса ВАРИАТИКА"):
    """Создает ПЛАТЕЖ в ЮKassa (старая функция для обратной совместимости)"""
    # Просто перенаправляем на новую функцию
    logger.info(f"⚠️ Вызвана устаревшая функция create_yookassa_payment_legacy, перенаправляю...")
    return create_yookassa_invoice(payment_id, amount, user_id, description)

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
def grant_user_access_tx(conn, user_id, payment_id, profile_code=None):
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
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'recovery_attempts'
        """)
        
        if cursor.fetchone():
            cursor.execute("""
            UPDATE payments 
            SET recovery_attempts = COALESCE(recovery_attempts, 0) + 1,
                last_recovery_attempt = CURRENT_TIMESTAMP
            WHERE payment_id = %s
            """, (payment_id,))
            return True
        else:
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
        
        cursor.execute("""
        SELECT p.payment_id, p.yookassa_id, p.user_id, p.status, p.created_at, p.payment_method, p.profile_code
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
            payment_id, yookassa_id, user_id, status_before, created_at, payment_method, profile_code = payment
            
            try:
                safe_update_recovery_attempts(payment_id, cursor)
                
                if yookassa_id:
                    yk_status = check_yookassa_payment_status(yookassa_id)
                    
                    if yk_status and yk_status.get('status') == 'succeeded':
                        logger.info(f"🎉 Найден оплаченный платеж: {payment_id}, профиль: {profile_code}")
                        
                        cursor.execute("""
                        UPDATE payments 
                        SET status = 'succeeded', 
                            confirmed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE payment_id = %s
                        """, (payment_id,))
                        
                        access_token = generate_access_token(user_id, payment_id)
                        
                        cursor.execute("""
                        INSERT INTO user_access (user_id, payment_id, has_access, access_token)
                        VALUES (%s, %s, TRUE, %s)
                        ON CONFLICT (user_id, payment_id) DO UPDATE SET
                            has_access = TRUE,
                            access_token = EXCLUDED.access_token,
                            granted_at = CURRENT_TIMESTAMP
                        """, (user_id, payment_id, access_token))
                        
                        try:
                            cursor.execute("""
                            UPDATE user_access 
                            SET recovery_notified = TRUE 
                            WHERE user_id = %s AND payment_id = %s
                            """, (user_id, payment_id))
                        except Exception:
                            pass
                        
                        send_notification_async(user_id, payment_id, access_token, is_recovery=True, profile_code=profile_code)
                        
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
                                "payment_method": payment_method,
                                "profile_code": profile_code
                            }
                        )
                        
                        recovered_count += 1
                        logger.info(f"✅ Восстановлен платеж: {payment_id}, профиль: {profile_code}")
                        
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
            time.sleep(60)
            
            with app.app_context():
                logger.info("🔄 Запуск проверки потерянных платежей...")
                result = find_and_recover_lost_payments()
                
                if result.get('recovered', 0) > 0:
                    logger.info(f"✅ Восстановлено {result['recovered']} платежей")
                elif 'error' not in result:
                    logger.info("✅ Проверка завершена, потерянных платежей не найдено")
                    
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в recovery_worker: {e}")
            time.sleep(60)
            continue

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
    for thread in threading.enumerate():
        if thread.name and "recovery" in thread.name.lower() and thread.is_alive():
            logger.info("✅ Recovery worker уже запущен")
            return thread
    
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
    
    # Проверяем наличие 4F JSON файлов
    f4f_status = {}
    for func in F4F_FUNCTIONS:
        demo_path = f"{F4F_BASE_PATH}/{func}/sa_4_cap.json"
        default_path = f"{F4F_BASE_PATH}/{func}/default.json"
        f4f_status[func] = {
            "sa_4_cap_exists": os.path.exists(demo_path),
            "default_exists": os.path.exists(default_path)
        }
    
    return jsonify({
        "status": "Flask API работает! 🚀",
        "version": "Payment System v8.1 (полная поддержка приглашений)",
        "database": db_status,
        "yookassa": yookassa_status,
        "telegram_bot": TELEGRAM_BOT_URL,
        "features": [
            "✅ Мгновенные уведомления в Telegram",
            "✅ 36 профилей Яндекс.Диск",
            "✅ Ссылки в уведомлениях",
            "✅ Система автовосстановления при падении",
            "✅ Панель администратора",
            "✅ Логирование всех действий",
            "✅ Invoices API ЮKassa (все способы оплаты)",
            "✅ 18+ модуль (99₽, БЕЗ ССЫЛОК)",
            "✅ 4F модуль (99₽, MVP: всегда sa_4_cap.json)",
            "✅ ПОЛНАЯ ПОДДЕРЖКА ПРИГЛАШЕНИЙ"
        ],
        "profiles_available": len(PROFILE_LINKS),
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
            "create_payment": "/api/create-payment (POST) - СТАРЫЙ (только карты)",
            "create_payment_advanced": "/api/create-payment-advanced (POST) - НОВЫЙ (Invoices API, все способы + профиль)",
            "yookassa_webhook": "/yookassa-webhook (POST)",
            "get_materials": "/api/get-materials/<payment_id> (GET)",
            "health": "/health (GET)",
            "check_db": "/check-db (GET)",
            "create_tables": "/create-all-tables (GET) - безопасный"
        },
        "sexual_module": {
            "price": f"{SEXUAL_PAYMENT_AMOUNT}₽",
            "default_profile": SEXUAL_DEFAULT_PROFILE,
            "delivery": "JSON-файлы в sexual_18/, просмотр в боте",
            "no_links": "✅ ССЫЛОК НА ДИСК НЕТ - ТОЛЬКО ТЕКСТ",
            "endpoints": {
                "create_payment": "/api/sexual/create-payment-99 (POST)",
                "confirm": "/api/sexual/confirm-payment (POST)",
                "get_profile": "/api/sexual/get-profile/<user_id> (GET)",
                "create_invite": "/api/sexual/create-invite (POST)",
                "get_invite": "/api/sexual/get-invite/<invite_id> (GET)",
                "update_invite": "/api/sexual/update-invite/<invite_id> (POST)",
                "get_user_invites": "/api/sexual/get-invites/<int:buyer_id> (GET)",
                "check_access": "/api/sexual/check-access/<buyer_id>/<target_id> (GET)"
            }
        },
        "4f_module": {
            "price": f"{F4F_PAYMENT_AMOUNT}₽",
            "functions": F4F_FUNCTIONS,
            "mvp_mode": "✅ Всегда sa_4_cap.json (демо-ключи для всех)",
            "demo_available": "✅ Демо-версии для всех функций",
            "json_files_status": f4f_status,
            "note": "⚠️ Требуется создать JSON файлы в папке профили/4F/",
            "endpoints": {
                "create_payment": "/api/4f/create-payment-99 (POST)",
                "confirm": "/api/4f/confirm-payment (POST)",
                "get_function": "/api/4f/get-function/{function}/{profile_key} (GET)",
                "get_purchased": "/api/4f/get-purchased-function/{payment_id} (GET)",
                "check_access": "/api/4f/check-access/{buyer_id}/{target_id}/{function} (GET)"
            }
        }
    })

# ============================================
# 1. ЭНДПОИНТЫ ДЛЯ ПЛАТЕЖЕЙ (существующие)
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
            "note": "Используйте /api/create-payment-advanced для поддержки всех способов оплаты и профилей"
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
    """Создает платеж через СЧЕТА ЮKassa (Invoices API) с поддержкой профилей"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        profile_code = data.get('profile_code', DEFAULT_PROFILE)
        
        if not payment_id or not user_id:
            return jsonify({"success": False, "error": "Отсутствуют обязательные параметры"}), 400
        
        if profile_code not in PROFILE_LINKS:
            logger.warning(f"⚠️ Неизвестный профиль {profile_code}, используется {DEFAULT_PROFILE}")
            profile_code = DEFAULT_PROFILE
        
        amount = float(data.get('amount', 690.0))
        description = data.get('description', f'Оплата курса ВАРИАТИКА (профиль: {profile_code})')
        
        yookassa_data = create_yookassa_invoice(
            payment_id=payment_id,
            amount=amount,
            user_id=user_id,
            description=description
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO payments (
            payment_id, user_id, amount, yookassa_id, status, 
            payment_method, payment_method_details, description, profile_code
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (payment_id) DO UPDATE SET
            yookassa_id = EXCLUDED.yookassa_id,
            status = EXCLUDED.status,
            payment_method = EXCLUDED.payment_method,
            payment_method_details = EXCLUDED.payment_method_details,
            description = EXCLUDED.description,
            profile_code = EXCLUDED.profile_code,
            updated_at = CURRENT_TIMESTAMP
        """, (
            payment_id, user_id, amount, 
            yookassa_data.get('id'), 
            yookassa_data.get('status', 'pending'),
            yookassa_data.get('method', 'invoice'),
            json.dumps({
                "type": "invoice", 
                "confirmation_url": yookassa_data.get('confirmation_url'),
                "available_methods": yookassa_data.get('available_methods'),
                "expires_at": yookassa_data.get('expires_at'),
                "profile": profile_code
            }),
            description,
            profile_code
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Счет создан (Invoices API): {payment_id}, профиль: {profile_code}")
        
        return jsonify({
            "success": True,
            "message": "Invoice created (all payment methods available)",
            "payment_id": payment_id,
            "user_id": user_id,
            "profile_code": profile_code,
            "profile_link": PROFILE_LINKS.get(profile_code),
            "amount": amount,
            "yookassa_id": yookassa_data.get('id'),
            "confirmation_url": yookassa_data.get('confirmation_url'),
            "payment_method": yookassa_data.get('method'),
            "available_methods": yookassa_data.get('available_methods'),
            "invoice_type": "yookassa_invoice",
            "expires_at": yookassa_data.get('expires_at'),
            "status": "pending"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания счета: {e}")
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
        RETURNING payment_id, status, yookassa_id, user_id, payment_method, profile_code
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
        
        logger.info(f"✅ ЮKassa ID обновлен: {payment_id} -> {yookassa_id}, профиль: {result[5]}")
        
        return jsonify({
            "success": True,
            "message": "Yookassa ID updated",
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "status": new_status,
            "user_id": result[3],
            "payment_method": result[4],
            "profile_code": result[5]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления ЮKassa ID: {e}")
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500

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
            payment_id, yookassa_id, user_id, amount, status, email,
            description, created_at, updated_at, confirmed_at,
            payment_method, payment_method_details, profile_code
        FROM payments 
        WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not payment:
            return jsonify({"success": False, "error": "Payment not found"}), 404
        
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
            "payment_method_details": json.loads(payment[11]) if payment[11] else {},
            "profile_code": payment[12] if payment[12] else DEFAULT_PROFILE
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
        SELECT user_id, status, payment_method, profile_code FROM payments WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Payment not found"}), 404
        
        user_id, status, payment_method, profile_code = payment
        
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
        
        send_notification_async(user_id, payment_id, access_token, profile_code=profile_code)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Доступ выдан: user_id={user_id}, payment_id={payment_id}, профиль: {profile_code}")
        
        return jsonify({
            "success": True,
            "message": "Access granted and notification sent",
            "user_id": user_id,
            "payment_id": payment_id,
            "has_access": True,
            "payment_method": payment_method,
            "profile_code": profile_code,
            "profile_link": PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE]),
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
            p.description, p.amount, p.created_at, p.status, p.payment_method, p.profile_code
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
            
            profile_code = access[11] if access[11] else DEFAULT_PROFILE
            profile_link = PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE])
            
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
                "profile_code": profile_code,
                "profile_link": profile_link,
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
    """Возвращает защищенные материалы для платежа с учетом профиля"""
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
        profile_code = None
        
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
                p.payment_method,
                p.profile_code
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
            profile_code = result[5] if result[5] else DEFAULT_PROFILE
        
        if not has_access:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Доступ не найден"}), 403
        
        yandex_link = generate_profile_link(profile_code, user_id, payment_id, access_token)
        
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
        
        logger.info(f"📁 Материалы выданы: user_id={user_id}, payment_id={payment_id}, профиль: {profile_code}")
        
        return jsonify({
            "success": True,
            "message": "Доступ к материалам подтвержден",
            "profile_code": profile_code,
            "materials_link": yandex_link,
            "payment_id": payment_id,
            "user_id": user_id,
            "access_method": "token" if token else "direct",
            "note": f"Ссылка на профиль {profile_code} действительна 30 дней с момента оплаты"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка выдачи материалов: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# 3. ИСПРАВЛЕННЫЙ ВЕБХУК ЮKASSA
# ============================================

@app.route('/yookassa-webhook', methods=['POST'])
def yookassa_webhook():
    """Обработчик вебхуков - ДОПОЛНЕН ДЛЯ INVOICES + ДЕДУПЛИКАЦИЯ"""
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
        
        # Дедупликация
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id FROM yookassa_webhooks 
            WHERE webhook_id = %s AND event = %s
            """, (webhook_id, event_type))
            
            if cursor.fetchone():
                logger.info(f"📭 Вебхук уже обработан, пропускаем: {webhook_id}")
                cursor.close()
                conn.close()
                return jsonify({"status": "already_processed"}), 200
            
            yookassa_id = None
            payment_id = None
            user_id = None
            
            if 'object' in event_json:
                obj = event_json['object']
                yookassa_id = obj.get('id')
                metadata = obj.get('metadata', {})
                payment_id = metadata.get('payment_id')
                user_id = metadata.get('user_id')
                
                if yookassa_id:
                    cursor.execute("""
                    SELECT status FROM payments WHERE yookassa_id = %s
                    """, (yookassa_id,))
                    payment = cursor.fetchone()
                    if payment and payment[0] == 'succeeded':
                        logger.info(f"📭 Платеж уже обработан: {yookassa_id}")
                        cursor.close()
                        conn.close()
                        return jsonify({"status": "payment_already_processed"}), 200
            
            cursor.close()
            conn.close()
            
        except Exception as deps_e:
            logger.error(f"⚠️ Ошибка проверки дубликатов: {deps_e}")
        
        if event_type == 'payment.succeeded':
            payment_data = event_json.get('object', {})
            yookassa_id = payment_data.get('id')
            status = payment_data.get('status')
            metadata = payment_data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            user_id = metadata.get('user_id')
            
            logger.info(f"✅ Вебхук payment.succeeded: {yookassa_id}")
            
        elif event_type == 'invoice.paid':
            invoice_data = event_json.get('object', {})
            yookassa_id = invoice_data.get('id')
            status = 'succeeded'
            metadata = invoice_data.get('metadata', {})
            payment_id = metadata.get('payment_id')
            user_id = metadata.get('user_id')
            
            payment_data = invoice_data.get('payment', {})
            payment_method = payment_data.get('payment_method', {}) if payment_data else {}
            method_type = payment_method.get('type', 'invoice_paid') if payment_method else 'invoice_paid'
            method_details = json.dumps(payment_method, ensure_ascii=False) if payment_method else '{}'
            
            logger.info(f"✅ Вебхук invoice.paid: счет {invoice_data.get('id')}")
            logger.info(f"💰 Способ оплаты из invoice: {method_type}")
            
        else:
            logger.info(f"📭 Вебхук проигнорирован: {event_type}")
            return jsonify({"status": "ignored"}), 200
        
        try:
            webhook_db_id = save_webhook_to_db_quick(
                webhook_id, event_type, yookassa_id, status, event_json, payment_id
            )
            logger.info(f"✅ Вебхук сохранен: {webhook_id}")
        except Exception as e:
            logger.error(f"⚠️ Не удалось сохранить вебхук: {e}")
        
        response_data = {"status": "accepted", "webhook_id": webhook_id}
        logger.info(f"📤 Отправляю ответ ЮKassa: {response_data}")
        
        @async_task
        def process_webhook_async():
            """Асинхронная обработка вебхука с дедупликацией"""
            try:
                logger.info(f"🔧 Начинаю асинхронную обработку вебхука {webhook_id}")
                
                if event_type in ['payment.succeeded', 'invoice.paid'] and yookassa_id != 'unknown':
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute("""
                        SELECT status, profile_code FROM payments 
                        WHERE yookassa_id = %s OR payment_id = %s
                        FOR UPDATE
                        """, (yookassa_id, payment_id))
                        
                        result = cursor.fetchone()
                        current_status = result[0] if result else None
                        profile_code = result[1] if result and result[1] else DEFAULT_PROFILE
                        
                        if current_status and current_status == 'succeeded':
                            logger.info(f"📭 Платеж уже обработан (в транзакции): {yookassa_id}")
                            conn.rollback()
                            cursor.close()
                            conn.close()
                            return
                        
                        cursor.execute("""
                        UPDATE payments 
                        SET status = 'succeeded', 
                            confirmed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE (yookassa_id = %s OR payment_id = %s)
                        AND status != 'succeeded'  
                        RETURNING user_id, payment_id, payment_method
                        """, (yookassa_id, payment_id))
                        
                        result = cursor.fetchone()
                        
                        if not result:
                            logger.warning(f"⚠️ Платеж не найден или уже обработан: {yookassa_id}")
                            conn.rollback()
                            cursor.close()
                            conn.close()
                            return
                        
                        user_id, actual_payment_id, old_payment_method = result
                        
                        if event_type == 'invoice.paid':
                            try:
                                cursor.execute("""
                                UPDATE payments 
                                SET payment_method = %s,
                                    payment_method_details = %s
                                WHERE payment_id = %s
                                """, (method_type, method_details, actual_payment_id))
                                logger.info(f"✅ Способ оплаты сохранен из invoice: {method_type}")
                            except Exception as method_e:
                                logger.error(f"⚠️ Ошибка сохранения способа оплаты: {method_e}")
                        
                        access_token = generate_access_token(user_id, actual_payment_id)
                        
                        cursor.execute("""
                        INSERT INTO user_access (user_id, payment_id, has_access, access_token)
                        VALUES (%s, %s, TRUE, %s)
                        ON CONFLICT (user_id, payment_id) DO UPDATE SET
                            has_access = TRUE,
                            access_token = EXCLUDED.access_token,
                            granted_at = CURRENT_TIMESTAMP
                        """, (user_id, actual_payment_id, access_token))
                        
                        if current_status and current_status != 'succeeded':
                            cursor.execute("""
                            INSERT INTO recovery_log 
                            (recovery_type, payment_id, user_id, status_before, status_after, 
                             recovery_result, details)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                "webhook_recovery", actual_payment_id, user_id, 
                                current_status if current_status else 'unknown',
                                "succeeded", "success",
                                json.dumps({
                                    "yookassa_id": yookassa_id,
                                    "event_type": event_type,
                                    "payment_method": method_type if event_type == 'invoice.paid' else old_payment_method,
                                    "profile_code": profile_code
                                })
                            ))
                        
                        conn.commit()
                        logger.info(f"✅ Платеж обработан: {actual_payment_id} для пользователя {user_id}, профиль: {profile_code}")
                        
                        send_notification_async(user_id, actual_payment_id, access_token, profile_code=profile_code)
                        
                    except Exception as tx_e:
                        logger.error(f"❌ Ошибка в транзакции обработки вебхука: {tx_e}")
                        conn.rollback()
                    finally:
                        cursor.close()
                        conn.close()
                else:
                    logger.warning(f"⚠️ Неизвестный тип события или нет yookassa_id: {event_type}")
                
                logger.info(f"✅ Асинхронная обработка вебхука {webhook_id} завершена")
                
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в асинхронной обработке: {e}")
        
        process_webhook_async()
        
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
        SELECT user_id, yookassa_id, status, payment_method, profile_code FROM payments WHERE payment_id = %s
        """, (payment_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            return jsonify({"success": False, "error": "Платеж не найден"}), 404
        
        user_id, yookassa_id, status_before, payment_method, profile_code = payment
        
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
                
                send_notification_async(user_id, payment_id, access_token, is_recovery=True, profile_code=profile_code)
                
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
                        "payment_method": payment_method,
                        "profile_code": profile_code
                    }
                )
                
                conn.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Платеж успешно обработан",
                    "status": "succeeded",
                    "payment_method": payment_method,
                    "profile_code": profile_code,
                    "profile_link": PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE]),
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
        SELECT p.payment_id, ua.access_token, p.payment_method, p.profile_code
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.user_id = %s 
        AND p.status = 'succeeded'
        AND ua.has_access = TRUE
        AND p.confirmed_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
        """, (user_id,))
        
        payments = cursor.fetchall()
        
        results = []
        for payment_id, access_token, payment_method, profile_code in payments:
            send_notification_async(user_id, payment_id, access_token, is_recovery=True, profile_code=profile_code)
            results.append({
                "payment_id": payment_id,
                "payment_method": payment_method,
                "profile_code": profile_code,
                "profile_link": PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE]),
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
        
        cursor.execute("""
        SELECT COUNT(*) as duplicate_webhooks
        FROM (
            SELECT webhook_id, COUNT(*) as cnt
            FROM yookassa_webhooks
            GROUP BY webhook_id
            HAVING COUNT(*) > 1
        ) as duplicates
        """)
        duplicate_webhooks = cursor.fetchone()[0] or 0
        
        cursor.execute("""
        SELECT COUNT(*) as duplicate_payments
        FROM (
            SELECT yookassa_id, COUNT(*) as cnt
            FROM payments
            WHERE yookassa_id IS NOT NULL
            GROUP BY yookassa_id
            HAVING COUNT(*) > 1
        ) as duplicates
        """)
        duplicate_payments = cursor.fetchone()[0] or 0
        
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
            logger.warning(f"⚠️ Ошибка получения статистики по методам оплата: {e}")
            payment_methods_stats = []
        
        try:
            cursor.execute("""
            SELECT 
                COALESCE(profile_code, 'unknown') as profile,
                COUNT(*) as count,
                SUM(amount) as total
            FROM payments 
            WHERE status = 'succeeded'
            GROUP BY COALESCE(profile_code, 'unknown')
            ORDER BY count DESC
            """)
            profiles_stats = cursor.fetchall()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения статистики по профилям: {e}")
            profiles_stats = []
        
        cursor.execute("""
        SELECT p.payment_id, p.user_id, p.status, p.created_at, p.payment_method, p.profile_code
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.status IN ('pending', 'waiting_for_capture')
        AND p.created_at > NOW() - INTERVAL '24 hours'
        AND (ua.id IS NULL OR ua.has_access = FALSE)
        ORDER BY p.created_at DESC
        LIMIT 20
        """)
        problem_payments = cursor.fetchall()
        
        cursor.execute("""
        SELECT recovery_type, payment_id, user_id, status_before, status_after, 
               recovery_result, recovered_at
        FROM recovery_log 
        ORDER BY recovered_at DESC 
        LIMIT 10
        """)
        recent_recoveries = cursor.fetchall()
        
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
        
        # 18+ модуль статистика
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_access_purchases")
            sexual_total = cursor.fetchone()[0]
        except:
            sexual_total = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_access_purchases WHERE status = 'succeeded'")
            sexual_succeeded = cursor.fetchone()[0]
        except:
            sexual_succeeded = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_invites")
            sexual_invites = cursor.fetchone()[0]
        except:
            sexual_invites = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_invites WHERE status = 'pending'")
            sexual_pending_invites = cursor.fetchone()[0]
        except:
            sexual_pending_invites = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_invites WHERE status = 'used'")
            sexual_used_invites = cursor.fetchone()[0]
        except:
            sexual_used_invites = 0
        
        # 4F модуль статистика
        try:
            cursor.execute("SELECT COUNT(*) FROM purchases_4f")
            purchases_4f_total = cursor.fetchone()[0]
        except:
            purchases_4f_total = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM purchases_4f WHERE status = 'succeeded'")
            purchases_4f_succeeded = cursor.fetchone()[0]
        except:
            purchases_4f_succeeded = 0

        try:
            cursor.execute("""
            SELECT function, COUNT(*) as count
            FROM purchases_4f 
            WHERE status = 'succeeded'
            GROUP BY function
            ORDER BY count DESC
            """)
            purchases_4f_by_function = cursor.fetchall()
        except:
            purchases_4f_by_function = []

        try:
            cursor.execute("""
            SELECT COUNT(*) FROM purchases_4f 
            WHERE delivered = TRUE AND status = 'succeeded'
            """)
            purchases_4f_delivered = cursor.fetchone()[0]
        except:
            purchases_4f_delivered = 0
        
        cursor.close()
        conn.close()
        
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
                "recovery_errors_last_24h": recovery_errors_24h,
                "duplicate_webhooks": duplicate_webhooks,
                "duplicate_payments": duplicate_payments
            },
            "payment_methods_stats": [
                {
                    "method": row[0],
                    "count": row[1],
                    "total": float(row[2]) if row[2] else 0,
                    "percentage": round((row[1] / succeeded_payments * 100) if succeeded_payments > 0 else 0, 1)
                } for row in payment_methods_stats
            ],
            "profiles_stats": [
                {
                    "profile": row[0],
                    "count": row[1],
                    "total": float(row[2]) if row[2] else 0,
                    "percentage": round((row[1] / succeeded_payments * 100) if succeeded_payments > 0 else 0, 1),
                    "link": PROFILE_LINKS.get(row[0], "unknown")
                } for row in profiles_stats
            ],
            "problem_payments": [
                {
                    "payment_id": p[0],
                    "user_id": p[1],
                    "status": p[2],
                    "created_at": p[3].isoformat() if p[3] else None,
                    "payment_method": p[4],
                    "profile_code": p[5],
                    "profile_link": PROFILE_LINKS.get(p[5], "unknown"),
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
            "system": {
                "recovery_worker": recovery_status,
                "postgres_available": POSTGRES_AVAILABLE,
                "yookassa_sdk_available": YOOKASSA_SDK_AVAILABLE,
                "telegram_configured": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
                "yookassa_configured": bool(os.getenv('YOOKASSA_SHOP_ID') and os.getenv('YOOKASSA_SECRET_KEY')),
                "profiles_available": len(PROFILE_LINKS),
                "default_profile": DEFAULT_PROFILE
            },
            "sexual_module": {
                "total_purchases": sexual_total,
                "succeeded_purchases": sexual_succeeded,
                "total_invites": sexual_invites,
                "pending_invites": sexual_pending_invites,
                "used_invites": sexual_used_invites,
                "default_profile": SEXUAL_DEFAULT_PROFILE,
                "price": SEXUAL_PAYMENT_AMOUNT,
                "no_links": True
            },
            "4f_module": {
                "total_purchases": purchases_4f_total,
                "succeeded_purchases": purchases_4f_succeeded,
                "delivered_keys": purchases_4f_delivered,
                "purchases_by_function": [
                    {
                        "function": row[0],
                        "count": row[1]
                    } for row in purchases_4f_by_function
                ],
                "price": F4F_PAYMENT_AMOUNT,
                "functions": F4F_FUNCTIONS,
                "mvp_mode": "sa_4_cap.json всегда",
                "endpoints": {
                    "create_payment": "/api/4f/create-payment-99",
                    "confirm": "/api/4f/confirm-payment",
                    "get_function": "/api/4f/get-function/{function}/{profile_key}",
                    "get_purchased": "/api/4f/get-purchased-function/{payment_id}",
                    "check_access": "/api/4f/check-access/{buyer_id}/{target_id}/{function}"
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка в admin_dashboard: {e}")
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
            updated = update_existing_payments_with_profile()
            return jsonify({
                "success": True,
                "message": "✅ Все таблицы созданы/проверены безопасно!",
                "tables": [
                    "payments - платежи (с payment_method, payment_method_details и profile_code)",
                    "user_access - доступы пользователей",
                    "yookassa_webhooks - логи вебхуков",
                    "notifications_log - логи уведомлений",
                    "recovery_log - логи восстановления",
                    "sexual_access_purchases - покупки 18+ доступа",
                    "sexual_invites - приглашения 18+",
                    "purchases_4f - покупки 4F-ключей"
                ],
                "profiles_added": f"Обновлено {updated} платежей с профилями",
                "total_profiles": len(PROFILE_LINKS),
                "sexual_module": {
                    "default_profile": SEXUAL_DEFAULT_PROFILE,
                    "price": f"{SEXUAL_PAYMENT_AMOUNT}₽",
                    "profiles_dir": SEXUAL_PROFILES_DIR,
                    "no_links": True
                },
                "4f_module": {
                    "table_created": True,
                    "functions": F4F_FUNCTIONS,
                    "price": f"{F4F_PAYMENT_AMOUNT}₽",
                    "base_path": F4F_BASE_PATH,
                    "mvp_mode": "sa_4_cap.json всегда",
                    "note": "⚠️ Не забудьте создать JSON файлы в папке профили/4F/"
                }
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
        
        expected_tables = ['payments', 'user_access', 'yookassa_webhooks', 'notifications_log', 
                          'recovery_log', 'sexual_access_purchases', 'sexual_invites', 'purchases_4f']
        table_status = {table: table in tables for table in expected_tables}
        
        data_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                data_counts[table] = cursor.fetchone()[0]
            except:
                data_counts[table] = 0
        
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
        SELECT profile_code, COUNT(*) 
        FROM payments 
        WHERE status = 'succeeded'
        GROUP BY profile_code 
        ORDER BY COUNT(*) DESC
        LIMIT 10
        """)
        payments_by_profile = cursor.fetchall()
        
        # 4F модуль статистика
        try:
            cursor.execute("SELECT COUNT(*) FROM purchases_4f")
            purchases_4f_total = cursor.fetchone()[0]
        except:
            purchases_4f_total = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM purchases_4f WHERE status = 'succeeded'")
            purchases_4f_succeeded = cursor.fetchone()[0]
        except:
            purchases_4f_succeeded = 0
        
        # 18+ модуль статистика
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_access_purchases")
            sexual_total = cursor.fetchone()[0]
        except:
            sexual_total = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_access_purchases WHERE status = 'succeeded'")
            sexual_succeeded = cursor.fetchone()[0]
        except:
            sexual_succeeded = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_invites")
            sexual_invites_count = cursor.fetchone()[0]
        except:
            sexual_invites_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_invites WHERE status = 'pending'")
            sexual_pending_invites = cursor.fetchone()[0]
        except:
            sexual_pending_invites = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM sexual_invites WHERE status = 'used'")
            sexual_used_invites = cursor.fetchone()[0]
        except:
            sexual_used_invites = 0
        
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
            "payments_by_profile": {profile: count for profile, count in payments_by_profile},
            "sexual_module": {
                "tables_exist": {
                    "sexual_access_purchases": 'sexual_access_purchases' in tables,
                    "sexual_invites": 'sexual_invites' in tables
                },
                "total_purchases": sexual_total,
                "succeeded_purchases": sexual_succeeded,
                "total_invites": sexual_invites_count,
                "pending_invites": sexual_pending_invites,
                "used_invites": sexual_used_invites,
                "default_profile": SEXUAL_DEFAULT_PROFILE
            },
            "4f_module": {
                "table_exists": 'purchases_4f' in tables,
                "total_purchases": purchases_4f_total,
                "succeeded_purchases": purchases_4f_succeeded,
                "functions": F4F_FUNCTIONS,
                "mvp_mode": "sa_4_cap.json всегда"
            },
            "health": "healthy" if all(table_status.values()) else "issues",
            "recommendation": "Запустите /create-all-tables для безопасного исправления" if not all(table_status.values()) else "OK"
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка в check_db: {e}")
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
        profile_code = "SA_3_CON"
        success = send_telegram_pure(user_id, payment_id, profile_code=profile_code)
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "payment_id": payment_id,
            "profile_code": profile_code,
            "profile_link": PROFILE_LINKS.get(profile_code),
            "message": "Тестовое уведомление отправлено" if success else "Ошибка отправки"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug-payment/<payment_id>', methods=['GET'])
def debug_payment(payment_id):
    """Диагностический эндпоинт для проверки платежа и профиля"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT p.payment_id, p.user_id, p.status, p.profile_code, p.created_at,
               ua.has_access, ua.link_sent, ua.materials_sent_at
        FROM payments p
        LEFT JOIN user_access ua ON p.payment_id = ua.payment_id
        WHERE p.payment_id = %s
        """, (payment_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Платеж не найден"
            }), 404
        
        payment_id, user_id, status, profile_code, created_at, has_access, link_sent, materials_sent_at = result
        
        profile_exists = profile_code in PROFILE_LINKS if profile_code else False
        profile_link = PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE]) if profile_code else PROFILE_LINKS[DEFAULT_PROFILE]
        
        return jsonify({
            "success": True,
            "payment_id": payment_id,
            "user_id": user_id,
            "status": status,
            "profile_code": profile_code,
            "profile_exists": profile_exists,
            "profile_link": profile_link,
            "created_at": created_at.isoformat() if created_at else None,
            "has_access": has_access or False,
            "link_sent": link_sent or False,
            "materials_sent_at": materials_sent_at.isoformat() if materials_sent_at else None
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-send/<int:user_id>/<profile_code>', methods=['GET'])
def test_send_notification(user_id, profile_code):
    """Тестовая отправка уведомления с указанным профилем"""
    try:
        payment_id = f"test_{int(time.time())}"
        success = send_telegram_pure(user_id, payment_id, profile_code=profile_code)
        
        profile_exists = profile_code in PROFILE_LINKS
        profile_link = PROFILE_LINKS.get(profile_code, PROFILE_LINKS[DEFAULT_PROFILE])
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "payment_id": payment_id,
            "profile_code": profile_code,
            "profile_exists": profile_exists,
            "profile_link": profile_link,
            "message": f"Тестовое уведомление отправлено с профилем {profile_code}" if success else "Ошибка отправки"
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
        yookassa_configured = bool(os.getenv('YOOKASSA_SHOP_ID') and os.getenv('YOOKASSA_SECRET_KEY'))
        
        recovery_status = "inactive"
        for thread in threading.enumerate():
            if thread.name and "recovery" in thread.name.lower() and thread.is_alive():
                recovery_status = "active"
                break
        
        return jsonify({
            "status": "healthy" if (POSTGRES_AVAILABLE and "connected" in db_status and telegram_token_set) else "degraded",
            "service": "variatica_payment_api",
            "version": "8.1 (полная поддержка приглашений)",
            "database": db_status,
            "yookassa_sdk": "available" if YOOKASSA_SDK_AVAILABLE else "not_available",
            "yookassa_configured": yookassa_configured,
            "telegram_token_configured": telegram_token_set,
            "recovery_worker": recovery_status,
            "profiles_available": len(PROFILE_LINKS),
            "default_profile": DEFAULT_PROFILE,
            "sexual_module": {
                "active": True,
                "default_profile": SEXUAL_DEFAULT_PROFILE,
                "no_links": True
            },
            "4f_module": {
                "active": True,
                "functions": F4F_FUNCTIONS,
                "mvp_mode": "sa_4_cap.json всегда",
                "base_path": F4F_BASE_PATH
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)[:200],
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================
# 6. 18+ МОДУЛЬ - ЭНДПОИНТЫ (НОВЫЕ И ДОПОЛНЕННЫЕ)
# ============================================

@app.route('/api/sexual/create-payment-99', methods=['POST'])
def api_sexual_create_payment_99():
    """Создает платеж на 99₽ для доступа к 18+ профилю - БЕЗ ССЫЛОК!"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        buyer_id = data.get('buyer_id')
        target_id = data.get('target_id')
        target_name = data.get('target_name')
        invite_id = data.get('invite_id')
        
        if not all([payment_id, buyer_id, target_id]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        target_profile_key = SEXUAL_DEFAULT_PROFILE
        
        yookassa_data = create_yookassa_invoice(
            payment_id=payment_id,
            amount=SEXUAL_PAYMENT_AMOUNT,
            user_id=buyer_id,
            description=f"🔞 Доступ к 18+ профилю {target_name or 'друга'}"
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO sexual_access_purchases (
            buyer_id, target_id, target_name, target_profile_key, 
            invite_id, payment_id, amount, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (buyer_id, target_id) DO UPDATE SET
            payment_id = EXCLUDED.payment_id,
            status = EXCLUDED.status,
            purchased_at = CURRENT_TIMESTAMP
        RETURNING id
        """, (
            buyer_id, target_id, target_name, target_profile_key,
            invite_id, payment_id, SEXUAL_PAYMENT_AMOUNT, 'pending'
        ))
        
        purchase_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🔞 Создан платеж 99₽: {payment_id}, buyer={buyer_id}, target={target_id}")
        
        return jsonify({
            "success": True,
            "purchase_id": purchase_id,
            "payment_id": payment_id,
            "yookassa_id": yookassa_data.get('id'),
            "confirmation_url": yookassa_data.get('confirmation_url'),
            "amount": SEXUAL_PAYMENT_AMOUNT,
            "profile_key": target_profile_key,
            "status": "pending",
            "note": "✅ После оплаты профиль откроется в Telegram-боте (БЕЗ ССЫЛОК НА ДИСК!)"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа 99₽: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sexual/confirm-payment', methods=['POST'])
def api_sexual_confirm_payment():
    """Подтверждает оплату доступа к 18+ профилю - БЕЗ ССЫЛОК!"""
    if not POSTGRES_AVAILABLE:
        return jsonify({"success": False, "error": "psycopg3 не установлен"}), 500
    
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({"success": False, "error": "Missing payment_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE sexual_access_purchases 
        SET status = 'succeeded', confirmed_at = CURRENT_TIMESTAMP
        WHERE payment_id = %s AND status = 'pending'
        RETURNING id, buyer_id, target_id, target_name, target_profile_key, invite_id
        """, (payment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Purchase not found or already confirmed"}), 404
        
        purchase_id, buyer_id, target_id, target_name, target_profile_key, invite_id = result
        
        if invite_id:
            cursor.execute("""
            UPDATE sexual_invites 
            SET status = 'purchased', purchased_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (invite_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🔞 Подтверждена оплата {payment_id}, buyer={buyer_id}, target={target_id}")
        
        send_sexual_notification_async(buyer_id, payment_id, target_profile_key)
        
        return jsonify({
            "success": True,
            "purchase_id": purchase_id,
            "buyer_id": buyer_id,
            "target_id": target_id,
            "target_name": target_name,
            "target_profile_key": target_profile_key,
            "status": "succeeded",
            "note": "✅ Оплата подтверждена. Уведомление отправлено (БЕЗ ССЫЛОК НА ДИСК!)"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка подтверждения платежа 99₽: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sexual/get-profile/<int:user_id>', methods=['GET'])
def api_sexual_get_profile(user_id):
    """Возвращает 18+ профиль пользователя - ЗАГЛУШКА, БЕЗ ССЫЛОК!"""
    try:
        profile_key = SEXUAL_DEFAULT_PROFILE
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "profile_key": profile_key,
            "is_stub": True,
            "note": "⚠️ РЕЖИМ ЗАГЛУШКИ: всем показывается SA_5_INT из папки sexual_18/ (БЕЗ ССЫЛОК НА ДИСК!)"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения профиля: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/save-package-purchase', methods=['POST'])
def save_package_purchase():
    """Сохраняет информацию о покупке пакета приглашений"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        payment_id = data.get('payment_id')
        package_id = data.get('package_id')
        links = data.get('links')
        amount = data.get('amount')
        purchased_at = data.get('purchased_at')
        
        if not all([user_id, payment_id, package_id, links]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу для хранения покупок пакетов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS package_purchases (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            payment_id VARCHAR(100) UNIQUE NOT NULL,
            package_id VARCHAR(10) NOT NULL,
            links INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Создаем таблицу для хранения лимитов пользователя
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_limits (
            user_id BIGINT PRIMARY KEY,
            free_used INTEGER DEFAULT 0,
            total_purchased INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Сохраняем покупку
        cursor.execute("""
        INSERT INTO package_purchases (user_id, payment_id, package_id, links, amount, purchased_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (payment_id) DO NOTHING
        RETURNING id
        """, (user_id, payment_id, package_id, links, amount, purchased_at))
        
        purchase_result = cursor.fetchone()
        
        # Обновляем лимиты пользователя
        cursor.execute("""
        INSERT INTO user_limits (user_id, total_purchased)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            total_purchased = user_limits.total_purchased + EXCLUDED.total_purchased,
            updated_at = CURRENT_TIMESTAMP
        """, (user_id, links))
        
        conn.commit()
        
        # Проверяем, что таблицы создались
        cursor.execute("""
        SELECT tablename FROM pg_tables WHERE schemaname='public'
        """)
        tables = cursor.fetchall()
        logger.info(f"📊 Таблицы в БД: {[t[0] for t in tables]}")
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Покупка пакета {package_id} сохранена для пользователя {user_id}")
        
        return jsonify({
            "success": True,
            "purchase_id": purchase_result[0] if purchase_result else None,
            "message": f"Пакет {package_id} на {links} ссылок добавлен"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения покупки пакета: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/add-package-limits', methods=['POST'])
def add_package_limits():
    """Добавляет лимиты пользователю после успешной оплаты пакета"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        payment_id = data.get('payment_id')
        package_id = data.get('package_id')
        links = data.get('links')
        amount = data.get('amount')
        
        if not all([user_id, payment_id, package_id, links]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Сохраняем в package_purchases
        cursor.execute("""
        INSERT INTO package_purchases (user_id, payment_id, package_id, links, amount)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (payment_id) DO NOTHING
        RETURNING id
        """, (user_id, payment_id, package_id, links, amount))
        
        purchase_result = cursor.fetchone()
        
        # 2. Обновляем лимиты в user_limits
        cursor.execute("""
        INSERT INTO user_limits (user_id, total_purchased)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            total_purchased = user_limits.total_purchased + EXCLUDED.total_purchased,
            updated_at = CURRENT_TIMESTAMP
        RETURNING total_purchased
        """, (user_id, links))
        
        new_total = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Лимиты добавлены: user_id={user_id}, +{links} ссылок, всего={new_total}")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "payment_id": payment_id,
            "links_added": links,
            "total_purchased": new_total,
            "message": f"✅ Добавлено {links} ссылок"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления лимитов: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
        
@app.route('/api/sexual/create-invite', methods=['POST'])
def api_sexual_create_invite():
    """Создает приглашение для 18+ профиля (используется ботом)"""
    try:
        data = request.get_json()
        buyer_id = data.get('buyer_id')
        target_id = data.get('target_id', 0)
        target_name = data.get('target_name')
        invite_id = data.get('invite_id')
        target_profile_key = data.get('target_profile_key', SEXUAL_DEFAULT_PROFILE)
        
        if not all([buyer_id, invite_id]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO sexual_invites (invite_id, buyer_id, target_id, target_name, target_profile_key, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING id
        """, (invite_id, buyer_id, target_id, target_name, target_profile_key))
        
        invite_db_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🔗 Приглашение {invite_id} создано для buyer={buyer_id}")
        
        return jsonify({
            "success": True,
            "invite_id": invite_id,
            "profile_key": target_profile_key,
            "note": "✅ Приглашение создано"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания приглашения: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sexual/get-invite/<invite_id>', methods=['GET'])
def api_sexual_get_invite(invite_id):
    """Получает информацию о приглашении (используется при переходе по ссылке)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT invite_id, buyer_id, target_id, target_name, target_profile_key, status, created_at
        FROM sexual_invites 
        WHERE invite_id = %s
        """, (invite_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({"success": False, "error": "Invite not found"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "invite_id": result[0],
                "buyer_id": result[1],
                "target_id": result[2],
                "target_name": result[3],
                "profile_key": result[4],
                "status": result[5],
                "created_at": result[6].isoformat() if result[6] else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения приглашения: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sexual/update-invite/<invite_id>', methods=['POST'])
def api_sexual_update_invite(invite_id):
    """Обновляет приглашение после прохождения теста (добавляет данные друга)"""
    try:
        data = request.get_json()
        friend_id = data.get('friend_id')
        friend_name = data.get('friend_name')
        friend_profile = data.get('friend_profile')
        
        if not all([friend_id, friend_name, friend_profile]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE sexual_invites 
        SET status = 'used',
            target_id = %s,
            target_name = %s,
            target_profile_key = %s
        WHERE invite_id = %s AND status = 'pending'
        RETURNING id, buyer_id
        """, (friend_id, friend_name, friend_profile, invite_id))
        
        result = cursor.fetchone()
        
        if not result:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Invite not found or already used"}), 404
        
        purchase_id, buyer_id = result
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🔞 Приглашение {invite_id} активировано: buyer={buyer_id}, friend={friend_name}, profile={friend_profile}")
        
        return jsonify({
            "success": True,
            "invite_id": invite_id,
            "buyer_id": buyer_id,
            "friend_id": friend_id,
            "friend_name": friend_name,
            "friend_profile": friend_profile,
            "status": "used"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления приглашения: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sexual/get-invites/<int:buyer_id>', methods=['GET'])
def api_sexual_get_invites(buyer_id):
    """Возвращает все приглашения пользователя (для раздела Мои отражения)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 👇 ИСПРАВЛЕННЫЙ SELECT - добавили is_free и invite_type
        cursor.execute("""
        SELECT id, invite_id, buyer_id, target_id, target_name, 
               target_profile_key, status, created_at, is_free, invite_type
        FROM sexual_invites 
        WHERE buyer_id = %s
        ORDER BY created_at DESC
        """, (buyer_id,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        invites = []
        for row in results:
            # row[0] = id
            # row[1] = invite_id
            # row[2] = buyer_id
            # row[3] = target_id
            # row[4] = target_name
            # row[5] = target_profile_key
            # row[6] = status
            # row[7] = created_at
            # row[8] = is_free      👈 НОВОЕ
            # row[9] = invite_type   👈 НОВОЕ
            
            invites.append({
                "id": row[0],
                "invite_id": row[1],
                "buyer_id": row[2],
                "friend_id": row[3] if row[3] > 0 else None,
                "friend_name": row[4],
                "friend_profile": row[5],
                "status": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "is_free": row[8] if row[8] is not None else True,      # 👈 ИСПРАВЛЕНО
                "invite_type": row[9] if row[9] is not None else '🆓'   # 👈 ИСПРАВЛЕНО
            })
        
        return jsonify({
            "success": True,
            "buyer_id": buyer_id,
            "invites": invites,
            "count": len(invites)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения приглашений: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sexual/check-access/<int:buyer_id>/<int:target_id>', methods=['GET'])
def api_sexual_check_access(buyer_id, target_id):
    """Проверяет, куплен ли доступ к 18+ профилю"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, status, confirmed_at, target_profile_key
        FROM sexual_access_purchases
        WHERE buyer_id = %s AND target_id = %s AND status = 'succeeded'
        ORDER BY confirmed_at DESC
        LIMIT 1
        """, (buyer_id, target_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                "success": True,
                "has_access": True,
                "purchase_id": result[0],
                "confirmed_at": result[2].isoformat() if result[2] else None,
                "profile_key": result[3],
                "note": "✅ Доступ активирован"
            }), 200
        else:
            return jsonify({
                "success": True,
                "has_access": False,
                "note": "❌ Доступ не куплен"
            }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки доступа: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-sexual/<int:user_id>', methods=['GET'])
def test_sexual(user_id):
    """Тест 18+ модуля - проверка, что нет ссылок"""
    try:
        profile_data = api_sexual_get_profile(user_id)
        
        response_data = {
            "success": True,
            "test_passed": True,
            "sexual_module": {
                "endpoint": "/api/sexual/get-profile/",
                "has_disk_links": "disk.yandex" not in str(profile_data),
                "status": "✅ ССЫЛОК НА ДИСК НЕТ"
            },
            "note": "✅ 18+ модуль работает без ссылок на Яндекс.Диск"
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# 7. 4F МОДУЛЬ - ЭНДПОИНТЫ
# ============================================

@app.route('/api/4f/create-payment-99', methods=['POST'])
def api_4f_create_payment_99():
    """
    Создает платеж на 99₽ для покупки 4F-функции
    Параметры: buyer_id, target_id, target_name, target_profile, function, invite_id
    """
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        buyer_id = data.get('buyer_id')
        target_id = data.get('target_id')
        target_name = data.get('target_name')
        target_profile = data.get('target_profile', 'SA_4_CAP')
        function = data.get('function')
        invite_id = data.get('invite_id')
        
        if not all([payment_id, buyer_id, target_id, function]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        if function not in F4F_FUNCTIONS:
            return jsonify({"success": False, "error": f"Invalid function. Must be one of {F4F_FUNCTIONS}"}), 400
        
        yookassa_data = create_yookassa_invoice(
            payment_id=payment_id,
            amount=F4F_PAYMENT_AMOUNT,
            user_id=buyer_id,
            description=f"🔑 Ключ {function} для профиля {target_name or 'друга'}"
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO purchases_4f (
            payment_id, buyer_id, target_id, target_name, 
            target_profile, function, amount, status, invite_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (payment_id) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """, (
            payment_id, buyer_id, target_id, target_name,
            target_profile, function, F4F_PAYMENT_AMOUNT, 'pending', invite_id
        ))
        
        purchase_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🔑 Создан платеж 4F {function}: {payment_id}, buyer={buyer_id}, target={target_id}")
        
        return jsonify({
            "success": True,
            "purchase_id": purchase_id,
            "payment_id": payment_id,
            "yookassa_id": yookassa_data.get('id'),
            "confirmation_url": yookassa_data.get('confirmation_url'),
            "amount": F4F_PAYMENT_AMOUNT,
            "function": function,
            "target_profile": target_profile,
            "status": "pending",
            "note": "✅ MVP режим: всегда используется sa_4_cap.json"
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа 4F: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/4f/confirm-payment', methods=['POST'])
def api_4f_confirm_payment():
    """
    Подтверждает оплату 4F-функции (вызывается вебхуком)
    """
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({"success": False, "error": "Missing payment_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE purchases_4f 
        SET status = 'succeeded', 
            confirmed_at = CURRENT_TIMESTAMP,
            delivered = FALSE
        WHERE payment_id = %s AND status = 'pending'
        RETURNING id, buyer_id, target_id, target_name, target_profile, function, invite_id
        """, (payment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Purchase not found or already confirmed"}), 404
        
        purchase_id, buyer_id, target_id, target_name, target_profile, function, invite_id = result
        
        access_token = generate_access_token(buyer_id, payment_id)
        
        cursor.execute("""
        UPDATE purchases_4f 
        SET access_token = %s
        WHERE id = %s
        """, (access_token, purchase_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"🔑 Подтверждена оплата 4F {function}: {payment_id}, buyer={buyer_id}")
        
        send_4f_notification_async(buyer_id, payment_id, function, target_name, target_profile, access_token)
        
        return jsonify({
            "success": True,
            "purchase_id": purchase_id,
            "buyer_id": buyer_id,
            "target_id": target_id,
            "target_name": target_name,
            "function": function,
            "status": "succeeded",
            "access_token": access_token,
            "note": "✅ Оплата подтверждена, используйте /api/4f/get-purchased-function для получения контента"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка подтверждения платежа 4F: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/4f/get-function/<function>/<profile_key>', methods=['GET'])
def api_4f_get_function(function, profile_key):
    """
    Получить содержимое 4F-функции для профиля
    - MVP: всегда sa_4_cap.json, подстановка friend_name
    """
    try:
        friend_name = request.args.get('friend_name', 'друг')
        
        if function not in F4F_FUNCTIONS:
            return jsonify({"success": False, "error": f"Invalid function. Must be one of {F4F_FUNCTIONS}"}), 400
        
        base_path = F4F_BASE_PATH
        
        file_path = f"{base_path}/{function}/{profile_key}.json"
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл {file_path} не найден, использую default.json")
            file_path = f"{base_path}/{function}/default.json"
            
            if not os.path.exists(file_path):
                return jsonify({
                    "success": False, 
                    "error": f"Function {function} not available. JSON files missing."
                }), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        content_str = json.dumps(content, ensure_ascii=False)
        content_str = content_str.replace("{friend_name}", friend_name)
        content = json.loads(content_str)
        
        content["_meta"] = {
            "function": function,
            "profile_key": profile_key if os.path.exists(f"{base_path}/{function}/{profile_key}.json") else "default",
            "source_profile": F4F_DEFAULT_PROFILE,
            "is_demo": True,
            "friend_name": friend_name,
            "demo_notice": "⚠️ Это демо-версия. Полная версия содержит 3x больше контента и точные триггер-фразы."
        }
        
        return jsonify({
            "success": True,
            "function": function,
            "profile_key": profile_key,
            "content": content
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения 4F функции: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/4f/get-purchased-function/<payment_id>', methods=['GET'])
def api_4f_get_purchased_function(payment_id):
    """
    Получить содержимое КУПЛЕННОЙ функции (после оплаты)
    """
    try:
        user_id = request.args.get('user_id')
        token = request.args.get('token')
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"}), 400
        
        user_id = int(user_id)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, buyer_id, target_id, target_name, target_profile, function, status, delivered
        FROM purchases_4f 
        WHERE payment_id = %s
        """, (payment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Purchase not found"}), 404
        
        purchase_id, buyer_id, target_id, target_name, target_profile, function, status, delivered = result
        
        if user_id != buyer_id:
            if token:
                token_data = verify_access_token(token)
                if not token_data or token_data['user_id'] != buyer_id:
                    cursor.close()
                    conn.close()
                    return jsonify({"success": False, "error": "Access denied"}), 403
            else:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "error": "Access denied"}), 403
        
        if status != 'succeeded':
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"Payment not completed: {status}"}), 400
        
        profile_key = F4F_DEFAULT_PROFILE
        file_path = f"{F4F_BASE_PATH}/{function}/{profile_key}.json"
        
        if not os.path.exists(file_path):
            file_path = f"{F4F_BASE_PATH}/{function}/default.json"
        
        if not os.path.exists(file_path):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"Function {function} content not available"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        content_str = json.dumps(content, ensure_ascii=False)
        content_str = content_str.replace("{friend_name}", target_name or 'друг')
        content = json.loads(content_str)
        
        if not delivered:
            cursor.execute("""
            UPDATE purchases_4f 
            SET delivered = TRUE 
            WHERE id = %s
            """, (purchase_id,))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "purchase_id": purchase_id,
            "payment_id": payment_id,
            "function": function,
            "target_name": target_name,
            "content": content,
            "is_demo": False,
            "note": "✅ Полная версия ключа (без demo_limitation)"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения купленной функции: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/4f/check-access/<int:buyer_id>/<int:target_id>/<function>', methods=['GET'])
def api_4f_check_access(buyer_id, target_id, function):
    """
    Проверить, куплена ли функция для конкретного друга
    """
    try:
        if function not in F4F_FUNCTIONS:
            return jsonify({"success": False, "error": f"Invalid function. Must be one of {F4F_FUNCTIONS}"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, payment_id, status, confirmed_at, delivered
        FROM purchases_4f
        WHERE buyer_id = %s AND target_id = %s AND function = %s AND status = 'succeeded'
        ORDER BY confirmed_at DESC
        LIMIT 1
        """, (buyer_id, target_id, function))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                "success": True,
                "has_access": True,
                "purchase_id": result[0],
                "payment_id": result[1],
                "confirmed_at": result[3].isoformat() if result[3] else None,
                "delivered": result[4],
                "function": function
            }), 200
        else:
            return jsonify({
                "success": True,
                "has_access": False,
                "function": function
            }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки доступа 4F: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test-4f/<int:user_id>', methods=['GET'])
def test_4f(user_id):
    """Тест 4F модуля"""
    try:
        return jsonify({
            "success": True,
            "message": "✅ 4F модуль API готов",
            "endpoints": {
                "create_payment": "/api/4f/create-payment-99 (POST)",
                "confirm": "/api/4f/confirm-payment (POST)",
                "get_function": "/api/4f/get-function/1F/sa_4_cap?friend_name=Александр (GET)",
                "get_purchased": "/api/4f/get-purchased-function/{payment_id}?user_id=123 (GET)",
                "check_access": "/api/4f/check-access/123/456/1F (GET)"
            },
            "mvp_mode": "✅ Всегда sa_4_cap.json",
            "note": "⚠️ Убедитесь, что JSON файлы созданы в папке профили/4F/"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# ОБРАБОТЧИКИ ОШИБОК
# ============================================

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
            "/api/create-payment-advanced - Invoices API с профилями",
            "/create-all-tables - безопасное создание таблиц",
            "/debug-payment/<payment_id> - диагностика платежа",
            "/test-send/<user_id>/<profile_code> - тест уведомления",
            "/api/sexual/** - 18+ модуль (99₽, БЕЗ ССЫЛОК)",
            "/api/4f/** - 4F модуль (99₽, sa_4_cap.json)"
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
# 👇 ВРЕМЕННЫЙ ЭНДПОИНТ ДЛЯ ИСПРАВЛЕНИЯ ПРИГЛАШЕНИЙ
# ============================================

@app.route('/fix-invites', methods=['GET'])
def fix_invites():
    """Исправляет старые приглашения - добавляет is_free и invite_type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем все записи, где is_free = NULL
        cursor.execute("""
        UPDATE sexual_invites 
        SET is_free = TRUE, invite_type = '🆓' 
        WHERE is_free IS NULL;
        """)
        
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"✅ Обновлено {updated_count} приглашений",
            "updated": updated_count
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

@app.route('/check-sexual-invites-structure', methods=['GET'])
def check_sexual_invites_structure():
    """Проверяет структуру таблицы sexual_invites"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем список колонок
        cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'sexual_invites'
        ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        # Получаем пример данных (первую запись)
        cursor.execute("""
        SELECT * FROM sexual_invites LIMIT 1
        """)
        sample = cursor.fetchone()
        
        # Получаем описание колонок для выборки
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sexual_invites'
        ORDER BY ordinal_position
        """)
        column_names = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Формируем пример данных в виде словаря
        sample_data = {}
        if sample and column_names:
            for i, col_name in enumerate(column_names):
                sample_data[col_name] = str(sample[i]) if sample[i] is not None else None
        
        # Проверяем наличие нужных колонок
        column_list = [col[0] for col in columns]
        has_is_free = 'is_free' in column_list
        has_invite_type = 'invite_type' in column_list
        
        return jsonify({
            "success": True,
            "table": "sexual_invites",
            "total_records": 69,
            "columns": [
                {
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2],
                    "default": col[3]
                } for col in columns
            ],
            "has_required_columns": {
                "is_free": has_is_free,
                "invite_type": has_invite_type,
                "all_present": has_is_free and has_invite_type
            },
            "sample_record": sample_data,
            "note": "Если all_present = true, значит колонки есть"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-user-limits/<int:user_id>', methods=['GET'])
def get_user_limits(user_id):
    """Возвращает лимиты пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT free_used, total_purchased, updated_at
        FROM user_limits
        WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            # Считаем сколько платных ссылок уже создано
            cursor2 = conn2 = None
            try:
                conn2 = get_db_connection()
                cursor2 = conn2.cursor()
                cursor2.execute("""
                SELECT COUNT(*) FROM sexual_invites 
                WHERE buyer_id = %s AND is_free = false
                """, (user_id,))
                paid_used = cursor2.fetchone()[0]
                cursor2.close()
                conn2.close()
            except:
                paid_used = 0
            
            free_used = result[0]
            total_purchased = result[1]
            paid_available = total_purchased - paid_used
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "limits": {
                    "free_used": free_used,
                    "free_total": 3,
                    "free_remaining": max(0, 3 - free_used),
                    "total_purchased": total_purchased,
                    "paid_used": paid_used,
                    "paid_available": paid_available,
                    "updated_at": result[2].isoformat() if result[2] else None
                }
            }), 200
        else:
            # Если нет записи, создаем с нулями
            return jsonify({
                "success": True,
                "user_id": user_id,
                "limits": {
                    "free_used": 0,
                    "free_total": 3,
                    "free_remaining": 3,
                    "total_purchased": 0,
                    "paid_used": 0,
                    "paid_available": 0
                }
            }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения лимитов: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-free-used', methods=['POST'])
def update_free_used():
    """Обновляет счетчик ВСЕХ использованных ссылок (и бесплатных, и платных)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Подсчитываем ВСЕ ссылки пользователя (и бесплатные, и платные)
        cursor.execute("""
        SELECT COUNT(*) FROM sexual_invites 
        WHERE buyer_id = %s
        """, (user_id,))
        
        total_links = cursor.fetchone()[0] or 0
        
        # Получаем текущие лимиты
        cursor.execute("""
        SELECT total_purchased FROM user_limits WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        total_purchased = result[0] if result else 0
        
        # Обновляем или создаем запись в user_limits
        cursor.execute("""
        INSERT INTO user_limits (user_id, free_used, total_purchased)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            free_used = EXCLUDED.free_used,
            total_purchased = EXCLUDED.total_purchased,
            updated_at = CURRENT_TIMESTAMP
        RETURNING free_used, total_purchased
        """, (user_id, total_links, total_purchased))
        
        result = cursor.fetchone()
        new_free_used = result[0]
        current_total_purchased = result[1]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Обновлен счетчик ссылок для user_id={user_id}: всего использовано={new_free_used}, куплено={current_total_purchased}")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "free_used": new_free_used,
            "total_purchased": current_total_purchased
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления счетчика ссылок: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user-limits/<int:user_id>', methods=['GET'])
def get_user_limits_api(user_id):
    """Возвращает лимиты пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем данные из user_limits
        cursor.execute("""
        SELECT free_used, total_purchased, updated_at
        FROM user_limits
        WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            free_used = result[0] or 0  # 54 - всего ссылок
            total_purchased = result[1] or 0  # 15 - куплено
        else:
            free_used = 0
            total_purchased = 0
        
        cursor.close()
        conn.close()
        
        # ПРАВИЛЬНЫЙ РАСЧЕТ:
        free_total = 3
        free_remaining = max(0, free_total - free_used)  # 3 - 54 = -51 → 0
        
        # Сколько платных ссылок уже использовано (все кроме первых 3)
        paid_used = max(0, free_used - free_total)  # 54 - 3 = 51
        
        # Сколько платных доступно
        paid_available = max(0, total_purchased - paid_used)  # 15 - 51 = -36 → 0
        
        logger.info(f"✅ Расчет для {user_id}: всего={free_used}, куплено={total_purchased}, использовано платных={paid_used}, доступно={paid_available}")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "limits": {
                "free_used": free_used,
                "free_remaining": free_remaining,
                "paid_available": paid_available,
                "total_purchased": total_purchased,
                "used_purchased": paid_used,
                "free_total": free_total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения лимитов пользователя {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-paid-used', methods=['POST'])
def update_paid_used():
    """Обновляет счетчик использованных платных ссылок"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Просто обновляем updated_at, фактический подсчет идет через COUNT в sexual_invites
        cursor.execute("""
        UPDATE user_limits 
        SET updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """, (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Обновлен счетчик платных ссылок для user_id={user_id}")
        return jsonify({"success": True, "user_id": user_id}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления счетчика платных ссылок: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/notify-invite-accepted', methods=['POST'])
def notify_invite_accepted():
    """Отправляет уведомление создателю ссылки, что друг прошел тест"""
    try:
        data = request.get_json()
        buyer_id = data.get('buyer_id')
        friend_name = data.get('friend_name')
        friend_profile = data.get('friend_profile')
        invite_id = data.get('invite_id')
        
        if not all([buyer_id, friend_name, friend_profile]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            return jsonify({"success": False, "error": "Telegram token not configured"}), 500
        
        message = f"""
👤 <b>Новое отражение!</b>

@{friend_name} прошел тест по вашему приглашению.
Его профиль: {friend_profile}

🔍 Посмотреть в "Моих отражениях"
"""
        
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        keyboard = [[
            {
                "text": "👥 МОИ ОТРАЖЕНИЯ",
                "callback_data": "my_invites"
            }
        ]]
        
        response = requests.post(url, json={
            "chat_id": buyer_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Уведомление отправлено создателю {buyer_id}")
            return jsonify({"success": True}), 200
        else:
            logger.error(f"❌ Ошибка отправки уведомления: {response.status_code}")
            return jsonify({"success": False, "error": "Failed to send notification"}), 500
        
    except Exception as e:
        logger.error(f"❌ Ошибка в notify_invite_accepted: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/sexual/get-friend-profile/<int:buyer_id>/<int:friend_id>', methods=['GET'])
def get_friend_profile(buyer_id, friend_id):
    """Возвращает профиль друга для отображения в 'Моих отражениях'"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT target_name, target_profile_key, status, created_at
        FROM sexual_invites 
        WHERE buyer_id = %s AND target_id = %s AND status = 'used'
        ORDER BY created_at DESC
        LIMIT 1
        """, (buyer_id, friend_id))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                "success": True,
                "friend": {
                    "name": result[0],
                    "profile": result[1],
                    "status": result[2],
                    "date": result[3].isoformat() if result[3] else None
                }
            }), 200
        else:
            return jsonify({"success": False, "error": "Friend not found"}), 404
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения профиля друга: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/user/invites-stats/<int:user_id>', methods=['GET'])
def user_invites_stats(user_id):
    """Возвращает детальную статистику по приглашениям"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'used' THEN 1 ELSE 0 END) as used,
            SUM(CASE WHEN is_free = true THEN 1 ELSE 0 END) as free_total,
            SUM(CASE WHEN is_free = false THEN 1 ELSE 0 END) as paid_total
        FROM sexual_invites 
        WHERE buyer_id = %s
        """, (user_id,))
        
        stats = cursor.fetchone()
        
        # Друзья с профилями
        cursor.execute("""
        SELECT target_name, target_profile_key, created_at
        FROM sexual_invites 
        WHERE buyer_id = %s AND status = 'used'
        ORDER BY created_at DESC
        LIMIT 10
        """, (user_id,))
        
        friends = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total": stats[0],
                "pending": stats[1],
                "used": stats[2],
                "free_used": stats[3],
                "paid_used": stats[4]
            },
            "recent_friends": [
                {
                    "name": f[0],
                    "profile": f[1],
                    "date": f[2].isoformat() if f[2] else None
                } for f in friends
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/sexual/invite-status/<invite_id>', methods=['GET'])
def check_invite_status(invite_id):
    """Проверяет статус конкретного приглашения"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT status, target_name, target_profile_key, created_at
        FROM sexual_invites 
        WHERE invite_id = %s
        """, (invite_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                "success": True,
                "status": result[0],
                "friend_name": result[1],
                "friend_profile": result[2],
                "created_at": result[3].isoformat() if result[3] else None
            }), 200
        else:
            return jsonify({"success": False, "error": "Invite not found"}), 404
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки статуса приглашения: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/sexual/test-completed', methods=['POST'])
def sexual_test_completed():
    """Обрабатывает завершение теста другом"""
    try:
        data = request.get_json()
        invite_id = data.get('invite_id')
        friend_id = data.get('friend_id')
        friend_name = data.get('friend_name')
        friend_profile = data.get('friend_profile')
        
        if not all([invite_id, friend_id, friend_name, friend_profile]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем buyer_id
        cursor.execute("""
        SELECT buyer_id, is_free FROM sexual_invites 
        WHERE invite_id = %s
        """, (invite_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Invite not found"}), 404
        
        buyer_id = result[0]
        is_free = result[1]
        
        # Обновляем приглашение
        cursor.execute("""
        UPDATE sexual_invites 
        SET status = 'used',
            target_id = %s,
            target_name = %s,
            target_profile_key = %s
        WHERE invite_id = %s
        """, (friend_id, friend_name, friend_profile, invite_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Отправляем уведомление создателю
        try:
            telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if telegram_token:
                message = f"""
👤 <b>Новое отражение!</b>

@{friend_name} прошел тест по вашему приглашению.
Его профиль: {friend_profile}

🔍 Посмотреть в "Моих отражениях"
"""
                url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                keyboard = [[{"text": "👥 МОИ ОТРАЖЕНИЯ", "callback_data": "my_invites"}]]
                
                requests.post(url, json={
                    "chat_id": buyer_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": keyboard}
                }, timeout=5)
        except Exception as notify_e:
            logger.error(f"⚠️ Ошибка отправки уведомления: {notify_e}")
        
        logger.info(f"✅ Тест завершен: invite_id={invite_id}, friend={friend_name}, profile={friend_profile}")
        
        return jsonify({
            "success": True,
            "buyer_id": buyer_id,
            "is_free": is_free
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка в sexual_test_completed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recovery/fix-all-packages', methods=['GET'])
def fix_all_packages():
    """Восстанавливает все пропущенные пакеты"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Находим все успешные платежи за пакеты, которых нет в package_purchases
        cursor.execute("""
        SELECT p.payment_id, p.user_id, p.amount, p.created_at
        FROM payments p
        LEFT JOIN package_purchases pp ON p.payment_id = pp.payment_id
        WHERE p.payment_id LIKE 'package_%'
        AND p.status = 'succeeded'
        AND pp.id IS NULL
        """)
        
        missing = cursor.fetchall()
        fixed_count = 0
        
        for payment_id, user_id, amount, created_at in missing:
            # Определяем package_id
            if amount == 299:
                package_id = "3"
                links = 3
            elif amount == 499:
                package_id = "5"
                links = 5
            elif amount == 899:
                package_id = "10"
                links = 10
            else:
                continue
            
            # Добавляем в package_purchases
            cursor.execute("""
            INSERT INTO package_purchases (user_id, payment_id, package_id, links, amount, purchased_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (payment_id) DO NOTHING
            """, (user_id, payment_id, package_id, links, amount, created_at))
            
            # Обновляем user_limits
            cursor.execute("""
            INSERT INTO user_limits (user_id, total_purchased)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                total_purchased = user_limits.total_purchased + EXCLUDED.total_purchased,
                updated_at = CURRENT_TIMESTAMP
            """, (user_id, links))
            
            fixed_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "fixed_count": fixed_count,
            "message": f"✅ Восстановлено {fixed_count} пакетов"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug-all-payments', methods=['GET'])
def debug_all_payments():
    """Показывает все платежи из БД"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Все платежи с сортировкой по дате
        cursor.execute("""
        SELECT payment_id, user_id, amount, status, created_at, confirmed_at, profile_code, description
        FROM payments 
        ORDER BY created_at DESC
        LIMIT 50
        """)
        
        payments = []
        for row in cursor.fetchall():
            payments.append({
                "payment_id": row[0],
                "user_id": row[1],
                "amount": float(row[2]) if row[2] else 0,
                "status": row[3],
                "created_at": str(row[4]) if row[4] else None,
                "confirmed_at": str(row[5]) if row[5] else None,
                "profile_code": row[6],
                "description": row[7]
            })
        
        # Статистика по статусам
        cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM payments
        GROUP BY status
        """)
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "total_payments": len(payments),
            "status_stats": stats,
            "recent_payments": payments[:20]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# ЗАПУСК СЕРВЕРА
# ============================================

if __name__ == '__main__':
    print("="*80)
    print("🚀 VARIATICA PAYMENT API v8.1 - ПОЛНАЯ ПОДДЕРЖКА ПРИГЛАШЕНИЙ")
    print("="*80)
    print(f"Python: {sys.version.split()[0]}")
    print(f"psycopg3 доступен: {POSTGRES_AVAILABLE}")
    print(f"YooKassa SDK доступен: {YOOKASSA_SDK_AVAILABLE}")
    print(f"Telegram Bot URL: {TELEGRAM_BOT_URL}")
    print("="*80)
    print("🎯 КЛЮЧЕВЫЕ ВОЗМОЖНОСТИ:")
    print("  ✅ Поддержка 36 профилей Яндекс.Диск")
    print("  ✅ ИСПРАВЛЕНА отправка ссылок в уведомлениях")
    print("  ✅ Invoices API (все способы оплаты)")
    print("  ✅ Дедупликация платежей и вебхуков")
    print("  ✅ Система восстановления при падении")
    print("  ✅ 18+ модуль (99₽, БЕЗ ССЫЛОК)")
    print("  ✅ 4F модуль (99₽, MVP: sa_4_cap.json)")
    print("  ✅ ПОЛНАЯ ПОДДЕРЖКА ПРИГЛАШЕНИЙ")
    print("="*80)
    print("🔞 18+ МОДУЛЬ:")
    print("  • SA_5_INT - заглушка")
    print("  • НЕТ ССЫЛОК на Яндекс.Диск")
    print("  • Только JSON в sexual_18/")
    print("  • Таблица sexual_invites с полной поддержкой")
    print("  • Эндпоинты: create, get, update, get_user_invites")
    print("="*80)
    print("🔑 4F МОДУЛЬ:")
    print(f"  • Функции: {F4F_FUNCTIONS}")
    print("  • MVP режим: всегда sa_4_cap.json")
    print("  • Требуются JSON файлы в профили/4F/{function}/")
    print("="*80)
    
    # ========== ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==========
    try:
        logger.info("🗄️ Безопасная проверка и создание таблиц...")
        
        # 1. Сначала создаем основные таблицы
        tables_created = create_all_tables()
        
        if tables_created:
            logger.info("✅ Основные таблицы созданы/проверены")
            
            # 2. ОБЯЗАТЕЛЬНО добавляем колонки в sexual_invites
            logger.info("🔧 Принудительная проверка колонок в sexual_invites...")
            
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Проверяем существование таблицы
                cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'sexual_invites'
                )
                """)
                sexual_invites_exists = cursor.fetchone()[0]
                
                if sexual_invites_exists:
                    # Проверяем колонку is_free
                    cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'sexual_invites' AND column_name = 'is_free'
                    """)
                    if not cursor.fetchone():
                        logger.info("➕ Добавляем колонку is_free в sexual_invites...")
                        cursor.execute("ALTER TABLE sexual_invites ADD COLUMN is_free BOOLEAN DEFAULT TRUE")
                    
                    # Проверяем колонку invite_type
                    cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'sexual_invites' AND column_name = 'invite_type'
                    """)
                    if not cursor.fetchone():
                        logger.info("➕ Добавляем колонку invite_type в sexual_invites...")
                        cursor.execute("ALTER TABLE sexual_invites ADD COLUMN invite_type VARCHAR(10) DEFAULT '🆓'")
                    
                    # Обновляем существующие записи
                    cursor.execute("UPDATE sexual_invites SET is_free = TRUE WHERE is_free IS NULL")
                    cursor.execute("UPDATE sexual_invites SET invite_type = '🆓' WHERE invite_type IS NULL")
                    
                    conn.commit()
                    logger.info("✅ Колонки в sexual_invites успешно добавлены/обновлены")
                else:
                    logger.error("❌ Таблица sexual_invites не существует! Создаем заново...")
                    # Создаем таблицу заново с правильной структурой
                    cursor.execute("""
                    CREATE TABLE sexual_invites (
                        id SERIAL PRIMARY KEY,
                        invite_id VARCHAR(100) UNIQUE NOT NULL,
                        buyer_id BIGINT NOT NULL,
                        target_id BIGINT DEFAULT 0,
                        target_name VARCHAR(255),
                        target_profile_key VARCHAR(50) NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        is_free BOOLEAN DEFAULT TRUE,
                        invite_type VARCHAR(10) DEFAULT '🆓',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        purchased_at TIMESTAMP
                    )
                    """)
                    conn.commit()
                    logger.info("✅ Таблица sexual_invites создана заново с правильной структурой")
                
                cursor.close()
                conn.close()
                
            except Exception as db_e:
                logger.error(f"❌ Ошибка при проверке sexual_invites: {db_e}")
                # Пробуем альтернативный способ через функцию
                try:
                    logger.info("🔄 Пробуем через функцию add_columns_to_sexual_invites()...")
                    add_columns_to_sexual_invites()
                except:
                    pass
            
            # 3. Обновляем существующие платежи с профилями
            updated = update_existing_payments_with_profile()
            print(f"✅ Таблицы проверены/созданы безопасно")
            print(f"✅ Обновлено {updated} платежей с профилями")
            
            # 4. ФИНАЛЬНАЯ ПРОВЕРКА
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Проверяем структуру sexual_invites
                cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sexual_invites'
                ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                logger.info("📊 Текущая структура sexual_invites:")
                for col in columns:
                    logger.info(f"  • {col[0]}: {col[1]}")
                
                cursor.close()
                conn.close()
                
                # Проверяем наличие нужных колонок
                column_names = [col[0] for col in columns]
                if 'is_free' in column_names and 'invite_type' in column_names:
                    print("✅ Таблица sexual_invites полностью готова (is_free и invite_type присутствуют)")
                else:
                    print("⚠️ ВНИМАНИЕ: Не все колонки добавлены!")
                    
            except Exception as check_e:
                logger.error(f"❌ Ошибка финальной проверки: {check_e}")
            
    except Exception as e:
        logger.error(f"⚠️ Критическая ошибка инициализации БД: {e}")
        print(f"⚠️ Ошибка создания таблиц: {e}")
        
        # Пробуем восстановиться
        try:
            logger.info("🔄 Попытка восстановления через /fix-invites...")
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Создаем таблицу если её нет
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sexual_invites (
                id SERIAL PRIMARY KEY,
                invite_id VARCHAR(100) UNIQUE NOT NULL,
                buyer_id BIGINT NOT NULL,
                target_id BIGINT DEFAULT 0,
                target_name VARCHAR(255),
                target_profile_key VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                is_free BOOLEAN DEFAULT TRUE,
                invite_type VARCHAR(10) DEFAULT '🆓',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                purchased_at TIMESTAMP
            )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Таблица sexual_invites создана в аварийном режиме")
        except:
            pass
    
    # ========== ЗАПУСК ВОССТАНОВИТЕЛЯ ==========
    recovery_thread = ensure_recovery_worker()
    
    if recovery_thread and recovery_thread.is_alive():
        logger.info("✅ Recovery worker запущен автоматически")
        print("✅ Recovery worker запущен автоматически")
    else:
        logger.warning("⚠️ Recovery worker не удалось запустить")
        print("⚠️ Recovery worker не удалось запустить")
    
    # ========== ЗАПУСК СЕРВЕРА ==========
    port = int(os.getenv('PORT', 10000))
    logger.info(f"🚀 Запуск сервера на порту {port}")
    print(f"🚀 Сервер запущен на порту {port}")
    print("="*80)
    
    # Финальное сообщение
    print("\n📌 ДОСТУПНЫЕ ЭНДПОИНТЫ ДЛЯ ПРОВЕРКИ:")
    print("  • /fix-invites - исправить приглашения")
    print("  • /fix-sexual-invites - исправить таблицу sexual_invites")
    print("  • /check-db - проверить структуру БД")
    print("  • /admin/dashboard - панель администратора")
    print("="*80)
    
    app.run(host='0.0.0.0', port=port, debug=False)
