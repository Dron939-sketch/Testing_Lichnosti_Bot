# payment_utils.py - Утилиты для платежей
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PaymentLogger:
    """Логирование платежных событий"""
    
    def log_payment_event(self, event_type, data):
        """Логирует платежное событие"""
        logger.info(f"💰 {event_type.upper()}: {data}")

def format_price(amount):
    """Форматирует цену в читаемый вид"""
    if isinstance(amount, (int, float)):
        return f"{amount:,.2f} ₽".replace(",", " ").replace(".00", "")
    return str(amount)

def validate_email(email):
    """Валидация email адреса"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_payment_id(user_id):
    """Генерация ID платежа"""
    timestamp = int(datetime.now().timestamp())
    return f"payment_{user_id}_{timestamp}"

def parse_amount(amount_str):
    """Парсит сумму из строки"""
    try:
        # Убираем все нецифровые символы, кроме точки
        cleaned = re.sub(r'[^\d.]', '', str(amount_str))
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

# Альтернативно, если хотите минимальную версию:
# def format_price(amount):
#     return f"{amount} ₽"
