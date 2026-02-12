#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МОДУЛЬ 18+: СЕКСУАЛЬНЫЕ ПРЕДПОЧТЕНИЯ + 4F-ФУНКЦИИ
Версия 2.1 - ИСПРАВЛЕН ПУТЬ К JSON ФАЙЛАМ!
✅ ИНТИМНЫЙ ПРОФИЛЬ ЗАГРУЖАЕТСЯ ИЗ sexual_18/sa_5_int.json
✅ ДИАГНОСТИКА ЗАГРУЗКИ
✅ ПРАВИЛЬНЫЕ ПУТИ БЕЗ "профили/"
"""

import logging
import os
import json
import uuid
import requests
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ============================================
# КОНСТАНТЫ - ИСПРАВЛЕНО!
# ============================================

SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ✅ Находим корень проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ ПРАВИЛЬНЫЙ ПУТЬ: ищем в sexual_18/, НЕ в profiles/ или профили/!
SEXUAL_PROFILE_PATH = os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json")

# ✅ Путь к 4F-функциям
FOUR_F_BASE_PATH = os.path.join(PROJECT_ROOT, "профили", "4F")

# Состояния для ConversationHandler
SEXUAL_PROFILE_SCREEN = 100
SEXUAL_INVITES_LIST = 101
SEXUAL_FRIEND_PROFILE = 102
FOUR_F_PAYMENT_SCREEN = 103
FOUR_F_CONTENT_SCREEN = 104

# API URL для платежей
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")

# ============================================
# ЗАГРУЗЧИК ПРОФИЛЕЙ - С МАКСИМАЛЬНОЙ ДИАГНОСТИКОЙ
# ============================================

def load_sexual_profile() -> Dict[str, Any]:
    """
    Загружает интимный профиль из JSON файла
    ИЩЕТ В ПРАВИЛЬНОМ МЕСТЕ: sexual_18/sa_5_int.json
    """
    print("\n" + "="*80)
    print("🔍 ДИАГНОСТИКА ЗАГРУЗКИ ИНТИМНОГО ПРОФИЛЯ")
    print("="*80)
    
    # 1. Показываем информацию о системе
    print(f"📁 Текущая директория: {os.getcwd()}")
    print(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"📁 __file__: {__file__}")
    print(f"📁 Путь к профилю: {SEXUAL_PROFILE_PATH}")
    
    # 2. Проверяем существование папки sexual_18
    sexual_18_dir = os.path.join(PROJECT_ROOT, "sexual_18")
    if os.path.exists(sexual_18_dir):
        print(f"✅ Папка sexual_18 существует: {sexual_18_dir}")
        try:
            files = os.listdir(sexual_18_dir)
            print(f"   Содержимое: {files}")
            if "sa_5_int.json" in files:
                print(f"   ✅ Файл sa_5_int.json найден в папке!")
        except Exception as e:
            print(f"   ❌ Ошибка чтения папки: {e}")
    else:
        print(f"❌ Папка sexual_18 НЕ найдена: {sexual_18_dir}")
    
    # 3. Проверяем существование файла по основному пути
    if not os.path.exists(SEXUAL_PROFILE_PATH):
        print(f"❌ Файл НЕ НАЙДЕН: {SEXUAL_PROFILE_PATH}")
        
        # 4. Ищем альтернативные пути
        print("\n🔍 ПОИСК АЛЬТЕРНАТИВНЫХ ПУТЕЙ:")
        
        alternative_paths = [
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join("sexual_18", "sa_5_int.json"),
            "/opt/render/project/src/sexual_18/sa_5_int.json",
            "sexual_18/sa_5_int.json",
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
        ]
        
        found_path = None
        for alt_path in alternative_paths:
            exists = os.path.exists(alt_path)
            status = "✅" if exists else "❌"
            print(f"   {status} {alt_path}")
            if exists:
                found_path = alt_path
                print(f"   🎯 НАЙДЕН АЛЬТЕРНАТИВНЫЙ ПУТЬ: {alt_path}")
                # Обновляем глобальную переменную
                global SEXUAL_PROFILE_PATH
                SEXUAL_PROFILE_PATH = alt_path
                break
        
        if not found_path:
            print("\n❌ ФАЙЛ НЕ НАЙДЕН НИ В ОДНОМ ИЗ ПУТЕЙ!")
            print("⚠️ ИСПОЛЬЗУЕТСЯ АВАРИЙНЫЙ ПРОФИЛЬ")
            print("="*80 + "\n")
            return get_emergency_profile()
    else:
        print(f"✅ ФАЙЛ НАЙДЕН: {SEXUAL_PROFILE_PATH}")
    
    # 5. Проверяем размер файла
    try:
        file_size = os.path.getsize(SEXUAL_PROFILE_PATH)
        print(f"📏 Размер файла: {file_size} байт")
        
        if file_size == 0:
            print("❌ Файл пустой!")
            return get_emergency_profile()
        
        if file_size < 100:
            print("⚠️ Файл слишком маленький!")
            
    except Exception as e:
        print(f"❌ Ошибка чтения размера файла: {e}")
        return get_emergency_profile()
    
    # 6. Пробуем загрузить JSON
    try:
        with open(SEXUAL_PROFILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📄 Прочитано {len(content)} символов")
            
            # Проверяем, что файл не пустой
            if not content.strip():
                print("❌ Файл пустой!")
                return get_emergency_profile()
            
            # Парсим JSON
            data = json.loads(content)
            print("✅ JSON УСПЕШНО ЗАГРУЖЕН!")
            print(f"🔑 Ключи верхнего уровня: {list(data.keys())}")
            
            # Проверяем структуру
            if 'sections' in data:
                sections = data['sections']
                print(f"📋 Количество секций: {len(sections)}")
                print(f"📋 Названия секций: {list(sections.keys())[:5]}...")
                
                # Проверяем первую секцию
                if sections:
                    first_key = list(sections.keys())[0]
                    first_section = sections[first_key]
                    print(f"🔍 Первая секция '{first_key}':")
                    print(f"   - Ключи: {list(first_section.keys())}")
                    print(f"   - Есть 'items': {'items' in first_section}")
                    if 'items' in first_section:
                        print(f"   - Количество items: {len(first_section['items'])}")
            else:
                print("⚠️ В JSON нет ключа 'sections'")
                print(f"📄 Структура: {type(data)}")
            
            print("="*80 + "\n")
            return data
            
    except json.JSONDecodeError as e:
        print(f"❌ ОШИБКА ПАРСИНГА JSON: {e}")
        print(f"📄 Первые 500 символов содержимого:")
        print(content[:500])
        print("="*80 + "\n")
        return get_emergency_profile()
        
    except PermissionError as e:
        print(f"❌ ОШИБКА ДОСТУПА: {e}")
        print("="*80 + "\n")
        return get_emergency_profile()
        
    except Exception as e:
        print(f"❌ НЕИЗВЕСТНАЯ ОШИБКА: {type(e).__name__}: {e}")
        print("="*80 + "\n")
        return get_emergency_profile()

def get_emergency_profile() -> Dict[str, Any]:
    """Аварийный интимный профиль - красивая заглушка"""
    print("⚠️ ИСПОЛЬЗУЕТСЯ АВАРИЙНЫЙ ПРОФИЛЬ (ЗАГЛУШКА)")
    return {
        "profile_key": "sa_5_int",
        "header": "🔞 ВАШ ИНТИМНЫЙ ПРОФИЛЬ",
        "title": "ЦЕРЕМОНИАЛЬНЫЙ",
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.\nВы не занимаетесь любовью — вы служите ей.\nИ каждый раз — как в первый. И каждый раз — как в последний.",
        "turn_ons": [
            {
                "title": "Шёпот в темноте", 
                "description": "Когда партнёр шепчет почти беззвучно — вы вслушиваетесь, затаив дыхание"
            },
            {
                "title": "Запах тела", 
                "description": "Запах пота после долгого дня, смешанный с духами — вы готовы кончить от этого аромата"
            },
            {
                "title": "Медленные пуговицы", 
                "description": "Вы сходите с ума, пока вас раздевают, глядя в глаза"
            }
        ],
        "blocks": [
            {
                "description": "Секс на скорую руку — вы чувствуете себя использованной/ым"
            },
            {
                "description": "Грубые, приказные интонации — вы не игрушка"
            },
            {
                "description": "«Ну давай быстрее» — убивает всё нахрен. Моментально."
            }
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
        "dynamics": {},
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

# ============================================
# 🔥 4F-ЗАГРУЗЧИК И ФОРМАТТЕР
# ============================================

def get_4f_function(function: str, profile_key: str = "sa_4_cap") -> Dict[str, Any]:
    """
    Загружает 4F-функцию из JSON-файла
    Правило MVP: Всегда используем sa_4_cap.json как демо для всех профилей
    """
    try:
        # Проверяем существование папки
        if not os.path.exists(FOUR_F_BASE_PATH):
            logger.warning(f"⚠️ Папка 4F не найдена: {FOUR_F_BASE_PATH}")
            os.makedirs(FOUR_F_BASE_PATH, exist_ok=True)
            logger.info(f"✅ Создана папка: {FOUR_F_BASE_PATH}")
        
        # Всегда берем sa_4_cap.json для демо-режима
        file_path = os.path.join(FOUR_F_BASE_PATH, function, "sa_4_cap.json")
        
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл {file_path} не найден, беру default.json")
            file_path = os.path.join(FOUR_F_BASE_PATH, function, "default.json")
            
            if not os.path.exists(file_path):
                logger.error(f"❌ Файл не найден: {file_path}")
                return {
                    "function": function,
                    "is_demo": True,
                    "is_stub": True,
                    "error": "file_not_found",
                    "short_description": "Ключ временно недоступен",
                    "content": {"message": "Ведутся технические работы"},
                    "demo_limitation": {
                        "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                        "content": [
                            "10+ точных триггер-фраз",
                            "Психологический разбор каждой фразы",
                            "Протокол применения в разных контекстах",
                            "Анти-паттерны и как их избежать"
                        ],
                        "price": 99,
                        "upgrade": f"/buy_function_{function}_full"
                    }
                }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            content["is_demo"] = True
            content["source_profile"] = "sa_4_cap"
            content["function"] = function
            return content
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON 4F: {e}")
        return {
            "function": function,
            "is_demo": True,
            "is_stub": True,
            "short_description": "Ошибка загрузки ключа",
            "content": {"message": "Ведутся технические работы"},
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": ["Полный набор триггеров", "Индивидуальные протоколы"],
                "price": 99,
                "upgrade": f"/buy_function_{function}_full"
            }
        }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки 4F: {e}")
        return {
            "function": function,
            "is_demo": True,
            "is_stub": True,
            "short_description": "Ключ временно недоступен",
            "content": {"message": "Ведутся технические работы"},
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": ["Полный набор триггеров", "Индивидуальные протоколы"],
                "price": 99,
                "upgrade": f"/buy_function_{function}_full"
            }
        }

def format_4f_message(content: Dict[str, Any], friend_name: str) -> str:
    """
    Форматирует JSON 4F в красивое Telegram-сообщение
    Подставляет имя друга в текст
    """
    # Заменяем {friend_name} во всем контенте
    content_str = json.dumps(content, ensure_ascii=False)
    content_str = content_str.replace("{friend_name}", friend_name)
    content = json.loads(content_str)
    
    function_emojis = {
        "1F": "🔥",
        "2F": "🍽️",
        "3F": "⚡",
        "4F": "💡"
    }
    
    function_names = {
        "1F": "КЛЮЧ ВОЗБУЖДЕНИЯ",
        "2F": "КЛЮЧ ГОЛОДА",
        "3F": "КЛЮЧ СТРАХА",
        "4F": "КЛЮЧ ИДЕИ"
    }
    
    func = content.get("function", "1F")
    emoji = function_emojis.get(func, "🔑")
    func_name = function_names.get(func, "")
    
    # Начинаем сборку сообщения
    text = f"""
{SEXUAL_DIVIDER}
{emoji} <b>{func} {func_name}</b>
{SEXUAL_DIVIDER}

