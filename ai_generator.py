#!/usr/bin/env python3
"""
ai_generator.py - Генерация профилей через DeepSeek в нужном стиле
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional
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
        print(f"✅ DeepSeek генератор инициализирован")
    
    def _load_from_cache(self, profile_type: str) -> Optional[str]:
        """Загружает из кэша"""
        cache_file = os.path.join(self.cache_dir, f"{profile_type}.py")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def _save_to_cache(self, profile_type: str, content: str):
        """Сохраняет в кэш"""
        cache_file = os.path.join(self.cache_dir, f"{profile_type}.py")
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def generate_profile(self, profile_type: str, force: bool = False) -> str:
        """
        Генерирует профиль в нужном стиле
        Возвращает готовый Python код
        """
        # Проверяем кэш
        if not force:
            cached = self._load_from_cache(profile_type)
            if cached:
                print(f"📦 Загружено из кэша: {profile_type}")
                return cached
        
        print(f"🤖 Генерация профиля {profile_type}...")
        
        # Определяем тип и уровень
        parts = profile_type.split('_')
        type_code = parts[0].upper()  # IA
        level = parts[1]  # 3
        suffix = parts[2]  # con
        
        # Маппинг названий
        titles = {
            "IA_3_con": "Скептик",
            "IA_3_beh": "Алхимик лжи",
            "IA_4_cap": "Хранитель карты",
            # Добавьте другие
        }
        
        title = titles.get(profile_type, profile_type)
        
        prompt = f"""Ты — психолог, создающий психологические профили для системы Variatica.

Сгенерируй профиль для типа {profile_type} (уровень {level}) в точном стиле примера ниже.

ВАЖНЫЕ ТРЕБОВАНИЯ К СТИЛЮ:
1. Метафоры — использовать образы (микроскоп, скальпель, окоп, клетка)
2. Физические ощущения — описывать, что в теле (холод, напряжение, тяжесть)
3. Прямое обращение на "ты"
4. Парадоксы — "дар и ловушка", "защита как клетка"
5. 4 цены в блоке pain
6. 5-7 пунктов в trigger
7. 4 шага в immediate_tool
8. 5 пунктов в cta

Верни ТОЛЬКО Python код, начинающийся с:
from ..base import VariaticaProfile

{profile_type.upper()} = VariaticaProfile(
    # === ИДЕНТИФИКАЦИЯ ===
    key="{profile_type.lower()}",
    type_code="{type_code}",
    level={level},
    number=21,  # примерный номер
    
    # === ОСНОВНАЯ ИНФОРМАЦИЯ ===
    title='"{title}"',
    archetype="[АРХЕТИП]",
    quote="«[ЦИТАТА]»",
    
    # === БЛОКИ ПРОФИЛЯ ===
    trigger="""ЭТО ТЫ, ЕСЛИ...
• [пункт 1]
• [пункт 2]
• [пункт 3]
• [пункт 4]
• [пункт 5]""",
    
    pain="""СУТЬ ПРОБЛЕМЫ: ЧТО ИДЕТ НЕ ТАК

[текст]

<b>Откуда это взялось</b>
[текст]

<b>Цена 1. [Название]</b>
[текст]

<b>Цена 2. [Название]</b>
[текст]

<b>Цена 3. [Название]</b>
[текст]

<b>Цена 4. [Название]</b>
[текст]

[итог]""",
    
    immediate_tool="""ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»: [НАЗВАНИЕ]

[текст]

<b>Шаг 1. [Действие]</b>
[текст]

<b>Шаг 2. [Действие]</b>
[текст]

<b>Шаг 3. [Действие]</b>
[текст]

<b>Шаг 4. [Действие]</b>
[текст]""",
    
    cta="""ЧТО ДАЛЬШЕ?

[текст]

В полной версии ты узнаешь:

• <b>[Тема 1]:</b> [текст]
• <b>[Тема 2]:</b> [текст]
• <b>[Тема 3]:</b> [текст]
• <b>[Тема 4]:</b> [текст]
• <b>[Тема 5]:</b> [текст]

[финал]"""
)"""
        
        try:
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
            
            # Очищаем от возможных маркдеров
            if code.startswith('```python'):
                code = code[9:]
            if code.endswith('```'):
                code = code[:-3]
            
            # Сохраняем в кэш
            self._save_to_cache(profile_type, code)
            print(f"✅ Профиль {profile_type} сгенерирован")
            
            return code
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return ""

# Тест
if __name__ == "__main__":
    generator = DeepSeekProfileGenerator()
    code = generator.generate_profile("IA_3_con")
    print(code)
