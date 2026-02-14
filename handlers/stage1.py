"""
Обработчики для ЭТАПА 1: Конфигурация восприятия
"""

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import STAGE_1, STAGE_2, PSYCHOLOGIST_TIPS, STAGE1_FEEDBACK
from questions import STAGE_1_QUESTIONS
from utils.calculations import determine_perception_type
from utils.validators import need_clarification_stage1
from utils.helpers import calculate_progress, generate_unique_callback

logger = logging.getLogger(__name__)

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 1"""
    query = update.callback_query
    
    intro_text = (
        f"🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"Как ваш виртуальный психолог, я начну с понимания вашей базовой конфигурации восприятия.\n\n"
        f"<b>Что мы исследуем:</b>\n"
        f"• Куда направлено ваше внимание\n"
        f"• Что вызывает тревогу\n"
        f"• Как вы обрабатываете информацию\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"<i>Отвечайте честно — это поможет мне лучше понять вас.</i>\n\n"
        f"Начнем наше исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage1_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ КОНФИГУРАЦИЯ ВОСПРИЯТИЯ?</b>\n\n"
        f"Это базовая программа, через которую вы воспринимаете мир.\n\n"
        f"<b>Мы измеряем две оси:</b>\n\n"
        f"<b>1. Направленность внимания:</b>\n"
        f"• ЭКСТЕРНАЛЬНАЯ — фокус на внешнем мире (люди, события)\n"
        f"• ИНТЕРНАЛЬНАЯ — фокус на внутреннем мире (мысли, чувства)\n\n"
        f"<b>2. Доминирующая тревога:</b>\n"
        f"• СИМВОЛИЧЕСКАЯ — страх отвержения, непонимания\n"
        f"• МАТЕРИАЛЬНАЯ — страх потери контроля, ресурсов\n\n"
        f"<b>Результат:</b> Один из четырёх типов восприятия\n\n"
        f"Это определит, какие вопросы вы получите на следующих этапах."
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
    context.user_data["stage1_last_answered"] = -1
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 1"""
    query = update.callback_query
    
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(STAGE_1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_1_QUESTIONS))
    tip = PSYCHOLOGIST_TIPS["stage1"][min(current, len(PSYCHOLOGIST_TIPS["stage1"])-1)]
    
    question_text = (
        f"🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    user_id = update.effective_user.id
    
    for option_id, option in question["options"].items():
        unique_callback = generate_unique_callback("stage1", user_id, current, option_id)
        keyboard.append([
            InlineKeyboardButton(option["text"], callback_data=unique_callback)
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
            
            sent_message = await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=question_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            context.user_data["last_message_id"] = sent_message.message_id
        else:
            logger.error(f"Ошибка при редактировании: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=question_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 1"""
    query = update.callback_query
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка при answer(): {e}")
    
    if context.user_data.get("processing", False):
        logger.debug(f"Пользователь {update.effective_user.id}: пропускаем повторное нажатие")
        return STAGE_1
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        
        if len(parts) < 3 or parts[0] != "stage1":
            logger.error(f"Неверный формат callback: {query.data}")
            return STAGE_1
        
        current = int(parts[1])
        option_id = parts[2]
        
        last_answered = context.user_data.get("stage1_last_answered", -1)
        if current <= last_answered:
            logger.debug(f"Вопрос {current} уже отвечен, пропускаем")
            return STAGE_1
        
        question = STAGE_1_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            logger.error(f"Опция {option_id} не найдена в вопросе {current}")
            return STAGE_1
        
        # Инициализируем scores если нет
        if "scores" not in context.user_data:
            context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
        
        for axis, score in selected_option.get("scores", {}).items():
            context.user_data["scores"][axis] += score
        
        logger.info(f"User {update.effective_user.id}: Stage 1 Q{current} -> {option_id}")
        
        context.user_data["stage1_last_answered"] = current
        context.user_data["stage1_current"] = current + 1
        
        return await ask_stage_1_question(update, context)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в handle_stage_1_answer: {e}", exc_info=True)
        return await ask_stage_1_question(update, context)
    finally:
        context.user_data["processing"] = False

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАП 1 - МОТИВАЦИОННЫЙ ЭКРАН"""
    query = update.callback_query
    scores = context.user_data.get("scores", {})
    
    clarifications_needed = need_clarification_stage1(scores)
    
    if clarifications_needed and not context.user_data.get("stage1_clarified", False):
        context.user_data["stage1_clarifications"] = clarifications_needed
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage1"
        
        logger.info(f"User {update.effective_user.id}: Stage 1 needs clarification")
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"✅ User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    result_text = STAGE1_FEEDBACK.get(perception_type, STAGE1_FEEDBACK["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    
    keyboard = [[InlineKeyboardButton("▶️ Перейти к этапу 2 — Конфигурация мышления", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    # ВАЖНО: Возвращаем STAGE_2 (который теперь равен 11)
    logger.info(f"🔄 User {update.effective_user.id}: finish_stage_1 → возвращаю STAGE_2 = {STAGE_2}")
    return STAGE_2
