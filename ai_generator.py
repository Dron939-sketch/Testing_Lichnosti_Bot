#!/usr/bin/env python3
"""
ai_generator.py - Генерация профилей через DeepSeek в стиле Variatica
"""

import os
import json
import time
from typing import Dict, Optional
from openai import OpenAI

class DeepSeekProfileGenerator:
    def __init__(self, cache_dir: str = "generated_profiles"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ OPENAI_API_KEY не найден!")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # База названий для разных типов и уровней
        self.titles = {
            # SP (Силовики)
            "SP_1_def": "Невидимка",
            "SP_2_sit": "Сканер",
            "SP_3_con": "Боец",
            "SP_4_exp": "Страж",
            "SP_5_int": "Мастер",
            "SP_6_aut": "Независимый",
            "SP_7_val": "Хозяин",
            "SP_8_tra": "Командир",
            "SP_9_ide": "Легенда",
            
            # IA (Мыслители)
            "IA_1_def": "Инстинктивный",
            "IA_2_sit": "Коллекционер",
            "IA_3_con": "Скептик",
            "IA_4_exp": "Догматик",
            "IA_5_cap": "Эмпирик",
            "IA_6_aut": "Системщик",
            "IA_7_val": "Учитель",
            "IA_8_tra": "Методолог",
            "IA_9_ide": "Создатель",
            
            # IP (Трудяги)
            "IP_1_def": "Домосед",
            "IP_2_sit": "Исполнитель",
            "IP_3_con": "Рыночник",
            "IP_4_exp": "Самозанятый",
            "IP_5_int": "Организатор",
            "IP_6_aut": "Перекупщик",
            "IP_7_val": "Рантье",
            "IP_8_tra": "Производитель",
            "IP_9_ide": "Создатель рынка",
            
            # SA (Социальные)
            "SA_1_def": "Ищущий внимания",
            "SA_2_sit": "Хамелеон",
            "SA_3_con": "Манипулятор",
            "SA_4_exp": "Сканер",
            "SA_5_int": "Системщик",
            "SA_6_aut": "Решала",
            "SA_7_val": "PR-гуру",
            "SA_8_tra": "Сетевой лидер",
            "SA_9_ide": "Культурный лидер",
        }
        
        # Номера для типов
        self.number_ranges = {
            "SP": (1, 9),
            "IA": (10, 18),
            "SA": (19, 27),
            "IP": (28, 36),
        }
    
    def _get_number(self, profile_type: str) -> int:
        """Возвращает порядковый номер для профиля"""
        parts = profile_type.split('_')
        type_code = parts[0]  # SP, IA, SA, IP
        level = int(parts[1])  # 1-9
        
        start, _ = self.number_ranges.get(type_code, (1, 36))
        return start + level - 1
    
    def generate_profile(self, profile_type: str, force: bool = False) -> Optional[str]:
        """
        Генерирует профиль через DeepSeek
        profile_type: например "IA_3_con", "SP_5_int"
        """
        # Проверяем кэш
        cache_file = os.path.join(self.cache_dir, f"{profile_type}.py")
        if not force and os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Разбираем тип
        parts = profile_type.split('_')
        type_code = parts[0]  # SP, IA, SA, IP
        level = parts[1]      # 1, 2, 3...
        suffix = parts[2]     # def, sit, con...
        
        title = self.titles.get(profile_type, profile_type)
        number = self._get_number(profile_type)
        
        # Формируем промпт
        prompt = f"""Ты — психолог, создающий психологические профили для системы Variatica.

Тебе нужно создать профиль для типа {profile_type} (уровень {level}) в точном стиле примеров ниже.

### ПРИМЕРЫ СТИЛЯ (SP_1_def "Невидимка"):
«Лучше сидеть тихо и быть незаметным, чем высунуться и получить по голове.»
Метафоры: замерзший человек, пожарная сигнализация

### СТРУКТУРА ПРОФИЛЯ:

from ..base import VariaticaProfile

{profile_type.upper()} = VariaticaProfile(
    # === ИДЕНТИФИКАЦИЯ ===
    key="{profile_type.lower()}",
    type_code="{type_code}",
    level={level},
    number={number},
    
    # === ОСНОВНАЯ ИНФОРМАЦИЯ ===
    title='"{title}"',
    archetype="[АРХЕТИП]",
    quote="«[ЦИТАТА]»",
    
    # === TRIGGER (5-7 пунктов) ===
    trigger=\"\"\"ЭТО ТЫ, ЕСЛИ...

• [пункт 1 с конкретной ситуацией и физическим ощущением]
• [пункт 2 с внутренним конфликтом]
• [пункт 3 с парадоксом]
• [пункт 4 с ценой паттерна]
• [пункт 5 с вопросом к себе]\"\",
    
    # === PAIN (4 цены) ===
    pain=\"\"\"СУТЬ ПРОБЛЕМЫ: ЧТО ИДЕТ НЕ ТАК

[Вступление]

<b>Откуда это взялось</b>
[Эволюционный контекст]

<b>Цена 1. [Название]</b>
[Описание]

<b>Цена 2. [Название]</b>
[Описание]

<b>Цена 3. [Название]</b>
[Описание]

<b>Цена 4. [Название]</b>
[Описание]

[Итог]\"\",
    
    # === IMMEDIATE TOOL (5 шагов) ===
    immediate_tool=\"\"\"ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»: [НАЗВАНИЕ]

[Введение]

<b>Шаг 1. [Действие]</b>
[Описание]

<b>Шаг 2. [Действие]</b>
[Описание]

<b>Шаг 3. [Действие]</b>
[Описание]

<b>Шаг 4. [Действие]</b>
[Описание]

<b>Шаг 5. [Действие]</b>
[Описание]\"\",
    
    # === CTA (5 пунктов) ===
    cta=\"\"\"ЧТО ДАЛЬШЕ?

[Вступление]

В полной версии ты узнаешь:

• <b>[Тема 1]:</b> [Описание]
• <b>[Тема 2]:</b> [Описание]
• <b>[Тема 3]:</b> [Описание]
• <b>[Тема 4]:</b> [Описание]
• <b>[Тема 5]:</b> [Описание]

[Финальная фраза]\"\"
)

### КЛЮЧЕВЫЕ ТРЕБОВАНИЯ:
1. Метафоры — яркие образы
2. Физические ощущения — что в теле
3. Прямое обращение — на "ты"
4. Парадоксы — защита как ловушка
5. Эволюционный контекст — почему так вышло
6. 4 цены в pain
7. 5-7 пунктов в trigger
8. 5 шагов в immediate_tool
9. 5 пунктов в cta

Сгенерируй профиль строго по этой структуре. Только код Python, без пояснений."""
        
        try:
            print(f"🤖 Генерация профиля {profile_type}...")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Ты создаешь психологические профили в формате Python."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=4000
            )
            
            code = response.choices[0].message.content
            
            # Очищаем от возможных маркдаунов
            if code.startswith('```python'):
                code = code[9:]
            if code.endswith('```'):
                code = code[:-3]
            
            # Сохраняем в кэш
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"✅ Профиль {profile_type} сгенерирован")
            return code
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

# Тест
if __name__ == "__main__":
    generator = DeepSeekProfileGenerator()
    
    # Генерируем тестовый профиль
    code = generator.generate_profile("IA_3_con")
    if code:
        print(code[:500] + "...")
