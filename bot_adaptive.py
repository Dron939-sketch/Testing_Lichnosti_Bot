# bot_adaptive.py
"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
3 этапа:
1. Определение конфигурации восприятия (6 адаптивных вопросов)
2. Определение конфигурации мышления (10 вопросов)
3. Определение стыка конфликтных частей (6 вопросов)
"""

import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

# Импорты вопросов
from adaptive_questions import STAGE_1_ADAPTIVE
from stage2_questions import STAGE_2_QUESTIONS
from stage3_questions import STAGE_3_BASE_QUESTIONS
from card_data import CARDS

# Получение токена из переменной окружения
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
STAGE_1, STAGE_2, STAGE_3, RESULT = range(4)

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%\nПройдено: {current}/{total}"

def calculate_suit(scores):
    """Определяет масть по баллам"""
    focus = "ВОВНЕ" if scores.get("ВОВНЕ", 0) > scores.get("ВНУТРИ", 0) else "ВНУТРИ"
    fear = "УМОЗРИТЕЛЬНОЕ" if scores.get("УМОЗРИТЕЛЬНОЕ", 0) > scores.get("ФАКТИЧЕСКОЕ", 0) else "ФАКТИЧЕСКОЕ"
    
    suit_map = {
        ("ВОВНЕ", "УМОЗРИТЕЛЬНОЕ"): "♣️ ТРЕФЫ",
        ("ВНУТРИ", "УМОЗРИТЕЛЬНОЕ"): "♥️ ЧЕРВИ",
        ("ВОВНЕ", "ФАКТИЧЕСКОЕ"): "♦️ БУБНЫ",
        ("ВНУТРИ", "ФАКТИЧЕСКОЕ"): "♠️ ПИКИ"
    }
    
    return suit_map.get((focus, fear), "♣️ ТРЕФЫ")

def calculate_card_level(level_score):
    """Определяет уровень карты по баллам (6-14)"""
    if level_score <= 2:
        return 6
    elif level_score <= 4:
        return 7
    elif level_score <= 6:
        return 8
    elif level_score <= 8:
        return 9
    elif level_score <= 10:
        return 10
    elif level_score <= 12:
        return 11  # Jack
    elif level_score <= 14:
        return 12  # Queen
    elif level_score <= 16:
        return 13  # King
    else:
        return 14  # Ace

def get_card_name(level):
    """Преобразует уровень в название карты"""
    card_names = {
        6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
        11: "J", 12: "Q", 13: "K", 14: "A"
    }
    return card_names.get(level, "6")

def calculate_dilts_level(dilts_answers):
    """Определяет проблемный уровень Дилтса"""
    from collections import Counter
    counter = Counter(dilts_answers)
    
    if counter:
        return counter.most_common(1)[0][0]
    return "ОКРУЖЕНИЕ"

# ============================================
# КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - ОБНОВЛЁННАЯ"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в диагностику архетипов!</b>\n\n"
        f"🔍 <b>Узнай, почему ты принимаешь именно такие решения и какие варианты еще есть, но ты их не замечаешь и почему?</b>\n\n"
        f"Этот тест поможет определить твой текущий архетип и понять:\n"
        f"• Почему ты реагируешь именно так и на какие триггеры 🤔\n"
        f"• Откуда берутся твои страхи и желания 💭\n"
        f"• Как изменить то, что тебя не устраивает 🚀\n\n"
        f"🎯 <b>Что тебя ждёт:</b>\n\n"
        f"1️⃣ <b>ЭТАП 1:</b> Определение конфигурации восприятия (6 вопросов)\n"
        f"→ Узнаешь свою базовую программу\n\n"
        f"2️⃣ <b>ЭТАП 2:</b> Определение конфигурации мышления (10 вопросов)\n"
        f"→ Найдём твою текущую программу\n\n"
        f"3️⃣ <b>ЭТАП 3:</b> Определение стыка конфликтных частей (6 вопросов)\n"
        f"→ Определим поведенческие паттерны и методы их коррекции\n\n"
        f"⏱ Займёт 10-15 минут\n\n"
        f"📌 Отвечай честно, как есть сейчас, а не как хотелось бы.\n\n"
        f"Готов начать? 🚀"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста С ЗАЩИТОЙ ОТ ЗАВИСАНИЙ"""
    query = update.callback_query
    await query.answer()
    
    # ПОЛНАЯ ОЧИСТКА ДАННЫХ
    context.user_data.clear()
    
    # Инициализация данных пользователя
    context.user_data["scores"] = {}
    context.user_data["answer_history"] = []
    context.user_data["current_question_id"] = "q1_focus"
    context.user_data["stage2_answers"] = []
    context.user_data["stage3_answers"] = []
    context.user_data["total_questions"] = 0
    context.user_data["processing"] = False
    context.user_data["started_at"] = asyncio.get_event_loop().time()
    
    logger.info(f"User {update.effective_user.id} started test")
    
    # Переход к первому вопросу
    return await ask_adaptive_question(update, context)

