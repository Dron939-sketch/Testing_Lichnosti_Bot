#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 10.1-final - ИСПРАВЛЕНИЯ: ПУТЬ К JSON, РАЗДЕЛИТЕЛЬ, МОИ ОТРАЖЕНИЯ, ПРОФИЛЬ ДРУГА
"""

import logging
import os
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

# ===== СОСТОЯНИЯ =====
RESULTS_SCREEN = 0
MY_SEXUAL_PROFILE = 1
INVITES_LIST = 2
FRIEND_MENU = 3
FOUR_F_MENU = 4
FOUR_F_CONTENT = 5
FOUR_F_PAYMENT_SCREEN = 6

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━"  # 10 черточек
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
        # ИСПРАВЛЕНО: profiles вместо профили (латиница)
        profile_path = os.path.join("profiles", "sexual_18", "sa_5_int.json")
        
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Загружен интимный профиль: {profile_path}")
                return data
        else:
            logger.warning(f"⚠️ Файл профиля не найден: {profile_path}")
            # Заглушка
            return {
                "profile_type": "SA-5_INT",
                "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
                "role": "Жрец/Жрица сексуальной мистерии",
                "quote": "«Со мной не скучно. Со мной — вкусно.»",
                "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.\nВы не занимаетесь любовью — вы служите ей.\nИ каждый раз — как в первый. И каждый раз — как в последний.",
                "sections": {}
            }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки интимного профиля: {e}")
        return {
            "profile_type": "SA-5_INT",
            "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
            "quote": "«Со мной не скучно. Со мной — вкусно.»",
            "description": "Ваш интимный профиль",
            "sections": {}
        }

def format_intimate_profile(profile_data: dict, user_name: str) -> str:
    """Форматирует интимный профиль для отображения в Telegram"""
    
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
    
    # Добавляем все секции из JSON
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
    
    # ИСПРАВЛЕНО: Разделитель в одной строке с заголовком
    message += f"""

{SEXUAL_DIVIDER} 🪞 ТАМ, ЗА ЗЕРКАЛОМ...

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
    """
    Загружает интимный профиль ДРУГА (тестовый режим - всегда sa_5_int)
    Подставляет имя друга в текст профиля
    """
    try:
        # Загружаем тот же JSON, что и для своего профиля
        profile_path = os.path.join("profiles", "sexual_18", "sa_5_int.json")
        
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Меняем тип профиля на "ТЕСТОВЫЙ"
                data["profile_type"] = f"ТЕСТ-{friend_profile or 'SA-5_INT'}"
                
                # Добавляем метаданные о друге
                data["friend_name"] = friend_name
                data["is_test_profile"] = True
                
                logger.info(f"✅ Загружен тестовый интимный профиль для друга {friend_name}")
                return data
        else:
            logger.warning(f"⚠️ Файл профиля не найден: {profile_path}")
            return get_friend_emergency_profile(friend_name)
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки интимного профиля друга: {e}")
        return get_friend_emergency_profile(friend_name)

