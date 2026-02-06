"""
Конфигурация бота и платежей
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Конфигурация бота и платежей"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # YooKassa
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")
    
    # Настройки платежей
    PAYMENT_AMOUNT: float = 690.00  # Сумма в рублях
    PAYMENT_CURRENCY: str = "RUB"
    PAYMENT_DESCRIPTION: str = "Полный пакет ВАРИАТИКА"
    
    # Пути возврата - ИЗМЕНИТЕ ЭТО!
    # Старый вариант (не работает):
    # RETURN_URL: str = "https://t.me/Testing_Lichnosti_bot"
    
    # Новый вариант (работает):
    RETURN_URL: str = "https://www.yoomoney.ru"  # или любой другой валидный HTTP URL
    # ИЛИ используйте ваш домен Render:
    # RETURN_URL: str = "https://testing-lichnosti-bot-qyra.onrender.com/payment-success"
    
    SUCCESS_URL: str = "https://t.me/Testing_Lichnosti_bot?start=success"
    FAILURE_URL: str = "https://t.me/Testing_Lichnosti_bot?start=failed"
    
    # Автор и ссылки
    AUTHOR_LINK: str = "@meysternlp"
    BOT_LINK: str = "t.me/Testing_Lichnosti_bot"
    PAYMENT_LINK: str = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"
    GIFT_PDF_LINK: str = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
    
    @property
    def is_payment_enabled(self) -> bool:
        """Проверка настроенности платежей"""
        return all([self.YOOKASSA_SHOP_ID, self.YOOKASSA_SECRET_KEY])
    
    @property
    def is_test_mode(self) -> bool:
        """Проверка тестового режима"""
        return self.YOOKASSA_SECRET_KEY.startswith("test_")
    
    def validate(self) -> bool:
        """Валидация конфигурации"""
        errors = []
        
        if not self.BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
        
        # Если платежи не настроены, просто предупреждаем
        if not self.is_payment_enabled:
            print("⚠️  ЮKassa не настроена. Платежи будут в демо-режиме.")
            # Не добавляем ошибку, чтобы бот мог работать
            # errors.append("ЮKassa не настроена (нужны SHOP_ID и SECRET_KEY)")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        return True
