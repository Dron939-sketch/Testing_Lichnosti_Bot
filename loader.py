"""
Загрузчик профилей из файловой системы
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
            file_name = os.path.basename(filepath)
            print(f"\n  📖 Загрузка файла: {file_name}")
            
            # Читаем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"    📄 Размер файла: {len(content)} символов")
            
            # Исправляем относительные импорты
            if 'from ..base import VariaticaProfile' in content:
                content = content.replace(
                    'from ..base import VariaticaProfile',
                    '# Импорт исправлен загрузчиком'
                )
                print(f"    🔧 Исправлен импорт 'from ..base import' в {file_name}")
            
            # Также исправляем другие возможные варианты
            if 'from .base import VariaticaProfile' in content:
                content = content.replace(
                    'from .base import VariaticaProfile',
                    '# Импорт исправлен загрузчиком'
                )
                print(f"    🔧 Исправлен импорт 'from .base import' в {file_name}")
            
            # Удаляем все импорты с VariaticaProfile
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                if 'VariaticaProfile' in line and ('import' in line or 'from' in line):
                    print(f"    🗑 Удален импорт: {line.strip()}")
                    continue
                cleaned_lines.append(line)
            
            content = '\n'.join(cleaned_lines)
            
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
            
            # КРИТИЧЕСКИ ВАЖНО: Добавляем VariaticaProfile в глобальное пространство
            module.__dict__['VariaticaProfile'] = VariaticaProfile
            module.__dict__['__name__'] = module_name
            module.__dict__['__file__'] = filepath
            
            # Также добавляем sys и os для совместимости
            module.__dict__['sys'] = sys
            module.__dict__['os'] = os
            
            # Выполняем код модуля
            print(f"    ⚙️ Выполняем код модуля...")
            exec(content, module.__dict__)
            
            # ОТЛАДОЧНЫЙ ВЫВОД: что есть в модуле?
            print(f"    🔍 Переменные в модуле после exec:")
            profile_vars = []
            for var_name, var_value in module.__dict__.items():
                if not var_name.startswith('__') and not var_name in ['sys', 'os', 'VariaticaProfile']:
                    var_type = type(var_value).__name__
                    print(f"      - {var_name}: {var_type}")
                    if isinstance(var_value, VariaticaProfile):
                        profile_vars.append((var_name, var_value))
            
            # Ищем объект VariaticaProfile в модуле
            profile = None
            
            if profile_vars:
                print(f"    ✅ Найдены {len(profile_vars)} объектов VariaticaProfile")
                for var_name, var_value in profile_vars:
                    print(f"      - {var_name}: {var_value}")
                
                # Берем первый найденный профиль
                profile = profile_vars[0][1]
                print(f"    🎯 Выбран профиль: {profile_vars[0][0]}")
                
                # Устанавливаем ключ профиля из имени файла, если его нет
                if not hasattr(profile, 'key') or not profile.key:
                    key_from_file = self.extract_profile_key_from_filename(filepath)
                    profile.key = key_from_file
                    print(f"    🔧 Установлен ключ профиля: {key_from_file}")
            
            # Если не нашли профиль в явных переменных, ищем в значениях
            if not profile:
                print(f"    🔍 Поиск профиля в значениях объектов...")
                for var_name, var_value in module.__dict__.items():
                    if isinstance(var_value, VariaticaProfile):
                        profile = var_value
                        print(f"    ✅ Найден профиль в переменной {var_name}")
                        break
            
            if not profile:
                print(f"    ❌ Не найден объект VariaticaProfile в {file_name}")
                # Посмотрим первые 20 строк файла для отладки
                print(f"    Первые 20 строк файла:")
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if i <= 20:
                            print(f"      {i:2}: {line.rstrip()}")
                        else:
                            break
            
            return profile
            
        except SyntaxError as e:
            print(f"    ❌ Синтаксическая ошибка в {os.path.basename(filepath)}: {e}")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"    ❌ Ошибка загрузки профиля из {os.path.basename(filepath)}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_profile_key_from_filename(self, filename: str) -> str:
        """
        Извлекает ключ профиля из имени файла
        
        Примеры:
            sp_1_def.py → SP_1_def
            SA/SA_1_def.py → SA_1_def
            profiles/SA/sa_1_def.py → SA_1_def
            profiles/ip-адрес/ip_4_exp.py → IP_4_exp
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
            print(f"\n📦 Начинаю загрузку профилей из {self.profiles_dir}...")
            
            # Создаём директорию, если её нет
            os.makedirs(self.profiles_dir, exist_ok=True)
            
            # Рекурсивно находим все файлы профилей
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
                        # Сначала пытаемся сгенерировать ключ из данных профиля
                        key_from_profile = self._generate_profile_key(profile)
                        
                        # Если не получилось, извлекаем из имени файла
                        if not key_from_profile:
                            key_from_profile = self.extract_profile_key_from_filename(filepath)
                        
                        # Нормализуем ключ
                        normalized_key = self.normalize_profile_key(key_from_profile)
                        
                        if normalized_key:
                            print(f"    🔑 Сохраняем профиль с ключом: {normalized_key}")
                            
                            # Сохраняем профиль с нормализованным ключом
                            self.profiles[normalized_key] = profile
                            
                            # Также сохраняем версию в нижнем регистре для поиска
                            self.profiles[normalized_key.lower()] = profile
                            
                            # Сохраняем версию с дефисом для ip-адрес
                            if normalized_key.startswith("IP_"):
                                ip_with_dash = normalized_key.replace("IP_", "IP-АДРЕС_", 1)
                                self.profiles[ip_with_dash] = profile
                                self.profiles[ip_with_dash.lower()] = profile
                            
                            successful_loads += 1
                        else:
                            print(f"    ⚠️ Не удалось сгенерировать ключ для профиля из {os.path.basename(filepath)}")
                            failed_loads += 1
                    else:
                        print(f"    ❌ Не удалось загрузить профиль из {os.path.basename(filepath)}")
                        failed_loads += 1
                        
                except Exception as e:
                    print(f"    ❌ Ошибка обработки файла {os.path.basename(filepath)}: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed_loads += 1
            
            print(f"\n📊 Результаты загрузки:")
            print(f"  ✅ Успешно: {successful_loads}")
            print(f"  ❌ Ошибок: {failed_loads}")
            print(f"  🎯 Всего в памяти: {len(self.profiles)} записей (включая альтернативные ключи)")
            
            # Выводим статистику по типам
            self.print_statistics()
            
        except Exception as e:
            print(f"❌ Критическая ошибка при загрузке профилей: {type(e).__name__}: {e}")
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
        
        total_unique = len(unique_keys)
        for type_code, count in type_counts.items():
            percentage = (count / total_unique * 100) if total_unique > 0 else 0
            print(f"  {type_code}: {count} профилей ({percentage:.1f}%)")
        
        print(f"\n  Всего уникальных профилей: {total_unique}")
        
        # Выводим все ключи
        if unique_keys:
            print(f"\n🔑 Все загруженные профили:")
            sorted_keys = sorted(list(unique_keys))
            for key in sorted_keys:
                profile = self.profiles[key]
                if hasattr(profile, 'title'):
                    title = profile.title[:40] + "..." if len(profile.title) > 40 else profile.title
                    print(f"  - {key:15} → {title}")
                else:
                    print(f"  - {key:15} → БЕЗ ЗАГОЛОВКА")
        
        print("="*40)
    
    def _generate_profile_key(self, profile: VariaticaProfile) -> str:
        """
        Генерирует ключ профиля
        
        Формат: {type_code}_{level}_{suffix}
        
        Пример: SP_1_def, SA_3_sit и т.д.
        """
        try:
            print(f"    🔧 Генерация ключа для профиля...")
            
            # Для нового формата
            if hasattr(profile, 'type_code') and hasattr(profile, 'level'):
                type_code = profile.type_code
                level = profile.level
                
                print(f"      type_code={type_code}, level={level}")
                
                # Извлекаем суффикс из ключа или имени файла
                suffix = "def"  # По умолчанию
                
                if hasattr(profile, 'key'):
                    print(f"      profile.key = {profile.key}")
                    # Пример: SP_1_def → def
                    parts = profile.key.split('_')
                    if len(parts) >= 3:
                        suffix = parts[-1]
                    elif len(parts) == 2:
                        suffix = parts[-1]
                    else:
                        # Пробуем получить из названия файла
                        suffix = "def"
                else:
                    print(f"      profile не имеет атрибута 'key'")
                
                result = f"{type_code}_{level}_{suffix}"
                print(f"      Сгенерированный ключ: {result}")
                return result
            
            # Для старого формата (если есть profile_name)
            elif hasattr(profile, 'profile_name'):
                # Парсим название профиля
                name = profile.profile_name
                print(f"      profile_name = {name}")
                
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
                
                result = f"{type_code}_{level}_{suffix}"
                print(f"      Сгенерированный ключ: {result}")
                return result
            
            # Если не удалось определить формат
            print(f"    ⚠️ Не удалось сгенерировать ключ для профиля")
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка генерации ключа для профиля: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу
        
        Args:
            profile_key: Ключ профиля (например, "SP_1_def", "ip_4_exp")
            
        Returns:
            Объект VariaticaProfile или None
        """
        if not profile_key or not isinstance(profile_key, str):
            return None
        
        # Убираем лишние пробелы
        profile_key = profile_key.strip()
        
        print(f"\n🔍 ЗАГРУЗЧИК: Поиск профиля '{profile_key}'")
        
        # 1. Пробуем как есть
        if profile_key in self.profiles:
            print(f"   ✅ Найден напрямую: {profile_key}")
            return self.profiles[profile_key]
        
        # 2. Пробуем нормализованный ключ
        normalized_key = self.normalize_profile_key(profile_key)
        if normalized_key in self.profiles:
            print(f"   ✅ Найден по нормализованному ключу: {normalized_key}")
            return self.profiles[normalized_key]
        
        # 3. Пробуем нижний регистр
        lower_key = profile_key.lower()
        if lower_key in self.profiles:
            print(f"   ✅ Найден по нижнему регистру: {lower_key}")
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
            
            # Убираем дубликаты
            variations = list(dict.fromkeys(variations))
            
            print(f"   🔍 Проверяем варианты для IP типа:")
            for var in variations:
                if var in self.profiles:
                    print(f"   ✅ Найден по варианту: {var}")
                    return self.profiles[var]
                else:
                    print(f"   ❌ Не найден: {var}")
        
        # 5. Поиск по частичному совпадению (без учёта регистра)
        search_key = profile_key.upper().replace('-', '_')
        print(f"   🔍 Поиск по частичному совпадению: {search_key}")
        
        found_key = None
        for key in self.profiles.keys():
            if key.upper() == search_key:
                found_key = key
                break
        
        if found_key:
            print(f"   ✅ Найден по частичному совпадению: {found_key}")
            return self.profiles[found_key]
        
        # 6. Логируем ошибку
        print(f"\n❌ Профиль не найден: '{profile_key}'")
        
        # Показываем доступные ключи для этого типа
        if '_' in profile_key:
            prefix = profile_key.split('_')[0].upper()
            similar_keys = []
            for key in self.profiles.keys():
                if key.upper().startswith(prefix):
                    similar_keys.append(key)
            
            if similar_keys:
                print(f"   📋 Доступные ключи начинающиеся с '{prefix}':")
                unique_similar = sorted(set(similar_keys))
                for key in unique_similar[:15]:  # Показываем первые 15
                    print(f"   - {key}")
                if len(unique_similar) > 15:
                    print(f"   ... и ещё {len(unique_similar) - 15} ключей")
        
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
        print("\n🔄 Перезагрузка профилей...")
        self.profiles.clear()
        self.load_all_profiles()
        print(f"✅ Профили перезагружены. Всего: {len(self.get_all_profiles())}")

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

# Вспомогательная функция для отладки
def debug_profile_loading():
    """Функция для отладки загрузки профилей"""
    print("\n" + "="*60)
    print("🐛 ОТЛАДКА ЗАГРУЗЧИКА ПРОФИЛЕЙ")
    print("="*60)
    
    # Получаем все профили
    all_profiles = get_all_profiles()
    print(f"📊 Всего уникальных профилей: {len(all_profiles)}")
    
    if all_profiles:
        # Группируем по типам
        types = {}
        for key in all_profiles:
            type_code = key.split('_')[0]
            if type_code not in types:
                types[type_code] = []
            types[type_code].append(key)
        
        # Выводим по типам
        for type_code in sorted(types.keys()):
            profiles = types[type_code]
            print(f"\n{type_code} профилей ({len(profiles)}):")
            for i, key in enumerate(sorted(profiles), 1):
                print(f"  {i:2d}. {key}")
    
    # Тестируем поиск
    print("\n🔍 Тестируем поиск профилей:")
    test_keys = [
        "ia_4",
        "IA_4",
        "ia_4_exp",
        "IA_4_exp",
        "ia_4_cap",
        "IA_4_cap",
        "sp_1_def",
        "SA_1_def"
    ]
    
    for key in test_keys:
        profile = get_profile(key)
        status = "✅ НАЙДЕН" if profile else "❌ НЕ НАЙДЕН"
        title = ""
        if profile and hasattr(profile, 'title'):
            title = profile.title[:30] + "..." if len(profile.title) > 30 else profile.title
            status = f"{status}: {title}"
        print(f"  {key:20} → {status}")
    
    print("="*60)

# При запуске loader.py напрямую, выполняем отладку
if __name__ == "__main__":
    debug_profile_loading()
