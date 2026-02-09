"""
Загрузчик профилей из файловой системы
ПОЛНАЯ ВЕРСИЯ С ИСПРАВЛЕННЫМ ПОИСКОМ
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
        self.all_suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
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
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"    ❌ Ошибка загрузки профиля из {os.path.basename(filepath)}: {type(e).__name__}: {e}")
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
                            
                            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сохраняем БАЗОВЫЙ ключ (тип_уровень)
                            # Дважды проверяем формат ключа
                            parts = normalized_key.split('_')
                            if len(parts) >= 2:
                                # Создаем базовый ключ
                                base_key = f"{parts[0]}_{parts[1]}"
                                base_key_lower = base_key.lower()
                                
                                print(f"    📍 СОЗДАЮ базовые ключи: '{base_key}' и '{base_key_lower}'")
                                
                                # Сохраняем в ВЕРХНЕМ регистре
                                self.profiles[base_key] = profile
                                
                                # Сохраняем в НИЖНЕМ регистре
                                self.profiles[base_key_lower] = profile
                            
                            successful_loads += 1
                        else:
                            print(f"    ⚠️ Не удалось сгенерировать ключ для профиля из {os.path.basename(filepath)}")
                            failed_loads += 1
                    else:
                        print(f"    ❌ Не удалось загрузить профиль из {os.path.basename(filepath)}")
                        failed_loads += 1
                        
                except Exception as e:
                    print(f"    ❌ Ошибка обработки файла {os.path.basename(filepath)}: {type(e).__name__}: {e}")
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
            traceback.print_exc()
    
    def print_statistics(self):
        """Выводим статистику по загруженным профилям с БАЗОВЫМИ ключами"""
        type_counts = {'SA': 0, 'IA': 0, 'SP': 0, 'IP': 0}
        unique_keys = set()
        base_keys = set()
        
        for key in self.profiles.keys():
            # Отделяем базовые ключи от полных
            if isinstance(key, str):
                parts = key.split('_')
                if len(parts) == 2 and parts[1].isdigit():
                    # Это базовый ключ (тип_уровень)
                    base_keys.add(key)
                
                # Считаем только нормализованные полные ключи
                if len(parts) >= 3 and not key.islower() and '-' not in key:
                    unique_keys.add(key)
                    
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
        
        total_unique = len(unique_keys)
        for type_code, count in type_counts.items():
            percentage = (count / total_unique * 100) if total_unique > 0 else 0
            print(f"  {type_code}: {count} профилей ({percentage:.1f}%)")
        
        print(f"\n  Всего уникальных профилей: {total_unique}")
        print(f"  Всего базовых ключей: {len(base_keys)}")
        
        # Выводим все базовые ключи
        if base_keys:
            print(f"\n🔑 Базовые ключи (тип_уровень):")
            sorted_base_keys = sorted(list(base_keys))
            for key in sorted_base_keys:
                print(f"  - {key}")
        
        # Выводим все полные ключи
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
        
        print("="*50)
    
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
            traceback.print_exc()
            return None
    
    def get_profile(self, profile_key: str) -> VariaticaProfile:
        """
        Получает профиль по ключу - УПРОЩЕННЫЙ ПОИСК
        
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
        
        # 2. Пробуем нижний регистр
        lower_key = profile_key.lower()
        if lower_key in self.profiles:
            print(f"   ✅ Найден по нижнему регистру: {lower_key}")
            return self.profiles[lower_key]
        
        # 3. Пробуем верхний регистр
        upper_key = profile_key.upper()
        if upper_key in self.profiles:
            print(f"   ✅ Найден по верхнему регистру: {upper_key}")
            return self.profiles[upper_key]
        
        # 4. Пробуем заменить дефисы на подчеркивания
        if '-' in profile_key:
            normalized = profile_key.replace('-', '_')
            if normalized in self.profiles:
                print(f"   ✅ Найден после замены дефисов: {normalized}")
                return self.profiles[normalized]
        
        # 5. УМНЫЙ ПОИСК - ищем профиль того же типа и уровня
        print(f"   🔍 УМНЫЙ ПОИСК: ищем профиль того же типа и уровня...")
        profile = self._smart_profile_search(profile_key)
        if profile:
            return profile
        
        # 6. Логируем ошибку
        print(f"\n❌ Профиль не найден: '{profile_key}'")
        
        # Показываем доступные ключи для этого типа
        if '_' in profile_key:
            parts = profile_key.split('_')
            if len(parts) > 0:
                prefix = parts[0].upper()
                similar_keys = []
                for key in self.profiles.keys():
                    if isinstance(key, str) and key.upper().startswith(prefix):
                        similar_keys.append(key)
                
                if similar_keys:
                    print(f"   📋 Доступные ключи начинающиеся с '{prefix}':")
                    unique_similar = sorted(set(similar_keys))
                    for key in unique_similar[:15]:  # Показываем первые 15
                        print(f"   - '{key}'")
                    if len(unique_similar) > 15:
                        print(f"   ... и ещё {len(unique_similar) - 15} ключей")
        
        return None
    
    def _smart_profile_search(self, profile_key: str) -> VariaticaProfile:
        """
        УМНЫЙ ПОИСК: Находит профиль того же типа и уровня
        Игнорирует суффикс Дилтса, ищет по типу и уровню
        """
        # Анализируем ключ
        clean_key = profile_key.lower().replace('-', '_')
        parts = clean_key.split('_')
        
        if len(parts) < 2:
            return None
        
        # Извлекаем тип и уровень
        type_part = parts[0]  # sa, sp, ia, ip
        level_part = parts[1]  # 1, 2, 3...
        
        print(f"     🤔 Ищем: тип={type_part}, уровень={level_part}")
        
        # Шаг 1: Ищем БАЗОВЫЙ ключ (тип_уровень)
        # Проверяем ВСЕ возможные варианты регистра
        base_variants = [
            f"{type_part}_{level_part}",           # sa_3
            f"{type_part.upper()}_{level_part}",   # SA_3
            f"{type_part}_{level_part.upper()}",   # sa_3 (если level_part уже в верхнем)
            f"{type_part.upper()}_{level_part.upper()}",  # SA_3
        ]
        
        print(f"     🔍 Ищу базовые ключи: {base_variants}")
        
        for base_key in base_variants:
            if base_key in self.profiles:
                print(f"     ✅ Найден базовый профиль: {base_key}")
                return self.profiles[base_key]
        
        # Шаг 2: Ищем любой профиль этого типа и уровня с любым суффиксом
        for suffix in self.all_suffixes:
            # Проверяем разные варианты регистра
            test_variants = [
                f"{type_part}_{level_part}_{suffix}",           # sa_3_con
                f"{type_part.upper()}_{level_part}_{suffix}",   # SA_3_con
                f"{type_part}_{level_part.upper()}_{suffix}",   # sa_3_con (если level_part в верхнем)
                f"{type_part.upper()}_{level_part.upper()}_{suffix}",  # SA_3_CON
                f"{type_part.upper()}_{level_part}_{suffix.upper()}",  # SA_3_CON (только суффикс верхний)
            ]
            
            for test_key in test_variants:
                if test_key in self.profiles:
                    print(f"     ✅ УМНЫЙ ПОИСК: найден {test_key} вместо {profile_key}")
                    return self.profiles[test_key]
        
        # Шаг 3: Если не нашли, пробуем ближайшие уровни (только для этого типа)
        print(f"     🔍 {type_part.upper()}_{level_part} не найден, ищу ближайшие уровни...")
        
        # Пробуем уровни в порядке близости
        try:
            target_level = int(level_part)
            level_order = []
            
            # Создаем порядок поиска
            if target_level > 1:
                level_order.append(str(target_level - 1))  # уровень ниже
            if target_level < 9:
                level_order.append(str(target_level + 1))  # уровень выше
            
            # Добавляем остальные уровни
            for i in range(1, 10):
                level_str = str(i)
                if level_str not in level_order and level_str != level_part:
                    level_order.append(level_str)
            
            for search_level in level_order:
                for suffix in self.all_suffixes:
                    # Проверяем разные варианты регистра
                    test_variants = [
                        f"{type_part}_{search_level}_{suffix}",
                        f"{type_part.upper()}_{search_level}_{suffix}",
                        f"{type_part.upper()}_{search_level.upper()}_{suffix}",
                        f"{type_part.upper()}_{search_level}_{suffix.upper()}",
                    ]
                    
                    for test_key in test_variants:
                        if test_key in self.profiles:
                            print(f"     🔄 Использую {test_key} (уровень {search_level}) вместо {profile_key}")
                            return self.profiles[test_key]
        except ValueError:
            pass
        
        # Шаг 4: Ищем любой профиль этого типа
        print(f"     🔍 Ищу любой профиль типа {type_part.upper()}...")
        for key in self.profiles.keys():
            if isinstance(key, str) and key.lower().startswith(f"{type_part}_"):
                print(f"     🔄 Использую {key} вместо {profile_key}")
                return self.profiles[key]
        
        return None
    
    def get_profile_smart(self, profile_key: str) -> VariaticaProfile:
        """
        ТОЛЬКО УМНЫЙ поиск профиля (без обычного поиска)
        Используется в основном коде бота для поиска профилей с разными суффиксами Дилтса
        """
        return self._smart_profile_search(profile_key)
    
    def get_all_profiles(self) -> list:
        """
        Возвращает список всех уникальных ключей профилей (только нормализованные)
        
        Returns:
            Список ключей профилей
        """
        unique_keys = set()
        for key in self.profiles.keys():
            # Берем только нормализованные ключи (в верхнем регистре, без дефисов)
            if isinstance(key, str) and not key.islower() and '-' not in key and '_' in key:
                parts = key.split('_')
                if len(parts) >= 3:  # Полные ключи (тип_уровень_суффикс)
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
            if isinstance(key, str) and key.startswith(normalized_type + '_'):
                result[key] = profile
        
        return result
    
    def reload_profiles(self):
        """Перезагружает все профили из файлов"""
        print("\n🔄 Перезагрузка профилей...")
        self.profiles.clear()
        self.load_all_profiles()
        print(f"✅ Профили перезагружены. Всего: {len(self.get_all_profiles())}")
    
    def check_all_profiles_loaded(self) -> bool:
        """
        Проверяет, загружены ли все 36 профилей
        
        Returns:
            True если все профили загружены, иначе False
        """
        expected_types = ['SA', 'SP', 'IA', 'IP']
        expected_levels = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        expected_suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
        
        missing_profiles = []
        
        for type_code in expected_types:
            for level in expected_levels:
                for suffix in expected_suffixes:
                    profile_key = f"{type_code}_{level}_{suffix}"
                    if profile_key not in self.profiles:
                        missing_profiles.append(profile_key)
        
        if missing_profiles:
            print(f"\n⚠️  Отсутствуют профили ({len(missing_profiles)}):")
            for profile in missing_profiles[:10]:  # Показываем первые 10
                print(f"   ❌ {profile}")
            if len(missing_profiles) > 10:
                print(f"   ... и ещё {len(missing_profiles) - 10} профилей")
            
            return False
        
        print(f"\n✅ Все 36 профилей загружены!")
        
        # Дополнительно проверяем базовые ключи
        base_keys_count = sum(1 for key in self.profiles.keys() 
                            if isinstance(key, str) and len(key.split('_')) == 2 and key.split('_')[1].isdigit())
        print(f"✅ Базовых ключей (тип_уровень): {base_keys_count}")
        
        return True

