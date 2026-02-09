"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа + адаптивные уточнения + СИСТЕМА БАЛЛОВ как в карточном тесте
ВЕРСИЯ 1.9: Исправлен fallback для всех типов профилей
"""

import logging
import os
import asyncio
import urllib.parse
import math
import re
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

# Состояния ConversationHandler
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION = range(10)

# Константы
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую.."
PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"

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
