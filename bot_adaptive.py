# bot_adaptive.py
"""
Telegram-бот для адаптивного психологического тестирования
Версия: 3.0 (с интеграцией готовых профилей из card_data.py)
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Импорт готовых профилей
from card_data import get_profile_description, check_all_profiles_exist

# Импорт генератора контента (для fallback)
from content_generator import generate_profile

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
(STAGE_1_INTRO, STAGE_1_QUESTIONS,
 STAGE_2_INTRO, STAGE_2_QUESTIONS,
 STAGE_3_INTRO, STAGE_3_QUESTIONS,
 STAGE_4_INTRO, STAGE_4_QUESTIONS) = range(8)

# Константы для типов мышления
TYPE_CODES = {
    "SA": "Социально-аффилиативный",
    "IA": "Экзистенциально-рефлексивный", 
    "SP": "Инструментально-достиженческий",
    "IP": "Структурно-аналитический"
}

# Константы для уровней Дилтса (5 уровней, без MISSION)
DILTS_LEVELS = {
    "ENVIRONMENT": {"code": "env", "name": "Окружение"},
    "BEHAVIOR": {"code": "beh", "name": "Поведение"},
    "CAPABILITIES": {"code": "cap", "name": "Способности"},
    "VALUES": {"code": "val", "name": "Ценности"},
    "IDENTITY": {"code": "ide", "name": "Идентичность"}
}

def get_dilts_code(level_name: str) -> str:
    """Получить код уровня Дилтса"""
    return DILTS_LEVELS.get(level_name, {}).get("code", "env")

# ========================================
# ВОПРОСЫ ДЛЯ ЭТАПА 1 (Определение типа)
# ========================================

STAGE_1_QUESTIONS = [
    {
        "id": 1,
        "text": """
🎯 **Вопрос 1 из 10**

Представьте: вы столкнулись со сложной проблемой на работе.

**Что для вас важнее всего?**
""",
        "options": [
            {"text": "Найти людей, которые помогут решить", "scores": {"SA": 2}},
            {"text": "Понять глубинную суть проблемы", "scores": {"IA": 2}},
            {"text": "Быстро найти работающее решение", "scores": {"SP": 2}},
            {"text": "Разработать системный подход", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 2,
        "text": """
🎯 **Вопрос 2 из 10**

Вы получили повышение и новую должность.

**Что вас больше всего мотивирует?**
""",
        "options": [
            {"text": "Новый статус и признание коллег", "scores": {"SA": 2}},
            {"text": "Возможность реализовать свои идеи", "scores": {"IA": 2}},
            {"text": "Больше власти и ресурсов", "scores": {"SP": 2}},
            {"text": "Более сложные задачи и проекты", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 3,
        "text": """
🎯 **Вопрос 3 из 10**

В команде возник конфликт между двумя сотрудниками.

**Как вы поступите?**
""",
        "options": [
            {"text": "Поговорю с каждым, помогу найти компромисс", "scores": {"SA": 2}},
            {"text": "Разберусь в причинах конфликта", "scores": {"IA": 2}},
            {"text": "Приму решение и потребую выполнения", "scores": {"SP": 2}},
            {"text": "Создам процедуру решения конфликтов", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 4,
        "text": """
🎯 **Вопрос 4 из 10**

Вам предложили возглавить новый проект.

**Что вы сделаете в первую очередь?**
""",
        "options": [
            {"text": "Соберу команду единомышленников", "scores": {"SA": 2}},
            {"text": "Изучу аналогичные проекты и подходы", "scores": {"IA": 2}},
            {"text": "Определю цели и начну действовать", "scores": {"SP": 2}},
            {"text": "Разработаю план и структуру проекта", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 5,
        "text": """
🎯 **Вопрос 5 из 10**

Вы заметили, что ваш подход к работе отличается от принятого.

**Как вы отреагируете?**
""",
        "options": [
            {"text": "Адаптируюсь к общепринятому стилю", "scores": {"SA": 2}},
            {"text": "Попытаюсь понять, почему так принято", "scores": {"IA": 2}},
            {"text": "Докажу эффективность своего подхода", "scores": {"SP": 2}},
            {"text": "Проанализирую плюсы и минусы обоих", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 6,
        "text": """
🎯 **Вопрос 6 из 10**

Компания переживает кризис.

**Что для вас важнее всего?**
""",
        "options": [
            {"text": "Сохранить команду и отношения", "scores": {"SA": 2}},
            {"text": "Понять причины и извлечь уроки", "scores": {"IA": 2}},
            {"text": "Быстро стабилизировать ситуацию", "scores": {"SP": 2}},
            {"text": "Реорганизовать процессы", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 7,
        "text": """
🎯 **Вопрос 7 из 10**

Вам нужно принять важное решение в условиях неопределенности.

**На что вы опираетесь?**
""",
        "options": [
            {"text": "Мнение людей, которым доверяю", "scores": {"SA": 2}},
            {"text": "Интуицию и внутреннее понимание", "scores": {"IA": 2}},
            {"text": "Опыт и проверенные методы", "scores": {"SP": 2}},
            {"text": "Анализ данных и логику", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 8,
        "text": """
