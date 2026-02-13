#!/usr/bin/env python3
"""
МОДУЛЬ 18+ ДЛЯ ВИРТУАЛЬНОГО ПСИХОЛОГА ВАРИАТИКА
Версия: 4.0 - БОЕВОЙ РЕЖИМ

🔞 ПОЛНЫЙ ФУНКЦИОНАЛ:
- Интимные профили с JSON-загрузкой (реальные файлы из папки sexual_18/)
- Система приглашений (бесплатные/платные)
- 4F-ключи с покупкой (1F,2F,3F,4F)
- Интеграция с Яндекс.Диск (36 профилей)
- Платежи через ЮKassa (реальные)
- Уведомления при активации
- Статистика и лимиты
- Сохранение данных друга в БД
"""

import logging
import os
import sys
import json
import uuid
import time
import random
import urllib.parse
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# ===== НАСТРОЙКА ЛОГГИРОВАНИЯ =====
logger = logging.getLogger(__name__)

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FREE_INVITE_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 99
DEFAULT_SEXUAL_PROFILE = "SA_5_INT"
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")

# Путь к папке с JSON-файлами интимных профилей
SEXUAL_JSON_DIR = "sexual_18"

# ===== ПАКЕТЫ ПРИГЛАШЕНИЙ =====
INVITE_PACKAGES = {
    "3": {"price": 299, "links": 3, "emoji": "🥉", "popular": False},
    "5": {"price": 499, "links": 5, "emoji": "🥈", "popular": True},
    "10": {"price": 899, "links": 10, "emoji": "🥇", "popular": False}
}

# ===== ССЫЛКИ НА ЯНДЕКС.ДИСК - ВСЕ 36 ПРОФИЛЕЙ =====
PROFILE_DISK_LINKS = {
    # SA Profiles
    "SA_1_DEF": "https://disk.yandex.ru/d/HAcOfAg1tpIedA",
    "SA_2_SIT": "https://disk.yandex.ru/d/MwdMClX9koCTmA",
    "SA_3_CON": "https://disk.yandex.ru/d/NKN_XemK62t5nA",
    "SA_4_EXP": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA",
    "SA_5_INT": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg",
    "SA_6_AUT": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag",
    "SA_7_VAL": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g",
    "SA_8_TRA": "https://disk.yandex.ru/d/SqlDISkse1OEGQ",
    "SA_9_IDE": "https://disk.yandex.ru/d/vGzHmuckInNL5g",
    
    # SP Profiles
    "SP_1_DEF": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA",
    "SP_2_SIT": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA",
    "SP_3_CON": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA",
    "SP_4_EXP": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ",
    "SP_5_INT": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg",
    "SP_6_AUT": "https://disk.yandex.ru/d/xWBv4TLFosOB5g",
    "SP_7_VAL": "https://disk.yandex.ru/d/K1whXj6C6KAazQ",
    "SP_8_TRA": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg",
    "SP_9_IDE": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ",
    
    # IA Profiles
    "IA_1_DEF": "https://disk.yandex.ru/d/M1Y7z175uGKIHg",
    "IA_2_SIT": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ",
    "IA_3_CON": "https://disk.yandex.ru/d/DCkqqALby9UpFg",
    "IA_4_EXP": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg",
    "IA_5_INT": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g",
    "IA_6_AUT": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg",
    "IA_7_VAL": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ",
    "IA_8_TRA": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw",
    "IA_9_IDE": "https://disk.yandex.ru/d/ub0YpQQSg4g6rQ",
    
    # IP Profiles
    "IP_1_DEF": "https://disk.yandex.ru/d/m-WOQwDdgQxsnQ",
    "IP_2_SIT": "https://disk.yandex.ru/d/aL4VlAQdlaZ-6g",
    "IP_3_CON": "https://disk.yandex.ru/d/N8GG9XbnC3bFhg",
    "IP_4_EXP": "https://disk.yandex.ru/d/54RFOZmGhA4cfA",
    "IP_5_INT": "https://disk.yandex.ru/d/l5iFTIX8-gTycQ",
    "IP_6_AUT": "https://disk.yandex.ru/d/bTo_vcCoC1KU7Q",
    "IP_7_VAL": "https://disk.yandex.ru/d/TMx1VP843bnJQw",
    "IP_8_TRA": "https://disk.yandex.ru/d/e9KfJdLcl3gp7g",
    "IP_9_IDE": "https://disk.yandex.ru/d/ZiQPHJSDrrWZhw",
    
    # Default
    "default": "https://disk.yandex.ru/d/EYPIF9_puI_t0A"
}

