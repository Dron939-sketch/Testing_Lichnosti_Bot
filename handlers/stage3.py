"""
Обработчики для ЭТАПА 3: Конфигурация поведения
"""

import logging
import sys
import os
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants import STAGE_3, STAGE_4
from config import PSYCHOLOGIST_TIPS, STAGE3_FEEDBACK
from questions import STAGE_3_QUESTIONS
from utils.calculations import calculate_final_level
from utils.validators import need_clarification_stage3
from utils.helpers import calculate_progress, generate_unique_callback

logger = logging.getLogger(__name__)

# 🔥 Функция для логирования в stderr
def log_debug(msg, user_id=None):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    user_part = f"[USER:{user_id}]" if user_id else ""
    print(f"🔍 {timestamp} {user_part} {msg}", file=sys.stderr, flush=True)
    logger.debug(msg)

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

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔵 show_stage_3_intro ВЫЗВАН", user_id)
    log_to_file("stage3_intro.log", f"show_stage_3_intro вызван", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_3
    log_debug(f"💾 Сохраняю состояние STAGE_3 = {STAGE_3}", user_id)
    
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 3: КОНФИГУРАЦИЯ ПОВЕДЕНИЯ</b>\n\n"
        f"Восприятие определяет, что вы видите.\n"
        f"Мышление — как вы это понимаете.\n\n"
        f"Конфигурация поведения — это то, \n"
        f"как вы на это реагируете.\n\n"
        f"В ней уже встроены стереотипы, роли \n"
        f"и паттерны, которые вы когда-то переняли у других.\n\n"
        f"<b>Здесь мы исследуем:</b>\n"
        f"• Ваши автоматические реакции\n"
        f"• Как вы действуете в разных ситуациях\n"
        f"• Какие стратегии поведения закреплены\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage3_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 show_stage_3_intro → возвращаю STAGE_3 = {STAGE_3}", user_id)
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 3"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"📋 show_stage_3_details ВЫЗВАН", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_3
    log_debug(f"💾 Сохраняю состояние STAGE_3 = {STAGE_3}", user_id)
    
    await query.answer()
    
    details_text = (
    f"🧠 <b>ЧТО СЕЙЧАС ПРОИЗОЙДЁТ?</b>\n\n"
    f"Восприятие — что вы видите.\n"
    f"Мышление — как понимаете.\n"
    f"<b>Поведение</b> — в каких формах проявляете.\n\n"
    f"<b>Мы принимаем формы:</b>\n"
    f"• Роли, которые носим как одежду\n"
    f"• Рамки, в которые сами себя ставим\n"
    f"• Сценарии, которые пишутся без нас\n\n"
    f"Но глубже — список того, что вы себе позволяете.\n"
    f"А позволения формируются незаметно:\n"
    f"• Триггеры дёргают за ниточки\n"
    f"• Реакции закрепляются, если сработали\n\n"
    f"🎯 <b>Самое важное</b>\n"
    f"<b>Форма управляет содержанием.</b>\n"
    f"То, в какой форме вы проявляетесь,\n"
    f"определяет, что вообще может случиться.\n\n"
    f"<b>Остаётся за кадром:</b>\n"
    f"• Реакции, которые спасали, а теперь мешают\n"
    f"• Чужие сценарии, которые носите как свои\n"
    f"• Невидимое, которое влияет сильнее всего\n\n"
    f"🧠 <b>Для чего я это рассказываю?</b>\n"
    f"Я ищу, где форма перестала работать,\n"
    f"где рамки стали тесны,\n"
    f"и что остаётся за кадром,\n"
    f"но продолжает управлять вашими реакциями.\n\n"
    f"Сейчас просто посмотрим, что остаётся за кадром."
)
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 show_stage_3_details → возвращаю STAGE_3 = {STAGE_3}", user_id)
    return STAGE_3

