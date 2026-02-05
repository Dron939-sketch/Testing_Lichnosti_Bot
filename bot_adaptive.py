# -*- coding: utf-8 -*-
"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа + адаптивные уточнения + СИСТЕМА БАЛЛОВ как в карточном тесте
ВЕРСИЯ 2.0: Добавлена интеграция с ЮKassa для автоматической отправки файлов
ИСПРАВЛЕННАЯ ВЕРСИЯ ДЛЯ RENDER.COM с python-telegram-bot==20.7
"""

### КОНФИГУРАЦИЯ ТОКЕНОВ ###
import os
import sys
import logging
import asyncio
import urllib.parse
import math
import re
import json
import base64
import requests
from datetime import datetime
from collections import Counter
from typing import Dict, Any, Optional, Tuple, List

# ГАРАНТИЯ РАБОТЫ НА RENDER - принудительная установка версии 20.7
def force_python_telegram_bot_20_7():
    """Принудительно устанавливает версию 20.7"""
    print("🔧 Проверяем версию python-telegram-bot...")
    try:
        import subprocess
        import importlib
        # Устанавливаем нужную версию
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--force-reinstall", "python-telegram-bot==20.7"
        ], check=True)
        print("✅ python-telegram-bot==20.7 установлен")
    except Exception as e:
        print(f"⚠️ Ошибка установки: {e}")

# Проверяем версию перед импортом
try:
    import telegram
    if not telegram.__version__.startswith("20."):
        print(f"⚠️ Неправильная версия: {telegram.__version__}")
        force_python_telegram_bot_20_7()
        import importlib
        importlib.reload(telegram)
        print(f"✅ Перезагружена версия: {telegram.__version__}")
except ImportError:
    print("⚠️ python-telegram-bot не установлен")
    force_python_telegram_bot_20_7()
    import telegram

# Теперь импортируем остальные модули CORRECTLY для версии 20.7
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    ApplicationBuilder,
)

# Проверяем наличие dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env файл загружен")
except ImportError:
    print("⚠️ python-dotenv не установлен")

# Загружаем токены из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "1262862")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# КРИТИЧЕСКАЯ ПРОВЕРКА ТОКЕНА
if not TELEGRAM_BOT_TOKEN:
    print("="*60)
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
    print("="*60)
    print("\nИНСТРУКЦИЯ ПО НАСТРОЙКЕ:")
    print("1. Для Render.com:")
    print("   - Environment -> Add Environment Variable")
    print("   - Key: TELEGRAM_BOT_TOKEN")
    print("   - Value: ваш_токен_бота")
    print("2. Добавьте также:")
    print("   - YOOKASSA_SECRET_KEY")
    print("3. Перезапустите сервис")
    sys.exit(1)

# ЛОГИРОВАНИЕ для Render
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# ИНФОРМАЦИЯ О КОНФИГУРАЦИИ
print("="*60)
print("🚀 ВАРИАТИКА БОТ v2.0 - ЗАПУСК НА RENDER.COM")
print("="*60)
print(f"✅ TELEGRAM_BOT_TOKEN: {'✓' if TELEGRAM_BOT_TOKEN else '✗'}")
print(f"✅ YOOKASSA_SHOP_ID: {YOOKASSA_SHOP_ID}")
print(f"✅ YOOKASSA_SECRET_KEY: {'✓' if YOOKASSA_SECRET_KEY else '✗'}")
print(f"✅ python-telegram-bot: {telegram.__version__}")
print("="*60)

if not YOOKASSA_SECRET_KEY:
    logger.warning("⚠️ YOOKASSA_SECRET_KEY не настроен. Платежи работать не будут!")

# ============================================
# КОНСТАНТЫ
# ============================================

BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чем еще не знал..."

# ФАЙЛЫ ДЛЯ ОТПРАВКИ ПОСЛЕ ОПЛАТЫ
PAID_FILES = [
    ("📚 Полный разбор профиля (PDF)", "https://disk.yandex.ru/d/full_analysis.pdf"),
    ("📖 Терапевтическая сказка", GIFT_PDF_LINK),
    ("📘 Книга ВАРИАТИКА", "https://disk.yandex.ru/d/book.pdf"),
    ("📋 Рекомендации по развитию", "https://disk.yandex.ru/d/recommendations.pdf"),
    ("🗺 Карта сильных и слабых сторон", "https://disk.yandex.ru/d/profile_map.pdf")
]

# Состояния ConversationHandler
(STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, 
 RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, 
 DILTS_CLARIFICATION, PAYMENT_CHECK) = range(11)

# ============================================
# ВОПРОСЫ ЭТАПА 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ (8 ВОПРОСОВ)
# ============================================

STAGE_1_QUESTIONS = [
    {
        "id": "q1_1",
        "text": "У тебя неожиданно освободился вечер.\n\nЧто звучит привлекательнее?",
        "options": {
            "a": {"text": "Позвать друзей", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Побыть одному", "scores": {"INTERNAL": 2}},
            "c": {"text": "Сходить куда-то (событие/место)", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Почитать/посмотреть что-то", "scores": {"INTERNAL": 1}}
        }
    },
    {
        "id": "q1_2",
        "text": "Что даёт тебе больше ресурса для жизни?",
        "options": {
            "a": {"text": "Люди, события, движение", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Мысли, чувства, тишина", "scores": {"INTERNAL": 2}},
            "c": {"text": "И то, и то в равной степени", "scores": {}},
            "d": {"text": "Зависит от ситуации", "scores": {}}
        }
    },
    {
        "id": "q1_3",
        "text": "Ты на вечеринке, где почти никого не знаешь.\n\nЧто происходит?",
        "options": {
            "a": {"text": "Активно знакомлюсь со всеми", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Нахожу 1-2 человек и общаюсь с ними", "scores": {"EXTERNAL": 1}},
            "c": {"text": "Держусь в стороне", "scores": {"INTERNAL": 1}},
            "d": {"text": "Ухожу при первой возможности", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_4",
        "text": "Если бы твоя жизнь была местом, это было бы:",
        "options": {
            "a": {"text": "Оживлённая площадь", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Уютная комната", "scores": {"INTERNAL": 1}},
            "c": {"text": "Открытое пространство", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Тихое уединённое место", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_5",
        "text": "Что тебя больше выбивает из равновесия?",
        "options": {
            "a": {"text": "Когда тебя не понимают", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Когда теряешь что-то важное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Когда не ясно, что происходит", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Когда всё идёт не по плану", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_6",
        "text": "Что для тебя важнее?",
        "options": {
            "a": {"text": "Достичь цели", "scores": {"MATERIAL": 1}},
            "b": {"text": "Сохранить отношения", "scores": {"SYMBOLIC": 2}},
            "c": {"text": "Понять суть", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Сделать результат", "scores": {"MATERIAL": 2}}
        }
    },
    {
        "id": "q1_7",
        "text": "Что страшнее потерять?",
        "options": {
            "a": {"text": "Связь с важными людьми", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Финансовую стабильность", "scores": {"MATERIAL": 2}},
            "c": {"text": "Понимание себя", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Контроль над ситуацией", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_8",
        "text": "Вспомни последнюю сильную тревогу.\n\nО чём она была?",
        "options": {
            "a": {"text": "Меня отвергнут / не поймут", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Я потеряю что-то ценное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Я не понимаю, что со мной", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Я не справлюсь / не успею", "scores": {"MATERIAL": 1}}
        }
    }
]

# Типы восприятия
PERCEPTION_TYPES = {
    ("EXTERNAL", "SYMBOLIC"): {
        "name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ",
        "code": "SA",
        "description": "Фокус на внешних отношениях и социальном принятии"
    },
    ("INTERNAL", "SYMBOLIC"): {
        "name": "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ",
        "code": "IA",
        "description": "Фокус на внутренних смыслах и глубине переживания"
    },
    ("EXTERNAL", "MATERIAL"): {
        "name": "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ",
        "code": "SP",
        "description": "Фокус на внешних достижениях и результатах"
    },
    ("INTERNAL", "MATERIAL"): {
        "name": "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ",
        "code": "IP",
        "description": "Фокус на внутреннем порядке и системах понимания"
    }
}

# ============================================
# ФУНКЦИИ ЮKASSA
# ============================================

def create_payment_link(user_id: int) -> Dict[str, Any]:
    """Создает платежную ссылку через ЮKassa API"""
    
    if not YOOKASSA_SECRET_KEY:
        logger.error("❌ YOOKASSA_SECRET_KEY не настроен")
        return {"success": False, "error": "Платежная система не настроена"}
    
    payment_data = {
        "amount": {
            "value": "690.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/Testing_Lichnosti_bot"
        },
        "capture": True,
        "description": "Полный пакет ВАРИАТИКА",
        "metadata": {
            "user_id": str(user_id),
            "product": "full_package",
            "telegram_bot": "VariaticaBot"
        }
    }
    
    try:
        auth = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(int(datetime.now().timestamp()))
        }
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payment_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Платеж создан: {result['id']} для пользователя {user_id}")
            return {
                "success": True,
                "payment_url": result["confirmation"]["confirmation_url"],
                "payment_id": result["id"]
            }
        else:
            logger.error(f"❌ YooKassa API error: {response.status_code} - {response.text[:200]}")
            return {"success": False, "error": f"API error {response.status_code}"}
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {"success": False, "error": str(e)}

def check_payment_status(payment_id: str) -> Dict[str, Any]:
    """Проверяет статус платежа в ЮKassa"""
    
    if not YOOKASSA_SECRET_KEY:
        return {"success": False, "error": "ЮKassa не настроена"}
    
    try:
        auth = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        
        response = requests.get(
            f"https://api.yookassa.ru/v3/payments/{payment_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Статус платежа {payment_id}: {result['status']}")
            return {
                "success": True,
                "status": result["status"],
                "paid": result["status"] == "succeeded",
                "metadata": result.get("metadata", {})
            }
        else:
            logger.error(f"❌ YooKassa API error: {response.status_code} - {response.text[:200]}")
            return {"success": False, "error": f"API error {response.status_code}"}
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки платежа: {e}")
        return {"success": False, "error": str(e)}

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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
    return final_level

# УПРОЩЕННАЯ ФУНКЦИЯ ДЛЯ ПОИСКА ПРОФИЛЯ
class SimpleProfile:
    def __init__(self, profile_data: dict):
        self.title = f"Профиль {profile_data['display_name']}"
        self.archetype = "Архетип"
        self.quote = "«Цитата профиля»"
        self.trigger = f"Это ты, если... (профиль {profile_data['display_name']})"
        self.pain = f"СУТЬ ПРОБЛЕМЫ:\nПроблема на уровне {profile_data['dilts_level'].lower()}"
        self.immediate_tool = "ПЕРВЫЙ ШАГ: Осознать паттерн"
        self.cta = "ДАЛЬШЕ: Пройти полный анализ"

def get_profile_fallback(profile_data: dict):
    """Возвращает простой профиль"""
    return SimpleProfile(profile_data)

def calculate_profile_final(context_data: dict) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля"""
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    level_scores_dict = context_data.get("stage2_level_scores_dict", {})
    stage2_level = calculate_thinking_level_by_scores(level_scores_dict)
    
    stage3_scores = context_data.get("stage3_level_scores", [])
    final_level = calculate_final_level(stage2_level, stage3_scores)
    final_level = max(1, min(9, final_level))
    
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

