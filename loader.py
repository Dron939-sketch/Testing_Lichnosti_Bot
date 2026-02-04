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
        
        # Проверяем существование директории
        if not os.path.exists(self.profiles_dir):
            print(f"⚠️ Директория {self.profiles_dir} не существует!")
            return profile_files
        
        print(f"🔍 Поиск файлов в {self.profiles_dir}...")
        
        # Рекурсивно ищем все .py файлы в profiles_dir и поддиректориях
        for root, dirs, files in os.walk(self.profiles_dir):
            # Пропускаем __pycache__ и другие служебные директории
            dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
            
            py_files = [f for f in files if f.endswith('.py') and f != '__init__.py']
            if py_files:
                print(f"  📁 Папка: {os.path.basename(root)}, файлов: {len(py_files)}")
                
            for file in py_files:
                filepath = os.path.join(root, file)
                profile_files.append(filepath)
                print(f"    📄 Найден: {file}")
        
        print(f"✅ Всего найдено файлов: {len(profile_files)}")
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
            print(f"❌ Ошибка загрузки профиля из {filepath}: {e}")
            return None
    
    def extract_profile_key_from_filename(self, filename: str) -> str:
        """
        Извлекает ключ профиля из имени файла
        
        Примеры:
            sp_1_def.py → SP_1_def
            SA/SA_1_def.py → SA_1_def
            profiles/SA/sa_1_def.py → SA_1_def
            profiles/ip-адрес/ip_4_exp.py → IP_4_exp  # <-- Обрабатываем дефис в имени папки
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
    
    def normalize_profile_key(self, key: str) -> str:
        """
        Нормализует ключ профиля для поиска
        
        Примеры:
            IP_4_exp → IP_4_exp
            ip_4_exp → IP_4_exp
            IP-АДРЕС_4_exp → IP_4_exp
        """
        if not key:
            return key
        
        # Удаляем дефисы и нормализуем
        if '-' in key:
            key = key.replace('-', '_')
        
        parts = key.split('_')
        if len(parts) >= 2:
            # Преобразуем тип в верхний регистр
            parts[0] = parts[0].upper()
            
            # Удаляем "АДРЕС" из IP типа если есть
            if parts[0] == "IP" and len(parts) > 1 and parts[1].upper() == "АДРЕС":
                parts.pop(1)
            
            return '_'.join(parts)
        
        return key.upper()
    
    def load_all_profiles(self):
        """Загружает все профили из директории profiles и поддиректорий"""
        try:
            # Создаём директорию, если её нет
            os.makedirs(self.profiles_dir, exist_ok=True)
            
            # Рекурсивно находим все файлы профилей
            profile_files = self.find_profile_files()
            
            print(f"\n📦 Загрузка профилей из {len(profile_files)} файлов...")
            
            for filepath in profile_files:
                try:
                    profile = self.load_profile_from_file(filepath)
                    if profile:
                        # Сначала пытаемся сгенерировать ключ из данных профиля
                        key_from_profile = self._generate_profile_key(profile)
                        
                        # Если не получилось, извлекаем из имени файла
                        if not key_from_profile:
                            key_from_profile = self.extract_profile_key_from_filename(filepath)
                        
                        # Нормализуем ключ
                        normalized_key = self.normalize_profile_key(key_from_profile)
                        
                        if normalized_key:
                            # Также сохраняем ненормализованный ключ для поиска
                            self.profiles[normalized_key] = profile
                            
                            # Сохраняем версию в нижнем регистре для поиска
                            self.profiles[normalized_key.lower()] = profile
                            
                            # Сохраняем версию с дефисом для ip-адрес
                            if normalized_key.startswith("IP_"):
                                ip_with_dash = normalized_key.replace("IP_", "IP-АДРЕС_", 1)
                                self.profiles[ip_with_dash] = profile
                                self.profiles[ip_with_dash.lower()] = profile
                            
                            print(f"✅ Загружен профиль: {normalized_key} из {os.path.basename(filepath)}")
                        else:
                            print(f"⚠️ Не удалось сгенерировать ключ для профиля из {filepath}")
                    else:
                        print(f"❌ Не удалось загрузить профиль из {filepath}")
                except Exception as e:
                    print(f"❌ Ошибка обработки файла {filepath}: {e}")
            
            print(f"\n🎯 Всего загружено профилей: {len(set(self.profiles.keys()))}")
            
            # Выводим статистику по типам
            self.print_statistics()
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке профилей: {e}")
            import traceback
            traceback.print_exc()
    
    def print_statistics(self):
        """Выводит статистику по загруженным профилям"""
        type_counts = {'SA': 0, 'IA': 0, 'SP': 0, 'IP': 0}
        unique_keys = set()
        
        for key in self.profiles.keys():
            # Пропускаем ключи в нижнем регистре и с дефисами
            if key.islower() or '-' in key:
                continue
                
            unique_keys.add(key)
            
            if key.startswith('SA_'):
                type_counts['SA'] += 1
            elif key.startswith('IA_'):
                type_counts['IA'] += 1
            elif key.startswith('SP_'):
                type_counts['SP'] += 1
            elif key.startswith('IP_'):
                type_counts['IP'] += 1
        
        print("\n" + "="*40)
        print("📊 СТАТИСТИКА ПРОФИЛЕЙ")
        print("="*40)
        for type_code, count in type_counts.items():
            print(f"  {type_code}: {count} профилей")
        print(f"\n  Всего уникальных профилей: {len(unique_keys)}")
        print("="*40)
        
        # Выводим несколько примеров ключей
        print("\n🔑 Примеры ключей профилей:")
        for key in sorted(list(unique_keys))[:5]:
            print(f"  - {key}")
        if len(unique_keys) > 5:
            print(f"  ... и ещё {len(unique_keys) - 5} профилей")
    
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
            print(f"⚠️ Ошибка генерации ключа для профиля: {e}")
            return None
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу
        
        Args:
            profile_key: Ключ профиля (например, "SP_1_def", "ip_4_exp")
            
        Returns:
            Объект VariaticaProfile или None
        """
        if not profile_key:
            return None
        
        # 1. Пробуем как есть
        if profile_key in self.profiles:
            return self.profiles[profile_key]
        
        # 2. Пробуем нормализованный ключ
        normalized_key = self.normalize_profile_key(profile_key)
        if normalized_key in self.profiles:
            return self.profiles[normalized_key]
        
        # 3. Пробуем нижний регистр
        lower_key = profile_key.lower()
        if lower_key in self.profiles:
            return self.profiles[lower_key]
        
        # 4. Для IP типа пробуем разные варианты
        if profile_key.lower().startswith("ip"):
            variations = [
                profile_key,
                profile_key.upper(),
                profile_key.lower(),
                normalized_key,
                normalized_key.lower(),
                profile_key.replace("ip_", "ip-адрес_"),
                profile_key.replace("IP_", "IP-АДРЕС_"),
                profile_key.replace("ip-адрес_", "ip_"),
                profile_key.replace("IP-АДРЕС_", "IP_"),
            ]
            
            for var in variations:
                if var in self.profiles:
                    return self.profiles[var]
        
        # 5. Поиск по частичному совпадению (без учёта регистра)
        search_key = profile_key.upper().replace('-', '_')
        for key in self.profiles.keys():
            if key.upper() == search_key:
                return self.profiles[key]
        
        print(f"🔍 Профиль не найден: {profile_key}")
        print(f"   Доступные ключи начинающиеся с {profile_key.split('_')[0].upper()}:")
        for key in sorted(self.profiles.keys()):
            if key.upper().startswith(profile_key.split('_')[0].upper()):
                print(f"   - {key}")
        
        return None
    
    def get_all_profiles(self) -> list:
        """
        Возвращает список всех уникальных ключей профилей (только нормализованные)
        
        Returns:
            Список ключей профилей
        """
        unique_keys = set()
        for key in self.profiles.keys():
            # Берем только нормализованные ключи (в верхнем регистре, без дефисов)
            if not key.islower() and '-' not in key:
                unique_keys.add(key)
        
        return sorted(list(unique_keys))
    
    def get_profiles_by_type(self, type_code: str) -> dict:
        """
        Получает все профили определённого типа
        
        Args:
            type_code: Код типа (SA, IA, SP, IP)
            
        Returns:
            Словарь профилей {key: profile} указанного типа
        """
        normalized_type = type_code.upper().replace('-', '_')
        result = {}
        
        for key, profile in self.profiles.items():
            if key.startswith(normalized_type + '_'):
                result[key] = profile
        
        return result
    
    def reload_profiles(self):
        """Перезагружает все профили из файлов"""
        self.profiles.clear()
        self.load_all_profiles()
        print(f"🔄 Профили перезагружены. Всего: {len(self.get_all_profiles())}")

