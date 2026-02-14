"""
Константы состояний для ConversationHandler
Вынесены в отдельный файл для избежания циклических импортов
"""

# Состояния теста (10-19)
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

# Состояния 18+ модуля (1-9)
MY_SEXUAL_PROFILE = 1
SEXUAL_PROFILE_SCREEN = 2
SEXUAL_INVITES_LIST = 3
SEXUAL_FRIEND_PROFILE = 4
FOUR_F_PAYMENT_SCREEN = 5
FOUR_F_CONTENT_SCREEN = 6
