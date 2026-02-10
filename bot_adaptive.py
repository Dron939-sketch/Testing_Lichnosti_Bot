#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА: ПУТЬ К САМОПОЗНАНИЮ
4 этапа адаптивного исследования + персональное описание профиля
ВЕРСИЯ 3.0: Виртуальный психолог для самопознания
С ИНТЕГРАЦИЕЙ ПЛАТЕЖНОЙ СИСТЕМЫ
"""

import logging
import os
import asyncio
import urllib.parse
import math
import re
import time
import random
import requests
import base64
import uuid
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Импорт загрузчика и профилей
from loader import loader
from base import VariaticaProfile

# Получение токена
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация платежной системы
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"
BOT_LINK = "t.me/Testing_Lichnosti_bot"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Мне в руки попало особое зеркало. В нём видно то, что обычно скрыто даже от себя.\n\nЯ посмотрел(а). Увидел(а). Теперь держи — твоя очередь смотреть."

# Состояния ConversationHandler
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION, PAYMENT_SCREEN = range(11)

# ============================================
# КОНСТАНТЫ ДЛЯ УПРОЩЕННОГО ПОИСКА
# ============================================

STANDARD_SUFFIXES = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
LEVEL_DIFFS = [0, 1, -1, 2, -2, 3, -3, 4, -4]
EMERGENCY_PROFILES = [
    "sa_1_def", "sa_2_sit", "sa_3_con",
    "sp_1_def", "sp_2_sit", "sp_3_con", 
    "ia_1_def", "ia_2_sit", "ia_3_con",
    "ip_1_def", "ip_2_sit", "ip_3_con"
]

# ============================================
# ЭТАП 1: КАК ВЫ ВОСПРИНИМАЕТЕ МИР?
# ============================================

STAGE_1_QUESTIONS = [
    {
        "id": "q1_1",
        "text": "У вас неожиданно освободился вечер.\n\nЧто звучит привлекательнее?",
        "options": {
            "a": {"text": "Позвать друзей", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Побыть одному", "scores": {"INTERNAL": 2}},
            "c": {"text": "Сходить куда-то (событие/место)", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Почитать/посмотреть что-то", "scores": {"INTERNAL": 1}}
        }
    },
    {
        "id": "q1_2",
        "text": "Что даёт вам больше ресурса для жизни?",
        "options": {
            "a": {"text": "Люди, события, движение", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Мысли, чувства, тишина", "scores": {"INTERNAL": 2}},
            "c": {"text": "И то, и то в равной степени", "scores": {}},
            "d": {"text": "Зависит от ситуации", "scores": {}}
        }
    },
    {
        "id": "q1_3",
        "text": "Вы на вечеринке, где почти никого не знаете.\n\nЧто происходит?",
        "options": {
            "a": {"text": "Активно знакомлюсь со всеми", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Нахожу 1-2 человек и общаюсь с ними", "scores": {"EXTERNAL": 1}},
            "c": {"text": "Держусь в стороне", "scores": {"INTERNAL": 1}},
            "d": {"text": "Ухожу при первой возможности", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_4",
        "text": "Если бы ваша жизнь была местом, это было бы:",
        "options": {
            "a": {"text": "Оживлённая площадь", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Уютная комната", "scores": {"INTERNAL": 1}},
            "c": {"text": "Открытое пространство", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Тихое уединённое место", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_5",
        "text": "Что вас больше выбивает из равновесия?",
        "options": {
            "a": {"text": "Когда вас не понимают", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Когда теряете что-то важное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Когда не ясно, что происходит", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Когда всё идёт не по плану", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_6",
        "text": "Что для вас важнее?",
        "options": {
            "a": {"text": "Достичь цели", "scores": {"MATERIAL": 1}},
            "b": {"text": "Сохранить отношения", "scores": {"SYMBOLIC": 2}},
            "c": {"text": "Понять суть", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Сделать результат", "scores": {"MATERIAL": 2}}
        }
    },
    {
        "id": "q1_7",
        "text": "Что страшнее потерять?",
        "options": {
            "a": {"text": "Связь с важными людьми", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Финансовую стабильность", "scores": {"MATERIAL": 2}},
            "c": {"text": "Понимание себя", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Контроль над ситуацией", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_8",
        "text": "Вспомните последнюю сильную тревогу.\n\nО чём она была?",
        "options": {
            "a": {"text": "Меня отвергнут / не поймут", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Я потеряю что-то ценное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Я не понимаю, что со мной", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Я не справлюсь / не успею", "scores": {"MATERIAL": 1}}
        }
    }
]

# Типы восприятия
PERCEPTION_TYPES = {
    ("EXTERNAL", "SYMBOLIC"): {
        "name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ",
        "code": "SA",
        "description": "Фокус на внешних отношениях и социальном принятии"
    },
    ("INTERNAL", "SYMBOLIC"): {
        "name": "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ",
        "code": "IA",
        "description": "Фокус на внутренних смыслах и глубине переживания"
    },
    ("EXTERNAL", "MATERIAL"): {
        "name": "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ",
        "code": "SP",
        "description": "Фокус на внешних достижениях и результатах"
    },
    ("INTERNAL", "MATERIAL"): {
        "name": "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ",
        "code": "IP",
        "description": "Фокус на внутреннем порядке и системах понимания"
    }
}

# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

STAGE_2_QUESTIONS = {
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": [
        {
            "text": "Сколько у вас близких людей?\n\n(С кем можно говорить о личном)",
            "options": {
                "1": "Нет таких",
                "2": "1-2 человека", 
                "3": "3-5 человек",
                "5": "Больше 5"
            }
        },
        {
            "text": "Как вы к этому относитесь?",
            "options": {
                "1": "Мне не хватает близости",
                "2": "Я в процессе поиска своих людей",
                "3": "Меня это устраивает",
                "4": "Я не нуждаюсь в этом"
            }
        },
        {
            "text": "Как часто за месяц вы отменяете встречи с друзьями?",
            "options": {
                "1": "Не отменяю / нет встреч",
                "3": "1-2 раза",
                "2": "3-5 раз",
                "1": "Постоянно отменяю"
            }
        },
        {
            "text": "Почему отменяете?",
            "options": {
                "1": "Нет сил на людей",
                "2": "Эти люди не мои",
                "5": "Появились более важные дела",
                "3": "Не отменяю"
            }
        },
        {
            "text": "Как часто вы чувствуете, что вас не понимают?",
            "options": {
                "1": "Постоянно",
                "2": "Часто",
                "4": "Иногда",
                "3": "Редко или никогда"
            }
        },
        {
            "text": "Что вы с этим делаете?",
            "options": {
                "1": "Пытаюсь объясниться",
                "2": "Ищу тех, кто поймёт",
                "4": "Принимаю это",
                "3": "Меня понимают"
            }
        },
        {
            "text": "Ваш друг постоянно меняет компании.\n\nКак думаете, почему?",
            "options": {
                "2": "Ищет своих людей",
                "1": "Боится близости",
                "5": "Ему везде интересно",
                "4": "Не может быть собой"
            }
        },
        {
            "text": "Что для вас значит «найти своих людей»?",
            "options": {
                "2": "Место, где меня принимают",
                "3": "Люди, с которыми не нужно притворяться",
                "5": "Глубокая связь на уровне ценностей",
                "1": "Не думал об этом"
            }
        }
    ],
    "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": [
        {
            "text": "Как часто вы задаёте себе вопрос «В чём смысл?»",
            "options": {
                "1": "Постоянно, это мучительно",
                "2": "Часто, ищу ответы",
                "4": "Иногда, это интересно",
                "5": "Редко, я знаю свой смысл"
            }
        },
        {
            "text": "Что вы чувствуете, когда остаётесь наедине с собой?",
            "options": {
                "1": "Тревогу, пустоту",
                "2": "Вопросы без ответов",
                "4": "Спокойствие, ясность",
                "5": "Глубину, полноту"
            }
        },
        {
            "text": "Сколько времени в день вы проводите в размышлениях?",
            "options": {
                "1": "Почти всё время (застреваю)",
                "2": "Несколько часов",
                "4": "1-2 часа осознанно",
                "5": "Мало, я живу в моменте"
            }
        },
        {
            "text": "Что происходит после размышлений?",
            "options": {
                "1": "Ещё больше вопросов",
                "2": "Новые идеи, но нет действий",
                "4": "Понимаение и действия",
                "5": "Трансформация опыта"
            }
        },
        {
            "text": "Как вы относитесь к своим переживаниям?",
            "options": {
                "1": "Боюсь их, избегаю",
                "2": "Анализирую, пытаюсь понять",
                "4": "Принимаю и наблюдаю",
                "5": "Использую как материал для роста"
            }
        },
        {
            "text": "Что для вас значит «быть собой»?",
            "options": {
                "1": "Не знаю, кто я",
                "2": "Ищу себя",
                "4": "Знаю и принимаю себя",
                "5": "Я — это процесс, а не статус"
            }
        },
        {
            "text": "Человник погружён в экзистенциальный кризис.\n\nЧто ему делать?",
            "options": {
                "1": "Отвлечься, не думать об этом",
                "2": "Искать ответы (книги, терапия)",
                "4": "Прожить это как опыт",
                "5": "Это не кризис, а трансформация"
            }
        },
        {
            "text": "Что для вас глубина жизни?",
            "options": {
                "1": "Не понимаю, что это",
                "2": "Хочу её найти",
                "4": "Чувствую её в моменты",
                "5": "Живу в ней постоянно"
            }
        }
    ],
    "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": [
        {
            "text": "Сколько целей вы достигли за последний год?",
            "options": {
                "1": "Ни одной (только планировал)",
                "2": "1-2 цели",
                "4": "3-5 целей",
                "5": "Больше 5 целей"
            }
        },
        {
            "text": "Как вы себя чувствуете, когда достигаете цели?",
            "options": {
                "1": "Пусто (а что дальше?)",
                "2": "Радость, но ненадолго",
                "4": "Удовлетворение",
                "5": "Уже думаю о следующей"
            }
        },
        {
            "text": "Как часто вы откладываете важные дела?",
            "options": {
                "1": "Постоянно (прокрастинация)",
                "2": "Часто",
                "4": "Иногда",
                "5": "Редко или никогда"
            }
        },
        {
            "text": "Почему откладываете?",
            "options": {
                "1": "Страх неудачи",
                "2": "Не знаю, с чего начать",
                "4": "Жду подходящего момента",
                "5": "Не откладываю"
            }
        },
        {
            "text": "Что для вас успех?",
            "options": {
                "1": "Не знаю, не достигал",
                "2": "Деньги, статус, признание",
                "4": "Реализация своих целей",
                "5": "Влияние и вклад в мир"
            }
        },
        {
            "text": "Как вы относитесь к конкуренции?",
            "options": {
                "1": "Избегаю её",
                "2": "Боюсь проиграть",
                "4": "Мотивирует меня",
                "5": "Играю свою игру"
            }
        },
        {
            "text": "Человник хочет большего, но не действует.\n\nПочему?",
            "options": {
                "1": "Не верит в себя",
                "2": "Не знает, как",
                "4": "Ждёт готовности",
                "5": "На самом деле не хочет"
            }
        },
        {
            "text": "Что важнее: процесс или результат?",
            "options": {
                "1": "Результат, но его нет",
                "2": "Результат любой ценой",
                "4": "Баланс процесса и результата",
                "5": "Процесс = результат"
            }
        }
    ],
    "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": [
        {
            "text": "Насколько упорядочена ваша жизнь?",
            "options": {
                "1": "Хаос, не могу навести порядок",
                "2": "Пытаюсь структурировать",
                "4": "Есть система, которая работает",
                "5": "Гибкая структура под задачи"
            }
        },
        {
            "text": "Что происходит, когда нарушается ваш порядок?",
            "options": {
                "1": "Паника, тревога",
                "2": "Раздражение, дискомфорт",
                "4": "Адаптируюсь",
                "5": "Это часть процесса"
            }
        },
        {
            "text": "Как вы принимаете решения?",
            "options": {
                "1": "Не могу выбрать (анализ паралич)",
                "2": "Долго взвешиваю все варианты",
                "4": "Анализирую и выбираю оптимальное",
                "5": "Быстро, на основе критериев"
            }
        },
        {
            "text": "Что для вас понимание?",
            "options": {
                "1": "Не могу понять, как всё устроено",
                "2": "Ищу логику и закономерности",
                "4": "Вижу систему и связи",
                "5": "Создаю новые модели понимания"
            }
        },
        {
            "text": "Как вы относитесь к неопределённости?",
            "options": {
                "1": "Не выношу её",
                "2": "Пытаюсь всё просчитать",
                "4": "Принимаю как данность",
                "5": "Использую как ресурс"
            }
        },
        {
            "text": "Сколько у вас систем организации жизни?",
            "options": {
                "1": "Нет системы",
                "2": "Пробую разные, ничего не работает",
                "4": "Одна рабочая система",
                "5": "Несколько интегрированных систем"
            }
        },
        {
            "text": "Человник перегружен информацией.\n\nЧто делать?",
            "options": {
                "1": "Избегать информации",
                "2": "Пытаться всё изучить",
                "4": "Фильтровать по критериям",
                "5": "Создать систему обработки"
            }
        },
        {
            "text": "Что для вас контроль?",
            "options": {
                "1": "Не могу контролировать жизнь",
                "2": "Пытаюсь всё контролировать",
                "4": "Контролирую важное",
                "5": "Контроль = осознанность"
            }
        }
    ]
}

# Таблица баллов для этапа 2
STAGE_2_SCORING = {
    "СОЦИАЛЬНО-AФФИЛИАТИВНЫЙ": {
        0: {"1": 2, "2": 2, "3": 2, "5": 2},
        1: {"1": 2, "2": 2, "3": 2, "4": 2},
        2: {"1": 2, "3": 2, "2": 2, "1": 2},
        3: {"1": 2, "2": 2, "5": 2, "3": 2},
        4: {"1": 2, "2": 2, "4": 2, "3": 2},
        5: {"1": 2, "2": 2, "4": 2, "3": 2},
        6: {"2": 1, "1": 1, "5": 2, "4": 2},
        7: {"2": 1, "3": 2, "5": 2, "1": 1}
    },
    "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": {
        0: {"1": 2, "2": 2, "4": 2, "5": 2},
        1: {"1": 2, "2": 2, "4": 2, "5": 2},
        2: {"1": 2, "2": 2, "4": 2, "5": 2},
        3: {"1": 2, "2": 2, "4": 2, "5": 2},
        4: {"1": 1, "2": 1, "4": 2, "5": 2},
        5: {"1": 1, "2": 1, "4": 2, "5": 2},
        6: {"2": 1, "4": 2, "5": 2, "1": 1},
        7: {"4": 2, "5": 2, "1": 1, "2": 1}
    },
    "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": {
        0: {"1": 2, "2": 2, "4": 2, "5": 2},
        1: {"1": 2, "2": 2, "4": 2, "5": 2},
        2: {"1": 2, "2": 2, "4": 2, "5": 2},
        3: {"1": 2, "2": 2, "4": 2, "5": 2},
        4: {"1": 1, "2": 1, "4": 2, "5": 2},
        5: {"1": 1, "2": 1, "4": 2, "5": 2},
        6: {"2": 1, "4": 2, "5": 2, "1": 1},
        7: {"4": 2, "5": 2, "1": 1, "2": 1}
    },
    "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": {
        0: {"1": 2, "2": 2, "4": 2, "5": 2},
        1: {"1": 2, "2": 2, "4": 2, "5": 2},
        2: {"1": 2, "2": 2, "4": 2, "5": 2},
        3: {"1": 2, "2": 2, "4": 2, "5": 2},
        4: {"1": 1, "2": 1, "4": 2, "5": 2},
        5: {"1": 1, "2": 1, "4": 2, "5": 2},
        6: {"2": 1, "4": 2, "5": 2, "1": 1},
        7: {"4": 2, "5": 2, "1": 1, "2": 1}
    }
}

# ============================================
# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
# ============================================

STAGE_3_QUESTIONS = [
    {"id": "q3_1", "text": "Вспомните последнюю неделю.\n\nСколько раз вы сделали что-то, что потом пожалели?", "options": {"a": {"text": "Ни разу", "level": 5}, "b": {"text": "1-2 раза", "level": 3}, "c": {"text": "3-5 раз", "level": 2}, "d": {"text": "Больше 5 раз", "level": 1}}},
    {"id": "q3_2", "text": "Последний конфликт.\n\nЧто вы сделали?", "options": {"a": {"text": "Избежал", "level": 1}, "b": {"text": "Уступил", "level": 1}, "c": {"text": "Отстоял позицию", "level": 3}, "d": {"text": "Нашёл компромисс", "level": 5}}},
    {"id": "q3_3", "text": "Как вы принимаете важные решения?", "options": {"a": {"text": "Долго мучаюсь", "level": 1}, "b": {"text": "Взвешиваю варианты", "level": 3}, "c": {"text": "Быстро, по интуиции", "level": 5}, "d": {"text": "Жду, когда решение придёт само", "level": 4}}},
    {"id": "q3_4", "text": "Как часто вы делаете то, что не хотите, но «надо»?", "options": {"a": {"text": "Постоянно (вся жизнь — «надо»)", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко (делаю то, что хочу)", "level": 5}}},
    {"id": "q3_5", "text": "Вспомните последнюю сильная эмоция.\n\nЧто вы с ней сделали?", "options": {"a": {"text": "Подавил", "level": 1}, "b": {"text": "Проанализировал", "level": 3}, "c": {"text": "Выразил (слова/действия/творчество)", "level": 5}, "d": {"text": "Наблюдал за ней", "level": 4}}},
    {"id": "q3_6", "text": "Как вы относитесь к своим слабостям?", "options": {"a": {"text": "Стыжусь их", "level": 1}, "b": {"text": "Пытаюсь исправить", "level": 2}, "c": {"text": "Принимаю их", "level": 4}, "d": {"text": "Вижу в них силу", "level": 6}}},
    {"id": "q3_7", "text": "Как часто вы чувствуете, что живёте не своей жизнью?", "options": {"a": {"text": "Постоянно", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко или никогда", "level": 5}}},
    {"id": "q3_8", "text": "Что вы делаете, когда не знаете, что делать?", "options": {"a": {"text": "Паникую", "level": 1}, "b": {"text": "Ищу информацию", "level": 2}, "c": {"text": "Действую методом проб", "level": 3}, "d": {"text": "Жду ясности", "level": 4}}}
]

# ============================================
# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

STAGE_4_QUESTIONS = [
    {"id": "q4_1", "text": "Как часто вы чувствуете, что «что-то не так» в жизни?", "options": {"a": {"text": "Постоянно", "dilts": "IDENTITY"}, "b": {"text": "Часто", "dilts": "VALUES"}, "c": {"text": "Иногда", "dilts": "CAPABILITIES"}, "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}}},
    {"id": "q4_2", "text": "Что именно «не так»?\n\nВыберите то, что ближе всего:", "options": {"a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"}, "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"}, "c": {"text": "Не умею делать то, что хочу", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}}},
    {"id": "q4_3", "text": "Человник чувствует себя несчастным.\n\nВ чём, скорее всего, причина?", "options": {"a": {"text": "Не те люди вокруг", "dilts": "ENVIRONMENT"}, "b": {"text": "Делает не то, что хочет", "dilts": "BEHAVIOR"}, "c": {"text": "Не умеет делать то, что хочет", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимает, чего хочет", "dilts": "VALUES"}}},
    {"id": "q4_4", "text": "Если бы вы могли изменить что-то одно, что бы это было?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Своё понимание целей", "dilts": "VALUES"}}},
    {"id": "q4_5", "text": "Что для вас сложнее всего?", "options": {"a": {"text": "Изменить внешние условия", "dilts": "ENVIRONMENT"}, "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"}, "c": {"text": "Научиться новому", "dilts": "CAPABILITIES"}, "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}}},
    {"id": "q4_6", "text": "Когда вы застреваете в проблеме, что обычно не хватает?", "options": {"a": {"text": "Ресурсов (время, деньги, связи)", "dilts": "ENVIRONMENT"}, "b": {"text": "Действий (не начинаю)", "dilts": "BEHAVIOR"}, "c": {"text": "Навыков (не умею)", "dilts": "CAPABILITIES"}, "d": {"text": "Понимания (не знаю зачем)", "dilts": "VALUES"}}},
    {"id": "q4_7", "text": "Что мешает вам быть счастливым?", "options": {"a": {"text": "Обстоятельства", "dilts": "ENVIRONMENT"}, "b": {"text": "Мои действия", "dilts": "BEHAVIOR"}, "c": {"text": "Мои ограничения", "dilts": "CAPABILITIES"}, "d": {"text": "Я не знаю, что такое счастье", "dilts": "VALUES"}}},
    {"id": "q4_8", "text": "Если бы у вас была волшебная палочка, что бы вы изменили?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Себя (кто я)", "dilts": "IDENTITY"}}}
]

# Уровни Дилтса
DILTS_LEVELS = {
    "ENVIRONMENT": {"name": "ОКРУЖЕНИЕ", "code": "env", "description": "Проблема во внешних условиях", "solution": "Измени окружение или отношение к нему"},
    "BEHAVIOR": {"name": "ПОВЕДЕНИЕ", "code": "beh", "description": "Проблема в действиях", "solution": "Начни действовать по-другому"},
    "CAPABILITIES": {"name": "СПОСОБНОСТИ", "code": "cap", "description": "Проблема в навыках", "solution": "Освой новые навыки"},
    "VALUES": {"name": "ЦЕННОСТИ", "code": "val", "description": "Проблема в мотивации", "solution": "Найди свои истинные ценности"},
    "IDENTITY": {"name": "ИДЕНТИЧНОСТЬ", "code": "ide", "description": "Проблема в самоопределении", "solution": "Переопредели, кто ты"}
}

# ============================================
# УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================

CLARIFICATION_QUESTIONS = {
    "stage1_external_internal": [
        {"id": "c1_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nПосле напряжённого дня что вам нужнее?", "options": {"a": {"text": "Встретиться с людьми", "scores": {"EXTERNAL": 2}}, "b": {"text": "Побыть в одиночестве", "scores": {"INTERNAL": 2}}}},
        {"id": "c1_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда вы думаете о выходных, что первое приходит в голову?", "options": {"a": {"text": "Куда пойти, с кем встретиться", "scores": {"EXTERNAL": 2}}, "b": {"text": "Чем заняться дома, о чём подумать", "scores": {"INTERNAL": 2}}}}
    ],
    "stage1_symbolic_material": [
        {"id": "c1_3", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЧто хуже: потерять деньги или потерять доверие близких?", "options": {"a": {"text": "Потерять доверие", "scores": {"SYMBOLIC": 2}}, "b": {"text": "Потерять деньги", "scores": {"MATERIAL": 2}}}},
        {"id": "c1_4", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда вы тревожитесь, о чём чаще?", "options": {"a": {"text": "Что обо мне подумают, как меня воспримут", "scores": {"SYMBOLIC": 2}}, "b": {"text": "Хватит ли денег, успею ли, справлюсь ли", "scores": {"MATERIAL": 2}}}}
    ],
    "stage2_borderline": [
        {"id": "c2_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто вы чувствуете, что застряли на месте?", "options": {"1": "Постоянно, не знаю как двигаться", "3": "Иногда, но нахожу выход", "4": "Редко, я в движении"}},
        {"id": "c2_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак вы относитесь к своим прошлым ошибкам?", "options": {"1": "Стыжусь их, избегаю вспоминать", "3": "Анализирую и учусь", "4": "Принимаю как опыт"}}
    ],
    "stage3_discrepancy": [
        {"id": "c3_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nВспомните последний месяц. Сколько раз вы действовали не так, как хотели?", "options": {"1": "Постоянно", "2": "Часто (больше 5 раз)", "3": "Иногда (2-4 раза)", "5": "Редко (0-1 раз)"}},
        {"id": "c3_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак быстро вы замечаете свои автоматические реакции?", "options": {"1": "Не замечаю, действую на автомате", "2": "Замечаю после", "4": "Замечаю в процессе", "5": "Замечаю до и могу изменить"}},
        {"id": "c3_3", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто вы делаете то, что обещали себе?", "options": {"1": "Почти никогда", "2": "Иногда", "4": "Часто", "5": "Почти всегда"}}
    ],
    "stage4_tie": [
        {"id": "c4_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЕсли бы вы могли изменить только одно, что бы выбрали?", "options": {"a": {"text": "Где я нахожусь", "dilts": "ENVIRONMENT"}, "b": {"text": "Что я делаю", "dilts": "BEHAVIOR"}, "c": {"text": "Что я умею", "dilts": "CAPABILITIES"}, "d": {"text": "Что для меня важно", "dilts": "VALUES"}, "e": {"text": "Кто я", "dilts": "IDENTITY"}}},
        {"id": "c4_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nГде находится ваша главная проблема?", "options": {"a": {"text": "В обстоятельствах", "dilts": "ENVIRONMENT"}, "b": {"text": "В моих действиях", "dilts": "BEHAVIOR"}, "c": {"text": "В моих навыках", "dilts": "CAPABILITIES"}, "d": {"text": "В моих целях", "dilts": "VALUES"}, "e": {"text": "В моём самоопределении", "dilts": "IDENTITY"}}}
    ]
}

# ============================================
# ФУНКЦИИ ПЛАТЕЖНОЙ СИСТЕМЫ
# ============================================

def generate_payment_id(prefix="buy") -> str:
    """Генерирует уникальный ID платежа"""
    timestamp = int(time.time())
    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    return f"{prefix}_{timestamp}_{random_str}"

def create_yookassa_invoice(payment_id: str, user_id: int, profile_code: str, amount: float = 1.0, email: str = None) -> dict:
    """
    Создает платеж через Invoices API ЮKassa
    """
    try:
        logger.info(f"📤 Создаю платеж ЮKassa: {payment_id}, профиль: {profile_code}")
        
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        unique_id = uuid.uuid4().hex[:16]
        idempotence_key = f"{payment_id}_{unique_id}_{int(time.time())}"
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': idempotence_key
        }
        
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Обновленное описание для виртуального психолога
        description = f"Полное описание профиля {profile_code} от виртуального психолога"
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": TELEGRAM_BOT_URL
            },
            "capture": True,
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id),
                "profile_code": profile_code,
                "is_test": "true" if amount == 1.0 else "false"
            },
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": f"Полное описание профиля {profile_code} от виртуального психолога",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": "1",
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }
                ]
            }
        }
        
        logger.info(f"💳 Отправляю запрос в ЮKassa...")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if confirmation_url:
                logger.info(f"✅ Платеж создан в ЮKassa: {data.get('id')}")
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": confirmation_url,
                    "yookassa_id": data.get('id'),
                    "amount": amount,
                    "profile_code": profile_code,
                    "invoice_type": "yookassa_invoice",
                    "available_methods": "all",
                    "status": data.get('status', 'pending')
                }
            else:
                logger.error(f"❌ Нет ссылки для оплаты в ответе ЮKassa")
                return {"success": False, "error": "Нет ссылки для оплаты"}
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            return {"success": False, "error": f"Ошибка ЮKassa: {response.status_code}", "details": error_text}
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа ЮKassa: {e}")
        return {"success": False, "error": str(e)}

async def create_payment_advanced(user_id: int, profile_code: str, amount: float = 1.00) -> dict:
    """
    СОЗДАЕТ ПЛАТЕЖ в нашей базе данных + в ЮKassa
    """
    
    timestamp = int(time.time())
    if amount == 1.0:
        payment_id = f"test_{user_id}_{timestamp}"
    else:
        payment_id = f"prod_{user_id}_{timestamp}"
    
    logger.info(f"💳 Создаю платеж: {payment_id}, профиль: {profile_code}, сумма: {amount}")
    
    try:
        db_payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "profile_code": profile_code.upper(),
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": f"Полное описание профиля {profile_code} от виртуального психолога"
        }
        
        db_response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=db_payload,
            timeout=10
        )
        
        if db_response.status_code in [200, 201]:
            db_data = db_response.json()
            
            if db_data.get("confirmation_url"):
                logger.info(f"✅ Платеж создан через API: {payment_id}")
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": db_data["confirmation_url"],
                    "amount": amount,
                    "profile_code": profile_code,
                    "yookassa_id": db_data.get("yookassa_id"),
                    "invoice_type": db_data.get("invoice_type", "yookassa_invoice"),
                    "available_methods": db_data.get("available_methods", "all"),
                    "status": db_data.get("status", "pending")
                }
            
            logger.info(f"🔄 Создаю платеж через ЮKassa напрямую: {payment_id}")
            yookassa_result = create_yookassa_invoice(
                payment_id=payment_id,
                user_id=user_id,
                profile_code=profile_code,
                amount=amount,
                email=f"user_{user_id}@telegram.org"
            )
            
            if yookassa_result["success"]:
                try:
                    update_response = requests.post(
                        f"{API_URL}/api/update-yookassa-id",
                        json={
                            "payment_id": payment_id,
                            "yookassa_id": yookassa_result.get("yookassa_id"),
                            "profile_code": profile_code,
                            "status": "waiting"
                        },
                        timeout=5
                    )
                    
                    if update_response.status_code in [200, 201]:
                        logger.info(f"✅ ID ЮKassa сохранен в БД")
                    else:
                        logger.warning(f"⚠️ Не удалось сохранить ID ЮKassa: {update_response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при сохранении ID ЮKassa: {e}")
                
                return yookassa_result
            else:
                logger.error(f"❌ Ошибка создания платежа в ЮKassa: {yookassa_result.get('error')}")
                return yookassa_result
                
        else:
            error_text = db_response.text[:200]
            logger.error(f"❌ Ошибка БД {db_response.status_code}: {error_text}")
            return {
                "success": False, 
                "error": f"Ошибка API: {db_response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к API: {e}")
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }

async def get_materials_link_api(payment_id: str, user_id: int) -> dict:
    """Получает ссылку на материалы через API"""
    try:
        response = requests.get(
            f"{API_URL}/api/get-materials/{payment_id}",
            params={"user_id": user_id},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return {
                    "success": True,
                    "materials_link": result.get("materials_link"),
                    "profile_code": result.get("profile_code"),
                    "profile_link": result.get("profile_link")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Materials API error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def check_payment_status_api(payment_id: str) -> dict:
    """Проверяет статус платежа через API"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "status": result.get("status", "unknown"),
                "payment_id": payment_id,
                "data": result
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%"

