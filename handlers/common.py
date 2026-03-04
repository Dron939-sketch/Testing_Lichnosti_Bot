"""
Общие обработчики для уточняющих вопросов и навигации
ИСПРАВЛЕННАЯ ВЕРСИЯ:
✅ Защита от повторных ответов
✅ Сохранение ответов для AI
✅ Упрощенная логика для stage1
✅ Метрики времени
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

# Константы
CLARIFICATION_TIMEOUT = 3600  # 1 час на прохождение уточнений

async def ask_clarification_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт уточняющий вопрос"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥 ask_clarification_question STARTED", user_id)
    log_debug(f"   callback_data: {query.data}", user_id)
    log_debug(f"   user_data: {context.user_data}", user_id)
    
    # Инициализируем время начала, если это первый вопрос
    if "clarification_start_time" not in context.user_data:
        context.user_data["clarification_start_time"] = time.time()
    
    clarification_stage = context.user_data.get("clarification_stage")
    current = context.user_data.get("clarification_current", 0)
    
    log_debug(f"   stage={clarification_stage}, current={current}", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = CLARIFICATION
    log_debug(f"💾 Сохраняю состояние CLARIFICATION = {CLARIFICATION}", user_id)
    
    # Инициализируем хранилище для AI
    if "all_answers" not in context.user_data:
        context.user_data["all_answers"] = []
    
    # Инициализируем хранилище отвеченных вопросов
    if "clarification_answered" not in context.user_data:
        context.user_data["clarification_answered"] = {}
    
    if clarification_stage == "stage1":
        # 🔥 УПРОЩЕННАЯ ЛОГИКА: создаем плоский список всех вопросов
        if "stage1_pending_questions" not in context.user_data:
            clarifications = context.user_data.get("stage1_clarifications", [])
            pending = []
            for c_type in clarifications:
                questions = CLARIFICATION_QUESTIONS.get(f"stage1_{c_type}", [])
                for q in questions:
                    pending.append({
                        'type': c_type,
                        'question': q
                    })
            context.user_data["stage1_pending_questions"] = pending
            context.user_data["clarification_current"] = 0
            log_debug(f"   создано {len(pending)} вопросов для stage1", user_id)
        
        pending = context.user_data.get("stage1_pending_questions", [])
        current = context.user_data.get("clarification_current", 0)
        
        if current >= len(pending):
            log_debug(f"   ✅ Все уточнения stage1 завершены", user_id)
            context.user_data["stage1_clarified"] = True
            context.user_data.pop("stage1_pending_questions", None)
            from handlers.stage1 import finish_stage_1
            return await finish_stage_1(update, context)
        
        question_data = pending[current]
        question = question_data['question']
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
    
    # 👇 ЗАЩИТА ОТ ПОВТОРНЫХ ОТВЕТОВ
    answered_key = query.data
    if context.user_data.get('clarification_answered', {}).get(answered_key):
        log_debug(f"⏭️ Ответ уже был обработан", user_id)
        return await ask_clarification_question(update, context)
    
    if context.user_data.get("processing", False):
        log_debug(f"⏭️ Пропускаем повторное нажатие", user_id)
        return CLARIFICATION
    
    context.user_data["processing"] = True
    
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
        
        # 👇 ОБРАБОТКА ДЛЯ stage1 (новая упрощенная логика)
        if stage == "stage1":
            pending = context.user_data.get("stage1_pending_questions", [])
            if current < len(pending):
                question_data = pending[current]
                question = question_data['question']
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
                            if "scores" not in context.user_data:
                                context.user_data["scores"] = {}
                            context.user_data["scores"][axis] = context.user_data["scores"].get(axis, 0) + score
                            log_debug(f"✅ +{score} к {axis}", user_id)
                
                # 👇 СОХРАНЯЕМ ОТВЕТ ДЛЯ AI
                if "all_answers" not in context.user_data:
                    context.user_data["all_answers"] = []
                
                context.user_data["all_answers"].append({
                    'stage': 'clarification',
                    'substage': 'stage1',
                    'question_index': current,
                    'question': question['text'],
                    'answer': option['text'] if isinstance(option, dict) else question['options'][option_id],
                    'option': option_id,
                    'scores': option.get('scores', {}) if isinstance(option, dict) else {}
                })
                
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
                
                # 👇 СОХРАНЯЕМ ОТВЕТ ДЛЯ AI
                if "all_answers" not in context.user_data:
                    context.user_data["all_answers"] = []
                
                context.user_data["all_answers"].append({
                    'stage': 'clarification',
                    'substage': 'stage2',
                    'question_index': current,
                    'question': question['text'],
                    'answer': option['text'] if isinstance(option, dict) else question['options'][option_id],
                    'option': option_id,
                    'scores': option.get('scores', {}) if isinstance(option, dict) else {}
                })
            
            new_index = current + 1
            context.user_data["clarification_current"] = new_index
            log_debug(f"   new_index: {new_index}, всего вопросов: {len(questions)}", user_id)
            
            if new_index >= len(questions):
                log_debug(f"✅ Все уточнения stage2 завершены", user_id)
                context.user_data["stage2_clarified"] = True
                from handlers.stage2 import finish_stage_2
                return await finish_stage_2(update, context)
            else:
                return await ask_clarification_question(update, context)
        
        # 👇 ОБРАБОТКА ДЛЯ stage3
        elif stage == "stage3":
            questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
            if current < len(questions):
                question = questions[current]
                selected_level = int(option_id)
                option = question["options"].get(option_id)
                
                if "stage3_level_scores" not in context.user_data:
                    context.user_data["stage3_level_scores"] = []
                context.user_data["stage3_level_scores"].append(selected_level)
                log_debug(f"✅ + уровень {selected_level} к stage3_scores", user_id)
                
                # 👇 СОХРАНЯЕМ ОТВЕТ ДЛЯ AI
                if "all_answers" not in context.user_data:
                    context.user_data["all_answers"] = []
                
                context.user_data["all_answers"].append({
                    'stage': 'clarification',
                    'substage': 'stage3',
                    'question_index': current,
                    'question': question['text'],
                    'answer': option if isinstance(option, str) else question['options'][option_id],
                    'option': option_id,
                    'value': selected_level
                })
            
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
                    
                    # 👇 СОХРАНЯЕМ ОТВЕТ ДЛЯ AI
                    if "all_answers" not in context.user_data:
                        context.user_data["all_answers"] = []
                    
                    context.user_data["all_answers"].append({
                        'stage': 'clarification',
                        'substage': 'stage4',
                        'question_index': current,
                        'question': question['text'],
                        'answer': option['text'],
                        'option': option_id,
                        'dilts': dilts
                    })
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        # 👇 ОТМЕЧАЕМ ВОПРОС КАК ОТВЕЧЕННЫЙ
        clarification_answered = context.user_data.get('clarification_answered', {})
        clarification_answered[query.data] = True
        context.user_data['clarification_answered'] = clarification_answered
        
        return CLARIFICATION
        
    except Exception as e:
        log_debug(f"❌ Ошибка: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_clarification_question(update, context)
    finally:
        context.user_data["processing"] = False
        log_debug(f"✅ handle_clarification_answer FINISHED", user_id)