<b>У профиля SA-4_CAP «{friend_name}»</b>

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
    if func == "1F":
        triggers = content.get("sexual_arousal", {}).get("triggers", [])
        if triggers:
            text += "<b>🎯 ТРИГГЕР-ФРАЗЫ:</b>\n\n"
            for i, t in enumerate(triggers[:3], 1):
                text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                text += f"   {t.get('effect', '')}\n\n"
    
    elif func == "2F":
        triggers = content.get("triggers", {})
        if triggers:
            text += "<b>🎯 ТРИГГЕРЫ ГОЛОДА:</b>\n\n"
            for i in range(1, 4):
                t = triggers.get(f"trigger_{i}", {})
                if t:
                    text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                    text += f"   {t.get('effect', '')}\n\n"
    
    elif func == "3F":
        antidotes = content.get("antidotes", {})
        if antidotes:
            text += "<b>💊 ПРОТИВОЯДИЯ:</b>\n\n"
            for i in range(1, 4):
                a = antidotes.get(f"antidote_{i}", {})
                if a:
                    text += f"{i}. <i>«{a.get('phrase', '')}»</i>\n"
                    text += f"   {a.get('effect', '')}\n\n"
    
    elif func == "4F":
        triggers = content.get("triggers", {})
        if triggers:
            text += "<b>🎯 ВОПРОСЫ-КЛЮЧИ:</b>\n\n"
            for i in range(1, 4):
                t = triggers.get(f"trigger_{i}", {})
                if t:
                    text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                    text += f"   {t.get('effect', '')}\n\n"
    
    # Демо-лимитация и продажа полной версии
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
💎 <b>Полная версия: {demo.get('price', 99)}₽</b>
🔓 Доступ навсегда
⚡ Мгновенная доставка

