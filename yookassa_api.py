# yookassa_api.py
import os
import base64
import uuid
import requests
import json
import logging
from datetime import datetime
from database import db

logger = logging.getLogger(__name__)

class YooKassaAPI:
    """Класс для работы с API ЮKassa"""
    
    def __init__(self):
        self.shop_id = os.getenv('YOOKASSA_SHOP_ID')
        self.secret_key = os.getenv('YOOKASSA_SECRET_KEY')
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
    
    def create_payment(self, amount, description, user_id, email=None, payment_id=None):
        """
        Создает платеж в ЮKassa
        
        Args:
            amount: Сумма (рубли)
            description: Описание платежа
            user_id: ID пользователя Telegram
            email: Email для чека (опционально)
            payment_id: Наш внутренний payment_id
            
        Returns:
            dict: Данные платежа или None при ошибке
        """
        if not self.shop_id or not self.secret_key:
            logger.error("❌ Ключи ЮKassa не настроены!")
            return None
        
        try:
            # Подготавливаем данные
            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "payment_method_data": {
                    "type": "bank_card"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/Testing_Lichnosti_bot"
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_id": user_id,
                    "payment_id": payment_id,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            # Добавляем чек, если есть email
            if email:
                payment_data["receipt"] = {
                    "customer": {"email": email},
                    "items": [
                        {
                            "description": description,
                            "quantity": "1",
                            "amount": {
                                "value": str(amount),
                                "currency": "RUB"
                            },
                            "vat_code": 1  # НДС 20%
                        }
                    ]
                }
            
            # Устанавливаем заголовки
            headers = {
                "Authorization": f"Basic {self._get_auth_token()}",
                "Idempotence-Key": self._generate_idempotence_key(),
                "Content-Type": "application/json"
            }
            
            # Отправляем запрос
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            if response.status_code == 200:
                payment_info = response.json()
                
                # Обновляем наш платеж с yookassa_id
                if payment_id:
                    db.update_payment_status(
                        payment_id, 
                        payment_info.get('status', 'pending'),
                        payment_info.get('id')
                    )
                
                logger.info(f"✅ Платеж создан в ЮKassa: {payment_info.get('id')}")
                return payment_info
            else:
                logger.error(f"❌ Ошибка создания платежа: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка в create_payment: {e}")
            return None
    
    def get_payment_info(self, yookassa_id):
        """Получает информацию о платеже из ЮKassa"""
        try:
            headers = {
                "Authorization": f"Basic {self._get_auth_token()}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/{yookassa_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка получения платежа: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка в get_payment_info: {e}")
            return None

# Глобальный экземпляр
yookassa_api = YooKassaAPI()
