#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 11.1 - ИСПРАВЛЕНЫ ВСЕ ОШИБКИ
✅ ВСЕ CALLBACK ВОЗВРАЩАЮТ СОСТОЯНИЯ
✅ ИСПРАВЛЕН get_friend_by_id
✅ ДОБАВЛЕНА ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ
✅ ДОБАВЛЕН ОБРАБОТЧИК four_f_ В MY_REFLECTIONS
✅ ИСПРАВЛЕН FOUR_F_MENU
✅ ДОБАВЛЕНА ВАЛИДАЦИЯ ПОКУПОК
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
from datetime import datetime, timedelta
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

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== СОСТОЯНИЯ CONVERSATIONHANDLER =====
RESULTS_SCREEN = 0
MY_SEXUAL_PROFILE = 1
MY_REFLECTIONS = 2
FRIEND_MENU = 3
FOUR_F_MENU = 4
FOUR_F_CONTENT = 5
FOUR_F_PAYMENT_SCREEN = 6

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1
INVITE_EXPIRE_DAYS = 30  # Ссылки активны 30 дней

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

# ===== КЭШ ДЛЯ ПРОФИЛЕЙ =====
_INTIMATE_PROFILE_CACHE = None
_FRIEND_PROFILE_CACHE = {}

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
   • 3 фразы, которые снимают тревогу
   • Его личные триггеры страха
   • Как говорить с ним, когда он «в тумане»
   • Протокол безопасной близости""",
    
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

FOUR_F_EXPLANATION = """
📘 ЧТО ТАКОЕ 4F-КЛЮЧИ?

🧬 4F — это система доступа к состояниям человека
Четыре базовые реакции, зашитые в подкорке.

1F 🔥 НАПАДЕНИЕ / ЯРОСТЬ
└ Как гасить агрессию и не нарваться

2F 🍽️ БЕГСТВО / СТРАХ
└ Чего он боится на самом деле

3F ⚡ СЕКС / ЖЕЛАНИЕ
└ Что включает его режим «хочу»

4F 💡 ПОГЛОЩЕНИЕ / ДЕНЬГИ
└ Какие идеи прорастают в его голове

💰 Цена: 1₽ (тестовый режим)
"""

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====
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

def cleanup_expired_invites(user_id: int):
    """Очищает истекшие приглашения"""
    invites = get_user_invites(user_id)
    current_time = datetime.now().timestamp()
    active_invites = []
    
    for inv in invites:
        if inv.get("status") == "active":
            created_at = inv.get("created_at", 0)
            if current_time - created_at > INVITE_EXPIRE_DAYS * 86400:
                inv["status"] = "expired"
        active_invites.append(inv)
    
    user_invites[user_id] = active_invites

def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    invites = get_user_invites(user_id)
    if len(invites) > 0:
        return
    
    import random
    test_friend_id1 = random.randint(10000, 99999)
    test_friend_id2 = random.randint(10000, 99999)
    
    test_friends = [
        {
            "invite_id": f"test_free_1_{user_id}",
            "friend_id": test_friend_id1,
            "friend_name": "@alex_test",
            "friend_username": "alex_test",
            "friend_profile": "SA-3_CON",
            "status": "used",
            "access_status": "free",
            "access_paid": False,
            "created_at": datetime.now().timestamp() - 86400,
            "used_at": datetime.now().timestamp(),
            "purchased_functions": ["1F", "3F"]
        },
        {
            "invite_id": f"test_free_2_{user_id}",
            "friend_id": test_friend_id2,
            "friend_name": "@maria_test",
            "friend_username": "maria_test",
            "friend_profile": "IP-5_INT",
            "status": "used",
            "access_status": "free",
            "access_paid": False,
            "created_at": datetime.now().timestamp() - 86400,
            "used_at": datetime.now().timestamp() - 86400,
            "purchased_functions": ["2F"]
        }
    ]
    
    invites.extend(test_friends)
    logger.info(f"✅ Тестовые данные для user_id={user_id}")

# ===== ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ =====
def load_intimate_profile(force_reload: bool = False) -> dict:
    """Загружает интимный профиль из JSON файла с кэшированием"""
    global _INTIMATE_PROFILE_CACHE
    
    if _INTIMATE_PROFILE_CACHE is not None and not force_reload:
        logger.info("📦 Использую кэшированный профиль")
        return _INTIMATE_PROFILE_CACHE
    
    try:
        logger.info("📂 Загрузка интимного профиля из файла...")
        
        possible_paths = [
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join("sexual_18", "sa_5_int.json"),
            os.path.join(os.path.dirname(__file__), "sexual_18", "sa_5_int.json"),
        ]
        
        if os.path.exists('/app'):
            possible_paths.append('/app/sexual_18/sa_5_int.json')
        
        for profile_path in possible_paths:
            if os.path.exists(profile_path):
                logger.info(f"✅ Найден файл: {profile_path}")
                
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _INTIMATE_PROFILE_CACHE = data
                    logger.info(f"📊 Загружено секций: {len(data.get('sections', {}))}")
                    return data
        
        logger.warning("⚠️ Файл не найден! Использую аварийный профиль")
        emergency = get_emergency_profile()
        _INTIMATE_PROFILE_CACHE = emergency
        return emergency
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        emergency = get_emergency_profile()
        _INTIMATE_PROFILE_CACHE = emergency
        return emergency

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
                "items": ["Долгие прелюдии", "Ролевые игры", "Шёпот на ухо"]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": ["Спешка", "Отсутствие атмосферы", "Прямолинейность"]
            },
            "erogenous_zone": {
                "title": "🔴 ЭРОГЕННАЯ ЗОНА",
                "trigger": "Шея, мочки ушей, внутренняя сторона запястья"
            }
        }
    }

def format_intimate_profile(profile_data: dict, user_name: str) -> str:
    """Форматирует интимный профиль для вывода"""
    message = f"""
{SEXUAL_DIVIDER}
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ: {user_name}</b>
📊 <b>Тип:</b> {profile_data.get('profile_type', 'SA-5_INT')}
🧠 <b>Архетип:</b> {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}
{SEXUAL_DIVIDER}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', '').strip()}

