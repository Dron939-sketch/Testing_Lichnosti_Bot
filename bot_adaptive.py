"""
🎴 VARIATICA BOT - ФИНАЛЬНАЯ ВЕРСИЯ
Автоматическая выдача персонализированных материалов после оплаты
"""

import os
import logging
import time
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

# ============================================
# КАРТА 36 ПРОФИЛЕЙ С ССЫЛКАМИ НА ЯНДЕКС.ДИСК
# ============================================

PROFILES = {
    # SA (Социально-Аффилиативный)
    "SA_1_DEF": {"name": "SA Уровень 1", "url": "https://disk.yandex.ru/d/HAcOfAg1tpIedA"},
    "SA_2_SIT": {"name": "SA Уровень 2", "url": "https://disk.yandex.ru/d/MwdMClX9koCTmA"},
    "SA_3_CON": {"name": "SA Уровень 3", "url": "https://disk.yandex.ru/d/NKN_XemK62t5nA"},
    "SA_4_EXP": {"name": "SA Уровень 4", "url": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA"},
    "SA_5_INT": {"name": "SA Уровень 5", "url": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg"},
    "SA_6_AUT": {"name": "SA Уровень 6", "url": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag"},
    "SA_7_VAL": {"name": "SA Уровень 7", "url": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g"},
    "SA_8_TRA": {"name": "SA Уровень 8", "url": "https://disk.yandex.ru/d/SqlDISkse1OEGQ"},
    "SA_9_IDE": {"name": "SA Уровень 9", "url": "https://disk.yandex.ru/d/vGzHmuckInNL5g"},
    
    # SP (Инструментально-Достиженческий)
    "SP_1_DEF": {"name": "SP Уровень 1", "url": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA"},
    "SP_2_SIT": {"name": "SP Уровень 2", "url": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA"},
    "SP_3_CON": {"name": "SP Уровень 3", "url": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA"},
    "SP_4_EXP": {"name": "SP Уровень 4", "url": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ"},
    "SP_5_INT": {"name": "SP Уровень 5", "url": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg"},
    "SP_6_AUT": {"name": "SP Уровень 6", "url": "https://disk.yandex.ru/d/xWBv4TLFosOB5g"},
    "SP_7_VAL": {"name": "SP Уровень 7", "url": "https://disk.yandex.ru/d/K1whXj6C6KAazQ"},
    "SP_8_TRA": {"name": "SP Уровень 8", "url": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg"},
    "SP_9_IDE": {"name": "SP Уровень 9", "url": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ"},
    
    # IA (Экзистенциально-Рефлексивный)
    "IA_1_DEF": {"name": "IA Уровень 1", "url": "https://disk.yandex.ru/d/M1Y7z175uGKIHg"},
    "IA_2_SIT": {"name": "IA Уровень 2", "url": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ"},
    "IA_3_CON": {"name": "IA Уровень 3", "url": "https://disk.yandex.ru/d/DCkqqALby9UpFg"},
    "IA_4_EXP": {"name": "IA Уровень 4", "url": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg"},
    "IA_5_INT": {"name": "IA Уровень 5", "url": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g"},
    "IA_6_AUT": {"name": "IA Уровень 6", "url": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg"},
    "IA_7_VAL": {"name": "IA Уровень 7", "url": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ"},
    "IA_8_TRA": {"name": "IA Уровень 8", "url": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw"},
    "IA_9_IDE": {"name": "IA Уровень 9", "url": "https://disk.yandex.ru/d/ub0YpQQgS4g6rQ"},
    
    # IP (Структурно-Аналитический)
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

# ============================================
# СИМУЛЯЦИЯ БАЗЫ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

class UserDatabase:
    """Простая база данных пользователей в памяти"""
    
    def __init__(self):
        self.users = {}  # user_id -> данные пользователя
        self.payments = {}  # payment_id -> данные платежа
        
    def get_user_profile(self, user_id: int) -> str:
        """Получает профиль пользователя (в реальности из теста)"""
        # В РЕАЛЬНОЙ СИСТЕМЕ: получаем из API или БД
        # Здесь для демонстрации назначаем случайный профиль
        
        # Профили из теста (ваш реальный API будет возвращать что-то вроде):
        # {"profile_key": "SA_4_EXP", "type_code": "SA", "level": 4, "dilts": "EXP"}
        
        # Для теста возвращаем SA_4_EXP
        return "SA_4_EXP"
    
    def create_payment(self, user_id: int, amount: int = 690) -> dict:
        """Создает запись о платеже"""
        payment_id = f"pay_{user_id}_{int(time.time())}"
        
        # Получаем профиль пользователя
        profile_key = self.get_user_profile(user_id)
        
        payment_data = {
            "id": payment_id,
            "user_id": user_id,
            "profile_key": profile_key,
            "amount": amount,
            "status": "pending",
            "created_at": time.time()
        }
        
        self.payments[payment_id] = payment_data
        
        # Сохраняем пользователя
        if user_id not in self.users:
            self.users[user_id] = {"profile": profile_key, "payments": []}
        
        self.users[user_id]["payments"].append(payment_id)
        
        logger.info(f"💰 Создан платеж {payment_id} для профиля {profile_key}")
        return payment_data
    
    def mark_paid(self, payment_id: str) -> bool:
        """Отмечает платеж как оплаченный"""
        if payment_id in self.payments:
            self.payments[payment_id]["status"] = "paid"
            self.payments[payment_id]["paid_at"] = time.time()
            logger.info(f"✅ Платеж {payment_id} оплачен")
            return True
        return False
    
    def get_payment(self, payment_id: str) -> dict:
        """Получает данные платежа"""
        return self.payments.get(payment_id)

# Инициализация базы данных
db = UserDatabase()

# ============================================
# ОСНОВНЫЕ КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    logger.info(f"👤 Пользователь {user.id} ({user.first_name})")
    
    keyboard = [
        [InlineKeyboardButton("💎 КУПИТЬ ДОСТУП (690 руб)", callback_data="buy_access")],
        [InlineKeyboardButton("🧪 ТЕСТОВЫЙ ПЛАТЕЖ (1 руб)", callback_data="test_payment")],
        [InlineKeyboardButton("📚 МОИ МАТЕРИАЛЫ", callback_data="my_materials")]
    ]
    
    await update.message.reply_text(
        f"🎴 *Добро пожаловать в VARIATICA!*\n\n"
        f"👋 *{user.first_name}*, здесь вы можете получить персонализированные материалы по вашему психологическому профилю.\n\n"
        f"*Как это работает:*\n"
        f"1️⃣ Вы проходите тест (уже есть результат)\n"
        f"2️⃣ Оплачиваете доступ к материалам\n"
        f"3️⃣ Получаете материалы *автоматически* в этот чат\n\n"
        f"*Что вы получите:*\n"
        f"✅ Полный разбор вашего профиля (PDF)\n"
        f"✅ Терапевтическая сказка (PDF)\n"
        f"✅ Книга «ВАРИАТИКА» (PDF)\n"
        f"✅ Персональные рекомендации\n\n"
        f"👇 *Выберите действие:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_access_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка доступа за 690 руб"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Получаем профиль пользователя
    profile_key = db.get_user_profile(user.id)
    profile = PROFILES.get(profile_key, PROFILES["SA_4_EXP"])
    
    # Создаем платеж
    payment = db.create_payment(user.id, amount=690)
    
    # Сохраняем в контексте
    context.user_data["current_payment"] = payment["id"]
    context.user_data["profile_key"] = profile_key
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 690 РУБ", callback_data=f"process_{payment['id']}")],
        [InlineKeyboardButton("🧪 ТЕСТ ПЛАТЕЖА (1 руб)", callback_data="test_payment")],
        [InlineKeyboardButton("🏠 В ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        f"💎 *ОФОРМЛЕНИЕ ЗАКАЗА*\n\n"
        f"👤 *Покупатель:* {user.first_name}\n"
        f"🎯 *Ваш профиль:* {profile['name']}\n"
        f"🔑 *Код профиля:* `{profile_key}`\n"
        f"💰 *Сумма:* 690 рублей\n"
        f"🆔 *ID заказа:* `{payment['id']}`\n\n"
        f"*Что вы получите:*\n"
        f"• Полный разбор вашего профиля (PDF)\n"
        f"• Терапевтическая сказка (PDF)\n"
        f"• Книга «ВАРИАТИКА» (PDF)\n"
        f"• Персональные рекомендации\n\n"
        f"👇 *Для оплаты нажмите кнопку:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def test_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж 1 рубль"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Создаем тестовый платеж
    payment = db.create_payment(user.id, amount=1)
    
    keyboard = [
        [InlineKeyboardButton("🧪 ИМИТИРОВАТЬ ОПЛАТУ (1 руб)", callback_data=f"process_{payment['id']}")],
        [InlineKeyboardButton("💎 ПОЛНЫЙ ДОСТУП (690 руб)", callback_data="buy_access")],
        [InlineKeyboardButton("🏠 В ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        f"🧪 *ТЕСТОВЫЙ ПЛАТЕЖ*\n\n"
        f"👤 *Пользователь:* {user.first_name}\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"🆔 *ID заказа:* `{payment['id']}`\n\n"
        f"*Для проверки работы системы:*\n"
        f"1. Нажмите кнопку имитации оплаты\n"
        f"2. Получите тестовые материалы\n"
        f"3. Убедитесь, что система работает\n\n"
        f"👇 *Нажмите для теста:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("process_"):
        payment_id = query.data[8:]  # Извлекаем ID платежа
        
        # Имитация обработки
        await query.edit_message_text(
            "⏳ *Обрабатываю платеж...*",
            parse_mode='Markdown'
        )
        
        # Ждем для реалистичности
        import asyncio
        await asyncio.sleep(1)
        
        # Отмечаем как оплаченный
        db.mark_paid(payment_id)
        
        # Получаем данные
        payment = db.get_payment(payment_id)
        if not payment:
            await query.edit_message_text(
                "❌ *Платеж не найден*",
                parse_mode='Markdown'
            )
            return
        
        profile_key = payment["profile_key"]
        profile = PROFILES.get(profile_key, PROFILES["SA_4_EXP"])
        
        # ============================================
        # СООБЩЕНИЕ 1: ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
        # ============================================
        
        await query.edit_message_text(
            "✅ *ЗАКАЗ ВЫПОЛНЕН!*\n\n"
            "*Все материалы отправлены.*\n"
            "Проверьте чат с ботом 📩\n\n"
            "Спасибо за покупку! 🎁\n\n"
            "Если что-то не получили, напишите в поддержку: @meysternlp",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 ПОСМОТРЕТЬ МАТЕРИАЛЫ", callback_data="view_materials")]
            ])
        )
        
        # Немного ждем
        await asyncio.sleep(1)
        
        # ============================================
        # СООБЩЕНИЕ 2: МАТЕРИАЛЫ
        # ============================================
        
        # Отправляем второе сообщение с материалами
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"📚 *ВАШИ МАТЕРИАЛЫ ГОТОВЫ!*\n\n"
                 f"*Что вы получили:*\n\n"
                 f"1. *Полный разбор профиля (PDF)*\n"
                 f"   • Детальный анализ вашего типа\n"
                 f"   • Рекомендации по развитию\n"
                 f"   • Карта сильных сторон\n\n"
                 f"2. *Терапевтическая сказка (PDF)*\n"
                 f"   • Для трансформации восприятия\n"
                 f"   • Работа с внутренними конфликтами\n\n"
                 f"3. *Книга «ВАРИАТИКА» (PDF)*\n"
                 f"   • Полное руководство по системе\n"
                 f"   • Примеры и практики\n\n"
                 f"4. *Персональные рекомендации*\n"
                 f"   • Пошаговый план развития\n"
                 f"   • Инструменты для работы\n\n"
                 f"*🎯 Ваш профиль:* {profile['name']}\n"
                 f"*🔑 Код профиля:* `{profile_key}`\n"
                 f"*💰 Сумма оплаты:* {payment['amount']} руб\n"
                 f"*🆔 ID заказа:* `{payment_id}`\n\n"
                 f"📥 *Ссылки для скачивания:*\n\n"
                 f"• *Основные материалы:* {profile['url']}\n\n"
                 f"📞 *Поддержка:*\n"
                 f"Если возникли вопросы: @meysternlp\n\n"
                 f"*Спасибо за покупку!* 🎁",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=profile['url'])]
            ]),
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Материалы отправлены пользователю {query.from_user.id} для профиля {profile_key}")

async def view_materials_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр материалов"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Ищем последний оплаченный платеж
    last_payment = None
    for payment_id, payment in db.payments.items():
        if payment["user_id"] == user.id and payment["status"] == "paid":
            last_payment = payment
            break
    
    if not last_payment:
        keyboard = [[InlineKeyboardButton("💎 КУПИТЬ ДОСТУП", callback_data="buy_access")]]
        await query.edit_message_text(
            "📭 *МАТЕРИАЛЫ НЕ НАЙДЕНЫ*\n\n"
            "У вас нет активных покупок.\n\n"
            "Чтобы получить материалы, приобретите доступ:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Показываем материалы
    profile_key = last_payment["profile_key"]
    profile = PROFILES.get(profile_key, PROFILES["SA_4_EXP"])
    
    await query.edit_message_text(
        f"📚 *ВАШИ МАТЕРИАЛЫ*\n\n"
        f"*Ваш профиль:* {profile['name']}\n"
        f"*Код профиля:* `{profile_key}`\n"
        f"*Дата покупки:* {time.strftime('%d.%m.%Y', time.localtime(last_payment.get('paid_at', time.time())))}\n\n"
        f"📥 *Ссылка для скачивания:*\n"
        f"{profile['url']}\n\n"
        f"Нажмите кнопку ниже:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 СКАЧАТЬ МАТЕРИАЛЫ", url=profile['url'])],
            [InlineKeyboardButton("💎 КУПИТЬ ЕЩЁ", callback_data="buy_access")],
            [InlineKeyboardButton("🏠 В ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]
        ]),
        disable_web_page_preview=True
    )

async def my_materials_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мои материалы"""
    query = update.callback_query
    await query.answer()
    
    await view_materials_handler(update, context)

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    query = update.callback_query
    await query.answer()
    
    fake_update = Update(
        update_id=update.update_id + 1000,
        message=query.message
    )
    await start(fake_update, context)

# ============================================
# ЛОГИКА ОПРЕДЕЛЕНИЯ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
# ============================================

async def get_user_profile_from_api(user_id: int) -> str:
    """
    В РЕАЛЬНОЙ СИСТЕМЕ: получает профиль пользователя из API
    Формат ответа API:
    {
        "success": true,
        "profile_key": "SA_4_EXP",
        "type_code": "SA",
        "level": 4,
        "dilts_code": "EXP",
        "display_name": "Социально-Аффилиативный Уровень 4"
    }
    
    Или если профиль не определен:
    {
        "success": false,
        "error": "Профиль не найден"
    }
    """
    # В реальности здесь будет запрос к вашему API:
    # response = requests.get(f"{API_URL}/api/user-profile/{user_id}")
    
    # Для демонстрации возвращаем SA_4_EXP
    return "SA_4_EXP"

def generate_profile_url(profile_key: str) -> str:
    """
    Генерирует или получает ссылку для профиля
    """
    if profile_key in PROFILES:
        return PROFILES[profile_key]["url"]
    
    # Если профиль не найден - логируем и возвращаем fallback
    logger.warning(f"Профиль {profile_key} не найден в карте, использую SA_4_EXP")
    return PROFILES["SA_4_EXP"]["url"]

# ============================================
# ЗАПУСК БОТА
# ============================================

def main():
    """Запуск бота"""
    logger.info("="*60)
    logger.info("🎴 VARIATICA BOT - ФИНАЛЬНАЯ ВЕРСИЯ")
    logger.info("="*60)
    logger.info(f"Доступно профилей: {len(PROFILES)}")
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Регистрируем callback-обработчики
    application.add_handler(CallbackQueryHandler(buy_access_handler, pattern="^buy_access$"))
    application.add_handler(CallbackQueryHandler(test_payment_handler, pattern="^test_payment$"))
    application.add_handler(CallbackQueryHandler(process_payment_handler, pattern="^process_"))
    application.add_handler(CallbackQueryHandler(view_materials_handler, pattern="^view_materials$"))
    application.add_handler(CallbackQueryHandler(my_materials_handler, pattern="^my_materials$"))
    application.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    
    logger.info("✅ Бот запущен!")
    logger.info("📱 Используйте /start в Telegram")
    
    # Запускаем
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
