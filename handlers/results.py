"""
Обработчики для экрана результатов
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# ИСПРАВЛЕНО: Импортируем константу из constants.py вместо config.py
from constants import RESULTS
from config import GIFT_PDF_LINK, BOT_LINK, SHARE_TEXT, GIFT_SCREEN_TEXT, logger
from questions import STANDARD_SUFFIXES, SUFFIX_TO_DILTS, CONFLICT_PHRASES
from utils.calculations import calculate_profile_final
from utils.profile_utils import get_profile_fallback, get_discrepancy_note
from utils.text_utils import get_card_description_from_profile, format_profile_title

# Импорт из 18+ модуля для ссылок
from sexual_18_plus import get_disk_link_by_profile

# Импорт загрузчика и профилей
from loader import loader

class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

async def show_results_screen(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    force_shared_view: bool = False
):
    """ЭКРАН РЕЗУЛЬТАТОВ с 18+ кнопкой"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"📊 show_results_screen ВЫЗВАН для пользователя {user_id}")
    
    has_shared = context.user_data.get("has_shared", False) or force_shared_view
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    try:
        profile = get_profile_fallback(profile_data)
    except ProfileNotFoundError as e:
        error_text = (
            f"🧠 <b>К сожалению, возникла техническая ошибка</b>\n\n"
            f"Как ваш виртуальный психолог, я не смог обработать все данные.\n\n"
            f"Попробуйте пройти тест заново, чтобы я мог помочь вам лучше:\n"
            f"/start\n\n"
            f"<i>Приношу извинения за неудобства.</i>"
        )
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    actual_profile_key = None
    try:
        if hasattr(profile, 'key'):
            actual_profile_key = profile.key.lower()
            logger.info(f"🔍 Найден ключ профиля: {actual_profile_key}")
            context.user_data["actual_profile_key"] = actual_profile_key
        elif hasattr(profile, 'profile_name'):
            actual_profile_key = profile.profile_name.lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        else:
            actual_profile_key = f"{profile_card.get('type_code', 'sa')}_{profile_card.get('level', 1)}_{profile_card.get('dilts_code', 'def')}".lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        
        parts = actual_profile_key.split('_')
        if len(parts) >= 3:
            profile_data['type_code'] = parts[0].upper()
            profile_data['level'] = int(parts[1])
            profile_data['dilts_code'] = parts[2].lower()
            profile_data['display_name'] = actual_profile_key.upper()
            context.user_data["profile_data"] = profile_data
            logger.info(f"✅ Обновлен profile_data реальным профилем: {profile_data['display_name']}")
            
    except Exception as e:
        logger.error(f"⚠️ Ошибка определения реального профиля: {e}")
    
    # ПРИМЕЧАНИЕ О КОНФЛИКТЕ
    discrepancy_note = ""
    if actual_profile_key:
        discrepancy_note = get_discrepancy_note(profile_data, actual_profile_key)
        logger.info(f"📝 Примечание о конфликте: {'✅ Есть' if discrepancy_note else '❌ Нет'}")
    
    message_1 = (
        f"🧠 <b>ВАШИ ПЕРВЫЕ ИНСАЙТЫ</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я проанализировал ваши ответы.</i>\n\n"
        f"Вот что я увидел:\n\n"
    )
    
    psychologist_comment = (
        f"<i>На основе ваших ответов я вижу характерные паттерны мышления и поведения. "
        f"Это хорошая отправная точка для самопознания.</i>\n\n"
    )
    
    message_1 += psychologist_comment
    
    profile_header = profile_data.get('display_name', f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}")
    raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
    formatted_title = format_profile_title(raw_title, profile_header)
    message_1 += f"<b>{formatted_title}</b>\n\n"
    
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
    
    trigger = profile_card.get('trigger', '')
    if trigger:
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_1 += f"<b>🔍 ЭТО ВЫ, ЕСЛИ...</b>\n\n"
        message_1 += f"{trigger}\n\n"
    
    pain = profile_card.get('pain', '')
    if pain:
        pain_lines = pain.strip().split('\n')
        if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
            pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
        
        if pain.strip():
            message_1 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
            message_1 += f"{pain.strip()}"

    if message_1.strip():
    # Проверяем длину сообщения (лимит Telegram 4096 символов)
    if len(message_1.strip()) > 4000:
        # Разбиваем на части
        parts = [message_1[i:i+4000] for i in range(0, len(message_1), 4000)]
        
        # Редактируем первое сообщение
        await query.edit_message_text(parts[0], parse_mode="HTML")
        
        # Отправляем остальные как новые сообщения
        for part in parts[1:]:
            await query.message.reply_text(part, parse_mode="HTML")
            await asyncio.sleep(0.5)
    else:
        await query.edit_message_text(message_1.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    message_2 = ""
    
    tool = profile_card.get('immediate_tool', '')
    if tool:
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            message_2 += f"<b>🛠 ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>\n\n"
            message_2 += f"<i>Что можно сделать прямо сейчас:</i>\n\n"
            message_2 += f"{tool.strip()}\n\n"
    
    cta = profile_card.get('cta', '')
    if cta:
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_2 += f"<b>🚀 СЛЕДУЮЩИЕ ШАГИ</b>\n\n"
            message_2 += f"{cta.strip()}\n\n"
    
    message_2 += "\n"
    
    message_2 += (
        f"🧠 <b>ЧТО ДАЛЬШЕ В НАШЕМ ПУТЕШЕСТВИИ?</b>\n\n"
        f"<i>Это только начало вашего пути к самопознанию.</i>\n\n"
    )
    
    # ПРИМЕЧАНИЕ О КОНФЛИКТЕ
    if discrepancy_note:
        message_2 += f"{discrepancy_note}"
    
    # КНОПКА 18+ ПРОФИЛЯ
    sexual_button = [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="show_my_sexual_profile")]
    
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="get_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Получить сказку «Мастер Меча»", callback_data="open_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    # ВАЖНО: Добавляем логирование возвращаемого значения
    logger.info(f"✅ User {user_id}: show_results_screen → возвращаю RESULTS = {RESULTS}")
    return RESULTS

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"⬅️ back_to_results ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("🔄 Возвращаюсь к результатам...")
    
    await show_results_screen(update, context, force_shared_view=True)
    
    logger.info(f"🔄 User {user_id}: back_to_results → RESULTS = {RESULTS}")
    return RESULTS

