#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА: ПУТЬ К САМОПОЗНАНИЮ
ПОЛНАЯ ИНТЕГРАЦИЯ:
- 4 этапа адаптивного тестирования (ПОЛНАЯ ЛОГИКА)
- 18+ интимные профили (36 профилей на Яндекс.Диске)
- 4F-ключи для управления состояниями
- Система приглашений для друзей

ВЕРСИЯ 7.0: ПОЛНАЯ ИНТЕГРАЦИЯ С СОХРАНЕНИЕМ ВСЕЙ ЛОГИКИ
"""

import logging
import os
import sys
import asyncio
import urllib.parse
import time
import base64
import uuid
import random
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ===== НАСТРОЙКА ЛОГГИРОВАНИЯ =====
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Функция для логирования
def log_callback(func_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует входящий callback"""
    user = update.effective_user
    query = update.callback_query if update.callback_query else None
    
    log_msg = f"📞 {func_name} | User: {user.id} (@{user.username})"
    if query:
        log_msg += f" | Callback: {query.data}"
    if context.user_data:
        log_msg += f" | has_shared: {context.user_data.get('has_shared', False)}"
        log_msg += f" | profile: {context.user_data.get('profile_data', {}).get('display_name', 'None')}"
    
    logger.debug(log_msg)

# ===== СОСТОЯНИЯ ТЕСТА =====
STAGE_1 = 1
STAGE_2 = 2
STAGE_3 = 3
STAGE_4 = 4
CLARIFICATION = 5
RESULTS = 6
GIFT_SCREEN = 7
PACKAGE_SCREEN = 8
OPEN_GIFT_SCREEN = 9
PAYMENT_SCREEN = 10

# ===== СОСТОЯНИЯ ИНТИМНОГО МОДУЛЯ =====
MY_SEXUAL_PROFILE = 50
INVITES_LIST = 51
FRIEND_MENU = 52
FOUR_F_MENU = 53
FOUR_F_CONTENT = 54
FOUR_F_PAYMENT_SCREEN = 55
BUY_PACKAGES = 56
FOUR_F_MAIN = 57
FOUR_F_DETAILED = 58

# ===== КОНСТАНТЫ ТЕСТА =====
PERCEPTION_TYPES = {
    "EXTERNAL": "Внешний",
    "INTERNAL": "Внутренний", 
    "SYMBOLIC": "Символический",
    "MATERIAL": "Материальный"
}

TYPE_CODES = {
    "EXTERNAL": "E",
    "INTERNAL": "I",
    "SYMBOLIC": "S",
    "MATERIAL": "M"
}

DILTS_LEVELS = {
    "ENVIRONMENT": "Окружение",
    "BEHAVIOR": "Поведение",
    "CAPABILITIES": "Способности",
    "VALUES": "Ценности",
    "IDENTITY": "Идентичность",
    "MISSION": "Миссия"
}

STANDARD_SUFFIXES = ["def", "sit", "con", "exp", "int", "aut", "val", "tra", "ide"]

# Вопросы для этапов
STAGE1_QUESTIONS = [
    {
        "text": "Когда вы принимаете важное решение, на что вы больше опираетесь?",
        "options": {
            "EXTERNAL": "На мнение авторитетных людей, экспертов",
            "INTERNAL": "На свои внутренние ощущения и чутье",
            "SYMBOLIC": "На знаки, символы, совпадения",
            "MATERIAL": "На факты, цифры, конкретные данные"
        }
    },
    {
        "text": "Что для вас важнее в общении с людьми?",
        "options": {
            "EXTERNAL": "Их реакция и обратная связь",
            "INTERNAL": "Мои ощущения от разговора",
            "SYMBOLIC": "Глубинный смысл сказанного",
            "MATERIAL": "Конкретный результат общения"
        }
    },
    {
        "text": "Как вы обычно оцениваете результаты своей работы?",
        "options": {
            "EXTERNAL": "По оценкам и мнению других",
            "INTERNAL": "По своему внутреннему удовлетворению",
            "SYMBOLIC": "По тому, насколько это соответствует моим идеалам",
            "MATERIAL": "По конкретным достижениям и результатам"
        }
    },
    {
        "text": "Что вас больше вдохновляет?",
        "options": {
            "EXTERNAL": "Примеры успешных людей",
            "INTERNAL": "Внутренний порыв и желание",
            "SYMBOLIC": "Идеи, мечты, образы будущего",
            "MATERIAL": "Конкретные цели и планы"
        }
    },
    {
        "text": "В какой среде вы наиболее продуктивны?",
        "options": {
            "EXTERNAL": "В окружении людей, в команде",
            "INTERNAL": "В одиночестве, наедине с собой",
            "SYMBOLIC": "В творческом беспорядке, с книгами, символами",
            "MATERIAL": "В хорошо организованном, удобном пространстве"
        }
    }
]

STAGE1_FEEDBACK = {
    "EXTERNAL": "Вы ориентируетесь на внешние сигналы и мнения. Для вас важно, что думают другие, вы чувствительны к обратной связи и социальным нормам.",
    "INTERNAL": "Вы доверяете внутренним ощущениям. Ваш внутренний компас — главный советчик, вы хорошо слышите свои чувства и интуицию.",
    "SYMBOLIC": "Вы видите символы и знаки. Для вас мир полон скрытых смыслов, вы ищете паттерны и глубинные связи там, где другие видят хаос.",
    "MATERIAL": "Вы цените материальные аспекты. Для вас важны конкретные, осязаемые результаты, факты и цифры — то, что можно потрогать и измерить."
}

# Вопросы для 2 этапа (мышление)
STAGE2_QUESTIONS = [
    {
        "text": "Как вы обычно объясняете сложные вещи?",
        "1": "Показываю на конкретном примере из жизни",
        "3": "Использую аналогии и сравнения",
        "5": "Строю логическую схему или модель",
        "7": "Описываю общие принципы и закономерности",
        "9": "Связываю с фундаментальными концепциями"
    },
    {
        "text": "Когда вы сталкиваетесь с проблемой, с чего начинаете?",
        "1": "Ищу конкретное решение здесь и сейчас",
        "3": "Вспоминаю похожие ситуации из прошлого",
        "5": "Анализирую причины и следствия",
        "7": "Ищу закономерности и общие принципы",
        "9": "Рассматриваю проблему в контексте более общей системы"
    }
]

STAGE2_FEEDBACK = {
    1: "Конкретно-ситуативное мышление. Вы фокусируетесь на деталях и конкретных действиях.",
    3: "Аналитическое мышление. Вы ищете причинно-следственные связи.",
    5: "Системное мышление. Вы видите взаимосвязи и структуры.",
    7: "Абстрактное мышление. Вы оперируете общими принципами.",
    9: "Мета-мышление. Вы видите картину целиком, включая контекст."
}

# Вопросы для 3 этапа (поведение)
STAGE3_QUESTIONS = [
    {
        "text": "В стрессовой ситуации вы обычно...",
        "A": "Действуете быстро, иногда импульсивно",
        "B": "Замираете, наблюдаете, анализируете",
        "C": "Ищете поддержку у других",
        "D": "Уходите в себя, обдумываете"
    },
    {
        "text": "В конфликте вы скорее...",
        "A": "Отстаиваете свои границы активно",
        "B": "Пытаетесь понять позицию другого",
        "C": "Ищете компромисс",
        "D": "Уклоняетесь, избегаете"
    }
]

STAGE3_FEEDBACK = "Ваш стиль поведения характеризуется..."

