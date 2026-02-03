# button_manager.py
"""
Менеджер динамических кнопок для бота ВАРИАТИКА
Позволяет обновлять кнопки без перезапуска бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Константы (можно менять без перезапуска бота)
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"
BOT_LINK = "t.me/Testing_Lichnosti_bot"  # Ссылка на вашего бота
SHARE_MESSAGE = f"🔍 Узнай о себе то, о чём ещё не знал! Пройди психодиагностический тест ВАРИАТИКА и получи свой архетип личности. {BOT_LINK}"

def get_results_keyboard(user_shared: bool = False):
    """
    Возвращает клавиатуру для финального экрана
    user_shared: True, если пользователь уже поделился ботом
    """
    if not user_shared:
        # ✅ Первая клавиатура (пользователь ещё не делился ботом)
        keyboard = [
            [InlineKeyboardButton("Поделиться ссылкой и получить 🎁", url=f"https://t.me/share/url?url={BOT_LINK}&text={SHARE_MESSAGE}")],  # ✅ ИЗМЕНЕНО
            [InlineKeyboardButton("💎 Полный пакет", url=PAYMENT_LINK)],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        # ✅ Клавиатура после шаринга
        keyboard = [
            [InlineKeyboardButton("🎁 Получить свой подарок", url=GIFT_PDF_LINK)],  # ✅ Теперь кнопка получения подарка
            [InlineKeyboardButton("💎 Полный пакет", url=PAYMENT_LINK)],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_after_share_keyboard():
    """✅ Явная функция для получения клавиатуры после шаринга"""
    keyboard = [
        [InlineKeyboardButton("🎁 Получить свой подарок", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("💎 Полный пакет", url=PAYMENT_LINK)],
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функции для динамического обновления ссылок (без перезапуска бота)
def update_gift_link(new_link: str):
    """Обновить ссылку на подарок"""
    global GIFT_PDF_LINK
    GIFT_PDF_LINK = new_link
    return True

def update_payment_link(new_link: str):
    """Обновить ссылку на оплату"""
    global PAYMENT_LINK
    PAYMENT_LINK = new_link
    return True

def update_bot_link(new_link: str):
    """Обновить ссылку на бота"""
    global BOT_LINK
    BOT_LINK = new_link
    return True

def update_share_message(new_message: str):
    """Обновить сообщение для шаринга"""
    global SHARE_MESSAGE
    SHARE_MESSAGE = new_message
    return True

def get_current_links():
    """Получить текущие ссылки (для мониторинга)"""
    return {
        "gift": GIFT_PDF_LINK,
        "payment": PAYMENT_LINK,
        "bot": BOT_LINK,
        "share_message": SHARE_MESSAGE
    }
