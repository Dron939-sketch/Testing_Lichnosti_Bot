"""
БОТ ВАРИАТИКА версия 2.0
Полная интеграция платежной системы ЮKassa и автоматической выдачи материалов
"""

import os
import logging
import asyncio
import urllib.parse
import base64
import uuid
import time
import requests
from typing import Dict, Optional, List, Any
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ============================================
# КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ============================================

# Получение токена бота
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Конфигурация API и платежей
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

# Проверка режима платежей
def check_payment_mode() -> str:
    """Определяет режим работы (боевой/тестовый)"""
    if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_'):
        return "БОЕВОЙ"
    else:
        return "ТЕСТОВЫЙ"

# Эндпоинты API
API_ENDPOINTS = {
    "create_payment": f"{API_URL}/api/create-payment-advanced",
    "check_access": f"{API_URL}/api/check-access/{{user_id}}",
    "get_materials": f"{API_URL}/api/get-materials/{{payment_id}}",
    "payment_status": f"{API_URL}/api/payment-status/{{payment_id}}",
    "save_profile": f"{API_URL}/api/save-profile",
    "update_yookassa_id": f"{API_URL}/api/update-yookassa-id"
}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния ConversationHandler
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION = range(10)

# Константы
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую.."

# ============================================
# КАРТА МАТЕРИАЛОВ НА ЯНДЕКС.ДИСКЕ (36 ПРОФИЛЕЙ)
# ============================================

YANDEX_DISK_FOLDERS = {
    # SA профили (9 папок)
    "SA_1_DEF": "https://disk.yandex.ru/d/HAcOfAg1tpIedA",
    "SA_2_SIT": "https://disk.yandex.ru/d/MwdMClX9koCTmA",
    "SA_3_CON": "https://disk.yandex.ru/d/NKN_XemK62t5nA",
    "SA_4_EXP": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA",
    "SA_5_INT": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg",
    "SA_6_AUT": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag",
    "SA_7_VAL": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g",
    "SA_8_TRA": "https://disk.yandex.ru/d/SqlDISkse1OEGQ",
    "SA_9_IDE": "https://disk.yandex.ru/d/vGzHmuckInNL5g",
    
    # SP профили (9 папок)
    "SP_1_DEF": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA",
    "SP_2_SIT": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA",
    "SP_3_CON": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA",
    "SP_4_EXP": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ",
    "SP_5_INT": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg",
    "SP_6_AUT": "https://disk.yandex.ru/d/xWBv4TLFosOB5g",
    "SP_7_VAL": "https://disk.yandex.ru/d/K1whXj6C6KAazQ",
    "SP_8_TRA": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg",
    "SP_9_IDE": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ",
    
    # IA профили (9 папок)
    "IA_1_DEF": "https://disk.yandex.ru/d/M1Y7z175uGKIHg",
    "IA_2_SIT": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ",
    "IA_3_CON": "https://disk.yandex.ru/d/DCkqqALby9UpFg",
    "IA_4_EXP": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg",
    "IA_5_INT": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g",
    "IA_6_AUT": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg",
    "IA_7_VAL": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ",
    "IA_8_TRA": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw",
    "IA_9_IDE": "https://disk.yandex.ru/d/ub0YpQQgS4g6rQ",
    
    # IP профили (9 папок)
    "IP_1_DEF": "https://disk.yandex.ru/d/m-WOQwDdgQxsnQ",
    "IP_2_SIT": "https://disk.yandex.ru/d/aL4VlAQdlaZ-6g",
    "IP_3_CON": "https://disk.yandex.ru/d/N8GG9XbnC3bFhg",
    "IP_4_EXP": "https://disk.yandex.ru/d/54RFOZmGhA4cfA",
    "IP_5_INT": "https://disk.yandex.ru/d/l5iFTIX8-gTycQ",
    "IP_6_AUT": "https://disk.yandex.ru/d/bTo_vcCoC1KU7Q",
    "IP_7_VAL": "https://disk.yandex.ru/d/TMx1VP843bnJQw",
    "IP_8_TRA": "https://disk.yandex.ru/d/e9KfJdLcl3gp7g",
    "IP_9_IDE": "https://disk.yandex.ru/d/ZiQPHJSDrrWZhw"
}

# ============================================
# ВОПРОСЫ ТЕСТА (упрощенная версия для примера)
# ============================================