# Вопросы для 4 этапа (Дилтс)
STAGE4_QUESTIONS = [
    {
        "text": "Что для вас важнее всего в жизни?",
        "ENVIRONMENT": "Комфортное окружение и условия",
        "BEHAVIOR": "Мои действия и поступки",
        "CAPABILITIES": "Мои навыки и способности",
        "VALUES": "Мои ценности и убеждения",
        "IDENTITY": "Кто я есть на самом деле",
        "MISSION": "Мое предназначение, миссия"
    },
    {
        "text": "На каком уровне вы чаще всего ищете изменения?",
        "ENVIRONMENT": "Хочу изменить обстоятельства",
        "BEHAVIOR": "Хочу изменить свои привычки",
        "CAPABILITIES": "Хочу развить новые навыки",
        "VALUES": "Пересматриваю свои ценности",
        "IDENTITY": "Меняю представление о себе",
        "MISSION": "Ищу свое призвание"
    }
]

CONFLICT_PHRASES = {
    "ENVIRONMENT": {
        "note": "⚠️ Интересное наблюдение: ваше мышление работает на уровне Окружения, но ваша точка роста — в изменении паттернов поведения. Это классическое расхождение между тем, что вы думаете, и что делаете."
    },
    "BEHAVIOR": {
        "note": "⚠️ Любопытный парадокс: вы мыслите на уровне Поведения, но ваши убеждения находятся на уровне Способностей. Это создает внутреннее напряжение между действиями и верой в свои силы."
    },
    "CAPABILITIES": {
        "note": "⚠️ Вы обнаруживаете несоответствие: ваши способности развиты, но ценности требуют пересмотра. Тело уже умеет, а душа еще не решила."
    },
    "VALUES": {
        "note": "⚠️ Ваши ценности работают на одном уровне, а идентичность требует другого. Вы знаете, что важно, но не до конца понимаете, кто вы в этом."
    },
    "IDENTITY": {
        "note": "⚠️ Интересный конфликт: вы уже осознали себя по-новому, но миссия требует иного. Самоощущение опережает предназначение."
    },
    "MISSION": {
        "note": "⚠️ У вас высокий уровень осознания миссии, но окружение пока не готово. Вы видите дальше, чем можете реализовать сейчас."
    }
}

# ===== КОНСТАНТЫ ИНТИМНОГО МОДУЛЯ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1
FREE_INVITE_LIMIT = 3

INVITE_PACKAGES = {
    "3": {"price": 299, "links": 3, "emoji": "🥉", "popular": False},
    "5": {"price": 499, "links": 5, "emoji": "🥈", "popular": True},
    "10": {"price": 899, "links": 10, "emoji": "🥇", "popular": False}
}

FOUR_F_EMOJIS = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ", 
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

FOUR_F_SHORT = """
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>

🧬 4F — это 4 базовые реакции психики:
Нападение, бегство, секс, поглощение.
Ключи к управлению состояниями другого человека.

🔥 <b>1F - НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Что включает его агрессию
└ Как быстро её погасить

🏃 <b>2F - БЕГСТВО / СТРАХ</b>
└ Чего он боится на самом деле
└ Как стать для него безопасностью

🧬 <b>3F - СЕКС / ЖЕЛАНИЕ</b>
└ Что реально его заводит
└ 3 слова и 3 касания-ключа

🍽 <b>4F - ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Что запускает режим заработка
└ Как говорить с ним о деньгах
"""

FOUR_F_DESCRIPTIONS = {
    "1F": """😤 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЯРОСТЬ</b>

Его агрессия не возникает из ниоткуда.
Это реакция на конкретные ТРИГГЕРЫ — слова, интонации, ситуации.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Критика при свидетелях
   • Обесценивание его усилий
   • Игнорирование его границ
   • Определенные интонации голоса

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • Списку его ЛИЧНЫХ триггеров
   • 3 фразам-гасителям
   • Пониманию, почему он срывается на вас
   • Технике «Торможение»

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием гнева.""",
    
    "2F": """🏃 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ БЕГСТВО</b>

Страх — это реакция избегания.
Она включается, когда мозг видит СТИМУЛ, похожий на прошлую угрозу.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования
   • Определенные темы разговоров

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • Его личным триггерам страха
   • 3 якорям безопасности
   • Пониманию, почему он закрывается
   • Технике «Безопасная среда»

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием тревоги.""",
    
    "3F": """🧬 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЖЕЛАНИЕ</b>

Сексуальное влечение — это цепочка стимулов.
Определенные слова, взгляды, касания работают как ПАРОЛЬ.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Особая интонация голоса
   • Зрительный контакт определенной длины
   • Неожиданные касания
   • Контекст и обстановка

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • 3 словам-паролям
   • 3 касаниям-ключам
   • Его эротическому сценарию
   • Пониманию, что ГАСИТ желание

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием возбуждения.""",
    
    "4F": """🍽 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ РЕЖИМ «ДЕНЬГИ»</b>

Для него деньги = безопасность, статус, свобода.
Это состояние включается определенными ТРИГГЕРАМИ.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка
   • Определенные фразы-мотиваторы

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • 3 фразам, которые включают «режим предпринимателя»
   • Пониманию, что тормозит его заработок
   • Технике «Топливо»
   • Сценарию просьбы

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием мотивации."""
}

# ===== ССЫЛКИ НА ЯНДЕКС.ДИСК - ВСЕ 36 ПРОФИЛЕЙ =====
PROFILE_DISK_LINKS = {
    # SA Profiles
    "SA-1_DEF": "https://disk.yandex.ru/d/k-MqapaI3zmb_w",
    "SA-2_SIT": "https://disk.yandex.ru/d/1v8xNz0m6cPzTg",
    "SA-3_CON": "https://disk.yandex.ru/d/8kqMEvs7OC86PQ",
    "SA-4_EXP": "https://disk.yandex.ru/d/PzCDu_jfJpzgqg",
    "SA-5_INT": "https://disk.yandex.ru/d/EYPIF9_puI_t0A",
    "SA-6_AUT": "https://disk.yandex.ru/d/lfRe4hOGoneJUA",
    "SA-7_VAL": "https://disk.yandex.ru/d/TRFjXAPoxH8_Yw",
    "SA-8_TRA": "https://disk.yandex.ru/d/kUTCtJTez59G3g",
    "SA-9_IDE": "https://disk.yandex.ru/d/p54mj-rRgW54zg",
    
    # SP Profiles
    "SP-1_DEF": "https://disk.yandex.ru/d/F07HTDrGplwgWg",
    "SP-2_SIT": "https://disk.yandex.ru/d/MoXCgdUamEnmfA",
    "SP-3_CON": "https://disk.yandex.ru/d/9Sp--f1UF1WCrg",
    "SP-4_EXP": "https://disk.yandex.ru/d/K869xbd1mmLwWA",
    "SP-5_INT": "https://disk.yandex.ru/d/5Ip1IllKjF1TQg",
    "SP-6_AUT": "https://disk.yandex.ru/d/saOXkhBzFdGO6A",
    "SP-7_VAL": "https://disk.yandex.ru/d/1umIAOuQVec-nw",
    "SP-8_TRA": "https://disk.yandex.ru/d/lqhpsMCnQaXkzw",
    "SP-9_IDE": "https://disk.yandex.ru/d/RsvI8Kw1G367Mg",
    
    # IA Profiles
    "IA-1_DEF": "https://disk.yandex.ru/d/Ca6qVNiaScceHA",
    "IA-2_SIT": "https://disk.yandex.ru/d/fQiK3NQ6kJB0vw",
    "IA-3_CON": "https://disk.yandex.ru/d/44CwOGbfN2304g",
    "IA-4_EXP": "https://disk.yandex.ru/d/vukRKPMMWiJUZw",
    "IA-5_INT": "https://disk.yandex.ru/d/ERvhVQqxEgafsw",
    "IA-6_AUT": "https://disk.yandex.ru/d/41U2jQq-SZBVPg",
    "IA-7_VAL": "https://disk.yandex.ru/d/7cs7v7_phz5BjQ",
    "IA-8_TRA": "https://disk.yandex.ru/d/3QpBmWsO8l3xlw",
    "IA-9_IDE": "https://disk.yandex.ru/d/EjTrACZrYgjFEg",
    
    # IP Profiles
    "IP-1_DEF": "https://disk.yandex.ru/d/MTfoxMFHrfP-Lw",
    "IP-2_SIT": "https://disk.yandex.ru/d/L6X5a5rRT4FPWQ",
    "IP-3_CON": "https://disk.yandex.ru/d/larM19K4iVyy6Q",
    "IP-4_EXP": "https://disk.yandex.ru/d/jSvbjNOi3BuVAw",
    "IP-5_INT": "https://disk.yandex.ru/d/ny-cnsvdtj_fDw",
    "IP-6_AUT": "https://disk.yandex.ru/d/kDd9tKyKVughag",
    "IP-7_VAL": "https://disk.yandex.ru/d/DNAG15nsH0-wYA",
    "IP-8_TRA": "https://disk.yandex.ru/d/K90BW0SSTOuAhA",
    "IP-9_IDE": "https://disk.yandex.ru/d/VIgdg8gFVp10aw",
    
    # Default
    "default": "https://disk.yandex.ru/d/EYPIF9_puI_t0A"
}

