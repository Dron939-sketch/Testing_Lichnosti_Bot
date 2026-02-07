# database.py - PostgreSQL версия для Render
import os
import logging
import json
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """PostgreSQL для Render"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', '')
        logger.info(f"DATABASE_URL получен: {'да' if self.database_url else 'нет'}")
        
        if self.database_url and ('postgres' in self.database_url or 'dpg-' in self.database_url):
            self.is_postgres = True
            logger.info("✅ Используется PostgreSQL")
            
            # Автодобавление sslmode
            if 'sslmode=' not in self.database_url:
                if '?' in self.database_url:
                    self.database_url += '&sslmode=require'
                else:
                    self.database_url += '?sslmode=require'
        else:
            self.is_postgres = False
            logger.warning("⚠️ Используется SQLite (fallback)")
            import sqlite3
    
    def get_connection(self):
        if self.is_postgres:
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(self.database_url, row_factory=dict_row)
        else:
            import sqlite3
            conn = sqlite3.connect("/tmp/variatica.db")
            conn.row_factory = sqlite3.Row
            return conn
    
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
            logger.error(f"❌ Ошибка БД: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def init_database(self):
        """Инициализация таблиц"""
        logger.info("🗄️ Инициализация базы данных...")
        
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    # PostgreSQL для Render
                    
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
                        description TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confirmed_at TIMESTAMP
                    )
                    """)
                    
                    # Таблица доступа пользователей
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_access (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        payment_id VARCHAR(255),
                        has_access BOOLEAN DEFAULT FALSE,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT,
                        UNIQUE(user_id, payment_id)
                    )
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
                        payload TEXT
                    )
                    """)
                    
                    # Таблица доставки
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS deliveries (
                        id SERIAL PRIMARY KEY,
                        payment_id VARCHAR(255),
                        user_id BIGINT NOT NULL,
                        delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        files_sent TEXT
                    )
                    """)
                    
                    logger.info("✅ Таблицы PostgreSQL созданы на Render")
                    
                else:
                    # SQLite fallback
                    import sqlite3
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
                        files_sent TEXT
                    )
                    """)
            
            logger.info("✅ База данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    # ========== БАЗОВЫЕ МЕТОДЫ ==========
    
    def create_payment(self, payment_data):
        """Создает новый платеж"""
        try:
            with self.db_cursor() as cursor:
                if self.is_postgres:
                    cursor.execute("""
                    INSERT INTO payments 
                    (payment_id, user_id, amount, description, email, metadata, status, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (payment_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
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
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (
                        payment_data['payment_id'],
                        payment_data['user_id'],
                        payment_data.get('amount', 690.00),
                        payment_data.get('description', 'Полный пакет ВАРИАТИКА'),
                        payment_data.get('email', ''),
                        payment_data.get('metadata', '{}'),
                        payment_data.get('status', 'pending')
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
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа: {e}")
            return None

# ========== ВАЖНО! ==========
# Добавьте эту строку в самый конец файла:
# Создаем глобальный экземпляр базы данных
db = Database()
