"""
API ЮKassa для обработки платежей
"""

import base64
import json
import requests
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from config import Config

# Настройка логирования
logger = logging.getLogger(__name__)

class YooKassaAPI:
    """Класс для работы с API ЮKassa"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "https://api.yookassa.ru/v3" if not config.is_test_mode else "https://api.yookassa.ru/v3"
        
        logger.info("="*50)
        logger.info("💰 ИНИЦИАЛИЗАЦИЯ ЮKASSA API")
        logger.info("="*50)
        logger.info(f"⚙️  Конфигурация:")
        logger.info(f"   Shop ID: {'✅ УСТАНОВЛЕН' if config.YOOKASSA_SHOP_ID else '❌ НЕ УСТАНОВЛЕН'}")
        logger.info(f"   Secret Key: {'✅ УСТАНОВЛЕН' if config.YOOKASSA_SECRET_KEY else '❌ НЕ УСТАНОВЛЕН'}")
        logger.info(f"   Webhook URL: {'✅ ' + config.WEBHOOK_URL if config.WEBHOOK_URL else '❌ НЕ УСТАНОВЛЕН'}")
        logger.info(f"   Test Mode: {'🟡 ДА' if config.is_test_mode else '🟢 НЕТ'}")
        logger.info(f"   Payment Enabled: {'✅ ДА' if config.is_payment_enabled else '❌ НЕТ'}")
        logger.info(f"   Base URL: {self.base_url}")
        
        if not config.is_payment_enabled:
            logger.warning("⚠️  ВНИМАНИЕ: Платежи ЮKassa НЕ настроены!")
            logger.warning("   Используется демо-режим без реальных платежей")
        
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для API"""
        if self.config.is_test_mode:
            logger.debug("🟡 ТЕСТОВЫЙ РЕЖИМ: Используем тестовые ключи")
        
        auth_string = f"{self.config.YOOKASSA_SHOP_ID}:{self.config.YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid.uuid4())
        }
        
        logger.debug(f"📋 Заголовки запроса:")
        logger.debug(f"   Auth: Basic *** (скрыто)")
        logger.debug(f"   Idempotence-Key: {headers['Idempotence-Key']}")
        
        return headers
    
    def _log_payment_request(self, user_id: int, description: str):
        """Логирование запроса на создание платежа"""
        logger.info("="*40)
        logger.info("🔧 СОЗДАНИЕ ПЛАТЕЖА")
        logger.info(f"   👤 User ID: {user_id}")
        logger.info(f"   📝 Description: {description}")
        logger.info(f"   💰 Amount: {self.config.PAYMENT_AMOUNT} {self.config.PAYMENT_CURRENCY}")
        logger.info(f"   🌐 Mode: {'DEMO' if not self.config.is_payment_enabled else 'REAL'}")
        logger.info(f"   🔗 Webhook: {self.config.WEBHOOK_URL if self.config.WEBHOOK_URL else '❌ Не настроен'}")
        logger.info("="*40)
    
    def _log_payment_response(self, success: bool, response_data: Dict[str, Any]):
        """Логирование ответа от API"""
        if success:
            logger.info("✅ ПЛАТЕЖ СОЗДАН УСПЕШНО")
            logger.info(f"   📋 Payment ID: {response_data.get('payment_id')}")
            logger.info(f"   🔗 Payment URL: {response_data.get('payment_url')}")
            logger.info(f"   📊 Status: {response_data.get('status')}")
        else:
            logger.error("❌ ОШИБКА СОЗДАНИЯ ПЛАТЕЖА")
            logger.error(f"   🚫 Error: {response_data.get('error')}")
            if response_data.get('details'):
                logger.error(f"   📋 Details: {response_data.get('details')}")
    
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
        # Логируем начало создания платежа
        self._log_payment_request(user_id, description or self.config.PAYMENT_DESCRIPTION)
        
        # Если платежи не настроены - демо-режим
        if not self.config.is_payment_enabled:
            logger.warning("🟡 ДЕМО-РЕЖИМ: создаю тестовый платеж")
            
            payment_id = f"demo_{uuid.uuid4().hex[:8]}"
            result = {
                "success": True,
                "payment_id": payment_id,
                "payment_url": f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={payment_id}",
                "status": "pending",
                "amount": str(self.config.PAYMENT_AMOUNT),
                "currency": self.config.PAYMENT_CURRENCY,
                "metadata": {
                    "user_id": str(user_id),
                    "demo": True,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            self._log_payment_response(True, result)
            return result
        
        try:
            # Формируем данные платежа с webhook URL
            payment_data = {
                "amount": {
                    "value": f"{self.config.PAYMENT_AMOUNT:.2f}",
                    "currency": self.config.PAYMENT_CURRENCY
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.config.RETURN_URL
                },
                "capture": True,
                "description": description or self.config.PAYMENT_DESCRIPTION,
                "metadata": {
                    "user_id": str(user_id),
                    "telegram_username": f"user_{user_id}",
                    "created_at": datetime.now().isoformat(),
                    "product": "variatica_full_package",
                    "version": "2.0"
                }
            }
            
            # Добавляем webhook URL если он указан в конфиге
            if hasattr(self.config, 'WEBHOOK_URL') and self.config.WEBHOOK_URL:
                webhook_url = self.config.WEBHOOK_URL.rstrip('/')
                payment_data["webhook_url"] = f"{webhook_url}/yookassa-webhook"
                logger.info(f"🔗 Webhook URL добавлен: {payment_data['webhook_url']}")
            else:
                logger.warning("⚠️  Webhook URL не указан в конфигурации!")
                logger.warning("   Автоматическое обновление статусов недоступно")
            
            logger.debug(f"📦 Данные платежа для API:")
            logger.debug(json.dumps(payment_data, indent=2, ensure_ascii=False))
            
            # Отправляем запрос к API ЮKassa
            logger.info("🌐 Отправка запроса к API ЮKassa...")
            
            response = requests.post(
                f"{self.base_url}/payments",
                json=payment_data,
                headers=self._get_headers(),
                timeout=30
            )
            
            # Логируем сырой ответ
            logger.debug(f"📡 HTTP Status: {response.status_code}")
            logger.debug(f"📡 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result_data = response.json()
                logger.debug(f"📊 Ответ API:")
                logger.debug(json.dumps(result_data, indent=2, ensure_ascii=False))
                
                result = {
                    "success": True,
                    "payment_id": result_data["id"],
                    "payment_url": result_data["confirmation"]["confirmation_url"],
                    "status": result_data["status"],
                    "amount": result_data["amount"]["value"],
                    "currency": result_data["amount"]["currency"],
                    "metadata": result_data.get("metadata", {})
                }
                
                self._log_payment_response(True, result)
                return result
                
            else:
                logger.error(f"❌ API Error: {response.status_code}")
                logger.error(f"📋 Response Text: {response.text}")
                
                try:
                    error_data = response.json()
                    logger.error(f"📊 Error JSON: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error(f"📋 Raw Error: {response.text}")
                
                result = {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text[:500] if response.text else "No error details",
                    "status_code": response.status_code
                }
                
                self._log_payment_response(False, result)
                return result
                
        except requests.exceptions.Timeout:
            logger.error("⏰ ТАЙМАУТ: Превышено время ожидания ответа от ЮKassa")
            result = {
                "success": False,
                "error": "Timeout: Превышено время ожидания",
                "details": "Сервер ЮKassa не ответил за 30 секунд"
            }
            self._log_payment_response(False, result)
            return result
            
        except requests.exceptions.ConnectionError:
            logger.error("🔌 ОШИБКА ПОДКЛЮЧЕНИЯ: Не удалось подключиться к ЮKassa")
            result = {
                "success": False,
                "error": "Connection Error",
                "details": "Не удалось установить соединение с API ЮKassa"
            }
            self._log_payment_response(False, result)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 ОШИБКА СЕТИ: {e}")
            result = {
                "success": False,
                "error": f"Network Error: {str(e)}",
                "details": "Ошибка сетевого запроса"
            }
            self._log_payment_response(False, result)
            return result
            
        except Exception as e:
            logger.error(f"🔥 НЕИЗВЕСТНАЯ ОШИБКА: {e}")
            import traceback
            logger.error(f"📋 Трассировка:\n{traceback.format_exc()}")
            
            result = {
                "success": False,
                "error": f"Exception: {str(e)}",
                "details": traceback.format_exc()[:500],
                "traceback": traceback.format_exc()
            }
            self._log_payment_response(False, result)
            return result
    
    def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Dict со статусом платежа
        """
        logger.info(f"🔍 ПРОВЕРКА СТАТУСА ПЛАТЕЖА: {payment_id}")
        
        # Если это демо-платеж
        if payment_id.startswith("demo_") or payment_id.startswith("test_"):
            logger.info("🟡 ДЕМО-РЕЖИМ: возвращаем успешный статус")
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "succeeded",
                "paid": True,
                "amount": str(self.config.PAYMENT_AMOUNT),
                "currency": self.config.PAYMENT_CURRENCY,
                "demo": True
            }
        
        # Если платежи не настроены
        if not self.config.is_payment_enabled:
            logger.warning("🟡 ДЕМО-РЕЖИМ: платежи не настроены")
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "succeeded",
                "paid": True,
                "amount": str(self.config.PAYMENT_AMOUNT),
                "currency": self.config.PAYMENT_CURRENCY,
                "demo": True
            }
        
        try:
            # Реальная проверка статуса
            logger.info(f"🌐 Запрос статуса к API ЮKassa...")
            
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=self._get_headers(),
                timeout=30
            )
            
            logger.debug(f"📡 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Статус платежа: {result['status']}")
                
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
                logger.error(f"❌ Ошибка проверки: {response.status_code}")
                logger.error(f"📋 Response: {response.text}")
                
                return {
                    "success": False,
                    "error": f"Ошибка проверки: {response.status_code}",
                    "status": "unknown",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"🔥 ОШИБКА ПРОВЕРКИ: {e}")
            import traceback
            logger.error(f"📋 Трассировка:\n{traceback.format_exc()}")
            
            return {
                "success": False,
                "error": f"Ошибка: {str(e)}",
                "status": "error"
            }

# Тестирование
if __name__ == "__main__":
    import os
    
    # Настройка логирования для теста
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 ТЕСТИРОВАНИЕ YOOKASSA API")
    print("="*50)
    
    # Проверяем переменные окружения
    shop_id = os.getenv('YOOKASSA_SHOP_ID')
    secret_key = os.getenv('YOOKASSA_SECRET_KEY')
    webhook_url = os.getenv('WEBHOOK_URL')
    
    print(f"🔍 Проверка переменных окружения:")
    print(f"   YOOKASSA_SHOP_ID: {'✅' if shop_id else '❌'} {'установлен' if shop_id else 'не установлен'}")
    print(f"   YOOKASSA_SECRET_KEY: {'✅' if secret_key else '❌'} {'установлен' if secret_key else 'не установлен'}")
    print(f"   WEBHOOK_URL: {'✅ ' + webhook_url if webhook_url else '❌ не установлен'}")
    
    # Создаем конфиг
    from config import Config
    config = Config()
    
    # Создаем API
    yookassa = YooKassaAPI(config)
    
    # Тест создания платежа
    print("\n🧪 Тест создания платежа...")
    result = yookassa.create_payment(
        user_id=123456789,
        description="Тестовый платеж"
    )
    
    print("\n📊 РЕЗУЛЬТАТ ТЕСТА:")
    print(f"   Успех: {'✅' if result['success'] else '❌'}")
    print(f"   Payment ID: {result.get('payment_id', 'N/A')}")
    print(f"   Payment URL: {result.get('payment_url', 'N/A')}")
    print(f"   Ошибка: {result.get('error', 'Нет')}")
    
    # Тест проверки статуса
    if result.get('payment_id'):
        print("\n🧪 Тест проверки статуса...")
        status_result = yookassa.check_payment(result['payment_id'])
        print(f"   Статус: {status_result.get('status', 'N/A')}")
        print(f"   Оплачен: {'✅' if status_result.get('paid') else '❌'}")