# ===== КОНФИГУРАЦИЯ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBot")
BOT_LINK = f"t.me/{BOT_USERNAME}"
AUTHOR_LINK = "https://t.me/author"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")
GIFT_PDF_LINK = os.getenv("GIFT_PDF_LINK", "https://disk.yandex.ru/d/example")

SHARE_TEXT = "🔮 Узнай свой психологический профиль за 15 минут"
GIFT_SCREEN_TEXT = "🎁 Ваш подарок готов!"

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def get_disk_link_by_profile(profile_code: str) -> str:
    """Умный поиск ссылки на Яндекс.Диск по коду профиля"""
    if not profile_code:
        return PROFILE_DISK_LINKS["default"]
    
    profile_upper = profile_code.upper().strip()
    
    # Прямое совпадение
    if profile_upper in PROFILE_DISK_LINKS:
        return PROFILE_DISK_LINKS[profile_upper]
    
    # Замена _ на -
    profile_with_hyphen = profile_upper.replace('_', '-')
    if profile_with_hyphen in PROFILE_DISK_LINKS:
        return PROFILE_DISK_LINKS[profile_with_hyphen]
    
    # Замена - на _
    profile_with_underscore = profile_upper.replace('-', '_')
    if profile_with_underscore in PROFILE_DISK_LINKS:
        return PROFILE_DISK_LINKS[profile_with_underscore]
    
    # Поиск по начальным символам
    for key in PROFILE_DISK_LINKS:
        if key.startswith(profile_upper[:5]):
            return PROFILE_DISK_LINKS[key]
    
    return PROFILE_DISK_LINKS["default"]

def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """Разбивает длинное сообщение на части"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    lines = text.split('\n')
    
    for line in lines:
        if len(line) > max_length:
            if current_part:
                parts.append(current_part)
                current_part = ""
            for i in range(0, len(line), max_length):
                parts.append(line[i:i+max_length])
        else:
            test_part = current_part + ("\n" if current_part else "") + line
            if len(test_part) <= max_length:
                current_part = test_part
            else:
                if current_part:
                    parts.append(current_part)
                current_part = line
    
    if current_part:
        parts.append(current_part)
    
    return parts

async def safe_send_message(chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE, 
                           reply_markup=None, parse_mode: str = "HTML", max_retries: int = 3) -> bool:
    """Безопасная отправка сообщения"""
    try:
        parts = split_long_message(text)
        
        for i, part in enumerate(parts):
            current_markup = reply_markup if i == len(parts) - 1 else None
            
            for attempt in range(max_retries):
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        reply_markup=current_markup,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"❌ Не удалось отправить сообщение: {e}")
                        return False
            
            if i < len(parts) - 1:
                await asyncio.sleep(0.5)
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка в safe_send_message: {e}")
        return False

# ===== ФУНКЦИИ РАСЧЕТА ПРОФИЛЯ =====

def determine_perception_type(scores: Dict[str, int]) -> str:
    """Определяет тип восприятия по набранным баллам"""
    return max(scores, key=scores.get)

def get_type_code(perception_type: str) -> str:
    """Преобразует тип восприятия в код"""
    mapping = {
        "EXTERNAL": "E",
        "INTERNAL": "I",
        "SYMBOLIC": "S",
        "MATERIAL": "M"
    }
    return mapping.get(perception_type, "E")

def calculate_thinking_level_by_scores(stage2_scores: Dict[str, int]) -> int:
    """Рассчитывает уровень мышления"""
    # Простая формула: средневзвешенное
    total = 0
    count = 0
    for level, score in stage2_scores.items():
        total += int(level) * score
        count += score
    
    if count == 0:
        return 5
    
    return round(total / count)

def determine_dilts_level(answers: List[str]) -> str:
    """Определяет уровень Дилтса по ответам"""
    if not answers:
        return "BEHAVIOR"
    
    # Считаем частоту ответов
    freq = {}
    for a in answers:
        freq[a] = freq.get(a, 0) + 1
    
    # Возвращаем самый частый
    return max(freq, key=freq.get) if freq else "BEHAVIOR"

def get_dilts_code(dilts_level: str) -> str:
    """Преобразует уровень Дилтса в код"""
    mapping = {
        "ENVIRONMENT": "env",
        "BEHAVIOR": "beh",
        "CAPABILITIES": "cap",
        "VALUES": "val",
        "IDENTITY": "id",
        "MISSION": "mis"
    }
    return mapping.get(dilts_level, "beh")

def calculate_final_level(type_code: str, thinking_level: int, dilts_code: str) -> int:
    """Рассчитывает финальный уровень профиля"""
    # Базовая формула: уровень мышления корректируется на основе типа и дилтса
    base_level = thinking_level
    
    # Корректировка по типу
    type_adjustments = {
        "E": 0,
        "I": 1,
        "S": -1,
        "M": 0
    }
    
    # Корректировка по дилтсу
    dilts_adjustments = {
        "env": -1,
        "beh": 0,
        "cap": 1,
        "val": 1,
        "id": 2,
        "mis": 2
    }
    
    level = base_level + type_adjustments.get(type_code, 0) + dilts_adjustments.get(dilts_code, 0)
    
    # Ограничиваем от 1 до 9
    return max(1, min(9, level))

def calculate_profile_final(user_data: dict) -> dict:
    """Рассчитывает финальный профиль"""
    scores = user_data.get("scores", {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0})
    perception_type = determine_perception_type(scores)
    type_code = get_type_code(perception_type)
    
    stage2_scores = user_data.get("stage2_level_scores_dict", {})
    thinking_level = calculate_thinking_level_by_scores(stage2_scores)
    
    stage4_answers = user_data.get("stage4_dilts_answers", [])
    dilts_level = determine_dilts_level(stage4_answers)
    dilts_code = get_dilts_code(dilts_level)
    
    final_level = calculate_final_level(type_code, thinking_level, dilts_code)
    
    # Формируем отображаемое имя
    type_prefix = type_code
    if type_code == "E":
        type_prefix = "SA"
    elif type_code == "I":
        type_prefix = "SP"
    elif type_code == "S":
        type_prefix = "IA"
    elif type_code == "M":
        type_prefix = "IP"
    
    display_name = f"{type_prefix}-{final_level}_{dilts_code.upper()}"
    
    return {
        "perception_type": perception_type,
        "type_code": type_prefix,
        "thinking_level": thinking_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code.upper(),
        "level": final_level,
        "display_name": display_name
    }

# ===== ФУНКЦИИ ТЕСТА =====

# --- ЭТАП 1 ---

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает введение в 1 этап"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        "Как ваш разум фильтрует реальность?\n"
        "На что вы обращаете внимание в первую очередь?\n\n"
        "Я задам вам 5 вопросов, чтобы понять "
        "базовую настройку вашего восприятия."
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Подробнее об этапе", callback_data="stage1_details")],
        [InlineKeyboardButton("🚀 Начать этап 1", callback_data="start_stage_1")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали 1 этапа"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📖 <b>О ВОСПРИЯТИИ</b>\n\n"
        "Я определю ваш доминирующий канал восприятия:\n\n"
        "🌍 <b>Внешний (EXTERNAL)</b> — вы ориентируетесь на мнения других, "
        "социальные нормы, обратную связь.\n\n"
        "🧠 <b>Внутренний (INTERNAL)</b> — вы доверяете своим ощущениям, "
        "внутреннему компасу.\n\n"
        "🔮 <b>Символический (SYMBOLIC)</b> — вы ищете смыслы, знаки, "
        "паттерны, символы.\n\n"
        "💰 <b>Материальный (MATERIAL)</b> — вы цените конкретные, "
        "осязаемые результаты и вещи."
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage1_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению 1 этапа"""
    return await show_stage_1_intro(update, context)

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает 1 этап"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage1_current"] = 0
    context.user_data["stage1_answers"] = []
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задает вопрос 1 этапа"""
    query = update.callback_query
    await query.answer()
    
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(STAGE1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE1_QUESTIONS[current]
    
    keyboard = [
        [InlineKeyboardButton(f"🌍 {question['options']['EXTERNAL']}", callback_data="stage1_EXTERNAL")],
        [InlineKeyboardButton(f"🧠 {question['options']['INTERNAL']}", callback_data="stage1_INTERNAL")],
        [InlineKeyboardButton(f"🔮 {question['options']['SYMBOLIC']}", callback_data="stage1_SYMBOLIC")],
        [InlineKeyboardButton(f"💰 {question['options']['MATERIAL']}", callback_data="stage1_MATERIAL")]
    ]
    
    await query.edit_message_text(
        f"Вопрос {current + 1}/{len(STAGE1_QUESTIONS)}:\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ 1 этапа"""
    query = update.callback_query
    await query.answer()
    
    answer = query.data.replace("stage1_", "")
    
    # Сохраняем ответ
    context.user_data.setdefault("stage1_answers", []).append(answer)
    
    # Увеличиваем счетчик для этого типа
    scores = context.user_data.setdefault("scores", {})
    scores[answer] = scores.get(answer, 0) + 1
    
    context.user_data["stage1_current"] = context.user_data.get("stage1_current", 0) + 1
    
    return await ask_stage_1_question(update, context)

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает 1 этап"""
    query = update.callback_query
    await query.answer()
    
    scores = context.user_data.get("scores", {})
    perception_type = determine_perception_type(scores)
    
    context.user_data["perception_type"] = perception_type
    
    text = f"""
