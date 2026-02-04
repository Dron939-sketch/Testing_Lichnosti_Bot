# loader.py
import os
import importlib
from typing import Dict
from base import VariaticaProfile

class ProfileLoader:
    def __init__(self):
        self.profiles: Dict[str, VariaticaProfile] = {}
        self.load_all_profiles()
    
    def load_all_profiles(self):
        """Загружает все профили из папок profiles/"""
        profile_types = ['sa', 'ia', 'sp', 'ip']
        
        for profile_type in profile_types:
            try:
                # Импортируем модуль целиком (например, profiles.sa)
                module_name = f"profiles.{profile_type}"
                module = importlib.import_module(module_name)
                
                # Ищем все переменные в модуле, которые являются VariaticaProfile
                for attr_name in dir(module):
                    if attr_name.startswith(profile_type.upper()):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, VariaticaProfile):
                            self.profiles[attr.key] = attr
                            print(f"✅ Загружен профиль: {attr.key}")
                        
            except ImportError as e:
                print(f"⚠ Не удалось загрузить {profile_type}: {e}")
            except Exception as e:
                print(f"❌ Ошибка при загрузке {profile_type}: {e}")
    
    def get_profile(self, key: str) -> VariaticaProfile:
        """Получить профиль по ключу"""
        return self.profiles.get(key)
    
    def get_all_profiles(self):
        """Получить все профили"""
        return list(self.profiles.keys())
    
    def get_profiles_by_type(self, type_code: str):
        """Получить профили определенного типа"""
        return {k: v for k, v in self.profiles.items() 
                if v.type_code == type_code.upper()}
    
    def get_profiles_by_level(self, level: int):
        """Получить профили определенного уровня"""
        return {k: v for k, v in self.profiles.items() 
                if v.level == level}

# Создаем глобальный загрузчик
loader = ProfileLoader()
