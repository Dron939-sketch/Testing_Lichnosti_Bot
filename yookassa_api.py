# yookassa_api.py - ОБНОВЛЕННЫЙ ДЛЯ WORKER
import os
import base64
import uuid
import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class YooKassaAPI:
    """Класс для работы с API ЮKassa - ДЛЯ WORKER"""
    
    def __init__(self, config):
        self.config = config
        self.shop_id = config.YOOKASSA_SHOP_ID
        self.secret_key = config.YOOKASSA_SECRET_KEY
        self.api_url = "https://api.yookassa.ru/v3/payments"
        
        if not self.shop_id or not self.secret_key:
            logger.warning("⚠️ Ключи ЮKassa не настроены. Используется тестовый режим.")
    
    def _get_auth_token(self):
        """Получение токена авторизации"""
        auth_string = f"{self.shop_id}:{self.secret_key}"
        return base64.b64encode(auth_string.encode()).decode()
    
    def _generate_idempotence_key(self):
        """Генерация ключа идемпотентности"""
        return str(uuid.uuid4())
    
    def create_payment_via_api(self, amount, description, user_id, email=None, payment_id=None):
        """
        Создает платеж ЧЕРЕЗ ВАШ FLASK API (не напрямую в ЮKassa)
        
        Worker → Flask API → ЮKassa → Flask API → PostgreSQL
        """
        try:
            # Вызываем наш Flask API для создания платежа
            response = requests.post(
                f"{self.config.API_URL}/api/create-payment",
                json={
                    "payment_id": payment_id or f"payment_{user_id}_{int(datetime.now().timestamp())}",
                    "user_id": user_id,
                    "amount": amount,
                    "email": email or "",
                    "description": description
                },
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"✅ Платеж создан через API: {data.get('payment_id')}")
                
                # Теперь создаем платеж в ЮKassa
                if not self.config.is_test_mode and self.shop_id and self.secret_key:
                    yookassa_result = self._create_yookassa_payment(
                        amount, description, user_id, payment_id
                    )
                    
                    if yookassa_result:
                        # Обновляем yookassa_id через API
                        requests.post(
                            f"{self.config.API_URL}/api/update-yookassa-id",
                            json={
                                "payment_id": payment_id,
                                "yookassa_id": yookassa_result.get('id')
                            },
                            timeout=10
                        )
                        
                        return {
                            "success": True,
                            "payment_id": payment_id,
                            "yookassa_id": yookassa_result.get('id'),
                            "payment_url": yookassa_result.get('confirmation', {}).get('confirmation_url'),
                            "amount": amount,
                            "status": "pending",
                            "api_data": data
                        }
                
                # Если тестовый режим или нет ключей
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "yookassa_id": None,
                    "payment_url": f"https://yookassa.ru/test/{payment_id}",
                    "amount": amount,
                    "status": "pending",
                    "api_data": data,
                    "message": "Тестовый режим (реальный платеж не создан)"
                }
            else:
                logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "payment_id": payment_id
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания платежа: {e}")
            return {
                "success": False,
                "error": str(e),
                "payment_id": payment_id
            }
    
    def _create_yookassa_payment(self, amount, description, user_id, payment_id):
        """Создает реальный платеж в ЮKassa"""
        if not self.shop_id or not self.secret_key:
            return None
        
        try:
            payment_data = {
                "amount": {"value": str(amount), "currency": "RUB"},
                "payment_method_data": {"type": "bank_card"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.config.BOT_LINK
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_id": user_id,
                    "payment_id": payment_id,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            headers = {
                "Authorization": f"Basic {self._get_auth_token()}",
                "Idempotence-Key": self._generate_idempotence_key(),
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ ЮKassa error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка ЮKassa: {e}")
            return None
    
    def check_payment_via_api(self, payment_id):
        """Проверяет статус платежа через Flask API"""
        try:
            response = requests.get(
                f"{self.config.API_URL}/api/payment-status/{payment_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("found"):
                    return {
                        "success": True,
                        "status": data.get("status", "pending"),
                        "amount": data.get("amount", 0),
                        "yookassa_id": data.get("yookassa_id"),
                        "user_id": data.get("user_id"),
                        "payment_data": data
                    }
                else:
                    return {
                        "success": False,
                        "status": "not_found",
                        "error": "Payment not found"
                    }
            else:
                return {
                    "success": False,
                    "status": "api_error",
                    "error": f"API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }

# Глобальный экземпляр
yookassa_api = None  # Инициализируется в основном файле
