# handlers/stage3.py
"""
Обработчики для ЭТАПА 3: Конфигурация поведения
"""

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import STAGE_3, STAGE_4, PSYCHOLOGIST_TIPS, STAGE3_FEEDBACK
from questions import STAGE_3_QUESTIONS
from utils.calculations import calculate_final_level
from utils.validators import need_clarification_stage3  # ИСПРАВЛЕНО: импорт из validators
from utils.helpers import calculate_progress, generate_unique_callback

logger = logging.getLogger(__name__)

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 3: КОНФИГУРАЦИЯ ПОВЕДЕНИЯ</b>\n\n"
        f"Теперь исследуем эволюцию ваших поведенческих реакций:\n\n"
        f"<b>Что мы измеряем:</b>\n"
        f"• АВТОМАТИЗМЫ (рефлексы, реакции избегания)\n"
        f"• СИМПТОМЫ (негативные паттерны, борьба)\n"
        f"• ПАТТЕРНЫ (осознанные реакции, анализ)\n"
        f"• СТРАТЕГИИ (трансформация, интеграция)\n\n"
        f"<b>Почему это важно:</b>\n"
        f"Поведение точнее показывает эволюцию вашего развития, чем мысли.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готовы исследовать свои поведенческие реакции?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage3_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>КОНФИГУРАЦИЯ ПОВЕДЕНИЯ</b>\n\n"
        f"<b>4 уровня развития реакций:</b>\n\n"
        f"1️⃣ <b>АВТОМАТИЗМЫ (уровень 1)</b>\n"
        f"   ↳ Рефлексы, реакции избегания\n"
        f"   ↳ Действия без осознания\n\n"
        f"2️⃣ <b>СИМПТОМЫ (уровень 2)</b>\n"
        f"   ↳ Негативные паттерны, борьба\n"
        f"   ↳ Реактивное поведение\n\n"
        f"3️⃣ <b>ПАТТЕРНЫ (уровень 4)</b>\n"
        f"   ↳ Осознанные реакции, анализ\n"
        f"   ↳ Выбор способа реагирования\n\n"
        f"4️⃣ <b>СТРАТЕГИИ (уровень 6)</b>\n"
        f"   ↳ Трансформация, интеграция\n"
        f"   ↳ Создание новых способов бытия\n\n"
        f"<b>Результат:</b> Уровень эволюции ваших поведенческих реакций"
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
    context.user_data["stage3_last_answered"] = -1
    
    # Инициализируем список баллов
    if "stage3_level_scores" not in context.user_data:
        context.user_data["stage3_level_scores"] = []
    
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    current = context.user_data.get("stage3_current", 0)
    
    if current >= len(STAGE_3_QUESTIONS):
        return await finish_stage_3(update, context)
    
    question = STAGE_3_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_3_QUESTIONS))
    tip = PSYCHOLOGIST_TIPS["stage3"][min(current, len(PSYCHOLOGIST_TIPS["stage3"])-1)]
    
    question_text = (
        f"🧠 <b>ЭТАП 3: КОНФИГУРАЦИЯ ПОВЕДЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    user_id = update.effective_user.id
    
    for option_id, option in question["options"].items():
        unique_callback = generate_unique_callback("stage3", user_id, current, option_id)
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
    
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3"""
    query = update.callback_query
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка при answer(): {e}")
    
    if context.user_data.get("processing", False):
        logger.debug(f"Пользователь {update.effective_user.id}: пропускаем повторное нажатие")
        return STAGE_3
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        if len(parts) < 3 or parts[0] != "stage3":
            logger.error(f"Неверный формат callback: {query.data}")
            return STAGE_3
        
        current = int(parts[1])
        option_id = parts[2]
        
        last_answered = context.user_data.get("stage3_last_answered", -1)
        if current <= last_answered:
            logger.debug(f"Вопрос {current} уже отвечен, пропускаем")
            return STAGE_3
        
        question = STAGE_3_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_3
        
        level = selected_option.get("level", 1)
        context.user_data["stage3_level_scores"].append(level)
        
        logger.info(f"User {update.effective_user.id}: Stage 3 Q{current} -> {option_id} (level={level})")
        
        context.user_data["stage3_last_answered"] = current
        context.user_data["stage3_current"] = current + 1
        return await ask_stage_3_question(update, context)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в handle_stage_3_answer: {e}", exc_info=True)
        return await ask_stage_3_question(update, context)
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3 - МОТИВАЦИОННЫЙ ЭКРАН"""
    query = update.callback_query
    
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    
    needs_clarification = need_clarification_stage3(stage2_level, stage3_scores)
    
    if needs_clarification and not context.user_data.get("stage3_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage3"
        
        logger.info(f"User {update.effective_user.id}: Stage 3 needs clarification")
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    final_level = calculate_final_level(stage2_level, stage3_scores)
    context.user_data["final_level"] = final_level
    
    if final_level <= 1:
        behavior_level = 1
    elif final_level <= 2:
        behavior_level = 2
    elif final_level <= 4:
        behavior_level = 4
    else:
        behavior_level = 6
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, behavior_level={behavior_level}")
    
    result_text = STAGE3_FEEDBACK.get(behavior_level, STAGE3_FEEDBACK[1])
    
    keyboard = [[InlineKeyboardButton("▶️ Перейти к завершающему этапу", callback_data="show_stage_4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text.strip(), reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4
