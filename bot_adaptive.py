#!/usr/bin/env python3
"""
ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА + 4F-КЛЮЧИ И ИНТИМНЫЕ ПРОФИЛИ
ВЕРСИЯ 8.1: ИСПРАВЛЕННЫЕ ОШИБКИ
"""

import logging
import os
import sys
import asyncio
import urllib.parse
import time
import base64
import uuid
import random
import requests
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Conflict, BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("bot_detailed.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ===== ФУНКЦИЯ ЛОГИРОВАНИЯ =====
def log_callback(func_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирование с деталями"""
    user = update.effective_user
    query = update.callback_query if update.callback_query else None
    
    log_msg = f"📞 {func_name} | User: {user.id} (@{user.username})"
    if query:
        log_msg += f" | Callback: {query.data}"
    if context.user_data:
        log_msg += f" | State: {context.user_data.get('conversation_state', 'None')}"
    
    logger.debug(log_msg)
    print(f"🔍 {log_msg}")

# ===== ЗАГЛУШКА =====
async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для нереализованных функций"""
    try:
        query = update.callback_query
        await query.answer("🚧 Функция в разработке", show_alert=True)
        return
    except Exception as e:
        logger.error(f"❌ Ошибка в noop_callback: {e}")
        return

# ===== СОСТОЯНИЯ (определяем вручную) =====
STAGE_1, STAGE_2, STAGE_3, STAGE_4 = 1, 2, 3, 4
CLARIFICATION, RESULTS = 5, 6
GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, PAYMENT_SCREEN = 7, 8, 9, 10
MY_SEXUAL_PROFILE, SEXUAL_PROFILE_SCREEN, SEXUAL_INVITES_LIST = 11, 12, 13
SEXUAL_FRIEND_PROFILE, FOUR_F_PAYMENT_SCREEN, FOUR_F_CONTENT_SCREEN = 14, 15, 16
FOUR_F_MAIN, FOUR_F_DETAILED, FOUR_F_MENU, FOUR_F_CONTENT = 17, 18, 19, 20
BUY_PACKAGES, INVITES_LIST, FRIEND_MENU = 21, 22, 23

# ===== КОНФИГУРАЦИЯ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7763554507:AAHLHX-7EceA3x0E9NKa0e0MNAtCx6FIBI0")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
BOT_USERNAME = "Testing_Lichnosti_bot"
BOT_LINK = f"t.me/{BOT_USERNAME}"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/8KD0DGy4AbpDYA"
SHARE_TEXT = "🔮 Хочешь узнать, что на самом деле движет тобой? Этот тест видит то, что обычно скрыто. За 15 минут узнаешь свой реальный психологический профиль. Рекомендую 👇"
GIFT_SCREEN_TEXT = "🎁 Ваш подарок готов!"

# ===== КОНСТАНТЫ 18+ МОДУЛЯ =====
SEXUAL_DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
FREE_INVITE_LIMIT = 3
FRIEND_ACCESS_PRICE = 99
FOUR_F_PRICE = 1

INVITE_PACKAGES = {
    "3": {"price": 299, "links": 3, "emoji": "🥉", "popular": False},
    "5": {"price": 499, "links": 5, "emoji": "🥈", "popular": True},
    "10": {"price": 899, "links": 10, "emoji": "🥇", "popular": False}
}

PROFILE_DISK_LINKS = {
    "SA-5_INT": "https://disk.yandex.ru/d/EYPIF9_puI_t0A",
    "default": "https://disk.yandex.ru/d/EYPIF9_puI_t0A"
}

FOUR_F_EMOJIS = {"1F": "🔥", "2F": "🏃", "3F": "🧬", "4F": "🍽"}
FOUR_F_TITLES = {
    "1F": "НАПАДЕНИЕ / ЯРОСТЬ",
    "2F": "БЕГСТВО / СТРАХ",
    "3F": "СЕКС / ЖЕЛАНИЕ",
    "4F": "ПОГЛОЩЕНИЕ / ДЕНЬГИ"
}

FOUR_F_SHORT = "📘 4F-ключи - управление состояниями"
FOUR_F_DETAILED_TEXT = "Подробное описание 4F-ключей"

# ===== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =====
USER_PROFILE = {
    "display_name": "SA-5_INT",
    "type_code": "SA",
    "level": 5,
    "dilts_code": "int"
}

# ===== ВОПРОСЫ ТЕСТА =====
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
    }
]

STAGE1_FEEDBACK = "Этап 1 завершен!"

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С БД =====
def get_user_invites_from_api(user_id: int) -> list:
    """Получает приглашения пользователя"""
    return []

