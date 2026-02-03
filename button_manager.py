# button_manager.py
"""
Менеджер динамических кнопок для бота ВАРИАТИКА
Позволяет обновлять кнопки без перезапуска бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Константы (можно менять без перезапуска бота)
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"
SHARE_MESSAGE = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны личности. КатеГОрически рекомендую пройти!"

def get_results_keyboard(user_shared: bool = False):
    """
    Возвращает клавиатуру для финального экрана
    user_shared: True, если пользователь уже поделился результатом
    """
    if not user_shared:
        # Стандартная клавиатура (первый показ)
        keyboard = [
            [InlineKeyboardButton("🎁 Поделиться результатом", switch_inline_query=SHARE_MESSAGE)],
            [InlineKeyboardButton("💎 Получить полный пакет (690 ₽)", url=PAYMENT_LINK)],
            [InlineKeyboardButton("🎁 Получить подарок", url=GIFT_PDF_LINK)]
        ]
    else:
        # Клавиатура после шаринга
        keyboard = [
            [InlineKeyboardButton("🎁 Получить подарок", url=GIFT_PDF_LINK)],
            [InlineKeyboardButton("💎 Полный пакет (690 ₽)", url=PAYMENT_LINK)],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_gift_keyboard():
    """Клавиатура для экрана с подарком после шаринга"""
    keyboard = [
        [InlineKeyboardButton("🎁 Получить подарок", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("💎 Полный пакет (690 ₽)", url=PAYMENT_LINK)],
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
        "share_message": SHARE_MESSAGE
    }
