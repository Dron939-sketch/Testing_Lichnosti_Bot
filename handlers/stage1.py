"""
Обработчики для ЭТАПА 1: Конфигурация восприятия
"""

import logging
import sys
import os
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants import STAGE_1, STAGE_2
from config import PSYCHOLOGIST_TIPS, STAGE1_FEEDBACK
from questions import STAGE_1_QUESTIONS
from utils.calculations import determine_perception_type
from utils.validators import need_clarification_stage1
from utils.helpers import calculate_progress, generate_unique_callback

# 🔥 Функция для логирования в stderr
def log_debug(msg, user_id=None):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    user_part = f"[USER:{user_id}]" if user_id else ""
    print(f"🔍 {timestamp} {user_part} {msg}", file=sys.stderr, flush=True)

# 🔥 Функция для записи в файл на Render
def log_to_file(filename: str, data: any, user_id: int = None):
    """Безопасная запись в файл с преобразованием любого типа в строку"""
    try:
        if isinstance(data, slice):
            data = f"slice({data.start}, {data.stop}, {data.step})"
        else:
            data = str(data)
        
        log_path = f'/tmp/{filename}'
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        user_part = f"[USER:{user_id}]" if user_id else ""
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} {user_part} {data}\n")
    except Exception as e:
        print(f"❌ Ошибка записи в файл {filename}: {e}", file=sys.stderr)

