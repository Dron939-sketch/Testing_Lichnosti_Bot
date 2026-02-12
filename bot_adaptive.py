#!/usr/bin/env python3
"""
ПРОТОТИП: НОВАЯ НАВИГАЦИЯ И 4F-КЛЮЧИ
Версия: 5.0-prototype
"""

import logging
import os
import uuid
import json
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
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "ваш_shop_id")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "ваш_secret_key")
API_URL = os.getenv("API_URL", "https://your-api.com")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== СОСТОЯНИЯ =====
RESULTS_SCREEN = 0
MY_SEXUAL_PROFILE = 1
INVITES_LIST = 2
FRIEND_MENU = 3
FOUR_F_MENU = 4
FOUR_F_CONTENT = 5
PAYMENT_SCREEN = 6
FOUR_F_PAYMENT_SCREEN = 7

# ===== КОНСТАНТЫ =====
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1  # ТЕСТОВЫЙ РЕЖИМ - 1 РУБЛЬ

# ===== ПРАВИЛЬНЫЕ 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {
    "1F": "🔥",
    "2F": "🏃", 
    "3F": "🧬",
    "4F": "🍽"
}

FOUR_F_TITLES = {
    "1F": "ATTACK / FIGHT",
    "2F": "ESCAPE / AVOIDANCE",
    "3F": "SEX / MATING",
    "4F": "ABSORPTION / SATIETY"
}

FOUR_F_DESCRIPTIONS = {
    "1F": "Access to fears and boundaries",
    "2F": "Access to traumas and triggers",
    "3F": "Access to desire and passion",
    "4F": "Access to trust and intimacy"
}

FOUR_F_FULL_DESCRIPTIONS = {
    "1F": """This key unlocks access to:
└ What he's afraid of
└ What makes him angry
└ How he defends himself
└ His boundaries and fears""",
    
    "2F": """This key unlocks access to:
└ What he runs from
└ His triggers and traumas
└ Situations he avoids
└ His escape patterns""",
    
    "3F": """This key unlocks access to:
└ What turns him on
└ His desire triggers
└ Attraction patterns
└ Intimate scenarios""",
    
    "4F": """This key unlocks access to:
└ What gives him safety
└ His calm triggers
└ Trust building patterns
└ Intimacy needs"""
}

FOUR_F_TAGS = {
    "1F": "Key to fears and boundaries",
    "2F": "Key to traumas and triggers",
    "3F": "Key to desire and passion",
    "4F": "Key to trust and intimacy"
}

# ===== ТЕКСТ ОБУЧАЙКИ 4F =====
FOUR_F_EXPLANATION = """
📘 <b>WHAT ARE 4F-KEYS?</b>

🧬 <b>4F is an access system to human states</b>
Four basic reactions coded in the subconscious.
Keys to understanding another person's deep states.

────────────────────

1F 🔥 <b>ATTACK / FIGHT</b>
└ What triggers aggression, defense, attack
└ What he fears, what angers him
└ <i>Key to fears and boundaries</i>

2F 🏃 <b>ESCAPE / AVOIDANCE</b>
└ What shuts him down, makes him run
└ Topics, people, situations he avoids
└ <i>Key to traumas and triggers</i>

3F 🧬 <b>SEX / MATING</b>
└ What turns on his sexuality
└ Words, touches, context, scenarios
└ <i>Key to desire and passion</i>

4F 🍽 <b>ABSORPTION / SATIETY</b>
└ What gives him SAFETY
└ What saturates, calms, relaxes
└ <i>Key to trust and intimacy</i>

────────────────────
💰 <b>Price:</b> 1₽ (test mode)
"""