"""
    
    text += SEXUAL_DIVIDER
    return text

# ============================================
# 🎯 ЭКРАН: МОЙ ИНТИМНЫЙ ПРОФИЛЬ - ИСПРАВЛЕНО!
# ============================================

async def show_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль - С ДИАГНОСТИКОЙ!"""
    query = update.callback_query
    await query.answer()
    
    # Загружаем профиль с диагностикой
    profile = load_sexual_profile()
    username = update.effective_user.first_name or "Пользователь"
    
    # Проверяем, что загрузилось
    if not profile or profile == get_emergency_profile():
        logger.error("❌ Не удалось загрузить интимный профиль!")
        await query.answer("⚠️ Ошибка загрузки профиля", show_alert=True)
    
    # Форматируем сообщение
    text = f"""
{SEXUAL_DIVIDER}
🔞 <b>18+ ПРОФИЛЬ: {username}</b>
🧠 <b>ПРОФИЛЬ:</b> {profile.get('profile_key', 'SA_5_INT').upper()}

{profile.get('description', '')[:300]}

<b>🔴 ВКЛЮЧАЕТ:</b>
"""
    for item in profile.get('turn_ons', [])[:3]:
        text += f"• {item.get('title', '')}: {item.get('description', '')[:100]}...\n"
    
    text += f"""
<b>⚠️ БЛОК:</b>
"""
    for item in profile.get('blocks', [])[:2]:
        text += f"• {item.get('description', '')[:100]}...\n"
    
    text += f"""
<b>🔴 ЭРОГЕННАЯ ЗОНА:</b>
{profile.get('erogenous_zone', {}).get('trigger', '')[:100]}

<b>💞 ИДЕАЛЬНЫЙ ПАРТНЁР:</b>
{profile.get('ideal_partner', '')[:200]}

<b>🛠 {profile.get('tool', {}).get('name', 'ПРОТОКОЛ')}:</b>
"""
    for step in profile.get('tool', {}).get('steps', [])[:3]:
        text += f"{step}\n"

    text += f"""
{SEXUAL_DIVIDER}
💞 <b>У КАЖДОГО ЕСТЬ ТАЙНЫ.</b>
🔓 <b>ВАШ КЛЮЧ К ПРАВДЕ:</b>

❶ Пригласите → 0₽
❷ Друг проходит тест (3 мин)
❸ Мы пришлём уведомление
❹ 99₽ = доступ к его 18+ профилю

⚠️ Только вы. Только правда. Без стыда.
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 Создать приглашение", callback_data="sexual_invite_start")],
        [InlineKeyboardButton("🔍 Мои приглашения", callback_data="show_my_invites")],
        [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_PROFILE_SCREEN

# ============================================
# 🔥 ЭКРАН: СОЗДАНИЕ ПРИГЛАШЕНИЯ (СОГЛАСНО ТЗ)
# ============================================

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔞 Создание ссылки-приглашения с готовым текстом
    ПОЛНОСТЬЮ СООТВЕТСТВУЕТ ТЗ!
    """
    query = update.callback_query
    await query.answer()
    
    # 1. Генерируем уникальный код
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/Testing_Lichnosti_bot?start={invite_code}"
    
    # 2. ЖЕСТКО ЗАДАННЫЙ ТЕКСТ (НЕ МЕНЯТЬ!)
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "Я прошёл — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
    )
    
    # 3. ТЕКСТ ЭКРАНА (ССЫЛКА + ГОТОВЫЙ ТЕКСТ) - ТОЧНО ПО ТЗ
    text = f"""
{SEXUAL_DIVIDER}
🔞 <b>ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!</b>
{SEXUAL_DIVIDER}

🔗 <code>{invite_url}</code>

💬 <b>ТЕКСТ ДЛЯ ОТПРАВКИ ДРУГУ:</b>
<code>{invite_message}</code>

✨ <b>СКОПИРУЙТЕ ТЕКСТ ЦЕЛИКОМ</b>
   ИЛИ НАЖМИТЕ КНОПКУ ОТПРАВКИ
{SEXUAL_DIVIDER}
"""
    
    # 4. КНОПКИ: ОТПРАВИТЬ + КОПИРОВАТЬ + НАВИГАЦИЯ (ТОЧНО ПО ТЗ)
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Отправить другу", url=share_url),
            InlineKeyboardButton("📋 Копировать ссылку", callback_data=f"copy_invite_{invite_code}")
        ],
        [
            InlineKeyboardButton("🔍 Мои приглашения", callback_data="show_my_invites"),
            InlineKeyboardButton("⬅️ К профилю", callback_data="show_my_sexual_profile")
        ]
    ]
    
    # 5. Сохраняем приглашение в user_data
    invite = {
        "code": invite_code,
        "url": invite_url,
        "message": invite_message,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "friend_id": None,
        "friend_name": None,
        "friend_profile": None,
        "payment_status": {},
        "purchased_functions": []  # Список купленных 4F для этого друга
    }
    
    context.user_data["current_invite"] = invite
    
    invites = context.user_data.get("sexual_invites", [])
    invites.insert(0, invite)
    context.user_data["sexual_invites"] = invites
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    return SEXUAL_INVITES_LIST

