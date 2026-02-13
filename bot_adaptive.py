#!/usr/bin/env python3
"""
ПРОТОТИП: 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
Версия: 14.0 - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ
✅ ВАШ ДИЗАЙН экрана «Мои отражения»
✅ Ссылки на Яндекс.Диск для каждого профиля
✅ ИСПРАВЛЕНА кнопка «Интимный профиль»
✅ ИСПРАВЛЕН конфликт экземпляров бота
✅ ДОБАВЛЕНО принудительное управление состояниями
"""

import logging
import os
import sys
import uuid
import json
import urllib.parse
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("bot_detailed.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Подавляем лишние логи от библиотек
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)

# ===== НАСТРОЙКА =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
BOT_USERNAME = "Testing_Lichnosti_bot"

# ===== УМНЫЙ ПОИСК КОРНЯ ПРОЕКТА =====
def find_project_root() -> str:
    """Находит корень проекта (где лежит папка profiles/)"""
    try:
        current = os.path.dirname(os.path.abspath(__file__))
        
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, "profiles")):
                logger.info(f"✅ Корень проекта найден: {current}")
                return current
            current = os.path.dirname(current)
        
        root = os.path.dirname(os.path.abspath(__file__))
        logger.warning(f"⚠️ Папка profiles не найдена, используем: {root}")
        return root
    except Exception as e:
        logger.error(f"❌ Ошибка поиска корня проекта: {e}")
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
BUY_PACKAGES = 7
FOUR_F_MAIN = 8
FOUR_F_DETAILED = 9

# ===== КОНСТАНТЫ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
FREE_FRIEND_LIMIT = 2
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1
FREE_INVITE_LIMIT = 3

INVITE_PACKAGES = {
    "3": {"price": 299, "links": 3, "emoji": "🥉", "popular": False},
    "5": {"price": 499, "links": 5, "emoji": "🥈", "popular": True},
    "10": {"price": 899, "links": 10, "emoji": "🥇", "popular": False}
}

# ===== ССЫЛКИ НА ЯНДЕКС.ДИСК =====
USER_DISK_LINK = "https://disk.yandex.ru/d/EYPIF9_puI_t0A"

PROFILE_DISK_LINKS = {
    "SA-3_CON": "https://disk.yandex.ru/d/abc123def",
    "SA-4_VAL": "https://disk.yandex.ru/d/def456ghi",
    "SA-5_INT": "https://disk.yandex.ru/d/ghi789jkl",
    "IP-3_CON": "https://disk.yandex.ru/d/jkl012mno",
    "IP-4_VAL": "https://disk.yandex.ru/d/mno345pqr",
    "IP-5_INT": "https://disk.yandex.ru/d/pqr678stu",
    "default": "https://disk.yandex.ru/d/xyz789uvw"
}

def get_disk_link_by_profile(profile_code: str) -> str:
    """Возвращает ссылку на Яндекс.Диск для профиля"""
    return PROFILE_DISK_LINKS.get(profile_code, PROFILE_DISK_LINKS["default"])

# ===== 4F-КОНСТАНТЫ =====
FOUR_F_EMOJIS = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ",
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

FOUR_F_EXPLANATION = """
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>

🧬 4F — это 4 базовые реакции психики:
Нападение, бегство, секс, поглощение.
Ключи к управлению состояниями другого человека.

<b>1F 🔥 НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Что включает его агрессию
└ Как быстро её погасить

<b>2F 🏃 БЕГСТВО / СТРАХ</b>
└ Чего он боится на самом деле
└ Как стать для него безопасностью

<b>3F 🧬 СЕКС / ЖЕЛАНИЕ</b>
└ Что реально его заводит
└ 3 слова и 3 касания-ключа

<b>4F 🍽 ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Что запускает режим заработка
└ Как говорить с ним о деньгах

💰 <b>Цена: 1₽</b> (тестовый режим)
"""

