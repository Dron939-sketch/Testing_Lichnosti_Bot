#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 10.3 - ИСПРАВЛЕН CONVERSATIONHANDLER
✅ КНОПКА "МОИ ОТРАЖЕНИЯ" РАБОТАЕТ
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

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1

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
    """Форматирует интимный профиль"""
    message = f"""
🔞 ИНТИМНЫЙ ПРОФИЛЬ
{user_name}

📊 Тип: {profile_data.get('profile_type', 'SA-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 ЦИТАТА:
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 ВАША ПРИРОДА:
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

🪞 ТАМ, ЗА ЗЕРКАЛОМ...

Вы увидели только что СВОЁ 🪞 отражение.
Но у каждого друга — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

⬇️ КАК УВИДЕТЬ ИХ:

1️⃣ Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО профиль и интимные подробности

💫 Чем больше друзей увидят себя в зеркале —
   тем больше тайн откроется вам.
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
🔞 ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
👤 {friend_name}

📊 Тип: {profile_data.get('profile_type', 'ТЕСТ-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 ЦИТАТА:
{profile_data.get('quote', f'«{friend_name}, со мной не скучно. Со мной — вкусно.»')}

🧠 ЕГО ПРИРОДА:
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
    """Инициализирует тестовые данные"""
    invites = get_user_invites(user_id)
    if len(invites) > 0:
        return
    
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
            "used_at": datetime.now().timestamp(),
            "purchased_functions": []
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
            "used_at": datetime.now().timestamp() - 86400,
            "purchased_functions": ["1F"]
        }
    ]
    
    invites.extend(test_friends)
    logger.info(f"✅ Инициализированы тестовые данные для user_id={user_id}")

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
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 ЭКРАН РЕЗУЛЬТАТОВ"""
    profile = context.user_data.get("profile", USER_PROFILE)
    
    message = f"""
🧠 ВАШ ПРОФИЛЬ ГОТОВ

📊 {profile['display_name']}

💬 ЦИТАТА:
«Я не ищу — я нахожу»

💔 СУТЬ ПРОБЛЕМЫ
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 ИНСТРУМЕНТ
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
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    query = update.callback_query
    await query.answer()
    
    profile = context.user_data.get("profile", USER_PROFILE)
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
    
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "У меня — совпало процентов на 90.\n\n"
        "Интересно, у тебя тоже?"
    )
    
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    text = f"""
🔞 ВАША ССЫЛКА ГОТОВА!

🔗 <code>{invite_url}</code>

💬 ТЕКСТ СООБЩЕНИЯ:
{invite_message}

{SEXUAL_DIVIDER}
🟢 АКТИВНО • ожидание
📅 {current_time}
{SEXUAL_DIVIDER}

🎯 Через 15 минут после теста
   вы увидите его 18+ профиль.
   То, что скрывается даже от близких.
"""
    
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
# 🔍 ЭКРАН 4: МОИ ОТРАЖЕНИЯ (ИСПРАВЛЕНО - РАБОТАЕТ!)
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 Мои отражения - РАБОТАЕТ ВСЕГДА!"""
    query = update.callback_query
    await query.answer()
    
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
🔍 МОИ ОТРАЖЕНИЯ

📊 СТАТИСТИКА:
   🔗 Всего ссылок: {total_invites}
   ✨ Отражений: {total_reflections}
   💎 Бесплатных: {free_used}/{FREE_FRIEND_LIMIT}
   🔓 Доступно: {paid_available}

