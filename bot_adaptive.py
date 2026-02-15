#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА + 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
ВЕРСИЯ 6.0: ПОЛНАЯ ИНТЕГРАЦИЯ
✅ Психологический тест (4 этапа) - версия 5.4
✅ 18+ интимные профили с приглашениями - версия 19.0
✅ 4F-ключи (1F,2F,3F,4F) для друзей
✅ Платежная система ЮKassa
✅ Интеграция с Яндекс.Диск (36 профилей)
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
import requests
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Conflict, BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("bot_detailed.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Функция для логирования входящих callback
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
    print(f"🔍 {log_msg}")

# ===== ИМПОРТ КОНСТАНТ СОСТОЯНИЙ =====
try:
    from constants import (
        STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS,
        GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, PAYMENT_SCREEN,
        MY_SEXUAL_PROFILE, SEXUAL_PROFILE_SCREEN, SEXUAL_INVITES_LIST,
        SEXUAL_FRIEND_PROFILE, FOUR_F_PAYMENT_SCREEN, FOUR_F_CONTENT_SCREEN,
        FOUR_F_MAIN, FOUR_F_DETAILED, FOUR_F_MENU, FOUR_F_CONTENT,
        BUY_PACKAGES, INVITES_LIST, FRIEND_MENU,
    )
    logger.info("✅ Константы успешно импортированы из constants.py")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта из constants.py: {e}")
    # Заглушки на случай ошибки импорта
    STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS = range(6)
    GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, PAYMENT_SCREEN = range(6, 10)
    MY_SEXUAL_PROFILE, SEXUAL_PROFILE_SCREEN, SEXUAL_INVITES_LIST, SEXUAL_FRIEND_PROFILE = range(10, 14)
    FOUR_F_PAYMENT_SCREEN, FOUR_F_CONTENT_SCREEN, FOUR_F_MAIN, FOUR_F_DETAILED = range(14, 18)
    FOUR_F_MENU, FOUR_F_CONTENT, BUY_PACKAGES, INVITES_LIST, FRIEND_MENU = range(18, 23)
    logger.warning("⚠️ Используются запасные значения констант")

# ===== ИМПОРТ КОНФИГУРАЦИИ =====
try:
    from config import (
        TOKEN, API_URL, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY,
        TELEGRAM_BOT_URL, BOT_LINK, AUTHOR_LINK, GIFT_PDF_LINK, SHARE_TEXT,
        GIFT_SCREEN_TEXT, STANDARD_SUFFIXES, CONFLICT_PHRASES, SUFFIX_TO_DILTS,
        EMERGENCY_PROFILES, LEVEL_DIFFS, PROFILE_LINKS, DEFAULT_PROFILE,
    )
    logger.info("✅ Конфигурация успешно импортирована из config.py")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта из config.py: {e}")
    # Заглушки
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
    API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
    YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "ваш_shop_id")
    YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "ваш_secret_key")
    BOT_USERNAME = "Testing_Lichnosti_bot"
    BOT_LINK = f"t.me/{BOT_USERNAME}"
    GIFT_PDF_LINK = "https://disk.yandex.ru/i/8KD0DGy4AbpDYA"
    AUTHOR_TELEGRAM = "https://t.me/meysternlp"
    SHARE_TEXT = "🔮 Хочешь узнать, что на самом деле движет тобой? Этот тест видит то, что обычно скрыто. За 15 минут узнаешь свой реальный психологический профиль. Рекомендую 👇"
    logger.warning("⚠️ Используются запасные значения конфигурации")

# ===== УМНЫЙ ПОИСК КОРНЯ ПРОЕКТА =====
def find_project_root() -> str:
    """Находит корень проекта (где лежит папка profiles/)"""
    try:
        current = os.path.dirname(os.path.abspath(__file__))
        
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, "profiles")):
                logger.info(f"✅ Корень проекта найден: {current}")
                return current
            current = os.path.dirname(current)
        
        root = os.path.dirname(os.path.abspath(__file__))
        logger.warning(f"⚠️ Папка profiles не найдена, используем: {root}")
        return root
    except Exception as e:
        logger.error(f"❌ Ошибка поиска корня проекта: {e}")
        return os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = find_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

logger.info(f"📁 Корень проекта: {PROJECT_ROOT}")

# ===== ИМПОРТ ВОПРОСОВ =====
try:
    from questions import (
        PERCEPTION_TYPES, CLARIFICATION_QUESTIONS,
        STAGE1_FEEDBACK, STAGE2_FEEDBACK, STAGE3_FEEDBACK, STAGE4_ANALYSIS_SCREEN
    )
    logger.info("✅ Вопросы успешно импортированы из questions.py")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта из questions.py: {e}")
    # Заглушки
    PERCEPTION_TYPES = {}
    CLARIFICATION_QUESTIONS = {}
    logger.warning("⚠️ Используются пустые заглушки для вопросов")

# ===== ИМПОРТ ОБРАБОТЧИКОВ ТЕСТА =====
try:
    from handlers import (
        show_stage_1_intro, show_stage_1_details, back_to_stage1_intro,
        start_stage_1, ask_stage_1_question, handle_stage_1_answer, finish_stage_1,
        
        show_stage_2_intro, show_stage_2_details, back_to_stage2_intro,
        start_stage_2, ask_stage_2_question, handle_stage_2_answer, finish_stage_2,
        
        show_stage_3_intro, show_stage_3_details, back_to_stage3_intro,
        start_stage_3, ask_stage_3_question, handle_stage_3_answer, finish_stage_3,
        
        show_stage_4_intro, show_stage_4_details, back_to_stage4_intro,
        start_stage_4, ask_stage_4_question, handle_stage_4_answer, finish_stage_4,
    )
    from handlers.common import ask_clarification_question, handle_clarification_answer
    logger.info("✅ Обработчики теста успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта обработчиков теста: {e}")
    # Заглушки-заглушки
    async def dummy_handler(update, context): return
    show_stage_1_intro = show_stage_2_intro = show_stage_3_intro = show_stage_4_intro = dummy_handler
    start_stage_1 = start_stage_2 = start_stage_3 = start_stage_4 = dummy_handler
    handle_stage_1_answer = handle_stage_2_answer = handle_stage_3_answer = handle_stage_4_answer = dummy_handler
    ask_clarification_question = handle_clarification_answer = dummy_handler
    logger.warning("⚠️ Используются заглушки для обработчиков теста")

# ===== ИМПОРТ УТИЛИТ =====
try:
    from utils.calculations import (
        determine_perception_type, get_type_code, get_level_name, get_dilts_code,
        determine_dilts_level, get_level_group, calculate_thinking_level_by_scores,
        calculate_final_level, check_profile_coherence, calculate_profile_final
    )
    from utils.validators import (
        need_clarification_stage1, need_clarification_stage2,
        need_clarification_stage3, need_clarification_stage4
    )
    from utils.helpers import calculate_progress
    logger.info("✅ Утилиты успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта утилит: {e}")
    # Заглушки
    def calculate_profile_final(data): return {"type_code": "SA", "level": 5, "dilts_code": "int", "display_name": "SA-5_INT"}
    logger.warning("⚠️ Используются заглушки для утилит")

# ===== ИМПОРТ ЗАГРУЗЧИКА ПРОФИЛЕЙ =====
try:
    from loader import loader
    from base import VariaticaProfile
    logger.info("✅ Загрузчик профилей успешно импортирован")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта загрузчика профилей: {e}")
    # Заглушки
    class VariaticaProfile: pass
    loader = None
    logger.warning("⚠️ Загрузчик профилей не доступен")

# ===== КОНСТАНТЫ 18+ МОДУЛЯ =====
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

