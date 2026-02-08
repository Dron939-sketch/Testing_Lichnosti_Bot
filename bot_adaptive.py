#!/usr/bin/env python3
"""
Telegram Bot для платежной системы VARIATICA
Версия с защитой от конфликтов (минимальные изменения)
"""

import os
import sys
import time
import json
import base64
import logging
import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ApplicationBuilder
)

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Уменьшаем логирование библиотек
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Ссылка на бота для возврата после оплаты
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"

# ========== ФУНКЦИИ ЗАЩИТЫ ОТ КОНФЛИКТОВ ==========
def clear_telegram_conflicts():
    """Очищает конфликты в Telegram API"""
    try:
        print("🔄 Проверяю конфликты в Telegram API...")
        
        # 1. Удаляем webhook (если есть)
        delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.get(delete_url, timeout=5)
        if response.status_code == 200:
            print("✅ Webhook удален")
        else:
            print(f"ℹ️ Webhook не найден или ошибка: {response.status_code}")
        
        # 2. Очищаем очередь обновлений
        updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1"
        response = requests.get(updates_url, timeout=5)
        if response.status_code == 200:
            print("✅ Очередь обновлений очищена")
        
        # 3. Получаем информацию о боте
        me_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(me_url, timeout=5)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ Бот: @{bot_info['result']['username']}")
            else:
                print(f"⚠️ Проблема с ботом: {bot_info}")
        else:
            print(f"⚠️ Не удалось получить информацию о боте")
        
        print("✅ Конфликты очищены, бот готов к запуску")
        return True
        
    except Exception as e:
        print(f"⚠️ Ошибка при очистке конфликтов: {e}")
        return False

def check_bot_health():
    """Проверяет здоровье системы перед запуском"""
    health_issues = []
    
    # Проверяем токен
    if not TOKEN:
        health_issues.append("❌ Токен бота не установлен")
    else:
        print(f"✅ Токен бота: установлен")
    
    # Проверяем API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API доступен")
        else:
            health_issues.append(f"⚠️ API недоступен: {response.status_code}")
    except:
        health_issues.append("❌ API недоступен (ошибка соединения)")
    
    # Проверяем ЮKassa
    if not YOOKASSA_SHOP_ID:
        health_issues.append("❌ YOOKASSA_SHOP_ID не установлен")
    
    if not YOOKASSA_SECRET_KEY:
        health_issues.append("❌ YOOKASSA_SECRET_KEY не установлен")
    
    if health_issues:
        print("⚠️ Проблемы с конфигурацией:")
        for issue in health_issues:
            print(f"  {issue}")
        return False
    
    return True

