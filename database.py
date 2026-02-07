# database.py
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

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
            # Для SQLite создаем локальную БД
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
    
    def init_database(self):
        """Инициализация таблиц в базе данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Таблица платежей (общая для бота и вебхуков)
            if self.is_postgres:
                # PostgreSQL версия
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    payment_id VARCHAR(100) UNIQUE NOT NULL,
                    yookassa_id VARCHAR(100),
                    user_id BIGINT NOT NULL,
                    amount DECIMAL(10,2) DEFAULT 690.00,
                    status VARCHAR(50) DEFAULT 'pending',
                    description TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    confirmed_at TIMESTAMP
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_access (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    payment_id VARCHAR(100) REFERENCES payments(payment_id),
                    has_access BOOLEAN DEFAULT FALSE,
                    granted_at TIMESTAMP,
                    files_sent TEXT,
                    UNIQUE(user_id, payment_id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS yookassa_webhooks (
                    id SERIAL PRIMARY KEY,
                    webhook_id VARCHAR(100) NOT NULL,
                    event VARCHAR(50) NOT NULL,
                    payment_id VARCHAR(100),
                    status VARCHAR(50),
                    received_at TIMESTAMP DEFAULT NOW(),
                    payload TEXT
                )
                ''')
                
            else:
                # SQLite версия
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id TEXT UNIQUE NOT NULL,
                    yookassa_id TEXT,
                    user_id INTEGER NOT NULL,
                    amount REAL DEFAULT 690.00,
                    status TEXT DEFAULT 'pending',
                    description TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    payment_id TEXT,
                    has_access BOOLEAN DEFAULT FALSE,
                    granted_at TIMESTAMP,
                    files_sent TEXT,
                    FOREIGN KEY (payment_id) REFERENCES payments(payment_id),
                    UNIQUE(user_id, payment_id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS yookassa_webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webhook_id TEXT NOT NULL,
                    event TEXT NOT NULL,
                    payment_id TEXT,
                    status TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payload TEXT
                )
                ''')
            
            conn.commit()
            logger.info("✅ Таблицы базы данных инициализированы")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Выполняет SQL запрос"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            if not query.strip().upper().startswith('SELECT'):
                conn.commit()
            
            return result
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise
        finally:
            conn.close()
    
    def get_payment_by_id(self, payment_id):
        """Получает платеж по ID"""
        query = "SELECT * FROM payments WHERE payment_id = %s"
        return self.execute_query(query, (payment_id,), fetch_one=True)
    
    def update_payment_status(self, payment_id, status, yookassa_id=None):
        """Обновляет статус платежа"""
        if yookassa_id:
            query = """
            UPDATE payments 
            SET status = %s, yookassa_id = %s, updated_at = NOW(), confirmed_at = NOW()
            WHERE payment_id = %s
            """
            params = (status, yookassa_id, payment_id)
        else:
            query = """
            UPDATE payments 
            SET status = %s, updated_at = NOW()
            WHERE payment_id = %s
            """
            params = (status, payment_id)
        
        return self.execute_query(query, params)
    
    def create_payment(self, payment_data):
        """Создает новый платеж"""
        query = """
        INSERT INTO payments 
        (payment_id, user_id, amount, description, metadata, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            payment_data['payment_id'],
            payment_data['user_id'],
            payment_data.get('amount', 690.00),
            payment_data.get('description', 'Полный пакет ВАРИАТИКА'),
            payment_data.get('metadata', '{}'),
            payment_data.get('status', 'pending')
        )
        
        return self.execute_query(query, params)

# Глобальный экземпляр базы данных
db = Database()