# ===== ЗАГРУЗКА ПРОФИЛЕЙ =====
def load_intimate_profile() -> dict:
    """Загружает интимный профиль"""
    return {
        "profile_type": "SA-5_INT",
        "archetype": "Первооткрыватель · Эстет · Соблазнитель",
        "role": "Тот, кто разжигает интерес",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": """
Вы не соблазняете — вы <b>ОТКРЫВАЕТЕ</b>.
Ваша сексуальность — это приглашение в путешествие.

Вас возбуждает не тело, а <b>ПРОЦЕСС</b>:
▪️ Как меняется взгляд
▪️ Как тают барьеры
▪️ Как запретное становится желанным
"""
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
    """Загружает контент 4F-ключа"""
    base_triggers = {
        "1F": [
            "«I understand why you react this way»",
            "«You have every right to be angry»",
            "«I'm on your side»",
            "«This is really unfair»",
            "«Your boundaries are important»"
        ],
        "2F": [
            "«You don't have to do this»",
            "«It's safe here»",
            "«I'll wait»",
            "«You can leave anytime»",
            "«No pressure»"
        ],
        "3F": [
            "«You're so...» (sincere compliment)",
            "Eye contact a little longer than usual",
            "«What do you like?» (interest in desires)",
            "Accidental touch that isn't withdrawn",
            "Whisper, intimate context"
        ],
        "4F": [
            "«I'm not going anywhere»",
            "«You can relax»",
            "Familiar smell, cozy place",
            "Rituals: tea, blanket, silence together",
            "Touch without expectations"
        ]
    }
    
    base_analysis = {
        "1F": "Fear of attack arises when a person doesn't feel safe. His aggression is defense. Don't devalue, don't argue, acknowledge the right to anger.",
        "2F": "Avoidance is a way to cope with overload. The person isn't weak, they're just protecting themselves from what they can't handle right now.",
        "3F": "Attraction turns on through play, mystery, unsaid. Directness kills interest. Tease, but don't taunt.",
        "4F": "Satiety is about safety. A person closes the basic need for 'fullness'. When scared - seeks food, warmth, familiar."
    }
    
    base_protocol = {
        "1F": "1. Notice the trigger\n2. Acknowledge the emotion\n3. Don't pressure\n4. Give time",
        "2F": "1. Remove pressure\n2. Give an exit\n3. Don't pursue\n4. Return control",
        "3F": "1. Create context\n2. Play with attention\n3. Read responses\n4. Build tension",
        "4F": "1. Create stability\n2. Remove surprises\n3. Feed literally and metaphorically\n4. Don't demand return"
    }
    
    return {
        "function": function,
        "emoji": FOUR_F_EMOJIS[function],
        "title": FOUR_F_TITLES[function],
        "description": FOUR_F_DESCRIPTIONS[function],
        "full_description": FOUR_F_FULL_DESCRIPTIONS[function],
        "tag": FOUR_F_TAGS[function],
        "triggers": base_triggers[function],
        "analysis": base_analysis[function],
        "protocol": base_protocol[function],
        "is_demo": False
    }

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====
def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    """Генерирует уникальный ID платежа"""
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """Создает платеж в ЮKassa (тестовый режим - 1 рубль)"""
    try:
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id
        }
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "test_mode": "true"
            }
        }
        
        # В прототипе возвращаем тестовый URL
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
    invites = get_user_invites(user_id)
    if len(invites) >= 2:
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

# ============================================
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ ТЕСТА (3 КНОПКИ)
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    context.user_data["profile"] = USER_PROFILE.copy()
    
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') else None
    profile = context.user_data.get("profile", USER_PROFILE)
    
    message = f"""
🧠 <b>YOUR PROFILE IS READY</b>

📊 <b>{profile['display_name']}</b>

💬 <b>QUOTE:</b>
«I don't seek - I find»

💔 <b>CORE ISSUE</b>
It's hard for you to ask for help, even when you need it.

🛠 <b>TOOL</b>
Today: ask someone for a small favor.
Notice that the world doesn't collapse.
"""
    
    keyboard = [
        [InlineKeyboardButton("🪞 Mirror", callback_data="share_mirror")],
        [InlineKeyboardButton("📖 Full", callback_data="full_description")],
        [InlineKeyboardButton("🔞 Sex", callback_data="my_sexual_profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    profile_data = load_intimate_profile()
    free_count = count_free_friends(query.from_user.id)
    invites = context.user_data.get("sexual_invites", [])
    used_friends = [inv for inv in invites if inv.get("status") == "used"]
    
    friends_list = ""
    for friend in used_friends[:3]:
        friend_name = friend.get("friend_name", "friend")
        friend_profile = friend.get("friend_profile", "SA-3_CON")
        keys = ""
        if friend.get("purchased_functions"):
            keys = f" · 🔑 {' '.join(friend['purchased_functions'])}"
        friends_list += f"\n   👤 {friend_name} · {friend_profile}{keys}"
    
    limit_status = ""
    if free_count >= FREE_FRIEND_LIMIT:
        limit_status = f"\n\n💎 <b>Free limit:</b> {free_count}/{FREE_FRIEND_LIMIT} · EXPIRED\n   Next friend: {FRIEND_ACCESS_PRICE}₽ for access"
    
    message = f"""
🔞 <b>YOUR INTIMATE PROFILE</b>

📊 <b>Type:</b> <code>{profile_data['profile_type']}</code>
🧠 <b>Archetype:</b> {profile_data['archetype']}

💬 <b>QUOTE:</b>
{profile_data['quote']}

────────────────────
🧠 <b>YOUR NATURE:</b>
{profile_data['description']}

────────────────────
🔗 <b>WANT TO SEE FRIEND'S INTIMATE PROFILE?</b>

⬇️ <b>HOW IT WORKS:</b>

1️⃣ Click <b>«🔞 Create invite»</b>
2️⃣ Send link to friend
3️⃣ Friend takes test → you get HIS profile
4️⃣ Free: first 2 friends
5️⃣ 3+ friend: {FRIEND_ACCESS_PRICE}₽ for access
{limit_status}

💎 <b>ACTIVATED FRIENDS:</b>{friends_list if friends_list else "\n   No friends yet"}
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 CREATE INVITE", callback_data="create_invite")],
        [InlineKeyboardButton("🔍 MY INVITES", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_results")]
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
    query = update.callback_query
    await query.answer("🔗 Creating link...")
    
    profile = context.user_data.get("profile", USER_PROFILE)
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}"
    invite_url = f"https://t.me/YourBot?start={invite_code}"
    
    invite_message = (
        "There's this thing.\n"
        "It defines your personality type.\n"
        "I took it - 90% match.\n"
        f"{invite_url}\n\n"
        "Wonder what you'll get?"
    )
    
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
    
    created_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    share_url = f"https://t.me/share/url?url={invite_url}&text={invite_message}"
    
    message = f"""
🔗 <b>YOUR INVITE IS READY</b>

💬 <b>MESSAGE:</b>

<code>{invite_message}</code>

────────────────────
🟢 <b>STATUS:</b> ACTIVE · waiting for friend
⏳ <b>Created:</b> {created_time}

────────────────────
⬇️ <b>JUST SEND:</b>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 SEND TO FRIEND", url=share_url)],
        [
            InlineKeyboardButton("🔄 CHECK STATUS", callback_data=f"check_{invite_code}"),
            InlineKeyboardButton("🔍 MY INVITES", callback_data="my_invites")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: СПИСОК ПРИГЛАШЕНИЙ
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    invites = context.user_data.get("sexual_invites", [])
    
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    message = f"""
🔍 <b>MY INVITES</b>

🔗 <b>TOTAL:</b> {len(invites)}
────────────────────
"""
    
    if active_invites:
        message += "\n🟢 <b>ACTIVE · waiting</b>"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
            days = int((datetime.now().timestamp() - inv["created_at"]) / 86400)
            message += f"\n   • {created} · waiting {days}d"
    
    if used_invites:
        message += "\n\n✅ <b>ACTIVATED · friends</b>"
        for inv in used_invites[:5]:
            friend_name = inv.get("friend_name", "friend")
            friend_profile = inv.get("friend_profile", "SA-3_CON")
            used_date = datetime.fromtimestamp(inv.get("used_at", inv["created_at"])).strftime('%d.%m.%Y')
            keys = ""
            if inv.get("purchased_functions"):
                keys = f" · 🔑 {' '.join(inv['purchased_functions'])}"
            
            message += f"\n\n   👤 {friend_name}"
            message += f"\n   📊 {friend_profile} · {used_date}{keys}"
    
    message += "\n────────────────────"
    
    keyboard = []
    
    for inv in used_invites[:5]:
        friend_name = inv.get("friend_name", "friend")
        friend_id = inv.get("friend_id")
        if friend_id:
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {friend_name}",
                    callback_data=f"friend_{friend_id}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔞 CREATE NEW", callback_data="create_invite")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="my_sexual_profile")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 👤 ЭКРАН 5: МЕНЮ ПРОФИЛЯ ДРУГА (4 КНОПКИ)
# ============================================

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Friend not found", show_alert=True)
        return INVITES_LIST
    
    context.user_data["current_friend_id"] = friend_id
    context.user_data["current_friend_data"] = friend_data
    
    friend_name = friend_data.get("friend_name", "friend")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    access_status = friend_data.get("access_status", "free")
    free_count = count_free_friends(query.from_user.id)
    
    if access_status == "locked" or (free_count >= FREE_FRIEND_LIMIT and not friend_data.get("access_paid")):
        return await show_payment_access_screen(update, context, friend_data)
    
    message = f"""
👤 <b>{friend_name}</b>

📊 <code>{friend_profile}</code>
💎 {'🔓 Free' if access_status == 'free' else '💰 Paid'}

────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Standart", callback_data=f"std_{friend_id}")],
        [InlineKeyboardButton("🔞 SEX", callback_data=f"int_{friend_id}")],
        [InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}")],
        [InlineKeyboardButton("📘 About 4F", callback_data="4f_explain")],
        [InlineKeyboardButton("⬅️ Back", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FRIEND_MENU

# ============================================
# 💰 ЭКРАН 6: ОПЛАТА ДОСТУПА
# ============================================

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
    query = update.callback_query
    
    friend_name = friend_data.get("friend_name", "friend")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 <b>{friend_name} LOCKED</b>

📊 <code>{friend_profile}</code>

⚠️ <b>FREE LIMIT EXPIRED</b>
   Used: {free_count}/{FREE_FRIEND_LIMIT}
   Next friend: {FRIEND_ACCESS_PRICE}₽

────────────────────
💰 <b>UNLOCK ACCESS:</b>
   • Price: {FRIEND_ACCESS_PRICE}₽ (one-time)
   • Standard profile
   • Intimate profile
   • 4F keys purchase
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton(f"🔓 UNLOCK - {FRIEND_ACCESS_PRICE}₽", callback_data=f"pay_access_{friend_data['friend_id']}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return PAYMENT_SCREEN

# ============================================
# 📊 ЭКРАН 7: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_name = "friend"
    
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "friend")
            break
    
    profile = load_friend_standard_profile()
    
    message = f"""
📊 <b>{friend_name}</b>

🧠 <b>Archetype:</b> {profile['archetype']}

💬 <b>Quote:</b>
{profile['quote']}

💔 <b>Issue:</b>
{profile['pain']}

🛠 <b>Tool:</b>
{profile['immediate_tool']}

🚀 <b>Next:</b>
{profile['cta']}
────────────────────
"""
    
    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"friend_{friend_id}"
        )
    ]]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FRIEND_MENU

# ============================================
# 🔞 ЭКРАН 8: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_name = "friend"
    friend_profile = "SA-3_CON"
    
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "friend")
            friend_profile = inv.get("friend_profile", "SA-3_CON")
            break
    
    message = f"""
🔞 <b>{friend_name}</b>

📊 <code>{friend_profile}</code>

⏳ <i>Full description coming soon.</i>
────────────────────
"""
    
    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"friend_{friend_id}"
        )
    ]]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FRIEND_MENU