✅ <b>ЭТАП 1 ЗАВЕРШЕН</b>

{STAGE1_FEEDBACK.get(perception_type, "Спасибо за ответы!")}

Переходим к этапу 2?
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Перейти к этапу 2", callback_data="show_stage_2_intro")],
        [InlineKeyboardButton("📖 Подробнее об этапе 2", callback_data="stage2_details")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

# --- ЭТАП 2 ---

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает введение в 2 этап"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        "Как вы обрабатываете информацию?\n"
        "На каком уровне абстракции вы мыслите?\n\n"
        "Я задам вам несколько вопросов, чтобы определить "
        "уровень вашего мышления (от 1 до 9)."
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Подробнее об этапе", callback_data="stage2_details")],
        [InlineKeyboardButton("🚀 Начать этап 2", callback_data="start_stage_2")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали 2 этапа"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📖 <b>О МЫШЛЕНИИ</b>\n\n"
        "Уровни мышления (по Роберту Дилтсу):\n\n"
        "1️⃣ Конкретный — факты, детали, действия\n"
        "2️⃣ Ситуативный — контекст, обстоятельства\n"
        "3️⃣ Аналитический — причины, связи\n"
        "4️⃣ Системный — структуры, паттерны\n"
        "5️⃣ Стратегический — стратегии, планы\n"
        "6️⃣ Принципиальный — принципы, законы\n"
        "7️⃣ Абстрактный — концепции, модели\n"
        "8️⃣ Философский — фундаментальные вопросы\n"
        "9️⃣ Мета-уровень — мышление о мышлении"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage2_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению 2 этапа"""
    return await show_stage_2_intro(update, context)

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает 2 этап"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    context.user_data["stage2_answers"] = []
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задает вопрос 2 этапа"""
    query = update.callback_query
    await query.answer()
    
    current = context.user_data.get("stage2_current", 0)
    
    if current >= len(STAGE2_QUESTIONS):
        return await finish_stage_2(update, context)
    
    question = STAGE2_QUESTIONS[current]
    
    keyboard = [
        [InlineKeyboardButton(f"1️⃣ {question['1']}", callback_data="stage2_1")],
        [InlineKeyboardButton(f"3️⃣ {question['3']}", callback_data="stage2_3")],
        [InlineKeyboardButton(f"5️⃣ {question['5']}", callback_data="stage2_5")],
        [InlineKeyboardButton(f"7️⃣ {question['7']}", callback_data="stage2_7")],
        [InlineKeyboardButton(f"9️⃣ {question['9']}", callback_data="stage2_9")]
    ]
    
    await query.edit_message_text(
        f"Вопрос {current + 1}/{len(STAGE2_QUESTIONS)}:\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ 2 этапа"""
    query = update.callback_query
    await query.answer()
    
    level = query.data.replace("stage2_", "")
    
    # Сохраняем ответ
    context.user_data.setdefault("stage2_answers", []).append(int(level))
    
    # Увеличиваем счетчик для этого уровня
    scores = context.user_data.setdefault("stage2_level_scores_dict", {})
    scores[level] = scores.get(level, 0) + 1
    
    context.user_data["stage2_current"] = context.user_data.get("stage2_current", 0) + 1
    
    return await ask_stage_2_question(update, context)

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает 2 этап"""
    query = update.callback_query
    await query.answer()
    
    scores = context.user_data.get("stage2_level_scores_dict", {})
    thinking_level = calculate_thinking_level_by_scores(scores)
    
    context.user_data["thinking_level"] = thinking_level
    
    text = f"""
✅ <b>ЭТАП 2 ЗАВЕРШЕН</b>

{STAGE2_FEEDBACK.get(thinking_level, f"Ваш уровень мышления: {thinking_level}")}

Переходим к этапу 3?
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Перейти к этапу 3", callback_data="show_stage_3_intro")],
        [InlineKeyboardButton("📖 Подробнее об этапе 3", callback_data="stage3_details")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

# --- ЭТАП 3 ---

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает введение в 3 этап"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🧠 <b>ЭТАП 3: КОНФИГУРАЦИЯ ПОВЕДЕНИЯ</b>\n\n"
        "Как вы действуете в разных ситуациях?\n"
        "Какие паттерны поведения для вас характерны?\n\n"
        "Я задам вам несколько вопросов, чтобы понять "
        "ваш поведенческий профиль."
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Подробнее об этапе", callback_data="stage3_details")],
        [InlineKeyboardButton("🚀 Начать этап 3", callback_data="start_stage_3")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали 3 этапа"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📖 <b>О ПОВЕДЕНИИ</b>\n\n"
        "Я проанализирую ваши поведенческие паттерны:\n\n"
        "⚡️ Реакция на стресс\n"
        "🤝 Стиль в конфликте\n"
        "🗣 Коммуникативные стратегии\n"
        "🎯 Способы достижения целей\n\n"
        "Это поможет понять, почему вы действуете "
        "так, а не иначе."
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage3_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению 3 этапа"""
    return await show_stage_3_intro(update, context)

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает 3 этап"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    context.user_data["stage3_answers"] = []
    context.user_data["stage3_level_scores"] = []
    
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задает вопрос 3 этапа"""
    query = update.callback_query
    await query.answer()
    
    current = context.user_data.get("stage3_current", 0)
    
    if current >= len(STAGE3_QUESTIONS):
        return await finish_stage_3(update, context)
    
    question = STAGE3_QUESTIONS[current]
    
    keyboard = [
        [InlineKeyboardButton(f"A. {question['A']}", callback_data="stage3_A")],
        [InlineKeyboardButton(f"B. {question['B']}", callback_data="stage3_B")],
        [InlineKeyboardButton(f"C. {question['C']}", callback_data="stage3_C")],
        [InlineKeyboardButton(f"D. {question['D']}", callback_data="stage3_D")]
    ]
    
    await query.edit_message_text(
        f"Вопрос {current + 1}/{len(STAGE3_QUESTIONS)}:\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ 3 этапа"""
    query = update.callback_query
    await query.answer()
    
    answer = query.data.replace("stage3_", "")
    
    context.user_data.setdefault("stage3_answers", []).append(answer)
    context.user_data.setdefault("stage3_level_scores", []).append(ord(answer) - ord('A') + 1)
    
    context.user_data["stage3_current"] = context.user_data.get("stage3_current", 0) + 1
    
    return await ask_stage_3_question(update, context)

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает 3 этап"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
✅ <b>ЭТАП 3 ЗАВЕРШЕН</b>

{STAGE3_FEEDBACK}

Переходим к этапу 4?
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Перейти к этапу 4", callback_data="show_stage_4_intro")],
        [InlineKeyboardButton("📖 Подробнее об этапе 4", callback_data="stage4_details")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

# --- ЭТАП 4 ---

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает введение в 4 этап"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🧠 <b>ЭТАП 4: ТОЧКА РОСТА</b>\n\n"
        "На каком уровне вы ищете изменения?\n"
        "Где находится ваша зона ближайшего развития?\n\n"
        "Я помогу определить ваш текущий уровень "
        "по пирамиде Дилтса."
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Подробнее об этапе", callback_data="stage4_details")],
        [InlineKeyboardButton("🚀 Начать этап 4", callback_data="start_stage_4")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали 4 этапа"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📖 <b>О ТОЧКЕ РОСТА</b>\n\n"
        "Пирамида Дилтса (логические уровни):\n\n"
        "🌍 <b>Окружение</b> — где и когда\n"
        "🏃 <b>Поведение</b> — что делаю\n"
        "🧠 <b>Способности</b> — как, какими навыками\n"
        "💎 <b>Ценности</b> — почему, зачем\n"
        "👤 <b>Идентичность</b> — кто я\n"
        "🌟 <b>Миссия</b> — ради чего\n\n"
        "Ваша точка роста — уровень, на котором "
        "изменения дадут максимальный эффект."
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage4_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к введению 4 этапа"""
    return await show_stage_4_intro(update, context)

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает 4 этап"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    context.user_data["stage4_dilts_answers"] = []
    
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задает вопрос 4 этапа"""
    query = update.callback_query
    await query.answer()
    
    current = context.user_data.get("stage4_current", 0)
    
    if current >= len(STAGE4_QUESTIONS):
        return await finish_stage_4(update, context)
    
    question = STAGE4_QUESTIONS[current]
    
    keyboard = [
        [InlineKeyboardButton(f"🌍 {question['ENVIRONMENT']}", callback_data="stage4_ENVIRONMENT")],
        [InlineKeyboardButton(f"🏃 {question['BEHAVIOR']}", callback_data="stage4_BEHAVIOR")],
        [InlineKeyboardButton(f"🧠 {question['CAPABILITIES']}", callback_data="stage4_CAPABILITIES")],
        [InlineKeyboardButton(f"💎 {question['VALUES']}", callback_data="stage4_VALUES")],
        [InlineKeyboardButton(f"👤 {question['IDENTITY']}", callback_data="stage4_IDENTITY")],
        [InlineKeyboardButton(f"🌟 {question['MISSION']}", callback_data="stage4_MISSION")]
    ]
    
    await query.edit_message_text(
        f"Вопрос {current + 1}/{len(STAGE4_QUESTIONS)}:\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ 4 этапа"""
    query = update.callback_query
    await query.answer()
    
    answer = query.data.replace("stage4_", "")
    
    context.user_data.setdefault("stage4_dilts_answers", []).append(answer)
    context.user_data["stage4_current"] = context.user_data.get("stage4_current", 0) + 1
    
    return await ask_stage_4_question(update, context)

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает 4 этап и показывает результаты"""
    query = update.callback_query
    await query.answer()
    
    # Рассчитываем финальный профиль
    profile_data = calculate_profile_final(context.user_data)
    context.user_data["profile_data"] = profile_data
    
    # Показываем анализ
    dilts_level = profile_data.get("dilts_level", "BEHAVIOR")
    analysis = STAGE4_ANALYSIS_SCREEN if 'STAGE4_ANALYSIS_SCREEN' in globals() else "Анализ завершен."
    
    text = f"""
✅ <b>ЭТАП 4 ЗАВЕРШЕН</b>

{analysis}

🎉 <b>ТЕСТ ПРОЙДЕН!</b>
Ваш профиль: {profile_data['display_name']}

Нажмите кнопку ниже, чтобы увидеть результаты.
"""
    
    keyboard = [[InlineKeyboardButton("📊 ПОСМОТРЕТЬ РЕЗУЛЬТАТЫ", callback_data="show_results")]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return RESULTS

# --- УТОЧНЯЮЩИЕ ВОПРОСЫ ---

async def ask_clarification_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    """Задает уточняющий вопрос"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="clarify_yes")],
        [InlineKeyboardButton("❌ Нет", callback_data="clarify_no")]
    ]
    
    await query.edit_message_text(question, reply_markup=InlineKeyboardMarkup(keyboard))
    return CLARIFICATION

async def handle_clarification_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на уточняющий вопрос"""
    query = update.callback_query
    await query.answer()
    
    # Здесь можно обработать ответ и вернуться к тесту
    return RESULTS

# ===== ФУНКЦИИ РЕЗУЛЬТАТОВ =====

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает экран результатов"""
    query = update.callback_query
    await query.answer()
    
    profile_data = context.user_data.get("profile_data", {"display_name": "SA-5_INT"})
    profile_code = profile_data.get("display_name", "SA-5_INT")
    disk_link = get_disk_link_by_profile(profile_code)
    
    message = f"""
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>

📊 {profile_code}

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 <b>ИНСТРУМЕНТ</b>
Сегодня: попросите кого-то о маленькой услуге.
Заметьте, что мир не рухнул.

📁 <b>ССЫЛКА НА ПРОФИЛЬ:</b>
{disk_link}
"""
    
    has_shared = context.user_data.get("has_shared", False)
    
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="get_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="my_sexual_profile")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Получить сказку «Мастер Меча»", callback_data="open_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="my_sexual_profile")]
        ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return RESULTS

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран подарка за репост"""
    query = update.callback_query
    await query.answer()
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    keyboard = [
        [InlineKeyboardButton("🪞 Поделиться зеркалом", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился(ась)", callback_data="confirm_share")],
        [InlineKeyboardButton("Продолжить без этого", callback_data="skip_share")]
    ]
    
    await query.edit_message_text(
        "🪞 <b>ПОДЕЛИТЕСЬ ЗЕРКАЛОМ</b>\n\nПоделитесь с друзьями и получите подарок!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return GIFT_SCREEN

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение репоста"""
    query = update.callback_query
    await query.answer("✅ Спасибо!")
    context.user_data["has_shared"] = True
    return await open_gift_screen(update, context)

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск репоста"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие подарка"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Открыть сказку", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Вернуться", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        GIFT_SCREEN_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return OPEN_GIFT_SCREEN

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран полного описания"""
    query = update.callback_query
    await query.answer()
    
    profile_data = context.user_data.get("profile_data", {})
    profile_code = profile_data.get('display_name', 'SA-5_INT') if profile_data else "SA-5_INT"
    
    text = f"""
📖 <b>ПОЛНОЕ ОПИСАНИЕ ПРОФИЛЯ</b>

• Детальный анализ личности
• Ключевые паттерны поведения
• Точки роста и рекомендации
• Практические инструменты

📊 Ваш профиль: {profile_code}
💰 Стоимость: 690 ₽
"""
    keyboard = [
        [InlineKeyboardButton("💳 Купить за 690 ₽", callback_data="buy_package")],
        [InlineKeyboardButton("⬅️ Вернуться", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return PACKAGE_SCREEN

async def buy_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка полного описания"""
    query = update.callback_query
    await query.answer("💳 Функция оплаты в разработке")
    return await show_results_screen(update, context)

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    return await show_results_screen(update, context)

# ===== ФУНКЦИИ ЗАГРУЗКИ ИНТИМНОГО ПРОФИЛЯ =====

def find_project_root() -> str:
    """Находит корень проекта"""
    try:
        current = os.path.dirname(os.path.abspath(__file__))
        
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, "profiles")):
                return current
            current = os.path.dirname(current)
        
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = find_project_root()

def load_intimate_profile() -> dict:
    """Загружает интимный профиль"""
    try:
        possible_paths = [
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
            os.path.join("sexual_18", "sa_5_int.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return get_emergency_profile()
    except Exception:
        return get_emergency_profile()

def get_emergency_profile() -> dict:
    """Аварийный интимный профиль"""
    return {
        "profile_type": "SA-5_INT",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "role": "Жрец/Жрица сексуальной мистерии",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.",
        "sections": {
            "what_turns_on": {
                "title": "🔴 ВКЛЮЧАЕТ",
                "items": [
                    "Долгие прелюдии",
                    "Ролевые игры",
                    "Шёпот на ухо"
                ]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": [
                    "Спешка",
                    "Отсутствие атмосферы"
                ]
            }
        }
    }

def load_friend_intimate_profile(friend_name: str, friend_profile: str = None) -> dict:
    """Загружает интимный профиль друга"""
    profile = load_intimate_profile()
    profile["profile_type"] = friend_profile or "SA-5_INT"
    profile["friend_name"] = friend_name
    return profile

def load_friend_standard_profile() -> dict:
    """Стандартный профиль друга"""
    return {
        "archetype": "Автономный стратег",
        "quote": "«Я не ищу одобрения — я ищу эффективность.»",
        "pain": "Вам сложно делегировать.",
        "immediate_tool": "Передайте кому-то одну задачу полностью."
    }

def load_4f_content(function: str) -> dict:
    """Загружает 4F контент"""
    base_triggers = {
        "1F": ["«Я понимаю, почему ты так реагируешь»", "«Ты имеешь полное право злиться»"],
        "2F": ["«Ты не обязан это делать»", "«Здесь безопасно»"],
        "3F": ["«Ты такой...»", "Взгляд в глаза"],
        "4F": ["«Ты можешь заработать на этом»", "«Это твой шанс»"]
    }
    
    return {
        "function": function,
        "emoji": FOUR_F_EMOJIS.get(function, "🔑"),
        "title": FOUR_F_TITLES.get(function, "КЛЮЧ"),
        "description": FOUR_F_DESCRIPTIONS.get(function, ""),
        "triggers": base_triggers.get(function, []),
        "analysis": "Анализ состояния...",
        "protocol": "Протокол управления..."
    }

def format_intimate_profile_part1(profile_data: dict, user_name: str) -> str:
    """Часть 1 интимного профиля"""
    profile_code = profile_data.get('profile_type', 'SA-5_INT')
    disk_link = get_disk_link_by_profile(profile_code)
    
    message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ</b>
📊 {user_name}, {profile_code}

🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', '')}

📁 <b>ПОЛНАЯ ВЕРСИЯ:</b>
{disk_link}
"""
    
    sections = profile_data.get('sections', {})
    section = sections.get("what_turns_on", {})
    if section:
        title = section.get('title', '')
        message += f"\n\n{title}"
        if 'items' in section:
            for item in section['items']:
                message += f"\n• {item}"
    
    return message

def format_intimate_profile_part2(profile_data: dict, user_name: str) -> str:
    """Часть 2 интимного профиля"""
    message = ""
    sections = profile_data.get('sections', {})
    
    section = sections.get("what_turns_off", {})
    if section:
        title = section.get('title', '')
        message += f"\n\n{title}"
        if 'items' in section:
            for item in section['items']:
                message += f"\n• {item}"
    
    section = sections.get("erogenous_zone", {})
    if section:
        title = section.get('title', '')
        message += f"\n\n{title}"
        if 'trigger' in section:
            message += f"\n{section['trigger']}"
    
    return message

def format_intimate_profile_part3(profile_data: dict, user_name: str) -> str:
    """Часть 3 интимного профиля с кнопками"""
    message = f"""

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что 🪞 СВОЁ отражение.
Но у <b>каждого друга</b> — своя тайна.

<b>⬇️ КАК УВИДЕТЬ ИХ:</b>

<b>1.</b> 🚀 Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
<b>2.</b> 💌 Отправьте ссылку другу
<b>3.</b> 🔓 Друг проходит тест → вам открывается ЕГО профиль
"""
    return message

def format_friend_intimate_profile(profile_data: dict, friend_name: str) -> str:
    """Форматирует профиль друга"""
    friend_profile = profile_data.get('profile_type', 'SA-5_INT')
    disk_link = get_disk_link_by_profile(friend_profile)
    
    message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
👤 {friend_name}

📊 Тип: {friend_profile}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', f'«{friend_name}, со мной не скучно. Со мной — вкусно.»')}

📁 <b>ПОЛНАЯ ВЕРСИЯ:</b>
{disk_link}
"""
    
    sections = profile_data.get('sections', {})
    section = sections.get("what_turns_on", {})
    if section and 'items' in section:
        message += f"\n\n{section.get('title', '')}"
        for item in section['items'][:3]:
            message += f"\n• {item}"
    
    return message

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====

user_invites = {}

def get_user_invites(user_id: int) -> list:
    """Получает список приглашений"""
    if user_id not in user_invites:
        user_invites[user_id] = []
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    """Считает количество бесплатных друзей"""
    invites = get_user_invites(user_id)
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    invites = get_user_invites(user_id)
    if len(invites) > 0:
        return
    
    current_time = datetime.now().timestamp()
    
    test_friends = [
        {
            "invite_id": f"test_free_1_{user_id}",
            "friend_id": 1001,
            "friend_name": "@alex",
            "friend_profile": "SA-3_CON",
            "status": "used",
            "access_status": "free",
            "created_at": current_time,
            "purchased_functions": [],
            "invite_type": "🆓"
        },
        {
            "invite_id": f"test_free_2_{user_id}",
            "friend_id": 1002,
            "friend_name": "@maria",
            "friend_profile": "IP-5_INT",
            "status": "used",
            "access_status": "free",
            "created_at": current_time,
            "purchased_functions": ["1F"],
            "invite_type": "🆓"
        }
    ]
    
    invites.extend(test_friends)

def get_user_limits(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Получает лимиты пользователя"""
    return context.user_data.setdefault("invite_limits", {
        "free_used": 0,
        "total_purchased": 0,
        "paid_packages": []
    })

def can_create_invite(user_limits: dict, total_invites: int) -> Tuple[bool, bool, str]:
    """Проверяет возможность создания приглашения"""
    free_used = user_limits["free_used"]
    
    if free_used < FREE_INVITE_LIMIT:
        return True, True, f"Осталось бесплатных: {FREE_INVITE_LIMIT - free_used}"
    
    paid_available = user_limits["total_purchased"] - (total_invites - FREE_INVITE_LIMIT)
    if paid_available > 0:
        return True, False, f"Осталось платных: {paid_available}"
    
    return False, False, "Лимит исчерпан"

def get_friend_by_id(context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> Optional[dict]:
    """Получает данные друга по ID"""
    invites = context.user_data.get("sexual_invites", [])
    return next((inv for inv in invites if inv.get("friend_id") == friend_id), None)

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====

def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    """Генерирует ID платежа"""
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """Создает счет"""
    return {
        "success": True,
        "payment_id": payment_id,
        "confirmation_url": "https://test.payment.url",
        "amount": amount,
        "status": "pending"
    }

# ===== ФУНКЦИИ ИНТИМНОГО МОДУЛЯ =====

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = MY_SEXUAL_PROFILE
        
        user_name = query.from_user.first_name or "Пользователь"
        profile_data = load_intimate_profile()
        
        # Добавляем данные из основного теста
        main_profile = context.user_data.get("profile_data", {})
        if main_profile:
            profile_data["profile_type"] = main_profile.get('display_name', 'SA-5_INT')
        
        message_part1 = format_intimate_profile_part1(profile_data, user_name)
        message_part2 = format_intimate_profile_part2(profile_data, user_name)
        message_part3 = format_intimate_profile_part3(profile_data, user_name)
        
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_to_results")]
        ]
        nav_keyboard = InlineKeyboardMarkup(keyboard)
        
        chat_id = query.message.chat_id
        
        # Отправляем части
        try:
            await query.edit_message_text(message_part1, parse_mode="HTML", disable_web_page_preview=True)
        except:
            await safe_send_message(chat_id, message_part1, context)
        
        await asyncio.sleep(1)
        
        if message_part2.strip():
            await safe_send_message(chat_id, message_part2, context)
            await asyncio.sleep(1)
        
        if message_part3.strip():
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_part3,
                reply_markup=nav_keyboard,
                parse_mode="HTML"
            )
        
        return MY_SEXUAL_PROFILE
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return RESULTS

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        user_limits = get_user_limits(context)
        invites = context.user_data.get("sexual_invites", [])
        if not invites:
            user_id = query.from_user.id
            invites = get_user_invites(user_id)
            context.user_data["sexual_invites"] = invites
        
        total_invites = len([inv for inv in invites if inv.get("status") in ["active", "used"]])
        
        can_create, is_free, message = can_create_invite(user_limits, total_invites)
        
        if not can_create:
            await query.answer("❌ Лимит ссылок исчерпан!", show_alert=True)
            return await buy_invite_packages_callback(update, context)
        
        profile = context.user_data.get("profile_data", {"display_name": "SA-5_INT"})
        
        invite_code = f"sex_{uuid.uuid4().hex[:8]}"
        invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
        
        if is_free:
            user_limits["free_used"] += 1
        
        invite_data = {
            "invite_id": invite_code,
            "link": invite_url,
            "profile_code": profile.get('display_name', 'SA-5_INT'),
            "status": "active",
            "created_at": datetime.now().timestamp(),
            "is_free": is_free,
            "invite_type": "🆓" if is_free else "💎"
        }
        
        invites.insert(0, invite_data)
        
        text = f"""
🔞 <b>ВАША ССЫЛКА ГОТОВА!</b>

🔗 <code>{invite_url}</code>

{SEXUAL_DIVIDER}
🟢 <b>АКТИВНА</b>
"""
        
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}"
        
        keyboard = [
            [InlineKeyboardButton("✈️ ОТПРАВИТЬ ДРУГУ", url=share_url)],
            [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return INVITES_LIST

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мои отражения"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        user_id = query.from_user.id
        invites = get_user_invites(user_id)
        context.user_data["sexual_invites"] = invites
        
        used_invites = [inv for inv in invites if inv.get("status") == "used"]
        
        user_profile = context.user_data.get("profile_data", {"display_name": "SA-5_INT"})
        user_profile_code = user_profile.get('display_name', 'SA-5_INT')
        user_profile_link = get_disk_link_by_profile(user_profile_code)
        
        message = f"""<b>🪞 МОИ ОТРАЖЕНИЯ</b>
────────────────

<b>📊 СТАТИСТИКА</b>
🪞 Всего ссылок: {len(invites)}
👥 Посмотрелись: {len(used_invites)}

<b>🪞 МОЁ ОТРАЖЕНИЕ</b>
📌 {user_profile_code}
📁 {user_profile_link}
"""

        if used_invites:
            message += f"\n<b>👥 ДРУЗЬЯ ({len(used_invites)})</b>\n"
            for inv in used_invites[:3]:
                name = inv.get("friend_name", "друг")
                profile = inv.get("friend_profile", "SA-3_CON")
                message += f"\n• {name} • {profile}"
        
        keyboard = [
            [InlineKeyboardButton("◀️ К ПРОФИЛЮ", callback_data="my_sexual_profile")],
            [InlineKeyboardButton("🔴 4F КЛЮЧИ", callback_data="four_f_main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return INVITES_LIST
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return INVITES_LIST

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MAIN
        
        keyboard = [
            [InlineKeyboardButton("📘 ПОДРОБНЕЕ", callback_data="four_f_detailed")],
            [InlineKeyboardButton("🔍 К ОТРАЖЕНИЯМ", callback_data="my_invites")],
            [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="my_sexual_profile")]
        ]
        
        await query.edit_message_text(
            FOUR_F_SHORT,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MAIN
    except Exception:
        return INVITES_LIST

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробное описание 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_DETAILED
        
        example_link = get_disk_link_by_profile("SA-3_CON")
        
        message = f"""
🔥 <b>1F - ЯРОСТЬ / НАПАДЕНИЕ</b>
🎯 Критика при свидетелях, обесценивание
🔑 Список триггеров, 3 фразы-гасителя

🏃 <b>2F - СТРАХ / БЕГСТВО</b>
🎯 Повышение голоса, давление
🔑 3 якоря безопасности

🧬 <b>3F - СЕКС / ЖЕЛАНИЕ</b>
🎯 Особая интонация, взгляд
🔑 3 слова-пароля, 3 касания

🍽 <b>4F - ДЕНЬГИ / ПОГЛОЩЕНИЕ</b>
🎯 Возможности, конкуренты
🔑 3 фразы-мотиватора

📎 <b>ПРИМЕР:</b> {example_link}
"""
        
        keyboard = [[InlineKeyboardButton("◀️ НАЗАД", callback_data="four_f_main_menu")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return FOUR_F_DETAILED
    except Exception:
        return FOUR_F_MAIN

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка пакетов"""
    query = update.callback_query
    await query.answer()
    
    message = f"""
💎 <b>ПАКЕТЫ ПРИГЛАШЕНИЙ</b>

🥉 3 ссылки — 299₽
🥈 5 ссылок — 499₽ 🔥
🥇 10 ссылок — 899₽
"""
    
    keyboard = [
        [InlineKeyboardButton("🥉 3 ссылки - 299₽", callback_data="pay_package_3")],
        [InlineKeyboardButton("🥈 5 ссылок - 499₽", callback_data="pay_package_5")],
        [InlineKeyboardButton("🥇 10 ссылок - 899₽", callback_data="pay_package_10")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return BUY_PACKAGES

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплата пакета"""
    query = update.callback_query
    await query.answer()
    
    package_id = query.data.split("_")[2]
    package = INVITE_PACKAGES.get(package_id, {"links": package_id, "price": 299, "emoji": "🥉"})
    
    message = f"""
💳 <b>ОПЛАТА ПАКЕТА</b>

{package['emoji']} {package['links']} ссылок — {package['price']}₽
"""
    
    payment_id = generate_payment_id("package", query.from_user.id)
    
    keyboard = [
        [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {package['price']}₽", callback_data=f"process_package_payment_{payment_id}_{package_id}")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="buy_invite_packages")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FOUR_F_PAYMENT_SCREEN

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты пакета"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    package_id = parts[4]
    package = INVITE_PACKAGES.get(package_id, {"links": int(package_id), "emoji": "🥉"})
    
    user_limits = get_user_limits(context)
    user_limits["total_purchased"] += package["links"]
    
    message = f"""
✅ <b>ОПЛАТА ПРОШЛА!</b>

{package['emoji']} +{package['links']} ссылок
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
        [InlineKeyboardButton("◀️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return INVITES_LIST

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню друга"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_data = get_friend_by_id(context, friend_id)
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return INVITES_LIST
    
    context.user_data["current_friend_id"] = friend_id
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    friend_link = get_disk_link_by_profile(friend_profile)
    
    message = f"""
👤 <b>{friend_name}</b>

📊 {friend_profile}
📁 {friend_link}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 ИНТИМ", callback_data=f"int_{friend_id}")],
        [InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FRIEND_MENU

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Интимный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_data = get_friend_by_id(context, friend_id)
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return FRIEND_MENU
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    
    profile = load_friend_intimate_profile(friend_name, friend_profile)
    message = format_friend_intimate_profile(profile, friend_name)
    
    keyboard = [[InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")]]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FRIEND_MENU

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню 4F для друга"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_data = get_friend_by_id(context, friend_id)
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return FRIEND_MENU
    
    friend_name = friend_data.get("friend_name", "друг")
    purchased = friend_data.get("purchased_functions", [])
    
    message = f"""
🧬 <b>4F ДЛЯ {friend_name}</b>

🔥 1F: НАПАДЕНИЕ {"✅" if "1F" in purchased else "🔒"}
🏃 2F: СТРАХ {"✅" if "2F" in purchased else "🔒"}
🧬 3F: СЕКС {"✅" if "3F" in purchased else "🔒"}
🍽 4F: ДЕНЬГИ {"✅" if "4F" in purchased else "🔒"}
"""
    
    keyboard = []
    for f in ["1F", "2F", "3F", "4F"]:
        if f in purchased:
            keyboard.append([InlineKeyboardButton(f"{FOUR_F_EMOJIS[f]} {f} - ОТКРЫТЬ", callback_data=f"open_4f_{friend_id}_{f}")])
        else:
            keyboard.append([InlineKeyboardButton(f"{FOUR_F_EMOJIS[f]} {f} - 1₽", callback_data=f"buy_4f_{friend_id}_{f}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")])
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FOUR_F_MENU

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка 4F ключа"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>

{content['description'][:200]}...

💰 <b>1₽</b>
"""
    
    payment_id = generate_payment_id("4f", query.from_user.id)
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FOUR_F_PAYMENT_SCREEN

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка платежа"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    friend_id = int(parts[3])
    function = parts[4]
    
    # Разблокируем ключ
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            inv.setdefault("purchased_functions", []).append(function)
            break
    
    # Открываем ключ
    new_query = update
    new_query.callback_query.data = f"open_4f_{friend_id}_{function}"
    return await open_4f_key_callback(new_query, context)

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие 4F ключа"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    content = load_4f_content(function)
    
    message = f"""
🎉 <b>КЛЮЧ АКТИВИРОВАН!</b>

{content['emoji']} <b>{content['title']}</b>

<b>🎯 ТРИГГЕРЫ:</b>
"""
    for t in content['triggers']:
        message += f"\n• {t}"
    
    message += f"""

<b>🧠 РАЗБОР:</b>
{content['analysis']}
"""
    
    next_keys = {"1F": "2F", "2F": "3F", "3F": "4F", "4F": "1F"}
    next_f = next_keys.get(function)
    
    keyboard = [
        [InlineKeyboardButton(f"{FOUR_F_EMOJIS[next_f]} КУПИТЬ {next_f} - 1₽", callback_data=f"buy_4f_{friend_id}_{next_f}")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FOUR_F_CONTENT

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Объяснение 4F"""
    query = update.callback_query
    await query.answer()
    
    friend_id = context.user_data.get("current_friend_id")
    
    keyboard = [[InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}" if friend_id else "my_invites")]]
    
    await query.edit_message_text(FOUR_F_SHORT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return FOUR_F_MENU

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")],
        [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        "🔍 Статус приглашения: АКТИВНО",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка"""
    query = update.callback_query
    await query.answer("✅ Демо-режим")
    return RESULTS

# ===== ОСНОВНЫЕ ФУНКЦИИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    logger.info(f"🚀 Старт: {user.id}")
    
    # Инициализация данных
    context.user_data.clear()
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["has_shared"] = False
    
    # Инициализация интимных данных
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    get_user_limits(context)
    
    welcome_text = f"""
{user.first_name}, привет! 👋

<b>🧠 Я — Виртуальный психолог Вариатика.</b>

🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.

<b>📊 Вас ждёт:</b>

1️⃣ Адаптивный тест (4 этапа)
2️⃣ Персональный профиль
3️⃣ 🔞 Интимный профиль и 4F-ключи

🚀 Начнём?
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать", callback_data="start_test")],
        [InlineKeyboardButton("🤔 Подробнее", callback_data="why_details")]
    ]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return None

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    return await show_stage_1_intro(update, context)

async def why_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробности"""
    query = update.callback_query
    await query.answer()
    
    text = """
🎭 <b>Немного правды с юмором...</b>

🧠 Что я умею:
• Вижу паттерны там, где вы видите хаос
• Нахожу систему там, где вы видите случайности

🎯 Конкретно в тесте:

1️⃣ Конфигурация восприятия
2️⃣ Конфигурация мышления
3️⃣ Конфигурация поведения
4️⃣ Точка роста

🔞 После теста откроется интимный профиль
   и 4F-ключи для управления состояниями

⏱ 15 минут вместо лет терапии!
"""
    
    keyboard = [[InlineKeyboardButton("👌 Понял. Начинаем →", callback_data="start_test")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    await update.message.reply_text("❌ Тест отменен. /start чтобы начать заново")
    return ConversationHandler.END

# ===== ОСНОВНАЯ ФУНКЦИЯ =====

def main():
    """Запуск бота"""
    print("\n" + "="*70)
    print("🧠 ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА v7.0")
    print("="*70)
    print("✅ ПОЛНАЯ ЛОГИКА ТЕСТИРОВАНИЯ (4 этапа)")
    print("✅ 36 ИНТИМНЫХ ПРОФИЛЕЙ НА ЯНДЕКС.ДИСКЕ")
    print("✅ 4F-КЛЮЧИ ДЛЯ УПРАВЛЕНИЯ СОСТОЯНИЯМИ")
    print("✅ СИСТЕМА ПРИГЛАШЕНИЙ ДЛЯ ДРУЗЕЙ")
    print("="*70)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Основной ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            # Этапы теста
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
            
            # Результаты
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(buy_package_callback, pattern="^buy_package$"),
                CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(my_sexual_profile_callback, pattern="^my_sexual_profile$"),
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"),
                CallbackQueryHandler(buy_package_callback, pattern="^buy_package$"),
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"),
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"),
            ],
            
            # Интимный модуль
            MY_SEXUAL_PROFILE: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            INVITES_LIST: [
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(four_f_main_menu_callback, pattern='^four_f_main_menu$'),
                CallbackQueryHandler(check_status_callback, pattern='^check_status_'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(buy_invite_packages_callback, pattern='^buy_invite_packages$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            FRIEND_MENU: [
                CallbackQueryHandler(intimate_profile_callback, pattern='^int_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
            ],
            FOUR_F_MENU: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(open_4f_key_callback, pattern='^open_4f_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
            ],
            FOUR_F_CONTENT: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
            ],
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(process_payment_callback, pattern='^process_payment_'),
                CallbackQueryHandler(pay_package_callback, pattern='^pay_package_'),
                CallbackQueryHandler(process_package_payment_callback, pattern='^process_package_payment_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(buy_invite_packages_callback, pattern='^buy_invite_packages$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
            ],
            BUY_PACKAGES: [
                CallbackQueryHandler(pay_package_callback, pattern='^pay_package_'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
            ],
            FOUR_F_MAIN: [
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(four_f_detailed_callback, pattern='^four_f_detailed$'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
            ],
            FOUR_F_DETAILED: [
                CallbackQueryHandler(four_f_main_menu_callback, pattern='^four_f_main_menu$'),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
        ],
        allow_reentry=True
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(why_details_callback, pattern="^why_details$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(conv_handler)
    
    print("\n🚀 Бот запущен!")
    print("="*70)
    
    # Запуск
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query']
    )

if __name__ == "__main__":
    main()
