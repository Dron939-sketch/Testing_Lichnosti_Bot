#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 19.7 - ИСПРАВЛЕН ЦИКЛИЧЕСКИЙ ИМПОРТ
✅ Все 36 ссылок на профили добавлены
✅ Умная функция поиска ссылок по профилю
✅ Корректное отображение в "Моих отражениях"
✅ Импорт состояний из constants.py
✅ Полный экспорт всех необходимых компонентов
✅ Интеграция с БД через API (app.py)
✅ Сохранение приглашений в БД
✅ Обновление статуса после прохождения теста
✅ Динамическая загрузка интимных профилей по коду пользователя
✅ Поиск профилей без учета суффикса (EXP → любой файл типа_уровня_*)

ВНИМАНИЕ: Этот файл предназначен для импорта в основной бот,
не для самостоятельного запуска!
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
import traceback
import asyncio
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Conflict, BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
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

# ===== ИМПОРТ КОНСТАНТ ИЗ CONSTANTS.PY =====
try:
    from constants import (
        # Состояния теста
        STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS,
        GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, PAYMENT_SCREEN,
        
        # Состояния 18+ модуля
        MY_SEXUAL_PROFILE,
        SEXUAL_PROFILE_SCREEN,
        SEXUAL_INVITES_LIST,
        SEXUAL_FRIEND_PROFILE,
        
        # Состояния 4F
        FOUR_F_PAYMENT_SCREEN,
        FOUR_F_CONTENT_SCREEN,
        FOUR_F_MAIN,
        FOUR_F_DETAILED,
        FOUR_F_MENU,
        FOUR_F_CONTENT,
        
        # Дополнительные состояния
        BUY_PACKAGES,
        INVITES_LIST,
        FRIEND_MENU,
        
        # Словарь состояний
        SEXUAL_STATES,
    )
    logger.info("✅ Константы успешно импортированы из constants.py")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта из constants.py: {e}")
    # Заглушки на случай ошибки импорта
    MY_SEXUAL_PROFILE = 1
    SEXUAL_PROFILE_SCREEN = 2
    SEXUAL_INVITES_LIST = 3
    SEXUAL_FRIEND_PROFILE = 4
    FOUR_F_PAYMENT_SCREEN = 5
    FOUR_F_CONTENT_SCREEN = 6
    FOUR_F_MAIN = 7
    FOUR_F_DETAILED = 8
    FOUR_F_MENU = 9
    FOUR_F_CONTENT = 10
    BUY_PACKAGES = 20
    INVITES_LIST = 21
    FRIEND_MENU = 22
    RESULTS_SCREEN = 15  # Используем RESULTS из теста
    SEXUAL_STATES = {}
    logger.warning("⚠️ Используются запасные значения констант")

# ===== НАСТРОЙКА =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "ваш_shop_id")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "ваш_secret_key")

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

# ===== КОНСТАНТЫ =====
RESULTS_SCREEN = RESULTS  # Алиас для совместимости

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
    "SA_1_DEF": "https://disk.yandex.ru/d/k-MqapaI3zmb_w",
    "SA_2_SIT": "https://disk.yandex.ru/d/1v8xNz0m6cPzTg",
    "SA_3_CON": "https://disk.yandex.ru/d/8kqMEvs7OC86PQ",
    "SA_4_EXP": "https://disk.yandex.ru/d/PzCDu_jfJpzgqg",
    "SA_5_INT": "https://disk.yandex.ru/d/EYPIF9_puI_t0A",
    "SA_6_AUT": "https://disk.yandex.ru/d/lfRe4hOGoneJUA",
    "SA_7_VAL": "https://disk.yandex.ru/d/TRFjXAPoxH8_Yw",
    "SA_8_TRA": "https://disk.yandex.ru/d/kUTCtJTez59G3g",
    "SA_9_IDE": "https://disk.yandex.ru/d/p54mj-rRgW54zg",
    
    # SP Profiles
    "SP_1_DEF": "https://disk.yandex.ru/d/F07HTDrGplwgWg",
    "SP_2_SIT": "https://disk.yandex.ru/d/MoXCgdUamEnmfA",
    "SP_3_CON": "https://disk.yandex.ru/d/9Sp--f1UF1WCrg",
    "SP_4_EXP": "https://disk.yandex.ru/d/K869xbd1mmLwWA",
    "SP_5_INT": "https://disk.yandex.ru/d/5Ip1IllKjF1TQg",
    "SP_6_AUT": "https://disk.yandex.ru/d/saOXkhBzFdGO6A",
    "SP_7_VAL": "https://disk.yandex.ru/d/1umIAOuQVec-nw",
    "SP_8_TRA": "https://disk.yandex.ru/d/lqhpsMCnQaXkzw",
    "SP_9_IDE": "https://disk.yandex.ru/d/RsvI8Kw1G367Mg",
    
    # IA Profiles
    "IA_1_DEF": "https://disk.yandex.ru/d/Ca6qVNiaScceHA",
    "IA_2_SIT": "https://disk.yandex.ru/d/fQiK3NQ6kJB0vw",
    "IA_3_CON": "https://disk.yandex.ru/d/44CwOGbfN2304g",
    "IA_4_EXP": "https://disk.yandex.ru/d/vukRKPMMWiJUZw",
    "IA_5_INT": "https://disk.yandex.ru/d/ERvhVQqxEgafsw",
    "IA_6_AUT": "https://disk.yandex.ru/d/41U2jQq-SZBVPg",
    "IA_7_VAL": "https://disk.yandex.ru/d/7cs7v7_phz5BjQ",
    "IA_8_TRA": "https://disk.yandex.ru/d/3QpBmWsO8l3xlw",
    "IA_9_IDE": "https://disk.yandex.ru/d/EjTrACZrYgjFEg",
    
    # IP Profiles
    "IP_1_DEF": "https://disk.yandex.ru/d/MTfoxMFHrfP-Lw",
    "IP_2_SIT": "https://disk.yandex.ru/d/L6X5a5rRT4FPWQ",
    "IP_3_CON": "https://disk.yandex.ru/d/larM19K4iVyy6Q",
    "IP_4_EXP": "https://disk.yandex.ru/d/jSvbjNOi3BuVAw",
    "IP_5_INT": "https://disk.yandex.ru/d/ny-cnsvdtj_fDw",
    "IP_6_AUT": "https://disk.yandex.ru/d/kDd9tKyKVughag",
    "IP_7_VAL": "https://disk.yandex.ru/d/DNAG15nsH0-wYA",
    "IP_8_TRA": "https://disk.yandex.ru/d/K90BW0SSTOuAhA",
    "IP_9_IDE": "https://disk.yandex.ru/d/VIgdg8gFVp10aw",
    
    # Default
    "default": "https://disk.yandex.ru/d/EYPIF9_puI_t0A"
}

