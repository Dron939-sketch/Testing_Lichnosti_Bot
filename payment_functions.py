# payment_functions.py
"""
Функции для работы с платежами ЮKassa
"""

import logging
import time
import random
import base64
import uuid
import requests
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, API_URL, TELEGRAM_BOT_URL, logger

def create_yookassa_invoice_payment(payment_id: str, user_id: int, profile_code: str, amount: float = 690.0, email: str = None) -> dict:
    """Создает платеж через Invoices API ЮKassa"""
    try:
        logger.info(f"📤 Создаю платеж ЮKassa: {payment_id}, профиль: {profile_code}")
        
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        unique_id = uuid.uuid4().hex[:16]
        idempotence_key = f"{payment_id}_{unique_id}_{int(time.time())}"
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': idempotence_key
        }
        
        if not email:
            email = f"user_{user_id}@example.com"
        
        description = f"Полное описание профиля {profile_code} от виртуального психолога"
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": TELEGRAM_BOT_URL
            },
            "capture": True,
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id),
                "profile_code": profile_code,
                "is_test": "false"
            },
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": f"Полное описание профиля {profile_code} от виртуального психолога",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": "1",
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }
                ]
            }
        }
        
        logger.info(f"💳 Отправляю запрос в ЮKassa...")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if confirmation_url:
                logger.info(f"✅ Платеж создан в ЮKassa: {data.get('id')}")
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": confirmation_url,
                    "yookassa_id": data.get('id'),
                    "amount": amount,
                    "profile_code": profile_code,
                    "invoice_type": "yookassa_invoice",
                    "available_methods": "all",
                    "status": data.get('status', 'pending')
                }
            else:
                logger.error(f"❌ Нет ссылки для оплаты в ответе ЮKassa")
                return {"success": False, "error": "Нет ссылки для оплаты"}
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            return {"success": False, "error": f"Ошибка ЮKassa: {response.status_code}", "details": error_text}
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа ЮKassa: {e}")
        return {"success": False, "error": str(e)}

async def create_payment_advanced(user_id: int, profile_code: str, amount: float = 690.00) -> dict:
    """Создает платеж в БД и ЮKassa"""
    
    timestamp = int(time.time())
    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
    user_suffix = str(user_id)[-6:]
    payment_id = f"prod_{timestamp}_{random_str}_{user_suffix}"
    
    logger.info(f"💳 Создаю платеж: {payment_id}, профиль: {profile_code}, сумма: {amount}")
    
    try:
        db_payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "profile_code": profile_code.upper(),
            "amount": amount,
            "email": f"user_{user_id}@example.com",
            "description": f"Полное описание профиля {profile_code} от виртуального психолога"
        }
        
        db_response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=db_payload,
            timeout=10
        )
        
        if db_response.status_code in [200, 201]:
            db_data = db_response.json()
            
            if db_data.get("confirmation_url"):
                logger.info(f"✅ Платеж создан через API: {payment_id}")
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": db_data["confirmation_url"],
                    "amount": amount,
                    "profile_code": profile_code,
                    "yookassa_id": db_data.get("yookassa_id"),
                    "invoice_type": db_data.get("invoice_type", "yookassa_invoice"),
                    "available_methods": db_data.get("available_methods", "all"),
                    "status": db_data.get("status", "pending")
                }
            
            logger.info(f"🔄 Создаю платеж через ЮKassa напрямую: {payment_id}")
            yookassa_result = create_yookassa_invoice_payment(
                payment_id=payment_id,
                user_id=user_id,
                profile_code=profile_code,
                amount=amount,
                email=f"user_{user_id}@example.com"
            )
            
            if yookassa_result["success"]:
                try:
                    update_response = requests.post(
                        f"{API_URL}/api/update-yookassa-id",
                        json={
                            "payment_id": payment_id,
                            "yookassa_id": yookassa_result.get("yookassa_id"),
                            "profile_code": profile_code,
                            "status": "waiting"
                        },
                        timeout=5
                    )
                    
                    if update_response.status_code in [200, 201]:
                        logger.info(f"✅ ID ЮKassa сохранен в БД")
                    else:
                        logger.warning(f"⚠️ Не удалось сохранить ID ЮKassa: {update_response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при сохранении ID ЮKassa: {e}")
                
                return yookassa_result
            else:
                logger.error(f"❌ Ошибка создания платежа в ЮKassa: {yookassa_result.get('error')}")
                return yookassa_result
                
        else:
            error_text = db_response.text[:200]
            logger.error(f"❌ Ошибка БД {db_response.status_code}: {error_text}")
            return {
                "success": False, 
                "error": f"Ошибка API: {db_response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к API: {e}")
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }

async def check_payment_status_api(payment_id: str) -> dict:
    """Проверяет статус платежа через API"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "status": result.get("status", "unknown"),
                "payment_id": payment_id,
                "data": result
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def get_materials_link_api(payment_id: str, user_id: int) -> dict:
    """Получает ссылку на материалы через API"""
    try:
        response = requests.get(
            f"{API_URL}/api/get-materials/{payment_id}",
            params={"user_id": user_id},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return {
                    "success": True,
                    "materials_link": result.get("materials_link"),
                    "profile_code": result.get("profile_code"),
                    "profile_link": result.get("profile_link")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Materials API error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
