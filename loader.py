# loader.py - загрузчик профилей для структуры с поддиректориями

import json
import os
import importlib.util
import sys
from collections import defaultdict

class VariaticaProfile:
    """Базовая структура профиля"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class ProfileLoader:
    """Загрузчик профилей с поддержкой поддиректорий"""
    
    def __init__(self):
        self.profiles = {}
        self._load_all_profiles()
    
    def _load_all_profiles(self):
        """Загружает все профили из файлов"""
        base_profile_dir = "профили"  # ваша директория
        
        if not os.path.exists(base_profile_dir):
            print(f"❌ Директория {base_profile_dir} не найдена!")
            return
        
        print(f"🔍 Поиск профилей в {base_profile_dir}")
        
        # Список директорий с типами профилей
        type_dirs = ['sa', 'sp', 'ia', 'ip - адрес']
        
        for type_dir in type_dirs:
            type_path = os.path.join(base_profile_dir, type_dir)
            
            if not os.path.exists(type_path):
                print(f"  ⚠️ Директория {type_dir} не найдена")
                continue
            
            # Определяем реальный код типа
            if type_dir == 'ip - адрес':
                actual_type = 'ip'
            else:
                actual_type = type_dir
            
            print(f"  📁 Загрузка профилей типа {actual_type.upper()}")
            
            # Загружаем все .py файлы в директории
            for filename in os.listdir(type_path):
                if filename.endswith('.py') and filename != '__init__.py':
                    try:
                        filepath = os.path.join(type_path, filename)
                        
                        # Читаем файл
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Парсим профиль
                        profile_data = self._parse_profile_file(content, filename, actual_type)
                        
                        if profile_data:
                            # Создаем ключ: type_level_dilts
                            key = filename.replace('.py', '').lower()
                            
                            # Нормализуем имя типа
                            if actual_type == 'ip':
                                key = key.replace('ip - адрес', 'ip').replace(' ', '')
                            
                            self.profiles[key] = VariaticaProfile(**profile_data)
                            print(f"    ✅ Загружен: {key}")
                            
                    except Exception as e:
                        print(f"    ❌ Ошибка загрузки {filename}: {e}")
    
    def _parse_profile_file(self, content: str, filename: str, profile_type: str) -> dict:
        """Парсит Python файл с профилем"""
        try:
            # Извлекаем переменные из Python файла
            namespace = {}
            
            # Исполняем код файла для получения переменных
            try:
                exec(content, namespace)
            except Exception as e:
                print(f"      ⚠️ Ошибка исполнения {filename}: {e}")
                return self._create_basic_profile(filename, profile_type)
            
            # Извлекаем основные поля
            title = namespace.get('title', f"Профиль {filename.replace('.py', '')}")
            archetype = namespace.get('archetype', f"Архетип {profile_type.upper()}")
            quote = namespace.get('quote', "«Познай себя — и ты познаешь вселенную»")
            trigger = namespace.get('trigger', "ЭТО ТЫ, ЕСЛИ...\n\nОписание триггерного паттерна")
            pain = namespace.get('pain', "СУТЬ ПРОБЛЕМЫ:\n\nОсновная проблема уровня")
            immediate_tool = namespace.get('immediate_tool', "ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:\n\nПервые шаги")
            cta = namespace.get('cta', "ЧТО ДАЛЬШЕ?\n\nДальнейшее развитие")
            
            # Извлекаем уровень и суффикс из имени файла
            name_parts = filename.replace('.py', '').split('_')
            level = 1
            dilts_suffix = 'def'
            
            if len(name_parts) >= 2 and name_parts[1].isdigit():
                level = int(name_parts[1])
            
            if len(name_parts) >= 3:
                dilts_suffix = name_parts[2]
            
            # Собираем все поля из namespace
            profile_data = {
                'title': title,
                'archetype': archetype,
                'quote': quote,
                'trigger': trigger,
                'pain': pain,
                'immediate_tool': immediate_tool,
                'cta': cta,
                'type_code': profile_type,
                'level': level,
                'dilts_suffix': dilts_suffix,
                'profile_name': filename.replace('.py', '')
            }
            
            # Добавляем все остальные переменные
            for key, value in namespace.items():
                if not key.startswith('__') and key not in profile_data:
                    profile_data[key] = value
            
            return profile_data
            
        except Exception as e:
            print(f"      ⚠️ Ошибка парсинга {filename}: {e}")
            return self._create_basic_profile(filename, profile_type)
    
    def _create_basic_profile(self, filename: str, profile_type: str) -> dict:
        """Создает базовый профиль при ошибке парсинга"""
        name_parts = filename.replace('.py', '').split('_')
        level = 1
        if len(name_parts) >= 2 and name_parts[1].isdigit():
            level = int(name_parts[1])
        
        return {
            'title': f"{profile_type.upper()} Уровень {level}",
            'archetype': f"Архетип {profile_type.upper()}",
            'quote': "«Дорогу осилит идущий»",
            'trigger': f"ЭТО ТЫ, ЕСЛИ...\n\nТы находишься на этапе развития {profile_type.upper()} уровня {level}",
            'pain': f"СУТЬ ПРОБЛЕМЫ:\n\nТребуется развитие аспектов уровня {level}",
            'immediate_tool': "ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:\n\n1. Принять текущее состояние\n2. Определить первый шаг\n3. Начать действовать",
            'cta': "ЧТО ДАЛЬШЕ?\n\nПродолжить самопознание и развитие",
            'type_code': profile_type,
            'level': level,
            'profile_name': filename.replace('.py', '')
        }
    
    def get_profile(self, key: str):
        """Получает профиль по ключу"""
        key_lower = key.lower()
        
        # Нормализуем ключ для IP типа
        if 'ip' in key_lower:
            key_lower = key_lower.replace('ip-адрес', 'ip').replace('ip - адрес', 'ip').replace(' ', '')
        
        # Пробуем найти профиль
        if key_lower in self.profiles:
            return self.profiles[key_lower]
        
        # Fallback: ищем похожие ключи
        for profile_key in self.profiles.keys():
            if key_lower in profile_key or profile_key in key_lower:
                print(f"🔀 Fallback: {key_lower} → {profile_key}")
                return self.profiles[profile_key]
        
        # Создаем fallback профиль
        print(f"⚠️ Профиль {key_lower} не найден, создаю fallback")
        return self._create_fallback_profile(key_lower)
    
    def get_all_profiles(self):
        """Возвращает все загруженные профили"""
        return list(self.profiles.keys())
    
    def _create_fallback_profile(self, key: str):
        """Создает fallback профиль"""
        parts = key.split('_')
        type_code = parts[0] if len(parts) > 0 else "sa"
        level = parts[1] if len(parts) > 1 else "1"
        dilts_code = parts[2] if len(parts) > 2 else "def"
        
        # Нормализуем тип для IP
        if type_code == 'ip-адрес' or type_code == 'ip':
            type_code = 'ip'
        
        return VariaticaProfile(
            title=f"{type_code.upper()}_{level}_{dilts_code}",
            archetype=f"Архетип {type_code.upper()}",
            quote="«Знание — сила, а самопознание — сверхсила»",
            trigger=f"🔍 ЭТО ТЫ, ЕСЛИ...\n\nТвой профиль: {type_code.upper()} уровень {level} ({dilts_code})",
            pain=f"💔 СУТЬ ПРОБЛЕМЫ\n\nРабота с конфликтом на уровне {dilts_code}",
            immediate_tool=f"🛠 ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»\n\nИнструменты для работы с паттернами уровня {level}",
            cta=f"🚀 ЧТО ДАЛЬШЕ?\n\nПереход к следующему этапу развития",
            type_code=type_code,
            level=int(level) if level.isdigit() else 1,
            dilts_suffix=dilts_code,
            profile_name=key
        )

# Создаем глобальный экземпляр загрузчика
loader = ProfileLoader()

# Тестируем загрузку
if __name__ == "__main__":
    print(f"\n📊 Загружено профилей: {len(loader.profiles)}")
    print("\n📋 Примеры загруженных профилей:")
    for i, key in enumerate(list(loader.profiles.keys())[:10]):
        print(f"  {i+1}. {key}")
