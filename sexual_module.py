#!/usr/bin/env python3
"""
МОДУЛЬ 18+: СЕКСУАЛЬНЫЕ ПРЕДПОЧТЕНИЯ + 4F-ФУНКЦИИ
Версия 2.0 (ПОЛНАЯ ИНТЕГРАЦИЯ 4F-КЛЮЧЕЙ)
"""

import logging
import os
import json
import uuid
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ============================================
# КОНСТАНТЫ
# ============================================

SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SEXUAL_PROFILE_PATH = "профили/сексуальный_18/sa_5_int.json"
FOUR_F_BASE_PATH = "профили/4F"

# Состояния для ConversationHandler
SEXUAL_PROFILE_SCREEN = 100
SEXUAL_INVITES_LIST = 101
SEXUAL_FRIEND_PROFILE = 102
FOUR_F_PAYMENT_SCREEN = 103
FOUR_F_CONTENT_SCREEN = 104

# API URL для платежей
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")

# ============================================
# ЗАГРУЗЧИК ПРОФИЛЕЙ
# ============================================

def load_sexual_profile() -> Dict[str, Any]:
    """Загружает интимный профиль (всегда sa_5_int для заглушки)"""
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
    """Аварийный интимный профиль"""
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
# 🔥 4F-ЗАГРУЗЧИК И ФОРМАТТЕР
# ============================================

def get_4f_function(function: str, profile_key: str = "sa_4_cap") -> Dict[str, Any]:
    """
    Загружает 4F-функцию из JSON-файла
    Правило MVP: Всегда используем sa_4_cap.json как демо для всех профилей
    """
    try:
        # Всегда берем sa_4_cap.json для демо-режима
        file_path = os.path.join(FOUR_F_BASE_PATH, function, "sa_4_cap.json")
        
        if not os.path.exists(file_path):
            logger.warning(f"Файл {file_path} не найден, беру default.json")
            file_path = os.path.join(FOUR_F_BASE_PATH, function, "default.json")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            content["is_demo"] = True
            content["source_profile"] = "sa_4_cap"
            return content
    except Exception as e:
        logger.error(f"Ошибка загрузки 4F: {e}")
        return {
            "function": function,
            "is_demo": True,
            "is_stub": True,
            "short_description": "Ключ временно недоступен",
            "content": {"message": "Ведутся технические работы"},
            "demo_limitation": {
                "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
                "content": ["Полный набор триггеров", "Индивидуальные протоколы"],
                "price": 99,
                "upgrade": f"/buy_function_{function}_full"
            }
        }