STAGE_1_QUESTIONS = [
    {
        "id": "q1_1",
        "text": "У тебя неожиданно освободился вечер.\n\nЧто звучит привлекательнее?",
        "options": {
            "a": {"text": "Позвать друзей", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Побыть одному", "scores": {"INTERNAL": 2}},
            "c": {"text": "Сходить куда-то", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Почитать/посмотреть", "scores": {"INTERNAL": 1}}
        }
    },
    # ... остальные вопросы (сокращено для примера)
]

# Типы восприятия
PERCEPTION_TYPES = {
    ("EXTERNAL", "SYMBOLIC"): {
        "name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ",
        "code": "SA",
        "description": "Фокус на внешних отношениях"
    },
    ("INTERNAL", "SYMBOLIC"): {
        "name": "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ",
        "code": "IA",
        "description": "Фокус на внутренних смыслах"
    },
    ("EXTERNAL", "MATERIAL"): {
        "name": "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ",
        "code": "SP",
        "description": "Фокус на внешних достижениях"
    },
    ("INTERNAL", "MATERIAL"): {
        "name": "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ",
        "code": "IP",
        "description": "Фокус на внутреннем порядке"
    }
}

# ============================================
# ПЛАТЕЖНАЯ СИСТЕМА - ОСНОВНЫЕ ФУНКЦИИ
# ============================================

def get_user_access(user_id: int) -> dict:
    """Получает информацию о доступах пользователя"""
    try:
        response = requests.get(
            f"{API_URL}/api/check-access/{user_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API error {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_materials_link(user_id: int, payment_id: str, token: str = None) -> dict:
    """Получает ссылку на материалы"""
    try:
        url = f"{API_URL}/api/get-materials/{payment_id}"
        params = {"user_id": user_id}
        
        if token:
            params["token"] = token
            
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API error {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            return {"success": True, "status": status}
        else:
            return {"success": False, "error": f"API error {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_payment_in_db(user_id: int, amount: float = 690.0, 
                         is_test: bool = False, profile_data: dict = None) -> dict:
    """
    Создает запись о платеже в БД с передачей профиля
    """
    try:
        timestamp = int(time.time())
        payment_id = f"test_{user_id}_{timestamp}" if is_test else f"variatica_{user_id}_{timestamp}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "description": f"Тестовый платеж {amount} руб" if is_test else "Полный пакет ВАРИАТИКА - 690 руб",
            "email": f"user_{user_id}@telegram.org"
        }
        
        # Передаем профиль если есть
        if profile_data:
            simplified_profile = {
                "profile_key": profile_data.get("display_name", ""),
                "type_code": profile_data.get("type_code", ""),
                "level": profile_data.get("level", 1),
                "dilts_code": profile_data.get("dilts_code", "")
            }
            payload["profile_data"] = simplified_profile
        
        # Отправляем в API
        response = requests.post(
            f"{API_URL}/api/create-payment-advanced",
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            return {
                "success": True,
                "payment_id": payment_id,
                "confirmation_url": response_data.get('confirmation_url'),
                "yookassa_id": response_data.get('yookassa_id')
            }
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 690.0, 
                           email: str = None, is_test: bool = False) -> dict:
    """
    Создает платеж через Invoices API ЮKassa
    """
    try:
        # Проверяем наличие ключей
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            return {"success": False, "error": "YooKassa credentials not configured"}
        
        # Кодирование авторизации
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        # Уникальный ключ для защиты от дублей
        unique_id = uuid.uuid4().hex[:16]
        idempotence_key = f"{payment_id}_{unique_id}_{int(time.time())}"
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': idempotence_key
        }
        
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Формирование payload для Invoices API
        description = f"Тестовый платеж 1 рубль #{payment_id}" if is_test else f"Полный пакет ВАРИАТИКА #{payment_id}"
        item_description = "Тестовый доступ" if is_test else "Полный пакет ВАРИАТИКА: полный разбор профиля + книга + терапевтическая сказка"
        
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
                "is_test": str(is_test)
            },
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": item_description,
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
        
        # URL API в зависимости от режима
        api_url = "https://api.yookassa.ru/v3/payments" if check_payment_mode() == "БОЕВОЙ" else "https://api.yookassa.ru/v3/payments"
        
        # Отправка запроса в ЮKassa
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"YooKassa response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if not confirmation_url:
                return {"success": False, "error": "No confirmation URL"}
            
            # Сохраняем ID платежа в БД
            try:
                requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={
                        "payment_id": payment_id,
                        "yookassa_id": data.get('id'),
                        "status": "waiting"
                    },
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Failed to update YooKassa ID: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "confirmation_url": confirmation_url,
                "invoice_type": "yookassa_invoice",
                "available_methods": "all"
            }
        else:
            error_text = response.text if hasattr(response, 'text') else "No error details"
            return {"success": False, "error": f"YooKassa error {response.status_code}: {error_text}"}
            
    except Exception as e:
        logger.error(f"Exception in create_yookassa_payment: {e}")
        return {"success": False, "error": str(e)}