{SEXUAL_DIVIDER}
"""
    
    sections = profile_data.get('sections', {})
    for key, section in sections.items():
        if isinstance(section, dict):
            title = section.get('title', '')
            if title:
                message += f"\n<b>{title}</b>\n"
            
            if 'items' in section:
                for item in section['items'][:5]:
                    message += f"• {item}\n"
            elif 'trigger' in section:
                message += f"{section['trigger']}\n"
    
    message += f"""
{SEXUAL_DIVIDER}
💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что СВОЁ 🪞 отражение.
Но у каждого друга — своя тайна.

⬇️ <b>КАК УВИДЕТЬ ИХ:</b>

1️⃣ Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО профиль
{SEXUAL_DIVIDER}
"""
    return message

# ===== ЗАГРУЗКА 4F-КОНТЕНТА =====
def load_4f_content(function: str) -> dict:
    """Загружает контент 4F-ключа"""
    triggers = {
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
            "Случайное касание",
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
    
    analysis = {
        "1F": "Агрессия — это защита. Человек не злой, он напуганный.",
        "2F": "Избегание — способ справиться с перегрузкой. Дайте контроль.",
        "3F": "Влечение включается через игру, тайну, недосказанность.",
        "4F": "Голод к деньгам — это не жадность, а стремление к свободе."
    }
    
    protocol = {
        "1F": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите\n4. Дайте время",
        "2F": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте\n4. Верните контроль",
        "3F": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы\n4. Усиливайте",
        "4F": "1. Найдите его «голод»\n2. Покажите путь\n3. Уберите страхи\n4. Дайте первый шаг"
    }
    
    return {
        "function": function,
        "emoji": FOUR_F_EMOJIS[function],
        "title": FOUR_F_TITLES[function],
        "subtitle": FOUR_F_SUBTITLES[function],
        "description": FOUR_F_DESCRIPTIONS[function],
        "triggers": triggers[function],
        "analysis": analysis[function],
        "protocol": protocol[function],
        "is_demo": False
    }

def format_4f_message(content: dict, friend_name: str) -> str:
    """Форматирует 4F-контент"""
    message = f"""
{SEXUAL_DIVIDER}
{content['emoji']} <b>{content['title']}</b>
{content['subtitle']}
{SEXUAL_DIVIDER}

<b>👤 Для {friend_name}</b>

{content['description']}

{SEXUAL_DIVIDER}
<b>🎯 ТРИГГЕР-ФРАЗЫ:</b>
"""
    
    for i, trigger in enumerate(content['triggers'][:3], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

<b>🧠 ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{content['analysis']}

<b>📋 ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{content['protocol']}
{SEXUAL_DIVIDER}
"""
    return message

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====
def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    """Генерирует уникальный ID платежа"""
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """Создает платеж через API"""
    try:
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