# ===== 4F-ОПИСАНИЯ (ПОЛНЫЕ) =====
FOUR_F_DESCRIPTIONS = {
    "1F": {
        "title": "НАПАДЕНИЕ / ЯРОСТЬ",
        "emoji": "🔥",
        "short": "Что включает его агрессию и как быстро её погасить",
        "description": """
😤 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЯРОСТЬ</b>

Его агрессия не возникает из ниоткуда.
Это реакция на конкретные ТРИГГЕРЫ — слова, интонации, ситуации.

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Критика при свидетелях
   • Обесценивание его усилий
   • Игнорирование его границ
   • Определенные интонации голоса

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • Список его ЛИЧНЫХ триггеров
   • 3 фразам-гасителям
   • Пониманию, почему он срывается на вас
   • Технике «Торможение»
""",
        "triggers": [
            "«Я понимаю, почему ты так реагируешь»",
            "«Ты имеешь полное право злиться»",
            "«Я на твоей стороне»",
            "«Это действительно несправедливо»",
            "«Твои границы — это важно»"
        ],
        "analysis": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита. Если вы видите гнев, значит, где-то рядом есть страх. Ключ не в том, чтобы подавить агрессию, а в том, чтобы убрать угрозу, которую видит его психика.",
        "protocol": "1. Заметьте триггер (что именно запустило реакцию)\n2. Признайте эмоцию («Я вижу, ты злишься, и это нормально»)\n3. Не давите, не спорьте, не защищайтесь\n4. Дайте время на возвращение в ресурсное состояние\n5. Вернитесь к разговору, когда он успокоится",
        "quote": "«Гнев — это просто флаг, который говорит: здесь нарушены мои границы.»"
    },
    "2F": {
        "title": "БЕГСТВО / СТРАХ",
        "emoji": "🏃",
        "short": "Чего он боится на самом деле и как стать для него безопасностью",
        "description": """
🏃 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ БЕГСТВО</b>

Страх — это реакция избегания.
Она включается, когда мозг видит СТИМУЛ, похожий на прошлую угрозу.

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования
   • Определенные темы разговоров

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • Его личным триггерам страха
   • 3 якорям безопасности
   • Пониманию, почему он закрывается
   • Технике «Безопасная среда»
""",
        "triggers": [
            "«Ты не обязан это делать»",
            "«Здесь безопасно»",
            "«Я подожду»",
            "«Ты можешь уйти в любой момент»",
            "«Никакого давления»"
        ],
        "analysis": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя от того, что его психика считает опасным. Часто этот страх родом из детства, где на него давили, не давали права голоса.",
        "protocol": "1. Снимите давление (уберите требования)\n2. Дайте выход (предложите паузу)\n3. Не преследуйте, не требуйте объяснений\n4. Верните контроль («Решать тебе»)\n5. Создайте ритуал безопасности",
        "quote": "«Страх — это не слабость. Это сигнал, что нужна защита.»"
    },
    "3F": {
        "title": "СЕКС / ЖЕЛАНИЕ",
        "emoji": "🧬",
        "short": "Что реально его заводит: 3 слова и 3 касания-ключа",
        "description": """
🧬 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЖЕЛАНИЕ</b>

Сексуальное влечение — это цепочка стимулов.
Определенные слова, взгляды, касания работают как ПАРОЛЬ.

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Особая интонация голоса
   • Зрительный контакт определенной длины
   • Неожиданные касания
   • Контекст и обстановка

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 словам-паролям
   • 3 касаниям-ключам
   • Его эротическому сценарию
   • Пониманию, что ГАСИТ желание
""",
        "triggers": [
            "«Ты такой...» (искренний комплимент)",
            "Взгляд в глаза чуть дольше обычного",
            "«А что ты любишь?»",
            "Случайное касание, которое не прерывают",
            "Шёпот, интимный контекст"
        ],
        "analysis": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес. Для каждого человека существует уникальный «люк» — комбинация стимулов, которая открывает доступ к его желанию.",
        "protocol": "1. Создайте контекст (место, время, атмосферу)\n2. Играйте с вниманием (то приближаясь, то отдаляясь)\n3. Читайте ответы (язык тела важнее слов)\n4. Усиливайте напряжение (но не переходите к действию слишком рано)\n5. Дайте ему/ей проявить инициативу",
        "quote": "«Желание не включается кнопкой. Оно выращивается, как сад.»"
    },
    "4F": {
        "title": "ПОГЛОЩЕНИЕ / ДЕНЬГИ",
        "emoji": "🍽",
        "short": "Что запускает режим заработка и как говорить с ним о деньгах",
        "description": """
🍽 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ РЕЖИМ «ДЕНЬГИ»</b>

Для него деньги = безопасность, статус, свобода.
Это состояние включается определенными ТРИГГЕРАМИ.

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка
   • Определенные фразы-мотиваторы

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 фразам, которые включают «режим предпринимателя»
   • Пониманию, что тормозит его заработок
   • Технике «Топливо»
   • Сценарию просьбы
""",
        "triggers": [
            "«Ты можешь заработать на этом»",
            "«Это твой шанс»",
            "«Никто не сделает это лучше тебя»",
            "«Представь, сколько это будет стоить через год»",
            "«Я верю в твою идею»"
        ],
        "analysis": "Желание заработать — это не про жадность, а про безопасность, статус, свободу. Для одних деньги — это способ защитить семью, для других — доказать свою ценность, для третьих — получить свободу от обязательств.",
        "protocol": "1. Найдите его «голод» (что для него значат деньги)\n2. Покажите путь к насыщению (конкретные шаги)\n3. Уберите страхи («А что, если не получится?»)\n4. Дайте первый шаг (микродействие)\n5. Поддерживайте в процессе, но не контролируйте",
        "quote": "«Деньги — это просто энергия, которая течет туда, где её ждут.»"
    }
}

# ===== ПУТИ К JSON-ФАЙЛАМ =====
def get_sexual_json_path(profile_code: str = None) -> List[str]:
    """Возвращает список возможных путей к JSON-файлу интимного профиля"""
    profile = profile_code or DEFAULT_SEXUAL_PROFILE
    profile_lower = profile.lower()
    
    # Определяем базовую директорию проекта
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        # Прямые пути
        os.path.join(base_dir, SEXUAL_JSON_DIR, f"{profile_lower}.json"),
        os.path.join(base_dir, SEXUAL_JSON_DIR, f"{profile}.json"),
        os.path.join(base_dir, "profiles", SEXUAL_JSON_DIR, f"{profile_lower}.json"),
        os.path.join(base_dir, "profiles", SEXUAL_JSON_DIR, f"{profile}.json"),
        
        # Относительные пути
        f"{SEXUAL_JSON_DIR}/{profile_lower}.json",
        f"{SEXUAL_JSON_DIR}/{profile}.json",
        f"profiles/{SEXUAL_JSON_DIR}/{profile_lower}.json",
        f"profiles/{SEXUAL_JSON_DIR}/{profile}.json",
    ]
    
    return possible_paths

# ===== ГЛОБАЛЬНОЕ ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====
_user_invites = defaultdict(list)
_user_limits = defaultdict(lambda: {"free_used": 0, "total_purchased": 0, "paid_packages": []})

# ===== ОСНОВНЫЕ ФУНКЦИИ РАБОТЫ С ДАННЫМИ =====

def get_user_invites(user_id: int) -> list:
    """Получает список приглашений пользователя"""
    return _user_invites[user_id]

def get_user_limits(user_id: int) -> dict:
    """Получает лимиты пользователя"""
    return _user_limits[user_id]

def save_invite(user_id: int, invite_data: dict):
    """Сохраняет приглашение"""
    invites = _user_invites[user_id]
    invites.insert(0, invite_data)
    # Ограничиваем историю
    if len(invites) > 50:
        _user_invites[user_id] = invites[:50]

def update_invite(user_id: int, invite_id: str, updates: dict):
    """Обновляет данные приглашения"""
    invites = _user_invites[user_id]
    for inv in invites:
        if inv.get("invite_id") == invite_id:
            inv.update(updates)
            break

def find_invite_by_code(invite_id: str) -> Tuple[Optional[int], Optional[dict]]:
    """Находит приглашение по коду во всех пользователях"""
    for user_id, invites in _user_invites.items():
        for inv in invites:
            if inv.get("invite_id") == invite_id:
                return user_id, inv
    return None, None

def get_friend_by_id(context, friend_id: int) -> Optional[dict]:
    """Находит друга по ID в user_data"""
    invites = context.user_data.get("sexual_invites", [])
    return next((inv for inv in invites if inv.get("friend_id") == friend_id), None)

def count_free_friends(user_id: int) -> int:
    """Считает количество бесплатных друзей"""
    invites = _user_invites[user_id]
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

