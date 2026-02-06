"""
Конфигурация приложения
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """
    Класс конфигурации приложения
    """
    
    def __init__(self):
        """Инициализация конфигурации"""
        logger.info("="*50)
        logger.info("⚙️  ИНИЦИАЛИЗАЦИЯ КОНФИГУРАЦИИ")
        logger.info("="*50)
        
        # ==================== TELEGRAM БОТ ====================
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.BOT_TOKEN = self.TELEGRAM_BOT_TOKEN  # Дублируем для совместимости
        
        # Проверка токена бота
        if not self.TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
        
        logger.info(f"🤖 Telegram Bot Token: {'✅ Установлен' if self.TELEGRAM_BOT_TOKEN else '❌ Отсутствует'}")
        
        # ==================== БАЗА ДАННЫХ ====================
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')
        
        # Для PostgreSQL используем другую строку подключения
        if self.DATABASE_URL.startswith('postgres://'):
            self.DATABASE_URL = self.DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        logger.info(f"🗄️  Database URL: {self.DATABASE_URL}")
        
        # ==================== YOOKASSA ПЛАТЕЖИ ====================
        self.YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', '')
        self.YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', '')
        
        # Webhook URL для YooKassa (критически важно!)
        # Ваш Render URL: https://testing-lichnosti-bot-qyra.onrender.com
        self.WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://testing-lichnosti-bot-qyra.onrender.com')
        if self.WEBHOOK_URL:
            self.WEBHOOK_URL = self.WEBHOOK_URL.rstrip('/')
        
        # URL для возврата после оплаты
        self.RETURN_URL = os.getenv('RETURN_URL', 'https://t.me/variatica_bot')
        
        # Проверка настроек YooKassa
        yookassa_configured = bool(self.YOOKASSA_SHOP_ID and self.YOOKASSA_SECRET_KEY)
        self.is_payment_enabled = yookassa_configured
        
        if yookassa_configured:
            logger.info("💰 YooKassa: ✅ Настроен (БОЕВОЙ РЕЖИМ)")
            logger.info(f"   Shop ID: {self.YOOKASSA_SHOP_ID[:10]}...")
            logger.info(f"   Webhook URL: {self.WEBHOOK_URL}")
            logger.info(f"   Return URL: {self.RETURN_URL}")
        else:
            logger.error("❌ YooKassa: ❌ НЕ настроен")
            logger.error("   Платежи работать НЕ БУДУТ!")
        
        # ==================== НАСТРОЙКИ ПЛАТЕЖЕЙ ====================
        self.PAYMENT_AMOUNT = float(os.getenv('PAYMENT_AMOUNT', '199.00'))
        self.PAYMENT_CURRENCY = os.getenv('PAYMENT_CURRENCY', 'RUB')
        self.PAYMENT_DESCRIPTION = os.getenv('PAYMENT_DESCRIPTION', 'Оплата подписки Variatica')
        
        # ВСЕГДА боевой режим (без тестового)
        self.is_test_mode = False
        
        logger.info(f"💵 Сумма платежа: {self.PAYMENT_AMOUNT} {self.PAYMENT_CURRENCY}")
        logger.info(f"📝 Описание: {self.PAYMENT_DESCRIPTION}")
        logger.info(f"🔧 Режим: {'🟡 Тестовый' if self.is_test_mode else '🟢 Боевой'}")
        
        # ==================== OPENAI API ====================
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        
        if self.OPENAI_API_KEY:
            logger.info(f"🧠 OpenAI: ✅ Настроен")
            logger.info(f"   Model: {self.OPENAI_MODEL}")
            logger.info(f"   Temperature: {self.OPENAI_TEMPERATURE}")
            logger.info(f"   Max Tokens: {self.OPENAI_MAX_TOKENS}")
        else:
            logger.warning("🧠 OpenAI: ❌ API ключ не установлен")
        
        # ==================== ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ====================
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Пути к файлам
        self.LOG_FILE = 'app.log'
        self.DATABASE_FILE = 'bot_database.db'
        
        # Настройки приложения
        self.APP_NAME = os.getenv('APP_NAME', 'Variatica Bot')
        self.APP_VERSION = os.getenv('APP_VERSION', '2.0')
        
        # Время жизни сессии (в секундах)
        self.SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))
        
        # Лимиты использования
        self.FREE_MESSAGES_LIMIT = int(os.getenv('FREE_MESSAGES_LIMIT', '5'))
        self.PREMIUM_MESSAGES_LIMIT = int(os.getenv('PREMIUM_MESSAGES_LIMIT', '1000'))
        
        # ==================== ССЫЛКИ ДЛЯ БОТА ====================
        self.BOT_LINK = os.getenv('BOT_LINK', 'https://t.me/variatica_bot')
        self.AUTHOR_LINK = os.getenv('AUTHOR_LINK', '@meysternlp')
        self.PAYMENT_LINK = os.getenv('PAYMENT_LINK', 'https://yoomoney.ru/checkout/payments/v2/contract')
        self.GIFT_PDF_LINK = os.getenv('GIFT_PDF_LINK', 'https://drive.google.com/file/d/ваш_файл/view')
        
        logger.info(f"🔗 Bot Link: {self.BOT_LINK}")
        logger.info(f"👤 Author: {self.AUTHOR_LINK}")
        logger.info(f"🎁 Gift PDF: {self.GIFT_PDF_LINK}")
        
        # ==================== ПРОВЕРКИ И ВАЛИДАЦИЯ ====================
        self._validate_configuration()
        
        logger.info("="*50)
        logger.info("✅ КОНФИГУРАЦИЯ ЗАГРУЖЕНА УСПЕШНО")
        logger.info("="*50)
    
    def _parse_admin_ids(self) -> list:
        """
        Парсинг списка ID администраторов
        
        Returns:
            Список ID администраторов
        """
        admin_ids_str = os.getenv('TELEGRAM_ADMIN_IDS', '')
        if not admin_ids_str:
            return []
        
        try:
            # Поддерживаем разные форматы: 123,456,789 или 123 456 789
            admin_ids_str = admin_ids_str.replace(' ', ',')
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip()]
            return admin_ids
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга TELEGRAM_ADMIN_IDS: {e}")
            return []
    
    def validate(self):
        """
        Валидация конфигурации
        """
        errors = []
        warnings = []
        
        # Проверка обязательных полей
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
        
        if not self.DATABASE_URL:
            warnings.append("DATABASE_URL не установлен, используется SQLite по умолчанию")
        
        # Проверка YooKassa для боевого режима
        if not self.is_payment_enabled:
            errors.append("YooKassa не настроен. Платежи работать не будут")
        
        # Проверка webhook URL
        if not self.WEBHOOK_URL:
            warnings.append("WEBHOOK_URL не установлен. Автоматическое обновление статусов платежей недоступно")
        
        # Проверка OpenAI (не обязательно, но рекомендуется)
        if not self.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY не установлен. Некоторые функции могут не работать")
        
        # Логирование ошибок и предупреждений
        if errors:
            logger.error("❌ Ошибки конфигурации:")
            for error in errors:
                logger.error(f"   - {error}")
            raise ValueError(f"Ошибки конфигурации: {', '.join(errors)}")
        
        if warnings:
            logger.warning("⚠️  Предупреждения конфигурации:")
            for warning in warnings:
                logger.warning(f"   - {warning}")
        
        return True
    
    def _validate_configuration(self):
        """
        Проверка валидности конфигурации
        """
        try:
            self.validate()
        except ValueError as e:
            logger.error(f"❌ Критическая ошибка конфигурации: {e}")
            raise
    
    def get_database_config(self) -> dict:
        """
        Получение конфигурации базы данных
        
        Returns:
            Словарь с настройками БД
        """
        return {
            'url': self.DATABASE_URL,
            'echo': self.DEBUG_MODE
        }
    
    def get_openai_config(self) -> dict:
        """
        Получение конфигурации OpenAI
        
        Returns:
            Словарь с настройками OpenAI
        """
        return {
            'api_key': self.OPENAI_API_KEY,
            'model': self.OPENAI_MODEL,
            'temperature': self.OPENAI_TEMPERATURE,
            'max_tokens': self.OPENAI_MAX_TOKENS
        }
    
    def get_yookassa_config(self) -> dict:
        """
        Получение конфигурации YooKassa
        
        Returns:
            Словарь с настройками YooKassa
        """
        return {
            'shop_id': self.YOOKASSA_SHOP_ID,
            'secret_key': self.YOOKASSA_SECRET_KEY,
            'webhook_url': self.WEBHOOK_URL,
            'return_url': self.RETURN_URL,
            'is_enabled': self.is_payment_enabled,
            'is_test_mode': self.is_test_mode,
            'amount': self.PAYMENT_AMOUNT,
            'currency': self.PAYMENT_CURRENCY,
            'description': self.PAYMENT_DESCRIPTION
        }
    
    def get_logging_config(self) -> dict:
        """
        Получение конфигурации логирования
        
        Returns:
            Словарь с настройками логирования
        """
        return {
            'level': self.LOG_LEVEL,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'filename': self.LOG_FILE,
            'filemode': 'a'
        }
    
    def get_app_config(self) -> dict:
        """
        Получение общей конфигурации приложения
        
        Returns:
            Словарь с настройками приложения
        """
        return {
            'name': self.APP_NAME,
            'version': self.APP_VERSION,
            'debug': self.DEBUG_MODE,
            'session_timeout': self.SESSION_TIMEOUT,
            'free_messages_limit': self.FREE_MESSAGES_LIMIT,
            'premium_messages_limit': self.PREMIUM_MESSAGES_LIMIT,
            'bot_link': self.BOT_LINK,
            'author_link': self.AUTHOR_LINK,
            'payment_link': self.PAYMENT_LINK,
            'gift_pdf_link': self.GIFT_PDF_LINK
        }
    
    def __str__(self) -> str:
        """
        Строковое представление конфигурации
        
        Returns:
            Форматированная строка с конфигурацией
        """
        config_str = []
        config_str.append("="*50)
        config_str.append("⚙️  КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ")
        config_str.append("="*50)
        
        config_str.append(f"🤖 Telegram Bot: {'✅' if self.TELEGRAM_BOT_TOKEN else '❌'}")
        
        config_str.append(f"🗄️  Database: {self.DATABASE_URL}")
        
        config_str.append(f"💰 YooKassa: {'✅' if self.is_payment_enabled else '❌'}")
        if self.is_payment_enabled:
            config_str.append(f"   Режим: {'🟡 Тестовый' if self.is_test_mode else '🟢 Боевой'}")
            config_str.append(f"   Webhook: {'✅' if self.WEBHOOK_URL else '❌'}")
            config_str.append(f"   Сумма: {self.PAYMENT_AMOUNT} {self.PAYMENT_CURRENCY}")
        
        config_str.append(f"🧠 OpenAI: {'✅' if self.OPENAI_API_KEY else '❌'}")
        if self.OPENAI_API_KEY:
            config_str.append(f"   Модель: {self.OPENAI_MODEL}")
        
        config_str.append(f"🔗 Ссылки:")
        config_str.append(f"   Бот: {self.BOT_LINK}")
        config_str.append(f"   Автор: {self.AUTHOR_LINK}")
        config_str.append(f"   Webhook: {self.WEBHOOK_URL}")
        
        config_str.append(f"📱 Приложение: {self.APP_NAME} v{self.APP_VERSION}")
        config_str.append(f"⏱️  Таймаут сессии: {self.SESSION_TIMEOUT} сек")
        config_str.append(f"📨 Лимиты: {self.FREE_MESSAGES_LIMIT} (бесп.) / {self.PREMIUM_MESSAGES_LIMIT} (премиум)")
        
        config_str.append("="*50)
        
        return "\n".join(config_str)


# Создаем глобальный экземпляр конфигурации
config = Config()

# Экспортируем конфигурацию
__all__ = ['Config', 'config']


if __name__ == "__main__":
    """
    Тестирование конфигурации
    """
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ")
    print("="*60)
    
    print(str(config))
    
    print("\n📋 Подробная информация:")
    print(f"   Токен бота: {'✅' if config.TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"   База данных: {config.DATABASE_URL}")
    print(f"   YooKassa настроен: {'✅' if config.is_payment_enabled else '❌'}")
    print(f"   Webhook URL: {config.WEBHOOK_URL}")
    print(f"   OpenAI API ключ: {'✅' if config.OPENAI_API_KEY else '❌'}")
    print(f"   Режим отладки: {config.DEBUG_MODE}")
    
    print("\n⚙️  Конфигурация YooKassa:")
    yookassa_config = config.get_yookassa_config()
    for key, value in yookassa_config.items():
        if key == 'secret_key' and value:
            value = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else "***"
        elif key == 'shop_id' and value:
            value = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else value
        print(f"   {key}: {value}")
    
    print("\n✅ Конфигурация загружена успешно!")
    print("="*60)
