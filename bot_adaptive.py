#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА: ПУТЬ К САМОПОЗНАНИЮ
4 этапа адаптивного исследования + персональное описание профиля
ВЕРСИЯ 6.0: ПОЛНАЯ ИНТЕГРАЦИЯ С 18+ МОДУЛЕМ 19.7
"""

import logging
import os
import sys
import asyncio
import urllib.parse
import time
import base64
import uuid
import random
import requests
import traceback
from typing import Dict, List, Optional, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ===== НАСТРОЙКА СУПЕР-ЛОГГИРОВАНИЯ =====
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Функция для логирования входящих callback
def log_callback(func_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует входящий callback"""
    user = update.effective_user
    query = update.callback_query if update.callback_query else None
    
    log_msg = f"📞 {func_name} | User: {user.id} (@{user.username})"
    if query:
        log_msg += f" | Callback: {query.data}"
    if context.user_data:
        log_msg += f" | has_shared: {context.user_data.get('has_shared', False)}"
        log_msg += f" | profile: {context.user_data.get('profile_data', {}).get('display_name', 'None')}"
    
    logger.debug(log_msg)
    print(f"🔍 {log_msg}")

# ===== ИМПОРТ КОНСТАНТ СОСТОЯНИЙ =====
from constants import (
    # Состояния теста
    STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS,
    GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, PAYMENT_SCREEN,
    
    # Состояния 18+ модуля
    MY_SEXUAL_PROFILE, SEXUAL_PROFILE_SCREEN,
    
    # Состояния 4F
    FOUR_F_PAYMENT_SCREEN, FOUR_F_CONTENT_SCREEN,
    FOUR_F_MAIN, FOUR_F_DETAILED, FOUR_F_MENU, FOUR_F_CONTENT,
    
    # Дополнительные состояния
    BUY_PACKAGES, INVITES_LIST, FRIEND_MENU,
    
    # Словарь для совместимости
    SEXUAL_STATES,
)

# ===== ИМПОРТ КОНФИГУРАЦИИ =====
from config import (
    TOKEN, API_URL, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY,
    TELEGRAM_BOT_URL, BOT_LINK, AUTHOR_LINK, GIFT_PDF_LINK, SHARE_TEXT,
    GIFT_SCREEN_TEXT, STANDARD_SUFFIXES, CONFLICT_PHRASES, SUFFIX_TO_DILTS,
    EMERGENCY_PROFILES, LEVEL_DIFFS, PROFILE_LINKS, DEFAULT_PROFILE,
)

