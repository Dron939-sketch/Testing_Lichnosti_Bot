#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА - МИНИМАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
ВЕРСИЯ 6.3: ТОЛЬКО ТЕСТ, МАКСИМАЛЬНАЯ ДИАГНОСТИКА
"""

import logging
import os
import sys
import asyncio
import random
from typing import Dict, List, Optional, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ===== НАСТРОЙКА МАКСИМАЛЬНОГО ЛОГИРОВАНИЯ =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("bot_debug.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ===== ПРОСТЫЕ СОСТОЯНИЯ =====
STAGE_1 = 10
STAGE_2 = 20
STAGE_3 = 30
STAGE_4 = 40
RESULTS = 50

# ===== ВОПРОСЫ ДЛЯ ЭТАПА 1 =====
STAGE1_QUESTIONS = [
    {
        "text": "У вас неожиданно освободился вечер. Что звучит привлекательнее?",
        "options": {
            "a": "Позвать друзей",
            "b": "Побыть одному",
            "c": "Сходить куда-то (событие/место)",
            "d": "Почитать/посмотреть что-то"
        }
    },
    {
        "text": "Вы замечаете, что чаще всего обращаете внимание на:",
        "options": {
            "a": "Людей вокруг, их настроение и реакции",
            "b": "Свои внутренние ощущения и мысли",
            "c": "Обстановку, интерьер, вещи",
            "d": "Идеи, смыслы, символы"
        }
    },
    {
        "text": "В конфликтной ситуации вы скорее:",
        "options": {
            "a": "Попытаетесь понять другого человека",
            "b": "Прислушаетесь к себе",
            "c": "Обратите внимание на обстановку",
            "d": "Попытаетесь найти идеальное решение"
        }
    },
    {
        "text": "Что для вас важнее в фильме/книге?",
        "options": {
            "a": "Отношения между героями",
            "b": "Что я чувствую при просмотре",
            "c": "Визуал, картинка, детали",
            "d": "Идея, смысл, послание"
        }
    },
    {
        "text": "Выбирая подарок, вы думаете о:",
        "options": {
            "a": "Что обрадует этого конкретного человека",
            "b": "Что мне самому хотелось бы получить",
            "c": "Как это будет выглядеть",
            "d": "Какой смысл в этом подарке"
        }
    },
    {
        "text": "В новой компании вы обращаете внимание на:",
        "options": {
            "a": "Кто с кем общается",
            "b": "Комфортно ли мне",
            "c": "Интерьер, музыка, еда",
            "d": "О чем говорят, какие темы"
        }
    },
    {
        "text": "Когда вы злитесь, вам важно:",
        "options": {
            "a": "Высказать другому",
            "b": "Побыть в тишине",
            "c": "Сменить обстановку",
            "d": "Понять, в чем дело"
        }
    },
    {
        "text": "Что для вас важнее в работе?",
        "options": {
            "a": "Команда и отношения",
            "b": "Автономия и свобода",
            "c": "Условия и оплата",
            "d": "Смысл и цель"
        }
    }
]

STAGE1_FEEDBACK = "Отлично! Первый этап пройден. Теперь я лучше понимаю, как вы воспринимаете мир."

# ===== ТОКЕН =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7763554507:AAHLHX-7EceA3x0E9NKa0e0MNAtCx6FIBI0")
BOT_USERNAME = "Testing_Lichnosti_bot"

# ===== ФУНКЦИИ ЭТАПА 1 =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    logger.info(f"🚀 /start от пользователя {user.id} (@{user.username})")
    
    # Очищаем данные
    context.user_data.clear()
    
    welcome_text = (
        f"{user.first_name}, привет! 👋\n\n"
        f"<b>🧠 Я — Виртуальный психолог Вариатика.</b>\n\n"
        f"🕒 За 15 минут узнаете о себе то, что обычно остаётся невидимым.\n\n"
        f"<b>📊 Вас ждёт:</b>\n\n"
        f"1️⃣ Адаптивный тест (4 этапа)\n"
        f"   ↳ Поймёте свой уникальный профиль\n\n"
        f"🚀 Начнём исследование?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать исследование →", callback_data="start_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    return

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    logger.info(f"🎯 start_test вызван пользователем {user_id}")
    
    # Инициализируем данные
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    
    logger.info(f"📊 Данные инициализированы: {context.user_data}")
    
    # Показываем интро к этапу 1
    text = (
        "🧠 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ\n\n"
        "Как вы воспринимаете мир? Через людей, идеи, вещи или себя?\n\n"
        "Сейчас я задам 8 простых вопросов о повседневных ситуациях.\n"
        "Отвечайте быстро — первая реакция самая честная."
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Начать этап 1", callback_data="start_stage_1")],
        [InlineKeyboardButton("📋 Подробнее об этапе", callback_data="stage1_details")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    logger.info(f"✅ Интро этапа 1 показано пользователю {user_id}")
    
    return STAGE_1

async def stage1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробности этапа 1"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"📋 stage1_details вызван пользователем {query.from_user.id}")
    
    text = (
        "📋 ЧТО ТАКОЕ КОНФИГУРАЦИЯ ВОСПРИЯТИЯ?\n\n"
        "Это то, на что вы обращаете внимание в первую очередь:\n\n"
        "👥 Внешние (EXTERNAL) — фокус на других людях, их мнении\n"
        "🧠 Внутренние (INTERNAL) — фокус на своих ощущениях и мыслях\n"
        "💭 Символические (SYMBOLIC) — фокус на идеях и смыслах\n"
        "🏠 Материальные (MATERIAL) — фокус на вещах и обстановке"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_stage1_intro")]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к интро этапа 1"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"🔙 back_to_stage1_intro вызван пользователем {query.from_user.id}")
    
    text = (
        "🧠 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ\n\n"
        "Как вы воспринимаете мир? Через людей, идеи, вещи или себя?\n\n"
        "Сейчас я задам 8 простых вопросов о повседневных ситуациях.\n"
        "Отвечайте быстро — первая реакция самая честная."
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Начать этап 1", callback_data="start_stage_1")],
        [InlineKeyboardButton("📋 Подробнее об этапе", callback_data="stage1_details")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает этап 1 с первого вопроса"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    logger.info(f"▶️ start_stage_1 вызван пользователем {user_id}")
    
    # Проверяем и инициализируем данные
    if "stage1_current" not in context.user_data:
        context.user_data["stage1_current"] = 0
        logger.info(f"📊 stage1_current инициализирован = 0")
    
    if "scores" not in context.user_data:
        context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
        logger.info(f"📊 scores инициализирован")
    
    # Первый вопрос
    first_question = STAGE1_QUESTIONS[0]
    
    keyboard = []
    for opt_key, opt_text in first_question["options"].items():
        random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
        callback_data = f"stage1_0_{opt_key}_{user_id}_{random_suffix}"
        keyboard.append([InlineKeyboardButton(opt_text, callback_data=callback_data)])
    
    await query.edit_message_text(
        f"🧠 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ\n\n"
        f"{first_question['text']}\n\n"
        f"🧠 Не раздумывайте слишком долго — важна первая реакция\n\n"
        f"Вопрос 1/8\n▓░░░░░░░░░ 12%",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    logger.info(f"✅ Первый вопрос показан пользователю {user_id}")
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на вопрос этапа 1"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    logger.info(f"📝 ПОЛУЧЕН ОТВЕТ: {callback_data} от пользователя {user_id}")
    
    # Парсим callback_data
    import re
    pattern = r"stage1_(\d+)_([a-d])_(\d+)_(\w+)"
    match = re.match(pattern, callback_data)
    
    if not match:
        logger.error(f"❌ НЕ УДАЛОСЬ РАСПАРСИТЬ: {callback_data}")
        await query.edit_message_text(
            "❌ Произошла ошибка. Пожалуйста, начните этап заново.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Начать этап 1", callback_data="start_stage_1")
            ]])
        )
        return STAGE_1
    
    question_idx = int(match.group(1))
    option = match.group(2)
    
    logger.info(f"✅ Распарсено: вопрос={question_idx}, вариант={option}")
    
    # Инициализируем данные если нужно
    if "scores" not in context.user_data:
        context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    
    if "stage1_current" not in context.user_data:
        context.user_data["stage1_current"] = 0
    
    # Обновляем счетчики
    scores_map = {
        'a': {"EXTERNAL": 1},
        'b': {"INTERNAL": 1},
        'c': {"MATERIAL": 1},
        'd': {"SYMBOLIC": 1},
    }
    
    if option in scores_map:
        for key, value in scores_map[option].items():
            old = context.user_data["scores"].get(key, 0)
            context.user_data["scores"][key] = old + value
            logger.info(f"📊 {key}: {old} -> {context.user_data['scores'][key]}")
    
    # Увеличиваем счетчик
    context.user_data["stage1_current"] = question_idx + 1
    current = context.user_data["stage1_current"]
    logger.info(f"📊 Текущий вопрос: {current}/8")
    
    # Проверяем, все ли вопросы отвечены
    if current >= 8:
        logger.info(f"🎉 ЭТАП 1 ЗАВЕРШЕН для пользователя {user_id}")
        
        scores = context.user_data["scores"]
        feedback = f"""✅ <b>ЭТАП 1 ЗАВЕРШЕН!</b>

