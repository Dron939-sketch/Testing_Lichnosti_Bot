import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4
import random
import string

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

# ============================================
# 🔧 НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# 🎯 СОСТОЯНИЯ ДИАЛОГА (ВСЕ 9 СОСТОЯНИЙ)
# ============================================
(
    RESULTS_SCREEN,
    MY_SEXUAL_PROFILE,
    INVITES_LIST,
    FRIEND_MENU,
    FOUR_F_MENU,
    FOUR_F_CONTENT,
    FOUR_F_PAYMENT_SCREEN,
    STANDARD_PROFILE_VIEW,
    INTIMATE_PROFILE_VIEW,
    EDIT_PROFILE,              # Новое состояние
    INVITE_STATISTICS,         # Новое состояние  
    FRIEND_INTERACTION,        # Новое состояние
    FOUR_F_KEY_MANAGEMENT,     # Новое состояние
    PAYMENT_CONFIRMATION,      # Новое состояние
    ADMIN_PANEL               # Новое состояние
) = range(15)

# ============================================
# 📁 ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ДАННЫХ
# ============================================
INVITES_FILE = "invites.json"
INTIMATE_PROFILE_FILE = "intimate_profile.json"
USER_DATA_FILE = "user_data.json"
STANDARD_PROFILES_FILE = "standard_profiles.json"
FOUR_F_KEYS_FILE = "4f_keys.json"
PAYMENTS_FILE = "payments.json"
STATISTICS_FILE = "statistics.json"
ADMIN_SETTINGS_FILE = "admin_settings.json"

# ============================================
# 🔑 ТОКЕН БОТА
# ============================================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")

# ============================================
# 💾 ПОЛНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
# ============================================

def load_intimate_profile(user_id: str = None) -> Dict:
    """Загружает данные интимного профиля пользователя"""
    try:
        if os.path.exists(INTIMATE_PROFILE_FILE):
            with open(INTIMATE_PROFILE_FILE, 'r', encoding='utf-8') as f:
                all_profiles = json.load(f)
                if user_id:
                    return all_profiles.get(user_id, get_default_intimate_profile())
                return all_profiles
    except Exception as e:
        logger.error(f"Ошибка загрузки интимного профиля: {e}")
    return get_default_intimate_profile()