🎯 **Вопрос 8 из 10**

Вы достигли значительного успеха.

**Что вы чувствуете в первую очередь?**
""",
        "options": [
            {"text": "Радость от признания окружающих", "scores": {"SA": 2}},
            {"text": "Удовлетворение от реализации идеи", "scores": {"IA": 2}},
            {"text": "Гордость от достижения цели", "scores": {"SP": 2}},
            {"text": "Удовлетворение от качества работы", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 9,
        "text": """
🎯 **Вопрос 9 из 10**

Вам предстоит выступление перед большой аудиторией.

**О чем вы думаете?**
""",
        "options": [
            {"text": "Как установить контакт с аудиторией", "scores": {"SA": 2}},
            {"text": "Как донести главную идею", "scores": {"IA": 2}},
            {"text": "Как убедить и повлиять на решения", "scores": {"SP": 2}},
            {"text": "Как структурировать информацию", "scores": {"IP": 2}}
        ]
    },
    {
        "id": 10,
        "text": """
🎯 **Вопрос 10 из 10**

Вы размышляете о своей карьере через 5 лет.

**Что вы видите?**
""",
        "options": [
            {"text": "Сильную команду и широкую сеть контактов", "scores": {"SA": 2}},
            {"text": "Реализацию своих идей и проектов", "scores": {"IA": 2}},
            {"text": "Высокую должность и влияние", "scores": {"SP": 2}},
            {"text": "Экспертность и профессионализм", "scores": {"IP": 2}}
        ]
    }
]

# ========================================
# ВОПРОСЫ ДЛЯ ЭТАПА 2 (Уточнение типа)
# ========================================

STAGE_2_QUESTIONS = {
    "SA": [
        {
            "id": 1,
            "text": """
🎯 **Уточняющий вопрос 1 из 5**

В социальных ситуациях вы чаще:
""",
            "options": [
                {"text": "Адаптируетесь к настроению группы", "scores": {"SA": 2, "IA": 0}},
                {"text": "Пытаетесь понять мотивы людей", "scores": {"SA": 0, "IA": 2}}
            ]
        },
        {
            "id": 2,
            "text": """
🎯 **Уточняющий вопрос 2 из 5**

Когда вы помогаете другим:
""",
            "options": [
                {"text": "Важно получить благодарность и признание", "scores": {"SA": 2, "IA": 0}},
                {"text": "Важно понять, действительно ли помог", "scores": {"SA": 0, "IA": 2}}
            ]
        },
        {
            "id": 3,
            "text": """
🎯 **Уточняющий вопрос 3 из 5**

В конфликте вы склонны:
""",
            "options": [
                {"text": "Искать компромисс, сохранять отношения", "scores": {"SA": 2, "IA": 0}},
                {"text": "Разбираться в причинах разногласий", "scores": {"SA": 0, "IA": 2}}
            ]
        },
        {
            "id": 4,
            "text": """
🎯 **Уточняющий вопрос 4 из 5**

Ваша мотивация в работе:
""",
            "options": [
                {"text": "Признание коллег и руководства", "scores": {"SA": 2, "IA": 0}},
                {"text": "Интересные задачи и саморазвитие", "scores": {"SA": 0, "IA": 2}}
            ]
        },
        {
            "id": 5,
            "text": """
🎯 **Уточняющий вопрос 5 из 5**

При принятии решений вы:
""",
            "options": [
                {"text": "Учитываете мнение окружающих", "scores": {"SA": 2, "IA": 0}},
                {"text": "Полагаетесь на свой анализ", "scores": {"SA": 0, "IA": 2}}
            ]
        }
    ],
    "SP": [
        {
            "id": 1,
            "text": """
🎯 **Уточняющий вопрос 1 из 5**

В работе вы предпочитаете:
""",
            "options": [
                {"text": "Быстро достигать результата", "scores": {"SP": 2, "IP": 0}},
                {"text": "Тщательно планировать процесс", "scores": {"SP": 0, "IP": 2}}
            ]
        },
        {
            "id": 2,
            "text": """
🎯 **Уточняющий вопрос 2 из 5**

Когда возникает проблема:
""",
            "options": [
                {"text": "Действую решительно и быстро", "scores": {"SP": 2, "IP": 0}},
                {"text": "Анализирую и ищу оптимальное решение", "scores": {"SP": 0, "IP": 2}}
            ]
        },
        {
            "id": 3,
            "text": """
🎯 **Уточняющий вопрос 3 из 5**

Ваш подход к целям:
""",
            "options": [
                {"text": "Главное - достичь цели любым путем", "scores": {"SP": 2, "IP": 0}},
                {"text": "Важен не только результат, но и метод", "scores": {"SP": 0, "IP": 2}}
            ]
        },
        {
            "id": 4,
            "text": """
🎯 **Уточняющий вопрос 4 из 5**

В команде вы:
""",
            "options": [
                {"text": "Беру инициативу и веду за собой", "scores": {"SP": 2, "IP": 0}},
                {"text": "Организую процессы и координирую", "scores": {"SP": 0, "IP": 2}}
            ]
        },
        {
            "id": 5,
            "text": """
