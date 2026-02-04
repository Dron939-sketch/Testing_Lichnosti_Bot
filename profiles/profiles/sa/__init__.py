"""
Пакет SA (Социально-аффилиативные) профилей
Экспортирует все 9 профилей
"""

# Автоматический импорт всех файлов sa_*.py
import importlib
import pkgutil
import sys
from pathlib import Path

# Динамически импортируем все модули в этой папке
package_dir = Path(__file__).parent
package_name = __name__

for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
    # Импортируем только sa_*.py файлы
    if module_name.startswith('sa_'):
        full_module_name = f"{package_name}.{module_name}"
        importlib.import_module(full_module_name)

# Собираем все профили из локальной области видимости
from ..base import VariaticaProfile

SA_PROFILES = {}
for name, obj in list(locals().items()):
    if isinstance(obj, VariaticaProfile):
        SA_PROFILES[obj.key] = obj

__all__ = list(SA_PROFILES.keys()) + ['SA_PROFILES']
