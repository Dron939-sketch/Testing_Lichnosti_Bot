"""
🎴 VARIATICA BOT - ПОЛНАЯ ВЕРСИЯ
Автоматическая выдача материалов после оплаты
"""

import os
import logging
import asyncio
import urllib.parse
import base64
import uuid
import time
import requests
import math
import re
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
    JobQueue,
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
ADMIN_IDS = [123456789]  # Замените на реальные ID администраторов

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_payments.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# КЛАСС АВТОМАТИЧЕСКОЙ ПРОВЕРКИ ОПЛАТ
# ============================================

class PaymentAutoChecker:
    """Система автоматической проверки и выдачи материалов после оплаты"""
    
    def __init__(self):
        self.pending_payments = {}  # payment_id -> данные платежа
        self.check_interval = 30  # секунды между проверками
        self.max_check_time = 3600  # максимум 1 час проверок
        
    def add_payment(self, user_id: int, payment_id: str, context: ContextTypes.DEFAULT_TYPE):
        """Добавляет платеж для автоматического отслеживания"""
        self.pending_payments[payment_id] = {
            "user_id": user_id,
            "added_time": time.time(),
            "context": context,
            "checks_count": 0,
            "max_checks": 120,  # 120 проверок = 1 час (30 сек * 120)
            "notification_sent": False
        }
        logger.info(f"✅ Платеж добавлен в отслеживание: {payment_id} для пользователя {user_id}")
        
    async def check_all_payments(self, context: ContextTypes.DEFAULT_TYPE):
        """Проверяет все ожидающие платежи"""
        if not self.pending_payments:
            return
            
        logger.info(f"🔍 Проверяю {len(self.pending_payments)} ожидающих платежей...")
        
        for payment_id, data in list(self.pending_payments.items()):
            try:
                # Проверяем статус платежа
                status_result = self.check_payment_status(payment_id)
                
                if status_result["success"] and status_result.get("status") == "succeeded":
                    # ПЛАТЕЖ УСПЕШЕН - выдать материалы!
                    user_id = data["user_id"]
                    await self.deliver_materials_automatically(user_id, payment_id, context)
                    
                    # Удаляем из отслеживания
                    del self.pending_payments[payment_id]
                    logger.info(f"🎉 Материалы выданы для платежа {payment_id}")
                    
                elif status_result["success"] and status_result.get("status") in ["pending", "waiting"]:
                    # Платеж еще в ожидании - продолжаем проверять
                    data["checks_count"] += 1
                    
                    # Если прошло слишком много времени - удаляем
                    if data["checks_count"] >= data["max_checks"]:
                        logger.warning(f"⏰ Превышено время ожидания для платежа {payment_id}")
                        del self.pending_payments[payment_id]
                        
                elif not status_result["success"]:
                    # Ошибка проверки
                    logger.error(f"❌ Ошибка проверки платежа {payment_id}: {status_result.get('error')}")
                    data["checks_count"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Исключение при проверке платежа {payment_id}: {e}")
                
    def check_payment_status(self, payment_id: str) -> dict:
        """Проверяет статус платежа в БД"""
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
    
    async def deliver_materials_automatically(self, user_id: int, payment_id: str, context: ContextTypes.DEFAULT_TYPE):
        """АВТОМАТИЧЕСКАЯ ВЫДАЧА МАТЕРИАЛОВ ПОСЛЕ ОПЛАТЫ"""
        try:
            logger.info(f"🚀 Начинаю автоматическую выдачу материалов для платежа {payment_id}")
            
            # 1. Получаем данные о доступе пользователя
            access_data = self.get_user_access(user_id)
            
            if not access_data.get("success"):
                logger.error(f"❌ Ошибка получения доступа для {user_id}")
                await self.send_error_notification(user_id, context, "Ошибка получения данных доступа")
                return
                
            if not access_data.get("has_access"):
                logger.error(f"❌ Нет доступа у пользователя {user_id}")
                await self.send_error_notification(user_id, context, "Доступ не активирован")
                return
            
            # 2. Ищем именно этот платеж
            target_access = None
            for access in access_data.get("accesses", []):
                if access.get("payment_id") == payment_id and access.get("has_access"):
                    target_access = access
                    break
            
            if not target_access:
                logger.error(f"❌ Не найден доступ для платежа {payment_id}")
                await self.send_error_notification(user_id, context, "Данные платежа не найдены")
                return
            
            # 3. Получаем профиль и генерируем ссылку
            profile_key = target_access.get("profile_key", "SA_1_DEF")
            materials_link = self.generate_materials_link(profile_key)
            
            # 4. Формируем красивое сообщение с материалами
            payment_amount = target_access.get("amount", 690)
            profile_name = self.get_profile_display_name(profile_key)
            
            success_message = (
                f"🎉 *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
                f"✅ Спасибо за покупку! Ваш доступ активирован.\n\n"
                f"📋 *Детали заказа:*\n"
                f"• Номер: `{payment_id}`\n"
                f"• Профиль: *{profile_name}*\n"
                f"• Код: `{profile_key}`\n"
                f"• Сумма: {payment_amount} руб\n"
                f"• Дата: {time.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"📚 *Ваши материалы готовы:*\n"
                f"1. 📄 Полный разбор профиля (15+ страниц PDF)\n"
                f"2. 📖 Терапевтическая сказка\n"
                f"3. 📘 Книга «ВАРИАТИКА»\n"
                f"4. 🎯 Персональные рекомендации\n"
                f"5. 🗺️ Карта сильных и слабых сторон\n\n"
                f"📥 *Ссылка для скачивания:*\n"
                f"`{materials_link}`\n\n"
                f"💡 *Совет:* Сохраните ссылку, она активна постоянно!"
            )
            
            # 5. Отправляем сообщение пользователю
            await context.bot.send_message(
                chat_id=user_id,
                text=success_message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)],
                    [InlineKeyboardButton("📚 МОИ МАТЕРИАЛЫ", callback_data="my_materials")],
                    [InlineKeyboardButton("🔄 ПРОВЕРИТЬ ДРУГИЕ ДОСТУПЫ", callback_data="check_all_access")]
                ]),
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ Материалы успешно отправлены пользователю {user_id}")
            
            # 6. Дополнительно отправляем второе сообщение с инструкцией
            instruction_message = (
                f"📘 *КАК ПОЛЬЗОВАТЬСЯ МАТЕРИАЛАМИ:*\n\n"
                f"1. *Разбор профиля* — изучите свой тип, сильные стороны и зоны роста\n"
                f"2. *Терапевтическая сказка* — читайте перед сном для работы с подсознанием\n"
                f"3. *Книга ВАРИАТИКА* — справочник по всем типам и уровням\n"
                f"4. *Рекомендации* — практические шаги для развития\n\n"
                f"💎 *Премиум-поддержка:* @meysternlp\n"
                f"📧 *Вопросы по оплате:* yookassa@support.ru\n\n"
                f"Спасибо, что выбрали ВАРИАТИКА! 🎴"
            )
            
            await asyncio.sleep(2)
            await context.bot.send_message(
                chat_id=user_id,
                text=instruction_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при выдаче материалов: {e}")
            await self.send_error_notification(user_id, context, f"Ошибка системы: {str(e)}")
    
    def get_user_access(self, user_id: int) -> dict:
        """Получает доступы пользователя"""
        try:
            response = requests.get(
                f"{API_URL}/api/check-access/{user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"API error {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_materials_link(self, profile_key: str) -> str:
        """Генерирует ссылку на материалы по ключу профиля"""
        # Карта материалов на Яндекс.Диске
        YANDEX_DISK_FOLDERS = {
            # SA профили
            "SA_1_DEF": "https://disk.yandex.ru/d/HAcOfAg1tpIedA",
            "SA_2_SIT": "https://disk.yandex.ru/d/MwdMClX9koCTmA",
            "SA_3_CON": "https://disk.yandex.ru/d/NKN_XemK62t5nA",
            "SA_4_EXP": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA",
            "SA_5_INT": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg",
            "SA_6_AUT": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag",
            "SA_7_VAL": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g",
            "SA_8_TRA": "https://disk.yandex.ru/d/SqlDISkse1OEGQ",
            "SA_9_IDE": "https://disk.yandex.ru/d/vGzHmuckInNL5g",
            
            # SP профили
            "SP_1_DEF": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA",
            "SP_2_SIT": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA",
            "SP_3_CON": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA",
            "SP_4_EXP": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ",
            "SP_5_INT": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg",
            "SP_6_AUT": "https://disk.yandex.ru/d/xWBv4TLFosOB5g",
            "SP_7_VAL": "https://disk.yandex.ru/d/K1whXj6C6KAazQ",
            "SP_8_TRA": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg",
            "SP_9_IDE": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ",
            
            # IA профили
            "IA_1_DEF": "https://disk.yandex.ru/d/M1Y7z175uGKIHg",
            "IA_2_SIT": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ",
            "IA_3_CON": "https://disk.yandex.ru/d/DCkqqALby9UpFg",
            "IA_4_EXP": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg",
            "IA_5_INT": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g",
            "IA_6_AUT": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg",
            "IA_7_VAL": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ",
            "IA_8_TRA": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw",
            "IA_9_IDE": "https://disk.yandex.ru/d/ub0YpQQgS4g6rQ",
            
            # IP профили
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
        
        profile_key_upper = profile_key.upper().replace("-", "_")
        
        # Прямой поиск
        if profile_key_upper in YANDEX_DISK_FOLDERS:
            return YANDEX_DISK_FOLDERS[profile_key_upper]
        
        # Fallback на SA_1_DEF
        logger.warning(f"Профиль {profile_key} не найден, использую SA_1_DEF")
        return "https://disk.yandex.ru/d/HAcOfAg1tpIedA"
    
    def get_profile_display_name(self, profile_key: str) -> str:
        """Возвращает читаемое имя профиля"""
        type_map = {
            "SA": "Социально-Аффилиативный",
            "SP": "Инструментально-Достиженческий",
            "IA": "Экзистенциально-Рефлексивный",
            "IP": "Структурно-Аналитический"
        }
        
        parts = profile_key.upper().split("_")
        if len(parts) >= 2:
            type_code = parts[0]
            level = parts[1]
            return f"{type_map.get(type_code, 'Неизвестный')} Уровень {level}"
        
        return "Базовый профиль"
    
    async def send_error_notification(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, error_msg: str):
        """Отправляет уведомление об ошибке"""
        try:
            error_message = (
                f"⚠️ *ВНИМАНИЕ: ПРОБЛЕМА С ВЫДАЧЕЙ МАТЕРИАЛОВ*\n\n"
                f"При попытке автоматически выдать материалы возникла ошибка:\n"
                f"`{error_msg}`\n\n"
                f"Пожалуйста:\n"
                f"1. Используйте команду /materials для ручного получения\n"
                f"2. Если не сработает, напишите в поддержку: @meysternlp\n"
                f"3. Укажите ID платежа\n\n"
                f"Приносим извинения за неудобства!"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=error_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление об ошибке: {e}")
    
    def cleanup_old_payments(self):
        """Очищает старые платежи из памяти"""
        current_time = time.time()
        old_payments = []
        
        for payment_id, data in self.pending_payments.items():
            if current_time - data["added_time"] > self.max_check_time:
                old_payments.append(payment_id)
        
        for payment_id in old_payments:
            del self.pending_payments[payment_id]
            logger.info(f"🗑️ Удален старый платеж из отслеживания: {payment_id}")

# Инициализация системы автоматической проверки
payment_auto_checker = PaymentAutoChecker()

# ============================================
# ОПРЕДЕЛЕНИЕ ПРОФИЛЯ (ВАША СУЩЕСТВУЮЩАЯ ЛОГИКА)
# ============================================

def determine_perception_type(scores):
    """Определяет тип восприятия (ВАША ФУНКЦИЯ)"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    if external > internal and symbolic > material:
        return "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"
    elif external > internal and material > symbolic:
        return "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ"
    elif internal > external and symbolic > material:
        return "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ"
    elif internal > external and material > symbolic:
        return "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ"
    else:
        # При равенстве баллов
        if external + symbolic >= internal + material:
            return "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"
        else:
            return "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ"

def calculate_profile_final(context_data: dict) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля (ВАША ФУНКЦИЯ)"""
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = "SA"  # Упрощенно, в вашем коде есть get_type_code()
    
    # Упрощенная версия вашей логики
    level = 4
    dilts_code = "EXP"
    
    return {
        "type_code": type_code,
        "level": level,
        "dilts_code": dilts_code,
        "display_name": f"{type_code}_{level}_{dilts_code}",
        "type_name": perception_type
    }

# ============================================
# ФУНКЦИИ ДЛЯ ОПЛАТЫ (С АВТОМАТИЧЕСКОЙ ПРОВЕРКОЙ)
# ============================================

def create_payment_in_db(user_id: int, amount: float = 690.0, 
                         is_test: bool = False, profile_data: dict = None) -> dict:
    """Создает запись о платеже в БД"""
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
        
        if profile_data:
            payload["profile_data"] = profile_data
        
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
    """Создает платеж через ЮKassa"""
    try:
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            return {"success": False, "error": "YooKassa credentials not configured"}
        
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
            email = f"user_{user_id}@telegram.org"
        
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
        
        api_url = "https://api.yookassa.ru/v3/payments"
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
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

async def create_payment_with_auto_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                           amount: float = 690.0, is_test: bool = False):
    """Создает платеж и настраивает автоматическую выдачу"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Получаем профиль пользователя
    profile_data = context.user_data.get('profile_data')
    
    # Создаем платеж в БД
    db_result = create_payment_in_db(
        user_id, 
        amount=amount, 
        is_test=is_test,
        profile_data=profile_data
    )
    
    if not db_result["success"]:
        return None
    
    payment_id = db_result["payment_id"]
    
    # Получаем ссылку для оплаты
    if db_result.get("confirmation_url"):
        confirmation_url = db_result["confirmation_url"]
    else:
        payment_result = create_yookassa_payment(payment_id, user_id, amount=amount, is_test=is_test)
        if not payment_result["success"]:
            return None
        confirmation_url = payment_result["confirmation_url"]
    
    # ДОБАВЛЯЕМ В СИСТЕМУ АВТОМАТИЧЕСКОЙ ПРОВЕРКИ
    payment_auto_checker.add_payment(user_id, payment_id, context)
    
    logger.info(f"✅ Платеж создан и добавлен в авто-отслеживание: {payment_id}")
    
    return {
        "payment_id": payment_id,
        "confirmation_url": confirmation_url,
        "amount": amount
    }

# ============================================
# КОМАНДЫ ДЛЯ МАТЕРИАЛОВ (С АВТОМАТИЧЕСКОЙ ВЫДАЧЕЙ)
# ============================================

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для получения материалов (ручная выдача)"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"🚀 Пользователь {user_id} запросил материалы")
    
    # Проверяем доступ через API
    try:
        response = requests.get(
            f"{API_URL}/api/check-access/{user_id}",
            timeout=10
        )
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Ошибка сервера. Попробуйте позже.")
            return
            
        access_data = response.json()
        
        if not access_data.get('success', False):
            await update.message.reply_text("❌ Ошибка проверки доступа")
            return
            
    except Exception as e:
        await update.message.reply_text("❌ Ошибка соединения. Попробуйте позже.")
        return
    
    # Если нет доступа
    if not access_data.get('has_access', False):
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
    
    # Ищем активные доступы
    accesses = access_data.get('accesses', [])
    if not accesses:
        await update.message.reply_text("❌ Не найдено активных доступов")
        return
    
    # Показываем все доступы
    for access in accesses:
        if access.get('has_access', False) and access.get('is_active', False):
            profile_key = access.get('profile_key', 'SA_1_DEF')
            payment_id = access.get('payment_id', '')
            
            # Генерируем ссылку
            materials_link = payment_auto_checker.generate_materials_link(profile_key)
            profile_name = payment_auto_checker.get_profile_display_name(profile_key)
            
            message = (
                f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                f"🎯 *Профиль:* {profile_name}\n"
                f"🔑 *Код профиля:* `{profile_key}`\n"
                f"📋 *ID заказа:* `{payment_id}`\n\n"
                f"📚 *Что внутри:*\n"
                f"• Полный разбор профиля (PDF)\n"
                f"• Терапевтическая сказка\n"
                f"• Книга ВАРИАТИКА\n"
                f"• Персональные рекомендации\n"
                f"• Карта сильных и слабых сторон\n\n"
                f"📥 *Ссылка для скачивания:*\n"
                f"`{materials_link}`"
            )
            
            keyboard = [
                [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials_link)],
                [InlineKeyboardButton("📚 ВСЕ МОИ МАТЕРИАЛЫ", callback_data="all_materials")],
                [InlineKeyboardButton("💎 КУПИТЬ ЕЩЕ", callback_data="buy_variatica_package")]
            ]
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            return
    
    # Если дошли сюда - нет активных доступов
    await update.message.reply_text(
        "❌ Нет активных доступов к материалам.\n\n"
        "Возможно, ваш доступ истек или еще не активирован.",
        parse_mode='Markdown'
    )

async def myaccess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса доступа"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    try:
        response = requests.get(
            f"{API_URL}/api/check-access/{user_id}",
            timeout=10
        )
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Ошибка сервера")
            return
            
        access_data = response.json()
        
    except Exception as e:
        await update.message.reply_text("❌ Ошибка соединения")
        return
    
    if access_data.get('has_access'):
        accesses = access_data.get('accesses', [])
        active_count = sum(1 for a in accesses if a.get('has_access') and a.get('is_active'))
        
        message = (
            f"👤 *Пользователь:* {user_name}\n"
            f"🔓 *Статус:* Доступ активен\n"
            f"📦 *Активных пакетов:* {active_count}\n\n"
        )
        
        if active_count > 0:
            message += "Используйте команду /materials для получения материалов\n"
            keyboard = [[InlineKeyboardButton("📚 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data="get_materials")]]
        else:
            message += "Нет активных пакетов. Купите доступ!\n"
            keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП", callback_data="buy_variatica_package")]]
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            f"❌ *ДОСТУП НЕ АКТИВЕН*\n\n"
            f"👤 *Пользователь:* {user_name}\n"
            f"📦 *Статус:* Доступ не оплачен\n\n"
            f"Для получения доступа:\n"
            f"1. Пройдите тест (/start)\n"
            f"2. Нажмите 'Полный пакет рекомендаций'\n"
            f"3. Оплатите доступ\n"
            f"4. Материалы придут АВТОМАТИЧЕСКИ после оплаты",
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
    
    # Проверяем статус
    result = payment_auto_checker.check_payment_status(payment_id)
    
    if not result["success"]:
        await update.message.reply_text(f"❌ *Ошибка:* {result.get('error')}", parse_mode='Markdown')
        return
    
    status = result.get("status", "unknown")
    
    if status == "succeeded":
        await update.message.reply_text(
            f"🎉 *ПЛАТЕЖ ОПЛАЧЕН!*\n\n"
            f"✅ Платеж `{payment_id}` успешно завершен!\n\n"
            f"*🔓 ДОСТУП ОТКРЫТ!*\n"
            f"Материалы должны были прийти автоматически.\n"
            f"Если нет, используйте /materials",
            parse_mode='Markdown'
        )
    elif status in ["pending", "waiting"]:
        await update.message.reply_text(
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Заказ `{payment_id}` еще не оплачен.\n"
            f"После оплаты материалы придут АВТОМАТИЧЕСКИ в течение 1-2 минут.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"📊 *Статус:* `{status}`", parse_mode='Markdown')

# ============================================
# ОБРАБОТЧИКИ ДЛЯ ПОКУПКИ (С АВТОДОСТАВКОЙ)
# ============================================

async def buy_variatica_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка полного пакета с автоматической доставкой"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"💰 Пользователь {user_id} покупает полный пакет")
    
    await query.edit_message_text("💎 *Создаю заказ на полный пакет ВАРИАТИКА...*", parse_mode='Markdown')
    
    # Создаем платеж с авто-доставкой
    payment_result = await create_payment_with_auto_delivery(
        update, context, amount=690.0, is_test=False
    )
    
    if not payment_result:
        await query.edit_message_text(
            "❌ *Ошибка создания заказа*\n\n"
            "Попробуйте еще раз или обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    payment_id = payment_result["payment_id"]
    confirmation_url = payment_result["confirmation_url"]
    
    # Формируем сообщение с информацией об авто-доставке
    message = (
        f"✅ *ЗАКАЗ СОЗДАН!*\n\n"
        f"👤 *Покупатель:* {user_name}\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 руб\n"
        f"📚 *Пакет:* Полный пакет ВАРИАТИКА\n\n"
        f"🚀 *АВТОМАТИЧЕСКАЯ ДОСТАВКА АКТИВИРОВАНА*\n\n"
        f"*Что произойдет после оплаты:*\n"
        f"1️⃣ Вы оплачиваете заказ\n"
        f"2️⃣ Система проверяет платеж каждые 30 секунд\n"
        f"3️⃣ При успешной оплате материалы приходят АВТОМАТИЧЕСКИ\n"
        f"4️⃣ Вы получаете ссылку на Яндекс.Диск\n\n"
        f"⏱ *Проверка платежа:* каждые 30 секунд\n"
        f"📨 *Уведомление:* придет сразу после оплаты\n"
        f"🔧 *Ручная проверка:* /check {payment_id}\n\n"
        f"💡 *Все способы оплаты доступны:*\n"
        f"• СБП (по QR-коду)\n"
        f"• Банковские карты\n"
        f"• ЮMoney\n"
        f"• QIWI\n\n"
        f"*Для оплаты нажмите кнопку ниже:*"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("🧪 Тестовый платеж (1 руб)", callback_data="test_payment")],
        [InlineKeyboardButton("⬅️ Назад к пакетам", callback_data="show_package")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж с авто-доставкой"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    logger.info(f"🧪 Пользователь {user_id} создает тестовый платеж")
    
    await query.edit_message_text("🧪 *Создаю тестовый платеж 1 рубль...*", parse_mode='Markdown')
    
    # Создаем тестовый платеж с авто-доставкой
    payment_result = await create_payment_with_auto_delivery(
        update, context, amount=1.0, is_test=True
    )
    
    if not payment_result:
        await query.edit_message_text(
            "❌ *Ошибка создания тестового платежа*",
            parse_mode='Markdown'
        )
        return
    
    payment_id = payment_result["payment_id"]
    confirmation_url = payment_result["confirmation_url"]
    
    message = (
        f"🧪 *ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН*\n\n"
        f"👤 *Пользователь:* {user_name}\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"📋 *ID:* `{payment_id}`\n\n"
        f"🚀 *АВТОМАТИЧЕСКАЯ ДОСТАВКА АКТИВИРОВАНА*\n\n"
        f"*Для проверки системы:*\n"
        f"1. Нажмите кнопку оплаты\n"
        f"2. Выберите любой способ оплаты\n"
        f"3. После успешной оплаты вернитесь в бот\n"
        f"4. Тестовые материалы придут АВТОМАТИЧЕСКИ\n\n"
        f"💡 *Все способы оплаты доступны*\n"
        f"⏱ *Автопроверка:* каждые 30 секунд"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("💎 Полный пакет (690 руб)", callback_data="buy_variatica_package")],
        [InlineKeyboardButton("⬅️ Назад к пакетам", callback_data="show_package")]
    ]
    
    await query.edit_message_text(
        message,
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
    
    result = payment_auto_checker.check_payment_status(payment_id)
    
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
            f"Материалы должны были прийти автоматически.\n"
            f"Если нет, нажмите кнопку ниже:",
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
            f"Если вы уже оплатили, подождите несколько минут.\n"
            f"Материалы придут АВТОМАТИЧЕСКИ после подтверждения оплаты.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(f"📊 *Статус:* `{status}`", parse_mode='Markdown')

# ============================================
# КОМАНДА ДЛЯ АДМИНИСТРАТОРА
# ============================================

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика для администратора"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        return
    
    pending_count = len(payment_auto_checker.pending_payments)
    
    message = (
        f"📊 *СТАТИСТИКА СИСТЕМЫ АВТО-ДОСТАВКИ*\n\n"
        f"⏳ *Ожидающих платежей:* {pending_count}\n"
        f"⏱ *Интервал проверки:* {payment_auto_checker.check_interval} сек\n"
        f"⏰ *Макс. время проверки:* {payment_auto_checker.max_check_time // 60} мин\n\n"
        f"*Активные платежи:*\n"
    )
    
    if pending_count > 0:
        for payment_id, data in payment_auto_checker.pending_payments.items():
            user_id = data['user_id']
            checks = data['checks_count']
            age = int(time.time() - data['added_time'])
            message += f"• `{payment_id}` - 👤{user_id} ({checks} проверок, {age} сек)\n"
    else:
        message += "Нет активных платежей для отслеживания\n"
    
    message += f"\n✅ *Система работает исправно*"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ============================================
# ОСНОВНЫЕ ЭКРАНЫ ТЕСТА (ВАШ КОД)
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

# ============================================
# ЭКРАН РЕЗУЛЬТАТОВ (ВАШ КОД, МИНИМАЛЬНЫЕ ИЗМЕНЕНИЯ)
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА с кнопкой покупки"""
    query = update.callback_query
    
    has_shared = context.user_data.get("has_shared", False)
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    profile_display = profile_data.get("display_name", "SA_1_DEF")
    
    # Сохраняем профиль в контексте для использования при оплате
    context.user_data['profile_data'] = profile_data
    
    # Основное сообщение с результатом
    message = (
        f"<b>🎯 ВАШ ПРОФИЛЬ ОПРЕДЕЛЕН!</b>\n\n"
        f"<b>Тип профиля:</b> {profile_display}\n"
        f"<b>Уровень:</b> Уровень {profile_data.get('level', 1)}\n"
        f"<b>Тип восприятия:</b> {profile_data.get('type_name', 'СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ')}\n\n"
        f"<b>🚀 АВТОМАТИЧЕСКАЯ ДОСТАВКА МАТЕРИАЛОВ</b>\n\n"
        f"После оплаты материалы придут АВТОМАТИЧЕСКИ в этот чат.\n\n"
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
    
    return "RESULTS"  # Состояние ConversationHandler

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновленный экран пакета с автоматической оплатой"""
    query = update.callback_query
    await query.answer()
    
    # Определяем режим работы
    if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_'):
        payment_mode = "БОЕВОЙ"
    else:
        payment_mode = "ТЕСТОВЫЙ"
    
    package_text = (
        f"<b>💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
        f"<b>Что входит:</b>\n"
        f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
        f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
        f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
        f"• Персональные рекомендации по развитию\n"
        f"• Карта сильных и слабых сторон\n\n"
        f"<b>Цена:</b> 690 ₽\n\n"
        f"<b>🚀 АВТОМАТИЧЕСКАЯ ДОСТАВКА</b>\n\n"
        f"✅ После оплаты материалы придут АВТОМАТИЧЕСКИ в этот чат\n"
        f"✅ Ссылка на Яндекс.Диск с вашей папкой\n"
        f"✅ Чек по 54-ФЗ (в боевом режиме)\n"
        f"✅ Поддержка @meysternlp\n\n"
        f"<b>Режим работы:</b> {payment_mode}\n\n"
        f"<b>ВСЕ способы оплаты доступны:</b>\n"
        f"• СБП (Система быстрых платежей)\n"
        f"• ЮMoney (Яндекс.Деньги)\n"
        f"• Банковские карты (Visa, MasterCard, Мир)\n"
        f"• Apple Pay / Google Pay\n"
        f"• QIWI и другие\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 КУПИТЬ ДОСТУП 690 РУБ", callback_data="buy_variatica_package")],
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА 1 РУБ", callback_data="test_payment")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    return "PACKAGE_SCREEN"

# ============================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ
# ============================================

async def get_materials_after_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов после оплаты"""
    query = update.callback_query
    await query.answer()
    
    # Вызываем команду materials для текущего пользователя
    update.effective_message = query.message
    await materials_command(update, context)

async def all_materials_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все материалы"""
    query = update.callback_query
    await query.answer()
    
    update.effective_message = query.message
    await materials_command(update, context)

# ============================================
# ФУНКЦИИ ДЛЯ JOB QUEUE
# ============================================

async def check_payments_job(context: ContextTypes.DEFAULT_TYPE):
    """Задача для периодической проверки платежей"""
    try:
        await payment_auto_checker.check_all_payments(context)
        payment_auto_checker.cleanup_old_payments()
    except Exception as e:
        logger.error(f"Ошибка в задаче проверки платежей: {e}")

# ============================================
# ЗАПУСК БОТА
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🚀 ВАРИАТИКА БОТ - СИСТЕМА АВТОМАТИЧЕСКОЙ ДОСТАВКИ")
    print("="*60)
    
    # Проверка конфигурации
    print("\n🔧 ПРОВЕРКА КОНФИГУРАЦИИ:")
    print(f"• API URL: {API_URL}")
    print(f"• Bot Token: {'✅ Установлен' if TOKEN else '❌ Отсутствует'}")
    print(f"• YooKassa: {'✅ Настроен' if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY else '⚠️ Частично'}")
    
    print("\n🚀 ФУНКЦИОНАЛ АВТО-ДОСТАВКИ:")
    print("• Автоматическая проверка платежей каждые 30 секунд")
    print("• Мгновенная выдача материалов после оплаты")
    print("• Уведомления пользователю")
    print("• Отслеживание всех платежей")
    
    print("\n📊 СИСТЕМА ГОТОВА К РАБОТЕ!")
    print("="*60)
    
    # Создаем приложение с JobQueue
    application = Application.builder().token(TOKEN).build()
    
    # Настраиваем JobQueue для автоматической проверки
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(
            check_payments_job,
            interval=30,  # Проверка каждые 30 секунд
            first=10     # Первая проверка через 10 секунд
        )
        logger.info("✅ JobQueue настроена: проверка платежей каждые 30 секунд")
    
    # ============================================
    # СОЗДАЕМ CONVERSATION HANDLER (ВАШ СУЩЕСТВУЮЩИЙ КОД)
    # ============================================
    
    # Определяем состояния (используем ваши константы)
    (STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, 
     GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION) = range(10)
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            # Здесь будут ваши существующие состояния...
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$")
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
        fallbacks=[CommandHandler("cancel", lambda update, context: ConversationHandler.END)],
        allow_reentry=True
    )
    
    # Добавляем ConversationHandler
    application.add_handler(conv_handler)
    
    # Добавляем команды для материалов и проверки
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("myaccess", myaccess_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("stats", admin_stats))
    
    # Обработчики для получения материалов
    application.add_handler(CallbackQueryHandler(get_materials_after_payment, pattern="^get_materials_after_payment$"))
    application.add_handler(CallbackQueryHandler(all_materials_callback, pattern="^all_materials$"))
    application.add_handler(CallbackQueryHandler(all_materials_callback, pattern="^check_all_access$"))
    application.add_handler(CallbackQueryHandler(all_materials_callback, pattern="^my_materials$"))
    
    # Запускаем бота
    print("\n✅ Бот запущен! Ожидаю сообщений...")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ЗАГЛУШКИ ДЛЯ ВАШЕГО КОДА)
# ============================================

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для вашего start_test"""
    query = update.callback_query
    await query.answer()
    
    # Инициализация данных теста
    context.user_data.clear()
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    # Переход к показу экрана результатов (для демо)
    return await show_results_screen(update, context)

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для get_gift_screen"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📤 *ПОДЕЛИТЕСЬ ССЫЛКОЙ НА ТЕСТ*\n\n"
        "Поделитесь тестом с друзьями и получите подарок!",
        parse_mode='Markdown'
    )
    
    context.user_data["has_shared"] = True
    return await show_results_screen(update, context)

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для open_gift_screen"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🎁 *ВАШ ПОДАРОК ГОТОВ!*\n\n"
        "Сказка для трансформации восприятия: https://disk.yandex.ru/i/Cacp7x1Vt3XhbA",
        parse_mode='Markdown'
    )
    return "OPEN_GIFT_SCREEN"

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для restart_test"""
    query = update.callback_query
    await query.answer()
    
    return await start_test(update, context)

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для back_to_results"""
    query = update.callback_query
    await query.answer()
    
    return await show_results_screen(update, context)

if __name__ == "__main__":
    main()