🎯 **Уточняющий вопрос 5 из 5**

Ваше отношение к правилам:
""",
            "options": [
                {"text": "Правила можно нарушить ради цели", "scores": {"SP": 2, "IP": 0}},
                {"text": "Правила важны для эффективности", "scores": {"SP": 0, "IP": 2}}
            ]
        }
    ]
}

# Копируем вопросы для других типов
STAGE_2_QUESTIONS["IA"] = STAGE_2_QUESTIONS["SA"]
STAGE_2_QUESTIONS["IP"] = STAGE_2_QUESTIONS["SP"]

# ========================================
# ВОПРОСЫ ДЛЯ ЭТАПА 3 (Определение уровня мышления)
# ========================================

STAGE_3_QUESTIONS = [
    {
        "id": 1,
        "text": """
🎯 **Вопрос 1 из 10**

Когда вы сталкиваетесь с новой задачей:
""",
        "options": [
            {"text": "Жду указаний, что делать", "level": 1},
            {"text": "Ищу похожие примеры", "level": 3},
            {"text": "Анализирую и планирую", "level": 5},
            {"text": "Вижу системные связи", "level": 7},
            {"text": "Создаю новые подходы", "level": 9}
        ]
    },
    {
        "id": 2,
        "text": """
🎯 **Вопрос 2 из 10**

Ваше понимание причин проблем:
""",
        "options": [
            {"text": "Виновато окружение/обстоятельства", "level": 1},
            {"text": "Дело в конкретных действиях", "level": 3},
            {"text": "Не хватает навыков/знаний", "level": 5},
            {"text": "Проблема в системе ценностей", "level": 7},
            {"text": "Вопрос идентичности и смысла", "level": 9}
        ]
    },
    {
        "id": 3,
        "text": """
🎯 **Вопрос 3 из 10**

Как вы учитесь новому:
""",
        "options": [
            {"text": "Повторяю за другими", "level": 2},
            {"text": "Пробую разные способы", "level": 4},
            {"text": "Изучаю теорию и практику", "level": 6},
            {"text": "Создаю свою методологию", "level": 8},
            {"text": "Переосмысливаю основы", "level": 9}
        ]
    },
    {
        "id": 4,
        "text": """
🎯 **Вопрос 4 из 10**

Ваш подход к планированию:
""",
        "options": [
            {"text": "Живу одним днем", "level": 1},
            {"text": "Планирую на неделю вперед", "level": 3},
            {"text": "Ставлю цели на месяцы", "level": 5},
            {"text": "Выстраиваю стратегию на годы", "level": 7},
            {"text": "Думаю о наследии и смысле", "level": 9}
        ]
    },
    {
        "id": 5,
        "text": """
🎯 **Вопрос 5 из 10**

Как вы принимаете решения:
""",
        "options": [
            {"text": "Спрашиваю совета у других", "level": 2},
            {"text": "Опираюсь на опыт", "level": 4},
            {"text": "Взвешиваю все факторы", "level": 6},
            {"text": "Учитываю долгосрочные последствия", "level": 8},
            {"text": "Следую внутренним принципам", "level": 9}
        ]
    },
    {
        "id": 6,
        "text": """
🎯 **Вопрос 6 из 10**

Ваше отношение к ошибкам:
""",
        "options": [
            {"text": "Боюсь ошибиться", "level": 1},
            {"text": "Учусь на ошибках", "level": 3},
            {"text": "Анализирую причины", "level": 5},
            {"text": "Вижу ошибки как часть процесса", "level": 7},
            {"text": "Переосмысливаю сам подход", "level": 9}
        ]
    },
    {
        "id": 7,
        "text": """
🎯 **Вопрос 7 из 10**

Как вы видите свое развитие:
""",
        "options": [
            {"text": "Хочу стабильности", "level": 1},
            {"text": "Осваиваю новые навыки", "level": 3},
            {"text": "Развиваю компетенции", "level": 5},
            {"text": "Меняю мировоззрение", "level": 7},
            {"text": "Ищу свое предназначение", "level": 9}
        ]
    },
    {
        "id": 8,
        "text": """
🎯 **Вопрос 8 из 10**

Ваше понимание успеха:
""",
        "options": [
            {"text": "Выжить и не потерять", "level": 2},
            {"text": "Достичь конкретных целей", "level": 4},
            {"text": "Стать профессионалом", "level": 6},
            {"text": "Реализовать потенциал", "level": 8},
            {"text": "Найти смысл жизни", "level": 9}
        ]
    },
    {
        "id": 9,
        "text": """
🎯 **Вопрос 9 из 10**

Как вы относитесь к изменениям:
""",
        "options": [
            {"text": "Сопротивляюсь изменениям", "level": 1},
            {"text": "Адаптируюсь к изменениям", "level": 3},
            {"text": "Управляю изменениями", "level": 5},
            {"text": "Инициирую изменения", "level": 7},
            {"text": "Создаю парадигмальные сдвиги", "level": 9}
        ]
    },
    {
        "id": 10,
        "text": """
