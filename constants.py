"""
Константы состояний для ConversationHandler
Вынесены в отдельный файл для избежания циклических импортов
"""

# ===== СОСТОЯНИЯ ТЕСТА (10-19) =====
STAGE_1 = 10
STAGE_2 = 11
STAGE_3 = 12
STAGE_4 = 13
CLARIFICATION = 14
RESULTS = 15
GIFT_SCREEN = 16
PACKAGE_SCREEN = 17
OPEN_GIFT_SCREEN = 18
PAYMENT_SCREEN = 19

# ===== СОСТОЯНИЯ 18+ МОДУЛЯ (1-9) =====
# Основные состояния
MY_SEXUAL_PROFILE = 1
SEXUAL_PROFILE_SCREEN = 2
SEXUAL_INVITES_LIST = 3
SEXUAL_FRIEND_PROFILE = 4

# Состояния 4F модуля
FOUR_F_PAYMENT_SCREEN = 5
FOUR_F_CONTENT_SCREEN = 6
FOUR_F_MAIN = 7          # Главное меню 4F (краткое описание)
FOUR_F_DETAILED = 8      # Подробное описание 4F
FOUR_F_MENU = 9          # Меню 4F-ключей для конкретного друга
FOUR_F_CONTENT = 10      # Просмотр открытого 4F-ключа (пересекается с тестом? лучше 20)

# ===== ДОПОЛНИТЕЛЬНЫЕ СОСТОЯНИЯ 18+ (20-29) =====
# Чтобы не конфликтовать с тестом, используем диапазон 20-29
BUY_PACKAGES = 20        # Покупка пакетов ссылок
INVITES_LIST = 21        # Список приглашений (алиас для SEXUAL_INVITES_LIST)
FRIEND_MENU = 22         # Меню друга (алиас для SEXUAL_FRIEND_PROFILE)

# ===== СОСТОЯНИЯ ДЛЯ СОВМЕСТИМОСТИ СО СТАРЫМИ ВЕРСИЯМИ =====
# Эти состояния нужны для обратной совместимости с рабочим файлом v19.0
INVITES_LIST_LEGACY = 2   # Старое состояние INVITES_LIST (для совместимости)

# ===== СОСТОЯНИЯ ДЛЯ 4F (30-39) =====
FOUR_F_MAIN_MENU = 30    # Главное меню 4F (альтернативное название)
FOUR_F_DETAILED_VIEW = 31 # Подробный просмотр 4F
FOUR_F_KEY_MENU = 32     # Меню ключей для друга
FOUR_F_KEY_CONTENT = 33  # Содержимое ключа

# ===== СЛОВАРЬ ДЛЯ СОВМЕСТИМОСТИ С 18+ МОДУЛЕМ =====
# Этот словарь нужен для sexual_18_plus.py, который ожидает SEXUAL_STATES
SEXUAL_STATES = {
    "SEXUAL_PROFILE_SCREEN": SEXUAL_PROFILE_SCREEN,
    "SEXUAL_INVITES_LIST": SEXUAL_INVITES_LIST,
    "SEXUAL_FRIEND_PROFILE": SEXUAL_FRIEND_PROFILE,
    "FOUR_F_PAYMENT_SCREEN": FOUR_F_PAYMENT_SCREEN,
    "FOUR_F_CONTENT_SCREEN": FOUR_F_CONTENT_SCREEN,
    "FOUR_F_MAIN": FOUR_F_MAIN,
    "FOUR_F_DETAILED": FOUR_F_DETAILED,
    "FOUR_F_MENU": FOUR_F_MENU,
    "FOUR_F_CONTENT": FOUR_F_CONTENT,
    "BUY_PACKAGES": BUY_PACKAGES,
    "INVITES_LIST": INVITES_LIST,
    "FRIEND_MENU": FRIEND_MENU,
    "INVITES_LIST_LEGACY": INVITES_LIST_LEGACY,
}

# ===== ЭКСПОРТ ВСЕХ КОНСТАНТ =====
__all__ = [
    # Состояния теста
    'STAGE_1', 'STAGE_2', 'STAGE_3', 'STAGE_4',
    'CLARIFICATION', 'RESULTS',
    'GIFT_SCREEN', 'PACKAGE_SCREEN', 'OPEN_GIFT_SCREEN', 'PAYMENT_SCREEN',
    
    # Состояния 18+ модуля
    'MY_SEXUAL_PROFILE',
    'SEXUAL_PROFILE_SCREEN',
    'SEXUAL_INVITES_LIST',
    'SEXUAL_FRIEND_PROFILE',
    
    # Состояния 4F
    'FOUR_F_PAYMENT_SCREEN',
    'FOUR_F_CONTENT_SCREEN',
    'FOUR_F_MAIN',
    'FOUR_F_DETAILED',
    'FOUR_F_MENU',
    'FOUR_F_CONTENT',
    
    # Дополнительные состояния
    'BUY_PACKAGES',
    'INVITES_LIST',
    'FRIEND_MENU',
    'INVITES_LIST_LEGACY',  # 👈 ДОБАВЛЕНО
    'FOUR_F_MAIN_MENU',
    'FOUR_F_DETAILED_VIEW',
    'FOUR_F_KEY_MENU',
    'FOUR_F_KEY_CONTENT',
    
    # Словарь для совместимости
    'SEXUAL_STATES',
]