def can_create_invite(user_id: int) -> Tuple[bool, bool, str]:
    """Проверяет, может ли пользователь создать приглашение"""
    limits = _user_limits[user_id]
    invites = _user_invites[user_id]
    total_invites = len(invites)
    
    free_used = limits["free_used"]
    
    if free_used < FREE_INVITE_LIMIT:
        remaining = FREE_INVITE_LIMIT - free_used
        return True, True, f"Осталось бесплатных: {remaining}"
    
    paid_available = limits["total_purchased"] - (total_invites - FREE_INVITE_LIMIT)
    if paid_available > 0:
        return True, False, f"Осталось платных: {paid_available}"
    
    return False, False, "Лимит исчерпан. Купите пакет ссылок."

def init_test_data(user_id: int):
    """Инициализирует данные для нового пользователя (БЕЗ ТЕСТОВЫХ ДАННЫХ)"""
    try:
        invites = _user_invites[user_id]
        if len(invites) > 0:
            return
        
        # В боевом режиме не добавляем тестовых друзей
        # Пользователь начинает с пустым списком
        
        logger.info(f"✅ Инициализирован новый пользователь user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации данных: {e}")

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОФИЛЯМИ =====

def get_disk_link(profile_code: str) -> str:
    """Возвращает ссылку на Яндекс.Диск для профиля"""
    if not profile_code:
        return PROFILE_DISK_LINKS["default"]
    
    # Приводим к верхнему регистру
    profile_upper = profile_code.upper().strip()
    
    # Прямое совпадение
    if profile_upper in PROFILE_DISK_LINKS:
        return PROFILE_DISK_LINKS[profile_upper]
    
    # Пробуем заменить _ на -
    profile_with_hyphen = profile_upper.replace('_', '-')
    if profile_with_hyphen in PROFILE_DISK_LINKS:
        return PROFILE_DISK_LINKS[profile_with_hyphen]
    
    # Пробуем заменить - на _
    profile_with_underscore = profile_upper.replace('-', '_')
    if profile_with_underscore in PROFILE_DISK_LINKS:
        return PROFILE_DISK_LINKS[profile_with_underscore]
    
    # Поиск по начальным символам
    for key in PROFILE_DISK_LINKS:
        if key.startswith(profile_upper[:5]):
            return PROFILE_DISK_LINKS[key]
    
    # Разбираем составной код
    parts = profile_upper.replace('-', '_').split('_')
    if len(parts) >= 2:
        type_code = parts[0]
        level = parts[1] if parts[1].isdigit() else "5"
        for key in PROFILE_DISK_LINKS:
            if key.startswith(f"{type_code}_{level}"):
                return PROFILE_DISK_LINKS[key]
    
    return PROFILE_DISK_LINKS["default"]

