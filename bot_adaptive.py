"""
🚀 ПРОСТОЙ БОТ С АВТОМАТИЧЕСКОЙ ВЫДАЧЕЙ МАТЕРИАЛОВ
После оплаты → сразу показывает ссылку на материалы
"""

import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8311564413:AAE5iu5n0VNFA_8cd9HT0BeD4776IKGsvtE")
ADMIN_CHAT_ID = 532205848  # ID админа для уведомлений

# Карта материалов (36 профилей)
MATERIALS_MAP = {
    # SA (Социально-аффилиативный)
    "SA_1_DEF": {"name": "SA Уровень 1", "url": "https://disk.yandex.ru/d/HAcOfAg1tpIedA"},
    "SA_2_SIT": {"name": "SA Уровень 2", "url": "https://disk.yandex.ru/d/MwdMClX9koCTmA"},
    "SA_3_CON": {"name": "SA Уровень 3", "url": "https://disk.yandex.ru/d/NKN_XemK62t5nA"},
    "SA_4_EXP": {"name": "SA Уровень 4", "url": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA"},
    "SA_5_INT": {"name": "SA Уровень 5", "url": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg"},
    "SA_6_AUT": {"name": "SA Уровень 6", "url": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag"},
    "SA_7_VAL": {"name": "SA Уровень 7", "url": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g"},
    "SA_8_TRA": {"name": "SA Уровень 8", "url": "https://disk.yandex.ru/d/SqlDISkse1OEGQ"},
    "SA_9_IDE": {"name": "SA Уровень 9", "url": "https://disk.yandex.ru/d/vGzHmuckInNL5g"},
    
    # SP (Инструментально-достиженческий)
    "SP_1_DEF": {"name": "SP Уровень 1", "url": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA"},
    "SP_2_SIT": {"name": "SP Уровень 2", "url": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA"},
    "SP_3_CON": {"name": "SP Уровень 3", "url": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA"},
    "SP_4_EXP": {"name": "SP Уровень 4", "url": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ"},
    "SP_5_INT": {"name": "SP Уровень 5", "url": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg"},
    "SP_6_AUT": {"name": "SP Уровень 6", "url": "https://disk.yandex.ru/d/xWBv4TLFosOB5g"},
    "SP_7_VAL": {"name": "SP Уровень 7", "url": "https://disk.yandex.ru/d/K1whXj6C6KAazQ"},
    "SP_8_TRA": {"name": "SP Уровень 8", "url": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg"},
    "SP_9_IDE": {"name": "SP Уровень 9", "url": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ"},
    
    # IA (Экзистенциально-рефлексивный)
    "IA_1_DEF": {"name": "IA Уровень 1", "url": "https://disk.yandex.ru/d/M1Y7z175uGKIHg"},
    "IA_2_SIT": {"name": "IA Уровень 2", "url": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ"},
    "IA_3_CON": {"name": "IA Уровень 3", "url": "https://disk.yandex.ru/d/DCkqqALby9UpFg"},
    "IA_4_EXP": {"name": "IA Уровень 4", "url": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg"},
    "IA_5_INT": {"name": "IA Уровень 5", "url": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g"},
    "IA_6_AUT": {"name": "IA Уровень 6", "url": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg"},
    "IA_7_VAL": {"name": "IA Уровень 7", "url": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ"},
    "IA_8_TRA": {"name": "IA Уровень 8", "url": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw"},
    "IA_9_IDE": {"name": "IA Уровень 9", "url": "https://disk.yandex.ru/d/ub0YpQQgS4g6rQ"},
    
    # IP (Структурно-аналитический)
    "IP_1_DEF": {"name": "IP Уровень 1", "url": "https://disk.yandex.ru/d/m-WOQwDdgQxsnQ"},
    "IP_2_SIT": {"name": "IP Уровень 2", "url": "https://disk.yandex.ru/d/aL4VlAQdlaZ-6g"},
    "IP_3_CON": {"name": "IP Уровень 3", "url": "https://disk.yandex.ru/d/N8GG9XbnC3bFhg"},
    "IP_4_EXP": {"name": "IP Уровень 4", "url": "https://disk.yandex.ru/d/54RFOZmGhA4cfA"},
    "IP_5_INT": {"name": "IP Уровень 5", "url": "https://disk.yandex.ru/d/l5iFTIX8-gTycQ"},
    "IP_6_AUT": {"name": "IP Уровень 6", "url": "https://disk.yandex.ru/d/bTo_vcCoC1KU7Q"},
    "IP_7_VAL": {"name": "IP Уровень 7", "url": "https://disk.yandex.ru/d/TMx1VP843bnJQw"},
    "IP_8_TRA": {"name": "IP Уровень 8", "url": "https://disk.yandex.ru/d/e9KfJdLcl3gp7g"},
    "IP_9_IDE": {"name": "IP Уровень 9", "url": "https://disk.yandex.ru/d/ZiQPHJSDrrWZhw"},
}

# Профили для тестирования
TEST_PROFILES = [
    {"name": "🧪 Тест SA_4_EXP", "key": "SA_4_EXP", "price": 690},
    {"name": "🧪 Тест SP_2_SIT", "key": "SP_2_SIT", "price": 690},
    {"name": "🧪 Тест IA_7_VAL", "key": "IA_7_VAL", "price": 690},
    {"name": "🧪 Тест IP_3_CON", "key": "IP_3_CON", "price": 690},
]

# ============================================
# ПРОСТЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ПЛАТЕЖАМИ
# ============================================

class SimplePaymentSystem:
    """Простая система платежей для демонстрации"""
    
    def __init__(self):
        self.payments = {}  # Храним платежи в памяти
        
    def create_payment(self, user_id: int, profile_key: str, amount: int) -> dict:
        """Создает тестовый платеж"""
        payment_id = f"pay_{user_id}_{int(os.urandom(4).hex(), 16)}"
        
        payment_data = {
            "payment_id": payment_id,
            "user_id": user_id,
            "profile_key": profile_key,
            "amount": amount,
            "status": "pending",  # pending, paid, failed
            "created_at": os.times().elapsed
        }
        
        self.payments[payment_id] = payment_data
        logger.info(f"💰 Создан платеж {payment_id} для user {user_id}")
        
        return {
            "success": True,
            "payment_id": payment_id,
            "amount": amount,
            "description": f"Оплата за материалы {profile_key}"
        }
    
    def process_payment(self, payment_id: str) -> bool:
        """Обрабатывает платеж (в реальности здесь будет ЮKassa)"""
        if payment_id in self.payments:
            self.payments[payment_id]["status"] = "paid"
            logger.info(f"✅ Платеж {payment_id} оплачен")
            return True
        return False
    
    def get_payment(self, payment_id: str) -> dict:
        """Получает информацию о платеже"""
        return self.payments.get(payment_id)

# Инициализируем платежную систему
payment_system = SimplePaymentSystem()

# ============================================
# ОСНОВНЫЕ КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    logger.info(f"👋 Пользователь {user.id} ({user.first_name}) запустил бота")
    
    keyboard = [
        [InlineKeyboardButton("🎯 ВЫБРАТЬ ПРОФИЛЬ", callback_data="choose_profile")],
        [InlineKeyboardButton("📁 ПОЛУЧИТЬ МАТЕРИАЛЫ", callback_data="get_materials")],
        [InlineKeyboardButton("💎 О ПРОЕКТЕ", callback_data="about")]
    ]
    
    await update.message.reply_text(
        f"*👋 Привет, {user.first_name}!*\n\n"
        f"🎴 *Добро пожаловать в VARIATICA!*\n\n"
        f"*Что здесь есть:*\n"
        f"✅ 36 персонализированных наборов материалов\n"
        f"✅ Простая оплата через бота\n"
        f"✅ Мгновенный доступ после оплаты\n"
        f"✅ Автоматическая выдача материалов\n\n"
        f"*Как это работает:*\n"
        f"1. Выбираете профиль\n"
        f"2. Оплачиваете 690 руб\n"
        f"3. Получаете материалы сразу\n\n"
        f"*Выберите действие:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def choose_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор профиля"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for profile in TEST_PROFILES:
        keyboard.append([
            InlineKeyboardButton(
                f"{profile['name']} - {profile['price']} руб",
                callback_data=f"buy_{profile['key']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])
    
    await query.edit_message_text(
        "🎯 *ВЫБЕРИТЕ ПРОФИЛЬ*\n\n"
        "Выберите один из тестовых профилей для оплаты:\n\n"
        "💎 *Что входит:*\n"
        "• Полный набор материалов профиля\n"
        "• Мгновенный доступ после оплаты\n"
        "• Персонализированный контент\n"
        "• Ссылка на Яндекс.Диск\n\n"
        "💰 *Стоимость:* 690 рублей\n\n"
        "👇 Нажмите на профиль для оплаты:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки профиля"""
    query = update.callback_query
    await query.answer()
    
    # Получаем profile_key из callback_data
    if query.data.startswith("buy_"):
        profile_key = query.data[4:]  # Убираем "buy_"
        
        if profile_key not in MATERIALS_MAP:
            await query.edit_message_text(
                "❌ *Профиль не найден*\n\n"
                "Пожалуйста, выберите другой профиль.",
                parse_mode='Markdown'
            )
            return
        
        user_id = query.from_user.id
        user_name = query.from_user.first_name
        profile_data = MATERIALS_MAP[profile_key]
        
        logger.info(f"🛒 Пользователь {user_id} выбрал профиль {profile_key}")
        
        # Создаем платеж
        payment_result = payment_system.create_payment(
            user_id=user_id,
            profile_key=profile_key,
            amount=690
        )
        
        if not payment_result["success"]:
            await query.edit_message_text(
                "❌ *Ошибка создания платежа*\n\n"
                "Попробуйте снова.",
                parse_mode='Markdown'
            )
            return
        
        payment_id = payment_result["payment_id"]
        
        # Сохраняем payment_id в контексте пользователя
        context.user_data["last_payment"] = payment_id
        context.user_data["profile_key"] = profile_key
        
        # Показываем экран оплаты
        keyboard = [
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", callback_data=f"pay_{payment_id}")],
            [InlineKeyboardButton("🧪 ИМИТИРОВАТЬ ОПЛАТУ", callback_data=f"mock_{payment_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="choose_profile")]
        ]
        
        await query.edit_message_text(
            f"💎 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\n"
            f"👤 *Покупатель:* {user_name}\n"
            f"🎯 *Профиль:* {profile_data['name']}\n"
            f"📋 *Код профиля:* `{profile_key}`\n"
            f"💰 *Сумма к оплате:* 690 руб\n"
            f"🆔 *ID заказа:* `{payment_id}`\n\n"
            f"*Что вы получите:*\n"
            f"✅ Персонализированный набор материалов\n"
            f"✅ Ссылка на Яндекс.Диск\n"
            f"✅ Мгновенный доступ после оплаты\n\n"
            f"*Для оплаты нажмите кнопку:*\n"
            f"После оплаты материалы придут сразу в этот чат!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def process_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("pay_"):
        # В реальности здесь будет переход на ЮKassa
        payment_id = query.data[4:]
        
        await query.edit_message_text(
            f"🔗 *ПЕРЕХОД НА ОПЛАТУ*\n\n"
            f"ID платежа: `{payment_id}`\n\n"
            f"В реальной системе здесь будет:\n"
            f"1. Переход на страницу ЮKassa\n"
            f"2. Оплата картой/СБП/ЮMoney\n"
            f"3. Возврат в бот\n"
            f"4. Автоматическая выдача материалов\n\n"
            f"Для теста используйте кнопку имитации оплаты.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧪 ИМИТИРОВАТЬ ОПЛАТУ", callback_data=f"mock_{payment_id}")]
            ])
        )
        
    elif query.data.startswith("mock_"):
        # Имитация успешной оплаты
        payment_id = query.data[5:]
        
        await query.edit_message_text(
            "⏳ *Имитирую успешную оплату...*",
            parse_mode='Markdown'
        )
        
        # Обрабатываем платеж
        success = payment_system.process_payment(payment_id)
        
        if not success:
            await query.edit_message_text(
                "❌ *Платеж не найден*\n\n"
                "Попробуйте создать новый заказ.",
                parse_mode='Markdown'
            )
            return
        
        # Получаем данные платежа
        payment_data = payment_system.get_payment(payment_id)
        profile_key = payment_data.get("profile_key", "SA_4_EXP")
        
        # Сохраняем профиль пользователя
        context.user_data["paid_profile"] = profile_key
        context.user_data["last_payment_id"] = payment_id
        
        # Немного ждем для реалистичности
        import asyncio
        await asyncio.sleep(1)
        
        # АВТОМАТИЧЕСКАЯ ВЫДАЧА МАТЕРИАЛОВ
        await send_materials_automatically(
            update=update,
            context=context,
            user_id=query.from_user.id,
            user_name=query.from_user.first_name,
            payment_id=payment_id,
            profile_key=profile_key
        )

async def send_materials_automatically(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     user_id: int, user_name: str, payment_id: str, profile_key: str):
    """АВТОМАТИЧЕСКАЯ ВЫДАЧА МАТЕРИАЛОВ ПОСЛЕ ОПЛАТЫ"""
    
    query = update.callback_query
    
    # Получаем данные материалов
    if profile_key not in MATERIALS_MAP:
        profile_key = "SA_4_EXP"  # fallback
    
    materials = MATERIALS_MAP[profile_key]
    
    # Отправляем уведомление об успешной оплате
    await query.edit_message_text(
        "🎉 *ОПЛАТА ПРОШЛА УСПЕШНО!*\n\n"
        "⏳ *Загружаю ваши материалы...*",
        parse_mode='Markdown'
    )
    
    # Немного ждем для эффекта
    import asyncio
    await asyncio.sleep(0.5)
    
    # Отправляем сообщение с материалами
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
             f"👤 *Покупатель:* {user_name}\n"
             f"🎯 *Профиль:* {materials['name']}\n"
             f"📋 *Код профиля:* `{profile_key}`\n"
             f"🆔 *ID заказа:* `{payment_id}`\n\n"
             f"*Что вы получили:*\n"
             f"🎴 Полный набор материалов по вашему профилю\n"
             f"📚 Эксклюзивный контент\n"
             f"🔗 Доступ к Яндекс.Диск\n\n"
             f"👇 *Нажмите кнопку ниже для скачивания:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials['url'])]
        ])
    )
    
    # Отправляем дополнительную информацию
    await context.bot.send_message(
        chat_id=user_id,
        text=f"📋 *ИНФОРМАЦИЯ О ЗАКАЗЕ*\n\n"
             f"🆔 *ID платежа:* `{payment_id}`\n"
             f"💰 *Сумма:* 690 руб\n"
             f"🎯 *Профиль:* {materials['name']}\n"
             f"📅 *Дата:* {os.times().elapsed:.0f}\n\n"
             f"*Что делать дальше:*\n"
             f"1. Скачайте материалы по ссылке выше\n"
             f"2. Сохраните их на своем устройстве\n"
             f"3. Изучайте в удобном темпе\n\n"
             f"*Нужна помощь?*\n"
             f"Напишите @meysternlp",
        parse_mode='Markdown'
    )
    
    logger.info(f"✅ Материалы отправлены пользователю {user_id} для профиля {profile_key}")

async def get_materials_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение материалов (если уже оплатили)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Проверяем, есть ли оплаченный профиль
    paid_profile = context.user_data.get("paid_profile")
    last_payment_id = context.user_data.get("last_payment_id")
    
    if paid_profile:
        # Если уже оплатили - показываем материалы снова
        materials = MATERIALS_MAP.get(paid_profile, MATERIALS_MAP["SA_4_EXP"])
        
        keyboard = [
            [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=materials['url'])],
            [InlineKeyboardButton("🎯 ВЫБРАТЬ ДРУГОЙ ПРОФИЛЬ", callback_data="choose_profile")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            f"📁 *ВАШИ МАТЕРИАЛЫ*\n\n"
            f"👤 *{user_name}*, вот ваши материалы:\n\n"
            f"🎯 *Профиль:* {materials['name']}\n"
            f"📋 *Код:* `{paid_profile}`\n"
            f"🆔 *Последний заказ:* `{last_payment_id or 'N/A'}`\n\n"
            f"Нажмите кнопку для скачивания:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Если нет оплаты - предлагаем купить
        keyboard = [[InlineKeyboardButton("🎯 ВЫБРАТЬ ПРОФИЛЬ", callback_data="choose_profile")]]
        
        await query.edit_message_text(
            f"📭 *МАТЕРИАЛЫ НЕ НАЙДЕНЫ*\n\n"
            f"👤 *{user_name}*, у вас нет активных покупок.\n\n"
            f"Чтобы получить материалы:\n"
            f"1. Выберите профиль\n"
            f"2. Оплатите 690 руб\n"
            f"3. Получите материалы сразу\n\n"
            f"Выберите профиль:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """О проекте"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎯 ВЫБРАТЬ ПРОФИЛЬ", callback_data="choose_profile")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        "💎 *О ПРОЕКТЕ VARIATICA*\n\n"
        "*Что это?*\n"
        "Платформа с 36 персонализированными наборами материалов "
        "по типологии личности.\n\n"
        "*Как работает?*\n"
        "1. Проходите тест (определяет ваш профиль)\n"
        "2. Получаете персонализированные материалы\n"
        "3. Изучаете в удобном темпе\n\n"
        "*Что вы получаете?*\n"
        "✅ 36 различных наборов материалов\n"
        "✅ Контент под ваш тип личности\n"
        "✅ Мгновенный доступ после оплаты\n"
        "✅ Ссылки на Яндекс.Диск\n\n"
        "*Стоимость:* 690 руб за профиль\n\n"
        "*Техническая поддержка:* @meysternlp",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    # Создаем фейковое обновление для вызова start
    fake_update = Update(
        update_id=update.update_id + 1000,
        message=query.message
    )
    
    await start(fake_update, context)

# ============================================
# ЗАПУСК БОТА
# ============================================

def main():
    """Запуск бота"""
    logger.info("🚀 ЗАПУСК ПРОСТОГО БОТА С АВТОМАТИЧЕСКОЙ ВЫДАЧЕЙ")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Регистрируем обработчики кнопок
    application.add_handler(CallbackQueryHandler(choose_profile_handler, pattern="^choose_profile$"))
    application.add_handler(CallbackQueryHandler(buy_profile_handler, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(process_payment_handler, pattern="^(pay_|mock_)"))
    application.add_handler(CallbackQueryHandler(get_materials_handler, pattern="^get_materials$"))
    application.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    
    logger.info("✅ Бот запущен!")
    logger.info("👉 Используйте /start в Telegram")
    logger.info("💰 После оплаты → автоматическая выдача материалов")
    
    # Запускаем бота
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