USER_DISK_LINK = PROFILE_DISK_LINKS["SA_5_INT"]  
EXAMPLE_DISK_LINK = PROFILE_DISK_LINKS["SA_3_CON"]
AUTHOR_TELEGRAM = "https://t.me/meysternlp"

def get_disk_link_by_profile(profile_code: str) -> str:
    """Поиск ссылки с поддержкой всех возможных форматов"""
    if not profile_code:
        logger.warning("⚠️ profile_code пустой, использую default")
        return PROFILE_DISK_LINKS["default"]
    
    logger.info(f"🔍 ВХОДНОЙ КОД: '{profile_code}'")
    
    # Приводим к верхнему регистру
    clean_code = profile_code.upper().strip()
    
    # Генерируем все возможные форматы
    possible_formats = []
    
    # 1. Исходный формат
    possible_formats.append(clean_code)
    
    # 2. Формат с дефисом между типом и уровнем (IP-4_EXP) - ЭТО НУЖНЫЙ ФОРМАТ!
    if '_' in clean_code:
        # Разбиваем на части
        parts = clean_code.split('_')
        if len(parts) == 2:
            # IP_4_EXP -> IP-4_EXP
            type_level = parts[0].replace('_', '-')  # IP_4 -> IP-4
            suffix = parts[1]
            possible_formats.append(f"{type_level}_{suffix}")
    
    # 3. Полная замена _ на - (IP-4-EXP)
    possible_formats.append(clean_code.replace('_', '-'))
    
    # 4. Полная замена - на _ (IP_4_EXP)
    possible_formats.append(clean_code.replace('-', '_'))
    
    # Убираем дубликаты
    seen = set()
    unique_formats = []
    for fmt in possible_formats:
        if fmt not in seen:
            seen.add(fmt)
            unique_formats.append(fmt)
    
    logger.info(f"📋 ПРОВЕРЯЕМ ФОРМАТЫ: {unique_formats}")
    
    # Пробуем каждый формат
    for fmt in unique_formats:
        if fmt in PROFILE_DISK_LINKS:
            link = PROFILE_DISK_LINKS[fmt]
            logger.info(f"✅ НАЙДЕНО! {fmt} -> {link}")
            return link
    
    # Если ничего не нашли
    logger.error(f"❌ НЕ НАЙДЕНО для '{profile_code}'!")
    logger.error(f"📋 ПЕРВЫЕ 10 КЛЮЧЕЙ: {list(PROFILE_DISK_LINKS.keys())[:10]}")
    
    return PROFILE_DISK_LINKS["default"]

# ===== АЛИАСЫ ДЛЯ СОВМЕСТИМОСТИ =====
get_disk_link = get_disk_link_by_profile

# ===== 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ",
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

# ===== ПОДРОБНЫЕ ОПИСАНИЯ 4F =====
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

# ===== ЭКРАН "4F - КРАТКО" =====
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

