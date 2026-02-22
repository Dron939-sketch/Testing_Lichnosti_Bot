"""
Общие обработчики для уточняющих вопросов и навигации
"""

import logging
import sys
import time
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants import CLARIFICATION, STAGE_1, STAGE_2, STAGE_3, STAGE_4
from config import logger
from questions import CLARIFICATION_QUESTIONS
from utils.helpers import generate_unique_callback

# 🔥 Функция для экстренного логирования в stderr
def log_debug(msg, user_id=None):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    user_part = f"[USER:{user_id}]" if user_id else ""
    print(f"🔍 {timestamp} {user_part} {msg}", file=sys.stderr, flush=True)
    logger.debug(msg)

async def ask_clarification_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт уточняющий вопрос"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥 ask_clarification_question STARTED", user_id)
    log_debug(f"   callback_data: {query.data}", user_id)
    log_debug(f"   user_data: {context.user_data}", user_id)
    
    clarification_stage = context.user_data.get("clarification_stage")
    current = context.user_data.get("clarification_current", 0)
    
    log_debug(f"   stage={clarification_stage}, current={current}", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = CLARIFICATION
    log_debug(f"💾 Сохраняю состояние CLARIFICATION = {CLARIFICATION}", user_id)
    
    if clarification_stage == "stage1":
        clarifications = context.user_data.get("stage1_clarifications", [])
        log_debug(f"   stage1_clarifications: {clarifications}", user_id)
        
        if current >= len(clarifications):
            log_debug(f"   ✅ Все уточнения stage1 завершены, возврат к finish_stage_1", user_id)
            context.user_data["stage1_clarified"] = True
            from handlers.stage1 import finish_stage_1
            return await finish_stage_1(update, context)
        
        clarification_type = clarifications[current]
        log_debug(f"   clarification_type: {clarification_type}", user_id)
        
        # 👇 ИНДЕКС ДЛЯ КОНКРЕТНОГО ТИПА
        type_index_key = f"stage1_{clarification_type}_index"
        type_current = context.user_data.get(type_index_key, 0)
        log_debug(f"   type_current for {clarification_type}: {type_current}", user_id)
        
        questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
        log_debug(f"   questions found: {len(questions)}", user_id)
        
        if type_current >= len(questions):
            log_debug(f"   ✅ Все вопросы типа {clarification_type} отвечены, переходим к следующему", user_id)
            context.user_data["clarification_current"] = current + 1
            context.user_data[type_index_key] = 0  # сбрасываем
            return await ask_clarification_question(update, context)
        
        question = questions[type_current]  # 👈 БЕРЕМ ПО ИНДЕКСУ ТИПА
        log_debug(f"   question id: {question.get('id')}", user_id)
        
    elif clarification_stage == "stage2":
        questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
        log_debug(f"   stage2_borderline questions: {len(questions)}", user_id)
        
        if current >= len(questions):
            log_debug(f"   ✅ Все уточнения stage2 завершены, возврат к finish_stage_2", user_id)
            context.user_data["stage2_clarified"] = True
            from handlers.stage2 import finish_stage_2
            return await finish_stage_2(update, context)
        
        question = questions[current]
        log_debug(f"   question id: {question.get('id')}", user_id)
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        log_debug(f"   stage3_discrepancy questions: {len(questions)}", user_id)
        
        if current >= len(questions):
            log_debug(f"   ✅ Все уточнения stage3 завершены, возврат к finish_stage_3", user_id)
            context.user_data["stage3_clarified"] = True
            from handlers.stage3 import finish_stage_3
            return await finish_stage_3(update, context)
        
        question = questions[current]
        log_debug(f"   question id: {question.get('id')}", user_id)
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        log_debug(f"   stage4_tie questions: {len(questions)}", user_id)
        
        if current >= len(questions):
            log_debug(f"   ✅ Все уточнения stage4 завершены, возврат к finish_stage_4", user_id)
            context.user_data["stage4_clarified"] = True
            from handlers.stage4 import finish_stage_4
            return await finish_stage_4(update, context)
        
        question = questions[current]
        log_debug(f"   question id: {question.get('id')}", user_id)
        
    else:
        log_debug(f"⚠️ Неизвестный clarification_stage: {clarification_stage}", user_id)
        return STAGE_1
    
    if not question:
        log_debug(f"⚠️ Вопрос не найден для stage={clarification_stage}, current={current}", user_id)
        return STAGE_1
    
    log_debug(f"   question text: {question['text'][:50]}...", user_id)
    
    question_text = (
        f"🧠 <b>УТОЧНЯЮЩИЙ ВОПРОС</b>\n\n"
        f"{question['text']}\n\n"
        f"<i>Это поможет мне точнее определить ваш профиль.</i>"
    )
    
    keyboard = []
    
    if clarification_stage in ["stage1", "stage4"]:
        for option_id, option in question["options"].items():
            log_debug(f"   creating button: {option_id} - {option['text'][:20]}...", user_id)
            unique_callback = generate_unique_callback("clarify", user_id, clarification_stage, current, option_id)
            keyboard.append([
                InlineKeyboardButton(option["text"], callback_data=unique_callback)
            ])
    else:
        for level, answer_text in question["options"].items():
            log_debug(f"   creating button: {level} - {answer_text[:20]}...", user_id)
            unique_callback = generate_unique_callback("clarify", user_id, clarification_stage, current, level)
            keyboard.append([
                InlineKeyboardButton(answer_text, callback_data=unique_callback)
            ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    log_debug(f"   keyboard rows: {len(keyboard)}", user_id)
    
    try:
        if hasattr(query, 'message') and query.message:
            await query.edit_message_text(
                question_text, 
                reply_markup=reply_markup, 
                parse_mode="HTML"
            )
            log_debug(f"✅ Вопрос {current+1} отправлен", user_id)
    except Exception as e:
        log_debug(f"❌ Ошибка при редактировании: {e}", user_id)
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=question_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            log_debug(f"✅ Отправлено новое сообщение", user_id)
        except Exception as e2:
            log_debug(f"❌ Критическая ошибка отправки: {e2}", user_id)
    
    return CLARIFICATION

async def handle_clarification_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на уточняющий вопрос"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # 🔥🔥🔥 АВАРИЙНАЯ ЗАПИСЬ В ФАЙЛ
    log_path = '/tmp/bot_debug.log'
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'🔥'*50}\n")
            f.write(f"🔥 TIME: {datetime.now()}\n")
            f.write(f"🔥 USER: {user_id}\n")
            f.write(f"🔥 CALLBACK: {query.data}\n")
            f.write(f"🔥 STAGE: {context.user_data.get('clarification_stage')}\n")
            f.write(f"🔥 CURRENT: {context.user_data.get('clarification_current')}\n")
            f.write(f"{'🔥'*50}\n")
            f.flush()
    except:
        pass
    
    log_debug(f"🔥 handle_clarification_answer STARTED", user_id)
    log_debug(f"   callback_data: {query.data}", user_id)
    
    await query.answer()
    
    try:
        parts = query.data.split("_")
        log_debug(f"   parts: {parts}", user_id)
        
        if len(parts) < 4:
            log_debug(f"❌ Неверный формат callback", user_id)
            return await ask_clarification_question(update, context)
        
        stage = parts[1]
        current = int(parts[2])
        option_id = parts[3]
        
        log_debug(f"   stage={stage}, current={current}, option_id={option_id}", user_id)
        
        # 👇 ОБРАБОТКА ДЛЯ stage1 (сложная логика с несколькими вопросами)
        if stage == "stage1":
            clarifications = context.user_data.get("stage1_clarifications", [])
            if current < len(clarifications):
                clarification_type = clarifications[current]
                type_index_key = f"stage1_{clarification_type}_index"
                type_current = context.user_data.get(type_index_key, 0)
                
                questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
                if type_current < len(questions):
                    question = questions[type_current]
                    option = question["options"].get(option_id)
                    
                    if option and "scores" in option:
                        if "level" in option["scores"]:
                            level_score = option["scores"]["level"]
                            if "clarification_scores" not in context.user_data:
                                context.user_data["clarification_scores"] = {}
                            context.user_data["clarification_scores"][question.get("id")] = level_score
                            log_debug(f"✅ Сохранен level {level_score}", user_id)
                        else:
                            for axis, score in option["scores"].items():
                                context.user_data["scores"][axis] += score
                                log_debug(f"✅ +{score} к {axis}", user_id)
                
                # Увеличиваем индекс для этого типа
                context.user_data[type_index_key] = type_current + 1
                log_debug(f"   type_index for {clarification_type}: {type_current} -> {type_current + 1}", user_id)
                
                # Проверяем, все ли вопросы этого типа отвечены
                if type_current + 1 >= len(questions):
                    log_debug(f"   ✅ Все вопросы типа {clarification_type} отвечены", user_id)
                    context.user_data["clarification_current"] = current + 1
            
            return await ask_clarification_question(update, context)
        
        # 👇 ОБРАБОТКА ДЛЯ stage2
        elif stage == "stage2":
            questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
            if current < len(questions):
                question = questions[current]
                option = question["options"].get(option_id)
                
                if option and "scores" in option and "level" in option["scores"]:
                    level_score = option["scores"]["level"]
                    if "stage2_level_scores_dict" not in context.user_data:
                        context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
                    
                    context.user_data["stage2_level_scores_dict"][str(level_score)] += 3
                    log_debug(f"✅ +3 к уровню {level_score}", user_id)
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        # 👇 ОБРАБОТКА ДЛЯ stage3
        elif stage == "stage3":
            questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
            if current < len(questions):
                selected_level = int(option_id)
                if "stage3_level_scores" not in context.user_data:
                    context.user_data["stage3_level_scores"] = []
                context.user_data["stage3_level_scores"].append(selected_level)
                log_debug(f"✅ + уровень {selected_level} к stage3_scores", user_id)
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        # 👇 ОБРАБОТКА ДЛЯ stage4
        elif stage == "stage4":
            questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
            if current < len(questions):
                question = questions[current]
                option = question["options"].get(option_id)
                if option:
                    dilts = option.get("dilts", "ENVIRONMENT")
                    if "stage4_dilts_answers" not in context.user_data:
                        context.user_data["stage4_dilts_answers"] = []
                    context.user_data["stage4_dilts_answers"].append(dilts)
                    log_debug(f"✅ + dilts={dilts}", user_id)
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        return CLARIFICATION
        
    except Exception as e:
        log_debug(f"❌ Ошибка: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_clarification_question(update, context)