# ============================================
# 🧬 ЭКРАН 9: МЕНЮ 4F-КЛЮЧЕЙ (НОВЫЙ ДИЗАЙН)
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Friend not found", show_alert=True)
        return INVITES_LIST
    
    friend_name = friend_data.get("friend_name", "friend")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    purchased = friend_data.get("purchased_functions", [])
    
    message = f"""
🧬 <b>4F-KEYS for {friend_name}</b>

📊 <code>{friend_profile}</code>

────────────────────

1F 🔥 <b>ATTACK / FIGHT</b>
└ {FOUR_F_DESCRIPTIONS['1F']}
└ What makes him angry, scares, defends

2F 🏃 <b>ESCAPE / AVOIDANCE</b>
└ {FOUR_F_DESCRIPTIONS['2F']}
└ What he runs from, avoids

3F 🧬 <b>SEX / MATING</b>
└ {FOUR_F_DESCRIPTIONS['3F']}
└ What turns him on, attracts

4F 🍽 <b>ABSORPTION / SATIETY</b>
└ {FOUR_F_DESCRIPTIONS['4F']}
└ What gives safety, calm, peace

────────────────────
"""
    
    keyboard = []
    
    for f in ["1F", "2F", "3F", "4F"]:
        emoji = FOUR_F_EMOJIS[f]
        if f in purchased:
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {f} - OPEN",
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
        InlineKeyboardButton("📘 About 4F", callback_data="4f_explain"),
        InlineKeyboardButton(f"⬅️ Back", callback_data=f"friend_{friend_id}")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

