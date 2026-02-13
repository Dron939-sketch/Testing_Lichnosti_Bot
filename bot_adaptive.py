#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 12.1 - УЛУЧШЕННАЯ ЗАГРУЗКА ПРОФИЛЯ
✅ Полностью переработан экран "Мои отражения" под ваш минималистичный дизайн
✅ Добавлены ссылки на Яндекс.Диск для каждого профиля
✅ Двухуровневая система 4F: кратко (обучайка) и подробно (стимульный контроль)
✅ Все кнопки управления убраны, только навигационные
✅ УЛУЧШЕНО: умный поиск файла профиля с диагностикой
✅ УЛУЧШЕНО: подробное логирование каждого шага
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
import traceback
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКА =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
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

# ===== СОСТОЯНИЯ =====
RESULTS_SCREEN = 0
MY_SEXUAL_PROFILE = 1
INVITES_LIST = 2
FRIEND_MENU = 3
FOUR_F_MENU = 4
FOUR_F_CONTENT = 5
FOUR_F_PAYMENT_SCREEN = 6
BUY_PACKAGES = 7
FOUR_F_MAIN = 8
FOUR_F_DETAILED = 9

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1

# НОВЫЕ константы для лимитов ссылок
FREE_INVITE_LIMIT = 3
INVITE_PACKAGES = {
    "3": {"price": 299, "links": 3, "emoji": "🥉", "popular": False},
    "5": {"price": 499, "links": 5, "emoji": "🥈", "popular": True},
    "10": {"price": 899, "links": 10, "emoji": "🥇", "popular": False}
}

# ===== ССЫЛКИ НА ЯНДЕКС.ДИСК =====
USER_DISK_LINK = "https://disk.yandex.ru/d/EYPIF9_puI_t0A"

PROFILE_DISK_LINKS = {
    # Стандартные профили
    "SA-3_CON": "https://disk.yandex.ru/d/abc123def",
    "SA-4_VAL": "https://disk.yandex.ru/d/def456ghi",
    "SA-5_INT": "https://disk.yandex.ru/d/ghi789jkl",
    
    # Интимные профили
    "IP-3_CON": "https://disk.yandex.ru/d/jkl012mno",
    "IP-4_VAL": "https://disk.yandex.ru/d/mno345pqr",
    "IP-5_INT": "https://disk.yandex.ru/d/pqr678stu",
    
    # Дефолтная
    "default": "https://disk.yandex.ru/d/xyz789uvw"
}

def get_disk_link_by_profile(profile_code: str) -> str:
    """Возвращает ссылку на Яндекс.Диск для профиля"""
    return PROFILE_DISK_LINKS.get(profile_code, PROFILE_DISK_LINKS["default"])

# ===== ОБНОВЛЕННЫЕ 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {
    "1F": "🔥",
    "2F": "🏃", 
    "3F": "🧬",
    "4F": "🍽"
}

FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ",
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

FOUR_F_SUBTITLES = {
    "1F": "🔥 Стимулы, запускающие агрессию",
    "2F": "🏃 Стимулы, запускающие страх и избегание",
    "3F": "🧬 Стимулы, запускающие желание",
    "4F": "🍽 Стимулы, запускающие режим заработка"
}

# ===== ПОДРОБНЫЕ ОПИСАНИЯ 4F (ДЛЯ ПОКУПКИ) =====
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
   • Списку его ЛИЧНЫХ триггеров (что конкретно заводит именно его)
   • 3 фразам-гасителям, которые переключают реакцию
   • Пониманию, почему он срывается на вас (стимул-реакция)
   • Технике «Торможение» — как не дать конфликту разгореться

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием гнева.
Вы будете знать, каких стимулов избегать, а какие — использовать.""",
    
    "2F": """🏃 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ БЕГСТВО</b>

Страх — это реакция избегания.
Она включается, когда мозг видит СТИМУЛ, похожий на прошлую угрозу.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования
   • Определенные темы разговоров

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • Его личным триггерам страха (что включает режим «беги»)
   • 3 якорям безопасности (стимулы, снимающие тревогу)
   • Пониманию, почему он закрывается и уходит
   • Технике «Безопасная среда» — как говорить без страха

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием тревоги.
Вы станете для него сигналом безопасности, а не угрозы.""",
    
    "3F": """🧬 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЖЕЛАНИЕ</b>

