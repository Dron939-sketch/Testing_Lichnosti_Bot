# bot_adaptive_v3.py
"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА (ВЕРСИЯ 3.0)

КЛЮЧЕВЫЕ УЛУЧШЕНИЯ:
✅ Оптимизированный алгоритм определения профиля (36 профилей)
✅ Интеграция с card_data.py для описаний
✅ Умная логика присвоения уровня Дилтса на основе уровня мышления
✅ Валидация и коррекция профиля
✅ Детальное логирование всех этапов
"""

import logging
import os
from datetime import datetime
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
# ИМПОРТ МОДУЛЕЙ
# ============================================
from card_data import get_profile_description
from questions_data_v2 import (
    STAGE_1_QUESTIONS,
    STAGE_2_BASE_QUESTIONS,
    STAGE_2_CLARIFYING_QUESTIONS,
    STAGE_3_BASE_QUESTIONS,
    STAGE_3_CLARIFYING_QUESTIONS,
    STAGE_4_QUESTIONS,
    PERCEPTION_TYPES,
    DILTS_LEVELS,
    DILTS_HIERARCHY
)

# Получение токена
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния ConversationHandler
STAGE_1, STAGE_2, STAGE_3, STAGE_4, RESULT = range(5)

# ============================================
# ОПТИМИЗИРОВАННЫЙ АЛГОРИТМ ОПРЕДЕЛЕНИЯ ПРОФИЛЯ
# ============================================

def calculate_thinking_level_optimized(level_scores):
    """
    ОПТИМИЗИРОВАННЫЙ алгоритм определения уровня мышления
    
    Логика (приоритеты):
    1. Если разброс ≤ 1 → среднее (стабильность)
    2. Если разброс = 2 → взвешенное среднее (min*0.3 + avg*0.7)
    3. Если разброс > 2:
       - Проверяем тренд (рост/падение)
       - Если рост → min + 1 (потенциал)
       - Если нет тренда → min (консервативная оценка)
    
    Returns:
        int: Уровень мышления (1-9)
    """
    if not level_scores:
        return 1
    
    min_level = min(level_scores)
    max_level = max(level_scores)
    avg_level = sum(level_scores) / len(level_scores)
    spread = max_level - min_level
    
    logger.info(f"[LEVEL_CALC] Scores: {level_scores}")
    logger.info(f"[LEVEL_CALC] Min={min_level}, Max={max_level}, Avg={avg_level:.2f}, Spread={spread}")
    
    # 1. Стабильные ответы (разброс ≤ 1)
    if spread <= 1:
        result = round(avg_level)
        logger.info(f"[LEVEL_CALC] ✓ Stable (spread≤1) → Level {result}")
        return max(1, min(result, 9))
    
    # 2. Небольшой разброс (разброс = 2)
    elif spread == 2:
        # Взвешенное среднее: больше веса среднему, меньше минимуму
        result = round(min_level * 0.3 + avg_level * 0.7)
        logger.info(f"[LEVEL_CALC] ✓ Small spread (=2) → Level {result}")
        return max(1, min(result, 9))
    
    # 3. Большой разброс (разброс > 2)
    else:
        # Проверяем тренд (только если достаточно данных)
        if len(level_scores) >= 6:
            first_third = level_scores[:len(level_scores)//3]
            last_third = level_scores[-len(level_scores)//3:]
            
            avg_first = sum(first_third) / len(first_third)
            avg_last = sum(last_third) / len(last_third)
            
            logger.info(f"[LEVEL_CALC] Trend: first={avg_first:.2f}, last={avg_last:.2f}")
            
            # Если есть рост (последняя треть > первой на 1.5+)
            if avg_last > avg_first + 1.5:
                result = min(min_level + 1, 9)
                logger.info(f"[LEVEL_CALC] ✓ Growth trend → Level {result}")
                return result
        
        # Нет роста или мало данных → консервативная оценка (минимум)
        result = min_level
        logger.info(f"[LEVEL_CALC] ✓ Large spread, no growth → Level {result}")
        return max(1, min(result, 9))


def determine_dilts_level_smart(final_level, dilts_answers):
    """
    УМНОЕ определение уровня Дилтса с учётом уровня мышления
    
    Логика:
    1. Подсчитываем частоту каждого уровня Дилтса
    2. Применяем взвешенный подсчёт (иерархия важности)
    3. КОРРЕКТИРУЕМ на основе уровня мышления:
       - Уровни 1-2 → не могут иметь IDENTITY/VALUES (снижаем до BEHAVIOR/CAPABILITIES)
       - Уровни 3-5 → могут иметь CAPABILITIES/VALUES
       - Уровни 6-7 → могут иметь VALUES/IDENTITY
       - Уровни 8-9 → могут иметь IDENTITY
    
    Returns:
        str: Уровень Дилтса (ENVIRONMENT, BEHAVIOR, CAPABILITIES, VALUES, IDENTITY)
    """
    if not dilts_answers:
        return "ENVIRONMENT"
    
    counter = Counter(dilts_answers)
    logger.info(f"[DILTS_CALC] Raw counts: {dict(counter)}")
    logger.info(f"[DILTS_CALC] Thinking level: {final_level}")
    
    # 1. Критическая проверка: IDENTITY (≥3 упоминания)
    if counter.get("IDENTITY", 0) >= 3:
        # Но только если уровень мышления позволяет
        if final_level >= 8:
            logger.info(f"[DILTS_CALC] ✓ Critical IDENTITY (level {final_level}≥8)")
            return "IDENTITY"
        else:
            logger.info(f"[DILTS_CALC] ✗ IDENTITY blocked (level {final_level}<8) → downgrade to VALUES")
            # Снижаем до VALUES
            counter["VALUES"] = counter.get("VALUES", 0) + counter.get("IDENTITY", 0)
            del counter["IDENTITY"]
    
    # 2. Критическая проверка: VALUES (≥3 упоминания)
    if counter.get("VALUES", 0) >= 3:
        # Только если уровень мышления позволяет
        if final_level >= 6:
            logger.info(f"[DILTS_CALC] ✓ Critical VALUES (level {final_level}≥6)")
            return "VALUES"
        else:
            logger.info(f"[DILTS_CALC] ✗ VALUES blocked (level {final_level}<6) → downgrade to CAPABILITIES")
            # Снижаем до CAPABILITIES
            counter["CAPABILITIES"] = counter.get("CAPABILITIES", 0) + counter.get("VALUES", 0)
            del counter["VALUES"]
    
    # 3. Взвешенный подсчёт
    weighted_scores = {}
    for level, count in counter.items():
        weight = DILTS_HIERARCHY.get(level, 1)
        weighted_scores[level] = count * weight
    
    logger.info(f"[DILTS_CALC] Weighted scores: {weighted_scores}")
    
    # Находим максимальный
    result = max(weighted_scores, key=weighted_scores.get)
    
    # 4. ФИНАЛЬНАЯ КОРРЕКЦИЯ на основе уровня мышления
    result = correct_dilts_by_level(result, final_level)
    
    logger.info(f"[DILTS_CALC] ✓ Final result: {result}")
    return result


def correct_dilts_by_level(dilts_level, thinking_level):
    """
    Корректирует уровень Дилтса на основе уровня мышления
    
    Правила:
    - Уровни 1-2: максимум BEHAVIOR
    - Уровни 3-5: максимум CAPABILITIES
    - Уровни 6-7: максимум VALUES
    - Уровни 8-9: любой уровень
    """
    # Иерархия Дилтса (от низшего к высшему)
    hierarchy = ["ENVIRONMENT", "BEHAVIOR", "CAPABILITIES", "VALUES", "IDENTITY"]
    
    # Определяем максимально допустимый уровень Дилтса
    if thinking_level <= 2:
        max_allowed = "BEHAVIOR"
    elif thinking_level <= 5:
        max_allowed = "CAPABILITIES"
    elif thinking_level <= 7:
        max_allowed = "VALUES"
    else:
        max_allowed = "IDENTITY"
    
    # Если текущий уровень Дилтса выше допустимого → снижаем
    if hierarchy.index(dilts_level) > hierarchy.index(max_allowed):
        logger.info(f"[DILTS_CORRECT] {dilts_level} → {max_allowed} (level {thinking_level})")
        return max_allowed
    
    return dilts_level


def calculate_profile_code(perception_type, final_level, dilts_level):
    """
    ОПТИМИЗИРОВАННОЕ вычисление кода профиля
    
    Формат: TYPE_LEVEL_DILTS
    Пример: SP_3_beh, IA_7_val
    
    Returns:
        str: Код профиля (например, "SP_3_beh")
    """
    # Маппинг типов восприятия
    type_map = {
        "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "SA",
        "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "IA",
        "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "SP",
        "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "IP"
    }
    
    # Маппинг уровней Дилтса
    dilts_map = {
        "ENVIRONMENT": "env",
        "BEHAVIOR": "beh",
        "CAPABILITIES": "cap",
        "VALUES": "val",
        "IDENTITY": "ide",
        "MISSION": "mis"
    }
    
    type_code = type_map.get(perception_type, "SA")
    dilts_code = dilts_map.get(dilts_level, "env")
    
    profile_code = f"{type_code}_{final_level}_{dilts_code}"
    
    logger.info(f"[PROFILE_CODE] Type={perception_type} → {type_code}")
    logger.info(f"[PROFILE_CODE] Level={final_level}")
    logger.info(f"[PROFILE_CODE] Dilts={dilts_level} → {dilts_code}")
    logger.info(f"[PROFILE_CODE] ✓ Final code: {profile_code}")
    
    return profile_code


def validate_and_correct_profile(context_data):
    """
    ВАЛИДАЦИЯ и КОРРЕКЦИЯ профиля
    
    Проверяет логические противоречия и корректирует их:
    1. Высокий уровень + низкий Дилтс → повышаем Дилтс
    2. Низкий уровень + высокий Дилтс → понижаем Дилтс
    3. Большой разброс между этапами → усредняем
    
    Returns:
        dict: Скорректированные данные профиля
    """
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    final_level = context_data.get("final_level", 1)
    dilts_level = context_data.get("dilts_level", "ENVIRONMENT")
    
    logger.info(f"[VALIDATION] Initial: type={perception_type}, level={final_level}, dilts={dilts_level}")
    
    warnings = []
    corrected = False
    
    # Проверка 1: Высокий уровень (≥6) + ENVIRONMENT
    if final_level >= 6 and dilts_level == "ENVIRONMENT":
        warnings.append("High level + ENVIRONMENT → correcting to CAPABILITIES")
        dilts_level = "CAPABILITIES"
        corrected = True
    
    # Проверка 2: Низкий уровень (≤2) + высокий Дилтс (VALUES/IDENTITY)
    if final_level <= 2 and dilts_level in ["VALUES", "IDENTITY"]:
        warnings.append(f"Low level + {dilts_level} → correcting to BEHAVIOR")
        dilts_level = "BEHAVIOR"
        corrected = True
    
    # Проверка 3: Средний уровень (3-5) + IDENTITY
    if 3 <= final_level <= 5 and dilts_level == "IDENTITY":
        warnings.append("Mid level + IDENTITY → correcting to CAPABILITIES")
        dilts_level = "CAPABILITIES"
        corrected = True
    
    # Проверка 4: Разброс между этапами 2 и 3
    stage2_level = context_data.get("thinking_level", final_level)
    if abs(final_level - stage2_level) > 2:
        warnings.append(f"Large discrepancy: Stage2={stage2_level}, Final={final_level}")
        # Усредняем (но не корректируем, только предупреждаем)
    
    if warnings:
        logger.warning(f"[VALIDATION] Warnings: {warnings}")
        context_data["validation_warnings"] = warnings
    
    if corrected:
        context_data["dilts_level"] = dilts_level
        logger.info(f"[VALIDATION] ✓ Corrected: dilts={dilts_level}")
    else:
        logger.info(f"[VALIDATION] ✓ Profile OK")
    
    return context_data


# ============================================
# АДАПТИВНОСТЬ: УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================

def need_clarification_stage2(level_scores, perception_type):
    """
    Решает, нужны ли уточняющие вопросы для ЭТАПА 2
    
    Критерии:
    1. Разброс > 2 уровня
    2. Много средних баллов (3-4)
    3. Противоречивые ответы (первая половина ≠ вторая)
    
    Returns:
        (bool, list): (нужны ли вопросы, список индексов вопросов)
    """
    if len(level_scores) < 8:
        return (False, [])
    
    min_level = min(level_scores)
    max_level = max(level_scores)
    spread = max_level - min_level
    
    logger.info(f"[STAGE2_CLARIFY] Spread={spread}, Scores={level_scores}")
    
    # Критерий 1: Большой разброс (> 2)
    if spread > 2:
        target_questions = select_clarifying_questions_stage2(level_scores, perception_type)
        logger.info(f"[STAGE2_CLARIFY] ✓ Large spread → questions {target_questions}")
        return (True, target_questions)
    
    # Критерий 2: Много средних баллов (неопределённость)
    middle_scores = [s for s in level_scores if 3 <= s <= 4]
    if len(middle_scores) >= 5:
        target_questions = [0, 1, 2]  # Первые 3 вопроса
        logger.info(f"[STAGE2_CLARIFY] ✓ Many middle scores → questions {target_questions}")
        return (True, target_questions)
    
    # Критерий 3: Противоречивые ответы
    if len(level_scores) >= 8:
        first_half = level_scores[:4]
        second_half = level_scores[4:]
        avg_first = sum(first_half) / 4
        avg_second = sum(second_half) / 4
        
        if abs(avg_second - avg_first) > 2:
            target_questions = [3, 4, 5]  # Средние вопросы
            logger.info(f"[STAGE2_CLARIFY] ✓ Contradictory answers → questions {target_questions}")
            return (True, target_questions)
    
    logger.info(f"[STAGE2_CLARIFY] ✗ No clarification needed")
    return (False, [])


def select_clarifying_questions_stage2(level_scores, perception_type):
    """
    Выбирает целенаправленно 3-4 уточняющих вопроса для ЭТАПА 2
    
    Логика:
    - Анализирует частоту уровней
    - Выбирает вопросы для различения проблемных зон
    """
    min_level = min(level_scores)
    max_level = max(level_scores)
    
    level_counts = Counter(level_scores)
    
    low_levels = sum(1 for s in level_scores if s <= 2)
    high_levels = sum(1 for s in level_scores if s >= 5)
    
    selected = []
    
    logger.info(f"[STAGE2_SELECT] Low={low_levels}, High={high_levels}, Counts={dict(level_counts)}")
    
    # Зона 1: Низкие уровни (1-2)
    if low_levels >= 2:
        selected.append(0)
    
    # Зона 2: Средне-низкие уровни (2-3)
    if level_counts.get(2, 0) >= 2 or level_counts.get(3, 0) >= 2:
        selected.append(1)
    
    # Зона 3: Средние уровни (3-4)
    if level_counts.get(3, 0) >= 2 or level_counts.get(4, 0) >= 2:
        selected.append(2)
    
    # Зона 4: Средне-высокие уровни (4-5)
    if level_counts.get(4, 0) >= 2 or level_counts.get(5, 0) >= 2:
        selected.append(3)
    
    # Зона 5: Высокие уровни (5-6)
    if high_levels >= 2:
        selected.append(4)
    
    # Зона 6: Очень высокие уровни (6+)
    if max_level >= 6:
        selected.append(5)
    
    # Если выбрано меньше 3 вопросов, добавляем универсальные
    if len(selected) < 3:
        for i in range(6):
            if i not in selected:
                selected.append(i)
                if len(selected) >= 3:
                    break
    
    # Ограничиваем до 4 вопросов
    selected = selected[:4]
    
    logger.info(f"[STAGE2_SELECT] ✓ Selected questions: {selected}")
    return selected


def need_clarification_stage3(stage2_level, stage3_scores):
    """
    Решает, нужны ли уточняющие вопросы для ЭТАПА 3
    
    Критерий: Расхождение > 2 уровня между ЭТАПОМ 2 и ЭТАПОМ 3
    
    Returns:
        (bool, list): (нужны ли вопросы, список индексов вопросов)
    """
    if len(stage3_scores) < 8:
        return (False, [])
    
    stage3_level = calculate_thinking_level_optimized(stage3_scores)
    diff = abs(stage3_level - stage2_level)
    
    logger.info(f"[STAGE3_CLARIFY] Stage2={stage2_level}, Stage3={stage3_level}, Diff={diff}")
    
    # Если расхождение > 2 уровня → нужны уточняющие вопросы
    if diff > 2:
        selected = [0, 1, 2]  # Первые 3 уточняющих вопроса
        logger.info(f"[STAGE3_CLARIFY] ✓ Large discrepancy → questions {selected}")
        return (True, selected)
    
    logger.info(f"[STAGE3_CLARIFY] ✗ No clarification needed")
    return (False, [])


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
    """Определяет тип восприятия по баллам"""
    focus = "EXTERNAL" if scores.get("EXTERNAL", 0) > scores.get("INTERNAL", 0) else "INTERNAL"
    anxiety = "SYMBOLIC" if scores.get("SYMBOLIC", 0) > scores.get("MATERIAL", 0) else "MATERIAL"
    
    type_data = PERCEPTION_TYPES.get((focus, anxiety), PERCEPTION_TYPES[("EXTERNAL", "SYMBOLIC")])
    
    logger.info(f"[PERCEPTION] Focus={focus}, Anxiety={anxiety} → Type={type_data['name']}")
    return type_data["name"]


def log_user_data(user_id, stage, data):
    """Детальное логирование данных пользователя"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{timestamp}] User {user_id} | {stage} | {data}")