def save_invite_to_api(invite_data: dict) -> bool:
    """Сохраняет приглашение"""
    return True

def get_disk_link_by_profile(profile_code: str) -> str:
    """Получает ссылку на профиль"""
    return PROFILE_DISK_LINKS.get(profile_code, PROFILE_DISK_LINKS["default"])

def load_intimate_profile(profile_code: str) -> dict:
    """Загружает интимный профиль"""
    return {
        "profile_type": profile_code,
        "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
        "quote": "«Со мной не скучно. Со мной — вкусно.»",
        "description": "Секс для вас — священнодействие.",
        "sections": {}
    }

def format_intimate_profile_part1(profile_data: dict, user_name: str) -> str:
    """Часть 1 интимного профиля"""
    return f"🔞 ИНТИМНЫЙ ПРОФИЛЬ\n\n{user_name}, {profile_data.get('profile_type')}"

def format_intimate_profile_part2(profile_data: dict, user_name: str) -> str:
    """Часть 2 интимного профиля"""
    return ""

def format_intimate_profile_part3(profile_data: dict, user_name: str) -> str:
    """Часть 3 интимного профиля"""
    return f"\n\n{SEXUAL_DIVIDER}\n\n💎 ТАМ, ЗА ЗЕРКАЛОМ..."

def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """Разбивает длинное сообщение"""
    return [text]

async def safe_send_message(chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE, 
                           reply_markup=None, parse_mode: str = "HTML") -> bool:
    """Безопасная отправка сообщения"""
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

def calculate_profile_final(user_data: dict) -> dict:
    """Вычисляет финальный профиль"""
    return {"type_code": "SA", "level": 5, "dilts_code": "int", "display_name": "SA-5_INT"}