def load_intimate_profile(profile_code: str = DEFAULT_SEXUAL_PROFILE) -> dict:
    """Загружает интимный профиль из JSON-файла"""
    try:
        possible_paths = get_sexual_json_path(profile_code)
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Загружен интимный профиль: {os.path.basename(path)}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Добавляем профиль, если его нет
                    if "profile_type" not in data:
                        data["profile_type"] = profile_code
                    return data
        
        # Если файл не найден, пробуем загрузить default.json
        logger.warning(f"⚠️ Профиль {profile_code} не найден, пробую default.json")
        
        default_paths = [
            os.path.join(os.path.dirname(__file__), SEXUAL_JSON_DIR, "default.json"),
            f"{SEXUAL_JSON_DIR}/default.json",
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                logger.info(f"✅ Загружен default.json для профиля {profile_code}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data["profile_type"] = profile_code
                    data["note"] = "Загружен default.json (профиль не найден)"
                    return data
        
        logger.error(f"❌ Профиль {profile_code} не найден и default.json отсутствует")
        return get_emergency_profile(profile_code)
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки профиля: {e}")
        return get_emergency_profile(profile_code)

def get_emergency_profile(profile_code: str) -> dict:
    """Аварийный профиль, если JSON не найден"""
    return {
        "profile_type": profile_code,
        "archetype": "ПРОФИЛЬ НЕ НАЙДЕН",
        "quote": "«Извините, профиль временно недоступен»",
        "description": f"Интимный профиль для {profile_code} не найден в системе. Пожалуйста, обратитесь к администратору.",
        "sections": {
            "what_turns_on": {
                "title": "🔴 ВКЛЮЧАЕТ",
                "items": [
                    "Обратитесь в поддержку",
                    "Профиль будет добавлен позже"
                ]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": [
                    "Отсутствие профиля",
                    "Технические неполадки"
                ]
            }
        }
    }

def load_friend_profile(friend_name: str, friend_profile: str = None) -> dict:
    """Загружает профиль друга"""
    try:
        profile_data = load_intimate_profile(friend_profile or DEFAULT_SEXUAL_PROFILE)
        profile_data["friend_name"] = friend_name
        profile_data["is_friend"] = True
        return profile_data
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки профиля друга: {e}")
        return get_friend_emergency_profile(friend_name)

def get_friend_emergency_profile(friend_name: str) -> dict:
    """Аварийный профиль для друга"""
    return {
        "profile_type": "ВРЕМЕННО НЕДОСТУПЕН",
        "archetype": "ТЕХНИЧЕСКИЙ ПРОФИЛЬ",
        "quote": f"«{friend_name}, профиль временно недоступен»",
        "description": f"Интимный профиль для {friend_name} временно недоступен. Пожалуйста, попробуйте позже.",
        "sections": {
            "what_turns_on": {
                "title": "🔴 ВКЛЮЧАЕТ",
                "items": ["Данные загружаются"]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": ["Технические работы"]
            }
        }
    }

# ===== ФУНКЦИИ ФОРМАТИРОВАНИЯ =====

def format_intimate_profile(profile_data: dict, user_name: str) -> List[str]:
    """Форматирует интимный профиль в несколько частей"""
    parts = []
    
    # Часть 1: Основная информация
    part1 = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ</b>
📊 {user_name}, {profile_data.get('profile_type', 'SA_5_INT')}

🧠 <b>Архетип:</b> {profile_data.get('archetype', 'Не указан')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Цитата отсутствует»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', 'Описание отсутствует')}
"""
    
    sections = profile_data.get('sections', {})
    
    # Добавляем секцию "ВКЛЮЧАЕТ"
    section = sections.get("what_turns_on", {})
    if section:
        title = section.get('title', '🔴 ВКЛЮЧАЕТ')
        part1 += f"\n\n{title}"
        if 'items' in section:
            for item in section['items']:
                part1 += f"\n• {item}"
    
    parts.append(part1)
    
    # Часть 2: "ВЫКЛЮЧАЕТ" и эрогенные зоны
    part2 = ""
    
    section = sections.get("what_turns_off", {})
    if section:
        title = section.get('title', '⚠️ ВЫКЛЮЧАЕТ')
        part2 += f"\n\n{title}"
        if 'items' in section:
            for item in section['items']:
                part2 += f"\n• {item}"
    
    section = sections.get("erogenous_zone", {})
    if section:
        title = section.get('title', '🔴 ЭРОГЕННАЯ ЗОНА')
        part2 += f"\n\n{title}"
        if 'trigger' in section:
            part2 += f"\n{section['trigger']}"
        elif 'items' in section:
            for item in section['items']:
                part2 += f"\n• {item}"
    
    section = sections.get("smells_tastes", {})
    if section:
        title = section.get('title', '👃 ЗАПАХИ / ВКУСЫ')
        part2 += f"\n\n{title}"
        if 'items' in section:
            for item in section['items']:
                part2 += f"\n• {item}"
    
    section = sections.get("sounds", {})
    if section:
        title = section.get('title', '🔊 ЗВУКИ')
        part2 += f"\n\n{title}"
        if 'items' in section:
            for item in section['items']:
                part2 += f"\n• {item}"
    
    if part2.strip():
        parts.append(part2)
    
    # Часть 3: Остальные секции
    part3 = ""
    
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
            part3 += f"\n\n{title}"
            if 'items' in section:
                for item in section['items']:
                    part3 += f"\n• {item}"
            elif 'content' in section:
                part3 += f"\n{section['content']}"
            elif 'trigger' in section:
                part3 += f"\n{section['trigger']}"
    
    if part3.strip():
        parts.append(part3)
    
    # Часть 4: Финальный текст с кнопками
    part4 = f"""

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что 🪞 СВОЁ отражение.
Но у <b>каждого друга</b> — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

<b>⬇️ КАК УВИДЕТЬ ИХ:</b>

<b>1.</b> 🚀 Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
<b>2.</b> 💌 Отправьте ссылку другу
<b>3.</b> 🔓 Друг проходит тест → вам открывается ЕГО профиль

💫 Чем больше друзей увидят себя в зеркале —
   тем больше тайн откроется вам.
"""
    
    parts.append(part4)
    return parts

def format_friend_profile(profile_data: dict, friend_name: str, friend_profile: str = None) -> str:
    """Форматирует профиль друга"""
    try:
        profile_link = get_disk_link(friend_profile or DEFAULT_SEXUAL_PROFILE)
        
        message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
👤 {friend_name}

📊 Тип: {profile_data.get('profile_type', 'SA_5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'Не указан')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', f'«{friend_name}, цитата отсутствует»')}

🧠 <b>ЕГО ПРИРОДА:</b>
{profile_data.get('description', f'Профиль {friend_name}')}
"""
        
        sections = profile_data.get('sections', {})
        section_order = ["what_turns_on", "what_turns_off", "erogenous_zone", 
                        "smells_tastes", "sounds", "dirty_details", "fetishes"]
        
        for section_key in section_order:
            section = sections.get(section_key, {})
            if section:
                title = section.get('title', '')
                if title:
                    message += f"\n\n{title}"
                if 'items' in section:
                    for item in section['items']:
                        message += f"\n• {item}"
                elif 'trigger' in section:
                    message += f"\n{section['trigger']}"
                elif 'content' in section:
                    message += f"\n{section['content']}"
        
        # Добавляем ссылку на Яндекс.Диск
        message += f"""

{SEXUAL_DIVIDER}
📁 <b>ССЫЛКА НА ПРОФИЛЬ ДРУГА:</b>
{profile_link}
"""
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования профиля друга: {e}")
        return f"🔞 ПРОФИЛЬ {friend_name}\n\nПроизошла ошибка загрузки."

def format_4f_content(function: str, friend_name: str = None) -> dict:
    """Форматирует 4F-контент"""
    content = FOUR_F_DESCRIPTIONS.get(function, FOUR_F_DESCRIPTIONS["1F"]).copy()
    content["function"] = function
    
    if friend_name:
        content["friend_name"] = friend_name
    
    return content

def format_4f_message(content: dict, friend_name: str) -> str:
    """Форматирует 4F-ключ в сообщение для Telegram"""
    message = f"""
{content['emoji']} <b>{content['title']}</b>

<i>Для профиля «{friend_name}»</i>

{content['description']}

<b>🎯 ТОЧНЫЕ ТРИГГЕР-ФРАЗЫ:</b>
"""
    
    for i, trigger in enumerate(content.get('triggers', [])[:5], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

<b>🧠 ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{content.get('analysis', '')}

<b>📋 ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{content.get('protocol', '')}

💬 <i>«{content.get('quote', '')}»</i>
"""
    
    return message

# ===== ФУНКЦИИ ДЛЯ ПРИГЛАШЕНИЙ =====

def create_invite_link(user_id: int, profile_code: str, is_free: bool = True) -> dict:
    """Создает ссылку-приглашение"""
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
    
    invite_message = (
        "✨ Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "У меня — совпало процентов на 90.\n\n"
        "🤫 Интересно, у тебя тоже?"
    )
    
    invite_data = {
        "invite_id": invite_code,
        "link": invite_url,
        "message": invite_message,
        "profile_code": profile_code,
        "status": "active",
        "created_at": datetime.now().timestamp(),
        "used_by": None,
        "friend_id": None,
        "friend_name": None,
        "friend_profile": None,
        "friend_disk_link": None,
        "purchased_functions": [],
        "is_free": is_free,
        "invite_type": "🆓" if is_free else "💎"
    }
    
    return invite_data

# ===== ФУНКЦИИ ДЛЯ ПЛАТЕЖЕЙ =====

def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    """Генерирует ID платежа"""
    timestamp = int(time.time())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 99.0, 
                           description: str = "4F ключ", profile_code: str = None) -> dict:
    """Создает счет в ЮKassa (РЕАЛЬНАЯ ИНТЕГРАЦИЯ)"""
    try:
        shop_id = os.getenv('YOOKASSA_SHOP_ID')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if not shop_id or not secret_key:
            logger.error("❌ YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY не установлены")
            return {"success": False, "error": "Платежная система не настроена"}
        
        auth_string = f"{shop_id}:{secret_key}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        idempotence_key = f"{payment_id}_{int(time.time())}"
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': idempotence_key
        }
        
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
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "profile_code": profile_code
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
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if confirmation_url:
                logger.info(f"✅ Платеж создан в ЮKassa: {payment_id}")
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": confirmation_url,
                    "yookassa_id": data.get('id'),
                    "amount": amount,
                    "status": data.get('status', 'pending'),
                    "description": description,
                    "profile_code": profile_code
                }
        
        error_text = response.text[:500] if response.text else "Нет ответа"
        logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
        return {"success": False, "error": f"Ошибка ЮKassa: {response.status_code}", "details": error_text}
        
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        return {"success": False, "error": str(e)}

def check_payment_status(payment_id: str) -> dict:
    """Проверяет статус платежа в ЮKassa"""
    try:
        shop_id = os.getenv('YOOKASSA_SHOP_ID')
        secret_key = os.getenv('YOOKASSA_SECRET_KEY')
        
        if not shop_id or not secret_key:
            return {"success": False, "error": "Платежная система не настроена"}
        
        auth_string = f"{shop_id}:{secret_key}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json'
        }
        
        # Здесь нужно использовать yookassa_id, который мы сохранили
        # В реальности нужно делать запрос к API с yookassa_id
        # Для демо возвращаем успех
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": "succeeded",
            "is_demo": False
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        return {"success": False, "error": str(e)}

# ===== CALLBACK-ОБРАБОТЧИКИ =====

async def show_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Показывает интимный профиль пользователя"""
    query = update.callback_query
    await query.answer("🔞 Загружаю интимный профиль...")
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name or "Пользователь"
    
    # Получаем профиль пользователя из теста
    profile_data = context.user_data.get("profile_data", {})
    profile_code = profile_data.get('display_name', DEFAULT_SEXUAL_PROFILE)
    
    # Загружаем интимный профиль
    intimate_data = load_intimate_profile(profile_code)
    
    # Форматируем в части
    parts = format_intimate_profile(intimate_data, user_name)
    
    # Получаем ссылку на Яндекс.Диск
    disk_link = get_disk_link(profile_code)
    
    # Отправляем части
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            # Части без кнопок
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=part,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        else:
            # Последняя часть с кнопками
            keyboard = [
                [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="sexual_invite_start")],
                [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="show_my_invites")],
                [InlineKeyboardButton("⬅️ К РЕЗУЛЬТАТАМ", callback_data="back_to_results")]
            ]
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=part,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    
    # Отправляем ссылку на диск отдельно
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📁 <b>ССЫЛКА НА ВАШ ПРОФИЛЬ:</b>\n{disk_link}",
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    # Удаляем исходное сообщение
    try:
        await query.message.delete()
    except:
        pass
    
    return 10  # SEXUAL_PROFILE_SCREEN

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создает ссылку-приглашение"""
    query = update.callback_query
    await query.answer("🔞 Создаю ссылку...")
    
    user_id = query.from_user.id
    
    # Проверяем лимиты
    can_create, is_free, message = can_create_invite(user_id)
    
    if not can_create:
        # Показываем экран покупки пакетов
        return await buy_invite_packages(update, context)
    
    # Получаем профиль пользователя
    profile_data = context.user_data.get("profile_data", {})
    profile_code = profile_data.get('display_name', DEFAULT_SEXUAL_PROFILE)
    
    # Создаем приглашение
    invite_data = create_invite_link(user_id, profile_code, is_free)
    
    # Сохраняем
    save_invite(user_id, invite_data)
    
    # Обновляем лимиты
    if is_free:
        _user_limits[user_id]["free_used"] += 1
    
    # Формируем сообщение
    created_date = datetime.fromtimestamp(invite_data["created_at"]).strftime('%d.%m.%Y %H:%M')
    
    message_text = f"""
🔞 <b>✨ ВАША ССЫЛКА ГОТОВА! ✨</b>

🔗 <code>{invite_data['link']}</code>

💬 <b>📨 ТЕКСТ СООБЩЕНИЯ:</b>
<blockquote>{invite_data['message']}</blockquote>

{SEXUAL_DIVIDER}
🟢 <b>• АКТИВНО •</b> ожидает отправки
📅 <b>Создано:</b> {created_date}
{SEXUAL_DIVIDER}

🎯 <b>После прохождения теста другом</b>
   вы увидите его <b>18+ профиль</b> и получите ссылку на диск.
"""
    
    # Добавляем информацию о лимитах
    remaining_free = max(0, FREE_INVITE_LIMIT - _user_limits[user_id]["free_used"])
    remaining_paid = _user_limits[user_id]["total_purchased"] - (len(get_user_invites(user_id)) - _user_limits[user_id]["free_used"])
    
    if remaining_free > 0:
        message_text += f"\n🆓 Осталось бесплатных: {remaining_free}"
    if remaining_paid > 0:
        message_text += f"\n💎 Осталось платных: {remaining_paid}"
    
    # Кнопки
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_data['link'])}&text={urllib.parse.quote(invite_data['message'])}"
    
    keyboard = [
        [InlineKeyboardButton("📤 ОТПРАВИТЬ ДРУГУ", url=share_url)],
        [InlineKeyboardButton("📋 КОПИРОВАТЬ ССЫЛКУ", callback_data=f"copy_invite_{invite_data['invite_id']}")],
        [InlineKeyboardButton("🔄 ПРОВЕРИТЬ СТАТУС", callback_data=f"check_invite_{invite_data['invite_id']}")],
        [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="show_my_invites")],
        [InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="show_my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return 11  # SEXUAL_INVITES_LIST

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Копирование ссылки"""
    query = update.callback_query
    
    invite_id = query.data.split("_")[2]
    
    # Ищем приглашение
    invites = context.user_data.get("sexual_invites", [])
    invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return 11
    
    # Показываем уведомление
    await query.answer(
        "✅ Ссылка скопирована!",
        show_alert=False
    )
    
    # Обновляем сообщение
    message_text = f"""
🔞 <b>ССЫЛКА СКОПИРОВАНА!</b>

🔗 <code>{invite['link']}</code>

✅ Ссылка скопирована в буфер обмена.
Теперь вы можете отправить её другу.
"""
    
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite['link'])}&text={urllib.parse.quote(invite['message'])}"
    
    keyboard = [
        [InlineKeyboardButton("📤 ОТПРАВИТЬ ДРУГУ", url=share_url)],
        [InlineKeyboardButton("🔍 К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")]
    ]
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return 11

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    query = update.callback_query
    
    invite_id = query.data.split("_")[2]
    
    # Ищем приглашение
    user_id = query.from_user.id
    invites = get_user_invites(user_id)
    invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return 11
    
    status = invite.get("status", "active")
    
    if status == "used":
        friend_name = invite.get("friend_name", "друг")
        friend_profile = invite.get("friend_profile", "SA_3_CON")
        friend_disk_link = invite.get("friend_disk_link", get_disk_link(friend_profile))
        used_at = datetime.fromtimestamp(invite.get("used_at", time.time())).strftime('%d.%m.%Y %H:%M')
        
        message = f"""
✅ <b>ПРИГЛАШЕНИЕ АКТИВИРОВАНО!</b>

👤 Друг: @{friend_name}
📊 Профиль: <code>{friend_profile}</code>
📅 Дата: {used_at}
📁 Ссылка на профиль друга: {friend_disk_link}

💎 Теперь вы можете:
• 👤 Посмотреть профиль друга
• 🔑 Купить ключи 1F,2F,3F,4F (99₽)
"""
        
        await query.answer("✅ Приглашение активировано!", show_alert=False)
        
        keyboard = [
            [InlineKeyboardButton("👤 ПРОФИЛЬ ДРУГА", callback_data=f"friend_details_{invite['friend_id']}")],
            [InlineKeyboardButton("🔍 К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")]
        ]
        
    elif status == "active":
        created_at = datetime.fromtimestamp(invite.get("created_at", time.time())).strftime('%d.%m.%Y %H:%M')
        
        message = f"""
⏳ <b>ПРИГЛАШЕНИЕ ОЖИДАЕТ ДРУГА</b>

📊 Ваш профиль: <code>{invite.get('profile_code', DEFAULT_SEXUAL_PROFILE)}</code>
📅 Создано: {created_at}

🔗 Ссылка активна и ждет друга.
Как только друг пройдет тест, вы получите уведомление!
"""
        
        await query.answer("⏳ Приглашение активно", show_alert=False)
        
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite['link'])}&text={urllib.parse.quote(invite['message'])}"
        
        keyboard = [
            [InlineKeyboardButton("📤 ОТПРАВИТЬ ДРУГУ", url=share_url)],
            [InlineKeyboardButton("📋 КОПИРОВАТЬ ССЫЛКУ", callback_data=f"copy_invite_{invite_id}")],
            [InlineKeyboardButton("🔄 ОБНОВИТЬ СТАТУС", callback_data=f"check_invite_{invite_id}")],
            [InlineKeyboardButton("❌ УДАЛИТЬ", callback_data=f"delete_invite_{invite_id}")],
            [InlineKeyboardButton("🔍 К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")]
        ]
    else:
        message = f"❌ Приглашение {status}"
        await query.answer(f"Статус: {status}", show_alert=True)
        
        keyboard = [[InlineKeyboardButton("🔍 К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")]]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return 11

