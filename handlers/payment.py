# handlers/payment.py
"""
Обработчики для платежей
"""

import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import PAYMENT_SCREEN, API_URL, TELEGRAM_BOT_URL, logger
from sexual_18_plus import get_disk_link

# Импортируем функции напрямую из payment_functions
# Предварительно нужно создать файл payment_functions.py в корне проекта
try:
    from payment_functions import (
        create_payment_advanced,
        check_payment_status_api,
        get_materials_link_api
    )
    logger.info("✅ Функции платежей успешно импортированы из payment_functions")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта функций из payment_functions: {e}")
    # Создаем заглушки для случаев, когда импорт не удался
    async def create_payment_advanced(user_id, profile_code, amount):
        logger.error("❌ Функция create_payment_advanced не импортирована")
        return {"success": False, "error": "Функция не доступна"}
    
    async def check_payment_status_api(payment_id):
        logger.error("❌ Функция check_payment_status_api не импортирована")
        return {"success": False, "error": "Функция не доступна"}
    
    async def get_materials_link_api(payment_id, user_id):
        logger.error("❌ Функция get_materials_link_api не импортирована")
        return {"success": False, "error": "Функция не доступна"}

logger = logging.getLogger(__name__)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /buy для получения описания профиля"""
    user_id = update.effective_user.id
    
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        keyboard = [
            [InlineKeyboardButton("🧠 Пройти тест для знакомства", callback_data="start_test")],
            [InlineKeyboardButton("💎 Получить описание без теста", callback_data="buy_without_test")]
        ]
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                f"🧠 *Чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
                f"давайте сначала познакомимся поближе через тест.*\n\n"
                f"💎 *Что вы получите в полном описании профиля:*\n"
                f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
                f"• 🎯 Конкретные паттерны поведения и мышления\n"
                f"• 🚀 Рекомендации по развитию от психолога\n"
                f"• 💡 Практические инструменты для жизни\n\n"
                f"💰 *Стоимость:* 690 рублей\n"
                f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
                f"*Выберите действие:*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"🧠 *Чтобы я как ваш виртуальный психолог мог подготовить персональное описание, "
                f"давайте сначала познакомимся поближе через тест.*\n\n"
                f"💎 *Что вы получите в полном описании профиля:*\n"
                f"• 📖 Детальный анализ вашей личности (15+ страниц)\n"
                f"• 🎯 Конкретные паттерны поведения и мышления\n"
                f"• 🚀 Рекомендации по развитию от психолога\n"
                f"• 💡 Практические инструменты для жизни\n\n"
                f"💰 *Стоимость:* 690 рублей\n"
                f"💳 *Все способы оплаты:* СБП, ЮMoney, банковские карты\n\n"
                f"*Выберите действие:*",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return PAYMENT_SCREEN
    
    profile_code = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    context.user_data["pending_payment_profile"] = profile_code
    
    return await show_payment_screen(update, context)

async def buy_without_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка без прохождения теста"""
    query = update.callback_query
    await query.answer("💳 Переход к оплате...")
    
    context.user_data["pending_payment_profile"] = "SA_1_DEF"
    
    return await show_payment_screen(update, context)

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран создания платежа"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    profile_data = context.user_data.get("profile_data")
    
    if profile_data and 'display_name' in profile_data:
        profile_code = profile_data['display_name']
        logger.info(f"✅ Использую РЕАЛЬНЫЙ профиль из теста: {profile_code}")
    else:
        profile_code = context.user_data.get("pending_payment_profile", "SA_1_DEF")
        logger.info(f"⚠️ Использую запасной профиль: {profile_code}")
    
    context.user_data["pending_payment_profile"] = profile_code
    
    if query:
        await query.edit_message_text(
            f"💳 *СОЗДАЮ ПЛАТЕЖ...*\n\n"
            f"🧠 *Виртуальный психолог Вариатика*\n"
            f"👤 *Клиент:* {user_name}\n"
            f"📊 *Профиль:* `{profile_code}`\n"
            f"💰 *Сумма:* 690 рублей\n\n"
            f"⏳ *Создаю ссылку для оплаты...*",
            parse_mode='Markdown'
        )
    
    # Проверяем, доступна ли функция
    if create_payment_advanced is None:
        error_text = (
            f"❌ *Ошибка конфигурации*\n\n"
            f"Функция создания платежа не доступна.\n"
            f"Пожалуйста, обратитесь к администратору."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Вернуться", callback_data="back_to_results")]]
        
        if query:
            await query.edit_message_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return PAYMENT_SCREEN
    
    payment_result = await create_payment_advanced(user_id, profile_code, 690.00)
    
    if not payment_result.get("success"):
        error_msg = payment_result.get("error", "Неизвестная ошибка")
        details = payment_result.get("details", "")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="buy_without_test")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        error_text = f"❌ *Ошибка при создании платежа:*\n`{error_msg}`"
        if details:
            error_text += f"\n\n`{details[:100]}`"
        
        if query:
            await query.edit_message_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                error_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return PAYMENT_SCREEN
    
    payment_id = payment_result["payment_id"]
    confirmation_url = payment_result["confirmation_url"]
    
    context.user_data["last_payment_id"] = payment_id
    context.user_data["last_payment_profile"] = profile_code
    
    if "payment_data" not in context.user_data:
        context.user_data["payment_data"] = {}
    
    context.user_data["payment_data"][payment_id] = {
        "confirmation_url": confirmation_url,
        "profile_code": profile_code,
        "timestamp": time.time(),
        "user_id": user_id
    }
    
    logger.info(f"💾 Сохранён payment_id {payment_id} с confirmation_url")
    
    invoice_info = ""
    invoice_type = payment_result.get('invoice_type', 'yookassa_invoice')
    available_methods = payment_result.get('available_methods', 'all')
    
    if invoice_type == 'yookassa_invoice' and available_methods == 'all':
        invoice_info = (
            "\n💡 *ВСЕ способы оплаты доступны:*\n"
            "• СБП (Сбербанк Онлайн)\n"
            "• ЮMoney\n"
            "• Банковские карты (Visa/Mastercard/Мир)\n"
            "• Тинькофф, Альфа-Банк\n"
            "• И другие\n"
        )
    
    # Получаем ссылку на Яндекс.Диск для экрана оплаты
    profile_link = get_disk_link(profile_code)
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить 690 рублей", url=confirmation_url)],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")],
        [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
    ]
    
    message_text = (
        f"✅ *ПЛАТЕЖ СОЗДАН!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *Клиент:* {user_name}\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"📋 *ID платежа:* `{payment_id}`\n"
        f"💰 *Сумма:* 690 рублей\n"
        f"{invoice_info}"
        f"\n🔒 *Защита от дублей:* ✅ активна\n"
        f"📊 *Профиль сохранен:* ✅ `{profile_code}`\n"
        f"📁 *Ссылка на материалы:* {profile_link}\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После успешной оплаты:\n"
        f"1. Вы получите уведомление\n"
        f"2. Ссылка на персональное описание профиля придет автоматически\n"
        f"3. Профиль `{profile_code}` будет сохранен\n\n"
        f"<i>Вы также можете вернуться к результатам теста и продолжить позже.</i>"
    )
    
    if query:
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    return PAYMENT_SCREEN

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    
    await query.edit_message_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС ПЛАТЕЖА...*\n\n"
        f"📋 *ID:* `{payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    if check_payment_status_api is None:
        error_text = f"❌ *Функция проверки статуса не доступна*"
        keyboard = [[InlineKeyboardButton("⬅️ Вернуться", callback_data="back_to_results")]]
        
        await query.edit_message_text(
            error_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    status_result = await check_payment_status_api(payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    status = status_result.get("status", "unknown")
    
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания профиля нажмите кнопку ниже:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📥 ПОЛУЧИТЬ ОПИСАНИЕ ПРОФИЛЯ", callback_data=f"get_materials_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты нажмите кнопку ниже:*"
        )
        
        payment_data = context.user_data.get("payment_data", {})
        payment_info = payment_data.get(payment_id, {})
        confirmation_url = payment_info.get("confirmation_url")
        
        if confirmation_url:
            keyboard = [
                [InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=confirmation_url)],
                [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
            ]
        
    else:
        message = (
            f"📊 *СТАТУС ПЛАТЕЖА:* `{status}`\n\n"
            f"📋 *ID:* `{payment_id}`"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return PAYMENT_SCREEN

async def get_materials_callback_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов после оплаты"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.split("_")[2]
    user_id = update.effective_user.id
    
    await query.edit_message_text(
        f"📦 *ПОЛУЧАЮ МАТЕРИАЛЫ...*\n\n"
        f"📋 *ID платежа:* `{payment_id}`\n\n"
        f"⏳ Загружаю ссылки...",
        parse_mode='Markdown'
    )
    
    if get_materials_link_api is None:
        error_text = f"❌ *Функция получения материалов не доступна*"
        keyboard = [[InlineKeyboardButton("⬅️ Вернуться", callback_data="back_to_results")]]
        
        await query.edit_message_text(
            error_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    materials_result = await get_materials_link_api(payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"get_materials_{payment_id}")],
            [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
        ]
        
        await query.edit_message_text(
            f"❌ *ОШИБКА ПРИ ПОЛУЧЕНИИ МАТЕРИАЛОВ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже или обратитесь в поддержку.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PAYMENT_SCREEN
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        await query.edit_message_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return PAYMENT_SCREEN
    
    keyboard = [
        [InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)],
        [InlineKeyboardButton("⬅️ Вернуться к результатам", callback_data="back_to_results")]
    ]
    
    await query.edit_message_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"🎉 Ваше персональное описание профиля успешно подготовлено!\n\n"
        f"📋 *ID заказа:* `{payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 690 рублей\n\n"
        f"📚 *Что вы получили:*\n"
        f"• 📖 <b>Полное описание вашего профиля</b> (15+ страниц)\n"
        f"• 🎯 Ключевые паттерны поведения и мышления\n"
        f"• 🚀 Рекомендации по развитию от психолога\n"
        f"• ⚠️ Ограничения и как их обходить\n"
        f"• 💡 Практические инструменты для ежедневного применения\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания вашего персонального руководства:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
    return PAYMENT_SCREEN

async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /materials для получения материалов после оплаты"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        await update.message.reply_text(
            f"🧠 *У вас нет активных платежей*\n\n"
            f"👤 *{user_name}*, для получения персонального описания профиля необходимо приобрести полный пакет.\n\n"
            f"💎 *Полное описание профиля от виртуального психолога:*\n"
            f"• Стоимость: 690 рублей\n"
            f"• Все способы оплаты (СБП, ЮMoney, карты)\n"
            f"• Мгновенный доступ после оплаты\n"
            f"• Ваше персональное руководство по самопознанию\n\n"
            f"Используйте команду `/buy` для покупки",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔍 *ПОИСК ПЕРСОНАЛЬНОГО ОПИСАНИЯ...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Проверяю доступ...",
        parse_mode='Markdown'
    )
    
    if get_materials_link_api is None:
        await update.message.reply_text(
            f"❌ *Функция получения материалов не доступна*",
            parse_mode='Markdown'
        )
        return
    
    materials_result = await get_materials_link_api(last_payment_id, user_id)
    
    if not materials_result.get("success"):
        error_msg = materials_result.get("error", "Неизвестная ошибка")
        
        keyboard = [[InlineKeyboardButton("💳 Получить описание профиля", callback_data="buy_without_test")]]
        
        await update.message.reply_text(
            f"❌ *НЕ УДАЛОСЬ ПОЛУЧИТЬ МАТЕРИАЛЫ*\n\n"
            f"`{error_msg}`\n\n"
            f"Возможно, платеж еще не обработан или возникла ошибка.\n"
            f"Попробуйте позже или приобретите описание заново.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    materials_link = materials_result.get("materials_link")
    profile_code = materials_result.get("profile_code", "SA_1_DEF")
    
    if not materials_link:
        await update.message.reply_text(
            f"❌ *ССЫЛКА НЕ НАЙДЕНА*\n\n"
            f"Материалы для платежа `{last_payment_id}` не найдены.\n"
            f"Обратитесь в поддержку.",
            parse_mode='Markdown'
        )
        return
    
    keyboard = [[InlineKeyboardButton("📥 СКАЧАТЬ ПЕРСОНАЛЬНОЕ ОПИСАНИЕ", url=materials_link)]]
    
    await update.message.reply_text(
        f"✅ *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n\n"
        f"🧠 *Виртуальный психолог Вариатика*\n\n"
        f"👤 *{user_name}*, вот ваше персональное описание профиля:\n\n"
        f"📋 *ID заказа:* `{last_payment_id}`\n"
        f"📊 *Ваш профиль:* `{profile_code}`\n"
        f"💰 *Сумма:* 690 рублей\n\n"
        f"🔗 *Ссылка на Яндекс.Диск:*\n"
        f"Нажмите кнопку ниже для скачивания:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status для проверки статуса последнего платежа"""
    user_id = update.effective_user.id
    last_payment_id = context.user_data.get("last_payment_id")
    
    if not last_payment_id:
        await update.message.reply_text(
            "📭 *Нет активных платежей*\n\n"
            "У вас нет последних платежей для проверки.\n"
            "Используйте `/buy` для создания нового платежа.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔍 *ПРОВЕРЯЮ СТАТУС...*\n\n"
        f"📋 *ID платежа:* `{last_payment_id}`\n\n"
        f"⏳ Запрашиваю информацию...",
        parse_mode='Markdown'
    )
    
    if check_payment_status_api is None:
        await update.message.reply_text(
            f"❌ *Функция проверки статуса не доступна*",
            parse_mode='Markdown'
        )
        return
    
    status_result = await check_payment_status_api(last_payment_id)
    
    if not status_result.get("success"):
        error_msg = status_result.get("error", "Неизвестная ошибка")
        
        await update.message.reply_text(
            f"❌ *ОШИБКА ПРИ ПРОВЕРКЕ*\n\n"
            f"`{error_msg}`\n\n"
            f"Попробуйте позже.",
            parse_mode='Markdown'
        )
        return
    
    status = status_result.get("status", "unknown")
    
    if status == "succeeded":
        message = (
            f"✅ *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
            f"🎉 Платеж `{last_payment_id}` успешно завершен!\n\n"
            f"📦 *ПЕРСОНАЛЬНОЕ ОПИСАНИЕ ГОТОВО!*\n"
            f"Для получения персонального описания используйте команду:\n"
            f"`/materials`\n\n"
            f"✅ Вы получите мгновенный доступ к вашему руководству."
        )
        
    elif status in ["pending", "waiting"]:
        message = (
            f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
            f"Платеж `{last_payment_id}` еще не оплачен.\n\n"
            f"💳 *Для оплаты используйте команду:*\n"
            f"`/buy`\n\n"
            f"Или дождитесь обработки платежа."
        )
        
    else:
        message = (
            f"📊 *СТАТУС ПЛАТЕЖА:* `{status.upper()}`\n\n"
            f"📋 *ID:* `{last_payment_id}`\n\n"
            f"Если статус не меняется, попробуйте создать новый платеж: `/buy`"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

__all__ = [
    'buy_command',
    'buy_without_test_callback',
    'show_payment_screen',
    'check_payment_callback',
    'get_materials_callback_payment',
    'materials_command',
    'status_command'
]
