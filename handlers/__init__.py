# handlers/__init__.py
"""
Пакет обработчиков для всех этапов теста
"""

from handlers.stage1 import *
from handlers.stage2 import *
from handlers.stage3 import *
from handlers.stage4 import *
from handlers.common import *
from handlers.results import *
from handlers.payment import *
from handlers.gifts import *

# Явно указываем, что экспортируем все имена из модулей
__all__ = []
# Имена автоматически добавляются через *
