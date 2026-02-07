# database.py - ТОЛЬКО SQLite ВЕРСИЯ
import os
import sqlite3
import logging
import json
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с SQLite (временно используем SQLite)"""
    
    def __init__(self):
        # ВСЕГДА используем SQLite
        self.is_postgres = False
        logger.info("🧪 Используется SQLite")
        self.sqlite_path = "variatica.db"
    
    def get_connection(self):
        """Подключение к SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
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
        """Инициализация таблиц в SQLite"""
        logger.info("🗄️ Инициализация SQLite БД...")
        
        try:
            with self.db_cursor() as cursor:
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
                
                # Таблица webhook уведомлений
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
                
                # Таблица доставки
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
            
            logger.info("✅ SQLite БД инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    # ========== ОБЩИЕ МЕТОДЫ ДЛЯ ВСЕХ СЕРВИСОВ ==========
    
    def create_payment(self, payment_data):
        """Создает новый платеж"""
        try:
            with self.db_cursor() as cursor:
                cursor.execute("""
                INSERT OR REPLACE INTO payments 
                (payment_id, user_id, amount, description, email, metadata, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
                cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа: {e}")
            return None
    
    def get_payment_by_yookassa_id(self, yookassa_id):
        """Получает платеж по ID ЮKassa"""
        try:
            with self.db_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM payments WHERE yookassa_id = ? OR payment_id = ?", 
                    (yookassa_id, yookassa_id)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка поиска платежа: {e}")
            return None
    
    def update_payment_status(self, payment_id, status, yookassa_id=None):
        """Обновляет статус платежа"""
        try:
            with self.db_cursor() as cursor:
                if yookassa_id:
                    cursor.execute("""
                    UPDATE payments 
                    SET status = ?, yookassa_id = ?, updated_at = CURRENT_TIMESTAMP, confirmed_at = CURRENT_TIMESTAMP
                    WHERE payment_id = ?
                    """, (status, yookassa_id, payment_id))
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
        try:
            event = webhook_data.get('event', 'unknown')
            payment_id = webhook_data.get('object', {}).get('id', 'unknown')
            status = webhook_data.get('object', {}).get('status', 'unknown')
            webhook_id = webhook_data.get('id', f"webhook_{datetime.now().timestamp()}")
            payload = json.dumps(webhook_data, ensure_ascii=False)
            
            with self.db_cursor() as cursor:
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
    
    def get_pending_payments(self):
        """Получает все ожидающие платежи"""
        try:
            with self.db_cursor() as cursor:
                cursor.execute("""
                SELECT * FROM payments 
                WHERE status = 'pending' 
                ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка получения платежей: {e}")
            return []
    
    def get_user_payments(self, user_id):
        """Получает все платежи пользователя"""
        try:
            with self.db_cursor() as cursor:
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

# Глобальный экземпляр базы данных
db = Database()
