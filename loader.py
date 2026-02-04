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
    
    def find_profile_files(self) -> list:
        """
        Рекурсивно находит все файлы профилей .py
        
        Returns:
            Список путей к файлам профилей
        """
        profile_files = []
        
        # Рекурсивно ищем все .py файлы в profiles_dir и поддиректориях
        for root, dirs, files in os.walk(self.profiles_dir):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    filepath = os.path.join(root, file)
                    profile_files.append(filepath)
        
        return profile_files
    
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
                    if "profile" in attr_name.lower() or attr_name.startswith(('SP_', 'SA_', 'IA_', 'IP_')):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, VariaticaProfile):
                            profile = attr
                            break
            
            return profile
            
        except Exception as e:
            print(f"Ошибка загрузки профиля из {filepath}: {e}")
            return None
    
    def extract_profile_key_from_filename(self, filename: str) -> str:
        """
        Извлекает ключ профиля из имени файла
        
        Примеры:
            sp_1_def.py → SP_1_def
            SA/SA_1_def.py → SA_1_def
            profiles/SA/sa_1_def.py → SA_1_def
        """
        # Извлекаем только имя файла без пути
        basename = os.path.basename(filename)
        
        # Удаляем расширение .py
        if basename.endswith('.py'):
            basename = basename[:-3]
        
        # Преобразуем в верхний регистр для типа (SA, SP, IA, IP)
        parts = basename.split('_')
        if len(parts) >= 2:
            # Преобразуем первую часть (тип) в верхний регистр
            parts[0] = parts[0].upper()
            # Оставляем остальные части как есть
            return '_'.join(parts)
        
        return basename
    
    def load_all_profiles(self):
        """Загружает все профили из директории profiles и поддиректорий"""
        try:
            # Создаём директорию, если её нет
            os.makedirs(self.profiles_dir, exist_ok=True)
            
            # Рекурсивно находим все файлы профилей
            profile_files = self.find_profile_files()
            
            print(f"Найдено {len(profile_files)} файлов профилей в {self.profiles_dir} и поддиректориях")
            
            for filepath in profile_files:
                try:
                    profile = self.load_profile_from_file(filepath)
                    if profile:
                        # Сначала пытаемся сгенерировать ключ из данных профиля
                        key_from_profile = self._generate_profile_key(profile)
                        
                        # Если не получилось, извлекаем из имени файла
                        if not key_from_profile:
                            key_from_profile = self.extract_profile_key_from_filename(filepath)
                        
                        key = key_from_profile
                        
                        if key:
                            self.profiles[key] = profile
                            print(f"✅ Загружен профиль: {key} из {filepath}")
                        else:
                            print(f"⚠️ Не удалось сгенерировать ключ для профиля из {filepath}")
                    else:
                        print(f"❌ Не удалось загрузить профиль из {filepath}")
                except Exception as e:
                    print(f"❌ Ошибка обработки файла {filepath}: {e}")
            
            print(f"Всего загружено профилей: {len(self.profiles)}")
            
            # Выводим статистику по типам
            self.print_statistics()
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке профилей: {e}")
    
    def print_statistics(self):
        """Выводит статистику по загруженным профилям"""
        type_counts = {'SA': 0, 'IA': 0, 'SP': 0, 'IP': 0}
        
        for key in self.profiles.keys():
            if key.startswith('SA_'):
                type_counts['SA'] += 1
            elif key.startswith('IA_'):
                type_counts['IA'] += 1
            elif key.startswith('SP_'):
                type_counts['SP'] += 1
            elif key.startswith('IP_'):
                type_counts['IP'] += 1
        
        print("\n=== СТАТИСТИКА ПРОФИЛЕЙ ===")
        for type_code, count in type_counts.items():
            print(f"{type_code}: {count} профилей")
        print(f"Всего: {sum(type_counts.values())} профилей")
    
    def _generate_profile_key(self, profile: VariaticaProfile) -> str:
        """
        Генерирует ключ профиля
        
        Формат: {type_code}_{level}_{suffix}
        
        Пример: SP_1_def, SA_3_sit и т.д.
        """
        try:
            # Для нового формата
            if hasattr(profile, 'type_code') and hasattr(profile, 'level'):
                type_code = profile.type_code
                level = profile.level
                
                # Извлекаем суффикс из ключа или имени файла
                suffix = "def"  # По умолчанию
                
                if hasattr(profile, 'key'):
                    # Пример: SP_1_def → def
                    parts = profile.key.split('_')
                    if len(parts) >= 3:
                        suffix = parts[-1]
                    elif len(parts) == 2:
                        suffix = parts[-1]
                
                return f"{type_code}_{level}_{suffix}"
            
            # Для старого формата (если есть profile_name)
            elif hasattr(profile, 'profile_name'):
                # Парсим название профиля
                name = profile.profile_name
                
                # Определяем тип
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
                
                # Суффикс по умолчанию
                suffix = "def"
                
                return f"{type_code}_{level}_{suffix}"
            
            # Если не удалось определить формат
            return None
            
        except Exception as e:
            print(f"Ошибка генерации ключа для профиля: {e}")
            return None
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу
        
        Args:
            profile_key: Ключ профиля (например, "SP_1_def")
            
        Returns:
            Объект VariaticaProfile или None
        """
        # Пробуем разные варианты написания ключа
        variations = [
            profile_key,  # Как есть
            profile_key.upper(),  # В верхнем регистре
            profile_key.lower(),  # В нижнем регистре
        ]
        
        for var in variations:
            if var in self.profiles:
                return self.profiles[var]
        
        return None
    
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
        return {k: v for k, v in self.profiles.items() if k.startswith(type_code.upper())}
    
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