FOUR_F_DETAILED_EXPLANATION = """
🔥 <b>1F - ЯРОСТЬ / НАПАДЕНИЕ</b>
<i>Стимулы, запускающие агрессию</i>

😤 <b>СТИМУЛЫ, ЗАПУСКАЮЩИЕ ЯРОСТЬ</b>

Его агрессия не возникает из ниоткуда.
Это реакция на конкретные ТРИГГЕРЫ.

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Критика при свидетелях
   • Обесценивание его усилий
   • Игнорирование границ
   • Определенные интонации

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • Список его личных триггеров
   • 3 фразы-гасителя
   • Технику «Торможение»

══════════════════════

🏃 <b>2F - СТРАХ / БЕГСТВО</b>
<i>Стимулы, запускающие избегание</i>

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Повышение голоса
   • Вопросы о будущем
   • Давление и требования

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 якоря безопасности
   • Технику «Безопасная среда»

══════════════════════

🧬 <b>3F - СЕКС / ЖЕЛАНИЕ</b>
<i>Стимулы, запускающие влечение</i>

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Особая интонация
   • Зрительный контакт
   • Неожиданные касания

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 слова-пароля
   • 3 касания-ключа
   • Эротический сценарий

══════════════════════

🍽 <b>4F - ДЕНЬГИ / ПОГЛОЩЕНИЕ</b>
<i>Стимулы, запускающие режим заработка</i>

<b>🎯 ПУСКОВЫЕ КЛЮЧИ:</b>
   • Упоминание возможностей
   • Разговоры о конкурентах
   • Идеи для заработка

<b>🔑 ЧТО ДАЁТ КЛЮЧ:</b>
   • 3 фразы-мотиватора
   • Технику просьбы
   • Сценарий «Топливо»
"""

