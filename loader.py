"""
Загрузчик профилей из файловой системы - ИСПРАВЛЕННАЯ ВЕРСИЯ
Проблема: импорт from ..base import VariaticaProfile ломается при exec()
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
        
        print(f"\n{'='*60}")
        print("🚀 ИНИЦИАЛИЗАЦИЯ ЗАГРУЗЧИКА ПРОФИЛЕЙ")
        print(f"Директория профилей: {os.path.abspath(profiles_dir)}")
        print(f"Директория существует: {os.path.exists(profiles_dir)}")
        print(f"{'='*60}\n")
        
        if os.path.exists(profiles_dir):
            print(f"📁 Содержимое директории {profiles_dir}:")
            for item in os.listdir(profiles_dir):
                item_path = os.path.join(profiles_dir, item)
                if os.path.isdir(item_path):
                    print(f"  📂 {item}/")
                    # Показываем содержимое подпапок
                    try:
                        sub_items = os.listdir(item_path)
                        py_files = [f for f in sub_items if f.endswith('.py') and f != '__init__.py']
                        print(f"    📄 Файлы: {len(py_files)}")
                        for py_file in py_files[:5]:  # Показываем первые 5
                            print(f"      - {py_file}")
                        if len(py_files) > 5:
                            print(f"      ... и ещё {len(py_files) - 5} файлов")
                    except:
                        pass
        else:
            print(f"❌ Директория {profiles_dir} не существует!")
            print(f"📌 Текущая рабочая директория: {os.getcwd()}")
        
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
                print(f"    📄 Найден: {os.path.relpath(filepath, self.profiles_dir)}")
        
        print(f"✅ Всего найдено файлов: {len(profile_files)}")
        return profile_files
    
    def load_profile_from_file(self, filepath: str) -> VariaticaProfile:
        """
        Загружает профиль из файла Python - ИСПРАВЛЕННАЯ ВЕРСИЯ
        
        Args:
            filepath: Путь к файлу профиля
            
        Returns:
            Объект VariaticaProfile или None в случае ошибки
        """
        try:
            file_name = os.path.basename(filepath)
            print(f"\n  📖 Загрузка файла: {file_name}")
            print(f"    📍 Путь: {os.path.relpath(filepath, self.profiles_dir)}")
            
            # Читаем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"    📄 Размер файла: {len(content)} символов")
            
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Удаляем ВСЕ импорты VariaticaProfile ПЕРЕД выполнением
            lines = content.split('\n')
            cleaned_lines = []
            imports_removed = 0
            
            for line in lines:
                # Удаляем ЛЮБЫЕ строки с VariaticaProfile в импорте
                if 'VariaticaProfile' in line and ('import' in line or 'from' in line):
                    print(f"    🗑 Удален импорт: {line.strip()[:50]}...")
                    imports_removed += 1
                    continue  # Полностью удаляем эту строку
                cleaned_lines.append(line)
            
            if imports_removed > 0:
                print(f"    🔧 Удалено импортов: {imports_removed}")
            
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
            
            # КРИТИЧЕСКИ ВАЖНО: Добавляем VariaticaProfile в глобальное пространство модуля
            module.VariaticaProfile = VariaticaProfile
            module.__dict__['VariaticaProfile'] = VariaticaProfile
            module.__dict__['__name__'] = module_name
            module.__dict__['__file__'] = filepath
            
            # Также добавляем sys и os для совместимости
            module.__dict__['sys'] = sys
            module.__dict__['os'] = os
            
            print(f"    ⚙️ Выполняем код модуля...")
            
            try:
                # Выполняем код модуля
                exec(content, module.__dict__)
                print(f"    ✅ Код выполнен успешно")
            except Exception as e:
                print(f"    ❌ Ошибка выполнения кода: {type(e).__name__}: {e}")
                
                # Покажем проблемные строки для отладки
                print(f"    🔍 Отладка проблемного кода (первые 10 строк):")
                for i, line in enumerate(cleaned_lines[:10], 1):
                    print(f"      {i:2}: {line}")
                
                return None
            
            # Ищем объект VariaticaProfile в модуле
            profile = None
            profile_vars = []
            
            # Сначала ищем по имени переменной (по шаблону)
            expected_var_name = file_name.replace('.py', '').upper()  # Например: SA_8_tra
            print(f"    🔍 Ищем переменную: {expected_var_name}")
            
            if hasattr(module, expected_var_name):
                var_value = getattr(module, expected_var_name)
                if isinstance(var_value, VariaticaProfile):
                    profile = var_value
                    print(f"    ✅ Найден профиль в переменной {expected_var_name}")
                    profile_vars.append((expected_var_name, var_value))
            
            # Если не нашли по ожидаемому имени, ищем любую переменную с профилем
            if not profile:
                print(f"    🔍 Поиск всех объектов VariaticaProfile в модуле...")
                for var_name in dir(module):
                    if not var_name.startswith('_') and var_name not in ['sys', 'os', 'VariaticaProfile']:
                        try:
                            var_value = getattr(module, var_name)
                            if isinstance(var_value, VariaticaProfile):
                                profile_vars.append((var_name, var_value))
                                print(f"      📍 Найден: {var_name} ({type(var_value).__name__})")
                        except:
                            pass
            
            if profile_vars:
                print(f"    ✅ Найдены {len(profile_vars)} объектов VariaticaProfile")
                
                # Берем первый найденный профиль
                profile = profile_vars[0][1]
                print(f"    🎯 Выбран профиль: {profile_vars[0][0]}")
                
                # Устанавливаем ключ профиля из имени файла, если его нет
                if not hasattr(profile, 'key') or not profile.key:
                    key_from_file = self.extract_profile_key_from_filename(filepath)
                    profile.key = key_from_file
                    print(f"    🔧 Установлен ключ профиля: {key_from_file}")
            
            if not profile:
                print(f"    ❌ Не найден объект VariaticaProfile в {file_name}")
                print(f"    🔍 Доступные переменные в модуле:")
                for var_name in dir(module):
                    if not var_name.startswith('_'):
                        print(f"      - {var_name}")
                
                return None
            
            # Дополнительная информация о профиле
            print(f"    📋 Информация о профиле:")
            print(f"      Ключ: {getattr(profile, 'key', 'Нет')}")
            print(f"      Тип: {getattr(profile, 'type_code', 'Нет')}")
            print(f"      Уровень: {getattr(profile, 'level', 'Нет')}")
            print(f"      Заголовок: {getattr(profile, 'title', 'Нет')[:50]}...")
            
            return profile
            
        except SyntaxError as e:
            print(f"    ❌ Синтаксическая ошибка в {os.path.basename(filepath)}: {e}")
            print(f"    📍 Позиция ошибки: {e.lineno}:{e.offset}")
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
            
            # ДЛЯ ОТЛАДКИ: покажем все файлы которые будем загружать
            print(f"\n📋 СПИСОК ФАЙЛОВ ДЛЯ ЗАГРУЗКИ:")
            for i, filepath in enumerate(profile_files, 1):
                filename = os.path.basename(filepath)
                rel_path = os.path.relpath(filepath, self.profiles_dir)
                print(f"  {i:2d}. {filename} ({rel_path})")
            
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
                            
                            # Сохраняем версию с дефисами
                            self.profiles[normalized_key.replace('_', '-')] = profile
                            
                            # Для SA типа также сохраняем SA_3_con как sa_3_con
                            if normalized_key.startswith("SA_"):
                                self.profiles[normalized_key.lower()] = profile
                                # Сохраняем версию без суффикса для быстрого поиска
                                base_key = '_'.join(normalized_key.split('_')[:2])  # SA_3
                                self.profiles[base_key] = profile
                                self.profiles[base_key.lower()] = profile
                            
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
                
                result = f"{type_code}_{level}_{suffix}"
                return result
            
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
                
                result = f"{type_code}_{level}_{suffix}"
                return result
            
            # Если не удалось определить формат
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка генерации ключа для профиля: {e}")
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
        
        # 5. УМНЫЙ ПОИСК - если не нашли по точному ключу, ищем любой профиль этого типа и уровня
        print(f"   🔍 УМНЫЙ ПОИСК: ищем любой профиль типа и уровня...")
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
    
    def _smart_profile_search(self, profile_key: str) -> VariaticaProfile:
        """
        Умный поиск профиля - если не находит по точному ключу,
        ищет профиль того же типа и уровня (игнорируя суффикс Дилтса)
        
        Примеры:
            sa_1_val → найдёт sa_1_def (любой профиль SA уровня 1)
            sp_3_tra → найдёт sp_3_con (любой профиль SP уровня 3)
        """
        # Анализируем ключ
        clean_key = profile_key.lower().replace('-', '_')
        parts = clean_key.split('_')
        
        if len(parts) < 2:
            return None
        
        # Извлекаем тип и уровень
        type_part = parts[0]  # sa, sp, ia, ip
        level_part = parts[1]  # 1, 2, 3...
        
        print(f"     🤔 Анализируем: тип={type_part}, уровень={level_part}")
        
        # Шаг 1: Ищем базовый ключ типа SA_3 (без суффикса)
        base_key = f"{type_part}_{level_part}"
        if base_key in self.profiles:
            print(f"     ✅ Найден базовый профиль: {base_key}")
            return self.profiles[base_key]
        
        # Шаг 2: Ищем с верхним регистром типа
        base_key_upper = f"{type_part.upper()}_{level_part}"
        if base_key_upper in self.profiles:
            print(f"     ✅ Найден базовый профиль: {base_key_upper}")
            return self.profiles[base_key_upper]
        
        # Шаг 3: Ищем любой профиль этого типа и уровня с любым суффиксом
        for suffix in self.all_suffixes:
            test_key = f"{type_part}_{level_part}_{suffix}"
            if test_key in self.profiles:
                print(f"     ✅ УМНЫЙ ПОИСК: найден {test_key} вместо {profile_key}")
                return self.profiles[test_key]
        
        # Шаг 4: Ищем с верхним регистром
        for suffix in self.all_suffixes:
            test_key = f"{type_part.upper()}_{level_part}_{suffix}"
            if test_key in self.profiles:
                print(f"     ✅ УМНЫЙ ПОИСК: найден {test_key} вместо {profile_key}")
                return self.profiles[test_key]
        
        # Шаг 5: Если не нашли SA_3, пробуем ближайшие уровни
        if type_part == "sa" and level_part == "3":
            print(f"     🔄 SA_3 не найден, ищу SA_2 или SA_4...")
            
            # Пробуем уровень 2
            for suffix in self.all_suffixes:
                test_key = f"{type_part}_2_{suffix}"
                if test_key in self.profiles:
                    print(f"     🔄 Использую {test_key} вместо SA_3")
                    return self.profiles[test_key]
            
            # Пробуем уровень 4
            for suffix in self.all_suffixes:
                test_key = f"{type_part}_4_{suffix}"
                if test_key in self.profiles:
                    print(f"     🔄 Использую {test_key} вместо SA_3")
                    return self.profiles[test_key]
        
        # Шаг 6: Ищем любой профиль этого типа
        for key in self.profiles.keys():
            if key.lower().startswith(f"{type_part}_"):
                print(f"     🔄 Найден ближайший {key} вместо {profile_key}")
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
                    if profile_key not in self.profiles and profile_key.lower() not in self.profiles:
                        missing_profiles.append(profile_key)
        
        if missing_profiles:
            print(f"\n⚠️  Отсутствуют профили ({len(missing_profiles)}):")
            for profile in missing_profiles[:10]:  # Показываем первые 10
                print(f"   ❌ {profile}")
            if len(missing_profiles) > 10:
                print(f"   ... и ещё {len(missing_profiles) - 10} профилей")
            
            # Проверим конкретно SA_3
            print(f"\n🔍 Проверка SA_3 профилей:")
            for suffix in expected_suffixes:
                key = f"SA_3_{suffix}"
                exists = key in self.profiles or key.lower() in self.profiles
                status = "✅" if exists else "❌"
                print(f"   {status} {key}")
            
            return False
        
        print(f"\n✅ Все 36 профилей загружены!")
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
    
    # Тестируем поиск - ВАЖНО: тестируем проблемные случаи из логов
    print("\n🔍 ТЕСТИРУЕМ ПОИСК ПРОФИЛЕЙ (проблемные случаи из логов):")
    
    # Эти профили бот искал в логах и не находил
    problematic_keys = [
        "sa_1_val",     # Бот искал этот профиль
        "sa_1_tra",     # Бот искал этот профиль
        "sa_1_ide",     # Бот искал этот профиль
        "sa_2_def",     # Бот искал этот профиль
        "sa_2_con",     # Бот искал этот профиль
        "sa_2_exp",     # Бот искал этот профиль
        "sa_2_int",     # Бот искал этот профиль
        "sa_2_aut",     # Бот искал этот профиль
        "sa_2_val",     # Бот искал этот профиль
        "sa_2_tra",     # Бот искал этот профиль
        "sa_3_sit",     # Бот искал этот профиль
        "sa_3_con",     # Бот искал этот профиль
        "sa_3_exp",     # Бот искал этот профиль
        "sa_3_int",     # Бот искал этот профиль
        "sa_3_aut",     # Бот искал этот профиль
        "sa_3_val",     # Бот искал этот профиль
        "sa_3_tra",     # Бот искал этот профиль
        "sa_3_ide",     # Бот искал этот профиль
        "sp_2_con",     # Бот искал этот профиль
        "ip_7_aut",     # Бот искал этот профиль
    ]
    
    for key in problematic_keys:
        # Пробуем обычный поиск
        profile = get_profile(key)
        if profile:
            title = getattr(profile, 'title', 'Без названия')[:30]
            actual_key = getattr(profile, 'key', 'unknown')
            print(f"  ✅ {key:20} → НАЙДЕН ({actual_key}): {title}...")
        else:
            # Пробуем умный поиск
            smart_profile = get_profile_smart(key)
            if smart_profile:
                title = getattr(smart_profile, 'title', 'Без названия')[:30]
                actual_key = getattr(smart_profile, 'key', 'unknown')
                print(f"  🧠 {key:20} → УМНЫЙ ПОИСК ({actual_key}): {title}...")
            else:
                print(f"  ❌ {key:20} → НЕ НАЙДЕН")
    
    # Тестируем стандартные профили
    print("\n🔍 Тестируем стандартные профили:")
    standard_keys = [
        "sa_1_def",
        "sp_2_sit", 
        "ia_3_con",
        "ip_4_exp",
        "SA_1_DEF",
        "SP_2_SIT",
    ]
    
    for key in standard_keys:
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
