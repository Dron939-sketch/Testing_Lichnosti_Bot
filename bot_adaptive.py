#!/usr/bin/env python3
"""
ВАРИАТИКА: ЕДИНЫЙ БОТ - ТЕСТ + ПЛАТЕЖНАЯ СИСТЕМА
Объединяет психодиагностику и персонализированные материалы
"""

import os
import json
import logging
import asyncio
import time
import base64
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
import math
import re

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    ApplicationBuilder
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Импортируем существующие модули
from loader import loader
from base import VariaticaProfile

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую.."

# Состояния ConversationHandler
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION = range(10)

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
        "text": "Что важнее в отношениях?",
        "options": {
            "a": {"text": "Понимание, чувства, близость", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Надёжность, стабильность, общее дело", "scores": {"MATERIAL": 2}},
            "c": {"text": "Доверие и уважение", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Практическая поддержка", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_7",
        "text": "Если бы ты мог сохранить только одно, что бы выбрал?",
        "options": {
            "a": {"text": "Память о важных моментах", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Ключевые материальные вещи", "scores": {"MATERIAL": 2}},
            "c": {"text": "Отношения с близкими", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Финансовую стабильность", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_8",
        "text": "Какой тип потерь переживается тяжелее?",
        "options": {
            "a": {"text": "Потерю смысла, надежды, веры", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Потерю денег, имущества, работы", "scores": {"MATERIAL": 2}},
            "c": {"text": "Потерю отношений", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Потерю безопасности", "scores": {"MATERIAL": 1}}
        }
    }
]

# ============================================
# ВОПРОСЫ ЭТАПА 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

STAGE_2_QUESTIONS = {
    "SP": [  # Инструментально-достиженческий (Инструменты + Действия)
        {
            "id": "q2_sp_1",
            "text": "Когда сталкиваешься с новой задачей, твой первый импульс:",
            "options": {
                "a": {"text": "Разобрать на шаги и действовать", "scores": {"SP": 2}},
                "b": {"text": "Понять суть, прежде чем действовать", "scores": {"IP": 1}},
                "c": {"text": "Спросить у других, как лучше сделать", "scores": {"SA": 1}},
                "d": {"text": "Сначала понять, зачем мне это", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_2",
            "text": "Что важнее в работе?",
            "options": {
                "a": {"text": "Результат и эффективность", "scores": {"SP": 2}},
                "b": {"text": "Процесс и качество", "scores": {"IP": 1}},
                "c": {"text": "Команда и атмосфера", "scores": {"SA": 1}},
                "d": {"text": "Смысл и развитие", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_3",
            "text": "Как ты принимаешь решения?",
            "options": {
                "a": {"text": "Быстро, на основе фактов", "scores": {"SP": 2}},
                "b": {"text": "Аналитически, взвесив всё", "scores": {"IP": 1}},
                "c": {"text": "С учётом мнений других", "scores": {"SA": 1}},
                "d": {"text": "По внутреннему ощущению", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_4",
            "text": "Твой подход к проблемам:",
            "options": {
                "a": {"text": "Ищу практическое решение", "scores": {"SP": 2}},
                "b": {"text": "Анализирую причины", "scores": {"IP": 1}},
                "c": {"text": "Обсуждаю с другими", "scores": {"SA": 1}},
                "d": {"text": "Ищу глубинный смысл", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_5",
            "text": "Что мотивирует тебя больше всего?",
            "options": {
                "a": {"text": "Достижения и успех", "scores": {"SP": 2}},
                "b": {"text": "Понимание и знания", "scores": {"IP": 1}},
                "c": {"text": "Принадлежность и признание", "scores": {"SA": 1}},
                "d": {"text": "Самовыражение и рост", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_6",
            "text": "Как ты относишься к правилам?",
            "options": {
                "a": {"text": "Как к инструменту для результата", "scores": {"SP": 2}},
                "b": {"text": "Как к системе, которую можно улучшить", "scores": {"IP": 1}},
                "c": {"text": "Как к социальным нормам", "scores": {"SA": 1}},
                "d": {"text": "Как к чему-то, что можно переосмыслить", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_7",
            "text": "Твоя сильная сторона в команде:",
            "options": {
                "a": {"text": "Организация и действие", "scores": {"SP": 2}},
                "b": {"text": "Анализ и планирование", "scores": {"IP": 1}},
                "c": {"text": "Коммуникация и поддержка", "scores": {"SA": 1}},
                "d": {"text": "Вдохновение и видение", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sp_8",
            "text": "Как ты учишься новому?",
            "options": {
                "a": {"text": "Через практику и действие", "scores": {"SP": 2}},
                "b": {"text": "Через изучение и анализ", "scores": {"IP": 1}},
                "c": {"text": "Через общение и примеры", "scores": {"SA": 1}},
                "d": {"text": "Через интуицию и опыт", "scores": {"IA": 1}}
            }
        }
    ],
    "IA": [  # Экзистенциально-рефлексивный (Идеи + Рефлексия)
        {
            "id": "q2_ia_1",
            "text": "Когда сталкиваешься с новой задачей, твой первый импульс:",
            "options": {
                "a": {"text": "Сначала понять, зачем мне это", "scores": {"IA": 2}},
                "b": {"text": "Разобрать на шаги и действовать", "scores": {"SP": 1}},
                "c": {"text": "Понять суть, прежде чем действовать", "scores": {"IP": 1}},
                "d": {"text": "Спросить у других, как лучше сделать", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_2",
            "text": "Что важнее в работе?",
            "options": {
                "a": {"text": "Смысл и развитие", "scores": {"IA": 2}},
                "b": {"text": "Результат и эффективность", "scores": {"SP": 1}},
                "c": {"text": "Процесс и качество", "scores": {"IP": 1}},
                "d": {"text": "Команда и атмосфера", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_3",
            "text": "Как ты принимаешь решения?",
            "options": {
                "a": {"text": "По внутреннему ощущению", "scores": {"IA": 2}},
                "b": {"text": "Быстро, на основе фактов", "scores": {"SP": 1}},
                "c": {"text": "Аналитически, взвесив всё", "scores": {"IP": 1}},
                "d": {"text": "С учётом мнений других", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_4",
            "text": "Твой подход к проблемам:",
            "options": {
                "a": {"text": "Ищу глубинный смысл", "scores": {"IA": 2}},
                "b": {"text": "Ищу практическое решение", "scores": {"SP": 1}},
                "c": {"text": "Анализирую причины", "scores": {"IP": 1}},
                "d": {"text": "Обсуждаю с другими", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_5",
            "text": "Что мотивирует тебя больше всего?",
            "options": {
                "a": {"text": "Самовыражение и рост", "scores": {"IA": 2}},
                "b": {"text": "Достижения и успех", "scores": {"SP": 1}},
                "c": {"text": "Понимание и знания", "scores": {"IP": 1}},
                "d": {"text": "Принадлежность и признание", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_6",
            "text": "Как ты относишься к правилам?",
            "options": {
                "a": {"text": "Как к чему-то, что можно переосмыслить", "scores": {"IA": 2}},
                "b": {"text": "Как к инструменту для результата", "scores": {"SP": 1}},
                "c": {"text": "Как к системе, которую можно улучшить", "scores": {"IP": 1}},
                "d": {"text": "Как к социальным нормам", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_7",
            "text": "Твоя сильная сторона в команде:",
            "options": {
                "a": {"text": "Вдохновение и видение", "scores": {"IA": 2}},
                "b": {"text": "Организация и действие", "scores": {"SP": 1}},
                "c": {"text": "Анализ и планирование", "scores": {"IP": 1}},
                "d": {"text": "Коммуникация и поддержка", "scores": {"SA": 1}}
            }
        },
        {
            "id": "q2_ia_8",
            "text": "Как ты учишься новому?",
            "options": {
                "a": {"text": "Через интуицию и опыт", "scores": {"IA": 2}},
                "b": {"text": "Через практику и действие", "scores": {"SP": 1}},
                "c": {"text": "Через изучение и анализ", "scores": {"IP": 1}},
                "d": {"text": "Через общение и примеры", "scores": {"SA": 1}}
            }
        }
    ],
    "IP": [  # Структурно-аналитический (Инструменты + Рефлексия)
        {
            "id": "q2_ip_1",
            "text": "Когда сталкиваешься с новой задачей, твой первый импульс:",
            "options": {
                "a": {"text": "Понять суть, прежде чем действовать", "scores": {"IP": 2}},
                "b": {"text": "Разобрать на шаги и действовать", "scores": {"SP": 1}},
                "c": {"text": "Спросить у других, как лучше сделать", "scores": {"SA": 1}},
                "d": {"text": "Сначала понять, зачем мне это", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_2",
            "text": "Что важнее в работе?",
            "options": {
                "a": {"text": "Процесс и качество", "scores": {"IP": 2}},
                "b": {"text": "Результат и эффективность", "scores": {"SP": 1}},
                "c": {"text": "Команда и атмосфера", "scores": {"SA": 1}},
                "d": {"text": "Смысл и развитие", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_3",
            "text": "Как ты принимаешь решения?",
            "options": {
                "a": {"text": "Аналитически, взвесив всё", "scores": {"IP": 2}},
                "b": {"text": "Быстро, на основе фактов", "scores": {"SP": 1}},
                "c": {"text": "С учётом мнений других", "scores": {"SA": 1}},
                "d": {"text": "По внутреннему ощущению", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_4",
            "text": "Твой подход к проблемам:",
            "options": {
                "a": {"text": "Анализирую причины", "scores": {"IP": 2}},
                "b": {"text": "Ищу практическое решение", "scores": {"SP": 1}},
                "c": {"text": "Обсуждаю с другими", "scores": {"SA": 1}},
                "d": {"text": "Ищу глубинный смысл", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_5",
            "text": "Что мотивирует тебя больше всего?",
            "options": {
                "a": {"text": "Понимание и знания", "scores": {"IP": 2}},
                "b": {"text": "Достижения и успех", "scores": {"SP": 1}},
                "c": {"text": "Принадлежность и признание", "scores": {"SA": 1}},
                "d": {"text": "Самовыражение и рост", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_6",
            "text": "Как ты относишься к правилам?",
            "options": {
                "a": {"text": "Как к системе, которую можно улучшить", "scores": {"IP": 2}},
                "b": {"text": "Как к инструменту для результата", "scores": {"SP": 1}},
                "c": {"text": "Как к социальным нормам", "scores": {"SA": 1}},
                "d": {"text": "Как к чему-то, что можно переосмыслить", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_7",
            "text": "Твоя сильная сторона в команде:",
            "options": {
                "a": {"text": "Анализ и планирование", "scores": {"IP": 2}},
                "b": {"text": "Организация и действие", "scores": {"SP": 1}},
                "c": {"text": "Коммуникация и поддержка", "scores": {"SA": 1}},
                "d": {"text": "Вдохновение и видение", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_ip_8",
            "text": "Как ты учишься новому?",
            "options": {
                "a": {"text": "Через изучение и анализ", "scores": {"IP": 2}},
                "b": {"text": "Через практику и действие", "scores": {"SP": 1}},
                "c": {"text": "Через общение и примеры", "scores": {"SA": 1}},
                "d": {"text": "Через интуицию и опыт", "scores": {"IA": 1}}
            }
        }
    ],
    "SA": [  # Социально-аффилиативный (Действия + Идеи)
        {
            "id": "q2_sa_1",
            "text": "Когда сталкиваешься с новой задачей, твой первый импульс:",
            "options": {
                "a": {"text": "Спросить у других, как лучше сделать", "scores": {"SA": 2}},
                "b": {"text": "Разобрать на шаги и действовать", "scores": {"SP": 1}},
                "c": {"text": "Понять суть, прежде чем действовать", "scores": {"IP": 1}},
                "d": {"text": "Сначала понять, зачем мне это", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_2",
            "text": "Что важнее в работе?",
            "options": {
                "a": {"text": "Команда и атмосфера", "scores": {"SA": 2}},
                "b": {"text": "Результат и эффективность", "scores": {"SP": 1}},
                "c": {"text": "Процесс и качество", "scores": {"IP": 1}},
                "d": {"text": "Смысл и развитие", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_3",
            "text": "Как ты принимаешь решения?",
            "options": {
                "a": {"text": "С учётом мнений других", "scores": {"SA": 2}},
                "b": {"text": "Быстро, на основе фактов", "scores": {"SP": 1}},
                "c": {"text": "Аналитически, взвесив всё", "scores": {"IP": 1}},
                "d": {"text": "По внутреннему ощущению", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_4",
            "text": "Твой подход к проблемам:",
            "options": {
                "a": {"text": "Обсуждаю с другими", "scores": {"SA": 2}},
                "b": {"text": "Ищу практическое решение", "scores": {"SP": 1}},
                "c": {"text": "Анализирую причины", "scores": {"IP": 1}},
                "d": {"text": "Ищу глубинный смысл", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_5",
            "text": "Что мотивирует тебя больше всего?",
            "options": {
                "a": {"text": "Принадлежность и признание", "scores": {"SA": 2}},
                "b": {"text": "Достижения и успех", "scores": {"SP": 1}},
                "c": {"text": "Понимание и знания", "scores": {"IP": 1}},
                "d": {"text": "Самовыражение и рост", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_6",
            "text": "Как ты относишься к правилам?",
            "options": {
                "a": {"text": "Как к социальным нормам", "scores": {"SA": 2}},
                "b": {"text": "Как к инструменту для результата", "scores": {"SP": 1}},
                "c": {"text": "Как к системе, которую можно улучшить", "scores": {"IP": 1}},
                "d": {"text": "Как к чему-то, что можно переосмыслить", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_7",
            "text": "Твоя сильная сторона в команде:",
            "options": {
                "a": {"text": "Коммуникация и поддержка", "scores": {"SA": 2}},
                "b": {"text": "Организация и действие", "scores": {"SP": 1}},
                "c": {"text": "Анализ и планирование", "scores": {"IP": 1}},
                "d": {"text": "Вдохновение и видение", "scores": {"IA": 1}}
            }
        },
        {
            "id": "q2_sa_8",
            "text": "Как ты учишься новому?",
            "options": {
                "a": {"text": "Через общение и примеры", "scores": {"SA": 2}},
                "b": {"text": "Через практику и действие", "scores": {"SP": 1}},
                "c": {"text": "Через изучение и анализ", "scores": {"IP": 1}},
                "d": {"text": "Через интуицию и опыт", "scores": {"IA": 1}}
            }
        }
    ]
}

# ============================================
# ВОПРОСЫ ЭТАПА 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
# ============================================

STAGE_3_QUESTIONS = [
    {
        "id": "q3_1",
        "text": "Когда что-то идёт не по плану, ты обычно:",
        "options": {
            "a": {"text": "Быстро ищу альтернативу", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Начинаю сомневаться в себе", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Виню обстоятельства или других", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Замираю и не знаю что делать", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_2",
        "text": "Как ты реагируешь на критику?",
        "options": {
            "a": {"text": "Принимаю как обратную связь", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Сильно переживаю, долго думаю об этом", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Сразу защищаюсь или контратакую", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Стараюсь избегать ситуаций с критикой", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_3",
        "text": "В конфликтной ситуации ты:",
        "options": {
            "a": {"text": "Ищу компромисс", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Уступаю, чтобы сохранить отношения", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Настаиваю на своём", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Избегаю конфликта", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_4",
        "text": "При принятии важного решения:",
        "options": {
            "a": {"text": "Собираю информацию и взвешиваю варианты", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Долго сомневаюсь, боюсь ошибиться", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Действую быстро, полагаясь на интуицию", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Жду, когда ситуация прояснится сама", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_5",
        "text": "Когда нужно сделать что-то новое и сложное:",
        "options": {
            "a": {"text": "Разбиваю на этапы и начинаю", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Откладываю, пока не буду уверен в успехе", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Берусь сразу, разбираясь по ходу дела", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Избегаю, если есть возможность", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_6",
        "text": "Твоё отношение к неудачам:",
        "options": {
            "a": {"text": "Это опыт для роста", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Это доказательство моей несостоятельности", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Это результат внешних факторов", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Это повод больше не пытаться", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_7",
        "text": "В отношениях с близкими ты склонен:",
        "options": {
            "a": {"text": "Открыто обсуждать проблемы", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Молчать, чтобы не расстраивать других", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Требовать понимания своих потребностей", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Избегать глубоких разговоров", "scores": {"FREEZE": 2}}
        }
    },
    {
        "id": "q3_8",
        "text": "Как ты относишься к своим ошибкам?",
        "options": {
            "a": {"text": "Анализирую и делаю выводы", "scores": {"ADAPTIVE": 2}},
            "b": {"text": "Долго корить себя", "scores": {"SELF_DOUBT": 2}},
            "c": {"text": "Нахожу оправдания", "scores": {"EXTERNAL_BLAME": 2}},
            "d": {"text": "Стараюсь забыть", "scores": {"FREEZE": 2}}
        }
    }
]

# ============================================
# ВОПРОСЫ ЭТАПА 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

STAGE_4_QUESTIONS = [
    {
        "id": "q4_1",
        "text": "Что тебе важнее в жизни?",
        "options": {
            "a": {"text": "Конкретные цели и результаты", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Правильные действия и привычки", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Умения и компетенции", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Ценности и убеждения", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_2",
        "text": "Когда чувствуешь неудовлетворённость, это обычно связано с:",
        "options": {
            "a": {"text": "Окружением (место, люди, условия)", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Тем, что я делаю или не делаю", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Нехваткой навыков или знаний", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Конфликтом с моими принципами", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_3",
        "text": "Для роста и развития тебе важнее всего:",
        "options": {
            "a": {"text": "Поменять окружение", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Начать действовать по-новому", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Освоить новые навыки", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Пересмотреть свои ценности", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_4",
        "text": "Основной источник проблем в жизни:",
        "options": {
            "a": {"text": "Внешние обстоятельства", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Неправильные действия", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Недостаток способностей", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Ошибочные убеждения", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_5",
        "text": "Какой комплимент был бы для тебя самым ценным?",
        "options": {
            "a": {"text": "Ты создаёшь отличную атмосферу", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Ты очень продуктивен", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Ты талантлив и способен", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Ты человек с принципами", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_6",
        "text": "На что ты обращаешь внимание при знакомстве с человеком?",
        "options": {
            "a": {"text": "Как он выглядит и где находится", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Что и как он делает", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "На что он способен", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Во что он верит", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_7",
        "text": "Что помогает тебе восстановить силы?",
        "options": {
            "a": {"text": "Смена обстановки", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Ритмичные действия (спорт, хобби)", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Изучение чего-то нового", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Разговор по душам о важном", "scores": {"VALUES": 2}}
        }
    },
    {
        "id": "q4_8",
        "text": "Что для тебя означает 'успех'?",
        "options": {
            "a": {"text": "Хорошие условия жизни", "scores": {"ENVIRONMENT": 2}},
            "b": {"text": "Регулярные достижения", "scores": {"BEHAVIOR": 2}},
            "c": {"text": "Признание мастерства", "scores": {"CAPABILITIES": 2}},
            "d": {"text": "Жизнь в согласии с собой", "scores": {"VALUES": 2}}
        }
    }
]

# ============================================
# УТОЧНЯЮЩИЕ ВОПРОСЫ (CLARIFICATION)
# ============================================

CLARIFICATION_QUESTIONS = {
    "SP": [
        {
            "id": "clar_sp_1",
            "text": "Когда ты достигаешь цели, что происходит дальше?",
            "options": {
                "a": {"text": "Сразу ставлю новую", "scores": {"SP": 2}},
                "b": {"text": "Наслаждаюсь результатом", "scores": {"SP": 1}},
                "c": {"text": "Анализирую, что можно было сделать лучше", "scores": {"IP": 1}},
                "d": {"text": "Делиться успехом с другими", "scores": {"SA": 1}}
            }
        },
        {
            "id": "clar_sp_2",
            "text": "Что для тебя важнее в проекте?",
            "options": {
                "a": {"text": "Результат и сроки", "scores": {"SP": 2}},
                "b": {"text": "Эффективность процесса", "scores": {"SP": 1}},
                "c": {"text": "Качество и детали", "scores": {"IP": 1}},
                "d": {"text": "Работа в команде", "scores": {"SA": 1}}
            }
        }
    ],
    "IA": [
        {
            "id": "clar_ia_1",
            "text": "Когда ты размышляешь о жизни, что тебя больше всего волнует?",
            "options": {
                "a": {"text": "Смысл и предназначение", "scores": {"IA": 2}},
                "b": {"text": "Личностный рост", "scores": {"IA": 1}},
                "c": {"text": "Практическая реализация идей", "scores": {"SP": 1}},
                "d": {"text": "Понимание систем и закономерностей", "scores": {"IP": 1}}
            }
        },
        {
            "id": "clar_ia_2",
            "text": "Как ты воплощаешь свои идеи в жизнь?",
            "options": {
                "a": {"text": "Через творческое выражение", "scores": {"IA": 2}},
                "b": {"text": "Ищу единомышленников", "scores": {"SA": 1}},
                "c": {"text": "Разрабатываю план", "scores": {"IP": 1}},
                "d": {"text": "Начинаю действовать", "scores": {"SP": 1}}
            }
        }
    ],
    "IP": [
        {
            "id": "clar_ip_1",
            "text": "Когда ты изучаешь что-то новое, как подходишь к процессу?",
            "options": {
                "a": {"text": "Систематически, от простого к сложному", "scores": {"IP": 2}},
                "b": {"text": "Углубляюсь в детали", "scores": {"IP": 1}},
                "c": {"text": "Ищу практическое применение", "scores": {"SP": 1}},
                "d": {"text": "Обсуждаю с экспертами", "scores": {"SA": 1}}
            }
        },
        {
            "id": "clar_ip_2",
            "text": "Как ты принимаешь сложные решения?",
            "options": {
                "a": {"text": "Создаю таблицы плюсов и минусов", "scores": {"IP": 2}},
                "b": {"text": "Исследую все варианты досконально", "scores": {"IP": 1}},
                "c": {"text": "Действую по ситуации", "scores": {"SP": 1}},
                "d": {"text": "Прислушиваюсь к интуиции", "scores": {"IA": 1}}
            }
        }
    ],
    "SA": [
        {
            "id": "clar_sa_1",
            "text": "Что для тебя самое важное в общении?",
            "options": {
                "a": {"text": "Эмоциональная связь", "scores": {"SA": 2}},
                "b": {"text": "Взаимопомощь и поддержка", "scores": {"SA": 1}},
                "c": {"text": "Обмен информацией и знаниями", "scores": {"IP": 1}},
                "d": {"text": "Совместные достижения", "scores": {"SP": 1}}
            }
        },
        {
            "id": "clar_sa_2",
            "text": "Как ты проявляешь заботу о других?",
            "options": {
                "a": {"text": "Через внимание и участие", "scores": {"SA": 2}},
                "b": {"text": "Помогаю практическими делами", "scores": {"SP": 1}},
                "c": {"text": "Стараюсь понять глубинные причины", "scores": {"IP": 1}},
                "d": {"text": "Вдохновляю и поддерживаю", "scores": {"IA": 1}}
            }
        }
    ]
}

# ============================================
# ФУНКЦИИ РАСЧЕТА ПРОФИЛЯ
# ============================================

def determine_perception_type(scores: Dict[str, int]) -> Dict[str, Any]:
    """Определяет тип восприятия по результатам 1 этапа"""
    external_score = scores.get("EXTERNAL", 0)
    internal_score = scores.get("INTERNAL", 0)
    symbolic_score = scores.get("SYMBOLIC", 0)
    material_score = scores.get("MATERIAL", 0)
    
    # Определяем ОРИЕНТАЦИЮ (внешняя/внутренняя)
    orientation = "EXTERNAL" if external_score > internal_score else "INTERNAL"
    if external_score == internal_score:
        orientation = "BALANCED"
    
    # Определяем ФОКУС (символический/материальный)
    focus = "SYMBOLIC" if symbolic_score > material_score else "MATERIAL"
    if symbolic_score == material_score:
        focus = "BALANCED"
    
    # Определяем КВАДРАНТ
    if orientation == "EXTERNAL" and focus == "MATERIAL":
        quadrant = "SP"  # Инструментально-достиженческий
    elif orientation == "INTERNAL" and focus == "SYMBOLIC":
        quadrant = "IA"  # Экзистенциально-рефлексивный
    elif orientation == "INTERNAL" and focus == "MATERIAL":
        quadrant = "IP"  # Структурно-аналитический
    elif orientation == "EXTERNAL" and focus == "SYMBOLIC":
        quadrant = "SA"  # Социально-аффилиативный
    else:
        quadrant = "SA"  # По умолчанию
    
    return {
        "orientation": orientation,
        "focus": focus,
        "quadrant": quadrant,
        "scores": {
            "EXTERNAL": external_score,
            "INTERNAL": internal_score,
            "SYMBOLIC": symbolic_score,
            "MATERIAL": material_score
        }
    }

def calculate_thinking_level_by_scores(scores: Dict[str, int]) -> Dict[str, Any]:
    """Расчет уровня мышления на основе баллов этапов 2 и 3"""
    thinking_type = max(scores, key=scores.get) if scores else "SA"
    
    primary_score = scores.get(thinking_type, 0)
    total_score = sum(scores.values())
    
    if total_score == 0:
        return {"level": 1, "coherence": 0.0, "type": "SA"}
    
    # Коэффициент согласованности (0-1)
    coherence = primary_score / total_score if total_score > 0 else 0.0
    
    # Определение уровня (1-9) на основе согласованности
    if coherence >= 0.9:
        level = 9
    elif coherence >= 0.8:
        level = 8
    elif coherence >= 0.7:
        level = 7
    elif coherence >= 0.6:
        level = 6
    elif coherence >= 0.5:
        level = 5
    elif coherence >= 0.4:
        level = 4
    elif coherence >= 0.3:
        level = 3
    elif coherence >= 0.2:
        level = 2
    else:
        level = 1
    
    return {
        "level": level,
        "coherence": coherence,
        "type": thinking_type
    }

def determine_dilts_level(scores: Dict[str, int]) -> str:
    """Определяет уровень конфликта по модели Дилтса"""
    if not scores:
        return "def"
    
    # Находим уровень с максимальным баллом
    max_level = max(scores, key=scores.get)
    max_score = scores[max_level]
    
    # Преобразуем в коды
    level_map = {
        "ENVIRONMENT": "def",
        "BEHAVIOR": "sit",
        "CAPABILITIES": "con",
        "VALUES": "exp"
    }
    
    return level_map.get(max_level, "def")

def check_profile_coherence(profile_data: Dict[str, Any]) -> bool:
    """Проверяет согласованность профиля"""
    if not profile_data:
        return False
    
    # Проверяем наличие необходимых полей
    required = ["type_code", "level", "dilts_code"]
    for field in required:
        if field not in profile_data:
            return False
    
    # Проверяем допустимость значений
    valid_types = ["sp", "ia", "ip", "sa"]
    if profile_data["type_code"] not in valid_types:
        return False
    
    if not 1 <= profile_data["level"] <= 9:
        return False
    
    valid_dilts = ["def", "sit", "con", "exp", "int", "aut", "val", "tra", "ide"]
    if profile_data["dilts_code"] not in valid_dilts:
        return False
    
    return True

def get_profile_fallback(type_code: str, level: int, dilts_code: str) -> VariaticaProfile:
    """Получает профиль с запасными вариантами"""
    # Пробуем точное совпадение
    profile_key = f"{type_code}_{level}_{dilts_code}"
    profile = loader.get_profile(profile_key)
    if profile:
        return profile
    
    # Пробуем с суффиксом 'def'
    fallback_key = f"{type_code}_{level}_def"
    profile = loader.get_profile(fallback_key)
    if profile:
        return profile
    
    # Базовый профиль
    return loader.get_profile("sa_1_def")

def calculate_profile_final(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Финальный расчет профиля на основе всех ответов"""
    try:
        # Собираем все баллы
        stage1_scores = user_data.get("stage1_scores", {})
        stage2_scores = user_data.get("stage2_scores", {})
        stage3_scores = user_data.get("stage3_scores", {})
        stage4_scores = user_data.get("stage4_scores", {})
        
        # Определяем тип восприятия
        perception = determine_perception_type(stage1_scores)
        quadrant = perception["quadrant"]
        
        # Объединяем баллы этапов 2 и 3 для расчета уровня
        thinking_scores = stage2_scores.copy()
        for key, value in stage3_scores.items():
            thinking_scores[key] = thinking_scores.get(key, 0) + value
        
        # Расчет уровня мышления
        thinking_data = calculate_thinking_level_by_scores(thinking_scores)
        level = thinking_data["level"]
        
        # Определяем уровень Дилтса
        dilts_code = determine_dilts_level(stage4_scores)
        
        # Маппинг типов
        type_map = {
            "SP": {"code": "sp", "name": "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ"},
            "IA": {"code": "ia", "name": "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ"},
            "IP": {"code": "ip", "name": "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ"},
            "SA": {"code": "sa", "name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"}
        }
        
        type_info = type_map.get(quadrant, type_map["SA"])
        
        # Маппинг уровней
        level_names = {
            1: "БАЗОВЫЙ", 2: "АДАПТИВНЫЙ", 3: "СТАБИЛЬНЫЙ",
            4: "КРИЗИСНЫЙ", 5: "ТРАНСФОРМАЦИОННЫЙ", 6: "ИНТЕГРИРОВАННЫЙ",
            7: "ТВОРЧЕСКИЙ", 8: "МАСТЕРСКИЙ", 9: "ТРАНСЦЕНДЕНТНЫЙ"
        }
        
        # Маппинг Дилтса
        dilts_map = {
            "def": {"name": "ОПРЕДЕЛЕНИЕ", "full": "КРИЗИС ОПРЕДЕЛЕНИЯ"},
            "sit": {"name": "СИТУАЦИЯ", "full": "КРИЗИС СИТУАЦИИ"},
            "con": {"name": "КОНЦЕПЦИЯ", "full": "КРИЗИС КОНЦЕПЦИИ"},
            "exp": {"name": "ЭКСПЕРИМЕНТ", "full": "КРИЗИС ЭКСПЕРИМЕНТА"},
            "int": {"name": "ИНТЕГРАЦИЯ", "full": "КРИЗИС ИНТЕГРАЦИИ"},
            "aut": {"name": "АВТОНОМИЯ", "full": "КРИЗИС АВТОНОМИИ"},
            "val": {"name": "ЦЕННОСТИ", "full": "КРИЗИС ЦЕННОСТЕЙ"},
            "tra": {"name": "ТРАНСФОРМАЦИЯ", "full": "КРИЗИС ТРАНСФОРМАЦИИ"},
            "ide": {"name": "ИДЕНТИЧНОСТЬ", "full": "КРИЗИС ИДЕНТИЧНОСТИ"}
        }
        
        dilts_info = dilts_map.get(dilts_code, dilts_map["def"])
        
        profile_data = {
            "type_code": type_info["code"],
            "level": level,
            "dilts_code": dilts_code,
            "display_name": f"{type_info['code']}_{level}_{dilts_code}",
            "type_name": type_info["name"],
            "level_name": level_names.get(level, "БАЗОВЫЙ"),
            "dilts_name": dilts_info["full"],
            "short_dilts": dilts_info["name"],
            "perception": perception,
            "thinking": thinking_data
        }
        
        return profile_data
        
    except Exception as e:
        logger.error(f"Ошибка расчета профиля: {e}")
        # Возвращаем профиль по умолчанию
        return {
            "type_code": "sa",
            "level": 1,
            "dilts_code": "def",
            "display_name": "sa_1_def",
            "type_name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ",
            "level_name": "БАЗОВЫЙ",
            "dilts_name": "КРИЗИС ОПРЕДЕЛЕНИЯ",
            "short_dilts": "ОПРЕДЕЛЕНИЕ"
        }

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Создает строку прогресса"""
    percentage = int((current / total) * 100) if total > 0 else 0
    filled = int(percentage / 10)
    empty = 10 - filled
    return f"[{'█' * filled}{'░' * empty}] {percentage}%"

def clean_duplicate_headers(text: str) -> str:
    """Удаляет дублирующиеся заголовки"""
    lines = text.split('\n')
    seen = set()
    result = []
    
    for line in lines:
        stripped = line.strip()
        if stripped and not any(stripped.startswith(prefix) for prefix in ['#', '=', '-', '*'] * 3):
            result.append(line)
        elif stripped and stripped not in seen:
            seen.add(stripped)
            result.append(line)
    
    return '\n'.join(result)

def format_profile_title(profile_data: Dict[str, Any]) -> str:
    """Форматирует заголовок профиля"""
    return f"{profile_data['type_name']} - Уровень {profile_data['level']}"

def get_card_description_from_profile(profile: VariaticaProfile) -> str:
    """Получает описание из профиля"""
    description_parts = []
    
    if hasattr(profile, 'quote') and profile.quote:
        description_parts.append(f"«{profile.quote}»")
    
    if hasattr(profile, 'trigger') and profile.trigger:
        description_parts.append(f"\n🔴 *ТРИГГЕР:* {profile.trigger}")
    
    if hasattr(profile, 'pain') and profile.pain:
        description_parts.append(f"\n💔 *БОЛЬ:* {profile.pain}")
    
    if hasattr(profile, 'immediate_tool') and profile.immediate_tool:
        description_parts.append(f"\n🛠️ *ИНСТРУМЕНТ:* {profile.immediate_tool}")
    
    if hasattr(profile, 'cta') and profile.cta:
        description_parts.append(f"\n🎯 *ДЕЙСТВИЕ:* {profile.cta}")
    
    return "\n".join(description_parts)

# ============================================
# ПЛАТЕЖНЫЕ ФУНКЦИИ
# ============================================

def clear_telegram_conflicts():
    """Очищает конфликты в Telegram API"""
    try:
        logger.info("🔄 Проверяю конфликты в Telegram API...")
        
        # Удаляем webhook (если есть)
        delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.get(delete_url, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Webhook удален")
        else:
            logger.info(f"ℹ️ Webhook не найден или ошибка: {response.status_code}")
        
        # Очищаем очередь обновлений
        updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1"
        response = requests.get(updates_url, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Очередь обновлений очищена")
        
        return True
        
    except Exception as e:
        logger.error(f"⚠️ Ошибка при очистке конфликтов: {e}")
        return False

def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 690.0, 
                           email: str = None, is_test: bool = False, 
                           profile_data: Dict[str, Any] = None) -> dict:
    """Создает платеж через Invoices API с привязкой к профилю"""
    try:
        logger.info(f"📤 Создаю платеж: {payment_id}, сумма: {amount} руб")
        
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            return {
                "success": False,
                "error": "Ключи ЮKassa не настроены"
            }
        
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        # Уникальный Idempotence-Key для каждого запроса
        unique_id = uuid.uuid4().hex[:16]
        idempotence_key = f"{payment_id}_{unique_id}_{int(time.time())}"
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': idempotence_key
        }
        
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        description = f"Тестовый платеж 1 рубль #{payment_id}" if is_test else f"Курс ВАРИАТИКА #{payment_id}"
        item_description = "Тестовый доступ к курсу ВАРИАТИКА" if is_test else "Полный курс ВАРИАТИКА с персонализированными материалами"
        
        # Подготовка метаданных с профилем
        metadata = {
            "payment_id": payment_id,
            "user_id": user_id,
            "telegram_id": str(user_id),
            "is_test": str(is_test)
        }
        
        # Добавляем данные профиля, если они есть
        if profile_data:
            metadata["profile_type"] = profile_data.get("type_code", "")
            metadata["profile_level"] = str(profile_data.get("level", 1))
            metadata["profile_dilts"] = profile_data.get("dilts_code", "")
            metadata["profile_name"] = profile_data.get("display_name", "")
        
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
            "metadata": metadata,
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
        
        logger.info(f"📤 Отправляю в ЮKassa (Invoices API)...")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            yookassa_id = data.get('id')
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if not confirmation_url:
                return {
                    "success": False,
                    "error": "No confirmation URL in response"
                }
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": yookassa_id,
                "confirmation_url": confirmation_url,
                "status": data.get('status'),
                "amount": amount,
                "description": description,
                "invoice_type": "yookassa_invoice",
                "available_methods": "all",
                "profile_data": profile_data
            }
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            return {
                "success": False,
                "error": f"Ошибка {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def create_payment_in_db(user_id: int, amount: float = 690.0, 
                        is_test: bool = False, 
                        profile_data: Dict[str, Any] = None) -> dict:
    """Создает запись о платеже в БД с привязкой к профилю"""
    try:
        timestamp = int(time.time())
        if is_test:
            payment_id = f"test_{user_id}_{timestamp}"
            description = f"Тестовый платеж {amount} руб"
        else:
            payment_id = f"prod_{user_id}_{timestamp}"
            description = "Полный курс ВАРИАТИКА - 690 руб"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": description
        }
        
        # Добавляем данные профиля, если они есть
        if profile_data:
            payload["profile_data"] = profile_data
        
        logger.info(f"📦 Создаю платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Платеж создан в БД: {payment_id}")
            
            response_data = response.json()
            
            return {
                "success": True,
                "payment_id": payment_id,
                "email": f"user_{user_id}@telegram.org",
                "amount": amount,
                "description": description,
                "profile_data": profile_data,
                "yookassa_id": response_data.get('yookassa_id'),
                "confirmation_url": response_data.get('confirmation_url'),
                "invoice_type": response_data.get('invoice_type', 'yookassa_invoice'),
                "available_methods": response_data.get('available_methods', 'all')
            }
        else:
            error_text = response.text[:200]
            logger.error(f"❌ Ошибка БД {response.status_code}: {error_text}")
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'payment' in data:
                status = data['payment'].get('status', 'unknown')
                amount = data['payment'].get('amount', 0)
                user_id = data['payment'].get('user_id')
                profile_data = data['payment'].get('profile_data', {})
            else:
                status = data.get('status', 'unknown')
                amount = 0
                user_id = None
                profile_data = {}
                
            return {
                "success": True,
                "status": status,
                "amount": amount,
                "user_id": user_id,
                "profile_data": profile_data,
                "data": data
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": "Платеж не найден"
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка: {response.status_code}",
                "details": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_user_access(user_id: int) -> dict:
    """Проверяет доступ пользователя"""
    try:
        response = requests.get(
            f"{API_URL}/api/check-access/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_materials_link(user_id: int, payment_id: str, 
                       token: str = None, 
                       profile_data: Dict[str, Any] = None) -> dict:
    """Получает ссылку на материалы с учетом профиля"""
    try:
        url = f"{API_URL}/api/get-materials/{payment_id}"
        params = {"user_id": user_id}
        
        if token:
            params["token"] = token
            
        # Добавляем данные профиля
        if profile_data:
            params["profile_type"] = profile_data.get("type_code", "")
            params["profile_level"] = str(profile_data.get("level", 1))
            params["profile_dilts"] = profile_data.get("dilts_code", "")
            
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_personalized_materials(profile_data: Dict[str, Any]) -> str:
    """Возвращает персонализированные материалы для профиля"""
    try:
        profile_key = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
        profile = loader.get_profile(profile_key)
        
        if not profile:
            # Используем fallback
            profile = get_profile_fallback(
                profile_data["type_code"],
                profile_data["level"],
                profile_data["dilts_code"]
            )
        
        if profile:
            # Возвращаем ссылку на конкретный файл профиля или общую папку
            # В реальной реализации здесь должна быть логика получения ссылок
            # из профиля или внешнего API
            materials = [
                f"📚 *Материалы для вашего профиля:*",
                f"🏷️ Тип: {profile_data['type_name']}",
                f"📊 Уровень: {profile_data['level']} ({profile_data['level_name']})",
                f"🎯 Точка роста: {profile_data['dilts_name']}",
                f"",
                f"📖 *Доступные материалы:*",
                f"• Подробный разбор вашего профиля",
                f"• Инструменты для развития",
                f"• Практические упражнения",
                f"• Рекомендации по применению"
            ]
            
            return "\n".join(materials)
        else:
            return "📚 *Общие материалы курса ВАРИАТИКА*"
            
    except Exception as e:
        logger.error(f"Ошибка получения материалов: {e}")
        return "📚 *Материалы курса ВАРИАТИКА*"

# ============================================
# ОБРАБОТЧИКИ ТЕСТА
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🚀 НАЧАТЬ ТЕСТ", callback_data="start_test")],
        [InlineKeyboardButton("💎 КУПИТЬ ПАКЕТ", callback_data="buy_variatica")],
        [InlineKeyboardButton("📁 МОИ МАТЕРИАЛЫ", callback_data="my_materials")]
    ]
    
    message_text = (
        f"👋 *Привет, {user.first_name}!*\n\n"
        f"Добро пожаловать в ВАРИАТИКА — психодиагностическую систему нового поколения.\n\n"
        f"✨ *Что вы можете сделать:*\n"
        f"• 🚀 Пройти тест из 32 вопросов\n"
        f"• 💎 Получить персонализированные материалы\n"
        f"• 📁 Доступ к архиву профилей\n\n"
        f"🎯 *Тест определит:*\n"
        f"• Ваш тип восприятия\n"
        f"• Конфигурацию мышления\n"
        f"• Поведенческие паттерны\n"
        f"• Точки роста по Дилтсу\n\n"
        f"Выберите действие:"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def start_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает тест"""
    query = update.callback_query
    await query.answer()
    
    # Инициализация данных пользователя
    context.user_data.clear()
    context.user_data["stage"] = 1
    context.user_data["question_index"] = 0
    context.user_data["stage1_scores"] = defaultdict(int)
    context.user_data["stage2_scores"] = defaultdict(int)
    context.user_data["stage3_scores"] = defaultdict(int)
    context.user_data["stage4_scores"] = defaultdict(int)
    context.user_data["answers"] = {}
    
    # Отправляем первый вопрос
    await send_question(update, context)
    return STAGE_1

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет текущий вопрос"""
    stage = context.user_data["stage"]
    question_index = context.user_data["question_index"]
    
    if stage == 1:
        questions = STAGE_1_QUESTIONS
    elif stage == 2:
        quadrant = context.user_data.get("quadrant", "SA")
        questions = STAGE_2_QUESTIONS.get(quadrant, STAGE_2_QUESTIONS["SA"])
    elif stage == 3:
        questions = STAGE_3_QUESTIONS
    elif stage == 4:
        questions = STAGE_4_QUESTIONS
    else:
        questions = []
    
    if question_index >= len(questions):
        await handle_stage_completion(update, context)
        return
    
    question = questions[question_index]
    
    # Создаем клавиатуру с вариантами ответов
    keyboard = []
    for key, option in question["options"].items():
        keyboard.append([InlineKeyboardButton(option["text"], callback_data=f"answer_{key}")])
    
    # Добавляем прогресс
    progress = calculate_progress(question_index + 1, len(questions))
    stage_text = f"Этап {stage}/4: "
    if stage == 1:
        stage_text += "Конфигурация восприятия"
    elif stage == 2:
        stage_text += "Конфигурация мышления"
    elif stage == 3:
        stage_text += "Поведенческие паттерны"
    elif stage == 4:
        stage_text += "Конфликт логических уровней"
    
    message = f"*{stage_text}*\n\n{question['text']}\n\n{progress}"
    
    if query := update.callback_query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на вопрос"""
    query = update.callback_query
    await query.answer()
    
    answer_key = query.data.split("_")[1]
    stage = context.user_data["stage"]
    question_index = context.user_data["question_index"]
    
    # Получаем текущий вопрос
    if stage == 1:
        questions = STAGE_1_QUESTIONS
    elif stage == 2:
        quadrant = context.user_data.get("quadrant", "SA")
        questions = STAGE_2_QUESTIONS.get(quadrant, STAGE_2_QUESTIONS["SA"])
    elif stage == 3:
        questions = STAGE_3_QUESTIONS
    elif stage == 4:
        questions = STAGE_4_QUESTIONS
    else:
        questions = []
    
    question = questions[question_index]
    answer_data = question["options"][answer_key]
    
    # Сохраняем ответ
    context.user_data["answers"][question["id"]] = answer_key
    
    # Добавляем баллы
    scores_dict = f"stage{stage}_scores"
    if scores_dict in context.user_data:
        for score_type, value in answer_data.get("scores", {}).items():
            context.user_data[scores_dict][score_type] += value
    
    # Переходим к следующему вопросу
    context.user_data["question_index"] += 1
    
    # Если это этап 1 и мы закончили его, определяем квадрант для этапа 2
    if stage == 1 and context.user_data["question_index"] >= len(questions):
        perception = determine_perception_type(context.user_data["stage1_scores"])
        context.user_data["quadrant"] = perception["quadrant"]
        logger.info(f"Определен квадрант: {perception['quadrant']}")
    
    await send_question(update, context)

async def handle_stage_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает завершение этапа"""
    stage = context.user_data["stage"]
    
    if stage < 4:
        # Переходим к следующему этапу
        context.user_data["stage"] += 1
        context.user_data["question_index"] = 0
        await send_question(update, context)
        return stage + 1  # Возвращаем следующее состояние
    else:
        # Все этапы завершены, показываем результаты
        await show_results(update, context)
        return RESULTS

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает результаты теста"""
    query = update.callback_query
    
    # Рассчитываем профиль
    profile_data = calculate_profile_final(context.user_data)
    
    # Сохраняем данные профиля в user_data
    context.user_data["profile_data"] = profile_data
    
    # Получаем объект профиля
    profile_key = profile_data["display_name"]
    profile = loader.get_profile(profile_key)
    
    if not profile:
        # Используем fallback
        profile = get_profile_fallback(
            profile_data["type_code"],
            profile_data["level"],
            profile_data["dilts_code"]
        )
    
    # Формируем сообщение с результатами
    result_text = f"🎉 *ТЕСТ ЗАВЕРШЁН!*\n\n"
    result_text += f"🏷️ *ВАШ ПРОФИЛЬ:*\n"
    result_text += f"```\n{format_profile_title(profile_data)}\n```\n\n"
    
    if profile:
        result_text += f"*{profile.archetype if hasattr(profile, 'archetype') else 'Архетип'}*\n\n"
        
        if hasattr(profile, 'quote') and profile.quote:
            result_text += f"«{profile.quote}»\n\n"
        
        # Добавляем описание из профиля
        description = get_card_description_from_profile(profile)
        if description:
            result_text += description + "\n\n"
    
    result_text += f"📊 *Характеристики:*\n"
    result_text += f"• Тип: {profile_data['type_name']}\n"
    result_text += f"• Уровень: {profile_data['level']} ({profile_data['level_name']})\n"
    result_text += f"• Точка роста: {profile_data['dilts_name']}\n\n"
    
    result_text += f"🎁 *Что дальше?*\n"
    result_text += f"Вы можете получить полный разбор вашего профиля с персонализированными материалами."
    
    keyboard = [
        [InlineKeyboardButton("💎 ПОЛУЧИТЬ ПОЛНЫЙ ПАКЕТ (690 руб)", callback_data="buy_variatica")],
        [InlineKeyboardButton("📁 ПОЛУЧИТЬ БЕСПЛАТНЫЙ ПОДАРОК", callback_data="get_gift")],
        [InlineKeyboardButton("🔄 ПРОЙТИ ТЕСТ ЗАНОВО", callback_data="start_test")]
    ]
    
    if query:
        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

# ============================================
# ПЛАТЕЖНЫЕ ОБРАБОТЧИКИ
# ============================================

async def buy_variatica_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки полного пакета"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Получаем данные профиля из user_data (если пользователь прошел тест)
    profile_data = context.user_data.get("profile_data", {})
    
    # Если профиля нет, создаем базовый
    if not profile_data or not check_profile_coherence(profile_data):
        profile_data = {
            "type_code": "sa",
            "level": 1,
            "dilts_code": "def",
            "display_name": "sa_1_def",
            "type_name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ",
            "level_name": "БАЗОВЫЙ",
            "dilts_name": "КРИЗИС ОПРЕДЕЛЕНИЯ"
        }
    
    await query.edit_message_text("📦 *Создаю заказ на полный курс ВАРИАТИКА...*", parse_mode='Markdown')
    
    # Создаем платеж в БД с привязкой к профилю
    db_result = create_payment_in_db(
        user_id=user_id,
        amount=690.0,
        is_test=False,
        profile_data=profile_data
    )
    
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка базы данных:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    # Если в ответе есть confirmation_url из API - используем его
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
        payment_result = db_result
    else:
        # Иначе создаем платеж через ЮKassa API
        await query.edit_message_text("💳 *Создаю платеж через Invoices API...*", parse_mode='Markdown')
        
        payment_result = create_yookassa_payment(
            payment_id=payment_id,
            user_id=user_id,
            amount=690.0,
            email=db_result.get("email"),
            is_test=False,
            profile_data=profile_data
        )
        
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка Invoices API:*\n`{error_msg}`", parse_mode='Markdown')
            return
        
        confirmation_url = payment_result["confirmation_url"]
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    # Информация о персонализации
    personalization_info = ""
    if profile_data.get("display_name") != "sa_1_def":
        personalization_info = f"\n🎯 *ПЕРСОНАЛИЗАЦИЯ:* Материалы будут адаптированы под ваш профиль: {profile_data['display_name']}"
    
    message_text = (
        f"✅ *ЗАКАЗ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 руб\n"
        f"📚 *Продукт:* Полный курс ВАРИАТИКА\n"
        f"💡 *Invoices API:* ВСЕ способы оплаты доступны{personalization_info}\n"
        f"🔒 *Защита от дублей:* ✅ активна\n\n"
        f"*Что вы получите после оплаты:*\n"
        f"✅ Персонализированные материалы под ваш профиль\n"
        f"✅ Полный доступ ко всем материалам курса\n"
        f"✅ Мгновенное уведомление в Telegram\n"
        f"✅ Техническую поддержку\n\n"
        f"*Для оплаты нажмите кнопку ниже:*"
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def test_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик тестового платежа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    await query.edit_message_text("📦 *Создаю тестовый платеж 1 рубль...*", parse_mode='Markdown')
    
    db_result = create_payment_in_db(user_id, amount=1.0, is_test=True)
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка базы данных:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    # Если в ответе есть confirmation_url из API - используем его
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
        payment_result = db_result
    else:
        await query.edit_message_text("💳 *Создаю платеж через Invoices API...*", parse_mode='Markdown')
        
        payment_result = create_yookassa_payment(payment_id, user_id, amount=1.0, email=db_result.get("email"), is_test=True)
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка Invoices API:*\n`{error_msg}`", parse_mode='Markdown')
            return
        
        confirmation_url = payment_result["confirmation_url"]
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    message_text = (
        f"✅ *ТЕСТОВЫЙ ПЛАТЕЖ 1 РУБЛЬ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID:* `{payment_id}`\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"💡 *Invoices API:* ВСЕ способы оплаты доступны\n"
        f"🔒 *Защита от дублей:* ✅ активна\n\n"
        f"*Для оплаты нажмите кнопку ниже:*"
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        amount = result.get("amount", 0)
        profile_data = result.get("profile_data", {})
        
        if status == "succeeded":
            is_test = amount == 1.0
            
            if is_test:
                message = (
                    f"🎉 *ТЕСТОВЫЙ ПЛАТЕЖ 1 РУБЛЬ ОПЛАЧЕН!*\n\n"
                    f"✅ Платеж `{payment_id}` успешно завершен!\n"
                    f"💰 Сумма: {amount} руб\n\n"
                    f"*🔓 СИСТЕМА РАБОТАЕТ КОРРЕКТНО!*\n"
                    f"Вы получите тестовые материалы."
                )
            else:
                message = (
                    f"🎉 *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
                    f"✅ Ваш заказ `{payment_id}` успешно оплачен!\n"
                    f"💰 Сумма: {amount} руб\n\n"
                    f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                    f"Вы получили доступ ко всем материалам курса ВАРИАТИКА!\n"
                )
                
                # Добавляем информацию о персонализации, если есть
                if profile_data:
                    message += f"\n🎯 *Материалы персонализированы под ваш профиль:* {profile_data.get('display_name', '')}"
                
                message += f"\n\n📁 Для получения материалов нажмите:\n`/materials`"
                
                user_id = result.get("user_id", query.from_user.id)
                access_data = get_user_access(user_id)
                if access_data.get('has_access', False):
                    accesses = access_data.get('accesses', [])
                    for access in accesses:
                        if access.get('payment_id') == payment_id and access.get('access_token'):
                            keyboard = [[InlineKeyboardButton("📁 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data=f"get_materials_{payment_id}")]]
                            await query.edit_message_text(
                                message,
                                reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode='Markdown'
                            )
                            return
            
        elif status in ["pending", "waiting"]:
            message = (
                f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
                f"Заказ `{payment_id}` еще не оплачен.\n"
                f"💰 Сумма: {amount} руб\n\n"
                f"*Для оплаты используйте кнопку ниже:*"
            )
            keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", callback_data=f"retry_{payment_id}")]]
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            message = f"📊 *Статус заказа:* `{status}`\n💰 *Сумма:* {amount} руб"
        
        await query.edit_message_text(message, parse_mode='Markdown')

async def get_materials_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_materials_"):
        payment_id = query.data[14:]
        user_id = query.from_user.id
        
        access_data = get_user_access(user_id)
        
        if not access_data.get('success', False):
            await query.edit_message_text(
                "❌ *Ошибка проверки доступа*",
                parse_mode='Markdown'
            )
            return
        
        access_token = None
        for access in access_data.get('accesses', []):
            if access.get('payment_id') == payment_id and access.get('has_access', False):
                access_token = access.get('access_token')
                profile_data = access.get('profile_data', {})
                break
        
        if not access_token:
            await query.edit_message_text(
                f"❌ *Доступ не найден*\n\n"
                f"Платеж `{payment_id}` не найден или доступ не активен.",
                parse_mode='Markdown'
            )
            return
        
        await query.edit_message_text("📁 *Получаю ссылку на материалы...*", parse_mode='Markdown')
        
        materials_data = get_materials_link(user_id, payment_id, access_token, profile_data)
        
        if materials_data.get('success', False):
            materials_link = materials_data.get('materials_link')
            
            keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
            
            message = f"✅ *МАТЕРИАЛЫ ГОТОВЫ!*\n\n📋 *ID заказа:* `{payment_id[:8]}`\n\n"
            
            # Добавляем информацию о персонализации
            if profile_data:
                message += f"🎯 *Персонализировано под профиль:* {profile_data.get('display_name', '')}\n\n"
            
            message += "🔗 *Ссылка на Яндекс.Диск:*\nНажмите кнопку ниже для скачивания материалов:"
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
        else:
            error = materials_data.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(
                f"❌ *Ошибка получения материалов*\n\n`{error}`",
                parse_mode='Markdown'
            )

async def my_materials_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мои материалы через callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        await query.edit_message_text(
            "❌ *Ошибка проверки доступа*\n\nПожалуйста, попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    if not access_data.get('has_access', False):
        keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_variatica")]]
        
        await query.edit_message_text(
            f"📭 *У вас нет доступа к материалам*\n\n"
            f"👤 *{user_name}*, для получения доступа необходимо приобрести курс.\n\n"
            f"💎 *Полный курс ВАРИАТИКА:*\n"
            f"• Стоимость: 690 руб\n"
            f"• Персонализированные материалы\n"
            f"• Мгновенный доступ после оплаты\n"
            f"• Все материалы курса\n\n"
            f"Нажмите кнопку ниже для покупки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    accesses = access_data.get('accesses', [])
    
    if not accesses:
        await query.edit_message_text(
            "❌ *Доступ не найден*\n\nОбратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    for access in accesses:
        if access.get('has_access', False) and access.get('is_active', False):
            payment_id = access.get('payment_id')
            access_token = access.get('access_token')
            profile_data = access.get('profile_data', {})
            
            materials_data = get_materials_link(user_id, payment_id, access_token, profile_data)
            
            if materials_data.get('success', False):
                materials_link = materials_data.get('materials_link')
                
                keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                
                message = (
                    f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                    f"👤 *{user_name}*, вот ваши материалы курса ВАРИАТИКА:\n\n"
                    f"📋 *ID заказа:* `{payment_id[:8]}`\n"
                    f"💰 *Сумма:* {access.get('amount', 0)} руб\n"
                    f"📅 *Доступ открыт:* {access.get('granted_at', '')[:10]}\n"
                )
                
                # Добавляем информацию о персонализации
                if profile_data:
                    message += f"🎯 *Профиль:* {profile_data.get('display_name', '')}\n\n"
                else:
                    message += "\n"
                
                message += "🔗 *Ссылка на Яндекс.Диск:*\nНажмите кнопку ниже для скачивания:"
                
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
                return
            else:
                error = materials_data.get('error', 'Неизвестная ошибка')
                await query.edit_message_text(
                    f"❌ *Ошибка получения материалов*\n\n`{error}`",
                    parse_mode='Markdown'
                )
                return
    
    keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_variatica")]]
    
    await query.edit_message_text(
        f"📭 *Доступ не активен*\n\n"
        f"👤 *{user_name}*, ваш доступ истек или не активен.\n\n"
        f"Для получения доступа приобретите курс:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /materials"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n\nПожалуйста, попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    if not access_data.get('has_access', False):
        keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_variatica")]]
        
        await update.message.reply_text(
            f"📭 *У вас нет доступа к материалам*\n\n"
            f"👤 *{user_name}*, для получения доступа необходимо приобрести курс.\n\n"
            f"💎 *Полный курс ВАРИАТИКА:*\n"
            f"• Стоимость: 690 руб\n"
            f"• Персонализированные материалы\n"
            f"• Мгновенный доступ после оплаты\n\n"
            f"Нажмите кнопку ниже для покупки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    accesses = access_data.get('accesses', [])
    
    if not accesses:
        await update.message.reply_text(
            "❌ *Доступ не найден*\n\nОбратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    for access in accesses:
        if access.get('has_access', False) and access.get('is_active', False):
            payment_id = access.get('payment_id')
            access_token = access.get('access_token')
            profile_data = access.get('profile_data', {})
            
            materials_data = get_materials_link(user_id, payment_id, access_token, profile_data)
            
            if materials_data.get('success', False):
                materials_link = materials_data.get('materials_link')
                
                keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                
                message = (
                    f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                    f"👤 *{user_name}*, вот ваши материалы курса ВАРИАТИКА:\n\n"
                    f"📋 *ID заказа:* `{payment_id[:8]}`\n"
                    f"💰 *Сумма:* {access.get('amount', 0)} руб\n"
                )
                
                if profile_data:
                    message += f"🎯 *Профиль:* {profile_data.get('display_name', '')}\n\n"
                
                message += "🔗 *Ссылка на Яндекс.Диск:*\nНажмите кнопку ниже для скачивания:"
                
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
                return
            else:
                error = materials_data.get('error', 'Неизвестная ошибка')
                await update.message.reply_text(
                    f"❌ *Ошибка получения материалов*\n\n`{error}`",
                    parse_mode='Markdown'
                )
                return
    
    keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_variatica")]]
    
    await update.message.reply_text(
        f"📭 *Доступ не активен*\n\n"
        f"👤 *{user_name}*, ваш доступ истек или не активен.\n\n"
        f"Для получения доступа приобретите курс:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def myaccess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /myaccess"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n\nПожалуйста, попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    has_access = access_data.get('has_access', False)
    accesses = access_data.get('accesses', [])
    
    if not accesses:
        message = (
            f"📭 *НЕТ АКТИВНЫХ ДОСТУПОВ*\n\n"
            f"👤 *{user_name}*, у вас нет активных подписок.\n\n"
            f"💎 *Доступные варианты:*\n"
            f"• Полный курс ВАРИАТИКА - 690 руб\n"
            f"• Персонализированные материалы\n"
            f"• Мгновенный доступ после оплаты\n\n"
            f"Используйте команду /start для покупки"
        )
    else:
        active_count = sum(1 for a in accesses if a.get('has_access', False) and a.get('is_active', False))
        total_count = len(accesses)
        
        message = (
            f"📊 *ВАШИ ДОСТУПЫ*\n\n"
            f"👤 *Пользователь:* {user_name}\n"
            f"🔓 *Активных доступов:* {active_count}/{total_count}\n\n"
        )
        
        for i, access in enumerate(accesses[:5], 1):
            status = "✅ АКТИВЕН" if access.get('has_access', False) and access.get('is_active', False) else "❌ НЕ АКТИВЕН"
            expires = access.get('expires_at', '')[:10] if access.get('expires_at') else "не указан"
            profile_info = access.get('profile_data', {})
            
            message += (
                f"{i}. *{access.get('description', 'Доступ')}*\n"
                f"   💰 Сумма: {access.get('amount', 0)} руб\n"
                f"   📋 ID: `{access.get('payment_id', '')[:8]}`\n"
            )
            
            if profile_info:
                message += f"   🎯 Профиль: {profile_info.get('display_name', '')}\n"
            
            message += (
                f"   📅 Доступ: {access.get('granted_at', '')[:10]}\n"
                f"   ⏳ Истекает: {expires}\n"
                f"   🔐 Статус: {status}\n\n"
            )
        
        if active_count > 0:
            message += "📁 Для получения материалов используйте /materials"
        else:
            message += "💎 Для покупки доступа используйте /start"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /check"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Проверка статуса платежа*\n\n"
            "Использование: `/check ID_платежа`\n\n"
            "Пример:\n"
            "`/check prod_532205848_1234567890`\n\n"
            "Или используйте меню теста /start",
            parse_mode='Markdown'
        )
        return
    
    payment_id = context.args[0]
    result = check_payment_status_db(payment_id)
    
    if result["success"]:
        status = result.get("status", "unknown")
        amount = result.get("amount", 0)
        profile_data = result.get("profile_data", {})
        
        status_emoji = {
            "succeeded": "✅",
            "pending": "⏳",
            "waiting": "⏳",
            "canceled": "❌",
            "failed": "❌"
        }.get(status, "📊")
        
        status_text = {
            "succeeded": "ОПЛАЧЕНО",
            "pending": "ОЖИДАЕТ ОПЛАТЫ",
            "waiting": "ОЖИДАЕТ ПОДТВЕРЖДЕНИЯ",
            "canceled": "ОТМЕНЕН",
            "failed": "ОШИБКА"
        }.get(status, status.upper())
        
        message = (
            f"{status_emoji} *СТАТУС ПЛАТЕЖА*\n\n"
            f"📋 *ID:* `{payment_id}`\n"
            f"💰 *Сумма:* {amount} руб\n"
            f"📊 *Статус:* {status_text}\n"
        )
        
        if profile_data:
            message += f"🎯 *Профиль:* {profile_data.get('display_name', '')}\n"
        
        if status == "succeeded":
            message += "\n🎉 *Платеж успешно завершен!*\n\n"
            message += "📁 Для получения материалов используйте команду:\n`/materials`\n\n"
            message += "✅ Вы получите мгновенное уведомление с доступом."
        elif status in ["pending", "waiting"]:
            keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", callback_data=f"retry_{payment_id}")]]
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await update.message.reply_text(
            f"❌ *Не удалось проверить платеж* `{payment_id}`:\n\n`{error_msg}`",
            parse_mode='Markdown'
        )

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    fake_update = Update(update.update_id + 1, message=query.message)
    await start_command(fake_update, context)

async def retry_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Повтор платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("retry_"):
        payment_id = query.data[6:]
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text(
                f"❌ *Не удалось найти платеж* `{payment_id}`",
                parse_mode='Markdown'
            )
            return
        
        amount = result.get("amount", 690.0)
        user_id = result.get("user_id", query.from_user.id)
        profile_data = result.get("profile_data", {})
        
        is_test = amount == 1.0
        
        # Создаем новый payment_id для ретрая
        new_payment_id = f"retry_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Создаем новый платеж
        payment_result = create_yookassa_payment(
            payment_id=new_payment_id,
            user_id=user_id,
            amount=amount,
            email=f"user_{user_id}@telegram.org",
            is_test=is_test,
            profile_data=profile_data
        )
        
        if payment_result.get("success", False):
            keyboard = [[InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=payment_result["confirmation_url"])]]
            
            amount_text = "1 рубль" if is_test else "690 руб"
            
            await query.edit_message_text(
                f"🔗 *НОВАЯ ССЫЛКА ДЛЯ ОПЛАТЫ*\n\n"
                f"📋 *ID:* `{new_payment_id}`\n"
                f"💰 *Сумма:* {amount_text}\n"
                f"🔒 *Защита от дублей:* ✅ активна\n\n"
                f"Нажмите кнопку ниже для оплаты:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
        else:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(
                f"❌ *Не удалось создать ссылку оплаты*\n\n`{error_msg}`",
                parse_mode='Markdown'
            )

async def get_gift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение бесплатного подарка"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ ПОДАРОК", url=GIFT_PDF_LINK)]]
    
    await query.edit_message_text(
        f"🎁 *БЕСПЛАТНЫЙ ПОДАРОК!*\n\n"
        f"В качестве благодарности за прохождение теста мы дарим вам:\n\n"
        f"📚 *«Введение в ВАРИАТИКУ»*\n"
        f"• Основные принципы системы\n"
        f"• Краткое описание типов\n"
        f"• Практические упражнения\n\n"
        f"Нажмите кнопку ниже для скачивания:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "Тест отменен. Используйте /start для начала нового теста."
    )
    return ConversationHandler.END

# ============================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Основная функция запуска бота"""
    print("=" * 80)
    print("🚀 VARIATICA UNIFIED BOT - ТЕСТ + ПЛАТЕЖНАЯ СИСТЕМА")
    print("=" * 80)
    
    # Очищаем конфликты
    clear_telegram_conflicts()
    
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Создаем ConversationHandler для теста
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(start_test_callback, pattern="^start_test$")],
            states={
                STAGE_1: [
                    CallbackQueryHandler(handle_answer, pattern="^answer_[abcd]$")
                ],
                STAGE_2: [
                    CallbackQueryHandler(handle_answer, pattern="^answer_[abcd]$")
                ],
                STAGE_3: [
                    CallbackQueryHandler(handle_answer, pattern="^answer_[abcd]$")
                ],
                STAGE_4: [
                    CallbackQueryHandler(handle_answer, pattern="^answer_[abcd]$")
                ],
                RESULTS: [
                    CallbackQueryHandler(buy_variatica_callback, pattern="^buy_variatica$"),
                    CallbackQueryHandler(get_gift_callback, pattern="^get_gift$"),
                    CallbackQueryHandler(start_test_callback, pattern="^start_test$")
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            allow_reentry=True
        )
        
        # Регистрация обработчиков команд
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("materials", materials_command))
        app.add_handler(CommandHandler("myaccess", myaccess_command))
        app.add_handler(CommandHandler("check", check_command))
        
        # Регистрация обработчиков callback
        app.add_handler(CallbackQueryHandler(buy_variatica_callback, pattern="^buy_variatica$"))
        app.add_handler(CallbackQueryHandler(test_buy_callback, pattern="^test_buy$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(get_materials_callback, pattern="^get_materials_"))
        app.add_handler(CallbackQueryHandler(my_materials_callback, pattern="^my_materials$"))
        app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
        app.add_handler(CallbackQueryHandler(retry_payment_callback, pattern="^retry_"))
        app.add_handler(CallbackQueryHandler(get_gift_callback, pattern="^get_gift$"))
        
        # Регистрация ConversationHandler
        app.add_handler(conv_handler)
        
        print("✅ Бот запущен успешно!")
        print(f"🤖 Токен: {TOKEN[:15]}...")
        print(f"🌐 API: {API_URL}")
        print(f"💳 ЮKassa: {'✅' if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY else '❌'}")
        print(f"📊 Профили: {len(loader.get_all_profiles())} загружено")
        print("=" * 80)
        print("🎯 Ключевые функции:")
        print("  • Полный тест из 32 вопросов")
        print("  • 4 этапа психодиагностики")
        print("  • Расчет профиля с fallback")
        print("  • Платежи через Invoices API")
        print("  • Персонализация материалов по профилю")
        print("=" * 80)
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка запуска: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