Сексуальное влечение — это цепочка стимулов.
Определенные слова, взгляды, касания работают как ПАРОЛЬ.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Особая интонация голоса
   • Зрительный контакт определенной длины
   • Неожиданные касания
   • Контекст и обстановка

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • 3 словам-паролям (аудиальные стимулы)
   • 3 касаниям-ключам (тактильные стимулы)
   • Его эротическому сценарию (последовательность стимулов)
   • Пониманию, что ГАСИТ желание (стоп-стимулы)

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием возбуждения.
Вы узнаете точную последовательность действий, которая включает его режим «хочу».""",
    
    "4F": """🍽 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ РЕЖИМ «ДЕНЬГИ»</b>

Для него деньги = безопасность, статус, свобода.
Это состояние включается определенными ТРИГГЕРАМИ.

<b>🎯 ЧТО ЯВЛЯЕТСЯ ПУСКОВЫМ КЛЮЧОМ:</b>
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка
   • Определенные фразы-мотиваторы

<b>🔑 ЭТОТ КЛЮЧ ДАЁТ ДОСТУП К:</b>
   • 3 фразам, которые включают его «режим предпринимателя»
   • Пониманию, что тормозит его заработок (стоп-стимулы)
   • Технике «Топливо» — как говорить о деньгах без конфликтов
   • Сценарию просьбы (как просить, чтобы он хотел дать)

<b>⚡️ ЧТО ВЫ ПОЛУЧИТЕ:</b>
Управление его состоянием мотивации.
Вы будете знать, какие стимулы зажигают его, а какие — гасят."""
}

FOUR_F_TAGS = {
    "1F": "🔥 Стимулы агрессии • 3 ключа-включателя • 3 гасителя",
    "2F": "🏃 Стимулы страха • 3 триггера бегства • 3 якоря безопасности",
    "3F": "🧬 Стимулы желания • 3 слова-пароля • 3 касания-ключа",
    "4F": "🍽 Стимулы мотивации • 3 фразы-включателя • Техника просьбы"
}

# ===== ОБУЧАЙКА 4F (КРАТКАЯ ВЕРСИЯ) =====
FOUR_F_EXPLANATION = """
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>

🧬 4F — это 4 базовые реакции психики:
Нападение, бегство, секс, поглощение.
Ключи к управлению состояниями другого человека.

<b>1F 🔥 НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Что включает его агрессию
└ Как быстро её погасить

<b>2F 🏃 БЕГСТВО / СТРАХ</b>
└ Чего он боится на самом деле
└ Как стать для него безопасностью

<b>3F 🧬 СЕКС / ЖЕЛАНИЕ</b>
└ Что реально его заводит
└ 3 слова и 3 касания-ключа

<b>4F 🍽 ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Что запускает режим заработка
└ Как говорить с ним о деньгах

💰 <b>Цена: 1₽</b> (тестовый режим)
"""

# ===== ПОДРОБНОЕ ОПИСАНИЕ 4F (ДЛЯ ОБУЧАЙКИ) =====
FOUR_F_DETAILED_EXPLANATION = """
🔥 <b>1F - ЯРОСТЬ / НАПАДЕНИЕ</b>
<i>Стимулы, запускающие агрессию</i>

😤 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЯРОСТЬ</b>

Его агрессия не возникает из ниоткуда.
Это реакция на конкретные ТРИГГЕРЫ.

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Критика при свидетелях
   • Обесценивание его усилий
   • Игнорирование границ
   • Определенные интонации

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • Список его личных триггеров
   • 3 фразы-гасителя
   • Технику «Торможение»

══════════════════════

🏃 <b>2F - СТРАХ / БЕГСТВО</b>
<i>Стимулы, запускающие избегание</i>

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 якоря безопасности
   • Технику «Безопасная среда»

══════════════════════

🧬 <b>3F - СЕКС / ЖЕЛАНИЕ</b>
<i>Стимулы, запускающие влечение</i>

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Особая интонация
   • Зрительный контакт
   • Неожиданные касания

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 слова-пароля
   • 3 касания-ключа
   • Эротический сценарий

