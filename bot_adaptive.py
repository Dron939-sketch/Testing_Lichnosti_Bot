#!/usr/bin/env python3
"""
ПРОТОТИП: НОВАЯ НАВИГАЦИЯ И 4F-КЛЮЧИ
Версия: 4.0-prototype
Фокус: Результаты → Интимный профиль → Приглашения → Друзья → 4F
Запуск: python prototype.py

СТРУКТУРА ЗАГЛУШЕК:
- Интимный профиль: sexual_18/sa_5_int.json
- Стандартный профиль друга: profiles/ip/ip_6_aut.py  
- 4F-ключи: profiles/4F/*/*.json
"""

import logging
import os
import uuid
import json
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

# ===== КОНСТАНТЫ =====
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 99
FOUR_F_BUNDLE_PRICE = 299

# ===== ПРАВИЛЬНЫЕ 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {
    "1F": "🔥",
    "2F": "🏃", 
    "3F": "🧬",
    "4F": "🍽"
}

FOUR_F_TITLES = {
    "1F": "КЛЮЧ НАПАДЕНИЯ / БЕЙ",
    "2F": "КЛЮЧ БЕГСТВА / ИЗБЕГАНИЕ",
    "3F": "КЛЮЧ СПАРИВАНИЯ / СЕКС",
    "4F": "КЛЮЧ ПОГЛОЩЕНИЯ / СЫТОСТЬ"
}

FOUR_F_DESCRIPTIONS = {
    "1F": "Что его бесит, пугает, заставляет защищаться",
    "2F": "От чего он убегает, чего избегает",
    "3F": "Что его включает, возбуждает, привлекает",
    "4F": "Что дает безопасность, насыщение, покой"
}

FOUR_F_TAGS = {
    "1F": "Ключ к страхам и границам",
    "2F": "Ключ к травмам и триггерам",
    "3F": "Ключ к желанию и страсти",
    "4F": "Ключ к доверию и близости"
}

# ===== ТЕКСТ ОБУЧАЙКИ 4F =====
FOUR_F_EXPLANATION = """
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>

🧬 <b>4F - это рептилоидная система мозга</b>
Четыре базовые реакции выживания, зашитые в подкорке.
Ключи доступа к глубинным состояниям другого человека.

────────────────────

🔥 <b>1F - БЕЙ / НАПАДЕНИЕ</b>
└ Что ВКЛЮЧАЕТ агрессию, защиту, нападение
└ Чего человек боится, что его злит
└ <i>Ключ к страхам и границам</i>

🏃 <b>2F - БЕГИ / ИЗБЕГАНИЕ</b>
└ Что ВЫКЛЮЧАЕТ, заставляет убегать
└ Какие темы, люди, ситуации пугают
└ <i>Ключ к травмам и триггерам</i>

🧬 <b>3F - СПАРИВАЙСЯ / СЕКС</b>
└ Что ВКЛЮЧАЕТ сексуальность и влечение
└ Слова, касания, контекст, сценарии
└ <i>Ключ к желанию и страсти</i>

🍽 <b>4F - ПОГЛОЩАЙ / СЫТОСТЬ</b>
└ Что дает ощущение БЕЗОПАСНОСТИ
└ Что насыщает, успокаивает, расслабляет
└ <i>Ключ к доверию и близости</i>

────────────────────
💰 <b>СТОИМОСТЬ:</b>
• Один ключ: 99₽
• Набор 4 ключа: 299₽ (экономия 97₽)
"""

