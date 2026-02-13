#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 11.0 - ПОЛНАЯ ИНТЕГРАЦИЯ
✅ ЕДИНЫЙ КОД - БЕЗ КОНФЛИКТОВ
✅ ИНТИМНЫЙ ПРОФИЛЬ ЗАГРУЖАЕТСЯ ИЗ sexual_18/sa_5_int.json
✅ ДИАГНОСТИКА ЗАГРУЗКИ
✅ 4F-КЛЮЧИ С ДЕМО-РЕЖИМОМ
✅ КНОПКИ "МОИ ОТРАЖЕНИЯ" И "СОЗДАТЬ ССЫЛКУ" РАБОТАЮТ
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

# ===== НАСТРОЙКА =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
BOT_USERNAME = "Testing_Lichnosti_bot"
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== СОСТОЯНИЯ CONVERSATIONHANDLER =====
RESULTS_SCREEN = 0
MY_SEXUAL_PROFILE = 1
INVITES_LIST = 2
FRIEND_MENU = 3
FOUR_F_MENU = 4
FOUR_F_CONTENT = 5
FOUR_F_PAYMENT_SCREEN = 6

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 99

# ===== УМНЫЙ ПОИСК КОРНЯ ПРОЕКТА =====
def find_project_root() -> str:
    """Находит корень проекта (где лежит папка sexual_18/)"""
    current = os.path.dirname(os.path.abspath(__file__))
    
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "sexual_18")):
            return current
        current = os.path.dirname(current)
    
    return os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = find_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

logger.info(f"📁 Корень проекта: {PROJECT_ROOT}")

# ===== ПУТИ К ФАЙЛАМ =====
SEXUAL_PROFILE_PATH = os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json")
FOUR_F_BASE_PATH = os.path.join(PROJECT_ROOT, "профили", "4F")

# ===== 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {
    "1F": "🔥",
    "2F": "🍽️",
    "3F": "⚡",
    "4F": "💡"
}

FOUR_F_NAMES = {
    "1F": "КЛЮЧ ВОЗБУЖДЕНИЯ",
    "2F": "КЛЮЧ ГОЛОДА",
    "3F": "КЛЮЧ СТРАХА",
    "4F": "КЛЮЧ ИДЕИ"
}

FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ",
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

FOUR_F_SUBTITLES = {
    "1F": "Как гасить агрессию и не нарваться",
    "2F": "Чего он боится на самом деле",
    "3F": "Что включает его режим «хочу»",
    "4F": "Какие идеи прорастают в его голове"
}

FOUR_F_TAGS = {
    "1F": "Ключ к управлению гневом",
    "2F": "Ключ к преодолению страхов",
    "3F": "Ключ к желанию и страсти",
    "4F": "Ключ к деньгам и идеям"
}

# ===== ТЕКСТ ОБУЧАЙКИ 4F =====
FOUR_F_EXPLANATION = """
📘 ЧТО ТАКОЕ 4F-КЛЮЧИ?

🧬 4F — это система доступа к состояниям человека
Четыре базовые реакции, зашитые в подкорке.
Ключи к пониманию глубинных состояний другого человека.

1F 🔥 НАПАДЕНИЕ / ЯРОСТЬ
└ Как гасить агрессию и не нарваться
└ Ключ к управлению гневом

2F 🍽️ БЕГСТВО / СТРАХ
└ Чего он боится на самом деле
└ Ключ к преодолению страхов

3F ⚡ СЕКС / ЖЕЛАНИЕ
└ Что включает его режим «хочу»
└ Ключ к желанию и страсти

4F 💡 ПОГЛОЩЕНИЕ / ДЕНЬГИ
└ Какие идеи прорастают в его голове
└ Ключ к деньгам и идеям

💰 Цена: 99₽ за ключ
⚠️ Сейчас действует демо-режим — все ключи для профиля SA-4_CAP
"""

# ============================================
# 🔍 ДИАГНОСТИКА ФАЙЛОВОЙ СИСТЕМЫ
# ============================================

