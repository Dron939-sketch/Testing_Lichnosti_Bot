#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА: ПУТЬ К САМОПОЗНАНИЮ
ПОЛНАЯ ИНТЕГРАЦИЯ:
- 4 этапа адаптивного тестирования
- Персональное описание профиля
- 18+ интимные профили (36 профилей на Яндекс.Диске)
- 4F-ключи для управления состояниями
- Система приглашений для друзей

ВЕРСИЯ 6.0: ИНТЕГРАЦИЯ С ИНТИМНЫМ МОДУЛЕМ 19.0
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
from typing import Dict, List, Optional, Any

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

CLARIFICATION_QUESTIONS = {
    "stage1_ext": "Вы сказали, что ориентируетесь на внешние сигналы...",
    "stage1_int": "Вы отметили важность внутренних ощущений...",
    # ... остальные вопросы
}

STAGE1_FEEDBACK = {
    "EXTERNAL": "Вы ориентируетесь на внешние сигналы...",
    "INTERNAL": "Вы доверяете внутренним ощущениям...",
    "SYMBOLIC": "Вы видите символы и знаки...",
    "MATERIAL": "Вы цените материальные аспекты..."
}

STAGE2_FEEDBACK = {
    1: "Первый уровень мышления...",
    3: "Третий уровень...",
    5: "Пятый уровень...",
    7: "Седьмой уровень...",
    9: "Девятый уровень..."
}

STAGE3_FEEDBACK = "Ваш стиль поведения..."
STAGE4_ANALYSIS_SCREEN = "Анализ вашей точки роста..."

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
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
AUTHOR_LINK = "https://t.me/meysternlp"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "ваш_shop_id")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "ваш_secret_key")
API_URL = os.getenv("API_URL", "http://localhost:8000")
GIFT_PDF_LINK = os.getenv("GIFT_PDF_LINK", "https://disk.yandex.ru/d/example")

SHARE_TEXT = "🔮 Узнай свой психологический профиль за 15 минут"
GIFT_SCREEN_TEXT = "🎁 Ваш подарок готов!"

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def get_disk_link_by_profile(profile_code: str) -> str:
    """
    Умная функция поиска ссылки на Яндекс.Диск по коду профиля
    Поддерживает разные форматы: SA-5_INT, SA_5_INT, sa-5-int и т.д.
    """
    if not profile_code:
        logger.warning("⚠️ profile_code пустой, использую default")
        return PROFILE_DISK_LINKS["default"]
    
    # Приводим к верхнему регистру
    profile_upper = profile_code.upper().strip()
    logger.debug(f"🔍 Поиск ссылки для профиля: {profile_upper}")
    
    # 1. Прямое совпадение
    if profile_upper in PROFILE_DISK_LINKS:
        logger.debug(f"✅ Прямое совпадение: {profile_upper}")
        return PROFILE_DISK_LINKS[profile_upper]
    
    # 2. Замена _ на -
    profile_with_hyphen = profile_upper.replace('_', '-')
    if profile_with_hyphen in PROFILE_DISK_LINKS:
        logger.debug(f"✅ После замены _ на -: {profile_with_hyphen}")
        return PROFILE_DISK_LINKS[profile_with_hyphen]
    
    # 3. Замена - на _
    profile_with_underscore = profile_upper.replace('-', '_')
    if profile_with_underscore in PROFILE_DISK_LINKS:
        logger.debug(f"✅ После замены - на _: {profile_with_underscore}")
        return PROFILE_DISK_LINKS[profile_with_underscore]
    
    # 4. Поиск по начальным символам
    for key in PROFILE_DISK_LINKS:
        if key.startswith(profile_upper[:5]):
            logger.debug(f"✅ Найдено по начальным символам: {key}")
            return PROFILE_DISK_LINKS[key]
    
    # 5. Возвращаем default
    logger.warning(f"⚠️ Профиль {profile_code} не найден, использую default")
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

