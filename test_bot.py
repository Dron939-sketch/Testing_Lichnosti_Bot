# test_bot.py
import sys
import os

# Добавляем путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Подавляем warnings
import warnings
warnings.filterwarnings("ignore")

try:
    print("Пытаюсь импортировать бота...")
    from bot_adaptive import main
    print("✅ Импорт успешен!")
    
    # Проверяем токен
    import os
    token = os.getenv('TELEGRAM_BOT_TOKEN', 'TEST')
    print(f"Токен: {token[:10]}...")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Другая ошибка: {e}")