{STAGE1_FEEDBACK}

📊 <b>ВАШИ БАЛЛЫ:</b>
• Внешние (EXTERNAL): {scores.get('EXTERNAL', 0)}
• Внутренние (INTERNAL): {scores.get('INTERNAL', 0)}
• Символические (SYMBOLIC): {scores.get('SYMBOLIC', 0)}
• Материальные (MATERIAL): {scores.get('MATERIAL', 0)}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔍 Показать результаты", callback_data="show_results")]
        ]
        
        await query.edit_message_text(
            feedback,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return RESULTS
    
    # Показываем следующий вопрос
    next_question = STAGE1_QUESTIONS[current]
    
    keyboard = []
    for opt_key, opt_text in next_question["options"].items():
        random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
        callback_data = f"stage1_{current}_{opt_key}_{user_id}_{random_suffix}"
        keyboard.append([InlineKeyboardButton(opt_text, callback_data=callback_data)])
    
    progress_bar = "▓" * current + "░" * (8 - current)
    progress_percent = int((current / 8) * 100)
    
    await query.edit_message_text(
        f"🧠 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ\n\n"
        f"{next_question['text']}\n\n"
        f"Вопрос {current + 1}/8\n"
        f"{progress_bar} {progress_percent}%",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    logger.info(f"➡️ Показан вопрос {current + 1}/8")
    return STAGE_1

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает результаты"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    logger.info(f"📊 show_results вызван пользователем {user_id}")
    
    scores = context.user_data.get("scores", {})
    
    # Определяем тип (упрощенно)
    type_map = {
        "EXTERNAL": "SA",
        "INTERNAL": "SP", 
        "SYMBOLIC": "IA",
        "MATERIAL": "IP"
    }
    
    max_score = max(scores.items(), key=lambda x: x[1]) if scores else ("EXTERNAL", 0)
    type_code = type_map.get(max_score[0], "SA")
    
    message = f"""🧠 <b>ВАШ ПРОФИЛЬ</b>

📊 Тип: {type_code}-5_INT

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.

📊 <b>ВАШИ БАЛЛЫ:</b>
• Внешние: {scores.get('EXTERNAL', 0)}
• Внутренние: {scores.get('INTERNAL', 0)}
• Символические: {scores.get('SYMBOLIC', 0)}
• Материальные: {scores.get('MATERIAL', 0)}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="restart_test")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    
    return RESULTS

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"🔄 restart_test вызван пользователем {query.from_user.id}")
    
    context.user_data.clear()
    
    return await start_test(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    logger.info(f"❌ cancel вызван пользователем {update.effective_user.id}")
    await update.message.reply_text("👋 До свидания!")
    return ConversationHandler.END

# ===== ГЛАВНАЯ ФУНКЦИЯ =====

def main():
    """Запуск бота"""
    print("\n" + "="*70)
    print("🧠 ВИРТУАЛЬНЫЙ ПСИХОЛОГ - МИНИМАЛЬНАЯ ВЕРСИЯ 6.3")
    print("="*70)
    print(f"Токен: {TOKEN[:10]}...")
    print(f"Состояния: STAGE_1={STAGE_1}")
    print("="*70)
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$"),
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(stage1_details, pattern="^stage1_details$"),
                CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$"),
                CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_"),
            ],
            RESULTS: [
                CallbackQueryHandler(show_results, pattern="^show_results$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        name="test_conversation",
        persistent=False,
    )
    
    application.add_handler(conv_handler)
    
    # Добавляем обработчик для всего остального (для отладки)
    async def catch_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.warning(f"⚠️ НЕОБРАБОТАННЫЙ callback: {update.callback_query.data}")
        await update.callback_query.answer("⚠️ Необработанный запрос")
    
    application.add_handler(CallbackQueryHandler(catch_all), group=1)
    
    print("\n🚀 Бот запускается...")
    print("="*30)
    
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query'],
        poll_interval=1.0
    )

if __name__ == "__main__":
    main()