# ===== ИМПОРТ 18+ МОДУЛЯ (НОВАЯ ВЕРСИЯ 19.7) =====
from sexual_19_7 import (
    # Константы
    SEXUAL_DIVIDER,
    FREE_INVITE_LIMIT,
    FRIEND_ACCESS_PRICE,
    FOUR_F_PRICE,
    INVITE_PACKAGES,
    PROFILE_DISK_LINKS,
    FOUR_F_DESCRIPTIONS,
    back_to_sexual_profile_callback,
    
    # Функции для работы с БД
    get_user_invites_from_api,
    save_invite_to_api,
    update_invite_in_api,
    find_invite_in_api,
    
    # Функции для работы с профилями
    get_disk_link_by_profile,
    get_disk_link,
    load_intimate_profile,
    load_friend_intimate_profile,
    format_intimate_profile_part1,
    format_intimate_profile_part2,
    format_intimate_profile_part3,
    format_friend_intimate_profile,
    
    # Функции для 4F
    load_4f_content,
    
    # Функции для приглашений
    get_user_invites,
    count_friends,
    init_test_data,
    get_friend_by_id,
    
    # Основные callback-обработчики
    show_my_sexual_profile,
    sexual_invite_start,
    create_invite_callback,
    send_invite_callback,
    confirm_send_callback,
    confirm_sent_callback,
    contact_selected_callback,
    my_invites_callback,
    copy_invite_callback,
    check_invite_callback,
    
    # 4F обработчики
    four_f_main_menu_callback,
    four_f_detailed_callback,
    four_f_menu_callback,
    four_f_explanation_callback,
    buy_4f_key_callback,
    process_payment_callback,
    open_4f_key_callback,
    
    # Пакеты приглашений
    buy_invite_packages_callback,       
    pay_package_callback,                 
    process_package_payment_callback,    
    check_package_callback,              
    
    # Меню друга
    friend_menu_callback,               
    show_payment_access_screen,          
    standard_profile_callback,            
    intimate_profile_callback,
    
    # Вспомогательные обработчики
    check_status_callback,
    back_to_results_callback,
    dummy_callback,
    
    # Вспомогательные функции
    split_long_message,
    safe_send_message,
    
    # Функции платежей
    generate_payment_id,
    create_yookassa_invoice,
)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для нереализованных функций"""
    query = update.callback_query
    await query.answer("🚧 Функция в разработке", show_alert=True)
    return

# ===== ИМПОРТ ВОПРОСОВ =====
from questions import (
    PERCEPTION_TYPES, CLARIFICATION_QUESTIONS,
    STAGE1_FEEDBACK, STAGE2_FEEDBACK, STAGE3_FEEDBACK, STAGE4_ANALYSIS_SCREEN
)

# ===== ИМПОРТ НАШИХ НОВЫХ МОДУЛЕЙ =====
from handlers import (
    show_stage_1_intro, show_stage_1_details, back_to_stage1_intro,
    start_stage_1, ask_stage_1_question, handle_stage_1_answer, finish_stage_1,
    
    show_stage_2_intro, show_stage_2_details, back_to_stage2_intro,
    start_stage_2, ask_stage_2_question, handle_stage_2_answer, finish_stage_2,
    
    show_stage_3_intro, show_stage_3_details, back_to_stage3_intro,
    start_stage_3, ask_stage_3_question, handle_stage_3_answer, finish_stage_3,
    
    show_stage_4_intro, show_stage_4_details, back_to_stage4_intro,
    start_stage_4, ask_stage_4_question, handle_stage_4_answer, finish_stage_4,
)

from handlers.common import ask_clarification_question, handle_clarification_answer

# ===== ПРОВЕРКА ИМПОРТОВ =====
logger.info("🔍 ПРОВЕРКА ИМПОРТОВ ИЗ handlers:")
logger.info(f"  start_stage_1: {start_stage_1}")
logger.info(f"  handle_stage_1_answer: {handle_stage_1_answer}")
logger.info(f"  ask_stage_1_question: {ask_stage_1_question}")
logger.info(f"  finish_stage_1: {finish_stage_1}")

# ===== ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА ТИПОВ =====
print("\n" + "="*60, file=sys.stderr)
print("🔍 ПРИНУДИТЕЛЬНАЯ ПРОВЕРКА ТИПОВ", file=sys.stderr)
print("="*60, file=sys.stderr)
print(f"🔥 start_stage_1 = {start_stage_1}", file=sys.stderr)
print(f"🔥 Тип start_stage_1 = {type(start_stage_1)}", file=sys.stderr)
print(f"🔥 start_stage_1 is None: {start_stage_1 is None}", file=sys.stderr)
print(f"🔥 start_stage_1 is callable: {callable(start_stage_1)}", file=sys.stderr)
print("="*60 + "\n", file=sys.stderr)
sys.stderr.flush()

from utils.calculations import (
    determine_perception_type, get_type_code, get_level_name, get_dilts_code,
    determine_dilts_level, get_level_group, calculate_thinking_level_by_scores,
    calculate_final_level, check_profile_coherence, calculate_profile_final
)

from utils.validators import (
    need_clarification_stage1, need_clarification_stage2,
    need_clarification_stage3, need_clarification_stage4
)

from utils.helpers import calculate_progress

# Импорт загрузчика и профилей
from loader import loader
from base import VariaticaProfile

# ============================================
# ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ ПРОФИЛЕЙ В БД
# ============================================

async def save_user_profile_background(user_id: int, profile_code: str):
    """Сохраняет профиль пользователя в БД (фоновая задача)"""
    try:
        logger.info(f"💾 Сохраняю профиль пользователя {user_id}: {profile_code}")
        
        response = requests.post(
            f"{API_URL}/api/save-user-profile",
            json={
                "user_id": user_id,
                "profile_code": profile_code
            },
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Профиль {profile_code} сохранен для пользователя {user_id}")
        else:
            logger.error(f"❌ Ошибка сохранения профиля: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении профиля: {e}")

# ============================================
# ФУНКЦИИ ПЛАТЕЖНОЙ СИСТЕМЫ
# ============================================

def create_yookassa_invoice_payment(payment_id: str, user_id: int, profile_code: str, amount: float = 690.0, email: str = None) -> dict:
    """Создает платеж через Invoices API ЮKassa"""
    try:
        logger.info(f"📤 Создаю платеж ЮKassa: {payment_id}, профиль: {profile_code}")
        
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            logger.error("❌ YOOKASSA ключи не установлены!")
            return {"success": False, "error": "Платежная система не настроена"}
        
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        unique_id = uuid.uuid4().hex[:16]
        idempotence_key = f"{payment_id}_{unique_id}_{int(time.time())}"
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': idempotence_key
        }
        
        if not email:
            email = f"user_{user_id}@example.com"
        
        description = f"Полное описание профиля {profile_code} от виртуального психолога"
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": TELEGRAM_BOT_URL
            },
            "capture": True,
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id),
                "profile_code": profile_code,
                "is_test": "false"
            },
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": f"Полное описание профиля {profile_code} от виртуального психолога",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": "1",
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }
                ]
            }
        }
        
        logger.info(f"💳 Отправляю запрос в ЮKassa...")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if confirmation_url:
                logger.info(f"✅ Платеж создан в ЮKassa: {data.get('id')}")
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": confirmation_url,
                    "yookassa_id": data.get('id'),
                    "amount": amount,
                    "profile_code": profile_code,
                    "invoice_type": "yookassa_invoice",
                    "available_methods": "all",
                    "status": data.get('status', 'pending')
                }
            else:
                logger.error(f"❌ Нет ссылки для оплаты в ответе ЮKassa")
                return {"success": False, "error": "Нет ссылки для оплаты"}
        else:
            error_text = response.text[:500] if response.text else "Нет ответа"
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            return {"success": False, "error": f"Ошибка ЮKassa: {response.status_code}", "details": error_text}
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа ЮKassa: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

async def create_payment_advanced(user_id: int, profile_code: str, amount: float = 690.00) -> dict:
    """Создает платеж в БД и ЮKassa"""
    
    timestamp = int(time.time())
    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
    user_suffix = str(user_id)[-6:]
    payment_id = f"prod_{timestamp}_{random_str}_{user_suffix}"
    
    logger.info(f"💳 Создаю платеж: {payment_id}, профиль: {profile_code}, сумма: {amount}")
    
    try:
        db_payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "profile_code": profile_code.upper(),
            "amount": amount,
            "email": f"user_{user_id}@example.com",
            "description": f"Полное описание профиля {profile_code} от виртуального психолога"
        }
        
        logger.debug(f"📤 Отправка запроса в API: {API_URL}/api/create-payment-advanced")
        db_response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=db_payload,
            timeout=10
        )
        
        logger.debug(f"📥 Ответ API: {db_response.status_code}")
        
        if db_response.status_code in [200, 201]:
            db_data = db_response.json()
            
            if db_data.get("confirmation_url"):
                logger.info(f"✅ Платеж создан через API: {payment_id}")
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "confirmation_url": db_data["confirmation_url"],
                    "amount": amount,
                    "profile_code": profile_code,
                    "yookassa_id": db_data.get("yookassa_id"),
                    "invoice_type": db_data.get("invoice_type", "yookassa_invoice"),
                    "available_methods": db_data.get("available_methods", "all"),
                    "status": db_data.get("status", "pending")
                }
            
            logger.info(f"🔄 Создаю платеж через ЮKassa напрямую: {payment_id}")
            yookassa_result = create_yookassa_invoice_payment(
                payment_id=payment_id,
                user_id=user_id,
                profile_code=profile_code,
                amount=amount,
                email=f"user_{user_id}@example.com"
            )
            
            if yookassa_result["success"]:
                try:
                    update_response = requests.post(
                        f"{API_URL}/api/update-yookassa-id",
                        json={
                            "payment_id": payment_id,
                            "yookassa_id": yookassa_result.get("yookassa_id"),
                            "profile_code": profile_code,
                            "status": "waiting"
                        },
                        timeout=5
                    )
                    
                    if update_response.status_code in [200, 201]:
                        logger.info(f"✅ ID ЮKassa сохранен в БД")
                    else:
                        logger.warning(f"⚠️ Не удалось сохранить ID ЮKassa: {update_response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при сохранении ID ЮKassa: {e}")
                
                return yookassa_result
            else:
                logger.error(f"❌ Ошибка создания платежа в ЮKassa: {yookassa_result.get('error')}")
                return yookassa_result
                
        else:
            error_text = db_response.text[:200] if db_response.text else "Нет ответа"
            logger.error(f"❌ Ошибка БД {db_response.status_code}: {error_text}")
            return {
                "success": False, 
                "error": f"Ошибка API: {db_response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к API: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Ошибка подключения: {str(e)}"
        }

async def check_payment_status_api(payment_id: str) -> dict:
    """Проверяет статус платежа через API"""
    try:
        logger.debug(f"🔍 Проверка статуса платежа: {payment_id}")
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        logger.debug(f"📥 Ответ API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"  Статус: {result.get('status', 'unknown')}")
            return {
                "success": True,
                "status": result.get("status", "unknown"),
                "payment_id": payment_id,
                "data": result
            }
        else:
            logger.error(f"❌ API error: {response.status_code}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Status check error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

async def get_materials_link_api(payment_id: str, user_id: int) -> dict:
    """Получает ссылку на материалы через API"""
    try:
        logger.debug(f"📦 Получение материалов: {payment_id}, user_id={user_id}")
        response = requests.get(
            f"{API_URL}/api/get-materials/{payment_id}",
            params={"user_id": user_id},
            timeout=10
        )
        
        logger.debug(f"📥 Ответ API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.debug(f"✅ Материалы получены: {result.get('profile_code')}")
                return {
                    "success": True,
                    "materials_link": result.get("materials_link"),
                    "profile_code": result.get("profile_code"),
                    "profile_link": result.get("profile_link")
                }
            else:
                logger.error(f"❌ Ошибка API: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        else:
            logger.error(f"❌ API error: {response.status_code}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
    except Exception as e:
        logger.error(f"Materials API error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# ФУНКЦИИ РАБОТЫ С ПРОФИЛЯМИ
# ============================================

class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

def get_profile_fallback(profile_data: dict) -> 'VariaticaProfile':
    """Упрощенная логика поиска профиля"""
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    logger.info(f"🔍 ПОИСК ПРОФИЛЯ: type={type_code}, level={level}, dilts={dilts_code}")
    
    search_order = []
    if dilts_code in STANDARD_SUFFIXES:
        search_order.append(dilts_code)
    search_order.extend(STANDARD_SUFFIXES)
    search_order = list(dict.fromkeys(search_order))
    
    logger.info(f"📋 Порядок поиска суффиксов: {search_order}")
    
    for suffix in search_order:
        profile_key = f"{type_code}_{level}_{suffix}"
        profile = loader.get_profile(profile_key)
        if profile:
            logger.info(f"✅ Найден профиль: {profile_key}")
            return profile
    
    logger.warning(f"⚠️ Не найдено профилей для {type_code}_{level}_*")
    
    for diff in LEVEL_DIFFS:
        test_level = level + diff
        if 1 <= test_level <= 9:
            for suffix in STANDARD_SUFFIXES:
                profile_key = f"{type_code}_{test_level}_{suffix}"
                profile = loader.get_profile(profile_key)
                if profile:
                    logger.info(f"✅ Найден на уровне {test_level} (разница {diff}): {profile_key}")
                    return profile
    
    logger.error(f"❌ Не найдено профилей типа {type_code} на уровнях 1-9")
    
    for emergency_key in EMERGENCY_PROFILES:
        profile = loader.get_profile(emergency_key)
        if profile:
            logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
            return profile
    
    error_msg = f"Не найден профиль для type={type_code}, level={level}"
    logger.critical(f"💥 {error_msg}")
    raise ProfileNotFoundError(error_msg)

def get_discrepancy_note(profile_data: dict, actual_profile_key: str) -> str:
    """Возвращает примечание о конфликте Дилтса"""
    if not actual_profile_key:
        logger.warning("⚠️ get_discrepancy_note: actual_profile_key отсутствует")
        return ""
    
    try:
        key_lower = actual_profile_key.lower()
        logger.info(f"🔍 Поиск суффикса в ключе: {key_lower}")
        
        found_suffix = None
        for suffix in STANDARD_SUFFIXES:
            if f"_{suffix}" in key_lower or key_lower.startswith(f"{suffix}_") or key_lower.endswith(f"_{suffix}") or key_lower == suffix:
                found_suffix = suffix
                logger.info(f"✅ Найден суффикс: {found_suffix}")
                break
        
        if found_suffix:
            dilts_level = SUFFIX_TO_DILTS.get(found_suffix, "ENVIRONMENT")
            conflict_phrase = CONFLICT_PHRASES.get(dilts_level, {})
            note = conflict_phrase.get("note", "")
            
            if note:
                logger.info(f"✅ Сформировано примечание о конфликте: суффикс={found_suffix}, dilts={dilts_level}")
                return f"{note}\n\n"
            else:
                return f"🔥 Примечание: Обнаружено несоответствие в вашем профиле.\n\n"
        
        logger.info(f"❌ Суффикс не найден в ключе: {key_lower}")
        return ""
        
    except Exception as e:
        logger.error(f"❌ Ошибка в get_discrepancy_note: {e}", exc_info=True)
        return ""

def clean_duplicate_headers(text: str, field_type: str) -> str:
    """Убирает заголовки, которые уже есть в тексте профиля"""
    if not text:
        return ""
    
    lines = text.strip().split('\n')
    if not lines:
        return text
    
    headers = {
        'trigger': ['ЭТО ТЫ, ЕСЛИ...', 'ЭТО ТЫ, ЕСЛИ:'],
        'pain': ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ: ПОЧЕМУ ЭТО ЛОМАЕТ ТВОЮ ЖИЗНЬ?'],
        'immediate_tool': ['ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:'],
        'cta': ['ЧТО ДАЛЬШЕ?', 'ДАЛЬШЕ:']
    }
    
    if field_type in headers and lines:
        first_line = lines[0].strip()
        for header in headers[field_type]:
            if header in first_line:
                lines.pop(0)
                if lines and not lines[0].strip():
                    lines.pop(0)
                break
    
    return '\n'.join(lines).strip()

def format_profile_title(profile_title: str, profile_header: str) -> str:
    """Форматирует заголовок профиля"""
    if not profile_title:
        return f"🎯 {profile_header}"
    
    profile_title = profile_title.strip()
    lines = profile_title.split('\n')
    
    if len(lines) == 1:
        title = lines[0].strip()
        return f"🎯 {profile_header} / {title}"
    
    elif len(lines) >= 2:
        line1 = lines[0].strip()
        line2 = lines[1].strip()
        
        if line2 == profile_header or line2.replace('_', ' ').lower() == profile_header.replace('_', ' ').lower():
            return f"🎯 {profile_header} / {line1}"
        else:
            return f"🎯 {profile_header} / {line1}"
    
    return f"🎯 {profile_header}"

def get_card_description_from_profile(profile: 'VariaticaProfile', profile_data: dict) -> dict:
    """Получает описание профиля с очисткой заголовков"""
    is_new_format = hasattr(profile, 'archetype') and profile.archetype
    
    if is_new_format:
        clean_trigger = clean_duplicate_headers(profile.trigger, 'trigger')
        clean_pain = clean_duplicate_headers(profile.pain, 'pain')
        clean_tool = clean_duplicate_headers(profile.immediate_tool, 'immediate_tool')
        clean_cta = clean_duplicate_headers(profile.cta, 'cta')
        
        return {
            "title": profile.title,
            "archetype": profile.archetype,
            "quote": profile.quote,
            "trigger": clean_trigger,
            "pain": clean_pain,
            "immediate_tool": clean_tool,
            "cta": clean_cta,
            "type_code": profile_data['type_code'],
            "level": profile_data['level'],
            "dilts_code": profile_data['dilts_code'],
        }
    else:
        return {
            "title": profile.title if hasattr(profile, 'title') else f"{profile_data['type_code']} Профиль",
            "profile_name": profile.profile_name if hasattr(profile, 'profile_name') else f"{profile_data['type_code']} Уровень {profile_data['level']}",
            "thinking_level": profile.thinking_level if hasattr(profile, 'thinking_level') else profile_data['level'],
            "dilts_level": profile.dilts_level if hasattr(profile, 'dilts_level') else profile_data['dilts_level'],
            "pain": profile.pain if hasattr(profile, 'pain') else "",
            "world": profile.world if hasattr(profile, 'world') else "",
            "superpower": profile.superpower if hasattr(profile, 'superpower') else "",
            "growth": profile.growth if hasattr(profile, 'growth') else f"Точка роста на уровне {profile_data['level']}",
            "cta": profile.cta if hasattr(profile, 'cta') else ""
        }

# ============================================
# ФУНКЦИИ РЕЗУЛЬТАТОВ
# ============================================

async def show_results_screen(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    force_shared_view: bool = False
):
    """ЭКРАН РЕЗУЛЬТАТОВ с 18+ кнопкой"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_callback("show_results_screen", update, context)
    
    # 👇 ДОБАВЛЯЕМ ПРОВЕРКУ current_invite
    logger.info(f"🔍 ПРОВЕРКА current_invite В НАЧАЛЕ show_results_screen: {context.user_data.get('current_invite')}")
    
    if "temp_has_shared" in context.user_data:
        context.user_data["has_shared"] = context.user_data.pop("temp_has_shared")
        logger.info(f"🔄 Восстановлен has_shared = {context.user_data['has_shared']}")
    
    has_shared = context.user_data.get("has_shared", False) or force_shared_view
    profile_data = context.user_data.get("profile_data")
    
    logger.debug(f"📊 has_shared={has_shared}, profile_data={'есть' if profile_data else 'нет'}")
    
    if not profile_data:
        logger.debug("🔄 profile_data отсутствует, вычисляем...")
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
        logger.debug(f"✅ profile_data вычислен: {profile_data.get('display_name')}")
    
    # 👇 ЭТА СТРОКА НА ТОМ ЖЕ УРОВНЕ, ЧТО И if not profile_data
    # Сохраняем профиль в БД
    if profile_data and profile_data.get('display_name'):
        asyncio.create_task(save_user_profile_background(
            user_id=update.effective_user.id,
            profile_code=profile_data['display_name']
        ))
    
    # Проверяем, есть ли активное приглашение (пользователь пришел по ссылке)
    current_invite = context.user_data.get("current_invite")
    if current_invite:
        logger.info(f"🔍 Найдено активное приглашение: {current_invite}")
        
        friend_data = {
            "target_id": update.effective_user.id,
            "target_name": update.effective_user.username or update.effective_user.first_name,
            "target_profile": profile_data.get('display_name', 'unknown')
        }
        
        # Вызываем функцию обновления
        try:
            success = update_invite_in_api(current_invite["invite_id"], friend_data)
            
            if success:
                logger.info(f"✅ Приглашение {current_invite['invite_id']} обновлено")
                # Очищаем данные приглашения после использования
                context.user_data.pop("current_invite", None)
                
                # Отправляем уведомление создателю ссылки
                buyer_id = current_invite.get("buyer_id")
                if buyer_id:
                    try:
                        # Формируем имя пользователя
                        username = update.effective_user.username or update.effective_user.first_name
                        profile_name = profile_data.get('display_name', 'неизвестно')
                        
                        # Получаем ссылку на профиль
                        profile_link = get_disk_link_by_profile(profile_name)
                        
                        logger.info(f"👤 Данные друга: username={username}, profile={profile_name}")
                        logger.info(f"🔗 Ссылка на профиль: {profile_link}")
                        
                        # Формируем сообщение с ссылкой на папку и двумя кнопками
                        message_text = (
                            f"👤 <b>🪞 НОВОЕ ОТРАЖЕНИЕ!</b>\n\n"
                            f"✨ @{username} посмотрелся в зеркало и теперь есть его отражение!\n"
                            f"📊 <b>Профиль:</b> <code>{profile_name}</code>\n"
                            f"📁 <b>Материалы профиля:</b>\n"
                            f"{profile_link}\n\n"
                            f"👇 <b>Выберите действие:</b>"
                        )
                        
                        # Две кнопки в одном ряду
                        keyboard = [
                            [
                                InlineKeyboardButton("🔗 СОЗДАТЬ ССЫЛКУ", callback_data="send_invite"),
                                InlineKeyboardButton("👥 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")
                            ]
                        ]
                        
                        await context.bot.send_message(
                            chat_id=buyer_id,
                            text=message_text,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            disable_web_page_preview=True
                        )
                        logger.info(f"✅ Уведомление успешно отправлено пользователю {buyer_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Не удалось отправить уведомление: {e}")
                        logger.error(f"❌ Детали ошибки: {traceback.format_exc()}")
                else:
                    logger.warning(f"⚠️ buyer_id отсутствует в current_invite. current_invite={current_invite}")
            
            else:
                logger.error(f"❌ Не удалось обновить приглашение {current_invite['invite_id']}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении приглашения: {e}")
            logger.error(f"❌ Детали ошибки: {traceback.format_exc()}")
    
    try:
        profile = get_profile_fallback(profile_data)
        logger.debug(f"✅ Профиль найден: {profile}")
    except ProfileNotFoundError as e:
        logger.error(f"❌ Профиль не найден: {e}", exc_info=True)
        error_text = (
            f"🧠 <b>К сожалению, возникла техническая ошибка</b>\n\n"
            f"Как ваш виртуальный психолог, я не смог обработать все данные.\n\n"
            f"Попробуйте пройти тест заново, чтобы я мог помочь вам лучше:\n"
            f"/start\n\n"
            f"<i>Приношу извинения за неудобства.</i>"
        )
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    actual_profile_key = None
    try:
        if hasattr(profile, 'key'):
            actual_profile_key = profile.key.lower()
            logger.info(f"🔍 Найден ключ профиля: {actual_profile_key}")
            context.user_data["actual_profile_key"] = actual_profile_key
        elif hasattr(profile, 'profile_name'):
            actual_profile_key = profile.profile_name.lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        else:
            actual_profile_key = f"{profile_card.get('type_code', 'sa')}_{profile_card.get('level', 1)}_{profile_card.get('dilts_code', 'def')}".lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        
        parts = actual_profile_key.split('_')
        if len(parts) >= 3:
            profile_data['type_code'] = parts[0].upper()
            profile_data['level'] = int(parts[1])
            profile_data['dilts_code'] = parts[2].lower()
            profile_data['display_name'] = actual_profile_key.upper()
            context.user_data["profile_data"] = profile_data
            logger.info(f"✅ Обновлен profile_data реальным профилем: {profile_data['display_name']}")
            
    except Exception as e:
        logger.error(f"⚠️ Ошибка определения реального профиля: {e}")
    
    # ПРИМЕЧАНИЕ О КОНФЛИКТЕ
    discrepancy_note = ""
    if actual_profile_key:
        discrepancy_note = get_discrepancy_note(profile_data, actual_profile_key)
        logger.info(f"📝 Примечание о конфликте: {'✅ Есть' if discrepancy_note else '❌ Нет'}")
    
    message_1 = (
        f"🧠 <b>ВАШИ ПЕРВЫЕ ИНСАЙТЫ</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я проанализировал ваши ответы.</i>\n\n"
        f"Вот что я увидел:\n\n"
    )
    
    psychologist_comment = (
        f"<i>На основе ваших ответов я вижу характерные паттерны мышления и поведения. "
        f"Это хорошая отправная точка для самопознания.</i>\n\n"
    )
    
    message_1 += psychologist_comment
    
    profile_header = profile_data.get('display_name', f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}")
    raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
    formatted_title = format_profile_title(raw_title, profile_header)
    message_1 += f"<b>{formatted_title}</b>\n\n"
    
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
    
    trigger = profile_card.get('trigger', '')
    if trigger:
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_1 += f"<b>🔍 ЭТО ВЫ, ЕСЛИ...</b>\n\n"
        message_1 += f"{trigger}\n\n"
    
    pain = profile_card.get('pain', '')
    if pain:
        pain_lines = pain.strip().split('\n')
        if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
            pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
        
        if pain.strip():
            message_1 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
            message_1 += f"{pain.strip()}"
    
    if message_1.strip():
        logger.debug(f"📤 Отправка message_1 ({len(message_1)} символов)")
        await query.edit_message_text(message_1.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    message_2 = ""
    
    tool = profile_card.get('immediate_tool', '')
    if tool:
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            message_2 += f"<b>🛠 ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>\n\n"
            message_2 += f"<i>Что можно сделать прямо сейчас:</i>\n\n"
            message_2 += f"{tool.strip()}\n\n"
    
    cta = profile_card.get('cta', '')
    if cta:
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_2 += f"<b>🚀 СЛЕДУЮЩИЕ ШАГИ</b>\n\n"
            message_2 += f"{cta.strip()}\n\n"
    
    message_2 += "\n"
    
    message_2 += (
        f"🧠 <b>ЧТО ДАЛЬШЕ В НАШЕМ ПУТЕШЕСТВИИ?</b>\n\n"
        f"<i>Это только начало вашего пути к самопознанию.</i>\n\n"
    )
    
    # ПРИМЕЧАНИЕ О КОНФЛИКТЕ
    if discrepancy_note:
        message_2 += f"{discrepancy_note}"
    
    # КНОПКА 18+ ПРОФИЛЯ
    sexual_button = [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="show_my_sexual_profile")]
    
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="get_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        logger.debug("🔘 Клавиатура: без подарка (has_shared=False)")
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Получить сказку «Мастер Меча»", callback_data="open_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        logger.debug(f"🔘 Клавиатура: с подарком, GIFT_PDF_LINK={GIFT_PDF_LINK}")
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.debug(f"📤 Отправка message_2 ({len(message_2)} символов) с {len(keyboard)} рядами кнопок")
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"✅ Результаты показаны пользователю {user_id}")
    return RESULTS