def get_friend_emergency_profile(friend_name: str) -> dict:
    """Аварийный интимный профиль для друга"""
    return {
        "profile_type": "SA-5_INT (ТЕСТ)",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "quote": f"«{friend_name}, со мной не скучно. Со мной — вкусно.»",
        "description": f"Тестовый интимный профиль для {friend_name}.\nВ реальном режиме здесь будут его персональные данные.",
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
    """Форматирует интимный профиль ДРУГА для отображения"""
    
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
    
    # Добавляем основные секции
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
    
    # Добавляем дисклеймер о тестовом режиме
    message += f"""

{SEXUAL_DIVIDER} ⚠️ ТЕСТОВЫЙ РЕЖИМ

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
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ (ИЗ JSON)
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
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ (НОВЫЙ ДИЗАЙН - ТОЧНО ПО ТЗ)
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения (ФИНАЛЬНЫЙ ДИЗАЙН ПО ТЗ)"""
    query = update.callback_query
    await query.answer()
    
    profile = context.user_data.get("profile", USER_PROFILE)
    
    # 1. Генерируем код и ссылку
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
    
    # 2. ТЕКСТ ДЛЯ ДРУГА - ИЗМЕНЕНА ТОЛЬКО ОДНА СТРОКА! (по ТЗ)
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "У меня — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
    )
    
    # 3. Текущее время
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # 4. НОВЫЙ ТЕКСТ ЭКРАНА (ТОЧНО ПО МАКЕТУ ИЗ ТЗ)
    text = f"""
🔞  ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!  🔞 

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

 ОСТАЛОСЬ ТОЛЬКО ОТПРАВИТЬ  ⬇️
"""
    
    # 5. Сохраняем приглашение
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
    
    # 6. КНОПКИ - БЕЗ ИЗМЕНЕНИЙ! (НЕ ТРОГАТЬ ПО ТЗ)
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Отправить другу", url=share_url),
            InlineKeyboardButton("📋 Копировать ссылку", callback_data=f"copy_invite_{invite_code}")
        ],
        [
            InlineKeyboardButton("🔍 Мои приглашения", callback_data="my_invites"),
            InlineKeyboardButton("⬅️ К профилю", callback_data="my_sexual_profile")
        ]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: МОИ ОТРАЖЕНИЯ (ИСПРАВЛЕНО)
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 Мои отражения - список приглашений"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # ✅ ИСПРАВЛЕНО: инициализируем тестовые данные
    init_test_data(user_id)
    
    # ✅ Загружаем свежие данные
    invites = get_user_invites(user_id)
    context.user_data["sexual_invites"] = invites
    
    active_invites = [inv for inv in invites if inv.get("status") == "active"]
    used_invites = [inv for inv in invites if inv.get("status") == "used"]
    
    # ✅ ИСПРАВЛЕНО: Добавлена статистика
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
# 📋 ЭКРАН: КОПИРОВАНИЕ ССЫЛКИ
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Копирование ссылки (заглушка)"""
    query = update.callback_query
    await query.answer("✅ Ссылка скопирована!", show_alert=False)
    return INVITES_LIST

# ============================================
# 👤 ЭКРАН 6: МЕНЮ ПРОФИЛЯ ДРУГА
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
    friend_name = "друг"
    
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_name = inv.get("friend_name", "друг")
            break
    
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
# 🔞 ЭКРАН 9: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА (ИСПРАВЛЕНО)
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга (ТЕСТОВЫЙ РЕЖИМ - всегда SA-5_INT)"""
    query = update.callback_query
    await query.answer()
    
    friend_id = int(query.data.split("_")[1])
    
    # Ищем данные друга
    friend_data = None
    for inv in context.user_data.get("sexual_invites", []):
        if inv.get("friend_id") == friend_id:
            friend_data = inv
            break
    
    if not friend_data:
        await query.answer("❌ Друг не найден", show_alert=True)
        return FRIEND_MENU
    
    friend_name = friend_data.get("friend_name", "друг")
    friend_profile = friend_data.get("friend_profile", "SA-3_CON")
    
    # ✅ ИСПРАВЛЕНО: Загружаем тестовый интимный профиль (всегда sa_5_int)
    profile_data = load_friend_intimate_profile(friend_name, friend_profile)
    
    # ✅ Форматируем для друга
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
    
    hot_hint = "\n🔥 ХИТ ПРОДАЖ: 1F покупают в 2 раза чаще"
    
    message = f"""
🧬 4F-КЛЮЧИ ДЛЯ {friend_name}

📊 {friend_profile}
{hot_hint if not purchased else ""}

1F 🔥 {FOUR_F_TITLES['1F']}
└ {FOUR_F_SUBTITLES['1F']}
└ ⚡ Например: боится, что его используют, поэтому нападает первым

2F 🏃 {FOUR_F_TITLES['2F']}
└ {FOUR_F_SUBTITLES['2F']}
└ ⚡ Например: избегает конфликтов, потому что в детстве за них наказывали

3F 🧬 {FOUR_F_TITLES['3F']}
└ {FOUR_F_SUBTITLES['3F']}
└ ⚡ Например: его заводит, когда партнёр берёт инициативу

4F 🍽 {FOUR_F_TITLES['4F']}
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
💳 СЧЁТ СФОРМИРОВАН

🔑 Ключ: {function}
👤 Друг: ID {friend_id}
💰 Сумма: 1₽ (тест)

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

👇 ЧТО ДАЛЬШЕ?
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
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v10.1")
    print("="*60)
    print("✅ ИСПРАВЛЕНИЯ:")
    print("   • Путь к JSON: profiles/sexual_18/sa_5_int.json")
    print("   • Разделитель: ━━━━━━━━━━ 🪞 ТАМ, ЗА ЗЕРКАЛОМ...")
    print("   • Текст: «Вы увидели только что СВОЁ 🪞 отражение»")
    print("   • Кнопка «Мои отражения» - ИСПРАВЛЕНА!")
    print("   • Интимный профиль друга - ТЕСТОВЫЙ РЕЖИМ")
    print("="*60)
    print("✅ Экран создания ссылки - НОВЫЙ ДИЗАЙН ПО ТЗ")
    print("   • Заголовок с двойными пробелами 🔞  🔞")
    print("   • Текст: «У меня — совпало процентов на 90»")
    print("   • Разделитель: ━━━━━━━━━━")
    print("   • Статус: 🟢 АКТИВНО • ожидание")
    print("   • Дата: 📅 с временем")
    print("   • Кнопки НЕ ТРОНУТЫ (строго по ТЗ)")
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
    app.add_handler(CallbackQueryHandler(copy_invite_callback, pattern="^copy_invite_"))
    
    # Приглашения
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
    
    print("\n🚀 Бот запущен!")
    print("="*60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
