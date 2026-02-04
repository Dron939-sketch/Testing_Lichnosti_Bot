# profiles/ia/__init__.py
# Экспортируем все профили из этой папки

# Импортируем каждый файл профиля
from .ia_1_def import IA_1_def
from .ia_2_sit import IA_2_sit
from .ia_3_con import IA_3_con
from .ia_4_exp import IA_4_exp
from .ia_5_int import IA_5_int
from .ia_6_aut import IA_6_aut
from .ia_7_val import IA_7_val
from .ia_8_tra import IA_8_tra
from .ia_9_ide import IA_9_ide

# Экспортируем для удобства
__all__ = [
    'IA_1_def',
    'IA_2_sit', 
    'IA_3_con',
    'IA_4_exp',
    'IA_5_int',
    'IA_6_aut',
    'IA_7_val',
    'IA_8_tra',
    'IA_9_ide'
]
