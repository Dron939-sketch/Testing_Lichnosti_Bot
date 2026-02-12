"""
Загрузчик профилей из файловой системы
ИСПРАВЛЕННАЯ ВЕРСИЯ - поиск по типу и уровню, игнорируя суффикс Дилтса

ДОБАВЛЕНО: 🟦 4F-МОДУЛЬ - загрузчик JSON-функций для интимных ключей
Версия: 1.0 (18+ интеграция)
"""

import os
import sys
import json
import importlib.util
import traceback
from typing import Dict, Any, Optional, List
from functools import lru_cache
from base import VariaticaProfile

# ============================================
# 🟦 4F-МОДУЛЬ: ЗАГРУЗЧИК JSON-ФУНКЦИЙ
# ============================================

class FourFLoader:
    """
    Загрузчик 4F-функций из JSON-файлов
    
    Структура папок:
    профили/4F/
    ├── 1F/
    │   ├── sa_4_cap.json      (🔥 живой демо-ключ для всех)
    │   └── default.json       (заглушка)
    ├── 2F/
    │   ├── sa_4_cap.json      (🍽 живой демо-ключ для всех)
    │   └── default.json       (заглушка)
    ├── 3F/
    │   ├── sa_4_cap.json      (⚡ живой демо-ключ для всех)
    │   └── default.json       (заглушка)
    └── 4F/
        ├── sa_4_cap.json      (💡 живой демо-ключ для всех)
        └── default.json       (заглушка)
    
    ⚠️ MVP: ВСЕГДА используем sa_4_cap.json для всех покупок!
    """
    
    # Эмодзи для каждой функции
    FUNCTION_EMOJI = {
        "1F": "🔥",
        "2F": "🍽",
        "3F": "⚡",
        "4F": "💡"
    }
    
    # Названия функций
    FUNCTION_NAMES = {
        "1F": "КЛЮЧ ВОЗБУЖДЕНИЯ",
        "2F": "КЛЮЧ НАСЫЩЕНИЯ",
        "3F": "КЛЮЧ РАЗРЯДКИ",
        "4F": "КЛЮЧ ИНТЕГРАЦИИ"
    }
    
    # Цвета/эмодзи для демо-режима
    DEMO_EMOJI = {
        "1F": "🔥",
        "2F": "🍽",
        "3F": "⚡",
        "4F": "💡"
    }
    
    def __init__(self, base_path: str = "профили/4F"):
        """
        Инициализация загрузчика 4F-функций
        
        Args:
            base_path: Базовая директория с 4F-функциями
        """
        self.base_path = base_path
        self.cache = {}
        self.ensure_directory_structure()
    
    def ensure_directory_structure(self):
        """Создаёт структуру папок 4F, если её нет"""
        functions = ["1F", "2F", "3F", "4F"]
        
        for func in functions:
            func_path = os.path.join(self.base_path, func)
            if not os.path.exists(func_path):
                os.makedirs(func_path, exist_ok=True)
                print(f"📁 Создана папка: {func_path}")
        
        print(f"✅ 4F-структура проверена: {self.base_path}")
    
    @lru_cache(maxsize=32)
    def _load_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Загружает JSON-файл с кэшированием
        
        Args:
            file_path: Путь к JSON-файлу
            
        Returns:
            Dict: Содержимое JSON-файла
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Пробуем загрузить default.json
            dir_path = os.path.dirname(file_path)
            default_path = os.path.join(dir_path, "default.json")
            
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                # Создаём базовую заглушку
                return self._create_default_content(file_path)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON {file_path}: {e}")
            return self._create_default_content(file_path)
    
    def _create_default_content(self, file_path: str) -> Dict[str, Any]:
        """
        Создаёт базовое содержимое для отсутствующего файла
        
        Args:
            file_path: Путь к файлу (для определения функции)
            
        Returns:
            Dict: Базовая заглушка
        """
        # Извлекаем название функции из пути
        path_parts = file_path.split(os.sep)
        function = "1F"
        
        for part in path_parts:
            if part in ["1F", "2F", "3F", "4F"]:
                function = part
                break
        
        emoji = self.FUNCTION_EMOJI.get(function, "🔑")
        name = self.FUNCTION_NAMES.get(function, "КЛЮЧ")
        
        return {
            "success": True,
            "function": function,
            "profile_key": "sa_4_cap",
            "source_profile": "sa_4_cap",
            "is_demo": True,
            "demo_notice": f"⚠️ Это демо-версия ключа {function}. Полная версия содержит 3x больше контента и персональные рекомендации.",
            "content": {
                "title": f"{emoji} {function}: {name}",
                "for": "У профиля SA-4_CAP «{friend_name}»",
                "short_description": f"Демо-версия ключа {function}. Приобретите полную версию для получения доступа ко всем материалам.",
                "triggers": [
                    "Пример триггер-фразы 1",
                    "Пример триггер-фразы 2",
                    "Пример триггер-фразы 3"
                ],
                "examples": [
                    "Пример применения 1",
                    "Пример применения 2"
                ],
                "quote": "«Это демо-версия. Полная версия содержит уникальный контент.»"
            },
            "demo_limitation": {
                "title": f"📌 В ПОЛНОЙ ВЕРСИИ {function}:",
                "content": [
                    "✓ 10+ точных триггер-фраз",
                    "✓ Психологический разбор каждой фразы",
                    "✓ Протокол применения в разных контекстах",
                    "✓ Анти-паттерны и как их избежать",
                    "✓ Персональные рекомендации"
                ],
                "price": 99,
                "upgrade_command": f"/buy_function_{function}_full"
            }
        }
    
    def get_function(self, function: str, profile_key: str = "sa_4_cap") -> Dict[str, Any]:
        """
        Получить содержимое 4F-функции
        
        ⚠️ MVP: ВСЕГДА используем sa_4_cap.json для всех покупок!
        
        Args:
            function: 1F, 2F, 3F, 4F
            profile_key: sa_4_cap (игнорируется, всегда sa_4_cap)
            
        Returns:
            Dict: Содержимое функции
        """
        # Нормализуем название функции
        function = function.upper()
        if function not in ["1F", "2F", "3F", "4F"]:
            function = "1F"
        
        # ⚠️ MVP: ВСЕГДА используем sa_4_cap.json
        target_profile = "sa_4_cap"
        
        # Формируем путь к файлу
        file_path = os.path.join(self.base_path, function, f"{target_profile}.json")
        
        # Загружаем содержимое
        content = self._load_json_file(file_path)
        
        # Добавляем метаданные
        content["function"] = function
        content["profile_key"] = profile_key
        content["source_profile"] = target_profile
        content["is_demo"] = content.get("is_demo", True)
        
        # Добавляем demo_notice, если его нет
        if "demo_notice" not in content:
            emoji = self.DEMO_EMOJI.get(function, "🔑")
            content["demo_notice"] = f"{emoji} Это демо-версия. Полная версия содержит 3x больше контента и стоит 99₽."
        
        return content
    
    def substitute_name(self, content: Dict[str, Any], friend_name: str) -> Dict[str, Any]:
        """
        Рекурсивно заменить {friend_name} на имя друга во всех строках
        
        Args:
            content: Словарь с контентом
            friend_name: Имя друга для подстановки
            
        Returns:
            Dict: Контент с подставленным именем
        """
        if not friend_name:
            friend_name = "Друг"
        
        def replace_recursive(obj):
            if isinstance(obj, dict):
                return {k: replace_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_recursive(item) for item in obj]
            elif isinstance(obj, str):
                # Заменяем все вхождения {friend_name}
                return obj.replace("{friend_name}", friend_name)
            else:
                return obj
        
        return replace_recursive(content)
    
    def get_demo_notice(self, function: str, price: int = 99) -> Dict[str, Any]:
        """
        Возвращает демо-уведомление для непокупленных ключей
        
        Args:
            function: 1F, 2F, 3F, 4F
            price: Цена полной версии
            
        Returns:
            Dict: Демо-уведомление
        """
        function = function.upper()
        emoji = self.DEMO_EMOJI.get(function, "🔑")
        name = self.FUNCTION_NAMES.get(function, "КЛЮЧ")
        
        return {
            "title": f"{emoji} ДЕМО-ВЕРСИЯ {function}",
            "notice": f"⚠️ Вы используете демо-версию ключа {function}.",
            "limitations": [
                "❌ Только 3 примера триггер-фраз",
                "❌ Нет психологического разбора",
                "❌ Нет протокола применения",
                "❌ Нет персональных рекомендаций"
            ],
            "upgrade": {
                "price": price,
                "emoji": emoji,
                "text": f"💰 Приобрести полную версию за {price}₽",
                "features": [
                    "✓ 10+ точных триггер-фраз",
                    "✓ Психологический разбор",
                    "✓ Протокол применения",
                    "✓ Персональные рекомендации"
                ]
            }
        }
    
    def validate_function_file(self, function: str, profile_key: str = "sa_4_cap") -> bool:
        """
        Проверяет существование файла функции
        
        Args:
            function: 1F, 2F, 3F, 4F
            profile_key: sa_4_cap, default
            
        Returns:
            bool: Существует ли файл
        """
        function = function.upper()
        file_path = os.path.join(self.base_path, function, f"{profile_key}.json")
        
        if os.path.exists(file_path):
            return True
        
        # Проверяем default.json
        default_path = os.path.join(self.base_path, function, "default.json")
        return os.path.exists(default_path)
    
    def get_all_functions(self) -> List[str]:
        """
        Возвращает список всех доступных 4F-функций
        
        Returns:
            List[str]: Список функций
        """
        functions = []
        
        if not os.path.exists(self.base_path):
            return functions
        
        for func in ["1F", "2F", "3F", "4F"]:
            func_path = os.path.join(self.base_path, func)
            if os.path.exists(func_path):
                functions.append(func)
        
        return functions
    
    def debug_4f_functions(self):
        """Отладочная информация о 4F-функциях"""
        print("\n" + "="*50)
        print("🔑 4F-ФУНКЦИИ: ДИАГНОСТИКА")
        print("="*50)
        
        # Проверяем наличие папок
        functions = self.get_all_functions()
        print(f"📁 Доступные функции: {functions}")
        
        for function in ["1F", "2F", "3F", "4F"]:
            print(f"\n{self.FUNCTION_EMOJI.get(function, '🔑')} {function}:")
            
            # Проверяем sa_4_cap.json
            sa_path = os.path.join(self.base_path, function, "sa_4_cap.json")
            if os.path.exists(sa_path):
                size = os.path.getsize(sa_path)
                print(f"  ✅ sa_4_cap.json ({size} байт)")
                
                # Пробуем загрузить
                try:
                    content = self.get_function(function, "sa_4_cap")
                    if content.get("is_demo"):
                        print(f"     📊 Режим: ДЕМО")
                    else:
                        print(f"     📊 Режим: ПОЛНЫЙ")
                    
                    # Проверяем структуру
                    if "content" in content:
                        triggers = content["content"].get("triggers", [])
                        print(f"     🎯 Триггеров: {len(triggers)}")
                except Exception as e:
                    print(f"     ❌ Ошибка загрузки: {e}")
            else:
                print(f"  ❌ sa_4_cap.json НЕ НАЙДЕН")
            
            # Проверяем default.json
            default_path = os.path.join(self.base_path, function, "default.json")
            if os.path.exists(default_path):
                print(f"  ✅ default.json")
            else:
                print(f"  ⚠️ default.json НЕ НАЙДЕН (будет создана заглушка)")
        
        print("\n" + "="*50)