{SEXUAL_DIVIDER}
"""
    
    keyboard = []
    
    if active_invites:
        message += f"\n🟢 ЖДУТ ОТКЛИКА ✨"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
            days = int((datetime.now().timestamp() - inv["created_at"]) / 86400)
            message += f"\n   • {created} · ждёт {days}д"
            keyboard.append([
                InlineKeyboardButton(
                    f"🔄 {inv['invite_id'][:8]}...",
                    callback_data=f"check_status_{inv['invite_id']}"
                )
            ])
    else:
        message += f"\n✨ У вас пока нет активных приглашений"
    
    if used_invites:
        message += f"\n\n✨ УЖЕ ОТРАЗИЛИСЬ — {len(used_invites)}"
        for inv in used_invites[:5]:
            friend_name = inv.get("friend_name", "друг")
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
"""
    
    keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")])
    keyboard.append([InlineKeyboardButton("⬅️ К ИНТИМНОМУ ПРОФИЛЮ", callback_data="my_sexual_profile")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 5: ПРОВЕРКА СТАТУСА
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer()
    
    invite_id = query.data.replace("check_status_", "")
    
    message = f"""
🔍 СТАТУС ПРИГЛАШЕНИЯ

🔗 <code>https://t.me/{BOT_USERNAME}?start={invite_id}</code>

🟢 · · · АКТИВНО · · · ждёт друга
⏳ Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}

✨ Друг ещё не прошёл тест.
   Напомните ему о себе.
"""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")],
        [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 👤 ЭКРАН 6: МЕНЮ ПРОФИЛЯ ДРУГА
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
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    access_status = friend_data.get("access_status", "free")
    free_count = count_free_friends(query.from_user.id)
    
    if access_status == "locked" or (free_count >= FREE_FRIEND_LIMIT and not friend_data.get("access_paid")):
        return await show_payment_access_screen(update, context, friend_data)
    
    purchased = friend_data.get("purchased_functions", [])
    progress = len(purchased)
    progress_bar = "▓" * progress + "░" * (4 - progress)
    
    message = f"""
👤 {friend_name}

📊 {friend_profile}
💎 {'🔓 Бесплатно' if access_status == 'free' else '💰 Куплен'}

🔓 РАЗГАДАНО: {progress}/4 [{progress_bar}]
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
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 {friend_name} ЗАБЛОКИРОВАН

📊 {friend_profile}

⚠️ БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽

💰 РАЗБЛОКИРОВАТЬ ДОСТУП:
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
# 📊 ЭКРАН 8: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_data = get_friend_by_id(context, friend_id)
    friend_name = friend_data.get("friend_name", "друг") if friend_data else "друг"
    
    profile = load_friend_standard_profile()
    
    message = f"""
📊 {friend_name}

🧠 Архетип: {profile['archetype']}

💬 Цитата:
{profile['quote']}

💔 Суть проблемы:
{profile['pain']}

🛠 Инструмент:
{profile['immediate_tool']}

🚀 Следующие шаги:
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
# 🔞 ЭКРАН 9: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
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
    
    friend_name = friend_data.get("friend_name", "друг")
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
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    purchased = friend_data.get("purchased_functions", [])
    
    hot_hint = "\n🔥 ХИТ ПРОДАЖ: 1F покупают в 2 раза чаще"
    
    message = f"""
🧬 4F-КЛЮЧИ ДЛЯ {friend_name}

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
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} {content['title']}
{content['subtitle']}

👤 Друг: {friend_name}
📊 Профиль: {friend_profile}

{content['description']}

💰 Цена: 1₽ (тестовый режим)
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
💳 СЧЁТ СФОРМИРОВАН

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
🎉 КЛЮЧ АКТИВИРОВАН!

{content['emoji']} {content['title']}
{content['subtitle']}

🎯 ТРИГГЕР-ФРАЗЫ:
"""
    
    for i, trigger in enumerate(content['triggers'][:3], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

🧠 ПСИХОЛОГИЧЕСКИЙ РАЗБОР:
{content['analysis']}

📋 ПРОТОКОЛ ПРИМЕНЕНИЯ:
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
            # Создаем новый callback_data для open_4f_key
            new_query = update
            new_query.data = f"open_4f_{friend_id}_{function}"
            return await open_4f_key_callback(new_query, context)
    else:
        await query.answer("✅ Демо-режим")
    
    return RESULTS_SCREEN

# ============================================
# 🚀 ЗАПУСК С ИСПРАВЛЕННЫМ CONVERSATIONHANDLER
# ============================================

def main():
    """Запуск бота с исправленным ConversationHandler"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v10.3")
    print("="*60)
    print("✅ ИСПРАВЛЕНО: КНОПКА «МОИ ОТРАЖЕНИЯ» РАБОТАЕТ!")
    print("   • Добавлен полноценный ConversationHandler")
    print("   • Все callback'и привязаны к состояниям")
    print("   • Работает при пустом списке и с данными")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # ===== СОЗДАЕМ CONVERSATION HANDLER С ВСЕМИ СОСТОЯНИЯМИ =====
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # Состояние 0: ЭКРАН РЕЗУЛЬТАТОВ
            RESULTS_SCREEN: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(dummy_callback, pattern='^share_mirror$'),
                CallbackQueryHandler(dummy_callback, pattern='^full_description$'),
                CallbackQueryHandler(show_results_screen, pattern='^show_results$'),
            ],
            
            # Состояние 1: МОЙ ИНТИМНЫЙ ПРОФИЛЬ - ЗДЕСЬ РАБОТАЕТ КНОПКА!
            MY_SEXUAL_PROFILE: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),  # ← ВОТ ЭТО РЕШЕНИЕ!
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # Состояние 2: ПРИГЛАШЕНИЯ И ОТРАЖЕНИЯ
            INVITES_LIST: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(check_status_callback, pattern='^check_status_'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # Состояние 3: МЕНЮ ДРУГА
            FRIEND_MENU: [
                CallbackQueryHandler(standard_profile_callback, pattern='^std_'),
                CallbackQueryHandler(intimate_profile_callback, pattern='^int_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
            ],
            
            # Состояние 4: МЕНЮ 4F
            FOUR_F_MENU: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(open_4f_key_callback, pattern='^open_4f_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
            ],
            
            # Состояние 5: КОНТЕНТ 4F
            FOUR_F_CONTENT: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
            ],
            
            # Состояние 6: ПЛАТЕЖИ
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(process_payment_callback, pattern='^process_payment_'),
                CallbackQueryHandler(dummy_callback, pattern='^check_payment_'),
                CallbackQueryHandler(dummy_callback, pattern='^pay_access_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
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
    
    # Добавляем отдельные хендлеры для callback'ов, которые могут приходить вне состояний
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern='^pay_access_'))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern='^share_mirror$'))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern='^full_description$'))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern='^check_payment_'))
    
    print("\n🚀 Бот запущен! Кнопка «МОИ ОТРАЖЕНИЯ» РАБОТАЕТ!")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
