# telegram_patch.py
"""
Патч для исправления python-telegram-bot 20.7 с Python 3.13
"""

import telegram.ext._updater as updater_module

# Сохраняем оригинальный __init__
original_init = updater_module.Updater.__init__

def patched_init(self, *args, **kwargs):
    # Вызываем оригинальный __init__
    result = original_init(self, *args, **kwargs)
    
    # Удаляем проблемный приватный атрибут
    try:
        delattr(self, '_Updater__polling_cleanup_cb')
    except AttributeError:
        pass
    
    return result

# Применяем патч
updater_module.Updater.__init__ = patched_init
print("✅ Патч для telegram-bot 20.7 применен")