# ========== УЛУЧШЕННЫЙ ОБРАБОТЧИК ОШИБОК ==========
async def enhanced_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок с защитой от конфликтов"""
    error_msg = str(context.error)
    
    # Логируем ошибку
    logger.error(f"Ошибка: {error_msg}")
    
    # КОНФЛИКТ БОТОВ - самая важная обработка
    if "Conflict" in error_msg and "getUpdates" in error_msg:
        logger.warning("⚡ ОБНАРУЖЕН КОНФЛИКТ БОТОВ!")
        print("=" * 60)
        print("🔄 АКТИВИРУЮ ЗАЩИТУ ОТ КОНФЛИКТОВ...")
        print("=" * 60)
        
        # 1. Пытаемся очистить конфликт
        clear_telegram_conflicts()
        
        # 2. Ждем 10 секунд
        print("⏳ Жду 10 секунд перед продолжением...")
        await asyncio.sleep(10)
        
        # 3. Пытаемся переподключиться
        print("🔄 Пытаюсь переподключиться...")
        return
    
    # Сетевые ошибки
    elif any(keyword in error_msg for keyword in ["Timeout", "Connection", "Network"]):
        logger.warning(f"Сетевая ошибка: {error_msg}")
        await asyncio.sleep(5)
        return
    
    # Другие ошибки - просто логируем
    else:
        logger.error(f"Ошибка: {error_msg}")

# ========== ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ ==========
# (Я сохраню ВСЕ ваши функции как есть, только добавлю защиту)

def check_configuration():
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    print("=" * 70)
    print("🤖 VARIATICA PAYMENT BOT - ПОЛНАЯ ВЕРСИЯ С МАТЕРИАЛАМИ")
    print("=" * 70)
    
    errors = []
    warnings = []
    
    # Проверка токена
    if not TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установлен")
        print("❌ Токен бота: НЕ УСТАНОВЛЕН!")
    else:
        print(f"✅ Токен бота: установлен")
    
    # Проверка URL API
    if not API_URL:
        errors.append("⚠️ API_URL не установлен, используется по умолчанию")
    print(f"✅ API URL: {API_URL}")
    
    # Проверка доступности API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API доступен: {response.status_code}")
            print(f"📊 Версия API: {data.get('version', 'unknown')}")
            print(f"📊 Статус: {data.get('status', 'unknown')}")
            
            # Проверяем есть ли функция уведомлений
            try:
                check_response = requests.get(f"{API_URL}/check-db", timeout=5)
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    if 'notifications_log' in check_data.get('tables', []):
                        print("✅ Уведомления: настроены")
                    else:
                        warnings.append("⚠️ Таблица уведомлений не создана")
                        print("⚠️ Уведомления: таблица не создана")
            except:
                pass
                
        else:
            warnings.append(f"⚠️ API недоступен: код {response.status_code}")
            print(f"⚠️ API ответ: {response.status_code}")
    except Exception as e:
        errors.append(f"❌ API недоступен: {str(e)}")
        print(f"❌ API недоступен: {e}")
    
    # Проверка ЮKassa
    if not YOOKASSA_SHOP_ID:
        errors.append("❌ YOOKASSA_SHOP_ID не установлен")
        print("❌ Shop ID: НЕ УСТАНОВЛЕН!")
    else:
        print(f"✅ Shop ID: {YOOKASSA_SHOP_ID[:10]}...")
    
    if not YOOKASSA_SECRET_KEY:
        errors.append("❌ YOOKASSA_SECRET_KEY не установлен")
        print("❌ Secret Key: НЕ УСТАНОВЛЕН!")
    else:
        key_type = "ТЕСТОВЫЙ" if YOOKASSA_SECRET_KEY.startswith('test_') else "БОЕВОЙ"
        print(f"✅ Secret Key: {key_type}")
        if key_type == "БОЕВОЙ":
            print("💡 Режим: БОЕВОЙ (требуется receipt)")
        else:
            print("💡 Режим: ТЕСТОВЫЙ (receipt не требуется)")
    
    print("=" * 70)
    
    if errors:
        print("❌ Критические ошибки конфигурации:")
        for error in errors:
            print(f"  {error}")
        return False
    
    if warnings:
        print("⚠️ Предупреждения конфигурации:")
        for warning in warnings:
            print(f"  {warning}")
    
    print("✅ Конфигурация проверена успешно!")
    print("=" * 70)
    print("🚀 Доступные команды:")
    print("  /start - Главное меню")
    print("  /materials - Получить материалы")
    print("  /myaccess - Мои доступы")
    print("  /buy - Купить доступ за 690 руб")
    print("  /check <id> - Проверить статус")
    print("=" * 70)
    return True

def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 1.0, email: str = None, is_test: bool = False) -> dict:
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    try:
        # Basic Auth для ЮKassa API v3
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id
        }
        
        # Формируем email для чека
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Описание в зависимости от типа платежа
        if is_test:
            description = f"Тестовый платеж #{payment_id}"
            item_description = "Тестовый доступ к курсу ВАРИАТИКА"
            return_url = TELEGRAM_BOT_URL
        else:
            description = f"Курс ВАРИАТИКА #{payment_id}"
            item_description = "Полный курс ВАРИАТИКА с материалами"
            return_url = TELEGRAM_BOT_URL
        
        # Базовая структура платежа
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id),
                "is_test": str(is_test)
            }
        }
        
        # Добавляем receipt если режим БОЕВОЙ
        if YOOKASSA_SECRET_KEY.startswith('live_'):
            payload["receipt"] = {
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
                        "vat_code": "1",  # НДС 20% (обязательно для РФ)
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }
                ]
            }
            if is_test:
                logger.info(f"🛡️ Создаю ТЕСТОВЫЙ платеж С receipt (боевой режим): {payment_id}")
            else:
                logger.info(f"🛡️ Создаю БОЕВОЙ платеж С receipt: {payment_id}")
        else:
            if is_test:
                logger.info(f"🧪 Создаю ТЕСТОВЫЙ платеж БЕЗ receipt: {payment_id}")
            else:
                logger.info(f"🧪 Создаю БОЕВОЙ платеж БЕЗ receipt: {payment_id}")
        
        logger.info(f"📤 Отправляю в ЮKassa: {json.dumps(payload, indent=2)[:500]}...")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            yookassa_id = data.get('id')
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if not confirmation_url:
                return {
                    "success": False,
                    "error": "No confirmation URL in response",
                    "details": json.dumps(data)[:200]
                }
            
            # Сохраняем ID ЮKassa в базе
            try:
                save_response = requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={
                        "payment_id": payment_id,
                        "yookassa_id": yookassa_id,
                        "status": "waiting"
                    },
                    timeout=10
                )
                
                if save_response.status_code == 200:
                    logger.info(f"✅ ID сохранен в БД: {yookassa_id}")
                else:
                    logger.error(f"⚠️ Ошибка сохранения ID: {save_response.status_code} - {save_response.text}")
                    
            except Exception as e:
                logger.error(f"⚠️ Ошибка сохранения ID: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": yookassa_id,
                "confirmation_url": confirmation_url,
                "status": data.get('status'),
                "amount": amount,
                "description": description
            }
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            
            return {
                "success": False,
                "error": f"Ошибка {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }

def create_payment_in_db(user_id: int, amount: float = 1.0, is_test: bool = False) -> dict:
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    try:
        timestamp = int(time.time())
        if is_test:
            payment_id = f"test_{user_id}_{timestamp}"
            description = f"Тестовый платеж {amount} руб"
        else:
            payment_id = f"prod_{user_id}_{timestamp}"
            description = "Полный курс ВАРИАТИКА - 690 руб"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": description
        }
        
        logger.info(f"📦 Создаю платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Платеж создан в БД: {payment_id}")
            return {
                "success": True,
                "payment_id": payment_id,
                "email": f"user_{user_id}@telegram.org",
                "amount": amount,
                "description": description
            }
        else:
            error_text = response.text[:200]
            logger.error(f"❌ Ошибка БД {response.status_code}: {error_text}")
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Получаем статус из правильного места
            if 'payment' in data:
                status = data['payment'].get('status', 'unknown')
                amount = data['payment'].get('amount', 0)
                user_id = data['payment'].get('user_id')
            else:
                status = data.get('status', 'unknown')
                amount = 0
                user_id = None
                
            return {
                "success": True,
                "status": status,
                "amount": amount,
                "user_id": user_id,
                "data": data
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": "Платеж не найден"
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка: {response.status_code}",
                "details": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_user_access(user_id: int) -> dict:
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
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
                "error": f"Ошибка API: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_materials_link(user_id: int, payment_id: str, token: str = None) -> dict:
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
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
                "error": f"Ошибка API: {response.status_code}",
                "details": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_690")],
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА (1 руб)", callback_data="test_buy")],
        [InlineKeyboardButton("📁 МОИ МАТЕРИАЛЫ", callback_data="my_materials")],
        [InlineKeyboardButton("🔍 ПРОВЕРИТЬ СТАТУС", callback_data="check_status_menu")]
    ]
    
    mode = "БОЕВОЙ" if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_') else "ТЕСТОВЫЙ"
    
    message_text = (
        f"🚀 *Добро пожаловать в VARIATICA!*\n\n"
        f"👋 *{user.first_name}*, выберите действие:\n\n"
        
        f"💎 *Полный курс:* 690 руб\n"
        f"• Полный доступ к материалам\n"
        f"• Мгновенная выдача после оплаты\n"
        f"• Техническая поддержка\n\n"
        
        f"🧪 *Тестовая оплата:* 1 руб\n"
        f"• Проверка платежной системы\n"
        f"• Тестовые материалы\n\n"
        
        f"⚙️ *Системная информация:*\n"
        f"• Режим: {mode}\n"
        f"• API: `{API_URL}`\n"
        f"• Бот: {TELEGRAM_BOT_URL}"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    await start(update, context)

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Проверяем доступ пользователя
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n\n"
            "Пожалуйста, попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    if not access_data.get('has_access', False):
        # Нет доступа - показываем кнопку покупки
        keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_690")]]
        
        await update.message.reply_text(
            f"📭 *У вас нет доступа к материалам*\n\n"
            f"👤 *{user_name}*, для получения доступа необходимо приобрести курс.\n\n"
            f"💎 *Полный курс ВАРИАТИКА:*\n"
            f"• Стоимость: 690 руб\n"
            f"• Мгновенный доступ после оплаты\n"
            f"• Все материалы курса\n\n"
            f"Нажмите кнопку ниже для покупки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Есть доступ - показываем материалы
    accesses = access_data.get('accesses', [])
    
    if not accesses:
        await update.message.reply_text(
            "❌ *Доступ не найден*\n\n"
            "Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    # Берем последний активный доступ
    for access in accesses:
        if access.get('has_access', False) and access.get('is_active', False):
            payment_id = access.get('payment_id')
            access_token = access.get('access_token')
            
            # Получаем ссылку на материалы
            materials_data = get_materials_link(user_id, payment_id, access_token)
            
            if materials_data.get('success', False):
                materials_link = materials_data.get('materials_link')
                
                keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
                
                await update.message.reply_text(
                    f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                    f"👤 *{user_name}*, вот ваши материалы курса ВАРИАТИКА:\n\n"
                    f"📋 *ID заказа:* `{payment_id[:8]}`\n"
                    f"💰 *Сумма:* {access.get('amount', 0)} руб\n"
                    f"📅 *Доступ открыт:* {access.get('granted_at', '')[:10]}\n"
                    f"⏳ *Действует до:* {access.get('expires_at', '')[:10]}\n\n"
                    f"🔗 *Ссылка на Яндекс.Диск:*\n"
                    f"Нажмите кнопку ниже для скачивания:",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
                return
            else:
                error = materials_data.get('error', 'Неизвестная ошибка')
                await update.message.reply_text(
                    f"❌ *Ошибка получения материалов*\n\n"
                    f"`{error}`\n\n"
                    f"Пожалуйста, обратитесь в поддержку.",
                    parse_mode='Markdown'
                )
                return
    
    # Если нет активных доступов
    keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_690")]]
    
    await update.message.reply_text(
        f"📭 *Доступ не активен*\n\n"
        f"👤 *{user_name}*, ваш доступ истек или не активен.\n\n"
        f"Для получения доступа приобретите курс:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def myaccess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Проверяем доступ пользователя
    access_data = get_user_access(user_id)
    
    if not access_data.get('success', False):
        await update.message.reply_text(
            "❌ *Ошибка проверки доступа*\n\n"
            "Пожалуйста, попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    has_access = access_data.get('has_access', False)
    accesses = access_data.get('accesses', [])
    
    if not accesses:
        message = (
            f"📭 *НЕТ АКТИВНЫХ ДОСТУПОВ*\n\n"
            f"👤 *{user_name}*, у вас нет активных подписок.\n\n"
            f"💎 *Доступные варианты:*\n"
            f"• Полный курс ВАРИАТИКА - 690 руб\n"
            f"• Мгновенный доступ после оплаты\n\n"
            f"Используйте команду /buy для покупки"
        )
    else:
        active_count = sum(1 for a in accesses if a.get('has_access', False) and a.get('is_active', False))
        total_count = len(accesses)
        
        message = (
            f"📊 *ВАШИ ДОСТУПЫ*\n\n"
            f"👤 *Пользователь:* {user_name}\n"
            f"🔓 *Активных доступов:* {active_count}/{total_count}\n\n"
        )
        
        for i, access in enumerate(accesses[:5], 1):  # Показываем первые 5
            status = "✅ АКТИВЕН" if access.get('has_access', False) and access.get('is_active', False) else "❌ НЕ АКТИВЕН"
            expires = access.get('expires_at', '')[:10] if access.get('expires_at') else "не указан"
            
            message += (
                f"{i}. *{access.get('description', 'Доступ')}*\n"
                f"   💰 Сумма: {access.get('amount', 0)} руб\n"
                f"   📋 ID: `{access.get('payment_id', '')[:8]}`\n"
                f"   📅 Доступ: {access.get('granted_at', '')[:10]}\n"
                f"   ⏳ Истекает: {expires}\n"
                f"   🔐 Статус: {status}\n\n"
            )
        
        if active_count > 0:
            message += "📁 Для получения материалов используйте /materials"
        else:
            message += "💎 Для покупки доступа используйте /buy"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    if not context.args:
        keyboard = [[InlineKeyboardButton("🔍 Проверить статус", callback_data="check_status_menu")]]
        
        await update.message.reply_text(
            "🔍 *Проверка статуса платежа*\n\n"
            "Использование: `/check ID_платежа`\n\n"
            "Пример:\n"
            "`/check test_532205848_1234567890`\n\n"
            "Или используйте кнопку ниже:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    payment_id = context.args[0]
    result = check_payment_status_db(payment_id)
    
    if result["success"]:
        status = result.get("status", "unknown")
        amount = result.get("amount", 0)
        user_id = result.get("user_id")
        
        status_emoji = {
            "succeeded": "✅",
            "pending": "⏳",
            "waiting": "⏳",
            "canceled": "❌",
            "failed": "❌"
        }.get(status, "📊")
        
        status_text = {
            "succeeded": "ОПЛАЧЕНО",
            "pending": "ОЖИДАЕТ ОПЛАТЫ",
            "waiting": "ОЖИДАЕТ ПОДТВЕРЖДЕНИЯ",
            "canceled": "ОТМЕНЕН",
            "failed": "ОШИБКА"
        }.get(status, status.upper())
        
        message = (
            f"{status_emoji} *СТАТУС ПЛАТЕЖА*\n\n"
            f"📋 *ID:* `{payment_id}`\n"
            f"💰 *Сумма:* {amount} руб\n"
            f"📊 *Статус:* {status_text}\n"
        )
        
        if status == "succeeded":
            message += "\n🎉 *Платеж успешно завершен!*\n\n"
            message += "📁 Для получения материалов используйте команду:\n`/materials`\n\n"
            message += "✅ Вы получите мгновенное уведомление с доступом."
        elif status in ["pending", "waiting"]:
            keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", callback_data=f"retry_{payment_id}")]]
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await update.message.reply_text(
            f"❌ *Не удалось проверить платеж* `{payment_id}`:\n\n"
            f"`{error_msg}`\n\n"
            f"Проверьте правильность ID платежа.",
            parse_mode='Markdown'
        )

async def test_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Шаг 1: Создаем в БД
    await query.edit_message_text("📦 *Шаг 1/3: Создаю платеж в базе данных...*", parse_mode='Markdown')
    
    db_result = create_payment_in_db(user_id, amount=1.0, is_test=True)
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка базы данных:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    email = db_result.get("email", f"user_{user_id}@telegram.org")
    
    # Шаг 2: Создаем в ЮKassa
    await query.edit_message_text("💳 *Шаг 2/3: Создаю платеж в ЮKassa...*", parse_mode='Markdown')
    
    payment_result = create_yookassa_payment(payment_id, user_id, amount=1.0, email=email, is_test=True)
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        details = payment_result.get('details', '')
        
        error_text = f"❌ *Ошибка ЮKassa:*\n`{error_msg}`"
        
        if "Receipt is missing" in details or "Квитанция отсутствует" in details:
            error_text += "\n\n💡 *Решение:* Включите тестовый режим в настройках."
        
        await query.edit_message_text(error_text, parse_mode='Markdown')
        return
    
    # Шаг 3: Показываем ссылку
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    mode_info = ""
    if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_'):
        safe_email = email.replace('_', r'\_').replace('@', r'\@')
        mode_info = f"📧 *Email для чека:* {safe_email}\n🛡️ *Режим:* Боевой (чек по 54-ФЗ)"
    else:
        mode_info = "🧪 *Режим:* Тестовый"
    
    message_text = (
        f"✅ *ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID:* `{payment_id}`\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"{mode_info}\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты вы получите мгновенное уведомление."
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def buy_690_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Шаг 1: Создаем в БД
    await query.edit_message_text("📦 *Шаг 1/3: Создаю заказ на полный курс...*", parse_mode='Markdown')
    
    db_result = create_payment_in_db(user_id, amount=690.0, is_test=False)
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        await query.edit_message_text(f"❌ *Ошибка базы данных:*\n`{error_msg}`", parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    email = db_result.get("email", f"user_{user_id}@telegram.org")
    
    # Шаг 2: Создаем в ЮKassa
    await query.edit_message_text("💳 *Шаг 2/3: Создаю платеж в ЮKassa...*", parse_mode='Markdown')
    
    payment_result = create_yookassa_payment(payment_id, user_id, amount=690.0, email=email, is_test=False)
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        
        error_text = f"❌ *Ошибка ЮKassa:*\n`{error_msg}`"
        
        await query.edit_message_text(error_text, parse_mode='Markdown')
        return
    
    # Шаг 3: Показываем ссылку
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    mode_info = "💎 *КУРС ВАРИАТИКА - ПОЛНЫЙ ДОСТУП*"
    
    message_text = (
        f"✅ *ЗАКАЗ СОЗДАН!*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 руб\n"
        f"📚 *Продукт:* Полный курс ВАРИАТИКА\n"
        f"{mode_info}\n\n"
        f"*Что вы получите после оплаты:*\n"
        f"✅ Полный доступ ко всем материалам\n"
        f"✅ Мгновенное уведомление в Telegram\n"
        f"✅ Защищенную ссылку на Яндекс.Диск\n"
        f"✅ Техническую поддержку\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты вы получите доступ к материалам."
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 *Проверяю статус:*\n`{payment_id}`", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка:* {error_msg}", parse_mode='Markdown')
            return
        
        status = result.get("status", "unknown")
        amount = result.get("amount", 0)
        
        if status == "succeeded":
            is_test = payment_id.startswith("test_")
            
            if is_test:
                message = (
                    f"🎉 *ТЕСТОВЫЙ ПЛАТЕЖ ОПЛАЧЕН!*\n\n"
                    f"✅ Платеж `{payment_id}` успешно завершен!\n"
                    f"💰 Сумма: {amount} руб\n\n"
                    f"*🔓 СИСТЕМА РАБОТАЕТ КОРРЕКТНО!*\n"
                    f"Вы получите тестовые материалы.\n\n"
                    f"Для полного курса используйте /buy"
                )
            else:
                message = (
                    f"🎉 *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
                    f"✅ Ваш заказ `{payment_id}` успешно оплачен!\n"
                    f"💰 Сумма: {amount} руб\n\n"
                    f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                    f"Вы получили доступ ко всем материалам курса ВАРИАТИКА!\n\n"
                    f"📁 Для получения материалов нажмите:\n"
                    f"`/materials`\n\n"
                    f"✅ Вы получите мгновенное уведомление с ссылкой."
                )
                
                # Также проверяем доступ
                user_id = result.get("user_id", query.from_user.id)
                access_data = get_user_access(user_id)
                if access_data.get('has_access', False):
                    accesses = access_data.get('accesses', [])
                    for access in accesses:
                        if access.get('payment_id') == payment_id and access.get('access_token'):
                            keyboard = [[InlineKeyboardButton("📁 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data=f"get_materials_{payment_id}")]]
                            await query.edit_message_text(
                                message,
                                reply_markup=InlineKeyboardMarkup(keyboard),
                                parse_mode='Markdown'
                            )
                            return
            
        elif status in ["pending", "waiting"]:
            message = (
                f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
                f"Заказ `{payment_id}` еще не оплачен.\n"
                f"💰 Сумма: {amount} руб\n\n"
                f"*Для оплаты используйте кнопку ниже:*"
            )
            keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", callback_data=f"retry_{payment_id}")]]
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            message = f"📊 *Статус заказа:* `{status}`\n💰 *Сумма:* {amount} руб"
        
        await query.edit_message_text(message, parse_mode='Markdown')

async def get_materials_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_materials_"):
        payment_id = query.data[14:]
        user_id = query.from_user.id
        
        # Получаем доступы пользователя
        access_data = get_user_access(user_id)
        
        if not access_data.get('success', False):
            await query.edit_message_text(
                "❌ *Ошибка проверки доступа*",
                parse_mode='Markdown'
            )
            return
        
        # Ищем нужный доступ
        access_token = None
        for access in access_data.get('accesses', []):
            if access.get('payment_id') == payment_id and access.get('has_access', False):
                access_token = access.get('access_token')
                break
        
        if not access_token:
            await query.edit_message_text(
                f"❌ *Доступ не найден*\n\n"
                f"Платеж `{payment_id}` не найден или доступ не активен.",
                parse_mode='Markdown'
            )
            return
        
        # Получаем ссылку на материалы
        await query.edit_message_text("📁 *Получаю ссылку на материалы...*", parse_mode='Markdown')
        
        materials_data = get_materials_link(user_id, payment_id, access_token)
        
        if materials_data.get('success', False):
            materials_link = materials_data.get('materials_link')
            
            keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)]]
            
            await query.edit_message_text(
                f"✅ *МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                f"📋 *ID заказа:* `{payment_id[:8]}`\n"
                f"🔗 *Ссылка на Яндекс.Диск:*\n\n"
                f"Нажмите кнопку ниже для скачивания материалов:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
        else:
            error = materials_data.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(
                f"❌ *Ошибка получения материалов*\n\n"
                f"`{error}`\n\n"
                f"Попробуйте использовать команду /materials",
                parse_mode='Markdown'
            )

async def my_materials_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    # Просто вызываем команду материалов
    fake_update = Update(update.update_id + 1, message=query.message)
    await materials_command(fake_update, context)

async def check_status_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 *Проверка статуса*\n\n"
        "Используйте команду:\n"
        "`/check ID_платежа`\n\n"
        "Или выберите действие:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧪 Новый тестовый платеж", callback_data="test_buy")],
            [InlineKeyboardButton("💎 Полный курс (690 руб)", callback_data="buy_690")],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ])
    )

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    # Создаем fake update для вызова start
    fake_update = Update(update.update_id + 1, message=query.message)
    await start(fake_update, context)

async def retry_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("retry_"):
        payment_id = query.data[6:]
        
        # Получаем информацию о платеже
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text(
                f"❌ *Не удалось найти платеж* `{payment_id}`",
                parse_mode='Markdown'
            )
            return
        
        amount = result.get("amount", 1.0)
        user_id = result.get("user_id", query.from_user.id)
        
        # Определяем тип платежа
        is_test = amount == 1.0
        
        # Пытаемся создать новую ссылку
        email = f"user_{user_id}@telegram.org"
        payment_result = create_yookassa_payment(payment_id, user_id, amount, email, is_test)
        
        if payment_result.get("success", False):
            keyboard = [[InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=payment_result["confirmation_url"])]]
            
            amount_text = "1 рубль" if is_test else "690 руб"
            
            await query.edit_message_text(
                f"🔗 *НОВАЯ ССЫЛКА ДЛЯ ОПЛАТЫ*\n\n"
                f"📋 *ID:* `{payment_id}`\n"
                f"💰 *Сумма:* {amount_text}\n\n"
                f"Нажмите кнопку ниже для оплаты:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
        else:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(
                f"❌ *Не удалось создать ссылку оплаты*\n\n"
                f"`{error_msg}`\n\n"
                f"Попробуйте создать новый платеж.",
                parse_mode='Markdown'
            )

# ========== ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА С ЗАЩИТОЙ ==========
def main():
    """Основная функция запуска с защитой от конфликтов"""
    print("=" * 80)
    print("🚀 VARIATICA PAYMENT BOT - ЗАЩИЩЕННАЯ ВЕРСИЯ")
    print("=" * 80)
    
    # 1. Проверяем конфигурацию (ВАША функция)
    if not check_configuration():
        print("❌ Конфигурация неполная, выход...")
        sys.exit(1)
    
    # 2. Очищаем возможные конфликты перед запуском
    print("\n🛡️ Проверяю и очищаю возможные конфликты...")
    clear_telegram_conflicts()
    
    # 3. Ждем немного перед запуском
    print("⏳ Жду 3 секунды перед запуском...")
    time.sleep(3)
    
    try:
        # 4. Создаем приложение
        app = ApplicationBuilder().token(TOKEN).build()
        
        # 5. Добавляем обработчики команд (ВАШИ функции)
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("buy", buy_command))
        app.add_handler(CommandHandler("materials", materials_command))
        app.add_handler(CommandHandler("myaccess", myaccess_command))
        app.add_handler(CommandHandler("check", check_command))
        
        # Callback обработчики (ВАШИ функции)
        app.add_handler(CallbackQueryHandler(test_buy_callback, pattern="^test_buy$"))
        app.add_handler(CallbackQueryHandler(buy_690_callback, pattern="^buy_690$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(get_materials_callback, pattern="^get_materials_"))
        app.add_handler(CallbackQueryHandler(my_materials_callback, pattern="^my_materials$"))
        app.add_handler(CallbackQueryHandler(check_status_menu_callback, pattern="^check_status_menu$"))
        app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
        app.add_handler(CallbackQueryHandler(retry_payment_callback, pattern="^retry_"))
        
        # 6. Добавляем улучшенный обработчик ошибок
        app.add_error_handler(enhanced_error_handler)
        
        print("✅ Бот запущен успешно!")
        print(f"📡 API: {API_URL}")
        print(f"🤖 Бот: {TELEGRAM_BOT_URL}")
        
        # Информация о режиме
        if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_'):
            print(f"🛡️ Режим: БОЕВОЙ")
            print(f"💡 Используется чек по 54-ФЗ")
        else:
            print(f"🧪 Режим: ТЕСТОВЫЙ")
        
        print(f"⏰ Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("📱 Используйте команду /start в Telegram")
        print("💎 Полный курс: 690 руб")
        print("🧪 Тестовый платеж: 1 руб")
        print("📁 Материалы: мгновенная выдача после оплаты")
        print("=" * 80)
        print("🛡️ РЕЖИМ: ЗАЩИТА ОТ КОНФЛИКТОВ ВКЛЮЧЕНА")
        print("=" * 80)
        
        # 7. Запускаем с максимальной защитой
        app.run_polling(
            drop_pending_updates=True,      # Удаляем ожидающие обновления
            allowed_updates=['message', 'callback_query'],
            poll_interval=1.0,              # Интервал опроса
            timeout=30,                     # Таймаут
            bootstrap_retries=3,            # Попытки переподключения
            retry_interval=2,               # Интервал между ретраями
            close_loop=False,               # Не закрывать loop при ошибке
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        
        # Автовосстановление при критической ошибке
        print(f"🔄 Автовосстановление через 10 секунд...")
        time.sleep(10)
        
        # Перезапускаем процесс
        os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    main()