# ============================================
# КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    log_user_data(user.id, "START", {"username": user.username, "first_name": user.first_name})
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест!</b>\n\n"
        f"🔍 <b>Узнай свой текущий психологический профиль и получи персональные рекомендации для развития.</b>\n\n"
        f"Этот тест поможет определить:\n"
        f"• Как ты воспринимаешь реальность 🧠\n"
        f"• На каком уровне развития ты находишься 📊\n"
        f"• Какие поведенческие паттерны у тебя есть 🎯\n"
        f"• Где находится твоя точка роста 🚀\n\n"
        f"🎯 <b>Что тебя ждёт:</b>\n\n"
        f"1️⃣ <b>ЭТАП 1:</b> Конфигурация восприятия (8 вопросов)\n"
        f"2️⃣ <b>ЭТАП 2:</b> Конфигурация мышления (8-12 вопросов, адаптивно)\n"
        f"3️⃣ <b>ЭТАП 3:</b> Поведенческие паттерны (8-11 вопросов, адаптивно)\n"
        f"4️⃣ <b>ЭТАП 4:</b> Конфликт логических уровней (8 вопросов)\n\n"
        f"⏱ Займёт 12-18 минут\n\n"
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
    
    user_id = update.effective_user.id
    
    # ПОЛНАЯ ОЧИСТКА
    context.user_data.clear()
    
    # Инициализация
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_current"] = 0
    context.user_data["stage2_level_scores"] = []
    context.user_data["stage2_clarifying_mode"] = False
    context.user_data["stage2_clarifying_questions"] = []
    context.user_data["stage3_current"] = 0
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage3_clarifying_mode"] = False
    context.user_data["stage3_clarifying_questions"] = []
    context.user_data["stage4_current"] = 0
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["start_time"] = datetime.now()
    
    log_user_data(user_id, "TEST_START", {"timestamp": context.user_data["start_time"]})
    
    return await show_stage_1_intro(update, context)


