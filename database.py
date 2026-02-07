"""
database.py - PostgreSQL версия для Render
Исправленная версия с детальным логированием ошибок
"""

import os
import logging
import json
from datetime import datetime
from contextlib import contextmanager

# Настройка логирования
logger = logging.getLogger(__name__)

class Database:
    """PostgreSQL для Render"""
    
    def __init__(self):
        # Получаем DATABASE_URL от Render
        database_url = os.getenv('DATABASE_URL', '')
        
        # Проверяем, это PostgreSQL от Render?
        if database_url and ('postgres' in database_url or 'dpg-' in database_url or 'render.com' in database_url):
            self.is_postgres = True
            self.database_url = database_url
            
            # Исправляем URL если нужно
            self._fix_database_url()
            
            logger.info(f"🗄️ Используется PostgreSQL на Render")
            logger.info(f"   URL: {self.database_url[:60]}...")
        else:
            # Fallback на SQLite для локальной разработки
            self.is_postgres = False
            logger.warning("⚠️ DATABASE_URL не настроен, используем SQLite (fallback)")
            self.sqlite_path = "/tmp/variatica.db"
    
    def _fix_database_url(self):
        """Исправляет URL для Render PostgreSQL"""
        # Добавляем порт если нет
        if ':5432' not in self.database_url and '.render.com/' in self.database_url:
            self.database_url = self.database_url.replace('.render.com/', '.render.com:5432/')
        
        # Добавляем sslmode=require если нет
        if 'sslmode=' not in self.database_url:
            if '?' in self.database_url:
                self.database_url += '&sslmode=require'
            else:
                self.database_url += '?sslmode=require'
    
    def get_connection(self):
        """Подключение к базе данных"""
        if self.is_postgres:
            try:
                # Используем psycopg3 (работает с Python 3.13)
                import psycopg
                from psycopg.rows import dict_row
                
                logger.debug(f"🔗 Подключение к PostgreSQL: {self.database_url[:50]}...")
                conn = psycopg.connect(
                    self.database_url,
                    row_factory=dict_row
                )
                logger.debug("✅ Подключение к PostgreSQL установлено")
                return conn
                
            except ImportError as e:
                logger.error("❌ psycopg не установлен. Добавьте в requirements.txt: psycopg[binary]>=3.2")
                logger.error(f"   Ошибка импорта: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
                raise
        else:
            # SQLite fallback
            import sqlite3
            try:
                conn = sqlite3.connect(self.sqlite_path)
                conn.row_factory = sqlite3.Row
                # Включаем WAL для лучшей производительности
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                return conn
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к SQLite: {e}")
                raise
    
    @contextmanager
    def db_cursor(self):
        """Контекстный менеджер для работы с БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка БД в транзакции: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def init_database(self):
        """Инициализация таблиц в базе данных"""
        logger.info("🗄️ Инициализация базы данных...")
        
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    # ========== PostgreSQL ВЕРСИЯ ==========
                    
                    # Таблица платежей
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
                    
                    # Индексы для таблицы payments
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
                    
                    # Таблица доступа пользователей
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
                    
                    cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_access_has_access 
                    ON user_access(has_access)
                    """)
                    
                    # Таблица webhook уведомлений
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
                    
                    # Таблица доставки
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deliveries (
                        id SERIAL PRIMARY KEY,
                        payment_id VARCHAR(255),
                        user_id BIGINT NOT NULL,
                        delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT DEFAULT '[]',
                        delivery_status VARCHAR(50) DEFAULT 'pending'
                    )
                    """)
                    
                    logger.info("✅ Таблицы PostgreSQL созданы на Render")
                    
                else:
                    # ========== SQLite ВЕРСИЯ (для разработки) ==========
                    
                    # Таблица платежей
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payment_id TEXT UNIQUE NOT NULL,
                        yookassa_id TEXT,
                        user_id INTEGER NOT NULL,
                        amount REAL DEFAULT 690.00,
                        status TEXT DEFAULT 'pending',
                        email TEXT,
                        description TEXT DEFAULT 'Полный пакет ВАРИАТИКА',
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confirmed_at TIMESTAMP
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_payment_id 
                    ON payments(payment_id)
                    """)
                    
                    cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_payments_user_id 
                    ON payments(user_id)
                    """)
                    
                    # Таблица доступа пользователей
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_access (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        payment_id TEXT,
                        has_access BOOLEAN DEFAULT 0,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT DEFAULT '[]',
                        UNIQUE(user_id, payment_id)
                    )
                    """)
                    
                    # Таблица webhook уведомлений
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS yookassa_webhooks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        webhook_id TEXT NOT NULL,
                        event TEXT NOT NULL,
                        payment_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        payload TEXT,
                        processed BOOLEAN DEFAULT 0
                    )
                    """)
                    
                    # Таблица доставки
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deliveries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payment_id TEXT,
                        user_id INTEGER NOT NULL,
                        delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT DEFAULT '[]',
                        delivery_status TEXT DEFAULT 'pending'
                    )
                    """)
                    
                    logger.info("✅ Таблицы SQLite созданы")
            
            logger.info("✅ База данных успешно инициализирована")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            # Детали для отладки в Render логах
            print("="*60)
            print("DATABASE INITIALIZATION ERROR:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Is PostgreSQL: {self.is_postgres}")
            print(f"Database URL present: {'DATABASE_URL' in os.environ}")
            print("="*60)
            return False
    
    # ========== ОСНОВНЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ПЛАТЕЖАМИ ==========
    
    def create_payment(self, payment_data):
        """Создает новый платеж - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ
            print("="*60)
            print("DATABASE.CREATE_PAYMENT CALLED")
            print(f"Payment data received: {json.dumps(payment_data, indent=2)}")
            print(f"Database type: {'PostgreSQL' if self.is_postgres else 'SQLite'}")
            print("="*60)
            
            # 1. Проверяем обязательные поля
            required_fields = ['payment_id', 'user_id']
            for field in required_fields:
                if field not in payment_data:
                    error_msg = f"Missing required field: {field}"
                    logger.error(f"❌ {error_msg}")
                    print(f"ERROR: {error_msg}")
                    print(f"Available fields: {list(payment_data.keys())}")
                    return False
            
            # 2. Подготавливаем значения
            payment_id = str(payment_data['payment_id'])
            user_id = int(payment_data['user_id'])
            amount = float(payment_data.get('amount', 1.0))
            description = payment_data.get('description', 'Тестовый платеж')
            email = payment_data.get('email', '')
            metadata = json.dumps(payment_data.get('metadata', {}))
            status = payment_data.get('status', 'pending')
            yookassa_id = payment_data.get('yookassa_id')
            
            print(f"Prepared values:")
            print(f"  payment_id: {payment_id}")
            print(f"  user_id: {user_id}")
            print(f"  amount: {amount}")
            print(f"  status: {status}")
            print(f"  yookassa_id: {yookassa_id}")
            
            # 3. Выполняем SQL запрос
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    # PostgreSQL версия
                    if yookassa_id:
                        sql = """
                        INSERT INTO payments 
                        (payment_id, user_id, amount, description, email, metadata, status, yookassa_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (payment_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        yookassa_id = EXCLUDED.yookassa_id,
                        updated_at = CURRENT_TIMESTAMP
                        RETURNING id, payment_id, status
                        """
                        values = (payment_id, user_id, amount, description, email, metadata, status, yookassa_id)
                    else:
                        sql = """
                        INSERT INTO payments 
                        (payment_id, user_id, amount, description, email, metadata, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (payment_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                        RETURNING id, payment_id, status
                        """
                        values = (payment_id, user_id, amount, description, email, metadata, status)
                else:
                    # SQLite версия
                    if yookassa_id:
                        sql = """
                        INSERT OR REPLACE INTO payments 
                        (payment_id, user_id, amount, description, email, metadata, status, yookassa_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """
                        values = (payment_id, user_id, amount, description, email, metadata, status, yookassa_id)
                    else:
                        sql = """
                        INSERT OR REPLACE INTO payments 
                        (payment_id, user_id, amount, description, email, metadata, status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """
                        values = (payment_id, user_id, amount, description, email, metadata, status)
                
                print(f"Executing SQL: {sql}")
                print(f"With values: {values}")
                
                cursor.execute(sql, values)
                
                if self.is_postgres:
                    result = cursor.fetchone()
                    print(f"PostgreSQL result: {result}")
            
            logger.info(f"✅ Создан/обновлен платеж: {payment_id} для пользователя {user_id}")
            print(f"SUCCESS: Payment {payment_id} created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            # ДЕТАЛИ ДЛЯ ОТЛАДКИ В RENDER ЛОГАХ
            print("="*60)
            print("DATABASE.CREATE_PAYMENT ERROR DETAILS:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Payment data: {payment_data}")
            print(f"Is PostgreSQL: {self.is_postgres}")
            print(f"Database URL: {'Set' if hasattr(self, 'database_url') else 'Not set'}")
            
            # Дополнительная диагностика для PostgreSQL ошибок
            if self.is_postgres:
                try:
                    import psycopg
                    if isinstance(e, psycopg.Error):
                        print(f"PostgreSQL error code: {e.pgcode}")
                        print(f"PostgreSQL error detail: {e.pgerror}")
                except:
                    pass
            
            print("="*60)
            return False
    
    def get_payment_by_id(self, payment_id):
        """Получает платеж по payment_id"""
        try:
            print(f"🔍 Searching for payment_id: {payment_id}")
            
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    SELECT id, payment_id, yookassa_id, user_id, amount, status, 
                           email, description, metadata, created_at, updated_at, confirmed_at
                    FROM payments WHERE payment_id = %s
                    """, (payment_id,))
                else:
                    cursor.execute("""
                    SELECT id, payment_id, yookassa_id, user_id, amount, status, 
                           email, description, metadata, created_at, updated_at, confirmed_at
                    FROM payments WHERE payment_id = ?
                    """, (payment_id,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    print(f"✅ Found payment: {result.get('payment_id')} - {result.get('status')}")
                    return result
                else:
                    print(f"❌ Payment not found: {payment_id}")
                    return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа: {e}")
            print(f"ERROR in get_payment_by_id: {str(e)}")
            return None
    
    def get_payment_by_yookassa_id(self, yookassa_id):
        """Получает платеж по yookassa_id"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("SELECT * FROM payments WHERE yookassa_id = %s", (yookassa_id,))
                else:
                    cursor.execute("SELECT * FROM payments WHERE yookassa_id = ?", (yookassa_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа по yookassa_id: {e}")
            return None
    
    def update_payment_status(self, payment_id, status, yookassa_id=None):
        """Обновляет статус платежа"""
        try:
            with self.db_cursor() as cursor:
                if yookassa_id:
                    if self.is_postgres:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = %s, yookassa_id = %s, updated_at = CURRENT_TIMESTAMP,
                        confirmed_at = CASE WHEN %s IN ('succeeded', 'completed') THEN CURRENT_TIMESTAMP ELSE confirmed_at END
                        WHERE payment_id = %s
                        """, (status, yookassa_id, status, payment_id))
                    else:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = ?, yookassa_id = ?, updated_at = datetime('now'),
                        confirmed_at = CASE WHEN ? IN ('succeeded', 'completed') THEN datetime('now') ELSE confirmed_at END
                        WHERE payment_id = ?
                        """, (status, yookassa_id, status, payment_id))
                else:
                    if self.is_postgres:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = %s, updated_at = CURRENT_TIMESTAMP,
                        confirmed_at = CASE WHEN %s IN ('succeeded', 'completed') THEN CURRENT_TIMESTAMP ELSE confirmed_at END
                        WHERE payment_id = %s
                        """, (status, status, payment_id))
                    else:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = ?, updated_at = datetime('now'),
                        confirmed_at = CASE WHEN ? IN ('succeeded', 'completed') THEN datetime('now') ELSE confirmed_at END
                        WHERE payment_id = ?
                        """, (status, status, payment_id))
            
            logger.info(f"📊 Обновлен статус платежа {payment_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления платежа: {e}")
            return False
    
    # ========== МЕТОДЫ ДЛЯ WEBHOOK ==========
    
    def save_webhook_notification(self, webhook_data):
        """Сохраняет уведомление от ЮKassa"""
        try:
            event = webhook_data.get('event', 'unknown')
            payment_id = webhook_data.get('object', {}).get('id', 'unknown')
            status = webhook_data.get('object', {}).get('status', 'unknown')
            webhook_id = webhook_data.get('id', f"webhook_{int(datetime.now().timestamp())}")
            payload = json.dumps(webhook_data, ensure_ascii=False)
            
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    INSERT INTO yookassa_webhooks 
                    (webhook_id, event, payment_id, status, payload)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (webhook_id, event, payment_id, status, payload))
                else:
                    cursor.execute("""
                    INSERT INTO yookassa_webhooks 
                    (webhook_id, event, payment_id, status, payload)
                    VALUES (?, ?, ?, ?, ?)
                    """, (webhook_id, event, payment_id, status, payload))
            
            logger.info(f"📨 Сохранен webhook: {event} для {payment_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения webhook: {e}")
            return False
    
    # ========== МЕТОДЫ ДЛЯ ДОСТУПА ПОЛЬЗОВАТЕЛЕЙ ==========
    
    def mark_access_granted(self, user_id, payment_id, files_sent=None):
        """Отмечает, что доступ предоставлен"""
        try:
            files_sent_json = json.dumps(files_sent or [])
            
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    INSERT INTO user_access 
                    (user_id, payment_id, has_access, files_sent)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (user_id, payment_id) DO UPDATE SET
                    has_access = TRUE,
                    granted_at = CURRENT_TIMESTAMP,
                    files_sent = EXCLUDED.files_sent
                    """, (user_id, payment_id, files_sent_json))
                else:
                    cursor.execute("""
                    INSERT OR REPLACE INTO user_access 
                    (user_id, payment_id, has_access, granted_at, files_sent)
                    VALUES (?, ?, 1, datetime('now'), ?)
                    """, (user_id, payment_id, files_sent_json))
            
            logger.info(f"✅ Доступ предоставлен пользователю {user_id} для платежа {payment_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка предоставления доступа: {e}")
            return False
    
    def user_has_access(self, user_id):
        """Проверяет, есть ли у пользователя доступ"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    SELECT COUNT(*) as count FROM user_access 
                    WHERE user_id = %s AND has_access = TRUE
                    """, (user_id,))
                else:
                    cursor.execute("""
                    SELECT COUNT(*) as count FROM user_access 
                    WHERE user_id = ? AND has_access = 1
                    """, (user_id,))
                
                result = cursor.fetchone()
                count = result['count'] if result else 0
                return count > 0
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа: {e}")
            return False
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def get_user_payments(self, user_id):
        """Получает все платежи пользователя"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    SELECT * FROM payments 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC
                    """, (user_id,))
                else:
                    cursor.execute("""
                    SELECT * FROM payments 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC
                    """, (user_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка получения платежей пользователя: {e}")
            return []
    
    def get_pending_payments(self):
        """Получает все ожидающие платежи"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    SELECT * FROM payments 
                    WHERE status = 'pending' 
                    ORDER BY created_at DESC
                    """)
                else:
                    cursor.execute("""
                    SELECT * FROM payments 
                    WHERE status = 'pending' 
                    ORDER BY created_at DESC
                    """)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка получения ожидающих платежей: {e}")
            return []
    
    def get_recent_webhooks(self, limit=10):
        """Получает последние webhook уведомления"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    SELECT * FROM yookassa_webhooks 
                    ORDER BY received_at DESC 
                    LIMIT %s
                    """, (limit,))
                else:
                    cursor.execute("""
                    SELECT * FROM yookassa_webhooks 
                    ORDER BY received_at DESC 
                    LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка получения webhook: {e}")
            return []
    
    def test_connection(self):
        """Тестирует подключение к базе данных"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("SELECT 1 as test_value, version() as db_version")
                else:
                    cursor.execute("SELECT 1 as test_value, sqlite_version() as db_version")
                
                result = cursor.fetchone()
                db_type = "PostgreSQL" if self.is_postgres else "SQLite"
                logger.info(f"✅ Тест подключения к {db_type} успешен")
                return dict(result) if result else {"test_value": 0, "db_version": "unknown"}
        except Exception as e:
            logger.error(f"❌ Тест подключения не удался: {e}")
            return {"test_value": 0, "error": str(e)}
    
    def check_tables_exist(self):
        """Проверяет существование таблиц - для диагностики"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename IN ('payments', 'user_access', 'yookassa_webhooks', 'deliveries')
                    """)
                else:
                    cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    AND name IN ('payments', 'user_access', 'yookassa_webhooks', 'deliveries')
                    """)
                
                tables = [row[0] for row in cursor.fetchall()]
                print("="*60)
                print("EXISTING TABLES CHECK:")
                for table in ['payments', 'user_access', 'yookassa_webhooks', 'deliveries']:
                    status = "✅ EXISTS" if table in tables else "❌ MISSING"
                    print(f"  {table}: {status}")
                print("="*60)
                return tables
        except Exception as e:
            print(f"ERROR checking tables: {str(e)}")
            return []

# ========== СОЗДАЕМ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ==========
db = Database()
