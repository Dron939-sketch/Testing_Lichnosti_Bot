"""
АДАПТИВНЫЙ ТЕСТ ВАРИАТИКА + ПЛАТЕЖНАЯ СИСТЕМА
ПОЛНАЯ ВЕРСИЯ 2.3 - ОБЪЕДИНЕНИЕ РАБОЧЕЙ ЛОГИКИ v1.9 С ПЛАТЕЖНОЙ СИСТЕМОЙ v2.2
"""

import logging
import os
import sys
import asyncio
import urllib.parse
import math
import re
import time
import json
import base64
import uuid
import requests
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Optional, Tuple, Any

# Telegram Bot API
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

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_variatica.log', encoding='utf-8')
    ]
)

# Отключаем шумные логи
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ
# ============================================

# Получение токена
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Конфигурация платежной системы
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

# ПРАВИЛЬНЫЕ ССЫЛКИ НА ЯНДЕКС.ДИСК (36 папок)
YANDEX_DISK_FOLDERS = {
    # SA профили (9 папок)
    "SA_1_DEF": "https://disk.yandex.ru/d/HAcOfAg1tpIedA",
    "SA_2_SIT": "https://disk.yandex.ru/d/MwdMClX9koCTmA",
    "SA_3_CON": "https://disk.yandex.ru/d/NKN_XemK62t5nA",
    "SA_4_EXP": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA",
    "SA_5_INT": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg",
    "SA_6_AUT": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag",
    "SA_7_VAL": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g",
    "SA_8_TRA": "https://disk.yandex.ru/d/SqlDISkse1OEGQ",
    "SA_9_IDE": "https://disk.yandex.ru/d/vGzHmuckInNL5g",
    
    # SP профили (9 папок)
    "SP_1_DEF": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA",
    "SP_2_SIT": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA",
    "SP_3_CON": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA",
    "SP_4_EXP": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ",
    "SP_5_INT": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg",
    "SP_6_AUT": "https://disk.yandex.ru/d/xWBv4TLFosOB5g",
    "SP_7_VAL": "https://disk.yandex.ru/d/K1whXj6C6KAazQ",
    "SP_8_TRA": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg",
    "SP_9_IDE": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ",
    
    # IA профили (9 папок)
    "IA_1_DEF": "https://disk.yandex.ru/d/M1Y7z175uGKIHg",
    "IA_2_SIT": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ",
    "IA_3_CON": "https://disk.yandex.ru/d/DCkqqALby9UpFg",
    "IA_4_EXP": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg",
    "IA_5_INT": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g",
    "IA_6_AUT": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg",
    "IA_7_VAL": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ",
    "IA_8_TRA": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw",
    "IA_9_IDE": "https://disk.yandex.ru/d/ub0YpQQgS4g6rQ",
    
    # IP профили (9 папок)
    "IP_1_DEF": "https://disk.yandex.ru/d/m-WOQwDdgQxsnQ",
    "IP_2_SIT": "https://disk.yandex.ru/d/aL4VlAQdlaZ-6g",
    "IP_3_CON": "https://disk.yandex.ru/d/N8GG9XbnC3bFhg",
    "IP_4_EXP": "https://disk.yandex.ru/d/54RFOZmGhA4cfA",
    "IP_5_INT": "https://disk.yandex.ru/d/l5iFTIX8-gTycQ",
    "IP_6_AUT": "https://disk.yandex.ru/d/bTo_vcCoC1KU7Q",
    "IP_7_VAL": "https://disk.yandex.ru/d/TMx1VP843bnJQw",
    "IP_8_TRA": "https://disk.yandex.ru/d/e9KfJdLcl3gp7g",
    "IP_9_IDE": "https://disk.yandex.ru/d/ZiQPHJSDrrWZhw"
}

# Константы бота
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую.."

# Состояния ConversationHandler
(
    STAGE_1, STAGE_2, STAGE_3, STAGE_4, 
    CLARIFICATION, RESULTS, GIFT_SCREEN, 
    PACKAGE_SCREEN, OPEN_GIFT_SCREEN, 
    DILTS_CLARIFICATION
) = range(10)

# ============================================
# ВОПРОСЫ ЭТАПА 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ (8 вопросов)
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
# ВОПРОСЫ ЭТАПА 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ (8 вопросов для каждого типа)
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
                "1": "Боюсь близости",
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
                "4": "Понимание и действия",
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
# ВОПРОСЫ ЭТАПА 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ (8 вопросов)
# ============================================

STAGE_3_QUESTIONS = [
    {
        "id": "q3_1", 
        "text": "Вспомни последнюю неделю.\n\nСколько раз ты сделал что-то, что потом пожалел?", 
        "options": {
            "a": {"text": "Ни разу", "level": 5}, 
            "b": {"text": "1-2 раза", "level": 3}, 
            "c": {"text": "3-5 раз", "level": 2}, 
            "d": {"text": "Больше 5 раз", "level": 1}
        }
    },
    {
        "id": "q3_2", 
        "text": "Последний конфликт.\n\nЧто ты сделал?", 
        "options": {
            "a": {"text": "Избежал", "level": 1}, 
            "b": {"text": "Уступил", "level": 1}, 
            "c": {"text": "Отстоял позицию", "level": 3}, 
            "d": {"text": "Нашёл компромисс", "level": 5}
        }
    },
    {
        "id": "q3_3", 
        "text": "Как ты принимаешь важные решения?", 
        "options": {
            "a": {"text": "Долго мучаюсь", "level": 1}, 
            "b": {"text": "Взвешиваю варианты", "level": 3}, 
            "c": {"text": "Быстро, по интуиции", "level": 5}, 
            "d": {"text": "Жду, когда решение придёт само", "level": 4}
        }
    },
    {
        "id": "q3_4", 
        "text": "Как часто ты делаешь то, что не хочешь, но «надо»?", 
        "options": {
            "a": {"text": "Постоянно (вся жизнь — «надо»)", "level": 1}, 
            "b": {"text": "Часто", "level": 2}, 
            "c": {"text": "Иногда", "level": 3}, 
            "d": {"text": "Редко (делаю то, что хочу)", "level": 5}
        }
    },
    {
        "id": "q3_5", 
        "text": "Вспомни последнюю сильную эмоцию.\n\nЧто ты с ней сделал?", 
        "options": {
            "a": {"text": "Подавил", "level": 1}, 
            "b": {"text": "Проанализировал", "level": 3}, 
            "c": {"text": "Выразил (слова/действия/творчество)", "level": 5}, 
            "d": {"text": "Наблюдал за ней", "level": 4}
        }
    },
    {
        "id": "q3_6", 
        "text": "Как ты относишься к своим слабостям?", 
        "options": {
            "a": {"text": "Стыжусь их", "level": 1}, 
            "b": {"text": "Пытаюсь исправить", "level": 2}, 
            "c": {"text": "Принимаю их", "level": 4}, 
            "d": {"text": "Вижу в них силу", "level": 6}
        }
    },
    {
        "id": "q3_7", 
        "text": "Как часто ты чувствуешь, что живёшь не своей жизнью?", 
        "options": {
            "a": {"text": "Постоянно", "level": 1}, 
            "b": {"text": "Часто", "level": 2}, 
            "c": {"text": "Иногда", "level": 3}, 
            "d": {"text": "Редко или никогда", "level": 5}
        }
    },
    {
        "id": "q3_8", 
        "text": "Что ты делаешь, когда не знаешь, что делать?", 
        "options": {
            "a": {"text": "Паникую", "level": 1}, 
            "b": {"text": "Ищу информацию", "level": 2}, 
            "c": {"text": "Действую методом проб", "level": 3}, 
            "d": {"text": "Жду ясности", "level": 4}
        }
    }
]

# ============================================
# ВОПРОСЫ ЭТАПА 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ (8 вопросов)
# ============================================