async def back_to_results_after_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам после подарка"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"⬅️ back_to_results_after_gift ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("🔄 Возвращаюсь к результатам...")
    
    await show_results_screen(update, context, force_shared_view=True)
    
    logger.info(f"🎁 User {user_id}: back_to_results_after_gift → RESULTS = {RESULTS}")
    return RESULTS

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск шаринга"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"⏩ skip_share ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("⏩ Продолжаем без репоста")
    
    await show_results_screen(update, context, force_shared_view=True)
    
    logger.info(f"🔄 User {user_id}: skip_share → RESULTS = {RESULTS}")
    return RESULTS

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"✅ confirm_share ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("✅ Спасибо за репост! Ваш бонус готов!")
    
    context.user_data["has_shared"] = True
    
    logger.info(f"✅ User {user_id}: confirm_share → open_gift_screen")
    from handlers.gifts import open_gift_screen
    return await open_gift_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"🔄 restart_test ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("🔄 Перезапускаю тест...")
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    # Инициализируем новые данные
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    # Инициализируем хранилище приглашений
    from sexual_18_plus import get_user_invites
    context.user_data["sexual_invites"] = get_user_invites(user_id)
    
    logger.info(f"User {user_id} перезапустил тест")
    
    # Переходим к первому этапу
    from handlers.stage1 import show_stage_1_intro
    return await show_stage_1_intro(update, context)

__all__ = [
    'show_results_screen',
    'back_to_results',
    'back_to_results_after_gift',
    'skip_share',
    'confirm_share',
    'restart_test'
]
