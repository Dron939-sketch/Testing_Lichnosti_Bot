"""
Обработчики для ЭТАПА 4: Конфликт логических уровней
"""

import logging
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ИСПРАВЛЕНО: Импортируем константы из constants.py вместо config.py
from constants import STAGE_4, RESULTS
from config import PSYCHOLOGIST_TIPS, STAGE4_ANALYSIS_SCREEN
from questions import STAGE_4_QUESTIONS
from utils.calculations import (
    determine_dilts_level, 
    calculate_profile_final,
    check_profile_coherence
)
from utils.validators import need_clarification_stage4
from utils.helpers import calculate_progress, generate_unique_callback

logger = logging.getLogger(__name__)

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"🔵 show_stage_4_intro ВЫЗВАН для пользователя {user_id}")
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    logger.info(f"💾 Сохраняю состояние STAGE_4 = {STAGE_4} для пользователя {user_id}")
    
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 4: ТОЧКА РОСТА</b>\n\n"
        f"Восприятие — что вы видите.\n"
        f"Мышление — как понимаете.\n"
        f"Поведение — как реагируете.\n\n"
        f"Всё это — ваша внутренняя система.\n\n"
        f"Но она живёт внутри внешней системы —\n"
        f"общества, которое постоянно меняется.\n\n"
        f"Когда одна система меняется,\n"
        f"а другая — нет,\n"
        f"возникает напряжение.\n\n"
        f"Здесь мы найдём, где именно\n"
        f"могут возникать потенциальные точки напряжения\n"
        f"между вашей системой и системой, в которой вы находитесь.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"🔄 User {user_id}: show_stage_4_intro → возвращаю STAGE_4 = {STAGE_4}")
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"📋 show_stage_4_details ВЫЗВАН для пользователя {user_id}")
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    logger.info(f"💾 Сохраняю состояние STAGE_4 = {STAGE_4} для пользователя {user_id}")
    
    await query.answer()
    
    details_text = (
        f"🧠 <b>ЧТО СЕЙЧАС ПРОИЗОЙДЁТ?</b>\n\n"
        f"Мы исследовали, как устроены\n"
        f"ваше восприятие, мышление и поведение.\n\n"
        f"Это ваша внутренняя система.\n\n"
        f"Но она не в вакууме —\n"
        f"она внутри общества,\n"
        f"которое живёт по своим законам\n"
        f"и постоянно меняется.\n\n"
        f"🎯 <b>Где возникает напряжение?</b>\n\n"
        f"Когда ритмы не совпадают —\n"
        f"вы меняетесь, а мир нет,\n"
        f"или мир меняется, а вы застыли —\n"
        f"возникает напряжение.\n\n"
        f"Оно может быть в разных местах:\n\n"
        f"• В том, что вас окружает\n"
        f"• В том, что вы делаете\n"
        f"• В том, что вы умеете\n"
        f"• В том, что для вас важно\n"
        f"• В том, кем вы себя считаете\n\n"
        f"🔍 <b>Что мы ищем?</b>\n\n"
        f"Мы ищем не слабое место,\n"
        f"а точку опоры — рычаг.\n\n"
        f"Место, где минимальное усилие\n"
        f"даёт максимальные изменения.\n\n"
        f"Сдвинув эту точку в своей системе,\n"
        f"вы меняете всё остальное —\n"
        f"и внутри, и вовне.\n\n"
        f"Сейчас просто посмотрим,\n"
        f"где именно может находиться этот рычаг.\n"
        f"Без оценок. Вместе."
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"🔄 User {user_id}: show_stage_4_details → возвращаю STAGE_4 = {STAGE_4}")
    return STAGE_4

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 4"""
    user_id = update.effective_user.id
    logger.info(f"⬅️ back_to_stage4_intro ВЫЗВАН для пользователя {user_id}")
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    
    return await show_stage_4_intro(update, context)

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"🔥🔥🔥 start_stage_4 ВЫЗВАН! User: {user_id}")
    logger.info(f"📊 Данные пользователя: username=@{query.from_user.username}")
    
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    context.user_data["stage4_last_answered"] = -1
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    logger.info(f"💾 Сохраняю состояние STAGE_4 = {STAGE_4} для пользователя {user_id}")
    
    # Инициализируем список ответов
    if "stage4_dilts_answers" not in context.user_data:
        context.user_data["stage4_dilts_answers"] = []
        logger.info(f"📊 Инициализирован stage4_dilts_answers для пользователя {user_id}")
    
    logger.info(f"✅ stage4_current инициализирован: 0 для пользователя {user_id}")
    
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    current = context.user_data.get("stage4_current", 0)
    
    logger.info(f"📝 ask_stage_4_question для пользователя {user_id}: current={current}")
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    
    if current >= len(STAGE_4_QUESTIONS):
        logger.info(f"🏁 Все вопросы заданы для пользователя {user_id}, завершаем этап 4")
        return await finish_stage_4(update, context)
    
    question = STAGE_4_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_4_QUESTIONS))
    
    question_text = (
        f"🧠 <b>ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    
    for option_id, option in question["options"].items():
        unique_callback = generate_unique_callback("stage4", user_id, current, option_id)
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
            logger.info(f"✅ Вопрос {current+1}/{len(STAGE_4_QUESTIONS)} этапа 4 отправлен пользователю {user_id}")
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
    user_id = update.effective_user.id
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка при answer(): {e}")
    
    if context.user_data.get("processing", False):
        logger.debug(f"Пользователь {user_id}: пропускаем повторное нажатие")
        return STAGE_4
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        if len(parts) < 3 or parts[0] != "stage4":
            logger.error(f"Неверный формат callback: {query.data}")
            return STAGE_4
        
        current = int(parts[1])
        option_id = parts[2]
        
        logger.info(f"📥 User {user_id}: получен ответ на вопрос {current} этапа 4, option={option_id}")
        
        last_answered = context.user_data.get("stage4_last_answered", -1)
        if current <= last_answered:
            logger.debug(f"Вопрос {current} уже отвечен, пропускаем")
            return STAGE_4
        
        question = STAGE_4_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            logger.error(f"Опция {option_id} не найдена в вопросе {current}")
            return STAGE_4
        
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        logger.info(f"✅ User {user_id}: Stage 4 Q{current} -> {option_id} (dilts={dilts})")
        
        context.user_data["stage4_last_answered"] = current
        context.user_data["stage4_current"] = current + 1
        
        # ✅ ВАЖНО: сохраняем состояние
        context.user_data["conversation_state"] = STAGE_4
        
        return await ask_stage_4_question(update, context)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в handle_stage_4_answer: {e}", exc_info=True)
        return await ask_stage_4_question(update, context)
    finally:
        context.user_data["processing"] = False

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 - ЭКРАН АНАЛИТИКИ ПЕРЕД РЕЗУЛЬТАТАМИ"""
    query = update.callback_query
    user_id = update.effective_user.id
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    
    logger.info(f"🎯 finish_stage_4 вызван для пользователя {user_id}")
    logger.info(f"📊 dilts_answers={dilts_answers}")
    
    needs_clarification = need_clarification_stage4(dilts_answers)
    
    if needs_clarification and not context.user_data.get("stage4_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage4"
        
        logger.info(f"User {user_id}: Stage 4 needs clarification (tie)")
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    profile_data = calculate_profile_final(context.user_data)
    context.user_data["profile_data"] = profile_data
    
    logger.info(f"✅ User {user_id}: Stage 4 complete, profile={profile_data.get('display_name', 'unknown')}")
    
    analysis_text = STAGE4_ANALYSIS_SCREEN
    await query.edit_message_text(analysis_text.strip(), parse_mode="HTML")
    
    await asyncio.sleep(3)
    
    from handlers.results import show_results_screen
    
    # ВАЖНО: Возвращаем результат от show_results_screen (который возвращает RESULTS = 15)
    result = await show_results_screen(update, context)
    logger.info(f"🔄 User {user_id}: finish_stage_4 → возвращаю RESULTS = {RESULTS}")
    return result
