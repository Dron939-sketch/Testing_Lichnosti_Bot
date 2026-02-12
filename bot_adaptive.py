#!/usr/bin/env python3
"""
ПРОТОТИП: НАВИГАЦИЯ С ЭКРАНА РЕЗУЛЬТАТОВ
Версия: 4.0-prototype
Фокус: Результаты → Интимный профиль → Приглашения → Друзья → 4F
Запуск: python results_prototype.py
"""

import logging
import os
import uuid
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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧬 <b>4F - это рептилоидная система мозга</b>
Четыре базовые реакции выживания, зашитые в подкорке.
Ключи доступа к глубинным состояниям другого человека.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>СТОИМОСТЬ:</b>
• Один ключ: 99₽
• Набор 4 ключа: 299₽ (экономия 97₽)
"""

# ===== МОК-ДАННЫЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ =====
USER_PROFILE = {
    "display_name": "SA_3_CON",
    "type_code": "SA",
    "level": 3,
    "dilts_code": "con",
    "level_name": "КОНСТРУКТИВНЫЙ",
    "type_name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"
}

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ (В ПАМЯТИ) =====
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

# ===== МОК-ДАННЫЕ ДЛЯ ТЕСТА =====
def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    invites = get_user_invites(user_id)
    
    # Если уже есть данные, не добавляем
    if len(invites) >= 2:
        return
    
    # Добавляем 2 бесплатных друзей
    test_friends = [
        {
            "invite_id": f"test_free_1_{user_id}",
            "friend_id": 1001,
            "friend_name": "@alex_free",
            "friend_username": "alex_free",
            "friend_profile": "SA_3_CON",
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
            "friend_profile": "IP_5_INT",
            "status": "used",
            "access_status": "free",
            "access_paid": False,
            "used_at": datetime.now().timestamp(),
            "purchased_functions": ["1F"]  # Мария уже купила 1F
        }
    ]
    
    invites.extend(test_friends)
    logger.info(f"✅ Добавлены тестовые друзья для {user_id}")

# ============================================
# 🎯 ЭКРАН 1: РЕЗУЛЬТАТЫ ТЕСТА (СТАРТОВЫЙ)
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота - сразу показываем экран результатов"""
    user = update.effective_user
    
    # Инициализируем данные пользователя
    context.user_data.clear()
    context.user_data["user_id"] = user.id
    context.user_data["profile"] = USER_PROFILE.copy()
    
    # Добавляем тестовых друзей
    init_test_data(user.id)
    context.user_data["sexual_invites"] = get_user_invites(user.id)
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🧠 ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА
    Стартовая точка прототипа
    """
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user = update.effective_user
    profile = context.user_data.get("profile", USER_PROFILE)
    
    # Формируем сообщение
    message = f"""
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>ЧТО ДАЛЬШЕ?</b>
"""
    
    # Кнопки навигации
    keyboard = [
        [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="share_mirror")],
        [InlineKeyboardButton("📖 Полное описание профиля", callback_data="full_description")],
        [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль"""
    query = update.callback_query
    await query.answer()
    
    profile = context.user_data.get("profile", USER_PROFILE)
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔞 <b>МОЙ ИНТИМНЫЙ ПРОФИЛЬ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>Тип:</b> <code>{profile['display_name']}</code>
🧠 <b>Конфигурация:</b> {profile['type_name']}
📈 <b>Уровень:</b> {profile['level_name']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💎 <b>БЕСПЛАТНЫЙ ЛИМИТ:</b> {free_count}/{FREE_FRIEND_LIMIT}
   {'🔴 ИСЧЕРПАН' if free_count >= FREE_FRIEND_LIMIT else '🟢 ЕСТЬ МЕСТО'}

👥 <b>Друзей активировано:</b> {free_count}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽ за доступ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 Создать приглашение", callback_data="create_invite")],
        [InlineKeyboardButton("🔍 Мои приглашения", callback_data="my_invites")],
        [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
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
    await query.answer("🔗 Создаю ссылку...")
    
    user = query.from_user
    profile = context.user_data.get("profile", USER_PROFILE)
    
    # Генерируем уникальную ссылку
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/YourBot?start={invite_code}"
    
    # Текст для отправки другу
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой тип личности.\n"
        "Я прошёл — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
    )
    
    # Сохраняем приглашение
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
    
    # Формируем сообщение
    message = f"""
🔗 <b>ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 <code>{invite_url}</code>

💬 <b>ТЕКСТ ДЛЯ ДРУГА:</b>
<code>{invite_message}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Ваш профиль:</b> {profile['display_name']}
🟢 <b>Статус:</b> Ожидает друга
"""
    
    share_url = f"https://t.me/share/url?url={invite_url}&text={invite_message}"
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Отправить другу", url=share_url),
            InlineKeyboardButton("📋 Копировать", callback_data=f"copy_{invite_code}")
        ],
        [
            InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_{invite_code}")
        ],
        [
            InlineKeyboardButton("🔍 Все приглашения", callback_data="my_invites"),
            InlineKeyboardButton("⬅️ Назад", callback_data="my_sexual_profile")
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
    """🔍 Список всех приглашений"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    invites = context.user_data.get("sexual_invites", [])
    free_count = count_free_friends(user_id)
    
    # Разделяем на активные и активированные
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    message = f"""
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 <b>БЕСПЛАТНЫЙ ЛИМИТ:</b> {free_count}/{FREE_FRIEND_LIMIT}
   {'🔴 ИСЧЕРПАН' if free_count >= FREE_FRIEND_LIMIT else f'🟢 Осталось {FREE_FRIEND_LIMIT - free_count}'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = []
    
    # АКТИВНЫЕ (ждут друга)
    if active_invites:
        message += "\n🟢 <b>АКТИВНЫЕ:</b>\n"
        for inv in active_invites[:3]:
            created = datetime.fromtimestamp(inv["created_at"]).strftime('%d.%m')
            message += f"  • Создана {created} · ожидание\n"
    
    # АКТИВИРОВАННЫЕ (друзья)
    if used_invites:
        message += "\n✅ <b>АКТИВИРОВАННЫЕ (ДРУЗЬЯ):</b>\n"
        
        for inv in used_invites:
            friend_name = inv.get("friend_name", "друг")
            friend_profile = inv.get("friend_profile", "SA_3_CON")
            access = "🔓 БЕСПЛАТНО" if inv.get("access_status") == "free" else "💰 ПЛАТНЫЙ"
            
            message += f"\n👤 <b>{friend_name}</b>\n"
            message += f"   📊 {friend_profile} · {access}\n"
            
            # КНОПКА ПРОФИЛЯ ДРУГА (всегда с именем!)
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 ПРОФИЛЬ {friend_name}",
                    callback_data=f"friend_{inv['friend_id']}"
                )
            ])
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton("🔞 Создать новое", callback_data="create_invite")
    ])
    keyboard.append([
        InlineKeyboardButton("⬅️ К интимному профилю", callback_data="my_sexual_profile"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
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
    
    # Парсим friend_id из callback
    friend_id = int(query.data.split("_")[1])
    
    # Ищем друга в данных
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return INVITES_LIST
    
    # Сохраняем контекст
    context.user_data["current_friend_id"] = friend_id
    context.user_data["current_friend_data"] = friend_data
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA_3_CON")
    access_status = friend_data.get("access_status", "free")
    free_count = count_free_friends(query.from_user.id)
    
    # ЕСЛИ ДРУГ ПЛАТНЫЙ (3+) - ПОКАЗЫВАЕМ ЭКРАН ОПЛАТЫ
    if access_status == "locked":
        return await show_payment_access_screen(update, context, friend_data)
    
    # ИНАЧЕ - ПОЛНОЕ МЕНЮ ВЫБОРА
    message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 <b>ПРОФИЛЬ {friend_name}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Тип профиля:</b> <code>{friend_profile}</code>
💎 <b>Статус:</b> {'🔓 БЕСПЛАТНО' if access_status == 'free' else '💰 ОПЛАЧЕН'}

<b>ВЫБЕРИТЕ, ЧТО ХОТИТЕ ОТКРЫТЬ:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = [
        # Стандартный профиль
        [InlineKeyboardButton(
            f"📊 СТАНДАРТНЫЙ ПРОФИЛЬ {friend_name}",
            callback_data=f"std_{friend_id}"
        )],
        # Интимный профиль
        [InlineKeyboardButton(
            f"🔞 ИНТИМНЫЙ ПРОФИЛЬ {friend_name}",
            callback_data=f"int_{friend_id}"
        )],
        # 4F-ключи
        [InlineKeyboardButton(
            f"🧬 4F-КЛЮЧИ ДЛЯ {friend_name}",
            callback_data=f"4f_{friend_id}"
        )],
        # Подробнее о 4F
        [InlineKeyboardButton(
            "📘 ЧТО ТАКОЕ 4F?",
            callback_data="4f_explain"
        )],
        # Навигация
        [
            InlineKeyboardButton(
                "⬅️ К ПРИГЛАШЕНИЯМ",
                callback_data="my_invites"
            ),
            InlineKeyboardButton(
                "🏠 ГЛАВНОЕ МЕНЮ",
                callback_data="main_menu"
            )
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
    """💰 Разблокировка платного друга"""
    query = update.callback_query
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA_3_CON")
    free_count = count_free_friends(query.from_user.id)
    
    message = f"""
🔒 <b>ПРОФИЛЬ {friend_name} ЗАБЛОКИРОВАН</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Профиль:</b> <code>{friend_profile}</code>

⚠️ <b>БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН</b>
   Использовано: {free_count}/{FREE_FRIEND_LIMIT}
   Следующий друг: {FRIEND_ACCESS_PRICE}₽

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>РАЗБЛОКИРОВКА ПРОФИЛЯ:</b>
   • Стоимость: {FRIEND_ACCESS_PRICE}₽ (разово)
   • Стандартный профиль
   • Интимный профиль
   • Покупка 4F-ключей

💎 <b>Это платёж ЗА ДОСТУП К ПРОФИЛЮ</b>
   Ключи 1F,2F,3F,4F оплачиваются отдельно
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = [
        [InlineKeyboardButton(
            f"🔓 РАЗБЛОКИРОВАТЬ - {FRIEND_ACCESS_PRICE}₽",
            callback_data=f"pay_access_{friend_data['friend_id']}"
        )],
        [InlineKeyboardButton(
            "⬅️ К ПРИГЛАШЕНИЯМ",
            callback_data="my_invites"
        )]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return PAYMENT_SCREEN

# ============================================
# 🧬 ЭКРАН 7: МЕНЮ 4F-КЛЮЧЕЙ
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ ВЫБОРА 4F-КЛЮЧЕЙ"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    
    # Ищем друга
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return INVITES_LIST
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA_3_CON")
    purchased = friend_data.get("purchased_functions", [])
    
    message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Профиль:</b> <code>{friend_profile}</code>

<b>РЕПТИЛОИДНАЯ СИСТЕМА ДРУГА:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = []
    
    # 4 функции
    for f in ["1F", "2F", "3F", "4F"]:
        emoji = FOUR_F_EMOJIS[f]
        title = FOUR_F_TITLES[f]
        desc = FOUR_F_DESCRIPTIONS[f]
        tag = FOUR_F_TAGS[f]
        
        message += f"\n{emoji} <b>{title}</b>\n"
        message += f"└ {desc}\n"
        message += f"└ <i>{tag}</i>\n"
        
        if f in purchased:
            message += f"└ ✅ КУПЛЕНО\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {f} - ОТКРЫТЬ",
                    callback_data=f"open_4f_{friend_id}_{f}"
                )
            ])
        else:
            message += f"└ 💰 {FOUR_F_PRICE}₽\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {f} - {FOUR_F_PRICE}₽",
                    callback_data=f"buy_4f_{friend_id}_{f}"
                )
            ])
    
    message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"🎁 <b>НАБОР 4 КЛЮЧА:</b> {FOUR_F_BUNDLE_PRICE}₽ (экономия 97₽)\n"
    
    # Кнопки управления
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
# 📘 ЭКРАН 8: ОБУЧАЙКА 4F (УМНЫЙ НАЗАД)
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ПОДРОБНОЕ ОБЪЯСНЕНИЕ 4F-СИСТЕМЫ"""
    query = update.callback_query
    await query.answer()
    
    # Запоминаем, откуда пришли
    context.user_data["4f_explanation_source"] = query.data
    
    message = FOUR_F_EXPLANATION
    
    # УМНАЯ КНОПКА НАЗАД
    keyboard = []
    
    friend_id = context.user_data.get("current_friend_id")
    friend_data = context.user_data.get("current_friend_data", {})
    friend_name = friend_data.get("friend_name", "друг") if friend_data else "друг"
    
    if "friend_" in query.data or friend_id:
        # Пришли из профиля друга
        keyboard.append([
            InlineKeyboardButton(
                f"⬅️ К ПРОФИЛЮ {friend_name}",
                callback_data=f"friend_{friend_id}"
            )
        ])
    else:
        # Пришли из меню 4F
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
# 🔑 ЭКРАН 9: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТИЕ КУПЛЕННОГО 4F-КЛЮЧА"""
    query = update.callback_query
    await query.answer("🔓 Открываю ключ...")
    
    parts = query.data.split("_")
    friend_id = int(parts[2])
    function = parts[3]
    
    # Демо-контент для ключа
    emoji = FOUR_F_EMOJIS[function]
    title = FOUR_F_TITLES[function]
    desc = FOUR_F_DESCRIPTIONS[function]
    tag = FOUR_F_TAGS[function]
    
    message = f"""
{emoji} <b>{title}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>Для профиля SA-3_CON «@friend»</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>ТОЧНЫЕ ТРИГГЕР-ФРАЗЫ:</b>

1. «Я понимаю, почему ты так реагируешь»
2. «Ты имеешь полное право злиться»
3. «Я на твоей стороне»

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 <b>ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{desc} Это проявляется в ситуациях,
когда человек чувствует угрозу своим границам.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 <b>ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
1. Заметьте триггер
2. Не обесценивайте реакцию
3. Дайте время на восстановление

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<i>«{tag}»</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
    
    # Полный сброс состояния
    context.user_data.clear()
    
    # Инициализируем заново
    context.user_data["user_id"] = query.from_user.id
    context.user_data["profile"] = USER_PROFILE.copy()
    init_test_data(query.from_user.id)
    context.user_data["sexual_invites"] = get_user_invites(query.from_user.id)
    
    return await show_results_screen(update, context)

# ============================================
# ⬅️ КНОПКИ НАЗАД
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def back_to_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к интимному профилю"""
    query = update.callback_query
    await query.answer()
    return await my_sexual_profile_callback(update, context)

# ============================================
# 🎭 ЗАГЛУШКИ ДЛЯ КОНТЕНТА
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль (заглушка)"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_name = "друг"
    
    # Ищем имя друга
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "друг")
            break
    
    message = f"""
📊 <b>СТАНДАРТНЫЙ ПРОФИЛЬ {friend_name}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 <b>Архетип:</b> Исследователь
💬 <b>Цитата:</b> «Я не ищу — я нахожу»
💔 <b>Суть проблемы:</b> Сложно просить о помощи
🛠 <b>Инструмент:</b> Попросить о маленькой услуге
🚀 <b>Следующие шаги:</b> Замечать свои потребности

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль (заглушка)"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    friend_name = "друг"
    friend_profile = "SA_3_CON"
    
    # Ищем данные друга
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "друг")
            friend_profile = inv.get("friend_profile", "SA_3_CON")
            break
    
    message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ {friend_name}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>Тип профиля:</b> <code>{friend_profile}</code>

⏳ <i>Полное описание интимного профиля появится позже.</i>
<i>Сейчас мы работаем над персонализацией.</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
# 🚀 ЗАПУСК
# ============================================

def main():
    """Запуск прототипа"""
    print("\n" + "="*60)
    print("🧠 ПРОТОТИП: НОВАЯ НАВИГАЦИЯ И 4F-КЛЮЧИ")
    print("="*60)
    print("🎯 Старт: Экран результатов теста")
    print("🔞 Интимный профиль → Приглашения → Друзья")
    print("🧬 4F-ключи с правильной концепцией")
    print("💰 Лимит: 2 бесплатных друга")
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
    app.add_handler(CallbackQueryHandler(back_to_sexual_profile_callback, pattern="^my_sexual_profile$"))
    
    # Результаты
    app.add_handler(CallbackQueryHandler(show_results_screen, pattern="^show_results$"))
    app.add_handler(CallbackQueryHandler(show_results_screen, pattern="^share_mirror$"))
    app.add_handler(CallbackQueryHandler(show_results_screen, pattern="^full_description$"))
    
    # Интимный профиль
    app.add_handler(CallbackQueryHandler(my_sexual_profile_callback, pattern="^my_sexual_profile$"))
    app.add_handler(CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"))
    app.add_handler(CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"))
    
    # Приглашения
    app.add_handler(CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"))
    app.add_handler(CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("✅ Скопировано!", show_alert=False), pattern="^copy_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("🟢 Приглашение активно"), pattern="^check_"))
    
    # Профиль друга
    app.add_handler(CallbackQueryHandler(friend_menu_callback, pattern="^friend_"))
    app.add_handler(CallbackQueryHandler(standard_profile_callback, pattern="^std_"))
    app.add_handler(CallbackQueryHandler(intimate_profile_callback, pattern="^int_"))
    
    # 4F
    app.add_handler(CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"))
    app.add_handler(CallbackQueryHandler(four_f_explanation_callback, pattern="^4f_explain$"))
    app.add_handler(CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("💳 Демо-платеж"), pattern="^buy_4f_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("🎁 Демо-набор"), pattern="^bundle_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer("💰 Демо-доступ"), pattern="^pay_access_"))
    
    print("\n🚀 Бот запущен!")
    print("📱 Проверяйте: @ваш_бот")
    print("\nТЕСТОВЫЕ ДРУЗЬЯ:")
    print("  • @alex_free - бесплатный, SA_3_CON, без ключей")
    print("  • @maria_free - бесплатный, IP_5_INT, куплен 1F")
    print("\nСТАТУСЫ:")
    print("  • Бесплатный лимит: 2/2")
    print("  • 3+ друг - платный доступ 99₽")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
