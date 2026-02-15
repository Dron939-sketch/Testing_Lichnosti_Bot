"""
Константы состояний для ConversationHandler
Вынесены в отдельный файл для избежания циклических импортов
ВЕРСИЯ 2.0: ПОЛНАЯ СОВМЕСТИМОСТЬ
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
# Эти состояния нужны для обратной совместимости с рабочим файлом v19.0
RESULTS_SCREEN = 0       # Старое состояние RESULTS_SCREEN
MY_SEXUAL_PROFILE_LEGACY = 1  # Старое состояние MY_SEXUAL_PROFILE (для совместимости)
INVITES_LIST_LEGACY = 2  # Старое состояние INVITES_LIST (для совместимости)
FOUR_F_CONTENT_LEGACY = 5  # Старое состояние FOUR_F_CONTENT

# ===== СОСТОЯНИЯ ДЛЯ ЧЕТКОГО РАЗДЕЛЕНИЯ =====
# Чтобы избежать путаницы, добавляем явные названия
MY_SEXUAL_PROFILE_VIEW = 50      # Просмотр интимного профиля
MY_INVITES_VIEW = 51             # Просмотр моих отражений
FRIEND_PROFILE_VIEW = 52         # Просмотр профиля друга
FOUR_F_PURCHASE = 53             # Покупка 4F ключа
FOUR_F_OPEN = 54                 # Открытие 4F ключа

# ===== СЛОВАРЬ ДЛЯ СОВМЕСТИМОСТИ С 18+ МОДУЛЕМ =====
# Этот словарь нужен для sexual_18_plus.py, который ожидает SEXUAL_STATES
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
    
    # Дополнительные состояния
    "BUY_PACKAGES": BUY_PACKAGES,
    "INVITES_LIST": INVITES_LIST,
    "FRIEND_MENU": FRIEND_MENU,
    
    # Для обратной совместимости
    "RESULTS_SCREEN": RESULTS_SCREEN,
    "MY_SEXUAL_PROFILE_LEGACY": MY_SEXUAL_PROFILE_LEGACY,
    "INVITES_LIST_LEGACY": INVITES_LIST_LEGACY,
    "FOUR_F_CONTENT_LEGACY": FOUR_F_CONTENT_LEGACY,
    
    # Явные состояния
    "MY_SEXUAL_PROFILE_VIEW": MY_SEXUAL_PROFILE_VIEW,
    "MY_INVITES_VIEW": MY_INVITES_VIEW,
    "FRIEND_PROFILE_VIEW": FRIEND_PROFILE_VIEW,
    "FOUR_F_PURCHASE": FOUR_F_PURCHASE,
    "FOUR_F_OPEN": FOUR_F_OPEN,
}

# ===== ПРОВЕРКА НА ДУБЛИКАТЫ =====
def check_duplicates():
    """Проверяет, нет ли одинаковых значений у разных констант"""
    values = {}
    duplicates = []
    
    for name, value in globals().items():
        if name.isupper() and isinstance(value, int):
            if value in values:
                duplicates.append(f"{name}={value} конфликтует с {values[value]}")
            else:
                values[value] = name
    
    if duplicates:
        print("\n⚠️ ВНИМАНИЕ: Найдены дубликаты состояний:")
        for d in duplicates:
            print(f"   {d}")
        print()
    else:
        print("✅ Конфликтов состояний не найдено")

# Вызываем проверку при импорте
check_duplicates()

# ===== ЭКСПОРТ ВСЕХ КОНСТАНТ =====
__all__ = [
    # Состояния теста
    'STAGE_1', 'STAGE_2', 'STAGE_3', 'STAGE_4',
    'CLARIFICATION', 'RESULTS',
    'GIFT_SCREEN', 'PACKAGE_SCREEN', 'OPEN_GIFT_SCREEN', 'PAYMENT_SCREEN',
    
    # Состояния 18+ модуля (основные)
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
    
    # Дополнительные состояния
    'BUY_PACKAGES',
    'INVITES_LIST',
    'FRIEND_MENU',
    'FOUR_F_MAIN_MENU',
    'FOUR_F_DETAILED_VIEW',
    'FOUR_F_KEY_MENU',
    'FOUR_F_KEY_CONTENT',
    
    # Для обратной совместимости
    'RESULTS_SCREEN',
    'MY_SEXUAL_PROFILE_LEGACY',
    'INVITES_LIST_LEGACY',
    'FOUR_F_CONTENT_LEGACY',
    
    # Явные состояния
    'MY_SEXUAL_PROFILE_VIEW',
    'MY_INVITES_VIEW',
    'FRIEND_PROFILE_VIEW',
    'FOUR_F_PURCHASE',
    'FOUR_F_OPEN',
    
    # Словарь для совместимости
    'SEXUAL_STATES',
]

# ===== КОНСТАНТЫ ДЛЯ УДОБСТВА =====
# Группы состояний
TEST_STATES = [STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS]
GIFT_STATES = [GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN]
PAYMENT_STATES = [PAYMENT_SCREEN, FOUR_F_PAYMENT_SCREEN]
SEXUAL_STATES_LIST = [
    MY_SEXUAL_PROFILE, SEXUAL_PROFILE_SCREEN, SEXUAL_INVITES_LIST, SEXUAL_FRIEND_PROFILE,
    FOUR_F_MAIN, FOUR_F_DETAILED, FOUR_F_MENU, FOUR_F_CONTENT_SCREEN,
    BUY_PACKAGES, INVITES_LIST, FRIEND_MENU
]

ALL_STATES = TEST_STATES + GIFT_STATES + PAYMENT_STATES + SEXUAL_STATES_LIST

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С СОСТОЯНИЯМИ =====
def get_state_name(state: int) -> str:
    """Возвращает имя состояния по его значению"""
    for name, value in globals().items():
        if name.isupper() and value == state:
            return name
    return f"UNKNOWN_{state}"

def is_test_state(state: int) -> bool:
    """Проверяет, относится ли состояние к тесту"""
    return state in TEST_STATES

def is_sexual_state(state: int) -> bool:
    """Проверяет, относится ли состояние к 18+ модулю"""
    return state in SEXUAL_STATES_LIST

def is_payment_state(state: int) -> bool:
    """Проверяет, относится ли состояние к оплате"""
    return state in PAYMENT_STATES
