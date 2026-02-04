# profiles/loader.py
"""
Загрузчик всех профилей
Простая версия - явные импорты
"""

from .base import VariaticaProfile
from typing import Dict, Optional

# Импортируем ВСЕ профили
# SA профили (9 штук)
from .sa.sa_1 import SA_1
from .sa.sa_2 import SA_2
from .sa.sa_3 import SA_3
from .sa.sa_4 import SA_4
from .sa.sa_5 import SA_5
from .sa.sa_6 import SA_6
from .sa.sa_7 import SA_7
from .sa.sa_8 import SA_8
from .sa.sa_9 import SA_9

# IA профили (9 штук)
from .ia.ia_1 import IA_1
from .ia.ia_2 import IA_2
from .ia.ia_3 import IA_3
from .ia.ia_4 import IA_4
from .ia.ia_5 import IA_5
from .ia.ia_6 import IA_6
from .ia.ia_7 import IA_7
from .ia.ia_8 import IA_8
from .ia.ia_9 import IA_9

# SP профили (9 штук)
from .sp.sp_1 import SP_1
from .sp.sp_2 import SP_2
from .sp.sp_3 import SP_3
from .sp.sp_4 import SP_4
from .sp.sp_5 import SP_5
from .sp.sp_6 import SP_6
from .sp.sp_7 import SP_7
from .sp.sp_8 import SP_8
from .sp.sp_9 import SP_9

# IP профили (9 штук)
from .ip.ip_1 import IP_1
from .ip.ip_2 import IP_2
from .ip.ip_3 import IP_3
from .ip.ip_4 import IP_4
from .ip.ip_5 import IP_5
from .ip.ip_6 import IP_6
from .ip.ip_7 import IP_7
from .ip.ip_8 import IP_8
from .ip.ip_9 import IP_9

# Реестр всех 36 профилей
PROFILES: Dict[str, VariaticaProfile] = {
    # SA (1-9)
    "SA_1": SA_1, "SA_2": SA_2, "SA_3": SA_3,
    "SA_4": SA_4, "SA_5": SA_5, "SA_6": SA_6,
    "SA_7": SA_7, "SA_8": SA_8, "SA_9": SA_9,
    
    # IA (10-18)
    "IA_1": IA_1, "IA_2": IA_2, "IA_3": IA_3,
    "IA_4": IA_4, "IA_5": IA_5, "IA_6": IA_6,
    "IA_7": IA_7, "IA_8": IA_8, "IA_9": IA_9,
    
    # SP (19-27)
    "SP_1": SP_1, "SP_2": SP_2, "SP_3": SP_3,
    "SP_4": SP_4, "SP_5": SP_5, "SP_6": SP_6,
    "SP_7": SP_7, "SP_8": SP_8, "SP_9": SP_9,
    
    # IP (28-36)
    "IP_1": IP_1, "IP_2": IP_2, "IP_3": IP_3,
    "IP_4": IP_4, "IP_5": IP_5, "IP_6": IP_6,
    "IP_7": IP_7, "IP_8": IP_8, "IP_9": IP_9,
}

def get_profile(key: str) -> Optional[VariaticaProfile]:
    """Получить профиль по ключу"""
    return PROFILES.get(key)

def get_all_profiles() -> Dict[str, VariaticaProfile]:
    """Получить все 36 профилей"""
    return PROFILES.copy()

def get_profiles_by_type(profile_type: str) -> Dict[str, VariaticaProfile]:
    """Получить профили по типу (SA, IA, SP, IP)"""
    return {k: v for k, v in PROFILES.items() if v.type_code == profile_type.upper()}

def get_profiles_by_level(level: int) -> Dict[str, VariaticaProfile]:
    """Получить профили по уровню (1-9)"""
    return {k: v for k, v in PROFILES.items() if v.level == level}

print(f"✅ Загружено профилей: {len(PROFILES)}/36")