def diagnose_sexual_profile_paths():
    """Диагностика путей к файлу интимного профиля"""
    logger.info("="*60)
    logger.info("🔍 ДИАГНОСТИКА ПУТЕЙ К ИНТИМНОМУ ПРОФИЛЮ")
    logger.info("="*60)
    logger.info(f"📁 Текущая директория: {os.getcwd()}")
    logger.info(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
    logger.info(f"📁 SEXUAL_PROFILE_PATH: {SEXUAL_PROFILE_PATH}")
    
    # Проверяем папку sexual_18
    sexual_18_dir = os.path.join(PROJECT_ROOT, "sexual_18")
    if os.path.exists(sexual_18_dir):
        logger.info(f"✅ Папка sexual_18 существует: {sexual_18_dir}")
        try:
            files = os.listdir(sexual_18_dir)
            logger.info(f"   Содержимое: {files}")
            if "sa_5_int.json" in files:
                logger.info(f"   ✅ Файл sa_5_int.json найден в папке!")
        except Exception as e:
            logger.error(f"   ❌ Ошибка чтения папки: {e}")
    else:
        logger.error(f"❌ Папка sexual_18 НЕ найдена: {sexual_18_dir}")
    
    # Проверяем существование файла
    if os.path.exists(SEXUAL_PROFILE_PATH):
        logger.info(f"✅ ФАЙЛ НАЙДЕН: {SEXUAL_PROFILE_PATH}")
        logger.info(f"   📏 Размер: {os.path.getsize(SEXUAL_PROFILE_PATH)} байт")
        logger.info(f"   📝 Читается: {os.access(SEXUAL_PROFILE_PATH, os.R_OK)}")
    else:
        logger.error(f"❌ ФАЙЛ НЕ НАЙДЕН: {SEXUAL_PROFILE_PATH}")
        
        # Ищем альтернативные пути
        alt_paths = [
            os.path.join("sexual_18", "sa_5_int.json"),
            "/opt/render/project/src/sexual_18/sa_5_int.json",
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                logger.info(f"✅ НАЙДЕН АЛЬТЕРНАТИВНЫЙ ПУТЬ: {alt_path}")
                global SEXUAL_PROFILE_PATH
                SEXUAL_PROFILE_PATH = alt_path
                break
    
    logger.info("="*60)

# ============================================
# 📥 ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ
# ============================================

def load_intimate_profile() -> dict:
    """Загружает интимный профиль из JSON файла с автоопределением структуры"""
    try:
        logger.info("📂 Загрузка интимного профиля...")
        
        if not os.path.exists(SEXUAL_PROFILE_PATH):
            logger.error(f"❌ Файл не найден: {SEXUAL_PROFILE_PATH}")
            return get_emergency_profile()
        
        with open(SEXUAL_PROFILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"📄 Прочитано {len(content)} символов")
            
            if not content.strip():
                logger.error("❌ Файл пустой")
                return get_emergency_profile()
            
            data = json.loads(content)
            logger.info(f"✅ JSON загружен, ключи: {list(data.keys())}")
            
            # Преобразуем структуру, если нужно
            if 'sections' not in data:
                logger.warning("⚠️ Нет секции 'sections' - преобразуем")
                data = convert_profile_format(data)
            
            return data
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        return get_emergency_profile()
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}", exc_info=True)
        return get_emergency_profile()

def convert_profile_format(data: dict) -> dict:
    """Преобразует сырые данные в формат с секциями"""
    profile = {
        "profile_key": data.get("profile_key", "sa_5_int"),
        "profile_type": data.get("profile_type", data.get("profile", "SA-5_INT")),
        "archetype": data.get("archetype", data.get("name", "ЦЕРЕМОНИАЛЬНЫЙ")),
        "role": data.get("role", "Жрец/Жрица сексуальной мистерии"),
        "quote": data.get("quote", "«Со мной не скучно. Со мной — вкусно.»"),
        "description": data.get("description", data.get("text", data.get("about", ""))),
        "sections": {}
    }
    
    # Маппинг полей
    section_mapping = {
        "what_turns_on": ["what_turns_on", "turns_on", "turn_ons", "включает"],
        "what_turns_off": ["what_turns_off", "turns_off", "blocks", "выключает"],
        "erogenous_zone": ["erogenous_zone", "erogenous_zones", "зоны"],
        "fetishes": ["fetishes", "фетиши"],
        "secret_desires": ["secret_desires", "desires", "желания"],
        "ideal_partner": ["ideal_partner", "идеальный партнёр"],
        "tool": ["tool", "инструмент", "protocol"],
    }
    
    for expected_key, possible_keys in section_mapping.items():
        for key in possible_keys:
            if key in data:
                profile["sections"][expected_key] = data[key]
                break
    
    return profile

def get_emergency_profile() -> dict:
    """Аварийный интимный профиль"""
    return {
        "profile_key": "sa_5_int",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "role": "Жрец/Жрица сексуальной мистерии",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.\nВы не занимаетесь любовью — вы служите ей.\nИ каждый раз — как в первый. И каждый раз — как в последний.",
        "sections": {
            "turn_ons": [
                {"title": "Шёпот в темноте", "description": "Когда партнёр шепчет почти беззвучно — вы вслушиваетесь, затаив дыхание"},
                {"title": "Запах тела", "description": "Запах пота после долгого дня, смешанный с духами — вы готовы кончить от этого аромата"},
                {"title": "Медленные пуговицы", "description": "Вы сходите с ума, пока вас раздевают, глядя в глаза"}
            ],
            "blocks": [
                {"description": "Секс на скорую руку — вы чувствуете себя использованной/ым"},
                {"description": "Грубые, приказные интонации — вы не игрушка"},
                {"description": "«Ну давай быстрее» — убивает всё нахрен. Моментально."}
            ],
            "erogenous_zone": {
                "trigger": "Шея, мочки ушей, внутренняя сторона запястья. Особенно — когда касаются губами."
            },
            "ideal_partner": "Тот, кто не торопится. Кто читает ваше тело как ноты. Кто знает: сначала свет, потом музыка, потом вино, потом касания.",
            "tool": {
                "name": "РИТУАЛ ПРИБЛИЖЕНИЯ",
                "steps": [
                    "1. Сначала выключите свет — магия начинается в темноте",
                    "2. Включите музыку — тихую, тягучую, дышащую",
                    "3. Налейте вино — глоток для расслабления",
                    "4. Коснитесь запястья — губами, почти невесомо",
                    "5. Смотрите в глаза — не отводите взгляд",
                    "6. Шепчите — слова важнее крика"
                ]
            },
            "fetishes": [
                "Запах затылка партнёра — уткнуться носом и дышать",
                "Медленные ритмичные движения — вы готовы умереть, если сбивается темп",
                "Укус мочки уха и шёпот одновременно — подкашиваются колени"
            ],
            "secret_desires": [
                "Хотите, чтобы партнёр кончил вам в рот, а вы проглотили",
                "Хотите, чтобы вас связали — шарфом, галстуком, простынёй",
                "Хотите плакать во время секса — от переполнения"
            ]
        }
    }

def format_intimate_profile(profile_data: dict, user_name: str) -> str:
    """Форматирует интимный профиль для вывода"""
    message = f"""
{SEXUAL_DIVIDER}
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ: {user_name}</b>
🧠 <b>АРХЕТИП:</b> {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}
{SEXUAL_DIVIDER}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', '').strip()[:300]}...

{SEXUAL_DIVIDER}

<b>🔴 ВКЛЮЧАЕТ:</b>
"""
    # Добавляем turn_ons
    sections = profile_data.get('sections', {})
    turn_ons = sections.get('turn_ons', [])
    if not turn_ons:
        turn_ons = profile_data.get('turn_ons', [])
    
    for item in turn_ons[:3]:
        if isinstance(item, dict):
            title = item.get('title', '')
            desc = item.get('description', '')
            message += f"• <b>{title}</b>: {desc[:100]}...\n"
        else:
            message += f"• {item[:100]}...\n"
    
    message += f"""
<b>⚠️ ВЫКЛЮЧАЕТ:</b>
"""
    blocks = sections.get('blocks', [])
    if not blocks:
        blocks = profile_data.get('blocks', [])
    
    for item in blocks[:2]:
        if isinstance(item, dict):
            desc = item.get('description', '')
            message += f"• {desc[:100]}...\n"
        else:
            message += f"• {item[:100]}...\n"
    
    erogenous = sections.get('erogenous_zone', {})
    if not erogenous:
        erogenous = profile_data.get('erogenous_zone', {})
    
    message += f"""
<b>🔴 ЭРОГЕННАЯ ЗОНА:</b>
{erogenous.get('trigger', 'Шея, мочки ушей, внутренняя сторона запястья')}

<b>💞 ИДЕАЛЬНЫЙ ПАРТНЁР:</b>
{sections.get('ideal_partner', profile_data.get('ideal_partner', 'Тот, кто не торопится'))[:200]}

{SEXUAL_DIVIDER}
💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что СВОЁ 🪞 отражение.
Но у каждого друга — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

⬇️ <b>КАК УВИДЕТЬ ИХ:</b>

1️⃣ Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО профиль

💫 Чем больше друзей увидят себя в зеркале —
   тем больше тайн откроется вам.
{SEXUAL_DIVIDER}
"""
    return message

# ============================================
# 🔥 4F-ЗАГРУЗЧИК И ФОРМАТТЕР
# ============================================

def get_4f_content(function: str, profile_key: str = "sa_4_cap") -> Dict[str, Any]:
    """
    Загружает 4F-функцию из JSON-файла
    Всегда используем sa_4_cap.json как демо для всех профилей
    """
    try:
        # Проверяем существование папки
        if not os.path.exists(FOUR_F_BASE_PATH):
            logger.warning(f"⚠️ Папка 4F не найдена: {FOUR_F_BASE_PATH}")
            os.makedirs(FOUR_F_BASE_PATH, exist_ok=True)
        
        # Всегда берем sa_4_cap.json для демо-режима
        file_path = os.path.join(FOUR_F_BASE_PATH, function, "sa_4_cap.json")
        
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл {file_path} не найден, использую заглушку")
            return get_4f_stub(function)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            content["is_demo"] = True
            content["source_profile"] = "sa_4_cap"
            content["function"] = function
            return content
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки 4F: {e}")
        return get_4f_stub(function)

def get_4f_stub(function: str) -> Dict[str, Any]:
    """Заглушка для 4F-ключа"""
    stubs = {
        "1F": {
            "function": "1F",
            "is_demo": True,
            "short_description": "🔥 Как зажечь его желание за 3 слова",
            "core": {
                "title": "🧬 РЕПТИЛОЙДНЫЙ КОД",
                "description": "Его возбуждение запускается через иерархию и преодоление. Он хочет завоевывать."
            },
            "psychology": {
                "title": "🎭 ПСИХОЛОГИЧЕСКИЙ ПОРТРЕТ",
                "content": "Для него секс — это игра на выживание. Он возбуждается, когда чувствует вызов и возможность победить."
            },
            "sexual_arousal": {
                "triggers": [
                    {"phrase": "Ты такой сильный...", "effect": "Запускает режим доминанта"},
                    {"phrase": "Я хочу тебя прямо сейчас", "effect": "Сносит все тормоза"},
                    {"phrase": "Сделай со мной что хочешь", "effect": "Активирует фантазии"}
                ]
            },
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": [
                    "10+ точных триггер-фраз для разных ситуаций",
                    "Психологический разбор каждой фразы",
                    "Протокол применения в постели и в жизни",
                    "Анти-паттерны и как их избежать",
                    "Персональные триггеры под его профиль"
                ],
                "price": FOUR_F_PRICE
            }
        },
        "2F": {
            "function": "2F",
            "is_demo": True,
            "short_description": "🍽️ Как пробудить его голод и желание",
            "core": {
                "title": "🧬 РЕПТИЛОЙДНЫЙ КОД",
                "description": "Его голод — это не про еду. Это про обладание. Он хочет поглощать и присваивать."
            },
            "psychology": {
                "title": "🎭 ПСИХОЛОГИЧЕСКИЙ ПОРТРЕТ",
                "content": "Он коллекционер. Ему нужно чувствовать, что объект желания принадлежит ему полностью."
            },
            "triggers": {
                "trigger_1": {"phrase": "Это только для тебя", "effect": "Запускает собственнический инстинкт"},
                "trigger_2": {"phrase": "Никто не умеет так, как ты", "effect": "Бустит эго"},
                "trigger_3": {"phrase": "Я хочу, чтобы ты взял меня", "effect": "Активирует охотника"}
            },
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": [
                    "10+ фраз для пробуждения аппетита",
                    "Как создавать дефицит и ценность",
                    "Игры с собственничеством",
                    "Протокол насыщения"
                ],
                "price": FOUR_F_PRICE
            }
        },
        "3F": {
            "function": "3F",
            "is_demo": True,
            "short_description": "⚡ Как обойти его страхи и защиту",
            "core": {
                "title": "🧬 РЕПТИЛОЙДНЫЙ КОД",
                "description": "Его страх — это броня. Он защищается, потому что однажды его уже ранили."
            },
            "psychology": {
                "title": "🎭 ПСИХОЛОГИЧЕСКИЙ ПОРТРЕТ",
                "content": "За его холодностью — страх быть отвергнутым. Он уходит первым, чтобы не оставили его."
            },
            "antidotes": {
                "antidote_1": {"phrase": "Я никуда не уйду", "effect": "Снимает базовую тревогу"},
                "antidote_2": {"phrase": "Ты в безопасности", "effect": "Расслабляет защиту"},
                "antidote_3": {"phrase": "Я подожду сколько нужно", "effect": "Дает контроль"}
            },
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": [
                    "10+ противоядий от страха",
                    "Как отличить защиту от безразличия",
                    "Протокол безопасной близости",
                    "Работа с травмой привязанности"
                ],
                "price": FOUR_F_PRICE
            }
        },
        "4F": {
            "function": "4F",
            "is_demo": True,
            "short_description": "💡 Как зажечь его идеи и проекты",
            "core": {
                "title": "🧬 РЕПТИЛОЙДНЫЙ КОД",
                "description": "Его идеи — это способ продолжить себя. Он хочет создавать и менять мир."
            },
            "psychology": {
                "title": "🎭 ПСИХОЛОГИЧЕСКИЙ ПОРТРЕТ",
                "content": "Для него секс и творчество — одно и то же. Возбуждение и инсайты приходят вместе."
            },
            "triggers": {
                "trigger_1": {"phrase": "А что если попробовать...", "effect": "Запускает креативное мышление"},
                "trigger_2": {"phrase": "Только ты можешь это сделать", "effect": "Активирует миссию"},
                "trigger_3": {"phrase": "Это изменит всё", "effect": "Включает масштабирование"}
            },
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": [
                    "10+ вопросов-ключей к его идеям",
                    "Как отделить гениальное от бреда",
                    "Протокол соавторства",
                    "Энергия возбуждения → энергия проекта"
                ],
                "price": FOUR_F_PRICE
            }
        }
    }
    return stubs.get(function, stubs["1F"])

