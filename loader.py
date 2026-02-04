# loader.py
"""
Загрузчик профилей из файловой системы
"""

import os
import glob
import importlib.util
from pathlib import Path
from base import VariaticaProfile

class ProfileLoader:
    """Загрузчик профилей из файлов"""
    
    def __init__(self, profiles_dir: str = "profiles"):
        """
        Инициализация загрузчика
        
        Args:
            profiles_dir: Директория с файлами профилей
        """
        self.profiles_dir = profiles_dir
        self.profiles = {}  # Словарь профилей: {profile_key: VariaticaProfile}
        self.load_all_profiles()
    
    def load_profile_from_file(self, filepath: str) -> VariaticaProfile:
        """
        Загружает профиль из файла Python
        
        Args:
            filepath: Путь к файлу профиля
            
        Returns:
            Объект VariaticaProfile или None в случае ошибки
        """
        try:
            # Загружаем модуль
            spec = importlib.util.spec_from_file_location("profile_module", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Ищем объект VariaticaProfile в модуле
            # Ищем все переменные, которые являются экземплярами VariaticaProfile
            profile = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, VariaticaProfile):
                    profile = attr
                    break
            
            if not profile:
                # Если не нашли экземпляр, ищем переменные с именем profile
                for attr_name in dir(module):
                    if "profile" in attr_name.lower() or "SP_" in attr_name or "SA_" in attr_name or "IA_" in attr_name or "IP_" in attr_name:
                        attr = getattr(module, attr_name)
                        if isinstance(attr, VariaticaProfile):
                            profile = attr
                            break
            
            return profile
            
        except Exception as e:
            print(f"Ошибка загрузки профиля из {filepath}: {e}")
            return None
    
    def load_all_profiles(self):
        """Загружает все профили из директории profiles"""
        try:
            # Создаём директорию, если её нет
            os.makedirs(self.profiles_dir, exist_ok=True)
            
            # Ищем все .py файлы в директории
            pattern = os.path.join(self.profiles_dir, "*.py")
            profile_files = glob.glob(pattern)
            
            print(f"Найдено {len(profile_files)} файлов профилей в {self.profiles_dir}")
            
            for filepath in profile_files:
                try:
                    profile = self.load_profile_from_file(filepath)
                    if profile:
                        key = self._generate_profile_key(profile)
                        if key:
                            self.profiles[key] = profile
                            print(f"✅ Загружен профиль: {key}")
                        else:
                            print(f"⚠️ Не удалось сгенерировать ключ для профиля из {filepath}")
                    else:
                        print(f"❌ Не удалось загрузить профиль из {filepath}")
                except Exception as e:
                    print(f"❌ Ошибка обработки файла {filepath}: {e}")
            
            print(f"Всего загружено профилей: {len(self.profiles)}")
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке профилей: {e}")
    
    def _generate_profile_key(self, profile: VariaticaProfile) -> str:
        """
        Генерирует ключ профиля
        
        Формат: {type_code}_{level}_{dilts_code}
        
        Пример: SP_1_env, SA_3_beh и т.д.
        """
        try:
            # Для нового формата
            if hasattr(profile, 'type_code') and hasattr(profile, 'level'):
                type_code = profile.type_code
                level = profile.level
                
                # Определяем код Дилтса
                dilts_code = "env"  # По умолчанию
                
                # Пытаемся извлечь из ключа или других полей
                if hasattr(profile, 'key'):
                    # Ищем dilts код в ключе (последняя часть после _)
                    parts = profile.key.split('_')
                    if len(parts) >= 3:
                        dilts_code = parts[-1]
                
                return f"{type_code}_{level}_{dilts_code}"
            
            # Для старого формата (если есть profile_name)
            elif hasattr(profile, 'profile_name'):
                # Парсим название профиля
                name = profile.profile_name
                
                # Пример: "Инструментально-Достиженческий (Уровень 1: Защитный)"
                # Извлекаем тип и уровень
                if "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ" in name or "SA" in name:
                    type_code = "SA"
                elif "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ" in name or "IA" in name:
                    type_code = "IA"
                elif "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ" in name or "SP" in name:
                    type_code = "SP"
                elif "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ" in name or "IP" in name:
                    type_code = "IP"
                else:
                    type_code = "SA"  # По умолчанию
                
                # Извлекаем уровень
                level = 1  # По умолчанию
                if hasattr(profile, 'thinking_level'):
                    level = profile.thinking_level
                
                # Определяем Дилтса
                dilts_code = "env"  # По умолчанию
                if hasattr(profile, 'dilts_level'):
                    dilts = profile.dilts_level
                    dilts_map = {
                        "ENVIRONMENT": "env",
                        "BEHAVIOR": "beh",
                        "CAPABILITIES": "cap",
                        "VALUES": "val",
                        "IDENTITY": "ide"
                    }
                    dilts_code = dilts_map.get(dilts, "env")
                
                return f"{type_code}_{level}_{dilts_code}"
            
            # Если не удалось определить формат
            return None
            
        except Exception as e:
            print(f"Ошибка генерации ключа для профиля: {e}")
            return None
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу
        
        Args:
            profile_key: Ключ профиля (например, "SP_1_env")
            
        Returns:
            Объект VariaticaProfile или None
        """
        return self.profiles.get(profile_key)
    
    def get_all_profiles(self) -> list:
        """
        Возвращает список всех ключей профилей
        
        Returns:
            Список ключей профилей
        """
        return list(self.profiles.keys())
    
    def get_profiles_by_type(self, type_code: str) -> dict:
        """
        Получает все профили определённого типа
        
        Args:
            type_code: Код типа (SA, IA, SP, IP)
            
        Returns:
            Словарь профилей {key: profile} указанного типа
        """
        return {k: v for k, v in self.profiles.items() if k.startswith(type_code)}
    
    def reload_profiles(self):
        """Перезагружает все профили из файлов"""
        self.profiles.clear()
        self.load_all_profiles()
        print(f"✅ Профили перезагружены. Всего: {len(self.profiles)}")

# Создаём глобальный экземпляр загрузчика
loader = ProfileLoader()

# Функции для удобного импорта
def get_profile(profile_key: str) -> VariaticaProfile:
    """Получает профиль по ключу"""
    return loader.get_profile(profile_key)

def get_all_profiles() -> list:
    """Возвращает все ключи профилей"""
    return loader.get_all_profiles()

def profile_exists(profile_key: str) -> bool:
    """Проверяет существование профиля"""
    return loader.get_profile(profile_key) is not None