def need_clarification_stage1(scores):
    """Нужны ли уточнения после ЭТАПА 1"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    clarifications = []
    if abs(external - internal) <= 2:
        clarifications.append("external_internal")
    if abs(symbolic - material) <= 2:
        clarifications.append("symbolic_material")
    
    return clarifications

def need_clarification_stage2(level_scores_dict):
    """Нужны ли уточнения после ЭТАПА 2"""
    if not level_scores_dict:
        return False
    
    sorted_levels = sorted(level_scores_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_levels) >= 2:
        first_score = sorted_levels[0][1]
        second_score = sorted_levels[1][1]
        
        if abs(first_score - second_score) < 3:
            logger.info(f"Stage2 needs clarification: {sorted_levels[0]} vs {sorted_levels[1]}")
            return True
    
    return False

# ============================================
# ЭКРАНЫ ОПЛАТЫ
# ============================================

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНЫЙ ПАКЕТ с созданием платежа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Создаем платеж
    payment_result = create_payment_link(user_id)
    
    if payment_result["success"]:
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить 690 ₽", url=payment_result["payment_url"])],
            [InlineKeyboardButton("✅ Проверить оплату", callback_data=f"check_{payment_result['payment_id']}")],
            [InlineKeyboardButton("📨 Помощь", url="https://t.me/meysternlp")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
        ]
        
        message_text = (
            f"<b>💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
            f"Сумма: <b>690 ₽</b>\n"
            f"ID платежа: <code>{payment_result['payment_id']}</code>\n\n"
            f"<b>Что входит:</b>\n"
            f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
            f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
            f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
            f"• Персональные рекомендации по развитию\n"
            f"• Карта сильных и слабых сторон\n\n"
            f"<b>Как получить файлы:</b>\n"
            f"1. Нажмите '💳 Оплатить 690 ₽'\n"
            f"2. Оплатите в открывшемся окне\n"
            f"3. Нажмите '✅ Проверить оплату'\n"
            f"4. Файлы придут автоматически\n\n"
            f"<i>Проблемы с оплатой? Нажмите '📨 Помощь'</i>"
        )
        
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="show_package")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
        ]
        message_text = (
            f"❌ <b>Ошибка создания платежа</b>\n\n"
            f"Попробуйте позже или напишите @meysternlp\n\n"
            f"Ошибка: {payment_result.get('error', 'Неизвестно')[:100]}"
        )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка оплаты"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("check_", "")
    
    try:
        # Проверяем статус платежа через API
        status_result = check_payment_status(payment_id)
        
        if not status_result["success"]:
            raise Exception(f"Ошибка API: {status_result.get('error', 'Неизвестно')}")
        
        if status_result["paid"]:
            # УСПЕШНАЯ ОПЛАТА!
            user_id = status_result["metadata"].get("user_id")
            
            # Валидация user_id
            if user_id and int(user_id) == query.from_user.id:
                # Отправляем файлы
                await send_files_after_payment(update, context, int(user_id))
                return ConversationHandler.END
            else:
                logger.error(f"❌ User ID mismatch")
                await query.edit_message_text(
                    "❌ <b>ОШИБКА БЕЗОПАСНОСТИ</b>\n\n"
                    "ID пользователя не совпадает. Напишите @meysternlp для помощи.",
                    parse_mode="HTML"
                )
                return PAYMENT_CHECK
                
        elif status_result["status"] == "pending":
            # Ожидание оплаты
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_{payment_id}")],
                [InlineKeyboardButton("📨 Помощь", url="https://t.me/meysternlp")],
                [InlineKeyboardButton("💳 Оплатить снова", callback_data="show_package")]
            ]
            
            await query.edit_message_text(
                f"⏳ <b>ОЖИДАНИЕ ОПЛАТЫ</b>\n\n"
                f"ID: <code>{payment_id}</code>\n"
                f"Статус: ожидание оплаты\n\n"
                f"Если вы уже оплатили:\n"
                f"1. Подождите 2-3 минуты\n"
                f"2. Проверьте снова\n"
                f"3. Или напишите @meysternlp",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return PAYMENT_CHECK
            
        else:
            # Неуспешный статус
            keyboard = [
                [InlineKeyboardButton("🔄 Создать новый платеж", callback_data="show_package")],
                [InlineKeyboardButton("📨 Помощь", url="https://t.me/meysternlp")]
            ]
            
            await query.edit_message_text(
                f"❌ <b>ПЛАТЕЖ НЕ ОПЛАЧЕН</b>\n\n"
                f"ID: <code>{payment_id}</code>\n"
                f"Статус: {status_result['status']}\n\n"
                f"Создать новый платеж?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return PAYMENT_CHECK
                
    except Exception as e:
        logger.error(f"❌ Payment check error for {payment_id}: {e}")
        await query.edit_message_text(
            f"⚠️ <b>ОШИБКА ПРОВЕРКИ</b>\n\n"
            f"ID: <code>{payment_id}</code>\n"
            f"Ошибка: {str(e)[:100]}\n\n"
            f"Напишите @meysternlp для помощи",
            parse_mode="HTML"
        )
        return PAYMENT_CHECK

async def send_files_after_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Отправляет файлы после успешной оплаты"""
    query = update.callback_query
    
    # Сообщение об успехе
    success_message = await query.edit_message_text(
        "🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n"
        "Подготовка файлов...",
        parse_mode="HTML"
    )
    
    sent_files = 0
    total_files = len(PAID_FILES)
    
    # Отправляем файлы
    for i, (file_name, file_url) in enumerate(PAID_FILES, 1):
        try:
            # Обновляем прогресс
            if i > 1:
                await success_message.edit_text(
                    f"🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n"
                    f"Отправляю файлы...\n"
                    f"📦 {i-1}/{total_files} отправлено",
                    parse_mode="HTML"
                )
            
            # Отправляем файл
            await context.bot.send_document(
                chat_id=user_id,
                document=file_url,
                caption=file_name
            )
            sent_files += 1
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"❌ Error sending file {file_name}: {e}")
            # Отправляем ссылку как сообщение
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Не удалось отправить {file_name}\nСсылка: {file_url}"
            )
    
    # Финальное сообщение
    await success_message.edit_text(
        f"✅ <b>ВСЕ ФАЙЛЫ ОТПРАВЛЕНЫ!</b>\n\n"
        f"Отправлено: {sent_files}/{total_files} файлов\n\n"
        f"Если нужна консультация:\n"
        f"👉 @meysternlp",
        parse_mode="HTML"
    )