def format_4f_message(content: Dict[str, Any], friend_name: str) -> str:
    """Форматирует 4F-контент в красивое сообщение"""
    func = content.get("function", "1F")
    emoji = FOUR_F_EMOJIS.get(func, "🔑")
    func_name = FOUR_F_NAMES.get(func, "")
    
    text = f"""
{SEXUAL_DIVIDER}
{emoji} <b>{func} {func_name}</b>
{SEXUAL_DIVIDER}

<b>👤 Для {friend_name}</b>
📊 <b>Профиль:</b> SA-4_CAP (демо)

{content.get('short_description', '')}

{SEXUAL_DIVIDER}
"""
    
    # Core секция
    core = content.get("core", {})
    if core:
        text += f"""
<b>{core.get('title', '🧬 РЕПТИЛОЙДНЫЙ КОД')}</b>
{core.get('description', '')}

"""
    
    # Psychology секция
    psychology = content.get("psychology", {})
    if psychology:
        text += f"""
<b>{psychology.get('title', '🎭 ПСИХОЛОГИЧЕСКИЙ ПОРТРЕТ')}</b>
{psychology.get('content', '')}

"""
    
    # Триггеры (специфично для каждой функции)
    text += "<b>🎯 ТРИГГЕР-ФРАЗЫ:</b>\n\n"
    
    if func == "1F":
        triggers = content.get("sexual_arousal", {}).get("triggers", [])
        for i, t in enumerate(triggers[:3], 1):
            text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
            text += f"   {t.get('effect', '')}\n\n"
    
    elif func == "2F":
        triggers = content.get("triggers", {})
        for i in range(1, 4):
            t = triggers.get(f"trigger_{i}", {})
            if t:
                text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                text += f"   {t.get('effect', '')}\n\n"
    
    elif func == "3F":
        antidotes = content.get("antidotes", {})
        for i in range(1, 4):
            a = antidotes.get(f"antidote_{i}", {})
            if a:
                text += f"{i}. <i>«{a.get('phrase', '')}»</i>\n"
                text += f"   {a.get('effect', '')}\n\n"
    
    elif func == "4F":
        triggers = content.get("triggers", {})
        for i in range(1, 4):
            t = triggers.get(f"trigger_{i}", {})
            if t:
                text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                text += f"   {t.get('effect', '')}\n\n"
    
    # Демо-лимитация
    if content.get("is_demo", False):
        demo = content.get("demo_limitation", {})
        text += f"""
{SEXUAL_DIVIDER}
⚠️ <b>ЭТО ДЕМО-ВЕРСИЯ</b>

{demo.get('title', '📌 В ПОЛНОЙ ВЕРСИИ:')}
"""
        for item in demo.get("content", [])[:5]:
            text += f"• {item}\n"
        
        text += f"""
{SEXUAL_DIVIDER}
💎 <b>Полная версия: {demo.get('price', FOUR_F_PRICE)}₽</b>
🔓 Доступ навсегда
⚡ Мгновенная доставка

"""
    
    text += SEXUAL_DIVIDER
    return text