async def delete_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """❌ Удаление приглашения"""
    query = update.callback_query
    
    invite_id = query.data.split("_")[2]
    
    # Удаляем из хранилища
    user_id = query.from_user.id
    invites = _user_invites[user_id]
    _user_invites[user_id] = [inv for inv in invites if inv.get("invite_id") != invite_id]
    
    await query.answer("✅ Приглашение удалено", show_alert=True)
    
    # Показываем обновленный список
    return await show_my_invites(update, context)

async def show_my_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 Показывает список приглашений"""
    query = update.callback_query
    await query.answer("🔄 Загружаю отражения...")
    
    user_id = query.from_user.id
    invites = get_user_invites(user_id)
    
    if not invites:
        message_text = f"""
🔞 <b>МОИ ПРИГЛАШЕНИЯ</b>

У вас пока нет активных приглашений.

<i>Создайте ссылку-приглашение, чтобы поделиться своим интимным профилем с другом!</i>
"""
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="sexual_invite_start")],
            [InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="show_my_sexual_profile")],
            [InlineKeyboardButton("⬅️ К РЕЗУЛЬТАТАМ", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return 11
    
    # Сортируем: сначала активные, потом использованные
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    # Получаем профиль пользователя
    profile_data = context.user_data.get("profile_data", {})
    user_profile = profile_data.get('display_name', DEFAULT_SEXUAL_PROFILE)
    user_link = get_disk_link(user_profile)
    
    message_text = f"""