# ============================================
# ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ
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
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage1_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 1", callback_data="start_stage_1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1


async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФИГУРАЦИЯ ВОСПРИЯТИЯ?</b>\n\n"
        f"Это базовая программа, через которую ты воспринимаешь мир.\n\n"
        f"<b>Мы измеряем две оси:</b>\n\n"
        f"<b>1. Направленность внимания:</b>\n"
        f"• ЭКСТЕРНАЛЬНАЯ — фокус на внешнем мире (люди, события)\n"
        f"• ИНТЕРНАЛЬНАЯ — фокус на внутреннем мире (мысли, чувства)\n\n"
        f"<b>2. Доминирующая тревога:</b>\n"
        f"• СИМВОЛИЧЕСКАЯ — страх отвержения, непонимания\n"
        f"• МАТЕРИАЛЬНАЯ — страх потери контроля, ресурсов\n\n"
        f"<b>Результат:</b> Один из четырёх типов восприятия\n\n"
        f"Это определит, какие вопросы ты получишь на следующих этапах."
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage1_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1


async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 1"""
    return await show_stage_1_intro(update, context)


async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage1_current"] = 0
    log_user_data(update.effective_user.id, "STAGE1_START", {})
    
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
        
        # Добавляем баллы
        for axis, score in selected_option.get("scores", {}).items():
            context.user_data["scores"][axis] += score
        
        log_user_data(
            update.effective_user.id, 
            f"STAGE1_Q{current+1}", 
            {"answer": option_id, "scores": selected_option.get("scores", {})}
        )
        
        context.user_data["stage1_current"] = current + 1
        return await ask_stage_1_question(update, context)
        
    finally:
        context.user_data["processing"] = False


async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 1"""
    query = update.callback_query
    
    scores = context.user_data.get("scores", {})
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    log_user_data(
        update.effective_user.id, 
        "STAGE1_COMPLETE", 
        {"scores": scores, "perception_type": perception_type}
    )
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Конфигурация восприятия определена</b>\n\n"
        f"Твой тип: <b>{perception_type}</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение конфигурации мышления.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2


# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ (АДАПТИВНЫЙ)
# ============================================

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Сейчас мы определим твой уровень когнитивной зрелости.\n\n"
        f"📊 <b>Вопросов:</b> 8-12 (адаптивно)\n"
        f"⏱ <b>Время:</b> ~4-6 минут\n\n"
        f"💡 <b>Адаптивность:</b> Если ответы неоднозначные, бот задаст дополнительные уточняющие вопросы.\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage2_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 2", callback_data="start_stage_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2


async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФИГУРАЦИЯ МЫШЛЕНИЯ?</b>\n\n"
        f"Это уровень развития твоего мышления внутри типа восприятия.\n\n"
        f"<b>9 уровней когнитивной зрелости:</b>\n\n"
        f"1️⃣ ДЕФИЦИТАРНЫЙ — базовая нужда не удовлетворена\n"
        f"2️⃣ ПОИСКОВЫЙ — активный поиск решения\n"
        f"3️⃣ КОНСТРУКТИВНЫЙ — создание стабильной базы\n"
        f"4️⃣ КРИЗИСНЫЙ — переосмысление достигнутого\n"
        f"5️⃣ ИНТЕГРАТИВНЫЙ — уверенное владение\n"
        f"6️⃣ АЛЬТРУИСТИЧЕСКИЙ — служение другим\n"
        f"7️⃣ МУДРЕЦКИЙ — глубокое понимание\n"
        f"8️⃣ СИСТЕМНЫЙ — управление на системном уровне\n"
        f"9️⃣ ТРАНСЦЕНДЕНТНЫЙ — выход за пределы\n\n"
        f"<b>Результат:</b> Твой текущий уровень развития"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2


