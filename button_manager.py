# button_manager.py
"""
Менеджер динамических кнопок для бота ВАРИАТИКА
Позволяет обновлять кнопки без перезапуска бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Константы (можно менять без перезапуска бота)
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"
BOT_LINK = "https://t.me/Testing_Lichnosti_bot"  # Полная ссылка на бота
SHARE_TEXT = "🔍 Узнай о себе то, о чём ещё не знал! Пройди психодиагностический тест ВАРИАТИКА и получи свой архетип личности. КатеГОрически рекомендую!"

def get_share_url():
    """Генерирует URL для шаринга бота"""
    share_text = f"{SHARE_TEXT}\n\n{BOT_LINK}"
    return f"https://t.me/share/url?url={BOT_LINK}&text={share_text}"

def get_first_keyboard():
    """✅ Клавиатура при первом показе результатов"""
    keyboard = [
        [InlineKeyboardButton("Поделиться ссылкой и получить 🎁", callback_data="share_bot")],
        [InlineKeyboardButton("💎 Полный пакет (690 ₽)", url=PAYMENT_LINK)],  # ✅ 690 ₽ вместо 960 ₽
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_share_confirmation_keyboard():
    """✅ Клавиатура после нажатия на шаринг (инструкция)"""
    keyboard = [
        [InlineKeyboardButton("📤 Открыть меню шаринга", url=get_share_url())],
        [InlineKeyboardButton("✅ Я поделился", callback_data="confirm_share")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_gift_keyboard():
    """✅ Клавиатура после подтверждения шаринга"""
    keyboard = [
        [InlineKeyboardButton("🎁 Получить свой подарок", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("💎 Полный пакет (690 ₽)", url=PAYMENT_LINK)],  # ✅ 690 ₽ вместо 960 ₽
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функции для динамического обновления ссылок
def update_gift_link(new_link: str):
    global GIFT_PDF_LINK
    GIFT_PDF_LINK = new_link
    return True

def update_payment_link(new_link: str):
    global PAYMENT_LINK
    PAYMENT_LINK = new_link
    return True

def update_bot_link(new_link: str):
    global BOT_LINK
    BOT_LINK = new_link
    return True

def update_share_text(new_text: str):
    global SHARE_TEXT
    SHARE_TEXT = new_text
    return True
