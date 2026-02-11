#!/usr/bin/env python3
"""
МОДУЛЬ 18+: СЕКСУАЛЬНЫЕ ПРЕДПОЧТЕНИЯ
Версия 1.0 (ЗАГЛУШКА)
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
# ЭКРАНЫ
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
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_PROFILE_SCREEN

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения"""
    query = update.callback_query
    await query.answer()
    
    # Генерируем уникальный код
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/Testing_Lichnosti_bot?start={invite_code}"
    
    # Сохраняем в user_data
    context.user_data["current_invite"] = {
        "code": invite_code,
        "url": invite_url,
        "created_at": datetime.now().isoformat()
    }
    
    text = f"""
🔞 ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!

🔗 <code>{invite_url}</code>

✨ Как только друг пройдёт тест — 
   я сразу пришлю вам уведомление.

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
# ОБРАБОТЧИК DEEP LINK
# ============================================

async def handle_sexual_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Обработчик /start sex_xxx"""
    user = update.effective_user
    inviter_name = "друг"  # В реальности получим из БД
    
    text = f"""
🎁 Вас пригласил(а) {inviter_name}!

Пройдите тест — и {inviter_name} сможет узнать 
ваши 18+ предпочтения (только если захочет и заплатит 99₽).

<i>Вы тоже сможете приглашать друзей 
и узнавать их предпочтения.</i>

🚀 Начнём?
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Пройти тест", callback_data="start_test")]
    ]
    
    # Сохраняем информацию о приглашении
    context.user_data["invited_by"] = 123456789  # В реальности ID пригласившего
    context.user_data["invite_code"] = payload
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