def format_4f_message(content: Dict[str, Any], friend_name: str) -> str:
    """
    Форматирует JSON 4F в красивое Telegram-сообщение
    Подставляет имя друга в текст
    """
    # Заменяем {friend_name} во всем контенте
    content_str = json.dumps(content, ensure_ascii=False)
    content_str = content_str.replace("{friend_name}", friend_name)
    content = json.loads(content_str)
    
    function_emojis = {
        "1F": "🔥",
        "2F": "🍽",
        "3F": "⚡",
        "4F": "💡"
    }
    
    function_names = {
        "1F": "КЛЮЧ ВОЗБУЖДЕНИЯ",
        "2F": "КЛЮЧ ГОЛОДА",
        "3F": "КЛЮЧ СТРАХА",
        "4F": "КЛЮЧ ИДЕИ"
    }
    
    func = content.get("function", "1F")
    emoji = function_emojis.get(func, "🔑")
    func_name = function_names.get(func, "")
    
    # Начинаем сборку сообщения
    text = f"""
{SEXUAL_DIVIDER}
{emoji} <b>{func} {func_name}</b>
{SEXUAL_DIVIDER}

<b>У профиля SA-4_CAP «{friend_name}»</b>

{content.get('short_description', '')}

{SEXUAL_DIVIDER}
"""
    
    # Core секция
    core = content.get("core", {})
    if core:
        text += f"""
<b>{core.get('title', '🧬 РЕПТИЛОЙДНЫЙ КОД')}</b>
{core.get('description', '')}

"""
    
    # Psychology секция
    psychology = content.get("psychology", {})
    if psychology:
        text += f"""
<b>{psychology.get('title', '🎭 ПСИХОЛОГИЧЕСКИЙ ПОРТРЕТ')}</b>
{psychology.get('content', '')}

"""
    
    # Триггеры (специфично для каждой функции)
    if func == "1F":
        triggers = content.get("sexual_arousal", {}).get("triggers", [])
        if triggers:
            text += "<b>🎯 ТРИГГЕР-ФРАЗЫ:</b>\n\n"
            for i, t in enumerate(triggers[:3], 1):
                text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                text += f"   {t.get('effect', '')}\n\n"
    
    elif func == "2F":
        triggers = content.get("triggers", {})
        if triggers:
            text += "<b>🎯 ТРИГГЕРЫ ГОЛОДА:</b>\n\n"
            for i in range(1, 4):
                t = triggers.get(f"trigger_{i}", {})
                if t:
                    text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                    text += f"   {t.get('effect', '')}\n\n"
    
    elif func == "3F":
        antidotes = content.get("antidotes", {})
        if antidotes:
            text += "<b>💊 ПРОТИВОЯДИЯ:</b>\n\n"
            for i in range(1, 4):
                a = antidotes.get(f"antidote_{i}", {})
                if a:
                    text += f"{i}. <i>«{a.get('phrase', '')}»</i>\n"
                    text += f"   {a.get('effect', '')}\n\n"
    
    elif func == "4F":
        triggers = content.get("triggers", {})
        if triggers:
            text += "<b>🎯 ВОПРОСЫ-КЛЮЧИ:</b>\n\n"
            for i in range(1, 4):
                t = triggers.get(f"trigger_{i}", {})
                if t:
                    text += f"{i}. <i>«{t.get('phrase', '')}»</i>\n"
                    text += f"   {t.get('effect', '')}\n\n"
    
    # Демо-лимитация и продажа полной версии
    if content.get("is_demo", False):
        demo = content.get("demo_limitation", {})
        text += f"""
{SEXUAL_DIVIDER}
⚠️ <b>ЭТО ДЕМО-ВЕРСИЯ</b>

{demo.get('title', '📌 В ПОЛНОЙ ВЕРСИИ:')}
"""
        for item in demo.get("content", [])[:5]:
            text += f"{item}\n"
        
        text += f"""
{SEXUAL_DIVIDER}
💎 <b>Полная версия: {demo.get('price', 99)}₽</b>
🔓 Доступ навсегда
⚡ Мгновенная доставка

"""
    
    text += SEXUAL_DIVIDER
    return text

# ============================================
# ЭКРАН: МОЙ ИНТИМНЫЙ ПРОФИЛЬ
# ============================================

async def show_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль"""
    query = update.callback_query
    await query.answer()
    
    profile = load_sexual_profile()
    username = update.effective_user.first_name
    
    text = f"""
{SEXUAL_DIVIDER}
🔞 <b>18+ ПРОФИЛЬ: {username}</b>
🧠 <b>ПРОФИЛЬ:</b> {profile.get('profile_key', 'SA_5_INT').upper()}

{profile.get('description', '')[:300]}

<b>🔴 ВКЛЮЧАЕТ:</b>
"""
    for item in profile.get('turn_ons', [])[:2]:
        text += f"• {item.get('title', '')}: {item.get('description', '')[:100]}...\n"
    
    text += f"""
<b>⚠️ БЛОК:</b>
{profile.get('blocks', [{}])[0].get('description', '')[:200] if profile.get('blocks') else ''}

<b>🔴 ЭРОГЕННАЯ ЗОНА:</b>
{profile.get('erogenous_zone', {}).get('trigger', '')[:100]}

<b>💞 ИДЕАЛЬНЫЙ ПАРТНЁР:</b>
{profile.get('ideal_partner', '')[:200]}

<b>🛠 {profile.get('tool', {}).get('name', 'ПРОТОКОЛ')}:</b>
"""
    for step in profile.get('tool', {}).get('steps', [])[:2]:
        text += f"{step}\n"

    text += f"""
{SEXUAL_DIVIDER}
💞 <b>У КАЖДОГО ЕСТЬ ТАЙНЫ.</b>
🔓 <b>ВАШ КЛЮЧ К ПРАВДЕ:</b>

❶ Пригласите → 0₽
❷ Друг проходит тест (3 мин)
❸ Мы пришлём уведомление
❹ 99₽ = доступ к его 18+ профилю

