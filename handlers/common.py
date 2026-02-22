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
        # 🔥🔥🔥 СУПЕР-ЛОГИРОВАНИЕ
        print("\n" + "="*50, file=sys.stderr)
        print(f"🔥🔥🔥 STAGE1 CLARIFICATION DEBUG", file=sys.stderr)
        print(f"current: {current}", file=sys.stderr)
        print(f"stage1_clarifications: {context.user_data.get('stage1_clarifications', [])}", file=sys.stderr)
        
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
    
    # 🔥🔥🔥 АВАРИЙНАЯ ЗАПИСЬ В ФАЙЛ (для Render.com)
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
        pass  # Игнорируем ошибки записи в файл
    
    # 🔥🔥🔥 МАКСИМАЛЬНОЕ ЛОГИРОВАНИЕ В stderr
    print("\n" + "🔥"*50, file=sys.stderr, flush=True)
    print(f"🔥 ВХОД В handle_clarification_answer", file=sys.stderr, flush=True)
    print(f"🔥 CALLBACK: {query.data}", file=sys.stderr, flush=True)
    print(f"🔥 USER_DATA:", file=sys.stderr, flush=True)
    for key, value in context.user_data.items():
        print(f"🔥   {key}: {value}", file=sys.stderr, flush=True)
    print("🔥"*50, file=sys.stderr, flush=True)
    
    log_debug(f"🔥 handle_clarification_answer STARTED", user_id)
    log_debug(f"   callback_data: {query.data}", user_id)
    
    await query.answer()
    
    try:
        parts = query.data.split("_")
        print(f"🔥 PARTS: {parts}", file=sys.stderr, flush=True)
        
        if len(parts) < 4:
            log_debug(f"❌ Неверный формат callback", user_id)
            return await ask_clarification_question(update, context)
        
        stage = parts[1]  # stage1, stage2, stage3, stage4
        question_id = parts[2]
        option_id = parts[3]
        
        log_debug(f"   stage={stage}, question_id={question_id}, option_id={option_id}", user_id)
        
        # Получаем вопрос из словаря
        clarification_dict = CLARIFICATION_QUESTIONS.get(stage, [])
        question = None
        for q in clarification_dict:
            if q.get("id") == question_id:
                question = q
                break
        
        if not question:
            log_debug(f"❌ Вопрос {question_id} не найден", user_id)
            return await ask_clarification_question(update, context)
        
        option = question["options"].get(option_id)
        if not option:
            log_debug(f"❌ Опция {option_id} не найдена", user_id)
            return await ask_clarification_question(update, context)
        
        # Обработка scores
        if isinstance(option, dict) and "scores" in option:
            log_debug(f"   option has scores: {option['scores']}", user_id)
            if "level" in option["scores"]:
                level_score = option["scores"]["level"]
                if "clarification_scores" not in context.user_data:
                    context.user_data["clarification_scores"] = {}
                context.user_data["clarification_scores"][question_id] = level_score
                log_debug(f"✅ Сохранен level {level_score}", user_id)
            else:
                for axis, score in option["scores"].items():
                    context.user_data["scores"][axis] += score
                    log_debug(f"✅ +{score} к {axis}", user_id)
        
        # 👇 ОБНОВЛЯЕМ ИНДЕКС ДЛЯ КОНКРЕТНОГО ТИПА (stage1)
        if stage == "stage1":
            current_index = context.user_data.get("clarification_current", 0)
            clarifications = context.user_data.get("stage1_clarifications", [])
            print(f"🔥 current_index: {current_index}", file=sys.stderr, flush=True)
            print(f"🔥 clarifications: {clarifications}", file=sys.stderr, flush=True)
            
            if current_index < len(clarifications):
                clarification_type = clarifications[current_index]
                type_index_key = f"stage1_{clarification_type}_index"
                type_current = context.user_data.get(type_index_key, 0)
                context.user_data[type_index_key] = type_current + 1
                print(f"🔥 {clarification_type}: {type_current} -> {type_current + 1}", file=sys.stderr, flush=True)
                log_debug(f"   type_index for {clarification_type}: {type_current} -> {type_current + 1}", user_id)
        
        # 👇 ИСПРАВЛЕННАЯ ЧАСТЬ: переход к следующему вопросу
        current_index = context.user_data.get("clarification_current", 0)
        clarification_stage = context.user_data.get("clarification_stage")
        
        log_debug(f"   current_index before: {current_index}", user_id)
        log_debug(f"   clarification_stage: {clarification_stage}", user_id)
        
        # Импортируем нужные функции
        if clarification_stage == "stage1":
            from handlers.stage1 import finish_stage_1
            finish_func = finish_stage_1
        elif clarification_stage == "stage2":
            from handlers.stage2 import finish_stage_2
            finish_func = finish_stage_2
        elif clarification_stage == "stage3":
            from handlers.stage3 import finish_stage_3
            finish_func = finish_stage_3
        elif clarification_stage == "stage4":
            from handlers.stage4 import finish_stage_4
            finish_func = finish_stage_4
        else:
            log_debug(f"❌ Неизвестный stage: {clarification_stage}", user_id)
            return STAGE_1
        
        # Увеличиваем индекс
        new_index = current_index + 1
        context.user_data["clarification_current"] = new_index
        log_debug(f"   new_index: {new_index}", user_id)
        
        # 👇 ПРАВИЛЬНАЯ ПРОВЕРКА ДЛЯ stage1
        if clarification_stage == "stage1":
            # Для stage1 проверяем по clarifications
            clarifications = context.user_data.get("stage1_clarifications", [])
            log_debug(f"   total clarifications: {len(clarifications)}", user_id)
            
            if new_index < len(clarifications):
                log_debug(f"➡️ Переход к следующему типу уточнений ({new_index + 1}/{len(clarifications)})", user_id)
                return await ask_clarification_question(update, context)
            else:
                log_debug(f"✅ Все уточнения stage1 завершены", user_id)
                context.user_data["stage1_clarified"] = True
                return await finish_stage_1(update, context)
        else:
            # Для stage2,3,4 проверяем по questions
            questions = CLARIFICATION_QUESTIONS.get(clarification_stage, [])
            log_debug(f"   total questions: {len(questions)}", user_id)
            
            if new_index < len(questions):
                log_debug(f"➡️ Переход к вопросу {new_index + 1}/{len(questions)}", user_id)
                return await ask_clarification_question(update, context)
            else:
                log_debug(f"✅ Все уточняющие вопросы завершены", user_id)
                context.user_data[f"{clarification_stage}_clarified"] = True
                return await finish_func(update, context)
        
    except Exception as e:
        log_debug(f"❌ Ошибка: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_clarification_question(update, context)
