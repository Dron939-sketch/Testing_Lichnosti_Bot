#!/usr/bin/env python3
"""
ПРОТОТИП: НОВАЯ НАВИГАЦИЯ И 4F-КЛЮЧИ
Версия: 5.2-prototype - РУССКАЯ
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

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== СОСТОЯНИЯ =====
RESULTS_SCREEN = 0
MY_SEXUAL_PROFILE = 1
INVITES_LIST = 2
FRIEND_MENU = 3
FOUR_F_MENU = 4
FOUR_F_CONTENT = 5
FOUR_F_PAYMENT_SCREEN = 6

# ===== КОНСТАНТЫ =====
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1  # ТЕСТОВЫЙ РЕЖИМ - 1 РУБЛЬ

# ===== ПРАВИЛЬНЫЕ 4F-КОНСТАНТЫ (НА РУССКОМ) =====
FOUR_F_EMOJIS = {
    "1F": "🔥",
    "2F": "🏃", 
    "3F": "🧬",
    "4F": "🍽"
}

FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / БЕЙ",
    "2F": "БЕГСТВО / ИЗБЕГАНИЕ",
    "3F": "СЕКС / СПАРИВАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / СЫТОСТЬ"
}

FOUR_F_DESCRIPTIONS = {
    "1F": "Доступ к страхам и границам",
    "2F": "Доступ к травмам и триггерам",
    "3F": "Доступ к желанию и страсти",
    "4F": "Доступ к доверию и близости"
}

FOUR_F_FULL_DESCRIPTIONS = {
    "1F": """Этот ключ открывает доступ к:
└ Чего он боится
└ Что его бесит
└ Как он защищается
└ Его границы и страхи""",
    
    "2F": """Этот ключ открывает доступ к:
└ От чего он убегает
└ Его триггеры и травмы
└ Ситуации, которых избегает
└ Его паттерны бегства""",
    
    "3F": """Этот ключ открывает доступ к:
└ Что его заводит
└ Его эротические триггеры
└ Паттерны привлечения
└ Интимные сценарии""",
    
    "4F": """Этот ключ открывает доступ к:
└ Что дает ему безопасность
└ Что его успокаивает
└ Как он доверяет
└ Потребности в близости"""
}

FOUR_F_TAGS = {
    "1F": "Ключ к страхам и границам",
    "2F": "Ключ к травмам и триггерам",
    "3F": "Ключ к желанию и страсти",
    "4F": "Ключ к доверию и близости"
}

# ===== ТЕКСТ ОБУЧАЙКИ 4F (НА РУССКОМ) =====
FOUR_F_EXPLANATION = """
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>

🧬 <b>4F — это система доступа к состояниям человека</b>
Четыре базовые реакции, зашитые в подкорке.
Ключи к пониманию глубинных состояний другого человека.

────────────────────

1F 🔥 <b>НАПАДЕНИЕ / БЕЙ</b>
└ Что включает агрессию, защиту, нападение
└ Чего он боится, что его злит
└ <i>Ключ к страхам и границам</i>

2F 🏃 <b>БЕГСТВО / ИЗБЕГАНИЕ</b>
└ Что выключает его, заставляет убегать
└ Темы, люди, ситуации, которых избегает
└ <i>Ключ к травмам и триггерам</i>

3F 🧬 <b>СЕКС / СПАРИВАНИЕ</b>
└ Что включает его сексуальность
└ Слова, касания, контекст, сценарии
└ <i>Ключ к желанию и страсти</i>

4F 🍽 <b>ПОГЛОЩЕНИЕ / СЫТОСТЬ</b>
└ Что дает ему БЕЗОПАСНОСТЬ
└ Что насыщает, успокаивает, расслабляет
└ <i>Ключ к доверию и близости</i>