async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 3"""
    user_id = update.effective_user.id
    log_debug(f"⬅️ back_to_stage3_intro ВЫЗВАН", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_3
    
    return await show_stage_3_intro(update, context)

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 3"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥🔥🔥 start_stage_3 ВЫЗВАН! User: {user_id}", user_id)
    log_debug(f"📊 username=@{query.from_user.username}", user_id)
    log_to_file("stage3_start.log", f"start_stage_3", user_id)
    
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    context.user_data["stage3_last_answered"] = -1
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_3
    log_debug(f"💾 Сохраняю состояние STAGE_3 = {STAGE_3}", user_id)
    
    # Инициализируем список баллов
    if "stage3_level_scores" not in context.user_data:
        context.user_data["stage3_level_scores"] = []
        log_debug(f"📊 Инициализирован stage3_level_scores", user_id)
    
    # Инициализируем словарь для хранения поведенческих уровней по стратегиям
    if "behavioral_levels" not in context.user_data:
        context.user_data["behavioral_levels"] = {
            "СБ": [],
            "ТФ": [],
            "УБ": [],
            "ЧВ": []
        }
        log_debug(f"📊 Инициализирован behavioral_levels", user_id)
    
    log_debug(f"✅ stage3_current инициализирован: 0", user_id)
    
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    user_id = update.effective_user.id
    current = context.user_data.get("stage3_current", 0)
    
    log_debug(f"📝 ask_stage_3_question: current={current}", user_id)
    log_to_file("stage3_questions.log", f"Вопрос {current+1}/8", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_3
    
    if current >= len(STAGE_3_QUESTIONS):
        log_debug(f"🏁 Все вопросы заданы, завершаем этап 3", user_id)
        return await finish_stage_3(update, context)
    
    question = STAGE_3_QUESTIONS[current]
    
    # 🔥 ПОЛУЧАЕМ СТРАТЕГИЮ ВОПРОСА
    strategy = question.get("strategy", "УБ")
    
    progress = calculate_progress(current + 1, len(STAGE_3_QUESTIONS))
    
    question_text = (
        f"🧠 <b>ЭТАП 3: КОНФИГУРАЦИЯ ПОВЕДЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    
    for option_id, option_text in question["options"].items():
        # 🔥 ИСПРАВЛЕНО: option_text — это строка
        unique_callback = generate_unique_callback("stage3", user_id, current, option_id, strategy)
        log_debug(f"   кнопка: {option_text[:20]}... -> {unique_callback}", user_id)
        log_to_file("stage3_callbacks.log", f"Создан callback: {unique_callback}", user_id)
        keyboard.append([
            InlineKeyboardButton(option_text, callback_data=unique_callback)
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if hasattr(query, 'message') and query.message:
            await query.edit_message_text(
                question_text, 
                reply_markup=reply_markup, 
                parse_mode="HTML"
            )
            log_debug(f"✅ Вопрос {current+1}/{len(STAGE_3_QUESTIONS)} отправлен", user_id)
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
            log_debug(f"❌ Критическая ошибка: {e2}", user_id)
    
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥 handle_stage_3_answer CALLED с callback: {query.data}", user_id)
    
    try:
        await query.answer()
    except Exception as e:
        log_debug(f"❌ Ошибка при answer(): {e}", user_id)
    
    if context.user_data.get("processing", False):
        log_debug(f"⏭️ Пропускаем повторное нажатие", user_id)
        return STAGE_3
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        log_debug(f"   parts: {parts}", user_id)
        
        if len(parts) < 3 or parts[0] != "stage3":
            log_debug(f"❌ Неверный формат callback: {query.data}", user_id)
            return STAGE_3
        
        # Парсим callback
        if len(parts) == 4:
            # Формат: stage3_0_1_СБ
            current = int(parts[1])
            option_id = parts[2]
            strategy = parts[3]
        elif len(parts) == 3:
            # Старый формат для обратной совместимости
            current = int(parts[1])
            option_id = parts[2]
            strategy = "УБ"
        else:
            log_debug(f"❌ Неверное количество частей: {len(parts)}", user_id)
            return STAGE_3
        
        log_debug(f"📥 Ответ на вопрос {current}, option={option_id}, strategy={strategy}", user_id)
        
        # Получаем текущий индекс
        stage3_current = context.user_data.get("stage3_current", 0)
        
        # 🔥 ИСПРАВЛЕНО: проверяем, не отвечали ли уже на этот вопрос
        if current < stage3_current:
            log_debug(f"⏭️ Вопрос {current} уже отвечен (текущий индекс {stage3_current})", user_id)
            # Всё равно переходим к следующему вопросу
            return await ask_stage_3_question(update, context)
        
        # Получаем вопрос
        question = STAGE_3_QUESTIONS[current]
        option_text = question["options"].get(option_id)
        
        if not option_text:
            log_debug(f"❌ Опция {option_id} не найдена", user_id)
            return STAGE_3
        
        # 🔥 ИСПРАВЛЕНО: уровень — это номер опции (1-6)
        try:
            level = int(option_id)
        except ValueError:
            level = 1
        
        log_debug(f"   Уровень: {level}", user_id)
        
        # Сохраняем в общий список
        if "stage3_level_scores" not in context.user_data:
            context.user_data["stage3_level_scores"] = []
        context.user_data["stage3_level_scores"].append(level)
        
        # Сохраняем по стратегиям
        if strategy in ["СБ", "ТФ", "УБ", "ЧВ"]:
            if "behavioral_levels" not in context.user_data:
                context.user_data["behavioral_levels"] = {
                    "СБ": [], "ТФ": [], "УБ": [], "ЧВ": []
                }
            context.user_data["behavioral_levels"][strategy].append(level)
            log_debug(f"   + уровень {level} к стратегии {strategy}", user_id)
        
        log_debug(f"✅ + уровень {level} к stage3_scores", user_id)
        log_debug(f"   теперь stage3_scores: {context.user_data['stage3_level_scores']}", user_id)
        
        # 🔥 ИСПРАВЛЕНО: обновляем индекс ТОЛЬКО если это новый вопрос
        if current == stage3_current:
            context.user_data["stage3_last_answered"] = current
            context.user_data["stage3_current"] = current + 1
            log_debug(f"   stage3_current увеличен до {current + 1}", user_id)
        
        # Задаём следующий вопрос
        return await ask_stage_3_question(update, context)
        
    except Exception as e:
        log_debug(f"❌ Ошибка: {e}", user_id)
        import traceback
        traceback.print_exc()
        return await ask_stage_3_question(update, context)
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3 - МОТИВАЦИОННЫЙ ЭКРАН"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    
    log_debug(f"🎯 finish_stage_3 вызван", user_id)
    log_debug(f"📊 stage2_level={stage2_level}, stage3_scores={stage3_scores}", user_id)
    
    # Логируем поведенческие уровни по стратегиям
    behavioral_levels = context.user_data.get("behavioral_levels", {})
    if behavioral_levels:
        log_debug(f"📊 ПОВЕДЕНЧЕСКИЕ УРОВНИ ПО СТРАТЕГИЯМ:", user_id)
        for strategy, values in behavioral_levels.items():
            if values:
                avg = sum(values) / len(values)
                log_debug(f"   {strategy}: {values} → среднее {avg:.1f}", user_id)
    
    needs_clarification = need_clarification_stage3(stage2_level, stage3_scores)
    log_debug(f"📊 needs_clarification: {needs_clarification}", user_id)
    
    if needs_clarification and not context.user_data.get("stage3_clarified", False):
        context.user_data["stage3_clarified"] = True
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage3"
        
        log_debug(f"🚀 Запуск уточнений stage3", user_id)
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
    
    log_debug(f"✅ Stage 3 complete, final_level={final_level}, behavior_level={behavior_level}", user_id)
    
    result_text = STAGE3_FEEDBACK.get(behavior_level, STAGE3_FEEDBACK[1])
    
    keyboard = [[InlineKeyboardButton("▶️ Перейти к завершающему этапу", callback_data="show_stage_4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 finish_stage_3 → возвращаю STAGE_4 = {STAGE_4}", user_id)
    return STAGE_4