# ============================================
# ФУНКЦИИ НАВИГАЦИИ
# ============================================

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    log_callback("back_to_results", update, context)
    query = update.callback_query
    await query.answer("🔄 Возвращаюсь к результатам...")
    
    result = await show_results_screen(update, context, force_shared_view=True)
    logger.info(f"🔄 User {update.effective_user.id}: back_to_results → RESULTS")
    return result

async def back_to_results_after_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам после подарка"""
    log_callback("back_to_results_after_gift", update, context)
    query = update.callback_query
    await query.answer("🔄 Возвращаюсь к результатам...")
    
    result = await show_results_screen(update, context, force_shared_view=True)
    logger.info(f"🎁 User {update.effective_user.id}: back_to_results_after_gift → RESULTS")
    return result

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск шаринга"""
    log_callback("skip_share", update, context)
    query = update.callback_query
    await query.answer("⏩ Продолжаем без репоста")
    
    result = await show_results_screen(update, context, force_shared_view=True)
    logger.info(f"🔄 User {update.effective_user.id}: skip_share → RESULTS")
    return result

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    log_callback("confirm_share", update, context)
    query = update.callback_query
    await query.answer("✅ Спасибо за репост! Ваш бонус готов!")
    
    context.user_data["has_shared"] = True
    logger.info(f"✅ User {update.effective_user.id}: has_shared установлен в True")
    
    logger.info(f"✅ User {update.effective_user.id}: confirm_share → open_gift_screen")
    return await open_gift_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    log_callback("restart_test", update, context)
    query = update.callback_query
    await query.answer("🔄 Перезапускаю тест...")
    
    # ✅ СОХРАНЯЕМ ВАЖНЫЕ ДАННЫЕ ПЕРЕД ОЧИСТКОЙ
    saved_limits = context.user_data.get("invite_limits", {})
    saved_invites = context.user_data.get("sexual_invites", [])
    
    logger.info(f"💾 Сохраняем лимиты перед перезапуском: {saved_limits}")
    
    # Очищаем данные пользователя
    context.user_data.clear()
    logger.debug(f"🧹 user_data очищена для {update.effective_user.id}")
    
    # ✅ ВОССТАНАВЛИВАЕМ ЛИМИТЫ
    if saved_limits:
        context.user_data["invite_limits"] = saved_limits
        logger.info(f"✅ Восстановлены лимиты: {saved_limits}")
    else:
        # Если лимитов не было, создаем новые
        context.user_data["invite_limits"] = {
            "free_used": 0,
            "total_purchased": 0,
            "paid_packages": []
        }
        logger.info(f"🆕 Созданы новые лимиты")
    
    if saved_invites:
        context.user_data["sexual_invites"] = saved_invites
        logger.info(f"✅ Восстановлено {len(saved_invites)} приглашений")
    
    # Инициализируем новые данные для теста
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    # Инициализируем хранилище приглашений (обновляем из БД)
    user_id = query.from_user.id
    context.user_data["sexual_invites"] = get_user_invites_from_api(user_id)
    
    logger.info(f"User {user_id} перезапустил тест (лимиты сохранены)")
    
    # Переходим к первому этапу
    return await show_stage_1_intro(update, context)

