#!/usr/bin/env python3
"""
МОДУЛЬ 18+: СЕКСУАЛЬНЫЕ ПРЕДПОЧТЕНИЯ
Версия 1.2 (ИСПРАВЛЕНА: добавлен готовый текст для друга)
"""

import logging
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ============================================
# КОНСТАНТЫ
# ============================================

SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SEXUAL_PROFILE_PATH = "sexual_18/sa_5_int.json"

# Состояния для ConversationHandler
SEXUAL_PROFILE_SCREEN = 100
SEXUAL_INVITES_LIST = 101
SEXUAL_FRIEND_PROFILE = 102

# ============================================
# ЗАГРУЗЧИК ПРОФИЛЯ (ВСЕГДА ЗАГЛУШКА)
# ============================================

def load_sexual_profile() -> Dict[str, Any]:
    """ЗАГЛУШКА: Всегда загружает sa_5_int.json"""
    try:
        if not os.path.exists(SEXUAL_PROFILE_PATH):
            logger.error(f"Файл не найден: {SEXUAL_PROFILE_PATH}")
            return get_emergency_profile()
        
        with open(SEXUAL_PROFILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        return get_emergency_profile()

def get_emergency_profile() -> Dict[str, Any]:
    """Аварийный профиль"""
    return {
        "profile_key": "sa_5_int",
        "header": "🔞 ВАШ ИНТИМНЫЙ ПРОФИЛЬ",
        "title": "ИЩИ СИСТЕМУ",
        "description": "Временно недоступно",
        "turn_ons": [],
        "blocks": [],
        "erogenous_zone": {},
        "ideal_partner": "",
        "tool": {"name": "", "steps": []},
        "dynamics": {}
    }

# ============================================
# ФОРМАТИРОВАНИЕ ПРОФИЛЯ (КРАТКО)
# ============================================

def format_sexual_profile(profile: Dict[str, Any], username: str = "Вы") -> str:
    """Форматирует профиль для Telegram (максимум 3500 символов)"""
    
    text = f"""
{SEXUAL_DIVIDER}
🔞 18+ ПРОФИЛЬ: {username}
🧠 ПРОФИЛЬ: {profile.get('profile_key', 'SA_5_INT').upper()}

{profile.get('description', '')[:300]}

🔴 ВКЛЮЧАЕТ:
"""
    # Turn-ons
    for item in profile.get('turn_ons', [])[:2]:
        text += f"• {item.get('title', '')}: {item.get('description', '')[:100]}...\n"
    
    # Фетиши (добавим позже)
    text += f"""
⚠️ БЛОК:
{profile.get('blocks', [{}])[0].get('description', '')[:200] if profile.get('blocks') else ''}

🔴 ЭРОГЕННАЯ ЗОНА:
{profile.get('erogenous_zone', {}).get('trigger', '')[:100]}

💞 ИДЕАЛЬНЫЙ ПАРТНЁР:
{profile.get('ideal_partner', '')[:200]}

🛠 {profile.get('tool', {}).get('name', 'ПРОТОКОЛ')}:
"""
    for step in profile.get('tool', {}).get('steps', [])[:2]:
        text += f"{step}\n"

    text += f"""
{SEXUAL_DIVIDER}
💞 У КАЖДОГО ЕСТЬ ТАЙНЫ.
🔓 ВАШ КЛЮЧ К ПРАВДЕ:

❶ Пригласите → 0₽
❷ Друг проходит тест (3 мин)
❸ Мы пришлём уведомление
❹ 99₽ = доступ к его 18+ профилю

⚠️ Только вы. Только правда. Без стыда.
{SEXUAL_DIVIDER}
"""
    return text

# ============================================
# ЭКРАН: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def show_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль (ЗАГЛУШКА)"""
    query = update.callback_query
    await query.answer()
    
    # Загружаем профиль-заглушку
    profile = load_sexual_profile()
    
    # Форматируем текст
    text = format_sexual_profile(profile, update.effective_user.first_name)
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton("🔞 Узнать предпочтения друга — 99₽", callback_data="sexual_invite_start")],
        [InlineKeyboardButton("🔍 Мои приглашения", callback_data="show_my_invites")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_PROFILE_SCREEN

# ============================================
# 🔥 ЭКРАН: СОЗДАНИЕ ПРИГЛАШЕНИЯ + ТЕКСТ ДЛЯ ДРУГА
# ============================================

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения + готовый текст для друга"""
    query = update.callback_query
    await query.answer()
    
    # Генерируем уникальный код
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/Testing_Lichnosti_bot?start={invite_code}"
    
    # 🔥 ТЕКСТ ДЛЯ ДРУГА (универсальный, без пола, без скобок)
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "У меня — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
    )
    
    # Создаем объект приглашения
    invite = {
        "code": invite_code,
        "url": invite_url,
        "message": invite_message,  # ✅ Сохраняем текст для истории
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "friend_id": None,
        "friend_name": None,
        "payment_status": None
    }
    
    # Сохраняем текущее приглашение
    context.user_data["current_invite"] = invite
    
    # Добавляем в список приглашений
    invites = context.user_data.get("sexual_invites", [])
    invites.insert(0, invite)
    context.user_data["sexual_invites"] = invites
    
    # 🔥 ЭКРАН С ГОТОВЫМ ТЕКСТОМ
    text = f"""
{SEXUAL_DIVIDER}
🔞 ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!
{SEXUAL_DIVIDER}

🔗 <code>{invite_url}</code>

💬 ГОТОВЫЙ ТЕКСТ ДЛЯ ДРУГА:
<code>{invite_message}</code>

✨ Просто скопируй всё сообщение целиком
   и отправь другу.

👉 99₽ = доступ к его 18+ профилю
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Копировать ссылку", callback_data=f"copy_invite_{invite_code}")],
        [InlineKeyboardButton("🔍 Мои приглашения", callback_data="show_my_invites")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_INVITES_LIST

# ============================================
# ЭКРАН: МОИ ПРИГЛАШЕНИЯ
# ============================================

async def show_my_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔍 МОИ ПРИГЛАШЕНИЯ
    Показывает список созданных приглашений и их статус
    """
    query = update.callback_query
    await query.answer()
    
    # Получаем список приглашений из user_data
    invites = context.user_data.get("sexual_invites", [])
    current_invite = context.user_data.get("current_invite")
    
    # Если есть текущее приглашение, но его нет в списке - добавляем
    if current_invite and current_invite not in invites:
        invites.insert(0, current_invite)
        context.user_data["sexual_invites"] = invites
    
    if not invites:
        # Нет ни одного приглашения
        text = f"""
{SEXUAL_DIVIDER}
🔍 МОИ ПРИГЛАШЕНИЯ
{SEXUAL_DIVIDER}

У вас пока нет активных приглашений.

✨ Создайте ссылку-приглашение, чтобы узнать 
18+ предпочтения друзей.

👉 99₽ = доступ к профилю друга
{SEXUAL_DIVIDER}
"""
        keyboard = [
            [InlineKeyboardButton("🔞 Создать приглашение", callback_data="sexual_invite_start")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
    else:
        # Показываем список приглашений
        text = f"""
{SEXUAL_DIVIDER}
🔍 МОИ ПРИГЛАШЕНИЯ
{SEXUAL_DIVIDER}

📋 Всего создано: {len(invites)}

"""
        # Добавляем первые 3 приглашения (остальные скрыты)
        for i, invite in enumerate(invites[:3], 1):
            code = invite.get('code', '')[:12]
            created_at = invite.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    created_at = dt.strftime("%d.%m.%Y")
                except:
                    created_at = created_at[:10]
            else:
                created_at = "только что"
            
            # Статус (всегда "ожидает" в заглушке)
            status = "⏳ Ожидает"
            
            text += f"{i}. <code>{code}</code>\n   📅 {created_at} • {status}\n\n"
        
        if len(invites) > 3:
            text += f"...и ещё {len(invites) - 3} приглашений\n\n"
        
        text += f"""
{SEXUAL_DIVIDER}
💞 Как только друг пройдёт тест —
   я сразу пришлю уведомление.

👉 99₽ = доступ к его 18+ профилю
{SEXUAL_DIVIDER}
"""
        keyboard = [
            [InlineKeyboardButton("🔞 Создать новое приглашение", callback_data="sexual_invite_start")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_INVITES_LIST

# ============================================
# ОБРАБОТЧИКИ КНОПОК
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки копирования ссылки"""
    query = update.callback_query
    await query.answer("📋 Ссылка скопирована в буфер обмена!", show_alert=False)
    return SEXUAL_INVITES_LIST

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer("⏳ Приглашение ожидает активации", show_alert=True)
    return SEXUAL_INVITES_LIST

async def delete_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление приглашения"""
    query = update.callback_query
    await query.answer("❌ Приглашение удалено", show_alert=True)
    return SEXUAL_INVITES_LIST

# ============================================
# ОБРАБОТЧИК DEEP LINK
# ============================================

async def handle_sexual_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Обработчик /start sex_xxx"""
    user = update.effective_user
    
    # Извлекаем код приглашения
    invite_code = payload
    
    # В заглушке всегда один и тот же друг
    inviter_name = "Александр"
    inviter_id = 123456789
    
    text = f"""
{SEXUAL_DIVIDER}
🎁 Вас пригласил(а) {inviter_name}!
{SEXUAL_DIVIDER}

Пройдите тест — и {inviter_name} сможет узнать 
ваши 18+ предпочтения (только если захочет и заплатит 99₽).

<i>Вы тоже сможете приглашать друзей 
и узнавать их предпочтения.</i>

⏱ Тест займёт всего 3 минуты
🔒 Полная анонимность
💞 Только правда, без стыда

{SEXUAL_DIVIDER}
🚀 Начнём?
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Пройти тест", callback_data="start_test")]
    ]
    
    # Сохраняем информацию о приглашении
    context.user_data["invited_by"] = inviter_id
    context.user_data["invite_code"] = payload
    context.user_data["inviter_name"] = inviter_name
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================
# ЭКСПОРТ (ВСЕ ФУНКЦИИ ДЛЯ main_bot.py)
# ============================================

__all__ = [
    'show_my_sexual_profile',
    'sexual_invite_start',
    'show_my_invites',
    'handle_sexual_deeplink',
    'copy_invite_callback',
    'check_invite_callback',
    'delete_invite_callback',
    'SEXUAL_PROFILE_SCREEN',
    'SEXUAL_INVITES_LIST',
    'SEXUAL_FRIEND_PROFILE'
]