# ============================================
# 🧠 ОСНОВНОЙ ЗАГРУЗЧИК ПРОФИЛЕЙ
# ============================================

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
    
    def get_4f_profile_info(self, profile_key: str) -> Dict[str, Any]:
        """
        Получает информацию о профиле для 4F-ключа
        Возвращает type_code, level, dilts_code
        
        Args:
            profile_key: Ключ профиля (например, "sa_3_con" или "SA_3")
            
        Returns:
            Dict: Информация о профиле
        """
        profile = self.get_profile(profile_key)
        
        if not profile:
            # Возвращаем базовую информацию
            return {
                "type_code": "SA",
                "level": 4,
                "dilts_code": "cap",
                "profile_key": "sa_4_cap",
                "display_name": "SA_4_CAP"
            }
        
        # Пытаемся получить реальный ключ профиля
        actual_key = getattr(profile, 'key', profile_key)
        
        # Разбираем ключ
        parts = actual_key.split('_')
        
        if len(parts) >= 3:
            type_code = parts[0].upper()
            try:
                level = int(parts[1])
            except ValueError:
                level = 4
            
            dilts_code = parts[2].lower() if len(parts) > 2 else 'cap'
        elif len(parts) == 2:
            type_code = parts[0].upper()
            try:
                level = int(parts[1])
            except ValueError:
                level = 4
            dilts_code = 'cap'
        else:
            type_code = "SA"
            level = 4
            dilts_code = "cap"
        
        return {
            "type_code": type_code,
            "level": level,
            "dilts_code": dilts_code,
            "profile_key": f"{type_code.lower()}_{level}_{dilts_code}",
            "display_name": f"{type_code}_{level}_{dilts_code.upper()}"
        }
    
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


