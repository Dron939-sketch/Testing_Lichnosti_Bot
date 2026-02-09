"""
Загрузчик профилей из файловой системы
ИСПРАВЛЕННАЯ ВЕРСИЯ - поиск по типу и уровню, игнорируя суффикс Дилтса
"""

import os
import sys
import importlib.util
import traceback
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
        
        # Все возможные суффиксы (из файлов)
        self.all_suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
        
        # Таблица соответствия суффиксов Дилтса
        # Все суффиксы одного типа считаются равными
        self.dilts_equivalence_groups = {
            # Группа 1: Окружение/Ситуация
            'sit': ['env', 'sit', 'sur', 'situation', 'environment'],
            # Группа 2: Поведение/Контекст
            'con': ['beh', 'con', 'act', 'behavior', 'context'],
            # Группа 3: Способности/Опыт
            'exp': ['cap', 'exp', 'ski', 'abi', 'capabilities', 'experience'],
            # Группа 4: Ценности
            'val': ['val', 'mot', 'bel', 'values', 'motivation'],
            # Группа 5: Идентичность
            'ide': ['ide', 'id', 'sel', 'identity', 'self'],
            # Группа 6: Прочие суффиксы из файлов
            'def': ['def', 'default'],
            'int': ['int', 'internal'],
            'aut': ['aut', 'autonomy'],
            'tra': ['tra', 'transformation']
        }
        
        # Обратный словарь для быстрого поиска
        self.suffix_to_group = {}
        for group, suffixes in self.dilts_equivalence_groups.items():
            for suffix in suffixes:
                self.suffix_to_group[suffix.lower()] = group
        
        # Основная группа для каждого уровня Дилтса
        self.dilts_to_main_suffix = {
            'ENVIRONMENT': 'sit',
            'BEHAVIOR': 'con',
            'CAPABILITIES': 'exp',
            'VALUES': 'val',
            'IDENTITY': 'ide'
        }
        
        self.load_all_profiles()
    
    def find_profile_files(self) -> list:
        """
        Рекурсивно находит все файлы профилей .py
        """
        profile_files = []
        
        if not os.path.exists(self.profiles_dir):
            print(f"⚠️ Директория {self.profiles_dir} не существует!")
            return profile_files
        
        print(f"🔍 Поиск файлов в {self.profiles_dir}...")
        
        for root, dirs, files in os.walk(self.profiles_dir):
            dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
            
            py_files = [f for f in files if f.endswith('.py') and f != '__init__.py']
            if py_files:
                print(f"  📁 Папка: {os.path.basename(root)}, файлов: {len(py_files)}")
                
            for file in py_files:
                filepath = os.path.join(root, file)
                profile_files.append(filepath)
        
        print(f"✅ Всего найдено файлов: {len(profile_files)}")
        return profile_files
    
    def load_profile_from_file(self, filepath: str) -> VariaticaProfile:
        """
        Загружает профиль из файла Python
        """
        try:
            file_name = os.path.basename(filepath)
            print(f"\n  📖 Загрузка файла: {file_name}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"    📄 Размер файла: {len(content)} символов")
            
            # Исправляем импорты
            if 'from ..base import VariaticaProfile' in content:
                content = content.replace(
                    'from ..base import VariaticaProfile',
                    '# Импорт исправлен загрузчиком'
                )
            
            if 'from .base import VariaticaProfile' in content:
                content = content.replace(
                    'from .base import VariaticaProfile',
                    '# Импорт исправлен загрузчиком'
                )
            
            # Удаляем все импорты с VariaticaProfile
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                if 'VariaticaProfile' in line and ('import' in line or 'from' in line):
                    continue
                cleaned_lines.append(line)
            
            content = '\n'.join(cleaned_lines)
            
            # Создаем модуль
            module_name = f"profile_{file_name.replace('.py', '').replace('-', '_')}"
            spec = importlib.util.spec_from_loader(module_name, loader=None, origin=filepath)
            
            if spec is None:
                print(f"    ❌ Не удалось создать спецификацию для {file_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Добавляем необходимые переменные
            module.__dict__['VariaticaProfile'] = VariaticaProfile
            module.__dict__['__name__'] = module_name
            module.__dict__['__file__'] = filepath
            module.__dict__['sys'] = sys
            module.__dict__['os'] = os
            
            # Выполняем код
            exec(content, module.__dict__)
            
            # Ищем объект VariaticaProfile в модуле
            profile = None
            for var_name, var_value in module.__dict__.items():
                if not var_name.startswith('__') and isinstance(var_value, VariaticaProfile):
                    profile = var_value
                    print(f"    ✅ Найден профиль в переменной {var_name}")
                    break
            
            if not profile:
                print(f"    ❌ Не найден объект VariaticaProfile в {file_name}")
                return None
            
            # Устанавливаем ключ профиля из имени файла
            if not hasattr(profile, 'key') or not profile.key:
                key_from_file = self.extract_profile_key_from_filename(filepath)
                profile.key = key_from_file
                print(f"    🔧 Установлен ключ профиля: {key_from_file}")
            
            return profile
            
        except SyntaxError as e:
            print(f"    ❌ Синтаксическая ошибка в {os.path.basename(filepath)}: {e}")
            return None
        except Exception as e:
            print(f"    ❌ Ошибка загрузки профиля из {os.path.basename(filepath)}: {type(e).__name__}: {e}")
            return None
    
    def extract_profile_key_from_filename(self, filename: str) -> str:
        """
        Извлекает ключ профиля из имени файла
        """
        basename = os.path.basename(filename)
        
        if basename.endswith('.py'):
            basename = basename[:-3]
        
        # Преобразуем тип в верхний регистр
        parts = basename.split('_')
        if len(parts) >= 2:
            parts[0] = parts[0].upper()
            return '_'.join(parts)
        
        return basename.upper()
    
    def normalize_suffix(self, suffix: str) -> str:
        """
        Нормализует суффикс Дилтса по таблице соответствия
        Пример: 'env' → 'sit', 'cap' → 'exp', 'beh' → 'con'
        """
        suffix_lower = suffix.lower()
        
        # Если суффикс уже есть в таблице соответствия
        if suffix_lower in self.suffix_to_group:
            return self.suffix_to_group[suffix_lower]
        
        # Если суффикс уже является основной группой
        if suffix_lower in self.dilts_equivalence_groups:
            return suffix_lower
        
        # По умолчанию
        return 'def'
    
    def get_suffix_group(self, suffix: str) -> str:
        """
        Получает группу суффикса
        """
        suffix_lower = suffix.lower()
        return self.suffix_to_group.get(suffix_lower, 'def')
    
    def are_suffixes_equivalent(self, suffix1: str, suffix2: str) -> bool:
        """
        Проверяет, эквивалентны ли два суффикса Дилтса
        """
        group1 = self.get_suffix_group(suffix1)
        group2 = self.get_suffix_group(suffix2)
        return group1 == group2
    
    def load_all_profiles(self):
        """Загружает все профили из директории profiles"""
        try:
            print(f"\n📦 Начинаю загрузку профилей из {self.profiles_dir}...")
            
            os.makedirs(self.profiles_dir, exist_ok=True)
            profile_files = self.find_profile_files()
            
            if not profile_files:
                print("❌ Не найдено файлов профилей!")
                return
            
            print(f"\n🔄 Загрузка {len(profile_files)} профилей...")
            
            successful_loads = 0
            failed_loads = 0
            
            for filepath in profile_files:
                try:
                    profile = self.load_profile_from_file(filepath)
                    if profile:
                        # Извлекаем ключ из имени файла
                        key_from_file = self.extract_profile_key_from_filename(filepath)
                        
                        if key_from_file:
                            print(f"    🔑 Сохраняем профиль с ключом: {key_from_file}")
                            
                            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: 
                            # Сохраняем профиль ТОЛЬКО под реальным ключом из файла
                            self.profiles[key_from_file] = profile
                            
                            # Также сохраняем в нижнем регистре для удобства поиска
                            self.profiles[key_from_file.lower()] = profile
                            
                            # Сохраняем БАЗОВЫЙ ключ (тип_уровень) для поиска
                            parts = key_from_file.split('_')
                            if len(parts) >= 2:
                                # Создаем базовый ключ без суффикса
                                base_key = f"{parts[0]}_{parts[1]}"
                                
                                # Сохраняем базовый ключ (если его еще нет)
                                if base_key not in self.profiles:
                                    print(f"    📍 Создаю базовый ключ: '{base_key}'")
                                    self.profiles[base_key] = profile
                                else:
                                    print(f"    ℹ️ Базовый ключ '{base_key}' уже существует")
                            
                            successful_loads += 1
                        else:
                            print(f"    ⚠️ Не удалось извлечь ключ из имени файла")
                            failed_loads += 1
                    else:
                        print(f"    ❌ Не удалось загрузить профиль")
                        failed_loads += 1
                        
                except Exception as e:
                    print(f"    ❌ Ошибка обработки файла: {type(e).__name__}: {e}")
                    failed_loads += 1
            
            print(f"\n📊 Результаты загрузки:")
            print(f"  ✅ Успешно: {successful_loads}")
            print(f"  ❌ Ошибок: {failed_loads}")
            print(f"  🎯 Всего записей: {len(self.profiles)}")
            
            self.print_statistics()
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке профилей: {type(e).__name__}: {e}")
            traceback.print_exc()
    
    def print_statistics(self):
        """Выводим статистику по загруженным профилям"""
        # Собираем уникальные профили (исключая дубли и базовые ключи)
        unique_profiles = {}
        base_keys = set()
        
        for key, profile in self.profiles.items():
            if isinstance(key, str):
                parts = key.split('_')
                if len(parts) == 3:  # Полный ключ (тип_уровень_суффикс)
                    unique_profiles[key] = profile
                elif len(parts) == 2:  # Базовый ключ (тип_уровень)
                    base_keys.add(key)
        
        # Группируем по типам
        type_counts = {'SA': 0, 'IA': 0, 'SP': 0, 'IP': 0}
        for key in unique_profiles.keys():
            if key.startswith('SA_'):
                type_counts['SA'] += 1
            elif key.startswith('IA_'):
                type_counts['IA'] += 1
            elif key.startswith('SP_'):
                type_counts['SP'] += 1
            elif key.startswith('IP_'):
                type_counts['IP'] += 1
        
        print("\n" + "="*50)
        print("📊 СТАТИСТИКА ПРОФИЛЕЙ")
        print("="*50)
        
        total_unique = len(unique_profiles)
        print(f"  Уникальных профилей: {total_unique}")
        
        for type_code, count in type_counts.items():
            percentage = (count / total_unique * 100) if total_unique > 0 else 0
            print(f"  {type_code}: {count} профилей ({percentage:.1f}%)")
        
        print(f"\n  Базовых ключей (тип_уровень): {len(base_keys)}")
        
        # Выводим все уникальные профили
        if unique_profiles:
            print(f"\n🔑 Все загруженные профили:")
            sorted_keys = sorted(unique_profiles.keys())
            for key in sorted_keys:
                profile = unique_profiles[key]
                if hasattr(profile, 'title'):
                    title = profile.title[:30] + "..." if len(profile.title) > 30 else profile.title
                    print(f"  - {key:15} → {title}")
                else:
                    print(f"  - {key:15} → БЕЗ ЗАГОЛОВКА")
        
        print("="*50)
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу - ИЩЕТ ПО ТИПУ И УРОВНЮ
        Игнорирует суффикс Дилтса, ищет любой профиль того же типа и уровня
        """
        if not profile_key or not isinstance(profile_key, str):
            return None
        
        profile_key = profile_key.strip()
        original_key = profile_key  # Сохраняем оригинальный ключ для логов
        
        print(f"\n🔍 ЗАГРУЗЧИК: поиск профиля '{profile_key}'")
        
        # 1. Пробуем найти как есть
        if profile_key in self.profiles:
            profile = self.profiles[profile_key]
            print(f"   ✅ Найден напрямую: {profile_key}")
            return profile
        
        # 2. Пробуем нижний регистр
        lower_key = profile_key.lower()
        if lower_key in self.profiles:
            profile = self.profiles[lower_key]
            print(f"   ✅ Найден по нижнему регистру: {lower_key}")
            return profile
        
        # 3. УМНЫЙ ПОИСК: Ищем по типу и уровню, игнорируя суффикс
        profile = self._smart_profile_search(profile_key)
        if profile:
            return profile
        
        print(f"❌ Профиль не найден: '{original_key}'")
        return None
    
    def _smart_profile_search(self, profile_key: str) -> VariaticaProfile:
        """
        УМНЫЙ ПОИСК: Находит профиль по ТИПУ и УРОВНЮ
        Игнорирует суффикс Дилтса
        """
        # Очищаем и анализируем ключ
        clean_key = profile_key.lower().replace('-', '_')
        parts = clean_key.split('_')
        
        if len(parts) < 2:
            print(f"   ❌ Неверный формат ключа: {profile_key}")
            return None
        
        # Извлекаем тип и уровень
        type_part = parts[0]  # sa, sp, ia, ip
        level_part = parts[1]  # 1, 2, 3...
        
        # Нормализуем тип (в верхний регистр)
        type_part = type_part.upper()
        
        print(f"   🔍 УМНЫЙ ПОИСК: ищем профиль типа {type_part}, уровень {level_part}")
        
        # Шаг 1: Ищем БАЗОВЫЙ ключ (тип_уровень)
        base_key = f"{type_part}_{level_part}"
        print(f"   🤔 Ищу базовый ключ: '{base_key}'")
        
        if base_key in self.profiles:
            profile = self.profiles[base_key]
            actual_key = getattr(profile, 'key', 'unknown')
            print(f"   ✅ Найден по базовому ключу: {base_key} → {actual_key}")
            return profile
        
        # Шаг 2: Ищем ЛЮБОЙ профиль этого типа и уровня (с любым суффиксом)
        print(f"   🔍 Ищу любой профиль {type_part}_{level_part}_*")
        
        # Создаем паттерн для поиска
        pattern = f"{type_part.lower()}_{level_part}_"
        
        for key in self.profiles.keys():
            if not isinstance(key, str):
                continue
            
            key_lower = key.lower()
            
            # Ищем ключи, которые начинаются с pattern
            if key_lower.startswith(pattern):
                # Проверяем, что это не базовый ключ (уже искали выше)
                parts_key = key_lower.split('_')
                if len(parts_key) == 3:  # Это полный ключ с суффиксом
                    profile = self.profiles[key]
                    actual_key = getattr(profile, 'key', 'unknown')
                    print(f"   ✅ Найден профиль: {key} → {actual_key}")
                    return profile
        
        # Шаг 3: Если не нашли, пробуем ближайшие уровни
        print(f"   🔍 {type_part}_{level_part} не найден, ищу ближайшие уровни...")
        
        try:
            target_level = int(level_part)
            
            # Порядок поиска: тот же уровень → +1 → -1 → +2 → -2
            search_levels = []
            for diff in [0, 1, -1, 2, -2, 3, -3, 4, -4]:
                level = target_level + diff
                if 1 <= level <= 9 and level not in search_levels:
                    search_levels.append(level)
            
            for search_level in search_levels:
                # Пробуем базовый ключ
                test_base_key = f"{type_part}_{search_level}"
                if test_base_key in self.profiles:
                    profile = self.profiles[test_base_key]
                    actual_key = getattr(profile, 'key', 'unknown')
                    print(f"   🔄 Найден ближайший: {test_base_key} (уровень {search_level}) → {actual_key}")
                    return profile
                
                # Пробуем с любым суффиксом
                pattern_level = f"{type_part.lower()}_{search_level}_"
                for key in self.profiles.keys():
                    if isinstance(key, str) and key.lower().startswith(pattern_level):
                        parts_key = key.lower().split('_')
                        if len(parts_key) == 3:
                            profile = self.profiles[key]
                            actual_key = getattr(profile, 'key', 'unknown')
                            print(f"   🔄 Найден ближайший с суффиксом: {key} (уровень {search_level}) → {actual_key}")
                            return profile
        except ValueError:
            pass
        
        print(f"   ❌ Профиль для {type_part}_{level_part} не найден")
        return None
    
    def get_profile_by_type_level(self, type_code: str, level: int, dilts_suffix: str = None) -> VariaticaProfile:
        """
        Получает профиль по типу и уровню
        dilts_suffix используется только для логирования, не для поиска
        """
        type_upper = type_code.upper()
        
        print(f"\n🎯 ПОИСК ПРОФИЛЯ ПО ТИПУ И УРОВНЮ:")
        print(f"   Тип: {type_upper}, Уровень: {level}, Суффикс Дилтса: {dilts_suffix or 'не указан'}")
        
        # 1. Ищем базовый ключ
        base_key = f"{type_upper}_{level}"
        profile = self.get_profile(base_key)
        
        if profile:
            return profile
        
        # 2. Если не нашли, используем умный поиск
        search_key = f"{type_upper}_{level}_{dilts_suffix}" if dilts_suffix else base_key
        return self._smart_profile_search(search_key)
    
    def get_all_profiles(self) -> list:
        """
        Возвращает список всех уникальных ключей профилей
        """
        unique_keys = set()
        for key in self.profiles.keys():
            if isinstance(key, str) and not key.islower() and '_' in key:
                parts = key.split('_')
                if len(parts) == 3:  # Полные ключи (тип_уровень_суффикс)
                    unique_keys.add(key)
        
        return sorted(list(unique_keys))
    
    def get_all_base_keys(self) -> list:
        """
        Возвращает список базовых ключей (тип_уровень)
        """
        base_keys = set()
        for key in self.profiles.keys():
            if isinstance(key, str):
                parts = key.split('_')
                if len(parts) == 2 and parts[1].isdigit():
                    base_keys.add(key)
        
        return sorted(list(base_keys))
    
    def check_all_profiles_loaded(self) -> bool:
        """
        Проверяет, загружены ли все 36 профилей
        """
        # Проверяем только базовые комбинации (4 типа × 9 уровней = 36)
        expected_types = ['SA', 'SP', 'IA', 'IP']
        expected_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        
        missing_profiles = []
        
        for type_code in expected_types:
            for level in expected_levels:
                base_key = f"{type_code}_{level}"
                
                # Проверяем базовый ключ
                if base_key not in self.profiles:
                    # Проверяем, есть ли хотя бы один профиль этого типа и уровня
                    found = False
                    for key in self.profiles.keys():
                        if isinstance(key, str) and key.startswith(f"{type_code}_{level}_"):
                            found = True
                            break
                    
                    if not found:
                        missing_profiles.append(base_key)
        
        if missing_profiles:
            print(f"\n⚠️  Отсутствуют профили ({len(missing_profiles)}):")
            for profile in missing_profiles[:10]:
                print(f"   ❌ {profile}")
            if len(missing_profiles) > 10:
                print(f"   ... и ещё {len(missing_profiles) - 10} профилей")
            
            return False
        
        print(f"\n✅ Все 36 профилей загружены!")
        return True

# Создаём глобальный экземпляр загрузчика
loader = ProfileLoader()

# Функции для удобного импорта
def get_profile(profile_key: str) -> VariaticaProfile:
    """Получает профиль по ключу"""
    return loader.get_profile(profile_key)

def get_profile_by_type_level(type_code: str, level: int, dilts_suffix: str = None) -> VariaticaProfile:
    """Получает профиль по типу и уровню"""
    return loader.get_profile_by_type_level(type_code, level, dilts_suffix)

def get_all_profiles() -> list:
    """Возвращает все уникальные ключи профилей"""
    return loader.get_all_profiles()

def get_all_base_keys() -> list:
    """Возвращает все базовые ключи (тип_уровень)"""
    return loader.get_all_base_keys()

def profile_exists(profile_key: str) -> bool:
    """Проверяет существование профиля"""
    return loader.get_profile(profile_key) is not None

def check_all_profiles() -> bool:
    """Проверяет наличие всех 36 профилей"""
    return loader.check_all_profiles_loaded()

# Вспомогательная функция для отладки
def debug_profile_loading():
    """Функция для отладки загрузки профилей"""
    print("\n" + "="*60)
    print("🐛 ОТЛАДКА ЗАГРУЗЧИКА ПРОФИЛЕЙ")
    print("="*60)
    
    all_profiles = get_all_profiles()
    print(f"📊 Всего уникальных профилей: {len(all_profiles)}")
    
    if all_profiles:
        types = {}
        for key in all_profiles:
            type_code = key.split('_')[0]
            if type_code not in types:
                types[type_code] = []
            types[type_code].append(key)
        
        for type_code in sorted(types.keys()):
            profiles = types[type_code]
            print(f"\n{type_code} профилей ({len(profiles)}):")
            for i, key in enumerate(sorted(profiles), 1):
                print(f"  {i:2d}. {key}")
    
    # Тестируем поиск
    print("\n🔍 ТЕСТИРУЕМ ПОИСК ПРОФИЛЕЙ:")
    
    test_cases = [
        ("sa_3_con", "Любой SA профиль уровня 3"),
        ("SA_3_con", "Любой SA профиль уровня 3"),
        ("sp_3_aut", "Любой SP профиль уровня 3"),
        ("sp_3_val", "Любой SP профиль уровня 3"),
        ("ip_4_exp", "Любой IP профиль уровня 4"),
        ("ia_2_sit", "Любой IA профиль уровня 2"),
        ("SA_3", "Базовый ключ SA_3"),
        ("sp_4", "Базовый ключ SP_4"),
    ]
    
    for search_key, description in test_cases:
        profile = get_profile(search_key)
        if profile:
            actual_key = getattr(profile, 'key', 'unknown')
            title = getattr(profile, 'title', 'Без названия')[:30]
            print(f"  ✅ {search_key:20} → {actual_key}: {title}...")
        else:
            print(f"  ❌ {search_key:20} → НЕ НАЙДЕН")
    
    # Проверяем поиск по типу и уровню
    print("\n🔍 ТЕСТИРУЕМ ПОИСК ПО ТИПУ И УРОВНЮ:")
    
    test_type_level = [
        ("sa", 3, "con"),
        ("sp", 3, "val"),
        ("ip", 4, "exp"),
        ("ia", 2, "sit"),
    ]
    
    for type_code, level, suffix in test_type_level:
        profile = get_profile_by_type_level(type_code, level, suffix)
        if profile:
            actual_key = getattr(profile, 'key', 'unknown')
            print(f"  ✅ {type_code}_{level}_{suffix} → {actual_key}")
        else:
            print(f"  ❌ {type_code}_{level}_{suffix} → НЕ НАЙДЕН")
    
    print("="*60)

if __name__ == "__main__":
    debug_profile_loading()
