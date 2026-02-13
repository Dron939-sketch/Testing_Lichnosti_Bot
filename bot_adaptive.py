#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 11.0 - НОВАЯ СИСТЕМА ПЛАТНЫХ ССЫЛОК
✅ Убрана кнопка "Создать ссылку" из "Мои отражения"
✅ Кнопка 4F выделена и перемещена вниз
✅ Добавлена система лимитов (3 бесплатных ссылки)
✅ Добавлены пакеты ссылок (3/5/10)
✅ Новый премиум-дизайн с рамками и прогресс-барами
✅ Убрано слово "бесплатная" при создании ссылки
✅ Укорочены линии для мобильных устройств
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
import requests
import base64
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

# ===== НАСТРОЙКА =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "ваш_shop_id")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "ваш_secret_key")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== УМНЫЙ ПОИСК КОРНЯ ПРОЕКТА =====
def find_project_root() -> str:
    """Находит корень проекта (где лежит папка profiles/)"""
    current = os.path.dirname(os.path.abspath(__file__))
    
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "profiles")):
            return current
        current = os.path.dirname(current)
    
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
BUY_PACKAGES = 7  # НОВОЕ состояние для покупки пакетов
FOUR_F_MAIN = 8   # НОВОЕ состояние для главного меню 4F

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

# ===== ПРАВИЛЬНЫЕ 4F-КОНСТАНТЫ =====
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
    "1F": "Как гасить агрессию и не нарваться",
    "2F": "Чего он боится на самом деле",
    "3F": "Что включает его режим «хочу»",
    "4F": "Какие идеи прорастают в его голове"
}

