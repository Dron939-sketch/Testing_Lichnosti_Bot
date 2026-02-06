# run_bot_simple.py
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("="*50)
    print("🤖 ЗАПУСК БОТА ВАРИАТИКА v2.0 с ЮKassa")
    print("="*50)
    
    # Проверяем конфигурацию ЮKassa
    shop_id = os.getenv('YOOKASSA_SHOP_ID')
    secret_key = os.getenv('YOOKASSA_SECRET_KEY')
    
    if shop_id and secret_key:
        logger.info(f"✅ ЮKassa настроен: Shop ID: {shop_id[:10]}...")
        logger.info(f"🌐 Webhook URL: {os.getenv('WEBHOOK_URL', 'Не настроен')}/yookassa-webhook")
    else:
        logger.warning("⚠️  ЮKassa не настроен. Платежи не будут работать.")
    
    # Проверяем токен Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
        logger.error("Добавьте в Environment Variables на Render")
        return
    
    logger.info(f"✅ Токен Telegram: {token[:10]}...")
    
    # Импортируем и запускаем бота
    try:
        import telegram
        logger.info(f"📦 python-telegram-bot: {telegram.__version__}")
        
        # Добавляем путь для импорта
        sys.path.insert(0, os.path.dirname(__file__))
        
        from bot_adaptive import main as bot_main
        logger.info("🚀 Запуск основного бота...")
        
        # Запускаем
        bot_main()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        import traceback
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