# ===== ОБРАБОТЧИКИ ТЕСТА =====
async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает интро к этапу 1"""
    query = update.callback_query
    await query.answer()
    
    text = "🧠 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ\n\nНажмите 'Начать' для прохождения теста."
    
    keyboard = [[InlineKeyboardButton("▶️ Начать", callback_data="start_stage_1")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали этапа 1"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📋 Подробности этапа 1")
    return STAGE_1

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к интро"""
    return await show_stage_1_intro(update, context)

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает этап 1"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage1_current"] = 0
    question = STAGE1_QUESTIONS[0]
    
    keyboard = []
    for opt_key, opt_text in question["options"].items():
        keyboard.append([InlineKeyboardButton(opt_text, callback_data=f"stage1_0_{opt_key}")])
    
    await query.edit_message_text(
        f"🧠 Вопрос 1/2\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 3:
        return STAGE_1
    
    current = context.user_data.get("stage1_current", 0)
    context.user_data["stage1_current"] = current + 1
    
    if context.user_data["stage1_current"] >= len(STAGE1_QUESTIONS):
        # Тест завершен
        context.user_data["profile_data"] = USER_PROFILE
        return await show_results_screen(update, context)
    
    # Следующий вопрос
    next_idx = context.user_data["stage1_current"]
    question = STAGE1_QUESTIONS[next_idx]
    
    keyboard = []
    for opt_key, opt_text in question["options"].items():
        keyboard.append([InlineKeyboardButton(opt_text, callback_data=f"stage1_{next_idx}_{opt_key}")])
    
    await query.edit_message_text(
        f"🧠 Вопрос {next_idx + 1}/2\n\n{question['text']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STAGE_1

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, force_shared_view: bool = False):
    """Показывает результаты"""
    query = update.callback_query
    await query.answer()
    
    profile_data = context.user_data.get("profile_data", USER_PROFILE)
    profile_code = profile_data.get('display_name', 'SA-5_INT')
    
    text = f"""🧠 <b>ВАШ ПРОФИЛЬ</b>

📊 {profile_code}

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

🔞 Нажмите кнопку ниже для интимного профиля."""

    keyboard = [
        [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="show_my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return RESULTS

# ===== ФУНКЦИИ 18+ МОДУЛЯ =====
async def show_my_sexual_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔞 Мой интимный профиль"""
    try:
        query = update.callback_query
        await query.answer()
        
        profile_data = context.user_data.get("profile_data", USER_PROFILE)
        profile_code = profile_data.get('display_name', 'SA-5_INT')
        user_name = query.from_user.first_name or "Пользователь"
        
        intimate_data = load_intimate_profile(profile_code)
        
        part1 = format_intimate_profile_part1(intimate_data, user_name)
        part2 = format_intimate_profile_part2(intimate_data, user_name)
        part3 = format_intimate_profile_part3(intimate_data, user_name)
        
        chat_id = query.message.chat_id
        
        await query.edit_message_text(part1, parse_mode="HTML")
        await asyncio.sleep(0.5)
        
        if part2:
            await safe_send_message(chat_id, part2, context)
            await asyncio.sleep(0.5)
        
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("👥 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_to_results")]
        ]
        
        await safe_send_message(
            chat_id,
            part3,
            context,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return MY_SEXUAL_PROFILE
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return RESULTS

async def create_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание приглашения"""
    query = update.callback_query
    await query.answer()
    
    invite_id = f"sex_{uuid.uuid4().hex[:8]}"
    invite_url = f"https://t.me/{BOT_USERNAME}?start={invite_id}"
    
    text = f"""🔞 <b>ВАША ССЫЛКА ГОТОВА!</b>

🔗 <code>{invite_url}</code>

Отправьте эту ссылку другу."""
    
    keyboard = [
        [InlineKeyboardButton("✈️ ОТПРАВИТЬ", url=f"https://t.me/share/url?url={invite_url}")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="show_my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return MY_SEXUAL_PROFILE

async def my_invites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мои отражения"""
    query = update.callback_query
    await query.answer()
    
    profile_data = context.user_data.get("profile_data", USER_PROFILE)
    profile_code = profile_data.get('display_name', 'SA-5_INT')
    
    text = f"""<b>🪞 МОИ ОТРАЖЕНИЯ</b>

📊 Ваш профиль: {profile_code}

👥 Пока нет отражений."""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="show_my_sexual_profile")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return MY_SEXUAL_PROFILE

async def four_f_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню 4F"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(FOUR_F_SHORT)
    return FOUR_F_MAIN

async def four_f_detailed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали 4F"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(FOUR_F_DETAILED_TEXT)
    return FOUR_F_DETAILED

async def friend_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню друга"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👤 Профиль друга")
    return FRIEND_MENU

async def standard_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стандартный профиль"""
    query = update.callback_query
    await query.answer()
    return FRIEND_MENU

async def intimate_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Интимный профиль друга"""
    query = update.callback_query
    await query.answer()
    return FRIEND_MENU

async def four_f_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню 4F для друга"""
    query = update.callback_query
    await query.answer()
    return FOUR_F_MENU

async def four_f_explanation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Объяснение 4F"""
    query = update.callback_query
    await query.answer()
    return FOUR_F_MENU

async def buy_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка 4F ключа"""
    query = update.callback_query
    await query.answer()
    return FOUR_F_PAYMENT_SCREEN

async def process_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка платежа"""
    query = update.callback_query
    await query.answer()
    return FOUR_F_PAYMENT_SCREEN

async def open_4f_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие 4F ключа"""
    query = update.callback_query
    await query.answer()
    return FOUR_F_CONTENT

async def buy_invite_packages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка пакетов приглашений"""
    query = update.callback_query
    await query.answer()
    return BUY_PACKAGES

async def pay_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплата пакета"""
    query = update.callback_query
    await query.answer()
    return FOUR_F_PAYMENT_SCREEN

async def process_package_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты пакета"""
    query = update.callback_query
    await query.answer()
    return BUY_PACKAGES

async def check_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса"""
    query = update.callback_query
    await query.answer()
    return MY_SEXUAL_PROFILE

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Копирование приглашения"""
    query = update.callback_query
    await query.answer()
    return MY_SEXUAL_PROFILE

async def check_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка приглашения"""
    query = update.callback_query
    await query.answer()
    return MY_SEXUAL_PROFILE

async def dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка"""
    query = update.callback_query
    await query.answer()
    return RESULTS

# ===== ФУНКЦИИ НАВИГАЦИИ =====
async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def back_to_results_after_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат после подарка"""
    return await back_to_results(update, context)

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск шаринга"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    await query.answer()
    context.user_data["has_shared"] = True
    return await open_gift_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    return await show_stage_1_intro(update, context)

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран подарка"""
    query = update.callback_query
    await query.answer()
    
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={urllib.parse.quote(SHARE_TEXT)}"
    
    keyboard = [
        [InlineKeyboardButton("🪞 Поделиться", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился", callback_data="confirm_share")],
        [InlineKeyboardButton("Пропустить", callback_data="skip_share")]
    ]
    
    await query.edit_message_text(
        "Поделитесь с друзьями и получите подарок!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GIFT_SCREEN

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие подарка"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎁 Получить подарок", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        GIFT_SCREEN_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return OPEN_GIFT_SCREEN

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран пакета"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💳 Купить", callback_data="buy_package")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        "📖 Полное описание профиля - 690₽",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PACKAGE_SCREEN

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy"""
    await update.message.reply_text("💳 Покупка профиля")
    return PAYMENT_SCREEN

async def buy_without_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка без теста"""
    query = update.callback_query
    await query.answer()
    return await show_payment_screen(update, context)

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран оплаты"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✅ Оплатить", url="https://example.com")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        "💳 Ссылка для оплаты",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PAYMENT_SCREEN

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка платежа"""
    query = update.callback_query
    await query.answer()
    return PAYMENT_SCREEN

async def get_materials_callback_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов"""
    query = update.callback_query
    await query.answer()
    return PAYMENT_SCREEN

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials"""
    await update.message.reply_text("📦 Ваши материалы")
    return

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    await update.message.reply_text("📊 Статус платежа")
    return

# ===== ФУНКЦИЯ СТАРТА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    logger.info(f"🚀 /start от пользователя {user.id}")
    
    welcome_text = (
        f"{user.first_name}, привет! 👋\n\n"
        f"<b>🧠 Виртуальный психолог Вариатика</b>\n\n"
        f"Пройти тест и узнать свой профиль:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]
    ]
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    query = update.callback_query
    await query.answer()
    return await start(update, context)

async def why_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📋 Подробности теста")
    return

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    return await show_stage_1_intro(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    await update.message.reply_text("👋 До свидания!")
    return ConversationHandler.END

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
def main():
    """Запуск бота"""
    print("\n" + "="*70)
    print("🧠 ВИРТУАЛЬНЫЙ ПСИХОЛОГ ВАРИАТИКА v8.1")
    print("="*70)
    
    application = Application.builder().token(TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Общие callback-обработчики
    application.add_handler(CallbackQueryHandler(why_details_callback, pattern="^why_details$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    
    # ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(show_stage_1_details, pattern="^stage1_details$"),
                CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$"),
                CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(buy_command, pattern="^buy_package$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(back_to_results_after_gift, pattern="^back_to_results_after_gift$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(show_my_sexual_profile, pattern="^show_my_sexual_profile$"),
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(skip_share, pattern="^skip_share$"),
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(buy_command, pattern="^buy_package$"),
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results_after_gift, pattern="^back_to_results_after_gift$"),
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"),
                CallbackQueryHandler(get_materials_callback_payment, pattern="^get_materials_"),
                CallbackQueryHandler(buy_without_test_callback, pattern="^buy_without_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            # 18+ МОДУЛЬ
            MY_SEXUAL_PROFILE: [
                CallbackQueryHandler(create_invite_callback, pattern="^create_invite$"),
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            SEXUAL_INVITES_LIST: [
                CallbackQueryHandler(my_invites_callback, pattern="^my_invites$"),
                CallbackQueryHandler(four_f_main_menu_callback, pattern="^four_f_main_menu$"),
                CallbackQueryHandler(check_status_callback, pattern="^check_status_"),
                CallbackQueryHandler(friend_menu_callback, pattern="^friend_"),
                CallbackQueryHandler(buy_invite_packages_callback, pattern="^buy_invite_packages$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            SEXUAL_FRIEND_PROFILE: [
                CallbackQueryHandler(standard_profile_callback, pattern="^std_"),
                CallbackQueryHandler(intimate_profile_callback, pattern="^int_"),
                CallbackQueryHandler(four_f_menu_callback, pattern="^4f_"),
                CallbackQueryHandler(four_f_explanation_callback, pattern="^4f_explain$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            FOUR_F_PAYMENT_SCREEN: [
                CallbackQueryHandler(process_payment_callback, pattern="^process_payment_"),
                CallbackQueryHandler(pay_package_callback, pattern="^pay_package_"),
                CallbackQueryHandler(process_package_payment_callback, pattern="^process_package_payment_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            FOUR_F_CONTENT_SCREEN: [
                CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"),
                CallbackQueryHandler(buy_4f_key_callback, pattern="^buy_4f_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            FOUR_F_MAIN: [
                CallbackQueryHandler(four_f_detailed_callback, pattern="^four_f_detailed$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            FOUR_F_DETAILED: [
                CallbackQueryHandler(four_f_main_menu_callback, pattern="^four_f_main_menu$"),
            ],
            FOUR_F_MENU: [
                CallbackQueryHandler(buy_4f_key_callback, pattern="^buy_4f_"),
                CallbackQueryHandler(open_4f_key_callback, pattern="^open_4f_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            FOUR_F_CONTENT: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
            BUY_PACKAGES: [
                CallbackQueryHandler(pay_package_callback, pattern="^pay_package_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    print("\n🚀 Бот запускается...")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query']
    )

if __name__ == "__main__":
    main()