# ============================================
# 🌍 ГЛОБАЛЬНЫЕ ЭКЗЕМПЛЯРЫ ЗАГРУЗЧИКОВ
# ============================================

# Основной загрузчик психологических профилей
loader = ProfileLoader()

# Загрузчик 4F-функций
four_f_loader = FourFLoader()


# ============================================
# 📦 ФУНКЦИИ ДЛЯ УДОБНОГО ИМПОРТА
# ============================================

# ----- Функции для работы с психологическими профилями -----
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

def get_4f_profile_info(profile_key: str) -> dict:
    """Получает информацию о профиле для 4F-ключа"""
    return loader.get_4f_profile_info(profile_key)


# ----- Функции для работы с 4F-ключами -----
def get_4f_function(function: str, profile_key: str = "sa_4_cap") -> dict:
    """
    Получить содержимое 4F-функции
    
    Args:
        function: 1F, 2F, 3F, 4F
        profile_key: Игнорируется, всегда sa_4_cap (MVP)
        
    Returns:
        dict: Содержимое функции
    """
    return four_f_loader.get_function(function, profile_key)

def substitute_friend_name(content: dict, friend_name: str) -> dict:
    """
    Подставить имя друга в контент 4F-функции
    
    Args:
        content: Словарь с контентом
        friend_name: Имя друга
        
    Returns:
        dict: Контент с подставленным именем
    """
    return four_f_loader.substitute_name(content, friend_name)