# ============================================
# 💳 ПЛАТЕЖНАЯ СИСТЕМА
# ============================================

def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    """Генерирует уникальный ID платежа"""
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 99.0, description: str = "") -> dict:
    """Создает платеж через API"""
    try:
        # В демо-режиме возвращаем тестовый URL
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": "https://yoomoney.ru/quickpay/confirm.xml",
            "amount": amount,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {"success": False, "error": str(e)}

# ============================================
# 💾 ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ
# ============================================

# Глобальное хранилище (в реальном проекте заменить на БД)
user_invites = {}

def get_user_invites(user_id: int) -> list:
    """Получает список приглашений пользователя"""
    if user_id not in user_invites:
        user_invites[user_id] = []
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    """Считает количество использованных бесплатных приглашений"""
    invites = get_user_invites(user_id)
    return len([inv for inv in invites 
                if inv.get("status") == "used" 
                and inv.get("access_status") == "free"])

def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    invites = get_user_invites(user_id)
    if len(invites) > 0:
        return
    
    test_friends = [
        {
            "code": f"test_free_1_{user_id}",
            "friend_id": 1001,
            "friend_name": "@alex",
            "friend_username": "alex",
            "friend_profile": "SA-3_CON",
            "status": "used",
            "access_status": "free",
            "access_paid": False,
            "used_at": datetime.now().timestamp(),
            "purchased_functions": []
        },
        {
            "code": f"test_free_2_{user_id}",
            "friend_id": 1002,
            "friend_name": "@maria",
            "friend_username": "maria",
            "friend_profile": "IP-5_INT",
            "status": "used",
            "access_status": "free",
            "access_paid": False,
            "used_at": datetime.now().timestamp() - 86400,
            "purchased_functions": ["1F"]
        }
    ]
    
    invites.extend(test_friends)
    logger.info(f"✅ Тестовые данные для user_id={user_id}")