# Создаём глобальный экземпляр загрузчика
loader = ProfileLoader()

# Функции для удобного импорта
def get_profile(profile_key: str) -> VariaticaProfile:
    """Получает профиль по ключу - использует умный поиск при необходимости"""
    return loader.get_profile(profile_key)

def get_profile_smart(profile_key: str) -> VariaticaProfile:
    """Получает профиль по ключу - ТОЛЬКО умный поиск"""
    return loader.get_profile_smart(profile_key)

def get_all_profiles() -> list:
    """Возвращает все уникальные ключи профилей"""
    return loader.get_all_profiles()

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
    print("\n🔍 ТЕСТИРУЕМ ПОИСК ПРОФИЛЕЙ:")
    
    test_cases = [
        # Критические случаи из логов
        ("sa_3_con", "SA_3_con"),
        ("SA_3_con", "SA_3_con"),
        ("sa_3_con", "SA_3_con"),
        
        # Проблемные случаи
        ("sp_3_aut", "SP_3_con"),
        ("sp_3_val", "SP_3_con"),
        ("sp_3_tra", "SP_3_con"),
        ("sp_3_ide", "SP_3_con"),
        
        # Стандартные профили
        ("sa_1_def", "SA_1_def"),
        ("sp_2_sit", "SP_2_sit"),
        ("ia_3_con", "IA_3_con"),
        ("ip_4_exp", "IP_4_exp"),
        
        # Проверка базовых ключей
        ("SA_3", "SA_3_con"),
        ("sp_4", "SP_4_exp"),
        ("ia_2", "IA_2_sit"),
    ]
    
    for search_key, expected_key in test_cases:
        profile = get_profile(search_key)
        if profile:
            actual_key = getattr(profile, 'key', 'unknown')
            title = getattr(profile, 'title', 'Без названия')[:30]
            
            if expected_key.lower() in actual_key.lower():
                status = "✅"
            else:
                status = "⚠️"
            
            print(f"  {status} {search_key:20} → {actual_key}: {title}...")
        else:
            print(f"  ❌ {search_key:20} → НЕ НАЙДЕН")
    
    # Проверяем базовые ключи
    print("\n🔍 ПРОВЕРКА БАЗОВЫХ КЛЮЧЕЙ:")
    test_base_keys = ["SA_3", "sa_3", "SP_4", "sp_4", "IA_2", "ia_2"]
    
    for base_key in test_base_keys:
        profile = get_profile(base_key)
        if profile:
            actual_key = getattr(profile, 'key', 'unknown')
            print(f"  ✅ {base_key:10} → {actual_key}")
        else:
            print(f"  ❌ {base_key:10} → НЕ НАЙДЕН")
    
    print("="*60)

# При запуске loader.py напрямую, выполняем отладку
if __name__ == "__main__":
    debug_profile_loading()
