"""
API ЮKassa для обработки платежей
"""

import base64
import json
import requests
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from config import Config


class YooKassaAPI:
    """Класс для работы с API ЮKassa"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://api.yookassa.ru/v3"
        
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для API"""
        auth_string = f"{self.config.YOOKASSA_SHOP_ID}:{self.config.YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        return {
            "Authorization": f"Basic {auth_encoded}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid.uuid4())  # Важно для предотвращения дублирования
        }
    
    def create_payment(
        self, 
        user_id: int, 
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создание платежа
        
        Args:
            user_id: ID пользователя в Telegram
            description: Описание платежа
            
        Returns:
            Dict с результатом создания платежа
        """
        # Проверяем, включены ли платежи
        if not self.config.is_payment_enabled:
            # Демо-режим
            payment_id = f"demo_{uuid.uuid4().hex[:8]}"
            return {
                "success": True,
                "payment_id": payment_id,
                "payment_url": f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={payment_id}",
                "status": "pending",
                "amount": "690.00",
                "currency": "RUB",
                "metadata": {"user_id": str(user_id)}
            }
        
        try:
            # Формируем данные платежа
            payment_data = {
                "amount": {
                    "value": f"{self.config.PAYMENT_AMOUNT:.2f}",
                    "currency": self.config.PAYMENT_CURRENCY
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.config.RETURN_URL
                },
                "capture": True,  # Автоматическое списание
                "description": description or self.config.PAYMENT_DESCRIPTION,
                "metadata": {
                    "user_id": str(user_id),
                    "telegram_username": f"user_{user_id}",
                    "created_at": datetime.now().isoformat(),
                    "product": "variatica_full_package",
                    "version": "2.0"
                }
            }
            
            # Отправляем запрос к API ЮKassa
            response = requests.post(
                f"{self.base_url}/payments",
                json=payment_data,
                headers=self._get_headers(),
                timeout=30
            )
            
            # Логируем ответ
            print(f"🔍 ЮKassa Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "payment_id": result["id"],
                    "payment_url": result["confirmation"]["confirmation_url"],
                    "status": result["status"],
                    "amount": result["amount"]["value"],
                    "currency": result["amount"]["currency"],
                    "metadata": result.get("metadata", {})
                }
            else:
                error_detail = response.text
                print(f"❌ ЮKassa Error: {response.status_code} - {error_detail}")
                return {
                    "success": False,
                    "error": f"Ошибка API: {response.status_code}",
                    "details": error_detail
                }
                
        except Exception as e:
            print(f"❌ Exception in create_payment: {e}")
            return {
                "success": False,
                "error": f"Ошибка: {str(e)}"
            }
    
    def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Dict со статусом платежа
        """
        # Если это демо-платеж
        if payment_id.startswith("demo_") or payment_id.startswith("test_"):
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "succeeded",
                "paid": True,
                "amount": "690.00",
                "currency": "RUB"
            }
        
        # Если платежи не настроены
        if not self.config.is_payment_enabled:
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "succeeded",
                "paid": True,
                "amount": "690.00",
                "currency": "RUB"
            }
        
        try:
            # Реальная проверка статуса
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "payment_id": result["id"],
                    "status": result["status"],
                    "paid": result["status"] == "succeeded",
                    "amount": result["amount"]["value"],
                    "currency": result["amount"]["currency"],
                    "metadata": result.get("metadata", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"Ошибка проверки: {response.status_code}",
                    "status": "unknown"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка: {str(e)}"
            }
