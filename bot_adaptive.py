#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 8.0-final - ВИЗУАЛ И НАВИГАЦИЯ
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
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
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
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>

🧬 <b>4F — это система доступа к состояниям человека</b>
Четыре базовые реакции, зашитые в подкорке.
Ключи к пониманию глубинных состояний другого человека.

1F 🔥 <b>НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Как гасить агрессию и не нарваться
└ <i>Ключ к управлению гневом</i>

2F 🏃 <b>БЕГСТВО / СТРАХ</b>
└ Чего он боится на самом деле
└ <i>Ключ к преодолению страхов</i>

3F 🧬 <b>СЕКС / ЖЕЛАНИЕ</b>
└ Что включает его режим «хочу»
└ <i>Ключ к желанию и страсти</i>

4F 🍽 <b>ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Какие идеи прорастают в его голове
└ <i>Ключ к деньгам и идеям</i>

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
Вы не соблазняете — вы ОТКРЫВАЕТЕ.
Ваша сексуальность — это приглашение в путешествие.

Вас возбуждает не тело, а ПРОЦЕСС:
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
            "«Ты можешь заработать на этом»",
            "«Это твой шанс»",
            "«Никто не сделает это лучше тебя»",
            "«Представь, сколько это будет стоить через год»",
            "«Я верю в твою идею»"
        ]
    }
    
    base_analysis = {
        "1F": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита. Не обесценивайте, не спорьте, признайте право на злость.",
        "2F": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя от того, с чем сейчас не справиться.",
        "3F": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес. Дразните, но не дразнитесь.",
        "4F": "Желание заработать — это не про жадность, а про безопасность, статус, свободу. Найдите его «голод» и предложите способ насытиться."
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
        [InlineKeyboardButton("🔞 Интимный профиль 18", callback_data="my_sexual_profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ 18
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль 18"""
    query = update.callback_query
    await query.answer()
    
    user_name = query.from_user.first_name or "Пользователь"
    profile_data = load_intimate_profile()
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ 18</b>
<b>{user_name}</b>

📊 <b>Тип:</b> <code>{profile_data['profile_type']}</code>
🧠 <b>Архетип:</b> {profile_data['archetype']}

💬 <b>ЦИТАТА:</b>
{profile_data['quote']}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data['description']}

🔮 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы видите только СВОЁ отражение.
Но у каждого друга — своя тайна.
Свои сценарии. Свои триггеры. Свои желания.

⬇️ <b>КАК УВИДЕТЬ ИХ:</b>

1️⃣ Нажмите <b>«🔞 СОЗДАТЬ ССЫЛКУ»</b>
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО профиль и интимные подробности

💫 <i>Чем больше друзей увидят себя в зеркале —
   тем больше тайн откроется вам.</i>
"""
    
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
# 🔗 ЭКРАН 3: СОЗДАНИЕ ССЫЛКИ (НОВЫЙ ДИЗАЙН)
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    query = update.callback_query
    await query.answer("🔗 Создаю ссылку...")
    
    profile = context.user_data.get("profile", USER_PROFILE)
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://{BOT_LINK}?start={invite_code}"
    
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "Я меня — совпало процентов на 90.\n"
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
🔗 <b>ВАША ССЫЛКА ГОТОВА</b>

💬 <b>ТЕКСТ СООБЩЕНИЯ:</b>

<code>{invite_message}</code>

🟢 · · · АКТИВНО · · · ждёт друга
⏳ Создано: {created_time}

✨ ЧЕРЕЗ 15 МИНУТ ПОСЛЕ ТЕСТА...
   Вы будете знать то, что знает о себе только он.
   А он даже не поймёт, как вы догадались.

⬇️ <b>ОСТАЛОСЬ ТОЛЬКО ОТПРАВИТЬ:</b>
"""
    
    keyboard = [
        [InlineKeyboardButton("🎁 ОТПРАВИТЬ ССЫЛКУ", url=share_url)],
        [InlineKeyboardButton("⬅️ Вернуться в 18", callback_data="my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: МОИ ОТРАЖЕНИЯ (ПОЧИНЕН!)
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 Мои отражения - список приглашений"""
    query = update.callback_query
    await query.answer()
    
    invites = context.user_data.get("sexual_invites", [])
    
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    message = f"""
🔍 <b>МОИ ОТРАЖЕНИЯ</b>

🔗 <b>ВСЕГО СОЗДАНО:</b> {len(invites)}
"""
    
    keyboard = []
    
    if active_invites:
        message += f"\n\n🟢 <b>ЖДУТ ОТКЛИКА ✨</b>"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
            days = int((datetime.now().timestamp() - inv["created_at"]) / 86400)
            message += f"\n   • {created} · ждёт {days}д"
            # Кнопка проверки статуса для каждой активной ссылки
            keyboard.append([
                InlineKeyboardButton(
                    f"🔄 Проверить статус ({inv['invite_id'][:8]}...)",
                    callback_data=f"check_status_{inv['invite_id']}"
                )
            ])
    
    if used_invites:
        message += f"\n\n✅ <b>ОТРАЗИЛИСЬ 🎉</b>"
        for inv in used_invites[:5]:
            friend_name = inv.get("friend_name", "друг")
            friend_profile = inv.get("friend_profile", "SA-3_CON")
            used_date = datetime.fromtimestamp(inv.get("used_at", inv["created_at"])).strftime('%d.%m.%Y')
            keys = ""
            if inv.get("purchased_functions"):
                keys = f" · 🔑 {' '.join(inv['purchased_functions'])}"
            
            message += f"\n\n   👤 {friend_name}"
            message += f"\n   📊 {friend_profile} · {used_date}{keys}"
            
            # Кнопка профиля друга
            if inv.get("friend_id"):
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 {friend_name}",
                        callback_data=f"friend_{inv['friend_id']}"
                    )
                ])
    
    keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")])
    keyboard.append([InlineKeyboardButton("⬅️ Вернуться в 18", callback_data="my_sexual_profile")])
    
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
🔍 <b>СТАТУС ПРИГЛАШЕНИЯ</b>