🎯 **Вопрос 10 из 10**

Ваше мышление о будущем:
""",
        "options": [
            {"text": "Боюсь будущего", "level": 1},
            {"text": "Планирую ближайшие шаги", "level": 3},
            {"text": "Выстраиваю карьеру", "level": 5},
            {"text": "Создаю свое будущее", "level": 7},
            {"text": "Думаю о наследии человечеству", "level": 9}
        ]
    }
]

# ========================================
# ВОПРОСЫ ДЛЯ ЭТАПА 4 (Определение уровня проблемы по Дилтсу)
# ========================================

STAGE_4_QUESTIONS = [
    {
        "id": 1,
        "text": """
🎯 **Вопрос 1 из 8**

Где вы чувствуете основную проблему:
""",
        "options": [
            {"text": "В месте, где я нахожусь", "dilts": "ENVIRONMENT"},
            {"text": "В том, что я делаю", "dilts": "BEHAVIOR"},
            {"text": "В моих навыках и знаниях", "dilts": "CAPABILITIES"},
            {"text": "В моих ценностях и убеждениях", "dilts": "VALUES"},
            {"text": "В понимании себя", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 2,
        "text": """
🎯 **Вопрос 2 из 8**

Что мешает вам больше всего:
""",
        "options": [
            {"text": "Неподходящее окружение", "dilts": "ENVIRONMENT"},
            {"text": "Неправильные действия", "dilts": "BEHAVIOR"},
            {"text": "Недостаток компетенций", "dilts": "CAPABILITIES"},
            {"text": "Внутренние противоречия", "dilts": "VALUES"},
            {"text": "Непонимание своего пути", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 3,
        "text": """
🎯 **Вопрос 3 из 8**

Если бы вы могли изменить что-то одно:
""",
        "options": [
            {"text": "Сменил бы место/людей вокруг", "dilts": "ENVIRONMENT"},
            {"text": "Изменил бы свое поведение", "dilts": "BEHAVIOR"},
            {"text": "Развил бы новые навыки", "dilts": "CAPABILITIES"},
            {"text": "Пересмотрел бы приоритеты", "dilts": "VALUES"},
            {"text": "Понял бы, кто я на самом деле", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 4,
        "text": """
🎯 **Вопрос 4 из 8**

Ваша главная трудность:
""",
        "options": [
            {"text": "Не та среда/условия", "dilts": "ENVIRONMENT"},
            {"text": "Не могу заставить себя действовать", "dilts": "BEHAVIOR"},
            {"text": "Не знаю, как это сделать", "dilts": "CAPABILITIES"},
            {"text": "Не понимаю, зачем мне это", "dilts": "VALUES"},
            {"text": "Не знаю, мое ли это", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 5,
        "text": """
🎯 **Вопрос 5 из 8**

Когда вы думаете о проблеме:
""",
        "options": [
            {"text": "Виню обстоятельства", "dilts": "ENVIRONMENT"},
            {"text": "Виню свои действия", "dilts": "BEHAVIOR"},
            {"text": "Виню недостаток навыков", "dilts": "CAPABILITIES"},
            {"text": "Виню свои убеждения", "dilts": "VALUES"},
            {"text": "Виню неправильный выбор пути", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 6,
        "text": """
🎯 **Вопрос 6 из 8**

Что бы решило вашу проблему:
""",
        "options": [
            {"text": "Другое место/окружение", "dilts": "ENVIRONMENT"},
            {"text": "Изменение привычек", "dilts": "BEHAVIOR"},
            {"text": "Обучение и практика", "dilts": "CAPABILITIES"},
            {"text": "Переоценка ценностей", "dilts": "VALUES"},
            {"text": "Поиск себя", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 7,
        "text": """
🎯 **Вопрос 7 из 8**

Ваш внутренний диалог:
""",
        "options": [
            {"text": "Здесь невозможно...", "dilts": "ENVIRONMENT"},
            {"text": "Я делаю что-то не так...", "dilts": "BEHAVIOR"},
            {"text": "Я не умею...", "dilts": "CAPABILITIES"},
            {"text": "Мне это не нужно...", "dilts": "VALUES"},
            {"text": "Это не мое...", "dilts": "IDENTITY"}
        ]
    },
    {
        "id": 8,
        "text": """
🎯 **Вопрос 8 из 8**

