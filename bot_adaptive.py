"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа + адаптивные уточнения + СИСТЕМА БАЛЛОВ как в карточном тесте
ВЕРСИЯ 2.0: Добавлен анализ расхождений между тестом и профилем
+ ИНТЕГРАЦИЯ Flask API для платежей
"""

import logging
import os
import asyncio
import urllib.parse
import math
import re
import time
import aiohttp
import json
from datetime import datetime
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

# Загрузка конфигурации
from config import Config

# Удаляем прямой импорт YooKassaAPI - используем Flask API
config = Config()

# Получение токена из конфига
TOKEN = config.BOT_TOKEN
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# URL вашего Flask API (из вашей архитектуры)
FLASK_API_URL = "https://testing-lichnosti-bot-1.onrender.com"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния ConversationHandler
(
    STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, 
    RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, 
    DILTS_CLARIFICATION, PAYMENT_SCREEN, PAYMENT_EMAIL, 
    PAYMENT_CHECK, PAYMENT_SUCCESS
) = range(14)

# Константы
BOT_LINK = config.BOT_LINK
GIFT_PDF_LINK = config.GIFT_PDF_LINK
AUTHOR_LINK = config.AUTHOR_LINK
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую.."
PAYMENT_LINK = config.PAYMENT_LINK
PAYMENT_AMOUNT = config.PAYMENT_AMOUNT

# ============================================
# НОВЫЕ КОНСТАНТЫ ДЛЯ v2.0
# ============================================

# Соответствие уровня (1-9) → суффикс файла
LEVEL_TO_SUFFIX = {
    1: "def",   # дефолтный
    2: "sit",   # ситуационный
    3: "con",   # конструктивный
    4: "exp",   # экспериментальный
    5: "int",   # интегративный
    6: "aut",   # автономный
    7: "val",   # ценностный
    8: "tra",   # трансцендентный
    9: "ide"    # ваше видение себя (Я)
}

# Соответствие суффикса файла → уровень Дилтса
SUFFIX_TO_DILTS = {
    "def": "ENVIRONMENT",   # окружение
    "sit": "BEHAVIOR",      # поведение
    "con": "CAPABILITIES",  # навыки
    "exp": "CAPABILITIES",  # навыки
    "int": "VALUES",        # ценности
    "aut": "VALUES",        # ценности
    "val": "VALUES",        # ценности
    "tra": "IDENTITY",      # ваше видение себя (Я)
    "ide": "IDENTITY"       # ваше видение себя (Я)
}

# ============================================
# ВОПРОСЫ ЭТАПА 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ
# ============================================

STAGE_1_QUESTIONS = [
    {
        "id": "q1_1",
        "text": "У тебя неожиданно освободился вечер.\n\nЧто звучит привлекательнее?",
        "options": {
            "a": {"text": "Позвать друзей", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Побыть одному", "scores": {"INTERNAL": 2}},
            "c": {"text": "Сходить куда-то (событие/место)", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Почитать/посмотреть что-то", "scores": {"INTERNAL": 1}}
        }
    },
    {
        "id": "q1_2",
        "text": "Что даёт тебе больше ресурса для жизни?",
        "options": {
            "a": {"text": "Люди, события, движение", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Мысли, чувства, тишина", "scores": {"INTERNAL": 2}},
            "c": {"text": "И то, и то в равной степени", "scores": {}},
            "d": {"text": "Зависит от ситуации", "scores": {}}
        }
    },
    {
        "id": "q1_3",
        "text": "Ты на вечеринке, где почти никого не знаешь.\n\nЧто происходит?",
        "options": {
            "a": {"text": "Активно знакомлюсь со всеми", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Нахожу 1-2 человек и общаюсь с ними", "scores": {"EXTERNAL": 1}},
            "c": {"text": "Держусь в стороне", "scores": {"INTERNAL": 1}},
            "d": {"text": "Ухожу при первой возможности", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_4",
        "text": "Если бы твоя жизнь была местом, это было бы:",
        "options": {
            "a": {"text": "Оживлённая площадь", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Уютная комната", "scores": {"INTERNAL": 1}},
            "c": {"text": "Открытое пространство", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Тихое уединённое место", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_5",
        "text": "Что тебя больше выбивает из равновесия?",
        "options": {
            "a": {"text": "Когда тебя не понимают", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Когда теряешь что-то важное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Когда не ясно, что происходит", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Когда всё идёт не по плану", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_6",
        "text": "Что для тебя важнее?",
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
        "text": "Вспомни последнюю сильную тревогу.\n\nО чём она была?",
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
# ВОПРОСЫ ЭТАПА 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

STAGE_2_QUESTIONS = {
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": [
        {
            "text": "Сколько у тебя близких людей?\n\n(С кем можно говорить о личном)",
            "options": {
                "1": "Нет таких",
                "2": "1-2 человека", 
                "3": "3-5 человек",
                "5": "Больше 5"
            }
        },
        {
            "text": "Как ты к этому относишься?",
            "options": {
                "1": "Мне не хватает близости",
                "2": "Я в процессе поиска своих людей",
                "3": "Меня это устраивает",
                "4": "Я не нуждаюсь в этом"
            }
        },
        {
            "text": "Как часто за месяц ты отменяешь встречи с друзьями?",
            "options": {
                "1": "Не отменяю / нет встреч",
                "3": "1-2 раза",
                "2": "3-5 раз",
                "1": "Постоянно отменяю"
            }
        },
        {
            "text": "Почему отменяешь?",
            "options": {
                "1": "Нет сил на людей",
                "2": "Эти люди не мои",
                "5": "Появились более важные дела",
                "3": "Не отменяю"
            }
        },
        {
            "text": "Как часто ты чувствуешь, что тебя не понимают?",
            "options": {
                "1": "Постоянно",
                "2": "Часто",
                "4": "Иногда",
                "3": "Редко или никогда"
            }
        },
        {
            "text": "Что ты с этим делаешь?",
            "options": {
                "1": "Пытаюсь объясниться",
                "2": "Ищу тех, кто поймёт",
                "4": "Принимаю это",
                "3": "Меня понимают"
            }
        },
        {
            "text": "Твой друг постоянно меняет компании.\n\nКак думаешь, почему?",
            "options": {
                "2": "Ищет своих людей",
                "1": "Боится близости",
                "5": "Ему везде интересно",
                "4": "Не может быть собой"
            }
        },
        {
            "text": "Что для тебя значит «найти своих людей»?",
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
            "text": "Как часто ты задаёшь себе вопрос «В чём смысл?»",
            "options": {
                "1": "Постоянно, это мучительно",
                "2": "Часто, ищу ответы",
                "4": "Иногда, это интересно",
                "5": "Редко, я знаю свой смысл"
            }
        },
        {
            "text": "Что ты чувствуешь, когда остаёшься наедине с собой?",
            "options": {
                "1": "Тревогу, пустоту",
                "2": "Вопросы без ответов",
                "4": "Спокойствие, ясность",
                "5": "Глубину, полноту"
            }
        },
        {
            "text": "Сколько времени в день ты проводишь в размышлениях?",
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
            "text": "Как ты относишься к своим переживаниям?",
            "options": {
                "1": "Боюсь их, избегаю",
                "2": "Анализирую, пытаюсь понять",
                "4": "Принимаю и наблюдаю",
                "5": "Использую как материал для роста"
            }
        },
        {
            "text": "Что для тебя значит «быть собой»?",
            "options": {
                "1": "Не знаю, кто я",
                "2": "Ищу себя",
                "4": "Знаю и принимаю себя",
                "5": "Я — это процесс, а не статус"
            }
        },
        {
            "text": "Человек погружён в экзистенциальный кризис.\n\nЧто ему делать?",
            "options": {
                "1": "Отвлечься, не думать об этом",
                "2": "Искать ответы (книги, терапия)",
                "4": "Прожить это как опыт",
                "5": "Это не кризис, а трансформация"
            }
        },
        {
            "text": "Что для тебя глубина жизни?",
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
            "text": "Сколько целей ты достиг за последний год?",
            "options": {
                "1": "Ни одной (только планировал)",
                "2": "1-2 цели",
                "4": "3-5 целей",
                "5": "Больше 5 целей"
            }
        },
        {
            "text": "Как ты себя чувствуешь, когда достигаешь цели?",
            "options": {
                "1": "Пусто (а что дальше?)",
                "2": "Радость, но ненадолго",
                "4": "Удовлетворение",
                "5": "Уже думаю о следующей"
            }
        },
        {
            "text": "Как часто ты откладываешь важные дела?",
            "options": {
                "1": "Постоянно (прокрастинация)",
                "2": "Часто",
                "4": "Иногда",
                "5": "Редко или никогда"
            }
        },
        {
            "text": "Почему откладываешь?",
            "options": {
                "1": "Страх неудачи",
                "2": "Не знаю, с чего начать",
                "4": "Жду подходящего момента",
                "5": "Не откладываю"
            }
        },
        {
            "text": "Что для тебя успех?",
            "options": {
                "1": "Не знаю, не достигал",
                "2": "Деньги, статус, признание",
                "4": "Реализация своих целей",
                "5": "Влияние и вклад в мир"
            }
        },
        {
            "text": "Как ты относишься к конкуренции?",
            "options": {
                "1": "Избегаю её",
                "2": "Боюсь проиграть",
                "4": "Мотивирует меня",
                "5": "Играю свою игру"
            }
        },
        {
            "text": "Человек хочет большего, но не действует.\n\nПочему?",
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
            "text": "Насколько упорядочена твоя жизнь?",
            "options": {
                "1": "Хаос, не могу навести порядок",
                "2": "Пытаюсь структурировать",
                "4": "Есть система, которая работает",
                "5": "Гибкая структура под задачи"
            }
        },
        {
            "text": "Что происходит, когда нарушается твой порядок?",
            "options": {
                "1": "Паника, тревога",
                "2": "Раздражение, дискомфорт",
                "4": "Адаптируюсь",
                "5": "Это часть процесса"
            }
        },
        {
            "text": "Как ты принимаешь решения?",
            "options": {
                "1": "Не могу выбрать (анализ паралич)",
                "2": "Долго взвешиваю все варианты",
                "4": "Анализирую и выбираю оптимальное",
                "5": "Быстро, на основе критериев"
            }
        },
        {
            "text": "Что для тебя понимание?",
            "options": {
                "1": "Не могу понять, как всё устроено",
                "2": "Ищу логику и закономерности",
                "4": "Вижу систему и связи",
                "5": "Создаю новые модели понимания"
            }
        },
        {
            "text": "Как ты относишься к неопределённости?",
            "options": {
                "1": "Не выношу её",
                "2": "Пытаюсь всё просчитать",
                "4": "Принимаю как данность",
                "5": "Использую как ресурс"
            }
        },
        {
            "text": "Сколько у тебя систем организации жизни?",
            "options": {
                "1": "Нет системы",
                "2": "Пробую разные, ничего не работает",
                "4": "Одна рабочая система",
                "5": "Несколько интегрированных систем"
            }
        },
        {
            "text": "Человек перегружен информацией.\n\nЧто делать?",
            "options": {
                "1": "Избегать информации",
                "2": "Пытаться всё изучить",
                "4": "Фильтровать по критериям",
                "5": "Создать систему обработки"
            }
        },
        {
            "text": "Что для тебя контроль?",
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
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": {
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
# ВОПРОСЫ ЭТАПА 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
# ============================================

STAGE_3_QUESTIONS = [
    {"id": "q3_1", "text": "Вспомни последнюю неделю.\n\nСколько раз ты сделал что-то, что потом пожалел?", "options": {"a": {"text": "Ни разу", "level": 5}, "b": {"text": "1-2 раза", "level": 3}, "c": {"text": "3-5 раз", "level": 2}, "d": {"text": "Больше 5 раз", "level": 1}}},
    {"id": "q3_2", "text": "Последний конфликт.\n\nЧто ты сделал?", "options": {"a": {"text": "Избежал", "level": 1}, "b": {"text": "Уступил", "level": 1}, "c": {"text": "Отстоял позицию", "level": 3}, "d": {"text": "Нашёл компромисс", "level": 5}}},
    {"id": "q3_3", "text": "Как ты принимаешь важные решения?", "options": {"a": {"text": "Долго мучаюсь", "level": 1}, "b": {"text": "Взвешиваю варианты", "level": 3}, "c": {"text": "Быстро, по интуиции", "level": 5}, "d": {"text": "Жду, когда решение придёт само", "level": 4}}},
    {"id": "q3_4", "text": "Как часто ты делаешь то, что не хочешь, но «надо»?", "options": {"a": {"text": "Постоянно (вся жизнь — «надо»)", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко (делаю то, что хочу)", "level": 5}}},
    {"id": "q3_5", "text": "Вспомни последнюю сильную эмоцию.\n\nЧто ты с ней сделал?", "options": {"a": {"text": "Подавил", "level": 1}, "b": {"text": "Проанализировал", "level": 3}, "c": {"text": "Выразил (слова/действия/творчество)", "level": 5}, "d": {"text": "Наблюдал за ней", "level": 4}}},
    {"id": "q3_6", "text": "Как ты относишься к своим слабостям?", "options": {"a": {"text": "Стыжусь их", "level": 1}, "b": {"text": "Пытаюсь исправить", "level": 2}, "c": {"text": "Принимаю их", "level": 4}, "d": {"text": "Вижу в них силу", "level": 6}}},
    {"id": "q3_7", "text": "Как часто ты чувствуешь, что живёшь не своей жизнью?", "options": {"a": {"text": "Постоянно", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко или никогда", "level": 5}}},
    {"id": "q3_8", "text": "Что ты делаешь, когда не знаешь, что делать?", "options": {"a": {"text": "Паникую", "level": 1}, "b": {"text": "Ищу информацию", "level": 2}, "c": {"text": "Действую методом проб", "level": 3}, "d": {"text": "Жду ясности", "level": 4}}}
]

# ============================================
# ВОПРОСЫ ЭТАПА 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

STAGE_4_QUESTIONS = [
    {"id": "q4_1", "text": "Как часто ты чувствуешь, что «что-то не так» в жизни?", "options": {"a": {"text": "Постоянно", "dilts": "IDENTITY"}, "b": {"text": "Часто", "dilts": "VALUES"}, "c": {"text": "Иногда", "dilts": "CAPABILITIES"}, "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}}},
    {"id": "q4_2", "text": "Что именно «не так»?\n\nВыбери то, что ближе всего:", "options": {"a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"}, "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"}, "c": {"text": "Не обладаю навыками для того, что хочу", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}}},
    {"id": "q4_3", "text": "Человек чувствует себя несчастным.\n\nВ чём, скорее всего, причина?", "options": {"a": {"text": "Не те люди вокруг", "dilts": "ENVIRONMENT"}, "b": {"text": "Делает не то, что хочет", "dilts": "BEHAVIOR"}, "c": {"text": "Не обладает навыками для того, что хочет", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимает, чего хочет", "dilts": "VALUES"}}},
    {"id": "q4_4", "text": "Если бы ты мог изменить что-то одно, что бы это было?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои навыки", "dilts": "CAPABILITIES"}, "d": {"text": "Своё понимание целей", "dilts": "VALUES"}}},
    {"id": "q4_5", "text": "Что для тебя сложнее всего?", "options": {"a": {"text": "Изменить внешние условия", "dilts": "ENVIRONMENT"}, "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"}, "c": {"text": "Освоить новые навыки", "dilts": "CAPABILITIES"}, "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}}},
    {"id": "q4_6", "text": "Когда ты застреваешь в проблеме, что обычно не хватает?", "options": {"a": {"text": "Ресурсов (время, деньги, связи)", "dilts": "ENVIRONMENT"}, "b": {"text": "Действий (не начинаю)", "dilts": "BEHAVIOR"}, "c": {"text": "Навыков (не умею)", "dilts": "CAPABILITIES"}, "d": {"text": "Понимания (не знаю зачем)", "dilts": "VALUES"}}},
    {"id": "q4_7", "text": "Что мешает тебе быть счастливым?", "options": {"a": {"text": "Обстоятельства", "dilts": "ENVIRONMENT"}, "b": {"text": "Мои действия", "dilts": "BEHAVIOR"}, "c": {"text": "Мои ограничения", "dilts": "CAPABILITIES"}, "d": {"text": "Я не знаю, что такое счастье", "dilts": "VALUES"}}},
    {"id": "q4_8", "text": "Если бы у тебя была волшебная палочка, что бы ты изменил?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои навыки", "dilts": "CAPABILITIES"}, "d": {"text": "Себя (кем я себя вижу)", "dilts": "IDENTITY"}}}
]

# Уровни Дилтса
DILTS_LEVELS = {
    "ENVIRONMENT": {"name": "ОКРУЖЕНИЕ", "code": "env", "description": "Проблема во внешних условиях", "solution": "Измени окружение или отношение к нему"},
    "BEHAVIOR": {"name": "ПОВЕДЕНИЕ", "code": "beh", "description": "Проблема в действиях", "solution": "Начни действовать по-другому"},
    "CAPABILITIES": {"name": "НАВЫКИ", "code": "cap", "description": "Проблема в навыках", "solution": "Освой новые навыки"},
    "VALUES": {"name": "ЦЕННОСТИ", "code": "val", "description": "Проблема в мотивации", "solution": "Найди свои истинные ценности"},
    "IDENTITY": {"name": "ВАШЕ ВИДЕНИЕ СЕБЯ (Я)", "code": "ide", "description": "Проблема в самоопределении", "solution": "Переопредели, кем ты себя видишь"}
}

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С FLASK API
# ============================================

async def create_payment_via_flask(user_id: int, payment_id: str, amount: float = 690.0) -> dict:
    """Создает платеж через Flask API"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "payment_id": payment_id,
                "user_id": user_id,
                "amount": amount,
                "email": f"user{user_id}@telegram.org"
            }
            
            async with session.post(
                f"{FLASK_API_URL}/api/create-payment",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                
                result = await response.json()
                return result
                
    except Exception as e:
        logger.error(f"Error creating payment via Flask: {e}")
        return {"success": False, "error": str(e)}

async def create_yookassa_payment_via_flask(payment_id: str, amount: float = 690.0) -> dict:
    """Создает платеж ЮKassa через Flask API"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "payment_id": payment_id,
                "amount": amount,
                "description": "Полный пакет ВАРИАТИКА - персональные рекомендации",
                "return_url": f"https://t.me/{BOT_LINK}" if BOT_LINK.startswith('@') else BOT_LINK
            }
            
            async with session.post(
                f"{FLASK_API_URL}/api/create-yookassa-payment",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                
                result = await response.json()
                return result
                
    except Exception as e:
        logger.error(f"Error creating YooKassa payment via Flask: {e}")
        return {"success": False, "error": str(e)}

async def check_payment_status_via_flask(payment_id: str) -> dict:
    """Проверяет статус платежа через Flask API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{FLASK_API_URL}/api/payment-status/{payment_id}"
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                
                result = await response.json()
                return result
                
    except Exception as e:
        logger.error(f"Error checking payment status via Flask: {e}")
        return {"success": False, "error": str(e)}

async def update_yookassa_id_via_flask(payment_id: str, yookassa_id: str) -> dict:
    """Обновляет ID ЮKassa через Flask API"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "payment_id": payment_id,
                "yookassa_id": yookassa_id
            }
            
            async with session.post(
                f"{FLASK_API_URL}/api/update-yookassa-id",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                
                result = await response.json()
                return result
                
    except Exception as e:
        logger.error(f"Error updating YooKassa ID via Flask: {e}")
        return {"success": False, "error": str(e)}

# ============================================
# ОСНОВНЫЕ ФУНКЦИИ БОТА (ТЕСТОВАЯ ЛОГИКА)
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%\nПройдено: {current}/{total}"

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
# ФУНКЦИИ ОБРАБОТКИ ПЛАТЕЖЕЙ (ОСНОВНЫЕ)
# ============================================

async def handle_payment_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса оплаты - через Flask API"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    payment_id = f"pay_{user_id}_{int(time.time())}"
    amount = 690.0
    
    logger.info(f"Starting payment for user {user_id}, payment_id: {payment_id}")
    
    try:
        # Шаг 1: Создаем запись платежа в БД через Flask API
        logger.info("Step 1: Creating payment in DB via Flask API")
        db_result = await create_payment_via_flask(user_id, payment_id, amount)
        
        if not db_result.get("success", False):
            error_msg = db_result.get("error", "Неизвестная ошибка при создании платежа в БД")
            raise Exception(f"Ошибка создания платежа в БД: {error_msg}")
        
        logger.info(f"Payment created in DB: {db_result}")
        
        # Шаг 2: Создаем платеж в ЮKassa через Flask API
        logger.info("Step 2: Creating YooKassa payment via Flask API")
        yookassa_result = await create_yookassa_payment_via_flask(payment_id, amount)
        
        if not yookassa_result.get("success", False):
            error_msg = yookassa_result.get("error", "Неизвестная ошибка при создании платежа ЮKassa")
            raise Exception(f"Ошибка создания платежа ЮKassa: {error_msg}")
        
        logger.info(f"YooKassa payment created: {yookassa_result}")
        
        # Шаг 3: Обновляем ID ЮKassa в БД
        yookassa_id = yookassa_result.get("yookassa_id")
        if yookassa_id:
            logger.info(f"Step 3: Updating YooKassa ID: {yookassa_id}")
            update_result = await update_yookassa_id_via_flask(payment_id, yookassa_id)
            if not update_result.get("success", False):
                logger.warning(f"Failed to update YooKassa ID: {update_result.get('error')}")
        
        # Формируем результат платежа
        payment_result = {
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "payment_url": yookassa_result.get("payment_url", ""),
            "amount": amount,
            "status": yookassa_result.get("status", "pending"),
            "success": True
        }
        
        # Сохраняем данные платежа в context
        context.user_data["current_payment"] = {
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "payment_url": payment_result["payment_url"],
            "amount": amount,
            "status": payment_result["status"],
            "created_at": datetime.now().isoformat()
        }
        
        # Показываем экран оплаты
        return await show_payment_screen(update, context, payment_result)
        
    except Exception as e:
        logger.error(f"Payment creation error: {e}", exc_info=True)
        
        error_text = (
            f"❌ <b>ОШИБКА СОЗДАНИЯ ПЛАТЕЖА</b>\n\n"
            f"{str(e)}\n\n"
            f"Пожалуйста, попробуйте позже или свяжитесь с поддержкой."
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="start_payment")],
            [InlineKeyboardButton("📞 Поддержка", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode="HTML")
        return PAYMENT_SCREEN

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_result: dict = None):
    """Экран оплаты"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if not payment_result and "current_payment" in context.user_data:
        payment_data = context.user_data["current_payment"]
        payment_result = {
            "payment_id": payment_data["payment_id"],
            "payment_url": payment_data["payment_url"],
            "amount": payment_data["amount"],
            "status": payment_data.get("status", "pending")
        }
    elif not payment_result:
        error_text = "❌ Информация о платеже не найдена. Пожалуйста, начните заново."
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(error_text, reply_markup=reply_markup, parse_mode="HTML")
        return PAYMENT_SCREEN
    
    payment_text = (
        f"💎 <b>ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
        f"<b>Что входит:</b>\n"
        f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
        f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
        f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
        f"• Персональные рекомендации по развитию\n"
        f"• Карта сильных и слабых сторон\n\n"
        f"<b>Цена:</b> 690 ₽\n"
        f"<b>ID заказа:</b> <code>{payment_result['payment_id'][:8]}...</code>\n\n"
        f"<b>📋 ИНСТРУКЦИЯ:</b>\n"
        f"1. Нажмите «💳 Оплатить»\n"
        f"2. Оплатите в открывшемся окне\n"
        f"3. Вернитесь в бота и нажмите «🔄 Проверить оплату»\n\n"
        f"<i>После успешной оплаты файлы будут отправлены автоматически.</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton(
            f"💳 Оплатить 690 ₽",
            url=payment_result["payment_url"]
        )],
        [InlineKeyboardButton(
            "🔄 Проверить оплату",
            callback_data=f"check_payment_{payment_result['payment_id']}"
        )],
        [
            InlineKeyboardButton("📞 Поддержка", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel_payment")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(payment_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(payment_text, reply_markup=reply_markup, parse_mode="HTML")
    
    return PAYMENT_SCREEN

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа через Flask API"""
    query = update.callback_query
    await query.answer("🔍 Проверяем оплату...")
    
    # Извлекаем payment_id из callback_data
    payment_id = query.data.replace("check_payment_", "")
    
    if not payment_id:
        payment_data = context.user_data.get("current_payment", {})
        payment_id = payment_data.get("payment_id")
    
    if not payment_id:
        await query.answer("❌ ID платежа не найден", show_alert=True)
        return PAYMENT_SCREEN
    
    logger.info(f"Checking payment status for: {payment_id}")
    
    try:
        # Проверяем статус через Flask API
        status_result = await check_payment_status_via_flask(payment_id)
        
        if not status_result.get("success", False):
            error_msg = status_result.get("error", "Неизвестная ошибка")
            raise Exception(f"Ошибка проверки статуса: {error_msg}")
        
        payment_status = status_result.get("status", "unknown")
        logger.info(f"Payment status for {payment_id}: {payment_status}")
        
        if payment_status == "succeeded":
            # ✅ Успешная оплата
            await query.answer("✅ Оплата прошла успешно!", show_alert=True)
            
            # Отправляем файлы
            await deliver_product(update, context, query.from_user.id)
            
            # Очищаем данные платежа
            if "current_payment" in context.user_data:
                del context.user_data["current_payment"]
            
            return PAYMENT_SUCCESS
            
        elif payment_status == "pending":
            # ⏳ Ожидание оплаты
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_payment_{payment_id}")],
                [
                    InlineKeyboardButton("💳 Оплатить", url=context.user_data.get("current_payment", {}).get("payment_url", PAYMENT_LINK)),
                    InlineKeyboardButton("📞 Поддержка", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}")
                ]
            ]
            
            await query.edit_message_text(
                f"⏳ <b>ОЖИДАНИЕ ОПЛАТЫ</b>\n\n"
                f"ID: <code>{payment_id[:8]}...</code>\n"
                f"Статус: ожидание оплаты\n\n"
                f"Если вы уже оплатили, подождите 1-2 минуты "
                f"и проверьте снова.\n\n"
                f"<i>Иногда платежи обрабатываются с задержкой.</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            
        else:
            # ❌ Неудачный платеж
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="start_payment")],
                [InlineKeyboardButton("📞 Поддержка", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}")]
            ]
            
            await query.edit_message_text(
                f"❌ <b>ПЛАТЕЖ НЕ ОПЛАЧЕН</b>\n\n"
                f"ID: <code>{payment_id[:8]}...</code>\n"
                f"Статус: {payment_status}\n\n"
                f"Попробуйте оплатить снова или обратитесь в поддержку.\n\n"
                f"<i>Если проблема повторяется, попробуйте другой способ оплаты.</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Payment status check error: {e}", exc_info=True)
        
        error_text = (
            f"⚠️ <b>ОШИБКА ПРОВЕРКИ</b>\n\n"
            f"ID: <code>{payment_id[:8]}...</code>\n"
            f"Ошибка: {str(e)}\n\n"
            f"Попробуйте позже или обратитесь в поддержку."
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("📞 Поддержка", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode="HTML")
    
    return PAYMENT_CHECK

async def deliver_product(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Доставка продукта после успешной оплаты"""
    query = update.callback_query
    
    # Показываем сообщение об успехе
    success_text = (
        "🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n"
        "✅ Ваш заказ подтвержден\n"
        "📦 Подготавливаем материалы...\n\n"
        "<i>Файлы будут отправлены в течение нескольких минут.</i>"
    )
    
    await query.edit_message_text(success_text, parse_mode="HTML")
    
    try:
        delivery_text = (
            "📚 <b>ВАШИ МАТЕРИАЛЫ ГОТОВЫ!</b>\n\n"
            "<b>Что вы получили:</b>\n\n"
            "1. <b>Полный разбор профиля</b> (PDF)\n"
            "   • Детальный анализ вашего типа\n"
            "   • Рекомендации по развитию\n"
            "   • Карта сильных сторон\n\n"
            "2. <b>Терапевтическая сказка</b> (PDF)\n"
            "   • Для трансформации восприятия\n"
            "   • Работа с внутренними конфликтами\n\n"
            "3. <b>Книга «ВАРИАТИКА»</b> (PDF)\n"
            "   • Полное руководство по системе\n"
            "   • Примеры и практики\n\n"
            "4. <b>Персональные рекомендации</b>\n"
            "   • Пошаговый план развития\n"
            "   • Инструменты для работы\n\n"
            "<b>📥 Ссылки для скачивания:</b>\n\n"
            "• Основные материалы: https://disk.yandex.ru/d/variatica_package\n"
            "• Дополнительные файлы: https://disk.yandex.ru/d/variatica_extra\n\n"
            "<b>📞 Поддержка:</b>\n"
            "Если возникли вопросы: @meysternlp\n\n"
            "<i>Спасибо за покупку! 🎁</i>"
        )
        
        # Отправляем пользователю
        await context.bot.send_message(
            chat_id=user_id,
            text=delivery_text,
            parse_mode="HTML"
        )
        
        # Обновляем исходное сообщение
        final_text = (
            "✅ <b>ЗАКАЗ ВЫПОЛНЕН!</b>\n\n"
            "Все материалы отправлены.\n"
            "Проверьте чат с ботом 📩\n\n"
            "Спасибо за покупку! 🎁\n\n"
            "<i>Если что-то не получили, напишите в поддержку: @meysternlp</i>"
        )
        
        await query.edit_message_text(final_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка доставки продукта: {e}")
        
        error_text = (
            "⚠️ <b>ОШИБКА ДОСТАВКИ</b>\n\n"
            "Файлы не были отправлены автоматически.\n"
            "Пожалуйста, обратитесь в поддержку:\n"
            f"👉 {AUTHOR_LINK}\n\n"
            "<i>При обращении укажите ID заказа.</i>"
        )
        
        await query.edit_message_text(error_text, parse_mode="HTML")

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена платежа"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем данные платежа
    if "current_payment" in context.user_data:
        del context.user_data["current_payment"]
    
    # Возвращаемся к результатам
    return await show_results_screen(update, context)

# ============================================
# ОСНОВНЫЕ КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест ВАРИАТИКА ver 2.0!</b>\n\n"
        f"🔍 <b>Узнай о себе то, что ты ещё не знаешь.</b>\n\n"
        f"<b>Этот тест поможет определить:</b>\n"
        f"• Как ты воспринимаешь реальность \n"
        f"• Каким способом обрабатываешь информацию \n"
        f"• Какие поведенческие паттерны у тебя есть \n"
        f"• Что не дает тебе расти 🚀\n\n"
        f"🎯 <b>Что тебя ждёт:</b>\n\n"
        f"1️⃣ <b>ЭТАП 1:</b> Конфигурация восприятия (8 вопросов)\n"
        f"2️⃣ <b>ЭТАП 2:</b> Конфигурация мышления (8 вопросов)\n"
        f"3️⃣ <b>ЭТАП 3:</b> Поведенческие паттерны (8 вопросов)\n"
        f"4️⃣ <b>ЭТАП 4:</b> Конфликт логических уровней (8 вопросов)\n\n"
        f"⏱ Займёт 10-15 минут\n\n"
        f"📌 Отвечай честно, как есть сейчас, а не как хотелось бы.\n\n"
        f"Готов начать? 🚀"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

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
    
    logger.info(f"User {update.effective_user.id} started test v2.0")
    
    # Показываем первый вопрос
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 1"""
    query = update.callback_query
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(STAGE_1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_1_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
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
    
    if query:
        await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    
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
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация восприятия определена: {perception_type}\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение конфигурации мышления.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="start_stage_2")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

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
    
    question_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
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
    
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    context.user_data["thinking_level"] = thinking_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация мышления определена: Уровень {thinking_level}\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="start_stage_3")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

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
    
    question_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
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
        if "stage3_level_scores" not in context.user_data:
            context.user_data["stage3_level_scores"] = []
        
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
    
    final_level = calculate_final_level(stage2_level, stage3_scores)
    context.user_data["final_level"] = final_level
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, final_level={final_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 3 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Поведенческие паттерны проанализированы\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 4</b>: конфликт логических уровней.\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="start_stage_4")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

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
    
    question_text = (
        f"<b>🎯 ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
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
        if "stage4_dilts_answers" not in context.user_data:
            context.user_data["stage4_dilts_answers"] = []
        
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
    
    dilts_level = determine_dilts_level(dilts_answers)
    dilts_code = get_dilts_code(dilts_level)
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    final_level = context.user_data.get("final_level", 1)
    
    profile_data = {
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code,
        "display_name": f"{type_code}_{final_level}_{dilts_code}",
        "type_name": perception_type,
        "level_name": get_level_name(final_level),
        "dilts_name": DILTS_LEVELS.get(dilts_level, {}).get('name', dilts_level)
    }
    
    context.user_data["profile_data"] = profile_data
    
    logger.info(f"User {update.effective_user.id}: Stage 4 complete, profile: {profile_data['display_name']}")
    
    loading_text = f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\nАнализирую твои ответы..."
    await query.edit_message_text(loading_text, parse_mode="HTML")
    await asyncio.sleep(2)
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает результаты теста"""
    query = update.callback_query
    
    profile_data = context.user_data.get("profile_data", {})
    has_shared = context.user_data.get("has_shared", False)
    
    # Формируем текст результатов
    result_text = (
        f"🎉 <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>ТВОЙ ПРОФИЛЬ:</b> {profile_data.get('display_name', 'Не определен')}\n\n"
        f"<b>Тип восприятия:</b> {profile_data.get('type_name', 'Не определен')}\n"
        f"<b>Уровень мышления:</b> {profile_data.get('level_name', 'Не определен')} ({profile_data.get('level', 1)})\n"
        f"<b>Точка роста:</b> {profile_data.get('dilts_name', 'Не определена')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if not has_shared:
        result_text += (
            f"<b>🎁 ПОДАРОК ЗА РЕПОСТ</b>\n"
            f"Поделись тестом с друзьями и получи бонусный материал.\n\n"
        )
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться и получить подарок", callback_data="get_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        result_text += (
            f"<b>🎉 ГОТОВО!</b>\n"
            f"Спасибо за репост! Твой подарок ждёт тебя.\n\n"
        )
        keyboard = [
            [InlineKeyboardButton("🎁 Забрать подарок", callback_data="open_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return RESULTS

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран подарка за репост"""
    query = update.callback_query
    await query.answer()
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    instruction_text = (
        f"<b>📤 ШАГ 1: ПОДЕЛИСЬ ССЫЛКОЙ</b>\n\n"
        f"Нажми кнопку ниже, чтобы отправить сообщение с ссылкой на тест.\n\n"
        f"После того как отправишь, вернись сюда и нажми «✅ Я поделился»"
    )
    
    keyboard = [
        [InlineKeyboardButton("📤 Поделиться ссылкой", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился", callback_data="confirm_share")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    return GIFT_SCREEN

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    await query.answer("✅ Спасибо за репост! Ваш подарок готов!")
    
    context.user_data["has_shared"] = True
    
    return await show_results_screen(update, context)

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран открытия подарка"""
    query = update.callback_query
    await query.answer()
    
    gift_text = (
        f"<b>🎁 ВАШ ПОДАРОК ГОТОВ!</b>\n\n"
        f"📚 Терапевтическая сказка для трансформации структуры восприятия\n\n"
        f"Эта сказка разрешает внутренние противоречия в конфигурации восприятия вашего профиля.\n\n"
        f"💡 <b>Как использовать:</b>\n"
        f"1. Нажми кнопку ниже, чтобы открыть PDF\n"
        f"2. Прочитай\n"
        f"3. Обращай внимание на символы и метафоры\n\n"
        f"Приятного чтения! 📖✨"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Открыть сказку", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(gift_text, reply_markup=reply_markup, parse_mode="HTML")
    return OPEN_GIFT_SCREEN

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран полного пакета"""
    query = update.callback_query
    await query.answer()
    
    package_text = (
        f"<b>💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
        f"<b>Что входит:</b>\n"
        f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
        f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
        f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
        f"• Персональные рекомендации по развитию\n"
        f"• Карта сильных и слабых сторон\n\n"
        f"<b>Цена:</b> 690 ₽\n\n"
        f"<b>🔒 БЕЗОПАСНАЯ ОПЛАТА ЧЕРЕЗ ЮKASSA</b>\n"
        f"• Официальный платежный агрегатор\n"
        f"• Поддержка карт, электронных кошельков\n"
        f"• Мгновенное получение материалов\n\n"
        f"<i>После оплаты файлы будут отправлены автоматически.</i>"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"💳 Купить за 690 ₽", callback_data="start_payment")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")],
        [InlineKeyboardButton("💬 Консультация", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

# ============================================
# ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ
# ============================================

async def payment_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по оплате"""
    help_text = (
        "💰 <b>ИНСТРУКЦИЯ ПО ОПЛАТЕ</b>\n\n"
        "<b>Как оплатить:</b>\n"
        "1. Выберите «Полный пакет рекомендаций»\n"
        "2. Нажмите «Купить за 690 ₽»\n"
        "3. Оплатите в открывшемся окне\n"
        "4. Вернитесь в бота и нажмите «Проверить оплату»\n\n"
        "<b>Поддерживаемые способы оплаты:</b>\n"
        "• Банковские карты (Visa, MasterCard, МИР)\n"
        "• Электронные кошельки (ЮMoney, QIWI)\n"
        "• Мобильные платежи\n"
        "• Интернет-банкинг\n\n"
        "<b>Безопасность:</b>\n"
        "• Все платежи защищены ЮKassa\n"
        "• Ваши данные не передаются третьим лицам\n"
        "• Мгновенная доставка файлов после оплаты\n\n"
        "<b>Если возникли проблемы:</b>\n"
        "• Напишите в поддержку: @meysternlp\n"
        "• Укажите ID заказа (первые 8 символов)\n"
        "• Опишите проблему\n\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Купить пакет", callback_data="show_package")],
        [InlineKeyboardButton("📞 Поддержка", url="https://t.me/meysternlp")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*50)
    print("🚀 ЗАПУСК БОТА ВАРИАТИКА ver 2.0")
    print("="*50)
    print("🔗 Flask API URL:", FLASK_API_URL)
    print("🤖 Bot token:", "Установлен" if TOKEN else "❌ Нет токена!")
    print("💰 Payment system: Flask API + ЮKassa")
    print("="*50 + "\n")
    
    # Проверка доступности Flask API
    async def test_flask_api():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{FLASK_API_URL}/") as response:
                    if response.status == 200:
                        print("✅ Flask API доступен")
                        return True
                    else:
                        print(f"⚠️ Flask API ответил с кодом: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Ошибка подключения к Flask API: {e}")
            return False
    
    # Тестируем подключение
    import asyncio as async_io
    try:
        loop = async_io.new_event_loop()
        async_io.set_event_loop(loop)
        api_available = loop.run_until_complete(test_flask_api())
        loop.close()
    except:
        api_available = False
    
    if not api_available:
        print("⚠️ Внимание: Flask API может быть недоступен!")
        print("Бот будет работать, но платежи могут не работать.")
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            STAGE_2: [
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4: [
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(handle_payment_start, pattern="^start_payment$")
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(check_payment_status, pattern="^check_payment_"),
                CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PAYMENT_SUCCESS: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$")
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    # Добавляем обработчики команд
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("payment_help", payment_help_command))
    
    logger.info("🚀 Bot started: ВАРИАТИКА ver 2.0 с интеграцией Flask API!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
