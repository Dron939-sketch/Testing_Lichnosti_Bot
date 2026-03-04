#!/usr/bin/env python3
"""
ai_personalized.py - Персонализированная генерация профилей через DeepSeek
Учитывает конкретные ответы пользователя для создания уникального профиля
"""

import os
import json
import time
import re
from typing import Dict, List, Optional, Any
from collections import Counter
from openai import OpenAI

class PersonalizedProfileGenerator:
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
        
        # База названий для разных типов
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
        type_code = parts[0]
        level = int(parts[1])
        start, _ = self.number_ranges.get(type_code, (1, 36))
        return start + level - 1
    
    def extract_themes_from_answers(self, answers: List[Dict]) -> Dict[str, Any]:
        """
        Извлекает ключевые темы и паттерны из ответов пользователя
        """
        if not answers:
            return {}
        
        themes = {
            "key_words": [],
            "emotional_triggers": [],
            "fears": [],
            "desires": [],
            "contradictions": [],
            "answer_count": len(answers)
        }
        
        # Словари для поиска тем
        fear_words = ['боюсь', 'страх', 'опасно', 'боязно', 'тревога', 'напряжение']
        desire_words = ['хочу', 'мечтаю', 'желаю', 'нравится', 'люблю']
        emotion_words = ['злюсь', 'радуюсь', 'грущу', 'тоска', 'одиночество']
        
        all_text = ""
        for a in answers:
            answer_text = a.get('answer', '').lower()
            question_text = a.get('question', '').lower()
            all_text += " " + answer_text
            
            # Ищем страхи
            for word in fear_words:
                if word in answer_text or word in question_text:
                    themes["fears"].append(word)
            
            # Ищем желания
            for word in desire_words:
                if word in answer_text or word in question_text:
                    themes["desires"].append(word)
            
            # Ищем эмоции
            for word in emotion_words:
                if word in answer_text or word in question_text:
                    themes["emotional_triggers"].append(word)
        
        # Находим самые частые слова (простейший анализ)
        words = re.findall(r'\b\w{4,}\b', all_text)
        word_counts = Counter(words)
        themes["key_words"] = [w for w, c in word_counts.most_common(10) if c > 1]
        
        return themes
    
    def generate_personalized_profile(self, 
                                      profile_type: str, 
                                      user_answers: List[Dict],
                                      user_name: str = "Пользователь",
                                      force: bool = False) -> Optional[str]:
        """
        Генерирует персонализированный профиль на основе ответов
        """
        # Разбираем тип
        parts = profile_type.split('_')
        type_code = parts[0]
        level = parts[1]
        
        title = self.titles.get(profile_type, profile_type)
        number = self._get_number(profile_type)
        
        # Анализируем ответы
        themes = self.extract_themes_from_answers(user_answers)
        
        # Формируем описание паттернов для AI
        patterns_desc = ""
        if themes:
            patterns_desc = f"""
### АНАЛИЗ ОТВЕТОВ ПОЛЬЗОВАТЕЛЯ:
- Ключевые слова: {', '.join(themes['key_words'][:5])}
- Страхи: {', '.join(set(themes['fears']))}
- Желания: {', '.join(set(themes['desires']))}
- Эмоциональные триггеры: {', '.join(set(themes['emotional_triggers']))}
- Всего ответов: {themes['answer_count']}
"""
        
        # Формируем промпт с персонализацией
        prompt = f"""Ты — психолог, создающий психологические профили для системы Variatica.

Тебе нужно создать ПЕРСОНАЛИЗИРОВАННЫЙ профиль для типа {profile_type} (уровень {level}).

{patterns_desc}

УЧТИ ЭТИ ОТВЕТЫ В ПРОФИЛЕ:
- Используй ключевые слова из ответов в описаниях
- Усиль темы, которые видны в ответах
- Добавь конкретные примеры, похожие на ситуации из ответов
- Сделай профиль уникальным для этого человека

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
    quote="«[ЦИТАТА, отражающая суть]»",
    
    # === TRIGGER (5-7 пунктов) ===
    trigger=\"\"\"ЭТО ТЫ, ЕСЛИ...

* [пункт 1 с ситуацией, похожей на ответы пользователя]
* [пункт 2 с физическим ощущением]
* [пункт 3 с внутренним конфликтом]
* [пункт 4 с парадоксом]
* [пункт 5 с вопросом к себе]\"\",
    
    # === PAIN (4 цены) ===
    pain=\"\"\"СУТЬ ПРОБЛЕМЫ: ЧТО ИДЕТ НЕ ТАК

[Вступление, отражающее ключевые темы из ответов]

<b>Откуда это взялось</b>
[Эволюционный контекст]

<b>Цена 1. [Название, связанное с ответами]</b>
[Описание]

<b>Цена 2. [Название]</b>
[Описание]

<b>Цена 3. [Название]</b>
[Описание]

<b>Цена 4. [Название]</b>
[Описание]

[Итог]\"\",
    
    # === IMMEDIATE TOOL (5 шагов) ===
    immediate_tool=\"\"\"ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»: [НАЗВАНИЕ, связанное с проблемой]

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

* <b>[Тема 1, связанная с ответами]:</b> [Описание]
* <b>[Тема 2]:</b> [Описание]
* <b>[Тема 3]:</b> [Описание]
* <b>[Тема 4]:</b> [Описание]
* <b>[Тема 5]:</b> [Описание]

[Финальная фраза, вдохновляющая]\"\"
)

### КЛЮЧЕВЫЕ ТРЕБОВАНИЯ:
1. Метафоры — яркие образы
2. Физические ощущения — что в теле
3. Прямое обращение — на "ты"
4. Парадоксы — защита как ловушка
5. 4 цены в pain
6. 5-7 пунктов в trigger
7. 5 шагов в immediate_tool
8. 5 пунктов в cta
9. **ОБЯЗАТЕЛЬНО** использовать ключевые слова из ответов
10. Добавлять примеры, похожие на ситуации из ответов

Сгенерируй профиль строго по этой структуре. Только код Python, без пояснений."""
        
        try:
            print(f"🤖 Генерация персонализированного профиля {profile_type}...")
            print(f"📊 Анализ ответов: {len(user_answers)} ответов, ключевые темы: {themes.get('key_words', [])[:3]}")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Ты создаешь персонализированные психологические профили."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=4000
            )
            
            code = response.choices[0].message.content
            
            # Очищаем от маркдаунов
            if code.startswith('```python'):
                code = code[9:]
            if code.endswith('```'):
                code = code[:-3]
            
            # Сохраняем с уникальным именем
            timestamp = int(time.time())
            cache_file = os.path.join(self.cache_dir, f"{profile_type}_{timestamp}.py")
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"✅ Персонализированный профиль сохранён в {cache_file}")
            return code
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

# Тест
if __name__ == "__main__":
    generator = PersonalizedProfileGenerator()
    
    # Тестовые ответы (для примера)
    test_answers = [
        {
            'stage': 1,
            'question': 'Что вы чувствуете в конфликте?',
            'answer': 'Я всегда боюсь, что меня обманут. Лучше сразу никому не верить.',
            'option': 'a'
        },
        {
            'stage': 2,
            'question': 'Как вы относитесь к людям?',
            'answer': 'Мне кажется, все хотят меня использовать. Я постоянно настороже.',
            'option': 'b'
        },
        {
            'stage': 3,
            'question': 'Что для вас самое важное?',
            'answer': 'Быть в безопасности. Никому не доверять.',
            'option': 'c'
        }
    ]
    
    # Генерируем
    code = generator.generate_personalized_profile(
        profile_type="IA_3_con",
        user_answers=test_answers,
        user_name="Тестовый пользователь"
    )
    
    if code:
        print("\n" + "="*60)
        print("✅ ПЕРСОНАЛИЗИРОВАННЫЙ ПРОФИЛЬ:")
        print("="*60)
        print(code[:500] + "...")
