"""
payments_db.py - Общая база данных для Telegram бота и Flask сервера
Оба сервиса используют эту БД для обмена данными
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "shared_payments.db"

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Инициализация базы данных (дублирует функцию из app.py)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица платежей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT UNIQUE NOT NULL,
            yookassa_id TEXT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL DEFAULT 199.0,
            status TEXT NOT NULL DEFAULT 'pending',
            email TEXT,
            description TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP,
            metadata TEXT
        )
        """)
        
        conn.commit()

def create_payment(payment_id: str, user_id: int, amount: float = 199.0, 
                   email: str = None, description: str = None):
    """Создает запись о платеже (используется Telegram ботом)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, amount, status, created_at, email, description)
        VALUES (?, ?, ?, 'pending', ?, ?, ?)
        """, (payment_id, user_id, amount, datetime.now().isoformat(), email, description))
        conn.commit()
    return payment_id

def get_payment_status(payment_id: str):
    """Получает статус платежа (используется Telegram ботом)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM payments WHERE payment_id = ?", (payment_id,))
        result = cursor.fetchone()
        return result['status'] if result else None

def get_user_payments(user_id: int):
    """Получает все платежи пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT payment_id, amount, status, created_at, yookassa_id
        FROM payments 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_succeeded_payments():
    """Получает успешные платежи для доставки"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT p.payment_id, p.user_id 
        FROM payments p
        LEFT JOIN deliveries d ON p.payment_id = d.payment_id
        WHERE p.status = 'succeeded' AND d.id IS NULL
        """)
        return [(row['payment_id'], row['user_id']) for row in cursor.fetchall()]

def mark_as_delivered(payment_id: str, user_id: int, files_sent: list = None):
    """Помечает платеж как доставленный"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO deliveries (payment_id, user_id, delivered_at, files_sent)
        VALUES (?, ?, ?, ?)
        """, (payment_id, user_id, datetime.now().isoformat(), 
              json.dumps(files_sent) if files_sent else None))
        conn.commit()
