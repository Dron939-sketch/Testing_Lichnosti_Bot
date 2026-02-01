# bot_adaptive.py
"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ КАРТЫ РОЖДЕНИЯ
3 этапа:
1. Определение масти (6 адаптивных вопросов)
2. Определение уровня (10 вопросов под масть)
3. Определение проблемного уровня Дилтса (6 вопросов)
"""

import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
from dotenv import load_dotenv

# Импорты вопросов
from adaptive_questions import STAGE_1_ADAPTIVE, SUIT_DESCRIPTIONS
from stage2_questions import STAGE_2_QUESTIONS
from stage3_questions import STAGE_3_BASE_QUESTIONS
from card_data import CARDS  # Старые данные карт для финального результата

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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
    # level_score от 0 до 20 (10 вопросов * 2 балла макс)
    # Распределяем на 9 уровней: 6, 7, 8, 9, 10, J(11), Q(12), K(13), A(14)
    
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
    # Подсчитываем частоту каждого уровня
    from collections import Counter
    counter = Counter(dilts_answers)
    
    # Возвращаем самый частый
    if counter:
        return counter.most_common(1)[0][0]
    return "ОКРУЖЕНИЕ"

# ============================================
# КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎴 <b>Добро пожаловать в адаптивный тест определения карты рождения!</b>\n\n"
        "📊 <b>Как это работает:</b>\n\n"
        "<b>ЭТАП 1:</b> Определение масти (6 вопросов)\n"
        "→ Узнаем твой фокус внимания и природу страхов\n\n"
        "<b>ЭТАП 2:</b> Определение уровня (10 вопросов)\n"
        "→ Уточняем твою карту внутри масти\n\n"
        "<b>ЭТАП 3:</b> Проблемный уровень (6 вопросов)\n"
        "→ Определяем, где искать решение\n\n"
        "⏱️ <b>Время:</b> 10-15 минут\n"
        "🎯 <b>Результат:</b> Твоя карта рождения + персональные рекомендации\n\n"
        "Готов начать?"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    # Инициализация данных пользователя
    context.user_data.clear()
    context.user_data["scores"] = {}
    context.user_data["answer_history"] = []
    context.user_data["current_question_id"] = "q1_focus"
    context.user_data["stage2_answers"] = []
    context.user_data["stage3_answers"] = []
    
    # Переход к первому вопросу
    return await ask_adaptive_question(update, context)

# ============================================
# ЭТАП 1: АДАПТИВНЫЕ ВОПРОСЫ
# ============================================

async def ask_adaptive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт адаптивный вопрос ЭТАПА 1"""
    query = update.callback_query
    
    # Получаем текущий вопрос
    current_q_id = context.user_data.get("current_question_id", "q1_focus")
    question = STAGE_1_ADAPTIVE.get(current_q_id)
    
    if not question:
        # Если вопроса нет, завершаем этап 1
        return await finish_stage_1(update, context)
    
    # Формируем текст
    question_text = (
        f"<b>{question['stage']}</b>\n"
        f"📊 Прогресс: {question['progress']}\n\n"
        f"{question['text']}"
    )
    
    # Формируем кнопки
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"adaptive_{current_q_id}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def handle_adaptive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка адаптивного ответа ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    parts = query.data.split("_")
    if len(parts) < 3:
        return STAGE_1
    
    question_id = "_".join(parts[1:-1])
    option_id = parts[-1]
    
    # Получаем данные ответа
    question = STAGE_1_ADAPTIVE.get(question_id)
    if not question:
        return STAGE_1
    
    selected_option = question["options"].get(option_id)
    if not selected_option:
        return STAGE_1
    
    # Начисляем баллы
    for axis, score in selected_option.get("scores", {}).items():
        context.user_data["scores"][axis] = context.user_data["scores"].get(axis, 0) + score
    
    # Сохраняем историю
    context.user_data["answer_history"].append({
        "question_id": question_id,
        "option_id": option_id,
        "text": selected_option["text"]
    })
    
    # Определяем следующий вопрос
    next_q_id = selected_option.get("next")
    
    # Если это конец этапа
    if next_q_id == "finish_stage_1":
        return await finish_stage_1(update, context)
    
    # Переходим к следующему вопросу
    context.user_data["current_question_id"] = next_q_id
    return await ask_adaptive_question(update, context)

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 1 и определение масти"""
    query = update.callback_query
    
    scores = context.user_data.get("scores", {})
    
    # Определяем масть
    suit = calculate_suit(scores)
    context.user_data["suit"] = suit
    
    # Получаем символ масти
    suit_symbol = suit.split()[0]
    
    # Показываем промежуточный результат
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎴 <b>Твоя масть: {suit}</b>\n\n"
        f"{SUIT_DESCRIPTIONS[suit]}\n\n"
        f"📊 <b>Твои показатели:</b>\n"
        f"• ВОВНЕ: {scores.get('ВОВНЕ', 0)} | ВНУТРИ: {scores.get('ВНУТРИ', 0)}\n"
        f"• УМОЗРИТЕЛЬНОЕ: {scores.get('УМОЗРИТЕЛЬНОЕ', 0)} | ФАКТИЧЕСКОЕ: {scores.get('ФАКТИЧЕСКОЕ', 0)}\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение уровня внутри масти.\n\n"
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
    
    # Инициализация ЭТАПА 2
    context.user_data["stage2_current"] = 0
    context.user_data["stage2_level_score"] = 0
    
    return await ask_stage2_question(update, context)

async def ask_stage2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    
    suit = context.user_data.get("suit")
    current = context.user_data.get("stage2_current", 0)
    
    # Получаем вопросы для масти
    questions = STAGE_2_QUESTIONS.get(suit, [])
    
    if current >= len(questions):
        # Завершаем ЭТАП 2
        return await finish_stage_2(update, context)
    
    question = questions[current]
    
    # Формируем текст
    question_text = (
        f"<b>🎯 ЭТАП 2: ОПРЕДЕЛЕНИЕ УРОВНЯ</b>\n"
        f"📊 Прогресс: {current + 1}/{len(questions)}\n"
        f"🎴 Масть: {suit}\n\n"
        f"{question['text']}"
    )
    
    # Формируем кнопки
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

async def handle_stage2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    parts = query.data.split("_")
    if len(parts) < 3:
        return STAGE_2
    
    current = int(parts[1])
    option_id = parts[2]
    
    # Получаем вопрос
    suit = context.user_data.get("suit")
    questions = STAGE_2_QUESTIONS.get(suit, [])
    
    if current >= len(questions):
        return STAGE_2
    
    question = questions[current]
    selected_option = question["options"].get(option_id)
    
    if not selected_option:
        return STAGE_2
    
    # Начисляем баллы
    level_score = selected_option.get("level_score", 0)
    context.user_data["stage2_level_score"] = context.user_data.get("stage2_level_score", 0) + level_score
    
    # Сохраняем ответ
    context.user_data["stage2_answers"].append({
        "question": question["text"],
        "answer": selected_option["text"],
        "score": level_score
    })
    
    # Переходим к следующему вопросу
    context.user_data["stage2_current"] = current + 1
    return await ask_stage2_question(update, context)

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2 и определение карты"""
    query = update.callback_query
    
    suit = context.user_data.get("suit")
    level_score = context.user_data.get("stage2_level_score", 0)
    
    # Определяем уровень карты
    card_level = calculate_card_level(level_score)
    card_name = get_card_name(card_level)
    
    # Сохраняем карту
    suit_symbol = suit.split()[0]
    full_card = f"{card_name}{suit_symbol}"
    context.user_data["card"] = full_card
    context.user_data["card_level"] = card_level
    
    # Показываем промежуточный результат
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎴 <b>Твоя карта: {full_card}</b>\n\n"
        f"📊 <b>Твой уровень:</b> {level_score} баллов\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: определение проблемного уровня.\n\n"
        f"Это последний этап! Готов?"
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
    
    # Инициализация ЭТАПА 3
    context.user_data["stage3_current"] = 0
    context.user_data["stage3_dilts_answers"] = []
    
    return await ask_stage3_question(update, context)

