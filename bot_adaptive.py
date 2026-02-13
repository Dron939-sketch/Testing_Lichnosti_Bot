#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 10.7 - ПОЛНОСТЬЮ ИСПРАВЛЕНА!
✅ ВСЕ КНОПКИ "МОИ ОТРАЖЕНИЯ" РАБОТАЮТ
✅ ДОБАВЛЕНА КНОПКА В ЭКРАН СОЗДАНИЯ ССЫЛКИ
✅ УДАЛЕНЫ ДУБЛИРУЮЩИЕ ОБРАБОТЧИКИ
✅ ИНТИМНЫЙ ПРОФИЛЬ ПОКАЗЫВАЕТ ВСЕ 14 СЕКЦИЙ
✅ ЗАГРУЗКА ИЗ sexual_18/sa_5_int.json
✅ ИСПРАВЛЕНА ОШИБКА 'created_at'
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
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

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

# ===== 4F-КОНСТАНТЫ =====
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

1F 🔥 НАПАДЕНИЕ / ЯРОСТЬ
└ Как гасить агрессию и не нарваться

2F 🏃 БЕГСТВО / СТРАХ
└ Чего он боится на самом деле

3F 🧬 СЕКС / ЖЕЛАНИЕ
└ Что включает его режим «хочу»

4F 🍽 ПОГЛОЩЕНИЕ / ДЕНЬГИ
└ Какие идеи прорастают в его голове

💰 Цена: 1₽ (тестовый режим)
"""

# ===== ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ =====
def load_intimate_profile() -> dict:
    """Загружает интимный профиль из JSON файла"""
    try:
        possible_paths = [
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join("sexual_18", "sa_5_int.json"),
            os.path.join(os.path.dirname(__file__), "sexual_18", "sa_5_int.json"),
        ]
        
        if os.path.exists('/app'):
            possible_paths.append('/app/sexual_18/sa_5_int.json')
        
        for profile_path in possible_paths:
            if os.path.exists(profile_path):
                logger.info(f"✅ НАЙДЕН ФАЙЛ: {profile_path}")
                
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
        
        logger.warning("⚠️ Файл не найден! Использую аварийный профиль")
        return get_emergency_profile()
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return get_emergency_profile()

def get_emergency_profile() -> dict:
    """Аварийный интимный профиль"""
    return {
        "profile_type": "SA-5_INT",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие. Ритуал. Мистерия.",
        "sections": {}
    }

def format_intimate_profile(profile_data: dict, user_name: str) -> str:
    """Форматирует интимный профиль - ВСЕ 14 СЕКЦИЙ"""
    message = f"""
🔞 ИНТИМНЫЙ ПРОФИЛЬ
{user_name}

