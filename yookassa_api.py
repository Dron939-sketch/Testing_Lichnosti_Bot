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
        amount: Optional[float] = None,
        description: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создание платежа
        
        Args:
            user_id: ID пользователя в Telegram
            amount: Сумма платежа
            description: Описание платежа
            email: Email пользователя (опционально)
            
        Returns:
            Dict с результатом создания платежа
        """
        if not self.config.is_payment_enabled:
            return {"success": False, "error": "Платежи не настроены"}
        
        # Формируем данные платежа
        payment_data = {
            "amount": {
                "value": f"{amount or self.config.PAYMENT_AMOUNT:.2f}",
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
        
        # Добавляем email, если есть
        if email:
            payment_data["receipt"] = {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": description or self.config.PAYMENT_DESCRIPTION,
                        "quantity": "1",
                        "amount": {
                            "value": f"{amount or self.config.PAYMENT_AMOUNT:.2f}",
                            "currency": self.config.PAYMENT_CURRENCY
                        },
                        "vat_code": "1",
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payment_data,
                headers=self._get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
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
            
        except requests.exceptions.RequestException as e:
            error_detail = ""
            try:
                if e.response:
                    error_detail = e.response.json().get("description", str(e))
            except:
                error_detail = str(e)
                
            return {
                "success": False,
                "error": f"Ошибка API: {error_detail}",
                "status_code": e.response.status_code if e.response else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Неожиданная ошибка: {str(e)}"
            }
    
    def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Dict со статусом платежа
        """
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=self._get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
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
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Ошибка проверки: {str(e)}"
            }
    
    def get_payment_history(self, limit: int = 10) -> Dict[str, Any]:
        """Получить историю платежей"""
        try:
            response = requests.get(
                f"{self.base_url}/payments?limit={limit}",
                headers=self._get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def create_payment_link(self, user_id: int) -> Dict[str, Any]:
        """
        Создать платежную ссылку (альтернативный метод)
        """
        return self.create_payment(
            user_id=user_id,
            description="Полный пакет ВАРИАТИКА - персональные рекомендации"
        )
