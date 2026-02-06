# telegram_patch.py
"""
ПАТЧ ДЛЯ ИСПРАВЛЕНИЯ python-telegram-bot 20.7 С PYTHON 3.13
Устраняет ошибку: AttributeError: у объекта 'Updater' нет атрибута '_Updater__polling_cleanup_cb'
"""

import sys
import logging

logger = logging.getLogger(__name__)

def apply_patch():
    """Применяет патч для совместимости python-telegram-bot с Python 3.13"""
    try:
        import telegram.ext._updater as updater_module
        
        # Сохраняем оригинальный метод
        original_init = updater_module.Updater.__init__
        
        def patched_init(self, *args, **kwargs):
            """
            Патченая версия __init__ для Updater
            Удаляет проблемный приватный атрибут
            """
            # Вызываем оригинальный конструктор
            result = original_init(self, *args, **kwargs)
            
            # Удаляем атрибут, который вызывает ошибку в Python 3.13
            for attr_name in ['_Updater__polling_cleanup_cb', '__polling_cleanup_cb']:
                try:
                    delattr(self, attr_name)
                except AttributeError:
                    pass
            
            # Также патчим другие проблемные методы если нужно
            if hasattr(self, '_cleanup'):
                try:
                    delattr(self, '_cleanup')
                except:
                    pass
            
            return result
        
        # Заменяем оригинальный конструктор
        updater_module.Updater.__init__ = patched_init
        
        logger.info("✅ Патч для telegram.ext.Updater применен успешно")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать telegram.ext: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка применения патча: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Автоматически применяем патч при импорте
if __name__ == "telegram_patch":
    apply_patch()
    print("🧩 Модуль telegram_patch загружен и патч применен")