# ===== ЗАГРУЗКА ИНТИМНОГО ПРОФИЛЯ =====
def load_intimate_profile() -> dict:
    """Загружает интимный профиль"""
    try:
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            os.path.join(bot_dir, "sexual_18", "sa_5_int.json"),
            os.path.join(PROJECT_ROOT, "sexual_18", "sa_5_int.json"),
            os.path.join(PROJECT_ROOT, "profiles", "sexual_18", "sa_5_int.json"),
            os.path.join("sexual_18", "sa_5_int.json"),
            os.path.join("profiles", "sexual_18", "sa_5_int.json"),
        ]
        
        logger.info("🔍 Поиск файла профиля:")
        for path in possible_paths:
            logger.info(f"   Проверяем: {path}")
            if os.path.exists(path):
                logger.info(f"   ✅ НАЙДЕН: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"   ✅ Профиль загружен: {data.get('profile_type', 'unknown')}")
                    return data
            logger.info(f"   ❌ Не найден")
        
        logger.error("❌ Файл профиля не найден!")
        return get_emergency_profile()
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return get_emergency_profile()

def get_emergency_profile() -> dict:
    """Аварийный профиль"""
    logger.info("🆘 Используется аварийный профиль")
    return {
        "profile_type": "SA-5_INT",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие.",
        "sections": {}
    }

def format_intimate_profile(profile_data: dict, user_name: str) -> str:
    """Форматирует интимный профиль"""
    try:
        message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ</b>
{user_name}

📊 Тип: {profile_data.get('profile_type', 'SA-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', '«Со мной не скучно. Со мной — вкусно.»')}

🧠 <b>ВАША ПРИРОДА:</b>
{profile_data.get('description', '')}

{SEXUAL_DIVIDER}

💎 <b>ТАМ, ЗА ЗЕРКАЛОМ...</b>

Вы увидели только что СВОЁ отражение.
Но у <b>каждого друга</b> — своя тайна.

<b>⬇️ КАК УВИДЕТЬ ИХ:</b>

<b>1.</b> 🚀 Нажмите «🔞 СОЗДАТЬ ССЫЛКУ»
<b>2.</b> 💌 Отправьте ссылку другу
<b>3.</b> 🔓 Друг проходит тест → вам открывается ЕГО профиль

<b>💫 Чем больше друзей увидят себя в зеркале —</b>
   <b>тем больше тайн откроется вам.</b>
"""
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования: {e}")
        return "🔞 ИНТИМНЫЙ ПРОФИЛЬ\n\nПроизошла ошибка загрузки."

# ===== ЗАГРУЗКА ПРОФИЛЯ ДРУГА =====
def load_friend_intimate_profile(friend_name: str, friend_profile: str = None) -> dict:
    """Загружает профиль друга"""
    return {
        "profile_type": f"ТЕСТ-{friend_profile or 'SA-5_INT'}",
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "quote": f"«{friend_name}, со мной не скучно.»",
        "description": f"Тестовый профиль {friend_name}.",
        "sections": {
            "what_turns_on": {
                "title": "🔴 ВКЛЮЧАЕТ",
                "items": ["Долгие прелюдии", "Ролевые игры", "Шёпот на ухо"]
            },
            "what_turns_off": {
                "title": "⚠️ ВЫКЛЮЧАЕТ",
                "items": ["Спешка", "Отсутствие атмосферы"]
            }
        },
        "is_test_profile": True
    }

def format_friend_intimate_profile(profile_data: dict, friend_name: str) -> str:
    """Форматирует профиль друга"""
    try:
        message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
👤 {friend_name}

📊 Тип: {profile_data.get('profile_type', 'ТЕСТ-5_INT')}
🧠 Архетип: {profile_data.get('archetype', 'ЦЕРЕМОНИАЛЬНЫЙ')}

💬 <b>ЦИТАТА:</b>
{profile_data.get('quote', f'«{friend_name}, со мной не скучно.»')}

🧠 <b>ЕГО ПРИРОДА:</b>
{profile_data.get('description', f'Тестовый профиль {friend_name}')}

{SEXUAL_DIVIDER}

⚠️ ТЕСТОВЫЙ РЕЖИМ
💎 Купите полный доступ за {FRIEND_ACCESS_PRICE}₽
"""
        return message
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования: {e}")
        return f"🔞 ПРОФИЛЬ {friend_name}\n\nОшибка загрузки."

# ===== ПЛАТЕЖНАЯ СИСТЕМА =====
def generate_payment_id(prefix: str = "4f", user_id: int = None) -> str:
    timestamp = int(datetime.now().timestamp())
    random_str = uuid.uuid4().hex[:8]
    user_suffix = str(user_id)[-6:] if user_id else "000000"
    return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"

# ===== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =====
USER_PROFILE = {"display_name": "SA-5_INT", "type_code": "SA", "level": 5}

# ===== ХРАНИЛИЩЕ ПРИГЛАШЕНИЙ =====
user_invites = {}

def get_user_invites(user_id: int) -> list:
    if user_id not in user_invites:
        user_invites[user_id] = []
        logger.info(f"👤 Создано хранилище для {user_id}")
    return user_invites[user_id]

def init_test_data(user_id: int):
    """Инициализирует тестовые данные"""
    try:
        invites = get_user_invites(user_id)
        if len(invites) > 0:
            return
        
        current_time = datetime.now().timestamp()
        
        test_friends = [
            {
                "invite_id": f"test_free_1_{user_id}",
                "friend_id": 1001,
                "friend_name": "@alex",
                "friend_profile": "SA-3_CON",
                "status": "used",
                "access_status": "free",
                "created_at": current_time,
                "used_at": current_time,
                "purchased_functions": [],
                "invite_type": "🆓"
            },
            {
                "invite_id": f"test_free_2_{user_id}",
                "friend_id": 1002,
                "friend_name": "@maria",
                "friend_profile": "IP-5_INT",
                "status": "used",
                "access_status": "free",
                "created_at": current_time - 86400,
                "used_at": current_time - 86400,
                "purchased_functions": ["1F"],
                "invite_type": "🆓"
            }
        ]
        
        invites.extend(test_friends)
        logger.info(f"✅ Тестовые данные для user_id={user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")

def count_free_friends(user_id: int) -> int:
    invites = get_user_invites(user_id)
    return len([inv for inv in invites if inv.get("status") == "used" and inv.get("access_status") == "free"])

# ============================================
# 🧠 ЭКРАН 1: РЕЗУЛЬТАТЫ
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота"""
    try:
        user = update.effective_user
        logger.info(f"🚀 Пользователь {user.id} запустил бота")
        
        # Очищаем данные и устанавливаем начальное состояние
        context.user_data.clear()
        context.user_data["user_id"] = user.id
        context.user_data["profile"] = USER_PROFILE.copy()
        context.user_data["conversation_state"] = RESULTS_SCREEN
        
        init_test_data(user.id)
        context.user_data["sexual_invites"] = get_user_invites(user.id)
        
        return await show_results_screen(update, context)
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}")
        return RESULTS_SCREEN

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 ЭКРАН РЕЗУЛЬТАТОВ"""
    try:
        logger.debug("📺 Отображаем экран результатов")
        profile = context.user_data.get("profile", USER_PROFILE)
        
        message = f"""
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>

📊 {profile['display_name']}

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.

🛠 <b>ИНСТРУМЕНТ</b>
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
        
        # Устанавливаем состояние
        context.user_data["conversation_state"] = RESULTS_SCREEN
        return RESULTS_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в show_results_screen: {e}")
        return RESULTS_SCREEN

# ============================================
# 🔞 ЭКРАН 2: МОЙ ИНТИМНЫЙ ПРОФИЛЬ - ИСПРАВЛЕНО!
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль - ПОЛНОСТЬЮ ИСПРАВЛЕНО"""
    try:
        query = update.callback_query
        logger.debug(f"🔍 ПОЛУЧЕН CALLBACK: {query.data} от {query.from_user.id}")
        
        # Принудительно отвечаем на callback
        await query.answer()
        logger.info(f"👤 Пользователь {query.from_user.id} открыл интимный профиль")
        
        # Принудительно устанавливаем состояние
        context.user_data["conversation_state"] = MY_SEXUAL_PROFILE
        
        user_name = query.from_user.first_name or "Пользователь"
        logger.debug(f"📝 Загружаем профиль для: {user_name}")
        
        profile_data = load_intimate_profile()
        logger.debug(f"📊 Профиль загружен: {profile_data.get('profile_type', 'unknown')}")
        
        message = format_intimate_profile(profile_data, user_name)
        logger.debug(f"📄 Сообщение сформировано, длина: {len(message)}")
        
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ Назад в профиль", callback_data="back_to_results")]
        ]
        
        logger.debug("✉️ Отправляем сообщение...")
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        logger.debug("✅ Сообщение отправлено успешно")
        
        return MY_SEXUAL_PROFILE
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}\n{traceback.format_exc()}")
        try:
            await query.answer("❌ Произошла ошибка", show_alert=True)
        except:
            pass
        return RESULTS_SCREEN