# ============================================
# 📘 ЭКРАН 10: ОБУЧАЙКА 4F
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    message = FOUR_F_EXPLANATION
    
    keyboard = []
    
    friend_id = context.user_data.get("current_friend_id")
    
    if friend_id:
        keyboard.append([
            InlineKeyboardButton("⬅️ Back", callback_data=f"friend_{friend_id}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("⬅️ Back", callback_data="my_invites")
        ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

# ============================================
# 💳 ЭКРАН 11: ПОКУПКА 4F-КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран покупки 4F-ключа с ценой 1₽ (тест)"""
    query = update.callback_query
    await query.answer("💰 Creating invoice...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Friend not found", show_alert=True)
        return FOUR_F_MENU
    
    friend_name = friend_data.get("friend_name", "friend")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>

👤 <b>Friend:</b> {friend_name}
📊 <b>Profile:</b> <code>{friend_profile}</code>

{content['full_description']}

🎯 <b>You will receive:</b>
└ 10+ exact trigger phrases
└ Psychological analysis
└ Application protocol

────────────────────
💰 <b>Price:</b> 1₽ (test mode)
────────────────────
"""
    
    payment_id = generate_payment_id("4f", query.from_user.id)
    
    keyboard = [
        [InlineKeyboardButton("💳 PAY 1₽", callback_data=f"process_payment_{payment_id}_{friend_id}_{function}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"4f_{friend_id}")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_PAYMENT_SCREEN

# ============================================
# 💳 ЭКРАН 12: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка платежа через ЮKassa"""
    query = update.callback_query
    await query.answer("💳 Connecting to payment system...")
    
    parts = query.data.split("_")
    payment_id = parts[2]
    friend_id = int(parts[3])
    function = parts[4]
    
    user_id = query.from_user.id
    
    payment_result = create_yookassa_invoice(
        payment_id=payment_id,
        user_id=user_id,
        amount=1.0,
        description=f"4F key {function} for friend {friend_id}"
    )
    
    if not payment_result.get("success"):
        await query.answer(f"❌ Payment error", show_alert=True)
        return FOUR_F_PAYMENT_SCREEN
    
    confirmation_url = payment_result["confirmation_url"]
    
    message = f"""
💳 <b>PAYMENT CREATED</b>

🔑 <b>Key:</b> {function}
👤 <b>Friend ID:</b> {friend_id}
💰 <b>Amount:</b> 1₽ (test mode)

────────────────────
✅ Click the button below to pay
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 PAY 1₽", url=confirmation_url)],
        [InlineKeyboardButton("🔄 CHECK PAYMENT", callback_data=f"check_payment_{payment_id}_{friend_id}_{function}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"4f_{friend_id}")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_PAYMENT_SCREEN

# ============================================
# 🔑 ЭКРАН 13: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔓 Opening key...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>

<i>for profile SA-4_CAP</i>

────────────────────

🎯 <b>TRIGGER PHRASES:</b>
"""
    
    for i, trigger in enumerate(content['triggers'], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

────────────────────

🧠 <b>ANALYSIS:</b>
{content['analysis']}

────────────────────

📋 <b>PROTOCOL:</b>
{content['protocol']}

────────────────────

<i>«{content['tag']}»</i>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back", callback_data=f"4f_{friend_id}")]
    ]
    
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
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    pattern = query.data
    
    if pattern.startswith("check_"):
        await query.answer("🟢 Active, waiting for friend")
    elif pattern.startswith("pay_access_"):
        await query.answer("💰 Demo payment")
    elif pattern == "share_mirror":
        await query.answer("🪞 Coming soon")
    elif pattern == "full_description":
        await query.answer("📖 690₽")
    elif pattern.startswith("check_payment_"):
        await query.answer("✅ Payment successful! (demo)")
        
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
            
            await query.answer("✅ Key unlocked!", show_alert=True)
            return await open_4f_key_callback(update, context)
    else:
        await query.answer("✅ Demo mode")
    
    return RESULTS_SCREEN

# ============================================
# 🚀 ЗАПУСК
# ============================================

def main():
    print("\n" + "="*60)
    print("🧠 PROTOTYPE: 4F-KEYS & NAVIGATION v5.0")
    print("="*60)
    print("✅ Results screen: 3 buttons (Mirror, Full, Sex)")
    print("✅ Friend menu: 4 buttons (Standart, SEX, 4F, About 4F)")
    print("✅ 4F menu: clean design, no prices in text")
    print("✅ 4F keys: 1₽ test mode, YooKassa integration")
    print("✅ No 'Bundle' button")
    print("✅ No 'Main Menu' button")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ERROR: Set TELEGRAM_BOT_TOKEN!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    
    # Navigation
    app.add_handler(CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"))
    
    # Results screen
    app.add_handler(CallbackQueryHandler(show_results_screen, pattern="^show_results$"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^share_mirror$"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^full_description$"))
    
    # Sexual profile
    app.add_handler(CallbackQueryHandler(my_sexual_profile_callback, pattern="^my_sexual_profile$"))
    app.add_handler(CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"))
    app.add_handler(CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"))
    
    # Invites
    app.add_handler(CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"))
    app.add_handler(CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^check_"))
    
    # Friend profile
    app.add_handler(CallbackQueryHandler(friend_menu_callback, pattern="^friend_"))
    app.add_handler(CallbackQueryHandler(standard_profile_callback, pattern="^std_"))
    app.add_handler(CallbackQueryHandler(intimate_profile_callback, pattern="^int_"))
    
    # 4F
    app.add_handler(CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"))
    app.add_handler(CallbackQueryHandler(four_f_explanation_callback, pattern="^4f_explain$"))
    app.add_handler(CallbackQueryHandler(buy_4f_key_callback, pattern="^buy_4f_"))
    app.add_handler(CallbackQueryHandler(process_payment_callback, pattern="^process_payment_"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^check_payment_"))
    app.add_handler(CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"))
    
    # Access payment
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^pay_access_"))
    
    print("\n🚀 Bot started!")
    print("\n📱 TEST FLOW:")
    print("  /start → 🔞 Sex → 🔞 CREATE INVITE")
    print("  → 🔍 MY INVITES → 👤 @alex")
    print("  → 🧬 4F → 🔥 1F - 1₽ → 💳 PAY 1₽")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