# Создаём глобальный экземпляр загрузчика
loader = ProfileLoader()

# Функции для удобного импорта
def get_profile(profile_key: str) -> VariaticaProfile:
    """Получает профиль по ключу"""
    return loader.get_profile(profile_key)

def get_all_profiles() -> list:
    """Возвращает все уникальные ключи профилей"""
    return loader.get_all_profiles()

def profile_exists(profile_key: str) -> bool:
    """Проверяет существование профиля"""
    return loader.get_profile(profile_key) is not None

def debug_loader():
    """Функция для отладки загрузчика"""
    print("\n" + "="*50)
    print("🐛 ОТЛАДКА LOADER")
    print("="*50)
    
    all_profiles = get_all_profiles()
    print(f"Всего профилей: {len(all_profiles)}")
    
    # Проверяем IP профили
    ip_profiles = [p for p in all_profiles if p.startswith('IP_')]
    print(f"\nIP профилей: {len(ip_profiles)}")
    for p in ip_profiles:
        print(f"  - {p}")
    
    # Пробуем найти конкретный профиль
    test_keys = ["ip_4_exp", "IP_4_exp", "IP-АДРЕС_4_exp", "ip-адрес_4_exp"]
    print(f"\n🔍 Тестируем поиск профиля ip_4_exp:")
    for key in test_keys:
        profile = get_profile(key)
        if profile:
            print(f"  ✅ Найден по ключу '{key}'")
        else:
            print(f"  ❌ Не найден по ключу '{key}'")
    
    print("="*50)

# При запуске loader.py напрямую, выполняем отладку
if __name__ == "__main__":
    debug_loader()
