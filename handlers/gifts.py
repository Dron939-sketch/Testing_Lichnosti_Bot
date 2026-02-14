# handlers/gifts.py
"""
Обработчики для подарков и шаринга
"""

import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ИСПРАВЛЕНО: Импортируем константы из constants.py вместо config.py
from constants import GIFT_SCREEN, OPEN_GIFT_SCREEN, PACKAGE_SCREEN, RESULTS
from config import GIFT_PDF_LINK, SHARE_TEXT, BOT_LINK, GIFT_SCREEN_TEXT, logger
from sexual_18_plus import PROFILE_DISK_LINKS

logger = logging.getLogger(__name__)

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"🎁 get_gift_screen ВЫЗВАН для пользователя {user_id}")
    
    await query.answer()
    
    instruction_text = (
        f"🧠 <b>ДАЙТЕ ДРУГИМ ЗЕРКАЛО — ПОЛУЧИТЕ МЕЧ</b>\n\n"
        f"Иногда самое полезное, что мы можем сделать для близких —\n"
        f"дать им зеркало.\n\n"
        f"<i>Поделитесь этим зеркалом с теми, кому оно может быть важно.</i>\n\n"
        f"⚔️ <b>А в благодарность — получите свой Меч:</b>\n"
        f"Терапевтическая сказка <b>«Мастер Меча»</b>\n\n"
        f"📖 <b>Эта сказка работает с тем, что мешает вам\n"
        f"«расправить плечи» на уровне убеждений.</b>\n\n"
        f"Она мягко трансформирует те ограничивающие установки,\n"
        f"которые создают невидимую тяжесть на ваших плечах.\n\n"
        f"🔗 <i>Просто нажмите кнопку ниже —\n"
        f"я подготовлю сообщение для друзей.</i>"
    )
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    keyboard = [
        [InlineKeyboardButton("🪞 Поделиться зеркалом", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился(ась) — получить подарок", callback_data="confirm_share")],
        [InlineKeyboardButton("Продолжить без этого →", callback_data="skip_share")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"🔄 User {user_id}: get_gift_screen → возвращаю GIFT_SCREEN = {GIFT_SCREEN}")
    return GIFT_SCREEN

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН С ПОДАРКОМ"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"🎁 open_gift_screen ВЫЗВАН для пользователя {user_id}")
    logger.info(f"📊 has_shared={context.user_data.get('has_shared', False)}")
    
    await query.answer()
    
    if not context.user_data.get("has_shared", False):
        logger.warning(f"❌ Пользователь {user_id} пытается открыть подарок без has_shared")
        await query.answer(
            "❌ Сначала поделитесь зеркалом с друзьями, чтобы получить подарок!", 
            show_alert=True
        )
        from handlers.results import show_results_screen
        return await show_results_screen(update, context, force_shared_view=True)
    
    # Проверяем наличие ссылки
    if not GIFT_PDF_LINK:
        logger.error(f"❌ GIFT_PDF_LINK не установлен для пользователя {user_id}")
        await query.answer(
            "❌ Ссылка на подарок временно недоступна. Пожалуйста, попробуйте позже.",
            show_alert=True
        )
        from handlers.results import show_results_screen
        return await show_results_screen(update, context, force_shared_view=True)
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Открыть сказку «Мастер Меча»", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results_after_gift")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.info(f"🎁 User {user_id} opened gift (has_shared={context.user_data.get('has_shared', False)})")
    
    await query.edit_message_text(
        GIFT_SCREEN_TEXT,
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )
    
    logger.info(f"🔄 User {user_id}: open_gift_screen → возвращаю OPEN_GIFT_SCREEN = {OPEN_GIFT_SCREEN}")
    return OPEN_GIFT_SCREEN

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНОЕ ОПИСАНИЕ ПРОФИЛЯ"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"📦 show_package_screen ВЫЗВАН для пользователя {user_id}")
    
    await query.answer()
    
    profile_data = context.user_data.get("profile_data")
    
    if profile_data:
        profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
        profile_info = f"\n📊 <b>Ваш профиль:</b> <code>{profile_code}</code>\n"
        personal_note = f"\n<i>Это описание будет создано персонально для вас на основе ваших ответов.</i>"
        logger.info(f"📊 Профиль пользователя: {profile_code}")
    else:
        profile_info = "\n📊 <b>Профиль:</b> будет определен после теста\n"
        personal_note = f"\n<i>После теста я подготовлю персональное описание именно для вас.</i>"
        logger.info(f"⚠️ profile_data отсутствует для пользователя {user_id}")
    
    package_text = (
        f"🧠 <b>ПОЛНОЕ ОПИСАНИЕ ВАШЕГО ПРОФИЛЯ</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я подготовлю для вас:</i>\n\n"
        f"• 📖 <b>Детальный анализ личности</b> (15+ страниц)\n"
        f"• 🎯 <b>Ключевые паттерны поведения</b> с примерами\n"
        f"• 🚀 <b>Точки роста</b> и рекомендации по развитию\n"
        f"• ⚠️ <b>Потенциальные ограничения</b> и как их обходить\n"
        f"• 💡 <b>Практические инструменты</b> для ежедневного применения\n"
        f"• 🔍 <b>Сильные стороны</b> и как их использовать\n\n"
        f"{profile_info}"
        f"<b>Стоимость:</b> 690 ₽\n\n"
        f"💳 <b>Все способы оплаты:</b> СБП, ЮMoney, банковские карты\n\n"
        f"{personal_note}\n\n"
        f"<b>Это ваше персональное руководство по самопознанию!</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🧠 Получить описание профиля за 690 ₽", callback_data="buy_package")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"🔄 User {user_id}: show_package_screen → возвращаю PACKAGE_SCREEN = {PACKAGE_SCREEN}")
    return PACKAGE_SCREEN

__all__ = [
    'get_gift_screen',
    'open_gift_screen',
    'show_package_screen'
]
