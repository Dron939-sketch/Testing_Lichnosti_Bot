"""
Общие обработчики для уточняющих вопросов и навигации
"""

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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
            from handlers.stage2 import finish_stage_2
            result = await finish_stage_2(update, context)
            logger.info(f"🔄 User {user_id}: clarification stage2 → возвращаю {result}")
            return result
        question = questions[current]
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current >= len(questions):
            context.user_data["stage3_clarified"] = True
            from handlers.stage3 import finish_stage_3
            result = await finish_stage_3(update, context)
            logger.info(f"🔄 User {user_id}: clarification stage3 → возвращаю {result}")
            return result
        question = questions[current]
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        if current >= len(questions):
            context.user_data["stage4_clarified"] = True
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
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка при answer(): {e}")
    
    logger.info(f"📥 handle_clarification_answer для пользователя {user_id}, data={query.data}")
    
    if context.user_data.get("processing", False):
        logger.debug(f"Пользователь {user_id}: пропускаем повторное нажатие")
        return CLARIFICATION
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        if len(parts) < 4:
            logger.error(f"Неверный формат callback: {query.data}")
            return CLARIFICATION
        
        clarification_stage = parts[1]
        current = int(parts[2])
        option_id = parts[3]
        
        logger.info(f"📊 clarification_stage={clarification_stage}, current={current}, option={option_id}")
        
        if clarification_stage == "stage1":
            clarifications = context.user_data.get("stage1_clarifications", [])
            if current < len(clarifications):
                clarification_type = clarifications[current]
                questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
                if questions:
                    question = questions[0]
                    selected_option = question["options"].get(option_id)
                    if selected_option:
                        for axis, score in selected_option.get("scores", {}).items():
                            context.user_data["scores"][axis] += score
                            logger.info(f"   +{score} к {axis}")
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
            
        elif clarification_stage == "stage2":
            questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
            if current < len(questions):
                question = questions[current]
                selected_level = option_id
                
                if "stage2_level_scores_dict" not in context.user_data:
                    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
                
                if selected_level in context.user_data["stage2_level_scores_dict"]:
                    context.user_data["stage2_level_scores_dict"][selected_level] += 3
                    logger.info(f"   +3 к уровню {selected_level}")
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
            
        elif clarification_stage == "stage3":
            questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
            if current < len(questions):
                question = questions[current]
                selected_level = option_id
                
                if "stage3_level_scores" not in context.user_data:
                    context.user_data["stage3_level_scores"] = []
                
                context.user_data["stage3_level_scores"].append(int(selected_level))
                logger.info(f"   + уровень {selected_level} к stage3_scores")
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
            
        elif clarification_stage == "stage4":
            questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
            if current < len(questions):
                question = questions[current]
                selected_option = question["options"].get(option_id)
                if selected_option:
                    dilts = selected_option.get("dilts", "ENVIRONMENT")
                    context.user_data["stage4_dilts_answers"].append(dilts)
                    logger.info(f"   + dilts={dilts} к stage4_answers")
            
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        return CLARIFICATION
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в handle_clarification_answer: {e}", exc_info=True)
        return await ask_clarification_question(update, context)
    finally:
        context.user_data["processing"] = False