# ===== ЭКРАН "4F - ПОДРОБНО" =====
FOUR_F_DETAILED_TEXT = """
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

# ===== ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ДОСТУПНЫХ ПРОФИЛЕЙ =====
def check_available_sexual_profiles() -> Dict[str, List[str]]:
    """
    Проверяет, какие интимные профили доступны в папке sexual_18/
    Возвращает словарь с найденными файлами и список отсутствующих
    """
    logger.info("🔍 ПРОВЕРКА ДОСТУПНЫХ ИНТИМНЫХ ПРОФИЛЕЙ")
    
    # Все возможные комбинации профилей
    all_profiles = []
    types = ['sa', 'sp', 'ia', 'ip']
    levels = range(1, 10)
    suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
    
    for t in types:
        for l in levels:
            for s in suffixes:
                profile = f"{t}_{l}_{s}"
                all_profiles.append(profile)
    
    # Пути для поиска
    search_paths = [
        os.path.join(PROJECT_ROOT, "sexual_18"),
        os.path.join("sexual_18"),
        os.path.join(PROJECT_ROOT, "profiles", "sexual_18"),
        os.path.join("profiles", "sexual_18"),
        "/opt/render/project/src/sexual_18",
        "/opt/render/project/src/profiles/sexual_18",
    ]
    
    found_files = []
    found_profiles = []
    
    for path in search_paths:
        if os.path.exists(path):
            logger.info(f"📁 Проверяем папку: {path}")
            try:
                files = os.listdir(path)
                json_files = [f for f in files if f.endswith('.json')]
                logger.info(f"   Найдено JSON файлов: {len(json_files)}")
                
                for file in json_files:
                    file_path = os.path.join(path, file)
                    found_files.append(file_path)
                    profile_name = file.replace('.json', '')
                    found_profiles.append(profile_name)
                    
            except Exception as e:
                logger.error(f"   ❌ Ошибка чтения папки: {e}")
    
    # Убираем дубликаты
    found_profiles = list(set(found_profiles))
    found_files = list(set(found_files))
    
    # Определяем, каких профилей не хватает
    missing_profiles = [p for p in all_profiles if p not in found_profiles]
    
    logger.info(f"📊 ВСЕГО НАЙДЕНО ПРОФИЛЕЙ: {len(found_profiles)}")
    logger.info(f"📋 СПИСОК НАЙДЕННЫХ ПРОФИЛЕЙ:")
    for profile in sorted(found_profiles):
        logger.info(f"   ✅ {profile}.json")
    
    logger.info(f"❌ ОТСУТСТВУЮТ ПРОФИЛЕЙ: {len(missing_profiles)}")
    logger.info(f"   Примеры отсутствующих: {missing_profiles[:10]}")
    
    return {
        "found": found_profiles,
        "missing": missing_profiles,
        "total_found": len(found_profiles),
        "total_missing": len(missing_profiles)
    }

# ===== ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ (НОВАЯ ВЕРСИЯ - БЕЗ УЧЕТА СУФФИКСА) =====
def load_intimate_profile(profile_code: str = "SA-5_INT") -> dict:
    """
    Загружает интимный профиль по коду профиля (без учета суффикса)
    Ищет любой файл вида {тип}_{уровень}_*.json
    """
    try:
        logger.info(f"🔍🔍🔍 НАЧАЛО ЗАГРУЗКИ ИНТИМНОГО ПРОФИЛЯ для кода: {profile_code}")
        
        # Извлекаем тип и уровень из кода (например, "IP-4_EXP" → тип="ip", уровень="4")
        code_parts = profile_code.upper().replace('-', '_').split('_')
        profile_type = None
        profile_level = None
        
        if len(code_parts) >= 2:
            profile_type = code_parts[0].lower()  # ip, sa, sp, ia
            profile_level = code_parts[1]          # 1,2,3,4,5,6,7,8,9
            logger.info(f"📊 Извлечены тип={profile_type}, уровень={profile_level}")
        else:
            logger.warning(f"⚠️ Не удалось распарсить код профиля: {profile_code}")
        
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"📁 Текущая директория: {bot_dir}")
        logger.info(f"📁 Корень проекта: {PROJECT_ROOT}")
        
        # Проверяем все возможные директории
        search_dirs = [
            os.path.join(bot_dir, "sexual_18"),
            os.path.join(PROJECT_ROOT, "sexual_18"),
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18"),
            os.path.join("sexual_18"),
            os.path.join("profiles", "sexual_18"),
            "/opt/render/project/src/sexual_18",
            "/opt/render/project/src/profiles/sexual_18",
        ]
        
        # Если удалось получить тип и уровень, ищем любой подходящий файл
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
                                logger.info(f"   ✅ НАЙДЕН! Файл: {filename} (соответствует шаблону {pattern})")
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
        
        # Если не нашли по шаблону, пробуем точное совпадение (для обратной совместимости)
        logger.info(f"🔍 Не нашли по шаблону, пробуем точное совпадение...")
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
        
        # Если ничего не нашли, пробуем default.json
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
        logger.info(f"📤 ВЫЗОВ update_invite_in_api для {invite_id}")
        logger.info(f"📦 friend_data = {friend_data}")
        logger.info(f"📡 API_URL = {API_URL}")
        logger.info(f"🔗 Полный URL: {API_URL}/api/sexual/update-invite/{invite_id}")
        
        response = requests.post(
            f"{API_URL}/api/sexual/update-invite/{invite_id}",
            json=friend_data,
            timeout=5
        )
        
        logger.info(f"📥 Статус ответа: {response.status_code}")
        logger.info(f"📥 Тело ответа: {response.text[:200]}")
        
        if response.status_code == 200:
            logger.info(f"✅ Приглашение {invite_id} обновлено в БД")
            return True
        else:
            logger.error(f"❌ Ошибка обновления приглашения: {response.status_code}")
            logger.error(f"❌ Текст ошибки: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении в БД: {e}")
        logger.error(f"❌ Детали: {traceback.format_exc()}")
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

# ===== ФУНКЦИИ ФОРМАТИРОВАНИЯ ИНТИМНОГО ПРОФИЛЯ =====
def format_intimate_profile_part1(profile_data: dict, user_name: str) -> str:
    """Форматирует ПЕРВУЮ ЧАСТЬ интимного профиля"""
    try:
        # Получаем код профиля для отображения
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
        
        # Добавляем примечание, если это аварийный профиль
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
        
        # Финальный текст (к нему будут прикреплены кнопки)
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

# ===== ФУНКЦИЯ ДЛЯ РАЗБИЕНИЯ ДЛИННЫХ СООБЩЕНИЙ =====
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

# ===== ЗАГРУЗКА ПРОФИЛЯ ДРУГА =====
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

# ===== ЗАГРУЗКА СТАНДАРТНОГО ПРОФИЛЯ ДРУГА =====
def load_friend_standard_profile() -> dict:
    return {
        "archetype": "Автономный стратег",
        "quote": "«Я не ищу одобрения — я ищу эффективность.»",
        "pain": "Вам сложно делегировать. Вы уверены: «Хочешь сделать хорошо — сделай сам».",
        "immediate_tool": "Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.",
        "cta": "Исследуйте баланс между автономией и доверием."
    }

# ===== ЗАГРУЗКА 4F-КОНТЕНТА =====
def load_4f_content(function: str) -> dict:
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

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====
def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """СОЗДАЕТ РЕАЛЬНЫЙ ПЛАТЕЖ В ЮKASSA через API бэкенда"""
    try:
        logger.info(f"💰 Создание реального платежа: {payment_id}, сумма: {amount}, пользователь: {user_id}")
        
        # Проверяем настройки API
        if not API_URL:
            logger.error("❌ API_URL не настроен")
            return {"success": False, "error": "API не настроен"}
        
        # Создаем платеж через API бэкенда
        response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json={
                "payment_id": payment_id,
                "user_id": user_id,
                "amount": amount,
                "profile_code": "PACKAGE",
                "description": description or f"Оплата на сумму {amount}₽",
                "email": f"user_{user_id}@example.com"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            confirmation_url = data.get("confirmation_url")
            
            if confirmation_url:
                logger.info(f"✅ Реальный платеж создан: {payment_id}, ссылка получена")
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": confirmation_url,
                    "amount": amount,
                    "status": "pending",
                    "yookassa_id": data.get("yookassa_id")
                }
            else:
                logger.error(f"❌ Нет confirmation_url в ответе: {data}")
                return {"success": False, "error": "Нет ссылки на оплату"}
        else:
            error_text = response.text[:200] if response.text else "Нет ответа"
            logger.error(f"❌ Ошибка API: {response.status_code} - {error_text}")
            
            # Пробуем создать платеж напрямую через ЮKassa (запасной вариант)
            try:
                logger.info("🔄 Пробую создать платеж напрямую через ЮKassa...")
                
                import base64
                
                auth = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
                
                payload = {
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": f"https://t.me/{BOT_USERNAME}"
                    },
                    "capture": True,
                    "description": description or f"Оплата на сумму {amount}₽",
                    "metadata": {
                        "payment_id": payment_id,
                        "user_id": user_id
                    }
                }
                
                headers = {
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/json",
                    "Idempotence-Key": payment_id
                }
                
                response = requests.post(
                    "https://api.yookassa.ru/v3/payments",
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    data = response.json()
                    confirmation_url = data.get("confirmation", {}).get("confirmation_url")
                    
                    if confirmation_url:
                        logger.info(f"✅ Прямой платеж через ЮKassa создан: {payment_id}")
                        return {
                            "success": True,
                            "payment_id": payment_id,
                            "confirmation_url": confirmation_url,
                            "amount": amount,
                            "status": "pending",
                            "yookassa_id": data.get("id")
                        }
                
                logger.error(f"❌ Ошибка прямого платежа: {response.status_code}")
                return {"success": False, "error": f"Ошибка ЮKassa: {response.status_code}"}
                
            except Exception as e2:
                logger.error(f"❌ Ошибка прямого платежа: {e2}")
                return {"success": False, "error": str(e2)}
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {"success": False, "error": str(e)}

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ (временное, для обратной совместимости) =====
user_invites = {}

def get_user_invites(user_id: int) -> list:
    """Получает список приглашений пользователя (сначала из БД, потом из памяти)"""
    # Пытаемся получить из БД
    db_invites = get_user_invites_from_api(user_id)
    if db_invites:
        return db_invites
    
    # Если БД недоступна, используем память
    if user_id not in user_invites:
        user_invites[user_id] = []
        logger.info(f"👤 Создано хранилище в памяти для пользователя {user_id}")
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    invites = get_user_invites(user_id)
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

def init_test_data(user_id: int):
    try:
        invites = get_user_invites(user_id)
        if len(invites) > 0:
            logger.info(f"👤 У пользователя {user_id} уже есть данные, пропускаем инициализацию")
            return
        
        current_time = datetime.now().timestamp()
        
        # Тестовые данные с корректными профилями
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

# ============================================
# 🧠 ЭКРАН РЕЗУЛЬТАТОВ
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.debug("📺 Отображаем экран результатов")
        profile = context.user_data.get("profile", USER_PROFILE)
        
        # Получаем ссылку на профиль пользователя
        user_profile_link = get_disk_link_by_profile(profile['display_name'])
        
        message = f"""
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>