async def why_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Детали'"""
    log_callback("why_details_callback", update, context)
    query = update.callback_query
    await query.answer()
    
    details_text = """🎭 Немного правды с юмором...

Как говорится: 'Нет здоровых, есть не дообследованные!' 
Я ваш виртуальный психолог — дообследую 😉

🧠 Что я умею (кроме шуток):
• Вижу паттерны там, где вы видите хаос
• Нахожу систему там, где вы видите случайности  
• Обнаруживаю 'прошивку' вашего восприятия

🎯 Конкретно в тесте:

1️⃣ Конфигурация восприятия
   ↳ Как ваш разум фильтрует реальность

2️⃣ Конфигурация мышления  
   ↳ Как обрабатываете информацию

3️⃣ Конфигурация поведения
   ↳ Что делаете 'на автомате'

4️⃣ Точка роста
   ↳ Куда двигаться осознанно

⏱ 15 минут вместо лет терапии!
Потому что в 21 веке даже самопознание должно быть эффективным!"""
    
    keyboard = [[InlineKeyboardButton("👌 Понял(а). Начинаем →", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup)

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    log_callback("main_menu_callback", update, context)
    query = update.callback_query
    await query.answer("🏠 Возврат в главное меню...")
    
    try:
        await query.message.delete()
        logger.info(f"✅ User {update.effective_user.id}: Удалено сообщение при main_menu")
    except Exception as e:
        logger.warning(f"⚠️ User {update.effective_user.id}: Не удалось удалить сообщение: {e}")
    
    context.user_data.clear()
    logger.info(f"🧹 User {update.effective_user.id}: user_data полностью очищена")
    
    user = update.effective_user
    user_name = user.first_name or "Пользователь"
    
    welcome_text = (
        f"{user_name}, привет! 👋\n\n"
        f"<b>🧠 Я — Виртуальный психолог Вариатика.</b>\n\n"
        f"🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.\n"
        f"👁️ Увидите скрытые паттерны, которые управляют вашими решениями.\n\n"
        f"⚡ А главное — узнаете то, о себе знать действительно нужно.\n"
        f"🎯 То, что даст точку опоры для роста.\n\n"
        f"<b>📊 Вас ждёт:</b>\n\n"
        f"1️⃣ Адаптивный тест (4 этапа)\n"
        f"   ↳ Поймёте свой уникальный профиль\n\n"
        f"2️⃣ Персональные материалы\n"
        f"   ↳ Узнаете куда направлять усилия\n\n"
        f"🚀 Начнём исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать исследование →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А зачем это вообще?", callback_data="why_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    logger.info(f"✅ User {update.effective_user.id}: main_menu_callback → ConversationHandler.END")
    return ConversationHandler.END

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    log_callback("start_test", update, context)
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.first_name or "Пользователь"
    
    # 👇 ПРОВЕРЯЕМ В БД, ПРОХОДИЛ ЛИ ПОЛЬЗОВАТЕЛЬ ТЕСТ
    # Получаем приглашения пользователя из БД
    user_invites = get_user_invites_from_api(user_id)
    
    # Проверяем, есть ли у пользователя профиль в БД
    # (например, по наличию приглашений или другим признакам)
    has_profile = False
    profile_code = "SA-5_INT"  # значение по умолчанию
    
    # Если есть приглашения - значит пользователь уже проходил тест
    if user_invites and len(user_invites) > 0:
        has_profile = True
        # Пытаемся получить профиль из первого приглашения
        if user_invites[0].get('friend_profile'):
            profile_code = user_invites[0]['friend_profile']
        elif user_invites[0].get('target_profile_key'):
            profile_code = user_invites[0]['target_profile_key']
    
    # Также проверяем, есть ли профиль в user_data (на всякий случай)
    profile = context.user_data.get("profile")
    if profile and profile.get('display_name'):
        has_profile = True
        profile_code = profile.get('display_name', profile_code)
    
    if has_profile:
        logger.info(f"👤 Пользователь {user_id} уже проходил тест, профиль: {profile_code}")
        
        message = f"""
🧠 <b>ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА</b>

👋 <b>С ВОЗВРАЩЕНИЕМ, {user_name}!</b>

Я помню вас! 🎯
Вы уже проходили исследование, и я определил ваш профиль:

📊 <b>ВАШ ПРОФИЛЬ:</b> <code>{profile_code}</code>

━━━━━━━━━━━━━━━━━━━━
❓ <b>ЧТО ДЕЛАЕМ ДАЛЬШЕ?</b>

Вы можете:
🔄 <b>Пройти тест заново</b> — если хотите перепроверить себя или что-то изменилось
👥 <b>Заглянуть в «Мои отражения»</b> — посмотреть, кто из друзей уже прошёл тест по вашим ссылкам

━━━━━━━━━━━━━━━━━━━━
⬇️ <b>ВЫБЕРИТЕ ДЕЙСТВИЕ:</b>
"""
        keyboard = [
            [InlineKeyboardButton("🔄 ПРОЙТИ ТЕСТ ЗАНОВО", callback_data="restart_test")],
            [InlineKeyboardButton("👥 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
        return RESULTS
    
    # 👇 ЕСЛИ ПОЛЬЗОВАТЕЛЬ НОВЫЙ - ПРОДОЛЖАЕМ КАК ОБЫЧНО
    await query.answer()
    
    # ✅ СОХРАНЯЕМ ВАЖНЫЕ ДАННЫЕ ПЕРЕД ОЧИСТКОЙ
    current_invite = context.user_data.get("current_invite")
    saved_limits = context.user_data.get("invite_limits", {})
    saved_invites = context.user_data.get("sexual_invites", [])
    
    logger.info(f"🔍 start_test: current_invite = {current_invite}")
    logger.info(f"🔍 start_test: saved_limits = {saved_limits}")
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    # ✅ ВОССТАНАВЛИВАЕМ ВАЖНЫЕ ДАННЫЕ
    if current_invite:
        context.user_data["current_invite"] = current_invite
        logger.info(f"✅ current_invite сохранен при старте теста: {current_invite}")
    
    if saved_limits:
        context.user_data["invite_limits"] = saved_limits
        logger.info(f"✅ invite_limits сохранены: {saved_limits}")
    
    if saved_invites:
        context.user_data["sexual_invites"] = saved_invites
        logger.info(f"✅ sexual_invites сохранены: {len(saved_invites)} шт.")
    
    # Инициализируем новые данные для теста
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    # Инициализируем хранилище приглашений (обновляем из БД)
    context.user_data["sexual_invites"] = get_user_invites_from_api(user_id)
    
    logger.info(f"User {user_id} начал знакомство с психологом")
    
    return await show_stage_1_intro(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    logger.info(f"❌ Тест отменен пользователем {update.effective_user.id}")
    
    # Проверяем, откуда пришел запрос (из сообщения или callback)
    if update.message:
        await update.message.reply_text(
            f"🧠 *Исследование отменено.*\n\n"
            f"Если захотите продолжить наше знакомство, просто напишите:\n"
            f"`/start`\n\n"
            f"*Всегда готов помочь,\nВаш виртуальный психолог Вариатика* 🧠",
            parse_mode='Markdown'
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            f"🧠 *Исследование отменено.*\n\n"
            f"Если захотите продолжить наше знакомство, просто напишите:\n"
            f"`/start`\n\n"
            f"*Всегда готов помочь,\nВаш виртуальный психолог Вариатика* 🧠",
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

async def daily_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - показать статистику за сутки"""
    user_id = update.effective_user.id
    
    # Проверяем, админ ли это
    try:
        from config import ADMIN_IDS
    except ImportError:
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
    
    if user_id not in ADMIN_IDS:
        logger.warning(f"❌ Попытка доступа к статистике от не-админа {user_id}")
        await update.message.reply_text("❌ У вас нет прав для этой команды")
        return
    
    await update.message.reply_text("📊 Запрашиваю статистику за последние 24 часа...")
    
    try:
        response = requests.get(
            f"{API_URL}/api/daily-stats",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get('success'):
                await update.message.reply_text(f"❌ Ошибка: {data.get('error', 'Неизвестная ошибка')}")
                return
            
            # Форматируем сообщение
            message = format_stats_message(data)
            
            # Отправляем
            await update.message.reply_text(message, parse_mode="HTML")
                
        else:
            await update.message.reply_text(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

def format_stats_message(data):
    """Форматирует статистику в красивое сообщение"""
    from datetime import datetime
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # Рассчитываем доход
    sexual_income = data['sexual']['succeeded'] * 99
    four_f_income = data['four_f']['succeeded'] * 1
    total_income = sexual_income + four_f_income
    
    message = f"""
📊 <b>СТАТИСТИКА ЗА СУТКИ</b>
📅 {now}

━━━━━━━━━━━━━━━━━━━━
<b>👥 ПОЛЬЗОВАТЕЛИ</b>
└ Новых: {data['new_users']}

<b>💳 ПЛАТЕЖИ (ОСНОВНОЙ ПРОДУКТ)</b>
└ Всего: {data['payments']['total']}
└ ✅ Успешных: {data['payments']['succeeded']}
└ ⏳ Ожидают: {data['payments']['pending']}

<b>📊 ПОПУЛЯРНЫЕ ПРОФИЛИ</b>
"""
    
    for p in data['profiles']:
        message += f"└ {p['code']}: {p['count']}\n"
    
    message += f"""
━━━━━━━━━━━━━━━━━━━━
<b>🔞 18+ МОДУЛЬ</b>
└ Покупок: {data['sexual']['succeeded']}
└ Доход: {sexual_income}₽
└ Приглашений создано: {data['invites']['created']}
└ Приглашений использовано: {data['invites']['used']}

<b>🔑 4F МОДУЛЬ</b>
└ Покупок ключей: {data['four_f']['succeeded']}
└ Доход: {four_f_income}₽
└ Доставлено: {data['four_f']['delivered']}

━━━━━━━━━━━━━━━━━━━━
💰 <b>ИТОГОВЫЙ ДОХОД: {total_income}₽</b>
━━━━━━━━━━━━━━━━━━━━
"""
    
    return message
    

# ============================================
# ФУНКЦИИ ПОДАРКОВ И ПАКЕТОВ
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ"""
    log_callback("get_gift_screen", update, context)
    query = update.callback_query
    await query.answer()
    
    instruction_text = (
        f"🧠 <b>ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ</b>\n\n"
        f"Иногда самое полезное, что мы можем сделать для близких —\n"
        f"дать им зеркало.\n\n"
        f"<i>Поделитесь этим зеркалом с теми, кому оно может быть важно.</i>\n\n"
        f"⚔️ <b>А в благодарность — получите свой Меч:</b>\n"
        f"Терапевтическая сказка <b>«Мастер Меча»</b>\n\n"
        f"📖 <b>Эта сказка работает с тем, что мешает вам\n"
        f"«расправить плечи» на уровне убеждений.</b>\n\n"
        f"Она мягко трансформирует те ограничивающие установки,\n"
        f"которые создают невидимую тяжесть на ваших плечах.\n\n"
        f"🔗 <i>Просто нажмите кнопку ниже —\n"
        f"я подготовлю сообщение для друзей.</i>"
    )
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    keyboard = [
        [InlineKeyboardButton("🪞 Поделиться зеркалом", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился(ась) — получить подарок", callback_data="confirm_share")],
        [InlineKeyboardButton("Продолжить без этого →", callback_data="skip_share")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    logger.info(f"🪞 Gift screen показан пользователю {update.effective_user.id}")
    return GIFT_SCREEN

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН С ПОДАРКОМ"""
    log_callback("open_gift_screen", update, context)
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.debug(f"🎁 open_gift_screen: user_id={user_id}, has_shared={context.user_data.get('has_shared', False)}")
    logger.debug(f"🎁 GIFT_PDF_LINK из config: {GIFT_PDF_LINK}")
    
    await query.answer()
    
    if not context.user_data.get("has_shared", False):
        logger.warning(f"❌ Пользователь {user_id} пытается открыть подарок без has_shared")
        await query.answer(
            "❌ Сначала поделитесь зеркалом с друзьями, чтобы получить подарок!", 
            show_alert=True
        )
        return await show_results_screen(update, context, force_shared_view=True)
    
    # Проверяем наличие ссылки
    if not GIFT_PDF_LINK:
        logger.error(f"❌ GIFT_PDF_LINK не установлен для пользователя {user_id}")
        await query.answer(
            "❌ Ссылка на подарок временно недоступна. Пожалуйста, попробуйте позже.",
            show_alert=True
        )
        return await show_results_screen(update, context, force_shared_view=True)
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Открыть сказку «Мастер Меча»", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results_after_gift")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.info(f"🎁 User {user_id} opened gift (has_shared={context.user_data.get('has_shared', False)})")
    
    await query.edit_message_text(
        GIFT_SCREEN_TEXT,
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )
    
    logger.info(f"✅ Gift screen показан пользователю {user_id}")
    return OPEN_GIFT_SCREEN

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНОЕ ОПИСАНИЕ ПРОФИЛЯ"""
    log_callback("show_package_screen", update, context)
    query = update.callback_query
    await query.answer()
    
    profile_data = context.user_data.get("profile_data")
    logger.debug(f"📦 profile_data: {'есть' if profile_data else 'нет'}")
    
    # 👇 КЛАВИАТУРА ОПРЕДЕЛЯЕТСЯ ДО ВСЕХ УСЛОВИЙ
    keyboard = [
        [InlineKeyboardButton("🧠 Получить описание профиля за 690 ₽", callback_data="buy_package")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if profile_data:
        profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
        profile_info = f"\n📊 <b>Ваш профиль:</b> <code>{profile_code}</code>\n"
        personal_note = f"\n<i>Это описание будет создано персонально для вас на основе ваших ответов.</i>"
        logger.debug(f"📊 Профиль пользователя: {profile_code}")
    else:
        profile_info = "\n📊 <b>Профиль:</b> будет определен после теста\n"
        personal_note = f"\n<i>После теста я подготовлю персональное описание именно для вас.</i>"
        logger.debug("⚠️ profile_data отсутствует")
    
    package_text = (
        f"💎 <b>ПОЛНЫЙ ПАКЕТ — 690 ₽</b>\n\n"
        f"📘 <b>Полное описание твоего архетипа (15+ страниц)</b>\n"
        f"   → Детальный анализ личности\n"
        f"   → Ключевые паттерны поведения\n"
        f"   → Твои сильные стороны и точки роста\n"
        f"   → Потенциальные ограничения и как их обходить\n\n"
        f"📖 <b>Персональная терапевтическая сказка</b>\n"
        f"   → Поможет подружить твои внутренние противоречия 🤝\n\n"
        f"📚 <b>Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (PDF)</b>\n"
        f"   → Покажет, какие формы может принимать твой профиль\n\n"
        f"✅ <b>Мгновенный доступ после оплаты</b>\n"
        f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
        f"{profile_info}"
    )
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    logger.info(f"📦 Package screen показан пользователю {update.effective_user.id}")
    return PACKAGE_SCREEN

# ============================================
# ФУНКЦИИ ПЛАТЕЖЕЙ (Callback handlers)
# ============================================

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy для получения описания профиля"""
    user_id = update.effective_user.id
    logger.info(f"💳 buy_command вызван пользователем {user_id}")
    
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        logger.debug(f"💳 profile_data отсутствует для {user_id}, показываем выбор")
        keyboard = [
            [InlineKeyboardButton("🧠 Пройти тест для знакомства", callback_data="start_test")],
            [InlineKeyboardButton("💎 Получить описание без теста", callback_data="buy_without_test")]
        ]
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                f"🧠 *Чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
                f"давайте сначала познакомимся поближе через тест.*\n\n"
                f"💎 *Что вы получите в полном описании профиля:*\n"
                f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
                f"• 🎯 Конкретные паттерны поведения и мышления\n"
                f"• 🚀 Рекомендации по развитию от психолога\n"
                f"• 💡 Практические инструменты для жизни\n\n"
                f"💰 *Стоимость:* 690 рублей\n"
                f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
                f"*Выберите действие:*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"🧠 *Чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
                f"давайте сначала познакомимся поближе через тест.*\n\n"
                f"💎 *Что вы получите в полном описании профиля:*\n"
                f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
                f"• 🎯 Конкретные паттерны поведения и мышления\n"
                f"• 🚀 Рекомендации по развитию от психолога\n"
                f"• 💡 Практические инструменты для жизни\n\n"
                f"💰 *Стоимость:* 690 рублей\n"
                f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
                f"*Выберите действие:*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return PAYMENT_SCREEN
    
    profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    context.user_data["pending_payment_profile"] = profile_code
    logger.info(f"💳 Профиль для оплаты: {profile_code}")
    
    return await show_payment_screen(update, context)

async def buy_without_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка без прохождения теста"""
    log_callback("buy_without_test_callback", update, context)
    query = update.callback_query
    await query.answer("💳 Переход к оплате...")
    
    context.user_data["pending_payment_profile"] = "SA_1_DEF"
    logger.info(f"💳 Покупка без теста, профиль по умолчанию: SA_1_DEF")
    
    return await show_payment_screen(update, context)

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран создания платежа (БЕЗ ССЫЛКИ НА МАТЕРИАЛЫ)"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"💳 show_payment_screen для пользователя {user_id}")
    
    profile_data = context.user_data.get("profile_data")
    
    if profile_data and 'display_name' in profile_data:
        profile_code = profile_data['display_name']
        logger.info(f"✅ Использую РЕАЛЬНЫЙ профиль из теста: {profile_code}")
    else:
        profile_code = context.user_data.get("pending_payment_profile", "SA_1_DEF")
        logger.info(f"⚠️ Использую запасной профиль: {profile_code}")
    
    context.user_data["pending_payment_profile"] = profile_code
    
    if query:
        await query.edit_message_text(
            f"💳 *СОЗДАЮ ПЛАТЕЖ...*\n\n"
            f"🧠 *Виртуальный психолог Вариатика*\n"
            f"👤 *Клиент:* {user_name}\n"
            f"📊 *Профиль:* `{profile_code}`\n"
            f"💰 *Сумма:* 690 рублей\n\n"
            f"⏳ *Создаю ссылку для оплаты...*",
            parse_mode='Markdown'
        )
    
    logger.debug(f"💳 Вызов create_payment_advanced для {profile_code}")
    payment_result = await create_payment_advanced(user_id, profile_code, 690.00)
    
    if not payment_result.get("success"):
        error_msg = payment_result.get("error", "Неизвестная ошибка")
        details = payment_result.get("details", "")
        
        logger.error(f"❌ Ошибка создания платежа: {error_msg}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="buy_without_test")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        error_text = f"❌ *Ошибка при создании платежа:*\n`{error_msg}`"
        if details:
            error_text += f"\n\n`{details[:100]}`"
        
        if query:
            await query.edit_message_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return PAYMENT_SCREEN
    
    payment_id = payment_result["payment_id"]
    confirmation_url = payment_result["confirmation_url"]
    
    logger.info(f"✅ Платеж создан: {payment_id}, confirmation_url получен")
    
    context.user_data["last_payment_id"] = payment_id
    context.user_data["last_payment_profile"] = profile_code
    
    if "payment_data" not in context.user_data:
        context.user_data["payment_data"] = {}
    
    context.user_data["payment_data"][payment_id] = {
        "confirmation_url": confirmation_url,
        "profile_code": profile_code,
        "timestamp": time.time(),
        "user_id": user_id
    }
    
    logger.info(f"💾 Сохранён payment_id {payment_id} с confirmation_url")
    
    invoice_info = ""
    invoice_type = payment_result.get('invoice_type', 'yookassa_invoice')
    available_methods = payment_result.get('available_methods', 'all')
    
    if invoice_type == 'yookassa_invoice' and available_methods == 'all':
        invoice_info = (
            "\n💡 *ВСЕ способы оплаты доступны:*\n"
            "• СБП (Сбербанк Онлайн)\n"
            "• ЮMoney\n"
            "• Банковские карты (Visa/Mastercard/Мир)\n"
            "• Тинькофф, Альфа-Банк\n"
            "• И другие\n"
        )
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    message_text = (
        f"✅ *ПЛАТЕЖ СОЗДАН!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *Клиент:* {user_name}\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"📋 *ID платежа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 рублей\n"
        f"{invoice_info}"
        f"\n🔒 *Защита от дублей:* ✅ активна\n"
        f"📊 *Профиль сохранен:* ✅ `{profile_code}`\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты:\n"
        f"1. Вы получите уведомление\n"
        f"2. Ссылка на персональное описание профиля придет автоматически\n"
        f"3. Профиль `{profile_code}` будет сохранен\n\n"
        f"<i>Вы также можете вернуться к результатам теста и продолжить позже.</i>"
    )
    
    if query:
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    logger.info(f"💳 Экран платежа показан пользователю {user_id}")
    return PAYMENT_SCREEN

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа через API"""
    log_callback("check_payment_callback", update, context)
    query = update.callback_query
    await query.answer()
    
    payment_id = "_".join(query.data.split("_")[2:])
    logger.info(f"🔍 Проверка статуса платежа: {payment_id}")
    
    # Показываем сообщение о проверке
    await query.edit_message_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС ПЛАТЕЖА...*\n\n"
        f"📋 *ID:* `{payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    # Получаем данные платежа из памяти (только для ссылки на оплату)
    payment_data = context.user_data.get("payment_data", {})
    payment_info = payment_data.get(payment_id, {})
    
    # Реальная проверка через API (без тестового режима)
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
        else:
            logger.error(f"❌ API error: {response.status_code}")
            status = "error"
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке статуса: {e}")
        status = "error"
    
    logger.info(f"📊 Статус платежа {payment_id}: {status}")
    
    # Формируем ответ в зависимости от статуса
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания профиля нажмите кнопку ниже:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📥 ПОЛУЧИТЬ ОПИСАНИЕ ПРОФИЛЯ", callback_data=f"get_materials_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты нажмите кнопку ниже:*"
        )
        
        confirmation_url = payment_info.get("confirmation_url") if payment_info else None
        
        if confirmation_url:
            keyboard = [
                [InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=confirmation_url)],
                [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
            ]
    else:
        message = (
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"Статус: `{status}`\n"
            f"Платеж `{payment_id}` не найден или произошла ошибка.\n\n"
            f"Попробуйте позже."
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PAYMENT_SCREEN

async def get_materials_callback_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов после оплаты"""
    log_callback("get_materials_callback_payment", update, context)
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    user_id = update.effective_user.id
    
    logger.info(f"📦 Получение материалов для платежа {payment_id}, user_id={user_id}")
    
    await query.edit_message_text(
        f"📦 *ПОЛУЧАЮ МАТЕРИАЛЫ...*\n\n"
        f"📋 *ID платежа:* `{payment_id}`\n\n"
        f"⏳ Загружаю ссылки...",
        parse_mode='Markdown'
    )
    
    materials_result = await get_materials_link_api(payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка получения материалов: {error_msg}")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"get_materials_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПОЛУЧЕНИИ МАТЕРИАЛОВ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        logger.error(f"❌ Ссылка на материалы не найдена для платежа {payment_id}")
        await query.edit_message_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return PAYMENT_SCREEN
    
    logger.info(f"✅ Материалы получены для профиля {profile_code}")
    
    keyboard = [
        [InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"🎉 Ваше персональное описание профиля успешно подготовлено!\n\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 690 рублей\n\n"
        f"📚 *Что вы получили:*\n\n"
        f"💎 <b>ПОЛНЫЙ ПАКЕТ — 690 ₽</b>\n\n"
        f"📘 <b>Полное описание твоего архетипа (15+ страниц)</b>\n"
        f"   → Детальный анализ личности\n"
        f"   → Ключевые паттерны поведения\n"
        f"   → Твои сильные стороны и точки роста\n"
        f"   → Потенциальные ограничения и как их обходить\n\n"
        f"📖 <b>Персональная терапевтическая сказка</b>\n"
        f"   → Поможет подружить твои внутренние противоречия 🤝\n\n"
        f"📚 <b>Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (PDF)</b>\n"
        f"   → Покажет, какие формы может принимать твой профиль\n\n"
        f"✅ <b>Мгновенный доступ после оплаты</b>\n"
        f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания вашего персонального руководства:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return PAYMENT_SCREEN

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials для получения материалов после оплаты"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"📦 materials_command вызван пользователем {user_id}")
    
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        logger.warning(f"📦 У пользователя {user_id} нет активных платежей")
        await update.message.reply_text(
            f"🧠 *У вас нет активных платежей*\n\n"
            f"👤 *{user_name}*, для получения персонального описания профиля необходимо приобрести полный пакет.\n\n"
            f"💎 <b>ПОЛНЫЙ ПАКЕТ — 690 ₽</b>\n\n"
            f"📘 <b>Полное описание твоего архетипа (15+ страниц)</b>\n"
            f"   → Детальный анализ личности\n"
            f"   → Ключевые паттерны поведения\n"
            f"   → Твои сильные стороны и точки роста\n"
            f"   → Потенциальные ограничения и как их обходить\n\n"
            f"📖 <b>Персональная терапевтическая сказка</b>\n"
            f"   → Поможет подружить твои внутренние противоречия 🤝\n\n"
            f"📚 <b>Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (PDF)</b>\n"
            f"   → Покажет, какие формы может принимать твой профиль\n\n"
            f"✅ <b>Мгновенный доступ после оплаты</b>\n"
            f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
            f"Используйте команду `/buy` для покупки",
            parse_mode='HTML'
        )
        return
    
    logger.info(f"📦 Последний платеж пользователя {user_id}: {last_payment_id}")
    
    await update.message.reply_text(
        f"🔍 *ПОИСК ПЕРСОНАЛЬНОГО ОПИСАНИЯ...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Проверяю доступ...",
        parse_mode='Markdown'
    )
    
    materials_result = await get_materials_link_api(last_payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка получения материалов: {error_msg}")
        
        keyboard = [[InlineKeyboardButton("💳 Получить описание профиля", callback_data="buy_without_test")]]
        
        await update.message.reply_text(
            f"❌ *НЕ УДАЛОСЬ ПОЛУЧИТЬ МАТЕРИАЛЫ*\n\n"
            f"`{error_msg}`\n\n"
            f"Возможно, платеж еще не обработан или возникла ошибка.\n"
            f"Попробуйте позже или приобретите описание заново.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        logger.error(f"❌ Ссылка на материалы не найдена для платежа {last_payment_id}")
        await update.message.reply_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{last_payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"✅ Материалы отправлены пользователю {user_id} для профиля {profile_code}")
    
    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)]]
    
    await update.message.reply_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *{user_name}*, вот ваше персональное описание профиля:\n\n"
        f"📋 *ID заказа:* `{last_payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 690 рублей\n\n"
        f"📚 *Что вы получили:*\n\n"
        f"💎 <b>ПОЛНЫЙ ПАКЕТ — 690 ₽</b>\n\n"
        f"📘 <b>Полное описание твоего архетипа (15+ страниц)</b>\n"
        f"   → Детальный анализ личности\n"
        f"   → Ключевые паттерны поведения\n"
        f"   → Твои сильные стороны и точки роста\n"
        f"   → Потенциальные ограничения и как их обходить\n\n"
        f"📖 <b>Персональная терапевтическая сказка</b>\n"
        f"   → Поможет подружить твои внутренние противоречия 🤝\n\n"
        f"📚 <b>Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (PDF)</b>\n"
        f"   → Покажет, какие формы может принимать твой профиль\n\n"
        f"✅ <b>Мгновенный доступ после оплаты</b>\n"
        f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status для проверки статуса последнего платежа"""
    user_id = update.effective_user.id
    logger.info(f"📊 status_command вызван пользователем {user_id}")
    
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        logger.warning(f"📊 У пользователя {user_id} нет последнего платежа")
        await update.message.reply_text(
            "📭 *Нет активных платежей*\n\n"
            "У вас нет последних платежей для проверки.\n"
            "Используйте `/buy` для создания нового платежа.",
            parse_mode='Markdown'
        )
        return
    
    logger.info(f"📊 Проверка статуса платежа {last_payment_id} для пользователя {user_id}")
    
    await update.message.reply_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    status_result = await check_payment_status_api(last_payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка проверки статуса: {error_msg}")
        
        await update.message.reply_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    status = status_result.get("status", "unknown")
    logger.info(f"📊 Статус платежа {last_payment_id}: {status}")
    
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{last_payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания используйте команду:\n"
            f"`/materials`\n\n"
            f"✅ Вы получите мгновенный доступ к вашему руководству."
        )
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{last_payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты используйте команду:*\n"
            f"`/buy`\n\n"
            f"Или дождитесь обработки платежа."
        )
        
    else:
        message = (
            f"📊 *СТАТУС ПЛАТЕЖА:* `{status.upper()}`\n\n"
            f"📋 *ID:* `{last_payment_id}`\n\n"
            f"Если статус не меняется, попробуйте создать новый платеж: `/buy`"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ============================================
# ФУНКЦИЯ СТАРТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основная команда /start с поддержкой deep link для 18+ и проверкой существующего пользователя"""
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Пользователь"
    logger.info(f"🚀 /start вызван пользователем {user_id} (@{user.username})")
    
    # Инициализируем тестовые данные для нового пользователя
    init_test_data(user_id)
    
    # ===== 18+ DEEP LINK =====
    if context.args and context.args[0].startswith("sex_"):
        logger.info(f"🔞 18+ переход по ссылке: {context.args[0]}")
        return await sexual_invite_start(update, context)
    # ===== КОНЕЦ 18+ =====
    
        # ===== ПРОВЕРКА СУЩЕСТВУЮЩЕГО ПОЛЬЗОВАТЕЛЯ =====
    # Получаем профиль пользователя из контекста
    profile = context.user_data.get("profile")
    profile_data = context.user_data.get("profile_data")
    
    # 👇 ВАЖНО: Проверяем, есть ли у пользователя СВОЙ профиль (не из приглашения)
    has_own_profile = False
    profile_code = None
    
    # Проверяем наличие profile_data (новый формат)
    if profile_data and profile_data.get('display_name'):
        # Если есть current_invite, значит пользователь пришел по ссылке
        # и еще не прошел тест - это НЕ его профиль
        if not context.user_data.get("current_invite"):
            has_own_profile = True
            profile_code = profile_data.get('display_name')
    
    # Проверяем наличие profile (старый формат) для обратной совместимости
    elif profile and profile.get('display_name'):
        if not context.user_data.get("current_invite"):
            has_own_profile = True
            profile_code = profile.get('display_name', 'SA-5_INT')
    
    if has_own_profile:
        logger.info(f"👤 Пользователь {user_id} уже проходил тест, профиль: {profile_code}")
        
        message = f"""
🧠 <b>ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА</b>

👋 <b>С ВОЗВРАЩЕНИЕМ, {user_name}!</b>

Я помню вас! 🎯
Вы уже проходили исследование, и я определил ваш профиль:

📊 <b>ВАШ ПРОФИЛЬ:</b> <code>{profile_code}</code>

━━━━━━━━━━━━━━━━━━━━
❓ <b>ЧТО ДЕЛАЕМ ДАЛЬШЕ?</b>

Вы можете:
🔄 <b>Пройти тест заново</b> — если хотите перепроверить себя или что-то изменилось
👥 <b>Заглянуть в «Мои отражения»</b> — посмотреть, кто из друзей уже прошёл тест по вашим ссылкам

━━━━━━━━━━━━━━━━━━━━
⬇️ <b>ВЫБЕРИТЕ ДЕЙСТВИЕ:</b>
"""
        keyboard = [
            [InlineKeyboardButton("🔄 ПРОЙТИ ТЕСТ ЗАНОВО", callback_data="restart_test")],
            [InlineKeyboardButton("👥 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение в зависимости от того, откуда пришел запрос
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
        elif update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
        
        return RESULTS  # возвращаем состояние RESULTS
    
    # ===== ЕСЛИ ПОЛЬЗОВАТЕЛЬ НОВЫЙ =====
    current_state = context.user_data.get("conversation_state")
    if current_state is not None:
        logger.debug(f"🔄 Сброс состояния пользователя {user.id}")
        await update.message.reply_text("🔄 Начинаем новое исследование...")
        context.user_data.clear()
    
    welcome_text = (
        f"{user_name}, привет! 👋\n\n"
        f"<b>🧠 Я — Виртуальный психолог Вариатика.</b>\n\n"
        f"🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.\n"
        f"👁️ Увидите скрытые паттерны, которые управляют вашими решениями.\n\n"
        f"⚡ А главное — узнаете то, о себе знать действительно нужно.\n"
        f"🎯 То, что даст точку опоры для роста.\n\n"
        f"<b>📊 Вас ждёт:</b>\n\n"
        f"1️⃣ Адаптивный тест (4 этапа)\n"
        f"   ↳ Поймёте свой уникальный профиль\n\n"
        f"2️⃣ Персональные материалы\n"
        f"   ↳ Узнаете куда направлять усилия\n\n"
        f"🚀 Начнём исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать исследование →", callback_data="start_test")],
        [InlineKeyboardButton("🤔 А зачем это вообще?", callback_data="why_details")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return None

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ С ИСПРАВЛЕННЫМ CONVERSATIONHANDLER
# ============================================

def main():
    """Запуск бота"""
    import traceback
    import sys
    
    print("\n" + "="*70)
    print("🧠 ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА (ВЕРСИЯ 6.0)")
    print("="*70)
    
    # ПРОВЕРКА ТОКЕНА
    print(f"🔍 Токен загружен: {'✅ ДА' if TOKEN else '❌ НЕТ'}")
    if TOKEN:
        print(f"🔍 Длина токена: {len(TOKEN)} символов")
        print(f"🔍 Первые 10 символов: {TOKEN[:10]}...")
    
    # ПРИНУДИТЕЛЬНЫЙ СБРОС ВЕБХУКА
    import requests
    print("\n" + "="*50)
    print("🔄 СБРОС ВЕБХУКА И ОЧИСТКА")
    print("="*50)
    
    try:
        # Сначала удаляем вебхук
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(url, timeout=10)
        print(f"Ответ deleteWebhook: {response.json()}")
        
        # Проверяем, что вебхук удален
        url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        print(f"Информация о вебхуке: {response.json()}")
    except Exception as e:
        print(f"❌ Ошибка при сбросе вебхука: {e}")
        traceback.print_exc()
    
    print("="*50 + "\n")
    
    # ПРОВЕРКА ЗАГРУЗКИ ПРОФИЛЕЙ
    print("🔍 ПРОВЕРКА ЗАГРУЗКИ ПРОФИЛЕЙ")
    print("="*30)
    
    try:
        all_profiles = loader.get_all_profiles()
        print(f"📊 Всего профилей загружено: {len(all_profiles)}")
        
        for profile_type in ['sa', 'sp', 'ia', 'ip']:
            type_profiles = [p for p in all_profiles if p.lower().startswith(f"{profile_type}_")]
            print(f"🔍 {profile_type.upper()} профилей: {len(type_profiles)}")
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке профилей: {e}")
        traceback.print_exc()
    
    print("\n💳 ПРОВЕРКА ПЛАТЕЖНОЙ СИСТЕМЫ")
    print("="*30)
    print(f"📡 API URL: {API_URL}")
    print(f"🏪 YooKassa Shop ID: {YOOKASSA_SHOP_ID if YOOKASSA_SHOP_ID else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"🔑 YooKassa Secret Key: {'✅ УСТАНОВЛЕН' if YOOKASSA_SECRET_KEY else '❌ НЕ УСТАНОВЛЕН'}")
    print("="*30)
    
    # СОЗДАНИЕ ПРИЛОЖЕНИЯ
    print("\n🚀 СОЗДАНИЕ ПРИЛОЖЕНИЯ BOT")
    print("="*30)
    
    try:
        application = Application.builder().token(TOKEN).build()
        print("✅ Application создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания Application: {e}")
        traceback.print_exc()
        return
    
    # ДОБАВЛЕНИЕ ОБРАБОТЧИКОВ
    print("📝 Добавление обработчиков...")
    
    try:
        # Команды
        application.add_handler(CommandHandler("buy", buy_command))
        application.add_handler(CommandHandler("materials", materials_command))
        application.add_handler(CommandHandler("status", status_command))
        print("✅ Команды добавлены")
        
        # Общие callback-обработчики
        application.add_handler(CallbackQueryHandler(why_details_callback, pattern="^why_details$"))
        application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
        application.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
        print("✅ Callback-обработчики добавлены")
        
        # ConversationHandler
        print("⏳ Создание ConversationHandler...")
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                CallbackQueryHandler(start_test, pattern="^start_test$")
            ],
            states={
                # ===== ЭТАПЫ ТЕСТА =====
                STAGE_1: [
                    CallbackQueryHandler(show_stage_1_details, pattern="^stage1_details$"),
                    CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$"),
                    CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                    CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
                ],
                STAGE_2: [
                    CallbackQueryHandler(show_stage_2_intro, pattern="^show_stage_2_intro$"),
                    CallbackQueryHandler(show_stage_2_details, pattern="^stage2_details$"),
                    CallbackQueryHandler(back_to_stage2_intro, pattern="^back_to_stage2_intro$"),
                    CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                    CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
                ],
                STAGE_3: [
                    CallbackQueryHandler(show_stage_3_intro, pattern="^show_stage_3_intro$"),
                    CallbackQueryHandler(show_stage_3_details, pattern="^stage3_details$"),
                    CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$"),
                    CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                    CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
                ],
                STAGE_4: [
                    CallbackQueryHandler(show_stage_4_intro, pattern="^show_stage_4_intro$"),
                    CallbackQueryHandler(show_stage_4_details, pattern="^stage4_details$"),
                    CallbackQueryHandler(back_to_stage4_intro, pattern="^back_to_stage4_intro$"),
                    CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                    CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
                ],
                CLARIFICATION: [
                    CallbackQueryHandler(ask_clarification_question, pattern="^ask_clarification$"),
                    CallbackQueryHandler(handle_clarification_answer, pattern="^clarify_")
                ],
                
                # ===== РЕЗУЛЬТАТЫ =====
                RESULTS: [
                    CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                    CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                    CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                    CallbackQueryHandler(buy_command, pattern="^buy_package$"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                    CallbackQueryHandler(back_to_results_after_gift, pattern="^back_to_results_after_gift$"),
                    CallbackQueryHandler(show_results_screen, pattern="^show_results$"),
                    CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                    CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                    CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                    CallbackQueryHandler(show_my_sexual_profile, pattern="^show_my_sexual_profile$"),
                    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),  # 👈 ДОБАВЛЕННАЯ СТРОКА
                ],
                
                # ===== ПОДАРКИ И ПАКЕТЫ =====
                GIFT_SCREEN: [
                    CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                    CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                    CallbackQueryHandler(get_gift_screen, pattern="^get_gift$")
                ],
                PACKAGE_SCREEN: [
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                    CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                    CallbackQueryHandler(buy_command, pattern="^buy_package$"),
                ],
                OPEN_GIFT_SCREEN: [
                    CallbackQueryHandler(back_to_results_after_gift, pattern="^back_to_results_after_gift$"),
                    CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                ],
                PAYMENT_SCREEN: [
                    CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"),
                    CallbackQueryHandler(get_materials_callback_payment, pattern="^get_materials_"),
                    CallbackQueryHandler(buy_without_test_callback, pattern="^buy_without_test$"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
                ],
                
                # ===== 18+ МОДУЛЬ =====
                MY_SEXUAL_PROFILE: [
                    CallbackQueryHandler(send_invite_callback, pattern="^send_invite$"), 
                    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                ],
                SEXUAL_PROFILE_SCREEN: [
                    CallbackQueryHandler(show_my_sexual_profile, pattern="^show_my_sexual_profile$"),
                    CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"),
                    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                ],
                INVITES_LIST: [
    CallbackQueryHandler(sexual_invite_start, pattern="^sexual_invite_start$"),
    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$|^show_my_invites$"),
    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
    CallbackQueryHandler(copy_invite_callback, pattern="^copy_invite_"),
    CallbackQueryHandler(check_invite_callback, pattern="^check_invite_"),
    CallbackQueryHandler(create_invite_callback, pattern="^create_new_invite$"),
    CallbackQueryHandler(send_invite_callback, pattern="^send_invite$"),
    CallbackQueryHandler(confirm_send_callback, pattern="^confirm_send_"),                  
    CallbackQueryHandler(confirm_sent_callback, pattern="^confirm_sent_"),
    CallbackQueryHandler(contact_selected_callback, pattern="^contact_"),
    CallbackQueryHandler(four_f_main_menu_callback, pattern="^four_f_main_menu$"),
    CallbackQueryHandler(check_status_callback, pattern="^check_status_"),
    CallbackQueryHandler(friend_menu_callback, pattern="^friend_"),
    CallbackQueryHandler(buy_invite_packages_callback, pattern="^buy_invite_packages$"),
    CallbackQueryHandler(back_to_sexual_profile_callback, pattern="^back_to_sexual_profile$"),
],
                FRIEND_MENU: [
                    CallbackQueryHandler(standard_profile_callback, pattern="^std_"),
                    CallbackQueryHandler(intimate_profile_callback, pattern="^int_"),
                    CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"),
                    CallbackQueryHandler(four_f_explanation_callback, pattern="^4f_explain$"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                ],
                FOUR_F_PAYMENT_SCREEN: [
                    CallbackQueryHandler(process_payment_callback, pattern="^process_payment_"),
                    CallbackQueryHandler(pay_package_callback, pattern="^pay_package_"),
                    CallbackQueryHandler(process_package_payment_callback, pattern="^process_package_payment_"),
                    CallbackQueryHandler(check_package_callback, pattern="^check_package_"),
                    CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"),
                    CallbackQueryHandler(buy_invite_packages_callback, pattern="^buy_invite_packages$"),
                    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                ],
                FOUR_F_CONTENT_SCREEN: [
                    CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"),
                    CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                ],
                FOUR_F_MAIN: [
                    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                    CallbackQueryHandler(four_f_detailed_callback, pattern="^four_f_detailed$"),
                    CallbackQueryHandler(four_f_explanation_callback, pattern="^4f_explain$"),
                    CallbackQueryHandler(show_my_sexual_profile, pattern="^my_sexual_profile$"),
                ],
                FOUR_F_DETAILED: [
                    CallbackQueryHandler(four_f_main_menu_callback, pattern="^four_f_main_menu$"),
                ],
                FOUR_F_MENU: [
                    CallbackQueryHandler(buy_4f_key_callback, pattern="^buy_4f_"),
                    CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"),
                    CallbackQueryHandler(four_f_explanation_callback, pattern="^4f_explain$"),
                    CallbackQueryHandler(friend_menu_callback, pattern="^friend_"),
                ],
                FOUR_F_CONTENT: [
                    CallbackQueryHandler(buy_4f_key_callback, pattern="^buy_4f_"),
                    CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"),
                ],
                BUY_PACKAGES: [
                    CallbackQueryHandler(pay_package_callback, pattern="^pay_package_"),
                    CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            allow_reentry=True
        )
        application.add_handler(conv_handler)
        print("✅ ConversationHandler добавлен")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении обработчиков: {e}")
        traceback.print_exc()
        return
    
    logger.info("🧠 Виртуальный психолог Вариатика запущен!")
    logger.info("✅ ВЕРСИЯ 6.0: ПОЛНАЯ ИНТЕГРАЦИЯ С 18+ МОДУЛЕМ!")
    
    print("\n🚀 ЗАПУСК БОТА")
    print("="*30)
    print("⏳ Запускаю polling...")
    
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query'],
            poll_interval=1.0
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"\n❌ Ошибка запуска: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Добавляем путь для импорта модулей
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()
