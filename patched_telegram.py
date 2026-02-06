# patched_telegram.py
"""
Патч для исправления ошибки python-telegram-bot с Python 3.13
"""

import telegram.ext._updater as updater_module

# Сохраняем оригинальный __init__
original_init = updater_module.Updater.__init__

def patched_init(self, *args, **kwargs):
    # Вызываем оригинальный __init__
    original_init(self, *args, **kwargs)
    
    # Удаляем проблемный атрибут если он есть
    try:
        delattr(self, '_Updater__polling_cleanup_cb')
    except AttributeError:
        pass

# Применяем патч
updater_module.Updater.__init__ = patched_init

print("✅ Патч для telegram-bot применен")
