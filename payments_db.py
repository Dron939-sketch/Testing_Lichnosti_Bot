"""
payments_db.py - Использует PostgreSQL на Render
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from contextlib import contextmanager

# Получаем строку подключения из переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL')

@contextmanager 
def get_db_connection():
    """Контекстный менеджер для подключения к PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Инициализация таблиц в PostgreSQL"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            
            # Таблица платежей
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                payment_id VARCHAR(255) UNIQUE NOT NULL,
                yookassa_id VARCHAR(255),
                user_id BIGINT NOT NULL,
                amount DECIMAL(10,2) DEFAULT 199.00,
                status VARCHAR(50) DEFAULT 'pending',
                email VARCHAR(255),
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP,
                metadata TEXT
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
                received_at TIMESTAMP DEFAULT NOW(),
                payload JSONB
            )
            """)
            
            # Таблица доставок
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
                id SERIAL PRIMARY KEY,
                payment_id VARCHAR(255) REFERENCES payments(payment_id),
                user_id BIGINT NOT NULL,
                delivered_at TIMESTAMP DEFAULT NOW(),
                files_sent JSONB
            )
            """)
            
            conn.commit()