📊 {profile['display_name']}

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 <b>ИНСТРУМЕНТ</b>
Сегодня: попросите кого-то о маленькой услуге.
Заметьте, что мир не рухнул.

📁 <b>ССЫЛКА НА ПРОФИЛЬ:</b>
{user_profile_link}
"""
        
        keyboard = [
            [InlineKeyboardButton("🪞 Зеркало", callback_data="share_mirror")],
            [InlineKeyboardButton("📖 Полный профиль", callback_data="full_description")],
            [InlineKeyboardButton("🔞 ИНТИМНЫЙ ПРОФИЛЬ", callback_data="my_sexual_profile")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            query = update.callback_query
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        
        context.user_data["conversation_state"] = RESULTS_SCREEN
        return RESULTS_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в show_results_screen: {e}")
        return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def show_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль - 3 ЧАСТИ, КНОПКИ НА ЧАСТИ 3"""
    try:
        query = update.callback_query
        logger.debug(f"🔍 ПОЛУЧЕН CALLBACK: {query.data} от пользователя {query.from_user.id}")
        
        await query.answer()
        logger.info(f"👤 Пользователь {query.from_user.id} открыл интимный профиль")
        
        context.user_data["conversation_state"] = MY_SEXUAL_PROFILE
        
        # ПОЛУЧАЕМ ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ИЗ РЕЗУЛЬТАТОВ ТЕСТА
        profile_data = context.user_data.get("profile_data")
        if profile_data and 'display_name' in profile_data:
            profile_code = profile_data['display_name']
            logger.info(f"📊 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ИЗ ТЕСТА: {profile_code}")
        else:
            # Если нет, берем из profile (по умолчанию)
            user_profile = context.user_data.get("profile", USER_PROFILE)
            profile_code = user_profile.get('display_name', 'SA-5_INT')
            logger.info(f"📊 ПРОФИЛЬ ПО УМОЛЧАНИЮ: {profile_code}")
        
        user_name = query.from_user.first_name or "Пользователь"
        logger.debug(f"📝 Загружаем интимный профиль для пользователя: {user_name} с кодом {profile_code}")
        
        # ЗАГРУЖАЕМ ИНТИМНЫЙ ПРОФИЛЬ С ЭТИМ КОДОМ
        intimate_data = load_intimate_profile(profile_code)
        
        # Логируем результат загрузки
        if intimate_data.get('is_emergency'):
            logger.warning(f"⚠️ ЗАГРУЖЕН АВАРИЙНЫЙ ПРОФИЛЬ для {profile_code}")
        elif intimate_data.get('is_default'):
            logger.warning(f"⚠️ ЗАГРУЖЕН ПРОФИЛЬ ПО УМОЛЧАНИЮ для {profile_code}")
        else:
            logger.info(f"✅ УСПЕШНО ЗАГРУЖЕН ПРОФИЛЬ: {profile_code} (из файла {intimate_data.get('loaded_from_file', 'неизвестно')})")
        
        logger.debug(f"📊 Интимный профиль загружен: {intimate_data.get('profile_type', 'unknown')} для {profile_code}")
        
        message_part1 = format_intimate_profile_part1(intimate_data, user_name)
        message_part2 = format_intimate_profile_part2(intimate_data, user_name)
        message_part3 = format_intimate_profile_part3(intimate_data, user_name)
        
        logger.debug(f"📄 Длина части 1: {len(message_part1)} символов")
        logger.debug(f"📄 Длина части 2: {len(message_part2)} символов")
        logger.debug(f"📄 Длина части 3: {len(message_part3)} символов")
        
        # 3 КНОПКИ (будут прикреплены к части 3)
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ-ПРИГЛАШЕНИЕ", callback_data="send_invite")],  # 👈 НАЗВАНИЕ СТАРОЕ, НО CALLBACK НОВЫЙ
            [InlineKeyboardButton("🔍 ПОСМОТРЕТЬ МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ НАЗАД В ПРОФИЛЬ", callback_data="back_to_results")]
        ]
        navigation_keyboard = InlineKeyboardMarkup(keyboard)
        
        chat_id = query.message.chat_id
        
        # Отправляем часть 1 (редактируем текущее сообщение)
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
        
        # Отправляем часть 2 (без кнопок)
        if message_part2.strip():
            logger.debug("✉️ Отправляем часть 2...")
            await safe_send_message(chat_id, message_part2, context)
            await asyncio.sleep(1)
        
        # Отправляем часть 3 С КНОПКАМИ
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
        logger.error(f"❌ Ошибка в show_my_sexual_profile: {e}\n{traceback.format_exc()}")
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
        return RESULTS_SCREEN