def determine_perception_type(scores):
    """Определяет тип восприятия"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    focus = "EXTERNAL" if external >= internal else "INTERNAL"
    anxiety = "SYMBOLIC" if symbolic >= material else "MATERIAL"
    
    type_data = PERCEPTION_TYPES.get((focus, anxiety), PERCEPTION_TYPES[("EXTERNAL", "SYMBOLIC")])
    return type_data["name"]

def get_type_code(perception_type: str) -> str:
    """Код типа (SA/IA/SP/IP)"""
    type_map = {
        "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "SA",
        "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "IA",
        "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "SP",
        "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "IP"
    }
    return type_map.get(perception_type, "SA")

def get_level_name(level_num):
    """Получаем название уровня по номеру"""
    level_names = {
        1: "ДЕФИЦИТАРНЫЙ",
        2: "ПОИСКОВЫЙ", 
        3: "КОНСТРУКТИВНЫЙ",
        4: "КРИЗИСНЫЙ",
        5: "ИНТЕГРАТИВНЫЙ",
        6: "АЛЬТРУИСТИЧЕСКИЙ",
        7: "МУДРЕЦКИЙ",
        8: "СИСТЕМНЫЙ",
        9: "ТРАНСЦЕНДЕНТНЫЙ"
    }
    return level_names.get(level_num, f"Уровень {level_num}")

def get_dilts_code(dilts_level: str) -> str:
    """Код Дилтса"""
    dilts_map = {
        "ENVIRONMENT": "env",
        "BEHAVIOR": "beh",
        "CAPABILITIES": "cap",
        "VALUES": "val",
        "IDENTITY": "ide"
    }
    return dilts_map.get(dilts_level, "env")

def determine_dilts_level(dilts_answers):
    """Определяет уровень Дилтса"""
    if not dilts_answers:
        return "ENVIRONMENT"
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(1)[0]
    return most_common[0]

# ============================================
# СИСТЕМА РАСЧЕТА УРОВНЯ
# ============================================

def calculate_thinking_level_by_scores(level_scores_dict):
    """Определяет уровень мышления (1-9) по системе баллов"""
    if not level_scores_dict:
        return 1
    
    numeric_scores = {int(k): v for k, v in level_scores_dict.items() if k.isdigit()}
    
    if not numeric_scores:
        return 1
    
    max_score = max(numeric_scores.values())
    max_levels = [level for level, score in numeric_scores.items() if score == max_score]
    
    if not max_levels:
        return 1
    
    return max(max_levels)

def calculate_final_level(stage2_level, stage3_scores):
    """Финальный уровень (приоритет поведению)"""
    if not stage3_scores:
        return stage2_level
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    weighted = stage3_avg * 0.7 + stage2_level * 0.3
    final_level = int(round(weighted))
    
    logger.info(f"Final level: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}, weighted={weighted:.2f}, final={final_level}")
    return final_level

# ============================================
# ФУНКЦИЯ ОЧИСТКИ ДУБЛИРУЮЩИХСЯ ЗАГОЛОВКОВ
# ============================================

def clean_duplicate_headers(text: str, field_type: str) -> str:
    """
    Убирает заголовки, которые уже есть в тексте профиля.
    """
    if not text:
        return ""
    
    lines = text.strip().split('\n')
    if not lines:
        return text
    
    headers = {
        'trigger': ['ЭТО ТЫ, ЕСЛИ...', 'ЭТО ТЫ, ЕСЛИ:'],
        'pain': ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ: ПОЧЕМУ ЭТО ЛОМАЕТ ТВОЮ ЖИЗНЬ?'],
        'immediate_tool': ['ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:'],
        'cta': ['ЧТО ДАЛЬШЕ?', 'ДАЛЬШЕ:']
    }
    
    if field_type in headers and lines:
        first_line = lines[0].strip()
        for header in headers[field_type]:
            if header in first_line:
                lines.pop(0)
                if lines and not lines[0].strip():
                    lines.pop(0)
                break
    
    return '\n'.join(lines).strip()

# ============================================
# ФУНКЦИЯ ФОРМАТИРОВАНИЯ ЗАГОЛОВКА ПРОФИЛЯ
# ============================================

def format_profile_title(profile_title: str, profile_header: str) -> str:
    """Форматирует заголовок профиля."""
    if not profile_title:
        return f"🎯 {profile_header}"
    
    profile_title = profile_title.strip()
    lines = profile_title.split('\n')
    
    if len(lines) == 1:
        title = lines[0].strip()
        return f"🎯 {profile_header} / {title}"
    
    elif len(lines) >= 2:
        line1 = lines[0].strip()
        line2 = lines[1].strip()
        
        if line2 == profile_header or line2.replace('_', ' ').lower() == profile_header.replace('_', ' ').lower():
            return f"🎯 {profile_header} / {line1}"
        else:
            return f"🎯 {profile_header} / {line1}"
    
    return f"🎯 {profile_header}"

# ============================================
# УПРОЩЕННАЯ ФУНКЦИЯ ПОИСКА ПРОФИЛЯ
# ============================================

class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

def get_profile_fallback(profile_data: dict) -> VariaticaProfile:
    """
    УПРОЩЕННАЯ логика поиска профиля.
    ПРИНЦИП: Игнорируем точный dilts_code, ищем по ТИПУ и УРОВНЮ.
    """
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    logger.info(f"🔍 ПОИСК ПРОФИЛЯ: type={type_code}, level={level}, dilts={dilts_code}")
    
    search_order = []
    if dilts_code in STANDARD_SUFFIXES:
        search_order.append(dilts_code)
    search_order.extend(STANDARD_SUFFIXES)
    search_order = list(dict.fromkeys(search_order))
    
    logger.info(f"📋 Порядок поиска суффиксов: {search_order}")
    
    for suffix in search_order:
        profile_key = f"{type_code}_{level}_{suffix}"
        profile = loader.get_profile(profile_key)
        if profile:
            logger.info(f"✅ Найден профиль: {profile_key}")
            return profile
    
    logger.warning(f"⚠️ Не найдено профилей для {type_code}_{level}_*")
    
    for diff in LEVEL_DIFFS:
        test_level = level + diff
        if 1 <= test_level <= 9:
            for suffix in STANDARD_SUFFIXES:
                profile_key = f"{type_code}_{test_level}_{suffix}"
                profile = loader.get_profile(profile_key)
                if profile:
                    logger.info(f"✅ Найден на уровне {test_level} (разница {diff}): {profile_key}")
                    return profile
    
    logger.error(f"❌ Не найдено профилей типа {type_code} на уровнях 1-9")
    
    for emergency_key in EMERGENCY_PROFILES:
        profile = loader.get_profile(emergency_key)
        if profile:
            logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
            return profile
    
    error_msg = f"Не найден профиль для type={type_code}, level={level}"
    logger.critical(f"💥 {error_msg}")
    raise ProfileNotFoundError(error_msg)

# ============================================
# ФУНКЦИЯ ПОЛУЧЕНИЯ ОПИСАНИЯ ПРОФИЛЯ
# ============================================

def get_card_description_from_profile(profile: VariaticaProfile, profile_data: dict) -> dict:
    """Получает описание профиля с очисткой заголовков"""
    is_new_format = hasattr(profile, 'archetype') and profile.archetype
    
    if is_new_format:
        clean_trigger = clean_duplicate_headers(profile.trigger, 'trigger')
        clean_pain = clean_duplicate_headers(profile.pain, 'pain')
        clean_tool = clean_duplicate_headers(profile.immediate_tool, 'immediate_tool')
        clean_cta = clean_duplicate_headers(profile.cta, 'cta')
        
        return {
            "title": profile.title,
            "archetype": profile.archetype,
            "quote": profile.quote,
            "trigger": clean_trigger,
            "pain": clean_pain,
            "immediate_tool": clean_tool,
            "cta": clean_cta,
            
            "type_code": profile_data['type_code'],
            "level": profile_data['level'],
            "dilts_code": profile_data['dilts_code'],
        }
    else:
        return {
            "title": profile.title if hasattr(profile, 'title') else f"{profile_data['type_code']} Профиль",
            "profile_name": profile.profile_name if hasattr(profile, 'profile_name') else f"{profile_data['type_code']} Уровень {profile_data['level']}",
            "thinking_level": profile.thinking_level if hasattr(profile, 'thinking_level') else profile_data['level'],
            "dilts_level": profile.dilts_level if hasattr(profile, 'dilts_level') else profile_data['dilts_level'],
            "pain": profile.pain if hasattr(profile, 'pain') else "",
            "world": profile.world if hasattr(profile, 'world') else "",
            "superpower": profile.superpower if hasattr(profile, 'superpower') else "",
            "growth": profile.growth if hasattr(profile, 'growth') else f"Точка роста на уровне {profile_data['level']}",
            "cta": profile.cta if hasattr(profile, 'cta') else ""
        }

# ============================================
# ФУНКЦИЯ РАСЧЕТА ПРОФИЛЯ
# ============================================

def calculate_profile_final(context_data: dict) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля"""
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    level_scores_dict = context_data.get("stage2_level_scores_dict", {})
    stage2_level = calculate_thinking_level_by_scores(level_scores_dict)
    
    stage3_scores = context_data.get("stage3_level_scores", [])
    final_level = calculate_final_level(stage2_level, stage3_scores)
    final_level = max(1, min(9, final_level))
    
    dilts_answers = context_data.get("stage4_dilts_answers", [])
    dilts_level = determine_dilts_level(dilts_answers)
    dilts_code = get_dilts_code(dilts_level)
    
    coherence = check_profile_coherence(final_level, dilts_level)
    
    logger.info(f" FINAL PROFILE CALCULATION:")
    logger.info(f"   Type: {type_code} ({perception_type})")
    logger.info(f"   Level: {final_level} ({get_level_name(final_level)})")
    logger.info(f"   Dilts: {dilts_level} ({dilts_code})")
    logger.info(f"   Coherence: {coherence['is_coherent']}")
    
    return {
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code,
        
        "display_name": f"{type_code}_{final_level}_{dilts_code}",
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        
        "coherence": coherence,
        "stage2_level": stage2_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
    }