══════════════════════

🍽 <b>4F - ДЕНЬГИ / ПОГЛОЩЕНИЕ</b>
<i>Стимулы, запускающие режим заработка</i>

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 фразы-мотиватора
   • Технику просьбы
   • Сценарий «Топливо»
"""

# ===== УЛУЧШЕННАЯ ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ ИЗ JSON =====
def load_intimate_profile() -> dict:
    """Загружает интимный профиль - ищет в нескольких местах"""
    try:
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Все возможные пути где может лежать файл
        possible_paths = [
            # Вариант А: sexual_18 рядом с ботом (ПРИОРИТЕТ)
            os.path.join(bot_dir, "sexual_18", "sa_5_int.json"),
            
            # Вариант Б: через PROJECT_ROOT
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            
            # Относительные пути
            os.path.join("sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
            
            # Абсолютные пути (для Render.com)
            "/opt/render/project/src/sexual_18/sa_5_int.json",
            "/opt/render/project/src/profiles/sexual_18/sa_5_int.json",
        ]
        
        logger.info("🔍 Поиск файла профиля:")
        for path in possible_paths:
            logger.info(f"   Проверяем: {path}")
            if os.path.exists(path):
                logger.info(f"   ✅ НАЙДЕН: {path}")
                
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Проверяем что загрузили
                    sections = data.get('sections', {})
                    logger.info(f"   📊 Секций загружено: {len(sections)}")
                    
                    # Если секции есть - успех
                    if sections:
                        logger.info(f"   ✅ Профиль успешно загружен: {data.get('profile_type', 'unknown')}")
                        return data
                    else:
                        logger.warning("   ⚠️ Файл найден но секции пустые!")
                        return data
            
            logger.info(f"   ❌ Не найден")
        
        # Если ничего не нашли
        logger.error("❌ Файл sa_5_int.json не найден нигде!")
        
        # Диагностика - покажем содержимое директорий
        if os.path.exists(os.path.join(bot_dir, "sexual_18")):
            logger.info(f"📁 В sexual_18 есть: {os.listdir(os.path.join(bot_dir, 'sexual_18'))}")
        if os.path.exists(os.path.join(PROJECT_ROOT, "sexual_18")):
            logger.info(f"📁 В PROJECT_ROOT/sexual_18 есть: {os.listdir(os.path.join(PROJECT_ROOT, 'sexual_18'))}")
        if os.path.exists(os.path.join(PROJECT_ROOT, "profiles", "sexual_18")):
            logger.info(f"📁 В profiles/sexual_18 есть: {os.listdir(os.path.join(PROJECT_ROOT, 'profiles', 'sexual_18'))}")
        
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
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.\nВы не занимаетесь любовью — вы служите ей.\nИ каждый раз — как в первый. И каждый раз — как в последний.",
        "sections": {}
    }

def format_intimate_profile(profile_data: dict, user_name: str) -> str:
    """Форматирует интимный профиль с новым дизайном"""
    try:
        message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ</b>
{user_name}

📊 Тип: {profile_data.get('profile_type', 'SA-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', '')}
"""
        
        sections = profile_data.get('sections', {})
        
        section_order = [
            "what_turns_on", "what_turns_off", "smells_tastes", "sounds",
            "dirty_details", "fetishes", "places", "morning", "secret_desires",
            "whispers", "core", "compliments", "tells", "remains"
        ]
        
        for section_key in section_order:
            section = sections.get(section_key, {})
            if section:
                title = section.get('title', '')
                message += f"\n\n{title}"
                
                if 'items' in section:
                    for item in section['items']:
                        message += f"\n• {item}"
                elif 'content' in section:
                    message += f"\n{section['content']}"
        
        message += f"""

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что СВОЁ отражение.
Но у <b>каждого друга</b> — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

<b>⬇️ КАК УВИДЕТЬ ИХ:</b>

<b>1.</b> 🚀 Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
<b>2.</b> 💌 Отправьте ссылку другу
<b>3.</b> 🔓 Друг проходит тест → вам открывается ЕГО профиль

<b>💫 Чем больше друзей увидят себя в зеркале —</b>
   <b>тем больше тайн откроется вам.</b>
"""
        
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования профиля: {e}")
        return "🔞 ИНТИМНЫЙ ПРОФИЛЬ\n\nПроизошла ошибка загрузки. Пожалуйста, попробуйте позже."