# ============================================
# 🔗 ОБРАБОТЧИК ПРИГЛАШЕНИЙ (DEEP LINK)
# ============================================

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик приглашений для 18+ модуля
    Вызывается при переходе по ссылке с параметром start=sex_
    """
    try:
        user = update.effective_user
        logger.info(f"🔗🔗🔗 ПОЛЬЗОВАТЕЛЬ {user.id} ПЕРЕШЕЛ ПО ПРИГЛАШЕНИЮ 🔗🔗🔗")
        
        # Получаем код приглашения из аргументов
        args = context.args
        logger.info(f"📦 context.args = {args}")
        
        invite_code = args[0] if args else None
        logger.info(f"🔍 Код приглашения: {invite_code}")
        
        if not invite_code:
            logger.warning("⚠️ Приглашение без кода")
            await update.message.reply_text(
                "❌ Неверная ссылка приглашения.\n"
                "Пожалуйста, попросите друга отправить вам новую ссылку."
            )
            return RESULTS_SCREEN
        
        # Ищем приглашение в БД
        logger.info(f"📡 Запрос к API: {API_URL}/api/sexual/get-invite/{invite_code}")
        invite = find_invite_in_api(invite_code)
        logger.info(f"📦 Ответ от API: {invite}")
        
        if not invite:
            # Если нет в БД, ищем в памяти
            logger.info("🔍 В БД не найдено, ищем в памяти...")
            invites = get_user_invites(user.id)
            logger.info(f"📦 В памяти найдено приглашений: {len(invites)}")
            invite = next((inv for inv in invites if inv.get("invite_id") == invite_code), None)
            logger.info(f"📦 В памяти найдено: {invite}")
        
        if not invite:
            logger.warning(f"❌ Приглашение {invite_code} не найдено")
            await update.message.reply_text(
                "❌ Приглашение не найдено или уже использовано.\n"
                "Попросите друга отправить новую ссылку."
            )
            return RESULTS_SCREEN
        
        # Сохраняем информацию о приглашении в данные пользователя
        buyer_id = invite.get("user_id") or invite.get("buyer_id")
        logger.info(f"👤 buyer_id = {buyer_id}")
        logger.info(f"📊 profile_code = {invite.get('profile_code')}")
        
        context.user_data["current_invite"] = {
            "invite_id": invite_code,
            "buyer_id": buyer_id,
            "buyer_profile": invite.get("profile_code")
        }
        logger.info(f"✅ current_invite сохранен: {context.user_data['current_invite']}")
        
        # Приветственное сообщение
        welcome_text = (
            f"🎮 <b>Вы получили секретный доступ к уровню 2.0!</b>\n\n"
            f"Кто-то из друзей передал вам ключ к расшифровке себя.\n"
            f"Это не просто тест — это карта вашего внутреннего мира.\n\n"
            f"<b>Ваш квест:</b>\n"
            f"🗺 Исследовать себя\n"
            f"🔓 Открыть скрытые возможности\n"
            f"🎯 Найти точку роста\n\n"
            f"🚀 Войти в игру?"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]
        ]
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Приветственное сообщение отправлено пользователю {user.id}")
        return RESULTS_SCREEN
        
    except Exception as e:
        logger.error(f"❌ Ошибка в sexual_invite_start: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке приглашения.\n"
            "Пожалуйста, попробуйте позже."
        )
        return RESULTS_SCREEN
        # ============================================
# 📋 КОПИРОВАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для копирования текста приглашения
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Извлекаем ID приглашения из callback_data
        invite_id = query.data.replace("copy_invite_", "")
        
        # Ищем приглашение в данных пользователя
        invites = context.user_data.get("sexual_invites", [])
        invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return
        
        # Текст приглашения для копирования
        invite_text = f"{invite.get('message', '')}\n\n{invite.get('link', '')}"
        
        # Отправляем сообщение с текстом для копирования
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


# ============================================
# ✅ ПРОВЕРКА ПРИГЛАШЕНИЯ
# ============================================

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для проверки статуса приглашения
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Извлекаем ID приглашения из callback_data
        invite_id = query.data.replace("check_invite_", "")
        
        # Ищем приглашение в данных пользователя
        invites = context.user_data.get("sexual_invites", [])
        invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return
        
        # Формируем сообщение со статусом
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


# ============================================
# 🔗 ЭКРАН: СОЗДАНИЕ ПРИГЛАШЕНИЯ (ПЕРЕНАПРАВЛЕНИЕ)
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔗 СОЗДАНИЕ ПРИГЛАШЕНИЯ - перенаправляет на send_invite_callback"""
    logger.info(f"🔗 create_invite_callback ВЫЗВАН! User: {update.effective_user.id} - перенаправляю на send_invite_callback")
    
    # Просто вызываем новую функцию
    return await send_invite_callback(update, context)

# ============================================
# ✈️ ЭКРАН: ОТПРАВКА ПРИГЛАШЕНИЯ
# ============================================

async def send_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✈️ ОТПРАВКА ПРИГЛАШЕНИЯ - создает новую ссылку"""
    logger.info(f"✈️ send_invite_callback ВЫЗВАН! User: {update.effective_user.id}")
    
    try:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        # ПОЛУЧАЕМ АКТУАЛЬНЫЕ ДАННЫЕ ИЗ БД
        current_invites = get_user_invites_from_api(user_id)
        context.user_data["sexual_invites"] = current_invites
        
        # 👇 СЧИТАЕМ РЕАЛЬНОЕ КОЛИЧЕСТВО БЕСПЛАТНЫХ ССЫЛОК
        free_invites_count = 0
        for inv in current_invites:
            # Проверяем по полю is_free (булево) или по типу
            if inv.get("is_free") or inv.get("invite_type") == "🆓":
                # Исключаем тестовые
                if not inv.get("invite_id", "").startswith("test_"):
                    free_invites_count += 1
        
        logger.info(f"📊 Пользователь {user_id}: всего ссылок {len(current_invites)}, бесплатных {free_invites_count}")
        
        # ПРОВЕРЯЕМ ЛИМИТЫ
        if free_invites_count < FREE_INVITE_LIMIT:
            # СОЗДАЕМ БЕСПЛАТНУЮ ССЫЛКУ
            is_free = True
            new_free_count = free_invites_count + 1
            logger.info(f"✅ Создаем БЕСПЛАТНУЮ ссылку ({new_free_count}/{FREE_INVITE_LIMIT})")
        else:
            # ПРОВЕРЯЕМ ПЛАТНЫЕ
            user_limits = get_user_limits(context)
            paid_invites_created = max(0, len(current_invites) - FREE_INVITE_LIMIT)
            paid_available = user_limits["total_purchased"] - paid_invites_created
            
            if paid_available > 0:
                is_free = False
                logger.info(f"✅ Создаем ПЛАТНУЮ ссылку")
            else:
                logger.warning(f"❌ Лимит ссылок исчерпан для пользователя {user_id}")
                await query.answer("❌ Лимит ссылок исчерпан! Купите пакет.", show_alert=True)
                return await buy_invite_packages_callback(update, context)

        # ПОЛУЧАЕМ ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
        profile = context.user_data.get("profile", USER_PROFILE)
        
        # СОЗДАЕМ НОВУЮ УНИКАЛЬНУЮ ССЫЛКУ
        invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}_{int(time.time())}"
        invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
        
        invite_message = (
            "✨ Есть одна штука.\n"
            "Определяет твой ночной тип личности.\n"
            "У меня — совпало процентов на 90.\n\n"
            "🤫 Интересно, у тебя тоже?"
        )
        
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        invite_type = "🆓" if is_free else "💎"
        
        # ФОРМИРУЕМ ДАННЫЕ ДЛЯ СОХРАНЕНИЯ
        invite_data = {
            "invite_id": invite_code,
            "link": invite_url,
            "message": invite_message,
            "profile_code": profile['display_name'],
            "status": "active",
            "created_at": datetime.now().timestamp(),
            "is_free": is_free,
            "invite_type": invite_type,
            "user_id": user_id
        }
        
        # СОХРАНЯЕМ В БД
        save_success = save_invite_to_api(invite_data)
        logger.info(f"💾 Сохранение в БД: {'успешно' if save_success else 'ошибка'}")
        
        # 👇 ОБНОВЛЯЕМ ДАННЫЕ В ПАМЯТИ
        updated_invites = get_user_invites_from_api(user_id)
        context.user_data["sexual_invites"] = updated_invites
        
        # 👇 ПЕРЕСЧИТЫВАЕМ РЕАЛЬНОЕ КОЛИЧЕСТВО БЕСПЛАТНЫХ
        actual_free_used = 0
        for inv in updated_invites:
            if inv.get("is_free") or inv.get("invite_type") == "🆓":
                if not inv.get("invite_id", "").startswith("test_"):
                    actual_free_used += 1
        
        # 👇 Обновляем лимиты в памяти
        user_limits = get_user_limits(context)
        user_limits["free_used"] = actual_free_used
        
        # 👇 СЧИТАЕМ АКТУАЛЬНЫЙ ОСТАТОК
        remaining_free = FREE_INVITE_LIMIT - actual_free_used
        
        logger.info(f"🔗 Пользователь {user_id} создал ссылку: {invite_code} (тип: {invite_type})")
        logger.info(f"📊 После создания: free_used={actual_free_used}, осталось={remaining_free}")
        
        # ГОТОВИМ ССЫЛКУ ДЛЯ ОТПРАВКИ
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
        
        # ФОРМИРУЕМ СООБЩЕНИЕ С АКТУАЛЬНЫМ СЧЕТЧИКОМ
        text = f"""
