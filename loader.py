# loader.py - заглушка для загрузки профилей

import json
import os
from collections import defaultdict

class VariaticaProfile:
    """Базовая структура профиля"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class ProfileLoader:
    """Загрузчик профилей"""
    
    def __init__(self):
        self.profiles = {}
        self._load_all_profiles()
    
    def _load_all_profiles(self):
        """Загружает все профили из файлов"""
        profile_dir = "profiles"
        
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            print(f"⚠️ Директория {profile_dir} создана. Добавьте туда файлы профилей.")
            return
        
        # Чтение всех .py файлов в директории profiles
        for filename in os.listdir(profile_dir):
            if filename.endswith('.py'):
                try:
                    # Простой парсинг Python файла
                    with open(os.path.join(profile_dir, filename), 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Извлекаем данные из файла
                    profile_data = self._parse_profile_file(content, filename)
                    
                    if profile_data:
                        key = filename.replace('.py', '').lower()
                        self.profiles[key] = VariaticaProfile(**profile_data)
                        
                except Exception as e:
                    print(f"Ошибка загрузки {filename}: {e}")
    
    def _parse_profile_file(self, content: str, filename: str) -> dict:
        """Парсит Python файл с профилем"""
        try:
            # Простой парсинг для демо
            profile_data = {
                'title': f"Профиль {filename.replace('.py', '')}",
                'archetype': f"Архетип {filename.split('_')[0].upper()}",
                'quote': "Цитата для примера...",
                'trigger': "ЭТО ТЫ, ЕСЛИ...\n\nТвой триггерный паттерн",
                'pain': "СУТЬ ПРОБЛЕМЫ:\n\nОсновная проблема твоего типа",
                'immediate_tool': "ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:\n\nПервые шаги",
                'cta': "ЧТО ДАЛЬШЕ?\n\nДальнейшие действия",
            }
            return profile_data
        except:
            return None
    
    def get_profile(self, key: str):
        """Получает профиль по ключу"""
        key_lower = key.lower()
        return self.profiles.get(key_lower, self._create_fallback_profile(key_lower))
    
    def get_all_profiles(self):
        """Возвращает все загруженные профили"""
        return list(self.profiles.keys())
    
    def _create_fallback_profile(self, key: str):
        """Создает fallback профиль"""
        parts = key.split('_')
        type_code = parts[0] if len(parts) > 0 else "sa"
        level = parts[1] if len(parts) > 1 else "1"
        
        return VariaticaProfile(
            title=f"Профиль {key.upper()}",
            archetype=f"Архетип {type_code.upper()}",
            quote="Каждый человек — уникальная конфигурация...",
            trigger=f"ЭТО ТЫ, ЕСЛИ...\n\nТы находишься на уровне {level} типа {type_code.upper()}",
            pain="СУТЬ ПРОБЛЕМЫ:\n\nБазовые потребности не удовлетворены",
            immediate_tool="ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:\n\n1. Осознать текущее состояние\n2. Принять себя\n3. Наметить первый шаг",
            cta="ЧТО ДАЛЬШЕ?\n\nПройти полную диагностику и получить персонализированные рекомендации",
            type_code=type_code,
            level=int(level) if level.isdigit() else 1
        )

# Создаем глобальный экземпляр загрузчика
loader = ProfileLoader()