def get_4f_demo_notice(function: str, price: int = 99) -> dict:
    """
    Получить демо-уведомление для 4F-функции
    
    Args:
        function: 1F, 2F, 3F, 4F
        price: Цена полной версии
        
    Returns:
        dict: Демо-уведомление
    """
    return four_f_loader.get_demo_notice(function, price)

def get_all_4f_functions() -> list:
    """
    Получить список всех доступных 4F-функций
    
    Returns:
        list: Список функций
    """
    return four_f_loader.get_all_functions()

def validate_4f_function(function: str, profile_key: str = "sa_4_cap") -> bool:
    """
    Проверить существование файла 4F-функции
    
    Args:
        function: 1F, 2F, 3F, 4F
        profile_key: sa_4_cap, default
        
    Returns:
        bool: Существует ли файл
    """
    return four_f_loader.validate_function_file(function, profile_key)


# ============================================
# 🐛 ОТЛАДОЧНЫЕ ФУНКЦИИ
# ============================================

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
    
    # Тестируем 4F-функцию
    print("\n🔑 ТЕСТИРУЕМ get_4f_profile_info():")
    test_profiles = ["sa_3_con", "SA_3", "sp_4_val", "ia_2"]
    
    for test_profile in test_profiles:
        info = get_4f_profile_info(test_profile)
        print(f"  {test_profile:12} → {info['display_name']} (уровень {info['level']})")
    
    print("="*60)


def debug_4f_functions():
    """Функция для отладки 4F-функций"""
    four_f_loader.debug_4f_functions()


def debug_all():
    """Полная отладка всех систем"""
    debug_profile_loading()
    debug_4f_functions()


# ============================================
# 🚀 ЗАПУСК ПРИ ПРЯМОМ ВЫПОЛНЕНИИ
# ============================================

if __name__ == "__main__":
    debug_all()