# ===== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ПО УМОЛЧАНИЮ =====
USER_PROFILE = {
    "display_name": "SA-5_INT",
    "type_code": "SA",
    "level": 5,
    "dilts_code": "int"
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

USER_DISK_LINK = PROFILE_DISK_LINKS["SA-5_INT"]
EXAMPLE_DISK_LINK = PROFILE_DISK_LINKS["SA-3_CON"]

def get_disk_link_by_profile(profile_code: str) -> str:
    """
    Умная функция поиска ссылки на Яндекс.Диск по коду профиля
    Поддерживает разные форматы: SA-5_INT, SA_5_INT, sa-5-int и т.д.
    """
    if not profile_code:
        logger.warning("⚠️ profile_code пустой, использую default")
        return PROFILE_DISK_LINKS["default"]
    
    profile_upper = profile_code.upper().strip()
    logger.debug(f"🔍 Поиск ссылки для профиля: {profile_upper}")
    
    if profile_upper in PROFILE_DISK_LINKS:
        logger.debug(f"✅ Прямое совпадение: {profile_upper}")
        return PROFILE_DISK_LINKS[profile_upper]
    
    profile_with_hyphen = profile_upper.replace('_', '-')
    if profile_with_hyphen in PROFILE_DISK_LINKS:
        logger.debug(f"✅ После замены _ на -: {profile_with_hyphen}")
        return PROFILE_DISK_LINKS[profile_with_hyphen]
    
    profile_with_underscore = profile_upper.replace('-', '_')
    if profile_with_underscore in PROFILE_DISK_LINKS:
        logger.debug(f"✅ После замены - на _: {profile_with_underscore}")
        return PROFILE_DISK_LINKS[profile_with_underscore]
    
    for key in PROFILE_DISK_LINKS:
        if key.startswith(profile_upper[:5]):
            logger.debug(f"✅ Найдено по начальным символам: {key}")
            return PROFILE_DISK_LINKS[key]
    
    logger.warning(f"⚠️ Профиль {profile_code} не найден, использую default")
    return PROFILE_DISK_LINKS["default"]

get_disk_link = get_disk_link_by_profile

# ===== 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ",
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

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

FOUR_F_DETAILED_TEXT = f"""
🔥 <b>1F - ЯРОСТЬ / НАПАДЕНИЕ</b>
<i>Стимулы, запускающие агрессию</i>

😤 СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЯРОСТЬ

Его агрессия не возникает из ниоткуда.
Это реакция на конкретные ТРИГГЕРЫ.

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Критика при свидетелях
   • Обесценивание его усилий
   • Игнорирование границ
   • Определенные интонации

🔑 ЧТО ДАЁТ КЛЮЧ:
   • Список его личных триггеров
   • 3 фразы-гасителя
   • Технику «Торможение»
────────────────────
🏃 <b>2F - СТРАХ / БЕГСТВО</b>
<i>Стимулы, запускающие избегание</i>

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования

🔑 ЧТО ДАЁТ КЛЮЧ:
   • 3 якоря безопасности
   • Технику «Безопасная среда»
────────────────────
🧬 <b>3F - СЕКС / ЖЕЛАНИЕ</b>
<i>Стимулы, запускающие влечение</i>

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Особая интонация
   • Зрительный контакт
   • Неожиданные касания

🔑 ЧТО ДАЁТ КЛЮЧ:
   • 3 слова-пароля
   • 3 касания-ключа
   • Эротический сценарий
────────────────────
🍽 <b>4F - ДЕНЬГИ / ПОГЛОЩЕНИЕ</b>
<i>Стимулы, запускающие режим заработка</i>

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка

🔑 ЧТО ДАЁТ КЛЮЧ:
   • 3 фразы-мотиватора
   • Технику просьбы
   • Сценарий «Топливо»
────────────────────
📎 <b>ПРИМЕР ОПИСАНИЯ И ФОРМАТ КЛЮЧЕЙ:</b>
{EXAMPLE_DISK_LINK}

📌 <b>Ключи предоставляются по запросу</b> с указанием:
   • Профиля человека (из раздела «МОИ ОТРАЖЕНИЯ» — тех, кто посмотрелся в ваше зеркало)
   • Номера ключа (1F, 2F, 3F, 4F)
"""

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С БД ЧЕРЕЗ API =====
def save_invite_to_api(invite_data: dict) -> bool:
    """Сохраняет приглашение в БД через API"""
    try:
        api_data = {
            "invite_id": invite_data['invite_id'],
            "buyer_id": invite_data['user_id'],
            "target_id": 0,
            "target_name": None,
            "target_profile_key": invite_data['profile_code']
        }
        
        response = requests.post(
            f"{API_URL}/api/sexual/create-invite",
            json=api_data,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Приглашение {invite_data['invite_id']} сохранено в БД")
            return True
        else:
            logger.error(f"❌ Ошибка сохранения приглашения: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в БД: {e}")
        return False

def find_invite_in_api(invite_id: str) -> Optional[dict]:
    """Находит приглашение в БД по коду"""
    try:
        response = requests.get(
            f"{API_URL}/api/sexual/get-invite/{invite_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Приглашение {invite_id} найдено в БД")
            return data.get('data', {})
        else:
            logger.warning(f"⚠️ Приглашение {invite_id} не найдено в БД")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка поиска приглашения: {e}")
        return None

def update_invite_in_api(invite_id: str, friend_data: dict) -> bool:
    """Обновляет приглашение после прохождения теста"""
    try:
        response = requests.post(
            f"{API_URL}/api/sexual/update-invite/{invite_id}",
            json=friend_data,
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Приглашение {invite_id} обновлено в БД")
            return True
        else:
            logger.error(f"❌ Ошибка обновления приглашения: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении в БД: {e}")
        return False

def get_user_invites_from_api(user_id: int) -> list:
    """Получает все приглашения пользователя из БД"""
    try:
        response = requests.get(
            f"{API_URL}/api/sexual/get-invites/{user_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            invites = data.get('invites', [])
            logger.info(f"✅ Получено {len(invites)} приглашений для пользователя {user_id}")
            return invites
        else:
            logger.warning(f"⚠️ Не удалось получить приглашения: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения приглашений: {e}")
        return []

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ (временное, для обратной совместимости) =====
user_invites = {}

def get_user_invites(user_id: int) -> list:
    """Получает список приглашений пользователя (сначала из БД, потом из памяти)"""
    db_invites = get_user_invites_from_api(user_id)
    if db_invites:
        return db_invites
    
    if user_id not in user_invites:
        user_invites[user_id] = []
        logger.info(f"👤 Создано хранилище в памяти для пользователя {user_id}")
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    invites = get_user_invites(user_id)
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

def init_test_data(user_id: int):
    """Инициализирует тестовые данные для нового пользователя"""
    try:
        invites = get_user_invites(user_id)
        if len(invites) > 0:
            logger.info(f"👤 У пользователя {user_id} уже есть данные, пропускаем инициализацию")
            return
        
        current_time = datetime.now().timestamp()
        
        test_friends = [
            {
                "invite_id": f"test_free_1_{user_id}",
                "friend_id": 1001,
                "friend_name": "@alex",
                "friend_username": "alex",
                "friend_profile": "SA-3_CON",
                "status": "used",
                "access_status": "free",
                "access_paid": False,
                "created_at": current_time,
                "used_at": current_time,
                "purchased_functions": [],
                "is_free": True,
                "invite_type": "🆓"
            },
            {
                "invite_id": f"test_free_2_{user_id}",
                "friend_id": 1002,
                "friend_name": "@maria",
                "friend_username": "maria",
                "friend_profile": "IP-5_INT",
                "status": "used",
                "access_status": "free",
                "access_paid": False,
                "created_at": current_time - 86400,
                "used_at": current_time - 86400,
                "purchased_functions": ["1F"],
                "is_free": True,
                "invite_type": "🆓"
            }
        ]
        
        invites.extend(test_friends)
        logger.info(f"✅ Инициализированы тестовые данные для user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации тестовых данных: {e}")

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_user_limits(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("invite_limits", {
        "free_used": 0,
        "total_purchased": 0,
        "paid_packages": []
    })

def can_create_invite(user_limits: dict, total_invites: int) -> tuple:
    free_used = user_limits["free_used"]
    
    if free_used < FREE_INVITE_LIMIT:
        remaining = FREE_INVITE_LIMIT - free_used
        return True, True, f"Осталось бесплатных: {remaining}"
    
    paid_available = user_limits["total_purchased"] - (total_invites - FREE_INVITE_LIMIT)
    if paid_available > 0:
        return True, False, f"Осталось платных: {paid_available}"
    
    return False, False, "Лимит исчерпан. Купите пакет ссылок."

def get_friend_by_id(context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> Optional[dict]:
    invites = context.user_data.get("sexual_invites", [])
    return next((inv for inv in invites if inv.get("friend_id") == friend_id), None)

# ===== ФУНКЦИИ ДЛЯ РАЗБИЕНИЯ ДЛИННЫХ СООБЩЕНИЙ =====
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

# ===== БЕЗОПАСНАЯ ОТПРАВКА СООБЩЕНИЙ =====
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
                    logger.debug(f"✅ Отправлена часть {i+1}/{len(parts)} ({len(part)} символов)")
                    break
                except Exception as e:
                    logger.warning(f"⚠️ Попытка {attempt + 1}/{max_retries} части {i+1} не удалась: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"❌ Не удалось отправить часть {i+1}")
                        return False
            
            if i < len(parts) - 1:
                await asyncio.sleep(0.5)
        
        return True
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в safe_send_message: {e}")
        return False

# ===== ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ =====
def load_intimate_profile(profile_code: str = "SA-5_INT") -> dict:
    """Загружает интимный профиль по коду профиля"""
    try:
        logger.info(f"🔍 ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ для кода: {profile_code}")
        
        code_parts = profile_code.upper().replace('-', '_').split('_')
        profile_type = None
        profile_level = None
        
        if len(code_parts) >= 2:
            profile_type = code_parts[0].lower()
            profile_level = code_parts[1]
            logger.info(f"📊 Извлечены тип={profile_type}, уровень={profile_level}")
        else:
            logger.warning(f"⚠️ Не удалось распарсить код профиля: {profile_code}")
        
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        
        search_dirs = [
            os.path.join(bot_dir, "sexual_18"),
            os.path.join(PROJECT_ROOT, "sexual_18"),
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18"),
            os.path.join("sexual_18"),
            os.path.join("profiles", "sexual_18"),
            "/opt/render/project/src/sexual_18",
            "/opt/render/project/src/profiles/sexual_18",
        ]
        
        if profile_type and profile_level:
            pattern = f"{profile_type}_{profile_level}_"
            logger.info(f"🔍 Ищем любой файл по шаблону: {pattern}*.json")
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    logger.info(f"📁 Проверяем папку: {search_dir}")
                    try:
                        for filename in os.listdir(search_dir):
                            if filename.lower().startswith(pattern) and filename.endswith('.json'):
                                file_path = os.path.join(search_dir, filename)
                                logger.info(f"   ✅ НАЙДЕН! Файл: {filename}")
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                        data['loaded_for_profile'] = profile_code
                                        data['loaded_from_file'] = filename
                                        data['profile_type'] = filename.replace('.json', '').upper()
                                        sections = data.get('sections', {})
                                        logger.info(f"   📊 Секций загружено: {len(sections)}")
                                        return data
                                except Exception as e:
                                    logger.error(f"   ❌ Ошибка чтения файла: {e}")
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка чтения папки: {e}")
        
        target_name = profile_code.lower().replace('-', '_') + '.json'
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                file_path = os.path.join(search_dir, target_name)
                if os.path.exists(file_path):
                    logger.info(f"   ✅ НАЙДЕН точный файл: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data['loaded_for_profile'] = profile_code
                            data['loaded_from_file'] = target_name
                            sections = data.get('sections', {})
                            logger.info(f"   📊 Секций загружено: {len(sections)}")
                            return data
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка чтения файла: {e}")
        
        logger.warning(f"⚠️ Файл для {profile_code} не найден, пробуем default.json")
        
        default_paths = [
            os.path.join(bot_dir, "sexual_18", "default.json"),
            os.path.join(PROJECT_ROOT, "sexual_18", "default.json"),
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "default.json"),
            os.path.join("sexual_18", "default.json"),
            os.path.join("profiles", "sexual_18", "default.json"),
            "/opt/render/project/src/sexual_18/default.json",
            "/opt/render/project/src/profiles/sexual_18/default.json",
        ]
        
        for path in default_paths:
            logger.info(f"   Проверяем default.json: {path}")
            if os.path.exists(path):
                logger.info(f"   ✅ НАЙДЕН default.json: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['loaded_for_profile'] = profile_code
                    data['is_default'] = True
                    logger.info(f"   ⚠️ Использую default.json для профиля {profile_code}")
                    return data
        
        logger.error(f"❌ Не найден ни файл для {profile_code}, ни default.json!")
        return get_emergency_profile(profile_code)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка загрузки: {e}\n{traceback.format_exc()}")
        return get_emergency_profile(profile_code)

def get_emergency_profile(profile_code: str = "SA-5_INT") -> dict:
    """Аварийный интимный профиль"""
    logger.info(f"🆘 СОЗДАН АВАРИЙНЫЙ ПРОФИЛЬ для {profile_code}")
    return {
        "profile_type": profile_code.upper(),
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "role": "Жрец/Жрица сексуальной мистерии",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.\nВы не занимаетесь любовью — вы служите ей.\nИ каждый раз — как в первый. И каждый раз — как в последний.",
        "sections": {},
        "is_emergency": True,
        "loaded_for_profile": profile_code
    }

def load_friend_intimate_profile(friend_name: str, friend_profile: str = None) -> dict:
    """Загружает интимный профиль ДРУГА"""
    try:
        profile_path = None
        possible_paths = [
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
            os.path.join(os.path.dirname(__file__), "profiles", "sexual_18", "sa_5_int.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                profile_path = path
                break
        
        if profile_path:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data["profile_type"] = f"ТЕСТ-{friend_profile or 'SA-5_INT'}"
                data["friend_name"] = friend_name
                data["is_test_profile"] = True
                logger.info(f"✅ Загружен профиль друга: {friend_name}")
                return data
        else:
            logger.warning(f"⚠️ Файл профиля друга не найден, используем аварийный")
            return get_friend_emergency_profile(friend_name)
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки профиля друга: {e}")
        return get_friend_emergency_profile(friend_name)

def get_friend_emergency_profile(friend_name: str) -> dict:
    """Аварийный профиль для друга"""
    return {
        "profile_type": "SA-5_INT (ТЕСТ)",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "quote": f"«{friend_name}, со мной не скучно. Со мной — вкусно.»",
        "description": f"Тестовый интимный профиль для {friend_name}.",
        "sections": {
            "what_turns_on": {
                "title": "🔴 ВКЛЮЧАЕТ",
                "items": [
                    "Долгие прелюдии (тестовые данные)",
                    "Ролевые игры",
                    "Шёпот на ухо",
                    "Визуальный контакт",
                    "Неожиданные касания"
                ]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": [
                    "Спешка",
                    "Отсутствие атмосферы",
                    "Прямолинейность",
                    "Фастфуд-секс"
                ]
            },
            "erogenous_zone": {
                "title": "🔴 ЭРОГЕННАЯ ЗОНА",
                "trigger": "Шея, мочки ушей, внутренняя сторона запястья"
            }
        },
        "is_test_profile": True
    }

def load_friend_standard_profile() -> dict:
    """Загружает стандартный профиль друга"""
    return {
        "archetype": "Автономный стратег",
        "quote": "«Я не ищу одобрения — я ищу эффективность.»",
        "pain": "Вам сложно делегировать. Вы уверены: «Хочешь сделать хорошо — сделай сам».",
        "immediate_tool": "Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.",
        "cta": "Исследуйте баланс между автономией и доверием."
    }

def load_4f_content(function: str) -> dict:
    """Загружает контент для 4F ключа"""
    try:
        base_triggers = {
            "1F": [
                "«Я понимаю, почему ты так реагируешь»",
                "«Ты имеешь полное право злиться»",
                "«Я на твоей стороне»",
                "«Это действительно несправедливо»",
                "«Твои границы — это важно»"
            ],
            "2F": [
                "«Ты не обязан это делать»",
                "«Здесь безопасно»",
                "«Я подожду»",
                "«Ты можешь уйти в любой момент»",
                "«Никакого давления»"
            ],
            "3F": [
                "«Ты такой...» (искренний комплимент)",
                "Взгляд в глаза чуть дольше обычного",
                "«А что ты любишь?»",
                "Случайное касание, которое не прерывают",
                "Шёпот, интимный контекст"
            ],
            "4F": [
                "«Ты можешь заработать на этом»",
                "«Это твой шанс»",
                "«Никто не сделает это лучше тебя»",
                "«Представь, сколько это будет стоить через год»",
                "«Я верю в твою идею»"
            ]
        }
        
        base_analysis = {
            "1F": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита.",
            "2F": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя.",
            "3F": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес.",
            "4F": "Желание заработать — это не про жадность, а про безопасность, статус, свободу."
        }
        
        base_protocol = {
            "1F": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите\n4. Дайте время",
            "2F": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте\n4. Верните контроль",
            "3F": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы\n4. Усиливайте напряжение",
            "4F": "1. Найдите его «голод»\n2. Покажите путь к насыщению\n3. Уберите страхи\n4. Дайте первый шаг"
        }
        
        return {
            "function": function,
            "emoji": FOUR_F_EMOJIS[function],
            "title": FOUR_F_TITLES[function],
            "description": FOUR_F_DESCRIPTIONS[function],
            "triggers": base_triggers[function],
            "analysis": base_analysis[function],
            "protocol": base_protocol[function],
            "is_demo": False
        }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки 4F контента: {e}")
        return {
            "function": function,
            "emoji": "❌",
            "title": "Ошибка загрузки",
            "description": "Произошла ошибка. Пожалуйста, попробуйте позже.",
            "triggers": [],
            "analysis": "",
            "protocol": "",
            "is_demo": True
        }

# ===== ФУНКЦИИ ФОРМАТИРОВАНИЯ ИНТИМНОГО ПРОФИЛЯ =====
def format_intimate_profile_part1(profile_data: dict, user_name: str) -> str:
    """Форматирует ПЕРВУЮ ЧАСТЬ интимного профиля"""
    try:
        profile_code = profile_data.get('loaded_for_profile', profile_data.get('profile_type', 'SA-5_INT'))
        
        message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ</b>
📊 {user_name}, {profile_code}

🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', '')}
"""
        
        sections = profile_data.get('sections', {})
        
        section = sections.get("what_turns_on", {})
        if section:
            title = section.get('title', '')
            message += f"\n\n{title}"
            if 'items' in section:
                for item in section['items']:
                    message += f"\n• {item}"
        
        if profile_data.get('is_emergency'):
            message += f"""

⚠️ <i>Этот профиль загружен в аварийном режиме.
Полная версия будет доступна после создания файла {profile_code.lower().replace('-', '_')}.json</i>
"""
        elif profile_data.get('is_default'):
            message += f"""

⚠️ <i>Используется профиль по умолчанию.
Специальный профиль для {profile_code} находится в разработке.</i>
"""
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования части 1: {e}")
        return "🔞 ИНТИМНЫЙ ПРОФИЛЬ\n\nПроизошла ошибка загрузки."

def format_intimate_profile_part2(profile_data: dict, user_name: str) -> str:
    """Форматирует ВТОРУЮ ЧАСТЬ интимного профиля"""
    try:
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
            elif 'items' in section:
                for item in section['items']:
                    message += f"\n• {item}"
        
        section = sections.get("smells_tastes", {})
        if section:
            title = section.get('title', '')
            message += f"\n\n{title}"
            if 'items' in section:
                for item in section['items']:
                    message += f"\n• {item}"
        
        section = sections.get("sounds", {})
        if section:
            title = section.get('title', '')
            message += f"\n\n{title}"
            if 'items' in section:
                for item in section['items']:
                    message += f"\n• {item}"
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования части 2: {e}")
        return ""

def format_intimate_profile_part3(profile_data: dict, user_name: str) -> str:
    """Форматирует ТРЕТЬЮ ЧАСТЬ интимного профиля (с финальным текстом)"""
    try:
        message = ""
        sections = profile_data.get('sections', {})
        
        remaining_sections = [
            ("dirty_details", "🔞 ГРЯЗНЫЕ ДЕТАЛИ"),
            ("fetishes", "🔗 ФЕТИШИ"),
            ("places", "🏠 МЕСТА"),
            ("morning", "🌅 УТРО ПОСЛЕ"),
            ("secret_desires", "🤫 ТАЙНЫЕ ЖЕЛАНИЯ"),
            ("whispers", "💕 ШЁПОТ НА УХО"),
            ("core", "🎯 САМОЕ ВАЖНОЕ"),
            ("compliments", "💬 КОМПЛИМЕНТЫ"),
            ("tells", "📢 РАССКАЖЕТ"),
            ("remains", "💎 ОСТАНЕТСЯ В НЁМ/НЕЙ")
        ]
        
        for section_key, section_title in remaining_sections:
            section = sections.get(section_key, {})
            if section:
                title = section.get('title', section_title)
                message += f"\n\n{title}"
                
                if 'items' in section:
                    for item in section['items']:
                        message += f"\n• {item}"
                elif 'content' in section:
                    message += f"\n{section['content']}"
                elif 'trigger' in section:
                    message += f"\n{section['trigger']}"
        
        message += f"""

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что 🪞 СВОЁ отражение.
Но у <b>каждого друга</b> — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

<b>⬇️ КАК УВИДЕТЬ ИХ:</b>

<b>1.</b> 🚀 Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
<b>2.</b> 💌 Отправьте ссылку другу
<b>3.</b> 🔓 Друг проходит тест → вам открывается ЕГО профиль, интимные подробности и 4F ключи

<b>💫 Чем больше друзей увидят себя в зеркале —</b>
   <b>тем больше тайн откроется вам.</b>
"""
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования части 3: {e}")
        return "\n\nПроизошла ошибка загрузки."

def format_friend_intimate_profile(profile_data: dict, friend_name: str) -> str:
    """Форматирует интимный профиль ДРУГА"""
    try:
        message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
👤 {friend_name}

📊 Тип: {profile_data.get('profile_type', 'ТЕСТ-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', f'«{friend_name}, со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ЕГО ПРИРОДА:</b>
{profile_data.get('description', f'Тестовый профиль {friend_name}')}
"""
        
        sections = profile_data.get('sections', {})
        section_order = ["what_turns_on", "what_turns_off", "erogenous_zone"]
        
        for section_key in section_order:
            section = sections.get(section_key, {})
            if section:
                title = section.get('title', '')
                message += f"\n\n{title}"
                
                if 'items' in section:
                    for item in section['items']:
                        message += f"\n• {item}"
                elif 'trigger' in section:
                    message += f"\n{section['trigger']}"
        
        message += f"""

{SEXUAL_DIVIDER}

⚠️ ТЕСТОВЫЙ РЕЖИМ

Это демо-профиль на основе SA-5_INT.
В реальном режиме здесь будут персональные данные {friend_name}.

✅ Что появится в боевом режиме:
   • Его реальные триггеры
   • Индивидуальные сценарии
   • Точные эрогенные зоны
   • Секретные желания

💎 Купите полный доступ за {FRIEND_ACCESS_PRICE}₽
"""
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования профиля друга: {e}")
        return f"🔞 ПРОФИЛЬ {friend_name}\n\nПроизошла ошибка загрузки."

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====
def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    try:
        logger.info(f"💰 Создание счета: {payment_id}, сумма: {amount}, пользователь: {user_id}")
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": "https://test.payment.url",
            "amount": amount,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {"success": False, "error": str(e)}

def create_yookassa_invoice_payment(payment_id: str, user_id: int, profile_code: str, amount: float = 690.0, email: str = None) -> dict:
    """Создает платеж через Invoices API ЮKassa"""
    try:
        logger.info(f"📤 Создаю платеж ЮKassa: {payment_id}, профиль: {profile_code}")
        
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            logger.error("❌ YOOKASSA ключи не установлены!")
            return {"success": False, "error": "Платежная система не настроена"}
        
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
            email = f"user_{user_id}@example.com"
        
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
                "is_test": "false"
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
            error_text = response.text[:500] if response.text else "Нет ответа"
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            return {"success": False, "error": f"Ошибка ЮKassa: {response.status_code}", "details": error_text}
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа ЮKassa: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

async def create_payment_advanced(user_id: int, profile_code: str, amount: float = 690.00) -> dict:
    """Создает платеж в БД и ЮKassa"""
    
    timestamp = int(time.time())
    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
    user_suffix = str(user_id)[-6:]
    payment_id = f"prod_{timestamp}_{random_str}_{user_suffix}"
    
    logger.info(f"💳 Создаю платеж: {payment_id}, профиль: {profile_code}, сумма: {amount}")
    
    try:
        db_payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "profile_code": profile_code.upper(),
            "amount": amount,
            "email": f"user_{user_id}@example.com",
            "description": f"Полное описание профиля {profile_code} от виртуального психолога"
        }
        
        logger.debug(f"📤 Отправка запроса в API: {API_URL}/api/create-payment-advanced")
        db_response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=db_payload,
            timeout=10
        )
        
        logger.debug(f"📥 Ответ API: {db_response.status_code}")
        
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
            yookassa_result = create_yookassa_invoice_payment(
                payment_id=payment_id,
                user_id=user_id,
                profile_code=profile_code,
                amount=amount,
                email=f"user_{user_id}@example.com"
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
            error_text = db_response.text[:200] if db_response.text else "Нет ответа"
            logger.error(f"❌ Ошибка БД {db_response.status_code}: {error_text}")
            return {
                "success": False, 
                "error": f"Ошибка API: {db_response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к API: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }

async def check_payment_status_api(payment_id: str) -> dict:
    """Проверяет статус платежа через API"""
    try:
        logger.debug(f"🔍 Проверка статуса платежа: {payment_id}")
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        logger.debug(f"📥 Ответ API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"  Статус: {result.get('status', 'unknown')}")
            return {
                "success": True,
                "status": result.get("status", "unknown"),
                "payment_id": payment_id,
                "data": result
            }
        else:
            logger.error(f"❌ API error: {response.status_code}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Status check error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

async def get_materials_link_api(payment_id: str, user_id: int) -> dict:
    """Получает ссылку на материалы через API"""
    try:
        logger.debug(f"📦 Получение материалов: {payment_id}, user_id={user_id}")
        response = requests.get(
            f"{API_URL}/api/get-materials/{payment_id}",
            params={"user_id": user_id},
            timeout=10
        )
        
        logger.debug(f"📥 Ответ API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.debug(f"✅ Материалы получены: {result.get('profile_code')}")
                return {
                    "success": True,
                    "materials_link": result.get("materials_link"),
                    "profile_code": result.get("profile_code"),
                    "profile_link": result.get("profile_link")
                }
            else:
                logger.error(f"❌ Ошибка API: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        else:
            logger.error(f"❌ API error: {response.status_code}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Materials API error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

# ===== ФУНКЦИИ РАБОТЫ С ПРОФИЛЯМИ =====
class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

def get_profile_fallback(profile_data: dict) -> 'VariaticaProfile':
    """Упрощенная логика поиска профиля"""
    if loader is None:
        raise ProfileNotFoundError("Загрузчик профилей не инициализирован")
    
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    logger.info(f"🔍 ПОИСК ПРОФИЛЯ: type={type_code}, level={level}, dilts={dilts_code}")
    
    search_order = [dilts_code] if dilts_code in STANDARD_SUFFIXES else []
    search_order.extend([s for s in STANDARD_SUFFIXES if s not in search_order])
    
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

def get_discrepancy_note(profile_data: dict, actual_profile_key: str) -> str:
    """Возвращает примечание о конфликте Дилтса"""
    if not actual_profile_key:
        logger.warning("⚠️ get_discrepancy_note: actual_profile_key отсутствует")
        return ""
    
    try:
        key_lower = actual_profile_key.lower()
        logger.info(f"🔍 Поиск суффикса в ключе: {key_lower}")
        
        found_suffix = None
        for suffix in STANDARD_SUFFIXES:
            if f"_{suffix}" in key_lower or key_lower.startswith(f"{suffix}_") or key_lower.endswith(f"_{suffix}") or key_lower == suffix:
                found_suffix = suffix
                logger.info(f"✅ Найден суффикс: {found_suffix}")
                break
        
        if found_suffix:
            dilts_level = SUFFIX_TO_DILTS.get(found_suffix, "ENVIRONMENT")
            conflict_phrase = CONFLICT_PHRASES.get(dilts_level, {})
            note = conflict_phrase.get("note", "")
            
            if note:
                logger.info(f"✅ Сформировано примечание о конфликте: суффикс={found_suffix}, dilts={dilts_level}")
                return f"{note}\n\n"
            else:
                return f"🔥 Примечание: Обнаружено несоответствие в вашем профиле.\n\n"
        
        logger.info(f"❌ Суффикс не найден в ключе: {key_lower}")
        return ""
        
    except Exception as e:
        logger.error(f"❌ Ошибка в get_discrepancy_note: {e}", exc_info=True)
        return ""

def clean_duplicate_headers(text: str, field_type: str) -> str:
    """Убирает заголовки, которые уже есть в тексте профиля"""
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
    """Форматирует заголовок профиля"""
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

def get_card_description_from_profile(profile: 'VariaticaProfile', profile_data: dict) -> dict:
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
# ФУНКЦИИ ТЕСТА - РЕЗУЛЬТАТЫ
# ============================================

async def show_results_screen(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    force_shared_view: bool = False
):
    """ЭКРАН РЕЗУЛЬТАТОВ с 18+ кнопкой"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_callback("show_results_screen", update, context)
    
    has_shared = context.user_data.get("has_shared", False) or force_shared_view
    profile_data = context.user_data.get("profile_data")
    
    logger.debug(f"📊 has_shared={has_shared}, profile_data={'есть' if profile_data else 'нет'}")
    
    if not profile_data:
        logger.debug("🔄 profile_data отсутствует, вычисляем...")
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
        logger.debug(f"✅ profile_data вычислен: {profile_data.get('display_name')}")
    
    try:
        profile = get_profile_fallback(profile_data)
        logger.debug(f"✅ Профиль найден: {profile}")
    except ProfileNotFoundError as e:
        logger.error(f"❌ Профиль не найден: {e}", exc_info=True)
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
    
    actual_profile_key = None
    try:
        if hasattr(profile, 'key'):
            actual_profile_key = profile.key.lower()
            logger.info(f"🔍 Найден ключ профиля: {actual_profile_key}")
            context.user_data["actual_profile_key"] = actual_profile_key
        elif hasattr(profile, 'profile_name'):
            actual_profile_key = profile.profile_name.lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        else:
            actual_profile_key = f"{profile_card.get('type_code', 'sa')}_{profile_card.get('level', 1)}_{profile_card.get('dilts_code', 'def')}".lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        
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
    
    discrepancy_note = ""
    if actual_profile_key:
        discrepancy_note = get_discrepancy_note(profile_data, actual_profile_key)
        logger.info(f"📝 Примечание о конфликте: {'✅ Есть' if discrepancy_note else '❌ Нет'}")
    
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
    
    profile_header = profile_data.get('display_name', f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}")
    raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
    formatted_title = format_profile_title(raw_title, profile_header)
    message_1 += f"<b>{formatted_title}</b>\n\n"
    
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
    
    trigger = profile_card.get('trigger', '')
    if trigger:
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_1 += f"<b>🔍 ЭТО ВЫ, ЕСЛИ...</b>\n\n"
        message_1 += f"{trigger}\n\n"
    
    pain = profile_card.get('pain', '')
    if pain:
        pain_lines = pain.strip().split('\n')
        if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
            pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
        
        if pain.strip():
            message_1 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
            message_1 += f"{pain.strip()}"
    
    if message_1.strip():
        logger.debug(f"📤 Отправка message_1 ({len(message_1)} символов)")
        await query.edit_message_text(message_1.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    message_2 = ""
    
    tool = profile_card.get('immediate_tool', '')
    if tool:
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            message_2 += f"<b>🛠 ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>\n\n"
            message_2 += f"<i>Что можно сделать прямо сейчас:</i>\n\n"
            message_2 += f"{tool.strip()}\n\n"
    
    cta = profile_card.get('cta', '')
    if cta:
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_2 += f"<b>🚀 СЛЕДУЮЩИЕ ШАГИ</b>\n\n"
            message_2 += f"{cta.strip()}\n\n"
    
    message_2 += "\n"
    
    message_2 += (
        f"🧠 <b>ЧТО ДАЛЬШЕ В НАШЕМ ПУТЕШЕСТВИИ?</b>\n\n"
        f"<i>Это только начало вашего пути к самопознанию.</i>\n\n"
    )
    
    if discrepancy_note:
        message_2 += f"{discrepancy_note}"
    
    sexual_button = [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="my_sexual_profile")]
    
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="get_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        logger.debug("🔘 Клавиатура: без подарка (has_shared=False)")
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Получить сказку «Мастер Меча»", callback_data="open_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        logger.debug(f"🔘 Клавиатура: с подарком, GIFT_PDF_LINK={GIFT_PDF_LINK}")
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.debug(f"📤 Отправка message_2 ({len(message_2)} символов) с {len(keyboard)} рядами кнопок")
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"✅ Результаты показаны пользователю {user_id}")
    return RESULTS

# ============================================
# ФУНКЦИИ ТЕСТА - НАВИГАЦИЯ
# ============================================

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    log_callback("back_to_results", update, context)
    query = update.callback_query
    await query.answer("🔄 Возвращаюсь к результатам...")
    
    result = await show_results_screen(update, context, force_shared_view=True)
    logger.info(f"🔄 User {update.effective_user.id}: back_to_results → RESULTS")
    return result

async def back_to_results_after_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам после подарка"""
    log_callback("back_to_results_after_gift", update, context)
    query = update.callback_query
    await query.answer("🔄 Возвращаюсь к результатам...")
    
    result = await show_results_screen(update, context, force_shared_view=True)
    logger.info(f"🎁 User {update.effective_user.id}: back_to_results_after_gift → RESULTS")
    return result

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск шаринга"""
    log_callback("skip_share", update, context)
    query = update.callback_query
    await query.answer("⏩ Продолжаем без репоста")
    
    result = await show_results_screen(update, context, force_shared_view=True)
    logger.info(f"🔄 User {update.effective_user.id}: skip_share → RESULTS")
    return result

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    log_callback("confirm_share", update, context)
    query = update.callback_query
    await query.answer("✅ Спасибо за репост! Ваш бонус готов!")
    
    context.user_data["has_shared"] = True
    logger.info(f"✅ User {update.effective_user.id}: has_shared установлен в True")
    
    logger.info(f"✅ User {update.effective_user.id}: confirm_share → open_gift_screen")
    return await open_gift_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    log_callback("restart_test", update, context)
    query = update.callback_query
    await query.answer("🔄 Перезапускаю тест...")
    
    context.user_data.clear()
    logger.debug(f"🧹 user_data очищена для {update.effective_user.id}")
    
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    user_id = query.from_user.id
    context.user_data["sexual_invites"] = get_user_invites_from_api(user_id)
    
    logger.info(f"User {user_id} перезапустил тест")
    
    return await show_stage_1_intro(update, context)

# ============================================
# ФУНКЦИИ ТЕСТА - ПОДАРКИ И ПАКЕТЫ
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ"""
    log_callback("get_gift_screen", update, context)
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
        [InlineKeyboardButton("🪞 Поделиться зеркалом", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился(ась) — получить подарок", callback_data="confirm_share")],
        [InlineKeyboardButton("Продолжить без этого →", callback_data="skip_share")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    logger.info(f"🪞 Gift screen показан пользователю {update.effective_user.id}")
    return GIFT_SCREEN

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН С ПОДАРКОМ"""
    log_callback("open_gift_screen", update, context)
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.debug(f"🎁 open_gift_screen: user_id={user_id}, has_shared={context.user_data.get('has_shared', False)}")
    logger.debug(f"🎁 GIFT_PDF_LINK: {GIFT_PDF_LINK}")
    
    await query.answer()
    
    if not context.user_data.get("has_shared", False):
        logger.warning(f"❌ Пользователь {user_id} пытается открыть подарок без has_shared")
        await query.answer(
            "❌ Сначала поделитесь зеркалом с друзьями, чтобы получить подарок!", 
            show_alert=True
        )
        return await show_results_screen(update, context, force_shared_view=True)
    
    if not GIFT_PDF_LINK:
        logger.error(f"❌ GIFT_PDF_LINK не установлен для пользователя {user_id}")
        await query.answer(
            "❌ Ссылка на подарок временно недоступна. Пожалуйста, попробуйте позже.",
            show_alert=True
        )
        return await show_results_screen(update, context, force_shared_view=True)
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Открыть сказку «Мастер Меча»", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results_after_gift")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.info(f"🎁 User {user_id} opened gift (has_shared={context.user_data.get('has_shared', False)})")
    
    await query.edit_message_text(
        GIFT_SCREEN_TEXT,
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )
    
    logger.info(f"✅ Gift screen показан пользователю {user_id}")
    return OPEN_GIFT_SCREEN

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНОЕ ОПИСАНИЕ ПРОФИЛЯ"""
    log_callback("show_package_screen", update, context)
    query = update.callback_query
    await query.answer()
    
    profile_data = context.user_data.get("profile_data")
    logger.debug(f"📦 profile_data: {'есть' if profile_data else 'нет'}")
    
    if profile_data:
        profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
        profile_info = f"\n📊 <b>Ваш профиль:</b> <code>{profile_code}</code>\n"
        personal_note = f"\n<i>Это описание будет создано персонально для вас на основе ваших ответов.</i>"
        logger.debug(f"📊 Профиль пользователя: {profile_code}")
    else:
        profile_info = "\n📊 <b>Профиль:</b> будет определен после теста\n"
        personal_note = f"\n<i>После теста я подготовлю персональное описание именно для вас.</i>"
        logger.debug("⚠️ profile_data отсутствует")
    
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
        f"<b>Стоимость:</b> 690 ₽\n\n"
        f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
        f"{personal_note}\n\n"
        f"<b>Это ваше персональное руководство по самопознанию!</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🧠 Получить описание профиля за 690 ₽", callback_data="buy_package")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    logger.info(f"📦 Package screen показан пользователю {update.effective_user.id}")
    return PACKAGE_SCREEN

# ============================================
# ФУНКЦИИ ТЕСТА - ПЛАТЕЖИ
# ============================================

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy для получения описания профиля"""
    user_id = update.effective_user.id
    logger.info(f"💳 buy_command вызван пользователем {user_id}")
    
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        logger.debug(f"💳 profile_data отсутствует для {user_id}, показываем выбор")
        keyboard = [
            [InlineKeyboardButton("🧠 Пройти тест для знакомства", callback_data="start_test")],
            [InlineKeyboardButton("💎 Получить описание без теста", callback_data="buy_without_test")]
        ]
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                f"🧠 *Чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
                f"давайте сначала познакомимся поближе через тест.*\n\n"
                f"💎 *Что вы получите в полном описании профиля:*\n"
                f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
                f"• 🎯 Конкретные паттерны поведения и мышления\n"
                f"• 🚀 Рекомендации по развитию от психолога\n"
                f"• 💡 Практические инструменты для жизни\n\n"
                f"💰 *Стоимость:* 690 рублей\n"
                f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
                f"*Выберите действие:*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"🧠 *Чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
                f"давайте сначала познакомимся поближе через тест.*\n\n"
                f"💎 *Что вы получите в полном описании профиля:*\n"
                f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
                f"• 🎯 Конкретные паттерны поведения и мышления\n"
                f"• 🚀 Рекомендации по развитию от психолога\n"
                f"• 💡 Практические инструменты для жизни\n\n"
                f"💰 *Стоимость:* 690 рублей\n"
                f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
                f"*Выберите действие:*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return PAYMENT_SCREEN
    
    profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    context.user_data["pending_payment_profile"] = profile_code
    logger.info(f"💳 Профиль для оплаты: {profile_code}")
    
    return await show_payment_screen(update, context)

async def buy_without_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка без прохождения теста"""
    log_callback("buy_without_test_callback", update, context)
    query = update.callback_query
    await query.answer("💳 Переход к оплате...")
    
    context.user_data["pending_payment_profile"] = "SA_1_DEF"
    logger.info(f"💳 Покупка без теста, профиль по умолчанию: SA_1_DEF")
    
    return await show_payment_screen(update, context)

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран создания платежа"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"💳 show_payment_screen для пользователя {user_id}")
    
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
            f"💰 *Сумма:* 690 рублей\n\n"
            f"⏳ *Создаю ссылку для оплаты...*",
            parse_mode='Markdown'
        )
    
    logger.debug(f"💳 Вызов create_payment_advanced для {profile_code}")
    payment_result = await create_payment_advanced(user_id, profile_code, 690.00)
    
    if not payment_result.get("success"):
        error_msg = payment_result.get("error", "Неизвестная ошибка")
        details = payment_result.get("details", "")
        
        logger.error(f"❌ Ошибка создания платежа: {error_msg}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="buy_without_test")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
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
        return PAYMENT_SCREEN
    
    payment_id = payment_result["payment_id"]
    confirmation_url = payment_result["confirmation_url"]
    
    logger.info(f"✅ Платеж создан: {payment_id}, confirmation_url получен")
    
    context.user_data["last_payment_id"] = payment_id
    context.user_data["last_payment_profile"] = profile_code
    
    if "payment_data" not in context.user_data:
        context.user_data["payment_data"] = {}
    
    context.user_data["payment_data"][payment_id] = {
        "confirmation_url": confirmation_url,
        "profile_code": profile_code,
        "timestamp": time.time(),
        "user_id": user_id
    }
    
    logger.info(f"💾 Сохранён payment_id {payment_id} с confirmation_url")
    
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
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    message_text = (
        f"✅ *ПЛАТЕЖ СОЗДАН!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *Клиент:* {user_name}\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"📋 *ID платежа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 рублей\n"
        f"{invoice_info}"
        f"\n🔒 *Защита от дублей:* ✅ активна\n"
        f"📊 *Профиль сохранен:* ✅ `{profile_code}`\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты:\n"
        f"1. Вы получите уведомление\n"
        f"2. Ссылка на персональное описание профиля придет автоматически\n"
        f"3. Профиль `{profile_code}` будет сохранен\n\n"
        f"<i>Вы также можете вернуться к результатам теста и продолжить позже.</i>"
    )
    
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
    
    logger.info(f"💳 Экран платежа показан пользователю {user_id}")
    return PAYMENT_SCREEN

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    log_callback("check_payment_callback", update, context)
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    logger.info(f"🔍 Проверка статуса платежа: {payment_id}")
    
    await query.edit_message_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС ПЛАТЕЖА...*\n\n"
        f"📋 *ID:* `{payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    status_result = await check_payment_status_api(payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка проверки статуса: {error_msg}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    status = status_result.get("status", "unknown")
    logger.info(f"📊 Статус платежа {payment_id}: {status}")
    
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания профиля нажмите кнопку ниже:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📥 ПОЛУЧИТЬ ОПИСАНИЕ ПРОФИЛЯ", callback_data=f"get_materials_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты нажмите кнопку ниже:*"
        )
        
        payment_data = context.user_data.get("payment_data", {})
        payment_info = payment_data.get(payment_id, {})
        confirmation_url = payment_info.get("confirmation_url")
        
        if confirmation_url:
            keyboard = [
                [InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=confirmation_url)],
                [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
            ]
        
    else:
        message = (
            f"📊 *СТАТУС ПЛАТЕЖА:* `{status}`\n\n"
            f"📋 *ID:* `{payment_id}`"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PAYMENT_SCREEN

async def get_materials_callback_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов после оплаты"""
    log_callback("get_materials_callback_payment", update, context)
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    user_id = update.effective_user.id
    
    logger.info(f"📦 Получение материалов для платежа {payment_id}, user_id={user_id}")
    
    await query.edit_message_text(
        f"📦 *ПОЛУЧАЮ МАТЕРИАЛЫ...*\n\n"
        f"📋 *ID платежа:* `{payment_id}`\n\n"
        f"⏳ Загружаю ссылки...",
        parse_mode='Markdown'
    )
    
    materials_result = await get_materials_link_api(payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка получения материалов: {error_msg}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"get_materials_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПОЛУЧЕНИИ МАТЕРИАЛОВ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        logger.error(f"❌ Ссылка на материалы не найдена для платежа {payment_id}")
        await query.edit_message_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return PAYMENT_SCREEN
    
    logger.info(f"✅ Материалы получены для профиля {profile_code}")
    
    keyboard = [
        [InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"🎉 Ваше персональное описание профиля успешно подготовлено!\n\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 690 рублей\n\n"
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
    
    return PAYMENT_SCREEN

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials для получения материалов после оплаты"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"📦 materials_command вызван пользователем {user_id}")
    
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        logger.warning(f"📦 У пользователя {user_id} нет активных платежей")
        await update.message.reply_text(
            f"🧠 *У вас нет активных платежей*\n\n"
            f"👤 *{user_name}*, для получения персонального описания профиля необходимо приобрести полный пакет.\n\n"
            f"💎 *Полное описание профиля от виртуального психолога:*\n"
            f"• Стоимость: 690 рублей\n"
            f"• Все способы оплаты (СБП, ЮMoney, карты)\n"
            f"• Мгновенный доступ после оплаты\n"
            f"• Ваше персональное руководство по самопознанию\n\n"
            f"Используйте команду `/buy` для покупки",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"📦 Последний платеж пользователя {user_id}: {last_payment_id}")
    
    await update.message.reply_text(
        f"🔍 *ПОИСК ПЕРСОНАЛЬНОГО ОПИСАНИЯ...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Проверяю доступ...",
        parse_mode='Markdown'
    )
    
    materials_result = await get_materials_link_api(last_payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка получения материалов: {error_msg}")
        
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
        logger.error(f"❌ Ссылка на материалы не найдена для платежа {last_payment_id}")
        await update.message.reply_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{last_payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"✅ Материалы отправлены пользователю {user_id} для профиля {profile_code}")
    
    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)]]
    
    await update.message.reply_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *{user_name}*, вот ваше персональное описание профиля:\n\n"
        f"📋 *ID заказа:* `{last_payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 690 рублей\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status для проверки статуса последнего платежа"""
    user_id = update.effective_user.id
    logger.info(f"📊 status_command вызван пользователем {user_id}")
    
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        logger.warning(f"📊 У пользователя {user_id} нет последнего платежа")
        await update.message.reply_text(
            "📭 *Нет активных платежей*\n\n"
            "У вас нет последних платежей для проверки.\n"
            "Используйте `/buy` для создания нового платежа.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"📊 Проверка статуса платежа {last_payment_id} для пользователя {user_id}")
    
    await update.message.reply_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    status_result = await check_payment_status_api(last_payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка проверки статуса: {error_msg}")
        
        await update.message.reply_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    status = status_result.get("status", "unknown")
    logger.info(f"📊 Статус платежа {last_payment_id}: {status}")
    
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
# ФУНКЦИЯ СТАРТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основная команда /start с поддержкой deep link для 18+"""
    user = update.effective_user
    logger.info(f"🚀 /start вызван пользователем {user.id} (@{user.username})")
    
    # Инициализируем тестовые данные для нового пользователя
    init_test_data(user.id)
    
    # ===== 18+ DEEP LINK =====
    if context.args and context.args[0].startswith("sex_"):
        logger.info(f"🔞 18+ переход по ссылке: {context.args[0]}")
        return await sexual_invite_start(update, context)
    # ===== КОНЕЦ 18+ =====
    
    current_state = context.user_data.get("conversation_state")
    if current_state is not None:
        logger.debug(f"🔄 Сброс состояния пользователя {user.id}")
        await update.message.reply_text("🔄 Начинаем новое исследование...")
        context.user_data.clear()
    
    welcome_text = (
        f"{user.first_name}, привет! 👋\n\n"
        f"<b>🧠 Я — Виртуальный психолог Вариатика.</b>\n\n"
        f"🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.\n"
        f"👁️ Увидите скрытые паттерны, которые управляют вашими решениями.\n\n"
        f"⚡ А главное — узнаете то, о себе знать действительно нужно.\n"
        f"🎯 То, что даст точку опоры для роста.\n\n"
        f"<b>📊 Вас ждёт:</b>\n\n"
        f"1️⃣ Адаптивный тест (4 этапа)\n"
        f"   ↳ Поймёте свой уникальный профиль\n\n"
        f"2️⃣ Персональные материалы\n"
        f"   ↳ Узнаете куда направлять усилия\n\n"
        f"🚀 Начнём исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать исследование →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А зачем это вообще?", callback_data="why_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    logger.info(f"✅ Приветствие отправлено пользователю {user.id}")
    return None

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    log_callback("main_menu_callback", update, context)
    query = update.callback_query
    await query.answer("🏠 Возврат в главное меню...")
    
    try:
        await query.message.delete()
        logger.info(f"✅ User {update.effective_user.id}: Удалено сообщение при main_menu")
    except Exception as e:
        logger.warning(f"⚠️ User {update.effective_user.id}: Не удалось удалить сообщение: {e}")
    
    context.user_data.clear()
    logger.info(f"🧹 User {update.effective_user.id}: user_data полностью очищена")
    
    user = update.effective_user
    
    welcome_text = (
        f"{user.first_name}, привет! 👋\n\n"
        f"🧠 Я — Виртуальный психолог Вариатика.\n\n"
        f"🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.\n"
        f"👁️ Увидите скрытые паттерны, которые управляют вашими решениями.\n\n"
        f"⚡ А главное — узнаете то, о себе знать действительно нужно.\n"
        f"🎯 То, что даст точку опоры для роста.\n\n"
        f"📊 Вас ждёт:\n\n"
        f"1️⃣ Адаптивный тест (4 этапа)\n"
        f"   ↳ Поймёте свой уникальный профиль\n\n"
        f"2️⃣ Персональные материалы\n"
        f"   ↳ Узнаете куда направлять усилия\n\n"
        f"🚀 Начнём исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать исследование →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А зачем это вообще?", callback_data="why_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        reply_markup=reply_markup
    )
    
    logger.info(f"✅ User {update.effective_user.id}: main_menu_callback → ConversationHandler.END")
    return ConversationHandler.END

async def why_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Детали'"""
    log_callback("why_details_callback", update, context)
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

3️⃣ Конфигурация поведения
   ↳ Что делаете 'на автомате'

4️⃣ Точка роста
   ↳ Куда двигаться осознанно

⏱ 15 минут вместо лет терапии!
Потому что в 21 веке даже самопознание должно быть эффективным!"""
    
    keyboard = [[InlineKeyboardButton("👌 Понял(а). Начинаем →", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    log_callback("start_test", update, context)
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
    
    # Инициализируем хранилище приглашений
    user_id = query.from_user.id
    context.user_data["sexual_invites"] = get_user_invites_from_api(user_id)
    
    logger.info(f"User {update.effective_user.id} начал знакомство с психологом")
    
    return await show_stage_1_intro(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    logger.info(f"❌ Тест отменен пользователем {update.effective_user.id}")
    await update.message.reply_text(
        f"🧠 *Исследование отменено.*\n\n"
        f"Если захотите продолжить наше знакомство, просто напишите:\n"
        f"`/start`\n\n"
        f"*Всегда готов помочь,\nВаш виртуальный психолог Вариатика* 🧠",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# ============================================
# ФУНКЦИИ 18+ МОДУЛЯ
# ============================================

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик приглашений для 18+ модуля
    Вызывается при переходе по ссылке с параметром start=sex_
    """
    try:
        user = update.effective_user
        logger.info(f"🔗 Пользователь {user.id} перешел по приглашению в 18+ модуль")
        
        args = context.args
        invite_code = args[0] if args else None
        
        if not invite_code:
            logger.warning("⚠️ Приглашение без кода")
            await update.message.reply_text(
                "❌ Неверная ссылка приглашения.\n"
                "Пожалуйста, попросите друга отправить вам новую ссылку."
            )
            return await show_results_screen(update, context)
        
        # Здесь будет логика обработки приглашения
        await update.message.reply_text(
            f"🔞 Приглашение в 18+ модуль получено!\n\n"
            f"Код приглашения: {invite_code}\n\n"
            f"Функция в разработке."
        )
        
        return await show_results_screen(update, context)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в sexual_invite_start: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке приглашения.")
        return RESULTS

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для копирования текста приглашения
    """
    try:
        query = update.callback_query
        await query.answer()
        
        invite_id = query.data.replace("copy_invite_", "")
        
        invites = context.user_data.get("sexual_invites", [])
        invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return
        
        invite_text = f"{invite.get('message', '')}\n\n{invite.get('link', '')}"
        
        await query.message.reply_text(
            f"📋 <b>Текст для отправки другу:</b>\n\n"
            f"<code>{invite_text}</code>\n\n"
            f"Просто скопируйте и отправьте другу!",
            parse_mode="HTML"
        )
        
        logger.info(f"📋 Пользователь {query.from_user.id} скопировал приглашение {invite_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в copy_invite_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для проверки статуса приглашения
    """
    try:
        query = update.callback_query
        await query.answer()
        
        invite_id = query.data.replace("check_invite_", "")
        
        invites = context.user_data.get("sexual_invites", [])
        invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return
        
        status_text = "🟢 АКТИВНО" if invite.get("status") == "active" else "🔴 ИСПОЛЬЗОВАНО"
        created_date = datetime.fromtimestamp(invite.get("created_at", datetime.now().timestamp())).strftime('%d.%m.%Y %H:%M')
        
        message = f"""
📋 <b>СТАТУС ПРИГЛАШЕНИЯ</b>

🔗 <code>{invite.get('link', '')}</code>
📊 Статус: {status_text}
📅 Создано: {created_date}
"""
        
        if invite.get("status") == "used" and invite.get("friend_name"):
            message += f"\n👤 Использовано: {invite.get('friend_name')}"
        
        await query.message.reply_text(
            message,
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Пользователь {query.from_user.id} проверил статус приглашения {invite_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в check_invite_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль - 3 ЧАСТИ, КНОПКИ НА ЧАСТИ 3"""
    try:
        query = update.callback_query
        logger.debug(f"🔍 ПОЛУЧЕН CALLBACK: {query.data} от пользователя {query.from_user.id}")
        
        await query.answer()
        logger.info(f"👤 Пользователь {query.from_user.id} открыл интимный профиль")
        
        context.user_data["conversation_state"] = MY_SEXUAL_PROFILE
        
        profile_data = context.user_data.get("profile_data")
        if profile_data and 'display_name' in profile_data:
            profile_code = profile_data['display_name']
            logger.info(f"📊 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ИЗ ТЕСТА: {profile_code}")
        else:
            user_profile = context.user_data.get("profile", USER_PROFILE)
            profile_code = user_profile.get('display_name', 'SA-5_INT')
            logger.info(f"📊 ПРОФИЛЬ ПО УМОЛЧАНИЮ: {profile_code}")
        
        user_name = query.from_user.first_name or "Пользователь"
        logger.debug(f"📝 Загружаем интимный профиль для пользователя: {user_name} с кодом {profile_code}")
        
        intimate_data = load_intimate_profile(profile_code)
        
        if intimate_data.get('is_emergency'):
            logger.warning(f"⚠️ ЗАГРУЖЕН АВАРИЙНЫЙ ПРОФИЛЬ для {profile_code}")
        elif intimate_data.get('is_default'):
            logger.warning(f"⚠️ ЗАГРУЖЕН ПРОФИЛЬ ПО УМОЛЧАНИЮ для {profile_code}")
        else:
            logger.info(f"✅ УСПЕШНО ЗАГРУЖЕН ПРОФИЛЬ: {profile_code}")
        
        message_part1 = format_intimate_profile_part1(intimate_data, user_name)
        message_part2 = format_intimate_profile_part2(intimate_data, user_name)
        message_part3 = format_intimate_profile_part3(intimate_data, user_name)
        
        logger.debug(f"📄 Длина части 1: {len(message_part1)} символов")
        logger.debug(f"📄 Длина части 2: {len(message_part2)} символов")
        logger.debug(f"📄 Длина части 3: {len(message_part3)} символов")
        
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ-ПРИГЛАШЕНИЕ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 ПОСМОТРЕТЬ МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ НАЗАД В ПРОФИЛЬ", callback_data="back_to_results")]
        ]
        navigation_keyboard = InlineKeyboardMarkup(keyboard)
        
        chat_id = query.message.chat_id
        
        logger.debug("✉️ Отправляем часть 1...")
        try:
            await query.edit_message_text(
                message_part1,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при редактировании сообщения: {e}")
            await safe_send_message(chat_id, message_part1, context)
        
        await asyncio.sleep(1)
        
        if message_part2.strip():
            logger.debug("✉️ Отправляем часть 2...")
            await safe_send_message(chat_id, message_part2, context)
            await asyncio.sleep(1)
        
        if message_part3.strip():
            logger.debug("✉️ Отправляем часть 3 с кнопками...")
            
            parts = split_long_message(message_part3)
            
            for i, part in enumerate(parts):
                current_markup = navigation_keyboard if i == len(parts) - 1 else None
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    reply_markup=current_markup,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                logger.debug(f"✅ Отправлена подчасть 3.{i+1}/{len(parts)}")
                
                if i < len(parts) - 1:
                    await asyncio.sleep(0.5)
        
        logger.debug("✅ Все сообщения и кнопки отправлены успешно")
        return MY_SEXUAL_PROFILE
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_sexual_profile_callback: {e}\n{traceback.format_exc()}")
        try:
            chat_id = update.callback_query.message.chat_id
            keyboard = [
                [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
                [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
                [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_to_results")]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text="💎 Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            pass
        return RESULTS

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔗 СОЗДАНИЕ ПРИГЛАШЕНИЯ"""
    logger.info(f"🔗 create_invite_callback ВЫЗВАН! User: {update.effective_user.id}")
    
    try:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        
        logger.info(f"✅ create_invite_callback: пользователь {user_id} успешно вызвал функцию")
        logger.info(f"📊 Данные пользователя: username=@{query.from_user.username}, first_name={query.from_user.first_name}")
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        user_limits = get_user_limits(context)
        invites = context.user_data.get("sexual_invites", [])
        total_invites = len(invites)
        
        logger.info(f"📊 Статистика пользователя {user_id}:")
        logger.info(f"   - Всего приглашений: {total_invites}")
        logger.info(f"   - Лимиты: free_used={user_limits['free_used']}, total_purchased={user_limits['total_purchased']}")
        
        can_create, is_free, limit_message = can_create_invite(user_limits, total_invites)
        
        logger.info(f"   - Может создать: {can_create}, бесплатно: {is_free}")
        logger.info(f"   - Сообщение: {limit_message}")
        
        if not can_create:
            logger.warning(f"❌ Лимит ссылок исчерпан для пользователя {user_id}")
            await query.answer("❌ Лимит ссылок исчерпан!", show_alert=True)
            return await buy_invite_packages_callback(update, context)
        
        profile_data = context.user_data.get("profile_data")
        if profile_data and 'display_name' in profile_data:
            profile_code = profile_data['display_name']
        else:
            user_profile = context.user_data.get("profile", USER_PROFILE)
            profile_code = user_profile.get('display_name', 'SA-5_INT')
        
        logger.info(f"📊 Профиль пользователя для создания ссылки: {profile_code}")
        
        invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
        invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
        
        invite_message = (
            "✨ Есть одна штука.\n"
            "Определяет твой ночной тип личности.\n"
            "У меня — совпало процентов на 90.\n\n"
            "🤫 Интересно, у тебя тоже?"
        )
        
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        invite_type = "🆓" if is_free else "💎"
        
        if is_free:
            user_limits["free_used"] += 1
            logger.info(f"✅ Использован бесплатный лимит. Осталось: {FREE_INVITE_LIMIT - user_limits['free_used']}")
        
        text = f"""
🔞 <b>✨ ВАША ССЫЛКА ГОТОВА! ✨</b>

🔗 <code>{invite_url}</code>

💬 <b>📨 ТЕКСТ СООБЩЕНИЯ:</b>
<blockquote>{invite_message}</blockquote>

{SEXUAL_DIVIDER}
🟢 <b>• АКТИВНО •</b> ожидает отправки
📅 <b>Создано:</b> {current_time}
{SEXUAL_DIVIDER}

🎯 <b>Через 15 минут после теста</b>
   вы увидите его <b>18+ профиль</b>.
"""
        
        remaining_free = max(0, FREE_INVITE_LIMIT - user_limits["free_used"])
        remaining_paid = user_limits["total_purchased"] - (total_invites + 1 - user_limits["free_used"])
        
        if remaining_free > 0:
            text += f"\n🆓 Осталось бесплатных: {remaining_free}"
        if remaining_paid > 0:
            text += f"\n💎 Осталось платных: {remaining_paid}"
        
        invite_data = {
            "invite_id": invite_code,
            "link": invite_url,
            "message": invite_message,
            "profile_code": profile_code,
            "status": "active",
            "created_at": datetime.now().timestamp(),
            "opened_at": None,
            "opened_count": 0,
            "used_by": None,
            "friend_id": None,
            "friend_name": None,
            "friend_profile": None,
            "access_status": None,
            "purchased_functions": [],
            "is_free": is_free,
            "invite_type": invite_type,
            "user_id": user_id
        }
        
        save_success = save_invite_to_api(invite_data)
        logger.info(f"💾 Сохранение в БД: {'успешно' if save_success else 'ошибка'}")
        
        invites.insert(0, invite_data)
        
        global_invites = get_user_invites(user_id)
        if invite_data not in global_invites:
            global_invites.insert(0, invite_data)
        
        logger.info(f"🔗 Пользователь {user_id} создал ссылку: {invite_code} (тип: {invite_type})")
        
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
        
        keyboard = [
            [InlineKeyboardButton("✈️ ОТПРАВИТЬ ДРУГУ", url=share_url)],
            [InlineKeyboardButton("⬅️ НАЗАД В ПРОФИЛЬ", callback_data="my_sexual_profile")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Сообщение с ссылкой отправлено пользователю {user_id}")
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка в create_invite_callback: {e}\n{traceback.format_exc()}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return INVITES_LIST

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 МОИ ОТРАЖЕНИЯ - с правильными ссылками на Яндекс.Диск"""
    try:
        query = update.callback_query
        await query.answer("🔄 Загружаю отражения...")
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        user_id = query.from_user.id
        invites = get_user_invites(user_id)
        context.user_data["sexual_invites"] = invites
        
        used_invites = [inv for inv in invites if inv.get("status") == "used"]
        total_invites = len(invites)
        total_reflections = len(used_invites)
        
        profile_data = context.user_data.get("profile_data")
        if profile_data and 'display_name' in profile_data:
            profile_code = profile_data['display_name']
        else:
            user_profile = context.user_data.get("profile", USER_PROFILE)
            profile_code = user_profile.get('display_name', 'SA-5_INT')

        logger.info(f"📊 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ДЛЯ 18+: {profile_code}")
        
        user_profile_link = get_disk_link_by_profile(profile_code)
        
        message = f"""<b>🪞 МОИ ОТРАЖЕНИЯ</b>
────────────────

<b>📊 СТАТИСТИКА</b>
🪞 Ссылок зеркал: {total_invites}
👥 Посмотрелись в зеркало: {total_reflections}

<b>🪞 МОЁ ОТРАЖЕНИЕ</b>
📌 Профиль: {profile_code}
📁 Диск:
{user_profile_link}
"""

        if used_invites:
            message += f"""
<b>👥 ОТРАЖЕНИЯ ТЕХ КТО ПОСМОТРЕЛСЯ В ВАШЕ ЗЕРКАЛО ({total_reflections})</b>
"""
            for idx, inv in enumerate(used_invites[:5], 1):
                friend_name = inv.get("friend_name", "друг").replace('@', '')
                friend_profile = inv.get("friend_profile", "SA-3_CON")
                
                disk_link = get_disk_link_by_profile(friend_profile)
                
                message += f"""
{idx}. 🆔 <b>{friend_name}</b> • {friend_profile}
   📁 {disk_link}"""
                
                if inv.get("purchased_functions"):
                    key_map = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
                    keys = " ".join(key_map.get(k, k) for k in inv["purchased_functions"])
                    message += f" • {keys}"
            
            if len(used_invites) > 5:
                message += f"\n\n... и ещё {len(used_invites) - 5}"
        else:
            message += f"""
<b>👥 ОТРАЖЕНИЯ ТЕХ КТО ПОСМОТРЕЛСЯ В ВАШЕ ЗЕРКАЛО (0)</b>

🌑 <i>Пока нет отражений</i>

💡 Создайте ссылку в профиле
   и отправьте другу
"""

        message += f"""
────────────────
💫 Каждое отражение — ключ к человеку."""

        keyboard = [
            [InlineKeyboardButton("◀️ К ПРОФИЛЮ", callback_data="my_sexual_profile")],
            [InlineKeyboardButton("🔴 4F КЛЮЧИ 🔴", callback_data="four_f_main_menu")]
        ]

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"🔍 Пользователь {user_id} открыл Мои отражения")
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_invites_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return INVITES_LIST

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 Главное меню 4F-ключей - краткая версия"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MAIN
        logger.info(f"🧬 Пользователь {query.from_user.id} открыл меню 4F")
        
        message = FOUR_F_SHORT
        
        keyboard = [
            [InlineKeyboardButton("📘 ПОДРОБНЕЕ", callback_data="four_f_detailed")],
            [InlineKeyboardButton("🔍 К ОТРАЖЕНИЯМ", callback_data="my_invites")],
            [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="my_sexual_profile")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MAIN
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_main_menu_callback: {e}")
        return INVITES_LIST

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ПОДРОБНОЕ ОПИСАНИЕ 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_DETAILED
        logger.info(f"📘 Пользователь {query.from_user.id} открыл подробное описание 4F")
        
        message = FOUR_F_DETAILED_TEXT
        
        keyboard = [
            [InlineKeyboardButton("🔐 ЗАПРОСИТЬ КЛЮЧИ", url=AUTHOR_TELEGRAM)],
            [InlineKeyboardButton("◀️ К ОБУЧАЙКЕ", callback_data="four_f_main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return FOUR_F_DETAILED
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_detailed_callback: {e}")
        return FOUR_F_MAIN

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        invite_id = query.data.replace("check_status_", "")
        
        invite = find_invite_in_api(invite_id)
        
        if not invite:
            invites = context.user_data.get("sexual_invites", [])
            invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return INVITES_LIST
        
        created_date = datetime.fromtimestamp(invite.get("created_at", datetime.now().timestamp())).strftime('%d.%m.%Y %H:%M')
        invite_type = invite.get("invite_type", "🆓")
        
        message = f"""
🔍 <b>СТАТУС ПРИГЛАШЕНИЯ</b>
{invite_type}

🔗 <code>https://t.me/{BOT_USERNAME}?start={invite_id}</code>

🟢 <b>• АКТИВНО •</b> ждёт друга
📅 <b>Создано:</b> {created_date}

✨ Друг ещё не прошёл тест.
   Напомните ему о себе.
"""
        
        keyboard = [
            [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")],
            [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="my_sexual_profile")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
    except Exception as e:
        logger.error(f"❌ Ошибка в check_status_callback: {e}")
        return INVITES_LIST

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка пакетов приглашений"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = BUY_PACKAGES
        
        message = f"""
💎 <b>ПАКЕТЫ ПРИГЛАШЕНИЙ</b>

<b>🆓 Бесплатные ссылки закончились!</b>
У вас было {FREE_INVITE_LIMIT} бесплатные ссылки, и вы их использовали.

<b>Выберите пакет для продолжения:</b>

"""
        
        for links, data in INVITE_PACKAGES.items():
            popular = " 🔥 ХИТ" if data["popular"] else ""
            price_per_link = data["price"] // data["links"]
            message += f"""
{data['emoji']} <b>{data['links']} ссылок</b> — {data['price']}₽{popular}
   💎 {price_per_link}₽ за ссылку
"""
        
        message += f"""

{SEXUAL_DIVIDER}
✅ После оплаты ссылки добавляются к вашему лимиту
🎁 Чем больше пакет — тем выгоднее!
"""
        
        keyboard = []
        for links, data in INVITE_PACKAGES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{data['emoji']} {data['links']} ССЫЛОК - {data['price']}₽",
                    callback_data=f"pay_package_{links}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("◀️ НАЗАД", callback_data="my_invites")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return BUY_PACKAGES
    except Exception as e:
        logger.error(f"❌ Ошибка в buy_invite_packages_callback: {e}")
        return INVITES_LIST

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплата пакета приглашений"""
    try:
        query = update.callback_query
        await query.answer("💰 Формирую счёт...")
        
        context.user_data["conversation_state"] = FOUR_F_PAYMENT_SCREEN
        
        package_id = query.data.split("_")[2]
        package = INVITE_PACKAGES.get(package_id)
        
        if not package:
            await query.answer("❌ Пакет не найден", show_alert=True)
            return
        
        payment_id = generate_payment_id("package", query.from_user.id)
        
        message = f"""
💳 <b>ОПЛАТА ПАКЕТА</b>

{package['emoji']} <b>Пакет: {package['links']} ссылок</b>
💰 <b>Сумма: {package['price']}₽</b>

✅ После оплаты ссылки будут добавлены к вашему аккаунту
"""
        
        keyboard = [
            [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {package['price']}₽", callback_data=f"process_package_payment_{payment_id}_{package_id}")],
            [InlineKeyboardButton("◀️ НАЗАД", callback_data="buy_invite_packages")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_PAYMENT_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в pay_package_callback: {e}")
        return BUY_PACKAGES

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение оплаты пакета"""
    try:
        query = update.callback_query
        await query.answer("🔄 Проверяю оплату...")
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        parts = query.data.split("_")
        payment_id = parts[3]
        package_id = parts[4]
        
        package = INVITE_PACKAGES.get(package_id)
        
        user_limits = get_user_limits(context)
        user_limits["total_purchased"] += package["links"]
        user_limits["paid_packages"].append({
            "package": package_id,
            "links": package["links"],
            "price": package["price"],
            "payment_id": payment_id,
            "purchased_at": datetime.now().timestamp()
        })
        
        logger.info(f"💰 Пользователь {query.from_user.id} купил пакет {package_id} ({package['links']} ссылок)")
        
        invites = context.user_data.get("sexual_invites", [])
        total_invites = len(invites)
        paid_available = user_limits["total_purchased"] - (total_invites - user_limits["free_used"])
        
        message = f"""
✅ <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>

{package['emoji']} <b>{package['links']} ссылок</b> добавлено
💰 Сумма: {package['price']}₽

💎 <b>Теперь у вас:</b>
   • Бесплатных использовано: {user_limits['free_used']}/{FREE_INVITE_LIMIT}
   • Платных доступно: {paid_available}

🎉 Можете создавать новые приглашения!
"""
        
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("◀️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
    except Exception as e:
        logger.error(f"❌ Ошибка в process_package_payment_callback: {e}")
        return INVITES_LIST

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню профиля друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FRIEND_MENU
        
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return INVITES_LIST
        
        context.user_data["current_friend_id"] = friend_id
        context.user_data["current_friend_data"] = friend_data
        
        friend_name = friend_data.get("friend_name", "друг").replace('@', '')
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        access_status = friend_data.get("access_status", "free")
        free_count = count_free_friends(query.from_user.id)
        inv_type = friend_data.get("invite_type", "🆓")
        
        if access_status == "locked" or (free_count >= FREE_FRIEND_LIMIT and not friend_data.get("access_paid")):
            return await show_payment_access_screen(update, context, friend_data)
        
        purchased = friend_data.get("purchased_functions", [])
        progress = len(purchased)
        progress_bar = "▓" * progress + "░" * (4 - progress)
        
        friend_disk_link = get_disk_link_by_profile(friend_profile)
        
        message = f"""
{inv_type} <b>{friend_name}</b>

📊 {friend_profile}
💎 {'🔓' if access_status == 'free' else '💰'}

🔓 {progress}/4 [{progress_bar}]

📁 <b>ССЫЛКА НА ПРОФИЛЬ:</b>
{friend_disk_link}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 СТАНДАРТ", callback_data=f"std_{friend_id}"),
                InlineKeyboardButton("🔞 ИНТИМ", callback_data=f"int_{friend_id}")
            ],
            [
                InlineKeyboardButton("🧬 4F-КЛЮЧИ", callback_data=f"4f_{friend_id}"),
                InlineKeyboardButton("❓ ЧТО ЭТО?", callback_data="4f_explain")
            ],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return FRIEND_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка в friend_menu_callback: {e}")
        return INVITES_LIST

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
    """Экран оплаты доступа к другу"""
    try:
        query = update.callback_query
        context.user_data["conversation_state"] = FOUR_F_PAYMENT_SCREEN
        
        friend_name = friend_data.get("friend_name", "друг").replace('@', '')
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        free_count = count_free_friends(query.from_user.id)
        
        message = f"""
🔒 <b>{friend_name} ЗАБЛОКИРОВАН</b>

📊 {friend_profile}

⚠️ <b>БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН</b>
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Цена: {FRIEND_ACCESS_PRICE}₽
"""
        
        keyboard = [
            [InlineKeyboardButton(f"🔓 РАЗБЛОКИРОВАТЬ - {FRIEND_ACCESS_PRICE}₽", callback_data=f"pay_access_{friend_data['friend_id']}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_PAYMENT_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в show_payment_access_screen: {e}")
        return INVITES_LIST

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стандартный профиль друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FRIEND_MENU
        
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "друг").replace('@', '') if friend_data else "друг"
        
        profile = load_friend_standard_profile()
        
        message = f"""
📊 <b>{friend_name}</b>

🧠 {profile['archetype']}

💬 {profile['quote']}

💔 {profile['pain']}

🛠 {profile['immediate_tool']}
"""
        
        keyboard = [[InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FRIEND_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка в standard_profile_callback: {e}")
        return FRIEND_MENU

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Интимный профиль друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FRIEND_MENU
        
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FRIEND_MENU
        
        friend_name = friend_data.get("friend_name", "друг").replace('@', '')
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        
        profile_data = load_friend_intimate_profile(friend_name, friend_profile)
        message = format_friend_intimate_profile(profile_data, friend_name)
        
        friend_disk_link = get_disk_link_by_profile(friend_profile)
        message += f"\n\n📁 <b>ССЫЛКА НА ПРОФИЛЬ:</b>\n{friend_disk_link}"
        
        keyboard = [[InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return FRIEND_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка в intimate_profile_callback: {e}")
        return FRIEND_MENU

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню 4F-ключей для друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MENU
        
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return INVITES_LIST
        
        friend_name = friend_data.get("friend_name", "друг").replace('@', '')
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        purchased = friend_data.get("purchased_functions", [])
        
        message = f"""
🧬 <b>4F ДЛЯ {friend_name}</b>

📊 {friend_profile}
"""
        
        for f in ["1F", "2F", "3F", "4F"]:
            emoji = FOUR_F_EMOJIS[f]
            status = "✅" if f in purchased else "🔒"
            message += f"\n{emoji} {FOUR_F_TITLES[f]} {status}"
        
        keyboard = []
        
        for f in ["1F", "2F", "3F", "4F"]:
            emoji = FOUR_F_EMOJIS[f]
            if f in purchased:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji} {f} - ОТКРЫТЬ",
                        callback_data=f"open_4f_{friend_id}_{f}"
                    )
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji} {f} - КУПИТЬ ЗА 1₽",
                        callback_data=f"buy_4f_{friend_id}_{f}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("❓ ЧТО ТАКОЕ 4F?", callback_data="4f_explain"),
            InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_menu_callback: {e}")
        return FRIEND_MENU

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обучение 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MENU
        
        message = FOUR_F_SHORT
        
        keyboard = []
        friend_id = context.user_data.get("current_friend_id")
        
        if friend_id:
            keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")])
        else:
            keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data="my_invites")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_explanation_callback: {e}")
        return FOUR_F_MENU

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка 4F-ключа"""
    try:
        query = update.callback_query
        await query.answer("💰 Создаю счёт...")
        
        context.user_data["conversation_state"] = FOUR_F_PAYMENT_SCREEN
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FOUR_F_MENU
        
        friend_name = friend_data.get("friend_name", "друг").replace('@', '')
        content = load_4f_content(function)
        
        message = f"""
{content['emoji']} <b>{content['title']}</b>
👤 {friend_name}

{content['description']}

💰 <b>1₽</b>
"""
        
        payment_id = generate_payment_id("4f", query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_PAYMENT_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в buy_4f_key_callback: {e}")
        return FOUR_F_MENU

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Процесс оплаты 4F-ключа"""
    try:
        query = update.callback_query
        await query.answer("💳 Подключаюсь...")
        
        parts = query.data.split("_")
        payment_id = parts[2]
        friend_id = int(parts[3])
        function = parts[4]
        
        payment_result = create_yookassa_invoice(
            payment_id=payment_id,
            user_id=query.from_user.id,
            amount=1.0,
            description=f"4F ключ {function}"
        )
        
        if not payment_result.get("success"):
            await query.answer(f"❌ Ошибка", show_alert=True)
            return FOUR_F_PAYMENT_SCREEN
        
        context.user_data["conversation_state"] = FOUR_F_PAYMENT_SCREEN
        
        message = f"""
💳 <b>СЧЁТ СФОРМИРОВАН</b>

🔑 {function}
💰 1₽
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ", url=payment_result["confirmation_url"])],
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=f"check_payment_{payment_id}_{friend_id}_{function}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_PAYMENT_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в process_payment_callback: {e}")
        return FOUR_F_PAYMENT_SCREEN

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытый 4F-ключ"""
    try:
        query = update.callback_query
        await query.answer("🔓 Открываю...")
        
        context.user_data["conversation_state"] = FOUR_F_CONTENT
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        content = load_4f_content(function)
        
        message = f"""
🎉 <b>КЛЮЧ АКТИВИРОВАН!</b>

{content['emoji']} <b>{content['title']}</b>

<b>🎯 ТРИГГЕРЫ:</b>
"""
        
        for i, trigger in enumerate(content['triggers'][:3], 1):
            message += f"\n{i}. {trigger}"
        
        message += f"""

<b>🧠 РАЗБОР:</b>
{content['analysis']}

<b>📋 ПРОТОКОЛ:</b>
{content['protocol']}
"""
        
        next_keys = {"1F": "2F", "2F": "3F", "3F": "4F", "4F": "1F"}
        next_f = next_keys.get(function)
        next_emoji = FOUR_F_EMOJIS[next_f]
        
        keyboard = [
            [InlineKeyboardButton(f"{next_emoji} КУПИТЬ {next_f} - 1₽", callback_data=f"buy_4f_{friend_id}_{next_f}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_CONTENT
    except Exception as e:
        logger.error(f"❌ Ошибка в open_4f_key_callback: {e}")
        return FOUR_F_MENU

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для нереализованных функций"""
    try:
        query = update.callback_query
        pattern = query.data
        
        if pattern.startswith("pay_access_"):
            await query.answer("💰 Демо-платёж")
        elif pattern == "share_mirror":
            await query.answer("🪞 Скоро здесь будет подарок")
        elif pattern == "full_description":
            await query.answer("📖 Полное описание — 690₽")
        elif pattern.startswith("check_payment_"):
            parts = pattern.split("_")
            if len(parts) >= 5:
                friend_id = int(parts[3])
                function = parts[4]
                
                for inv in context.user_data.get("sexual_invites", []):
                    if inv.get("friend_id") == friend_id:
                        if "purchased_functions" not in inv:
                            inv["purchased_functions"] = []
                        if function not in inv["purchased_functions"]:
                            inv["purchased_functions"].append(function)
                        break
                
                await query.answer("✅ Ключ разблокирован!", show_alert=True)
                new_query = update
                new_query.callback_query.data = f"open_4f_{friend_id}_{function}"
                return await open_4f_key_callback(new_query, context)
        else:
            await query.answer("✅ Демо-режим")
        
        return RESULTS
    except Exception as e:
        logger.error(f"❌ Ошибка в dummy_callback: {e}")
        return RESULTS

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    # Сброс вебхука
    import requests
    print("\n" + "="*50)
    print("🔄 СБРОС ВЕБХУКА")
    print("="*50)
    
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
    response = requests.get(url)
    print(f"Ответ: {response.json()}")
    
    url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    response = requests.get(url)
    print(f"Информация о вебхуке: {response.json()}")
    print("="*50 + "\n")
    
    print("\n" + "="*70)
    print("🧠 ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА (ВЕРСИЯ 5.4)")
    print("="*70)
    print("🔞 ПОЛНАЯ ИНТЕГРАЦИЯ 18+ МОДУЛЯ")
    print("="*70)
    print("📊 ОСНОВНЫЕ КОМПОНЕНТЫ:")
    print("1. ✅ Психологический тест (4 этапа)")
    print("2. ✅ 18+ интимные профили с приглашениями")
    print("3. ✅ 4F-ключи (1F,2F,3F,4F) для друзей")
    print("4. ✅ Платежная система ЮKassa")
    print("5. ✅ Интеграция с Яндекс.Диск (36 профилей)")
    print("="*70)
    print("🔧 ИСПРАВЛЕНИЯ В 5.4:")
    print("   ✅ Исправлен циклический импорт (константы вынесены в constants.py)")
    print("   ✅ Импорты STAGE_1, STAGE_2 теперь из constants.py")
    print("   ✅ Устранена проблема с start_stage_1 = None")
    print("="*70)
    
    # Проверка наличия GIFT_PDF_LINK
    if not GIFT_PDF_LINK:
        logger.warning("⚠️ GIFT_PDF_LINK не установлена, используется ссылка по умолчанию")
    else:
        logger.info(f"🎁 GIFT_PDF_LINK загружена: {GIFT_PDF_LINK[:30]}...")
    
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
    print(f"💰 Стоимость профиля: 690 рублей")
    print(f"💰 Стоимость 4F ключа: {FOUR_F_PRICE} рублей")
    print(f"💰 Стоимость доступа к другу: {FRIEND_ACCESS_PRICE} рублей")
    print("="*30)
    
    application = Application.builder().token(TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Общие callback-обработчики
    application.add_handler(CallbackQueryHandler(why_details_callback, pattern="^why_details$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    
    # Заглушки для 18+ модуля
    application.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
    
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
                CallbackQueryHandler(buy_command, pattern="^buy_package$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(back_to_results_after_gift, pattern="^back_to_results_after_gift$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(show_my_sexual_profile, pattern="^show_my_sexual_profile$"),
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(buy_command, pattern="^buy_package$"),
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results_after_gift, pattern="^back_to_results_after_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"),
                CallbackQueryHandler(get_materials_callback_payment, pattern="^get_materials_"),
                CallbackQueryHandler(buy_without_test_callback, pattern="^buy_without_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            # ===== 18+ МОДУЛЬ =====
            MY_SEXUAL_PROFILE: [
                CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"),
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            SEXUAL_PROFILE_SCREEN: [
                CallbackQueryHandler(show_my_sexual_profile, pattern="^show_my_sexual_profile$"),
                CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"),
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            SEXUAL_INVITES_LIST: [
                CallbackQueryHandler(sexual_invite_start, pattern="^sexual_invite_start$"),
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$|^show_my_invites$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(copy_invite_callback, pattern="^copy_invite_"),
                CallbackQueryHandler(check_invite_callback, pattern="^check_invite_"),
                CallbackQueryHandler(create_invite_callback, pattern="^create_new_invite$"),
                CallbackQueryHandler(noop_callback, pattern="^delete_invite_"),
                CallbackQueryHandler(noop_callback, pattern="^buy_function_"),
                CallbackQueryHandler(noop_callback, pattern="^open_4f_key_"),
                CallbackQueryHandler(noop_callback, pattern="^buy_invite_packages$"),
            ],
            SEXUAL_FRIEND_PROFILE: [
                CallbackQueryHandler(noop_callback, pattern="^friend_details_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(noop_callback, pattern="^check_4f_payment_"),
                CallbackQueryHandler(noop_callback, pattern="^open_4f_key_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$|^show_my_invites$"),
            ],
            FOUR_F_CONTENT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$|^show_my_invites$"),
            ],
            # ===== КОНЕЦ 18+ =====
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    logger.info("🧠 Виртуальный психолог Вариатика запущен!")
    logger.info("✅ ВЕРСИЯ 5.4: ИСПРАВЛЕН ЦИКЛИЧЕСКИЙ ИМПОРТ!")
    logger.info("✅ Константы вынесены в отдельный файл constants.py")
    logger.info("✅ Вопросы вынесены в отдельный файл questions.py")
    logger.info("✅ Обработчики этапов вынесены в папку handlers/")
    logger.info("✅ Утилиты вынесены в папку utils/")
    logger.info("✅ Супер-логирование активировано!")
    
    # ✅ ВАЖНО: Добавляем обработку ошибок и сброс вебхука
    print("\n🚀 ЗАПУСК БОТА")
    print("="*30)
    
    try:
        application.run_polling(
            drop_pending_updates=True,  # ОЧЕНЬ ВАЖНО!
            allowed_updates=['message', 'callback_query'],  # Только нужные типы
            poll_interval=1.0  # Частота опроса
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"\n❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    # Добавляем путь для импорта модулей
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()
