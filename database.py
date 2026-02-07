# database.py - для psycopg3
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', '')
        logger.info(f"DATABASE_URL получен: {'да' if self.database_url else 'нет'}")
        
        if self.database_url and ('postgres' in self.database_url or 'dpg-' in self.database_url):
            self.is_postgres = True
            logger.info("✅ Используется PostgreSQL с psycopg3")
        else:
            self.is_postgres = False
            logger.warning("⚠️ Используется SQLite (fallback)")
    
    def get_connection(self):
        if self.is_postgres:
            try:
                # psycopg3
                import psycopg
                from psycopg.rows import dict_row
                
                conn = psycopg.connect(
                    self.database_url,
                    row_factory=dict_row
                )
                logger.debug("✅ Подключение к PostgreSQL установлено (psycopg3)")
                return conn
            except ImportError:
                logger.error("❌ psycopg не установлен. Добавьте в requirements.txt: psycopg[binary]")
                raise
        else:
            import sqlite3
            conn = sqlite3.connect("/tmp/variatica.db")
            conn.row_factory = sqlite3.Row
            return conn
    
    @contextmanager 
    def db_cursor(self):
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
        """Инициализация таблиц для psycopg3"""
        logger.info("🗄️ Инициализация PostgreSQL с psycopg3...")
        
        try:
            with self.db_cursor() as cursor:
                # Таблицы остаются такими же
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
                
                # ... остальные таблицы ...
                
            logger.info("✅ PostgreSQL БД инициализирована (psycopg3)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