def load_intimate_profile() -> dict:
    """Загружает интимный профиль"""
    try:
        possible_paths = [
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
            os.path.join("sexual_18", "sa_5_int.json"),
        ]
        
        logger.info("🔍 Поиск файла профиля:")
        for path in possible_paths:
            logger.info(f"   Проверяем: {path}")
            if os.path.exists(path):
                logger.info(f"   ✅ НАЙДЕН: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"   📊 Профиль загружен: {data.get('profile_type', 'unknown')}")
                    return data
            logger.info(f"   ❌ Не найден")
        
        logger.error("❌ Файл профиля не найден!")
        return get_emergency_profile()
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}\n{traceback.format_exc()}")
        return get_emergency_profile()

def get_emergency_profile() -> dict:
    """Аварийный интимный профиль"""
    logger.info("🆘 Используется аварийный профиль")
    return {
        "profile_type": "SA-5_INT",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "role": "Жрец/Жрица сексуальной мистерии",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.",
        "sections": {}
    }

def load_friend_intimate_profile(friend_name: str, friend_profile: str = None) -> dict:
    """Загружает интимный профиль ДРУГА"""
    try:
        profile_data = load_intimate_profile()
        profile_data["profile_type"] = f"ТЕСТ-{friend_profile or 'SA-5_INT'}"
        profile_data["friend_name"] = friend_name
        profile_data["is_test_profile"] = True
        return profile_data
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
                    "Визуальный контакт"
                ]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": [
                    "Спешка",
                    "Отсутствие атмосферы",
                    "Прямолинейность"
                ]
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
    """Загружает контент для 4F-ключа"""
    try:
        base_triggers = {
            "1F": [
                "«Я понимаю, почему ты так реагируешь»",
                "«Ты имеешь полное право злиться»",
                "«Я на твоей стороне»"
            ],
            "2F": [
                "«Ты не обязан это делать»",
                "«Здесь безопасно»",
                "«Я подожду»"
            ],
            "3F": [
                "«Ты такой...» (искренний комплимент)",
                "Взгляд в глаза чуть дольше обычного",
                "Шёпот, интимный контекст"
            ],
            "4F": [
                "«Ты можешь заработать на этом»",
                "«Это твой шанс»",
                "«Никто не сделает это лучше тебя»"
            ]
        }
        
        base_analysis = {
            "1F": "Страх нападения возникает, когда человек не чувствует безопасности.",
            "2F": "Избегание — это способ справиться с перегрузкой.",
            "3F": "Влечение включается через игру, тайну, недосказанность.",
            "4F": "Желание заработать — это не про жадность, а про безопасность."
        }
        
        base_protocol = {
            "1F": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите",
            "2F": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте",
            "3F": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы",
            "4F": "1. Найдите его «голод»\n2. Покажите путь\n3. Уберите страхи"
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
            "description": "Произошла ошибка.",
            "triggers": [],
            "analysis": "",
            "protocol": "",
            "is_demo": True
        }

# ===== ФОРМАТИРОВАНИЕ ИНТИМНОГО ПРОФИЛЯ =====

