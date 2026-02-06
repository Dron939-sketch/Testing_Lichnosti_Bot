"""
Конфигурация приложения для Variatica Bot + Flask Webhook
Версия для двух сервисов на Render:
1. Telegram Bot (Web Service)
2. Flask Webhook Server (Web Service)
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
        logger.info("⚙️  ИНИЦИАЛИЗАЦИЯ КОНФИГУРАЦИИ VARIATICA 2.0")
        logger.info("="*50)
        
        # ==================== ОБЩИЕ НАСТРОЙКИ ====================
        self.APP_NAME = "Variatica Adaptive Test Bot"
        self.APP_VERSION = "2.0"
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        # Определяем какой сервис запущен (по переменной окружения или по контексту)
        self.SERVICE_TYPE = os.getenv('SERVICE_TYPE', 'telegram_bot')  # telegram_bot или flask_webhook
        
        # ==================== TELEGRAM БОТ ====================
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.BOT_TOKEN = self.TELEGRAM_BOT_TOKEN  # Дублируем для совместимости
        
        # Проверка токена бота (только для Telegram бота)
        if self.SERVICE_TYPE == 'telegram_bot':
            if not self.TELEGRAM_BOT_TOKEN:
                logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
                raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
            
            logger.info(f"🤖 Telegram Bot Token: {'✅ Установлен' if self.TELEGRAM_BOT_TOKEN else '❌ Отсутствует'}")
        else:
            logger.info(f"🤖 Telegram Bot Token: Не требуется (Flask сервер)")
        
        # ==================== WEBHOOK URL (КРИТИЧЕСКИ ВАЖНО!) ====================
        # Это URL твоего Flask сервера на Render:
        # https://testing-lichnosti-bot-qyra.onrender.com
        self.WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://testing-lichnosti-bot-qyra.onrender.com')
        if self.WEBHOOK_URL:
            self.WEBHOOK_URL = self.WEBHOOK_URL.rstrip('/')
        
        logger.info(f"🌐 Webhook URL: {self.WEBHOOK_URL}")
        
        # Проверяем, что WEBHOOK_URL установлен (особенно важно для Telegram бота)
        if self.SERVICE_TYPE == 'telegram_bot' and not self.WEBHOOK_URL:
            logger.error("❌ WEBHOOK_URL не установлен! Telegram бот не сможет работать с API")
            raise ValueError("WEBHOOK_URL не установлен в переменных окружения")
        
        # ==================== YOOKASSA ПЛАТЕЖИ ====================
        self.YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', '')
        self.YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', '')
        
        # URL для возврата после оплаты
        self.RETURN_URL = os.getenv('RETURN_URL', 'https://t.me/variatica_bot')
        
        # Определяем кто обрабатывает платежи:
        # telegram_bot: создает платежи (если есть ключи)
        # flask_webhook: принимает webhook и обновляет БД
        if self.SERVICE_TYPE == 'telegram_bot':
            # Для бота - платежи создаются через API, ключи опциональны
            yookassa_configured = bool(self.YOOKASSA_SHOP_ID and self.YOOKASSA_SECRET_KEY)
            self.is_payment_enabled = yookassa_configured
            
            if yookassa_configured:
                logger.info("💰 YooKassa: ✅ Настроен (бот создает платежи)")
                logger.info(f"   Shop ID: {self.YOOKASSA_SHOP_ID[:10]}...")
            else:
                logger.warning("💰 YooKassa: ⚠️  Ключи не указаны")
                logger.warning("   Бот будет создавать платежи через Flask API")
        
        elif self.SERVICE_TYPE == 'flask_webhook':
            # Для Flask сервера - ключи ОБЯЗАТЕЛЬНЫ для верификации webhook
            yookassa_configured = bool(self.YOOKASSA_SHOP_ID and self.YOOKASSA_SECRET_KEY)
            self.is_payment_enabled = yookassa_configured
            
            if yookassa_configured:
                logger.info("💰 YooKassa: ✅ Настроен (Flask принимает webhook)")
                logger.info(f"   Shop ID: {self.YOOKASSA_SHOP_ID[:10]}...")
                logger.info(f"   Webhook endpoint: {self.WEBHOOK_URL}/yookassa-webhook")
            else:
                logger.error("❌ YooKassa: ⚠️  Ключи не указаны!")
                logger.error("   Flask сервер не сможет верифицировать webhook от ЮKassa")
        
        # ==================== НАСТРОЙКИ ПЛАТЕЖЕЙ ====================
        self.PAYMENT_AMOUNT = float(os.getenv('PAYMENT_AMOUNT', '199.00'))
        self.PAYMENT_CURRENCY = os.getenv('PAYMENT_CURRENCY', 'RUB')
        self.PAYMENT_DESCRIPTION = os.getenv('PAYMENT_DESCRIPTION', 'Оплата подписки Variatica')
        
        # ВСЕГДА боевой режим (без тестового)
        self.is_test_mode = False
        
        logger.info(f"💵 Сумма платежа: {self.PAYMENT_AMOUNT} {self.PAYMENT_CURRENCY}")
        logger.info(f"📝 Описание: {self.PAYMENT_DESCRIPTION}")
        logger.info(f"🔧 Режим: {'🟡 Тестовый' if self.is_test_mode else '🟢 Боевой'}")
        
        # ==================== БАЗА ДАННЫХ ====================
        # Для Flask сервера используем PostgreSQL от Render
        # Для Telegram бота - SQLite (или БД не нужна)
        self.DATABASE_URL = os.getenv('DATABASE_URL', '')
        
        if self.SERVICE_TYPE == 'flask_webhook':
            if not self.DATABASE_URL:
                logger.error("❌ DATABASE_URL не установлен для Flask сервера!")
                raise ValueError("DATABASE_URL не установлен в переменных окружения для Flask сервера")
            
            # Для PostgreSQL исправляем строку подключения
            if self.DATABASE_URL.startswith('postgres://'):
                self.DATABASE_URL = self.DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            
            logger.info(f"🗄️  Database URL (PostgreSQL): Установлен")
            logger.info(f"   Используется PostgreSQL от Render")
        
        elif self.SERVICE_TYPE == 'telegram_bot':
            # Для бота можно использовать SQLite
            if self.DATABASE_URL:
                logger.info(f"🗄️  Database URL: {self.DATABASE_URL}")
            else:
                logger.info("🗄️  Database URL: Не требуется (бот работает через API)")
        
        # ==================== OPENAI API (ОПЦИОНАЛЬНО) ====================
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        
        if self.OPENAI_API_KEY:
            logger.info(f"🧠 OpenAI: ✅ Настроен")
            logger.info(f"   Model: {self.OPENAI_MODEL}")
        else:
            logger.info("🧠 OpenAI: ❌ API ключ не установлен (опционально)")
        
        # ==================== ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ====================
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Пути к файлам
        self.LOG_FILE = 'app.log'
        
        # Время жизни сессии (в секундах)
        self.SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))
        
        # Лимиты использования (для будущих функций)
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
        
        # ==================== ПОРТЫ ДЛЯ RENDER ====================
        self.TELEGRAM_BOT_PORT = int(os.getenv('PORT', '10000'))  # Render сам назначает порт
        self.FLASK_WEBHOOK_PORT = int(os.getenv('PORT', '10001'))  # Render сам назначает порт
        
        logger.info(f"🚀 Сервис запущен как: {self.SERVICE_TYPE.upper()}")
        logger.info(f"🔌 Telegram бот порт: {self.TELEGRAM_BOT_PORT}")
        logger.info(f"🔌 Flask сервер порт: {self.FLASK_WEBHOOK_PORT}")
        
        # ==================== ПРОВЕРКИ И ВАЛИДАЦИЯ ====================
        self._validate_configuration()
        
        logger.info("="*50)
        logger.info(f"✅ КОНФИГУРАЦИЯ ЗАГРУЖЕНА ({self.SERVICE_TYPE.upper()})")
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
        
        if self.SERVICE_TYPE == 'telegram_bot':
            # Проверки для Telegram бота
            if not self.TELEGRAM_BOT_TOKEN:
                errors.append("TELEGRAM_BOT_TOKEN не установлен")
            
            if not self.WEBHOOK_URL:
                errors.append("WEBHOOK_URL не установлен. Бот не сможет работать с API")
            
            # YooKassa ключи необязательны для бота (может работать через API)
            if not self.YOOKASSA_SHOP_ID or not self.YOOKASSA_SECRET_KEY:
                warnings.append("YooKassa ключи не установлены. Бот будет создавать платежи через Flask API")
        
        elif self.SERVICE_TYPE == 'flask_webhook':
            # Проверки для Flask сервера
            if not self.WEBHOOK_URL:
                warnings.append("WEBHOOK_URL не установлен. Самопроверка недоступна")
            
            if not self.YOOKASSA_SHOP_ID or not self.YOOKASSA_SECRET_KEY:
                errors.append("YooKassa ключи не установлены. Flask сервер не сможет верифицировать webhook")
            
            if not self.DATABASE_URL:
                errors.append("DATABASE_URL не установлен. Flask серверу нужна PostgreSQL БД")
        
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
            'echo': self.DEBUG_MODE,
            'service': self.SERVICE_TYPE
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
            'webhook_url': f"{self.WEBHOOK_URL}/yookassa-webhook" if self.WEBHOOK_URL else None,
            'return_url': self.RETURN_URL,
            'is_enabled': self.is_payment_enabled,
            'is_test_mode': self.is_test_mode,
            'amount': self.PAYMENT_AMOUNT,
            'currency': self.PAYMENT_CURRENCY,
            'description': self.PAYMENT_DESCRIPTION,
            'service_type': self.SERVICE_TYPE
        }
    
    def get_api_config(self) -> dict:
        """
        Получение конфигурации API
        
        Returns:
            Словарь с настройками API
        """
        return {
            'webhook_url': self.WEBHOOK_URL,
            'api_endpoints': {
                'payment_status': f"{self.WEBHOOK_URL}/api/payment-status" if self.WEBHOOK_URL else None,
                'create_payment': f"{self.WEBHOOK_URL}/api/create-payment" if self.WEBHOOK_URL else None,
                'update_yookassa': f"{self.WEBHOOK_URL}/api/update-yookassa-id" if self.WEBHOOK_URL else None
            }
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
            'filemode': 'a',
            'service': self.SERVICE_TYPE
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
            'service_type': self.SERVICE_TYPE,
            'session_timeout': self.SESSION_TIMEOUT,
            'free_messages_limit': self.FREE_MESSAGES_LIMIT,
            'premium_messages_limit': self.PREMIUM_MESSAGES_LIMIT,
            'bot_link': self.BOT_LINK,
            'author_link': self.AUTHOR_LINK,
            'payment_link': self.PAYMENT_LINK,
            'gift_pdf_link': self.GIFT_PDF_LINK,
            'webhook_url': self.WEBHOOK_URL,
            'ports': {
                'telegram_bot': self.TELEGRAM_BOT_PORT,
                'flask_webhook': self.FLASK_WEBHOOK_PORT
            }
        }
    
    def get_service_specific_config(self) -> dict:
        """
        Получение специфической конфигурации для сервиса
        
        Returns:
            Словарь с настройками сервиса
        """
        if self.SERVICE_TYPE == 'telegram_bot':
            return {
                'start_command': 'python bot_adaptive.py',
                'health_check': f'https://variatica-telegram-bot.onrender.com',
                'api_calls': True,
                'requires_database': False,
                'requires_yookassa_keys': False
            }
        elif self.SERVICE_TYPE == 'flask_webhook':
            return {
                'start_command': 'gunicorn app:app',
                'health_check': self.WEBHOOK_URL,
                'api_calls': False,
                'requires_database': True,
                'requires_yookassa_keys': True
            }
        return {}
    
    def __str__(self) -> str:
        """
        Строковое представление конфигурации
        
        Returns:
            Форматированная строка с конфигурацией
        """
        config_str = []
        config_str.append("="*50)
        config_str.append(f"⚙️  КОНФИГУРАЦИЯ {self.SERVICE_TYPE.upper()}")
        config_str.append("="*50)
        
        config_str.append(f"📱 Приложение: {self.APP_NAME} v{self.APP_VERSION}")
        config_str.append(f"🔧 Сервис: {self.SERVICE_TYPE}")
        config_str.append(f"🌐 Webhook URL: {self.WEBHOOK_URL}")
        
        if self.SERVICE_TYPE == 'telegram_bot':
            config_str.append(f"🤖 Telegram Bot: {'✅' if self.TELEGRAM_BOT_TOKEN else '❌'}")
            config_str.append(f"🔌 Порт: {self.TELEGRAM_BOT_PORT}")
        
        config_str.append(f"💰 YooKassa: {'✅' if self.is_payment_enabled else '❌'}")
        if self.is_payment_enabled:
            config_str.append(f"   Режим: {'🟡 Тестовый' if self.is_test_mode else '🟢 Боевой'}")
            config_str.append(f"   Сумма: {self.PAYMENT_AMOUNT} {self.PAYMENT_CURRENCY}")
        
        if self.SERVICE_TYPE == 'flask_webhook':
            config_str.append(f"🗄️  Database: {'✅ PostgreSQL' if self.DATABASE_URL else '❌ Нет'}")
            config_str.append(f"🔌 Порт: {self.FLASK_WEBHOOK_PORT}")
            config_str.append(f"📡 Webhook endpoint: {self.WEBHOOK_URL}/yookassa-webhook")
        
        config_str.append(f"🧠 OpenAI: {'✅' if self.OPENAI_API_KEY else '❌'}")
        
        config_str.append(f"🔗 Ссылки:")
        config_str.append(f"   Бот: {self.BOT_LINK}")
        config_str.append(f"   Автор: {self.AUTHOR_LINK}")
        
        service_config = self.get_service_specific_config()
        if service_config:
            config_str.append(f"⚙️  Конфигурация сервиса:")
            for key, value in service_config.items():
                config_str.append(f"   {key}: {value}")
        
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
    print(f"   Сервис: {config.SERVICE_TYPE}")
    print(f"   Webhook URL: {config.WEBHOOK_URL}")
    
    if config.SERVICE_TYPE == 'telegram_bot':
        print(f"   Токен бота: {'✅' if config.TELEGRAM_BOT_TOKEN else '❌'}")
    
    print(f"   YooKassa настроен: {'✅' if config.is_payment_enabled else '❌'}")
    
    if config.SERVICE_TYPE == 'flask_webhook':
        print(f"   База данных: {'✅' if config.DATABASE_URL else '❌'}")
        print(f"   Webhook endpoint: {config.WEBHOOK_URL}/yookassa-webhook")
    
    api_config = config.get_api_config()
    print(f"\n🌐 API конфигурация:")
    for endpoint, url in api_config['api_endpoints'].items():
        print(f"   {endpoint}: {url}")
    
    print(f"\n⚙️  Конфигурация YooKassa:")
    yookassa_config = config.get_yookassa_config()
    for key, value in yookassa_config.items():
        if key in ['secret_key', 'shop_id'] and value:
            if isinstance(value, str) and len(value) > 10:
                value = f"{value[:5]}...{value[-5:]}"
        print(f"   {key}: {value}")
    
    print("\n✅ Конфигурация загружена успешно!")
    print("="*60)