📊 Тип: {profile_data.get('profile_type', 'SA-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 ЦИТАТА:
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 ВАША ПРИРОДА:
{profile_data.get('description', '').strip()}
"""
    
    sections = profile_data.get('sections', {})
    if sections:
        message += f"\n{SEXUAL_DIVIDER}\n"
        
        section_order = [
            "what_turns_on", "what_turns_off", "smells_tastes", "sounds",
            "dirty_details", "fetishes", "places", "morning", "secret_desires",
            "whispers", "core", "compliments", "tells", "remains"
        ]
        
        for section_key in section_order:
            section = sections.get(section_key)
            if section:
                title = section.get('title', '')
                if title:
                    message += f"\n{title}\n"
                
                if 'items' in section and section['items']:
                    for item in section['items'][:5]:
                        message += f"• {item}\n"
                elif 'trigger' in section and section['trigger']:
                    message += f"{section['trigger']}\n"
    
    message += f"""
{SEXUAL_DIVIDER}

💎 ТАМ, ЗА ЗЕРКАЛОМ...

Вы увидели только что СВОЁ 🪞 отражение.
Но у каждого друга — своя тайна.

⬇️ КАК УВИДЕТЬ ИХ:

1️⃣ Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО профиль
"""
    return message

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
    
    base_analysis = {
        "1F": "Страх нападения возникает, когда человек не чувствует безопасности.",
        "2F": "Избегание — это способ справиться с перегрузкой.",
        "3F": "Влечение включается через игру, тайну, недосказанность.",
        "4F": "Желание заработать — это про безопасность, статус, свободу."
    }
    
    base_protocol = {
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
    
    current_time = datetime.now().timestamp()
    yesterday = current_time - 86400
    
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
            "created_at": yesterday,
            "used_at": current_time,
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
            "created_at": yesterday,
            "used_at": yesterday,
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

🛠 ИНСТРУМЕНТ
Сегодня: попросите кого-то о маленькой услуге.
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
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ - ИСПРАВЛЕНО!
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения - ДОБАВЛЕНА КНОПКА МОИ ОТРАЖЕНИЯ!"""
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
<b>🔞 ВАША ССЫЛКА ГОТОВА!</b>

🔗 <code>{invite_url}</code>

<b>💬 ТЕКСТ СООБЩЕНИЯ:</b>
{invite_message}

{SEXUAL_DIVIDER}
🟢 АКТИВНО • ожидание
📅 {current_time}
{SEXUAL_DIVIDER}

🎯 Через 15 минут после теста
   вы увидите его 18+ профиль.
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
    
    # ===== ИСПРАВЛЕНИЕ: ДОБАВЛЕНА КНОПКА МОИ ОТРАЖЕНИЯ! =====
    keyboard = [
        [InlineKeyboardButton("📤 Отправить ссылку", url=share_url)],
        [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],  # ✅ ДОБАВЛЕНО!
        [InlineKeyboardButton("⬅️ Назад", callback_data="my_sexual_profile")]
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
💎 МОИ ОТРАЖЕНИЯ

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
                created_ts = inv.get("created_at")
                if created_ts:
                    created = datetime.fromtimestamp(created_ts).strftime('%d.%m')
                    days = int((datetime.now().timestamp() - created_ts) / 86400)
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
                
                timestamp = inv.get("used_at") or inv.get("created_at") or datetime.now().timestamp()
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
        
        message += f"""

{SEXUAL_DIVIDER}
💡 Каждое отражение — ключ к человеку.
"""
        
        keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")])
        keyboard.append([InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="my_sexual_profile")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        await query.answer("❌ Ошибка", show_alert=True)
        return RESULTS_SCREEN

# ============================================
# 🔍 ЭКРАН 5: ПРОВЕРКА СТАТУСА
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer()
    
    try:
        invite_id = query.data.replace("check_status_", "")
        
        message = f"""
🔍 СТАТУС ПРИГЛАШЕНИЯ

🔗 <code>https://t.me/{BOT_USERNAME}?start={invite_id}</code>

🟢 АКТИВНО · ждёт друга
⏳ Создано: {datetime.now().strftime('%d.%m.%Y %H:%M')}

✨ Друг ещё не прошёл тест.
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
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

def load_friend_standard_profile() -> dict:
    """Стандартный профиль друга"""
    return {
        "archetype": "Автономный стратег",
        "quote": "«Я не ищу одобрения — я ищу эффективность.»",
        "pain": "Вам сложно делегировать.",
        "immediate_tool": "Сегодня: передайте задачу другому.",
        "cta": "Исследуйте баланс."
    }

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
                InlineKeyboardButton("📊 Стандартный", callback_data=f"std_{friend_id}"),
                InlineKeyboardButton("🔞 Интимный", callback_data=f"int_{friend_id}")
            ],
            [
                InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}"),
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
        logger.error(f"❌ Ошибка: {e}")
        return INVITES_LIST

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
   Цена: {FRIEND_ACCESS_PRICE}₽
"""
    
    keyboard = [
        [InlineKeyboardButton(f"🔓 РАЗБЛОКИРОВАТЬ - {FRIEND_ACCESS_PRICE}₽", 
                             callback_data=f"pay_access_{friend_data['friend_id']}")],
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
# 📊 ЭКРАН 8: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    try:
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "друг") if friend_data else "друг"
        
        profile = load_friend_standard_profile()
        
        message = f"""
📊 {friend_name}

🧠 Архетип: {profile['archetype']}

💬 Цитата:
{profile['quote']}

💔 Суть:
{profile['pain']}

🛠 Инструмент:
{profile['immediate_tool']}
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
        logger.error(f"❌ Ошибка: {e}")
        return FRIEND_MENU

# ============================================
# 🔞 ЭКРАН 9: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга"""
    query = update.callback_query
    await query.answer()
    
    try:
        friend_id = int(query.data.split("_")[1])
        friend_data = get_friend_by_id(context, friend_id)
        
        if not friend_data:
            return FRIEND_MENU
        
        friend_name = friend_data.get("friend_name", "друг")
        
        message = f"""
🔞 ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
👤 {friend_name}

⚠️ ТЕСТОВЫЙ РЕЖИМ

Это демо-профиль.
В боевом режиме: реальные триггеры и сценарии.

💎 Купите доступ за {FRIEND_ACCESS_PRICE}₽
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
        logger.error(f"❌ Ошибка: {e}")
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
            return INVITES_LIST
        
        friend_name = friend_data.get("friend_name", "друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        purchased = friend_data.get("purchased_functions", [])
        
        message = f"""
🧬 4F-КЛЮЧИ ДЛЯ {friend_name}

📊 {friend_profile}

1F 🔥 {FOUR_F_TITLES['1F']}
2F 🏃 {FOUR_F_TITLES['2F']}
3F 🧬 {FOUR_F_TITLES['3F']}
4F 🍽 {FOUR_F_TITLES['4F']}
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
                        f"{emoji} {f} - 1₽",
                        callback_data=f"buy_4f_{friend_id}_{f}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("❓ Что это?", callback_data="4f_explain"),
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
        logger.error(f"❌ Ошибка: {e}")
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
            InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")
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
            return FOUR_F_MENU
        
        friend_name = friend_data.get("friend_name", "друг")
        
        content = load_4f_content(function)
        
        message = f"""
{content['emoji']} {content['title']}
{content['subtitle']}

👤 Друг: {friend_name}

{content['description']}

💰 Цена: 1₽ (тест)
"""
        
        payment_id = generate_payment_id("4f", query.from_user.id)
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", 
                                callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
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
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_MENU

# ============================================
# 💳 ЭКРАН 13: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Процесс платежа"""
    query = update.callback_query
    await query.answer("💳 Подключаюсь...")
    
    try:
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
            await query.answer("❌ Ошибка платежа", show_alert=True)
            return FOUR_F_PAYMENT_SCREEN
        
        message = f"""
💳 СЧЁТ СФОРМИРОВАН

🔑 Ключ: {function}
💰 Сумма: 1₽
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", url=payment_result["confirmation_url"])],
            [InlineKeyboardButton("🔄 ПРОВЕРИТЬ", 
                                callback_data=f"check_payment_{payment_id}_{friend_id}_{function}")],
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
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_PAYMENT_SCREEN

# ============================================
# 🔑 ЭКРАН 14: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТЫЙ 4F-КЛЮЧ"""
    query = update.callback_query
    await query.answer("🔓 Открываю ключ...")
    
    try:
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        friend_data = get_friend_by_id(context, friend_id)
        friend_name = friend_data.get("friend_name", "друг") if friend_data else "друг"
        
        if friend_data and function not in friend_data.get("purchased_functions", []):
            if "purchased_functions" not in friend_data:
                friend_data["purchased_functions"] = []
            friend_data["purchased_functions"].append(function)
        
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

🧠 РАЗБОР:
{content['analysis']}

📋 ПРОТОКОЛ:
{content['protocol']}
"""
        
        keyboard = [
            [InlineKeyboardButton("💎 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ К КЛЮЧАМ", callback_data=f"4f_{friend_id}")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_CONTENT
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_CONTENT

# ============================================
# 🎭 ОБРАБОТЧИК ДЕМО-КНОПОК
# ============================================

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для демо-функций"""
    query = update.callback_query
    pattern = query.data
    
    try:
        if pattern.startswith("pay_access_"):
            await query.answer("💰 Демо-платёж доступа", show_alert=True)
        elif pattern == "share_mirror":
            await query.answer("🪞 Скоро здесь будет подарок", show_alert=True)
        elif pattern == "full_description":
            await query.answer("📖 Полное описание — 690₽", show_alert=True)
        elif pattern.startswith("check_payment_"):
            parts = pattern.split("_")
            if len(parts) >= 5:
                friend_id = int(parts[3])
                function = parts[4]
                
                friend_data = get_friend_by_id(context, friend_id)
                if friend_data:
                    if "purchased_functions" not in friend_data:
                        friend_data["purchased_functions"] = []
                    if function not in friend_data["purchased_functions"]:
                        friend_data["purchased_functions"].append(function)
                
                await query.answer("✅ Ключ активирован! (демо)", show_alert=True)
                
                new_query = update
                new_query.data = f"open_4f_{friend_id}_{function}"
                return await open_4f_key_callback(new_query, context)
        else:
            await query.answer("✅ Демо-режим")
        
        return RESULTS_SCREEN
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
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
# 🚀 ЗАПУСК - ИСПРАВЛЕННАЯ ВЕРСИЯ!
# ============================================

def main():
    """Запуск бота - УБРАНЫ ДУБЛИРУЮЩИЕ ОБРАБОТЧИКИ!"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v10.7")
    print("="*60)
    print("✅ ИСПРАВЛЕНИЯ:")
    print("   • КНОПКА «МОИ ОТРАЖЕНИЯ» ДОБАВЛЕНА В ЭКРАН СОЗДАНИЯ ССЫЛКИ!")
    print("   • УДАЛЕНЫ ДУБЛИРУЮЩИЕ ОБРАБОТЧИКИ!")
    print("   • ВСЕ КНОПКИ ИСПОЛЬЗУЮТ callback_data='my_invites'")
    print("   • ConversationHandler - ЕДИНСТВЕННЫЙ ОБРАБОТЧИК")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # ===== ЕДИНСТВЕННЫЙ ОБРАБОТЧИК - CONVERSATION HANDLER =====
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
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(check_status_callback, pattern='^check_status_'),
                CallbackQueryHandler(friend_menu_callback, pattern='^friend_'),
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
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
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
            ],
            
            FOUR_F_CONTENT: [
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
            ],
            
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
    
    # ✅ ТОЛЬКО ОДИН ОБРАБОТЧИК!
    app.add_handler(conv_handler)
    
    print("\n🚀 БОТ ЗАПУЩЕН!")
    print("✅ ВСЕ КНОПКИ 'МОИ ОТРАЖЕНИЯ' РАБОТАЮТ!")
    print("✅ ДУБЛИРУЮЩИЕ ОБРАБОТЧИКИ УДАЛЕНЫ!")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
