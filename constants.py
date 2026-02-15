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
FOUR_F_CONTENT = 10      # 👈 ДОБАВЛЕНО (просмотр открытого ключа)

# ===== ДОПОЛНИТЕЛЬНЫЕ СОСТОЯНИЯ (20-39) =====
# Состояния для пакетов
BUY_PACKAGES = 20        # Покупка пакетов ссылок
INVITES_LIST = 21        # Список приглашений (алиас для SEXUAL_INVITES_LIST)
FRIEND_MENU = 22         # Меню друга (алиас для SEXUAL_FRIEND_PROFILE)

# Состояния для 4F (альтернативные названия)
FOUR_F_MAIN_MENU = 30    # Главное меню 4F (альтернативное название)
FOUR_F_DETAILED_VIEW = 31 # Подробный просмотр 4F
FOUR_F_KEY_MENU = 32     # Меню ключей для друга
FOUR_F_KEY_CONTENT = 33  # Содержимое ключа

# ===== СОСТОЯНИЯ ДЛЯ СОВМЕСТИМОСТИ СО СТАРЫМИ ВЕРСИЯМИ =====
# 👇 ИСПРАВЛЕНО: используем другие значения, чтобы избежать конфликтов
RESULTS_SCREEN_LEGACY = 100       # Старое состояние RESULTS_SCREEN
MY_SEXUAL_PROFILE_LEGACY = 101    # Старое состояние MY_SEXUAL_PROFILE
INVITES_LIST_LEGACY = 102         # Старое состояние INVITES_LIST
FOUR_F_CONTENT_LEGACY = 103       # Старое состояние FOUR_F_CONTENT

# ===== СОСТОЯНИЯ ДЛЯ ЧЕТКОГО РАЗДЕЛЕНИЯ =====
# Чтобы избежать путаницы, добавляем явные названия
MY_SEXUAL_PROFILE_VIEW = 50      # Просмотр интимного профиля
MY_INVITES_VIEW = 51             # Просмотр моих отражений
FRIEND_PROFILE_VIEW = 52         # Просмотр профиля друга
FOUR_F_PURCHASE = 53             # Покупка 4F ключа
FOUR_F_OPEN = 54                 # Открытие 4F ключа

# ===== СЛОВАРЬ ДЛЯ СОВМЕСТИМОСТИ С 18+ МОДУЛЕМ =====
SEXUAL_STATES = {
    # Основные состояния
    "MY_SEXUAL_PROFILE": MY_SEXUAL_PROFILE,
    "SEXUAL_PROFILE_SCREEN": SEXUAL_PROFILE_SCREEN,
    "SEXUAL_INVITES_LIST": SEXUAL_INVITES_LIST,
    "SEXUAL_FRIEND_PROFILE": SEXUAL_FRIEND_PROFILE,
    
    # Состояния 4F
    "FOUR_F_PAYMENT_SCREEN": FOUR_F_PAYMENT_SCREEN,
    "FOUR_F_CONTENT_SCREEN": FOUR_F_CONTENT_SCREEN,
    "FOUR_F_MAIN": FOUR_F_MAIN,
    "FOUR_F_DETAILED": FOUR_F_DETAILED,
    "FOUR_F_MENU": FOUR_F_MENU,
    "FOUR_F_CONTENT": FOUR_F_CONTENT,  # 👈 ДОБАВЛЕНО
    
    # Дополнительные состояния
    "BUY_PACKAGES": BUY_PACKAGES,
    "INVITES_LIST": INVITES_LIST,
    "FRIEND_MENU": FRIEND_MENU,
    
    # Для обратной совместимости (исправленные значения)
    "RESULTS_SCREEN_LEGACY": RESULTS_SCREEN_LEGACY,
    "MY_SEXUAL_PROFILE_LEGACY": MY_SEXUAL_PROFILE_LEGACY,
    "INVITES_LIST_LEGACY": INVITES_LIST_LEGACY,
    "FOUR_F_CONTENT_LEGACY": FOUR_F_CONTENT_LEGACY,
}