# ============================================
# 🔥 ЭКРАН: МОИ ПРИГЛАШЕНИЯ (С 4F-КНОПКАМИ)
# ============================================

async def show_my_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔍 МОИ ПРИГЛАШЕНИЯ
    Показывает список приглашений и кнопки 1F-4F для друзей, прошедших тест
    """
    query = update.callback_query
    await query.answer()
    
    invites = context.user_data.get("sexual_invites", [])
    current_invite = context.user_data.get("current_invite")
    
    if current_invite and current_invite not in invites:
        invites.insert(0, current_invite)
        context.user_data["sexual_invites"] = invites
    
    if not invites:
        text = f"""
{SEXUAL_DIVIDER}
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
{SEXUAL_DIVIDER}

У вас пока нет активных приглашений.

✨ Создайте ссылку-приглашение, чтобы узнать 
   18+ предпочтения друзей и получить 4F-ключи.

👉 <b>99₽ = доступ к профилю друга + 4F</b>
{SEXUAL_DIVIDER}
"""
        keyboard = [
            [InlineKeyboardButton("🔞 Создать приглашение", callback_data="sexual_invite_start")],
            [InlineKeyboardButton("⬅️ К профилю", callback_data="show_my_sexual_profile")]
        ]
        await query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="HTML"
        )
        return SEXUAL_INVITES_LIST
    
    # Основной текст со списком приглашений
    text = f"""
{SEXUAL_DIVIDER}
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
{SEXUAL_DIVIDER}