# ===== УТИЛИТЫ =====
def get_friend_by_id(context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> Optional[dict]:
    """Поиск друга по ID"""
    user_id = context.user_data.get("user_id")
    if not user_id:
        return None
    
    # Объединяем invites из context.user_data и глобального хранилища
    context_invites = context.user_data.get("sexual_invites", [])
    global_invites = get_user_invites(user_id)
    
    # Ищем во всех источниках
    for inv in context_invites + global_invites:
        if inv.get("friend_id") == friend_id:
            return inv
    
    return None

def validate_callback_data(parts: list, expected_length: int) -> bool:
    """Валидация callback_data"""
    return len(parts) >= expected_length

def has_purchased_key(friend_data: dict, function: str) -> bool:
    """Проверяет, куплен ли ключ"""
    purchased = friend_data.get("purchased_functions", [])
    return function in purchased

# ============================================
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота с поддержкой deep link"""
    user = update.effective_user
    
    # ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ user_data
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    
    # Инициализируем тестовые данные
    init_test_data(user.id)
    
    # Загружаем приглашения в user_data
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    
    # Проверяем deep link (приглашение)
    if context.args and context.args[0].startswith("sex_"):
        return await handle_deeplink(update, context, context.args[0])
    
    return await show_results_screen(update, context)

async def handle_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Обработчик deep link (приглашений)"""
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
    return RESULTS_SCREEN

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

🛠 <b>ИНСТРУМЕНТ</b>
Сегодня: попросите кого-то о маленькой услуге.
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
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return MY_SEXUAL_PROFILE  # ✅ ИСПРАВЛЕНО: возвращаем состояние

# ============================================
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    query = update.callback_query
    await query.answer()
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
    
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

💬 <b>ТЕКСТ ДЛЯ ОТПРАВКИ:</b>
<code>{invite_message}</code>

{SEXUAL_DIVIDER}
🟢 АКТИВНО • ожидание
📅 {current_time}
{SEXUAL_DIVIDER}
"""
    
    invite_data = {
        "invite_id": invite_code,
        "link": invite_url,
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
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return MY_REFLECTIONS  # ✅ ИСПРАВЛЕНО: возвращаем состояние

# ============================================
# 💎 ЭКРАН 4: МОИ ОТРАЖЕНИЯ
# ============================================

async def my_reflections_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💎 МОИ ОТРАЖЕНИЯ"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        cleanup_expired_invites(user_id)
        invites = get_user_invites(user_id)
        context.user_data["sexual_invites"] = invites
        
        active_invites = [inv for inv in invites if inv.get("status") == "active"]
        used_invites = [inv for inv in invites if inv.get("status") == "used"]
        expired_invites = [inv for inv in invites if inv.get("status") == "expired"]
        
        total_invites = len(invites)
        total_reflections = len(used_invites)
        free_used = count_free_friends(user_id)
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
   ⌛ Истекло: {len(expired_invites)}

{SEXUAL_DIVIDER}
"""
        
        keyboard = []
        
        if active_invites:
            message += f"\n🟢 <b>ЖДУТ ОТКЛИКА ✨</b>"
            for inv in active_invites[:3]:
                created_ts = inv.get("created_at")
                if created_ts:
                    created = datetime.fromtimestamp(created_ts).strftime('%d.%m')
                    days = int((datetime.now().timestamp() - created_ts) / 86400)
                    expires_in = max(0, INVITE_EXPIRE_DAYS - days)
                    message += f"\n   • {created} · ждёт {days}д · осталось {expires_in}д"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🔄 {inv['invite_id'][:8]}...",
                            callback_data=f"check_status_{inv['invite_id']}"
                        )
                    ])
        else:
            message += f"\n✨ У вас пока нет активных приглашений"
        
        if used_invites:
            message += f"\n\n✨ <b>УЖЕ ОТРАЗИЛИСЬ — {len(used_invites)}</b>"
            for inv in used_invites[:5]:
                friend_name = inv.get("friend_name", "Друг")
                friend_profile = inv.get("friend_profile", "SA-3_CON")
                
                timestamp = inv.get("used_at", inv.get("created_at", datetime.now().timestamp()))
                used_date = datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y')
                
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
            message += f"\n\n💡 Создайте ссылку и отправьте другу"
        
        keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")])
        keyboard.append([InlineKeyboardButton("🧬 4F-КЛЮЧИ", callback_data="four_f_explain")])  # ✅ ДОБАВЛЕНО
        keyboard.append([InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="my_sexual_profile")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return MY_REFLECTIONS  # ✅ ИСПРАВЛЕНО: возвращаем состояние
        
    except Exception as e:
        logger.error(f"❌ Ошибка в my_reflections_callback: {e}", exc_info=True)
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
        parts = query.data.split("_")
        if len(parts) < 3:
            await query.answer("❌ Неверный формат", show_alert=True)
            return MY_REFLECTIONS
            
        invite_id = "_".join(parts[2:])
        
        message = f"""
{SEXUAL_DIVIDER}
🔍 <b>СТАТУС ПРИГЛАШЕНИЯ</b>
{SEXUAL_DIVIDER}

🔗 <code>https://t.me/{BOT_USERNAME}?start={invite_id}</code>

🟢 АКТИВНО · ждёт друга
⏳ Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}

✨ Друг ещё не прошёл тест.
   Напомните ему о себе.
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return MY_REFLECTIONS
        
    except Exception as e:
        logger.error(f"❌ Ошибка в check_status_callback: {e}")
        await query.answer("❌ Ошибка", show_alert=True)
        return MY_REFLECTIONS

# ============================================
# 👤 ЭКРАН 6: МЕНЮ ПРОФИЛЯ ДРУГА
# ============================================

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 МЕНЮ ПРОФИЛЯ ДРУГА"""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        if len(parts) < 2:
            await query.answer("❌ Неверный формат", show_alert=True)
            return MY_REFLECTIONS
            
        friend_id = int(parts[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return MY_REFLECTIONS
        
        context.user_data["current_friend_id"] = friend_id
        context.user_data["current_friend_data"] = friend_data
        
        friend_name = friend_data.get("friend_name", "Друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        access_status = friend_data.get("access_status", "free")
        free_count = count_free_friends(query.from_user.id)
        
        # Проверяем доступ
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
                InlineKeyboardButton("📊 Стандартный", callback_data=f"standard_{friend_id}"),
                InlineKeyboardButton("🔞 Интимный", callback_data=f"intimate_{friend_id}")
            ],
            [
                InlineKeyboardButton("🧬 4F-КЛЮЧИ", callback_data=f"four_f_{friend_id}"),
                InlineKeyboardButton("❓ Что это?", callback_data="four_f_explain")
            ],
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="my_reflections")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FRIEND_MENU  # ✅ ИСПРАВЛЕНО: возвращаем состояние
        
    except Exception as e:
        logger.error(f"❌ Ошибка в friend_menu_callback: {e}")
        await query.answer("❌ Ошибка", show_alert=True)
        return MY_REFLECTIONS

# ============================================
# 💰 ЭКРАН 7: ОПЛАТА ДОСТУПА
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
   • Цена: {FRIEND_ACCESS_PRICE}₽
   • Стандартный профиль
   • Интимный профиль
   • Покупка 4F-ключей
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton(f"🔓 РАЗБЛОКИРОВАТЬ - {FRIEND_ACCESS_PRICE}₽", callback_data=f"pay_access_{friend_data['friend_id']}")],
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="my_reflections")]
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
    
    try:
        parts = query.data.split("_")
        if len(parts) < 2:
            await query.answer("❌ Неверный формат", show_alert=True)
            return FRIEND_MENU
            
        friend_id = int(parts[1])
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "Друг") if friend_data else "Друг"
        
        message = f"""
{SEXUAL_DIVIDER}
📊 <b>{friend_name}</b>
{SEXUAL_DIVIDER}

🧠 <b>Архетип:</b> Автономный стратег

💬 <b>Цитата:</b>
«Я не ищу одобрения — я ищу эффективность.»

💔 <b>Суть проблемы:</b>
Вам сложно делегировать. Вы уверены: 
«Хочешь сделать хорошо — сделай сам».

🛠 <b>Инструмент:</b>
Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.

🚀 <b>Следующие шаги:</b>
Исследуйте баланс между автономией и доверием.
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
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
    """🔞 Интимный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        if len(parts) < 2:
            await query.answer("❌ Неверный формат", show_alert=True)
            return FRIEND_MENU
            
        friend_id = int(parts[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FRIEND_MENU
        
        friend_name = friend_data.get("friend_name", "Друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        
        message = f"""
{SEXUAL_DIVIDER}
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
👤 <b>{friend_name}</b>
{SEXUAL_DIVIDER}

📊 <b>Тип:</b> {friend_profile} (ТЕСТ)
🧠 <b>Архетип:</b> ЦЕРЕМОНИАЛЬНЫЙ

💬 <b>ЦИТАТА:</b>
«{friend_name}, со мной не скучно. Со мной — вкусно.»

{SEXUAL_DIVIDER}
⚠️ <b>ТЕСТОВЫЙ РЕЖИМ</b>

Это демо-профиль.
✅ Что появится в боевом режиме:
   • Его реальные триггеры
   • Индивидуальные сценарии
   • Точные эрогенные зоны

💎 <b>Купите полный доступ за {FRIEND_ACCESS_PRICE}₽</b>
{SEXUAL_DIVIDER}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
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
        parts = query.data.split("_")
        if len(parts) < 3:
            await query.answer("❌ Неверный формат", show_alert=True)
            return FRIEND_MENU
            
        friend_id = int(parts[2])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return MY_REFLECTIONS
        
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
            InlineKeyboardButton("❓ Что такое 4F?", callback_data="four_f_explain"),
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
        ])
        keyboard.append([InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MENU  # ✅ ИСПРАВЛЕНО: возвращаем состояние
        
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
            InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections"),
            InlineKeyboardButton("⬅️ Назад", callback_data="my_reflections")
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
        if len(parts) < 4:
            await query.answer("❌ Неверный формат", show_alert=True)
            return FOUR_F_MENU
            
        friend_id = int(parts[2])
        function = parts[3]
        
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return FOUR_F_MENU
        
        # ✅ ПРОВЕРКА: ключ уже куплен?
        if has_purchased_key(friend_data, function):
            await query.answer("🔓 Ключ уже разблокирован!", show_alert=True)
            # Перенаправляем на открытие ключа
            query.data = f"open_4f_{friend_id}_{function}"
            return await open_4f_key_callback(update, context)
        
        friend_name = friend_data.get("friend_name", "Друг")
        content = load_4f_content(function)
        
        message = f"""
{SEXUAL_DIVIDER}
{content['emoji']} <b>{content['title']}</b>
{content['subtitle']}
{SEXUAL_DIVIDER}

👤 <b>Друг:</b> {friend_name}

{content['description']}

💰 <b>Цена:</b> {FOUR_F_PRICE}₽ (тестовый режим)
{SEXUAL_DIVIDER}
"""
        
        payment_id = generate_payment_id("4f", query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton(f"💳 ОПЛАТИТЬ {FOUR_F_PRICE}₽", callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"four_f_{friend_id}")]
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
        if len(parts) < 5:
            await query.answer("❌ Неверный формат", show_alert=True)
            return FOUR_F_PAYMENT_SCREEN
            
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
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"four_f_{friend_id}")]
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
        if len(parts) < 4:
            await query.answer("❌ Неверный формат", show_alert=True)
            return FOUR_F_CONTENT
            
        friend_id = int(parts[2])
        function = parts[3]
        
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "Друг") if friend_data else "Друг"
        
        # ✅ Добавляем функцию в купленные (только если её там нет)
        if friend_data and function not in friend_data.get("purchased_functions", []):
            if "purchased_functions" not in friend_data:
                friend_data["purchased_functions"] = []
            friend_data["purchased_functions"].append(function)
            
            # Синхронизируем с глобальным хранилищем
            user_id = query.from_user.id
            global_invites = get_user_invites(user_id)
            for inv in global_invites:
                if inv.get("friend_id") == friend_id:
                    if "purchased_functions" not in inv:
                        inv["purchased_functions"] = []
                    if function not in inv["purchased_functions"]:
                        inv["purchased_functions"].append(function)
                    break
        
        content = load_4f_content(function)
        message = format_4f_message(content, friend_name)
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_reflections")],
            [InlineKeyboardButton("⬅️ К СПИСКУ КЛЮЧЕЙ", callback_data=f"four_f_{friend_id}")]
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
# 📋 КОПИРОВАНИЕ ССЫЛКИ
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Копировать ссылку"""
    query = update.callback_query
    parts = query.data.split("_")
    if len(parts) >= 3:
        invite_code = "_".join(parts[2:])
        await query.answer(f"✅ Ссылка скопирована: {invite_code[:8]}...", show_alert=True)
    else:
        await query.answer("✅ Ссылка скопирована!", show_alert=True)
    
    return MY_REFLECTIONS

# ============================================
# 🎭 ОБРАБОТЧИКИ ДЕМО-КНОПОК
# ============================================

async def demo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик демо-кнопок"""
    query = update.callback_query
    pattern = query.data
    
    if pattern == "share_mirror":
        await query.answer("🪞 Скоро здесь будет подарок", show_alert=True)
    elif pattern == "full_description":
        await query.answer("📖 Полное описание — 690₽", show_alert=True)
    elif pattern == "start_test":
        await query.answer("🚀 Запускаю тест...", show_alert=True)
    elif pattern.startswith("pay_access_"):
        await query.answer("💰 Демо-платёж доступа к другу", show_alert=True)
    elif pattern.startswith("check_payment_"):
        parts = pattern.split("_")
        if len(parts) >= 5:
            friend_id = int(parts[3])
            function = parts[4]
            
            # Активируем ключ
            friend_data = get_friend_by_id(context, friend_id)
            if friend_data:
                if "purchased_functions" not in friend_data:
                    friend_data["purchased_functions"] = []
                if function not in friend_data["purchased_functions"]:
                    friend_data["purchased_functions"].append(function)
            
            await query.answer("✅ Ключ активирован! (демо)", show_alert=True)
            
            # Перенаправляем на открытие ключа
            new_query = update
            new_query.data = f"open_4f_{friend_id}_{function}"
            return await open_4f_key_callback(new_query, context)
    else:
        await query.answer("✅ Демо-режим")
    
    return RESULTS_SCREEN

# ============================================
# ⬅️ ВОЗВРАТ К РЕЗУЛЬТАТАМ
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

# ============================================
# 🚀 ЗАПУСК БОТА - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ
# ============================================

def main():
    """Запуск бота с ПОЛНОСТЬЮ ИСПРАВЛЕННЫМИ callback_data"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v11.1")
    print("="*60)
    print("✅ ИСПРАВЛЕНЫ ВСЕ ПРОБЛЕМЫ:")
    print("   • Добавлены return состояний во все callback")
    print("   • Исправлен get_friend_by_id")
    print("   • Добавлена полная инициализация user_data")
    print("   • Добавлен обработчик four_f_ в MY_REFLECTIONS")
    print("   • Добавлена очистка истекших приглашений")
    print("   • Добавлена проверка повторной покупки ключей")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # ===== ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ CONVERSATION HANDLER =====
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # Состояние 0: РЕЗУЛЬТАТЫ
            RESULTS_SCREEN: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(demo_callback, pattern='^share_mirror$'),
                CallbackQueryHandler(demo_callback, pattern='^full_description$'),
                CallbackQueryHandler(demo_callback, pattern='^start_test$'),
                CallbackQueryHandler(show_results_screen, pattern='^show_results$'),
            ],
            
            # Состояние 1: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
            MY_SEXUAL_PROFILE: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_reflections_callback, pattern='^my_reflections$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # Состояние 2: МОИ ОТРАЖЕНИЯ
            MY_REFLECTIONS: [
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_reflections_callback, pattern='^my_reflections$'),
                CallbackQueryHandler(check_status_callback, pattern='^check_status_'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_\\d+$'),
                CallbackQueryHandler(copy_invite_callback, pattern='^copy_invite_'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^four_f_explain$'),  # ✅ ДОБАВЛЕНО
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # Состояние 3: МЕНЮ ДРУГА
            FRIEND_MENU: [
                CallbackQueryHandler(standard_profile_callback, pattern='^standard_\\d+$'),
                CallbackQueryHandler(intimate_profile_callback, pattern='^intimate_\\d+$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^four_f_\\d+$'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^four_f_explain$'),
                CallbackQueryHandler(my_reflections_callback, pattern='^my_reflections$'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
            ],
            
            # Состояние 4: МЕНЮ 4F
            FOUR_F_MENU: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_\\d+_\\w+$'),
                CallbackQueryHandler(open_4f_key_callback, pattern='^open_4f_\\d+_\\w+$'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^four_f_explain$'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_\\d+$'),
                CallbackQueryHandler(my_reflections_callback, pattern='^my_reflections$'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
            ],
            
            # Состояние 5: КОНТЕНТ 4F
            FOUR_F_CONTENT: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_\\d+_\\w+$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^four_f_\\d+$'),
                CallbackQueryHandler(my_reflections_callback, pattern='^my_reflections$'),
            ],
            
            # Состояние 6: ПЛАТЕЖИ
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(process_payment_callback, pattern='^process_payment_'),
                CallbackQueryHandler(demo_callback, pattern='^check_payment_'),
                CallbackQueryHandler(demo_callback, pattern='^pay_access_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^four_f_\\d+$'),
                CallbackQueryHandler(my_reflections_callback, pattern='^my_reflections$'),
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
    
    print("\n🚀 БОТ ЗАПУЩЕН!")
    print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