async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 2"""
    return await show_stage_2_intro(update, context)


async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    context.user_data["stage2_clarifying_mode"] = False
    log_user_data(update.effective_user.id, "STAGE2_START", {})
    
    return await ask_stage_2_question(update, context)


async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2 (с адаптивностью)"""
    query = update.callback_query
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    current = context.user_data.get("stage2_current", 0)
    level_scores = context.user_data.get("stage2_level_scores", [])
    clarifying_mode = context.user_data.get("stage2_clarifying_mode", False)
    
    # Базовые вопросы
    base_questions = STAGE_2_BASE_QUESTIONS.get(perception_type, STAGE_2_BASE_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    
    # Проверка: закончились ли базовые вопросы?
    if not clarifying_mode and current >= len(base_questions):
        # Анализ: нужны ли уточняющие вопросы?
        need_clarify, target_indices = need_clarification_stage2(level_scores, perception_type)
        
        if need_clarify:
            # Переходим в режим уточняющих вопросов
            context.user_data["stage2_clarifying_mode"] = True
            context.user_data["stage2_clarifying_questions"] = target_indices
            context.user_data["stage2_current"] = 0
            
            log_user_data(
                update.effective_user.id, 
                "STAGE2_CLARIFYING_START", 
                {"target_questions": target_indices}
            )
            
            # Показываем переходный экран
            return await show_stage_2_clarifying_intro(update, context)
        else:
            # Уточняющие вопросы не нужны → завершаем этап
            return await finish_stage_2(update, context)
    
    # Определяем, какой вопрос задавать
    if clarifying_mode:
        # Уточняющие вопросы
        clarifying_questions = STAGE_2_CLARIFYING_QUESTIONS.get(perception_type, [])
        target_indices = context.user_data.get("stage2_clarifying_questions", [])
        
        if current >= len(target_indices):
            # Все уточняющие вопросы заданы
            return await finish_stage_2(update, context)
        
        question_index = target_indices[current]
        question = clarifying_questions[question_index]
        total_questions = len(base_questions) + len(target_indices)
        actual_current = len(base_questions) + current + 1
    else:
        # Базовые вопросы
        question = base_questions[current]
        total_questions = len(base_questions)
        actual_current = current + 1
    
    progress = calculate_progress(actual_current, total_questions)
    
    question_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage2_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2


async def show_stage_2_clarifying_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переходный экран перед уточняющими вопросами ЭТАПА 2"""
    query = update.callback_query
    
    target_count = len(context.user_data.get("stage2_clarifying_questions", []))
    
    intro_text = (
        f"<b>🔍 УТОЧНЯЮЩИЕ ВОПРОСЫ</b>\n\n"
        f"Твои ответы показали неоднозначность.\n\n"
        f"Задам ещё <b>{target_count} вопроса</b> для точного определения уровня.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="continue_stage_2_clarifying")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2


async def continue_stage_2_clarifying(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Продолжение после переходного экрана"""
    query = update.callback_query
    await query.answer()
    
    return await ask_stage_2_question(update, context)


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
        option_id = parts[2]
        
        perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
        clarifying_mode = context.user_data.get("stage2_clarifying_mode", False)
        
        if clarifying_mode:
            clarifying_questions = STAGE_2_CLARIFYING_QUESTIONS.get(perception_type, [])
            target_indices = context.user_data.get("stage2_clarifying_questions", [])
            question_index = target_indices[current]
            question = clarifying_questions[question_index]
        else:
            base_questions = STAGE_2_BASE_QUESTIONS.get(perception_type, STAGE_2_BASE_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
            question = base_questions[current]
        
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_2
        
        level = selected_option.get("level", 1)
        context.user_data["stage2_level_scores"].append(level)
        
        log_user_data(
            update.effective_user.id, 
            f"STAGE2_Q{current+1}_{'CLARIFY' if clarifying_mode else 'BASE'}", 
            {"answer": option_id, "level": level}
        )
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    finally:
        context.user_data["processing"] = False


async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2"""
    query = update.callback_query
    
    level_scores = context.user_data.get("stage2_level_scores", [])
    thinking_level = calculate_thinking_level_optimized(level_scores)
    context.user_data["thinking_level"] = thinking_level
    
    log_user_data(
        update.effective_user.id, 
        "STAGE2_COMPLETE", 
        {"level_scores": level_scores, "thinking_level": thinking_level}
    )
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Конфигурация мышления определена</b>\n\n"
        f"Твой уровень: <b>{thinking_level}</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3


# ============================================
# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ (АДАПТИВНЫЙ)
# ============================================

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"Сейчас мы уточним твой уровень через анализ автоматических реакций.\n\n"
        f"📊 <b>Вопросов:</b> 8-11 (адаптивно)\n"
        f"⏱ <b>Время:</b> ~3-5 минут\n\n"
        f"💡 <b>Адаптивность:</b> Если уровень из ЭТАПА 2 расходится с поведением, задам уточняющие вопросы.\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage3_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 3", callback_data="start_stage_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3


async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ?</b>\n\n"
        f"Это автоматические реакции в типичных ситуациях.\n\n"
        f"<b>Зачем это нужно:</b>\n\n"
        f"Человек может не осознавать свой уровень развития, но его поведение его выдаёт.\n\n"
        f"Мы зададим вопросы о реальных действиях (не о мнениях), чтобы уточнить твой уровень.\n\n"
        f"<b>Результат:</b> Подтверждение или корректировка уровня из ЭТАПА 2"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3


async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 3"""
    return await show_stage_3_intro(update, context)


async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    context.user_data["stage3_clarifying_mode"] = False
    log_user_data(update.effective_user.id, "STAGE3_START", {})
    
    return await ask_stage_3_question(update, context)


async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3 (с адаптивностью)"""
    query = update.callback_query
    
    current = context.user_data.get("stage3_current", 0)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    clarifying_mode = context.user_data.get("stage3_clarifying_mode", False)
    stage2_level = context.user_data.get("thinking_level", 1)
    
    # Базовые вопросы
    base_questions = STAGE_3_BASE_QUESTIONS
    
    # Проверка: закончились ли базовые вопросы?
    if not clarifying_mode and current >= len(base_questions):
        # Анализ: нужны ли уточняющие вопросы?
        need_clarify, target_indices = need_clarification_stage3(stage2_level, stage3_scores)
        
        if need_clarify:
            # Переходим в режим уточняющих вопросов
            context.user_data["stage3_clarifying_mode"] = True
            context.user_data["stage3_clarifying_questions"] = target_indices
            context.user_data["stage3_current"] = 0
            
            log_user_data(
                update.effective_user.id, 
                "STAGE3_CLARIFYING_START", 
                {"target_questions": target_indices}
            )
            
            # Показываем переходный экран
            return await show_stage_3_clarifying_intro(update, context)
        else:
            # Уточняющие вопросы не нужны → завершаем этап
            return await finish_stage_3(update, context)
    
    # Определяем, какой вопрос задавать
    if clarifying_mode:
        # Уточняющие вопросы
        clarifying_questions = STAGE_3_CLARIFYING_QUESTIONS
        target_indices = context.user_data.get("stage3_clarifying_questions", [])
        
        if current >= len(target_indices):
            # Все уточняющие вопросы заданы
            return await finish_stage_3(update, context)
        
        question_index = target_indices[current]
        question = clarifying_questions[question_index]
        total_questions = len(base_questions) + len(target_indices)
        actual_current = len(base_questions) + current + 1
    else:
        # Базовые вопросы
        question = base_questions[current]
        total_questions = len(base_questions)
        actual_current = current + 1
    
    progress = calculate_progress(actual_current, total_questions)
    
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


async def show_stage_3_clarifying_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переходный экран перед уточняющими вопросами ЭТАПА 3"""
    query = update.callback_query
    
    target_count = len(context.user_data.get("stage3_clarifying_questions", []))
    
    intro_text = (
        f"<b>🔍 УТОЧНЯЮЩИЕ ВОПРОСЫ</b>\n\n"
        f"Твои ответы расходятся с ЭТАПОМ 2.\n\n"
        f"Задам ещё <b>{target_count} вопроса</b> для точного определения уровня.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="continue_stage_3_clarifying")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3


async def continue_stage_3_clarifying(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Продолжение после переходного экрана"""
    query = update.callback_query
    await query.answer()
    
    return await ask_stage_3_question(update, context)


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
        
        clarifying_mode = context.user_data.get("stage3_clarifying_mode", False)
        
        if clarifying_mode:
            clarifying_questions = STAGE_3_CLARIFYING_QUESTIONS
            target_indices = context.user_data.get("stage3_clarifying_questions", [])
            question_index = target_indices[current]
            question = clarifying_questions[question_index]
        else:
            base_questions = STAGE_3_BASE_QUESTIONS
            question = base_questions[current]
        
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_3
        
        level = selected_option.get("level", 1)
        context.user_data["stage3_level_scores"].append(level)
        
        log_user_data(
            update.effective_user.id, 
            f"STAGE3_Q{current+1}_{'CLARIFY' if clarifying_mode else 'BASE'}", 
            {"answer": option_id, "level": level}
        )
        
        context.user_data["stage3_current"] = current + 1
        return await ask_stage_3_question(update, context)
        
    finally:
        context.user_data["processing"] = False


async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3"""
    query = update.callback_query
    
    # Корректировка уровня на основе поведенческих паттернов
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    stage3_level = calculate_thinking_level_optimized(stage3_scores)
    
    # Если расхождение больше 1 уровня, корректируем
    if abs(stage3_level - stage2_level) > 1:
        final_level = int((stage2_level + stage3_level) / 2)
        logger.info(f"[STAGE3] Level adjusted: stage2={stage2_level}, stage3={stage3_level}, final={final_level}")
    else:
        final_level = stage2_level
        logger.info(f"[STAGE3] Level confirmed: final={final_level}")
    
    context.user_data["final_level"] = final_level
    
    log_user_data(
        update.effective_user.id, 
        "STAGE3_COMPLETE", 
        {"stage3_scores": stage3_scores, "stage3_level": stage3_level, "final_level": final_level}
    )
    
    result_text = (
        f"✅ <b>ЭТАП 3 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Поведенческие паттерны проанализированы</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 4</b>: конфликт логических уровней.\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4


# ============================================
# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"Сейчас мы определим, на каком уровне находится твоя точка роста.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 4", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4


async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ?</b>\n\n"
        f"Это модель Роберта Дилтса, которая показывает, на каком уровне находится проблема.\n\n"
        f"<b>6 уровней (снизу вверх):</b>\n\n"
        f"1️⃣ ОКРУЖЕНИЕ — внешние условия\n"
        f"2️⃣ ПОВЕДЕНИЕ — твои действия\n"
        f"3️⃣ СПОСОБНОСТИ — твои навыки\n"
        f"4️⃣ ЦЕННОСТИ — твои мотивы\n"
        f"5️⃣ ИДЕНТИЧНОСТЬ — кто ты\n"
        f"6️⃣ МИССИЯ — зачем ты в мире\n\n"
        f"<b>Принцип:</b> Проблема на нижнем уровне решается изменением верхнего.\n\n"
        f"<b>Результат:</b> Твой проблемный уровень + вектор развития"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4


async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 4"""
    return await show_stage_4_intro(update, context)


async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    log_user_data(update.effective_user.id, "STAGE4_START", {})
    
    return await ask_stage_4_question(update, context)


async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    
    current = context.user_data.get("stage4_current", 0)
    
    if current >= len(STAGE_4_QUESTIONS):
        return await finish_stage_4(update, context)
    
    question = STAGE_4_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_4_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
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
        
        question = STAGE_4_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_4
        
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        log_user_data(
            update.effective_user.id, 
            f"STAGE4_Q{current+1}", 
            {"answer": option_id, "dilts": dilts}
        )
        
        context.user_data["stage4_current"] = current + 1
        return await ask_stage_4_question(update, context)
        
    finally:
        context.user_data["processing"] = False


async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 и показ результата"""
    query = update.callback_query
    
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    final_level = context.user_data.get("final_level", 1)
    
    # УМНОЕ определение уровня Дилтса с учётом уровня мышления
    dilts_level = determine_dilts_level_smart(final_level, dilts_answers)
    context.user_data["dilts_level"] = dilts_level
    
    log_user_data(
        update.effective_user.id, 
        "STAGE4_COMPLETE", 
        {"dilts_answers": dilts_answers, "dilts_level": dilts_level}
    )
    
    # Валидация и коррекция профиля
    context.user_data = validate_and_correct_profile(context.user_data)
    
    return await show_result(update, context)


# ============================================
# РЕЗУЛЬТАТ
# ============================================

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ финального результата с использованием card_data.py"""
    query = update.callback_query
    
    # Получаем данные профиля
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    final_level = context.user_data.get("final_level", 1)
    dilts_level = context.user_data.get("dilts_level", "ENVIRONMENT")
    
    # Вычисляем код профиля
    profile_code = calculate_profile_code(perception_type, final_level, dilts_level)
    
    # ПОЛУЧАЕМ ОПИСАНИЕ ИЗ CARD_DATA.PY
    try:
        profile_description = get_profile_description(profile_code)
    except Exception as e:
        logger.error(f"Error getting profile description: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка при получении описания профиля. Попробуй начать заново: /start"
        )
        return ConversationHandler.END
    
    # Получаем описание уровня Дилтса
    dilts_info = DILTS_LEVELS.get(dilts_level, DILTS_LEVELS["ENVIRONMENT"])
    
    log_user_data(
        update.effective_user.id, 
        "RESULT_SHOWN", 
        {"profile_code": profile_code, "final_level": final_level, "dilts_level": dilts_level}
    )
    
    # ФОРМИРУЕМ ИТОГОВЫЙ ЭКРАН
    result_text = (
        f"🎉 <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>📊 ТВОЙ ПРОФИЛЬ:</b>\n\n"
        f"{profile_description}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>🎪 Проблемный уровень:</b>\n{dilts_info['name']}\n"
        f"<i>{dilts_info['description']}</i>\n\n"
        f"<b>🚀 ВЕКТОР РАЗВИТИЯ:</b>\n"
        f"{dilts_info['solution']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>🔑 Код профиля:</b> <code>{profile_code}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 <b>РАБОЧИЙ ИНСТРУМЕНТ КОРРЕКЦИИ</b>\n\n"
        f"💡 Твой инструмент который корректирует конфигурацию поведения, на уровне конфигурации мышления – это метафорическая форма (ссылка на сказку внизу экрана).\n\n"
        f"💎 <b>ПОЛНЫЙ ПАКЕТ (960 ₽)</b>\n"
        f"✓ Полное описание архетипа и персональные рекомендации (15+ страниц)\n"
        f"✓ Персональная терапевтическая сказка для коррекции других конфликтующих частей\n"
        f"✓ Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (pdf) для самостоятельной коррекции на уровне конфигурации восприятия\n\n"
        f"💬 <b>Хочешь разобраться глубже?</b>\n"
        f"Получить персональную консультацию:\n"
        f"👉 @meysternlp"
    )
    
    story_link = "https://drive.google.com/file/d/1Y0nr2C_sWlQVOF84THLXa3nflFBVSI77/view?usp=sharing"
    bot_link = "https://t.me/Testing_Lichnosti_bot"
    
    keyboard = [
        [InlineKeyboardButton("📖 Читать сказку", url=story_link)],
        [InlineKeyboardButton("💳 Получить полный пакет (960 ₽)", url="https://t.me/meysternlp")],
        [InlineKeyboardButton("🎁 Поделиться тестом", url=f"https://t.me/share/url?url={bot_link}&text=Пройди тест и узнай свой психотип!")],
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_text, 
        reply_markup=reply_markup, 
        parse_mode="HTML", 
        disable_web_page_preview=True
    )
    
    # Очистка данных после завершения
    context.user_data.clear()
    
    return ConversationHandler.END


# ============================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    cancel_text = (
        f"❌ Тест отменён.\n"
        f"Хочешь начать заново?\n"
        f"👉 /start"
    )
    await update.message.reply_text(cancel_text)
    context.user_data.clear()
    return ConversationHandler.END


async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка таймаута"""
    if update.effective_message:
        await update.effective_message.reply_text(
            "⏱ Время сеанса истекло.\n"
            "Начни тест заново: /start"
        )
    context.user_data.clear()
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Exception: {context.error}", exc_info=context.error)
    
    if update and hasattr(update, 'effective_message'):
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуй начать заново: /start"
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    if hasattr(context, 'user_data') and context.user_data:
        context.user_data.clear()


# ============================================
# MAIN
# ============================================

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(show_stage_1_intro, pattern="^show_stage_1_intro$"),
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
                CallbackQueryHandler(continue_stage_2_clarifying, pattern="^continue_stage_2_clarifying$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(show_stage_3_intro, pattern="^show_stage_3_intro$"),
                CallbackQueryHandler(show_stage_3_details, pattern="^stage3_details$"),
                CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$"),
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(continue_stage_3_clarifying, pattern="^continue_stage_3_clarifying$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4: [
                CallbackQueryHandler(show_stage_4_intro, pattern="^show_stage_4_intro$"),
                CallbackQueryHandler(show_stage_4_details, pattern="^stage4_details$"),
                CallbackQueryHandler(back_to_stage4_intro, pattern="^back_to_stage4_intro$"),
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, timeout_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        conversation_timeout=1800,
        allow_reentry=True,
        per_message=False
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен! (Версия 3.0 - Оптимизированный алгоритм)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