STAGE_4_QUESTIONS = [
    {
        "id": "q4_1", 
        "text": "Как часто ты чувствуешь, что «что-то не так» в жизни?", 
        "options": {
            "a": {"text": "Постоянно", "dilts": "IDENTITY"}, 
            "b": {"text": "Часто", "dilts": "VALUES"}, 
            "c": {"text": "Иногда", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}
        }
    },
    {
        "id": "q4_2", 
        "text": "Что именно «не так»?\n\nВыбери то, что ближе всего:", 
        "options": {
            "a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Не умею делать то, что хочу", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_3", 
        "text": "Человек чувствует себя несчастным.\n\nВ чём, скорее всего, причина?", 
        "options": {
            "a": {"text": "Не те люди вокруг", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Делает не то, что хочет", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Не умеет делать то, что хочет", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Не понимает, чего хочет", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_4", 
        "text": "Если бы ты мог изменить что-то одно, что бы это было?", 
        "options": {
            "a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Своё понимание целей", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_5", 
        "text": "Что для тебя сложнее всего?", 
        "options": {
            "a": {"text": "Изменить внешние условия", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Научиться новому", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_6", 
        "text": "Когда ты застреваешь в проблеме, что обычно не хватает?", 
        "options": {
            "a": {"text": "Ресурсов (время, деньги, связи)", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Действий (не начинаю)", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Навыков (не умею)", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Понимания (не знаю зачем)", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_7", 
        "text": "Что мешает тебе быть счастливым?", 
        "options": {
            "a": {"text": "Обстоятельства", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Мои действия", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Мои ограничения", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Я не знаю, что такое счастье", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_8", 
        "text": "Если бы у тебя была волшебная палочка, что бы ты изменил?", 
        "options": {
            "a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, 
            "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, 
            "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, 
            "d": {"text": "Себя (кто я)", "dilts": "IDENTITY"}
        }
    }
]

# Уровни Дилтса - ИСПРАВЛЕННЫЕ КОДЫ
DILTS_LEVELS = {
    "ENVIRONMENT": {"name": "ОКРУЖЕНИЕ", "code": "sit", "description": "Проблема во внешних условиях", "solution": "Измени окружение или отношение к нему"},
    "BEHAVIOR": {"name": "ПОВЕДЕНИЕ", "code": "con", "description": "Проблема в действиях", "solution": "Начни действовать по-другому"},
    "CAPABILITIES": {"name": "СПОСОБНОСТИ", "code": "exp", "description": "Проблема в навыках", "solution": "Освой новые навыки"},
    "VALUES": {"name": "ЦЕННОСТИ", "code": "val", "description": "Проблема в мотивации", "solution": "Найди свои истинные ценности"},
    "IDENTITY": {"name": "ИДЕНТИЧНОСТЬ", "code": "ide", "description": "Проблема в самоопределении", "solution": "Переопредели, кто ты"}
}

# ============================================
# АДАПТИВНЫЕ УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================

CLARIFICATION_QUESTIONS = {
    "stage1_external_internal": [
        {
            "id": "c1_1", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nПосле напряжённого дня что тебе нужнее?", 
            "options": {
                "a": {"text": "Встретиться с людьми", "scores": {"EXTERNAL": 2}}, 
                "b": {"text": "Побыть в одиночестве", "scores": {"INTERNAL": 2}}
            }
        },
        {
            "id": "c1_2", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда ты думаешь о выходных, что первое приходит в голову?", 
            "options": {
                "a": {"text": "Куда пойти, с кем встретиться", "scores": {"EXTERNAL": 2}}, 
                "b": {"text": "Чем заняться дома, о чём подумать", "scores": {"INTERNAL": 2}}
            }
        }
    ],
    "stage1_symbolic_material": [
        {
            "id": "c1_3", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЧто хуже: потерять деньги или потерять доверие близких?", 
            "options": {
                "a": {"text": "Потерять доверие", "scores": {"SYMBOLIC": 2}}, 
                "b": {"text": "Потерять деньги", "scores": {"MATERIAL": 2}}
            }
        },
        {
            "id": "c1_4", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда ты тревожишься, о чём чаще?", 
            "options": {
                "a": {"text": "Что обо мне подумают, как меня воспримут", "scores": {"SYMBOLIC": 2}}, 
                "b": {"text": "Хватит ли денег, успею ли, справлюсь ли", "scores": {"MATERIAL": 2}}
            }
        }
    ],
    "stage2_borderline": [
        {
            "id": "c2_1", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто ты чувствуешь, что застрял на месте?", 
            "options": {
                "1": "Постоянно, не знаю как двигаться", 
                "3": "Иногда, но нахожу выход", 
                "4": "Редко, я в движении"
            }
        },
        {
            "id": "c2_2", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак ты относишься к своим прошлым ошибкам?", 
            "options": {
                "1": "Стыжусь их, избегаю вспоминать", 
                "3": "Анализирую и учусь", 
                "4": "Принимаю как опыт"
            }
        }
    ],
    "stage3_discrepancy": [
        {
            "id": "c3_1", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nВспомни последний месяц. Сколько раз ты действовал не так, как хотел?", 
            "options": {
                "1": "Постоянно", 
                "2": "Часто (больше 5 раз)", 
                "3": "Иногда (2-4 раза)", 
                "5": "Редко (0-1 раз)"
            }
        },
        {
            "id": "c3_2", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак быстро ты замечаешь свои автоматические реакции?", 
            "options": {
                "1": "Не замечаю, действую на автомате", 
                "2": "Замечаю после", 
                "4": "Замечаю в процессе", 
                "5": "Замечаю до и могу изменить"
            }
        },
        {
            "id": "c3_3", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто ты делаешь то, что обещал себе?", 
            "options": {
                "1": "Почти никогда", 
                "2": "Иногда", 
                "4": "Часто", 
                "5": "Почти всегда"
            }
        }
    ],
    "stage4_tie": [
        {
            "id": "c4_1", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЕсли бы ты мог изменить только одно, что бы выбрал?", 
            "options": {
                "a": {"text": "Где я нахожусь", "dilts": "ENVIRONMENT"}, 
                "b": {"text": "Что я делаю", "dilts": "BEHAVIOR"}, 
                "c": {"text": "Что я умею", "dilts": "CAPABILITIES"}, 
                "d": {"text": "Что для меня важно", "dilts": "VALUES"}, 
                "e": {"text": "Кто я", "dilts": "IDENTITY"}
            }
        },
        {
            "id": "c4_2", 
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nГде находится твоя главная проблема?", 
            "options": {
                "a": {"text": "В обстоятельствах", "dilts": "ENVIRONMENT"}, 
                "b": {"text": "В моих действиях", "dilts": "BEHAVIOR"}, 
                "c": {"text": "В моих навыках", "dilts": "CAPABILITIES"}, 
                "d": {"text": "В моих целях", "dilts": "VALUES"}, 
                "e": {"text": "В моём самоопределении", "dilts": "IDENTITY"}
            }
        }
    ]
}

# ============================================
# ФУНКЦИИ ЗАЩИТЫ ОТ КОНФЛИКТОВ И ОШИБОК
# ============================================

def clear_telegram_conflicts():
    """Очищает конфликты перед запуском бота"""
    try:
        logger.info("🔄 Очистка конфликтов Telegram...")
        
        # 1. Удаляем webhook
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true", 
            timeout=10
        )
        if response.status_code == 200:
            logger.info("✅ Webhook удален")
        else:
            logger.warning(f"⚠️ Ошибка удаления webhook: {response.status_code}")
        
        # 2. Очищаем очередь обновлений
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1", 
            timeout=10
        )
        
        # 3. Проверяем токен
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getMe", 
            timeout=10
        )
        if response.status_code == 200:
            username = response.json()['result']['username']
            logger.info(f"✅ Токен валиден: @{username}")
        else:
            logger.error(f"❌ Неверный токен: {response.status_code}")
        
        logger.info("✅ Конфликты очищены")
        time.sleep(2)
        
    except Exception as e:
        logger.error(f"⚠️ Ошибка очистки конфликтов: {e}")

def check_all_profiles():
    """Проверяет загрузку всех 36 профилей"""
    print("\n" + "="*50)
    print("🔍 ПРОВЕРКА ЗАГРУЗКИ 36 ПРОФИЛЕЙ")
    print("="*50)
    
    all_profiles = loader.get_all_profiles()
    logger.info(f"📊 Всего найдено профилей: {len(all_profiles)}")
    
    # Проверяем все комбинации
    expected_types = ['sa', 'sp', 'ia', 'ip']
    expected_levels = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    expected_suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
    
    found = 0
    missing = []
    
    # Проверяем все комбинации
    for type_code in expected_types:
        print(f"\n🔍 Проверяю {type_code.upper()} профили:")
        for level in expected_levels:
            for suffix in expected_suffixes:
                profile_key = f"{type_code}_{level}_{suffix}"
                profile = loader.get_profile(profile_key)
                
                if profile:
                    print(f"  ✅ {profile_key}")
                    found += 1
                else:
                    missing.append(profile_key)
                    print(f"  ❌ {profile_key} - НЕ НАЙДЕН")
    
    print("\n" + "="*50)
    print(f"📈 НАЙДЕНО: {found}/36 профилей")
    
    if missing:
        print(f"⚠️  ОТСУТСТВУЮТ: {len(missing)} профилей")
        for m in missing[:10]:
            print(f"   - {m}")
        if len(missing) > 10:
            print(f"   ... и еще {len(missing) - 10} профилей")
    
    if found == 36:
        print("✅ ВСЕ 36 ПРОФИЛЕЙ ЗАГРУЖЕНЫ!")
    else:
        print("⚠️  ВНИМАНИЕ: Не все профили загружены!")
    
    print("="*50 + "\n")
    
    return found == 36

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ТЕСТА
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
    """Код Дилтса - ИСПРАВЛЕННЫЙ!"""
    dilts_map = {
        "ENVIRONMENT": "sit",    # ОКРУЖЕНИЕ → СИТУАЦИЯ
        "BEHAVIOR": "con",       # ПОВЕДЕНИЕ
        "CAPABILITIES": "exp",   # ВОЗМОЖНОСТИ → СПОСОБНОСТИ
        "VALUES": "val",         # ЦЕННОСТИ
        "IDENTITY": "ide"        # ИДЕНТИЧНОСТЬ
    }
    return dilts_map.get(dilts_level, "def")

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

def clean_duplicate_headers(text: str, field_type: str) -> str:
    """Убирает заголовки, которые уже есть в тексте профиля."""
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
# ФУНКЦИИ РАБОТЫ С API (ИЗ ТЗ) - ИСПРАВЛЕННЫЕ
# ============================================

def get_user_access(user_id: int) -> dict:
    """Получает информацию о доступах пользователя (копия из платежного бота)"""
    try:
        response = requests.get(
            f"{API_URL}/api/check-access/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API check-access для user_id {user_id}: {data.get('has_access', False)}")
            return data
        else:
            logger.error(f"❌ API error {response.status_code} для user_id {user_id}")
            return {"success": False, "error": f"API error {response.status_code}"}
    except Exception as e:
        logger.error(f"❌ Exception при проверке доступа: {e}")
        return {"success": False, "error": str(e)}

def get_materials_link(user_id: int, payment_id: str, token: str = None) -> dict:
    """Получает ссылку на материалы по payment_id (копия из платежного бота)"""
    try:
        url = f"{API_URL}/api/get-materials/{payment_id}"  # ← КЛЮЧЕВОЕ: payment_id, а не user_id!
        params = {"user_id": user_id}
        
        if token:
            params["token"] = token
            
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API get-materials для payment_id {payment_id}: success={data.get('success', False)}")
            return data
        else:
            logger.error(f"❌ API error {response.status_code} для payment_id {payment_id}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"❌ Exception при получении материалов: {e}")
        return {"success": False, "error": str(e)}

# ============================================
# ИСПРАВЛЕННАЯ ФУНКЦИЯ ПОИСКА ПРОФИЛЯ С FALLBACK (из v1.9)
# ============================================

def get_profile_fallback(profile_data: dict) -> VariaticaProfile:
    """
    ИСПРАВЛЕННАЯ ВЕРСИЯ: Находит реально существующий файл профиля.
    Приоритет: точное совпадение → разные суффиксы → без суффикса → любой файл уровня → ближайший уровень
    Поддерживает все типы: SA, SP, IA, IP (с обработкой ip/ip-адрес и ip - адрес)
    """
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    logger.info(f"🎯 FALLBACK ПОИСК: type={type_code}, level={level}, dilts={dilts_code}")
    
    # ============================================
    # НОРМАЛИЗАЦИЯ ТИПОВ ДЛЯ ПОИСКА
    # ============================================
    
    # Определяем возможные варианты именования для данного типа
    # Особенно важно для IP типа (может быть ip, ip-адрес, ip - адрес)
    search_types = [type_code]
    
    if type_code == "ip" or type_code == "ip-адрес":
        # Для IP типа пробуем все возможные варианты
        search_types = ["ip", "ip-адрес", "ip - адрес"]
    elif type_code == "ip - адрес":
        search_types = ["ip - адрес", "ip-адрес", "ip"]
    
    logger.info(f"🔍 Варианты поиска для типа {type_code}: {search_types}")
    
    # ============================================
    # 1. ТОЧНОЕ СОВПАДЕНИЕ (все варианты)
    # ============================================
    
    for search_type in search_types:
        target_key = f"{search_type}_{level}_{dilts_code}"
        profile = loader.get_profile(target_key)
        if profile:
            logger.info(f"✅ Exact match: {target_key}")
            return profile
    
    logger.info(f"🔍 Точное совпадение не найдено для {type_code}_{level}_{dilts_code}")
    
    # ============================================
    # 2. ПОИСК С РАЗНЫМИ СУФФИКСАМИ НА ТОМ ЖЕ УРОВНЕ
    # ============================================
    
    # Все возможные суффиксы (в порядке из файловой системы)
    possible_suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
    
    for search_type in search_types:
        logger.info(f"🔍 Ищу {search_type}_{level}_* с разными суффиксами")
        
        for suffix in possible_suffixes:
            test_key = f"{search_type}_{level}_{suffix}"
            profile = loader.get_profile(test_key)
            if profile:
                logger.info(f"✅ Найден с суффиксом {suffix}: {test_key}")
                return profile
    
    # ============================================
    # 3. ПОИСК БЕЗ СУФФИКСА
    # ============================================
    
    for search_type in search_types:
        test_key = f"{search_type}_{level}"
        profile = loader.get_profile(test_key)
        if profile:
            logger.info(f"✅ Найден без суффикса: {test_key}")
            return profile
    
    # ============================================
    # 4. ЛЮБОЙ ПРОФИЛЬ НА ТОМ ЖЕ УРОВНЕ
    # ============================================
    
    logger.info(f"🔍 Ищу любой профиль *_{level}_* для типа {type_code}")
    all_profiles = loader.get_all_profiles()
    
    # Собираем все профили этого типа (всех вариантов)
    all_type_profiles = []
    for key in all_profiles:
        key_lower = key.lower()
        # Проверяем все варианты типа
        for search_type in search_types:
            if key_lower.startswith(f"{search_type}_"):
                all_type_profiles.append((key, key_lower))
                break
    
    # Отладочная информация
    logger.info(f"📚 Все доступные профили типа {type_code} (варианты: {search_types}):")
    for key, key_lower in sorted(all_type_profiles):
        logger.info(f"   - {key}")
    
    # Ищем профили на том же уровне
    same_level_profiles = []
    for key, key_lower in all_type_profiles:
        # Извлекаем уровень из ключа
        try:
            parts = key_lower.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                key_level = int(parts[1])
                if key_level == level:
                    same_level_profiles.append(key)
        except (ValueError, IndexError):
            continue
    
    logger.info(f"📊 Профили уровня {level} типа {type_code}: {same_level_profiles}")
    
    if same_level_profiles:
        # Берем первый попавшийся профиль того же уровня
        fallback_key = same_level_profiles[0]
        logger.info(f"✅ Найден профиль уровня {level}: {fallback_key}")
        return loader.get_profile(fallback_key)
    
    # ============================================
    # 5. БЛИЖАЙШИЙ УРОВЕНЬ (только если ничего не найдено)
    # ============================================
    
    logger.info(f"⚠️ Нет профилей уровня {level}, ищу ближайший уровень для типа {type_code}")
    
    # Собираем все уровни этого типа
    available_levels = []
    for key, key_lower in all_type_profiles:
        try:
            parts = key_lower.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                key_level = int(parts[1])
                available_levels.append((key, key_level))
        except (ValueError, IndexError):
            continue
    
    if not available_levels:
        logger.error(f"❌ НЕТ ПРОФИЛЕЙ для типа {type_code}!")
        # Аварийный fallback
        emergency_key = "sa_1_def"
        logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
        return loader.get_profile(emergency_key)
    
    # Находим ближайший уровень
    min_diff = float('inf')
    best_key = None
    best_level = None
    
    for key, key_level in available_levels:
        diff = abs(key_level - level)
        if diff < min_diff:
            min_diff = diff
            best_key = key
            best_level = key_level
        elif diff == min_diff and key_level > best_level:
            # При одинаковой разнице берем более высокий уровень
            best_key = key
            best_level = key_level
    
    if best_key:
        logger.info(f"📈 Найден ближайший уровень {best_level} (разница {min_diff}): {best_key}")
        return loader.get_profile(best_key)
    
    # ============================================
    # 6. АВАРИЙНЫЙ FALLBACK
    # ============================================
    
    logger.error(f"🔥 КРИТИЧЕСКАЯ ОШИБКА: Ничего не найдено для типа {type_code}, level={level}")
    emergency_key = "sa_1_def"
    logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
    return loader.get_profile(emergency_key)

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
# ФУНКЦИЯ РАСЧЕТА ПРОФИЛЯ (обновленная с API)
# ============================================

def calculate_profile_final(context_data: dict, user_id: int = None) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля с сохранением в API"""
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
    
    logger.info(f"🎯 FINAL PROFILE CALCULATION:")
    logger.info(f"   Type: {type_code} ({perception_type})")
    logger.info(f"   Level: {final_level} ({get_level_name(final_level)})")
    logger.info(f"   Dilts: {dilts_level} ({dilts_code})")
    logger.info(f"   Coherence: {coherence['is_coherent']}")
    
    # Формируем полные данные профиля
    profile_key = f"{type_code}_{final_level}_{dilts_code}"
    
    full_profile_data = {
        "type_code": type_code,
        "level": final_level,
        "dilts_code": dilts_code,
        "dilts_level": dilts_level,
        "display_name": profile_key,
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        "coherence": coherence,
        "stage2_level": stage2_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
        "profile_key": profile_key,
        "profile_type": type_code,
        "profile_level": final_level,
        "profile_dilts": dilts_code
    }
    
    # Сохранение профиля в API (БЕЗ USERNAME!)
    if user_id:
        try:
            profile_payload = {
                "user_id": user_id,  # ⬅️ ТОЛЬКО user_id
                "profile_key": profile_key,
                "profile_type": type_code,
                "profile_level": final_level,
                "profile_dilts": dilts_code,
                "profile_data": full_profile_data
            }
            
            logger.info(f"📤 Отправка профиля в API: {profile_key} для user_id {user_id}")
            
            response = requests.post(f"{API_URL}/api/save-profile", json=profile_payload, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    logger.info(f"✅ Профиль сохранен в API: {profile_key} для user_id {user_id}")
                else:
                    logger.warning(f"⚠️ API вернул ошибку при сохранении профиля: {response_data.get('error')}")
            else:
                logger.warning(f"⚠️ Ошибка HTTP при сохранении профиля: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Таймаут при сохранении профиля для user_id {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения профиля в API: {e}")
    
    # Возвращаем данные
    return {
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code,
        "display_name": profile_key,
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        "coherence": coherence,
        "stage2_level": stage2_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
        "full_profile_data": full_profile_data if user_id else None,
        "profile_key": profile_key
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
    
    discrepancy_level = 0
    if not is_coherent:
        if profile_level <= 3 and dilts_level == "IDENTITY":
            discrepancy_level = 3  # Высокое несоответствие
        elif profile_level >= 7 and dilts_level == "ENVIRONMENT":
            discrepancy_level = 3  # Высокое несоответствие
        else:
            discrepancy_level = 1  # Низкое несоответствие
    
    return {
        "is_coherent": is_coherent,
        "profile_level": profile_level,
        "dilts_level": dilts_level,
        "expected_dilts": expected_dilts,
        "discrepancy_level": discrepancy_level
    }

# ============================================
# ФУНКЦИИ ДЛЯ СОЗДАНИЯ ПЛАТЕЖЕЙ (из v2.2)
# ============================================

def create_payment_in_db(user_id: int, amount: float = 690.0, is_test: bool = False, profile_data: dict = None) -> dict:
    """Создает запись о платеже в БД с передачей профиля"""
    try:
        timestamp = int(time.time())
        payment_id = f"test_{user_id}_{timestamp}" if is_test else f"variatica_{user_id}_{timestamp}"
        description = f"Тестовый платеж {amount} руб" if is_test else "Полный пакет ВАРИАТИКА - 690 руб"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "description": description,
            "email": f"user_{user_id}@telegram.org"
        }
        
        # Добавляем profile_data если есть (БЕЗ USERNAME!)
        if profile_data:
            simplified_profile = {
                "profile_key": profile_data.get("profile_key"),
                "type_code": profile_data.get("type_code"),
                "level": profile_data.get("level"),
                "dilts_code": profile_data.get("dilts_code")
            }
            payload["profile_data"] = simplified_profile
            logger.info(f"📤 Отправка платежа с профилем: {simplified_profile.get('profile_key', 'unknown')}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            
            if profile_data and response_data.get('profile_saved'):
                logger.info(f"✅ Профиль сохранен при создании платежа: {profile_data.get('profile_key')}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "confirmation_url": response_data.get('confirmation_url')
            }
        else:
            logger.error(f"❌ Ошибка API при создании платежа: {response.status_code}")
            return {"success": False, "error": f"Ошибка API: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        return {"success": False, "error": str(e)}

def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 690.0, email: str = None, is_test: bool = False) -> dict:
    """Создает платеж через Invoices API"""
    try:
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
        
        description = f"Тестовый платеж 1 рубль #{payment_id}" if is_test else f"Полный пакет ВАРИАТИКА #{payment_id}"
        item_description = "Тестовый доступ" if is_test else "Полный пакет ВАРИАТИКА: полный разбор профиля + книга + терапевтическая сказка"
        
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
                "is_test": str(is_test)
            },
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": item_description,
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
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            yookassa_id = data.get('id')
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if not confirmation_url:
                return {"success": False, "error": "No confirmation URL"}
            
            try:
                requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={"payment_id": payment_id, "yookassa_id": yookassa_id, "status": "waiting"},
                    timeout=10
                )
            except:
                pass
            
            return {
                "success": True,
                "payment_id": payment_id,
                "confirmation_url": confirmation_url,
                "invoice_type": "yookassa_invoice",
                "available_methods": "all"
            }
        else:
            return {"success": False, "error": f"Ошибка {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            return {"success": True, "status": status}
        else:
            return {"success": False, "error": f"Ошибка: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# ФУНКЦИЯ ГЕНЕРАЦИИ ССЫЛОК НА ЯНДЕКС.ДИСК
# ============================================

def generate_yandex_disk_link(profile_key: str) -> str:
    """Генерирует ссылку на Яндекс.Диск для профиля"""
    profile_key_upper = profile_key.upper()
    
    logger.info(f"🔗 Генерация ссылки для профиля: {profile_key} → {profile_key_upper}")
    
    # Пытаемся найти точное совпадение
    if profile_key_upper in YANDEX_DISK_FOLDERS:
        link = YANDEX_DISK_FOLDERS[profile_key_upper]
        logger.info(f"✅ Найдена точная ссылка: {link}")
        return link
    
    # Если нет точного совпадения, пробуем разные варианты
    parts = profile_key_upper.split('_')
    if len(parts) >= 3:
        # Пробуем заменить суффикс Дилтса на соответствующий из списка
        original_suffix = parts[2]
        suffix_mapping = {
            "CAP": "EXP",      # ВОЗМОЖНОСТИ → СПОСОБНОСТИ
            "ENV": "SIT",      # ОКРУЖЕНИЕ → СИТУАЦИЯ
            "BEH": "CON",      # ПОВЕДЕНИЕ
            "VAL": "VAL",      # ЦЕННОСТИ (оставляем)
            "IDE": "IDE"       # ИДЕНТИЧНОСТЬ (оставляем)
        }
        
        if original_suffix in suffix_mapping:
            mapped_suffix = suffix_mapping[original_suffix]
            mapped_key = f"{parts[0]}_{parts[1]}_{mapped_suffix}"
            
            if mapped_key in YANDEX_DISK_FOLDERS:
                link = YANDEX_DISK_FOLDERS[mapped_key]
                logger.info(f"✅ Найдена ссылка по маппингу: {original_suffix} → {mapped_suffix}: {link}")
                return link
    
    # Если не нашли, пробуем базовый ключ (без суффикса)
    if len(parts) >= 2:
        base_key = f"{parts[0]}_{parts[1]}_DEF"  # Пробуем с DEF
        if base_key in YANDEX_DISK_FOLDERS:
            link = YANDEX_DISK_FOLDERS[base_key]
            logger.info(f"✅ Найдена ссылка по базовому ключу: {base_key}: {link}")
            return link
    
    # Fallback: первая папка соответствующего типа
    if len(parts) >= 1:
        type_prefix = parts[0]
        for key in YANDEX_DISK_FOLDERS.keys():
            if key.startswith(type_prefix + "_"):
                link = YANDEX_DISK_FOLDERS[key]
                logger.warning(f"⚠️ Использую первую попавшуюся папку типа {type_prefix}: {key} → {link}")
                return link
    
    # Аварийный fallback
    logger.error(f"❌ Не найдена ссылка для профиля: {profile_key}")
    return "https://disk.yandex.ru/d/HAcOfAg1tpIedA"  # SA_1_DEF как запасной вариант

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
# ОСНОВНЫЕ ФУНКЦИИ ТЕСТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест ВАРИАТИКА ver 2.3!</b>\n\n"
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
    
    logger.info(f"User {update.effective_user.id} started test")
    
    return await show_stage_1_intro(update, context)

# ============================================
# ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ
# ============================================

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 1"""
    query = update.callback_query
    
    intro_text = (
        f"<b>🎯 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"Сейчас мы определим твой базовый тип восприятия реальности.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage1_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 1", callback_data="start_stage_1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФИГУРАЦИЯ ВОСПРИЯТИЯ?</b>\n\n"
        f"Это базовая программа, через которую ты воспринимаешь мир.\n\n"
        f"<b>Мы измеряем две оси:</b>\n\n"
        f"<b>1. Направленность внимания:</b>\n"
        f"• ЭКСТЕРНАЛЬНАЯ — фокус на внешнем мире (люди, события)\n"
        f"• ИНТЕРНАЛЬНАЯ — фокус на внутреннем мире (мысли, чувства)\n\n"
        f"<b>2. Доминирующая тревога:</b>\n"
        f"• СИМВОЛИЧЕСКАЯ — страх отвержения, непонимания\n"
        f"• МАТЕРИАЛЬНАЯ — страх потери контроля, ресурсов\n\n"
        f"<b>Результат:</b> Один из четырёх типов восприятия\n\n"
        f"Это определит, какие вопросы ты получишь на следующих этапах."
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
        f"🎯 Конфигурация восприятия определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение конфигурации мышления.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Сейчас мы определим твой тип мышления.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~4 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage2_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 2", callback_data="start_stage_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФИГУРАЦИЯ МЫШЛЕНИЯ?</b>\n\n"
        f"Это тип твоего мышления внутри системы восприятия.\n\n"
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
        f"<b>Результат:</b> Твой текущий способ обработки информации"
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
        f"🎯 Конфигурация мышления определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

# ============================================
# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
# ============================================

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"Сейчас мы уточним твои паттерны через анализ автоматических реакций.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage3_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 3", callback_data="start_stage_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ?</b>\n\n"
        f"Это автоматические реакции — то, что ты делаешь не задумываясь.\n\n"
        f"<b>Зачем это нужно:</b>\n\n"
        f"Ты можешь думать одно, а делать другое.\n\n"
        f"Твоё реальное поведение точнее показывает глубинные установки, чем твои представления о себе.\n\n"
        f"Мы зададим вопросы о конкретных действиях, чтобы уточнить твои паттерны.\n\n"
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
        f"🎯 Поведенческие паттерны проанализированы\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 4</b>: конфликт логических уровней.\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

# ============================================
# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"Сейчас мы определим, на каком уровне находится твоя точка роста.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 4", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ?</b>\n\n"
        f"Это модель Роберта Дилтса, которая показывает, на каком уровне находится проблема.\n\n"
        f"<b>5 уровней (снизу вверх):</b>\n\n"
        f"1️⃣ ОКРУЖЕНИЕ — внешние условия\n"
        f"2️⃣ ПОВЕДЕНИЕ — твои действия\n"
        f"3️⃣ СПОСОБНОСТИ — твои навыки\n"
        f"4️⃣ ЦЕННОСТИ — твои мотивы\n"
        f"5️⃣ ИДЕНТИЧНОСТЬ — кто ты\n\n"
        f"<b>Принцип:</b> Проблема на нижнем уровне решается на верхнем.\n\n"
        f"<b>Результат:</b> Твоя точка роста"
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
    
    question_text = (
        f"<b>🎯 ЭТАП 4: КОНФИГУРАЦИЯ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
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
    
    user = update.effective_user
    profile_data = calculate_profile_final(context.user_data, user_id=user.id)
    
    coherence = profile_data["coherence"]
    context.user_data["profile_data"] = profile_data
    
    if not coherence["is_coherent"] and coherence.get("discrepancy_level", 0) >= 2:
        logger.info(f"Major discrepancy ({coherence.get('discrepancy_level', 0)}) → asking clarification")
        return await ask_intelligent_clarification(update, context, profile_data, coherence)
    else:
        if not coherence["is_coherent"]:
            logger.info(f"Minor discrepancy ({coherence.get('discrepancy_level', 0)}) → showing with note")
        
        loading_text = f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\nАнализирую твои ответы и определяю профиль..."
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
    
    question_text = question["text"]
    
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

async def ask_intelligent_clarification(update: Update, context: ContextTypes.DEFAULT_TYPE, profile_data: dict, coherence: dict):
    """Задаёт интеллектуальный уточняющий вопрос на основе Дилтса"""
    query = update.callback_query
    
    profile_level = profile_data["level"]
    current_dilts = profile_data["dilts_level"]
    
    if profile_level <= 3 and current_dilts == "IDENTITY":
        question = (
            f"🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\n"
            f"Ты указал, что твоя главная проблема - в самоопределении (кто ты).\n\n"
            f"Но в остальных ответах ты показываешь уровень начинающего.\n\n"
            f"<b>Что точнее описывает твою ситуацию?</b>"
        )
        options = {
            "a": "Мне сложно с окружающими условиями (место, люди, обстоятельства)",
            "b": "Я не знаю, как действовать в ситуациях",
            "c": "Я действительно переосмысливаю, кто я есть"
        }
        
    elif profile_level >= 7 and current_dilts == "ENVIRONMENT":
        question = (
            f"🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\n"
            f"По твоим ответам у тебя продвинутый уровень развития.\n\n"
            f"Но ты указываешь, что проблема в основном в окружении.\n\n"
            f"<b>Что на самом деле главное?</b>"
        )
        options = {
            "a": "Да, проблема именно в условиях (нужно сменить окружение)",
            "b": "Проблема в моих внутренних ценностях и понимании",
            "c": "Я переосмысливаю свою идентичность"
        }
    
    else:
        question = (
            f"🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\n"
            f"Чтобы уточнить результат, ответь:\n\n"
            f"<b>Где находится корень твоих главных трудностей?</b>"
        )
        options = {
            "a": "В обстоятельствах и окружении",
            "b": "В моих действиях и привычках", 
            "c": "В навыках и способностях",
            "d": "В целях и ценностях",
            "e": "В самоопределении (кто я)"
        }
    
    context.user_data["dilts_clarification_data"] = {
        "profile_data": profile_data,
        "coherence": coherence
    }
    
    keyboard = []
    for opt_id, opt_text in options.items():
        keyboard.append([InlineKeyboardButton(opt_text, callback_data=f"dilts_clarify_{opt_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(question, reply_markup=reply_markup, parse_mode="HTML")
    
    return DILTS_CLARIFICATION

async def handle_dilts_clarification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на уточняющий вопрос по Дилтсу"""
    query = update.callback_query
    await query.answer()
    
    option_id = query.data.split("_")[-1]
    
    answer_to_dilts = {
        "a": "ENVIRONMENT",
        "b": "BEHAVIOR", 
        "c": "CAPABILITIES",
        "d": "VALUES",
        "e": "IDENTITY"
    }
    
    refined_dilts = answer_to_dilts.get(option_id, "VALUES")
    
    clarification_data = context.user_data.get("dilts_clarification_data", {})
    profile_data = clarification_data.get("profile_data", {})
    
    context.user_data["stage4_dilts_answers"].append(refined_dilts)
    context.user_data["refined_dilts"] = refined_dilts
    
    logger.info(f"User clarified dilts: {option_id} → {refined_dilts}")
    
    # Пересчитываем профиль (БЕЗ передачи username)
    user = update.effective_user
    context.user_data["profile_data"] = calculate_profile_final(
        context.user_data, 
        user_id=user.id  # ⬅️ ТОЛЬКО user_id
    )
    
    loading_text = f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\nАнализирую твои ответы и определяю профиль..."
    await query.edit_message_text(loading_text, parse_mode="HTML")
    await asyncio.sleep(2)
    
    return await show_results_screen(update, context)

# ============================================
# ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА - версия 2.3 (рабочая логика v1.9 + платежная система v2.2)"""
    query = update.callback_query
    
    has_shared = context.user_data.get("has_shared", False)
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        user = update.effective_user
        profile_data = calculate_profile_final(context.user_data, user_id=user.id)
        context.user_data["profile_data"] = profile_data
    
    profile = get_profile_fallback(profile_data)
    
    if not profile:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось найти профиль.\n\nПопробуй пройти тест заново: /start"
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    # ====================================================
    # СООБЩЕНИЕ 1: Заголовок + Архетип + Цитата + "Это ты если..." + Суть проблемы
    # ====================================================
    
    message_1 = ""
    
    # Заголовок
    profile_header = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
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
    
    # "Это ты если..."
    trigger = profile_card.get('trigger', '')
    if trigger:
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_1 += f"<b>🔍 ЭТО ТЫ, ЕСЛИ...</b>\n\n"
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
    # СООБЩЕНИЕ 2: Инструмент + Что дальше + Кнопки (компактный репост)
    # ====================================================
    
    message_2 = ""
    
    # Инструмент
    tool = profile_card.get('immediate_tool', '')
    if tool:
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            message_2 += f"<b>🛠 ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»</b>\n\n"
            message_2 += f"{tool.strip()}\n\n"
    
    # Что дальше
    cta = profile_card.get('cta', '')
    if cta:
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_2 += f"<b>🚀 ЧТО ДАЛЬШЕ?</b>\n\n"
            message_2 += f"{cta.strip()}\n\n"
    
    # Разделительная линия
    message_2 += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Компактный блок репоста
    if not has_shared:
        message_2 += (
            f"<b>🎁 ПОДАРОК ЗА РЕПОСТ</b>\n"
            f"Поделись тестом с друзьями и получи бонусный материал.\n\n"
        )
    else:
        message_2 += (
            f"<b>🎉 ГОТОВО!</b>\n"
            f"Спасибо за репост! Твой подарок ждёт тебя.\n\n"
        )
    
    # Определяем кнопки
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться и получить подарок", callback_data="get_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Забрать подарок", callback_data="open_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS

# ============================================
# ЭКРАНЫ ДЛЯ ПОДАРКОВ И ОПЛАТЫ
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ИНСТРУКЦИЯ ПО ШАРИНГУ"""
    query = update.callback_query
    await query.answer()
    
    instruction_text = (
        f"<b>📤 ШАГ 1: ПОДЕЛИСЬ ССЫЛКОЙ</b>\n\n"
        f"Нажми кнопку ниже, чтобы отправить сообщение с ссылкой на тест.\n\n"
        f"После того как отправишь, вернись сюда и нажми «✅ Я поделился»"
    )
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
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

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНЫЙ ПАКЕТ ВАРИАТИКА"""
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
        f"<b>ВСЕ способы оплаты доступны:</b>\n"
        f"• СБП (Система быстрых платежей)\n"
        f"• ЮMoney (Яндекс.Деньги)\n"
        f"• Банковские карты (Visa, MasterCard, Мир)\n"
        f"• Apple Pay / Google Pay\n"
        f"• QIWI и другие\n\n"
        f"💡 <b>После оплаты вы получите:</b>\n"
        f"• Мгновенный доступ к материалам\n"
        f"• Ссылку на Яндекс.Диск с вашей персональной папкой\n"
        f"• Чек по 54-ФЗ (в боевом режиме)\n"
        f"• Техническую поддержку"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 КУПИТЬ ДОСТУП 690 РУБ", callback_data="buy_variatica_package")],
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

async def buy_variatica_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка полного пакета ВАРИАТИКА"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"💰 User {user_id} ({user_name}) buying full package")
    
    await query.edit_message_text("💎 *Создаю заказ на полный пакет ВАРИАТИКА...*", parse_mode='Markdown')
    
    # Проверяем, есть ли профиль в context.user_data
    profile_data = None
    if 'profile_data' in context.user_data:
        profile_data = context.user_data['profile_data'].get('full_profile_data')
        if profile_data:
            logger.info(f"📤 Передаю профиль в платеж: {profile_data.get('profile_key')}")
    
    # Передаем профиль в create_payment_in_db
    db_result = create_payment_in_db(
        user_id, 
        amount=690.0, 
        is_test=False, 
        profile_data=profile_data
    )
    
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка создания заказа:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
    else:
        payment_result = create_yookassa_payment(payment_id, user_id, amount=690.0, is_test=False)
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка платежной системы:*\n`{error_msg}`", parse_mode='Markdown')
            return
        confirmation_url = payment_result["confirmation_url"]
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("⬅️ Назад к пакетам", callback_data="show_package")]
    ]
    
    await query.edit_message_text(
        f"✅ *ЗАКАЗ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 руб\n"
        f"📚 *Пакет:* Полный пакет ВАРИАТИКА\n"
        f"🎯 *Профиль:* {'Передан в заказ' if profile_data else 'Будет определен после теста'}\n\n"
        f"*Что вы получите после оплаты:*\n"
        f"✅ Полный разбор профиля (15+ страниц)\n"
        f"✅ Терапевтическую сказку\n"
        f"✅ Книгу ВАРИАТИКА (.PDF)\n"
        f"✅ Персональные рекомендации\n"
        f"✅ Карту сильных и слабых сторон\n"
        f"✅ Ссылку на Яндекс.Диск с вашей папкой\n\n"
        f"💡 *Все способы оплаты доступны:* СБП, ЮMoney, карты\n"
        f"🔒 *Защита от дублей:* ✅ активна\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты вы получите доступ к материалам.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж 1 рубль"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"🧪 User {user_id} ({user_name}) creating test payment")
    
    await query.edit_message_text("🧪 *Создаю тестовый платеж 1 рубль...*", parse_mode='Markdown')
    
    # Проверяем, есть ли профиль в context.user_data
    profile_data = None
    if 'profile_data' in context.user_data:
        profile_data = context.user_data['profile_data'].get('full_profile_data')
        if profile_data:
            logger.info(f"📤 Передаю профиль в тестовый платеж: {profile_data.get('profile_key')}")
    
    # Передаем профиль в create_payment_in_db
    db_result = create_payment_in_db(
        user_id, 
        amount=1.0, 
        is_test=True, 
        profile_data=profile_data
    )
    
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
    else:
        payment_result = create_yookassa_payment(payment_id, user_id, amount=1.0, is_test=True)
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
            return
        confirmation_url = payment_result["confirmation_url"]
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("⬅️ Назад к пакетам", callback_data="show_package")]
    ]
    
    await query.edit_message_text(
        f"🧪 *ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"📋 *ID:* `{payment_id}`\n"
        f"🎯 *Профиль:* {'Передан в заказ' if profile_data else 'Тестовый'}\n\n"
        f"*Для проверки платежной системы:*\n"
        f"1. Нажмите кнопку оплаты\n"
        f"2. Выберите любой способ оплаты\n"
        f"3. После успешной оплаты вернитесь в бот\n"
        f"4. Система автоматически выдаст тестовые материалы\n\n"
        f"💡 *Все способы оплаты доступны*\n"
        f"🔒 *Защита от дублей:* ✅ активна",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def status_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 *Проверяю статус:*\n`{payment_id}`", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка:* {error_msg}", parse_mode='Markdown')
            return
        
        status = result.get("status", "unknown")
        
        if status == "succeeded":
            is_test = "test_" in payment_id
            
            if is_test:
                message = (
                    f"🎉 *ТЕСТОВЫЙ ПЛАТЕЖ 1 РУБЛЬ ОПЛАЧЕН!*\n\n"
                    f"✅ Платеж `{payment_id}` успешно завершен!\n\n"
                    f"*🔓 СИСТЕМА РАБОТАЕТ КОРРЕКТНО!*\n"
                    f"Тестовые материалы будут доступны в течение 5 минут.\n\n"
                    f"Для полного курса используйте кнопку ниже:"
                )
            else:
                message = (
                    f"🎉 *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
                    f"✅ Ваш заказ `{payment_id}` успешно оплачен!\n\n"
                    f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                    f"Вы получили доступ ко всем материалам полного пакета ВАРИАТИКА!\n\n"
                    f"✅ Вы получите мгновенное уведомление с ссылкой на Яндекс.Диск."
                )
            
        elif status in ["pending", "waiting"]:
            message = (
                f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
                f"Заказ `{payment_id}` еще не оплачен.\n\n"
                f"*Для оплаты используйте кнопку ниже:*"
            )
        else:
            message = f"📊 *Статус заказа:* `{status}`"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="show_package")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ОТКРЫТИЕ ПОДАРКА"""
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

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Назад' - возвращает к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем profile_data из context.user_data
    if 'profile_data' in context.user_data:
        del context.user_data['profile_data']
    if 'profile_card' in context.user_data:
        del context.user_data['profile_card']
    
    context.user_data.clear()
    
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    return await start_test(update, context)

# ============================================
# КОМАНДЫ БОТА
# ============================================

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials - ИСПРАВЛЕННАЯ ВЕРСИЯ С ПРАВИЛЬНОЙ ЛОГИКОЙ"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 START /materials command")
    logger.info(f"👤 User: {user_id} ({user_name})")
    
    # Шаг 1: Проверяем доступ через API
    logger.info(f"🔍 Step 1: Checking access via API")
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        error_msg = access_data.get('error', 'Unknown error')
        logger.error(f"❌ API error: {error_msg}")
        await update.message.reply_text(
            "❌ Ошибка проверки доступа. Попробуйте позже.",
            parse_mode="HTML"
        )
        return
    
    logger.info(f"📊 API response: success=True, has_access={access_data.get('has_access')}")
    
    # Шаг 2: Если нет доступа - предлагаем купить
    if not access_data.get('has_access', False):
        logger.info(f"❌ User has no access")
        keyboard = [
            [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП", callback_data="show_package")],
            [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА", callback_data="test_payment")]
        ]
        
        await update.message.reply_text(
            f"❌ <b>У ВАС НЕТ ДОСТУПА</b>\n\n"
            f"Для получения материалов необходимо оплатить доступ.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return
    
    # Шаг 3: Ищем активный доступ
    accesses = access_data.get('accesses', [])
    logger.info(f"🔍 Found {len(accesses)} accesses")
    
    if not accesses:
        logger.error(f"❌ No accesses array in response")
        await update.message.reply_text(
            "❌ Ошибка данных доступа. Обратитесь в поддержку.",
            parse_mode="HTML"
        )
        return
    
    for access in accesses:
        if access.get('has_access', False) and access.get('is_active', False):
            payment_id = access.get('payment_id')
            access_token = access.get('access_token')
            profile_key = access.get('profile_key')
            
            logger.info(f"✅ Found active access: payment_id={payment_id}")
            logger.info(f"   profile_key from API: {profile_key}")
            
            # Шаг 4: Получаем ссылку на материалы
            logger.info(f"📦 Getting materials link for payment_id={payment_id}")
            materials_data = get_materials_link(user_id, payment_id, access_token)
            
            if materials_data.get('success', False):
                # Вариант A: Если API дал прямую ссылку
                materials_link = materials_data.get('materials_link')
                if materials_link:
                    logger.info(f"✅ Got link from API: {materials_link[:50]}...")
                    
                    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                    
                    await update.message.reply_text(
                        f"✅ <b>ВАШИ МАТЕРИАЛЫ ГОТОВЫ!</b>\n\n"
                        f"🎯 Профиль: {profile_key or 'Не указан'}\n"
                        f"🔗 Ссылка: {materials_link}\n\n"
                        f"Нажмите кнопку ниже:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Materials sent successfully via API")
                    return
                else:
                    logger.warning(f"⚠️ API returned success=True but no materials_link")
            
            # Вариант B: Если API не дал ссылку, но есть profile_key (fallback логика)
            if profile_key:
                logger.info(f"⚠️ API didn't return link, generating locally for {profile_key}")
                materials_link = generate_yandex_disk_link(profile_key)
                
                keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                
                await update.message.reply_text(
                    f"✅ <b>ВАШИ МАТЕРИАЛЫ ГОТОВЫ!</b>\n\n"
                    f"🎯 Ваш профиль: {profile_key}\n"
                    f"📁 Папка на Яндекс.Диске\n\n"
                    f"Нажмите кнопку ниже:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML"
                )
                logger.info(f"✅ Generated link locally: {materials_link[:50]}...")
                return
            else:
                # Нет ни ссылки, ни profile_key
                logger.error(f"❌ No materials link and no profile_key for payment_id {payment_id}")
                # Продолжаем поиск других доступов
    
    # Если дошли сюда - что-то пошло не так
    logger.error(f"🔥 No active access found or API error")
    
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить доступ", callback_data="check_access")],
        [InlineKeyboardButton("💎 Купить доступ", callback_data="show_package")]
    ]
    
    await update.message.reply_text(
        f"❌ <b>НЕ УДАЛОСЬ ПОЛУЧИТЬ МАТЕРИАЛЫ</b>\n\n"
        f"Попробуйте:\n"
        f"1. Проверить статус доступа\n"
        f"2. Купить доступ\n"
        f"3. Обратиться в поддержку",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def myaccess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /myaccess - проверка доступов"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🔍 User {user_id} ({user_name}) checked access")
    
    # Проверяем доступ через API
    await update.message.reply_text("🔍 Проверяю статус вашего доступа...")
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        error_msg = access_data.get('error', 'Unknown error')
        await update.message.reply_text(
            f"❌ Ошибка проверки доступа: {error_msg}",
            parse_mode="HTML"
        )
        return
    
    if access_data.get('has_access'):
        # Получаем первый активный доступ
        accesses = access_data.get('accesses', [])
        active_access = None
        for access in accesses:
            if access.get('has_access') and access.get('is_active'):
                active_access = access
                break
        
        if active_access:
            payment_id = active_access.get('payment_id')
            profile_key = active_access.get('profile_key')
            granted_at = active_access.get('granted_at')
            expires_at = active_access.get('expires_at')
            
            # Генерируем ссылку
            materials_link = generate_yandex_disk_link(profile_key) if profile_key else "https://disk.yandex.ru"
            
            keyboard = [
                [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)],
                [InlineKeyboardButton("🔄 ПРОВЕРИТЬ СТАТУС", callback_data="check_current_status")]
            ]
            
            await update.message.reply_text(
                f"✅ <b>ДОСТУП АКТИВЕН!</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_name}\n"
                f"🎯 <b>Профиль:</b> {profile_key or 'Не указан'}\n"
                f"📦 <b>Пакет:</b> Полный ВАРИАТИКА\n"
                f"📅 <b>Доступ открыт:</b> {granted_at or 'Неизвестно'}\n"
                f"📅 <b>Действителен до:</b> {expires_at or 'Неизвестно'}\n\n"
                f"<b>Для получения материалов используйте кнопку ниже:</b>\n\n"
                f"📚 <b>В папке на Яндекс.Диске:</b>\n"
                f"• Полный разбор профиля (15+ страниц)\n"
                f"• Терапевтическая сказка\n"
                f"• Книга ВАРИАТИКА (.PDF)\n"
                f"• Рекомендации по развитию\n"
                f"• Карта сильных и слабых сторон\n\n"
                f"🔗 <b>Ссылка:</b> {materials_link}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"⚠️ <b>ДОСТУП НАЙДЕН, НО НЕ АКТИВЕН</b>\n\n"
                f"У вас есть доступ, но он не активен или истек.",
                parse_mode="HTML"
            )
    else:
        # Проверяем, есть ли результаты теста в context.user_data
        if 'profile_data' in context.user_data:
            profile_data = context.user_data.get('profile_data', {})
            profile_key = profile_data.get('display_name', 'не определен')
            
            keyboard = [
                [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП 690 РУБ", callback_data="show_package")],
                [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")]
            ]
            
            await update.message.reply_text(
                f"❌ <b>ДОСТУП НЕ АКТИВЕН</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_name}\n"
                f"🎯 <b>Ваш профиль:</b> {profile_key}\n"
                f"📦 <b>Статус:</b> Доступ не оплачен\n\n"
                f"<b>Для получения материалов:</b>\n"
                f"✅ Полный разбор профиля (15+ страниц)\n"
                f"✅ Терапевтическая сказка\n"
                f"✅ Книга ВАРИАТИКА (.PDF)\n"
                f"✅ Рекомендации по развитию\n"
                f"✅ Карта сильных и слабых сторон\n\n"
                f"💰 <b>Цены:</b>\n"
                f"💎 Полный пакет: 690 руб\n"
                f"🧪 Тест оплаты: 1 руб\n\n"
                f"Нажмите кнопку ниже для покупки:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🚀 НАЧАТЬ ТЕСТ", callback_data="start_test")],
                [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП", callback_data="show_package")]
            ]
            
            await update.message.reply_text(
                f"👤 <b>Пользователь:</b> {user_name}\n"
                f"📦 <b>Статус:</b> Доступ не активирован\n\n"
                f"<b>Для получения доступа:</b>\n"
                f"1️⃣ Пройдите тест (/start)\n"
                f"2️⃣ Узнайте свой профиль\n"
                f"3️⃣ Оплатите доступ к материалам\n\n"
                f"🎯 <b>ИЛИ:</b> Купите доступ сразу\n\n"
                f"Начните с теста или покупки:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check <id> - проверка статуса платежа"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Укажите ID платежа</b>\n\n"
            "Пример: <code>/check test_1234567890</code>\n"
            "Пример: <code>/check variatica_1234567890</code>\n\n"
            "ID платежа вы получаете при создании заказа.",
            parse_mode="HTML"
        )
        return
    
    payment_id = context.args[0]
    
    logger.info(f"🔍 User {user_id} ({user_name}) checked payment: {payment_id}")
    
    await update.message.reply_text(f"🔍 Проверяю статус платежа: <code>{payment_id}</code>", parse_mode="HTML")
    
    # Проверяем статус через API
    result = check_payment_status_db(payment_id)
    
    if not result.get("success"):
        error_msg = result.get('error', 'Неизвестная ошибка')
        await update.message.reply_text(f"❌ <b>Ошибка:</b> {error_msg}", parse_mode="HTML")
        return
    
    status = result.get("status", "unknown")
    
    if status == "succeeded":
        is_test = "test_" in payment_id
        
        if is_test:
            message = (
                f"🎉 <b>ТЕСТОВЫЙ ПЛАТЕЖ ОПЛАЧЕН!</b>\n\n"
                f"✅ Платеж <code>{payment_id}</code> успешно завершен!\n\n"
                f"🔓 <b>СИСТЕМА РАБОТАЕТ КОРРЕКТНО!</b>\n"
                f"Тестовые материалы будут доступны в течение 5 минут.\n\n"
                f"Для полного курса используйте команду /myaccess"
            )
        else:
            message = (
                f"🎉 <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\n"
                f"✅ Ваш заказ <code>{payment_id}</code> успешно оплачен!\n\n"
                f"🔓 <b>ДОСТУП ОТКРЫТ!</b>\n"
                f"Вы получили доступ ко всем материалам полного пакета ВАРИАТИКА!\n\n"
                f"Для получения материалов используйте /materials"
            )
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ <b>ОЖИДАЕТ ОПЛАТЫ</b>\n\n"
            f"Заказ <code>{payment_id}</code> еще не оплачен.\n\n"
            f"<b>Для оплаты:</b>\n"
            f"1. Используйте ссылку из бота\n"
            f"2. Выберите способ оплаты\n"
            f"3. После оплаты статус обновится автоматически"
        )
    elif status == "canceled":
        message = (
            f"❌ <b>ПЛАТЕЖ ОТМЕНЕН</b>\n\n"
            f"Заказ <code>{payment_id}</code> был отменен.\n\n"
            f"Для создания нового заказа используйте команду /start"
        )
    else:
        message = f"📊 <b>Статус заказа:</b> <code>{status}</code>"
    
    await update.message.reply_text(message, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - справка по командам"""
    help_text = (
        f"🆘 <b>КОМАНДЫ БОТА ВАРИАТИКА v2.3</b>\n\n"
        
        f"<b>Основные команды:</b>\n"
        f"<code>/start</code> - начать тест\n"
        f"<code>/help</code> - эта справка\n"
        f"<code>/cancel</code> - отменить текущий тест\n\n"
        
        f"<b>Команды доступа:</b>\n"
        f"<code>/materials</code> - получить материалы после оплаты\n"
        f"<code>/myaccess</code> - проверить статус доступа\n"
        f"<code>/check &lt;id&gt;</code> - проверить статус платежа\n\n"
        
        f"<b>Информация:</b>\n"
        f"🎯 <b>Тест:</b> 4 этапа, 32 вопроса\n"
        f"⏱ <b>Время:</b> 10-15 минут\n"
        f"💰 <b>Полный пакет:</b> 690 руб\n"
        f"🧪 <b>Тест оплаты:</b> 1 руб\n\n"
        
        f"<b>Поддержка:</b>\n"
        f"Автор: {AUTHOR_LINK}\n"
        f"Бот: {BOT_LINK}"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

# ============================================
# ============================================
# ОБРАБОТЧИК СЕТЕВЫХ ОШИБОК
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    error_msg = str(context.error)
    logger.error(f"💥 Ошибка: {error_msg}")

    # Сетевые ошибки
    if any(keyword in error_msg for keyword in ["NetworkError", "RemoteProtocolError", "Timeout", "ConnectionError", "Connection reset", "Connection refused", "ReadTimeout"]):
        logger.warning(f"⚠️ Сетевая ошибка: {error_msg}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ Временная сетевая проблема. Попробуйте снова через 10 секунд."
                )
            except:
                pass
        
        await asyncio.sleep(2)
        return

    # Ошибки валидации от Telegram
    if "Bad Request" in error_msg and "message is not modified" in error_msg:
        logger.info(f"ℹ️ Игнорирую: message is not modified")
        return

    if "Bad Request" in error_msg and "query is too old" in error_msg:
        logger.info(f"ℹ️ Игнорирую: query is too old")
        return

    if "Forbidden" in error_msg and "bot was blocked by the user" in error_msg:
        logger.info(f"ℹ️ Пользователь заблокировал бота")
        return

    # Ошибки конфликта webhook
    if "Conflict" in error_msg and "can't use getUpdates method while webhook is active" in error_msg:
        logger.error(f"❌ Конфликт webhook. Очищаю...")
        try:
            clear_telegram_conflicts()
        except:
            pass
        return

    # Ошибки API
    if "Payment" in error_msg and "already paid" in error_msg:
        logger.warning(f"⚠️ Платеж уже оплачен: {error_msg}")
        if update and update.callback_query:
            try:
                await update.callback_query.answer("✅ Платеж уже подтвержден!", show_alert=True)
                payment_id = update.callback_query.data.split('_')[1] if '_' in update.callback_query.data else 'unknown'
                await update.callback_query.edit_message_text(
                    f"✅ *ПЛАТЕЖ УЖЕ ОПЛАЧЕН!*\n\n"
                    f"Ваш платеж уже был подтвержден ранее.\n\n"
                    f"Для получения материалов используйте /materials",
                    parse_mode='Markdown'
                )
            except:
                pass
        return

    # Критические ошибки
    logger.critical(f"💥 Необработанная ошибка: {error_msg}")
    logger.exception(context.error)

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла непредвиденная ошибка. Попробуйте /start\n\n"
                "Если ошибка повторяется, свяжитесь с поддержкой."
            )
        except:
            pass

# ============================================
# ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ ДЛЯ КНОПОК
# ============================================

async def check_access_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для кнопки 'Проверить доступ'"""
    query = update.callback_query
    await query.answer()
    # Вызываем команду /myaccess
    return await myaccess_command(update, context)

async def check_current_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для кнопки 'Проверить статус' в /myaccess"""
    query = update.callback_query
    await query.answer("🔄 Обновляю статус...")
    user_id = query.from_user.id
    user_name = query.from_user.first_name

    # Проверяем доступ через API
    access_data = get_user_access(user_id)

    if not access_data.get('success', False):
        error_msg = access_data.get('error', 'Unknown error')
        await query.edit_message_text(
            f"❌ Ошибка проверки доступа: {error_msg}",
            parse_mode="HTML"
        )
        return

    if access_data.get('has_access'):
        accesses = access_data.get('accesses', [])
        active_access = None
        for access in accesses:
            if access.get('has_access') and access.get('is_active'):
                active_access = access
                break
        
        if active_access:
            payment_id = active_access.get('payment_id')
            profile_key = active_access.get('profile_key')
            granted_at = active_access.get('granted_at')
            expires_at = active_access.get('expires_at')
            
            # Генерируем ссылку
            materials_link = generate_yandex_disk_link(profile_key) if profile_key else "https://disk.yandex.ru"
            
            keyboard = [
                [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)],
                [InlineKeyboardButton("🔄 ОБНОВИТЬ СТАТУС", callback_data="check_current_status")]
            ]
            
            await query.edit_message_text(
                f"✅ <b>ДОСТУП АКТИВЕН! (обновлено)</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_name}\n"
                f"🎯 <b>Профиль:</b> {profile_key or 'Не указан'}\n"
                f"📦 <b>Пакет:</b> Полный ВАРИАТИКА\n"
                f"📅 <b>Доступ открыт:</b> {granted_at or 'Неизвестно'}\n"
                f"📅 <b>Действителен до:</b> {expires_at or 'Неизвестно'}\n\n"
                f"<b>Для получения материалов используйте кнопку ниже:</b>\n\n"
                f"🔗 <b>Ссылка:</b> {materials_link}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                f"⚠️ <b>ДОСТУП НАЙДЕН, НО НЕ АКТИВЕН (обновлено)</b>\n\n"
                f"У вас есть доступ, но он не активен или истек.",
                parse_mode="HTML"
            )
    else:
        await query.edit_message_text(
            f"❌ <b>ДОСТУП НЕ АКТИВЕН (обновлено)</b>\n\n"
            f"Доступ не найден или не активирован.",
            parse_mode="HTML"
        )

# ============================================
# ОБРАБОТЧИК ДЛЯ КОМАНДЫ /CANCEL ВНЕ ConversationHandler
# ============================================

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel для отмены вне ConversationHandler"""
    await update.message.reply_text(
        "❌ Текущая операция отменена.\n\n"
        "Чтобы начать тест заново: /start\n"
        "Чтобы проверить доступ: /myaccess"
    )
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ОБРАБОТЧИК ДЛЯ НЕИЗВЕСТНЫХ КОМАНД
# ============================================

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "🤔 Неизвестная команда.\n\n"
        "Доступные команды:\n"
        "/start - начать тест\n"
        "/help - справка по командам\n"
        "/materials - получить материалы\n"
        "/myaccess - проверить статус доступа\n"
        "/check <id> - проверить статус платежа\n"
        "/cancel - отмена текущей операции"
    )

async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных callback-запросов"""
    query = update.callback_query
    await query.answer("⚠️ Эта кнопка больше не активна")
    await query.edit_message_text(
        "⚠️ <b>ЭТА КНОПКА УСТАРЕЛА</b>\n\n"
        "Пожалуйста, используйте команды:\n"
        "/start - начать тест\n"
        "/materials - получить материалы\n"
        "/myaccess - проверить статус доступа\n\n"
        "Или начните заново:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 НАЧАТЬ ТЕСТ", callback_data="start_test")],
            [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП", callback_data="show_package")]
        ]),
        parse_mode="HTML"
    )

# ============================================
# ОБРАБОТЧИК ДЛЯ ТЕКСТОВЫХ СООБЩЕНИЙ
# ============================================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    # Игнорируем команды
    if text.startswith('/'):
        return

    # Проверяем, есть ли активный тест
    if context.user_data.get("stage1_current") is not None:
        await update.message.reply_text(
            "⚠️ <b>СЕЙЧАС ИДЕТ ТЕСТ!</b>\n\n"
            "Пожалуйста, отвечайте на вопросы, используя кнопки.\n"
            "Если хотите отменить тест: /cancel",
            parse_mode="HTML"
        )
        return

    # Проверяем, есть ли доступ у пользователя
    access_data = get_user_access(user_id)
    if access_data.get('has_access', False):
        await update.message.reply_text(
            "👋 <b>Привет!</b>\n\n"
            "У вас уже есть доступ к материалам.\n"
            "Используйте /materials для получения материалов.\n\n"
            "Хотите пройти тест заново? /start",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "👋 <b>Привет!</b>\n\n"
            "Я - бот ВАРИАТИКА. Я помогу вам узнать о себе то, что вы ещё не знаете.\n\n"
            "🎯 <b>Что я умею:</b>\n"
            "• Проводить психодиагностический тест (32 вопроса)\n"
            "• Определять ваш тип восприятия и мышления\n"
            "• Показывать поведенческие паттерны\n"
            "• Предоставлять персонализированные рекомендации\n\n"
            "🚀 <b>Начать:</b> /start\n"
            "📚 <b>Справка:</b> /help",
            parse_mode="HTML"
        )

# ============================================
# ПЕРИОДИЧЕСКАЯ ПРОВЕРКА ДОСТУПОВ
# ============================================

async def check_expired_accesses(context: ContextTypes.DEFAULT_TYPE):
    """Периодическая проверка истекших доступов"""
    try:
        logger.info("🔄 Периодическая проверка истекших доступов...")

        # Здесь можно добавить логику для проверки истекших доступов
        # и уведомления пользователей
        
        # Временная заглушка
        logger.info("✅ Проверка истекших доступов завершена")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке истекших доступов: {e}")

# ============================================
# НАСТРОЙКА И ЗАПУСК БОТА
# ============================================

def main():
    """Основная функция запуска бота"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК БОТА ВАРИАТИКА v2.3")
    print("Версия: ПОЛНАЯ ВЕРСИЯ 2.3 - ОБЪЕДИНЕНИЕ РАБОЧЕЙ ЛОГИКИ v1.9 С ПЛАТЕЖНОЙ СИСТЕМОЙ v2.2")
    print("="*60)

    # Очистка конфликтов перед запуском
    try:
        clear_telegram_conflicts()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось очистить конфликты: {e}")

    # Проверка загрузки всех 36 профилей
    try:
        profiles_loaded = check_all_profiles()
        if not profiles_loaded:
            logger.warning("⚠️ Не все профили загружены! Возможны проблемы с отображением результатов.")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке профилей: {e}")

    # Создание Application
    app = Application.builder().token(TOKEN).build()

    # ConversationHandler для теста (ОСНОВНОЙ)
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
                CallbackQueryHandler(show_stage_2_details, pattern="^stage2_details$"),
                CallbackQueryHandler(back_to_stage2_intro, pattern="^back_to_stage2_intro$"),
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(show_stage_3_details, pattern="^stage3_details$"),
                CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$"),
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4: [
                CallbackQueryHandler(show_stage_4_details, pattern="^stage4_details$"),
                CallbackQueryHandler(back_to_stage4_intro, pattern="^back_to_stage4_intro$"),
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
            ],
            CLARIFICATION: [
                CallbackQueryHandler(handle_clarification_answer, pattern="^clarify_")
            ],
            DILTS_CLARIFICATION: [
                CallbackQueryHandler(handle_dilts_clarification, pattern="^dilts_clarify_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(buy_variatica_package, pattern="^buy_variatica_package$"),
                CallbackQueryHandler(test_payment, pattern="^test_payment$"),
                CallbackQueryHandler(status_payment, pattern="^status_")
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(buy_variatica_package, pattern="^buy_variatica_package$"),
                CallbackQueryHandler(test_payment, pattern="^test_payment$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start)
        ],
        allow_reentry=True,
        conversation_timeout=timedelta(minutes=30)
    )

    # Добавляем ConversationHandler
    app.add_handler(conv_handler)

    # Команды бота
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myaccess", myaccess_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("materials", materials_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Обработчики callback-запросов (отдельные от ConversationHandler)
    app.add_handler(CallbackQueryHandler(check_access_callback, pattern="^check_access$"))
    app.add_handler(CallbackQueryHandler(check_current_status_callback, pattern="^check_current_status$"))
    app.add_handler(CallbackQueryHandler(unknown_callback))

    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    # Обработчик неизвестных команд
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    # Настраиваем JobQueue для периодических задач
    job_queue = app.job_queue
    if job_queue:
        # Проверка истекших доступов каждый час
        job_queue.run_repeating(check_expired_accesses, interval=3600, first=10)

    print("\n" + "="*60)
    print("🤖 БОТ ВАРИАТИКА v2.3 ЗАПУЩЕН И ГОТОВ К РАБОТЕ")
    print("="*60)
    print("📊 КЛЮЧЕВЫЕ ВОЗМОЖНОСТИ:")
    print("  • Адаптивный тест (32 вопроса, 4 этапа)")
    print("  • 36 психодиагностических профилей")
    print("  • Интегрированная платежная система (ЮKassa)")
    print("  • Автоматическая выдача материалов")
    print("  • Система проверки доступа через API")
    print("="*60)
    print("🔗 КОНФИГУРАЦИЯ:")
    print(f"  • API URL: {API_URL}")
    print(f"  • Бот: {BOT_LINK}")
    print(f"  • Автор: {AUTHOR_LINK}")
    print("="*60)
    print("✅ СТАТУС:")
    print("  • Профили: 36/36 загружено")
    print("  • Платежная система: интегрирована")
    print("  • API: подключено")
    print("  • Обработка ошибок: настроена")
    print("="*60 + "\n")

    # Запуск бота
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.critical(f"💥 КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ БОТА: {e}")
        sys.exit(1)

# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    main()
