# database.py - ЕДИНАЯ ВЕРСИЯ ДЛЯ ВСЕХ СЕРВИСОВ
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """Универсальный класс для работы с PostgreSQL (продакшн) и SQLite (разработка)"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.is_postgres = self.database_url and self.database_url.startswith('postgresql://')
        
        if self.is_postgres:
            logger.info("✅ Используется PostgreSQL (продакшн)")
        else:
            logger.info("🧪 Используется SQLite (разработка)")
            self.sqlite_path = "variatica.db"
    
    def get_connection(self):
        """Возвращает подключение к базе данных"""
        if self.is_postgres:
            # PostgreSQL на Render
            conn = psycopg2.connect(self.database_url, sslmode='require')
            conn.autocommit = False
            return conn
        else:
            # SQLite для разработки
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    @contextmanager
    def db_cursor(self):
        """Контекстный менеджер для работы с БД"""
        conn = self.get_connection()
        cursor = None
        try:
            if self.is_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()
            
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Ошибка БД: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def init_database(self):
        """Инициализация ЕДИНЫХ таблиц в базе данных"""
        logger.info("🗄️ Инициализация ЕДИНОЙ базы данных...")
        
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    # PostgreSQL версия - ЕДИНАЯ СХЕМА
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        id SERIAL PRIMARY KEY,
                        payment_id VARCHAR(255) UNIQUE NOT NULL,
                        yookassa_id VARCHAR(255),
                        user_id BIGINT NOT NULL,
                        amount DECIMAL(10,2) DEFAULT 690.00,
                        status VARCHAR(50) DEFAULT 'pending',
                        email VARCHAR(255),
                        description TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        confirmed_at TIMESTAMP
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_access (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        payment_id VARCHAR(255) REFERENCES payments(payment_id),
                        has_access BOOLEAN DEFAULT FALSE,
                        granted_at TIMESTAMP DEFAULT NOW(),
                        files_sent TEXT,
                        UNIQUE(user_id, payment_id)
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS yookassa_webhooks (
                        id SERIAL PRIMARY KEY,
                        webhook_id VARCHAR(255) NOT NULL,
                        event VARCHAR(100) NOT NULL,
                        payment_id VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        received_at TIMESTAMP DEFAULT NOW(),
                        payload JSONB
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deliveries (
                        id SERIAL PRIMARY KEY,
                        payment_id VARCHAR(255) REFERENCES payments(payment_id),
                        user_id BIGINT NOT NULL,
                        delivered_at TIMESTAMP DEFAULT NOW(),
                        files_sent JSONB
                    )
                    """)
                    
                else:
                    # SQLite версия - ЕДИНАЯ СХЕМА
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payment_id TEXT UNIQUE NOT NULL,
                        yookassa_id TEXT,
                        user_id INTEGER NOT NULL,
                        amount REAL DEFAULT 690.00,
                        status TEXT DEFAULT 'pending',
                        email TEXT,
                        description TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confirmed_at TIMESTAMP
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_access (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        payment_id TEXT,
                        has_access BOOLEAN DEFAULT FALSE,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT,
                        FOREIGN KEY (payment_id) REFERENCES payments(payment_id),
                        UNIQUE(user_id, payment_id)
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS yookassa_webhooks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        webhook_id TEXT NOT NULL,
                        event TEXT NOT NULL,
                        payment_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        payload TEXT
                    )
                    """)
                    
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deliveries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payment_id TEXT,
                        user_id INTEGER NOT NULL,
                        delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT,
                        FOREIGN KEY (payment_id) REFERENCES payments(payment_id)
                    )
                    """)
            
            logger.info("✅ Единая база данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    # ========== ОБЩИЕ МЕТОДЫ ДЛЯ ВСЕХ СЕРВИСОВ ==========
    
    def create_payment(self, payment_data):
        """Создает новый платеж (для бота и API)"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    INSERT INTO payments 
                    (payment_id, user_id, amount, description, email, metadata, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (payment_id) DO UPDATE SET
                        updated_at = NOW(),
                        yookassa_id = EXCLUDED.yookassa_id
                    """, (
                        payment_data['payment_id'],
                        payment_data['user_id'],
                        payment_data.get('amount', 690.00),
                        payment_data.get('description', 'Полный пакет ВАРИАТИКА'),
                        payment_data.get('email', ''),
                        payment_data.get('metadata', '{}'),
                        payment_data.get('status', 'pending')
                    ))
                else:
                    cursor.execute("""
                    INSERT OR REPLACE INTO payments 
                    (payment_id, user_id, amount, description, email, metadata, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        payment_data['payment_id'],
                        payment_data['user_id'],
                        payment_data.get('amount', 690.00),
                        payment_data.get('description', 'Полный пакет ВАРИАТИКА'),
                        payment_data.get('email', ''),
                        payment_data.get('metadata', '{}'),
                        payment_data.get('status', 'pending'),
                        'NOW()'
                    ))
            
            logger.info(f"📝 Создан платеж: {payment_data['payment_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            return False
    
    def get_payment_by_id(self, payment_id):
        """Получает платеж по ID"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("SELECT * FROM payments WHERE payment_id = %s", (payment_id,))
                else:
                    cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
                
                result = cursor.fetchone()
                if result:
                    if isinstance(result, dict):
                        return result
                    elif hasattr(result, '_asdict'):
                        return result._asdict()
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, result))
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа: {e}")
            return None
    
    def get_payment_by_yookassa_id(self, yookassa_id):
        """Получает платеж по ID ЮKassa"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute(
                        "SELECT * FROM payments WHERE yookassa_id = %s OR payment_id = %s", 
                        (yookassa_id, yookassa_id)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM payments WHERE yookassa_id = ? OR payment_id = ?", 
                        (yookassa_id, yookassa_id)
                    )
                
                result = cursor.fetchone()
                if result:
                    if isinstance(result, dict):
                        return result
                    elif hasattr(result, '_asdict'):
                        return result._asdict()
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        return dict(zip(columns, result))
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа: {e}")
            return None
    
    def update_payment_status(self, payment_id, status, yookassa_id=None):
        """Обновляет статус платежа"""
        try:
            with self.db_cursor() as cursor:
                if yookassa_id:
                    if self.is_postgres:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = %s, yookassa_id = %s, updated_at = NOW(), confirmed_at = NOW()
                        WHERE payment_id = %s
                        """, (status, yookassa_id, payment_id))
                    else:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = ?, yookassa_id = ?, updated_at = CURRENT_TIMESTAMP, confirmed_at = CURRENT_TIMESTAMP
                        WHERE payment_id = ?
                        """, (status, yookassa_id, payment_id))
                else:
                    if self.is_postgres:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = %s, updated_at = NOW()
                        WHERE payment_id = %s
                        """, (status, payment_id))
                    else:
                        cursor.execute("""
                        UPDATE payments 
                        SET status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE payment_id = ?
                        """, (status, payment_id))
            
            logger.info(f"📊 Обновлен статус платежа {payment_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления платежа: {e}")
            return False
    
    def save_webhook_notification(self, webhook_data):
        """Сохраняет уведомление от ЮKassa"""
        import json
        from datetime import datetime
        
        try:
            event = webhook_data.get('event', 'unknown')
            payment_id = webhook_data.get('object', {}).get('id', 'unknown')
            status = webhook_data.get('object', {}).get('status', 'unknown')
            webhook_id = webhook_data.get('id', f"webhook_{datetime.now().timestamp()}")
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
            
            logger.info(f"📨 Сохранено webhook: {event} для {payment_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения webhook: {e}")
            return False
    
    def mark_access_granted(self, user_id, payment_id, files_sent=None):
        """Отмечает, что доступ предоставлен"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    INSERT INTO user_access (user_id, payment_id, has_access, files_sent)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (user_id, payment_id) DO UPDATE SET
                        has_access = TRUE,
                        granted_at = NOW(),
                        files_sent = EXCLUDED.files_sent
                    """, (user_id, payment_id, files_sent))
                else:
                    cursor.execute("""
                    INSERT OR REPLACE INTO user_access 
                    (user_id, payment_id, has_access, granted_at, files_sent)
                    VALUES (?, ?, TRUE, CURRENT_TIMESTAMP, ?)
                    """, (user_id, payment_id, files_sent))
            
            logger.info(f"✅ Доступ предоставлен пользователю {user_id}")
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
                    SELECT COUNT(*) FROM user_access 
                    WHERE user_id = %s AND has_access = TRUE
                    """, (user_id,))
                else:
                    cursor.execute("""
                    SELECT COUNT(*) FROM user_access 
                    WHERE user_id = ? AND has_access = 1
                    """, (user_id,))
                
                result = cursor.fetchone()
                count = result[0] if result else 0
                return count > 0
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа: {e}")
            return False

# Глобальный экземпляр базы данных
db = Database()