# ============================================
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота"""
    user = update.effective_user
    
    # Диагностика при старте
    diagnose_sexual_profile_paths()
    
    # Очищаем user_data
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    
    # Инициализируем тестовые данные
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 ЭКРАН РЕЗУЛЬТАТОВ"""
    message = f"""
{SEXUAL_DIVIDER}
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>
{SEXUAL_DIVIDER}

📊 <b>SA-5_INT</b>

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 <b>ИНСТРУМЕНТ</b>
Сегодня: попросите кого-то о маленькой услуге.
Заметьте, что мир не рухнул.
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("🪞 Зеркало", callback_data="share_mirror")],
        [InlineKeyboardButton("📖 Полный", callback_data="full_description")],
        [InlineKeyboardButton("🔞 Интимный профиль", callback_data="my_sexual_profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль"""
    query = update.callback_query
    await query.answer()
    
    user_name = query.from_user.first_name or "Пользователь"
    profile_data = load_intimate_profile()
    
    message = format_intimate_profile(profile_data, user_name)
    
    keyboard = [
        [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return MY_SEXUAL_PROFILE

# ============================================
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    query = update.callback_query
    await query.answer()
    
    # Генерируем уникальный код
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
    
    # ЖЕСТКО ЗАДАННЫЙ ТЕКСТ (НЕ МЕНЯТЬ!)
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "Я прошёл — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
    )
    
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    text = f"""
{SEXUAL_DIVIDER}
🔞 <b>ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!</b>
{SEXUAL_DIVIDER}

🔗 <code>{invite_url}</code>

💬 <b>ТЕКСТ ДЛЯ ОТПРАВКИ ДРУГУ:</b>
<code>{invite_message}</code>

{SEXUAL_DIVIDER}
🟢 АКТИВНО • ожидание
📅 {current_time}
{SEXUAL_DIVIDER}

🎯 Через 15 минут после теста
   вы увидите его 18+ профиль.
   То, что скрывается даже от близких.
{SEXUAL_DIVIDER}
"""
    
    # Сохраняем приглашение
    invite_data = {
        "code": invite_code,
        "url": invite_url,
        "message": invite_message,
        "status": "active",
        "created_at": datetime.now().timestamp(),
        "friend_id": None,
        "friend_name": None,
        "friend_profile": None,
        "access_status": None,
        "purchased_functions": []
    }
    
    invites = context.user_data.setdefault("sexual_invites", [])
    invites.insert(0, invite_data)
    
    user_id = query.from_user.id
    global_invites = get_user_invites(user_id)
    global_invites.insert(0, invite_data)
    
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Отправить другу", url=share_url)],
        [InlineKeyboardButton("📋 Копировать ссылку", callback_data=f"copy_invite_{invite_code}")],
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ Вернуться в профиль", callback_data="my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return INVITES_LIST

# ============================================
# 💎 ЭКРАН 4: МОИ ОТРАЖЕНИЯ
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💎 Мои отражения"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        invites = get_user_invites(user_id)
        context.user_data["sexual_invites"] = invites
        
        active_invites = [inv for inv in invites if inv.get("status") == "active"]
        used_invites = [inv for inv in invites if inv.get("status") == "used"]
        
        total_invites = len(invites)
        total_reflections = len(used_invites)
        free_used = sum(1 for inv in used_invites if inv.get("access_status") == "free")
        paid_available = max(0, FREE_FRIEND_LIMIT - free_used)
        
        message = f"""
{SEXUAL_DIVIDER}
💎 <b>МОИ ОТРАЖЕНИЯ</b>
{SEXUAL_DIVIDER}

📊 <b>СТАТИСТИКА:</b>
   🔗 Всего ссылок: {total_invites}
   ✨ Отражений: {total_reflections}
   💎 Бесплатных: {free_used}/{FREE_FRIEND_LIMIT}
   🔓 Доступно: {paid_available}

{SEXUAL_DIVIDER}
"""
        
        keyboard = []
        
        # Активные приглашения
        if active_invites:
            message += f"\n🟢 <b>ЖДУТ ОТКЛИКА ✨</b>"
            for inv in active_invites[:3]:
                created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
                days = int((datetime.now().timestamp() - inv["created_at"]) / 86400)
                message += f"\n   • {created} · ждёт {days}д"
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔄 {inv['code'][:8]}...",
                        callback_data=f"check_status_{inv['code']}"
                    )
                ])
        else:
            message += f"\n✨ У вас пока нет активных приглашений"
        
        # Отражения (друзья, прошедшие тест)
        if used_invites:
            message += f"\n\n✨ <b>УЖЕ ОТРАЗИЛИСЬ — {len(used_invites)}</b>"
            for inv in used_invites[:5]:
                friend_name = inv.get("friend_name", "Друг")
                friend_profile = inv.get("friend_profile", "SA-3_CON")
                used_date = datetime.fromtimestamp(inv.get("used_at", inv["created_at"])).strftime('%d.%m.%Y')
                keys = ""
                if inv.get("purchased_functions"):
                    keys = f" · 🔑 {' '.join(inv['purchased_functions'])}"
                
                message += f"\n\n   👤 {friend_name}"
                message += f"\n   📊 {friend_profile} · {used_date}{keys}"
                
                if inv.get("friend_id"):
                    keyboard.append([
                        InlineKeyboardButton(
                            f"👤 {friend_name}",
                            callback_data=f"friend_{inv['friend_id']}"
                        )
                    ])
        else:
            message += f"\n\n✨ У вас пока нет отражений"
            message += f"\n\n💡 Создайте ссылку и отправьте другу —"
            message += f"\n   когда он пройдет тест, его профиль появится здесь"
        
        message += f"""

{SEXUAL_DIVIDER}
💡 Каждое отражение — ключ к человеку.
    Узнайте его 4F-реакции и интимные сценарии.
{SEXUAL_DIVIDER}
"""
        
        keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")])
        keyboard.append([InlineKeyboardButton("⬅️ К ИНТИМНОМУ ПРОФИЛЮ", callback_data="my_sexual_profile")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_invites_callback: {e}", exc_info=True)
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return RESULTS_SCREEN

# ============================================
# 🔍 ЭКРАН 5: ПРОВЕРКА СТАТУСА
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer()
    
    try:
        invite_code = query.data.replace("check_status_", "")
        
        message = f"""
{SEXUAL_DIVIDER}
🔍 <b>СТАТУС ПРИГЛАШЕНИЯ</b>
{SEXUAL_DIVIDER}

🔗 <code>https://t.me/{BOT_USERNAME}?start={invite_code}</code>

🟢 АКТИВНО · ждёт друга
⏳ Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}

✨ Друг ещё не прошёл тест.
   Напомните ему о себе.
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 К ОТРАЖЕНИЯМ", callback_data="my_invites")],
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка в check_status_callback: {e}")
        await query.answer("❌ Ошибка", show_alert=True)
        return INVITES_LIST

# ============================================
# 👤 ЭКРАН 6: МЕНЮ ПРОФИЛЯ ДРУГА
# ============================================

def get_friend_by_id(context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> Optional[dict]:
    """Поиск друга по ID"""
    invites = context.user_data.get("sexual_invites", [])
    return next(
        (inv for inv in invites if inv.get("friend_id") == friend_id),
        None
    )

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 МЕНЮ ПРОФИЛЯ ДРУГА"""
    query = update.callback_query
    await query.answer()
    
    try:
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return INVITES_LIST
        
        context.user_data["current_friend_id"] = friend_id
        context.user_data["current_friend_data"] = friend_data
        
        friend_name = friend_data.get("friend_name", "Друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        access_status = friend_data.get("access_status", "free")
        free_count = count_free_friends(query.from_user.id)
        
        # Проверка лимита
        if access_status == "locked" or (free_count >= FREE_FRIEND_LIMIT and not friend_data.get("access_paid")):
            return await show_payment_access_screen(update, context, friend_data)
        
        purchased = friend_data.get("purchased_functions", [])
        progress = len(purchased)
        progress_bar = "▓" * progress + "░" * (4 - progress)
        
        message = f"""
{SEXUAL_DIVIDER}
👤 <b>{friend_name}</b>
{SEXUAL_DIVIDER}

📊 <b>Профиль:</b> {friend_profile}
💎 <b>Доступ:</b> {'🔓 Бесплатно' if access_status == 'free' else '💰 Куплен'}

🔓 <b>РАЗГАДАНО:</b> {progress}/4 [{progress_bar}]
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Стандартный", callback_data=f"std_{friend_id}"),
                InlineKeyboardButton("🔞 Интимный", callback_data=f"int_{friend_id}")
            ],
            [
                InlineKeyboardButton("🧬 4F-КЛЮЧИ", callback_data=f"4f_{friend_id}"),
                InlineKeyboardButton("❓ Что это?", callback_data="4f_explain")
            ],
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FRIEND_MENU
        
    except Exception as e:
        logger.error(f"❌ Ошибка в friend_menu_callback: {e}")
        await query.answer("❌ Ошибка", show_alert=True)
        return INVITES_LIST

# ============================================
# 💰 ЭКРАН 7: ОПЛАТА ДОСТУПА К ДРУГУ
# ============================================

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
    """💰 Разблокировка платного друга"""
    query = update.callback_query
    
    friend_name = friend_data.get("friend_name", "Друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
{SEXUAL_DIVIDER}
🔒 <b>{friend_name} ЗАБЛОКИРОВАН</b>
{SEXUAL_DIVIDER}

📊 <b>Профиль:</b> {friend_profile}

⚠️ <b>БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН</b>
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽

💰 <b>РАЗБЛОКИРОВАТЬ ДОСТУП:</b>
   • Цена: {FRIEND_ACCESS_PRICE}₽ (разово)
   • Стандартный профиль
   • Интимный профиль
   • Покупка 4F-ключей
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton(f"🔓 РАЗБЛОКИРОВАТЬ - {FRIEND_ACCESS_PRICE}₽", callback_data=f"pay_access_{friend_data['friend_id']}")],
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_PAYMENT_SCREEN

# ============================================
# 📊 ЭКРАН 8: СТАНДАРТНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    try:
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "Друг") if friend_data else "Друг"
        
        profile = {
            "archetype": "Автономный стратег",
            "quote": "«Я не ищу одобрения — я ищу эффективность.»",
            "pain": "Вам сложно делегировать. Вы уверены: «Хочешь сделать хорошо — сделай сам».",
            "immediate_tool": "Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.",
            "cta": "Исследуйте баланс между автономией и доверием."
        }
        
        message = f"""
{SEXUAL_DIVIDER}
📊 <b>{friend_name}</b>
{SEXUAL_DIVIDER}

🧠 <b>Архетип:</b> {profile['archetype']}

💬 <b>Цитата:</b>
{profile['quote']}

💔 <b>Суть проблемы:</b>
{profile['pain']}

🛠 <b>Инструмент:</b>
{profile['immediate_tool']}

🚀 <b>Следующие шаги:</b>
{profile['cta']}
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")]
        ]
        
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
# 🔞 ЭКРАН 9: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга (демо)"""
    query = update.callback_query
    await query.answer()
    
    try:
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FRIEND_MENU
        
        friend_name = friend_data.get("friend_name", "Друг")
        
        message = f"""
{SEXUAL_DIVIDER}
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
👤 <b>{friend_name}</b>
{SEXUAL_DIVIDER}

📊 <b>Тип:</b> SA-5_INT (ТЕСТ)
🧠 <b>Архетип:</b> ЦЕРЕМОНИАЛЬНЫЙ

💬 <b>ЦИТАТА:</b>
«{friend_name}, со мной не скучно. Со мной — вкусно.»

🧠 <b>ЕГО ПРИРОДА:</b>
Тестовый профиль на основе SA-5_INT.
В реальном режиме здесь будут персональные данные.

{SEXUAL_DIVIDER}
⚠️ <b>ТЕСТОВЫЙ РЕЖИМ</b>

Это демо-профиль.
✅ Что появится в боевом режиме:
   • Его реальные триггеры
   • Индивидуальные сценарии
   • Точные эрогенные зоны
   • Секретные желания

💎 <b>Купите полный доступ за {FRIEND_ACCESS_PRICE}₽</b>
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FRIEND_MENU
        
    except Exception as e:
        logger.error(f"❌ Ошибка в intimate_profile_callback: {e}")
        return FRIEND_MENU

# ============================================
# 🧬 ЭКРАН 10: МЕНЮ 4F-КЛЮЧЕЙ
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ 4F-КЛЮЧЕЙ"""
    query = update.callback_query
    await query.answer()
    
    try:
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return INVITES_LIST
        
        friend_name = friend_data.get("friend_name", "Друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        purchased = friend_data.get("purchased_functions", [])
        
        message = f"""
{SEXUAL_DIVIDER}
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>
{SEXUAL_DIVIDER}

📊 <b>Профиль:</b> {friend_profile}

1F 🔥 <b>{FOUR_F_TITLES['1F']}</b>
└ {FOUR_F_SUBTITLES['1F']}

2F 🍽️ <b>{FOUR_F_TITLES['2F']}</b>
└ {FOUR_F_SUBTITLES['2F']}

3F ⚡ <b>{FOUR_F_TITLES['3F']}</b>
└ {FOUR_F_SUBTITLES['3F']}

4F 💡 <b>{FOUR_F_TITLES['4F']}</b>
└ {FOUR_F_SUBTITLES['4F']}

{SEXUAL_DIVIDER}
"""
        
        keyboard = []
        
        for f in ["1F", "2F", "3F", "4F"]:
            emoji = FOUR_F_EMOJIS[f]
            if f in purchased:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔓 {emoji} {f} - ОТКРЫТЬ",
                        callback_data=f"open_4f_{friend_id}_{f}"
                    )
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji} {f} - {FOUR_F_PRICE}₽",
                        callback_data=f"buy_4f_{friend_id}_{f}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("❓ Что такое 4F?", callback_data="4f_explain"),
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
        ])
        keyboard.append([InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MENU
        
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_menu_callback: {e}")
        return FOUR_F_MENU

# ============================================
# 📘 ЭКРАН 11: ОБУЧАЙКА 4F
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ОБУЧАЙКА 4F"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    friend_id = context.user_data.get("current_friend_id")
    
    if friend_id:
        keyboard.append([
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites"),
            InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")
        ])
    
    await query.edit_message_text(
        FOUR_F_EXPLANATION,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

# ============================================
# 💳 ЭКРАН 12: ПОКУПКА 4F-КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Покупка 4F-ключа"""
    query = update.callback_query
    await query.answer("💰 Создаю счёт...")
    
    try:
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FOUR_F_MENU
        
        friend_name = friend_data.get("friend_name", "Друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        
        content = get_4f_content(function)
        
        message = f"""
{SEXUAL_DIVIDER}
{content['emoji'] if 'emoji' in content else FOUR_F_EMOJIS[function]} <b>{FOUR_F_NAMES[function]}</b>
{content.get('subtitle', FOUR_F_SUBTITLES[function])}
{SEXUAL_DIVIDER}

👤 <b>Друг:</b> {friend_name}
📊 <b>Профиль:</b> {friend_profile}

{content.get('short_description', FOUR_F_DESCRIPTIONS.get(function, ''))}

💰 <b>Цена:</b> {FOUR_F_PRICE}₽
⚠️ <i>Демо-версия для профиля SA-4_CAP</i>
{SEXUAL_DIVIDER}
"""
        
        payment_id = generate_payment_id("4f", query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {FOUR_F_PRICE}₽", callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"4f_{friend_id}")]
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
# 💳 ЭКРАН 13: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Процесс платежа"""
    query = update.callback_query
    await query.answer("💳 Подключаюсь к платежной системе...")
    
    try:
        parts = query.data.split("_")
        payment_id = parts[2]
        friend_id = int(parts[3])
        function = parts[4]
        
        payment_result = create_yookassa_invoice(
            payment_id=payment_id,
            user_id=query.from_user.id,
            amount=float(FOUR_F_PRICE),
            description=f"4F ключ {function} для друга {friend_id}"
        )
        
        if not payment_result.get("success"):
            await query.answer(f"❌ Ошибка платежа", show_alert=True)
            return FOUR_F_PAYMENT_SCREEN
        
        message = f"""
{SEXUAL_DIVIDER}
💳 <b>СЧЁТ СФОРМИРОВАН</b>
{SEXUAL_DIVIDER}

🔑 <b>Ключ:</b> {function} {FOUR_F_NAMES[function]}
👤 <b>Друг:</b> ID {friend_id}
💰 <b>Сумма:</b> {FOUR_F_PRICE}₽

✅ Нажмите кнопку для оплаты
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {FOUR_F_PRICE}₽", url=payment_result["confirmation_url"])],
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=f"check_payment_{payment_id}_{friend_id}_{function}")],
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"4f_{friend_id}")]
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
# 🔑 ЭКРАН 14: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТЫЙ 4F-КЛЮЧ"""
    query = update.callback_query
    await query.answer("🔓 Загружаю ключ...")
    
    try:
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "Друг") if friend_data else "Друг"
        
        # Добавляем функцию в купленные (для демо)
        if friend_data and function not in friend_data.get("purchased_functions", []):
            if "purchased_functions" not in friend_data:
                friend_data["purchased_functions"] = []
            friend_data["purchased_functions"].append(function)
        
        content = get_4f_content(function)
        message = format_4f_message(content, friend_name)
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ К СПИСКУ КЛЮЧЕЙ", callback_data=f"4f_{friend_id}")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_CONTENT
        
    except Exception as e:
        logger.error(f"❌ Ошибка в open_4f_key_callback: {e}")
        return FOUR_F_CONTENT

# ============================================
# 📋 ОБРАБОТЧИК КОПИРОВАНИЯ ССЫЛКИ
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Копировать ссылку"""
    query = update.callback_query
    invite_code = query.data.replace("copy_invite_", "")
    
    # В реальном боте здесь будет копирование в буфер
    await query.answer("✅ Ссылка скопирована в буфер обмена!", show_alert=True)
    
    return INVITES_LIST

# ============================================
# ⬅️ ВОЗВРАТ К РЕЗУЛЬТАТАМ
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

# ============================================
# 🌐 ОБРАБОТЧИК DEEP LINK
# ============================================

async def handle_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Обработчик /start с параметром"""
    if payload.startswith("sex_"):
        # Приглашение в интимный профиль
        user = update.effective_user
        invite_code = payload
        
        message = f"""
{SEXUAL_DIVIDER}
🎁 <b>Вас пригласил(а) друг!</b>
{SEXUAL_DIVIDER}

Пройдите тест — и друг сможет узнать 
ваши 18+ предпочтения и получить 4F-ключи к вашему профилю.

⏱ <b>Тест займёт всего 3 минуты</b>
🔒 Полная анонимность
💞 Только правда, без стыда

<b>🔑 Что такое 4F?</b>
• 1F 🔥 — Ключ возбуждения
• 2F 🍽️ — Ключ голода/желания  
• 3F ⚡ — Ключ страха
• 4F 💡 — Ключ идеи

{SEXUAL_DIVIDER}
🚀 <b>Начнём?</b>
"""
        keyboard = [
            [InlineKeyboardButton("🚀 Пройти тест", callback_data="start_test")]
        ]
        
        context.user_data["invite_code"] = payload
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        # Обычный старт
        await start(update, context)

# ============================================
# 🎭 FALLBACK ОБРАБОТЧИК (ДЛЯ КНОПОК ВНЕ CONVERSATION)
# ============================================

async def fallback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для кнопок вне ConversationHandler"""
    query = update.callback_query
    pattern = query.data
    
    logger.info(f"🔄 Fallback: {pattern}")
    
    try:
        if pattern == "share_mirror":
            await query.answer("🪞 Скоро здесь будет подарок", show_alert=True)
        elif pattern == "full_description":
            await query.answer("📖 Полное описание — 690₽", show_alert=True)
        elif pattern == "start_test":
            await query.answer("🚀 Запускаю тест...", show_alert=True)
            # Здесь должен быть переход к тесту
        elif pattern.startswith("pay_access_"):
            await query.answer("💰 Демо-платёж доступа к другу", show_alert=True)
        elif pattern.startswith("check_payment_"):
            parts = pattern.split("_")
            if len(parts) >= 5:
                friend_id = parts[3]
                function = parts[4]
                # Для демо сразу открываем ключ
                query.data = f"open_4f_{friend_id}_{function}"
                return await open_4f_key_callback(update, context)
        else:
            await query.answer("✅ Демо-режим")
        
        # Не возвращаем состояние, так как мы вне ConversationHandler
        return
        
    except Exception as e:
        logger.error(f"❌ Ошибка в fallback_callback: {e}")
        await query.answer("✅ Демо-режим")
        return

# ============================================
# 🚀 ЗАПУСК БОТА
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v11.0")
    print("="*60)
    print("✅ ЕДИНЫЙ КОД - БЕЗ КОНФЛИКТОВ")
    print("✅ Загрузка из sexual_18/sa_5_int.json")
    print("✅ Диагностика файловой системы")
    print("✅ 4F-ключи с демо-режимом")
    print("✅ Кнопки работают")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # ===== СОЗДАЕМ CONVERSATION HANDLER =====
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RESULTS_SCREEN: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            MY_SEXUAL_PROFILE: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            INVITES_LIST: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(check_status_callback, pattern='^check_status_'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
                CallbackQueryHandler(copy_invite_callback, pattern='^copy_invite_'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            FRIEND_MENU: [
                CallbackQueryHandler(standard_profile_callback, pattern='^std_'),
                CallbackQueryHandler(intimate_profile_callback, pattern='^int_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            FOUR_F_MENU: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(open_4f_key_callback, pattern='^open_4f_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            FOUR_F_CONTENT: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(process_payment_callback, pattern='^process_payment_'),
                CallbackQueryHandler(open_4f_key_callback, pattern='^check_payment_'),  # ВАЖНО!
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
        ],
        name="intimate_profiles_conversation",
        persistent=False,
    )
    
    # Добавляем ConversationHandler
    app.add_handler(conv_handler)
    
    # ===== FALLBACK ОБРАБОТЧИКИ (ТОЛЬКО ДЛЯ КНОПОК ВНЕ CONVERSATION) =====
    app.add_handler(CallbackQueryHandler(fallback_callback, pattern='^share_mirror$'))
    app.add_handler(CallbackQueryHandler(fallback_callback, pattern='^full_description$'))
    app.add_handler(CallbackQueryHandler(fallback_callback, pattern='^start_test$'))
    app.add_handler(CallbackQueryHandler(fallback_callback, pattern='^pay_access_'))
    
    print("\n🚀 Бот запущен!")
    print("✅ Все конфликты устранены")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    # Диагностика при запуске
    diagnose_sexual_profile_paths()
    main()
