"""
Обработчики для ЭТАПА 4: Конфликт логических уровней
ИСПРАВЛЕННАЯ ВЕРСИЯ:
✅ Добавлено сохранение ответов для AI
✅ Добавлены метрики времени
✅ Динамическое отображение количества вопросов
✅ Улучшен экран аналитики
✅ Константы для таймаутов
"""

import logging
import sys
import os
import time
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

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

# Константы
TOTAL_QUESTIONS = len(STAGE_4_QUESTIONS)  # 8 вопросов
TIME_PER_QUESTION = 0.4  # минут на вопрос
ANALYSIS_SCREEN_DELAY = 3  # секунд для экрана аналитики

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔵 show_stage_4_intro ВЫЗВАН", user_id)
    log_to_file("stage4_intro.log", f"show_stage_4_intro вызван", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    log_debug(f"💾 Сохраняю состояние STAGE_4 = {STAGE_4}", user_id)
    
    await query.answer()
    
    estimated_time = round(TOTAL_QUESTIONS * TIME_PER_QUESTION)
    
    intro_text = (
    f"🧠 <b>ЭТАП 4: ТОЧКА РОСТА</b>\n\n"
    f"Восприятие — что вы видите.\n"
    f"Мышление — как понимаете.\n"
    f"Поведение — как реагируете.\n"
    f"Всё это — ваша внутренняя система.\n\n"
    f"🌍 Но она живёт внутри внешней системы —\n"
    f"общества, которое постоянно меняется.\n\n"
    f"⚡ Когда одна система меняется,\n"
    f"а другая — нет,\n"
    f"возникает напряжение.\n\n"
    f"🔍 Здесь мы найдём, где именно\n"
    f"могут возникать потенциальные точки напряжения\n"
    f"между вашей системой и системой, в которой вы находитесь.\n\n"
    f"📊 <b>Вопросов:</b> {TOTAL_QUESTIONS}\n"
    f"⏱ <b>Время:</b> ~{estimated_time} минуты"
)
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Подробнее об этапе", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать исследование", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 show_stage_4_intro → возвращаю STAGE_4 = {STAGE_4}", user_id)
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"📋 show_stage_4_details ВЫЗВАН", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    log_debug(f"💾 Сохраняю состояние STAGE_4 = {STAGE_4}", user_id)
    
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
    f"<b>Оно может быть в разных местах:</b>\n"
    f"• В том, что вас окружает\n"
    f"• В том, что вы делаете\n"
    f"• В том, что вы умеете\n"
    f"• В том, что для вас важно\n"
    f"• В том, кем вы себя считаете\n\n"
    f"🔍 <b>Что мы ищем?</b>\n\n"
    f"- Мы ищем не слабое место,\n"
    f"а точку опоры — рычаг.\n"
    f"- Место, где минимальное усилие\n"
    f"даёт максимальные изменения.\n"
    f"- Сдвинув эту точку в своей системе,\n"
    f"вы меняете всё остальное —\n"
    f"и внутри, и вовне.\n\n"
    f"Сейчас просто посмотрим,\n"
    f"где именно может находиться этот рычаг."
)
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    
    log_debug(f"🔄 show_stage_4_details → возвращаю STAGE_4 = {STAGE_4}", user_id)
    return STAGE_4

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 4"""
    user_id = update.effective_user.id
    log_debug(f"⬅️ back_to_stage4_intro ВЫЗВАН", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    
    return await show_stage_4_intro(update, context)

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    log_debug(f"🔥🔥🔥 start_stage_4 ВЫЗВАН! User: {user_id}", user_id)
    log_debug(f"📊 username=@{query.from_user.username}", user_id)
    log_to_file("stage4_start.log", f"start_stage_4", user_id)
    
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    context.user_data["stage4_last_answered"] = -1
    context.user_data["stage4_start_time"] = time.time()  # для метрик
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    log_debug(f"💾 Сохраняю состояние STAGE_4 = {STAGE_4}", user_id)
    
    # Инициализируем хранилище для AI
    if "all_answers" not in context.user_data:
        context.user_data["all_answers"] = []
    
    # Инициализируем список ответов
    if "stage4_dilts_answers" not in context.user_data:
        context.user_data["stage4_dilts_answers"] = []
        log_debug(f"📊 Инициализирован stage4_dilts_answers", user_id)
    
    # 🔥 НОВОЕ: инициализируем счётчики для 5 уровней Дилтса
    if "dilts_counts" not in context.user_data:
        context.user_data["dilts_counts"] = {
            "ENVIRONMENT": 0,
            "BEHAVIOR": 0,
            "CAPABILITIES": 0,
            "VALUES": 0,
            "IDENTITY": 0
        }
        log_debug(f"📊 Инициализирован dilts_counts с 5 уровнями", user_id)
    
    log_debug(f"✅ stage4_current инициализирован: 0", user_id)
    
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    current = context.user_data.get("stage4_current", 0)
    
    log_debug(f"📝 ask_stage_4_question: current={current}", user_id)
    log_to_file("stage4_questions.log", f"Вопрос {current+1}/{TOTAL_QUESTIONS}", user_id)
    
    # ✅ ВАЖНО: сохраняем состояние
    context.user_data["conversation_state"] = STAGE_4
    
    if current >= TOTAL_QUESTIONS:
        log_debug(f"🏁 Все вопросы заданы, завершаем этап 4", user_id)
        return await finish_stage_4(update, context)
    
    question = STAGE_4_QUESTIONS[current]
    progress = calculate_progress(current + 1, TOTAL_QUESTIONS)
    
    question_text = (
        f"🧠 <b>ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    
    for option_id, option in question["options"].items():
        # 🔥 ИЗМЕНЕНО: теперь 5 вариантов (a, b, c, d, e)
        unique_callback = generate_unique_callback("stage4", user_id, current, option_id)
        log_debug(f"   кнопка: {option['text'][:20]}... -> {unique_callback}", user_id)
        log_to_file("stage4_callbacks.log", f"Создан callback: {unique_callback}", user_id)
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
            log_debug(f"✅ Вопрос {current+1}/{TOTAL_QUESTIONS} отправлен", user_id)
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
    
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 4"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # 🔥🔥🔥 АВАРИЙНОЕ ЛОГИРОВАНИЕ
    log_to_file("stage4_answers.log", f"ПОЛУЧЕН CALLBACK: {query.data}", user_id)
    log_to_file("stage4_answers.log", f"stage4_current до: {context.user_data.get('stage4_current')}", user_id)
    log_to_file("stage4_answers.log", f"stage4_last_answered: {context.user_data.get('stage4_last_answered')}", user_id)
    
    print("\n" + "🔥"*50, file=sys.stderr, flush=True)
    print(f"🔥 handle_stage_4_answer CALLED", file=sys.stderr, flush=True)
    print(f"🔥 callback: {query.data}", file=sys.stderr, flush=True)
    print(f"🔥 user_id: {user_id}", file=sys.stderr, flush=True)
    print("🔥"*50, file=sys.stderr, flush=True)
    
    try:
        await query.answer()
    except Exception as e:
        log_debug(f"❌ Ошибка при answer(): {e}", user_id)
    
    if context.user_data.get("processing", False):
        log_debug(f"⏭️ Пропускаем повторное нажатие", user_id)
        return STAGE_4
    
    context.user_data["processing"] = True
    
    try:
        parts = query.data.split("_")
        log_debug(f"   parts: {parts}", user_id)
        log_to_file("stage4_answers.log", f"parts: {parts}", user_id)
        
        if len(parts) < 3 or parts[0] != "stage4":
            log_debug(f"❌ Неверный формат callback: {query.data}", user_id)
            log_to_file("stage4_errors.log", f"Неверный формат: {query.data}", user_id)
            return STAGE_4
        
        current = int(parts[1])
        option_id = parts[2]
        
        log_debug(f"📥 Ответ на вопрос {current}, option={option_id}", user_id)
        log_to_file("stage4_answers.log", f"Ответ на вопрос {current}, option={option_id}", user_id)
        
        last_answered = context.user_data.get("stage4_last_answered", -1)
        if current <= last_answered:
            log_debug(f"⏭️ Вопрос {current} уже отвечен (last={last_answered})", user_id)
            log_to_file("stage4_answers.log", f"Вопрос {current} уже отвечен", user_id)
            return STAGE_4
        
        question = STAGE_4_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            log_debug(f"❌ Опция {option_id} не найдена", user_id)
            log_to_file("stage4_errors.log", f"Опция {option_id} не найдена", user_id)
            return STAGE_4
        
        # 🔥 ИЗМЕНЕНО: теперь получаем dilts из option
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        
        # 🔥 НОВОЕ: сохраняем в счётчики
        if "dilts_counts" not in context.user_data:
            context.user_data["dilts_counts"] = {
                "ENVIRONMENT": 0,
                "BEHAVIOR": 0,
                "CAPABILITIES": 0,
                "VALUES": 0,
                "IDENTITY": 0
            }
        
        context.user_data["dilts_counts"][dilts] += 1
        
        # Сохраняем также в список для обратной совместимости
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        # 👇 СОХРАНЯЕМ ОТВЕТ ДЛЯ AI
        if "all_answers" not in context.user_data:
            context.user_data["all_answers"] = []
        
        context.user_data["all_answers"].append({
            'stage': 4,
            'question_index': current,
            'question': question['text'],
            'answer': selected_option['text'],
            'option': option_id,
            'dilts': dilts
        })
        log_debug(f"   💾 Ответ сохранён для AI", user_id)
        
        log_debug(f"✅ + dilts={dilts} (теперь всего: {context.user_data['dilts_counts'][dilts]})", user_id)
        log_to_file("stage4_scores.log", f"Q{current}: + dilts={dilts}", user_id)
        log_debug(f"   теперь stage4_answers: {context.user_data['stage4_dilts_answers']}", user_id)
        
        context.user_data["stage4_last_answered"] = current
        context.user_data["stage4_current"] = current + 1
        log_debug(f"   stage4_current увеличен до {current + 1}", user_id)
        log_to_file("stage4_answers.log", f"stage4_current теперь = {current + 1}", user_id)
        
        # ✅ ВАЖНО: сохраняем состояние
        context.user_data["conversation_state"] = STAGE_4
        
        return await ask_stage_4_question(update, context)
        
    except Exception as e:
        log_debug(f"❌ Ошибка: {e}", user_id)
        log_to_file("stage4_errors.log", f"Исключение: {e}", user_id)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return await ask_stage_4_question(update, context)
    finally:
        context.user_data["processing"] = False
        log_debug(f"✅ handle_stage_4_answer FINISHED", user_id)

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 - ЭКРАН АНАЛИТИКИ ПЕРЕД РЕЗУЛЬТАТАМИ"""
    query = update.callback_query
    user_id = update.effective_user.id
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    dilts_counts = context.user_data.get("dilts_counts", {})
    
    log_debug(f"🎯 finish_stage_4 вызван", user_id)
    log_to_file("stage4_finish.log", f"finish_stage_4 вызван", user_id)
    log_debug(f"📊 dilts_answers={dilts_answers}", user_id)
    log_to_file("stage4_finish.log", f"dilts_answers={dilts_answers}", user_id)
    
    # 👇 ЛОГИРУЕМ МЕТРИКИ ВРЕМЕНИ
    if "stage4_start_time" in context.user_data:
        elapsed = time.time() - context.user_data["stage4_start_time"]
        logger.info(f"📊 User {user_id}: Stage 4 completed in {elapsed:.1f} seconds")
        log_to_file("stage4_metrics.log", f"time:{elapsed:.1f}", user_id)
        log_to_file("stage4_metrics.log", f"answers:{len(dilts_answers)}", user_id)
    
    # 🔥 ЛОГИРУЕМ ИТОГОВЫЕ СЧЁТЧИКИ
    if dilts_counts:
        log_debug(f"📊 ИТОГОВЫЕ СЧЁТЧИКИ ДИЛТСА:", user_id)
        total = sum(dilts_counts.values())
        for level, count in dilts_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            log_debug(f"   {level}: {count} ({percentage:.1f}%)", user_id)
            log_to_file("stage4_finish.log", f"{level}: {count} ({percentage:.1f}%)", user_id)
    
    needs_clarification = need_clarification_stage4(dilts_answers)
    log_debug(f"📊 needs_clarification: {needs_clarification}", user_id)
    log_to_file("stage4_finish.log", f"needs_clarification: {needs_clarification}", user_id)
    
    if needs_clarification and not context.user_data.get("stage4_clarified", False):
        context.user_data["stage4_clarified"] = True
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage4"
        
        log_debug(f"🚀 Запуск уточнений stage4", user_id)
        log_to_file("stage4_finish.log", f"Запуск уточнений stage4", user_id)
        from handlers.common import ask_clarification_question
        return await ask_clarification_question(update, context)
    
    # 🔥 ИЗМЕНЕНО: определяем доминирующий уровень Дилтса
    if dilts_counts:
        # Находим уровень с максимальным количеством
        dominant_dilts = max(dilts_counts.items(), key=lambda x: x[1])[0]
        context.user_data["dominant_dilts"] = dominant_dilts
        log_debug(f"🏆 Доминирующий уровень Дилтса: {dominant_dilts}", user_id)
        log_to_file("stage4_finish.log", f"Доминирующий уровень: {dominant_dilts}", user_id)
    
    profile_data = calculate_profile_final(context.user_data)
    context.user_data["profile_data"] = profile_data
    
    log_debug(f"✅ Stage 4 complete, profile={profile_data.get('display_name', 'unknown')}", user_id)
    log_to_file("stage4_finish.log", f"Stage 4 complete: {profile_data.get('display_name', 'unknown')}", user_id)
    
    # 🔥 УЛУЧШЕННЫЙ ЭКРАН АНАЛИТИКИ
    analysis_text = f"""
🧠 <b>АНАЛИЗИРУЮ ДАННЫЕ</b>

<b>Соединяются четыре слоя информации:</b>
▸ ✅ Конфигурация восприятия — определена
▸ ✅ Конфигурация мышления — проанализирована
▸ ✅ Конфигурация поведения — обработана
▸ ✅ Точка напряжения — найдена

<b>Формирую ваш уникальный профиль...</b>

⏳ Пожалуйста, подождите несколько секунд...
"""
    
    await query.edit_message_text(analysis_text.strip(), parse_mode="HTML")
    
    await asyncio.sleep(ANALYSIS_SCREEN_DELAY)
    
    from handlers.results import show_results_screen
    
    result = await show_results_screen(update, context)
    log_debug(f"🔄 finish_stage_4 → возвращаю RESULTS = {RESULTS}", user_id)
    log_to_file("stage4_finish.log", f"Возвращаю RESULTS = {RESULTS}", user_id)
    return result
