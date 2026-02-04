"""
Динамический загрузчик всех 36 профилей
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Optional
from .base import VariaticaProfile

# Реестр всех профилей {ключ: объект}
PROFILE_REGISTRY: Dict[str, VariaticaProfile] = {}

def _discover_profiles():
    """Автоматически находит и загружает все профили"""
    package_dir = Path(__file__).parent
    
    # Папки типов
    type_folders = ['sa', 'ia', 'sp', 'ip']
    
    for folder in type_folders:
        type_dir = package_dir / folder
        
        if not type_dir.exists():
            continue
            
        # Импортируем модуль типа (например, profiles.sa)
        try:
            type_module = importlib.import_module(f"profiles.{folder}")
            
            # Ищем все атрибуты-профили в модуле
            for attr_name in dir(type_module):
                attr = getattr(type_module, attr_name)
                
                if isinstance(attr, VariaticaProfile):
                    PROFILE_REGISTRY[attr.key] = attr
                    print(f"✅ Загружен профиль: {attr.key}")
                    
        except ImportError as e:
            print(f"⚠️ Не удалось загрузить {folder}: {e}")

def get_profile(key: str) -> Optional[VariaticaProfile]:
    """Получить профиль по ключу"""
    return PROFILE_REGISTRY.get(key)

def get_all_profiles() -> Dict[str, VariaticaProfile]:
    """Получить все 36 профилей"""
    if not PROFILE_REGISTRY:
        _discover_profiles()
    return PROFILE_REGISTRY.copy()

def get_profiles_by_type(profile_type: str) -> Dict[str, VariaticaProfile]:
    """Получить профили по типу (SA, IA, SP, IP)"""
    return {
        k: v for k, v in get_all_profiles().items() 
        if v.type_code == profile_type.upper()
    }

def get_profiles_by_level(level: int) -> Dict[str, VariaticaProfile]:
    """Получить профили по уровню (1-9)"""
    return {
        k: v for k, v in get_all_profiles().items() 
        if v.level == level
    }

# Автозагрузка при импорте
_discover_profiles()
print(f"📊 Загружено профилей: {len(PROFILE_REGISTRY)}/36")