⚠️ Только вы. Только правда. Без стыда.
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔞 Создать приглашение", callback_data="sexual_invite_start")],
        [InlineKeyboardButton("🔍 Мои приглашения", callback_data="show_my_invites")],
        [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_PROFILE_SCREEN

# ============================================
# 🔥 ЭКРАН: СОЗДАНИЕ ПРИГЛАШЕНИЯ
# ============================================

async def sexual_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Создание ссылки-приглашения с готовым текстом"""
    query = update.callback_query
    await query.answer()
    
    invite_code = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
    invite_url = f"https://t.me/Testing_Lichnosti_bot?start={invite_code}"
    
    invite_message = (
        "Есть одна штука.\n"
        "Определяет твой ночной тип личности.\n"
        "У меня — совпало процентов на 90.\n"
        f"{invite_url}\n\n"
        "Интересно, у тебя тоже?"
    )
    
    invite = {
        "code": invite_code,
        "url": invite_url,
        "message": invite_message,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "friend_id": None,
        "friend_name": None,
        "friend_profile": None,
        "payment_status": {},
        "purchased_functions": []  # Список купленных 4F для этого друга
    }
    
    context.user_data["current_invite"] = invite
    
    invites = context.user_data.get("sexual_invites", [])
    invites.insert(0, invite)
    context.user_data["sexual_invites"] = invites
    
    text = f"""
{SEXUAL_DIVIDER}
🔞 <b>ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!</b>
{SEXUAL_DIVIDER}

🔗 <code>{invite_url}</code>

💬 <b>ГОТОВЫЙ ТЕКСТ ДЛЯ ДРУГА:</b>
<code>{invite_message}</code>

✨ Просто скопируй всё сообщение целиком
   и отправь другу.

👉 <b>99₽ = доступ к его 18+ профилю</b>
   и ко всем 4F-ключам
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Копировать ссылку", callback_data=f"copy_invite_{invite_code}")],
        [InlineKeyboardButton("🔍 Мои приглашения", callback_data="show_my_invites")],
        [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_INVITES_LIST

# ============================================
# 🔥 ЭКРАН: МОИ ПРИГЛАШЕНИЯ (С 4F-КНОПКАМИ)
# ============================================

async def show_my_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔍 МОИ ПРИГЛАШЕНИЯ
    Показывает список приглашений и кнопки 1F-4F для друзей, прошедших тест
    """
    query = update.callback_query
    await query.answer()
    
    invites = context.user_data.get("sexual_invites", [])
    current_invite = context.user_data.get("current_invite")
    
    if current_invite and current_invite not in invites:
        invites.insert(0, current_invite)
        context.user_data["sexual_invites"] = invites
    
    if not invites:
        text = f"""
{SEXUAL_DIVIDER}
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
{SEXUAL_DIVIDER}

У вас пока нет активных приглашений.

✨ Создайте ссылку-приглашение, чтобы узнать 
   18+ предпочтения друзей и получить 4F-ключи.

👉 <b>99₽ = доступ к профилю друга + 4F</b>
{SEXUAL_DIVIDER}
"""
        keyboard = [
            [InlineKeyboardButton("🔞 Создать приглашение", callback_data="sexual_invite_start")],
            [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return SEXUAL_INVITES_LIST
    
    # Основной текст со списком приглашений
    text = f"""
{SEXUAL_DIVIDER}
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
{SEXUAL_DIVIDER}

📋 <b>Всего создано:</b> {len(invites)}

"""
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
        
        friend_name = invite.get('friend_name')
        status_emoji = "✅" if friend_name else "⏳"
        status_text = f"👤 {friend_name}" if friend_name else "⏳ Ожидает ответа"
        
        text += f"{i}. <code>{code}</code>\n   📅 {created_at} • {status_emoji} {status_text}\n\n"
    
    if len(invites) > 3:
        text += f"...и ещё {len(invites) - 3} приглашений\n\n"
    
    text += f"""
{SEXUAL_DIVIDER}
💞 <b>Как только друг пройдёт тест —</b>
   вы увидите его имя и получите доступ к кнопкам 1F-4F.

<b>🔑 4F-КЛЮЧИ (99₽/шт):</b>
• 🔥 1F — Как вызвать возбуждение
• 🍽 2F — Как пробудить голод/желание
• ⚡ 3F — Как обойти страх
• 💡 4F — Как родить идею

⚠️ <i>Сейчас работает демо-режим для всех профилей</i>
{SEXUAL_DIVIDER}
"""
    
    # Создаем клавиатуру
    keyboard = []
    
    # Для каждого друга, прошедшего тест, добавляем ряд с кнопками 1F-4F
    for invite in invites:
        friend_name = invite.get('friend_name')
        if friend_name:
            # Ряд с именем друга (не кликабельно, просто текст)
            keyboard.append([InlineKeyboardButton(f"👤 {friend_name}", callback_data="noop")])
            
            # Ряд с кнопками 1F-4F
            row = []
            purchased = invite.get("purchased_functions", [])
            
            for f in ["1F", "2F", "3F", "4F"]:
                if f in purchased:
                    row.append(InlineKeyboardButton(
                        f"🔓 {f}",
                        callback_data=f"open_4f_{invite['code']}_{f}"
                    ))
                else:
                    row.append(InlineKeyboardButton(
                        f"{f} (99₽)",
                        callback_data=f"buy_function_{invite['code']}_{f}"
                    ))
            keyboard.append(row)
            
            # Кнопка "Детали профиля"
            keyboard.append([InlineKeyboardButton(
                "📋 Детали профиля",
                callback_data=f"friend_details_{invite['code']}"
            )])
    
    # Кнопки навигации
    keyboard.append([InlineKeyboardButton("🔞 Создать новое приглашение", callback_data="sexual_invite_start")])
    keyboard.append([InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_INVITES_LIST

# ============================================
# 🔥 ПОКУПКА 4F-ФУНКЦИИ
# ============================================

async def buy_function_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки 1F/2F/3F/4F"""
    query = update.callback_query
    await query.answer("💳 Создаю платеж...")
    
    # Парсим callback_data: buy_function_{invite_code}_{function}
    parts = query.data.split("_")
    invite_code = parts[2]
    function = parts[3]
    
    # Ищем приглашение
    invites = context.user_data.get("sexual_invites", [])
    invite = None
    for inv in invites:
        if inv.get("code") == invite_code:
            invite = inv
            break
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return SEXUAL_INVITES_LIST
    
    friend_name = invite.get("friend_name", "Друг")
    friend_profile = invite.get("friend_profile", "SA_4_EXP")
    buyer_id = update.effective_user.id
    
    # Создаем платеж через API
    payment_id = f"4f_{function}_{buyer_id}_{int(datetime.now().timestamp())}"
    
    try:
        response = requests.post(
            f"{API_URL}/api/4f/create-payment-99",
            json={
                "payment_id": payment_id,
                "buyer_id": buyer_id,
                "target_id": invite.get("friend_id", 0),
                "target_name": friend_name,
                "target_profile": friend_profile,
                "function": function,
                "invite_code": invite_code
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            confirmation_url = data.get("confirmation_url")
            
            # Сохраняем payment_id в приглашении
            if "payment_ids" not in invite:
                invite["payment_ids"] = {}
            invite["payment_ids"][function] = payment_id
            
            text = f"""
{SEXUAL_DIVIDER}
🔑 <b>ПОКУПКА КЛЮЧА {function}</b>
{SEXUAL_DIVIDER}

👤 <b>Друг:</b> {friend_name}
📊 <b>Профиль:</b> {friend_profile}
🔐 <b>Функция:</b> {function}

💎 <b>Стоимость:</b> 99 ₽

<b>После оплаты вы получите:</b>
• Полное описание ключа {function}
• 10+ точных триггер-фраз
• Психологический разбор
• Протокол применения

⚠️ <i>Сейчас действует демо-режим — 
вы получите готовый ключ для профиля SA-4_CAP</i>
{SEXUAL_DIVIDER}
"""
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить 99 ₽", url=confirmation_url)],
                [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_4f_payment_{payment_id}_{function}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="show_my_invites")]
            ]
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return FOUR_F_PAYMENT_SCREEN
        else:
            await query.answer("❌ Ошибка создания платежа", show_alert=True)
            return SEXUAL_INVITES_LIST
            
    except Exception as e:
        logger.error(f"Ошибка при создании платежа 4F: {e}")
        await query.answer("❌ Ошибка соединения с платежной системой", show_alert=True)
        return SEXUAL_INVITES_LIST

# ============================================
# 🔥 ПРОВЕРКА ПЛАТЕЖА 4F
# ============================================

async def check_4f_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа за 4F"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    payment_id = parts[3]
    function = parts[4]
    
    try:
        response = requests.get(
            f"{API_URL}/api/4f/check-payment/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "pending")
            
            if status == "succeeded":
                # Платеж успешен - показываем ключ
                return await open_4f_key_callback(update, context)
            elif status == "pending":
                await query.answer("⏳ Платеж еще не обработан", show_alert=True)
            else:
                await query.answer(f"❌ Статус: {status}", show_alert=True)
        else:
            await query.answer("⏳ Платеж обрабатывается", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")
        await query.answer("❌ Ошибка проверки", show_alert=True)
    
    return FOUR_F_PAYMENT_SCREEN

# ============================================
# 🔥 ОТКРЫТИЕ КУПЛЕННОГО 4F-КЛЮЧА
# ============================================

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открыть купленный 4F-ключ"""
    query = update.callback_query
    await query.answer("🔓 Загружаю ключ...")
    
    parts = query.data.split("_")
    
    if len(parts) >= 4 and parts[1] == "4f":
        # open_4f_{invite_code}_{function}
        invite_code = parts[2]
        function = parts[3]
        
        # Ищем приглашение
        invites = context.user_data.get("sexual_invites", [])
        invite = None
        for inv in invites:
            if inv.get("code") == invite_code:
                invite = inv
                break
        
        if not invite:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return SEXUAL_INVITES_LIST
        
        friend_name = invite.get("friend_name", "Друг")
        
        # Загружаем демо-ключ
        content = get_4f_function(function, "sa_4_cap")
        text = format_4f_message(content, friend_name)
        
        keyboard = [
            [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="show_my_invites")],
            [InlineKeyboardButton("🔒 Купить полную версию (99₽)", callback_data=f"buy_function_{invite_code}_{function}")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return FOUR_F_CONTENT_SCREEN
        
    else:
        # Проверяем через payment_id
        payment_id = parts[3]
        function = parts[4] if len(parts) > 4 else "1F"
        
        try:
            response = requests.get(
                f"{API_URL}/api/4f/get-purchased-function/{payment_id}",
                params={"user_id": update.effective_user.id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", {})
                friend_name = data.get("target_name", "Друг")
                
                text = format_4f_message(content, friend_name)
                
                keyboard = [
                    [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="show_my_invites")],
                    [InlineKeyboardButton("🔒 Купить еще", callback_data="sexual_invite_start")]
                ]
                
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML"
                )
                return FOUR_F_CONTENT_SCREEN
            else:
                await query.answer("❌ Ключ не найден", show_alert=True)
                return SEXUAL_INVITES_LIST
                
        except Exception as e:
            logger.error(f"Ошибка получения ключа: {e}")
            await query.answer("❌ Ошибка загрузки", show_alert=True)
            return SEXUAL_INVITES_LIST

# ============================================
# ДЕТАЛИ ПРОФИЛЯ ДРУГА
# ============================================

async def friend_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает детали профиля друга"""
    query = update.callback_query
    await query.answer()
    
    invite_code = query.data.split("_")[2]
    
    invites = context.user_data.get("sexual_invites", [])
    invite = None
    for inv in invites:
        if inv.get("code") == invite_code:
            invite = inv
            break
    
    if not invite:
        await query.answer("❌ Приглашение не найдено", show_alert=True)
        return SEXUAL_INVITES_LIST
    
    friend_name = invite.get("friend_name", "Друг")
    friend_profile = invite.get("friend_profile", "SA_4_EXP")
    purchased = invite.get("purchased_functions", [])
    
    text = f"""
{SEXUAL_DIVIDER}
👤 <b>ПРОФИЛЬ ДРУГА</b>
{SEXUAL_DIVIDER}

<b>Имя:</b> {friend_name}
<b>Общий профиль:</b> {friend_profile}
<b>Интимный профиль:</b> sa_5_int (тестовая заглушка)

<b>🔑 Купленные ключи:</b>
"""
    if purchased:
        for f in purchased:
            text += f"  • {f}\n"
    else:
        text += "  • Нет купленных ключей\n"
    
    text += f"""
{SEXUAL_DIVIDER}
💎 <b>4F-ключи — 99₽/шт</b>
• 1F: Ключ возбуждения
• 2F: Ключ голода/желания
• 3F: Ключ страха
• 4F: Ключ идеи

⚠️ <i>Сейчас все ключи работают в демо-режиме
для профиля SA-4_CAP</i>
{SEXUAL_DIVIDER}
"""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="show_my_invites")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SEXUAL_FRIEND_PROFILE

# ============================================
# ОБРАБОТЧИКИ СТАНДАРТНЫХ КНОПОК
# ============================================

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Копирование ссылки"""
    query = update.callback_query
    await query.answer("📋 Ссылка скопирована!", show_alert=False)
    return SEXUAL_INVITES_LIST

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса приглашения"""
    query = update.callback_query
    await query.answer("⏳ Ожидает активации", show_alert=True)
    return SEXUAL_INVITES_LIST

async def delete_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление приглашения"""
    query = update.callback_query
    await query.answer("❌ Приглашение удалено", show_alert=True)
    return SEXUAL_INVITES_LIST

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для некликабельных кнопок"""
    query = update.callback_query
    await query.answer()
    return SEXUAL_INVITES_LIST

# ============================================
# ОБРАБОТЧИК DEEP LINK
# ============================================

async def handle_sexual_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Обработчик /start sex_xxx"""
    user = update.effective_user
    invite_code = payload
    
    inviter_name = "Александр"
    inviter_id = 123456789
    
    text = f"""
{SEXUAL_DIVIDER}
🎁 <b>Вас пригласил(а) {inviter_name}!</b>
{SEXUAL_DIVIDER}

Пройдите тест — и {inviter_name} сможет узнать 
ваши 18+ предпочтения и получить 4F-ключи к вашему профилю
(только если захочет и заплатит 99₽ за каждый ключ).

<i>Вы тоже сможете приглашать друзей 
и покупать 4F-ключи к их профилям.</i>

⏱ <b>Тест займёт всего 3 минуты</b>
🔒 Полная анонимность
💞 Только правда, без стыда

<b>🔑 Что такое 4F?</b>
• 1F — Ключ возбуждения
• 2F — Ключ голода/желания  
• 3F — Ключ страха
• 4F — Ключ идеи

{SEXUAL_DIVIDER}
🚀 <b>Начнём?</b>
"""
    keyboard = [
        [InlineKeyboardButton("🚀 Пройти тест", callback_data="start_test")]
    ]
    
    context.user_data["invited_by"] = inviter_id
    context.user_data["invite_code"] = payload
    context.user_data["inviter_name"] = inviter_name
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================
# ПРОВЕРКА ПРИГЛАШЕНИЯ ПОСЛЕ ТЕСТА
# ============================================

async def check_sexual_invitation(context: ContextTypes.DEFAULT_TYPE, user_id: int, username: str, profile_code: str):
    """
    Вызывается после прохождения теста
    Обновляет статус приглашения и привязывает профиль друга
    """
    invite_code = context.user_data.get("invite_code")
    inviter_name = context.user_data.get("inviter_name", "друг")
    
    if not invite_code:
        return False
    
    logger.info(f"🔞 Пользователь {user_id} ({username}) прошел тест по приглашению {invite_code}")
    
    # Ищем приглашение в user_data отправителя (это сложно, нужно через API)
    # В заглушке просто сохраняем в контексте текущего пользователя
    
    # Сохраняем информацию о том, что мы прошли по приглашению
    context.user_data["i_was_invited"] = True
    context.user_data["my_inviter"] = inviter_name
    
    # Очищаем данные приглашения
    context.user_data.pop("invited_by", None)
    context.user_data.pop("invite_code", None)
    context.user_data.pop("inviter_name", None)
    
    return True

# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'show_my_sexual_profile',
    'sexual_invite_start',
    'show_my_invites',
    'handle_sexual_deeplink',
    'copy_invite_callback',
    'check_invite_callback',
    'delete_invite_callback',
    'buy_function_callback',
    'check_4f_payment_callback',
    'open_4f_key_callback',
    'friend_details_callback',
    'noop_callback',
    'check_sexual_invitation',
    'SEXUAL_PROFILE_SCREEN',
    'SEXUAL_INVITES_LIST',
    'SEXUAL_FRIEND_PROFILE',
    'FOUR_F_PAYMENT_SCREEN',
    'FOUR_F_CONTENT_SCREEN'
]
