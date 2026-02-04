"""
Главный пакет профилей - экспортирует все 36 профилей
"""

from .base import VariaticaProfile
from .loader import (
    get_profile,
    get_all_profiles,
    get_profiles_by_type,
    get_profiles_by_level,
    PROFILE_REGISTRY
)

__all__ = [
    'VariaticaProfile',
    'get_profile',
    'get_all_profiles', 
    'get_profiles_by_type',
    'get_profiles_by_level',
    'PROFILE_REGISTRY'
]