────────────────────
💰 <b>Цена:</b> 1₽ (тестовый режим)
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
            "«А что ты любишь?» (интерес к желаниям)",
            "Случайное касание, которое не прерывают",
            "Шёпот, интимный контекст"
        ],
        "4F": [
            "«Я никуда не уйду»",
            "«Ты можешь расслабиться»",
            "Знакомый запах, уютное место",
            "Ритуалы: чай, плед, тишина вдвоём",
            "Прикосновения без ожиданий"
        ]
    }
    
    base_analysis = {
        "1F": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита. Не обесценивайте, не спорьте, признайте право на злость.",
        "2F": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя от того, с чем сейчас не справиться.",
        "3F": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес. Дразните, но не дразнитесь.",
        "4F": "Насыщение — это про безопасность. Человек закрывает базовую потребность в «сытости». Когда страшно — ищет еду, тепло, знакомое."
    }
    
    base_protocol = {
        "1F": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите\n4. Дайте время",
        "2F": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте\n4. Верните контроль",
        "3F": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы\n4. Усиливайте напряжение",
        "4F": "1. Создайте стабильность\n2. Уберите неожиданности\n3. Кормите буквально и метафорически\n4. Не требуйте отдачи"
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
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

def create_yookassa_invoice(payment_id: str, user_id: int, amount: float = 1.0, description: str = "") -> dict:
    """Создает платеж в ЮKassa (тестовый режим - 1 рубль)"""
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
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ (3 КНОПКИ)
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
    query = update.callback_query
    profile = context.user_data.get("profile", USER_PROFILE)
    
    message = f"""
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>

📊 <b>{profile['display_name']}</b>

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
        [InlineKeyboardButton("🔞 Sex", callback_data="my_sexual_profile")]
    ]
    
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ (БЕЗ ДЕНЕГ)
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
        friend_name = friend.get("friend_name", "друг")
        friend_profile = friend.get("friend_profile", "SA-3_CON")
        keys = ""
        if friend.get("purchased_functions"):
            keys = f" · 🔑 {' '.join(friend['purchased_functions'])}"
        friends_list += f"\n   👤 {friend_name} · {friend_profile}{keys}"
    
    message = f"""
🔞 <b>ВАШ ИНТИМНЫЙ ПРОФИЛЬ</b>

📊 <b>Тип:</b> <code>{profile_data['profile_type']}</code>
🧠 <b>Архетип:</b> {profile_data['archetype']}

💬 <b>ЦИТАТА:</b>
{profile_data['quote']}

────────────────────
🧠 <b>ВАША ПРИРОДА:</b>
{profile_data['description']}

────────────────────
🔗 <b>ХОТИТЕ УВИДЕТЬ ИНТИМНЫЙ ПРОФИЛЬ ДРУГА?</b>

⬇️ <b>КАК ЭТО РАБОТАЕТ:</b>

1️⃣ Нажмите <b>«🔞 Создать»</b>
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО профиль

💎 <b>УЖЕ С ВАМИ:</b>{friends_list if friends_list else "\n   Пока никого"}
────────────────────
💫 <i>Чем больше друзей увидят себя в зеркале —
   тем больше интимных профилей откроется вам.</i>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 СОЗДАТЬ", callback_data="create_invite")],
        [InlineKeyboardButton("🔍 МОИ", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return MY_SEXUAL_PROFILE

# ============================================
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ (С МОТИВАЦИЕЙ)
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔗 Создаю ссылку...")
    
    profile = context.user_data.get("profile", USER_PROFILE)
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}"
    invite_url = f"https://t.me/YourBot?start={invite_code}"
    
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой тип личности.\n"
        "Я прошёл — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
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
🔗 <b>ВАШЕ ПРИГЛАШЕНИЕ ГОТОВО</b>

💬 <b>СООБЩЕНИЕ:</b>

<code>{invite_message}</code>

────────────────────
🟢 <b>СТАТУС:</b> АКТИВНО · ждёт друга
⏳ <b>Создано:</b> {created_time}

✨ <b>Один клик — и друг увидит себя настоящим.</b>
   <b>А вы увидите его.</b>

────────────────────
⬇️ <b>ОСТАЛОСЬ ТОЛЬКО ОТПРАВИТЬ:</b>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 ОТПРАВИТЬ", url=share_url)],
        [
            InlineKeyboardButton("🔄 СТАТУС", callback_data=f"check_{invite_code}"),
            InlineKeyboardButton("🔍 МОИ", callback_data="my_invites")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: МОИ ПРИГЛАШЕНИЯ (ВЕСЁЛЫЙ)
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    invites = context.user_data.get("sexual_invites", [])
    
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    message = f"""
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>

🔗 <b>ВСЕГО СОЗДАНО:</b> {len(invites)}
────────────────────
"""
    
    if active_invites:
        message += "\n🟢 <b>ЖДУТ ДРУГА ✨</b>"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
            days = int((datetime.now().timestamp() - inv["created_at"]) / 86400)
            message += f"\n   • {created} · ждёт {days}д"
    
    if used_invites:
        message += "\n\n✅ <b>УЖЕ С ВАМИ 🎉</b>"
        for inv in used_invites[:5]:
            friend_name = inv.get("friend_name", "друг")
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
        friend_name = inv.get("friend_name", "друг")
        friend_id = inv.get("friend_id")
        if friend_id:
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {friend_name}",
                    callback_data=f"friend_{friend_id}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ", callback_data="create_invite")])
    keyboard.append([InlineKeyboardButton("⬅️ К ИНТИМНОМУ", callback_data="my_sexual_profile")])
    
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
    
    message = f"""
👤 <b>{friend_name}</b>

📊 <code>{friend_profile}</code>
💎 {'🔓 Бесплатно' if access_status == 'free' else '💰 Куплен'}

────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Standart", callback_data=f"std_{friend_id}")],
        [InlineKeyboardButton("🔞 SEX", callback_data=f"int_{friend_id}")],
        [InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}")],
        [InlineKeyboardButton("📘 About 4F", callback_data="4f_explain")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")]
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
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 <b>{friend_name} ЗАБЛОКИРОВАН</b>

📊 <code>{friend_profile}</code>

⚠️ <b>БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН</b>
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽

────────────────────
💰 <b>РАЗБЛОКИРОВАТЬ ДОСТУП:</b>
   • Цена: {FRIEND_ACCESS_PRICE}₽ (разово)
   • Стандартный профиль
   • Интимный профиль
   • Покупка 4F-ключей
────────────────────
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
# 📊 ЭКРАН 7: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_name = "друг"
    
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "друг")
            break
    
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
────────────────────
"""
    
    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Назад",
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
    friend_name = "друг"
    friend_profile = "SA-3_CON"
    
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "друг")
            friend_profile = inv.get("friend_profile", "SA-3_CON")
            break
    
    message = f"""
🔞 <b>{friend_name}</b>

📊 <code>{friend_profile}</code>

⏳ <i>Полное описание появится позже.</i>
   Мы работаем над персонализацией.
────────────────────
"""
    
    keyboard = [[
        InlineKeyboardButton(
            "⬅️ Назад",
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
# 🧬 ЭКРАН 9: МЕНЮ 4F-КЛЮЧЕЙ (РУССКИЙ)
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
        await query.answer("❌ Друг не найден", show_alert=True)
        return INVITES_LIST
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    purchased = friend_data.get("purchased_functions", [])
    
    message = f"""
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>

📊 <code>{friend_profile}</code>

────────────────────

1F 🔥 <b>НАПАДЕНИЕ / БЕЙ</b>
└ {FOUR_F_DESCRIPTIONS['1F']}
└ Что его бесит, пугает, заставляет защищаться

2F 🏃 <b>БЕГСТВО / ИЗБЕГАНИЕ</b>
└ {FOUR_F_DESCRIPTIONS['2F']}
└ От чего он убегает, чего избегает

3F 🧬 <b>СЕКС / СПАРИВАНИЕ</b>
└ {FOUR_F_DESCRIPTIONS['3F']}
└ Что его заводит, привлекает, возбуждает

4F 🍽 <b>ПОГЛОЩЕНИЕ / СЫТОСТЬ</b>
└ {FOUR_F_DESCRIPTIONS['4F']}
└ Что дает безопасность, покой, расслабление

────────────────────
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
        InlineKeyboardButton("📘 About 4F", callback_data="4f_explain"),
        InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
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
# 💳 ЭКРАН 11: ПОКУПКА 4F-КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("💰 Создаю счёт...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return FOUR_F_MENU
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>

👤 <b>Друг:</b> {friend_name}
📊 <b>Профиль:</b> <code>{friend_profile}</code>

{content['full_description']}

🎯 <b>Вы получите:</b>
└ 10+ точных триггер-фраз
└ Психологический разбор
└ Протокол применения

────────────────────
💰 <b>Цена:</b> 1₽ (тестовый режим)
────────────────────
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
# 💳 ЭКРАН 12: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("💳 Подключаюсь к платежной системе...")
    
    parts = query.data.split("_")
    payment_id = parts[2]
    friend_id = int(parts[3])
    function = parts[4]
    
    user_id = query.from_user.id
    
    payment_result = create_yookassa_invoice(
        payment_id=payment_id,
        user_id=user_id,
        amount=1.0,
        description=f"4F ключ {function} для друга {friend_id}"
    )
    
    if not payment_result.get("success"):
        await query.answer(f"❌ Ошибка платежа", show_alert=True)
        return FOUR_F_PAYMENT_SCREEN
    
    confirmation_url = payment_result["confirmation_url"]
    
    message = f"""
💳 <b>СЧЁТ СФОРМИРОВАН</b>

🔑 <b>Ключ:</b> {function}
👤 <b>Друг:</b> ID {friend_id}
💰 <b>Сумма:</b> 1₽ (тест)

────────────────────
✅ Нажмите кнопку для оплаты
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", url=confirmation_url)],
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
# 🔑 ЭКРАН 13: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔓 Открываю ключ...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>

<i>для профиля SA-4_CAP</i>

────────────────────

🎯 <b>ТРИГГЕР-ФРАЗЫ:</b>
"""
    
    for i, trigger in enumerate(content['triggers'], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

────────────────────

🧠 <b>ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{content['analysis']}

────────────────────

📋 <b>ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{content['protocol']}

────────────────────

<i>«{content['tag']}»</i>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"4f_{friend_id}")]
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
        await query.answer("🟢 Активно, ждём друга")
    elif pattern.startswith("pay_access_"):
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
            return await open_4f_key_callback(update, context)
    else:
        await query.answer("✅ Демо-режим")
    
    return RESULTS_SCREEN

# ============================================
# 🚀 ЗАПУСК
# ============================================

def main():
    print("\n" + "="*60)
    print("🧠 ПРОТОТИП: 4F-КЛЮЧИ И НАВИГАЦИЯ v5.2")
    print("="*60)
    print("✅ Экран результатов: 3 кнопки (Зеркало, Полный, Sex)")
    print("✅ Интимный профиль: без денег, только суть")
    print("✅ Приглашение: мотивирующий текст, кнопка «ОТПРАВИТЬ»")
    print("✅ Мои приглашения: весёлый, живой, с эмодзи")
    print("✅ Меню друга: 4 кнопки (Standart, SEX, 4F, About 4F)")
    print("✅ 4F-ключи: 1₽ тестовый режим, ЮKassa")
    print("="*60)
    print("🎯 ТЕКСТ — 100% РУССКИЙ (кроме названий кнопок)")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    
    # Навигация
    app.add_handler(CallbackQueryHandler(back_to_results_callback, pattern="^back_to_results$"))
    
    # Результаты
    app.add_handler(CallbackQueryHandler(show_results_screen, pattern="^show_results$"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^share_mirror$"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^full_description$"))
    
    # Интимный профиль
    app.add_handler(CallbackQueryHandler(my_sexual_profile_callback, pattern="^my_sexual_profile$"))
    app.add_handler(CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"))
    app.add_handler(CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"))
    
    # Приглашения
    app.add_handler(CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"))
    app.add_handler(CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^check_"))
    
    # Профиль друга
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
    
    # Доступ к другу
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^pay_access_"))
    
    print("\n🚀 Бот запущен!")
    print("\n📱 ТЕСТОВЫЙ МАРШРУТ:")
    print("  /start → 🔞 Sex → 🔞 СОЗДАТЬ")
    print("  → 🔍 МОИ → 👤 @alex")
    print("  → 🧬 4F → 🔥 1F - 1₽ → 💳 ОПЛАТИТЬ 1₽")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
