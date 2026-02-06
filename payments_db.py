"""
payments_db.py - Общая база для платежей
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "payments.db"

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,  -- 'pending', 'succeeded', 'failed'
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP,
        yookassa_id TEXT,
        email TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivered_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        delivered_at TIMESTAMP NOT NULL,
        FOREIGN KEY (payment_id) REFERENCES payments (payment_id)
    )
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def create_payment(payment_id: str, user_id: int, amount: float = 199.0):
    """Создает запись о платеже"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, amount, status, created_at)
        VALUES (?, ?, ?, 'pending', ?)
        """, (payment_id, user_id, amount, datetime.now().isoformat()))
        conn.commit()

def update_payment_status(payment_id: str, status: str, yookassa_id: str = None):
    """Обновляет статус платежа"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE payments 
        SET status = ?, updated_at = ?, yookassa_id = ?
        WHERE payment_id = ?
        """, (status, datetime.now().isoformat(), yookassa_id, payment_id))
        conn.commit()

def get_pending_payments():
    """Получает ожидающие платежи"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT payment_id, user_id FROM payments WHERE status = 'pending'")
        return cursor.fetchall()