# ============================================
# ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА"""
    query = update.callback_query
    
    has_shared = context.user_data.get("has_shared", False)
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    profile = get_profile_fallback(profile_data)
    
    message = (
        f"<b>🎯 ВАШ ПРОФИЛЬ: {profile_data['display_name']}</b>\n\n"
        f"<b>Тип восприятия:</b> {profile_data['type_name']}\n"
        f"<b>Уровень мышления:</b> {profile_data['level_name']} ({profile_data['level']})\n"
        f"<b>Точка роста:</b> {profile_data['dilts_level'].title()}\n\n"
        f"<b>{profile.title}</b>\n\n"
        f"{profile.trigger}\n\n"
        f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
        f"{profile.pain}\n\n"
        f"<b>🛠 ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»</b>\n\n"
        f"{profile.immediate_tool}\n\n"
        f"<b>🚀 ЧТО ДАЛЬШЕ?</b>\n\n"
        f"{profile.cta}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    if not has_shared:
        message += (
            f"<b>🎁 ПОДАРОК ЗА РЕПОСТ</b>\n"
            f"Поделись тестом с друзьями и получи бонусный материал.\n\n"
        )
    else:
        message += (
            f"<b>🎉 ГОТОВО!</b>\n"
            f"Спасибо за репост! Твой подарок ждёт тебя.\n\n"
        )
    
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться и получить подарок", callback_data="get_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Забрать подарок", callback_data="open_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    return RESULTS

# ============================================
# ОСТАЛЬНЫЕ ЭКРАНЫ
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

# ============================================
# НАЧАЛЬНЫЕ ЭКРАНЫ И КОМАНДЫ
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
    
    return await show_stage_1_intro(update, context)

# ============================================
# ПРОСТЫЕ ЭТАПЫ ТЕСТА (без сложной логики уточнений)
# ============================================

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 1"""
    query = update.callback_query
    
    intro_text = (
        f"<b>🎯 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"Сейчас мы определим твой базовый тип восприятия реальности.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("▶️ Начать ЭТАП 1", callback_data="start_stage_1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage1_current"] = 0
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
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_1
    
    context.user_data["processing"] = True
    
    try:
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
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАП 1"""
    query = update.callback_query
    scores = context.user_data.get("scores", {})
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация восприятия определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="start_stage_2")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

