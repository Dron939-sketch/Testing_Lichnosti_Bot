# handlers/stage4.py
"""
Обработчики для ЭТАПА 4: Конфликт логических уровней
"""

import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import STAGE_4, RESULTS, PSYCHOLOGIST_TIPS, STAGE4_ANALYSIS_SCREEN
from questions import STAGE_4_QUESTIONS
from utils.calculations import (
    determine_dilts_level, 
    need_clarification_stage4, 
    calculate_profile_final,
    check_profile_coherence
)
from utils.helpers import calculate_progress

logger = logging.getLogger(__name__)

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"Последний этап нашего исследования определит, на каком уровне находится ваша главная точка роста.\n\n"
        f"<b>Что мы узнаем:</b>\n"
        f"• Где находится основное напряжение в вашей жизни\n"
        f"• На каком уровне нужно работать для изменений\n"
        f"• Какие ресурсы вам нужны для роста\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Это завершающий этап нашего исследования! Готовы?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО ТАКОЕ КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ?</b>\n\n"
        f"Это модель Роберта Дилтса, которая показывает, на каком уровне находится проблема.\n\n"
        f"<b>5 уровней (снизу вверх):</b>\n\n"
        f"1️⃣ ОКРУЖЕНИЕ — внешние условия\n"
        f"2️⃣ ПОВЕДЕНИЕ — ваши действия\n"
        f"3️⃣ СПОСОБНОСТИ — ваши навыки\n"
        f"4️⃣ ЦЕННОСТИ — ваши мотивы\n"
        f"5️⃣ ИДЕНТИЧНОСТЬ — кто вы\n\n"
        f"<b>Принцип:</b> Проблема на нижнем уровне решается на верхнем.\n\n"
        f"<b>Результат:</b> Ваша точка роста"
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
    context.user_data["stage4_last_answered"] = -1
    
    # Инициализируем список ответов
    if "stage4_dilts_answers" not in context.user_data:
        context.user_data["stage4_dilts_answers"] = []
    
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    current = context.user_data.get("stage4_current", 0)
    
    if current >= len(STAGE_4_QUESTIONS):
        return await finish_stage_4(update, context)
    
    question = STAGE_4_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_4_QUESTIONS))
    tip = PSYCHOLOGIST_TIPS["stage4"][min(current, len(PSYCHOLOGIST_TIPS["stage4"])-1)]
    
    question_text = (
        f"🧠 <b>ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{tip}\n\n"
        f"{progress}"
    )
    
    keyboard = []
    user_id = update.effective_user.id
    timestamp = int(time.time())
    
    for option_id, option in question["options"].items():
        unique_callback = f"stage4_{current}_{option_id}_{user_id}_{timestamp}"
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
    
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 4"""
    query = update.callback_query
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка при answer(): {e}")
    
    if context.user_data.get("processing", False):
        logger.debug(f"Пользователь {update.effective_user.id}: пропускаем повторное нажатие")
        return STAGE_4
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        if len(parts) < 3 or parts[0] != "stage4":
            logger.error(f"Неверный формат callback: {query.data}")
            return STAGE_4
        
        current = int(parts[1])
        option_id = parts[2]
        
        last_answered = context.user_data.get("stage4_last_answered", -1)
        if current <= last_answered:
            logger.debug(f"Вопрос {current} уже отвечен, пропускаем")
            return STAGE_4
        
        question = STAGE_4_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_4
        
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        logger.info(f"User {update.effective_user.id}: Stage 4 Q{current} -> {option_id} (dilts={dilts})")
        
        context.user_data["stage4_last_answered"] = current
        context.user_data["stage4_current"] = current + 1
        return await ask_stage_4_question(update, context)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в handle_stage_4_answer: {e}", exc_info=True)
        return await ask_stage_4_question(update, context)
    finally:
        context.user_data["processing"] = False

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 - ЭКРАН АНАЛИТИКИ ПЕРЕД РЕЗУЛЬТАТАМИ"""
    query = update.callback_query
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    
    needs_clarification = need_clarification_stage4(dilts_answers)
    
    if needs_clarification and not context.user_data.get("stage4_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage4"
        
        logger.info(f"User {update.effective_user.id}: Stage 4 needs clarification (tie)")
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    profile_data = calculate_profile_final(context.user_data)
    coherence = profile_data["coherence"]
    context.user_data["profile_data"] = profile_data
    
    analysis_text = STAGE4_ANALYSIS_SCREEN
    await query.edit_message_text(analysis_text.strip(), parse_mode="HTML")
    
    await asyncio.sleep(3)
    
    from handlers.results import show_results_screen
    return await show_results_screen(update, context)
