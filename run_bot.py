#!/usr/bin/env python3
"""
Запуск бота с фиксом для Python 3.13
"""

import os
import sys

# Фикс для imghdr в Python 3.13
if sys.version_info >= (3, 13):
    print("🔧 Применяем фикс для отсутствующего imghdr в Python 3.13")
    
    class ImghdrPatch:
        @staticmethod
        def what(*args, **kwargs):
            return None
        
        @staticmethod
        def test_jpeg(*args, **kwargs):
            return False
        
        @staticmethod
        def test_png(*args, **kwargs):
            return False
        
        @staticmethod
        def test_gif(*args, **kwargs):
            return False
        
        @staticmethod
        def test_bmp(*args, **kwargs):
            return False
    
    sys.modules['imghdr'] = ImghdrPatch()

# Теперь импортируем и запускаем основной бот
try:
    import bot_adaptive
    bot_adaptive.main()
except Exception as e:
    print(f"❌ Ошибка запуска бота: {e}")
    sys.exit(1)
