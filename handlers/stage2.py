# handlers/stage2.py
"""
Обработчики для ЭТАПА 2: Конфигурация мышления
"""

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import STAGE_2, STAGE_3, PSYCHOLOGIST_TIPS, STAGE2_FEEDBACK
from questions import STAGE_2_QUESTIONS, STAGE_2_SCORING
from utils.calculations import calculate_thinking_level_by_scores, need_clarification_stage2, get_level_group
from utils.helpers import calculate_progress

logger = logging.getLogger(__name__)

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Теперь исследуем ваш тип мышления внутри системы восприятия.\n\n"
        f"<b>Что мы узнаем:</b>\n"
        f"• Ваш текущий способ обработки информации\n"
        f"• Уровень развития мышления\n"
        f"• Характерные паттерны мыслительных процессов\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~4 минуты\n\n"
        f"Готовы продолжить наше исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage2_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ КОНФИГУРАЦИЯ МЫШЛЕНИЯ?</b>\n\n"
        f"Это тип вашего мышления внутри системы восприятия.\n\n"
        f"<b>9 типов конфигураций мышления:</b>\n\n"
        f"1️⃣ ДЕФИЦИТАРНЫЙ — базовая нужда не удовлетворена\n"
        f"2️⃣ ПОИСКОВЫЙ — активный поиск решения\n"
        f"3️⃣ КОНСТРУКТИВНЫЙ — создание стабильной базы\n"
        f"4️⃣ КРИЗИСНЫЙ — переосмысление достигнутого\n"
        f"5️⃣ ИНТЕГРАТИВНЫЙ — уверенное владение\n"
        f"6️⃣ АЛЬТРУИСТИЧЕСКИЙ — служение другим\n"
        f"7️⃣ МУДРЕЦКИЙ — глубокое понимание\n"
        f"8️⃣ СИСТЕМНЫЙ — управление на системном уровне\n"
        f"9️⃣ ТРАНСЦЕНДЕНТНЫЙ — выход за пределы\n\n"
        f"<b>Результат:</b> Ваш текущий способ обработки информации"
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
    context.user_data["stage2_last_answered"] = -1
    
    # Инициализируем словарь баллов
    if "stage2_level_scores_dict" not in context.user_data:
        context.user_data["stage2_level_scores_dict"] = {
            "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
            "6": 0, "7": 0, "8": 0, "9": 0
        }
    
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    current = context.user_data.get("stage2_current", 0)
    
    questions = STAGE_2_QUESTIONS.get(perception_type, STAGE_2_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    
    if current >= len(questions):
        return await finish_stage_2(update, context)
    
    question = questions[current]
    progress = calculate_progress(current + 1, len(questions))
    tip = PSYCHOLOGIST_TIPS["stage2"][min(current, len(PSYCHOLOGIST_TIPS["stage2"])-1)]
    
    question_text = (
        f"🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    user_id = update.effective_user.id
    timestamp = int(time.time())
    
    for level_num, answer_text in question["options"].items():
        unique_callback = f"stage2_{current}_{level_num}_{user_id}_{timestamp}"
        keyboard.append([
            InlineKeyboardButton(answer_text, callback_data=unique_callback)
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if hasattr(query, 'message') and query.message:
            await query.edit_message_text(
                question_text, 
                reply_markup=reply_markup, 
                parse_mode="HTML"
            )
    except Exception as e:
        error_str = str(e).lower()
        if "message is not modified" in error_str:
            pass
        elif "message can't be edited" in error_str:
            try:
                await query.message.delete()
            except:
                pass
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=question_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            logger.error(f"Ошибка при редактировании: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=question_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2"""
    query = update.callback_query
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка при answer(): {e}")
    
    if context.user_data.get("processing", False):
        logger.debug(f"Пользователь {update.effective_user.id}: пропускаем повторное нажатие")
        return STAGE_2
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        if len(parts) < 3 or parts[0] != "stage2":
            logger.error(f"Неверный формат callback: {query.data}")
            return STAGE_2
        
        current = int(parts[1])
        selected_level = parts[2]
        
        last_answered = context.user_data.get("stage2_last_answered", -1)
        if current <= last_answered:
            logger.debug(f"Вопрос {current} уже отвечен, пропускаем")
            return STAGE_2
        
        perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
        
        scoring_table = STAGE_2_SCORING.get(perception_type, {})
        if current in scoring_table and selected_level in scoring_table[current]:
            if "stage2_level_scores_dict" not in context.user_data:
                context.user_data["stage2_level_scores_dict"] = {
                    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
                    "6": 0, "7": 0, "8": 0, "9": 0
                }
            
            points = scoring_table[current][selected_level]
            context.user_data["stage2_level_scores_dict"][selected_level] += points
            
            logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> level={selected_level} (+{points} points)")
        
        context.user_data["stage2_last_answered"] = current
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в handle_stage_2_answer: {e}", exc_info=True)
        return await ask_stage_2_question(update, context)
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2 - МОТИВАЦИОННЫЙ ЭКРАН"""
    query = update.callback_query
    level_scores_dict = context.user_data.get("stage2_level_scores_dict", {"1": 0})
    
    needs_clarification = need_clarification_stage2(level_scores_dict)
    
    if needs_clarification and not context.user_data.get("stage2_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage2"
        
        logger.info(f"User {update.effective_user.id}: Stage 2 needs clarification")
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    context.user_data["thinking_level"] = thinking_level
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    level_group = get_level_group(thinking_level)
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}, group={level_group}")
    
    result_text = STAGE2_FEEDBACK.get((perception_type, level_group))
    if not result_text:
        result_text = STAGE2_FEEDBACK[("СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ", "1-3")]
    
    keyboard = [[InlineKeyboardButton("▶️ Перейти к этапу 3 — Конфигурация поведения", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text.strip(), reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3