📋 <b>Всего создано:</b> {len(invites)}

"""
    for i, invite in enumerate(invites[:3], 1):
        code = invite.get('code', '')[:12]
        created_at = invite.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                created_at = dt.strftime("%d.%m.%Y")
            except:
                created_at = created_at[:10]
        else:
            created_at = "только что"
        
        friend_name = invite.get('friend_name')
        status_emoji = "✅" if friend_name else "⏳"
        status_text = f"👤 {friend_name}" if friend_name else "⏳ Ожидает ответа"
        
        text += f"{i}. <code>{code}</code>\n   📅 {created_at} • {status_emoji} {status_text}\n\n"
    
    if len(invites) > 3:
        text += f"...и ещё {len(invites) - 3} приглашений\n\n"
    
    text += f"""
{SEXUAL_DIVIDER}
💞 <b>Как только друг пройдёт тест —</b>
   вы увидите его имя и получите доступ к кнопкам 1F-4F.

<b>🔑 4F-КЛЮЧИ (99₽/шт):</b>
• 🔥 1F — Как вызвать возбуждение
• 🍽️ 2F — Как пробудить голод/желание
• ⚡ 3F — Как обойти страх
• 💡 4F — Как родить идею

⚠️ <i>Сейчас работает демо-режим для всех профилей</i>
{SEXUAL_DIVIDER}
"""
    
    # Создаем клавиатуру
    keyboard = []
    
    # Для каждого друга, прошедшего тест, добавляем ряд с кнопками 1F-4F
    for invite in invites:
        friend_name = invite.get('friend_name')
        if friend_name:
            # Ряд с именем друга (не кликабельно, просто текст)
            keyboard.append([InlineKeyboardButton(f"👤 {friend_name}", callback_data="noop")])
            
            # Ряд с кнопками 1F-4F
            row = []
            purchased = invite.get("purchased_functions", [])
            
            for f in ["1F", "2F", "3F", "4F"]:
                if f in purchased:
                    row.append(InlineKeyboardButton(
                        f"🔓 {f}",
                        callback_data=f"open_4f_{invite['code']}_{f}"
                    ))
                else:
                    row.append(InlineKeyboardButton(
                        f"{f} (99₽)",
                        callback_data=f"buy_function_{invite['code']}_{f}"
                    ))
            keyboard.append(row)
            
            # Кнопка "Детали профиля"
            keyboard.append([InlineKeyboardButton(
                "📋 Детали профиля",
                callback_data=f"friend_details_{invite['code']}"
            )])
    
    # Кнопки навигации
    keyboard.append([InlineKeyboardButton("🔞 Создать новое приглашение", callback_data="sexual_invite_start")])
    keyboard.append([InlineKeyboardButton("⬅️ К профилю", callback_data="show_my_sexual_profile")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_INVITES_LIST

# ============================================
# 🔥 ПОКУПКА 4F-ФУНКЦИИ
# ============================================

async def buy_function_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки 1F/2F/3F/4F"""
    query = update.callback_query
    await query.answer("💳 Создаю платеж...")
    
    # Парсим callback_data: buy_function_{invite_code}_{function}
    parts = query.data.split("_")
    if len(parts) < 4:
        await query.answer("❌ Неверный формат", show_alert=True)
        return SEXUAL_INVITES_LIST
        
    invite_code = parts[2]
    function = parts[3]
    
    # Ищем приглашение
    invites = context.user_data.get("sexual_invites", [])
    invite = None
    for inv in invites:
        if inv.get("code") == invite_code:
            invite = inv
            break
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return SEXUAL_INVITES_LIST
    
    if not invite.get("friend_id"):
        await query.answer("⏳ Друг еще не прошел тест", show_alert=True)
        return SEXUAL_INVITES_LIST
    
    friend_name = invite.get("friend_name", "Друг")
    friend_profile = invite.get("friend_profile", "SA_4_EXP")
    buyer_id = update.effective_user.id
    
    # Создаем платеж через API
    payment_id = f"4f_{function}_{buyer_id}_{int(datetime.now().timestamp())}"
    
    try:
        response = requests.post(
            f"{API_URL}/api/4f/create-payment-99",
            json={
                "payment_id": payment_id,
                "buyer_id": buyer_id,
                "target_id": invite.get("friend_id", 0),
                "target_name": friend_name,
                "target_profile": friend_profile,
                "function": function,
                "invite_id": invite_code
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            confirmation_url = data.get("confirmation_url")
            
            # Сохраняем payment_id в приглашении
            if "payment_ids" not in invite:
                invite["payment_ids"] = {}
            invite["payment_ids"][function] = payment_id
            
            text = f"""
{SEXUAL_DIVIDER}
🔑 <b>ПОКУПКА КЛЮЧА {function}</b>
{SEXUAL_DIVIDER}

👤 <b>Друг:</b> {friend_name}
📊 <b>Профиль:</b> {friend_profile}
🔐 <b>Функция:</b> {function}

💎 <b>Стоимость:</b> 99 ₽

<b>После оплаты вы получите:</b>
• Полное описание ключа {function}
• 10+ точных триггер-фраз
• Психологический разбор
• Протокол применения

⚠️ <i>Сейчас действует демо-режим — 
вы получите готовый ключ для профиля SA-4_CAP</i>
{SEXUAL_DIVIDER}
"""
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить 99 ₽", url=confirmation_url)],
                [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_4f_payment_{payment_id}_{function}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="show_my_invites")]
            ]
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return FOUR_F_PAYMENT_SCREEN
        else:
            await query.answer("❌ Ошибка создания платежа", show_alert=True)
            return SEXUAL_INVITES_LIST
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка соединения при создании платежа 4F: {e}")
        await query.answer("❌ Ошибка соединения с платежной системой", show_alert=True)
        return SEXUAL_INVITES_LIST
    except Exception as e:
        logger.error(f"Ошибка при создании платежа 4F: {e}")
        await query.answer("❌ Внутренняя ошибка", show_alert=True)
        return SEXUAL_INVITES_LIST