def format_intimate_profile_part1(profile_data: dict, user_name: str) -> str:
    """Форматирует ПЕРВУЮ ЧАСТЬ интимного профиля"""
    try:
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
        
        section = sections.get("smells_tastes", {})
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
    """Форматирует ТРЕТЬЮ ЧАСТЬ интимного профиля"""
    try:
        message = ""
        sections = profile_data.get('sections', {})
        
        remaining_sections = [
            ("sounds", "🔊 ЗВУКИ"),
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
        
        # Финальный текст
        message += f"""

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что 🪞 СВОЁ отражение.
Но у <b>каждого друга</b> — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

<b>⬇️ КАК УВИДЕТЬ ИХ:</b>

<b>1.</b> 🚀 Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
<b>2.</b> 💌 Отправьте ссылку другу
<b>3.</b> 🔓 Друг проходит тест → вам открывается ЕГО профиль
"""
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования части 3: {e}")
        return "\n\nПроизошла ошибка загрузки."

def format_friend_intimate_profile(profile_data: dict, friend_name: str) -> str:
    """Форматирует интимный профиль ДРУГА"""
    try:
        friend_profile = profile_data.get('profile_type', 'ТЕСТ-5_INT')
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
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования профиля друга: {e}")
        return f"🔞 ПРОФИЛЬ {friend_name}\n\nПроизошла ошибка загрузки."

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====

user_invites = {}

def get_user_invites(user_id: int) -> list:
    """Получает список приглашений пользователя"""
    if user_id not in user_invites:
        user_invites[user_id] = []
        logger.info(f"👤 Создано хранилище для пользователя {user_id}")
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    """Считает количество бесплатных друзей"""
    invites = get_user_invites(user_id)
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    try:
        invites = get_user_invites(user_id)
        if len(invites) > 0:
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

def get_user_limits(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Получает лимиты пользователя"""
    return context.user_data.setdefault("invite_limits", {
        "free_used": 0,
        "total_purchased": 0,
        "paid_packages": []
    })

def can_create_invite(user_limits: dict, total_invites: int) -> tuple:
    """Проверяет, может ли пользователь создать приглашение"""
    free_used = user_limits["free_used"]
    
    if free_used < FREE_INVITE_LIMIT:
        remaining = FREE_INVITE_LIMIT - free_used
        return True, True, f"Осталось бесплатных: {remaining}"
    
    paid_available = user_limits["total_purchased"] - (total_invites - FREE_INVITE_LIMIT)
    if paid_available > 0:
        return True, False, f"Осталось платных: {paid_available}"
    
    return False, False, "Лимит исчерпан. Купите пакет ссылок."

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
    """Создает счет в ЮKassa"""
    try:
        logger.info(f"💰 Создание счета: {payment_id}, сумма: {amount}, пользователь: {user_id}")
        
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            logger.warning("⚠️ ЮKassa не настроена, используем демо-режим")
            return {
                "success": True,
                "payment_id": payment_id,
                "confirmation_url": "https://test.payment.url",
                "amount": amount,
                "status": "pending"
            }
        
        # Здесь должна быть реальная интеграция с ЮKassa
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

# ===== ФУНКЦИИ ТЕСТА =====

def calculate_profile_final(user_data: dict) -> dict:
    """Рассчитывает финальный профиль"""
    # Упрощенная версия для демо
    return {
        "display_name": "SA-5_INT",
        "type_code": "SA",
        "level": 5,
        "dilts_code": "INT"
    }

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
    # Переходим к следующему этапу
    return RESULTS

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает введение в 1 этап"""
    query = update.callback_query
    await query.answer()
    
    text = """
🧠 <b>ЭТАП 1: ВАШЕ ВОСПРИЯТИЕ</b>

Как вы воспринимаете мир?
Что для вас первично?

Ответьте на несколько вопросов,
и я пойму ваш базовый тип восприятия.
"""
    keyboard = [
        [InlineKeyboardButton("📖 Подробнее", callback_data="stage1_details")],
        [InlineKeyboardButton("🚀 Начать", callback_data="start_stage_1")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает детали 1 этапа"""
    query = update.callback_query
    await query.answer()
    
    text = """
📖 <b>О ВОСПРИЯТИИ</b>

Я определю ваш доминирующий канал:
• Внешний - ориентир на других
• Внутренний - опора на себя
• Символический - поиск смыслов
• Материальный - ценность вещей
"""
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
    
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задает вопрос 1 этапа"""
    query = update.callback_query
    await query.answer()
    
    questions = [
        "Когда вы принимаете важное решение, на что вы больше опираетесь?",
        "Что для вас важнее в общении с людьми?",
        "Как вы обычно оцениваете результаты своей работы?"
    ]
    
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(questions):
        return await finish_stage_1(update, context)
    
    question = questions[current]
    
    keyboard = [
        [InlineKeyboardButton("🧠 На мнение авторитетов", callback_data="stage1_a")],
        [InlineKeyboardButton("💭 На свои ощущения", callback_data="stage1_b")],
        [InlineKeyboardButton("🔮 На символы и знаки", callback_data="stage1_c")],
        [InlineKeyboardButton("💰 На материальный результат", callback_data="stage1_d")]
    ]
    
    await query.edit_message_text(
        f"Вопрос {current + 1}/{len(questions)}:\n\n{question}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ 1 этапа"""
    query = update.callback_query
    await query.answer()
    
    answer = query.data
    context.user_data.setdefault("stage1_answers", []).append(answer)
    context.user_data["stage1_current"] = context.user_data.get("stage1_current", 0) + 1
    
    return await ask_stage_1_question(update, context)

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает 1 этап"""
    query = update.callback_query
    await query.answer()
    
    # Определяем тип восприятия (упрощенно)
    answers = context.user_data.get("stage1_answers", [])
    perception_type = "EXTERNAL"  # По умолчанию
    
    context.user_data["perception_type"] = perception_type
    context.user_data.setdefault("scores", {})[perception_type] = 5
    
    text = f"""
✅ <b>ЭТАП 1 ЗАВЕРШЕН</b>

{STAGE1_FEEDBACK.get(perception_type, "Спасибо за ответы!")}

Переходим к этапу 2?
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Перейти к этапу 2", callback_data="show_stage_2_intro")],
        [InlineKeyboardButton("📖 Подробнее", callback_data="stage2_details")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

# Упрощенные функции для остальных этапов
async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🧠 <b>ЭТАП 2: ВАШЕ МЫШЛЕНИЕ</b>\n\nОпределим уровень абстракции вашего мышления."
    keyboard = [[InlineKeyboardButton("🚀 Начать", callback_data="start_stage_2")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "📖 <b>О МЫШЛЕНИИ</b>\n\nУровни от конкретного до абстрактного."
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage2_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_stage_2_intro(update, context)

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "Вопрос этапа 2: Выберите утверждение..."
    keyboard = [[InlineKeyboardButton("Вариант 1", callback_data="stage2_1")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await finish_stage_2(update, context)

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "✅ Этап 2 завершен. Переходим к этапу 3?"
    keyboard = [[InlineKeyboardButton("🚀 Перейти к этапу 3", callback_data="show_stage_3_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🧠 <b>ЭТАП 3: ВАШЕ ПОВЕДЕНИЕ</b>"
    keyboard = [[InlineKeyboardButton("🚀 Начать", callback_data="start_stage_3")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "📖 <b>О ПОВЕДЕНИИ</b>"
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage3_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_stage_3_intro(update, context)

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "Вопрос этапа 3..."
    keyboard = [[InlineKeyboardButton("Вариант", callback_data="stage3_1")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await finish_stage_3(update, context)

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "✅ Этап 3 завершен. Переходим к этапу 4?"
    keyboard = [[InlineKeyboardButton("🚀 Перейти к этапу 4", callback_data="show_stage_4_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🧠 <b>ЭТАП 4: ТОЧКА РОСТА</b>"
    keyboard = [[InlineKeyboardButton("🚀 Начать", callback_data="start_stage_4")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "📖 <b>О ТОЧКЕ РОСТА</b>"
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_stage4_intro")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_stage_4_intro(update, context)

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "Вопрос этапа 4..."
    keyboard = [[InlineKeyboardButton("Вариант", callback_data="stage4_1")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await finish_stage_4(update, context)

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Рассчитываем финальный профиль
    profile_data = calculate_profile_final(context.user_data)
    context.user_data["profile_data"] = profile_data
    
    return await show_results_screen(update, context)

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

# ===== ФУНКЦИИ ИНТИМНОГО МОДУЛЯ =====

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль - 3 ЧАСТИ, КНОПКИ НА ЧАСТИ 3"""
    try:
        query = update.callback_query
        await query.answer()
        logger.info(f"👤 Пользователь {query.from_user.id} открыл интимный профиль")
        
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
        
        # Кнопки для части 3
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ-ПРИГЛАШЕНИЕ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 ПОСМОТРЕТЬ МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ НАЗАД В ПРОФИЛЬ", callback_data="back_to_results")]
        ]
        navigation_keyboard = InlineKeyboardMarkup(keyboard)
        
        chat_id = query.message.chat_id
        
        # Отправляем часть 1
        try:
            await query.edit_message_text(
                message_part1,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при редактировании: {e}")
            await safe_send_message(chat_id, message_part1, context)
        
        await asyncio.sleep(1)
        
        # Отправляем часть 2
        if message_part2.strip():
            await safe_send_message(chat_id, message_part2, context)
            await asyncio.sleep(1)
        
        # Отправляем часть 3 с кнопками
        if message_part3.strip():
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
                if i < len(parts) - 1:
                    await asyncio.sleep(0.5)
        
        return MY_SEXUAL_PROFILE
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_sexual_profile_callback: {e}\n{traceback.format_exc()}")
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
        
        total_invites = len([inv for inv in invites if inv.get("status") == "active" or inv.get("status") == "used"])
        
        can_create, is_free, limit_message = can_create_invite(user_limits, total_invites)
        
        if not can_create:
            await query.answer("❌ Лимит ссылок исчерпан!", show_alert=True)
            return await buy_invite_packages_callback(update, context)
        
        profile = context.user_data.get("profile_data", {"display_name": "SA-5_INT"})
        profile_code = profile.get('display_name', 'SA-5_INT')
        
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
            "invite_type": invite_type
        }
        
        invites.insert(0, invite_data)
        
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
        
        keyboard = [
            [InlineKeyboardButton("✈️ ОТПРАВИТЬ ДРУГУ", url=share_url)],
            [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return INVITES_LIST
    except Exception as e:
        logger.error(f"❌ Ошибка в create_invite_callback: {e}")
        return INVITES_LIST

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 МОИ ОТРАЖЕНИЯ"""
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
        
        user_profile = context.user_data.get("profile_data", {"display_name": "SA-5_INT"})
        user_profile_code = user_profile.get('display_name', 'SA-5_INT')
        user_profile_link = get_disk_link_by_profile(user_profile_code)
        
        message = f"""<b>🪞 МОИ ОТРАЖЕНИЯ</b>
────────────────

<b>📊 СТАТИСТИКА</b>
🪞 Ссылок зеркал: {total_invites}
👥 Посмотрелись в зеркало: {total_reflections}

<b>🪞 МОЁ ОТРАЖЕНИЕ</b>
📌 Профиль: {user_profile_code}
📁 Диск:
{user_profile_link}
"""

        if used_invites:
            message += f"""
<b>👥 ОТРАЖЕНИЯ ТЕХ, КТО ПОСМОТРЕЛСЯ В ВАШЕ ЗЕРКАЛО ({total_reflections})</b>
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
<b>👥 ОТРАЖЕНИЯ ТЕХ, КТО ПОСМОТРЕЛСЯ В ВАШЕ ЗЕРКАЛО (0)</b>

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
        
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_invites_callback: {e}")
        return INVITES_LIST

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 Главное меню 4F-ключей"""
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
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_main_menu_callback: {e}")
        return INVITES_LIST

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 Подробное описание 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_DETAILED
        
        example_link = get_disk_link_by_profile("SA-3_CON")
        
        message = f"""
🔥 <b>1F - ЯРОСТЬ / НАПАДЕНИЕ</b>
<i>Стимулы, запускающие агрессию</i>

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Критика при свидетелях
   • Обесценивание его усилий
   • Игнорирование границ

🔑 ЧТО ДАЁТ КЛЮЧ:
   • Список его личных триггеров
   • 3 фразы-гасителя
   • Технику «Торможение»
────────────────────
🏃 <b>2F - СТРАХ / БЕГСТВО</b>

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования

🔑 ЧТО ДАЁТ КЛЮЧ:
   • 3 якоря безопасности
   • Технику «Безопасная среда»
────────────────────
🧬 <b>3F - СЕКС / ЖЕЛАНИЕ</b>

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

🎯 ПУСКОВЫЕ КЛЮЧИ:
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка

🔑 ЧТО ДАЁТ КЛЮЧ:
   • 3 фразы-мотиватора
   • Технику просьбы
   • Сценарий «Топливо»
────────────────────
📎 <b>ПРИМЕР ОПИСАНИЯ:</b>
{example_link}
"""
        
        keyboard = [
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

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка пакетов приглашений"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = BUY_PACKAGES
        
        message = f"""
💎 <b>ПАКЕТЫ ПРИГЛАШЕНИЙ</b>

<b>🆓 Бесплатные ссылки закончились!</b>
У вас было {FREE_INVITE_LIMIT} бесплатные ссылки.

<b>Выберите пакет для продолжения:</b>

"""
        
        for links, data in INVITE_PACKAGES.items():
            popular = " 🔥 ХИТ" if data["popular"] else ""
            price_per_link = data["price"] // data["links"]
            message += f"""
{data['emoji']} <b>{data['links']} ссылок</b> — {data['price']}₽{popular}
   💎 {price_per_link}₽ за ссылку
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
    """Оплата пакета"""
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

✅ После оплаты ссылки будут добавлены
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
    """Обработка оплаты пакета"""
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

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        invite_id = query.data.replace("check_status_", "")
        
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

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню друга"""
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
        
        friend_disk_link = get_disk_link_by_profile(friend_profile)
        
        message = f"""
👤 <b>{friend_name}</b>

📊 {friend_profile}
💎 {'🔓' if access_status == 'free' else '💰'}

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
    """Объяснение 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MENU
        
        keyboard = []
        friend_id = context.user_data.get("current_friend_id")
        
        if friend_id:
            keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"friend_{friend_id}")])
        else:
            keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data="my_invites")])
        
        await query.edit_message_text(
            FOUR_F_SHORT,
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
    """Обработка платежа за 4F-ключ"""
    try:
        query = update.callback_query
        await query.answer("💳 Подключаюсь...")
        
        parts = query.data.split("_")
        payment_id = parts[2]
        friend_id = int(parts[3])
        function = parts[4]
        
        # В демо-режиме сразу разблокируем ключ
        for inv in context.user_data.get("sexual_invites", []):
            if inv.get("friend_id") == friend_id:
                if "purchased_functions" not in inv:
                    inv["purchased_functions"] = []
                if function not in inv["purchased_functions"]:
                    inv["purchased_functions"].append(function)
                break
        
        # Перенаправляем на открытие ключа
        new_query = update
        new_query.callback_query.data = f"open_4f_{friend_id}_{function}"
        return await open_4f_key_callback(new_query, context)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в process_payment_callback: {e}")
        return FOUR_F_PAYMENT_SCREEN

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие 4F-ключа"""
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

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    return await show_results_screen(update, context)

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для нереализованных функций"""
    query = update.callback_query
    await query.answer("✅ Демо-режим")
    return RESULTS

# ===== ОСНОВНЫЕ ФУНКЦИИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основная команда /start"""
    user = update.effective_user
    logger.info(f"🚀 /start вызван пользователем {user.id} (@{user.username})")
    
    # Инициализируем данные
    context.user_data.clear()
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    # Инициализируем интимные данные
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    get_user_limits(context)
    
    welcome_text = f"""
{user.first_name}, привет! 👋

<b>🧠 Я — Виртуальный психолог Вариатика.</b>

🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.
👁️ Увидите скрытые паттерны, которые управляют вашими решениями.

<b>📊 Вас ждёт:</b>

1️⃣ Адаптивный тест (4 этапа)
   ↳ Поймёте свой уникальный профиль

2️⃣ Персональные материалы
   ↳ Узнаете куда направлять усилия

3️⃣ 🔞 Интимный профиль и 4F-ключи
   ↳ Поймёте свою сексуальную природу

🚀 Начнём исследование?
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать исследование →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А зачем это вообще?", callback_data="why_details")]
    ]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return None

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    return await show_stage_1_intro(update, context)

async def why_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробности о тесте"""
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
    
    keyboard = [[InlineKeyboardButton("👌 Понял(а). Начинаем →", callback_data="start_test")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text("❌ Тест отменен. /start чтобы начать заново")
    return ConversationHandler.END

# ===== ОСНОВНАЯ ФУНКЦИЯ =====

def main():
    """Запуск бота"""
    print("\n" + "="*70)
    print("🧠 ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА v6.0")
    print("="*70)
    print("🔞 ПОЛНАЯ ИНТЕГРАЦИЯ С ИНТИМНЫМ МОДУЛЕМ 19.0")
    print("✅ 36 профилей на Яндекс.Диске")
    print("✅ 4 этапа тестирования")
    print("✅ Интимные профили и 4F-ключи")
    print("✅ Система приглашений для друзей")
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
            
            # Результаты теста
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
            
            # ИНТИМНЫЙ МОДУЛЬ
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
                CallbackQueryHandler(standard_profile_callback, pattern='^std_'),
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
                CallbackQueryHandler(dummy_callback, pattern='^check_payment_'),
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
    
    # Добавляем общие обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(why_details_callback, pattern="^why_details$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(conv_handler)
    
    print("\n🚀 Бот запущен! Версия 6.0")
    print("="*70)
    logger.info("✅ Бот успешно запущен")
    
    # Запускаем бота
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query']
    )

if __name__ == "__main__":
    main()