Что вас больше всего беспокоит:
""",
        "options": [
            {"text": "Где я нахожусь", "dilts": "ENVIRONMENT"},
            {"text": "Что я делаю", "dilts": "BEHAVIOR"},
            {"text": "Что я могу/не могу", "dilts": "CAPABILITIES"},
            {"text": "Во что я верю", "dilts": "VALUES"},
            {"text": "Кто я", "dilts": "IDENTITY"}
        ]
    }
]

# ========================================
# ФУНКЦИИ РАСЧЕТА РЕЗУЛЬТАТОВ
# ========================================

def calculate_type_scores(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    """Подсчет баллов по типам мышления"""
    scores = {"SA": 0, "IA": 0, "SP": 0, "IP": 0}
    
    stage1_answers = context.user_data.get('stage1_answers', {})
    stage2_answers = context.user_data.get('stage2_answers', {})
    
    # Подсчет баллов из этапа 1
    for answer in stage1_answers.values():
        for type_code, score in answer.items():
            scores[type_code] += score
    
    # Подсчет баллов из этапа 2
    for answer in stage2_answers.values():
        for type_code, score in answer.items():
            scores[type_code] += score
    
    return scores

def determine_type(scores: Dict[str, int]) -> str:
    """Определение доминирующего типа"""
    return max(scores, key=scores.get)

def calculate_thinking_level_optimized(context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Оптимизированный расчет уровня мышления (1-9)
    Более точное распределение по уровням
    """
    stage3_answers = context.user_data.get('stage3_answers', {})
    
    if not stage3_answers:
        return 1
    
    # Собираем все уровни из ответов
    levels = [answer for answer in stage3_answers.values()]
    
    if not levels:
        return 1
    
    # Вычисляем средний уровень
    avg_level = sum(levels) / len(levels)
    
    # Округляем до ближайшего целого (1-9)
    final_level = round(avg_level)
    
    # Гарантируем диапазон 1-9
    final_level = max(1, min(9, final_level))
    
    return final_level

def determine_dilts_level_smart(context: ContextTypes.DEFAULT_TYPE, thinking_level: int) -> str:
    """
    Умное определение уровня Дилтса с учетом уровня мышления
    Низкие уровни мышления не могут иметь высокие проблемы
    """
    stage4_answers = context.user_data.get('stage4_answers', {})
    
    if not stage4_answers:
        return "ENVIRONMENT"
    
    # Подсчитываем частоту каждого уровня
    dilts_counts = {
        "ENVIRONMENT": 0,
        "BEHAVIOR": 0,
        "CAPABILITIES": 0,
        "VALUES": 0,
        "IDENTITY": 0
    }
    
    for dilts_level in stage4_answers.values():
        dilts_counts[dilts_level] += 1
    
    # Находим доминирующий уровень
    dominant_dilts = max(dilts_counts, key=dilts_counts.get)
    
    # Применяем коррекцию на основе уровня мышления
    dilts_hierarchy = ["ENVIRONMENT", "BEHAVIOR", "CAPABILITIES", "VALUES", "IDENTITY"]
    max_allowed_index = 4  # по умолчанию разрешены все уровни
    
    # Ограничения по уровню мышления
    if thinking_level <= 2:
        max_allowed_index = 1  # максимум BEHAVIOR
    elif thinking_level <= 5:
        max_allowed_index = 2  # максимум CAPABILITIES
    elif thinking_level <= 7:
        max_allowed_index = 3  # максимум VALUES
    # 8-9 уровень: доступны все уровни включая IDENTITY
    
    # Если доминирующий уровень выше разрешенного, понижаем
    dominant_index = dilts_hierarchy.index(dominant_dilts)
    if dominant_index > max_allowed_index:
        dominant_dilts = dilts_hierarchy[max_allowed_index]
    
    return dominant_dilts

def calculate_profile_key(type_code: str, level: int, dilts_level: str) -> str:
    """
    Формирование ключа профиля
    Формат: TYPE_LEVEL_DILTS (например, SA_3_beh)
    """
    dilts_code = get_dilts_code(dilts_level)
    return f"{type_code}_{level}_{dilts_code}"

# ========================================
# ОБРАБОТЧИКИ КОМАНД
# ========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я помогу тебе пройти **адаптивное психологическое тестирование** и определить твой уникальный профиль мышления.

🎯 **Что ты получишь:**
• Определение типа мышления (4 типа)
• Оценку уровня развития (9 уровней)
• Анализ текущих проблем (5 уровней)
• Персональные рекомендации

⏱ **Время прохождения:** 10-15 минут

Тестирование состоит из 4 этапов:
1️⃣ Определение типа мышления (10 вопросов)
2️⃣ Уточнение типа (5 вопросов)
3️⃣ Оценка уровня развития (10 вопросов)
4️⃣ Анализ проблем (8 вопросов)

Готов начать? 🚀
"""
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тестирование", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало тестирования"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем предыдущие данные
    context.user_data.clear()
    context.user_data['stage1_answers'] = {}
    context.user_data['current_question'] = 0
    
    intro_text = """
📋 **ЭТАП 1: ОПРЕДЕЛЕНИЕ ТИПА МЫШЛЕНИЯ**

Сейчас я задам тебе 10 вопросов, которые помогут определить твой базовый тип мышления.

🎯 **Типы мышления:**
• **SA** - Социально-аффилиативный (фокус на людях)
• **IA** - Экзистенциально-рефлексивный (фокус на смыслах)
• **SP** - Инструментально-достиженческий (фокус на результате)
• **IP** - Структурно-аналитический (фокус на системах)

