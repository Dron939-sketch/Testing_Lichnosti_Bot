# payment_utils.py
import os
import uuid
import json
import logging
from datetime import datetime
from database import db

logger = logging.getLogger(__name__)

class PaymentUtils:
    """Утилиты для работы с платежами"""
    
    @staticmethod
    def generate_payment_id(user_id):
        """Генерация уникального ID платежа"""
        timestamp = int(datetime.now().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        return f"payment_{user_id}_{timestamp}_{unique_id}"
    
    @staticmethod
    def create_payment_record(user_id, amount=690.00, description="Полный пакет ВАРИАТИКА"):
        """Создает запись о платеже в БД"""
        payment_id = PaymentUtils.generate_payment_id(user_id)
        
        payment_data = {
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'description': description,
            'metadata': json.dumps({
                'created_via': 'telegram_bot',
                'timestamp': datetime.now().isoformat(),
                'product': 'variatica_full_package'
            })
        }
        
        try:
            db.create_payment(payment_data)
            logger.info(f"✅ Создан платеж: {payment_id} для пользователя {user_id}")
            return payment_id
        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            return None
    
    @staticmethod
    def get_payment_status(payment_id):
        """Получает статус платежа"""
        try:
            payment = db.get_payment_by_id(payment_id)
            if payment:
                return payment['status']
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса платежа: {e}")
            return None
    
    @staticmethod
    def get_pending_payments_for_user(user_id):
        """Получает все pending платежи пользователя"""
        query = """
        SELECT * FROM payments 
        WHERE user_id = %s AND status = 'pending'
        ORDER BY created_at DESC
        """
        return db.execute_query(query, (user_id,), fetch_all=True)
    
    @staticmethod
    def mark_access_granted(user_id, payment_id, files_sent=None):
        """Отмечает, что доступ предоставлен"""
        query = """
        INSERT INTO user_access (user_id, payment_id, has_access, granted_at, files_sent)
        VALUES (%s, %s, TRUE, NOW(), %s)
        ON CONFLICT (user_id, payment_id) DO UPDATE SET
            has_access = TRUE,
            granted_at = NOW(),
            files_sent = EXCLUDED.files_sent
        """
        return db.execute_query(query, (user_id, payment_id, files_sent))
    
    @staticmethod
    def user_has_access(user_id):
        """Проверяет, есть ли у пользователя доступ"""
        query = """
        SELECT COUNT(*) FROM user_access 
        WHERE user_id = %s AND has_access = TRUE
        """
        result = db.execute_query(query, (user_id,), fetch_one=True)
        return result[0] > 0 if result else False

# Создаем глобальный экземпляр
payment_utils = PaymentUtils()
