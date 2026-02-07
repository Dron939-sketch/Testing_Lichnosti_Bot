# worker_config.py - Конфигурация ТОЛЬКО для Worker
import os

class WorkerConfig:
    """Конфигурация Worker (отдельно от основной БД)"""
    def __init__(self):
        # Telegram Bot Token
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        # API сервера Flask
        self.API_URL = os.getenv('API_URL', 'https://testing-lichnosti-bot-1.onrender.com')
        
        # Ключи ЮKassa (если Worker сам делает платежи)
        self.YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', '')
        self.YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', '')
        
        # Ссылки
        self.BOT_LINK = "https://t.me/Testing_Lichnosti_bot"
        self.GIFT_PDF_LINK = "https://example.com/gift.pdf"
        self.AUTHOR_LINK = "@meysternlp"
        self.PAYMENT_LINK = "https://example.com/payment"
        self.PAYMENT_AMOUNT = 690.00
        
        # Режимы
        self.is_test_mode = os.getenv('TEST_MODE', 'True').lower() == 'true'
    
    def validate(self):
        """Проверка конфигурации Worker"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в Environment Variables!")
        
        if not self.API_URL:
            print("⚠️ API_URL не установлен, некоторые функции не будут работать")
        
        return True

# Глобальный экземпляр
config = WorkerConfig()