Отвечай честно, здесь нет правильных или неправильных ответов! ✨
"""
    
    keyboard = [[InlineKeyboardButton("▶️ Начать этап 1", callback_data="start_stage_1")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup)
    
    return STAGE_1_INTRO

# ========================================
# ЭТАП 1: ОПРЕДЕЛЕНИЕ ТИПА
# ========================================

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало этапа 1"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_question'] = 0
    
    return await show_stage_1_question(update, context)

async def show_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать вопрос этапа 1"""
    query = update.callback_query
    question_index = context.user_data['current_question']
    
    if question_index >= len(STAGE_1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[question_index]
    
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            option['text'],
            callback_data=f"stage1_{question_index}_{i}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(question['text'], reply_markup=reply_markup)
    
    return STAGE_1_QUESTIONS

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа этапа 1"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    _, question_index, option_index = query.data.split('_')
    question_index = int(question_index)
    option_index = int(option_index)
    
    # Сохраняем ответ
    question = STAGE_1_QUESTIONS[question_index]
    selected_option = question['options'][option_index]
    context.user_data['stage1_answers'][question_index] = selected_option['scores']
    
    # Переход к следующему вопросу
    context.user_data['current_question'] = question_index + 1
    
    return await show_stage_1_question(update, context)

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение этапа 1"""
    query = update.callback_query
    
    # Подсчет баллов
    scores = calculate_type_scores(context)
    primary_type = max(scores, key=scores.get)
    secondary_type = sorted(scores, key=scores.get, reverse=True)[1]
    
    context.user_data['primary_type'] = primary_type
    context.user_data['secondary_type'] = secondary_type
    
    result_text = f"""
✅ **ЭТАП 1 ЗАВЕРШЕН**

Твои результаты:
• {TYPE_CODES[primary_type]}: {scores[primary_type]} баллов
• {TYPE_CODES[secondary_type]}: {scores[secondary_type]} баллов

📊 Предварительный тип: **{TYPE_CODES[primary_type]}**

Переходим к уточняющим вопросам! 🎯
"""
    
    keyboard = [[InlineKeyboardButton("▶️ Начать этап 2", callback_data="start_stage_2")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup)
    
    return STAGE_2_INTRO

# ========================================
# ЭТАП 2: УТОЧНЕНИЕ ТИПА
# ========================================

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало этапа 2"""
    query = update.callback_query
    await query.answer()
    
    primary_type = context.user_data['primary_type']
    
    intro_text = f"""
📋 **ЭТАП 2: УТОЧНЕНИЕ ТИПА**

Ты показал склонность к типу **{TYPE_CODES[primary_type]}**.

Сейчас я задам 5 уточняющих вопросов, чтобы подтвердить результат.

Готов? 🎯
"""
    
    context.user_data['stage2_answers'] = {}
    context.user_data['current_question'] = 0
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_2_question")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup)
    
    return STAGE_2_QUESTIONS

async def show_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать вопрос этапа 2"""
    query = update.callback_query
    await query.answer()
    
    question_index = context.user_data['current_question']
    primary_type = context.user_data['primary_type']
    
    questions = STAGE_2_QUESTIONS[primary_type]
    
    if question_index >= len(questions):
        return await finish_stage_2(update, context)
    
    question = questions[question_index]
    
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            option['text'],
            callback_data=f"stage2_{question_index}_{i}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(question['text'], reply_markup=reply_markup)
    
    return STAGE_2_QUESTIONS

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа этапа 2"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    _, question_index, option_index = query.data.split('_')
    question_index = int(question_index)
    option_index = int(option_index)
    
    # Сохраняем ответ
    primary_type = context.user_data['primary_type']
    question = STAGE_2_QUESTIONS[primary_type][question_index]
    selected_option = question['options'][option_index]
    context.user_data['stage2_answers'][question_index] = selected_option['scores']
    
    # Переход к следующему вопросу
    context.user_data['current_question'] = question_index + 1
    
    return await show_stage_2_question(update, context)

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение этапа 2"""
    query = update.callback_query
    
    # Финальный подсчет типа
    scores = calculate_type_scores(context)
    final_type = determine_type(scores)
    
    context.user_data['final_type'] = final_type
    
    result_text = f"""
✅ **ЭТАП 2 ЗАВЕРШЕН**

Твой тип мышления: **{TYPE_CODES[final_type]}**

Теперь определим уровень развития! 📈
"""
    
    keyboard = [[InlineKeyboardButton("▶️ Начать этап 3", callback_data="start_stage_3")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup)
    
    return STAGE_3_INTRO

# ========================================
# ЭТАП 3: ОПРЕДЕЛЕНИЕ УРОВНЯ МЫШЛЕНИЯ
# ========================================

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало этапа 3"""
    query = update.callback_query
    await query.answer()
    
    intro_text = """
📋 **ЭТАП 3: ОЦЕНКА УРОВНЯ РАЗВИТИЯ**

Сейчас я определю твой уровень мышления по 9-уровневой шкале:

**Уровни 1-3:** Базовый (зависимость от окружения)
**Уровни 4-6:** Средний (развитие компетенций)
**Уровни 7-9:** Высокий (системное мышление)

Ответь на 10 вопросов честно! 🎯
"""
    
    context.user_data['stage3_answers'] = {}
    context.user_data['current_question'] = 0
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_3_question")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup)
    
    return STAGE_3_QUESTIONS

async def show_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать вопрос этапа 3"""
    query = update.callback_query
    await query.answer()
    
    question_index = context.user_data['current_question']
    
    if question_index >= len(STAGE_3_QUESTIONS):
        return await finish_stage_3(update, context)
    
    question = STAGE_3_QUESTIONS[question_index]
    
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            option['text'],
            callback_data=f"stage3_{question_index}_{i}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(question['text'], reply_markup=reply_markup)
    
    return STAGE_3_QUESTIONS

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа этапа 3"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    _, question_index, option_index = query.data.split('_')
    question_index = int(question_index)
    option_index = int(option_index)
    
    # Сохраняем ответ
    question = STAGE_3_QUESTIONS[question_index]
    selected_option = question['options'][option_index]
    context.user_data['stage3_answers'][question_index] = selected_option['level']
    
    # Переход к следующему вопросу
    context.user_data['current_question'] = question_index + 1
    
    return await show_stage_3_question(update, context)

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение этапа 3"""
    query = update.callback_query
    
    # Расчет уровня
    thinking_level = calculate_thinking_level_optimized(context)
    context.user_data['thinking_level'] = thinking_level
    
    level_description = ""
    if thinking_level <= 3:
        level_description = "Базовый уровень"
    elif thinking_level <= 6:
        level_description = "Средний уровень"
    else:
        level_description = "Высокий уровень"
    
    result_text = f"""
✅ **ЭТАП 3 ЗАВЕРШЕН**

Твой уровень мышления: **{thinking_level}/9**
Категория: {level_description}

Последний этап - анализ проблем! 🎯
"""
    
    keyboard = [[InlineKeyboardButton("▶️ Начать этап 4", callback_data="start_stage_4")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup)
    
    return STAGE_4_INTRO

# ========================================
# ЭТАП 4: ОПРЕДЕЛЕНИЕ УРОВНЯ ПРОБЛЕМЫ (ДИЛТС)
# ========================================

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало этапа 4"""
    query = update.callback_query
    await query.answer()
    
    intro_text = """
📋 **ЭТАП 4: АНАЛИЗ ПРОБЛЕМ**

Последний этап! Определим уровень твоих проблем по пирамиде Дилтса:

🔹 **Окружение** - проблемы с местом/людьми
🔹 **Поведение** - проблемы с действиями
🔹 **Способности** - проблемы с навыками
🔹 **Ценности** - проблемы с убеждениями
🔹 **Идентичность** - проблемы с самоопределением

Ответь на 8 вопросов! 🎯
"""
    
    context.user_data['stage4_answers'] = {}
    context.user_data['current_question'] = 0
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_4_question")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup)
    
    return STAGE_4_QUESTIONS

async def show_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать вопрос этапа 4"""
    query = update.callback_query
    await query.answer()
    
    question_index = context.user_data['current_question']
    
    if question_index >= len(STAGE_4_QUESTIONS):
        return await calculate_and_show_results(update, context)
    
    question = STAGE_4_QUESTIONS[question_index]
    
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            option['text'],
            callback_data=f"stage4_{question_index}_{i}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(question['text'], reply_markup=reply_markup)
    
    return STAGE_4_QUESTIONS

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа этапа 4"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    _, question_index, option_index = query.data.split('_')
    question_index = int(question_index)
    option_index = int(option_index)
    
    # Сохраняем ответ
    question = STAGE_4_QUESTIONS[question_index]
    selected_option = question['options'][option_index]
    context.user_data['stage4_answers'][question_index] = selected_option['dilts']
    
    # Переход к следующему вопросу
    context.user_data['current_question'] = question_index + 1
    
    return await show_stage_4_question(update, context)

# ========================================
# РАСЧЕТ И ОТПРАВКА РЕЗУЛЬТАТОВ
# ========================================

async def calculate_and_show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расчет финальных результатов"""
    query = update.callback_query
    
    # Получаем все данные
    final_type = context.user_data['final_type']
    thinking_level = context.user_data['thinking_level']
    
    # Определяем уровень Дилтса с учетом уровня мышления
    dilts_level = determine_dilts_level_smart(context, thinking_level)
    dilts_code = get_dilts_code(dilts_level)
    
    # Формируем ключ профиля
    profile_key = calculate_profile_key(final_type, thinking_level, dilts_level)
    
    # Сохраняем результаты
    context.user_data['results'] = {
        'type': final_type,
        'level': thinking_level,
        'dilts_level': dilts_code,
        'profile_key': profile_key
    }
    
    logger.info(f"✅ Profile calculated: {profile_key} (type={final_type}, level={thinking_level}, dilts={dilts_code})")
    
    # Показываем прогресс
    progress_text = """
⏳ **ОБРАБОТКА РЕЗУЛЬТАТОВ...**

Анализирую твои ответы...
Формирую персональный профиль...

Это займет несколько секунд ⚡
"""
    
    await query.edit_message_text(progress_text)
    
    # Переход к отправке результатов
    return await send_results(update, context)

async def send_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка результатов с использованием готовых описаний из card_data.py"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    
    try:
        # Получаем результаты
        results = context.user_data.get('results', {})
        
        if not results:
            await query.edit_message_text(
                "❌ Результаты не найдены. Пройдите тест заново.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Начать заново", callback_data="start_test")
                ]])
            )
            return
        
        # Извлекаем данные
        type_code = results.get('type')
        level = results.get('level')
        dilts_code = results.get('dilts_level')
        
        # Формируем ключ профиля
        profile_key = f"{type_code}_{level}_{dilts_code}"
        
        logger.info(f"📊 Sending results for user {user_id}: {profile_key}")
        
        # ✅ ИСПОЛЬЗУЕМ ГОТОВОЕ ОПИСАНИЕ ИЗ card_data.py
        profile_description = get_profile_description(profile_key)
        
        # Проверяем, найдено ли описание
        if profile_description.startswith("⚠️"):
            # Если профиля нет в базе, используем fallback (AI-генерацию)
            logger.warning(f"⚠️ Profile {profile_key} not found in card_data.py, using AI generation")
            
            # Fallback на AI-генерацию
            profile_description = await generate_profile(type_code, level, dilts_code)
            
            if not profile_description:
                profile_description = f"""
⚠️ **Временная проблема с генерацией описания**

Ваш профиль: **{profile_key}**

Тип: {type_code}
Уровень мышления: {level}
Уровень проблемы: {dilts_code}

Пожалуйста, обратитесь к администратору для получения полного описания.
"""
        
        # Формируем финальное сообщение
        final_message = f"""
🎯 **РЕЗУЛЬТАТЫ ВАШЕГО ТЕСТИРОВАНИЯ**

{profile_description}

---

📊 **Ваши показатели:**
• Тип мышления: {type_code}
• Уровень развития: {level}/9
• Уровень проблемы: {dilts_code}

🔑 **Код профиля:** `{profile_key}`
"""
        
        # Отправляем результат
        keyboard = [
            [InlineKeyboardButton("🔄 Пройти тест заново", callback_data="start_test")],
            [InlineKeyboardButton("💾 Сохранить результат", callback_data="save_result")],
            [InlineKeyboardButton("📤 Поделиться", callback_data="share_result")]
        ]
        
        await query.edit_message_text(
            final_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Results sent successfully for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error sending results: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Произошла ошибка при отправке результатов. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Начать заново", callback_data="start_test")
            ]])
        )

# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ОБРАБОТЧИКИ
# ========================================

async def save_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение результата"""
    query = update.callback_query
    await query.answer("💾 Результат сохранен!")

async def share_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поделиться результатом"""
    query = update.callback_query
    await query.answer("📤 Функция в разработке")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена тестирования"""
    await update.message.reply_text(
        "❌ Тестирование отменено. Используй /start для начала заново."
    )
    return ConversationHandler.END

async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик таймаута"""
    await update.message.reply_text(
        "⏰ Время сессии истекло. Используй /start для начала заново."
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

# ========================================
# ОБРАБОТЧИКИ ДЛЯ НАВИГАЦИИ НАЗАД
# ========================================

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению этапа 1"""
    return await start_test(update, context)

async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению этапа 2"""
    return await finish_stage_1(update, context)

async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению этапа 3"""
    return await finish_stage_2(update, context)

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению этапа 4"""
    return await finish_stage_3(update, context)

# ========================================
# ГЛАВНАЯ ФУНКЦИЯ
# ========================================

def main():
    """Запуск бота"""
    
    # ✅ ПРОВЕРКА НАЛИЧИЯ ВСЕХ ПРОФИЛЕЙ
    check_result = check_all_profiles_exist()
    logger.info(f"📊 Profile database status:")
    logger.info(f"   Total profiles: {check_result['total']}")
    logger.info(f"   Existing: {check_result['existing']}")
    logger.info(f"   Missing: {check_result['missing']}")
    
    if not check_result['is_complete']:
        logger.warning(f"⚠️ Only {check_result['existing']}/{check_result['total']} profiles available")
    else:
        logger.info(f"✅ All {check_result['existing']} profiles loaded successfully!")
    
    # Получаем токен из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1_INTRO: [
                CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$")
            ],
            STAGE_1_QUESTIONS: [
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            STAGE_2_INTRO: [
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$")
            ],
            STAGE_2_QUESTIONS: [
                CallbackQueryHandler(show_stage_2_question, pattern="^show_stage_2_question$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3_INTRO: [
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(back_to_stage2_intro, pattern="^back_to_stage2_intro$")
            ],
            STAGE_3_QUESTIONS: [
                CallbackQueryHandler(show_stage_3_question, pattern="^show_stage_3_question$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4_INTRO: [
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$")
            ],
            STAGE_4_QUESTIONS: [
                CallbackQueryHandler(show_stage_4_question, pattern="^show_stage_4_question$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_"),
                CallbackQueryHandler(save_result, pattern="^save_result$"),
                CallbackQueryHandler(share_result, pattern="^share_result$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        conversation_timeout=1800,
        allow_reentry=True,
        per_message=False
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен с интеграцией готовых профилей из card_data.py!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