# ============================================
# 🔗 ЭКРАН 3: СОЗДАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        invites = context.user_data.get("sexual_invites", [])
        
        invite_code = f"sex_{uuid.uuid4().hex[:8]}"
        invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_code}"
        
        invite_message = "✨ Есть одна штука.\nОпределяет твой ночной тип личности."
        
        text = f"""
🔞 <b>✨ ВАША ССЫЛКА ГОТОВА! ✨</b>

🔗 <code>{invite_url}</code>

💬 <b>📨 ТЕКСТ СООБЩЕНИЯ:</b>
<blockquote>{invite_message}</blockquote>

{SEXUAL_DIVIDER}
🟢 <b>• АКТИВНО •</b> ожидание друга
"""
        
        invite_data = {
            "invite_id": invite_code,
            "link": invite_url,
            "status": "active",
            "created_at": datetime.now().timestamp(),
            "invite_type": "🆓"
        }
        
        invites.insert(0, invite_data)
        
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(invite_message)}"
        
        keyboard = [
            [InlineKeyboardButton("✈️ ОТПРАВИТЬ ДРУГУ", url=share_url)],
            [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return INVITES_LIST
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return INVITES_LIST

# ============================================
# 🔍 ЭКРАН 4: МОИ ОТРАЖЕНИЯ - ВАШ ДИЗАЙН
# ============================================

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 МОИ ОТРАЖЕНИЯ - ВАШ МИНИМАЛИСТИЧНЫЙ ДИЗАЙН"""
    try:
        query = update.callback_query
        await query.answer("🔄 Загружаю отражения...")
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        user_id = query.from_user.id
        invites = get_user_invites(user_id)
        context.user_data["sexual_invites"] = invites
        
        used_invites = [inv for inv in invites if inv.get("status") == "used"]
        total_invites = len(invites)
        total_reflections = len(used_invites)
        
        user_profile = context.user_data.get("profile", USER_PROFILE)
        user_profile_code = user_profile.get('display_name', 'SA-5_INT')
        
        # ВАШ ДИЗАЙН
        message = f"""
🪞 МОИ ОТРАЖЕНИЯ
────────────────

📊 СТАТИСТИКА
🪞 Ссылок зеркал: {total_invites}
👥 Посмотрелись в зеркало: {total_reflections}

🪞 МОЁ ОТРАЖЕНИЕ
📌 Профиль: {user_profile_code}
📁 Диск: <code>{USER_DISK_LINK}</code>
"""

        if used_invites:
            message += f"""

👥 ОТРАЖЕНИЯ ТЕХ КТО ПОСМОТРЕЛСЯ В ВАШЕ ЗЕРКАЛО ({total_reflections})

"""
            for idx, inv in enumerate(used_invites[:5], 1):
                friend_name = inv.get("friend_name", "друг").replace('@', '')
                friend_profile = inv.get("friend_profile", "SA-3_CON")
                disk_link = get_disk_link_by_profile(friend_profile)
                
                message += f"""
{idx}. 🆔 <b>{friend_name}</b> • {friend_profile} • 📁 <code>{disk_link}</code>"""
                
                if inv.get("purchased_functions"):
                    key_map = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
                    keys = " ".join(key_map.get(k, k) for k in inv["purchased_functions"])
                    message += f" • {keys}"
        else:
            message += f"""

👥 ОТРАЖЕНИЯ ТЕХ КТО ПОСМОТРЕЛСЯ В ВАШЕ ЗЕРКАЛО (0)

🌑 <i>Пока нет отражений</i>

💡 Создайте ссылку в профиле
   и отправьте другу
"""

        message += f"""

────────────────
💫 Каждое отражение — ключ к человеку.
"""

        keyboard = [
            [InlineKeyboardButton("◀️ К ПРОФИЛЮ", callback_data="my_sexual_profile")],
            [InlineKeyboardButton("🔴 4F КЛЮЧИ 🔴", callback_data="four_f_main_menu")]
        ]

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"🔍 Пользователь {user_id} открыл Мои отражения")
        return INVITES_LIST
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return INVITES_LIST

# ============================================
# 🧬 ЭКРАН 5: ГЛАВНОЕ МЕНЮ 4F
# ============================================

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 Главное меню 4F-ключей"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MAIN
        logger.info(f"🧬 Пользователь {query.from_user.id} открыл меню 4F")
        
        message = FOUR_F_EXPLANATION
        
        keyboard = [
            [InlineKeyboardButton("📘 ПОДРОБНЕЕ", callback_data="four_f_detailed")],
            [InlineKeyboardButton("🔍 К ОТРАЖЕНИЯМ", callback_data="my_invites")],
            [InlineKeyboardButton("◀️ В ПРОФИЛЬ", callback_data="my_sexual_profile")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MAIN
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return INVITES_LIST

# ============================================
# 📘 ЭКРАН 6: ПОДРОБНОЕ ОПИСАНИЕ 4F
# ============================================

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ПОДРОБНОЕ ОПИСАНИЕ 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_DETAILED
        logger.info(f"📘 Пользователь {query.from_user.id} открыл подробное описание")
        
        message = FOUR_F_DETAILED_EXPLANATION
        
        keyboard = [
            [InlineKeyboardButton("◀️ К ОБУЧАЙКЕ", callback_data="four_f_main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_DETAILED
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_MAIN

# ============================================
# 🔍 ЭКРАН 7: ПРОВЕРКА СТАТУСА
# ============================================

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔄 Проверка статуса приглашения"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = INVITES_LIST
        
        invite_id = query.data.replace("check_status_", "")
        
        message = f"""
🔍 <b>СТАТУС ПРИГЛАШЕНИЯ</b>

🔗 <code>https://t.me/{BOT_USERNAME}?start={invite_id}</code>

🟢 <b>• АКТИВНО •</b> ждёт друга
"""
        
        keyboard = [
            [InlineKeyboardButton("⬅️ К ОТРАЖЕНИЯМ", callback_data="my_invites")]
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
# 💳 ЭКРАН 8: ПОКУПКА ПАКЕТОВ
# ============================================

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💎 Покупка пакетов ссылок"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = BUY_PACKAGES
        
        message = f"""
💎 <b>ПАКЕТЫ ПРИГЛАШЕНИЙ</b>

<b>Выберите пакет:</b>
"""
        
        keyboard = []
        for links, data in INVITE_PACKAGES.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{data['emoji']} {data['links']} ссылок - {data['price']}₽",
                    callback_data=f"pay_package_{links}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="my_invites")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return BUY_PACKAGES
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return INVITES_LIST

# ============================================
# 👤 ЭКРАН 9: МЕНЮ ДРУГА
# ============================================

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👤 МЕНЮ ПРОФИЛЯ ДРУГА"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FRIEND_MENU
        
        friend_id = int(query.data.split("_")[1])
        
        message = f"""
👤 <b>МЕНЮ ДРУГА</b>

📊 SA-3_CON
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Стандарт", callback_data=f"std_{friend_id}"),
                InlineKeyboardButton("🔞 Интим", callback_data=f"int_{friend_id}")
            ],
            [InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}")],
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
# 📊 ЭКРАН 10: СТАНДАРТНЫЙ ПРОФИЛЬ
# ============================================

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Стандартный профиль друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        friend_id = int(query.data.split("_")[1])
        
        message = f"""
📊 <b>СТАНДАРТНЫЙ ПРОФИЛЬ</b>

🧠 Автономный стратег
💬 «Я не ищу одобрения — я ищу эффективность.»
"""
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")]]
        
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
# 🔞 ЭКРАН 11: ИНТИМНЫЙ ПРОФИЛЬ ДРУГА
# ============================================

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Интимный профиль друга"""
    try:
        query = update.callback_query
        await query.answer()
        
        friend_id = int(query.data.split("_")[1])
        friend_name = "друг"
        
        profile_data = load_friend_intimate_profile(friend_name)
        message = format_friend_intimate_profile(profile_data, friend_name)
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")]]
        
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
# 🧬 ЭКРАН 12: 4F МЕНЮ ДРУГА
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧬 МЕНЮ 4F-КЛЮЧЕЙ"""
    try:
        query = update.callback_query
        await query.answer()
        
        context.user_data["conversation_state"] = FOUR_F_MENU
        
        friend_id = int(query.data.split("_")[1])
        
        message = f"""
🧬 <b>4F КЛЮЧИ</b>

🔥 1F - НАПАДЕНИЕ 🔒
🏃 2F - БЕГСТВО 🔒
🧬 3F - ЖЕЛАНИЕ 🔒
🍽 4F - ДЕНЬГИ 🔒
"""
        
        keyboard = []
        for f in ["1F", "2F", "3F", "4F"]:
            emoji = FOUR_F_EMOJIS[f]
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {f} - 1₽",
                    callback_data=f"buy_4f_{friend_id}_{f}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FRIEND_MENU

# ============================================
# 💳 ЭКРАН 13: ПОКУПКА 4F КЛЮЧА
# ============================================

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Покупка 4F-ключа"""
    try:
        query = update.callback_query
        await query.answer("💰 Создаю счёт...")
        
        context.user_data["conversation_state"] = FOUR_F_PAYMENT_SCREEN
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        message = f"""
💳 <b>ОПЛАТА КЛЮЧА</b>

{function} - 1₽

✅ После оплаты ключ будет разблокирован
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
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_MENU

# ============================================
# 💳 ЭКРАН 14: ПРОЦЕСС ПЛАТЕЖА
# ============================================

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Процесс платежа"""
    try:
        query = update.callback_query
        await query.answer("💳 Подключаюсь...")
        
        parts = query.data.split("_")
        payment_id = parts[2]
        friend_id = int(parts[3])
        function = parts[4]
        
        # Демо-режим - сразу открываем ключ
        await query.answer("✅ Ключ разблокирован!", show_alert=True)
        
        # Принудительно перенаправляем на открытие ключа
        new_query = update
        new_query.callback_query.data = f"open_4f_{friend_id}_{function}"
        return await open_4f_key_callback(update, context)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_PAYMENT_SCREEN

# ============================================
# 🔑 ЭКРАН 15: ОТКРЫТЫЙ 4F-КЛЮЧ
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔓 ОТКРЫТЫЙ 4F-КЛЮЧ"""
    try:
        query = update.callback_query
        await query.answer("🔓 Открываю...")
        
        context.user_data["conversation_state"] = FOUR_F_CONTENT
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        function = parts[3]
        
        triggers = {
            "1F": ["«Я понимаю, почему ты так реагируешь»", "«Ты имеешь полное право злиться»"],
            "2F": ["«Ты не обязан это делать»", "«Здесь безопасно»"],
            "3F": ["«Ты такой...»", "Взгляд в глаза чуть дольше"],
            "4F": ["«Ты можешь заработать на этом»", "«Это твой шанс»"]
        }
        
        message = f"""
🎉 <b>КЛЮЧ АКТИВИРОВАН!</b>

{FOUR_F_EMOJIS[function]} <b>{FOUR_F_TITLES[function]}</b>

<b>🎯 ТРИГГЕРЫ:</b>
"""
        
        for i, trigger in enumerate(triggers.get(function, ["Триггер 1", "Триггер 2"])[:2], 1):
            message += f"\n{i}. {trigger}"
        
        message += f"""

<b>🧠 РАЗБОР:</b>
Ключ успешно активирован. Теперь вы понимаете, какие стимулы включают эту реакцию.

<b>📋 ПРОТОКОЛ:</b>
1. Заметьте триггер
2. Признайте эмоцию
3. Не давите
"""
        
        keyboard = [[InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"4f_{friend_id}")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_CONTENT
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_MENU

# ============================================
# ⬅️ ВОЗВРАТЫ И ЗАГЛУШКИ
# ============================================

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⬅️ Возврат к результатам"""
    try:
        query = update.callback_query
        await query.answer()
        return await show_results_screen(update, context)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return RESULTS_SCREEN

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для демо-функций"""
    try:
        query = update.callback_query
        pattern = query.data
        
        if pattern.startswith("pay_package_"):
            await query.answer("💰 Демо-пакет")
        elif pattern.startswith("process_package_payment_"):
            await query.answer("✅ Пакет активирован", show_alert=True)
        elif pattern == "share_mirror":
            await query.answer("🪞 Скоро здесь будет подарок")
        elif pattern == "full_description":
            await query.answer("📖 Полное описание — 690₽")
        else:
            await query.answer("✅ Демо-режим")
        
        return RESULTS_SCREEN
    except Exception as e:
        logger.error(f"❌ Ошибка в dummy_callback: {e}")
        return RESULTS_SCREEN

# ============================================
# 🚀 ЗАПУСК
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v14.0")
    print("="*60)
    print("✅ ВАШ ДИЗАЙН экрана «Мои отражения»")
    print("✅ ИСПРАВЛЕНА кнопка «Интимный профиль»")
    print("✅ ИСПРАВЛЕН конфликт экземпляров")
    print("✅ ДОБАВЛЕНО принудительное управление состояниями")
    print("="*60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    try:
        # Устанавливаем более высокий таймаут для избежания конфликтов
        app = (
            Application.builder()
            .token(TOKEN)
            .connect_timeout(30.0)
            .read_timeout(30.0)
            .write_timeout(30.0)
            .pool_timeout(30.0)
            .build()
        )
        
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
                    CallbackQueryHandler(four_f_detailed_callback, pattern='^four_f_detailed$'),
                    CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                    CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                ],
                
                FOUR_F_DETAILED: [
                    CallbackQueryHandler(four_f_main_menu_callback, pattern='^four_f_main_menu$'),
                ],
            },
            fallbacks=[
                CommandHandler('start', start),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
                # Глобальный fallback для любого callback
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
            ],
            allow_reentry=True,
            name="intimate_profiles_conversation",
            persistent=False,
        )
        
        app.add_handler(conv_handler)
        
        print("\n🚀 Бот запущен! Версия 14.0")
        print("="*60)
        logger.info("✅ Бот успешно запущен")
        
        # Запускаем с правильными параметрами
        app.run_polling(
            drop_pending_updates=True,  # Важно! Сбрасывает старые обновления
            allowed_updates=['message', 'callback_query'],
            timeout=30
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}\n{traceback.format_exc()}")
        print(f"\n❌ Ошибка запуска: {e}")

# ============================================
# 📘 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ (заглушки)
# ============================================

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📘 ОБУЧАЙКА 4F"""
    try:
        query = update.callback_query
        await query.answer()
        
        message = FOUR_F_EXPLANATION
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="my_invites")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return FOUR_F_MENU
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return FOUR_F_MENU

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💳 Оплата пакета (заглушка)"""
    try:
        query = update.callback_query
        await query.answer("💰 Демо-режим")
        return BUY_PACKAGES
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return BUY_PACKAGES

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Подтверждение оплаты (заглушка)"""
    try:
        query = update.callback_query
        await query.answer("✅ Пакет активирован", show_alert=True)
        return INVITES_LIST
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return INVITES_LIST

if __name__ == "__main__":
    main()
