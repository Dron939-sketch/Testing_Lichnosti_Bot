"""
Обработчики для ЭТАПА 2: Конфигурация мышления
"""

import logging
import sys
import os
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from constants import STAGE_2, STAGE_3
from config import PSYCHOLOGIST_TIPS, STAGE2_FEEDBACK
from questions import STAGE_2_QUESTIONS, STAGE_2_SCORING
from utils.calculations import calculate_thinking_level_by_scores, get_level_group
from utils.validators import need_clarification_stage2
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
        # 🔥 ПРЕОБРАЗУЕМ slice В СТРОКУ
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
        
async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔵 show_stage_2_intro ВЫЗВАН", user_id)
    log_to_file("stage2_intro.log", f"show_stage_2_intro вызван", user_id)
    
    context.user_data["conversation_state"] = STAGE_2
    log_debug(f"💾 Сохраняю состояние STAGE_2 = {STAGE_2}", user_id)
    
    await query.answer()
    
    intro_text = (
        f"🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Теперь исследуем ваш тип мышления внутри системы восприятия.\n\n"
        f"<b>Что мы узнаем:</b>\n"
        f"• Ваш текущий способ обработки информации\n"
        f"• Способ мышления\n"
        f"• Характерные паттерны мыслительных процессов\n\n"
        f"📊 <b>Вопросов:</b> 16\n"  # 🔥 ИЗМЕНЕНО: было 8, стало 16
        f"⏱ <b>Время:</b> ~6 минут\n\n"  # 🔥 ИЗМЕНЕНО
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage2_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 show_stage_2_intro → возвращаю STAGE_2 = {STAGE_2}", user_id)
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 2"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"📋 show_stage_2_details ВЫЗВАН", user_id)
    
    context.user_data["conversation_state"] = STAGE_2
    log_debug(f"💾 Сохраняю состояние STAGE_2 = {STAGE_2}", user_id)
    
    await query.answer()
    
    details_text = (
    f"🧠 <b>ЧТО СЕЙЧАС ПРОИЗОЙДЁТ?</b>\n\n"
    f"На предыдущем этапе мы определили вашу конфигурацию восприятия — "
    f"линзу, через которую вы смотрите на мир.\n\n"
    f"Она сформирована культурой, нормами, ценностями и опытом, "
    f"который вас строил. Это определило, что вы замечаете автоматически, "
    f"а что остаётся за кадром.\n\n"
    f"🧠 <b>Теперь мы идём глубже</b>\n"
    f"Внутри неё — конфигурация мышления. Она определяется задачами: "
    f"как вы обрабатываете информацию, какие связи видите, какой объём "
    f"можете удержать.\n\n"
    f"🎯 <b>Самое важное</b>\n"
    f"Конфигурация мышления — это траектория с чётким пунктом назначения: "
    f"результат, к которому вы придёте.\n\n"
    f"Если ничего не менять — вы попадёте именно туда. Не туда, куда хотите, "
    f"а туда, куда ведёт ваше мышление.\n\n"
    f"🔍 <b>Что с невидимым?</b>\n"
    f"Восприятие отсекает невидимое. Но мышление может его вычислить, "
    f"домыслить, понять — даже то, что не лежит на поверхности.\n\n"
    f"🧠 <b>Для чего я это рассказываю?</b>\n"
    f"Я сравниваю: куда вы хотите попасть и куда ведёт ваше мышление. "
    f"Если есть разница — я обязан предупредить."
)
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 show_stage_2_details → возвращаю STAGE_2 = {STAGE_2}", user_id)
    return STAGE_2

async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 2"""
    user_id = update.effective_user.id
    log_debug(f"⬅️ back_to_stage2_intro ВЫЗВАН", user_id)
    
    context.user_data["conversation_state"] = STAGE_2
    
    return await show_stage_2_intro(update, context)

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 2"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥🔥🔥 start_stage_2 ВЫЗВАН! User: {user_id}", user_id)
    log_to_file("stage2_start.log", f"start_stage_2", user_id)
    
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    context.user_data["stage2_last_answered"] = -1
    
    context.user_data["conversation_state"] = STAGE_2
    log_debug(f"💾 Сохраняю состояние STAGE_2 = {STAGE_2}", user_id)
    
    if "stage2_level_scores_dict" not in context.user_data:
        context.user_data["stage2_level_scores_dict"] = {
            "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
            "6": 0, "7": 0, "8": 0, "9": 0
        }
        log_debug(f"📊 Инициализирован stage2_level_scores_dict", user_id)
    
    # 🔥 НОВОЕ: инициализируем словарь для хранения уровней всех стратегий
    if "strategy_levels" not in context.user_data:
        context.user_data["strategy_levels"] = {
            "СБ": [],
            "ТФ": [],
            "УБ": [],
            "ЧВ": []
        }
        log_debug(f"📊 Инициализирован strategy_levels", user_id)
    
    log_debug(f"✅ stage2_current инициализирован: 0", user_id)
    
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    current = context.user_data.get("stage2_current", 0)
    
    questions = STAGE_2_QUESTIONS.get(perception_type, STAGE_2_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    total_questions = len(questions)  # 🔥 теперь 16
    
    log_debug(f"📝 ask_stage_2_question: current={current}, type={perception_type}, всего={total_questions}", user_id)
    log_to_file("stage2_questions.log", f"Вопрос {current+1}/{total_questions} type={perception_type}", user_id)
    
    context.user_data["conversation_state"] = STAGE_2
    
    if current >= total_questions:
        log_debug(f"🏁 Все вопросы заданы, завершаем этап 2", user_id)
        return await finish_stage_2(update, context)
    
    question = questions[current]
    
    # 🔥 ПОЛУЧАЕМ, ЧТО ИЗМЕРЯЕТ ВОПРОС
    measures = question.get("measures", "thinking")
    
    progress = calculate_progress(current + 1, total_questions)
    
    question_text = (
        f"🧠 <b>ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    
    for level_num, answer_text in question["options"].items():
        # 🔥 ИЗМЕНЕНО: добавляем measures в callback
        unique_callback = generate_unique_callback("stage2", user_id, current, level_num, measures)
        log_debug(f"   кнопка: {answer_text[:20]}... -> {unique_callback}", user_id)
        log_to_file("stage2_callbacks.log", f"Создан callback: {unique_callback}", user_id)
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
            log_debug(f"✅ Вопрос {current+1}/{total_questions} отправлен", user_id)
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
    
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # 🔥🔥🔥 АВАРИЙНОЕ ЛОГИРОВАНИЕ В ФАЙЛ
    log_to_file("stage2_answers.log", f"ПОЛУЧЕН CALLBACK: {query.data}", user_id)
    log_to_file("stage2_answers.log", f"stage2_current до: {context.user_data.get('stage2_current')}", user_id)
    log_to_file("stage2_answers.log", f"stage2_last_answered: {context.user_data.get('stage2_last_answered')}", user_id)
    
    # 🔥🔥🔥 АВАРИЙНОЕ ЛОГИРОВАНИЕ В КОНСОЛЬ
    print("\n" + "🔥"*50, file=sys.stderr, flush=True)
    print(f"🔥 handle_stage_2_answer CALLED", file=sys.stderr, flush=True)
    print(f"🔥 callback: {query.data}", file=sys.stderr, flush=True)
    print(f"🔥 user_id: {user_id}", file=sys.stderr, flush=True)
    print(f"🔥 user_data stage2_current: {context.user_data.get('stage2_current')}", file=sys.stderr, flush=True)
    print(f"🔥 user_data stage2_last_answered: {context.user_data.get('stage2_last_answered')}", file=sys.stderr, flush=True)
    print("🔥"*50, file=sys.stderr, flush=True)
    
    try:
        await query.answer()
    except Exception as e:
        log_debug(f"❌ Ошибка при answer(): {e}", user_id)
    
    if context.user_data.get("processing", False):
        log_debug(f"⏭️ Пропускаем повторное нажатие", user_id)
        return STAGE_2
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        log_debug(f"   parts: {parts}", user_id)
        log_to_file("stage2_answers.log", f"parts: {parts}", user_id)
        
        if len(parts) < 3 or parts[0] != "stage2":
            log_debug(f"❌ Неверный формат callback: {query.data}", user_id)
            log_to_file("stage2_errors.log", f"Неверный формат: {query.data}", user_id)
            return STAGE_2
        
        # 🔥 ИЗМЕНЕНО: парсим с учётом measures
        if len(parts) == 4:
            # Формат: stage2_0_1_thinking
            current = int(parts[1])
            selected_level = parts[2]
            measures = parts[3]
        elif len(parts) == 3:
            # Старый формат для обратной совместимости
            current = int(parts[1])
            selected_level = parts[2]
            measures = "thinking"
        else:
            log_debug(f"❌ Неверное количество частей: {len(parts)}", user_id)
            return STAGE_2
        
        log_debug(f"📥 Ответ на вопрос {current}, level={selected_level}, measures={measures}", user_id)
        log_to_file("stage2_answers.log", f"Ответ на вопрос {current}, level={selected_level}, measures={measures}", user_id)
        
        last_answered = context.user_data.get("stage2_last_answered", -1)
        if current <= last_answered:
            log_debug(f"⏭️ Вопрос {current} уже отвечен (last={last_answered})", user_id)
            log_to_file("stage2_answers.log", f"Вопрос {current} уже отвечен", user_id)
            return STAGE_2
        
        perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
        log_debug(f"   perception_type: {perception_type}", user_id)
        
        scoring_table = STAGE_2_SCORING.get(perception_type, {})
        log_debug(f"   scoring_table keys: {list(scoring_table.keys())}", user_id)
        
        # 🔥 СОХРАНЯЕМ ДЛЯ УРОВНЯ МЫШЛЕНИЯ (оригинальные вопросы)
        if measures == "thinking" and current in scoring_table and selected_level in scoring_table[current]:
            log_debug(f"   ✅ Найдены баллы для current={current}, level={selected_level}", user_id)
            
            if "stage2_level_scores_dict" not in context.user_data:
                context.user_data["stage2_level_scores_dict"] = {
                    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
                    "6": 0, "7": 0, "8": 0, "9": 0
                }
            
            points = scoring_table[current][selected_level]
            context.user_data["stage2_level_scores_dict"][selected_level] += points
            
            log_debug(f"   +{points} к уровню {selected_level}", user_id)
            log_debug(f"   теперь уровень {selected_level}: {context.user_data['stage2_level_scores_dict'][selected_level]}", user_id)
            log_to_file("stage2_scores.log", f"Q{current}: +{points} к уровню {selected_level}", user_id)
        
        # 🔥 НОВОЕ: СОХРАНЯЕМ ДЛЯ СТРАТЕГИЙ
        if measures in ["СБ", "ТФ", "УБ", "ЧВ"]:
            if "strategy_levels" not in context.user_data:
                context.user_data["strategy_levels"] = {
                    "СБ": [], "ТФ": [], "УБ": [], "ЧВ": []
                }
            
            # Преобразуем выбранный уровень в число и сохраняем
            try:
                value = int(selected_level)
                context.user_data["strategy_levels"][measures].append(value)
                log_debug(f"   +{value} к стратегии {measures}", user_id)
                log_to_file("stage2_strategies.log", f"Q{current}: +{value} к {measures}", user_id)
            except ValueError:
                log_debug(f"⚠️ Не удалось преобразовать {selected_level} в число", user_id)
        
        context.user_data["stage2_last_answered"] = current
        context.user_data["stage2_current"] = current + 1
        log_debug(f"   stage2_current увеличен до {current + 1}", user_id)
        log_to_file("stage2_answers.log", f"stage2_current теперь = {current + 1}", user_id)
        
        context.user_data["conversation_state"] = STAGE_2
        
        return await ask_stage_2_question(update, context)
        
    except Exception as e:
        log_debug(f"❌ Ошибка: {e}", user_id)
        log_to_file("stage2_errors.log", f"Исключение: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_stage_2_question(update, context)
    finally:
        context.user_data["processing"] = False
        log_debug(f"✅ handle_stage_2_answer FINISHED", user_id)

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2 - МОТИВАЦИОННЫЙ ЭКРАН"""
    query = update.callback_query
    user_id = update.effective_user.id
    level_scores_dict = context.user_data.get("stage2_level_scores_dict", {"1": 0})
    
    log_debug(f"🎯 finish_stage_2 вызван", user_id)
    log_to_file("stage2_finish.log", f"finish_stage_2 вызван", user_id)
    log_debug(f"📊 ИТОГОВЫЕ БАЛЛЫ ПО УРОВНЯМ:", user_id)
    for level in range(1, 10):
        score = level_scores_dict.get(str(level), 0)
        if score > 0:
            log_debug(f"   Уровень {level}: {score} баллов", user_id)
            log_to_file("stage2_finish.log", f"Уровень {level}: {score}", user_id)
    
    # 🔥 ЛОГИРУЕМ УРОВНИ СТРАТЕГИЙ
    strategy_levels = context.user_data.get("strategy_levels", {})
    if strategy_levels:
        log_debug(f"📊 УРОВНИ СТРАТЕГИЙ:", user_id)
        for strategy, values in strategy_levels.items():
            if values:
                avg = sum(values) / len(values)
                log_debug(f"   {strategy}: {values} → среднее {avg:.1f}", user_id)
                log_to_file("stage2_strategies.log", f"ИТОГО {strategy}: {values} → {avg:.1f}", user_id)
    
    needs_clarification = need_clarification_stage2(level_scores_dict)
    log_debug(f"📊 needs_clarification: {needs_clarification}", user_id)
    log_to_file("stage2_finish.log", f"needs_clarification: {needs_clarification}", user_id)
    
    if needs_clarification and not context.user_data.get("stage2_clarified", False):
        context.user_data["stage2_clarified"] = True
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage2"
        
        log_debug(f"🚀 Запуск уточнений stage2", user_id)
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    context.user_data["thinking_level"] = thinking_level
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    level_group = get_level_group(thinking_level)
    
    log_debug(f"✅ Stage 2 complete, level={thinking_level}, group={level_group}", user_id)
    log_to_file("stage2_finish.log", f"Stage 2 complete: level={thinking_level}, group={level_group}", user_id)
    
    result_text = STAGE2_FEEDBACK.get((perception_type, level_group))
    if not result_text:
        result_text = STAGE2_FEEDBACK[("СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ", "1-3")]
    
    keyboard = [[InlineKeyboardButton("▶️ Перейти к этапу 3 — Конфигурация поведения", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 finish_stage_2 → возвращаю STAGE_3 = {STAGE_3}", user_id)
    log_to_file("stage2_finish.log", f"Возвращаю STAGE_3 = {STAGE_3}", user_id)
    return STAGE_3