# ============================================
# ЭТАП 1: АДАПТИВНЫЕ ВОПРОСЫ
# ============================================

async def ask_adaptive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт адаптивный вопрос ЭТАПА 1"""
    query = update.callback_query
    
    current_q_id = context.user_data.get("current_question_id", "q1_focus")
    question = STAGE_1_ADAPTIVE.get(current_q_id)
    
    if not question:
        logger.info(f"User {update.effective_user.id}: Finishing stage 1")
        return await finish_stage_1(update, context)
    
    # Подсчёт текущего вопроса
    context.user_data["total_questions"] = context.user_data.get("total_questions", 0) + 1
    current_num = context.user_data["total_questions"]
    
    # Прогресс-бар
    progress = calculate_progress(current_num, 6)
    
    question_text = (
        f"<b>{question['stage']}</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        # УБИРАЕМ ВСЕ ЭМОДЗИ ИЗ ТЕКСТА КНОПОК
        clean_text = option["text"].replace("🎯", "").replace("💪", "").replace("🧠", "").replace("❤️", "").strip()
        keyboard.append([
            InlineKeyboardButton(
                clean_text, 
                callback_data=f"adaptive_{current_q_id}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def handle_adaptive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка адаптивного ответа ЭТАПА 1 С ЗАЩИТОЙ ОТ ДУБЛИРОВАНИЯ"""
    query = update.callback_query
    
    # ЗАЩИТА ОТ ПОВТОРНЫХ НАЖАТИЙ
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_1
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_1
        
        question_id = "_".join(parts[1:-1])
        option_id = parts[-1]
        
        question = STAGE_1_ADAPTIVE.get(question_id)
        if not question:
            return STAGE_1
        
        selected_option = question["options"].get(option_id)
        if not selected_option:
            return STAGE_1
        
        for axis, score in selected_option.get("scores", {}).items():
            context.user_data["scores"][axis] = context.user_data["scores"].get(axis, 0) + score
        
        context.user_data["answer_history"].append({
            "question_id": question_id,
            "option_id": option_id,
            "text": selected_option["text"]
        })
        
        logger.info(f"User {update.effective_user.id}: Answered {question_id} -> {option_id}")
        
        next_q_id = selected_option.get("next")
        
        if next_q_id == "finish_stage_1":
            return await finish_stage_1(update, context)
        
        context.user_data["current_question_id"] = next_q_id
        return await ask_adaptive_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 1 - КОМПАКТНЫЙ ТЕКСТ"""
    query = update.callback_query
    
    scores = context.user_data.get("scores", {})
    suit = calculate_suit(scores)
    context.user_data["suit"] = suit
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, suit={suit}")
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Конфигурация восприятия определена</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение конфигурации мышления.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Начать ЭТАП 2", callback_data="start_stage_2")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

# ============================================
# ЭТАП 2: ОПРЕДЕЛЕНИЕ УРОВНЯ
# ============================================

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    context.user_data["stage2_level_score"] = 0
    context.user_data["processing"] = False
    
    logger.info(f"User {update.effective_user.id}: Starting stage 2")
    
    return await ask_stage2_question(update, context)

async def ask_stage2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    
    suit = context.user_data.get("suit")
    current = context.user_data.get("stage2_current", 0)
    
    questions = STAGE_2_QUESTIONS.get(suit, [])
    
    if current >= len(questions):
        return await finish_stage_2(update, context)
    
    question = questions[current]
    
    # Прогресс-бар
    progress = calculate_progress(current + 1, len(questions))
    
    question_text = (
        f"<b>🎯 ЭТАП 2: ОПРЕДЕЛЕНИЕ КОНФИГУРАЦИИ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        # УБИРАЕМ ВСЕ ЭМОДЗИ ИЗ ТЕКСТА КНОПОК
        clean_text = option["text"].replace("🎯", "").replace("💪", "").replace("🧠", "").replace("❤️", "").replace("⚡", "").replace("🌟", "").strip()
        keyboard.append([
            InlineKeyboardButton(
                clean_text, 
                callback_data=f"stage2_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def handle_stage2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2 С ЗАЩИТОЙ ОТ ДУБЛИРОВАНИЯ"""
    query = update.callback_query
    
    # ЗАЩИТА ОТ ПОВТОРНЫХ НАЖАТИЙ
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
        
        suit = context.user_data.get("suit")
        questions = STAGE_2_QUESTIONS.get(suit, [])
        
        if current >= len(questions):
            return STAGE_2
        
        question = questions[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_2
        
        level_score = selected_option.get("level_score", 0)
        context.user_data["stage2_level_score"] = context.user_data.get("stage2_level_score", 0) + level_score
        
        context.user_data["stage2_answers"].append({
            "question": question["text"],
            "answer": selected_option["text"],
            "score": level_score
        })
        
        logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> {option_id}")
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage2_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2 - КОМПАКТНЫЙ ТЕКСТ"""
    query = update.callback_query
    
    suit = context.user_data.get("suit")
    level_score = context.user_data.get("stage2_level_score", 0)
    
    card_level = calculate_card_level(level_score)
    card_name = get_card_name(card_level)
    
    suit_symbol = suit.split()[0]
    full_card = f"{card_name}{suit_symbol}"
    context.user_data["card"] = full_card
    context.user_data["card_level"] = card_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, card={full_card}")
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Конфигурация мышления определена</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: определение стыка конфликтных частей.\n\n"
        f"Готов?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Начать ЭТАП 3", callback_data="start_stage_3")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

# ============================================
# ЭТАП 3: ОПРЕДЕЛЕНИЕ ПРОБЛЕМНОГО УРОВНЯ
# ============================================

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    context.user_data["stage3_dilts_answers"] = []
    context.user_data["processing"] = False
    
    logger.info(f"User {update.effective_user.id}: Starting stage 3")
    
    return await ask_stage3_question(update, context)

async def ask_stage3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    
    current = context.user_data.get("stage3_current", 0)
    questions = STAGE_3_BASE_QUESTIONS
    
    if current >= len(questions):
        return await finish_stage_3(update, context)
    
    question = questions[current]
    
    # Прогресс-бар
    progress = calculate_progress(current + 1, len(questions))
    
    question_text = (
        f"<b>🎯 ЭТАП 3: СТЫК КОНФЛИКТНЫХ ЧАСТЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        # УБИРАЕМ ВСЕ ЭМОДЗИ ИЗ ТЕКСТА КНОПОК
        clean_text = option["text"].replace("🎯", "").replace("💪", "").replace("🧠", "").replace("❤️", "").replace("⚡", "").replace("🌟", "").strip()
        keyboard.append([
            InlineKeyboardButton(
                clean_text, 
                callback_data=f"stage3_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def handle_stage3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3 С ЗАЩИТОЙ ОТ ДУБЛИРОВАНИЯ"""
    query = update.callback_query
    
    # ЗАЩИТА ОТ ПОВТОРНЫХ НАЖАТИЙ
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
        
        questions = STAGE_3_BASE_QUESTIONS
        
        if current >= len(questions):
            return STAGE_3
        
        question = questions[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_3
        
        dilts_level = selected_option.get("dilts")
        context.user_data["stage3_dilts_answers"].append(dilts_level)
        
        context.user_data["stage3_answers"].append({
            "question": question["text"],
            "answer": selected_option["text"],
            "dilts": dilts_level
        })
        
        logger.info(f"User {update.effective_user.id}: Stage 3 Q{current} -> {option_id}")
        
        context.user_data["stage3_current"] = current + 1
        return await ask_stage3_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3 и показ результата"""
    query = update.callback_query
    
    dilts_answers = context.user_data.get("stage3_dilts_answers", [])
    dilts_level = calculate_dilts_level(dilts_answers)
    context.user_data["dilts_level"] = dilts_level
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, dilts={dilts_level}")
    
    return await show_result(update, context)

# ============================================
# РЕЗУЛЬТАТ
# ============================================

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ финального результата С ПОЛНЫМИ ДАННЫМИ"""
    query = update.callback_query
    
    card = context.user_data.get("card", "?")
    card_data = CARDS.get(card, {})
    
    logger.info(f"User {update.effective_user.id}: Showing result for card={card}")
    
    # ПРОВЕРКА НАЛИЧИЯ ДАННЫХ
    if not card_data:
        error_text = (
            f"⚠️ Произошла ошибка при определении архетипа.\n"
            f"Пожалуйста, пройдите тест заново:\n"
            f"👉 /start"
        )
        keyboard = [[InlineKeyboardButton("🔄 Пройти заново", callback_data="start_test")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode="HTML")
        return ConversationHandler.END
    
    # РЕЗУЛЬТАТ С ПОЛНЫМИ ДАННЫМИ
    result_text = (
        f"🎉 <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"📖 <b>Описание вашей конфигурации мышления и поведения</b>\n\n"
        f"👤 <b>КТО ТЫ</b>\n"
        f"{card_data.get('who', card_data.get('description', 'Описание отсутствует'))}\n\n"
        f"💭 <b>НАРРАТИВ</b>\n"
        f"{card_data.get('narrative', card_data.get('archetype', 'Нарратив отсутствует'))}\n\n"
        f"🌑 <b>ТЕНЬ</b>\n"
        f"{card_data.get('shadow', 'Описание тени отсутствует')}\n\n"
        f"⚠️ <b>ЛОВУШКА</b>\n"
        f"{card_data.get('trap', 'Описание ловушки отсутствует')}\n\n"
        f"✅ <b>ЧТО ДЕЛАТЬ</b>\n"
        f"{card_data.get('what_to_do', 'Рекомендации отсутствуют')}\n\n"
        f"🚀 <b>КАК РАСТИ</b>\n"
        f"{card_data.get('how_to_grow', 'Рекомендации по росту отсутствуют')}\n\n"
        f"⚡ <b>ТРИГГЕР ПЕРЕХОДА</b>\n"
        f"{card_data.get('trigger', 'Триггер не определён')}\n\n"
        f"💰 <b>ДЕНЬГИ</b>\n"
        f"{card_data.get('money', 'Информация о деньгах отсутствует')}\n\n"
        f"📚 <b>РАБОЧИЙ ИНСТРУМЕНТ КОРРЕКЦИИ</b>\n"
        f"💡 Твой инструмент который корректирует конфигурацию поведения, на уровне конфигурации мышления – это метафорическая форма.\n\n"
        f"💎 <b>ПОЛНЫЙ ПАКЕТ (960 ₽)</b>\n"
        f"✓ Полное описание архетипа и персональные рекомендации (15+ страниц)\n"
        f"✓ Персональная терапевтическая сказка для коррекции других конфликтующих частей\n"
        f"✓ Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (pdf) для самостоятельной коррекции на уровне конфигурации восприятия\n\n"
        f"💬 <b>Хочешь разобраться глубже?</b>\n"
        f"Получить персональную консультацию:\n"
        f"👉 @meysternlp"
    )
    
    # Если текст слишком длинный, разбиваем на 2 части
    if len(result_text) > 4096:
        part1 = (
            f"🎉 <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
            f"📖 <b>Описание вашей конфигурации мышления и поведения</b>\n\n"
            f"👤 <b>КТО ТЫ</b>\n"
            f"{card_data.get('who', card_data.get('description', 'Описание отсутствует'))}\n\n"
            f"💭 <b>НАРРАТИВ</b>\n"
            f"{card_data.get('narrative', card_data.get('archetype', 'Нарратив отсутствует'))}\n\n"
            f"🌑 <b>ТЕНЬ</b>\n"
            f"{card_data.get('shadow', 'Описание тени отсутствует')}\n\n"
            f"⚠️ <b>ЛОВУШКА</b>\n"
            f"{card_data.get('trap', 'Описание ловушки отсутствует')}"
        )
        
        part2 = (
            f"✅ <b>ЧТО ДЕЛАТЬ</b>\n"
            f"{card_data.get('what_to_do', 'Рекомендации отсутствуют')}\n\n"
            f"🚀 <b>КАК РАСТИ</b>\n"
            f"{card_data.get('how_to_grow', 'Рекомендации по росту отсутствуют')}\n\n"
            f"⚡ <b>ТРИГГЕР ПЕРЕХОДА</b>\n"
            f"{card_data.get('trigger', 'Триггер не определён')}\n\n"
            f"💰 <b>ДЕНЬГИ</b>\n"
            f"{card_data.get('money', 'Информация о деньгах отсутствует')}\n\n"
            f"📚 <b>РАБОЧИЙ ИНСТРУМЕНТ КОРРЕКЦИИ</b>\n"
            f"💡 Твой инструмент который корректирует конфигурацию поведения, на уровне конфигурации мышления – это метафорическая форма.\n\n"
            f"💎 <b>ПОЛНЫЙ ПАКЕТ (960 ₽)</b>\n"
            f"✓ Полное описание архетипа и персональные рекомендации (15+ страниц)\n"
            f"✓ Персональная терапевтическая сказка для коррекции других конфликтующих частей\n"
            f"✓ Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (pdf) для самостоятельной коррекции на уровне конфигурации восприятия\n\n"
            f"💬 <b>Хочешь разобраться глубже?</b>\n"
            f"Получить персональную консультацию:\n"
            f"👉 @meysternlp"
        )
        
        await query.message.reply_text(part1, parse_mode="HTML")
        
        keyboard = [
            [InlineKeyboardButton("📖 Читать сказку", url=card_data.get('link', 'https://t.me/meysternlp'))],
            [InlineKeyboardButton("💳 Получить полный пакет (960 ₽)", url="https://t.me/meysternlp")],
            [InlineKeyboardButton("📤 Поделиться тестом", url="https://t.me/share/url?url=https://t.me/YOUR_BOT&text=Пройди тест и узнай свой архетип!")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(part2, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
    else:
        keyboard = [
            [InlineKeyboardButton("📖 Читать сказку", url=card_data.get('link', 'https://t.me/meysternlp'))],
            [InlineKeyboardButton("💳 Получить полный пакет (960 ₽)", url="https://t.me/meysternlp")],
            [InlineKeyboardButton("📤 Поделиться тестом", url="https://t.me/share/url?url=https://t.me/YOUR_BOT&text=Пройди тест и узнай свой архетип!")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(result_text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
    
    await query.delete_message()
    
    # Очистка данных после завершения
    context.user_data.clear()
    
    return ConversationHandler.END

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

# ============================================
# ERROR HANDLER
# ============================================

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
    
    # Очистка данных пользователя
    if hasattr(context, 'user_data') and context.user_data:
        context.user_data.clear()

# ============================================
# MAIN
# ============================================

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # ConversationHandler С ТАЙМАУТОМ
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(handle_adaptive_answer, pattern="^adaptive_")
            ],
            STAGE_2: [
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(handle_stage2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(handle_stage3_answer, pattern="^stage3_")
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, timeout_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        conversation_timeout=1800,  # 30 минут
        allow_reentry=True,
        per_message=False
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