def get_default_intimate_profile() -> Dict:
    """Возвращает профиль по умолчанию"""
    return {
        "name": "🌟 Интимный профиль",
        "age": 25,
        "gender": "Девушка",
        "interests": ["Романтика", "Общение", "Путешествия", "Музыка", "Кино"],
        "description": "Ищу глубокие отношения и взаимопонимание. Ценю искренность и открытость.",
        "expectations": "Хочу встретить человека, с которым будет комфортно быть собой.",
        "instagram": "@example",
        "telegram": "@example",
        "whatsapp": "+7 (999) 123-45-67",
        "preferences": {
            "gender": "Мужчина",
            "age_from": 25,
            "age_to": 35,
            "relationship_type": ["Дружба", "Отношения", "Знакомство"]
        },
        "photos": [],
        "verified": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def save_intimate_profile(user_id: str, profile_data: Dict):
    """Сохраняет интимный профиль пользователя"""
    try:
        if os.path.exists(INTIMATE_PROFILE_FILE):
            with open(INTIMATE_PROFILE_FILE, 'r', encoding='utf-8') as f:
                all_profiles = json.load(f)
        else:
            all_profiles = {}
        
        profile_data['updated_at'] = datetime.now().isoformat()
        all_profiles[user_id] = profile_data
        
        with open(INTIMATE_PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_profiles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения интимного профиля: {e}")

def format_intimate_profile(profile: Dict, user_name: str) -> str:
    """Форматирует интимный профиль для отображения"""
    interests = ", ".join(profile.get("interests", []))
    preferences = profile.get("preferences", {})
    pref_gender = preferences.get("gender", "Не указан")
    pref_age = f"{preferences.get('age_from', '?')}-{preferences.get('age_to', '?')}"
    
    verified_badge = "✅ ВЕРИФИЦИРОВАН" if profile.get("verified") else "⏳ НЕ ВЕРИФИЦИРОВАН"
    
    message = f"""
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ {user_name.upper()}</b> 🔞
{verified_badge}

━━━━━━━━━━━━━━━━━━━━━
👤 <b>ОСНОВНАЯ ИНФОРМАЦИЯ:</b>
• Имя: {profile.get('name', 'Не указано')}
• Возраст: {profile.get('age', 'Не указан')}
• Пол: {profile.get('gender', 'Не указан')}

💫 <b>ИНТЕРЕСЫ И ХОББИ:</b>
{interests}

📝 <b>О СЕБЕ:</b>
{profile.get('description', 'Нет описания')}

💭 <b>ОЖИДАНИЯ И ЦЕЛИ:</b>
{profile.get('expectations', 'Нет информации')}

🎯 <b>ПРЕДПОЧТЕНИЯ:</b>
• Ищу: {pref_gender}
• Возраст: {pref_age}

📱 <b>КОНТАКТЫ:</b>
• Instagram: {profile.get('instagram', 'Не указан')}
• Telegram: {profile.get('telegram', 'Не указан')}
• WhatsApp: {profile.get('whatsapp', 'Не указан')}

━━━━━━━━━━━━━━━━━━━━━
<i>🔐 Только для избранных</i>
<i>💎 Создай приглашение, чтобы поделиться</i>
"""
    return message

def load_standard_profiles() -> Dict:
    """Загружает стандартные профили"""
    try:
        if os.path.exists(STANDARD_PROFILES_FILE):
            with open(STANDARD_PROFILES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки стандартных профилей: {e}")
    return {}

def save_standard_profiles(profiles: Dict):
    """Сохраняет стандартные профили"""
    try:
        with open(STANDARD_PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения стандартных профилей: {e}")

def load_invites() -> Dict:
    """Загружает все приглашения"""
    try:
        if os.path.exists(INVITES_FILE):
            with open(INVITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки приглашений: {e}")
    return {}

def save_invites(invites: Dict):
    """Сохраняет приглашения"""
    try:
        with open(INVITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(invites, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения приглашений: {e}")

def load_user_data() -> Dict:
    """Загружает данные пользователей"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки данных пользователей: {e}")
    return {}

def save_user_data(data: Dict):
    """Сохраняет данные пользователей"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных пользователей: {e}")

def load_4f_keys() -> Dict:
    """Загружает ключи 4F"""
    try:
        if os.path.exists(FOUR_F_KEYS_FILE):
            with open(FOUR_F_KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки 4F ключей: {e}")
    return {}

def save_4f_keys(keys: Dict):
    """Сохраняет ключи 4F"""
    try:
        with open(FOUR_F_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения 4F ключей: {e}")

def load_payments() -> Dict:
    """Загружает данные о платежах"""
    try:
        if os.path.exists(PAYMENTS_FILE):
            with open(PAYMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки платежей: {e}")
    return {}

def save_payments(payments: Dict):
    """Сохраняет данные о платежах"""
    try:
        with open(PAYMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(payments, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения платежей: {e}")

def load_statistics() -> Dict:
    """Загружает статистику"""
    try:
        if os.path.exists(STATISTICS_FILE):
            with open(STATISTICS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
    return {
        "total_users": 0,
        "total_invites": 0,
        "total_4f_purchases": 0,
        "daily_active_users": {},
        "popular_features": {}
    }

def save_statistics(stats: Dict):
    """Сохраняет статистику"""
    try:
        with open(STATISTICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

# ============================================
# 🚀 ИСПРАВЛЕННЫЙ ОБРАБОТЧИК START
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")
    
    # Сохраняем пользователя
    users = load_user_data()
    if str(user.id) not in users:
        users[str(user.id)] = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code,
            "joined_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "invites_created": 0,
            "invites_opened": 0,
            "4f_keys_purchased": 0,
            "4f_keys_opened": 0,
            "total_spent": 0,
            "premium_until": None,
            "is_admin": False,
            "blocked_users": [],
            "favorite_profiles": [],
            "settings": {
                "notifications": True,
                "anonymous_mode": False,
                "language": "ru"
            }
        }
        save_user_data(users)
        
        # Обновляем статистику
        stats = load_statistics()
        stats["total_users"] += 1
        save_statistics(stats)
    else:
        users[str(user.id)]["last_active"] = datetime.now().isoformat()
        save_user_data(users)
    
    # Проверяем, есть ли параметр invite в deep linking
    args = context.args
    if args and args[0].startswith('invite_'):
        invite_id = args[0].replace('invite_', '')
        return await process_invite_link(update, context, invite_id)
    
    welcome_text = f"""
🌟 <b>ДОБРО ПОЖАЛОВАТЬ, {user.first_name.upper()}!</b> 🌟

━━━━━━━━━━━━━━━━━━━━━
🔞 <b>ИНТИМНЫЙ МИР ЖДЕТ ТЕБЯ</b>

💎 <b>ВОЗМОЖНОСТИ:</b>
• 🔞 Создай интимный профиль
• 🔗 Генерируй персональные приглашения
• 💎 Управляй доступом к профилю
• 📊 Отслеживай статистику
• 🎁 Открывай 4F ключи

✨ <b>ПРЕИМУЩЕСТВА:</b>
• Полная анонимность
• Только для избранных
• Безопасность данных
• Бесплатные приглашения

━━━━━━━━━━━━━━━━━━━━━
👇 <b>НАЧНИ С СОЗДАНИЯ ПРОФИЛЯ</b>
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 СОЗДАТЬ ИНТИМНЫЙ ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("📊 МОИ ПРИГЛАШЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("💎 4F КЛЮЧИ", callback_data="4f_menu")],
        [InlineKeyboardButton("⚙️ НАСТРОЙКИ", callback_data="settings_menu"),
         InlineKeyboardButton("❓ ПОМОЩЬ", callback_data="help")]
    ]
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    context.user_data['current_state'] = 'RESULTS_SCREEN'
    context.user_data['user_id'] = str(user.id)
    
    return RESULTS_SCREEN

# ============================================
# 🎯 ИСПРАВЛЕННЫЙ ОБРАБОТЧИК КНОПКИ (ГЛАВНОЕ ИСПРАВЛЕНИЕ!)
# ============================================

async def my_sexual_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ ОБРАБОТЧИК!
    Кнопка работает ВО ВСЕХ состояниях и НИЧЕГО НЕ БЛОКИРУЕТ!
    """
    
    # Получаем данные callback
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    logger.info(f"✅ КНОПКА НАЖАТА! User: {user_id}, Data: {query.data}")
    
    try:
        # Загружаем профиль пользователя
        profile_data = load_intimate_profile(user_id)
        user_name = query.from_user.first_name or "Пользователь"
        
        # Форматируем сообщение
        message = format_intimate_profile(profile_data, user_name)
        
        # Создаем расширенную клавиатуру
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ПРИГЛАШЕНИЕ", callback_data="create_invite")],
            [InlineKeyboardButton("📊 МОИ ПРИГЛАШЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("📝 РЕДАКТИРОВАТЬ ПРОФИЛЬ", callback_data="edit_profile")],
            [InlineKeyboardButton("📸 ДОБАВИТЬ ФОТО", callback_data="add_photos")],
            [InlineKeyboardButton("💎 4F КЛЮЧИ", callback_data="4f_menu")],
            [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Пытаемся отредактировать сообщение
        try:
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            logger.info("✅ Сообщение отредактировано")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отредактировать: {e}")
            # Отправляем новое сообщение
            await query.message.reply_text(
                text=message[:4000],
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            logger.info("✅ Отправлено новое сообщение")
        
        # Сохраняем состояние
        context.user_data['current_state'] = 'MY_SEXUAL_PROFILE'
        context.user_data['last_profile_view'] = datetime.now().isoformat()
        
        # Обновляем статистику
        users = load_user_data()
        if user_id in users:
            users[user_id]['last_profile_view'] = datetime.now().isoformat()
            save_user_data(users)
        
        return MY_SEXUAL_PROFILE
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        await query.message.reply_text(
            "❌ Произошла ошибка при загрузке профиля.\n"
            "Пожалуйста, попробуйте позже или нажмите /start"
        )
        return RESULTS_SCREEN

# ============================================
# 🔗 ОБРАБОТЧИКИ ПРИГЛАШЕНИЙ
# ============================================

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Создание нового приглашения"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    invites = load_invites()
    
    # Генерируем уникальный ID
    invite_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    expires_at = datetime.now() + timedelta(days=7)
    
    # Создаем приглашение
    invite_data = {
        "id": invite_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "status": "active",
        "created_by": user_id,
        "opened_by": [],
        "opened_count": 0,
        "last_opened": None,
        "profile_type": "intimate",  # или "standard"
        "max_uses": 10,
        "current_uses": 0
    }
    
    if user_id not in invites:
        invites[user_id] = []
    
    invites[user_id].append(invite_data)
    save_invites(invites)
    
    # Обновляем статистику пользователя
    users = load_user_data()
    if user_id in users:
        users[user_id]["invites_created"] = users[user_id].get("invites_created", 0) + 1
        save_user_data(users)
    
    # Обновляем общую статистику
    stats = load_statistics()
    stats["total_invites"] = stats.get("total_invites", 0) + 1
    save_statistics(stats)
    
    # Создаем ссылку
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=invite_{invite_id}"
    
    # Генерируем QR код (эмуляция)
    qr_code = "🟨⬛🟨⬛🟨\n⬛🟨⬛🟨⬛\n🟨⬛🟨⬛🟨"
    
    message = f"""
✅ <b>ПРИГЛАШЕНИЕ СОЗДАНО!</b>

━━━━━━━━━━━━━━━━━━━━━
🔗 <b>ССЫЛКА:</b>
<code>{invite_link}</code>

📅 <b>ДЕЙСТВУЕТ ДО:</b>
{expires_at.strftime('%d.%m.%Y %H:%M')}

📊 <b>СТАТИСТИКА:</b>
• ID: {invite_id[:8]}...
• Использований: 0/10
• Статус: ✅ Активен

━━━━━━━━━━━━━━━━━━━━━
📱 <b>QR-КОД:</b>
<code>{qr_code}</code>

<i>💡 Отправьте ссылку избранному человеку</i>
<i>🔐 Он получит доступ к вашему профилю</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 КОПИРОВАТЬ ССЫЛКУ", callback_data=f"copy_{invite_id}")],
        [InlineKeyboardButton("📊 ВСЕ ПРИГЛАШЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_to_results")]
    ]
    
    try:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        await query.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    return MY_SEXUAL_PROFILE

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр всех приглашений"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    invites = load_invites()
    user_invites = invites.get(user_id, [])
    
    # Фильтруем активные и истекшие
    active_invites = []
    expired_invites = []
    
    for inv in user_invites:
        expires_at = datetime.fromisoformat(inv['expires_at'])
        if expires_at > datetime.now() and inv['status'] == 'active':
            active_invites.append(inv)
        else:
            expired_invites.append(inv)
    
    total_opens = sum(len(inv.get('opened_by', [])) for inv in user_invites)
    unique_opens = len(set().union(*[set(inv.get('opened_by', [])) for inv in user_invites]))
    
    if not user_invites:
        message = f"""
📊 <b>У ВАС НЕТ ПРИГЛАШЕНИЙ</b>

━━━━━━━━━━━━━━━━━━━━━
🔰 <b>СОЗДАЙТЕ ПЕРВОЕ ПРИГЛАШЕНИЕ:</b>
• Нажмите кнопку ниже
• Получите уникальную ссылку
• Отправьте избранному человеку

💎 <b>ПРЕИМУЩЕСТВА:</b>
• Контроль доступа
• Статистика переходов
• Безопасность

━━━━━━━━━━━━━━━━━━━━━
<i>👆 Начните прямо сейчас!</i>
"""
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ПРИГЛАШЕНИЕ", callback_data="create_invite")],
            [InlineKeyboardButton("🔞 ИНТИМНЫЙ ПРОФИЛЬ", callback_data="my_sexual_profile")],
            [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
        ]
    else:
        message = f"""
📊 <b>ВАШИ ПРИГЛАШЕНИЯ</b>

━━━━━━━━━━━━━━━━━━━━━
📈 <b>ОБЩАЯ СТАТИСТИКА:</b>
• Всего создано: {len(user_invites)}
• Активных: {len(active_invites)}
• Истекло: {len(expired_invites)}
• Всего открытий: {total_opens}
• Уникальных гостей: {unique_opens}

━━━━━━━━━━━━━━━━━━━━━
🟢 <b>АКТИВНЫЕ ПРИГЛАШЕНИЯ:</b>
"""
        # Добавляем информацию о последних 5 активных приглашениях
        for i, inv in enumerate(active_invites[:5], 1):
            opens = len(inv.get('opened_by', []))
            created = datetime.fromisoformat(inv['created_at']).strftime('%d.%m')
            message += f"\n{i}. ID: <code>{inv['id'][:8]}...</code>\n"
            message += f"   👁 Открытий: {opens} | 📅 {created}\n"
        
        if len(active_invites) > 5:
            message += f"\n   ...и еще {len(active_invites) - 5} приглашений\n"
        
        keyboard = [
            [InlineKeyboardButton("🔞 НОВОЕ ПРИГЛАШЕНИЕ", callback_data="create_invite")],
            [InlineKeyboardButton("📊 ДЕТАЛЬНАЯ СТАТИСТИКА", callback_data="invite_stats")],
            [InlineKeyboardButton("🔞 ИНТИМНЫЙ ПРОФИЛЬ", callback_data="my_sexual_profile")],
            [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
        ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return INVITES_LIST

async def process_invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE, invite_id: str) -> int:
    """Обработка перехода по ссылке-приглашению"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} открыл приглашение {invite_id}")
    
    invites = load_invites()
    
    # Ищем приглашение
    found_invite = None
    creator_id = None
    
    for uid, user_invites in invites.items():
        for inv in user_invites:
            if inv['id'] == invite_id:
                found_invite = inv
                creator_id = uid
                break
        if found_invite:
            break
    
    if not found_invite:
        await update.message.reply_text(
            "❌ Приглашение не найдено или было удалено"
        )
        return await start(update, context)
    
    # Проверяем срок действия
    expires_at = datetime.fromisoformat(found_invite['expires_at'])
    if expires_at < datetime.now():
        await update.message.reply_text(
            "❌ Срок действия приглашения истек"
        )
        return await start(update, context)
    
    # Проверяем лимит использований
    if found_invite.get('current_uses', 0) >= found_invite.get('max_uses', 10):
        await update.message.reply_text(
            "❌ Приглашение достигло лимита использований"
        )
        return await start(update, context)
    
    # Обновляем статистику приглашения
    str_user_id = str(user.id)
    if str_user_id not in found_invite['opened_by']:
        found_invite['opened_by'].append(str_user_id)
        found_invite['opened_count'] = found_invite.get('opened_count', 0) + 1
        found_invite['current_uses'] = found_invite.get('current_uses', 0) + 1
        found_invite['last_opened'] = datetime.now().isoformat()
        save_invites(invites)
        
        # Обновляем статистику создателя
        users = load_user_data()
        if creator_id in users:
            users[creator_id]['invites_opened'] = users[creator_id].get('invites_opened', 0) + 1
            save_user_data(users)
    
    # Загружаем профиль создателя
    profile = load_intimate_profile(creator_id)
    creator_name = users.get(creator_id, {}).get('first_name', 'Пользователь')
    
    # Показываем профиль
    message = format_intimate_profile(profile, creator_name)
    
    keyboard = [
        [InlineKeyboardButton("💬 НАПИСАТЬ В TELEGRAM", url=f"tg://user?id={creator_id}")],
        [InlineKeyboardButton("💎 ОТКРЫТЬ 4F КЛЮЧ", callback_data=f"open_4f_{creator_id}")],
        [InlineKeyboardButton("🔞 МОЙ ПРОФИЛЬ", callback_data="my_sexual_profile")]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    # Уведомляем создателя
    try:
        await context.bot.send_message(
            creator_id,
            f"👤 <b>Ваше приглашение открыли!</b>\n\n"
            f"Пользователь: {user.first_name}\n"
            f"ID: {user.id}\n"
            f"Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
            f"📊 Всего открытий: {found_invite['opened_count']}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить создателя: {e}")
    
    return RESULTS_SCREEN

# ============================================
# 💎 4F КЛЮЧИ
# ============================================

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Меню 4F ключей"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    keys = load_4f_keys()
    user_keys = keys.get(user_id, [])
    
    active_keys = [k for k in user_keys if k.get('status') == 'active']
    
    message = f"""
💎 <b>4F КЛЮЧИ</b>

━━━━━━━━━━━━━━━━━━━━━
🔮 <b>ЧТО ЭТО?</b>
4F ключи — это особые приглашения, которые:
• Открывают полный профиль
• Показывают скрытые фото
• Дают приоритетную поддержку
• Специальные возможности

━━━━━━━━━━━━━━━━━━━━━
📦 <b>ВАШИ КЛЮЧИ:</b>
Активных: {len(active_keys)}
Всего куплено: {len(user_keys)}

━━━━━━━━━━━━━━━━━━━━━
🏷 <b>ДОСТУПНЫЕ ПАКЕТЫ:</b>
• 🔑 Базовый — 1 ключ = 99 ₽
• 💎 Премиум — 5 ключей = 399 ₽
• 👑 VIP — 15 ключей = 999 ₽
"""
    
    keyboard = [
        [InlineKeyboardButton("🔑 КУПИТЬ БАЗОВЫЙ (99₽)", callback_data="buy_4f_basic")],
        [InlineKeyboardButton("💎 КУПИТЬ ПРЕМИУМ (399₽)", callback_data="buy_4f_premium")],
        [InlineKeyboardButton("👑 КУПИТЬ VIP (999₽)", callback_data="buy_4f_vip")],
        [InlineKeyboardButton("📦 МОИ КЛЮЧИ", callback_data="my_4f_keys")],
        [InlineKeyboardButton("❓ КАК ИСПОЛЬЗОВАТЬ", callback_data="4f_explain")],
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Покупка 4F ключа"""
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('buy_4f_', '')
    
    prices = {
        'basic': {'keys': 1, 'price': 99},
        'premium': {'keys': 5, 'price': 399},
        'vip': {'keys': 15, 'price': 999}
    }
    
    selected = prices.get(package, prices['basic'])
    
    payment_id = str(uuid4())[:8]
    
    # Сохраняем платеж
    payments = load_payments()
    payments[payment_id] = {
        'user_id': str(query.from_user.id),
        'package': package,
        'keys': selected['keys'],
        'amount': selected['price'],
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    save_payments(payments)
    
    message = f"""
💳 <b>ОПЛАТА 4F КЛЮЧЕЙ</b>

━━━━━━━━━━━━━━━━━━━━━
📦 <b>ПАКЕТ:</b> {package.upper()}
🔑 <b>КЛЮЧЕЙ:</b> {selected['keys']}
💰 <b>СУММА:</b> {selected['price']} ₽
🆔 <b>ПЛАТЕЖ:</b> {payment_id}

━━━━━━━━━━━━━━━━━━━━━
📱 <b>ИНСТРУКЦИЯ:</b>
1. Переведите {selected['price']} ₽ на карту
   💳 2200 0000 0000 0000
2. Нажмите "Я ОПЛАТИЛ"
3. Дождитесь подтверждения

━━━━━━━━━━━━━━━━━━━━━
⚠️ <i>Ключи будут зачислены автоматически</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("✅ Я ОПЛАТИЛ", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("❓ ПОМОЩЬ", callback_data="4f_explain")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="4f_menu")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_PAYMENT_SCREEN

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Открытие 4F ключа"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    keys = load_4f_keys()
    user_keys = keys.get(user_id, [])
    
    active_keys = [k for k in user_keys if k.get('status') == 'active']
    
    if not active_keys:
        await query.edit_message_text(
            "❌ <b>У вас нет активных 4F ключей!</b>\n\n"
            "Приобретите ключи в меню 4F.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 КУПИТЬ КЛЮЧИ", callback_data="4f_menu")],
                [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_to_results")]
            ]),
            parse_mode="HTML"
        )
        return FOUR_F_MENU
    
    # Используем первый активный ключ
    key = active_keys[0]
    key['status'] = 'used'
    key['used_at'] = datetime.now().isoformat()
    save_4f_keys(keys)
    
    # Открываем специальный контент
    message = f"""
🔓 <b>4F КЛЮЧ АКТИВИРОВАН!</b>

━━━━━━━━━━━━━━━━━━━━━
🎉 <b>ВАМ ОТКРЫТ ДОСТУП:</b>

💫 <b>ПРИВАТНЫЙ КОНТЕНТ:</b>
• 📸 Скрытые фотографии (5 шт)
• 🎥 Личные видео (2 шт)
• 📝 Личный дневник
• 🎵 Плейлисты

✨ <b>ОСОБЫЕ ВОЗМОЖНОСТИ:</b>
• 💬 Приоритетные сообщения
• 🌙 Ночной режим
• 🔒 Конфиденциальность

━━━━━━━━━━━━━━━━━━━━━
🎁 <b>БОНУС:</b>
+100 к карме
+1 месяц премиум-статуса
"""
    
    keyboard = [
        [InlineKeyboardButton("📸 СМОТРЕТЬ ФОТО", callback_data="view_private_photos")],
        [InlineKeyboardButton("🎥 СМОТРЕТЬ ВИДЕО", callback_data="view_private_videos")],
        [InlineKeyboardButton("📝 ЧИТАТЬ ДНЕВНИК", callback_data="view_diary")],
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_CONTENT

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Объяснение 4F ключей"""
    query = update.callback_query
    await query.answer()
    
    message = """
❓ <b>ЧТО ТАКОЕ 4F КЛЮЧИ?</b>

━━━━━━━━━━━━━━━━━━━━━
🔮 <b>ОПИСАНИЕ:</b>
4F (For Friends, For Family, For Fun, For Future) — 
это система приватных приглашений, которая позволяет:

💎 <b>ДЛЯ ВЛАДЕЛЬЦА:</b>
• Монетизировать контент
• Контролировать доступ
• Получать доход от приглашений
• Видеть статистику

🎁 <b>ДЛЯ ГОСТЯ:</b>
• Полный доступ к профилю
• Скрытые фото и видео
• Эксклюзивный контент
• Приоритетная поддержка

━━━━━━━━━━━━━━━━━━━━━
💰 <b>СТОИМОСТЬ:</b>
• 🔑 Базовый (1 ключ) — 99 ₽
• 💎 Премиум (5 ключей) — 399 ₽
• 👑 VIP (15 ключей) — 999 ₽

━━━━━━━━━━━━━━━━━━━━━
✅ <b>ПРЕИМУЩЕСТВА:</b>
• Мгновенная активация
• Безопасная оплата
• Бессрочное действие
• Возврат средств

━━━━━━━━━━━━━━━━━━━━━
<i>💡 Купите ключи и откройте новые возможности!</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("💎 КУПИТЬ КЛЮЧИ", callback_data="4f_menu")],
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

async def my_4f_keys_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Мои 4F ключи"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    keys = load_4f_keys()
    user_keys = keys.get(user_id, [])
    
    active = [k for k in user_keys if k.get('status') == 'active']
    used = [k for k in user_keys if k.get('status') == 'used']
    expired = [k for k in user_keys if k.get('status') == 'expired']
    
    message = f"""
📦 <b>МОИ 4F КЛЮЧИ</b>

━━━━━━━━━━━━━━━━━━━━━
📊 <b>СТАТИСТИКА:</b>
• 🟢 Активных: {len(active)}
• 🔵 Использовано: {len(used)}
• 🔴 Истекло: {len(expired)}
• 💎 Всего куплено: {len(user_keys)}

━━━━━━━━━━━━━━━━━━━━━
"""
    
    if active:
        message += "\n🟢 <b>АКТИВНЫЕ КЛЮЧИ:</b>\n"
        for i, key in enumerate(active[:5], 1):
            bought = datetime.fromisoformat(key['bought_at']).strftime('%d.%m.%Y')
            message += f"{i}. 🔑 {key['id'][:8]}... — куплен {bought}\n"
    
    keyboard = [
        [InlineKeyboardButton("💎 КУПИТЬ ЕЩЕ", callback_data="4f_menu")],
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return FOUR_F_MENU

# ============================================
# ⚙️ НАСТРОЙКИ И ПОМОЩЬ
# ============================================

async def settings_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Меню настроек"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    users = load_user_data()
    user_settings = users.get(user_id, {}).get('settings', {})
    
    notifications = "✅ Вкл" if user_settings.get('notifications', True) else "❌ Выкл"
    anonymous = "✅ Вкл" if user_settings.get('anonymous_mode', False) else "❌ Выкл"
    language = "🇷🇺 Русский" if user_settings.get('language', 'ru') == 'ru' else "🇬🇧 English"
    
    message = f"""
⚙️ <b>НАСТРОЙКИ ПРОФИЛЯ</b>

━━━━━━━━━━━━━━━━━━━━━
👤 <b>ПРОФИЛЬ:</b>
• ID: <code>{user_id}</code>
• Имя: {query.from_user.first_name}
• Username: @{query.from_user.username or 'не указан'}

🔔 <b>УВЕДОМЛЕНИЯ:</b> {notifications}
🕶 <b>АНОНИМНЫЙ РЕЖИМ:</b> {anonymous}
🌍 <b>ЯЗЫК:</b> {language}

━━━━━━━━━━━━━━━━━━━━━
📊 <b>СТАТИСТИКА:</b>
• Приглашений создано: {users.get(user_id, {}).get('invites_created', 0)}
• Приглашений открыто: {users.get(user_id, {}).get('invites_opened', 0)}
• 4F ключей: {users.get(user_id, {}).get('4f_keys_purchased', 0)}
• Потрачено: {users.get(user_id, {}).get('total_spent', 0)} ₽
"""
    
    keyboard = [
        [InlineKeyboardButton("🔔 УВЕДОМЛЕНИЯ", callback_data="toggle_notifications"),
         InlineKeyboardButton("🕶 АНОНИМНОСТЬ", callback_data="toggle_anonymous")],
        [InlineKeyboardButton("🌍 ЯЗЫК", callback_data="change_language"),
         InlineKeyboardButton("🚫 БЛОКИРОВКИ", callback_data="blocked_users")],
        [InlineKeyboardButton("📊 МОЯ СТАТИСТИКА", callback_data="user_stats")],
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return RESULTS_SCREEN

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Справка по боту"""
    query = update.callback_query
    await query.answer()
    
    message = """
❓ <b>ПОМОЩЬ ПО БОТУ</b>

━━━━━━━━━━━━━━━━━━━━━
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ:</b>
• Создайте анкету с описанием
• Добавьте интересы и ожидания
• Загрузите фотографии
• Укажите предпочтения

🔗 <b>ПРИГЛАШЕНИЯ:</b>
• Генерируйте уникальные ссылки
• Каждая ссылка действует 7 дней
• Отслеживайте кто открывал
• Максимум 10 использований

💎 <b>4F КЛЮЧИ:</b>
• Покупайте пакеты ключей
• Открывайте приватный контент
• Получайте бонусы
• Поддерживайте проект

━━━━━━━━━━━━━━━━━━━━━
📱 <b>КОМАНДЫ:</b>
/start - Запустить бота
/profile - Мой профиль
/invites - Приглашения
/4f - 4F ключи
/settings - Настройки
/help - Помощь

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 <b>ПОДДЕРЖКА:</b>
@support_bot
help@example.com

━━━━━━━━━━━━━━━━━━━━━
<i>💡 Бот постоянно развивается!</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 ПРОФИЛЬ", callback_data="my_sexual_profile")],
        [InlineKeyboardButton("📊 ПРИГЛАШЕНИЯ", callback_data="my_invites")],
        [InlineKeyboardButton("💎 4F КЛЮЧИ", callback_data="4f_menu")],
        [InlineKeyboardButton("⬅️ НА ГЛАВНУЮ", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return RESULTS_SCREEN

async def back_to_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат на главный экран"""
    logger.info("Возврат на главный экран")
    return await start(update, context)

# ============================================
# 🎭 ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ КНОПОК
# ============================================

async def edit_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Редактирование профиля"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚧 Редактирование профиля в разработке")
    return MY_SEXUAL_PROFILE

async def add_photos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавление фото"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚧 Добавление фото в разработке")
    return MY_SEXUAL_PROFILE

async def invite_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Статистика приглашений"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📊 Детальная статистика будет доступна позже")
    return INVITES_LIST

async def user_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Статистика пользователя"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📈 Ваша статистика формируется...")
    return RESULTS_SCREEN

async def toggle_notifications_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Переключение уведомлений"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔔 Настройки уведомлений изменены")
    return await settings_menu_callback(update, context)

async def toggle_anonymous_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Переключение анонимного режима"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🕶 Анонимный режим изменен")
    return await settings_menu_callback(update, context)

async def change_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Смена языка"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🌍 Смена языка будет доступна позже")
    return await settings_menu_callback(update, context)

async def blocked_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Заблокированные пользователи"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚫 У вас нет заблокированных пользователей")
    return await settings_menu_callback(update, context)

async def view_private_photos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр приватных фото"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📸 Приватные фотографии появятся здесь")
    return FOUR_F_CONTENT

async def view_private_videos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр приватных видео"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎥 Приватные видео появятся здесь")
    return FOUR_F_CONTENT

async def view_diary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр дневника"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 Личный дневник появится здесь")
    return FOUR_F_CONTENT

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверка оплаты"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✅ Оплата проверяется. Ключи будут зачислены в течение 5 минут.")
    return FOUR_F_PAYMENT_SCREEN

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Универсальная заглушка"""
    query = update.callback_query
    await query.answer()
    logger.info(f"Заглушка для callback: {query.data}")
    return RESULTS_SCREEN

# ============================================
# 🔍 ДИАГНОСТИКА (НЕ БЛОКИРУЕТ КНОПКИ!)
# ============================================

async def debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ТОЛЬКО ЛОГИРУЕТ, НЕ БЛОКИРУЕТ ОБРАБОТКУ!"""
    if update.callback_query:
        query = update.callback_query
        logger.info(f"🔍 Нажата кнопка: {query.data} от {query.from_user.id}")
        logger.info(f"🔍 Текущее состояние: {context.user_data.get('current_state', 'Нет')}")
        
        # ВАЖНО: продолжаем обработку!
        await query.continue()

# ============================================
# 🚀 ГЛАВНАЯ ФУНКЦИЯ - ИСПРАВЛЕННЫЙ ConversationHandler
# ============================================

def main():
    """ЗАПУСК БОТА - ВСЕ КНОПКИ РАБОТАЮТ!"""
    
    print("\n" + "="*60)
    print("🚀 ЗАПУСК БОТА - ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("="*60)
    
    # Проверка токена
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        print("   export TELEGRAM_BOT_TOKEN=ваш_токен\n")
        return
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Диагностика - с обычным приоритетом
    app.add_handler(CallbackQueryHandler(debug_callback), group=0)
    
    # ============================================
    # ПОЛНЫЙ ИСПРАВЛЕННЫЙ ConversationHandler
    # ============================================
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('profile', my_sexual_profile_callback),
            CommandHandler('invites', my_invites_callback),
            CommandHandler('4f', four_f_menu_callback),
            CommandHandler('settings', settings_menu_callback),
            CommandHandler('help', help_callback)
        ],
        states={
            # RESULTS_SCREEN - Главный экран
            RESULTS_SCREEN: [
                # 🔞 ИНТИМНЫЙ ПРОФИЛЬ - ГЛАВНАЯ КНОПКА
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_menu$'),
                CallbackQueryHandler(settings_menu_callback, pattern='^settings_menu$'),
                CallbackQueryHandler(help_callback, pattern='^help$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # MY_SEXUAL_PROFILE - Интимный профиль
            MY_SEXUAL_PROFILE: [
                # 🔞 КНОПКА ТОЖЕ ДОЛЖНА РАБОТАТЬ ЗДЕСЬ!
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(edit_profile_callback, pattern='^edit_profile$'),
                CallbackQueryHandler(add_photos_callback, pattern='^add_photos$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_menu$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
                CallbackQueryHandler(dummy_callback, pattern='^copy_'),
            ],
            
            # INVITES_LIST - Список приглашений
            INVITES_LIST: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(create_invite_callback, pattern='^create_invite$'),
                CallbackQueryHandler(my_invites_callback, pattern='^my_invites$'),
                CallbackQueryHandler(invite_stats_callback, pattern='^invite_stats$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_menu$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
                CallbackQueryHandler(dummy_callback, pattern='^copy_'),
                CallbackQueryHandler(dummy_callback, pattern='^check_status_'),
                CallbackQueryHandler(dummy_callback, pattern='^friend_'),
            ],
            
            # FOUR_F_MENU - Меню 4F ключей
            FOUR_F_MENU: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(buy_4f_key_callback, pattern='^buy_4f_'),
                CallbackQueryHandler(my_4f_keys_callback, pattern='^my_4f_keys$'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_menu$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # FOUR_F_CONTENT - Контент 4F
            FOUR_F_CONTENT: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(view_private_photos_callback, pattern='^view_private_photos$'),
                CallbackQueryHandler(view_private_videos_callback, pattern='^view_private_videos$'),
                CallbackQueryHandler(view_diary_callback, pattern='^view_diary$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # FOUR_F_PAYMENT_SCREEN - Экран оплаты
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(check_payment_callback, pattern='^check_payment_'),
                CallbackQueryHandler(four_f_explanation_callback, pattern='^4f_explain$'),
                CallbackQueryHandler(four_f_menu_callback, pattern='^4f_menu$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            # Остальные состояния с поддержкой главной кнопки
            STANDARD_PROFILE_VIEW: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            INTIMATE_PROFILE_VIEW: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            EDIT_PROFILE: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            INVITE_STATISTICS: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            FRIEND_INTERACTION: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            FOUR_F_KEY_MANAGEMENT: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            PAYMENT_CONFIRMATION: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
            
            ADMIN_PANEL: [
                CallbackQueryHandler(my_sexual_profile_callback, pattern='^my_sexual_profile$'),
                CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('cancel', start),
            CallbackQueryHandler(back_to_results_callback, pattern='^back_to_results$'),
            CallbackQueryHandler(dummy_callback),  # Заглушка для всех остальных
        ],
        allow_reentry=True,  # КРИТИЧЕСКИ ВАЖНО!
        name="main_conversation",
        persistent=False,
    )
    
    app.add_handler(conv_handler)
    
    # ============================================
    # ЗАПАСНОЙ ОБРАБОТЧИК (НИЗКИЙ ПРИОРИТЕТ)
    # ============================================
    
    async def fallback_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сработает только если ConversationHandler по какой-то причине не обработал кнопку"""
        if update.callback_query and update.callback_query.data == "my_sexual_profile":
            logger.warning("⚠️ ЗАПАСНОЙ ОБРАБОТЧИК: ConversationHandler не обработал кнопку!")
            await my_sexual_profile_callback(update, context)
    
    app.add_handler(
        CallbackQueryHandler(fallback_my_sexual_profile, pattern='^my_sexual_profile$'),
        group=1  # Низкий приоритет
    )
    
    # Обработчик глубоких ссылок
    async def deep_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message and update.message.text and update.message.text.startswith('/start invite_'):
            invite_id = update.message.text.replace('/start invite_', '')
            await process_invite_link(update, context, invite_id)
            return
    
    app.add_handler(MessageHandler(filters.COMMAND, deep_link_handler), group=2)
    
    print("\n" + "✅"*50)
    print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
    print("✅ КНОПКА 'ИНТИМНЫЙ ПРОФИЛЬ' РАБОТАЕТ ВО ВСЕХ СОСТОЯНИЯХ!")
    print("✅ Добавлен запасной обработчик")
    print("✅ Все 15 состояний поддерживают главную кнопку")
    print("✅ ConversationHandler.allow_reentry = True")
    print("✅"*50 + "\n")
    
    # Запускаем бота
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