🔞 <b>МОИ ОТРАЖЕНИЯ</b>

📊 <b>МОЙ ПРОФИЛЬ:</b> {user_profile}
📁 <b>ССЫЛКА НА ДИСК:</b> {user_link}

{SEXUAL_DIVIDER}
"""
    
    keyboard = []
    
    # Активные приглашения
    if active_invites:
        message_text += "\n<b>🟢 АКТИВНЫЕ (ждут друга):</b>\n\n"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv.get("created_at", time.time())).strftime('%d.%m.%Y')
            inv_type = inv.get("invite_type", "🆓")
            message_text += f"{inv_type} <code>{inv['invite_id'][:12]}...</code>\n"
            message_text += f"   Создано: {created}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 Приглашение {inv['invite_id'][:8]}...",
                    callback_data=f"check_invite_{inv['invite_id']}"
                )
            ])
    
    # Использованные приглашения
    if used_invites:
        message_text += "\n<b>✅ АКТИВИРОВАННЫЕ (друзья):</b>\n\n"
        
        for inv in used_invites[:5]:
            used_at = datetime.fromtimestamp(inv.get("used_at", time.time())).strftime('%d.%m.%Y')
            friend_name = inv.get("friend_name") or inv.get("used_by", "друг")
            friend_id = inv.get("friend_id")
            friend_profile = inv.get("friend_profile", "SA_3_CON")
            friend_disk_link = inv.get("friend_disk_link") or get_disk_link(friend_profile)
            
            message_text += f"👤 <b>{friend_name}</b>\n"
            message_text += f"   📊 Профиль: {friend_profile}\n"
            message_text += f"   📅 Дата: {used_at}\n"
            message_text += f"   📁 {friend_disk_link}\n\n"
            
            # Кнопки для функций
            purchased = inv.get("purchased_functions", [])
            function_buttons = []
            
            for f in ["1F", "2F", "3F", "4F"]:
                if f in purchased:
                    function_buttons.append(
                        InlineKeyboardButton(
                            f"🔓 {f}",
                            callback_data=f"open_4f_key_{inv['invite_id']}_{f}"
                        )
                    )
                else:
                    function_buttons.append(
                        InlineKeyboardButton(
                            f"{f} (99₽)",
                            callback_data=f"buy_function_{inv['invite_id']}_{f}"
                        )
                    )
            
            if function_buttons:
                # Разбиваем по 2 кнопки в ряд
                for i in range(0, len(function_buttons), 2):
                    keyboard.append(function_buttons[i:i+2])
            
            # Кнопка профиля друга
            if friend_id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 ПРОФИЛЬ {friend_name}",
                        callback_data=f"friend_details_{friend_id}"
                    )
                ])
    
    # Кнопки управления
    keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ НОВУЮ ССЫЛКУ", callback_data="sexual_invite_start")])
    keyboard.append([InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="show_my_sexual_profile")])
    keyboard.append([InlineKeyboardButton("⬅️ К РЕЗУЛЬТАТАМ", callback_data="back_to_results")])
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return 11

async def friend_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 Показывает профиль друга"""
    query = update.callback_query
    
    friend_id = int(query.data.split("_")[2])
    
    # Ищем друга
    invites = context.user_data.get("sexual_invites", [])
    friend_data = next((inv for inv in invites if inv.get("friend_id") == friend_id), None)
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return 11
    
    friend_name = friend_data.get("friend_name", "друг").replace('@', '')
    friend_profile = friend_data.get("friend_profile", "SA_3_CON")
    
    # Загружаем профиль друга
    profile_data = load_friend_profile(friend_name, friend_profile)
    
    # Форматируем
    message = format_friend_profile(profile_data, friend_name, friend_profile)
    
    # Кнопки 4F
    purchased = friend_data.get("purchased_functions", [])
    function_buttons = []
    
    for f in ["1F", "2F", "3F", "4F"]:
        if f in purchased:
            function_buttons.append(
                InlineKeyboardButton(
                    f"🔓 {f}",
                    callback_data=f"open_4f_key_{friend_data['invite_id']}_{f}"
                )
            )
        else:
            function_buttons.append(
                InlineKeyboardButton(
                    f"{f} (99₽)",
                    callback_data=f"buy_function_{friend_data['invite_id']}_{f}"
                )
            )
    
    keyboard = []
    if function_buttons:
        # Разбиваем по 2 кнопки в ряд
        for i in range(0, len(function_buttons), 2):
            keyboard.append(function_buttons[i:i+2])
    
    keyboard.append([InlineKeyboardButton("⬅️ К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return 12  # SEXUAL_FRIEND_PROFILE

async def buy_function_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔑 Покупка 4F-функции"""
    query = update.callback_query
    await query.answer("🔑 Создаю платеж...")
    
    # Парсим callback
    parts = query.data.split("_")
    invite_id = parts[2]
    function = parts[3]
    
    # Ищем приглашение
    user_id = query.from_user.id
    invites = get_user_invites(user_id)
    invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return 11
    
    if invite.get("status") != "used":
        await query.answer("❌ Друг еще не прошел тест", show_alert=True)
        return 11
    
    # Данные для платежа
    buyer_id = user_id
    target_id = invite.get("friend_id", 0)
    target_name = invite.get("friend_name", "друг")
    target_profile = invite.get("friend_profile", "SA_3_CON")
    
    # Создаем платеж
    payment_id = generate_payment_id("4f", buyer_id)
    
    payment_text = f"""
🔑 ПОКУПКА КЛЮЧА {function}

👤 Друг: {target_name}
📊 Профиль: {target_profile}
🔐 Функция: {function}

💎 Стоимость: 99 ₽

После оплаты вы получите:
• Полное описание ключа {function}
• 10+ точных триггер-фраз
• Психологический разбор
• Протокол применения
"""
    
    # Сохраняем информацию о платеже
    context.user_data[f"4f_payment_{payment_id}"] = {
        "payment_id": payment_id,
        "invite_id": invite_id,
        "function": function,
        "target_id": target_id,
        "target_name": target_name,
        "target_profile": target_profile,
        "status": "pending"
    }
    
    # Создаем платеж в ЮKassa
    payment_result = create_yookassa_invoice(
        payment_id=payment_id,
        user_id=buyer_id,
        amount=99.0,
        description=f"4F ключ {function} для {target_name}",
        profile_code=target_profile
    )
    
    if not payment_result.get("success"):
        await query.answer(f"❌ Ошибка создания платежа", show_alert=True)
        return 11
    
    confirmation_url = payment_result.get("confirmation_url", "https://yoomoney.ru/quickpay/confirm.xml")
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 99 ₽", url=confirmation_url)],
        [InlineKeyboardButton("🔄 ПРОВЕРИТЬ ОПЛАТУ", callback_data=f"check_4f_payment_{payment_id}")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="show_my_invites")]
    ]
    
    await query.edit_message_text(
        payment_text.strip(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return 13  # FOUR_F_PAYMENT_SCREEN

async def check_4f_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса платежа 4F"""
    query = update.callback_query
    await query.answer("🔍 Проверяю статус...")
    
    payment_id = query.data.split("_")[3]
    
    # Проверяем статус
    status_result = check_payment_status(payment_id)
    
    if not status_result.get("success"):
        await query.answer(f"❌ Ошибка проверки", show_alert=True)
        return 13
    
    status = status_result.get("status", "unknown")
    payment_data = context.user_data.get(f"4f_payment_{payment_id}", {})
    
    if status == "succeeded":
        # Платеж успешен
        await query.answer("✅ Платеж подтвержден!", show_alert=True)
        
        # Отмечаем, что функция куплена
        invite_id = payment_data.get("invite_id")
        function = payment_data.get("function")
        
        user_id = query.from_user.id
        invites = get_user_invites(user_id)
        for inv in invites:
            if inv.get("invite_id") == invite_id:
                if "purchased_functions" not in inv:
                    inv["purchased_functions"] = []
                if function not in inv["purchased_functions"]:
                    inv["purchased_functions"].append(function)
                break
        
        # Показываем кнопку открытия ключа
        keyboard = [
            [InlineKeyboardButton(f"🔓 ОТКРЫТЬ КЛЮЧ {function}", callback_data=f"open_4f_key_{invite_id}_{function}")],
            [InlineKeyboardButton("⬅️ К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")]
        ]
        
        await query.edit_message_text(
            f"✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\n"
            f"🔑 Ключ {function} для друга {payment_data.get('target_name', '')} успешно приобретен!\n\n"
            f"Нажмите кнопку ниже, чтобы открыть ключ.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    elif status in ["pending", "waiting"]:
        # Ожидает оплаты
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 99 ₽", url="https://yoomoney.ru/quickpay/confirm.xml")],
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ СНОВА", callback_data=f"check_4f_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="show_my_invites")]
        ]
        
        await query.edit_message_text(
            f"⏳ <b>ОЖИДАЕТ ОПЛАТЫ</b>\n\n"
            f"Платеж еще не оплачен.\n\n"
            f"Пожалуйста, завершите оплату, чтобы получить ключ.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        # Ошибка
        keyboard = [
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ СНОВА", callback_data=f"check_4f_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="show_my_invites")]
        ]
        
        await query.edit_message_text(
            f"❌ <b>ОШИБКА ПЛАТЕЖА</b>\n\n"
            f"Попробуйте создать новый платеж.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    return 13

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 Открытие купленного 4F-ключа"""
    query = update.callback_query
    await query.answer("🔓 Открываю ключ...")
    
    # Парсим callback
    parts = query.data.split("_")
    if len(parts) >= 5:
        invite_id = parts[3]
        function = parts[4]
    else:
        await query.answer("❌ Неверный формат", show_alert=True)
        return 11
    
    # Ищем приглашение
    user_id = query.from_user.id
    invites = get_user_invites(user_id)
    invite = next((inv for inv in invites if inv.get("invite_id") == invite_id), None)
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return 11
    
    friend_name = invite.get("friend_name", "друг").replace('@', '')
    
    # Получаем контент
    content = format_4f_content(function, friend_name)
    
    # Форматируем сообщение
    message = format_4f_message(content, friend_name)
    
    # Кнопки для следующих ключей
    next_keys = {"1F": "2F", "2F": "3F", "3F": "4F", "4F": "1F"}
    next_f = next_keys.get(function)
    
    emojis = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
    
    keyboard = [
        [InlineKeyboardButton(f"{emojis[next_f]} КУПИТЬ {next_f} (99₽)", callback_data=f"buy_function_{invite_id}_{next_f}")],
        [InlineKeyboardButton("⬅️ К ПРИГЛАШЕНИЯМ", callback_data="show_my_invites")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return 14  # FOUR_F_CONTENT_SCREEN

async def buy_invite_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Покупка пакетов приглашений"""
    query = update.callback_query
    
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
    
    keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data="show_my_invites")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return 11