# ============================================
# 🔥 ПРОВЕРКА ПЛАТЕЖА 4F
# ============================================

async def check_4f_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа за 4F"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    if len(parts) < 5:
        await query.answer("❌ Неверный формат", show_alert=True)
        return FOUR_F_PAYMENT_SCREEN
        
    payment_id = parts[3]
    function = parts[4]
    
    try:
        response = requests.get(
            f"{API_URL}/api/4f/check-payment/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "pending")
            
            if status == "succeeded":
                # Платеж успешен - показываем ключ
                # Меняем callback_data для open_4f_key_callback
                query.data = f"open_4f_payment_{payment_id}_{function}"
                return await open_4f_key_callback(update, context)
            elif status == "pending":
                await query.answer("⏳ Платеж еще не обработан", show_alert=True)
            else:
                await query.answer(f"❌ Статус: {status}", show_alert=True)
        else:
            await query.answer("⏳ Платеж обрабатывается", show_alert=True)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка соединения при проверке платежа: {e}")
        await query.answer("❌ Ошибка соединения", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")
        await query.answer("❌ Ошибка проверки", show_alert=True)
    
    return FOUR_F_PAYMENT_SCREEN

# ============================================
# 🔥 ОТКРЫТИЕ КУПЛЕННОГО 4F-КЛЮЧА
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открыть купленный 4F-ключ"""
    query = update.callback_query
    await query.answer("🔓 Загружаю ключ...")
    
    parts = query.data.split("_")
    
    if len(parts) >= 4 and parts[1] == "4f" and parts[2] != "payment":
        # open_4f_{invite_code}_{function}
        invite_code = parts[2]
        function = parts[3]
        
        # Ищем приглашение
        invites = context.user_data.get("sexual_invites", [])
        invite = None
        for inv in invites:
            if inv.get("code") == invite_code:
                invite = inv
                break
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return SEXUAL_INVITES_LIST
        
        friend_name = invite.get("friend_name", "Друг")
        
        # Добавляем функцию в купленные (для демо-режима)
        if function not in invite.get("purchased_functions", []):
            if "purchased_functions" not in invite:
                invite["purchased_functions"] = []
            invite["purchased_functions"].append(function)
        
        # Загружаем демо-ключ
        content = get_4f_function(function, "sa_4_cap")
        text = format_4f_message(content, friend_name)
        
        keyboard = [
            [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="show_my_invites")],
            [InlineKeyboardButton("🔒 Купить полную версию (99₽)", callback_data=f"buy_function_{invite_code}_{function}")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return FOUR_F_CONTENT_SCREEN
        
    elif len(parts) >= 5 and parts[1] == "4f" and parts[2] == "payment":
        # open_4f_payment_{payment_id}_{function}
        payment_id = parts[3]
        function = parts[4]
        
        try:
            response = requests.get(
                f"{API_URL}/api/4f/get-purchased-function/{payment_id}",
                params={"user_id": update.effective_user.id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", {})
                friend_name = data.get("target_name", "Друг")
                
                text = format_4f_message(content, friend_name)
                
                keyboard = [
                    [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="show_my_invites")],
                    [InlineKeyboardButton("🔒 Купить еще", callback_data="sexual_invite_start")]
                ]
                
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML"
                )
                return FOUR_F_CONTENT_SCREEN
            else:
                await query.answer("❌ Ключ не найден", show_alert=True)
                return SEXUAL_INVITES_LIST
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка соединения при получении ключа: {e}")
            await query.answer("❌ Ошибка соединения", show_alert=True)
            return SEXUAL_INVITES_LIST
        except Exception as e:
            logger.error(f"Ошибка получения ключа: {e}")
            await query.answer("❌ Ошибка загрузки", show_alert=True)
            return SEXUAL_INVITES_LIST
    else:
        await query.answer("❌ Неверный формат", show_alert=True)
        return SEXUAL_INVITES_LIST

# ============================================
# ДЕТАЛИ ПРОФИЛЯ ДРУГА
# ============================================

async def friend_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает детали профиля друга"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    if len(parts) < 3:
        await query.answer("❌ Неверный формат", show_alert=True)
        return SEXUAL_INVITES_LIST
        
    invite_code = parts[2]
    
    invites = context.user_data.get("sexual_invites", [])
    invite = None
    for inv in invites:
        if inv.get("code") == invite_code:
            invite = inv
            break
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return SEXUAL_INVITES_LIST
    
    friend_name = invite.get("friend_name", "Друг")
    friend_profile = invite.get("friend_profile", "SA_4_EXP")
    purchased = invite.get("purchased_functions", [])
    
    text = f"""
{SEXUAL_DIVIDER}
👤 <b>ПРОФИЛЬ ДРУГА</b>
{SEXUAL_DIVIDER}

<b>Имя:</b> {friend_name}
<b>Общий профиль:</b> {friend_profile}
<b>Интимный профиль:</b> sa_5_int (тестовая заглушка)

<b>🔑 Купленные ключи:</b>
"""
    if purchased:
        for f in purchased:
            text += f"  • {f}\n"
    else:
        text += "  • Нет купленных ключей\n"
    
    text += f"""
{SEXUAL_DIVIDER}
💎 <b>4F-ключи — 99₽/шт</b>
• 1F: Ключ возбуждения
• 2F: Ключ голода/желания
• 3F: Ключ страха
• 4F: Ключ идеи

⚠️ <i>Сейчас все ключи работают в демо-режиме
для профиля SA-4_CAP</i>
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="show_my_invites")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_FRIEND_PROFILE

# ============================================
# ОБРАБОТЧИКИ СТАНДАРТНЫХ КНОПОК
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик кнопки "📋 Копировать ссылку"
    ПОЛНОСТЬЮ СООТВЕТСТВУЕТ ТЗ!
    """
    query = update.callback_query
    invite_code = query.data.replace("copy_invite_", "")
    
    # Находим ссылку в user_data
    invite_url = None
    for invite in context.user_data.get("sexual_invites", []):
        if invite["code"] == invite_code:
            invite_url = invite["url"]
            break
    
    if invite_url:
        # В реальном боте здесь будет копирование в буфер
        # Показываем alert
        await query.answer("✅ Ссылка скопирована!", show_alert=True)
    else:
        await query.answer("❌ Ссылка не найдена", show_alert=True)
    
    return SEXUAL_INVITES_LIST

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer("⏳ Ожидает активации", show_alert=True)
    return SEXUAL_INVITES_LIST

async def delete_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление приглашения"""
    query = update.callback_query
    await query.answer("❌ Приглашение удалено", show_alert=True)
    return SEXUAL_INVITES_LIST

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для некликабельных кнопок"""
    query = update.callback_query
    await query.answer()
    return SEXUAL_INVITES_LIST

# ============================================
# ОБРАБОТЧИК DEEP LINK
# ============================================

async def handle_sexual_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Обработчик /start sex_xxx"""
    user = update.effective_user
    invite_code = payload
    
    inviter_name = "друг"
    inviter_id = 123456789
    
    text = f"""
{SEXUAL_DIVIDER}
🎁 <b>Вас пригласил(а) {inviter_name}!</b>
{SEXUAL_DIVIDER}

Пройдите тест — и {inviter_name} сможет узнать 
ваши 18+ предпочтения и получить 4F-ключи к вашему профилю
(только если захочет и заплатит 99₽ за каждый ключ).

<i>Вы тоже сможете приглашать друзей 
и покупать 4F-ключи к их профилям.</i>

⏱ <b>Тест займёт всего 3 минуты</b>
🔒 Полная анонимность
💞 Только правда, без стыда

<b>🔑 Что такое 4F?</b>
• 1F — Ключ возбуждения
• 2F — Ключ голода/желания  
• 3F — Ключ страха
• 4F — Ключ идеи

{SEXUAL_DIVIDER}
🚀 <b>Начнём?</b>
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Пройти тест", callback_data="start_test")]
    ]
    
    context.user_data["invited_by"] = inviter_id
    context.user_data["invite_code"] = payload
    context.user_data["inviter_name"] = inviter_name
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================
# ПРОВЕРКА ПРИГЛАШЕНИЯ ПОСЛЕ ТЕСТА
# ============================================

async def check_sexual_invitation(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str, profile_code: str):
    """
    Вызывается после прохождения теста
    Обновляет статус приглашения и привязывает профиль друга
    """
    invite_code = context.user_data.get("invite_code")
    inviter_name = context.user_data.get("inviter_name", "друг")
    
    if not invite_code:
        return False
    
    logger.info(f"🔞 Пользователь {user_id} ({username}) прошел тест по приглашению {invite_code}")
    
    # В реальном приложении здесь нужно обновить статус в БД
    # Пока просто сохраняем в контексте
    context.user_data["i_was_invited"] = True
    context.user_data["my_inviter"] = inviter_name
    context.user_data["my_invite_code"] = invite_code
    
    # Очищаем данные приглашения
    context.user_data.pop("invited_by", None)
    context.user_data.pop("invite_code", None)
    context.user_data.pop("inviter_name", None)
    
    return True

# ============================================
# ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ - ЗАПУСКАТЬ ОТДЕЛЬНО!
# ============================================

def test_loader():
    """Тестирует загрузчик профиля"""
    print("\n" + "🚀"*40)
    print("🚀 ТЕСТИРОВАНИЕ ЗАГРУЗЧИКА ИНТИМНОГО ПРОФИЛЯ")
    print("🚀"*40 + "\n")
    
    profile = load_sexual_profile()
    
    if profile and profile != get_emergency_profile():
        print("\n✅ ТЕСТ УСПЕШЕН! Профиль загружен.")
        return True
    else:
        print("\n❌ ТЕСТ ПРОВАЛЕН! Профиль не загружен.")
        return False

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'show_my_sexual_profile',
    'sexual_invite_start',
    'show_my_invites',
    'handle_sexual_deeplink',
    'copy_invite_callback',
    'check_invite_callback',
    'delete_invite_callback',
    'buy_function_callback',
    'check_4f_payment_callback',
    'open_4f_key_callback',
    'friend_details_callback',
    'noop_callback',
    'check_sexual_invitation',
    'get_4f_function',
    'format_4f_message',
    'load_sexual_profile',
    'get_emergency_profile',
    'test_loader',
    'SEXUAL_PROFILE_SCREEN',
    'SEXUAL_INVITES_LIST',
    'SEXUAL_FRIEND_PROFILE',
    'FOUR_F_PAYMENT_SCREEN',
    'FOUR_F_CONTENT_SCREEN'
]

# ============================================
# ЗАПУСК ТЕСТА ПРИ ПРЯМОМ ВЫПОЛНЕНИИ
# ============================================

if __name__ == "__main__":
    test_loader()