# ============================================
# ПРОСТЫЕ ВОПРОСЫ ЭТАПА 2
# ============================================

STAGE_2_SIMPLE_QUESTIONS = [
    {
        "text": "Сколько у тебя близких людей?\n\n(С кем можно говорить о личном)",
        "options": {
            "1": "Нет таких",
            "2": "1-2 человека", 
            "3": "3-5 человек",
            "5": "Больше 5"
        }
    },
    {
        "text": "Как ты к этому относишься?",
        "options": {
            "1": "Мне не хватает близости",
            "2": "Я в процессе поиска своих людей",
            "3": "Меня это устраивает",
            "4": "Я не нуждаюсь в этом"
        }
    },
    {
        "text": "Как часто за месяц ты отменяешь встречи с друзьями?",
        "options": {
            "1": "Не отменяю / нет встреч",
            "3": "1-2 раза",
            "2": "3-5 раз",
            "1": "Постоянно отменяю"
        }
    },
    {
        "text": "Почему отменяешь?",
        "options": {
            "1": "Нет сил на людей",
            "2": "Эти люди не мои",
            "5": "Появились более важные дела",
            "3": "Не отменяю"
        }
    },
    {
        "text": "Как часто ты чувствуешь, что тебя не понимают?",
        "options": {
            "1": "Постоянно",
            "2": "Часто",
            "4": "Иногда",
            "3": "Редко или никогда"
        }
    },
    {
        "text": "Что ты с этим делаешь?",
        "options": {
            "1": "Пытаюсь объясниться",
            "2": "Ищу тех, кто поймёт",
            "4": "Принимаю это",
            "3": "Меня понимают"
        }
    },
    {
        "text": "Твой друг постоянно меняет компании.\n\nКак думаешь, почему?",
        "options": {
            "2": "Ищет своих людей",
            "1": "Боится близости",
            "5": "Ему везде интересно",
            "4": "Не может быть собой"
        }
    },
    {
        "text": "Что для тебя значит «найти своих людей»?",
        "options": {
            "2": "Место, где меня принимают",
            "3": "Люди, с которыми не нужно притворяться",
            "5": "Глубокая связь на уровне ценностей",
            "1": "Не думал об этом"
        }
    }
]

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    current = context.user_data.get("stage2_current", 0)
    
    if current >= len(STAGE_2_SIMPLE_QUESTIONS):
        return await finish_stage_2(update, context)
    
    question = STAGE_2_SIMPLE_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_2_SIMPLE_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for level_num, answer_text in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                answer_text, 
                callback_data=f"stage2_{current}_{level_num}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_2
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_2
        
        current = int(parts[1])
        selected_level = parts[2]
        
        if "stage2_level_scores_dict" not in context.user_data:
            context.user_data["stage2_level_scores_dict"] = {
                "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
                "6": 0, "7": 0, "8": 0, "9": 0
            }
        
        # Простая логика подсчета
        if selected_level in context.user_data["stage2_level_scores_dict"]:
            context.user_data["stage2_level_scores_dict"][selected_level] += 2
        
        logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> level={selected_level}")
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2"""
    query = update.callback_query
    level_scores_dict = context.user_data.get("stage2_level_scores_dict", {"1": 0})
    
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    context.user_data["thinking_level"] = thinking_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация мышления определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="start_stage_3")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

# ============================================
# ПРОСТЫЕ ВОПРОСЫ ЭТАПА 3
# ============================================

STAGE_3_SIMPLE_QUESTIONS = [
    {"id": "q3_1", "text": "Вспомни последнюю неделю.\n\nСколько раз ты сделал что-то, что потом пожалел?", "options": {"a": {"text": "Ни разу", "level": 5}, "b": {"text": "1-2 раза", "level": 3}, "c": {"text": "3-5 раз", "level": 2}, "d": {"text": "Больше 5 раз", "level": 1}}},
    {"id": "q3_2", "text": "Последний конфликт.\n\nЧто ты сделал?", "options": {"a": {"text": "Избежал", "level": 1}, "b": {"text": "Уступил", "level": 1}, "c": {"text": "Отстоял позицию", "level": 3}, "d": {"text": "Нашёл компромисс", "level": 5}}},
    {"id": "q3_3", "text": "Как ты принимаешь важные решения?", "options": {"a": {"text": "Долго мучаюсь", "level": 1}, "b": {"text": "Взвешиваю варианты", "level": 3}, "c": {"text": "Быстро, по интуиции", "level": 5}, "d": {"text": "Жду, когда решение придёт само", "level": 4}}},
    {"id": "q3_4", "text": "Как часто ты делаешь то, что не хочешь, но «надо»?", "options": {"a": {"text": "Постоянно (вся жизнь — «надо»)", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко (делаю то, что хочу)", "level": 5}}},
]

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    current = context.user_data.get("stage3_current", 0)
    
    if current >= len(STAGE_3_SIMPLE_QUESTIONS):
        return await finish_stage_3(update, context)
    
    question = STAGE_3_SIMPLE_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_3_SIMPLE_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage3_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_3
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_3
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_3_SIMPLE_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_3
        
        level = selected_option.get("level", 1)
        if "stage3_level_scores" not in context.user_data:
            context.user_data["stage3_level_scores"] = []
        context.user_data["stage3_level_scores"].append(level)
        
        logger.info(f"User {update.effective_user.id}: Stage 3 Q{current} -> {option_id} (level={level})")
        
        context.user_data["stage3_current"] = current + 1
        return await ask_stage_3_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3"""
    query = update.callback_query
    
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    
    final_level = calculate_final_level(stage2_level, stage3_scores)
    context.user_data["final_level"] = final_level
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, final_level={final_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 3 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Поведенческие паттерны проанализированы\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 4</b>: конфликт логических уровней.\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="start_stage_4")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