🔗 <code>https://{BOT_LINK}?start={invite_id}</code>

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
# 👤 ЭКРАН 6: МЕНЮ ПРОФИЛЯ ДРУГА (С 4F)
# ============================================

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 МЕНЮ ПРОФИЛЯ ДРУГА"""
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
    
    purchased = friend_data.get("purchased_functions", [])
    progress = len(purchased)
    progress_bar = "▓" * progress + "░" * (4 - progress)
    
    message = f"""
👤 <b>{friend_name}</b>

📊 <code>{friend_profile}</code>
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
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 <b>{friend_name} ЗАБЛОКИРОВАН</b>

📊 <code>{friend_profile}</code>

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
# 📊 ЭКРАН 8: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
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

⏳ <i>Скоро здесь будет его интимный профиль.</i>
   Мы работаем над персонализацией.
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
# 🧬 ЭКРАН 10: МЕНЮ 4F-КЛЮЧЕЙ
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ 4F-КЛЮЧЕЙ"""
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
    
    hot_hint = "\n🔥 <b>ХИТ ПРОДАЖ:</b> 1F покупают в 2 раза чаще"
    
    message = f"""
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>

📊 <code>{friend_profile}</code>
{hot_hint if not purchased else ""}

1F 🔥 <b>{FOUR_F_TITLES['1F']}</b>
└ {FOUR_F_SUBTITLES['1F']}
└ ⚡ Например: боится, что его используют, поэтому нападает первым

2F 🏃 <b>{FOUR_F_TITLES['2F']}</b>
└ {FOUR_F_SUBTITLES['2F']}
└ ⚡ Например: избегает конфликтов, потому что в детстве за них наказывали

3F 🧬 <b>{FOUR_F_TITLES['3F']}</b>
└ {FOUR_F_SUBTITLES['3F']}
└ ⚡ Например: его заводит, когда партнёр берёт инициативу

4F 🍽 <b>{FOUR_F_TITLES['4F']}</b>
└ {FOUR_F_SUBTITLES['4F']}
└ ⚡ Например: загорается идеей, где можно быстро заработать
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
<i>{content['subtitle']}</i>

👤 <b>Друг:</b> {friend_name}
📊 <b>Профиль:</b> <code>{friend_profile}</code>

{content['description']}

💰 <b>Цена:</b> 1₽ (тестовый режим)
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

✅ Нажмите кнопку для оплаты
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
<i>{content['subtitle']}</i>

🎯 <b>ТРИГГЕР-ФРАЗЫ:</b>
"""
    
    for i, trigger in enumerate(content['triggers'][:3], 1):
        message += f"\n{i}. {trigger}"
    
    message += f"""

🧠 <b>ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{content['analysis']}

📋 <b>ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{content['protocol']}

<i>«{content['tag']}»</i>

👇 <b>ЧТО ДАЛЬШЕ?</b>
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
            return await open_4f_key_callback(update, context)
    else:
        await query.answer("✅ Демо-режим")
    
    return RESULTS_SCREEN

# ============================================
# 🚀 ЗАПУСК
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ 18 И 4F-КЛЮЧИ v8.0")
    print("="*60)
    print("✅ Кнопка: «🔞 Интимный профиль 18»")
    print("✅ В профиле: имя пользователя")
    print("✅ Кнопка: «🔞 СОЗДАТЬ ССЫЛКУ»")
    print("✅ Экран ссылки: БЕЗ ЛИНИЙ, БЕЗ «МОИ ОТРАЖЕНИЯ»")
    print("✅ Кнопка: «🎁 ОТПРАВИТЬ ССЫЛКУ»")
    print("✅ Кнопка: «⬅️ Вернуться в 18»")
    print("✅ «МОИ ОТРАЖЕНИЯ»: ПОЧИНЕНЫ!")
    print("✅ Статус: · · · АКТИВНО · · · ждёт друга")
    print("✅ 4F: в профиле друга (понятное место)")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
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
    app.add_handler(CallbackQueryHandler(check_status_callback, pattern="^check_status_"))
    
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
    
    print("\n🚀 Бот запущен! ВСЁ ИСПРАВЛЕНО ✅")
    print("\n📱 ПРОВЕРЬ:")
    print("  • «МОИ ОТРАЖЕНИЯ» — РАБОТАЕТ!")
    print("  • В экране ссылки ТОЛЬКО «ОТПРАВИТЬ» и «Вернуться»")
    print("  • Нет лишних линий")
    print("  • Кнопка «🎁 ОТПРАВИТЬ ССЫЛКУ»")
    print("  • 4F — в профиле друга")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