def check_profile_coherence(profile_level: int, dilts_level: str) -> dict:
    """Проверяет согласованность уровня профиля и уровня Дилтса"""
    expected_dilts_by_level = {
        1: ["ENVIRONMENT", "BEHAVIOR"],
        2: ["BEHAVIOR", "CAPABILITIES"],
        3: ["CAPABILITIES", "VALUES"],
        4: ["VALUES", "IDENTITY"],
        5: ["VALUES", "IDENTITY"],
        6: ["IDENTITY", "VALUES"],
        7: ["IDENTITY"],
        8: ["IDENTITY"],
        9: ["IDENTITY"]
    }
    
    expected_dilts = expected_dilts_by_level.get(profile_level, ["VALUES"])
    is_coherent = dilts_level in expected_dilts
    
    return {
        "is_coherent": is_coherent,
        "profile_level": profile_level,
        "dilts_level": dilts_level,
        "expected_dilts": expected_dilts
    }

# ============================================
# ПРОВЕРКИ УТОЧНЕНИЙ
# ============================================

def need_clarification_stage1(scores):
    """Нужны ли уточнения после ЭТАПА 1"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    clarifications = []
    if abs(external - internal) <= 2:
        clarifications.append("external_internal")
    if abs(symbolic - material) <= 2:
        clarifications.append("symbolic_material")
    
    return clarifications

def need_clarification_stage2(level_scores_dict):
    """Нужны ли уточнения после ЭТАПА 2"""
    if not level_scores_dict:
        return False
    
    sorted_levels = sorted(level_scores_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_levels) >= 2:
        first_score = sorted_levels[0][1]
        second_score = sorted_levels[1][1]
        
        if abs(first_score - second_score) < 3:
            logger.info(f"Stage2 needs clarification: {sorted_levels[0]} vs {sorted_levels[1]}")
            return True
    
    return False

def need_clarification_stage3(stage2_level, stage3_scores):
    """Нужны ли уточнения после ЭТАПА 3"""
    if not stage3_scores:
        return False
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    return abs(stage2_level - stage3_avg) > 2

def need_clarification_stage4(dilts_answers):
    """Нужны ли уточнения после ЭТАПА 4"""
    if not dilts_answers:
        return False
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(2)
    if len(most_common) >= 2:
        return most_common[0][1] == most_common[1][1]
    return False

# ============================================
# ПСИХОЛОГИЧЕСКИЕ ПОДСКАЗКИ ДЛЯ ВОПРОСОВ
# ============================================

PSYCHOLOGIST_TIPS = {
    "stage1": [
        "🧠 <i>Не думайте слишком долго — важна первая реакция</i>",
        "🧠 <i>Отвечайте так, как есть сейчас, а не как хотелось бы</i>",
        "🧠 <i>Это безопасное пространство для честности с собой</i>",
        "🧠 <i>Все ответы важны для построения точного профиля</i>",
        "🧠 <i>Чем честнее вы будете, тем точнее будут рекомендации</i>",
        "🧠 <i>Не бывает правильных или неправильных ответов</i>",
        "🧠 <i>Это исследование, а не оценка</i>",
        "🧠 <i>Спасибо за доверие в этом процессе самопознания</i>"
    ],
    "stage2": [
        "🧠 <i>Опишите текущую реальность, а не идеальную ситуацию</i>",
        "🧠 <i>Ваши ответы помогают мне понять ваш внутренний мир</i>",
        "🧠 <i>Будьте максимально искренни — это только для вас</i>",
        "🧠 <i>Каждый ответ добавляет деталь к вашему портрету</i>",
        "🧠 <i>Не оценивайте свои ответы как хорошие или плохие</i>",
        "🧠 <i>Это путь к лучшему пониманию себя</i>",
        "🧠 <i>Ваша честность — ключ к точным инсайтам</i>",
        "🧠 <i>Спасибо за открытость в этом диалоге</i>"
    ],
    "stage3": [
        "🧠 <i>Вспомните реальные ситуации из последнего времени</i>",
        "🧠 <i>Автоматические реакции часто говорят больше, чем мысли</i>",
        "🧠 <i>Не осуждайте себя за прошлые действия</i>",
        "🧠 <i>Это исследование паттернов, а не критика</i>",
        "🧠 <i>Чем точнее ответы, тем полезнее будут рекомендации</i>",
        "🧠 <i>Поведение часто противоречит нашим представлениям о себе</i>",
        "🧠 <i>Это нормально — действовать не так, как хотелось бы</i>",
        "🧠 <i>Вы делаете важную работу по самопознанию</i>"
    ],
    "stage4": [
        "🧠 <i>Где вы чувствуете главное напряжение в жизни?</i>",
        "🧠 <i>Это поможет определить точку для роста</i>",
        "🧠 <i>Что вызывает наибольшее сопротивление?</i>",
        "🧠 <i>Проблема часто находится там, где мы её не ожидаем</i>",
        "🧠 <i>Это завершающий этап нашего исследования</i>",
        "🧠 <i>Ваши ответы помогут сфокусировать рекомендации</i>",
        "🧠 <i>Готовьтесь к важным инсайтам о себе</i>",
        "🧠 <i>Благодарю за доверие в этом путешествии</i>"
    ]
}

# ============================================
# ИСПРАВЛЕННЫЙ ЭКРАН РЕЗУЛЬТАТОВ
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ - версия виртуального психолога"""
    query = update.callback_query
    
    has_shared = context.user_data.get("has_shared", False)
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    try:
        profile = get_profile_fallback(profile_data)
    except ProfileNotFoundError as e:
        error_text = (
            f"🧠 <b>К сожалению, возникла техническая ошибка</b>\n\n"
            f"Как ваш виртуальный психолог, я не смог обработать все данные.\n\n"
            f"Попробуйте пройти тест заново, чтобы я мог помочь вам лучше:\n"
            f"/start\n\n"
            f"<i>Приношу извинения за неудобства.</i>"
        )
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    try:
        if hasattr(profile, 'key'):
            actual_profile_key = profile.key.lower()
            logger.info(f"🔍 Найден ключ профиля: {actual_profile_key}")
        elif hasattr(profile, 'profile_name'):
            actual_profile_key = profile.profile_name.lower()
        else:
            actual_profile_key = f"{profile_card.get('type_code', 'sa')}_{profile_card.get('level', 1)}_{profile_card.get('dilts_code', 'def')}".lower()
        
        parts = actual_profile_key.split('_')
        if len(parts) >= 3:
            profile_data['type_code'] = parts[0].upper()
            profile_data['level'] = int(parts[1])
            profile_data['dilts_code'] = parts[2].lower()
            profile_data['display_name'] = actual_profile_key.upper()
            context.user_data["profile_data"] = profile_data
            logger.info(f"✅ Обновлен profile_data реальным профилем: {profile_data['display_name']}")
            
    except Exception as e:
        logger.error(f"⚠️ Ошибка определения реального профиля: {e}")
    
    # ====================================================
    # СООБЩЕНИЕ 1: Введение от психолога
    # ====================================================
    
    message_1 = (
        f"🧠 <b>ВАШИ ПЕРВЫЕ ИНСАЙТЫ</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я проанализировал ваши ответы.</i>\n\n"
        f"Вот что я увидел:\n\n"
    )
    
    psychologist_comment = (
        f"<i>На основе ваших ответов я вижу характерные паттерны мышления и поведения. "
        f"Это хорошая отправная точка для самопознания.</i>\n\n"
    )
    
    message_1 += psychologist_comment
    
    # Заголовок
    profile_header = profile_data.get('display_name', f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}")
    raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
    formatted_title = format_profile_title(raw_title, profile_header)
    message_1 += f"<b>{formatted_title}</b>\n\n"
    
    # Архетип
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    # Цитата
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
    
    # "Это вы если..."
    trigger = profile_card.get('trigger', '')
    if trigger:
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_1 += f"<b>🔍 ЭТО ВЫ, ЕСЛИ...</b>\n\n"
        message_1 += f"{trigger}\n\n"
    
    # Суть проблемы
    pain = profile_card.get('pain', '')
    if pain:
        pain_lines = pain.strip().split('\n')
        if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
            pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
        
        if pain.strip():
            message_1 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
            message_1 += f"{pain.strip()}"
    
    if message_1.strip():
        await query.edit_message_text(message_1.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    # ====================================================
    # СООБЩЕНИЕ 2: Практическая часть + кнопки
    # ====================================================
    
    message_2 = ""
    
    # Инструмент
    tool = profile_card.get('immediate_tool', '')
    if tool:
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            message_2 += f"<b>🛠 ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>\n\n"
            message_2 += f"<i>Что можно сделать прямо сейчас:</i>\n\n"
            message_2 += f"{tool.strip()}\n\n"
    
    # Что дальше
    cta = profile_card.get('cta', '')
    if cta:
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_2 += f"<b>🚀 СЛЕДУЮЩИЕ ШАГИ</b>\n\n"
            message_2 += f"{cta.strip()}\n\n"
    
    # Разделительная линия
    message_2 += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Призыв к действию от психолога
    message_2 += (
        f"🧠 <b>ЧТО ДАЛЬШЕ В НАШЕМ ПУТЕШЕСТВИИ?</b>\n\n"
        f"<i>Это только начало вашего пути к самопознанию.</i>\n\n"
    )
    
    if not has_shared:
        message_2 += (
            f"<b>🎁 БОНУС ЗА РЕПОСТ:</b>\n"
            f"Поделитесь открытием с друзьями и получите дополнительный материал.\n\n"
        )
    else:
        message_2 += (
            f"<b>🎉 БОНУС ГОТОВ!</b>\n"
            f"Спасибо за репост! Ваш подарок ждёт вас.\n\n"
        )
    
    # Определяем кнопки
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться и получить бонус", callback_data="get_gift")],
            [InlineKeyboardButton("🧠 Полное описание профиля от психолога", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти исследование заново", callback_data="restart_test")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Забрать бонус", callback_data="open_gift")],
            [InlineKeyboardButton("🧠 Полное описание профиля от психолога", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти исследование заново", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS

# ============================================
# ОБНОВЛЕННЫЕ ФУНКЦИИ ШАРИНГА
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ"""
    query = update.callback_query
    await query.answer()
    
    instruction_text = (
        f"🧠 <b>ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ</b>\n\n"
        
        f"Иногда самое полезное, что мы можем сделать для близких —\n"
        f"дать им зеркало.\n\n"
        
        f"<i>Поделитесь этим зеркалом с теми, кому оно может быть важно.</i>\n\n"
        
        f"⚔️ <b>А в благодарность — получите свой Меч:</b>\n"
        f"Терапевтическая сказка <b>«Мастер Меча»</b>\n\n"
        
        f"📖 <b>Эта сказка работает с тем, что мешает вам\n"
        f"«расправить плечи» на уровне убеждений.</b>\n\n"
        
        f"Она мягко трансформирует те ограничивающие установки,\n"
        f"которые создают невидимую тяжесть на ваших плечах.\n\n"
        
        f"🔗 <i>Просто нажмите кнопку ниже —\n"
        f"я подготовлю сообщение для друзей.</i>"
    )
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    keyboard = [
        [InlineKeyboardButton("🪞 Передать зеркало другу", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился — получить сказку", callback_data="confirm_share")],
        [InlineKeyboardButton("Продолжить без этого →", callback_data="skip_share")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    return GIFT_SCREEN

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОКАЗ СКАЗКИ «МАСТЕР МЕЧА»"""
    query = update.callback_query
    await query.answer()
    
    # Используем существующую ссылку
    GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
    
    gift_text = (
        f"⚔️ <b>ВАШ МЕЧ ГОТОВ!</b>\n\n"
        
        f"📚 <b>Терапевтическая сказка «Мастер Меча»</b>\n\n"
        
        f"Эта сказка работает именно с тем, что мешает вам\n"
        f"расправить плечи на уровне убеждений.\n\n"
        
        f"<i>Она не «ломает» старые установки,\n"
        f"а создаёт пространство для новых —\n"
        f"тех, что позволяют стоять прямо и легко.</i>\n\n"
        
        f"💡 <b>Как читать для максимального эффекта:</b>\n"
        f"1. Прочитайте перед сном\n"
        f"2. Ищите в тексте «металл» (вашу истинную природу)\n"
        f"3. Отмечайте «зазубрины» (ваши ограничения)\n"
        f"4. Обращайте внимание на символы тяжести/лёгкости\n\n"
        
        f"<i>Приятного чтения и лёгкости в плечах!</i> 🪶✨"
    )
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Открыть сказку «Мастер Меча»", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Назад к результатам", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(gift_text, reply_markup=reply_markup, parse_mode="HTML")
    return OPEN_GIFT_SCREEN

# ============================================
# ЭКРАНЫ ПЛАТЕЖНОЙ СИСТЕМЫ
# ============================================

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy для получения полного описания профиля"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Проверяем, есть ли результаты теста
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        # Пользователь еще не прошел тест
        keyboard = [
            [InlineKeyboardButton("🧠 Пройти тест для знакомства", callback_data="start_test")],
            [InlineKeyboardButton("💎 Получить описание без теста", callback_data="buy_without_test")]
        ]
        
        await update.message.reply_text(
            f"🧠 *{user_name}*, чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
            f"давайте сначала познакомимся поближе через тест.\n\n"
            f"💎 *Что вы получите в полном описании профиля:*\n"
            f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
            f"• 🎯 Конкретные паттерны поведения и мышления\n"
            f"• 🚀 Рекомендации по развитию от психолога\n"
            f"• 💡 Практические инструменты для жизни\n\n"
            f"💰 *Стоимость:* 1 руб (тестовый режим)\n"
            f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
            f"*Выберите действие:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Если есть результаты теста, используем профиль пользователя
    profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    context.user_data["pending_payment_profile"] = profile_code
    
    await show_payment_screen(update, context)

async def buy_without_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка без прохождения теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["pending_payment_profile"] = "SA_1_DEF"
    
    await show_payment_screen(update, context)

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран создания платежа"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    profile_data = context.user_data.get("profile_data")
    
    if profile_data and 'display_name' in profile_data:
        profile_code = profile_data['display_name']
        logger.info(f"✅ Использую РЕАЛЬНЫЙ профиль из теста: {profile_code}")
    else:
        profile_code = context.user_data.get("pending_payment_profile", "SA_1_DEF")
        logger.info(f"⚠️ Использую запасной профиль: {profile_code}")
    
    context.user_data["pending_payment_profile"] = profile_code
    
    if query:
        await query.edit_message_text(
            f"💳 *СОЗДАЮ ПЛАТЕЖ...*\n\n"
            f"🧠 *Виртуальный психолог Вариатика*\n"
            f"👤 *Клиент:* {user_name}\n"
            f"📊 *Профиль:* `{profile_code}`\n"
            f"💰 *Сумма:* 1 руб (тестовый режим)\n\n"
            f"⏳ *Создаю ссылку для оплаты...*",
            parse_mode='Markdown'
        )
    
    # Создаем платеж через API с суммой 1 рубль
    payment_result = await create_payment_advanced(user_id, profile_code, 1.00)
    
    if not payment_result.get("success"):
        error_msg = payment_result.get("error", "Неизвестная ошибка")
        details = payment_result.get("details", "")
        
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data="buy_without_test")]]
        
        error_text = f"❌ *Ошибка при создании платежа:*\n`{error_msg}`"
        if details:
            error_text += f"\n\n`{details[:100]}`"
        
        if query:
            await query.edit_message_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return
    
    # Сохраняем информацию о платеже
    payment_id = payment_result["payment_id"]
    confirmation_url = payment_result["confirmation_url"]
    
    context.user_data["last_payment_id"] = payment_id
    context.user_data["last_payment_profile"] = profile_code
    
    invoice_info = ""
    invoice_type = payment_result.get('invoice_type', 'yookassa_invoice')
    available_methods = payment_result.get('available_methods', 'all')
    
    if invoice_type == 'yookassa_invoice' and available_methods == 'all':
        invoice_info = (
            "\n💡 *ВСЕ способы оплаты доступны:*\n"
            "• СБП (Сбербанк Онлайн)\n"
            "• ЮMoney\n"
            "• Банковские карты (Visa/Mastercard/Мир)\n"
            "• Тинькофф, Альфа-Банк\n"
            "• И другие\n"
        )
    
    # Финальное сообщение пользователю
    message_text = (
        f"✅ *ПЛАТЕЖ СОЗДАН!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *Клиент:* {user_name}\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"📋 *ID платежа:* `{payment_id}`\n"
        f"💰 *Сумма:* 1 руб (тестовый режим)\n"
        f"{invoice_info}"
        f"\n🔒 *Защита от дублей:* ✅ активна\n"
        f"📊 *Профиль сохранен:* ✅ `{profile_code}`\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты:\n"
        f"1. Вы получите уведомление\n"
        f"2. Ссылка на персональное описание профиля придет автоматически\n"
        f"3. Профиль `{profile_code}` будет сохранен"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ (тест)", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    if query:
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    return PAYMENT_SCREEN

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    
    await query.edit_message_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС ПЛАТЕЖА...*\n\n"
        f"📋 *ID:* `{payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    # Проверяем статус через API
    status_result = await check_payment_status_api(payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        
        keyboard = [[InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")]]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    status = status_result.get("status", "unknown")
    
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания профиля нажмите кнопку ниже:"
        )
        
        keyboard = [[InlineKeyboardButton("📥 ПОЛУЧИТЬ ОПИСАНИЕ ПРОФИЛЯ", callback_data=f"get_materials_{payment_id}")]]
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты нажмите кнопку ниже:*"
        )
        
        payment_data = context.user_data.get("payment_data", {})
        confirmation_url = payment_data.get(payment_id, {}).get("confirmation_url")
        
        if confirmation_url:
            keyboard = [[InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=confirmation_url)]]
        else:
            keyboard = [[InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")]]
        
    else:
        message = (
            f"📊 *СТАТУС ПЛАТЕЖА:* `{status}`\n\n"
            f"📋 *ID:* `{payment_id}`"
        )
        keyboard = [[InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")]]
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def get_materials_callback_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов после оплаты"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    user_id = update.effective_user.id
    
    await query.edit_message_text(
        f"📦 *ПОЛУЧАЮ МАТЕРИАЛЫ...*\n\n"
        f"📋 *ID платежа:* `{payment_id}`\n\n"
        f"⏳ Загружаю ссылки...",
        parse_mode='Markdown'
    )
    
    # Получаем материалы через API
    materials_result = await get_materials_link_api(payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"get_materials_{payment_id}")]]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПОЛУЧЕНИИ МАТЕРИАЛОВ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        await query.edit_message_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    # Показываем ссылку на материалы
    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)]]
    
    await query.edit_message_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"🎉 Ваше персональное описание профиля успешно подготовлено!\n\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 1 руб (тестовый режим)\n\n"
        f"📚 *Что вы получили:*\n"
        f"• 📖 <b>Полное описание вашего профиля</b> (15+ страниц)\n"
        f"• 🎯 Ключевые паттерны поведения и мышления\n"
        f"• 🚀 Рекомендации по развитию от психолога\n"
        f"• ⚠️ Ограничения и как их обходить\n"
        f"• 💡 Практические инструменты для ежедневного применения\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания вашего персонального руководства:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

# ============================================
# ОСТАЛЬНЫЕ ЭКРАНЫ (ОБНОВЛЕННЫЕ)
# ============================================

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    await query.answer("✅ Спасибо за репост! Ваш бонус готов!")
    
    context.user_data["has_shared"] = True
    
    return await show_results_screen(update, context)

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск шаринга"""
    query = update.callback_query
    await query.answer("Продолжаем без репоста")
    
    return await show_results_screen(update, context)

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНОЕ ОПИСАНИЕ ПРОФИЛЯ ОТ ПСИХОЛОГА"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, есть ли результаты теста
    profile_data = context.user_data.get("profile_data")
    
    if profile_data:
        profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
        profile_info = f"\n📊 <b>Ваш профиль:</b> <code>{profile_code}</code>\n"
        personal_note = f"\n<i>Это описание будет создано персонально для вас на основе ваших ответов.</i>"
    else:
        profile_info = "\n📊 <b>Профиль:</b> будет определен после теста\n"
        personal_note = f"\n<i>После теста я подготовлю персональное описание именно для вас.</i>"
    
    package_text = (
        f"🧠 <b>ПОЛНОЕ ОПИСАНИЕ ВАШЕГО ПРОФИЛЯ</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я подготовлю для вас:</i>\n\n"
        f"• 📖 <b>Детальный анализ личности</b> (15+ страниц)\n"
        f"• 🎯 <b>Ключевые паттерны поведения</b> с примерами\n"
        f"• 🚀 <b>Точки роста</b> и рекомендации по развитию\n"
        f"• ⚠️ <b>Потенциальные ограничения</b> и как их обходить\n"
        f"• 💡 <b>Практические инструменты</b> для ежедневного применения\n"
        f"• 🔍 <b>Сильные стороны</b> и как их использовать\n\n"
        f"{profile_info}"
        f"<b>Стоимость:</b> 1 ₽ (тестовый режим)\n\n"
        f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
        f"{personal_note}\n\n"
        f"<b>Это ваше персональное руководство по самопознанию!</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🧠 Получить описание профиля за 1 руб", callback_data="buy_package")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

async def buy_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка пакета из экрана результатов"""
    query = update.callback_query
    await query.answer()
    
    # Переходим к созданию платежа
    return await buy_command(update, context)

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Назад' - возвращает к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    return await start_test(update, context)

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    fake_update = Update(update.update_id + 1, message=query.message)
    return await start(fake_update, context)

# ============================================
# КОМАНДА /START С КНОПКОЙ "ДЕТАЛИ" - ОБНОВЛЕННАЯ ВЕРСИЯ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основная команда /start с двумя кнопками"""
    user = update.effective_user
    
    welcome_text = (
        f"{user.first_name}, привет! 👋\n\n"
        f"Я — Виртуальный психолог Вариатика.\n\n"
        f"За 15 минут узнаете о себе то, что обычно остаётся невидимым.\n"
        f"Увидите скрытые паттерны, которые управляют вашими решениями.\n\n"
        f"А главное — узнаете то, о себе знать действительно нужно.\n"
        f"То, что даст точку опоры для роста.\n\n"
        f"Вас ждёт:\n\n"
        f"1️⃣ Адаптивный тест (4 этапа)\n"
        f"   ↳ Поймёте свой уникальный профиль\n\n"
        f"2️⃣ Персональные материалы\n"
        f"   ↳ Узнаете куда направлять усилия\n\n"
        f"Начнём исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("Начать исследование →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А зачем это вообще?", callback_data="why_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return None

# ============================================
# КНОПКА "ДЕТАЛИ" (why_details)
# ============================================

async def why_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Детали'"""
    query = update.callback_query
    await query.answer()
    
    details_text = """🎭 Немного правды с юмором...

Как говорится: 'Нет здоровых, есть не дообследованные!' 
Я ваш виртуальный психолог — дообследую 😉

🧠 Что я умею (кроме шуток):
• Вижу паттерны там, где вы видите хаос
• Нахожу систему там, где вы видите случайности  
• Обнаруживаю 'прошивку' вашего восприятия

🎯 Конкретно в тесте:

1️⃣ Конфигурация восприятия
   ↳ Как ваш разум фильтрует реальность

2️⃣ Конфигурация мышления  
   ↳ Как обрабатываете информацию

3️⃣ Паттерны поведения
   ↳ Что делаете 'на автомате'

4️⃣ Точка роста
   ↳ Куда двигаться осознанно

⏱ 15 минут вместо лет терапии!
Потому что в 21 веке даже самопознание должно быть эффективным!"""
    
    keyboard = [[InlineKeyboardButton("Ладно, убедил! Начинаем →", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup)

# ============================================
# НАЧАЛО ТЕСТА
# ============================================

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    logger.info(f"User {update.effective_user.id} начал знакомство с психологом")
    
    return await show_stage_1_intro(update, context)

# ============================================
# ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ (ОБНОВЛЕННЫЕ ЭКРАНЫ)
# ============================================

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 1"""
    query = update.callback_query
    
    intro_text = (
        f"🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"Как ваш виртуальный психолог, я начну с понимания вашей базовой конфигурации восприятия.\n\n"
        f"<b>Что мы исследуем:</b>\n"
        f"• Куда направлено ваше внимание\n"
        f"• Что вызывает тревогу\n"
        f"• Как вы обрабатываете информацию\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"<i>Отвечайте честно — это поможет мне лучше понять вас.</i>\n\n"
        f"Начнем наше исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage1_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ КОНФИГУРАЦИЯ ВОСПРИЯТИЯ?</b>\n\n"
        f"Это базовая программа, через которую вы воспринимаете мир.\n\n"
        f"<b>Мы измеряем две оси:</b>\n\n"
        f"<b>1. Направленность внимания:</b>\n"
        f"• ЭКСТЕРНАЛЬНАЯ — фокус на внешнем мире (люди, события)\n"
        f"• ИНТЕРНАЛЬНАЯ — фокус на внутреннем мире (мысли, чувства)\n\n"
        f"<b>2. Доминирующая тревога:</b>\n"
        f"• СИМВОЛИЧЕСКАЯ — страх отвержения, непонимания\n"
        f"• МАТЕРИАЛЬНАЯ — страх потери контроля, ресурсов\n\n"
        f"<b>Результат:</b> Один из четырёх типов восприятия\n\n"
        f"Это определит, какие вопросы вы получите на следующих этапах."
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage1_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 1"""
    return await show_stage_1_intro(update, context)

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage1_current"] = 0
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 1"""
    query = update.callback_query
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(STAGE_1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_1_QUESTIONS))
    
    tip = PSYCHOLOGIST_TIPS["stage1"][min(current, len(PSYCHOLOGIST_TIPS["stage1"])-1)]
    
    # Убираем номер вопроса из текста вопроса, оставляем только заголовок этапа
    question_text = (
        f"🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"{question['text']}\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage1_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 1"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_1
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_1
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_1_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_1
        
        for axis, score in selected_option.get("scores", {}).items():
            context.user_data["scores"][axis] += score
        
        logger.info(f"User {update.effective_user.id}: Stage 1 Q{current} -> {option_id}")
        
        context.user_data["stage1_current"] = current + 1
        return await ask_stage_1_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАП 1"""
    query = update.callback_query
    scores = context.user_data.get("scores", {})
    
    clarifications_needed = need_clarification_stage1(scores)
    
    if clarifications_needed and not context.user_data.get("stage1_clarified", False):
        context.user_data["stage1_clarifications"] = clarifications_needed
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage1"
        
        logger.info(f"User {update.effective_user.id}: Stage 1 needs clarification")
        return await ask_clarification_question(update, context)
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🧠 Конфигурация восприятия определена\n\n"
        f"<i>Хорошая работа! Теперь я лучше понимаю, как вы видите мир.</i>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: конфигурация мышления.\n\n"
        f"Готовы продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить исследование", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ (ОБНОВЛЕННЫЕ ЭКРАНЫ)
# ============================================

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Теперь исследуем ваш тип мышления внутри системы восприятия.\n\n"
        f"<b>Что мы узнаем:</b>\n"
        f"• Ваш текущий способ обработки информации\n"
        f"• Уровень развития мышления\n"
        f"• Характерные паттерны мыслительных процессов\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~4 минуты\n\n"
        f"Готовы продолжить наше исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage2_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ КОНФИГУРАЦИЯ МЫШЛЕНИЯ?</b>\n\n"
        f"Это тип вашего мышления внутри системы восприятия.\n\n"
        f"<b>9 типов конфигураций мышления:</b>\n\n"
        f"1️⃣ ДЕФИЦИТАРНЫЙ — базовая нужда не удовлетворена\n"
        f"2️⃣ ПОИСКОВЫЙ — активный поиск решения\n"
        f"3️⃣ КОНСТРУКТИВНЫЙ — создание стабильной базы\n"
        f"4️⃣ КРИЗИСНЫЙ — переосмысление достигнутого\n"
        f"5️⃣ ИНТЕГРАТИВНЫЙ — уверенное владение\n"
        f"6️⃣ АЛЬТРУИСТИЧЕСКИЙ — служение другим\n"
        f"7️⃣ МУДРЕЦКИЙ — глубокое понимание\n"
        f"8️⃣ СИСТЕМНЫЙ — управление на системном уровне\n"
        f"9️⃣ ТРАНСЦЕНДЕНТНЫЙ — выход за пределы\n\n"
        f"<b>Результат:</b> Ваш текущий способ обработки информации"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 2"""
    return await show_stage_2_intro(update, context)

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    current = context.user_data.get("stage2_current", 0)
    
    questions = STAGE_2_QUESTIONS.get(perception_type, STAGE_2_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    
    if current >= len(questions):
        return await finish_stage_2(update, context)
    
    question = questions[current]
    progress = calculate_progress(current + 1, len(questions))
    
    tip = PSYCHOLOGIST_TIPS["stage2"][min(current, len(PSYCHOLOGIST_TIPS["stage2"])-1)]
    
    # Убираем номер вопроса из текста вопроса, оставляем только заголовок этапа
    question_text = (
        f"🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"{question['text']}\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for level_num, answer_text in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                answer_text, 
                callback_data=f"stage2_{current}_{level_num}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_2
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_2
        
        current = int(parts[1])
        selected_level = parts[2]
        
        perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
        
        scoring_table = STAGE_2_SCORING.get(perception_type, {})
        if current in scoring_table and selected_level in scoring_table[current]:
            if "stage2_level_scores_dict" not in context.user_data:
                context.user_data["stage2_level_scores_dict"] = {
                    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
                    "6": 0, "7": 0, "8": 0, "9": 0
                }
            
            points = scoring_table[current][selected_level]
            context.user_data["stage2_level_scores_dict"][selected_level] += points
            
            logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> level={selected_level} (+{points} points)")
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2"""
    query = update.callback_query
    level_scores_dict = context.user_data.get("stage2_level_scores_dict", {"1": 0})
    
    needs_clarification = need_clarification_stage2(level_scores_dict)
    
    if needs_clarification and not context.user_data.get("stage2_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage2"
        
        logger.info(f"User {update.effective_user.id}: Stage 2 needs clarification")
        return await ask_clarification_question(update, context)
    
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    context.user_data["thinking_level"] = thinking_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🧠 Конфигурация мышления определена\n\n"
        f"<i>Отличная работа! Теперь я вижу, как вы обрабатываете информацию.</i>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готовы продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить исследование", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

# ============================================
# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ (ОБНОВЛЕННЫЕ ЭКРАНЫ)
# ============================================

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"Теперь исследуем ваши автоматические реакции и поведенческие паттерны.\n\n"
        f"<b>Почему это важно:</b>\n"
        f"• Мы часто думаем одно, а делаем другое\n"
        f"• Поведение точнее показывает установки, чем мысли\n"
        f"• Автоматические реакции раскрывают глубинные программы\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готовы исследовать свои паттерны поведения?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage3_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ?</b>\n\n"
        f"Это автоматические реакции — то, что вы делаете не задумываясь.\n\n"
        f"<b>Зачем это нужно:</b>\n\n"
        f"Вы можете думать одно, а делать другое.\n\n"
        f"Ваше реальное поведение точнее показывает глубинные установки, чем ваши представления о себе.\n\n"
        f"Мы зададим вопросы о конкретных действиях, чтобы уточнить ваши паттерны.\n\n"
        f"<b>Результат:</b> Подтверждение или корректировка типа из ЭТАПА 2"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 3"""
    return await show_stage_3_intro(update, context)

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    current = context.user_data.get("stage3_current", 0)
    
    if current >= len(STAGE_3_QUESTIONS):
        return await finish_stage_3(update, context)
    
    question = STAGE_3_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_3_QUESTIONS))
    
    tip = PSYCHOLOGIST_TIPS["stage3"][min(current, len(PSYCHOLOGIST_TIPS["stage3"])-1)]
    
    # Убираем номер вопроса из текста вопроса, оставляем только заголовок этапа
    question_text = (
        f"🧠 <b>ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"{question['text']}\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage3_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_3
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_3
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_3_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_3
        
        level = selected_option.get("level", 1)
        context.user_data["stage3_level_scores"].append(level)
        
        logger.info(f"User {update.effective_user.id}: Stage 3 Q{current} -> {option_id} (level={level})")
        
        context.user_data["stage3_current"] = current + 1
        return await ask_stage_3_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3"""
    query = update.callback_query
    
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    
    needs_clarification = need_clarification_stage3(stage2_level, stage3_scores)
    
    if needs_clarification and not context.user_data.get("stage3_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage3"
        
        logger.info(f"User {update.effective_user.id}: Stage 3 needs clarification")
        return await ask_clarification_question(update, context)
    
    final_level = calculate_final_level(stage2_level, stage3_scores)
    context.user_data["final_level"] = final_level
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, final_level={final_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 3 ЗАВЕРШЁН!</b>\n\n"
        f"🧠 Поведенческие паттерны проанализированы\n\n"
        f"<i>Отлично! Теперь я вижу полную картину ваших автоматических реакций.</i>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 4</b>: конфликт логических уровней.\n\n"
        f"Это последний этап! Готовы?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить исследование", callback_data="show_stage_4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

# ============================================
# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ (ОБНОВЛЕННЫЕ ЭКРАНЫ)
# ============================================

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"Последний этап нашего исследования определит, на каком уровне находится ваша главная точка роста.\n\n"
        f"<b>Что мы узнаем:</b>\n"
        f"• Где находится основное напряжение в вашей жизни\n"
        f"• На каком уровне нужно работать для изменений\n"
        f"• Какие ресурсы вам нужны для роста\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Это завершающий этап нашего исследования! Готовы?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ?</b>\n\n"
        f"Это модель Роберта Дилтса, которая показывает, на каком уровне находится проблема.\n\n"
        f"<b>5 уровней (снизу вверх):</b>\n\n"
        f"1️⃣ ОКРУЖЕНИЕ — внешние условия\n"
        f"2️⃣ ПОВЕДЕНИЕ — ваши действия\n"
        f"3️⃣ СПОСОБНОСТИ — ваши навыки\n"
        f"4️⃣ ЦЕННОСТИ — ваши мотивы\n"
        f"5️⃣ ИДЕНТИЧНОСТЬ — кто вы\n\n"
        f"<b>Принцип:</b> Проблема на нижнем уровне решается на верхнем.\n\n"
        f"<b>Результат:</b> Ваша точка роста"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 4"""
    return await show_stage_4_intro(update, context)

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    current = context.user_data.get("stage4_current", 0)
    
    if current >= len(STAGE_4_QUESTIONS):
        return await finish_stage_4(update, context)
    
    question = STAGE_4_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_4_QUESTIONS))
    
    tip = PSYCHOLOGIST_TIPS["stage4"][min(current, len(PSYCHOLOGIST_TIPS["stage4"])-1)]
    
    # Убираем номер вопроса из текста вопроса, оставляем только заголовок этапа
    question_text = (
        f"🧠 <b>ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"{question['text']}\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage4_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 4"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_4
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_4
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_4_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_4
        
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        logger.info(f"User {update.effective_user.id}: Stage 4 Q{current} -> {option_id} (dilts={dilts})")
        
        context.user_data["stage4_current"] = current + 1
        return await ask_stage_4_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4"""
    query = update.callback_query
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    
    needs_clarification = need_clarification_stage4(dilts_answers)
    
    if needs_clarification and not context.user_data.get("stage4_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage4"
        
        logger.info(f"User {update.effective_user.id}: Stage 4 needs clarification (tie)")
        return await ask_clarification_question(update, context)
    
    profile_data = calculate_profile_final(context.user_data)
    coherence = profile_data["coherence"]
    context.user_data["profile_data"] = profile_data
    
    loading_text = (
        f"🧠 <b>АНАЛИЗИРУЮ РЕЗУЛЬТАТЫ...</b>\n\n"
        f"<i>Собираю все данные нашего исследования в единую картину.</i>\n\n"
        f"⏳ Это займет несколько секунд..."
    )
    await query.edit_message_text(loading_text, parse_mode="HTML")
    await asyncio.sleep(2)
    
    return await show_results_screen(update, context)

# ============================================
# ФУНКЦИИ УТОЧНЕНИЙ
# ============================================

async def ask_clarification_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт уточняющий вопрос"""
    query = update.callback_query
    
    clarification_stage = context.user_data.get("clarification_stage")
    current = context.user_data.get("clarification_current", 0)
    
    if clarification_stage == "stage1":
        clarifications = context.user_data.get("stage1_clarifications", [])
        if current >= len(clarifications):
            context.user_data["stage1_clarified"] = True
            return await finish_stage_1(update, context)
        
        clarification_type = clarifications[current]
        questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
        
        if not questions:
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        question = questions[0]
        
    elif clarification_stage == "stage2":
        questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
        if current >= len(questions):
            context.user_data["stage2_clarified"] = True
            return await finish_stage_2(update, context)
        question = questions[current]
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current >= len(questions):
            context.user_data["stage3_clarified"] = True
            return await finish_stage_3(update, context)
        question = questions[current]
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        if current >= len(questions):
            context.user_data["stage4_clarified"] = True
            return await finish_stage_4(update, context)
        question = questions[current]
    else:
        return STAGE_1
    
    if not question:
        return STAGE_1
    
    question_text = (
        f"🧠 <b>УТОЧНЯЮЩИЙ ВОПРОС</b>\n\n"
        f"{question['text']}\n\n"
        f"<i>Это поможет мне точнее определить ваш профиль.</i>"
    )
    
    keyboard = []
    if clarification_stage in ["stage1", "stage4"]:
        for option_id, option in question["options"].items():
            keyboard.append([
                InlineKeyboardButton(
                    option["text"], 
                    callback_data=f"clarify_{clarification_stage}_{current}_{option_id}"
                )
            ])
    else:
        for level, answer_text in question["options"].items():
            keyboard.append([
                InlineKeyboardButton(
                    answer_text, 
                    callback_data=f"clarify_{clarification_stage}_{current}_{level}"
                )
            ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return CLARIFICATION

async def handle_clarification_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на уточняющий вопрос"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    if len(parts) < 4:
        return CLARIFICATION
    
    clarification_stage = parts[1]
    current = int(parts[2])
    option_id = parts[3]
    
    if clarification_stage == "stage1":
        clarifications = context.user_data.get("stage1_clarifications", [])
        if current < len(clarifications):
            clarification_type = clarifications[current]
            questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
            if questions:
                question = questions[0]
                selected_option = question["options"].get(option_id)
                if selected_option:
                    for axis, score in selected_option.get("scores", {}).items():
                        context.user_data["scores"][axis] += score
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage2":
        questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
        if current < len(questions):
            question = questions[current]
            selected_level = option_id
            
            if "stage2_level_scores_dict" not in context.user_data:
                context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
            
            if selected_level in context.user_data["stage2_level_scores_dict"]:
                context.user_data["stage2_level_scores_dict"][selected_level] += 3
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current < len(questions):
            question = questions[current]
            selected_level = option_id
            
            if "stage3_level_scores" not in context.user_data:
                context.user_data["stage3_level_scores"] = []
            
            context.user_data["stage3_level_scores"].append(int(selected_level))
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        if current < len(questions):
            question = questions[current]
            selected_option = question["options"].get(option_id)
            if selected_option:
                dilts = selected_option.get("dilts", "ENVIRONMENT")
                context.user_data["stage4_dilts_answers"].append(dilts)
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
    
    return CLARIFICATION

# ============================================
# ОТМЕНА ТЕСТА
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "🧠 *Исследование отменено.*\n\n"
        "Если захотите продолжить наше знакомство, просто напишите:\n"
        "`/start`\n\n"
        "*Всегда готов помочь,\nВаш виртуальный психолог Вариатика* 🧠",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# ============================================
# КОМАНДА ДЛЯ ПОЛУЧЕНИЯ МАТЕРИАЛОВ
# ============================================

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials для получения материалов после оплаты"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Проверяем, есть ли сохраненный payment_id
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        await update.message.reply_text(
            f"🧠 *У вас нет активных платежей*\n\n"
            f"👤 *{user_name}*, для получения персонального описания профиля необходимо приобрести полный пакет.\n\n"
            f"💎 *Полное описание профиля от виртуального психолога:*\n"
            f"• Стоимость: 1 руб (тестовый режим)\n"
            f"• Все способы оплаты (СБП, ЮMoney, карты)\n"
            f"• Мгновенный доступ после оплаты\n"
            f"• Ваше персональное руководство по самопознанию\n\n"
            f"Используйте команду `/buy` для покупки",
            parse_mode='Markdown'
        )
        return
    
    # Пытаемся получить материалы
    await update.message.reply_text(
        f"🔍 *ПОИСК ПЕРСОНАЛЬНОГО ОПИСАНИЯ...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Проверяю доступ...",
        parse_mode='Markdown'
    )
    
    materials_result = await get_materials_link_api(last_payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        
        keyboard = [[InlineKeyboardButton("💳 Получить описание профиля", callback_data="buy_without_test")]]
        
        await update.message.reply_text(
            f"❌ *НЕ УДАЛОСЬ ПОЛУЧИТЬ МАТЕРИАЛЫ*\n\n"
            f"`{error_msg}`\n\n"
            f"Возможно, платеж еще не обработан или возникла ошибка.\n"
            f"Попробуйте позже или приобретите описание заново.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        await update.message.reply_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{last_payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    # Показываем ссылку на материалы
    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)]]
    
    await update.message.reply_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *{user_name}*, вот ваше персональное описание профиля:\n\n"
        f"📋 *ID заказа:* `{last_payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 1 руб (тестовый режим)\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

# ============================================
# КОМАНДА ДЛЯ ПРОВЕРКИ СТАТУСА
# ============================================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status для проверки статуса последнего платежа"""
    user_id = update.effective_user.id
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        await update.message.reply_text(
            "📭 *Нет активных платежей*\n\n"
            "У вас нет последних платежей для проверки.\n"
            "Используйте `/buy` для создания нового платежа.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    # Проверяем статус через API
    status_result = await check_payment_status_api(last_payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        
        await update.message.reply_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    status = status_result.get("status", "unknown")
    
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{last_payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания используйте команду:\n"
            f"`/materials`\n\n"
            f"✅ Вы получите мгновенный доступ к вашему руководству."
        )
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{last_payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты используйте команду:*\n"
            f"`/buy`\n\n"
            f"Или дождитесь обработки платежа."
        )
        
    else:
        message = (
            f"📊 *СТАТУС ПЛАТЕЖА:* `{status.upper()}`\n\n"
            f"📋 *ID:* `{last_payment_id}`\n\n"
            f"Если статус не меняется, попробуйте создать новый платеж: `/buy`"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ============================================
# ЗАКЛЮЧИТЕЛЬНОЕ СООБЩЕНИЕ ОТ ПСИХОЛОГА
# ============================================

async def show_psychologist_conclusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заключительное сообщение от психолога"""
    query = update.callback_query
    await query.answer()
    
    conclusion_text = (
        f"🧠 <b>БЛАГОДАРЮ ЗА ДОВЕРИЕ!</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я рад был помочь вам в начале пути самопознания.</i>\n\n"
        f"<b>Что дальше?</b>\n\n"
        f"1️⃣ <b>Используйте полученные инсайты</b>\n"
        f"   ↳ Обращайте внимание на обнаруженные паттерны\n\n"
        f"2️⃣ <b>Получите полное описание профиля</b>\n"
        f"   ↳ Глубокий анализ от психолога\n"
        f"   ↳ Конкретные рекомендации для вас\n\n"
        f"3️⃣ <b>Возвращайтесь к тесту через 3-6 месяцев</b>\n"
        f"   ↳ Отслеживайте свой прогресс\n"
        f"   ↳ Замечайте изменения в паттернах\n\n"
        f"<i>Помните: самопознание — это путь, а не пункт назначения.</i>\n\n"
        f"Всегда готов помочь,\n"
        f"<b>Ваш виртуальный психолог Вариатика</b> 🧠"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Получить полное описание профиля", callback_data="show_package")],
        [InlineKeyboardButton("🔄 Пройти исследование заново", callback_data="restart_test")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(conclusion_text, reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🧠 ЗАПУСК ВИРТУАЛЬНОГО ПСИХОЛОГА ВАРИАТИКА")
    print("="*60)
    print("ОСНОВНЫЕ ФУНКЦИИ:")
    print("1. Виртуальный психолог для самопознания")
    print("2. Адаптивная психодиагностика (4 этапа)")
    print("3. Персональное описание профиля личности")
    print("4. Интеграция с платежной системой")
    print("="*60 + "\n")
    
    # Проверка загрузки профилей
    print("🔍 ПРОВЕРКА ЗАГРУЗКИ ПРОФИЛЕЙ")
    print("="*30)
    
    try:
        all_profiles = loader.get_all_profiles()
        print(f"📊 Всего профилей загружено: {len(all_profiles)}")
        
        for profile_type in ['sa', 'sp', 'ia', 'ip']:
            type_profiles = [p for p in all_profiles if p.lower().startswith(f"{profile_type}_")]
            print(f"🔍 {profile_type.upper()} профилей: {len(type_profiles)}")
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке профилей: {e}")
    
    print("\n💳 ПРОВЕРКА ПЛАТЕЖНОЙ СИСТЕМЫ")
    print("="*30)
    print(f"📡 API URL: {API_URL}")
    print(f"🏪 YooKassa Shop ID: {YOOKASSA_SHOP_ID if YOOKASSA_SHOP_ID else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"🔑 YooKassa Secret Key: {'✅ УСТАНОВЛЕН' if YOOKASSA_SECRET_KEY else '❌ НЕ УСТАНОВЛЕН'}")
    if YOOKASSA_SECRET_KEY:
        key_type = "БОЕВОЙ (live_)" if YOOKASSA_SECRET_KEY.startswith('live_') else "ТЕСТОВЫЙ (test_)"
        print(f"📊 Тип ключа: {key_type}")
    print("✅ Платежная система: ГОТОВА")
    print("💎 Продукт: Полное описание профиля от виртуального психолога")
    print("💰 Стоимость: 1 руб (ТЕСТОВЫЙ РЕЖИМ)")
    print("💳 Доступные способы оплаты: СБП, ЮMoney, банковские карты")
    print("="*30)
    print("🚀 Запускаю виртуального психолога...")
    
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем команды
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Добавляем обработчик для кнопки "Детали"
    application.add_handler(CallbackQueryHandler(why_details_callback, pattern="^why_details$"))
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(show_stage_1_details, pattern="^stage1_details$"),
                CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$"),
                CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            STAGE_2: [
                CallbackQueryHandler(show_stage_2_intro, pattern="^show_stage_2_intro$"),
                CallbackQueryHandler(show_stage_2_details, pattern="^stage2_details$"),
                CallbackQueryHandler(back_to_stage2_intro, pattern="^back_to_stage2_intro$"),
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(show_stage_3_intro, pattern="^show_stage_3_intro$"),
                CallbackQueryHandler(show_stage_3_details, pattern="^stage3_details$"),
                CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$"),
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4: [
                CallbackQueryHandler(show_stage_4_intro, pattern="^show_stage_4_intro$"),
                CallbackQueryHandler(show_stage_4_details, pattern="^stage4_details$"),
                CallbackQueryHandler(back_to_stage4_intro, pattern="^back_to_stage4_intro$"),
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
            ],
            CLARIFICATION: [
                CallbackQueryHandler(handle_clarification_answer, pattern="^clarify_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(buy_package_callback, pattern="^buy_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$"),
                CallbackQueryHandler(show_psychologist_conclusion, pattern="^psychologist_conclusion$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$")
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(buy_package_callback, pattern="^buy_package$")
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$")
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"),
                CallbackQueryHandler(get_materials_callback_payment, pattern="^get_materials_"),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
                CallbackQueryHandler(buy_without_test_callback, pattern="^buy_without_test$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    logger.info("🧠 Виртуальный психолог Вариатика запущен!")
    logger.info(f"📡 API: {API_URL}")
    logger.info(f"💳 YooKassa: {'✅ ACTIVE' if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY else '❌ INACTIVE'}")
    logger.info("💰 Payment system: ACTIVE (1 RUB TEST MODE, all methods)")
    logger.info("🧠 Positioning: Виртуальный психолог для самопознания")
    logger.info("💎 Product: Полное описание профиля личности")
    logger.info("🔄 Updated: Система шаринга 'Зеркало → Меч' v1.0")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