logger = logging.getLogger(__name__)

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 1"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔵 show_stage_1_intro ВЫЗВАН", user_id)
    log_to_file("stage1_intro.log", f"show_stage_1_intro вызван", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние в user_data
    context.user_data["conversation_state"] = STAGE_1
    log_debug(f"💾 Сохраняю состояние STAGE_1 = {STAGE_1}", user_id)
    
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"Как ваш виртуальный психолог, я начну с понимания вашей базовой конфигурации восприятия.\n\n"
        f"<b>Что мы исследуем:</b>\n"
        f"• Куда направлено ваше внимание\n"
        f"• Что вызывает тревогу\n"
        f"• Как вы обрабатываете информацию\n\n"
        f"📊 <b>Вопросов:</b> 10\n"
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
    
    log_debug(f"🔄 show_stage_1_intro → возвращаю STAGE_1 = {STAGE_1}", user_id)
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 1"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"📋 show_stage_1_details ВЫЗВАН", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_1
    log_debug(f"💾 Сохраняю состояние STAGE_1 = {STAGE_1}", user_id)
    
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
    
    log_debug(f"🔄 show_stage_1_details → возвращаю STAGE_1 = {STAGE_1}", user_id)
    return STAGE_1

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 1"""
    user_id = update.effective_user.id
    log_debug(f"⬅️ back_to_stage1_intro ВЫЗВАН", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_1
    
    return await show_stage_1_intro(update, context)

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 1"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥🔥🔥 start_stage_1 ВЫЗВАН! User: {user_id}", user_id)
    log_debug(f"📊 Данные пользователя: username=@{query.from_user.username}", user_id)
    log_debug(f"📊 callback_data: {query.data}", user_id)
    log_debug(f"📊 Текущее состояние user_data: {context.user_data}", user_id)
    log_to_file("stage1_start.log", f"start_stage_1", user_id)
    
    await query.answer()
    
    context.user_data["stage1_current"] = 0
    context.user_data["stage1_last_answered"] = -1
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_1
    log_debug(f"💾 Сохраняю состояние STAGE_1 = {STAGE_1}", user_id)
    log_debug(f"📊 После сохранения user_data: {context.user_data}", user_id)
    
    log_debug(f"✅ stage1_current инициализирован: 0", user_id)
    
    result = await ask_stage_1_question(update, context)
    log_debug(f"🔄 start_stage_1 → ask_stage_1_question вернул: {result}", user_id)
    return result

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 1"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    current = context.user_data.get("stage1_current", 0)
    log_debug(f"📝 ask_stage_1_question для пользователя {user_id}: current={current}", user_id)
    log_to_file("stage1_questions.log", f"Вопрос {current+1}/9", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_1
    
    if current >= len(STAGE_1_QUESTIONS):
        log_debug(f"🏁 Все вопросы заданы для пользователя {user_id}, завершаем этап 1", user_id)
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_1_QUESTIONS))
    
    question_text = (
        f"🧠 <b>ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    
    for option_id, option in question["options"].items():
        unique_callback = generate_unique_callback("stage1", user_id, current, option_id)
        log_debug(f"   кнопка: {option['text'][:20]}... -> {unique_callback}", user_id)
        log_to_file("stage1_callbacks.log", f"Создан callback: {unique_callback}", user_id)
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
            log_debug(f"✅ Вопрос {current+1}/{len(STAGE_1_QUESTIONS)} отправлен пользователю {user_id}", user_id)
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
            log_debug(f"✅ Отправлено новое сообщение (message_id={sent_message.message_id})", user_id)
        else:
            log_debug(f"❌ Ошибка при редактировании: {e}", user_id)
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
    user_id = update.effective_user.id
    
    # 🔍 ДОБАВЛЕНО РАСШИРЕННОЕ ЛОГИРОВАНИЕ
    log_debug(f"🔍🔍🔍 handle_stage_1_answer ВЫЗВАН! User: {user_id}", user_id)
    log_debug(f"🔍 Данные callback: {query.data}", user_id)
    log_debug(f"🔍 Текущее состояние user_data: {context.user_data}", user_id)
    log_to_file("stage1_answers.log", f"ПОЛУЧЕН CALLBACK: {query.data}", user_id)
    log_to_file("stage1_answers.log", f"stage1_current до: {context.user_data.get('stage1_current')}", user_id)
    log_to_file("stage1_answers.log", f"stage1_last_answered: {context.user_data.get('stage1_last_answered')}", user_id)
    
    try:
        await query.answer()
    except Exception as e:
        log_debug(f"❌ Ошибка при answer(): {e}", user_id)
    
    if context.user_data.get("processing", False):
        log_debug(f"⏭️ Пользователь {user_id}: пропускаем повторное нажатие", user_id)
        return STAGE_1
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        log_debug(f"   parts: {parts}", user_id)
        log_to_file("stage1_answers.log", f"parts: {parts}", user_id)
        
        if len(parts) < 3 or parts[0] != "stage1":
            log_debug(f"❌ Неверный формат callback: {query.data}", user_id)
            return STAGE_1
        
        current = int(parts[1])
        option_id = parts[2]
        
        log_debug(f"📥 User {user_id}: получен ответ на вопрос {current}, option={option_id}", user_id)
        log_to_file("stage1_answers.log", f"Ответ на вопрос {current}, option={option_id}", user_id)
        
        last_answered = context.user_data.get("stage1_last_answered", -1)
        if current <= last_answered:
            log_debug(f"⏭️ Вопрос {current} уже отвечен (last_answered={last_answered})", user_id)
            log_to_file("stage1_answers.log", f"Вопрос {current} уже отвечен", user_id)
            return STAGE_1
        
        question = STAGE_1_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            log_debug(f"❌ Опция {option_id} не найдена в вопросе {current}", user_id)
            log_to_file("stage1_errors.log", f"Опция {option_id} не найдена", user_id)
            return STAGE_1
        
        # Инициализируем scores если нет
        if "scores" not in context.user_data:
            context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
        
        # 👇 ИЗМЕНЕНО: обрабатываем и старые оси, и новые прямые баллы
        for axis, score in selected_option.get("scores", {}).items():
            # Старые оси
            if axis in ["EXTERNAL", "INTERNAL", "SYMBOLIC", "MATERIAL"]:
                context.user_data["scores"][axis] += score
                log_debug(f"   +{score} к {axis} (теперь: {context.user_data['scores'][axis]})", user_id)
                log_to_file("stage1_scores.log", f"+{score} к {axis}", user_id)
            
            # 👇 НОВЫЕ прямые баллы за типы
            elif axis in ["SP", "IP", "IA", "SA"]:
                # Добавляем в общий словарь scores
                if axis not in context.user_data["scores"]:
                    context.user_data["scores"][axis] = 0
                context.user_data["scores"][axis] += score
                log_debug(f"   +{score} к прямому типу {axis} (теперь: {context.user_data['scores'][axis]})", user_id)
                log_to_file("stage1_scores.log", f"+{score} к {axis}", user_id)
        
        log_debug(f"✅ User {user_id}: Stage 1 Q{current} -> {option_id}", user_id)
        
        context.user_data["stage1_last_answered"] = current
        context.user_data["stage1_current"] = current + 1
        log_debug(f"   stage1_current увеличен до {current+1}", user_id)
        log_to_file("stage1_answers.log", f"stage1_current теперь = {current+1}", user_id)
        
        # ✅ ВАЖНО: сохраняем состояние
        context.user_data["conversation_state"] = STAGE_1
        log_debug(f"💾 После ответа сохраняю состояние STAGE_1 = {STAGE_1}", user_id)
        log_debug(f"📊 После сохранения user_data: {context.user_data}", user_id)
        
        result = await ask_stage_1_question(update, context)
        log_debug(f"🔄 handle_stage_1_answer → ask_stage_1_question вернул: {result}", user_id)
        return result
        
    except Exception as e:
        log_debug(f"❌ Критическая ошибка в handle_stage_1_answer: {e}", user_id)
        log_to_file("stage1_errors.log", f"Исключение: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_stage_1_question(update, context)
    finally:
        context.user_data["processing"] = False
        log_debug(f"✅ handle_stage_1_answer FINISHED", user_id)
        
async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАП 1 - МОТИВАЦИОННЫЙ ЭКРАН"""
    query = update.callback_query
    user_id = update.effective_user.id
    scores = context.user_data.get("scores", {})
    
    log_debug(f"🎯 finish_stage_1 вызван для пользователя {user_id}", user_id)
    log_to_file("stage1_finish.log", f"finish_stage_1 вызван", user_id)
    log_debug(f"📊 Итоговые scores: {scores}", user_id)
    log_to_file("stage1_finish.log", f"scores: {scores}", user_id)
    
    clarifications_needed = need_clarification_stage1(scores)
    log_debug(f"📊 clarifications_needed: {clarifications_needed}", user_id)
    log_to_file("stage1_finish.log", f"clarifications_needed: {clarifications_needed}", user_id)
    
    if clarifications_needed and not context.user_data.get("stage1_clarified", False):
        context.user_data["stage1_clarifications"] = clarifications_needed
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage1"
        
        log_debug(f"🚀 ЗАПУСК УТОЧНЯЮЩИХ ВОПРОСОВ stage1", user_id)
        log_debug(f"   clarifications: {clarifications_needed}", user_id)
        log_debug(f"   clarification_current: 0", user_id)
        log_debug(f"   clarification_stage: stage1", user_id)
        log_to_file("stage1_finish.log", f"ЗАПУСК УТОЧНЕНИЙ: {clarifications_needed}", user_id)
        
        logger.info(f"User {user_id}: Stage 1 needs clarification: {clarifications_needed}")
        from handlers.common import ask_clarification_question
        log_debug(f"   ВЫЗЫВАЮ ask_clarification_question", user_id)
        result = await ask_clarification_question(update, context)
        log_debug(f"   ask_clarification_question вернул: {result}", user_id)
        return result
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    log_debug(f"✅ User {user_id}: Stage 1 complete, type={perception_type}", user_id)
    logger.info(f"✅ User {user_id}: Stage 1 complete, type={perception_type}")
    log_to_file("stage1_finish.log", f"Stage 1 complete, type={perception_type}", user_id)
    
    result_text = STAGE1_FEEDBACK.get(perception_type, STAGE1_FEEDBACK["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    
    keyboard = [[InlineKeyboardButton("▶️ Перейти к этапу 2 — Конфигурация мышления", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 finish_stage_1 → возвращаю STAGE_2 = {STAGE_2}", user_id)
    logger.info(f"🔄 User {user_id}: finish_stage_1 → возвращаю STAGE_2 = {STAGE_2}")
    log_to_file("stage1_finish.log", f"Возвращаю STAGE_2 = {STAGE_2}", user_id)
    return STAGE_2