# ===== ЗАГРУЗКА ТЕСТОВОГО ИНТИМНОГО ПРОФИЛЯ ДЛЯ ДРУГА =====
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
    """Загружает стандартный профиль друга"""
    return {
        "archetype": "Автономный стратег",
        "quote": "«Я не ищу одобрения — я ищу эффективность.»",
        "pain": "Вам сложно делегировать. Вы уверены: «Хочешь сделать хорошо — сделай сам».",
        "immediate_tool": "Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.",
        "cta": "Исследуйте баланс между автономией и доверием."
    }

# ===== ЗАГРУЗКА 4F-КОНТЕНТА =====
def load_4f_content(function: str) -> dict:
    """Загружает контент 4F-ключа"""
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
            "subtitle": FOUR_F_SUBTITLES[function],
            "description": FOUR_F_DESCRIPTIONS[function],
            "tag": FOUR_F_TAGS[function],
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
            "subtitle": "",
            "description": "Произошла ошибка. Пожалуйста, попробуйте позже.",
            "tag": "",
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
    payment_id = f"{prefix}_{timestamp}_{random_str}_{user_suffix}"
    logger.info(f"💰 Сгенерирован payment_id: {payment_id}")
    return payment_id

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """Создает платеж в ЮKassa"""
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

# ===== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =====
USER_PROFILE = {
    "display_name": "SA-5_INT",
    "type_code": "SA",
    "level": 5,
    "dilts_code": "int"
}

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====
user_invites = {}

def get_user_invites(user_id: int) -> list:
    if user_id not in user_invites:
        user_invites[user_id] = []
        logger.info(f"👤 Создано хранилище для пользователя {user_id}")
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    invites = get_user_invites(user_id)
    count = len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])
    return count