# ===== ЗАГРУЗКА ПРОФИЛЕЙ (ЗАГЛУШКИ) =====
def load_intimate_profile() -> dict:
    """Загружает интимный профиль из sexual_18/sa_5_int.json"""
    try:
        # Для прототипа возвращаем заглушку
        return {
            "profile_type": "SA-5_INT",
            "archetype": "Первооткрыватель · Эстет · Соблазнитель",
            "role": "Тот, кто разжигает интерес",
            "quote": "«Со мной не скучно. Со мной — вкусно.»",
            "description": """
Вы не соблазняете — вы <b>ОТКРЫВАЕТЕ</b>.
Ваша сексуальность — это приглашение в путешествие.
Партнёр чувствует: с вами он станет кем-то другим.
Кем-то, кого сам в себе ещё не встречал.

Вас возбуждает не тело, а <b>ПРОЦЕСС</b>:
▪️ Как меняется взгляд
▪️ Как тают барьеры
▪️ Как запретное становится желанным

Вы — проводник в неизведанное.
И это ваш главный афродизиак.
"""
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки интимного профиля: {e}")
        return {
            "profile_type": "SA-5_INT",
            "archetype": "Первооткрыватель",
            "role": "Соблазнитель",
            "quote": "«Со мной не скучно.»",
            "description": "Ваш интимный профиль"
        }

def load_friend_standard_profile() -> dict:
    """Загружает стандартный профиль друга из profiles/ip/ip_6_aut.py"""
    try:
        # Для прототипа возвращаем заглушку
        return {
            "archetype": "Автономный стратег",
            "quote": "«Я не ищу одобрения — я ищу эффективность.»",
            "pain": """
Вам сложно делегировать. 
Вы уверены: «Хочешь сделать хорошо — сделай сам».
Но это приводит к выгоранию и одиночеству в решениях.
""",
            "immediate_tool": """
Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.
Не контролируйте, не проверяйте, не исправляйте.
Просто примите, что результат может быть другим.
""",
            "cta": """
Исследуйте баланс между автономией и доверием.
Ваша сила — в способности действовать самому.
Ваш рост — в способности доверять другим.
"""
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки стандартного профиля: {e}")
        return {
            "archetype": "Автономный стратег",
            "quote": "«Я сделаю сам.»",
            "pain": "Сложно делегировать",
            "immediate_tool": "Передайте одну задачу",
            "cta": "Учитесь доверять"
        }

def load_4f_content(function: str, profile: str = "sa_4_cap") -> dict:
    """Загружает контент 4F-ключа из profiles/4F/*/*.json"""
    try:
        # Для прототипа возвращаем заглушку
        base_content = {
            "1F": {
                "triggers": [
                    "«Я понимаю, почему ты так реагируешь»",
                    "«Ты имеешь полное право злиться»",
                    "«Я на твоей стороне»",
                    "«Это действительно несправедливо»",
                    "«Твои границы — это важно»"
                ],
                "analysis": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита. Не обесценивайте, не спорьте, признайте право на злость.",
                "protocol": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите\n4. Дайте время"
            },
            "2F": {
                "triggers": [
                    "«Ты не обязан это делать»",
                    "«Здесь безопасно»",
                    "«Я подожду»",
                    "«Ты можешь уйти в любой момент»",
                    "«Никакого давления»"
                ],
                "analysis": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя от того, с чем сейчас не справиться.",
                "protocol": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте\n4. Верните контроль"
            },
            "3F": {
                "triggers": [
                    "«Ты такой...» (искренний комплимент)",
                    "Взгляд в глаза чуть дольше обычного",
                    "«А что ты любишь?» (интерес к желаниям)",
                    "Случайное касание, которое не прерывают",
                    "Шёпот, интимный контекст"
                ],
                "analysis": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес. Дразните, но не дразнитесь.",
                "protocol": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы\n4. Усиливайте напряжение"
            },
            "4F": {
                "triggers": [
                    "«Я никуда не уйду»",
                    "«Ты можешь расслабиться»",
                    "Знакомый запах, уютное место",
                    "Ритуалы: чай, плед, тишина вдвоём",
                    "Прикосновения без ожиданий"
                ],
                "analysis": "Насыщение — это про безопасность. Человек закрывает базовую потребность в «сытости». Когда страшно — ищет еду, тепло, знакомое.",
                "protocol": "1. Создайте стабильность\n2. Уберите неожиданности\n3. Кормите буквально и метафорически\n4. Не требуйте отдачи"
            }
        }
        
        return {
            "function": function,
            "emoji": FOUR_F_EMOJIS[function],
            "title": FOUR_F_TITLES[function],
            "description": FOUR_F_DESCRIPTIONS[function],
            "tag": FOUR_F_TAGS[function],
            "triggers": base_content[function]["triggers"],
            "analysis": base_content[function]["analysis"],
            "protocol": base_content[function]["protocol"],
            "is_demo": False
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки 4F-контента: {e}")
        return {
            "function": function,
            "emoji": FOUR_F_EMOJIS.get(function, "🔑"),
            "title": FOUR_F_TITLES.get(function, f"КЛЮЧ {function}"),
            "description": FOUR_F_DESCRIPTIONS.get(function, ""),
            "tag": FOUR_F_TAGS.get(function, ""),
            "triggers": ["Триггер 1", "Триггер 2", "Триггер 3"],
            "analysis": "Психологический разбор",
            "protocol": "Протокол применения",
            "is_demo": True
        }

# ===== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =====
USER_PROFILE = {
    "display_name": "SA-5_INT",
    "type_code": "SA",
    "level": 5,
    "dilts_code": "int",
    "level_name": "ИНТЕГРАТИВНЫЙ",
    "type_name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"
}

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====
user_invites = {}  # user_id -> list of invites

def get_user_invites(user_id: int) -> list:
    """Получить приглашения пользователя"""
    if user_id not in user_invites:
        user_invites[user_id] = []
    return user_invites[user_id]

def count_free_friends(user_id: int) -> int:
    """Считает количество БЕСПЛАТНЫХ активированных друзей"""
    invites = get_user_invites(user_id)
    free_used = [
        inv for inv in invites 
        if inv.get("status") == "used" 
        and inv.get("access_status") == "free"
    ]
    return len(free_used)

def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    invites = get_user_invites(user_id)
    
    if len(invites) >= 2:
        return
    
    test_friends = [
        {
            "invite_id": f"test_free_1_{user_id}",
            "friend_id": 1001,
            "friend_name": "@alex_free",
            "friend_username": "alex_free",
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
            "friend_name": "@maria_free",
            "friend_username": "maria_free",
            "friend_profile": "IP-5_INT",
            "status": "used",
            "access_status": "free",
            "access_paid": False,
            "used_at": datetime.now().timestamp() - 86400,
            "purchased_functions": ["1F"]
        }
    ]
    
    invites.extend(test_friends)
    logger.info(f"✅ Добавлены тестовые друзья для {user_id}")

# ============================================
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ ТЕСТА (СТАРТОВЫЙ)
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота - сразу показываем экран результатов"""
    user = update.effective_user
    
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    context.user_data["profile"] = USER_PROFILE.copy()
    
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    profile = context.user_data.get("profile", USER_PROFILE)
    
    message = f"""
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>

📊 <b>{profile['display_name']}</b>
<i>{profile['level_name']} · {profile['type_name']}</i>

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 <b>ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>
Сегодня: попросите кого-то о маленькой услуге.
Заметьте, что мир не рухнул.

────────────────────
<b>ЧТО ДАЛЬШЕ?</b>
"""
    
    keyboard = [
        [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="share_mirror")],
        [InlineKeyboardButton("📖 Полное описание профиля", callback_data="full_description")],
        [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
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
    """🔞 Мой интимный профиль"""
    query = update.callback_query
    await query.answer()
    
    profile_data = load_intimate_profile()
    free_count = count_free_friends(query.from_user.id)
    invites = context.user_data.get("sexual_invites", [])
    used_friends = [inv for inv in invites if inv.get("status") == "used"]
    
    # Формируем список друзей для отображения
    friends_list = ""
    for friend in used_friends[:3]:  # Показываем максимум 3 друзей
        friend_name = friend.get("friend_name", "друг")
        friend_profile = friend.get("friend_profile", "SA-3_CON")
        keys = ""
        if friend.get("purchased_functions"):
            keys = f" · 🔑 {' '.join(friend['purchased_functions'])}"
        friends_list += f"\n   👤 {friend_name} · {friend_profile}{keys}"
    
    limit_status = ""
    if free_count >= FREE_FRIEND_LIMIT:
        limit_status = f"\n\n💎 <b>Бесплатный лимит:</b> {free_count}/{FREE_FRIEND_LIMIT} · ИСЧЕРПАН\n   Следующий друг: {FRIEND_ACCESS_PRICE}₽ за доступ"
    
    message = f"""
🔞 <b>ВАШ ИНТИМНЫЙ ПРОФИЛЬ</b>

📊 <b>Тип:</b> <code>{profile_data['profile_type']}</code>
🧠 <b>Архетип:</b> {profile_data['archetype']}
🎭 <b>Роль:</b> {profile_data['role']}

💬 <b>ЦИТАТА:</b>
{profile_data['quote']}

────────────────────
🧠 <b>ВАША ПРИРОДА:</b>
{profile_data['description']}

────────────────────
🔗 <b>ХОТИТЕ УВИДЕТЬ ИНТИМНЫЙ ПРОФИЛЬ ДРУГА?</b>

Сейчас вы видите <b>СВОЙ</b> профиль.
Чтобы открыть <b>ЧУЖОЙ</b> — нужно зеркало с той стороны.

⬇️ <b>КАК ЭТО РАБОТАЕТ:</b>

1️⃣ Нажмите <b>«🔞 Создать приглашение»</b>
2️⃣ Отправьте ссылку другу
3️⃣ Друг проходит тест → вам открывается ЕГО интимный профиль
4️⃣ Бесплатно: первые 2 друга
5️⃣ 3+ друг: {FRIEND_ACCESS_PRICE}₽ за доступ к профилю
{limit_status}

💎 <b>УЖЕ ЕСТЬ АКТИВИРОВАННЫЕ ДРУЗЬЯ:</b>{friends_list if friends_list else "\n   Пока нет активированных друзей"}

────────────────────
💡 <i>Чем больше друзей увидят себя в зеркале —
   тем больше интимных профилей откроется вам.</i>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 СОЗДАТЬ ПРИГЛАШЕНИЕ", callback_data="create_invite")],
        [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="my_invites")],
        [
            InlineKeyboardButton("⬅️ К РЕЗУЛЬТАТАМ", callback_data="back_to_results"),
            InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
        ]
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
    """🔞 Создание ссылки-приглашения (без кнопки копировать)"""
    query = update.callback_query
    await query.answer("🔗 Создаю ссылку...")
    
    profile = context.user_data.get("profile", USER_PROFILE)
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
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

💬 <b>СООБЩЕНИЕ ДЛЯ ДРУГА:</b>

<code>{invite_message}</code>

────────────────────
🟢 <b>СТАТУС:</b> ССЫЛКА АКТИВНА · ждет друга
⏳ <b>Создана:</b> {created_time}

────────────────────
⬇️ <b>ОСТАЛОСЬ ТОЛЬКО ОТПРАВИТЬ:</b>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 ОТПРАВИТЬ ДРУГУ (Telegram)", url=share_url)],
        [
            InlineKeyboardButton("🔄 ПРОВЕРИТЬ СТАТУС", callback_data=f"check_{invite_code}"),
            InlineKeyboardButton("🔍 ВСЕ ПРИГЛАШЕНИЯ", callback_data="my_invites")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: СПИСОК ПРИГЛАШЕНИЙ (МИНИМАЛИЗМ)
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 Список всех приглашений - чистый, без лишнего"""
    query = update.callback_query
    await query.answer()
    
    invites = context.user_data.get("sexual_invites", [])
    
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    message = f"""
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>

🔗 <b>ССЫЛОК СОЗДАНО:</b> {len(invites)}
────────────────────
"""
    
    # АКТИВНЫЕ - ждут друга
    if active_invites:
        message += "\n🟢 <b>АКТИВНЫЕ · ждут друга</b>"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
            days = int((datetime.now().timestamp() - inv["created_at"]) / 86400)
            message += f"\n   • {created} · ссылка active · ожидание {days}д"
    
    # АКТИВИРОВАННЫЕ - друзья
    if used_invites:
        message += "\n\n✅ <b>АКТИВИРОВАННЫЕ · друзья</b>"
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
    
    # Кнопки для каждого активированного друга
    for inv in used_invites[:5]:
        friend_name = inv.get("friend_name", "друг")
        friend_id = inv.get("friend_id")
        if friend_id:
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 ПРОФИЛЬ {friend_name}",
                    callback_data=f"friend_{friend_id}"
                )
            ])
    
    # Кнопки управления
    keyboard.append([InlineKeyboardButton("🔞 СОЗДАТЬ НОВОЕ", callback_data="create_invite")])
    keyboard.append([
        InlineKeyboardButton("⬅️ К ИНТИМНОМУ", callback_data="my_sexual_profile"),
        InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

# ============================================
# 👤 ЭКРАН 5: МЕНЮ ПРОФИЛЯ ДРУГА
# ============================================

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 МЕНЮ ВЫБОРА ПРОФИЛЯ ДРУГА"""
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
    
    # Если друг платный (3+) и доступ не оплачен
    if access_status == "locked" or (free_count >= FREE_FRIEND_LIMIT and not friend_data.get("access_paid")):
        return await show_payment_access_screen(update, context, friend_data)
    
    message = f"""
👤 <b>ПРОФИЛЬ {friend_name}</b>

📊 <b>Тип профиля:</b> <code>{friend_profile}</code>
💎 <b>Статус:</b> {'🔓 БЕСПЛАТНО' if access_status == 'free' else '💰 ОПЛАЧЕН'}

────────────────────
<b>ВЫБЕРИТЕ, ЧТО ХОТИТЕ ОТКРЫТЬ:</b>
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton(
            f"📊 СТАНДАРТНЫЙ ПРОФИЛЬ {friend_name}",
            callback_data=f"std_{friend_id}"
        )],
        [InlineKeyboardButton(
            f"🔞 ИНТИМНЫЙ ПРОФИЛЬ {friend_name}",
            callback_data=f"int_{friend_id}"
        )],
        [InlineKeyboardButton(
            f"🧬 4F-КЛЮЧИ ДЛЯ {friend_name}",
            callback_data=f"4f_{friend_id}"
        )],
        [InlineKeyboardButton(
            "📘 ЧТО ТАКОЕ 4F?",
            callback_data="4f_explain"
        )],
        [
            InlineKeyboardButton("⬅️ К ПРИГЛАШЕНИЯМ", callback_data="my_invites"),
            InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FRIEND_MENU

# ============================================
# 💰 ЭКРАН 6: ОПЛАТА ДОСТУПА К ПЛАТНОМУ ДРУГУ
# ============================================

async def show_payment_access_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_data: dict):
    """💰 Разблокировка платного друга (3+ друг)"""
    query = update.callback_query
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 <b>ПРОФИЛЬ {friend_name} ЗАБЛОКИРОВАН</b>

📊 <b>Профиль:</b> <code>{friend_profile}</code>

⚠️ <b>БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН</b>
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽

────────────────────
💰 <b>РАЗБЛОКИРОВКА ПРОФИЛЯ:</b>
   • Стоимость: {FRIEND_ACCESS_PRICE}₽ (разово)
   • Стандартный профиль
   • Интимный профиль
   • Покупка 4F-ключей

💎 <b>Это платёж ЗА ДОСТУП К ПРОФИЛЮ</b>
   Ключи 1F,2F,3F,4F оплачиваются отдельно
────────────────────
"""
    
    keyboard = [
        [InlineKeyboardButton(
            f"🔓 РАЗБЛОКИРОВАТЬ - {FRIEND_ACCESS_PRICE}₽",
            callback_data=f"pay_access_{friend_data['friend_id']}"
        )],
        [InlineKeyboardButton("⬅️ К ПРИГЛАШЕНИЯМ", callback_data="my_invites")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return PAYMENT_SCREEN

# ============================================
# 📊 ЭКРАН 7: СТАНДАРТНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга (из ip_6_aut.py)"""
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
📊 <b>СТАНДАРТНЫЙ ПРОФИЛЬ {friend_name}</b>

🧠 <b>Архетип:</b> {profile['archetype']}

💬 <b>ЦИТАТА:</b>
{profile['quote']}

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
{profile['pain']}

🛠 <b>ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>
{profile['immediate_tool']}

🚀 <b>СЛЕДУЮЩИЕ ШАГИ</b>
{profile['cta']}
────────────────────
"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"⬅️ К ВЫБОРУ ПРОФИЛЯ {friend_name}",
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
# 🔞 ЭКРАН 8: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА (ЗАГЛУШКА)
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга (заглушка)"""
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
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ {friend_name}</b>

📊 <b>Тип профиля:</b> <code>{friend_profile}</code>

⏳ <i>Полное описание интимного профиля появится позже.</i>
<i>Сейчас мы работаем над персонализацией.</i>

────────────────────
"""
    
    keyboard = [[
        InlineKeyboardButton(
            f"⬅️ К ВЫБОРУ ПРОФИЛЯ {friend_name}",
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
# 🧬 ЭКРАН 9: МЕНЮ 4F-КЛЮЧЕЙ
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ ВЫБОРА 4F-КЛЮЧЕЙ"""
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

📊 <b>Профиль:</b> <code>{friend_profile}</code>

────────────────────
<b>РЕПТИЛОИДНАЯ СИСТЕМА ДРУГА:</b>
────────────────────
"""
    
    keyboard = []
    
    for f in ["1F", "2F", "3F", "4F"]:
        emoji = FOUR_F_EMOJIS[f]
        title = FOUR_F_TITLES[f]
        desc = FOUR_F_DESCRIPTIONS[f]
        tag = FOUR_F_TAGS[f]
        
        message += f"\n{emoji} <b>{title}</b>"
        message += f"\n└ {desc}"
        message += f"\n└ <i>{tag}</i>"
        
        if f in purchased:
            message += f"\n└ ✅ КУПЛЕНО"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {f} - ОТКРЫТЬ",
                    callback_data=f"open_4f_{friend_id}_{f}"
                )
            ])
        else:
            message += f"\n└ 💰 {FOUR_F_PRICE}₽"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {f} - {FOUR_F_PRICE}₽",
                    callback_data=f"buy_4f_{friend_id}_{f}"
                )
            ])
    
    message += f"\n\n────────────────────"
    message += f"\n🎁 <b>НАБОР 4 КЛЮЧА:</b> {FOUR_F_BUNDLE_PRICE}₽ (экономия 97₽)"
    message += f"\n────────────────────"
    
    keyboard.append([
        InlineKeyboardButton(
            "🎁 КУПИТЬ НАБОР",
            callback_data=f"bundle_{friend_id}"
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            "📘 ЧТО ТАКОЕ 4F?",
            callback_data="4f_explain"
        ),
        InlineKeyboardButton(
            f"⬅️ К ПРОФИЛЮ {friend_name}",
            callback_data=f"friend_{friend_id}"
        )
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

# ============================================
# 📘 ЭКРАН 10: ОБУЧАЙКА 4F (УМНЫЙ НАЗАД)
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ПОДРОБНОЕ ОБЪЯСНЕНИЕ 4F-СИСТЕМЫ"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["4f_explanation_source"] = query.data
    
    message = FOUR_F_EXPLANATION
    
    keyboard = []
    
    friend_id = context.user_data.get("current_friend_id")
    friend_data = context.user_data.get("current_friend_data", {})
    friend_name = friend_data.get("friend_name", "друг") if friend_data else "друг"
    
    if "friend_" in query.data or friend_id:
        keyboard.append([
            InlineKeyboardButton(
                f"⬅️ К ПРОФИЛЮ {friend_name}",
                callback_data=f"friend_{friend_id}" if friend_id else "my_invites"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "⬅️ К ВЫБОРУ КЛЮЧЕЙ",
                callback_data=f"4f_{friend_id}" if friend_id else "my_invites"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

# ============================================
# 🔑 ЭКРАН 11: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТИЕ КУПЛЕННОГО 4F-КЛЮЧА"""
    query = update.callback_query
    await query.answer("🔓 Открываю ключ...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    content = load_4f_content(function)
    
    message = f"""
{content['emoji']} <b>{content['title']}</b>

<i>Для профиля SA-4_CAP «@friend»</i>

────────────────────

🎯 <b>ТОЧНЫЕ ТРИГГЕР-ФРАЗЫ:</b>
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
        [InlineKeyboardButton(
            "⬅️ К ВЫБОРУ КЛЮЧЕЙ",
            callback_data=f"4f_{friend_id}"
        )],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_CONTENT

# ============================================
# 🏠 ГЛАВНОЕ МЕНЮ (ПОЛНЫЙ СБРОС)
# ============================================

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🏠 Полный сброс и возврат на старт"""
    query = update.callback_query
    await query.answer("🏠 Возврат в главное меню...")
    
    user_id = query.from_user.id
    
    context.user_data.clear()
    context.user_data["user_id"] = user_id
    context.user_data["profile"] = USER_PROFILE.copy()
    init_test_data(user_id)
    context.user_data["sexual_invites"] = get_user_invites(user_id)
    
    return await show_results_screen(update, context)

# ============================================
# ⬅️ КНОПКИ НАЗАД
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

# ============================================
# 🎭 ЗАГЛУШКИ ДЛЯ ДЕМО-ФУНКЦИЙ
# ============================================

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для демо-функций"""
    query = update.callback_query
    pattern = query.data
    
    if pattern.startswith("check_"):
        await query.answer("🟢 Ссылка активна, друг еще не прошел тест")
    elif pattern.startswith("buy_4f_"):
        await query.answer("💳 Демо-режим: оплата 99₽")
    elif pattern.startswith("bundle_"):
        await query.answer("🎁 Демо-режим: набор 299₽")
    elif pattern.startswith("pay_access_"):
        await query.answer("💰 Демо-режим: оплата доступа 99₽")
    elif pattern == "share_mirror":
        await query.answer("🪞 Скоро здесь будет подарок")
    elif pattern == "full_description":
        await query.answer("📖 Полное описание профиля — 690₽")
    else:
        await query.answer("✅ Демо-режим")
    
    return RESULTS_SCREEN

# ============================================
# 🚀 ЗАПУСК
# ============================================

def main():
    """Запуск прототипа"""
    print("\n" + "="*60)
    print("🧠 ПРОТОТИП: НОВАЯ НАВИГАЦИЯ И 4F-КЛЮЧИ")
    print("="*60)
    print("✅ Интимный профиль: sexual_18/sa_5_int.json")
    print("✅ Стандартный профиль: profiles/ip/ip_6_aut.py")
    print("✅ 4F-ключи: profiles/4F/*/*.json")
    print("✅ Бесплатный лимит: 2 друга")
    print("✅ Платный доступ: 99₽ (3+ друг)")
    print("✅ 4F-ключи: 99₽/ключ, 299₽/набор")
    print("="*60)
    print("❌ Кнопка 'Копировать' - УДАЛЕНА")
    print("✅ Только 'Отправить другу' в 1 клик")
    print("✅ Короткие разделители ────────────────────")
    print("✅ Чистый экран приглашений без лишнего")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("results", start))
    
    # Навигация
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
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
    app.add_handler(CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^buy_4f_"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^bundle_"))
    app.add_handler(CallbackQueryHandler(dummy_callback, pattern="^pay_access_"))
    
    print("\n🚀 Бот запущен! Тестируйте навигацию:")
    print("   /start → 🔞 Мой интимный профиль")
    print("   → 🔞 СОЗДАТЬ ПРИГЛАШЕНИЕ (без кнопки копировать)")
    print("   → 🔍 МОИ ПРИГЛАШЕНИЯ (чистый список)")
    print("   → 👤 ПРОФИЛЬ @alex_free")
    print("   → 🧬 4F-КЛЮЧИ ДЛЯ @alex_free")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