def generate_yandex_disk_link(profile_key: str) -> str:
    """
    Генерирует ссылку на Яндекс.Диск для профиля
    """
    # Приводим к верхнему регистру для поиска
    profile_key_upper = profile_key.upper().replace("-", "_")
    
    logger.info(f"🔗 Генерация ссылки для профиля: {profile_key} → {profile_key_upper}")
    
    # 1. Прямой поиск
    if profile_key_upper in YANDEX_DISK_FOLDERS:
        return YANDEX_DISK_FOLDERS[profile_key_upper]
    
    # 2. Пробуем разные форматы
    variations = [
        profile_key_upper,
        profile_key_upper.replace("_", " "),
        profile_key_upper.replace(" ", "_"),
    ]
    
    for variation in variations:
        if variation in YANDEX_DISK_FOLDERS:
            return YANDEX_DISK_FOLDERS[variation]
    
    # 3. Ищем по частям
    parts = profile_key_upper.split('_')
    if len(parts) >= 3:
        # Пробуем с разными суффиксами
        suffixes = ['DEF', 'SIT', 'CON', 'EXP', 'INT', 'AUT', 'VAL', 'TRA', 'IDE']
        for suffix in suffixes:
            test_key = f"{parts[0]}_{parts[1]}_{suffix}"
            if test_key in YANDEX_DISK_FOLDERS:
                return YANDEX_DISK_FOLDERS[test_key]
    
    # 4. Fallback на первый профиль типа
    if len(parts) >= 1:
        type_prefix = parts[0]
        for key in YANDEX_DISK_FOLDERS:
            if key.startswith(type_prefix + "_"):
                return YANDEX_DISK_FOLDERS[key]
    
    # 5. Аварийный fallback
    logger.error(f"❌ Не найдена ссылка для профиля: {profile_key}")
    return "https://disk.yandex.ru/d/HAcOfAg1tpIedA"  # SA_1_DEF

