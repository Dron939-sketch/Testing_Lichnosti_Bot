"""
Общие обработчики для уточняющих вопросов и навигации
"""

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ИСПРАВЛЕНО: Импортируем константы из constants.py вместо config.py
from constants import CLARIFICATION, STAGE_1, STAGE_2, STAGE_3, STAGE_4
from config import logger
from questions import CLARIFICATION_QUESTIONS
from utils.helpers import generate_unique_callback

async def ask_clarification_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт уточняющий вопрос"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"❓ ask_clarification_question ВЫЗВАН для пользователя {user_id}")
    
    clarification_stage = context.user_data.get("clarification_stage")
    current = context.user_data.get("clarification_current", 0)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = CLARIFICATION
    logger.info(f"💾 Сохраняю состояние CLARIFICATION = {CLARIFICATION} для пользователя {user_id}")
    
    if clarification_stage == "stage1":
        clarifications = context.user_data.get("stage1_clarifications", [])
        if current >= len(clarifications):
            context.user_data["stage1_clarified"] = True
            # ИМПОРТ ВНУТРИ ФУНКЦИИ
            from handlers.stage1 import finish_stage_1
            result = await finish_stage_1(update, context)
            logger.info(f"🔄 User {user_id}: clarification stage1 → возвращаю {result}")
            return result
        
        clarification_type = clarifications[current]
        questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
        
        if not questions or current >= len(questions):
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        question = questions[0]
        
    elif clarification_stage == "stage2":
        questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
        if current >= len(questions):
            context.user_data["stage2_clarified"] = True
            # ИМПОРТ ВНУТРИ ФУНКЦИИ
            from handlers.stage2 import finish_stage_2
            result = await finish_stage_2(update, context)
            logger.info(f"🔄 User {user_id}: clarification stage2 → возвращаю {result}")
            return result
        question = questions[current]
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current >= len(questions):
            context.user_data["stage3_clarified"] = True
            # ИМПОРТ ВНУТРИ ФУНКЦИИ
            from handlers.stage3 import finish_stage_3
            result = await finish_stage_3(update, context)
            logger.info(f"🔄 User {user_id}: clarification stage3 → возвращаю {result}")
            return result
        question = questions[current]
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        if current >= len(questions):
            context.user_data["stage4_clarified"] = True
            # ИМПОРТ ВНУТРИ ФУНКЦИИ
            from handlers.stage4 import finish_stage_4
            result = await finish_stage_4(update, context)
            logger.info(f"🔄 User {user_id}: clarification stage4 → возвращаю {result}")
            return result
        question = questions[current]
    else:
        logger.warning(f"⚠️ Неизвестный clarification_stage: {clarification_stage}")
        return STAGE_1
    
    if not question:
        logger.warning(f"⚠️ Вопрос не найден для stage={clarification_stage}, current={current}")
        return STAGE_1
    
    question_text = (
        f"🧠 <b>УТОЧНЯЮЩИЙ ВОПРОС</b>\n\n"
        f"{question['text']}\n\n"
        f"<i>Это поможет мне точнее определить ваш профиль.</i>"
    )
    
    keyboard = []
    
    if clarification_stage in ["stage1", "stage4"]:
        for option_id, option in question["options"].items():
            unique_callback = generate_unique_callback("clarify", user_id, clarification_stage, current, option_id)
            keyboard.append([
                InlineKeyboardButton(option["text"], callback_data=unique_callback)
            ])
    else:
        for level, answer_text in question["options"].items():
            unique_callback = generate_unique_callback("clarify", user_id, clarification_stage, current, level)
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
            logger.info(f"✅ Уточняющий вопрос {current+1} отправлен пользователю {user_id}")
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
    
    return CLARIFICATION

async def handle_clarification_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на уточняющий вопрос"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"📋 handle_clarification_answer ВЫЗВАН для пользователя {user_id}")
    logger.info(f"📋 callback_data: {query.data}")
    
    await query.answer()
    
    try:
        # Парсим callback: clarify_{stage}_{question_id}_{option_id}
        parts = query.data.split("_")
        if len(parts) < 4:
            logger.error(f"❌ Неверный формат callback: {query.data}")
            return await show_clarification_question(update, context)
        
        stage = parts[1]  # stage1, stage2, stage3, stage4
        question_id = parts[2]
        option_id = parts[3]
        
        logger.info(f"📊 stage={stage}, question_id={question_id}, option_id={option_id}")
        
        # Получаем вопрос из словаря
        clarification_dict = CLARIFICATION_QUESTIONS.get(stage, [])
        question = None
        for q in clarification_dict:
            if q.get("id") == question_id:
                question = q
                break
        
        if not question:
            logger.error(f"❌ Вопрос {question_id} не найден")
            return await show_clarification_question(update, context)
        
        # Получаем выбранный вариант
        option = question["options"].get(option_id)
        if not option:
            logger.error(f"❌ Опция {option_id} не найдена")
            return await show_clarification_question(update, context)
        
        # 👇 ВАЖНО: новая логика обработки scores
        if "scores" in option:
            # Для вопросов с scores (новый формат)
            if "level" in option["scores"]:
                # Для stage2_borderline
                level_score = option["scores"]["level"]
                # Сохраняем в user_data для последующего расчета
                if "clarification_scores" not in context.user_data:
                    context.user_data["clarification_scores"] = {}
                context.user_data["clarification_scores"][question_id] = level_score
                logger.info(f"✅ Сохранен level {level_score} для вопроса {question_id}")
            else:
                # Для external/internal и symbolic/material
                for axis, score in option["scores"].items():
                    context.user_data["scores"][axis] += score
                    logger.info(f"✅ +{score} к {axis}")
        else:
            # Для старого формата (если остался где-то)
            logger.warning(f"⚠️ Старый формат ответа без scores: {option}")
            # Пытаемся интерпретировать как level
            try:
                level_score = int(option_id)
                if "clarification_scores" not in context.user_data:
                    context.user_data["clarification_scores"] = {}
                context.user_data["clarification_scores"][question_id] = level_score
                logger.info(f"✅ Сохранен level {level_score} из option_id")
            except ValueError:
                logger.error(f"❌ Не удалось интерпретировать ответ")
        
        # Переходим к следующему уточняющему вопросу или завершаем
        current_index = context.user_data.get("clarification_current", 0)
        clarification_list = context.user_data.get("stage2_clarifications", [])
        
        if current_index < len(clarification_list) - 1:
            # Есть еще вопросы
            context.user_data["clarification_current"] = current_index + 1
            from handlers.common import ask_clarification_question
            return await ask_clarification_question(update, context)
        else:
            # Все вопросы отвечены
            logger.info(f"✅ Все уточняющие вопросы для stage2 завершены")
            # Возвращаемся к завершению этапа 2
            from handlers.stage2_finish import finish_stage_2
            return await finish_stage_2(update, context)
            
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_clarification_answer: {e}", exc_info=True)
        return await show_clarification_question(update, context)
        
    finally:
        context.user_data["processing"] = False
