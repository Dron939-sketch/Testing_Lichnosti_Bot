"""
Упрощенный API ЮKassa (без requests для тестирования)
"""

import base64
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class YooKassaAPI:
    """Класс для работы с API ЮKassa (упрощенный)"""
    
    def __init__(self, config):
        self.config = config
        
    def create_payment(self, user_id: int, description: Optional[str] = None) -> Dict[str, Any]:
        """Создание платежа (заглушка)"""
        print(f"🔄 Создание платежа для пользователя {user_id}")
        
        # Генерируем тестовый URL
        payment_id = f"test_{uuid.uuid4().hex[:8]}"
        
        return {
            "success": True,
            "payment_id": payment_id,
            "payment_url": f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={payment_id}",
            "status": "pending",
            "amount": "690.00",
            "currency": "RUB",
            "metadata": {"user_id": str(user_id)}
        }
    
    def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """Проверка статуса платежа (заглушка)"""
        print(f"🔄 Проверка платежа {payment_id}")
        
        # Для тестовых платежей всегда возвращаем успех
        if payment_id.startswith("test_"):
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "succeeded",
                "paid": True,
                "amount": "690.00",
                "currency": "RUB"
            }
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": "pending",
            "paid": False,
            "amount": "690.00",
            "currency": "RUB"
        }