# ============================================
# КОМАНДЫ ДЛЯ ПОЛУЧЕНИЯ МАТЕРИАЛОВ И ПРОВЕРКИ
# ============================================

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда для получения материалов после оплаты
    """
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🚀 User {user_id} ({user_name}) requested materials")
    
    # 1. Проверяем доступ через API
    access_data = get_user_access(user_id)
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: Правильная проверка success
    if not access_data.get('success', False):
        error_msg = access_data.get('error', 'Unknown error')
        logger.error(f"❌ API error for user {user_id}: {error_msg}")
        
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    # 2. Если нет доступа - предлагаем купить
    if not access_data.get('has_access', False):
        logger.info(f"❌ User {user_id} has no access")
        
        keyboard = [
            [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП 690 РУБ", callback_data="buy_variatica_package")],
            [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")]
        ]
        
        await update.message.reply_text(
            f"📭 *У ВАС НЕТ ДОСТУПА*\n\n"
            f"👤 *{user_name}*, для получения материалов необходимо оплатить доступ.\n\n"
            f"💎 *Полный пакет ВАРИАТИКА:* 690 руб\n"
            f"• Полный разбор вашего профиля (15+ страниц)\n"
            f"• Терапевтическая сказка\n"
            f"• Книга ВАРИАТИКА (.PDF)\n"
            f"• Персональные рекомендации\n"
            f"• Карта сильных и слабых сторон\n\n"
            f"🧪 *Тестовая оплата:* 1 руб\n"
            f"• Проверка платежной системы\n"
            f"• Тестовые материалы\n\n"
            f"Нажмите кнопку ниже для покупки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # 3. Ищем активный доступ
    accesses = access_data.get('accesses', [])
    logger.info(f"🔍 Found {len(accesses)} accesses for user {user_id}")
    
    if not accesses:
        await update.message.reply_text(
            "❌ *Ошибка данных доступа*\n\n"
            "Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    for access in accesses:
        if access.get('has_access', False) and access.get('is_active', False):
            payment_id = access.get('payment_id')
            access_token = access.get('access_token')
            profile_key = access.get('profile_key')
            
            logger.info(f"✅ Found active access: payment_id={payment_id}, profile_key={profile_key}")
            
            # 4. Получаем ссылку на материалы
            materials_data = get_materials_link(user_id, payment_id, access_token)
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: Правильная проверка success
            if materials_data.get('success', False):
                # Вариант A: API дал прямую ссылку
                materials_link = materials_data.get('materials_link')
                if materials_link:
                    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                    
                    await update.message.reply_text(
                        f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                        f"🎯 Профиль: `{profile_key}`\n"
                        f"🔗 Ссылка на Яндекс.Диск\n\n"
                        f"Нажмите кнопку ниже для скачивания:",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return
            
            # Вариант B: Генерируем ссылку локально
            if profile_key:
                materials_link = generate_yandex_disk_link(profile_key)
                
                keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                
                await update.message.reply_text(
                    f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                    f"🎯 Ваш профиль: `{profile_key}`\n"
                    f"📁 Папка на Яндекс.Диске\n\n"
                    f"Нажмите кнопку ниже для скачивания:",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
    
    # Если дошли сюда - что-то пошло не так
    await update.message.reply_text(
        "❌ *Не удалось получить материалы*\n\n"
        "Попробуйте:\n"
        "1. Проверить статус доступа (/myaccess)\n"
        "2. Обратиться в поддержку",
        parse_mode='Markdown'
    )

async def myaccess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса доступа"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🔍 User {user_id} ({user_name}) checked access")
    
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n"
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    if access_data.get('has_access'):
        accesses = access_data.get('accesses', [])
        
        for access in accesses:
            if access.get('has_access') and access.get('is_active'):
                payment_id = access.get('payment_id')
                profile_key = access.get('profile_key')
                granted_at = access.get('granted_at')
                amount = access.get('amount', 690)
                
                materials_link = generate_yandex_disk_link(profile_key) if profile_key else None
                
                message = (
                    f"✅ *ДОСТУП АКТИВЕН!*\n\n"
                    f"👤 *Пользователь:* {user_name}\n"
                    f"🎯 *Профиль:* `{profile_key or 'Не указан'}`\n"
                    f"💰 *Оплачено:* {amount} руб\n"
                    f"📦 *Пакет:* Полный ВАРИАТИКА\n"
                    f"📅 *Доступ открыт:* {granted_at or 'Неизвестно'}\n\n"
                )
                
                if materials_link:
                    message += f"🔗 *Ссылка:* `{materials_link}`\n\n"
                    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                else:
                    message += "📁 *Материалы:* Готовятся к выдаче\n\n"
                    keyboard = []
                
                message += "📚 *В папке:*\n• Полный разбор профиля\n• Терапевтическая сказка\n• Книга ВАРИАТИКА\n• Рекомендации"
                
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                return
    else:
        await update.message.reply_text(
            f"❌ *ДОСТУП НЕ АКТИВЕН*\n\n"
            f"👤 *Пользователь:* {user_name}\n"
            f"📦 *Статус:* Доступ не оплачен\n\n"
            f"Для получения доступа:\n"
            f"1. Пройдите тест (/start)\n"
            f"2. Нажмите 'Полный пакет рекомендаций'\n"
            f"3. Оплатите доступ\n"
            f"4. Используйте /materials для получения материалов",
            parse_mode='Markdown'
        )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    if not context.args:
        await update.message.reply_text(
            "❌ *Укажите ID платежа*\n\n"
            "Пример: `/check test_1234567890`\n"
            "Пример: `/check variatica_1234567890`",
            parse_mode='Markdown'
        )
        return
    
    payment_id = context.args[0]
    
    await update.message.reply_text(f"🔍 *Проверяю статус:* `{payment_id}`", parse_mode='Markdown')
    
    result = check_payment_status_db(payment_id)
    
    if not result["success"]:
        await update.message.reply_text(f"❌ *Ошибка:* {result.get('error')}", parse_mode='Markdown')
        return
    
    status = result.get("status", "unknown")
    
    if status == "succeeded":
        await update.message.reply_text(
            f"🎉 *ПЛАТЕЖ ОПЛАЧЕН!*\n\n"
            f"✅ Платеж `{payment_id}` успешно завершен!\n\n"
            f"*🔓 ДОСТУП ОТКРЫТ!*\n"
            f"Для получения материалов используйте /materials",
            parse_mode='Markdown'
        )
    elif status in ["pending", "waiting"]:
        await update.message.reply_text(
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Заказ `{payment_id}` еще не оплачен.\n"
            f"После оплаты используйте /materials для получения материалов.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"📊 *Статус:* `{status}`", parse_mode='Markdown')

# ============================================
# ОБРАБОТЧИКИ ДЛЯ ЭКРАНА РЕЗУЛЬТАТОВ
# ============================================

async def buy_variatica_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка полного пакета ВАРИАТИКА"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"💰 User {user_id} ({user_name}) buying full package")
    
    await query.edit_message_text("💎 *Создаю заказ на полный пакет ВАРИАТИКА...*", parse_mode='Markdown')
    
    # Проверяем, есть ли профиль в context.user_data
    profile_data = None
    if 'profile_data' in context.user_data:
        profile_data = context.user_data['profile_data']
        logger.info(f"📤 Using profile from context: {profile_data.get('display_name')}")
    
    # Создаем платеж в БД
    db_result = create_payment_in_db(
        user_id, 
        amount=690.0, 
        is_test=False, 
        profile_data=profile_data
    )
    
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка создания заказа:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    # Если API вернул ссылку - используем ее
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
    else:
        # Иначе создаем платеж через ЮKassa
        payment_result = create_yookassa_payment(payment_id, user_id, amount=690.0, is_test=False)
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка платежной системы:*\n`{error_msg}`", parse_mode='Markdown')
            return
        confirmation_url = payment_result["confirmation_url"]
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("⬅️ Назад к пакетам", callback_data="show_package")]
    ]
    
    await query.edit_message_text(
        f"✅ *ЗАКАЗ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 руб\n"
        f"📚 *Пакет:* Полный пакет ВАРИАТИКА\n"
        f"🎯 *Профиль:* {'Привязан к заказу' if profile_data else 'Определится после теста'}\n\n"
        f"*Что вы получите после оплаты:*\n"
        f"✅ Полный разбор профиля (15+ страниц)\n"
        f"✅ Терапевтическую сказку\n"
        f"✅ Книгу ВАРИАТИКА (.PDF)\n"
        f"✅ Персональные рекомендации\n"
        f"✅ Карту сильных и слабых сторон\n\n"
        f"💡 *Все способы оплаты доступны:* СБП, ЮMoney, карты\n"
        f"🔒 *Защита от дублей:* ✅ активна\n\n"
        f"*Для оплаты нажмите кнопку ниже:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж 1 рубль"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"🧪 User {user_id} ({user_name}) creating test payment")
    
    await query.edit_message_text("🧪 *Создаю тестовый платеж 1 рубль...*", parse_mode='Markdown')
    
    # Создаем платеж в БД
    db_result = create_payment_in_db(user_id, amount=1.0, is_test=True)
    
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    
    # Если API вернул ссылку - используем ее
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
    else:
        # Иначе создаем платеж через ЮKassa
        payment_result = create_yookassa_payment(payment_id, user_id, amount=1.0, is_test=True)
        if not payment_result["success"]:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка:*\n`{error_msg}`", parse_mode='Markdown')
            return
        confirmation_url = payment_result["confirmation_url"]
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("⬅️ Назад к пакетам", callback_data="show_package")]
    ]
    
    await query.edit_message_text(
        f"🧪 *ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"📋 *ID:* `{payment_id}`\n\n"
        f"*Для проверки платежной системы:*\n"
        f"1. Нажмите кнопку оплаты\n"
        f"2. Выберите любой способ оплаты\n"
        f"3. После успешной оплаты вернитесь в бот\n"
        f"4. Система автоматически выдаст тестовые материалы\n\n"
        f"💡 *Все способы оплаты доступны*\n"
        f"🔒 *Защита от дублей:* ✅ активна",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def status_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа по кнопке"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("status_", "")
    
    await query.edit_message_text(f"🔍 *Проверяю статус:* `{payment_id}`", parse_mode='Markdown')
    
    result = check_payment_status_db(payment_id)
    
    if not result["success"]:
        await query.edit_message_text(f"❌ *Ошибка:* {result.get('error')}", parse_mode='Markdown')
        return
    
    status = result.get("status", "unknown")
    
    if status == "succeeded":
        keyboard = [[InlineKeyboardButton("📥 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data="get_materials_after_payment")]]
        
        await query.edit_message_text(
            f"🎉 *ПЛАТЕЖ ОПЛАЧЕН!*\n\n"
            f"✅ Платеж `{payment_id}` успешно завершен!\n\n"
            f"*🔓 ДОСТУП ОТКРЫТ!*\n"
            f"Нажмите кнопку ниже для получения материалов:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif status in ["pending", "waiting"]:
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить статус", callback_data=f"status_{payment_id}")],
            [InlineKeyboardButton("💳 Оплатить снова", callback_data="show_package")]
        ]
        
        await query.edit_message_text(
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Заказ `{payment_id}` еще не оплачен.\n\n"
            f"Если вы уже оплатили, подождите несколько минут и обновите статус.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(f"📊 *Статус:* `{status}`", parse_mode='Markdown')

# ============================================
# ОБНОВЛЕННЫЙ ЭКРАН ПАКЕТА
# ============================================

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновленный экран пакета с автоматической оплатой"""
    query = update.callback_query
    await query.answer()
    
    payment_mode = check_payment_mode()
    
    package_text = (
        f"<b>💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
        f"<b>Что входит:</b>\n"
        f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
        f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
        f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
        f"• Персональные рекомендации по развитию\n"
        f"• Карта сильных и слабых сторон\n\n"
        f"<b>Цена:</b> 690 ₽\n\n"
        f"<b>Режим работы:</b> {payment_mode}\n\n"
        f"<b>ВСЕ способы оплаты доступны:</b>\n"
        f"• СБП (Система быстрых платежей)\n"
        f"• ЮMoney (Яндекс.Деньги)\n"
        f"• Банковские карты (Visa, MasterCard, Мир)\n"
        f"• Apple Pay / Google Pay\n"
        f"• QIWI и другие\n\n"
        f"💡 <b>После оплаты вы получите:</b>\n"
        f"• Мгновенный доступ к материалам\n"
        f"• Ссылку на Яндекс.Диск с вашей персональной папкой\n"
        f"• Чек по 54-ФЗ (в боевом режиме)\n"
        f"• Техническую поддержку"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 КУПИТЬ ДОСТУП 690 РУБ", callback_data="buy_variatica_package")],
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

# ============================================
# ФУНКЦИИ ТЕСТА (упрощенные для примера)
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%\nПройдено: {current}/{total}"

def determine_perception_type(scores):
    """Определяет тип восприятия"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    focus = "EXTERNAL" if external >= internal else "INTERNAL"
    anxiety = "SYMBOLIC" if symbolic >= material else "MATERIAL"
    
    type_data = PERCEPTION_TYPES.get((focus, anxiety), PERCEPTION_TYPES[("EXTERNAL", "SYMBOLIC")])
    return type_data["name"]

def get_type_code(perception_type: str) -> str:
    """Код типа (SA/IA/SP/IP)"""
    type_map = {
        "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "SA",
        "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "IA",
        "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "SP",
        "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "IP"
    }
    return type_map.get(perception_type, "SA")

def get_level_name(level_num):
    """Получаем название уровня по номеру"""
    level_names = {
        1: "ДЕФИЦИТАРНЫЙ",
        2: "ПОИСКОВЫЙ", 
        3: "КОНСТРУКТИВНЫЙ",
        4: "КРИЗИСНЫЙ",
        5: "ИНТЕГРАТИВНЫЙ",
        6: "АЛЬТРУИСТИЧЕСКИЙ",
        7: "МУДРЕЦКИЙ",
        8: "СИСТЕМНЫЙ",
        9: "ТРАНСЦЕНДЕНТНЫЙ"
    }
    return level_names.get(level_num, f"Уровень {level_num}")

def get_dilts_code(dilts_level: str) -> str:
    """Код Дилтса"""
    dilts_map = {
        "ENVIRONMENT": "env",
        "BEHAVIOR": "beh",
        "CAPABILITIES": "cap",
        "VALUES": "val",
        "IDENTITY": "ide"
    }
    return dilts_map.get(dilts_level, "env")

def determine_dilts_level(dilts_answers):
    """Определяет уровень Дилтса"""
    if not dilts_answers:
        return "ENVIRONMENT"
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(1)[0]
    return most_common[0]

def calculate_thinking_level_by_scores(level_scores_dict):
    """Определяет уровень мышления (1-9) по системе баллов"""
    if not level_scores_dict:
        return 1
    
    numeric_scores = {int(k): v for k, v in level_scores_dict.items() if k.isdigit()}
    
    if not numeric_scores:
        return 1
    
    max_score = max(numeric_scores.values())
    max_levels = [level for level, score in numeric_scores.items() if score == max_score]
    
    if not max_levels:
        return 1
    
    return max(max_levels)

def calculate_final_level(stage2_level, stage3_scores):
    """Финальный уровень (приоритет поведению)"""
    if not stage3_scores:
        return stage2_level
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    weighted = stage3_avg * 0.7 + stage2_level * 0.3
    final_level = int(round(weighted))
    
    logger.info(f"Final level: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}, weighted={weighted:.2f}, final={final_level}")
    return max(1, min(9, final_level))

def calculate_profile_final(context_data: dict) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля"""
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    level_scores_dict = context_data.get("stage2_level_scores_dict", {})
    stage2_level = calculate_thinking_level_by_scores(level_scores_dict)
    
    stage3_scores = context_data.get("stage3_level_scores", [])
    final_level = calculate_final_level(stage2_level, stage3_scores)
    
    dilts_answers = context_data.get("stage4_dilts_answers", [])
    dilts_level = determine_dilts_level(dilts_answers)
    dilts_code = get_dilts_code(dilts_level)
    
    logger.info(f" FINAL PROFILE CALCULATION:")
    logger.info(f"   Type: {type_code} ({perception_type})")
    logger.info(f"   Level: {final_level} ({get_level_name(final_level)})")
    logger.info(f"   Dilts: {dilts_level} ({dilts_code})")
    
    return {
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code,
        
        "display_name": f"{type_code}_{final_level}_{dilts_code}",
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        
        "stage2_level": stage2_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
    }

# ============================================
# ОСНОВНЫЕ ЭКРАНЫ ТЕСТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест ВАРИАТИКА ver 2.0!</b>\n\n"
        f"🔍 <b>Узнай о себе то, что ты ещё не знаешь.</b>\n\n"
        f"<b>Этот тест поможет определить:</b>\n"
        f"• Как ты воспринимаешь реальность \n"
        f"• Каким способом обрабатываешь информацию \n"
        f"• Какие поведенческие паттерны у тебя есть \n"
        f"• Что не дает тебе расти 🚀\n\n"
        f"🎯 <b>Что тебя ждёт:</b>\n\n"
        f"1️⃣ <b>ЭТАП 1:</b> Конфигурация восприятия (8 вопросов)\n"
        f"2️⃣ <b>ЭТАП 2:</b> Конфигурация мышления (8 вопросов)\n"
        f"3️⃣ <b>ЭТАП 3:</b> Поведенческие паттерны (8 вопросов)\n"
        f"4️⃣ <b>ЭТАП 4:</b> Конфликт логических уровней (8 вопросов)\n\n"
        f"⏱ Займёт 10-15 минут\n\n"
        f"📌 Отвечай честно, как есть сейчас, а не как хотелось бы.\n\n"
        f"Готов начать? 🚀"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    logger.info(f"User {update.effective_user.id} started test")
    
    # Показываем первый вопрос
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 1"""
    query = update.callback_query
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(STAGE_1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_1_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage1_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    if len(parts) < 3:
        return STAGE_1
    
    current = int(parts[1])
    option_id = parts[2]
    
    question = STAGE_1_QUESTIONS[current]
    selected_option = question["options"].get(option_id)
    
    if not selected_option:
        return STAGE_1
    
    for axis, score in selected_option.get("scores", {}).items():
        context.user_data["scores"][axis] += score
    
    logger.info(f"User {update.effective_user.id}: Stage 1 Q{current} -> {option_id}")
    
    context.user_data["stage1_current"] = current + 1
    return await ask_stage_1_question(update, context)

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАП 1"""
    query = update.callback_query
    scores = context.user_data.get("scores", {})
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    # Переходим сразу к результатам для примера
    profile_data = calculate_profile_final(context.user_data)
    context.user_data["profile_data"] = profile_data
    
    return await show_results_screen(update, context)

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА с кнопкой покупки"""
    query = update.callback_query
    
    has_shared = context.user_data.get("has_shared", False)
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    profile_display = profile_data.get("display_name", "SA_1_DEF")
    
    # Основное сообщение с результатом
    message = (
        f"<b>🎯 ВАШ ПРОФИЛЬ ОПРЕДЕЛЕН!</b>\n\n"
        f"<b>Тип профиля:</b> {profile_display}\n"
        f"<b>Уровень:</b> {profile_data.get('level_name', 'ДЕФИЦИТАРНЫЙ')}\n"
        f"<b>Тип восприятия:</b> {profile_data.get('type_name', 'СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ')}\n\n"
        f"<b>📊 Что дальше?</b>\n\n"
        f"Вы получили базовый анализ вашего профиля. Для получения полного разбора:\n\n"
        f"✅ <b>Полный пакет ВАРИАТИКА включает:</b>\n"
        f"• Детальный разбор профиля (15+ страниц)\n"
        f"• Терапевтическую сказку\n"
        f"• Книгу ВАРИАТИКА (.PDF)\n"
        f"• Персональные рекомендации\n"
        f"• Карту сильных и слабых сторон\n\n"
        f"💎 <b>Стоимость:</b> 690 рублей\n"
        f"🧪 <b>Тестовый платеж:</b> 1 рубль (для проверки системы)\n\n"
        f"<i>После оплаты материалы будут доступны мгновенно!</i>"
    )
    
    # Определяем кнопки
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("📤 Поделиться и получить подарок", callback_data="get_gift")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🎁 Забрать подарок", callback_data="open_gift")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS

# ============================================
# ДОПОЛНИТЕЛЬНЫЕ ЭКРАНЫ
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ИНСТРУКЦИЯ ПО ШАРИНГУ"""
    query = update.callback_query
    await query.answer()
    
    instruction_text = (
        f"<b>📤 ШАГ 1: ПОДЕЛИСЬ ССЫЛКОЙ</b>\n\n"
        f"Нажми кнопку ниже, чтобы отправить сообщение с ссылкой на тест.\n\n"
        f"После того как отправишь, вернись сюда и нажми «✅ Я поделился»"
    )
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Поделиться ссылкой", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился", callback_data="confirm_share")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    return GIFT_SCREEN

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    await query.answer("✅ Спасибо за репост! Ваш подарок готов!")
    
    context.user_data["has_shared"] = True
    
    return await show_results_screen(update, context)

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ОТКРЫТИЕ ПОДАРКА"""
    query = update.callback_query
    await query.answer()
    
    gift_text = (
        f"<b>🎁 ВАШ ПОДАРОК ГОТОВ!</b>\n\n"
        f"📚 Терапевтическая сказка для трансформации структуры восприятия\n\n"
        f"Эта сказка разрешает внутренние противоречия в конфигурации восприятия вашего профиля.\n\n"
        f"💡 <b>Как использовать:</b>\n"
        f"1. Нажми кнопку ниже, чтобы открыть PDF\n"
        f"2. Прочитай\n"
        f"3. Обращай внимание на символы и метафоры\n\n"
        f"Приятного чтения! 📖✨"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Открыть сказку", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(gift_text, reply_markup=reply_markup, parse_mode="HTML")
    return OPEN_GIFT_SCREEN

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Назад' - возвращает к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    return await start_test(update, context)

async def get_materials_after_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов после оплаты"""
    query = update.callback_query
    await query.answer()
    
    # Вызываем команду materials для текущего пользователя
    update.effective_message = query.message
    await materials_command(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

# ============================================
# WEBHOOK ОБРАБОТЧИК (для получения уведомлений от ЮKassa)
# ============================================

async def webhook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик webhook-уведомлений от ЮKassa"""
    try:
        # Здесь будет логика обработки webhook от ЮKassa
        # В реальной реализации нужно получать и проверять уведомления
        
        logger.info("Webhook received from YooKassa")
        
        # После успешной оплаты можно отправить уведомление пользователю
        # или обновить статус в базе данных
        
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА БОТА
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*50)
    print("🚀 ЗАПУСК БОТА ВАРИАТИКА ver 2.0")
    print("="*50)
    print("ИНТЕГРАЦИЯ:")
    print("1. Платежная система ЮKassa")
    print("2. Автоматическая выдача материалов")
    print("3. 36 персонализированных наборов")
    print("="*50)
    
    # Проверка конфигурации
    print("\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ:")
    print(f"• Режим платежей: {check_payment_mode()}")
    print(f"• API URL: {API_URL}")
    print(f"• Bot Token: {'✅ Установлен' if TOKEN else '❌ Отсутствует'}")
    print(f"• YooKassa Shop ID: {'✅ Установлен' if YOOKASSA_SHOP_ID else '❌ Отсутствует'}")
    print(f"• YooKassa Secret Key: {'✅ Установлен' if YOOKASSA_SECRET_KEY else '❌ Отсутствует'}")
    
    if not all([TOKEN, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY]):
        print("\n⚠️  ВНИМАНИЕ: Не все переменные окружения установлены!")
        print("Для работы платежной системы необходимо установить:")
        print("• TELEGRAM_BOT_TOKEN")
        print("• YOOKASSA_SHOP_ID")
        print("• YOOKASSA_SECRET_KEY")
    
    print("\n📁 Карта материалов:")
    print(f"• Всего профилей: {len(YANDEX_DISK_FOLDERS)}")
    print(f"• SA профилей: {len([k for k in YANDEX_DISK_FOLDERS if k.startswith('SA')])}")
    print(f"• SP профилей: {len([k for k in YANDEX_DISK_FOLDERS if k.startswith('SP')])}")
    print(f"• IA профилей: {len([k for k in YANDEX_DISK_FOLDERS if k.startswith('IA')])}")
    print(f"• IP профилей: {len([k for k in YANDEX_DISK_FOLDERS if k.startswith('IP')])}")
    
    print("\n✅ Проверка завершена. Запускаю бота...")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$")
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(buy_variatica_package, pattern="^buy_variatica_package$"),
                CallbackQueryHandler(test_payment, pattern="^test_payment$"),
                CallbackQueryHandler(status_payment, pattern="^status_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$")
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    # Добавляем обработчики команд
    application.add_handler(conv_handler)
    
    # Добавляем команды для материалов и проверки
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("myaccess", myaccess_command))
    application.add_handler(CommandHandler("check", check_command))
    
    # Обработчик для получения материалов после оплаты
    application.add_handler(CallbackQueryHandler(get_materials_after_payment, pattern="^get_materials_after_payment$"))
    
    logger.info("🚀 Bot started: ВАРИАТИКА ver 2.0!")
    logger.info("💰 Интеграция: Платежная система ЮKassa + автоматическая выдача материалов")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