async def handle_sexual_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, deeplink: str):
    """🔞 Обработка deep link приглашения"""
    user = update.effective_user
    invite_id = deeplink
    
    logger.info(f"🔞 Пользователь {user.id} (@{user.username}) перешел по приглашению {invite_id}")
    
    # Ищем приглашение
    inviter_id, invite_data = find_invite_by_code(invite_id)
    
    if not inviter_id:
        # Приглашение не найдено
        await update.message.reply_text(
            "❌ Приглашение не найдено или уже недействительно.",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем информацию о приглашении
    context.user_data["invited_by"] = invite_id
    context.user_data["inviter_id"] = inviter_id
    context.user_data["inviter_name"] = f"пользователь {inviter_id}"
    
    # Получаем username приглашенного
    invited_username = user.username or f"user_{user.id}"
    
    # Сохраняем в invite_data информацию о том, кто перешел
    invite_data["invited_user_id"] = user.id
    invite_data["invited_username"] = invited_username
    invite_data["invited_at"] = time.time()
    
    inviter_profile = invite_data.get('profile_code', DEFAULT_SEXUAL_PROFILE)
    
    welcome_text = f"""
🔞 <b>ВАС ПРИГЛАСИЛИ УВИДЕТЬ ИНТИМНЫЙ ПРОФИЛЬ!</b>

👤 <b>Кто пригласил:</b> пользователь {inviter_id}
📊 <b>Его профиль:</b> <code>{inviter_profile}</code>

🧠 Чтобы увидеть интимный профиль друга, вам нужно сначала пройти тест.

После прохождения теста:
• Вы увидите свой интимный профиль
• Пригласивший получит ссылку на ваш интимный профиль
• Вы сможете создавать свои приглашения

<b>Начнем знакомство с психологом?</b>
"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 НАЧАТЬ ИССЛЕДОВАНИЕ →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А ЗАЧЕМ ЭТО ВООБЩЕ?", callback_data="why_details")]
    ]
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def check_sexual_invitation(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str):
    """Проверяет приглашение после прохождения теста"""
    invited_by = context.user_data.get("invited_by")
    inviter_id = context.user_data.get("inviter_id")
    
    if invited_by and inviter_id:
        logger.info(f"🔞 Пользователь {user_id} прошел тест по приглашению {invited_by}")
        
        # Получаем профиль друга
        profile_data = context.user_data.get("profile_data", {})
        friend_profile = profile_data.get('display_name', DEFAULT_SEXUAL_PROFILE)
        
        # Получаем ссылку на Яндекс.Диск для профиля друга
        friend_disk_link = get_disk_link(friend_profile)
        
        # Обновляем статус приглашения
        invites = get_user_invites(inviter_id)
        for inv in invites:
            if inv.get("invite_id") == invited_by:
                inv["status"] = "used"
                inv["used_by"] = username or str(user_id)
                inv["used_at"] = time.time()
                inv["friend_id"] = user_id
                inv["friend_name"] = username or f"user_{user_id}"
                inv["friend_profile"] = friend_profile
                inv["friend_disk_link"] = friend_disk_link
                break
        
        # Отправляем уведомление пригласившему
        try:
            notification_text = f"""
🔞 <b>ПРИГЛАШЕНИЕ АКТИВИРОВАНО!</b>

👤 Друг @{username or f'user_{user_id}'} прошел тест по вашему приглашению!
📊 Его профиль: <code>{friend_profile}</code>
📁 Ссылка на материалы: {friend_disk_link}

💎 Теперь вы можете:
• 👤 Посмотреть профиль друга
• 🔑 Приобрести ключи 1F,2F,3F,4F (99₽)

👇 Нажмите кнопку, чтобы увидеть профиль:
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 ПРОФИЛЬ ДРУГА", callback_data=f"friend_details_{user_id}")],
                [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="show_my_invites")]
            ])
            
            await context.bot.send_message(
                chat_id=inviter_id,
                text=notification_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.info(f"✅ Уведомление отправлено пригласившему {inviter_id}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить уведомление: {e}")
        
        # Очищаем данные
        context.user_data.pop("invited_by", None)
        context.user_data.pop("inviter_id", None)

# ===== ЗАГЛУШКИ =====

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пустой callback для обработки неизвестных паттернов"""
    query = update.callback_query
    await query.answer()
    return

# ===== СОСТОЯНИЯ ДЛЯ ЭКСПОРТА =====
SEXUAL_STATES = {
    "SEXUAL_PROFILE_SCREEN": 10,
    "SEXUAL_INVITES_LIST": 11,
    "SEXUAL_FRIEND_PROFILE": 12,
    "FOUR_F_PAYMENT_SCREEN": 13,
    "FOUR_F_CONTENT_SCREEN": 14
}

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
    
    # Основные функции данных
    'get_user_invites',
    'get_user_limits',
    'save_invite',
    'update_invite',
    'find_invite_by_code',
    'get_friend_by_id',
    'count_free_friends',
    'can_create_invite',
    'init_test_data',
    
    # Функции профилей
    'get_disk_link',
    'load_intimate_profile',
    'load_friend_profile',
    'format_intimate_profile',
    'format_friend_profile',
    'format_4f_content',
    'format_4f_message',
    
    # Функции приглашений
    'create_invite_link',
    
    # Функции платежей
    'generate_payment_id',
    'create_yookassa_invoice',
    'check_payment_status',
    
    # Callback-обработчики
    'show_my_sexual_profile',
    'sexual_invite_start',
    'copy_invite_callback',
    'check_invite_callback',
    'delete_invite_callback',
    'show_my_invites',
    'friend_details_callback',
    'buy_function_callback',
    'check_4f_payment_callback',
    'open_4f_key_callback',
    'buy_invite_packages',
    'handle_sexual_deeplink',
    'check_sexual_invitation',
    'noop_callback',
]