🔞 <b>✨ НОВАЯ ССЫЛКА СОЗДАНА! ✨</b>

🔗 <code>{invite_url}</code>

💬 <b>📨 ТЕКСТ СООБЩЕНИЯ:</b>
<blockquote>{invite_message}</blockquote>

{SEXUAL_DIVIDER}
🟢 <b>• УНИКАЛЬНАЯ ССЫЛКА •</b>
📅 <b>Создано:</b> {current_time}
{SEXUAL_DIVIDER}

⚠️ <b>Эта ссылка работает только для ОДНОГО человека!</b>
   После использования она станет неактивной.

🆓 Осталось бесплатных: {remaining_free}
"""
        
        # КНОПКИ
        keyboard = [
            [InlineKeyboardButton("✈️ ОТПРАВИТЬ ДРУГУ", url=share_url)],
            [InlineKeyboardButton("🔞 В ИНТИМНЫЙ ПРОФИЛЬ", callback_data="back_to_sexual_profile")],
            [InlineKeyboardButton("🪞 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Сообщение с новой ссылкой отправлено пользователю {user_id}")
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка в send_invite_callback: {e}\n{traceback.format_exc()}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return INVITES_LIST

# ============================================
# 🔍 ЭКРАН: МОИ ОТРАЖЕНИЯ
# ============================================

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
        
        # Сначала пытаемся получить из profile_data (результат теста)
        profile_data = context.user_data.get("profile_data")
        if profile_data and 'display_name' in profile_data:
            profile_code = profile_data['display_name']
        else:
            # Если нет, берем из profile (по умолчанию)
            user_profile = context.user_data.get("profile", USER_PROFILE)
            profile_code = user_profile.get('display_name', 'SA-5_INT')

        logger.info(f"📊 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ДЛЯ 18+: {profile_code}")
        
        # Получаем ссылку на профиль пользователя
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
                
                # Получаем правильную ссылку на профиль друга
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

        # 👇 ИСПРАВЛЕННЫЕ КНОПКИ
        keyboard = [
            [InlineKeyboardButton("🔞 В ИНТИМНЫЙ ПРОФИЛЬ", callback_data="back_to_sexual_profile")],
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

# ============================================
# 🧬 ЭКРАН: ГЛАВНОЕ МЕНЮ 4F (КРАТКО)
# ============================================

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
            [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="back_to_results")]
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

# ============================================
# 📘 ЭКРАН: ПОДРОБНОЕ ОПИСАНИЕ 4F
# ============================================

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ПОДРОБНОЕ ОПИСАНИЕ 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_DETAILED
        logger.info(f"📘 Пользователь {query.from_user.id} открыл подробное описание 4F")
        
        # Используем правильную подстановку ссылки
        message = FOUR_F_DETAILED_TEXT.replace("{EXAMPLE_DISK_LINK}", EXAMPLE_DISK_LINK)
        
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

# ============================================
# 🔍 ЭКРАН: ПРОВЕРКА СТАТУСА
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        invite_id = query.data.replace("check_status_", "")
        
        # Пытаемся найти в БД
        invite = find_invite_in_api(invite_id)
        
        if not invite:
            # Если нет в БД, ищем в памяти
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
        
        # 👇 ИСПРАВЛЕННЫЕ КНОПКИ
        keyboard = [
            [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")],
            [InlineKeyboardButton("🔞 В ИНТИМНЫЙ ПРОФИЛЬ", callback_data="back_to_sexual_profile")]
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

# ============================================
# 💳 ЭКРАН: ПОКУПКА ПАКЕТОВ ССЫЛОК
# ============================================

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 ПОКАЗАТЬ ДОСТУПНЫЕ ПАКЕТЫ ПРИГЛАШЕНИЙ"""
    try:
        query = update.callback_query
        await query.answer("📦 Загружаю пакеты...")
        
        context.user_data["conversation_state"] = BUY_PACKAGES
        logger.info(f"📦 Пользователь {query.from_user.id} открыл покупку пакетов")
        
        message = f"""
💎 <b>ПАКЕТЫ ПРИГЛАШЕНИЙ</b>

<b>🆓 Бесплатные ссылки закончились!</b>
У вас было {FREE_INVITE_LIMIT} бесплатных ссылок, и вы их использовали.

<b>Выберите пакет для продолжения:</b>

"""
        
        for package_id, data in INVITE_PACKAGES.items():
            popular = " 🔥 ХИТ" if data.get("popular") else ""
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
        for package_id, data in INVITE_PACKAGES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{data['emoji']} {data['links']} ССЫЛОК - {data['price']}₽",
                    callback_data=f"pay_package_{package_id}"
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
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return INVITES_LIST

