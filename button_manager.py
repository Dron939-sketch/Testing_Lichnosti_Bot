# button_manager.py
"""
МЕНЕДЖЕР КНОПОК ДЛЯ БОТА ВАРИАТИКА
Содержит функции для создания клавиатур:
1. После результатов теста (ещё не поделились)
2. После шаринга (получить подарок)
3. Для подтверждения шаринга
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ============================================
# КОНСТАНТЫ ДЛЯ КНОПОК
# ============================================
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую:"

def get_share_url():
    """Генерирует ссылку для шаринга с текстом"""
    import urllib.parse
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    return f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"

def get_results_keyboard(user_shared=False):
    """
    Клавиатура после получения результатов теста
    
    Args:
        user_shared: Пользователь уже поделился ботом?
    """
    if user_shared:
        # Если уже поделился - показываем кнопку получить подарок
        keyboard = [
            [InlineKeyboardButton("🎁 Получить свой подарок", callback_data="get_gift")],
            [InlineKeyboardButton("💎 Купить полный пакет", callback_data="buy_full")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        # Если ещё не поделился - показываем кнопку шаринга
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться ссылкой и получить 🎁", callback_data="share_link")],
            [InlineKeyboardButton("💎 Купить полный пакет", callback_data="buy_full")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_share_confirmation_keyboard():
    """Клавиатура для подтверждения шаринга"""
    keyboard = [
        [InlineKeyboardButton("📤 Поделиться ботом", url=get_share_url())],
        [InlineKeyboardButton("✅ Я поделился", callback_data="share_confirmed")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_results")]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_gift_keyboard():
    """Клавиатура для получения подарка"""
    keyboard = [
        [InlineKeyboardButton("🎁 Получить свой подарок", callback_data="get_gift")],
        [InlineKeyboardButton("💎 Купить полный пакет", callback_data="buy_full")],
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
    ]
    
    return InlineKeyboardMarkup(keyboard)
