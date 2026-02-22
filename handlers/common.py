"""
Общие обработчики для уточняющих вопросов и навигации
"""

import logging
import sys
import time
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
        
        questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
        log_debug(f"   questions found: {len(questions)}", user_id)
        
        if not questions:
            log_debug(f"   ⚠️ Вопросы не найдены, пропускаем", user_id)
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        question = questions[0]
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
    
    log_debug(f"🔥 handle_clarification_answer STARTED", user_id)
    log_debug(f"   callback_data: {query.data}", user_id)
    log_debug(f"   user_data: {context.user_data}", user_id)
    
    await query.answer()
    
    try:
        # Парсим callback: clarify_{stage}_{question_id}_{option_id}
        parts = query.data.split("_")
        log_debug(f"   parsed parts: {parts}", user_id)
        
        if len(parts) < 4:
            log_debug(f"❌ Неверный формат callback", user_id)
            return await ask_clarification_question(update, context)
        
        stage = parts[1]  # stage1, stage2, stage3, stage4
        question_id = parts[2]
        option_id = parts[3]
        
        log_debug(f"   stage={stage}, question_id={question_id}, option_id={option_id}", user_id)
        
        # Получаем вопрос из словаря
        clarification_dict = CLARIFICATION_QUESTIONS.get(stage, [])
        log_debug(f"   clarification_dict length: {len(clarification_dict)}", user_id)
        
        question = None
        for q in clarification_dict:
            if q.get("id") == question_id:
                question = q
                log_debug(f"   found question: {q.get('id')}", user_id)
                break
        
        if not question:
            log_debug(f"❌ Вопрос {question_id} не найден", user_id)
            return await ask_clarification_question(update, context)
        
        option = question["options"].get(option_id)
        if not option:
            log_debug(f"❌ Опция {option_id} не найдена", user_id)
            log_debug(f"   available options: {list(question['options'].keys())}", user_id)
            return await ask_clarification_question(update, context)
        
        log_debug(f"   option found: {option}", user_id)
        
        # 👇 Обработка scores
        if isinstance(option, dict) and "scores" in option:
            log_debug(f"   option has scores: {option['scores']}", user_id)
            if "level" in option["scores"]:
                level_score = option["scores"]["level"]
                if "clarification_scores" not in context.user_data:
                    context.user_data["clarification_scores"] = {}
                context.user_data["clarification_scores"][question_id] = level_score
                log_debug(f"✅ Сохранен level {level_score} для {question_id}", user_id)
            else:
                for axis, score in option["scores"].items():
                    context.user_data["scores"][axis] += score
                    log_debug(f"✅ +{score} к {axis}", user_id)
        else:
            log_debug(f"⚠️ Старый формат ответа: {option}", user_id)
            # Для stage3_discrepancy и других старых форматов
            try:
                level_score = int(option_id)
                if "clarification_scores" not in context.user_data:
                    context.user_data["clarification_scores"] = {}
                context.user_data["clarification_scores"][question_id] = level_score
                log_debug(f"✅ Сохранен level {level_score} из option_id", user_id)
            except ValueError:
                log_debug(f"❌ Не удалось интерпретировать ответ", user_id)
        
        # Переходим к следующему вопросу
        current_index = context.user_data.get("clarification_current", 0)
        log_debug(f"   current_index before: {current_index}", user_id)
        
        context.user_data["clarification_current"] = current_index + 1
        log_debug(f"   current_index after: {current_index + 1}", user_id)
        
        log_debug(f"   calling ask_clarification_question...", user_id)
        return await ask_clarification_question(update, context)
            
    except Exception as e:
        log_debug(f"❌ Исключение: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_clarification_question(update, context)
        
    finally:
        context.user_data["processing"] = False
        log_debug(f"✅ handle_clarification_answer FINISHED", user_id)