# ============================================
# ПРОСТЫЕ ВОПРОСЫ ЭТАПА 4
# ============================================

STAGE_4_SIMPLE_QUESTIONS = [
    {"id": "q4_1", "text": "Как часто ты чувствуешь, что «что-то не так» в жизни?", "options": {"a": {"text": "Постоянно", "dilts": "IDENTITY"}, "b": {"text": "Часто", "dilts": "VALUES"}, "c": {"text": "Иногда", "dilts": "CAPABILITIES"}, "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}}},
    {"id": "q4_2", "text": "Что именно «не так»?\n\nВыбери то, что ближе всего:", "options": {"a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"}, "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"}, "c": {"text": "Не умею делать то, что хочу", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}}},
    {"id": "q4_3", "text": "Если бы ты мог изменить что-то одно, что бы это было?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Своё понимание целей", "dilts": "VALUES"}}},
    {"id": "q4_4", "text": "Что для тебя сложнее всего?", "options": {"a": {"text": "Изменить внешние условия", "dilts": "ENVIRONMENT"}, "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"}, "c": {"text": "Научиться новому", "dilts": "CAPABILITIES"}, "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}}},
]

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    current = context.user_data.get("stage4_current", 0)
    
    if current >= len(STAGE_4_SIMPLE_QUESTIONS):
        return await finish_stage_4(update, context)
    
    question = STAGE_4_SIMPLE_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_4_SIMPLE_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 4: КОНФИГУРАЦИЯ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage4_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 4"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_4
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_4
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_4_SIMPLE_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_4
        
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        if "stage4_dilts_answers" not in context.user_data:
            context.user_data["stage4_dilts_answers"] = []
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        logger.info(f"User {update.effective_user.id}: Stage 4 Q{current} -> {option_id} (dilts={dilts})")
        
        context.user_data["stage4_current"] = current + 1
        return await ask_stage_4_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4"""
    query = update.callback_query
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    
    profile_data = calculate_profile_final(context.user_data)
    context.user_data["profile_data"] = profile_data
    
    loading_text = f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\nАнализирую твои ответы и определяю профиль..."
    await query.edit_message_text(loading_text, parse_mode="HTML")
    await asyncio.sleep(2)
    
    return await show_results_screen(update, context)

# ============================================
# ОТМЕНА ТЕСТА
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

# ============================================
# HEALTH CHECK ДЛЯ RENDER
# ============================================

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check эндпоинт для мониторинга"""
    await update.message.reply_text(
        "✅ Бот работает нормально!\n"
        f"Версия: python-telegram-bot {telegram.__version__}\n"
        f"ЮKassa настроена: {'✅' if YOOKASSA_SECRET_KEY else '❌'}"
    )

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*60)
    print("🚀 ВАРИАТИКА БОТ v2.0 - ЗАПУСК НА RENDER.COM")
    print("="*60)
    
    # Проверка ЮKassa
    if YOOKASSA_SECRET_KEY:
        if YOOKASSA_SECRET_KEY.startswith("test_"):
            print("💰 Режим ЮKassa: ТЕСТОВЫЙ (test_...)")
        elif YOOKASSA_SECRET_KEY.startswith("live_"):
            print("💰 Режим ЮKassa: ПРОДАКШЕН (live_...)")
        else:
            print("⚠️  Режим ЮKassa: НЕИЗВЕСТНЫЙ ФОРМАТ КЛЮЧА")
    else:
        print("⚠️  ЮKassa: НЕ НАСТРОЕНА (платежи не будут работать)")
    
    print(f"✅ Загружено вопросов: ЭТАП 1: {len(STAGE_1_QUESTIONS)}, "
          f"ЭТАП 2: {len(STAGE_2_SIMPLE_QUESTIONS)}, "
          f"ЭТАП 3: {len(STAGE_3_SIMPLE_QUESTIONS)}, "
          f"ЭТАП 4: {len(STAGE_4_SIMPLE_QUESTIONS)}")
    print("="*60)
    
    try:
        # ИСПРАВЛЕННЫЙ ЗАПУСК для python-telegram-bot==20.7
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                CallbackQueryHandler(start_test, pattern="^start_test$")
            ],
            states={
                STAGE_1: [
                    CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                    CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
                ],
                STAGE_2: [
                    CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                    CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
                ],
                STAGE_3: [
                    CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                    CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
                ],
                STAGE_4: [
                    CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                    CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
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
                    CallbackQueryHandler(check_payment, pattern="^check_"),
                    CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                    CallbackQueryHandler(show_package_screen, pattern="^show_package$")
                ],
                PAYMENT_CHECK: [
                    CallbackQueryHandler(check_payment, pattern="^check_"),
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
        
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("health", health_check))
        
        print("✅ Бот запущен и готов к работе!")
        print("="*60)
        
        # ИСПРАВЛЕННЫЙ МЕТОД ЗАПУСКА
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
