"""
Загрузчик профилей из файловой системы - улучшенная версия
"""

import os
import sys
import importlib.util
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
        self.aliases = {}   # Словарь алиасов для быстрого поиска
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
            
            # Ищем файлы профилей (формат: тип_уровень_суффикс.py)
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    # Проверяем формат имени файла
                    if self._is_profile_filename(file):
                        filepath = os.path.join(root, file)
                        profile_files.append(filepath)
                        print(f"  ✅ Найден: {file}")
                    else:
                        print(f"  ⚠️  Пропущен (неверный формат): {file}")
        
        print(f"✅ Всего найдено файлов: {len(profile_files)}")
        return profile_files
    
    def _is_profile_filename(self, filename: str) -> bool:
        """Проверяет, является ли имя файла корректным именем профиля"""
        if not filename.endswith('.py'):
            return False
        
        name = filename[:-3]  # Убираем .py
        parts = name.split('_')
        
        # Допустимые форматы: sa_1_def, ia_9_ide, sp_1_def, ip_4_exp
        if len(parts) >= 2:
            type_part = parts[0].lower()
            return type_part in ['sa', 'ia', 'sp', 'ip']
        
        return False
    
    def load_profile_from_file(self, filepath: str) -> VariaticaProfile:
        """
        Загружает профиль из файла Python
        
        Args:
            filepath: Путь к файлу профиля
            
        Returns:
            Объект VariaticaProfile или None в случае ошибки
        """
        try:
            file_name = os.path.basename(filepath)
            print(f"\n  📖 Загрузка файла: {file_name}")
            
            # Читаем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Исправляем импорты
            content = self._fix_imports(content, file_name)
            
            # Создаем уникальное имя модуля
            module_name = f"profile_{file_name.replace('.py', '').replace('-', '_')}"
            
            # Создаем спецификацию модуля
            spec = importlib.util.spec_from_loader(
                module_name, 
                loader=None,
                origin=filepath
            )
            
            if spec is None:
                print(f"    ❌ Не удалось создать спецификацию для {file_name}")
                return None
            
            # Создаем модуль
            module = importlib.util.module_from_spec(spec)
            
            # Добавляем необходимые переменные в глобальное пространство
            module_globals = {
                'VariaticaProfile': VariaticaProfile,
                '__name__': module_name,
                '__file__': filepath,
                'sys': sys,
                'os': os,
                'print': print  # Добавляем print для отладки внутри профилей
            }
            
            # Выполняем код модуля
            print(f"    ⚙️ Выполняем код модуля...")
            exec(content, module_globals)
            
            # Ищем объект VariaticaProfile в модуле
            profile = self._find_profile_in_module(module_globals, file_name)
            
            if profile:
                # Добавляем метаинформацию о файле
                profile._source_file = filepath
                profile._source_filename = file_name
                
                # Устанавливаем корректный ключ, если его нет
                if not hasattr(profile, 'key') or not profile.key:
                    profile.key = file_name[:-3]  # Без .py
                    print(f"    🔧 Установлен ключ профиля: {profile.key}")
                
                print(f"    ✅ Успешно загружен: {profile.key}")
                return profile
            else:
                print(f"    ❌ Не найден объект VariaticaProfile в {file_name}")
                return None
            
        except SyntaxError as e:
            print(f"    ❌ Синтаксическая ошибка в {os.path.basename(filepath)}: {e}")
            return None
        except Exception as e:
            print(f"    ❌ Ошибка загрузки профиля из {os.path.basename(filepath)}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fix_imports(self, content: str, filename: str) -> str:
        """Исправляет импорты в содержимом файла"""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Удаляем все импорты, связанные с VariaticaProfile
            if 'VariaticaProfile' in line and ('import' in line or 'from' in line):
                print(f"    🗑 Удален импорт: {line.strip()}")
                continue
            
            # Исправляем относительные импорты
            if 'from ..' in line and 'VariaticaProfile' in line:
                print(f"    🔧 Исправлен относительный импорт в {filename}")
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _find_profile_in_module(self, module_globals: dict, filename: str):
        """Ищет объект VariaticaProfile в глобальных переменных модуля"""
        profiles_found = []
        
        for var_name, var_value in module_globals.items():
            if not var_name.startswith('__') and var_name not in ['sys', 'os', 'VariaticaProfile', 'print']:
                if isinstance(var_value, VariaticaProfile):
                    profiles_found.append((var_name, var_value))
        
        if len(profiles_found) == 1:
            var_name, profile = profiles_found[0]
            print(f"    ✅ Найден профиль в переменной '{var_name}'")
            return profile
        elif len(profiles_found) > 1:
            print(f"    ⚠️ Найдено {len(profiles_found)} профилей, берём первый")
            return profiles_found[0][1]
        
        # Если не нашли по типу, ищем в значениях объектов
        print(f"    🔍 Углубленный поиск профиля...")
        for var_name, var_value in module_globals.items():
            if isinstance(var_value, dict):
                for key, val in var_value.items():
                    if isinstance(val, VariaticaProfile):
                        print(f"    ✅ Найден профиль в словаре {var_name}[{key}]")
                        return val
        
        return None
    
    def extract_profile_key(self, filepath: str) -> str:
        """
        Извлекает ключ профиля из пути к файлу
        
        Примеры:
            profiles/ia/ia_1_def.py → IA_1_def
            profiles/sa/sa_4_exp.py → SA_4_exp
            profiles/sp/sp_1_def.py → SP_1_def
            profiles/ip/ip_9_ide.py → IP_9_ide
        """
        # Получаем относительный путь от profiles_dir
        rel_path = os.path.relpath(filepath, self.profiles_dir)
        
        # Преобразуем путь в ключ
        key = rel_path.replace('/', '_').replace('\\', '_').replace('.py', '')
        
        # Нормализуем ключ (верхний регистр для типа)
        parts = key.split('_')
        if len(parts) >= 2:
            parts[0] = parts[0].upper()
            return '_'.join(parts)
        
        return key.upper()
    
    def create_search_aliases(self, key: str) -> list:
        """
        Создает все возможные варианты ключа для поиска
        
        Args:
            key: Основной ключ (например: "IA_4_exp")
            
        Returns:
            Список всех возможных вариантов для поиска
        """
        aliases = []
        
        # Оригинальный ключ
        aliases.append(key)
        
        # Все в нижнем регистре
        aliases.append(key.lower())
        
        # Все в верхнем регистре
        aliases.append(key.upper())
        
        # Без суффикса (только тип_уровень)
        parts = key.split('_')
        if len(parts) >= 2:
            # Тип_уровень
            type_level = f"{parts[0]}_{parts[1]}"
            aliases.append(type_level)
            aliases.append(type_level.lower())
            aliases.append(type_level.upper())
            
            # Только уровень
            aliases.append(parts[1])  # Только номер уровня
            aliases.append(f"level_{parts[1]}")  # level_4
        
        # Для IP типа добавляем варианты с дефисом
        if key.startswith('IP_'):
            ip_with_dash = key.replace('IP_', 'IP-АДРЕС_')
            aliases.append(ip_with_dash)
            aliases.append(ip_with_dash.lower())
            
            # Также вариант без типа, только номер
            if len(parts) >= 2:
                aliases.append(f"IP{parts[1]}")  # IP4
                aliases.append(f"ip{parts[1]}")  # ip4
        
        # Убираем дубликаты и возвращаем
        return list(dict.fromkeys(aliases))
    
    def load_all_profiles(self):
        """Загружает все профили из директории profiles и поддиректорий"""
        try:
            print(f"\n📦 Начинаю загрузку профилей из {self.profiles_dir}...")
            
            # Создаём директорию, если её нет
            os.makedirs(self.profiles_dir, exist_ok=True)
            
            # Находим все файлы профилей
            profile_files = self.find_profile_files()
            
            if not profile_files:
                print("❌ Не найдено файлов профилей!")
                print("   Ожидаемые файлы: ia_1_def.py, sa_4_exp.py, sp_1_def.py, ip_9_ide.py и т.д.")
                print("   В папках: ia/, sa/, sp/, ip/")
                return
            
            print(f"\n🔄 Загрузка {len(profile_files)} профилей...")
            
            successful_loads = 0
            failed_loads = 0
            
            for filepath in profile_files:
                try:
                    profile = self.load_profile_from_file(filepath)
                    if profile:
                        # Получаем ключ из имени файла
                        main_key = self.extract_profile_key(filepath)
                        
                        # Сохраняем профиль под основным ключом
                        self.profiles[main_key] = profile
                        print(f"    💾 Сохранён как: {main_key}")
                        
                        # Создаем все алиасы для поиска
                        aliases = self.create_search_aliases(main_key)
                        for alias in aliases:
                            if alias != main_key:  # Основной ключ уже сохранен
                                self.aliases[alias] = main_key
                        
                        successful_loads += 1
                    else:
                        print(f"    ❌ Не удалось загрузить профиль из {os.path.basename(filepath)}")
                        failed_loads += 1
                        
                except Exception as e:
                    print(f"    ❌ Ошибка обработки файла {os.path.basename(filepath)}: {type(e).__name__}: {e}")
                    failed_loads += 1
            
            print(f"\n📊 Результаты загрузки:")
            print(f"  ✅ Успешно: {successful_loads}")
            print(f"  ❌ Ошибок: {failed_loads}")
            print(f"  🎯 Всего ключей: {len(self.profiles)}")
            print(f"  🔍 Алиасов для поиска: {len(self.aliases)}")
            
            # Выводим статистику
            self.print_statistics()
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке профилей: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def print_statistics(self):
        """Выводит статистику по загруженным профилям"""
        type_counts = {'SA': 0, 'IA': 0, 'SP': 0, 'IP': 0}
        levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        for key in self.profiles.keys():
            parts = key.split('_')
            if len(parts) >= 2:
                type_code = parts[0]
                level = int(parts[1]) if parts[1].isdigit() else 0
                
                if type_code in type_counts:
                    type_counts[type_code] += 1
                
                if level in levels:
                    levels[level] += 1
        
        print("\n" + "="*50)
        print("📊 СТАТИСТИКА ПРОФИЛЕЙ")
        print("="*50)
        
        # Статистика по типам
        print("\n📈 По типам:")
        for type_code in ['SA', 'IA', 'SP', 'IP']:
            count = type_counts[type_code]
            print(f"  {type_code}: {count} профилей")
        
        # Статистика по уровням
        print("\n📊 По уровням:")
        for level in sorted(levels.keys()):
            count = levels[level]
            if count > 0:
                print(f"  Уровень {level}: {count} профилей")
        
        # Список всех профилей
        print(f"\n📋 Все загруженные профили ({len(self.profiles)}):")
        sorted_keys = sorted(self.profiles.keys())
        for key in sorted_keys:
            profile = self.profiles[key]
            if hasattr(profile, 'title'):
                title = profile.title[:50] + "..." if len(profile.title) > 50 else profile.title
                print(f"  • {key:15} → {title}")
            else:
                print(f"  • {key:15} → (без названия)")
        
        print("="*50)
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу (с расширенным поиском)
        
        Args:
            profile_key: Ключ профиля или любой из алиасов
            
        Returns:
            Объект VariaticaProfile или None
        """
        if not profile_key or not isinstance(profile_key, str):
            print(f"❌ Неверный ключ профиля: {profile_key}")
            return None
        
        # Очищаем ключ
        profile_key = profile_key.strip()
        
        print(f"\n🔍 Поиск профиля: '{profile_key}'")
        
        # 1. Прямой поиск по основным ключам
        if profile_key in self.profiles:
            print(f"   ✅ Найден напрямую: {profile_key}")
            return self.profiles[profile_key]
        
        # 2. Поиск через алиасы
        if profile_key in self.aliases:
            main_key = self.aliases[profile_key]
            print(f"   ✅ Найден через алиас '{profile_key}' → {main_key}")
            return self.profiles[main_key]
        
        # 3. Попробуем нормализовать ключ
        normalized = self.normalize_key(profile_key)
        if normalized and normalized in self.profiles:
            print(f"   ✅ Найден по нормализованному ключу: {normalized}")
            return self.profiles[normalized]
        
        # 4. Поиск по частичному совпадению
        print(f"   🔍 Поиск по частичному совпадению...")
        
        # Сначала по типу и уровню
        search_lower = profile_key.lower().replace('-', '_')
        
        # Пробуем разные варианты поиска
        search_patterns = [
            search_lower,  # Как есть
            search_lower.upper(),  # В верхнем регистре
            search_lower.replace('_', ''),  # Без подчеркиваний
        ]
        
        # Добавляем варианты для IP
        if search_lower.startswith('ip'):
            search_patterns.append(search_lower.replace('ip', 'ip-адрес'))
            search_patterns.append(search_lower.replace('ip_', 'ip-адрес_'))
        
        # Ищем во всех алиасах
        for pattern in search_patterns:
            for alias, main_key in self.aliases.items():
                if alias.lower() == pattern.lower():
                    print(f"   ✅ Найден через частичное совпадение: {alias} → {main_key}")
                    return self.profiles[main_key]
        
        # 5. Поиск по уровню (если введен только номер)
        if profile_key.isdigit():
            level = int(profile_key)
            print(f"   🔍 Поиск всех профилей уровня {level}...")
            
            # Ищем профили этого уровня
            found_profiles = []
            for key in self.profiles.keys():
                parts = key.split('_')
                if len(parts) >= 2 and parts[1] == str(level):
                    found_profiles.append(key)
            
            if found_profiles:
                print(f"   ⚠️ Найдено {len(found_profiles)} профилей уровня {level}")
                print(f"   👉 Используйте конкретный ключ, например: {found_profiles[0]}")
                return self.profiles[found_profiles[0]]
        
        # 6. Выводим подсказки
        print(f"\n❌ Профиль не найден: '{profile_key}'")
        self.show_search_suggestions(profile_key)
        
        return None
    
    def normalize_key(self, key: str) -> str:
        """Нормализует ключ профиля"""
        if not key:
            return key
        
        # Заменяем дефисы на подчеркивания
        key = key.replace('-', '_').replace(' ', '_')
        
        # Разбиваем на части
        parts = [p for p in key.split('_') if p]
        
        if len(parts) >= 2:
            # Первая часть - тип (в верхнем регистре)
            parts[0] = parts[0].upper()
            
            # Вторая часть - уровень (должна быть цифрой)
            if parts[1].isdigit():
                # Оставляем как есть
                pass
            
            return '_'.join(parts)
        
        return key.upper()
    
    def show_search_suggestions(self, search_key: str):
        """Показывает подсказки для поиска"""
        print(f"\n💡 Подсказки для поиска '{search_key}':")
        
        # Преобразуем поисковый запрос
        search_lower = search_key.lower()
        
        # Ищем похожие ключи
        suggestions = []
        
        for main_key in self.profiles.keys():
            main_lower = main_key.lower()
            
            # Проверяем разные варианты совпадения
            if search_lower in main_lower or main_lower in search_lower:
                suggestions.append(main_key)
            elif search_lower.replace('_', '') in main_lower.replace('_', ''):
                suggestions.append(main_key)
            elif search_lower.startswith('ip') and 'ip' in main_lower:
                suggestions.append(main_key)
        
        # Также проверяем алиасы
        for alias in self.aliases.keys():
            if search_lower in alias.lower():
                main_key = self.aliases[alias]
                if main_key not in suggestions:
                    suggestions.append(main_key)
        
        if suggestions:
            print(f"   Возможно, вы искали один из этих профилей:")
            for key in sorted(set(suggestions))[:10]:  # Показываем первые 10
                profile = self.profiles[key]
                title = ""
                if hasattr(profile, 'title'):
                    title = profile.title[:40] + "..." if len(profile.title) > 40 else profile.title
                
                print(f"   • {key:15} → {title}")
            
            if len(suggestions) > 10:
                print(f"   ... и ещё {len(suggestions) - 10} вариантов")
        else:
            print(f"   Доступные типы профилей: SA, IA, SP, IP")
            print(f"   Примеры ключей: SA_1_def, IA_4_exp, SP_1_def, IP_9_ide")
            print(f"   Всего доступно {len(self.profiles)} профилей")
    
    def get_all_profiles(self) -> list:
        """Возвращает список всех основных ключей профилей"""
        return sorted(list(self.profiles.keys()))
    
    def get_profiles_by_type(self, type_code: str) -> dict:
        """Получает все профили определённого типа"""
        normalized_type = type_code.upper()
        result = {}
        
        for key, profile in self.profiles.items():
            if key.startswith(normalized_type + '_'):
                result[key] = profile
        
        return result
    
    def get_profiles_by_level(self, level: int) -> dict:
        """Получает все профили определённого уровня"""
        result = {}
        
        for key, profile in self.profiles.items():
            parts = key.split('_')
            if len(parts) >= 2 and parts[1] == str(level):
                result[key] = profile
        
        return result
    
    def reload_profiles(self):
        """Перезагружает все профили из файлов"""
        print("\n🔄 Перезагрузка профилей...")
        self.profiles.clear()
        self.aliases.clear()
        self.load_all_profiles()
        print(f"✅ Профили перезагружены. Всего: {len(self.profiles)}")

# Создаём глобальный экземпляр загрузчика
loader = ProfileLoader()

# Функции для удобного импорта
def get_profile(profile_key: str) -> VariaticaProfile:
    """Получает профиль по ключу"""
    return loader.get_profile(profile_key)

def get_all_profiles() -> list:
    """Возвращает все уникальные ключи профилей"""
    return loader.get_all_profiles()

def get_profiles_by_type(type_code: str) -> dict:
    """Получает все профили определённого типа"""
    return loader.get_profiles_by_type(type_code)

def get_profiles_by_level(level: int) -> dict:
    """Получает все профили определённого уровня"""
    return loader.get_profiles_by_level(level)

def profile_exists(profile_key: str) -> bool:
    """Проверяет существование профиля"""
    return loader.get_profile(profile_key) is not None

# Функция для тестирования всех профилей
def test_all_profiles():
    """Тестирует загрузку всех профилей"""
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ ЗАГРУЗКИ ВСЕХ ПРОФИЛЕЙ")
    print("="*60)
    
    all_keys = get_all_profiles()
    print(f"📊 Всего профилей: {len(all_keys)}")
    
    if len(all_keys) != 36:
        print(f"⚠️ Ожидалось 36 профилей, найдено {len(all_keys)}")
    
    # Тестируем поиск по разным вариантам
    test_cases = [
        # Основные форматы
        ("SA_1_def", True),
        ("ia_4_exp", True),
        ("SP_1_def", True),
        ("IP_9_ide", True),
        
        # Без суффикса
        ("SA_1", True),
        ("ia_4", True),
        
        # Только уровень
        ("4", True),  # Должен найти любой профиль уровня 4
        
        # Неправильные, но близкие
        ("sa1def", True),  # Без подчеркиваний
        ("IP-АДРЕС_4", True),  # С дефисом
        
        # Несуществующие
        ("XX_1_def", False),
        ("SA_10_def", False),
    ]
    
    print("\n🔍 Тестируем поиск:")
    for search_key, should_exist in test_cases:
        profile = get_profile(search_key)
        found = profile is not None
        status = "✅" if found == should_exist else "❌"
        
        if found:
            actual_key = getattr(profile, 'key', 'unknown')
            print(f"  {status} '{search_key:20}' → найдено ({actual_key})")
        else:
            print(f"  {status} '{search_key:20}' → не найдено (ожидалось: {'да' if should_exist else 'нет'})")
    
    print("="*60)

# При запуске напрямую, выполняем тестирование
if __name__ == "__main__":
    test_all_profiles()
