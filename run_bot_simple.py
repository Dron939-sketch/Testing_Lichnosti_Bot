# run_bot_simple.py
"""
ПРОСТОЙ ЗАПУСК БОТА БЕЗ FLASK
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("="*50)
    print("🤖 ЗАПУСК БОТА ВАРИАТИКА")
    print("="*50)
    
    # Проверяем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
        print("Добавьте в Environment Variables на Render")
        return
    
    print(f"✅ Токен: {token[:10]}...")
    
    # Импортируем и запускаем бота
    try:
        import telegram
        print(f"📦 python-telegram-bot: {telegram.__version__}")
        
        from bot_adaptive import main as bot_main
        print("🚀 Запуск основного бота...")
        bot_main()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