async def ask_stage3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    
    current = context.user_data.get("stage3_current", 0)
    questions = STAGE_3_BASE_QUESTIONS
    
    if current >= len(questions):
        # Завершаем ЭТАП 3
        return await finish_stage_3(update, context)
    
    question = questions[current]
    card = context.user_data.get("card", "?")
    
    # Формируем текст
    question_text = (
        f"<b>🎯 ЭТАП 3: ПРОБЛЕМНЫЙ УРОВЕНЬ</b>\n"
        f"📊 Прогресс: {current + 1}/{len(questions)}\n"
        f"🎴 Твоя карта: {card}\n\n"
        f"{question['text']}"
    )
    
    # Формируем кнопки
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

async def handle_stage3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    # Парсим callback_data
    parts = query.data.split("_")
    if len(parts) < 3:
        return STAGE_3
    
    current = int(parts[1])
    option_id = parts[2]
    
    # Получаем вопрос
    questions = STAGE_3_BASE_QUESTIONS
    
    if current >= len(questions):
        return STAGE_3
    
    question = questions[current]
    selected_option = question["options"].get(option_id)
    
    if not selected_option:
        return STAGE_3
    
    # Сохраняем уровень Дилтса
    dilts_level = selected_option.get("dilts")
    context.user_data["stage3_dilts_answers"].append(dilts_level)
    
    # Сохраняем ответ
    context.user_data["stage3_answers"].append({
        "question": question["text"],
        "answer": selected_option["text"],
        "dilts": dilts_level
    })
    
    # Переходим к следующему вопросу
    context.user_data["stage3_current"] = current + 1
    return await ask_stage3_question(update, context)

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3 и показ результата"""
    query = update.callback_query
    
    # Определяем проблемный уровень
    dilts_answers = context.user_data.get("stage3_dilts_answers", [])
    dilts_level = calculate_dilts_level(dilts_answers)
    context.user_data["dilts_level"] = dilts_level
    
    # Переходим к результату
    return await show_result(update, context)

# ============================================
# РЕЗУЛЬТАТ
# ============================================

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ финального результата"""
    query = update.callback_query
    
    card = context.user_data.get("card", "?")
    suit = context.user_data.get("suit", "?")
    dilts_level = context.user_data.get("dilts_level", "ОКРУЖЕНИЕ")
    
    # Получаем данные карты из старого словаря
    card_data = CARDS.get(card, {})
    
    result_text = (
        f"🎉 <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"🎴 <b>Твоя карта рождения: {card}</b>\n\n"
        f"<b>📊 ТВОИ РЕЗУЛЬТАТЫ:</b>\n\n"
        f"🎴 <b>Масть:</b> {suit}\n"
        f"🎯 <b>Проблемный уровень:</b> {dilts_level}\n\n"
        f"<b>💡 ОПИСАНИЕ КАРТЫ:</b>\n"
        f"{card_data.get('description', 'Описание карты')}\n\n"
        f"<b>🎭 АРХЕТИП:</b>\n"
        f"{card_data.get('archetype', 'Архетип карты')}\n\n"
        f"<b>⚠️ ТЕНЕВАЯ СТОРОНА:</b>\n"
        f"{card_data.get('shadow', 'Теневая сторона')}\n\n"
        f"<b>🌟 РЕКОМЕНДАЦИИ:</b>\n"
        f"Твой проблемный уровень — <b>{dilts_level}</b>.\n"
        f"Работай на этом уровне для максимального эффекта!\n\n"
        f"Хочешь пройти тест заново?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_test")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ статистики ответов"""
    query = update.callback_query
    await query.answer()
    
    card = context.user_data.get("card", "?")
    scores = context.user_data.get("scores", {})
    level_score = context.user_data.get("stage2_level_score", 0)
    dilts_answers = context.user_data.get("stage3_dilts_answers", [])
    
    from collections import Counter
    dilts_counter = Counter(dilts_answers)
    
    stats_text = (
        f"📊 <b>ТВОЯ СТАТИСТИКА</b>\n\n"
        f"🎴 <b>Карта:</b> {card}\n\n"
        f"<b>ЭТАП 1: МАСТЬ</b>\n"
        f"• ВОВНЕ: {scores.get('ВОВНЕ', 0)}\n"
        f"• ВНУТРИ: {scores.get('ВНУТРИ', 0)}\n"
        f"• УМОЗРИТЕЛЬНОЕ: {scores.get('УМОЗРИТЕЛЬНОЕ', 0)}\n"
        f"• ФАКТИЧЕСКОЕ: {scores.get('ФАКТИЧЕСКОЕ', 0)}\n\n"
        f"<b>ЭТАП 2: УРОВЕНЬ</b>\n"
        f"• Баллы: {level_score}\n\n"
        f"<b>ЭТАП 3: УРОВНИ ДИЛТСА</b>\n"
    )
    
    for level, count in dilts_counter.most_common():
        stats_text += f"• {level}: {count}\n"
    
    keyboard = [
        [InlineKeyboardButton("◀️ Назад к результату", callback_data="back_to_result")],
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode="HTML")

async def back_to_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результату"""
    return await show_result(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text("Тест отменён. Используй /start для начала.")
    return ConversationHandler.END

# ============================================
# MAIN
# ============================================

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # ConversationHandler
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
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(show_stats, pattern="^show_stats$"),
            CallbackQueryHandler(back_to_result, pattern="^back_to_result$"),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
    )
    
    application.add_handler(conv_handler)
    
    logger.info("🚀 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