# ============================================
# 💳 ЭКРАН: ОПЛАТА ПАКЕТА
# ============================================

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 СОЗДАНИЕ ПЛАТЕЖА ДЛЯ ПАКЕТА С РЕАЛЬНОЙ ССЫЛКОЙ НА ОПЛАТУ"""
    try:
        query = update.callback_query
        await query.answer("💰 Создаю платеж...")
        
        context.user_data["conversation_state"] = FOUR_F_PAYMENT_SCREEN
        
        # Получаем ID пакета из callback_data (формат: "pay_package_3")
        package_id = query.data.split("_")[2]
        package = INVITE_PACKAGES.get(package_id)
        
        if not package:
            logger.error(f"❌ Пакет {package_id} не найден")
            await query.answer("❌ Пакет не найден", show_alert=True)
            return BUY_PACKAGES
        
        user_id = query.from_user.id
        logger.info(f"💰 Пользователь {user_id} выбрал пакет {package_id} ({package['links']} ссылок за {package['price']}₽)")
        
        # Генерируем ID платежа
        payment_id = generate_payment_id("package", user_id)
        
        # СОЗДАЕМ РЕАЛЬНЫЙ ПЛАТЕЖ ЧЕРЕЗ API
        confirmation_url = None
        
        try:
            # Пробуем создать платеж через API
            response = requests.post(
                f"{API_URL}/api/create-payment-advanced",
                json={
                    "payment_id": payment_id,
                    "user_id": user_id,
                    "amount": package['price'],
                    "profile_code": f"PACKAGE_{package_id}",
                    "description": f"Пакет {package['links']} ссылок для приглашений",
                    "email": f"user_{user_id}@example.com"
                },
                timeout=15
            )
            
            logger.info(f"📥 Ответ от API: статус {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                logger.info(f"📦 Данные ответа: {data}")
                
                confirmation_url = data.get("confirmation_url")
                yookassa_id = data.get("yookassa_id")
                
                if confirmation_url:
                    logger.info(f"✅ Платеж {payment_id} создан, ссылка получена")
                else:
                    logger.error(f"❌ Нет confirmation_url в ответе: {data}")
                    await query.answer("❌ Ошибка: не получена ссылка на оплату", show_alert=True)
                    return BUY_PACKAGES
            else:
                error_text = response.text[:200] if response.text else "Нет ответа"
                logger.error(f"❌ Ошибка API: {response.status_code} - {error_text}")
                await query.answer(f"❌ Ошибка платежной системы: {response.status_code}", show_alert=True)
                return BUY_PACKAGES
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Таймаут при создании платежа")
            await query.answer("❌ Превышено время ожидания. Попробуйте позже.", show_alert=True)
            return BUY_PACKAGES
        except Exception as e:
            logger.error(f"❌ Ошибка при создании платежа: {e}")
            await query.answer("❌ Ошибка соединения", show_alert=True)
            return BUY_PACKAGES
        
        # Сохраняем данные платежа
        if "payment_data" not in context.user_data:
            context.user_data["payment_data"] = {}
        
        context.user_data["payment_data"][payment_id] = {
            "confirmation_url": confirmation_url,
            "package_id": package_id,
            "amount": package['price'],
            "links": package['links'],
            "timestamp": time.time(),
            "status": "pending"
        }
        
        # Сохраняем ID платежа для быстрого доступа
        context.user_data["last_payment_id"] = payment_id
        
        # Формируем сообщение с реальной ссылкой на оплату
        message = f"""
💳 <b>ПЛАТЕЖ СОЗДАН</b>

{package['emoji']} <b>Пакет: {package['links']} ссылок</b>
💰 <b>Сумма: {package['price']}₽</b>
📋 <b>ID платежа:</b> <code>{payment_id}</code>

✅ <b>Для оплаты нажмите кнопку ниже</b>

