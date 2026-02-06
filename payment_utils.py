"""
Вспомогательные функции для платежей
"""

import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def format_price(amount: float) -> str:
    """Форматирование цены"""
    return f"{amount:.2f} ₽"


def validate_email(email: str) -> bool:
    """Валидация email"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def split_message(text: str, max_length: int = 4096) -> List[str]:
    """Разделение длинных сообщений"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        
        split_index = text.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = text.rfind(' ', 0, max_length)
        if split_index == -1:
            split_index = max_length
        
        parts.append(text[:split_index])
        text = text[split_index:].lstrip()
    
    return parts


def create_payment_keyboard(payment_url: str, payment_id: str) -> List[List[dict]]:
    """
    Создание клавиатуры для оплаты
    """
    return [
        [
            {
                "text": f"💳 Оплатить {format_price(690.00)}",
                "url": payment_url
            }
        ],
        [
            {
                "text": "🔄 Проверить оплату",
                "callback_data": f"check_payment_{payment_id}"
            }
        ],
        [
            {
                "text": "📞 Поддержка",
                "url": "https://t.me/meysternlp"
            },
            {
                "text": "❌ Отмена",
                "callback_data": "cancel_payment"
            }
        ]
    ]


class PaymentLogger:
    """Логирование платежей"""
    
    def __init__(self, log_file="payments.log"):
        self.log_file = log_file
    
    def log_payment_event(self, event_type: str, data: dict):
        """Логирование события платежа"""
        from datetime import datetime
        import json
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            logger.info(f"Payment {event_type}: {data.get('payment_id', 'N/A')}")
        except Exception as e:
            logger.error(f"Ошибка логирования платежа: {e}")
