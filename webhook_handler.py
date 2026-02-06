"""
Webhook обработчик для ЮKassa
Получает уведомления о платежах и обрабатывает их
"""

import os
import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class YooKassaWebhookHandler:
    """Обработчик webhook уведомлений от ЮKassa"""
    
    def __init__(self, bot_instance=None, db_path="payments.json"):
        """
        Инициализация обработчика
        
        Args:
            bot_instance: Экземпляр Telegram бота (опционально)
            db_path: Путь к файлу для хранения платежей
        """
        self.bot = bot_instance
        self.db_path = db_path
        self.webhook_secret = os.getenv("YOOKASSA_WEBHOOK_SECRET", "")
        
        # Создаем директорию для логов, если нет
        os.makedirs("logs", exist_ok=True)
        os.makedirs("payments", exist_ok=True)
        
        logger.info(f"💰 Webhook handler initialized. Secret: {'SET' if self.webhook_secret else 'NOT SET'}")
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """
        Проверка подписи webhook от ЮKassa
        
        Args:
            body: Тело запроса (строка)
            signature: Подпись из заголовка
            
        Returns:
            bool: True если подпись верна
        """
        if not self.webhook_secret:
            logger.warning("⚠️ Webhook secret not set, skipping signature verification")
            return True
        
        if not signature:
            logger.error("❌ No signature provided")
            return False
        
        # Убираем префикс "sha256=" если есть
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.error(f"❌ Invalid signature. Expected: {expected_signature[:16]}..., Got: {signature[:16]}...")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Signature verification error: {e}")
            return False
    
    async def handle_webhook_request(self, request_body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Обработка входящего webhook запроса
        
        Args:
            request_body: Тело запроса (JSON строка)
            headers: Заголовки запроса
            
        Returns:
            Dict с результатом обработки
        """
        try:
            # Получаем подпись из заголовков
            signature = headers.get('X-Yookassa-Signature') or headers.get('HTTP_YOOKASSA_SIGNATURE') or headers.get('Yookassa-Signature')
            
            if not signature:
                logger.error("❌ No signature found in headers")
                return {"status": "error", "message": "No signature"}
            
            # Проверяем подпись
            if not self.verify_signature(request_body, signature):
                return {"status": "error", "message": "Invalid signature"}
            
            # Парсим JSON
            data = json.loads(request_body)
            event = data.get('event')
            payment_data = data.get('object', {})
            payment_id = payment_data.get('id', 'unknown')
            
            logger.info(f"📨 Webhook received: {event} | ID: {payment_id}")
            
            # Логируем входящий запрос
            await self.log_webhook_request(data, headers)
            
            # Обрабатываем событие
            result = await self.process_event(event, payment_data)
            
            return {
                "status": "success",
                "event": event,
                "payment_id": payment_id,
                "result": result
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return {"status": "error", "message": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ Webhook processing error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_event(self, event: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка конкретного события
        
        Args:
            event: Тип события
            payment_data: Данные платежа
            
        Returns:
            Dict с результатом обработки
        """
        event_handlers = {
            'payment.succeeded': self.handle_payment_succeeded,
            'payment.canceled': self.handle_payment_canceled,
            'refund.succeeded': self.handle_refund_succeeded,
            'payment.waiting_for_capture': self.handle_payment_waiting,
            'payment_method.active': self.handle_payment_method_active,
        }
        
        handler = event_handlers.get(event)
        if handler:
            return await handler(payment_data)
        else:
            logger.warning(f"⚠️ Unhandled event type: {event}")
            return {"status": "ignored", "message": f"Unhandled event: {event}"}
    
    async def handle_payment_succeeded(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка успешного платежа"""
        try:
            payment_id = payment_data.get('id')
            amount_data = payment_data.get('amount', {})
            amount = amount_data.get('value', '0')
            currency = amount_data.get('currency', 'RUB')
            metadata = payment_data.get('metadata', {})
            user_id = metadata.get('user_id')
            
            logger.info(f"💰 Payment SUCCEEDED: {payment_id} | Amount: {amount} {currency} | User: {user_id}")
            
            # Сохраняем информацию о платеже
            await self.save_payment_to_db(payment_data, "succeeded")
            
            # Отправляем файлы пользователю (если есть user_id)
            if user_id:
                delivery_result = await self.deliver_product_to_user(user_id, payment_data)
                return {
                    "status": "success",
                    "message": "Payment processed",
                    "user_notified": bool(delivery_result.get('success')),
                    "delivery_result": delivery_result
                }
            else:
                logger.warning(f"⚠️ No user_id in metadata for payment {payment_id}")
                return {
                    "status": "success",
                    "message": "Payment saved but no user to notify"
                }
                
        except Exception as e:
            logger.error(f"❌ Error processing successful payment: {e}")
            return {"status": "error", "message": str(e)}
    
    async def handle_payment_canceled(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка отмененного платежа"""
        try:
            payment_id = payment_data.get('id')
            reason = payment_data.get('cancellation_details', {}).get('reason', 'unknown')
            
            logger.info(f"❌ Payment CANCELED: {payment_id} | Reason: {reason}")
            
            # Сохраняем информацию
            await self.save_payment_to_db(payment_data, "canceled")
            
            # Уведомляем пользователя (если есть user_id)
            metadata = payment_data.get('metadata', {})
            user_id = metadata.get('user_id')
            
            if user_id and self.bot:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=f"❌ Ваш платеж был отменен.\nID: {payment_id[:8]}...\nПричина: {reason}\n\nПопробуйте оплатить снова."
                    )
                except Exception as e:
                    logger.error(f"Error notifying user about cancel: {e}")
            
            return {"status": "success", "message": "Cancel processed"}
            
        except Exception as e:
            logger.error(f"❌ Error processing canceled payment: {e}")
            return {"status": "error", "message": str(e)}
    
    async def handle_refund_succeeded(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка успешного возврата"""
        try:
            refund_id = payment_data.get('id')
            payment_id = payment_data.get('payment_id')
            amount = payment_data.get('amount', {}).get('value', '0')
            
            logger.info(f"↩️ Refund SUCCEEDED: {refund_id} | Payment: {payment_id} | Amount: {amount}")
            
            # Сохраняем информацию о возврате
            await self.save_refund_to_db(payment_data)
            
            return {"status": "success", "message": "Refund processed"}
            
        except Exception as e:
            logger.error(f"❌ Error processing refund: {e}")
            return {"status": "error", "message": str(e)}
    
    async def handle_payment_waiting(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка платежа, ожидающего подтверждения"""
        payment_id = payment_data.get('id')
        logger.info(f"⏳ Payment WAITING: {payment_id}")
        
        await self.save_payment_to_db(payment_data, "waiting")
        return {"status": "success", "message": "Waiting payment saved"}
    
    async def handle_payment_method_active(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка привязанного способа оплаты"""
        method_id = payment_data.get('id')
        logger.info(f"💳 Payment method ACTIVATED: {method_id}")
        return {"status": "success", "message": "Payment method activated"}
    
    async def save_payment_to_db(self, payment_data: Dict[str, Any], status: str):
        """Сохранение информации о платеже в файл"""
        try:
            payment_id = payment_data.get('id')
            
            payment_info = {
                "id": payment_id,
                "status": status,
                "original_status": payment_data.get('status'),
                "amount": payment_data.get('amount'),
                "created_at": payment_data.get('created_at'),
                "captured_at": payment_data.get('captured_at'),
                "metadata": payment_data.get('metadata', {}),
                "description": payment_data.get('description'),
                "webhook_received_at": datetime.now().isoformat(),
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Сохраняем в отдельный файл для каждого платежа
            payment_file = f"payments/{payment_id}.json"
            with open(payment_file, "w", encoding="utf-8") as f:
                json.dump(payment_info, f, ensure_ascii=False, indent=2)
            
            # Также добавляем в общий лог
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "payment_id": payment_id,
                "status": status,
                "amount": payment_data.get('amount', {}).get('value'),
                "currency": payment_data.get('amount', {}).get('currency')
            }
            
            with open("logs/payments_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            logger.debug(f"💾 Payment saved: {payment_id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving payment: {e}")
    
    async def save_refund_to_db(self, refund_data: Dict[str, Any]):
        """Сохранение информации о возврате"""
        try:
            refund_id = refund_data.get('id')
            
            refund_info = {
                "id": refund_id,
                "payment_id": refund_data.get('payment_id'),
                "status": refund_data.get('status'),
                "amount": refund_data.get('amount'),
                "created_at": refund_data.get('created_at'),
                "webhook_received_at": datetime.now().isoformat()
            }
            
            refund_file = f"payments/refund_{refund_id}.json"
            with open(refund_file, "w", encoding="utf-8") as f:
                json.dump(refund_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error saving refund: {e}")
    
    async def deliver_product_to_user(self, user_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Доставка продукта пользователю
        
        Args:
            user_id: ID пользователя в Telegram
            payment_data: Данные платежа
            
        Returns:
            Dict с результатом доставки
        """
        try:
            payment_id = payment_data.get('id')
            
            if not self.bot:
                logger.warning(f"⚠️ Bot instance not available for delivery to user {user_id}")
                return {"success": False, "error": "Bot not available"}
            
            # Отправляем сообщение пользователю
            message_text = (
                f"🎉 <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\n"
                f"✅ Спасибо за покупку!\n"
                f"💰 Сумма: {payment_data.get('amount', {}).get('value')} {payment_data.get('amount', {}).get('currency')}\n"
                f"📋 ID заказа: <code>{payment_id[:8]}...</code>\n\n"
                f"<b>Ваши материалы:</b>\n\n"
                f"1. <b>Полный разбор профиля</b>\n"
                f"   • Ссылка: https://disk.yandex.ru/d/variatica_package\n\n"
                f"2. <b>Терапевтическая сказка</b>\n"
                f"   • Ссылка: https://disk.yandex.ru/d/variatica_extra\n\n"
                f"3. <b>Книга «ВАРИАТИКА»</b>\n"
                f"   • Ссылка: https://disk.yandex.ru/d/variatica_book\n\n"
                f"<i>Ссылки действительны в течение 30 дней.</i>\n\n"
                f"📞 По вопросам: @meysternlp"
            )
            
            await self.bot.send_message(
                chat_id=int(user_id),
                text=message_text,
                parse_mode="HTML"
            )
            
            logger.info(f"📦 Product delivered to user {user_id} for payment {payment_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "payment_id": payment_id,
                "delivered_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error delivering product to user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def log_webhook_request(self, data: Dict[str, Any], headers: Dict[str, str]):
        """Логирование входящего webhook запроса"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": data.get('event'),
                "payment_id": data.get('object', {}).get('id'),
                "headers": {k: v for k, v in headers.items() if k.lower() not in ['authorization', 'cookie']},
                "data_summary": {
                    "amount": data.get('object', {}).get('amount'),
                    "status": data.get('object', {}).get('status'),
                    "metadata": data.get('object', {}).get('metadata')
                }
            }
            
            log_file = f"logs/webhook_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"❌ Error logging webhook: {e}")
    
    async def notify_admin(self, message: str):
        """Уведомление администратора"""
        try:
            admin_id = os.getenv("ADMIN_ID")
            if admin_id and self.bot:
                await self.bot.send_message(
                    chat_id=int(admin_id),
                    text=f"🔔 Webhook: {message}"
                )
        except Exception as e:
            logger.error(f"❌ Error notifying admin: {e}")


# Функция для быстрого создания обработчика
def create_webhook_handler(bot=None):
    """
    Создание экземпляра обработчика webhook
    
    Args:
        bot: Экземпляр Telegram бота (опционально)
        
    Returns:
        YooKassaWebhookHandler
    """
    return YooKassaWebhookHandler(bot_instance=bot)


# Тестовая функция для проверки webhook
async def test_webhook_handler():
    """Тестирование обработчика webhook"""
    handler = YooKassaWebhookHandler()
    
    # Тестовые данные успешного платежа
    test_payment = {
        "event": "payment.succeeded",
        "object": {
            "id": "test_2a6f1234",
            "status": "succeeded",
            "amount": {
                "value": "690.00",
                "currency": "RUB"
            },
            "metadata": {
                "user_id": "123456789",
                "telegram_username": "test_user"
            },
            "created_at": datetime.now().isoformat(),
            "captured_at": datetime.now().isoformat(),
            "description": "Полный пакет ВАРИАТИКА"
        }
    }
    
    test_body = json.dumps(test_payment)
    test_headers = {"X-Yookassa-Signature": "test_signature"}
    
    result = await handler.handle_webhook_request(test_body, test_headers)
    print(f"Test result: {result}")
    
    return result


if __name__ == "__main__":
    # Тестирование обработчика
    print("🧪 Testing webhook handler...")
    asyncio.run(test_webhook_handler())