После успешной оплаты:
1. Нажмите "ПРОВЕРИТЬ ОПЛАТУ"
2. Ссылки будут добавлены к вашему аккаунту
3. Вы сможете создавать новые приглашения
"""
        
        # ВАЖНО: используем URL, а не callback_data для кнопки оплаты
        keyboard = [
            [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {package['price']}₽", url=confirmation_url)],
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=f"check_package_{payment_id}_{package_id}")],
            [InlineKeyboardButton("◀️ НАЗАД", callback_data="buy_invite_packages")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Пользователь {user_id} перенаправлен на оплату пакета {package_id}")
        return FOUR_F_PAYMENT_SCREEN
        
    except Exception as e:
        logger.error(f"❌ Ошибка в pay_package_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return BUY_PACKAGES


# ============================================
# ✅ ПРОВЕРКА ОПЛАТЫ ПАКЕТА
# ============================================

async def check_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ ПРОВЕРКА СТАТУСА ОПЛАТЫ ПАКЕТА И АКТИВАЦИЯ ССЫЛОК"""
    try:
        query = update.callback_query
        await query.answer("🔄 Проверяю оплату...")
        
        parts = query.data.split("_")
        payment_id = parts[2]
        package_id = parts[3]
        
        package = INVITE_PACKAGES.get(package_id)
        if not package:
            await query.answer("❌ Пакет не найден", show_alert=True)
            return
        
        logger.info(f"🔍 Проверка платежа {payment_id} для пакета {package_id}")
        
        # Получаем данные платежа из памяти
        payment_data = context.user_data.get("payment_data", {})
        payment_info = payment_data.get(payment_id, {})
        
        # Проверяем статус через API
        status = "pending"
        try:
            response = requests.get(
                f"{API_URL}/api/payment-status/{payment_id}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "pending")
                logger.info(f"📊 Статус платежа {payment_id}: {status}")
            else:
                logger.warning(f"⚠️ API вернул {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса: {e}")
        
        if status == "succeeded":
            # ПЛАТЕЖ УСПЕШЕН - добавляем ссылки пользователю
            user_limits = get_user_limits(context)
            user_limits["total_purchased"] += package["links"]
            user_limits["paid_packages"].append({
                "package": package_id,
                "links": package["links"],
                "price": package["price"],
                "payment_id": payment_id,
                "purchased_at": datetime.now().timestamp()
            })
            
            # Обновляем статус в payment_data
            if payment_id in payment_data:
                payment_data[payment_id]["status"] = "succeeded"
            
            # Получаем статистику
            invites = context.user_data.get("sexual_invites", [])
            total_invites = len(invites)
            free_used = user_limits["free_used"]
            paid_available = user_limits["total_purchased"] - (total_invites - free_used)
            
            message = f"""
✅ <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>

{package['emoji']} <b>Пакет: {package['links']} ссылок</b>
💰 Сумма: {package['price']}₽
📋 ID платежа: <code>{payment_id}</code>

💎 <b>НОВЫЙ ЛИМИТ ССЫЛОК:</b>
   • Бесплатных использовано: {free_used}/{FREE_INVITE_LIMIT}
   • Платных доступно: {paid_available}
   • Всего ссылок создано: {total_invites}

🎉 <b>Теперь вы можете создавать новые приглашения!</b>
"""
            keyboard = [
                [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
                [InlineKeyboardButton("◀️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
            ]
            
            logger.info(f"✅ Пользователь {query.from_user.id} получил пакет {package_id} ({package['links']} ссылок)")
            
            # Очищаем данные платежа после успешной активации
            if payment_id in payment_data:
                del payment_data[payment_id]
                
        elif status in ["pending", "waiting"]:
            # ПЛАТЕЖ В ОЖИДАНИИ
            confirmation_url = payment_info.get("confirmation_url")
            if not confirmation_url:
                # Если ссылка потеряна, пробуем создать новый платеж
                logger.warning(f"⚠️ Ссылка на оплату не найдена для {payment_id}")
                await query.answer("🔄 Создаю новый платеж...")
                return await pay_package_callback(update, context)
            
            message = f"""
⏳ <b>ПЛАТЕЖ ОЖИДАЕТ ОПЛАТЫ</b>

{package['emoji']} <b>Пакет: {package['links']} ссылок</b>
💰 Сумма: {package['price']}₽
📋 ID платежа: <code>{payment_id}</code>
📊 Статус: {status}

💳 Для завершения оплаты нажмите кнопку ниже
"""
            keyboard = [
                [InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=confirmation_url)],
                [InlineKeyboardButton("🔄 ПРОВЕРИТЬ СНОВА", callback_data=f"check_package_{payment_id}_{package_id}")],
                [InlineKeyboardButton("◀️ НАЗАД", callback_data="buy_invite_packages")]
            ]
        else:
            # ОШИБКА ИЛИ ПЛАТЕЖ НЕ НАЙДЕН
            message = f"""
❌ <b>ПЛАТЕЖ НЕ НАЙДЕН</b>

Платеж <code>{payment_id}</code> не найден или произошла ошибка.

Попробуйте создать новый платеж.
"""
            keyboard = [
                [InlineKeyboardButton("📦 ВЫБРАТЬ ПАКЕТ", callback_data="buy_invite_packages")],
                [InlineKeyboardButton("◀️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
            ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_PAYMENT_SCREEN
        
    except Exception as e:
        logger.error(f"❌ Ошибка в check_package_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return BUY_PACKAGES

# ============================================
# ✅ ЭКРАН: ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ПАКЕТА (старая версия для совместимости)
# ============================================

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старая версия для обратной совместимости"""
    try:
        query = update.callback_query
        await query.answer("🔄 Перенаправляю...")
        
        parts = query.data.split("_")
        payment_id = parts[3]
        package_id = parts[4]
        
        # Перенаправляем на новую функцию
        new_query = update
        new_query.callback_query.data = f"check_package_{payment_id}_{package_id}"
        return await check_package_callback(new_query, context)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в process_package_payment_callback: {e}")
        return INVITES_LIST

# ============================================
# 👤 ЭКРАН: МЕНЮ ПРОФИЛЯ ДРУГА
# ============================================

def get_friend_by_id(context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> Optional[dict]:
    invites = context.user_data.get("sexual_invites", [])
    return next((inv for inv in invites if inv.get("friend_id") == friend_id), None)

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # Получаем ссылку на профиль друга
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

# ============================================
# 💰 ЭКРАН: ОПЛАТА ДОСТУПА
# ============================================

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
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

# ============================================
# 📊 ЭКРАН: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================
# 🔞 ЭКРАН: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # Добавляем ссылку на профиль друга
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

# ============================================
# 🧬 ЭКРАН: МЕНЮ 4F-КЛЮЧЕЙ ДЛЯ ДРУГА
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================
# 📘 ЭКРАН: ОБУЧАЙКА 4F
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================
# 💳 ЭКРАН: ПОКУПКА 4F-КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================
# 💳 ЭКРАН: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================
# 🔑 ЭКРАН: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================
# 🔄 ВОЗВРАТ В ИНТИМНЫЙ ПРОФИЛЬ (НОВАЯ ФУНКЦИЯ)
# ============================================

async def back_to_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в интимный профиль"""
    try:
        query = update.callback_query
        await query.answer("🔄 Возвращаюсь в интимный профиль...")
        
        # Просто вызываем функцию показа интимного профиля
        # Она сама загрузит профиль по коду из profile_data или profile
        return await show_my_sexual_profile(update, context)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в back_to_sexual_profile_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return RESULTS_SCREEN

# ============================================
# ⬅️ ВОЗВРАТЫ И ЗАГЛУШКИ
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        return await show_results_screen(update, context)
    except Exception as e:
        logger.error(f"❌ Ошибка в back_to_results_callback: {e}")
        return RESULTS_SCREEN

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        return RESULTS_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в dummy_callback: {e}")
        return RESULTS_SCREEN

# ===== ЭКСПОРТ =====
__all__ = [
    # Константы
    'SEXUAL_DIVIDER',
    'FREE_INVITE_LIMIT',
    'FRIEND_ACCESS_PRICE',
    'FOUR_F_PRICE',
    'INVITE_PACKAGES',
    'PROFILE_DISK_LINKS',
    'FOUR_F_DESCRIPTIONS',
    'SEXUAL_STATES',
    'SEXUAL_PROFILE_SCREEN',
    'SEXUAL_INVITES_LIST',
    'SEXUAL_FRIEND_PROFILE',
    'FOUR_F_PAYMENT_SCREEN',
    'FOUR_F_CONTENT_SCREEN',
    
    # Функции для работы с БД
    'save_invite_to_api',
    'find_invite_in_api',
    'update_invite_in_api',
    'get_user_invites_from_api',
    
    # Функции для работы с профилями
    'get_disk_link_by_profile',
    'get_disk_link',
    'load_intimate_profile',
    'load_friend_intimate_profile',
    'format_intimate_profile_part1',
    'format_intimate_profile_part2',
    'format_intimate_profile_part3',
    'format_friend_intimate_profile',
    'get_friend_emergency_profile',
    'get_emergency_profile',
    'check_available_sexual_profiles',
    
    # Функции для 4F
    'load_4f_content',
    
    # Функции для приглашений
    'get_user_invites',
    'count_free_friends',
    'init_test_data',
    'get_user_limits',
    'can_create_invite',
    
    # Основные callback-обработчики
    'show_my_sexual_profile',
    'sexual_invite_start',
    'copy_invite_callback',
    'check_invite_callback',
    'create_invite_callback',
    'send_invite_callback',
    'my_invites_callback',
    'four_f_main_menu_callback',
    'four_f_detailed_callback',
    'check_status_callback',
    'buy_invite_packages_callback',
    'pay_package_callback',
    'process_package_payment_callback',
    'friend_menu_callback',
    'show_payment_access_screen',
    'standard_profile_callback',
    'intimate_profile_callback',
    'four_f_menu_callback',
    'four_f_explanation_callback',
    'buy_4f_key_callback',
    'process_payment_callback',
    'open_4f_key_callback',
    'back_to_results_callback',
    'back_to_sexual_profile_callback',
    'check_package_callback',
    'dummy_callback',
    
    # Вспомогательные функции
    'split_long_message',
    'safe_send_message',
    
    # Функции платежей
    'generate_payment_id',
    'create_yookassa_invoice',
    
    # Функции экранов
    'show_results_screen',
]

# ===== ВНИМАНИЕ: Этот файл не предназначен для самостоятельного запуска! =====
# Удалена функция main() и весь код запуска бота
# Используйте этот файл только для импорта в основной бот