FOUR_F_DESCRIPTIONS = {
    "1F": """Он не злой. Он — ВЗВЕДЁННЫЙ.
Достаточно одной искры, чтобы рвануло.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 фразы, которые моментально сбивают агрессию
   • Что нельзя говорить, когда он уже завёлся
   • Как перевести конфликт в диалог за 30 секунд
   • Почему он злится именно на вас""",
    
    "2F": """Он не трус. Он — ПРЕДУСМОТРИТЕЛЬНЫЙ.
Просто однажды его уже больно ударили.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 фразы, которые включают панику (чтобы знать, чего НЕ делать)
   • 3 фразы, которые снимают тревогу (чтобы успокоить)
   • Его личные триггеры страха
   • Как говорить с ним, когда он «в тумане»""",
    
    "3F": """Ему не нужны порно-приёмы.
Ему нужен ПАРОЛЬ — слово, взгляд, касание, которое щёлкает тумблер.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 слова, которые работают как афродизиак
   • 3 касания, от которых он теряет голову
   • Его скрытые эротические сценарии
   • Что гасит желание мгновенно""",
    
    "4F": """Он не жадный. Он — ГОЛОДНЫЙ.
Голодный до денег, проектов, возможностей, статуса.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 фразы, которые зажигают его «режим предпринимателя»
   • Какие предложения он не может отклонить
   • Как продавать ему, не продавая
   • Что его тормозит в заработке"""
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

2F 🏃 БЕГСТВО / СТРАХ
└ Чего он боится на самом деле
└ Ключ к преодолению страхов

3F 🧬 СЕКС / ЖЕЛАНИЕ
└ Что включает его режим «хочу»
└ Ключ к желанию и страсти

4F 🍽 ПОГЛОЩЕНИЕ / ДЕНЬГИ
└ Какие идеи прорастают в его голове
└ Ключ к деньгам и идеям

💰 Цена: 1₽ (тестовый режим)
"""

# ===== ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ ИЗ JSON =====
def load_intimate_profile() -> dict:
    """Загружает интимный профиль из JSON файла"""
    try:
        possible_paths = [
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
            os.path.join(os.path.dirname(__file__), "profiles", "sexual_18", "sa_5_int.json"),
        ]
        
        for profile_path in possible_paths:
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✅ Загружен интимный профиль: {profile_path}")
                    return data
        
        logger.warning(f"⚠️ Файл профиля не найден")
        return get_emergency_profile()
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки интимного профиля: {e}")
        return get_emergency_profile()

def get_emergency_profile() -> dict:
    """Аварийный интимный профиль"""
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
    
    # НОВЫЙ ДИЗАЙН БЛОКА "ТАМ, ЗА ЗЕРКАЛОМ"
    message += f"""

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b> 🪞

Вы увидели только что СВОЁ отражение. ✨
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
                return data
        else:
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

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====
def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """Создает платеж в ЮKassa"""
    try:
        return {
            "success": True,
            "payment_id": payment_id,
            "confirmation_url": "https://test.payment.url",
            "amount": amount,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
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
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    invites = get_user_invites(user_id)
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

def init_test_data(user_id: int):
    """Инициализирует тестовые данные с created_at и is_free"""
    invites = get_user_invites(user_id)
    if len(invites) > 0:
        return
    
    current_time = datetime.now().timestamp()
    
    # ОБНОВЛЕННЫЕ тестовые данные с is_free
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

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ЛИМИТОВ =====
def get_user_limits(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Получает или создает данные о лимитах пользователя"""
    return context.user_data.setdefault("invite_limits", {
        "free_used": 0,                    # Использовано бесплатных
        "total_purchased": 0,               # Всего куплено ссылок
        "paid_packages": []                  # История покупок
    })

def can_create_invite(user_limits: dict, total_invites: int) -> tuple:
    """
    Проверяет, может ли пользователь создать ссылку
    Возвращает (can_create: bool, is_free: bool, message: str)
    """
    free_used = user_limits["free_used"]
    
    # Бесплатные есть?
    if free_used < FREE_INVITE_LIMIT:
        remaining = FREE_INVITE_LIMIT - free_used
        return True, True, f"Осталось бесплатных: {remaining}"
    
    # Платные есть?
    paid_available = user_limits["total_purchased"] - (total_invites - FREE_INVITE_LIMIT)
    if paid_available > 0:
        return True, False, f"Осталось платных: {paid_available}"
    
    # Нет доступа
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
    user = update.effective_user
    
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    context.user_data["profile"] = USER_PROFILE.copy()
    
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    
    # Инициализируем лимиты
    get_user_limits(context)
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 ЭКРАН РЕЗУЛЬТАТОВ"""
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
        [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ Назад в профиль", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return MY_SEXUAL_PROFILE

# ============================================
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ (ОБНОВЛЕН)
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения с проверкой лимитов (УБРАНО СЛОВО "БЕСПЛАТНАЯ")"""
    query = update.callback_query
    await query.answer()
    
    # Получаем лимиты
    user_limits = get_user_limits(context)
    invites = context.user_data.get("sexual_invites", [])
    total_invites = len(invites)
    
    # Проверяем, можно ли создать ссылку
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
    
    # Определяем тип ссылки (УБРАНО СЛОВО "бесплатная"/"платная")
    invite_type = "🆓" if is_free else "💎"
    
    # Обновляем счетчики
    if is_free:
        user_limits["free_used"] += 1
    
    text = f"""
🔞 <b>✨ ВАША ССЫЛКА ГОТОВА! ✨</b>
{invite_type}

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
    
    # Показываем остаток ссылок
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

# ============================================
# 🔍 ЭКРАН 4: МОИ ОТРАЖЕНИЯ - НОВЫЙ ДИЗАЙН (КОРОТКИЕ ЛИНИИ)
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 МОИ ОТРАЖЕНИЯ - ПРЕМИУМ ДИЗАЙН, КОРОТКИЕ ЛИНИИ, БЕЗ КНОПКИ СОЗДАНИЯ ССЫЛКИ"""
    query = update.callback_query
    await query.answer("🔄 Загружаю отражения...")
    
    user_id = query.from_user.id
    invites = get_user_invites(user_id)
    context.user_data["sexual_invites"] = invites
    
    # Получаем лимиты
    user_limits = get_user_limits(context)
    
    # Считаем статистику
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    total_invites = len(invites)
    total_reflections = len(used_invites)
    
    # Бесплатные лимиты
    free_used = user_limits["free_used"]
    free_remaining = max(0, FREE_INVITE_LIMIT - free_used)
    
    # Платные лимиты
    paid_available = user_limits["total_purchased"] - (total_invites - free_used)
    
    # Прогресс-бар для бесплатных
    free_progress = create_progress_bar(free_used, FREE_INVITE_LIMIT)
    
    now = datetime.now().timestamp()
    
    # Основное сообщение с новым дизайном (КОРОТКИЕ ЛИНИИ)
    message = f"""
🔍 ✨ МОИ ОТРАЖЕНИЯ ✨

┌─ 📊 СТАТИСТИКА ─────┐
│
│   🔗 Всего ссылок:  {total_invites}
│   ✨ Отражений:     {total_reflections}
│
│   🆓 Бесплатные:    {free_used}/{FREE_INVITE_LIMIT}  [{free_progress}]
│   💎 Платные:       {max(0, paid_available)} доступно
│
└─────────────────────┘
"""

    if active_invites:
        message += f"""
┌─ 🟢 ЖДУТ ОТКЛИКА ─┐
│
"""
        for inv in active_invites[:5]:
            created = datetime.fromtimestamp(inv.get("created_at", now)).strftime('%d.%m')
            days = int((now - inv.get("created_at", now)) / 86400)
            days_text = f"<b>{days}д</b>" if days > 0 else "<b>сегодня</b>"
            inv_type = inv.get("invite_type", "🆓")
            
            message += f"│   {inv_type} • {created} • {days_text} ⏳\n"
        
        if len(active_invites) > 5:
            message += f"│   ... и ещё {len(active_invites) - 5}\n"
        message += f"│\n└─────────────────────┘\n"

    if used_invites:
        message += f"""
┌─ ✨ ОТРАЖЕНИЯ ─────┐
│
"""
        for inv in used_invites[:5]:
            friend_name = inv.get("friend_name", "друг").replace('@', '')
            friend_profile = inv.get("friend_profile", "SA-3_CON")
            used_date = datetime.fromtimestamp(inv.get("used_at", inv.get("created_at", datetime.now().timestamp()))).strftime('%d.%m.%Y')
            inv_type = inv.get("invite_type", "🆓")
            
            message += f"│   {inv_type} <b>{friend_name}</b>\n"
            message += f"│      📊 {friend_profile}  •  {used_date}"
            
            if inv.get("purchased_functions"):
                key_map = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
                keys = "  •  <b>" + " ".join(key_map.get(k, k) for k in inv["purchased_functions"]) + "</b>"
                message += keys
            
            message += f"\n│\n"
        
        if len(used_invites) > 5:
            message += f"│   ... и ещё {len(used_invites) - 5}\n│\n"
        message += f"└─────────────────────┘\n\n"
    else:
        message += f"""
┌─ ✨ ОТРАЖЕНИЯ ─────┐
│
│   <i>Пока нет отражений</i> 🌑
│
│   💡 <b>Создайте ссылку</b> в профиле и отправьте другу —
│      когда он пройдёт тест,
│      его профиль появится здесь
│
└─────────────────────┘

"""

    # Подсказка
    message += f"""
💫 <b>Каждое отражение — ключ к человеку.</b>
   Узнайте его 4F-реакции и интимные сценарии.
"""

    # КНОПКИ - ТОЛЬКО 2 КНОПКИ
    keyboard = []
    
    # Кнопка возврата
    keyboard.append([
        InlineKeyboardButton("◀️ К ИНТИМНОМУ ПРОФИЛЮ", callback_data="my_sexual_profile")
    ])
    
    # Кнопка 4F - ВЫДЕЛЕННАЯ, СНИЗУ
    keyboard.append([
        InlineKeyboardButton("🔴🧬 4F КЛЮЧИ 🔴", callback_data="four_f_main_menu")
    ])

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 🧬 НОВЫЙ ЭКРАН: ГЛАВНОЕ МЕНЮ 4F
# ============================================

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 Главное меню 4F-ключей"""
    query = update.callback_query
    await query.answer()
    
    message = f"""
🧬 <b>4F-КЛЮЧИ</b>

<b>Что это?</b>
4F — система доступа к глубинным состояниям человека.
Четыре базовые реакции, зашитые в подкорке.

<b>Доступные ключи:</b>

1F 🔥 <b>НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Как гасить агрессию и не нарваться

2F 🏃 <b>БЕГСТВО / СТРАХ</b>
└ Чего он боится на самом деле

3F 🧬 <b>СЕКС / ЖЕЛАНИЕ</b>
└ Что включает его режим «хочу»

4F 🍽 <b>ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Какие идеи прорастают в его голове

{SEXUAL_DIVIDER}
💡 Чтобы открыть 4F-ключи друга:
   1. Выберите друга в списке отражений
   2. Нажмите "🧬 4F" в его меню
   3. Купите нужный ключ
"""
    
    keyboard = [
        [InlineKeyboardButton("🔍 К ОТРАЖЕНИЯМ", callback_data="my_invites")],
        [InlineKeyboardButton("📘 ПОДРОБНЕЕ", callback_data="4f_explain")],
        [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MAIN

# ============================================
# 🔍 ЭКРАН 5: ПРОВЕРКА СТАТУСА (ОБНОВЛЕН)
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer()
    
    invite_id = query.data.replace("check_status_", "")
    
    # Находим приглашение
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

🟢 <b>• • • АКТИВНО • • •</b> ждёт друга
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

# ============================================
# 💳 НОВЫЙ ЭКРАН: ПОКУПКА ПАКЕТОВ ССЫЛОК
# ============================================

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💎 Покупка пакетов ссылок"""
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
    
    # Кнопки пакетов
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

# ============================================
# 💳 НОВЫЙ ЭКРАН: ОПЛАТА ПАКЕТА
# ============================================

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Оплата пакета ссылок"""
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

# ============================================
# ✅ НОВЫЙ ЭКРАН: ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ПАКЕТА
# ============================================

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Подтверждение оплаты пакета"""
    query = update.callback_query
    await query.answer("🔄 Проверяю оплату...")
    
    parts = query.data.split("_")
    payment_id = parts[3]
    package_id = parts[4]
    
    package = INVITE_PACKAGES.get(package_id)
    
    # Здесь должна быть реальная проверка платежа
    # Сейчас имитируем успешную оплату
    
    # Обновляем лимиты пользователя
    user_limits = get_user_limits(context)
    user_limits["total_purchased"] += package["links"]
    user_limits["paid_packages"].append({
        "package": package_id,
        "links": package["links"],
        "price": package["price"],
        "payment_id": payment_id,
        "purchased_at": datetime.now().timestamp()
    })
    
    # Считаем оставшиеся лимиты для отображения
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

# ============================================
# 👤 ЭКРАН 6: МЕНЮ ПРОФИЛЯ ДРУГА (ОБНОВЛЕН)
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
💎 {'🔓 Бесплатно' if access_status == 'free' else '💰 Куплен'}

🔓 <b>РАЗГАДАНО:</b> {progress}/4 [{progress_bar}]
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Standart", callback_data=f"std_{friend_id}"),
            InlineKeyboardButton("🔞 SEX", callback_data=f"int_{friend_id}")
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

# ============================================
# 💰 ЭКРАН 7: ОПЛАТА ДОСТУПА
# ============================================

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
    """💰 Разблокировка платного друга"""
    query = update.callback_query
    
    friend_name = friend_data.get("friend_name", "друг").replace('@', '')
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 <b>{friend_name} ЗАБЛОКИРОВАН</b>

📊 {friend_profile}

⚠️ <b>БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН</b>
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽

💰 <b>РАЗБЛОКИРОВАТЬ ДОСТУП:</b>
   • Цена: {FRIEND_ACCESS_PRICE}₽ (разово)
   • Стандартный профиль
   • Интимный профиль
   • Покупка 4F-ключей
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

# ============================================
# 📊 ЭКРАН 8: СТАНДАРТНЫЙ ПРОФИЛЬ (ОБНОВЛЕН)
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_data = get_friend_by_id(context, friend_id)
    friend_name = friend_data.get("friend_name", "друг").replace('@', '') if friend_data else "друг"
    
    profile = load_friend_standard_profile()
    
    message = f"""
📊 <b>{friend_name}</b>

🧠 <b>Архетип:</b> {profile['archetype']}

💬 <b>Цитата:</b>
{profile['quote']}

💔 <b>Суть проблемы:</b>
{profile['pain']}

🛠 <b>Инструмент:</b>
{profile['immediate_tool']}

🚀 <b>Следующие шаги:</b>
{profile['cta']}
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

# ============================================
# 🔞 ЭКРАН 9: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА (ОБНОВЛЕН)
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга"""
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

# ============================================
# 🧬 ЭКРАН 10: МЕНЮ 4F-КЛЮЧЕЙ
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ 4F-КЛЮЧЕЙ"""
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
    
    hot_hint = "\n🔥 ХИТ ПРОДАЖ: 1F покупают в 2 раза чаще"
    
    message = f"""
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>

📊 {friend_profile}
{hot_hint if not purchased else ""}

1F 🔥 {FOUR_F_TITLES['1F']}
└ {FOUR_F_SUBTITLES['1F']}

2F 🏃 {FOUR_F_TITLES['2F']}
└ {FOUR_F_SUBTITLES['2F']}

3F 🧬 {FOUR_F_TITLES['3F']}
└ {FOUR_F_SUBTITLES['3F']}

4F 🍽 {FOUR_F_TITLES['4F']}
└ {FOUR_F_SUBTITLES['4F']}
"""
    
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

# ============================================
# 📘 ЭКРАН 11: ОБУЧАЙКА 4F
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ОБУЧАЙКА 4F"""
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

# ============================================
# 💳 ЭКРАН 12: ПОКУПКА 4F-КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Покупка 4F-ключа"""
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
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>
{content['subtitle']}

👤 Друг: {friend_name}
📊 Профиль: {friend_profile}

{content['description']}

💰 <b>Цена: 1₽ (тестовый режим)</b>
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

# ============================================
# 💳 ЭКРАН 13: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Процесс платежа"""
    query = update.callback_query
    await query.answer("💳 Подключаюсь к платежной системе...")
    
    parts = query.data.split("_")
    payment_id = parts[2]
    friend_id = int(parts[3])
    function = parts[4]
    
    payment_result = create_yookassa_invoice(
        payment_id=payment_id,
        user_id=query.from_user.id,
        amount=1.0,
        description=f"4F ключ {function} для друга {friend_id}"
    )
    
    if not payment_result.get("success"):
        await query.answer(f"❌ Ошибка платежа", show_alert=True)
        return FOUR_F_PAYMENT_SCREEN
    
    message = f"""
💳 <b>СЧЁТ СФОРМИРОВАН</b>

🔑 Ключ: {function}
👤 Друг: ID {friend_id}
💰 Сумма: 1₽ (тест)

✅ Нажмите кнопку для оплаты
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 ПРОВЕРИТЬ", callback_data=f"check_payment_{payment_id}_{friend_id}_{function}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"4f_{friend_id}")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_PAYMENT_SCREEN

# ============================================
# 🔑 ЭКРАН 14: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТЫЙ 4F-КЛЮЧ"""
    query = update.callback_query
    await query.answer("🔓 Открываю ключ...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    content = load_4f_content(function)
    
    message = f"""
🎉 <b>КЛЮЧ АКТИВИРОВАН!</b>

{content['emoji']} <b>{content['title']}</b>
{content['subtitle']}

<b>🎯 ТРИГГЕР-ФРАЗЫ:</b>
"""
    
    for i, trigger in enumerate(content['triggers'][:3], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

<b>🧠 ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{content['analysis']}

<b>📋 ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{content['protocol']}

{content['tag']}
"""
    
    keyboard = []
    
    next_keys = {
        "1F": "2F",
        "2F": "3F",
        "3F": "4F",
        "4F": "1F"
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
        InlineKeyboardButton("⬅️ К СПИСКУ КЛЮЧЕЙ", callback_data=f"4f_{friend_id}")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_CONTENT

# ============================================
# ⬅️ ВОЗВРАТЫ И ЗАГЛУШКИ
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для демо-функций"""
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

# ============================================
# 🚀 ЗАПУСК С ОБНОВЛЕННЫМ CONVERSATIONHANDLER
# ============================================

def main():
    """Запуск бота - НОВАЯ ВЕРСИЯ 11.0"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v11.0")
    print("="*60)
    print("✅ НОВАЯ СИСТЕМА ПЛАТНЫХ ССЫЛОК!")
    print("   • Убрана кнопка «Создать ссылку» из «Мои отражения»")
    print("   • Кнопка 4F выделена и перемещена вниз")
    print("   • Добавлены лимиты: 3 бесплатных ссылки")
    print("   • Пакеты ссылок: 3/299₽, 5/499₽, 10/899₽")
    print("   • Новый премиум-дизайн с рамками")
    print("   • Убрано слово «бесплатная» при создании ссылки")
    print("   • Укорочены линии для мобильных устройств")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # ===== ОБНОВЛЕННЫЙ CONVERSATION HANDLER =====
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
    
    print("\n🚀 Бот запущен! Новая версия 11.0")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