def init_test_data(user_id: int):
    """Инициализирует тестовые данные с created_at и is_free"""
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

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ЛИМИТОВ =====
def get_user_limits(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Получает или создает данные о лимитах пользователя"""
    return context.user_data.setdefault("invite_limits", {
        "free_used": 0,
        "total_purchased": 0,
        "paid_packages": []
    })

def can_create_invite(user_limits: dict, total_invites: int) -> tuple:
    """
    Проверяет, может ли пользователь создать ссылку
    Возвращает (can_create: bool, is_free: bool, message: str)
    """
    free_used = user_limits["free_used"]
    
    if free_used < FREE_INVITE_LIMIT:
        remaining = FREE_INVITE_LIMIT - free_used
        return True, True, f"Осталось бесплатных: {remaining}"
    
    paid_available = user_limits["total_purchased"] - (total_invites - FREE_INVITE_LIMIT)
    if paid_available > 0:
        return True, False, f"Осталось платных: {paid_available}"
    
    return False, False, "Лимит исчерпан. Купите пакет ссылок."

def create_progress_bar(current: int, total: int, length: int = 3) -> str:
    """Создает прогресс-бар"""
    if total == 0:
        return "░" * length
    filled = int(length * current / total)
    empty = length - filled
    return "▓" * filled + "░" * empty

# ============================================
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота"""
    try:
        user = update.effective_user
        logger.info(f"🚀 Пользователь {user.id} (@{user.username}) запустил бота")
        
        context.user_data.clear()
        context.user_data["user_id"] = user.id
        context.user_data["profile"] = USER_PROFILE.copy()
        
        init_test_data(user.id)
        context.user_data["sexual_invites"] = get_user_invites(user.id)
        
        get_user_limits(context)
        
        return await show_results_screen(update, context)
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}\n{traceback.format_exc()}")
        await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        return RESULTS_SCREEN

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 ЭКРАН РЕЗУЛЬТАТОВ"""
    try:
        profile = context.user_data.get("profile", USER_PROFILE)
        
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
"""
        
        keyboard = [
            [InlineKeyboardButton("🪞 Зеркало", callback_data="share_mirror")],
            [InlineKeyboardButton("📖 Полный", callback_data="full_description")],
            [InlineKeyboardButton("🔞 Интимный профиль", callback_data="my_sexual_profile")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            query = update.callback_query
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
        
        return RESULTS_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в show_results_screen: {e}")
        return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль"""
    try:
        query = update.callback_query
        await query.answer()
        logger.info(f"👤 Пользователь {query.from_user.id} открыл интимный профиль")
        
        user_name = query.from_user.first_name or "Пользователь"
        profile_data = load_intimate_profile()
        
        message = format_intimate_profile(profile_data, user_name)
        
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад в профиль", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return MY_SEXUAL_PROFILE
    except Exception as e:
        logger.error(f"❌ Ошибка в my_sexual_profile_callback: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return RESULTS_SCREEN

# ============================================
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_limits = get_user_limits(context)
        invites = context.user_data.get("sexual_invites", [])
        total_invites = len(invites)
        
        can_create, is_free, limit_message = can_create_invite(user_limits, total_invites)
        
        if not can_create:
            await query.answer("❌ Лимит ссылок исчерпан!", show_alert=True)
            return await buy_invite_packages_callback(update, context)
        
        profile = context.user_data.get("profile", USER_PROFILE)
        
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
🟢 <b>• АКТИВНО •</b> ожидание друга
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
            "profile_code": profile['display_name'],
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
        
        user_id = query.from_user.id
        global_invites = get_user_invites(user_id)
        global_invites.insert(0, invite_data)
        
        logger.info(f"🔗 Пользователь {user_id} создал ссылку: {invite_code} (тип: {invite_type})")
        
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
        logger.error(f"❌ Ошибка в create_invite_callback: {e}\n{traceback.format_exc()}")
        await query.answer("❌ Произошла ошибка при создании ссылки", show_alert=True)
        return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: МОИ ОТРАЖЕНИЯ - ВАШ ДИЗАЙН
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 МОИ ОТРАЖЕНИЯ - ВАШ МИНИМАЛИСТИЧНЫЙ ДИЗАЙН"""
    try:
        query = update.callback_query
        await query.answer("🔄 Загружаю отражения...")
        
        user_id = query.from_user.id
        invites = get_user_invites(user_id)
        context.user_data["sexual_invites"] = invites
        
        # Статистика
        used_invites = [inv for inv in invites if inv.get("status") == "used"]
        total_invites = len(invites)
        total_reflections = len(used_invites)
        
        # Профиль пользователя
        user_profile = context.user_data.get("profile", USER_PROFILE)
        user_profile_code = user_profile.get('display_name', 'SA-5_INT')
        
        # ВАШ ДИЗАЙН
        message = f"""
══════════════════
📊  СТАТИСТИКА
🪞  Ссылок зеркал     <b>{total_invites}</b>
👥  Отражений         <b>{total_reflections}</b>

══════════════════
🪞  МОЁ ОТРАЖЕНИЕ
📌 <b>Профиль</b>  {user_profile_code}
📁 <b>Диск</b>     <code>{USER_DISK_LINK}</code>
"""

        if used_invites:
            message += f"""

═══════════════════
👥  ОТРАЖЕНИЕ ТЕХ КТО ПОСМОТРЕЛСЯ({total_reflections})

"""
            for idx, inv in enumerate(used_invites[:5], 1):
                friend_name = inv.get("friend_name", "друг").replace('@', '')
                friend_profile = inv.get("friend_profile", "SA-3_CON")
                disk_link = get_disk_link_by_profile(friend_profile)
                
                message += f"""
{idx}.  🆔 <b>{friend_name}</b>
    └ 📊 {friend_profile}
    └ 📁 <code>{disk_link}</code>"""
                
                if inv.get("purchased_functions"):
                    key_map = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
                    keys = " ".join(key_map.get(k, k) for k in inv["purchased_functions"])
                    message += f"""
    └ {keys}"""
                
                message += f"\n"
            
            if len(used_invites) > 5:
                message += f"\n... и ещё {len(used_invites) - 5}\n"
        else:
            message += f"""

═══════════════════
👥  ОТРАЖЕНИЕ ТЕХ КТО ПОСМОТРЕЛСЯ(0)

🌑  <i>Пока нет отражений</i>

💡  Создайте ссылку в профиле
    и отправьте другу
"""

        message += f"""

───────────────────────────
💫  <i>Каждое отражение — ключ к человеку</i>
"""

        # Кнопки навигации
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
        logger.error(f"❌ Ошибка в my_invites_callback: {e}\n{traceback.format_exc()}")
        await query.answer("❌ Произошла ошибка", show_alert=True)
        return INVITES_LIST

# ============================================
# 🧬 ЭКРАН 5: ГЛАВНОЕ МЕНЮ 4F (ОБУЧАЙКА)
# ============================================

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 Главное меню 4F-ключей (краткая версия)"""
    try:
        query = update.callback_query
        await query.answer()
        logger.info(f"🧬 Пользователь {query.from_user.id} открыл меню 4F")
        
        message = FOUR_F_EXPLANATION
        
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

# ============================================
# 📘 ЭКРАН 6: ПОДРОБНОЕ ОПИСАНИЕ 4F
# ============================================

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ПОДРОБНОЕ ОПИСАНИЕ 4F"""
    try:
        query = update.callback_query
        await query.answer()
        logger.info(f"📘 Пользователь {query.from_user.id} открыл подробное описание 4F")
        
        message = FOUR_F_DETAILED_EXPLANATION
        
        keyboard = [
            [InlineKeyboardButton("◀️ К ОБУЧАЙКЕ", callback_data="four_f_main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MAIN
    except Exception as e:
        logger.error(f"❌ Ошибка в four_f_detailed_callback: {e}")
        return FOUR_F_MAIN

# ============================================
# 🔍 ЭКРАН 7: ПРОВЕРКА СТАТУСА
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
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

# ============================================
# 💳 ЭКРАН 8: ПОКУПКА ПАКЕТОВ ССЫЛОК
# ============================================

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💎 Покупка пакетов ссылок"""
    try:
        query = update.callback_query
        await query.answer()
        
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
                    f"{data['emoji']} {data['links']} ссылок - {data['price']}₽",
                    callback_data=f"pay_package_{links}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data="my_invites")
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return BUY_PACKAGES
    except Exception as e:
        logger.error(f"❌ Ошибка в buy_invite_packages_callback: {e}")
        return INVITES_LIST

# ============================================
# 💳 ЭКРАН 9: ОПЛАТА ПАКЕТА
# ============================================

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Оплата пакета ссылок"""
    try:
        query = update.callback_query
        await query.answer("💰 Формирую счёт...")
        
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
            [InlineKeyboardButton("◀️ Назад", callback_data="buy_invite_packages")]
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

# ============================================
# ✅ ЭКРАН 10: ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ПАКЕТА
# ============================================

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Подтверждение оплаты пакета"""
    try:
        query = update.callback_query
        await query.answer("🔄 Проверяю оплату...")
        
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

# ============================================
# 👤 ЭКРАН 11: МЕНЮ ПРОФИЛЯ ДРУГА
# ============================================

def get_friend_by_id(context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> Optional[dict]:
    """Утилита для поиска друга по ID"""
    invites = context.user_data.get("sexual_invites", [])
    return next(
        (inv for inv in invites if inv.get("friend_id") == friend_id),
        None
    )

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 МЕНЮ ПРОФИЛЯ ДРУГА"""
    try:
        query = update.callback_query
        await query.answer()
        
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
        
        message = f"""
{inv_type} <b>{friend_name}</b>

📊 {friend_profile}
💎 {'🔓' if access_status == 'free' else '💰'}

🔓 {progress}/4 [{progress_bar}]
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Стандарт", callback_data=f"std_{friend_id}"),
                InlineKeyboardButton("🔞 Интим", callback_data=f"int_{friend_id}")
            ],
            [
                InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}"),
                InlineKeyboardButton("❓ Что это?", callback_data="4f_explain")
            ],
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
        return INVITES_LIST

# ============================================
# 💰 ЭКРАН 12: ОПЛАТА ДОСТУПА
# ============================================

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
    """💰 Разблокировка платного друга"""
    try:
        query = update.callback_query
        
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
            [InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")]
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
# 📊 ЭКРАН 13: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
    try:
        query = update.callback_query
        await query.answer()
        
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
        
        keyboard = [[
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
        ]]
        
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
# 🔞 ЭКРАН 14: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FRIEND_MENU
        
        friend_name = friend_data.get("friend_name", "друг").replace('@', '')
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        
        profile_data = load_friend_intimate_profile(friend_name, friend_profile)
        message = format_friend_intimate_profile(profile_data, friend_name)
        
        keyboard = [[
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
        ]]
        
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
# 🧬 ЭКРАН 15: МЕНЮ 4F-КЛЮЧЕЙ ДЛЯ ДРУГА
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ 4F-КЛЮЧЕЙ"""
    try:
        query = update.callback_query
        await query.answer()
        
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
                        f"{emoji} {f} - 1₽",
                        callback_data=f"buy_4f_{friend_id}_{f}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("❓ Что такое 4F?", callback_data="4f_explain"),
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
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
# 📘 ЭКРАН 16: ОБУЧАЙКА 4F (ДЛЯ ДРУГА)
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ОБУЧАЙКА 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        message = FOUR_F_EXPLANATION
        
        keyboard = []
        friend_id = context.user_data.get("current_friend_id")
        
        if friend_id:
            keyboard.append([
                InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")
            ])
        
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
# 💳 ЭКРАН 17: ПОКУПКА 4F-КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Покупка 4F-ключа"""
    try:
        query = update.callback_query
        await query.answer("💰 Создаю счёт...")
        
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
{content['subtitle']}

👤 {friend_name}

{content['description']}

💰 <b>1₽</b>
"""
        
        payment_id = generate_payment_id("4f", query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
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
# 💳 ЭКРАН 18: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Процесс платежа"""
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
        
        message = f"""
💳 <b>СЧЁТ СФОРМИРОВАН</b>

🔑 {function}
💰 1₽
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ", url=payment_result["confirmation_url"])],
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ", callback_data=f"check_payment_{payment_id}_{friend_id}_{function}")],
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
# 🔑 ЭКРАН 19: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТЫЙ 4F-КЛЮЧ"""
    try:
        query = update.callback_query
        await query.answer("🔓 Открываю...")
        
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
        
        keyboard = []
        
        next_keys = {
            "1F": "2F", "2F": "3F", "3F": "4F", "4F": "1F"
        }
        next_f = next_keys.get(function)
        next_emoji = FOUR_F_EMOJIS[next_f]
        
        keyboard.append([
            InlineKeyboardButton(
                f"{next_emoji} КУПИТЬ {next_f} - 1₽",
                callback_data=f"buy_4f_{friend_id}_{next_f}"
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")
        ])
        
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
# ⬅️ ВОЗВРАТЫ И ЗАГЛУШКИ
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    try:
        query = update.callback_query
        await query.answer()
        return await show_results_screen(update, context)
    except Exception as e:
        logger.error(f"❌ Ошибка в back_to_results_callback: {e}")
        return RESULTS_SCREEN

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для демо-функций"""
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

# ============================================
# 🚀 ЗАПУСК
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v12.1")
    print("="*60)
    print("✅ ВАШ ДИЗАЙН экрана «Мои отражения»")
    print("✅ Ссылки на Яндекс.Диск для каждого профиля")
    print("✅ Двухуровневая система 4F: кратко и подробно")
    print("✅ Минималистичная навигация (только 2 кнопки)")
    print("✅ УЛУЧШЕНО: умный поиск файла профиля с диагностикой")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    try:
        app = Application.builder().token(TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                RESULTS_SCREEN: [
                    CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                    CallbackQueryHandler(dummy_callback, pattern='^share_mirror$'),
                    CallbackQueryHandler(dummy_callback, pattern='^full_description$'),
                    CallbackQueryHandler(show_results_screen, pattern='^show_results$'),
                ],
                
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
                    CallbackQueryHandler(dummy_callback, pattern='^pay_access_'),
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
            },
            fallbacks=[
                CommandHandler('start', start),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            name="intimate_profiles_conversation",
            persistent=False,
        )
        
        app.add_handler(conv_handler)
        
        print("\n🚀 Бот запущен! Версия 12.1")
        print("="*60)
        logger.info("✅ Бот успешно запущен")
        
        app.run_polling()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}\n{traceback.format_exc()}")
        print(f"\n❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
