"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа + адаптивные уточнения + СИСТЕМА БАЛЛОВ как в карточном тесте
ИСПРАВЛЕННАЯ ВЕРСИЯ: fix_profile_errors + clean_headers + beautiful_formatting
"""

import logging
import os
import asyncio
import urllib.parse
import math
import re
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ============================================
# ИСПРАВЛЕННЫЙ ИМПОРТ - ФАЙЛОВАЯ СИСТЕМА
# ============================================
from loader import loader  # Импортируем загрузчик
from base import VariaticaProfile  # Импортируем класс профиля

# Получение токена из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
#  СОСТОЯНИЯ ConversationHandler
# ============================================
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION = range(10)

# ============================================
# КОНСТАНТЫ
# ============================================
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую:"
PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"

# ============================================
# ДАННЫЕ ВОПРОСОВ (ЭТАП 1 - БЕЗ ИЗМЕНЕНИЙ)
# ============================================

# ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ
STAGE_1_QUESTIONS = [
    {
        "id": "q1_1",
        "text": "У тебя неожиданно освободился вечер.\n\nЧто звучит привлекательнее?",
        "options": {
            "a": {"text": "Позвать друзей", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Побыть одному", "scores": {"INTERNAL": 2}},
            "c": {"text": "Сходить куда-то (событие/место)", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Почитать/посмотреть что-то", "scores": {"INTERNAL": 1}}
        }
    },
    {
        "id": "q1_2",
        "text": "Что даёт тебе больше ресурса для жизни?",
        "options": {
            "a": {"text": "Люди, события, движение", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Мысли, чувства, тишина", "scores": {"INTERNAL": 2}},
            "c": {"text": "И то, и то в равной степени", "scores": {}},
            "d": {"text": "Зависит от ситуации", "scores": {}}
        }
    },
    {
        "id": "q1_3",
        "text": "Ты на вечеринке, где почти никого не знаешь.\n\nЧто происходит?",
        "options": {
            "a": {"text": "Активно знакомлюсь со всеми", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Нахожу 1-2 человек и общаюсь с ними", "scores": {"EXTERNAL": 1}},
            "c": {"text": "Держусь в стороне", "scores": {"INTERNAL": 1}},
            "d": {"text": "Ухожу при первой возможности", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_4",
        "text": "Если бы твоя жизнь была местом, это было бы:",
        "options": {
            "a": {"text": "Оживлённая площадь", "scores": {"EXTERNAL": 2}},
            "b": {"text": "Уютная комната", "scores": {"INTERNAL": 1}},
            "c": {"text": "Открытое пространство", "scores": {"EXTERNAL": 1}},
            "d": {"text": "Тихое уединённое место", "scores": {"INTERNAL": 2}}
        }
    },
    {
        "id": "q1_5",
        "text": "Что тебя больше выбивает из равновесия?",
        "options": {
            "a": {"text": "Когда тебя не понимают", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Когда теряешь что-то важное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Когда не ясно, что происходит", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Когда всё идёт не по плану", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_6",
        "text": "Что для тебя важнее?",
        "options": {
            "a": {"text": "Достичь цели", "scores": {"MATERIAL": 1}},
            "b": {"text": "Сохранить отношения", "scores": {"SYMBOLIC": 2}},
            "c": {"text": "Понять суть", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Сделать результат", "scores": {"MATERIAL": 2}}
        }
    },
    {
        "id": "q1_7",
        "text": "Что страшнее потерять?",
        "options": {
            "a": {"text": "Связь с важными людьми", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Финансовую стабильность", "scores": {"MATERIAL": 2}},
            "c": {"text": "Понимание себя", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Контроль над ситуацией", "scores": {"MATERIAL": 1}}
        }
    },
    {
        "id": "q1_8",
        "text": "Вспомни последнюю сильную тревогу.\n\nО чём она была?",
        "options": {
            "a": {"text": "Меня отвергнут / не поймут", "scores": {"SYMBOLIC": 2}},
            "b": {"text": "Я потеряю что-то ценное", "scores": {"MATERIAL": 2}},
            "c": {"text": "Я не понимаю, что со мной", "scores": {"SYMBOLIC": 1}},
            "d": {"text": "Я не справлюсь / не успею", "scores": {"MATERIAL": 1}}
        }
    }
]

# ТИПЫ ВОСПРИЯТИЯ
PERCEPTION_TYPES = {
    ("EXTERNAL", "SYMBOLIC"): {
        "name": "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ",
        "code": "SA",
        "description": "Фокус на внешних отношениях и социальном принятии"
    },
    ("INTERNAL", "SYMBOLIC"): {
        "name": "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ",
        "code": "IA",
        "description": "Фокус на внутренних смыслах и глубине переживания"
    },
    ("EXTERNAL", "MATERIAL"): {
        "name": "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ",
        "code": "SP",
        "description": "Фокус на внешних достижениях и результатат"
    },
    ("INTERNAL", "MATERIAL"): {
        "name": "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ",
        "code": "IP",
        "description": "Фокус на внутреннем порядке и системах понимания"
    }
}

# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

STAGE_2_QUESTIONS = {
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": [
        {
            "text": "Сколько у тебя близких людей?\n\n(С кем можно говорить о личном)",
            "options": {
                "1": "Нет таких",
                "2": "1-2 человека", 
                "3": "3-5 человек",
                "5": "Больше 5"
            }
        },
        {
            "text": "Как ты к этому относишься?",
            "options": {
                "1": "Мне не хватает близости",
                "2": "Я в процессе поиска своих людей",
                "3": "Меня это устраивает",
                "4": "Я не нуждаюсь в этом"
            }
        },
        {
            "text": "Как часто за месяц ты отменяешь встречи с друзьями?",
            "options": {
                "1": "Не отменяю / нет встреч",
                "3": "1-2 раза",
                "2": "3-5 раз",
                "1": "Постоянно отменяю"
            }
        },
        {
            "text": "Почему отменяешь?",
            "options": {
                "1": "Нет сил на людей",
                "2": "Эти люди не мои",
                "5": "Появились более важные дела",
                "3": "Не отменяю"
            }
        },
        {
            "text": "Как часто ты чувствуешь, что тебя не понимают?",
            "options": {
                "1": "Постоянно",
                "2": "Часто",
                "4": "Иногда",
                "3": "Редко или никогда"
            }
        },
        {
            "text": "Что ты с этим делаешь?",
            "options": {
                "1": "Пытаюсь объясниться",
                "2": "Ищу тех, кто поймёт",
                "4": "Принимаю это",
                "3": "Меня понимают"
            }
        },
        {
            "text": "Твой друг постоянно меняет компании.\n\nКак думаешь, почему?",
            "options": {
                "2": "Ищет своих людей",
                "1": "Боятся близости",
                "5": "Ему везде интересно",
                "4": "Не может быть собой"
            }
        },
        {
            "text": "Что для тебя значит «найти своих людей»?",
            "options": {
                "2": "Место, где меня принимают",
                "3": "Люди, с которыми не нужно притворяться",
                "5": "Глубокая связь на уровне ценностей",
                "1": "Не думал об этом"
            }
        }
    ],
    "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": [
        {
            "text": "Как часто ты задаёшь себе вопрос «В чём смысл?»",
            "options": {
                "1": "Постоянно, это мучительно",
                "2": "Часто, ищу ответы",
                "4": "Иногда, это интересно",
                "5": "Редко, я знаю свой смысл"
            }
        },
        {
            "text": "Что ты чувствуешь, когда остаёшься наедине с собой?",
            "options": {
                "1": "Тревогу, пустоту",
                "2": "Вопросы без ответов",
                "4": "Спокойствие, ясность",
                "5": "Глубину, полноту"
            }
        },
        {
            "text": "Сколько времени в день ты проводишь в размышлениях?",
            "options": {
                "1": "Почти всё время (застреваю)",
                "2": "Несколько часов",
                "4": "1-2 часа осознанно",
                "5": "Мало, я живу в моменте"
            }
        },
        {
            "text": "Что происходит после размышлений?",
            "options": {
                "1": "Ещё больше вопросов",
                "2": "Новые идеи, но нет действий",
                "4": "Понимание и действия",
                "5": "Трансформация опыта"
            }
        },
        {
            "text": "Как ты относишься к своим переживаниям?",
            "options": {
                "1": "Боюсь их, избегаю",
                "2": "Анализирую, пытаюсь понять",
                "4": "Принимаю и наблюдаю",
                "5": "Использую как материал для роста"
            }
        },
        {
            "text": "Что для тебя значит «быть собой»?",
            "options": {
                "1": "Не знаю, кто я",
                "2": "Ищу себя",
                "4": "Знаю и принимаю себя",
                "5": "Я — это процесс, а не статус"
            }
        },
        {
            "text": "Человек погружён в экзистенциальный кризис.\n\nЧто ему делать?",
            "options": {
                "1": "Отвлечься, не думать об этом",
                "2": "Искать ответы (книги, терапия)",
                "4": "Прожить это как опыт",
                "5": "Это не кризис, а трансформация"
            }
        },
        {
            "text": "Что для тебя глубина жизни?",
            "options": {
                "1": "Не понимаю, что это",
                "2": "Хочу её найти",
                "4": "Чувствую её в моменты",
                "5": "Живу в ней постоянно"
            }
        }
    ],
    "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": [
        {
            "text": "Сколько целей ты достиг за последний год?",
            "options": {
                "1": "Ни одной (только планировал)",
                "2": "1-2 цели",
                "4": "3-5 целей",
                "5": "Больше 5 целей"
            }
        },
        {
            "text": "Как ты себя чувствуешь, когда достигаешь цели?",
            "options": {
                "1": "Пусто (а что дальше?)",
                "2": "Радость, но ненадолго",
                "4": "Удовлетворение",
                "5": "Уже думаю о следующей"
            }
        },
        {
            "text": "Как часто ты откладываешь важные дела?",
            "options": {
                "1": "Постоянно (прокрастинация)",
                "2": "Часто",
                "4": "Иногда",
                "5": "Редко или никогда"
            }
        },
        {
            "text": "Почему откладываешь?",
            "options": {
                "1": "Страх неудачи",
                "2": "Не знаю, с чего начать",
                "4": "Жду подходящего момента",
                "5": "Не откладываю"
            }
        },
        {
            "text": "Что для тебя успех?",
            "options": {
                "1": "Не знаю, не достигал",
                "2": "Деньги, статус, признание",
                "4": "Реализация своих целей",
                "5": "Влияние и вклад в мир"
            }
        },
        {
            "text": "Как ты относишься к конкуренции?",
            "options": {
                "1": "Избегаю её",
                "2": "Боюсь проиграть",
                "4": "Мотивирует меня",
                "5": "Играю свою игру"
            }
        },
        {
            "text": "Человек хочет большего, но не действует.\n\nПочему?",
            "options": {
                "1": "Не верит в себя",
                "2": "Не знает, как",
                "4": "Ждёт готовности",
                "5": "На самом деле не хочет"
            }
        },
        {
            "text": "Что важнее: процесс или результат?",
            "options": {
                "1": "Результат, но его нет",
                "2": "Результат любой ценой",
                "4": "Баланс процесса и результата",
                "5": "Процесс = результат"
            }
        }
    ],
    "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": [
        {
            "text": "Насколько упорядочена твоя жизнь?",
            "options": {
                "1": "Хаос, не могу навести порядок",
                "2": "Пытаюсь структурировать",
                "4": "Есть система, которая работает",
                "5": "Гибкая структура под задачи"
            }
        },
        {
            "text": "Что происходит, когда нарушается твой порядок?",
            "options": {
                "1": "Паника, тревога",
                "2": "Раздражение, дискомфорт",
                "4": "Адаптируюсь",
                "5": "Это часть процесса"
            }
        },
        {
            "text": "Как ты принимаешь решения?",
            "options": {
                "1": "Не могу выбрать (анализ  паралич)",
                "2": "Долго взвешиваю все варианты",
                "4": "Анализирую и выбираю оптимальное",
                "5": "Быстро, на основе критериев"
            }
        },
        {
            "text": "Что для тебя понимание?",
            "options": {
                "1": "Не могу понять, как всё устроено",
                "2": "Ищу логику и закономерности",
                "4": "Вижу систему и связи",
                "5": "Создаю новые модели понимания"
            }
        },
        {
            "text": "Как ты относишься к неопределённости?",
            "options": {
                "1": "Не выношу её",
                "2": "Пытаюсь всё просчитать",
                "4": "Принимаю как данность",
                "5": "Использую как ресурс"
            }
        },
        {
            "text": "Сколько у тебя систем организации жизни?",
            "options": {
                "1": "Нет системы",
                "2": "Пробую разные, ничего не работает",
                "4": "Одна рабочая система",
                "5": "Несколько интегрированных систем"
            }
        },
        {
            "text": "Человек перегружен информацией.\n\nЧто делать?",
            "options": {
                "1": "Избегать информации",
                "2": "Пытаться всё изучить",
                "4": "Фильтровать по критериям",
                "5": "Создать систему обработки"
            }
        },
        {
            "text": "Что для тебя контроль?",
            "options": {
                "1": "Не могу контролировать жизнь",
                "2": "Пытаюсь всё контролировать",
                "4": "Контролирую важное",
                "5": "Контроль = осознанность"
            }
        }
    ]
}

# ТАБЛИЦА НАЧИСЛЕНИЯ БАЛЛОВ ДЛЯ ЭТАПА 2
STAGE_2_SCORING = {
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": {
        0: {"1": 2, "2": 2, "3": 2, "5": 2},
        1: {"1": 2, "2": 2, "3": 2, "4": 2},
        2: {"1": 2, "3": 2, "2": 2, "1": 2},
        3: {"1": 2, "2": 2, "5": 2, "3": 2},
        4: {"1": 2, "2": 2, "4": 2, "3": 2},
        5: {"1": 2, "2": 2, "4": 2, "3": 2},
        6: {"2": 1, "1": 1, "5": 2, "4": 2},
        7: {"2": 1, "3": 2, "5": 2, "1": 1}
    },
    "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": {
        0: {"1": 2, "2": 2, "4": 2, "5": 2},
        1: {"1": 2, "2": 2, "4": 2, "5": 2},
        2: {"1": 2, "2": 2, "4": 2, "5": 2},
        3: {"1": 2, "2": 2, "4": 2, "5": 2},
        4: {"1": 1, "2": 1, "4": 2, "5": 2},
        5: {"1": 1, "2": 1, "4": 2, "5": 2},
        6: {"2": 1, "4": 2, "5": 2, "1": 1},
        7: {"4": 2, "5": 2, "1": 1, "2": 1}
    },
    "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": {
        0: {"1": 2, "2": 2, "4": 2, "5": 2},
        1: {"1": 2, "2": 2, "4": 2, "5": 2},
        2: {"1": 2, "2": 2, "4": 2, "5": 2},
        3: {"1": 2, "2": 2, "4": 2, "5": 2},
        4: {"1": 1, "2": 1, "4": 2, "5": 2},
        5: {"1": 1, "2": 1, "4": 2, "5": 2},
        6: {"2": 1, "4": 2, "5": 2, "1": 1},
        7: {"4": 2, "5": 2, "1": 1, "2": 1}
    },
    "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": {
        0: {"1": 2, "2": 2, "4": 2, "5": 2},
        1: {"1": 2, "2": 2, "4": 2, "5": 2},
        2: {"1": 2, "2": 2, "4": 2, "5": 2},
        3: {"1": 2, "2": 2, "4": 2, "5": 2},
        4: {"1": 1, "2": 1, "4": 2, "5": 2},
        5: {"1": 1, "2": 1, "4": 2, "5": 2},
        6: {"2": 1, "4": 2, "5": 2, "1": 1},
        7: {"4": 2, "5": 2, "1": 1, "2": 1}
    }
}

# ============================================
# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
# ============================================

STAGE_3_QUESTIONS = [
    {"id": "q3_1", "text": "Вспомни последнюю неделю.\n\nСколько раз ты сделал что-то, что потом пожалел?", "options": {"a": {"text": "Ни разу", "level": 5}, "b": {"text": "1-2 раза", "level": 3}, "c": {"text": "3-5 раз", "level": 2}, "d": {"text": "Больше 5 раз", "level": 1}}},
    {"id": "q3_2", "text": "Последний конфликт.\n\nЧто ты сделал?", "options": {"a": {"text": "Избежал", "level": 1}, "b": {"text": "Уступил", "level": 1}, "c": {"text": "Отстоял позицию", "level": 3}, "d": {"text": "Нашёл компромисс", "level": 5}}},
    {"id": "q3_3", "text": "Как ты принимаешь важные решения?", "options": {"a": {"text": "Долго мучаюсь", "level": 1}, "b": {"text": "Взвешиваю варианты", "level": 3}, "c": {"text": "Быстро, по интуиции", "level": 5}, "d": {"text": "Жду, когда решение придёт само", "level": 4}}},
    {"id": "q3_4", "text": "Как часто ты делаешь то, что не хочешь, но «надо»?", "options": {"a": {"text": "Постоянно (вся жизнь — «надо»)", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко (делаю то, что хочу)", "level": 5}}},
    {"id": "q3_5", "text": "Вспомни последнюю сильная эмоция.\n\nЧто ты с ней сделал?", "options": {"a": {"text": "Подавил", "level": 1}, "b": {"text": "Проанализировал", "level": 3}, "c": {"text": "Выразил (слова/действия/творчество)", "level": 5}, "d": {"text": "Наблюдал за ней", "level": 4}}},
    {"id": "q3_6", "text": "Как ты относишься к своим слабостям?", "options": {"a": {"text": "Стыжусь их", "level": 1}, "b": {"text": "Пытаюсь исправить", "level": 2}, "c": {"text": "Принимаю их", "level": 4}, "d": {"text": "Вижу в них силу", "level": 6}}},
    {"id": "q3_7", "text": "Как часто ты чувствуешь, что живёшь не своей жизнью?", "options": {"a": {"text": "Постоянно", "level": 1}, "b": {"text": "Часто", "level": 2}, "c": {"text": "Иногда", "level": 3}, "d": {"text": "Редко или никогда", "level": 5}}},
    {"id": "q3_8", "text": "Что ты делаешь, когда не знаешь, что делать?", "options": {"a": {"text": "Паникую", "level": 1}, "b": {"text": "Ищу информацию", "level": 2}, "c": {"text": "Действую методом проб", "level": 3}, "d": {"text": "Жду ясности", "level": 4}}}
]

# ============================================
# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

STAGE_4_QUESTIONS = [
    {"id": "q4_1", "text": "Как часто ты чувствуешь, что «что-то не так» в жизни?", "options": {"a": {"text": "Постоянно", "dilts": "IDENTITY"}, "b": {"text": "Часто", "dilts": "VALUES"}, "c": {"text": "Иногда", "dilts": "CAPABILITIES"}, "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}}},
    {"id": "q4_2", "text": "Что именно «не так»?\n\nВыбери то, что ближе всего:", "options": {"a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"}, "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"}, "c": {"text": "Не умею делать то, что хочу", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}}},
    {"id": "q4_3", "text": "Человек чувствует себя несчастным.\n\nВ чём, скорее всего, причина?", "options": {"a": {"text": "Не те люди вокруг", "dilts": "ENVIRONMENT"}, "b": {"text": "Делает не то, что хочет", "dilts": "BEHAVIOR"}, "c": {"text": "Не умеет делать то, что хочет", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимает, чего хочет", "dilts": "VALUES"}}},
    {"id": "q4_4", "text": "Если бы ты мог изменить что-то одно, что бы это было?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Своё понимание целей", "dilts": "VALUES"}}},
    {"id": "q4_5", "text": "Что для тебя сложнее всего?", "options": {"a": {"text": "Изменить внешные условия", "dilts": "ENVIRONMENT"}, "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"}, "c": {"text": "Научиться новому", "dilts": "CAPABILITIES"}, "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}}},
    {"id": "q4_6", "text": "Когда ты застреваешь в проблеме, что обычно не хватает?", "options": {"a": {"text": "Ресурсов (время, деньги, связи)", "dilts": "ENVIRONMENT"}, "b": {"text": "Действий (не начинаю)", "dilts": "BEHAVIOR"}, "c": {"text": "Навыков (не умею)", "dilts": "CAPABILITIES"}, "d": {"text": "Понимания (не знаю зачем)", "dilts": "VALUES"}}},
    {"id": "q4_7", "text": "Что мешает тебе быть счастливым?", "options": {"a": {"text": "Обстоятельства", "dilts": "ENVIRONMENT"}, "b": {"text": "Мои действия", "dilts": "BEHAVIOR"}, "c": {"text": "Мои ограничения", "dilts": "CAPABILITIES"}, "d": {"text": "Я не знаю, что такое счастье", "dilts": "VALUES"}}},
    {"id": "q4_8", "text": "Если бы у тебя была волшебная палочка, что бы ты изменил?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Себя (кто я)", "dilts": "IDENTITY"}}}
]

# УРОВНИ ДИЛТСА
DILTS_LEVELS = {
    "ENVIRONMENT": {"name": "ОКРУЖЕНИЕ", "code": "env", "description": "Проблема во внешних условиях", "solution": "Измени окружение или отношение к нему"},
    "BEHAVIOR": {"name": "ПОВЕДЕНИЕ", "code": "beh", "description": "Проблема в действиях", "solution": "Начни действовать по-другому"},
    "CAPABILITIES": {"name": "СПОСОБНОСТИ", "code": "cap", "description": "Проблема в навыках", "solution": "Освой новые навыки"},
    "VALUES": {"name": "ЦЕННОСТИ", "code": "val", "description": "Проблема в мотивации", "solution": "Найди свои истинные ценности"},
    "IDENTITY": {"name": "ИДЕНТИЧНОСТЬ", "code": "ide", "description": "Проблема в самоопределении", "solution": "Переопредели, кто ты"}
}

# ============================================
# АДАПТИВНЫЕ УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================

CLARIFICATION_QUESTIONS = {
    "stage1_external_internal": [
        {"id": "c1_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nПосле напряжённого дня что тебе нужнее?", "options": {"a": {"text": "Встретиться с людьми", "scores": {"EXTERNAL": 2}}, "b": {"text": "Побыть в одиночестве", "scores": {"INTERNAL": 2}}}},
        {"id": "c1_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда ты думаешь о выходных, что первое приходит в голову?", "options": {"a": {"text": "Куда пойти, с кем встретиться", "scores": {"EXTERNAL": 2}}, "b": {"text": "Чем заняться дома, о чём подумать", "scores": {"INTERNAL": 2}}}}
    ],
    "stage1_symbolic_material": [
        {"id": "c1_3", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЧто хуже: потерять деньги или потерять доверие близких?", "options": {"a": {"text": "Потерять доверие", "scores": {"SYMBOLIC": 2}}, "b": {"text": "Потерять деньги", "scores": {"MATERIAL": 2}}}},
        {"id": "c1_4", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда ты тревожишься, о чём чаще?", "options": {"a": {"text": "Что обо мне подумают, как меня воспримут", "scores": {"SYMBOLIC": 2}}, "b": {"text": "Хватит ли денег, успею ли, справлюсь ли", "scores": {"MATERIAL": 2}}}}
    ],
    "stage2_borderline": [
        {"id": "c2_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто ты чувствуешь, что застрял на месте?", "options": {"1": "Постоянно, не знаю как двигаться", "3": "Иногда, но нахожу выход", "4": "Редко, я в движении"}},
        {"id": "c2_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак ты относишься к своим прошлым ошибкам?", "options": {"1": "Стыжусь их, избегаю вспоминать", "3": "Анализирую и учусь", "4": "Принимаю как опыт"}}
    ],
    "stage3_discrepancy": [
        {"id": "c3_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nВспомни последний месяц. Сколько раз ты действовал не так, как хотел?", "options": {"1": "Постоянно", "2": "Часто (больше 5 раз)", "3": "Иногда (2-4 раза)", "5": "Редко (0-1 раз)"}},
        {"id": "c3_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак быстро ты замечаешь свои автоматические реакции?", "options": {"1": "Не замечаю, действую на автомате", "2": "Замечаю после", "4": "Замечаю в процессе", "5": "Замечаю до и могу изменить"}},
        {"id": "c3_3", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто ты делаешь то, что обещал себе?", "options": {"1": "Почти никогда", "2": "Иногда", "4": "Часто", "5": "Почти всегда"}}
    ],
    "stage4_tie": [
        {"id": "c4_1", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЕсли бы ты мог изменить только одно, что бы выбрал?", "options": {"a": {"text": "Где я нахожусь", "dilts": "ENVIRONMENT"}, "b": {"text": "Что я делаю", "dilts": "BEHAVIOR"}, "c": {"text": "Что я умею", "dilts": "CAPABILITIES"}, "d": {"text": "Что для меня важно", "dilts": "VALUES"}, "e": {"text": "Кто я", "dilts": "IDENTITY"}}},
        {"id": "c4_2", "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nГде находится твоя главная проблема?", "options": {"a": {"text": "В обстоятельствах", "dilts": "ENVIRONMENT"}, "b": {"text": "В моих действиях", "dilts": "BEHAVIOR"}, "c": {"text": "В моих навыках", "dilts": "CAPABILITIES"}, "d": {"text": "В моих целях", "dilts": "VALUES"}, "e": {"text": "В моём самоопределении", "dilts": "IDENTITY"}}}
    ]
}

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ИСПРАВЛЕННЫЕ)
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%\nПройдено: {current}/{total}"

def determine_perception_type(scores):
    """Определяет тип восприятия"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    focus = "EXTERNAL" if external >= internal else "INTERNAL"
    anxiety = "SYMBOLIC" if symbolic >= material else "MATERIAL"
    
    type_data = PERCEPTION_TYPES.get((focus, anxiety), PERCEPTION_TYPES[("EXTERNAL", "SYMBOLIC")])
    return type_data["name"]

def get_type_code(perception_type: str) -> str:
    """Код типа (SA/IA/SP/IP)"""
    type_map = {
        "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "SA",
        "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "IA",
        "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "SP",
        "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "IP"
    }
    return type_map.get(perception_type, "SA")

def get_level_name(level_num):
    """Получаем название уровня по номеру"""
    level_names = {
        1: "ДЕФИЦИТАРНЫЙ",
        2: "ПОИСКОВЫЙ", 
        3: "КОНСТРУКТИВНЫЙ",
        4: "КРИЗИСНЫЙ",
        5: "ИНТЕГРАТИВНЫЙ",
        6: "АЛЬТРУИСТИЧЕСКИЙ",
        7: "МУДРЕЦКИЙ",
        8: "СИСТЕМНЫЙ",
        9: "ТРАНСЦЕНДЕНТНЫЙ"
    }
    return level_names.get(level_num, f"Уровень {level_num}")

def get_dilts_code(dilts_level: str) -> str:
    """Код Дилтса"""
    dilts_map = {
        "ENVIRONMENT": "env",
        "BEHAVIOR": "beh",
        "CAPABILITIES": "cap",
        "VALUES": "val",
        "IDENTITY": "ide"
    }
    return dilts_map.get(dilts_level, "env")

def determine_dilts_level(dilts_answers):
    """Определяет уровень Дилтса"""
    if not dilts_answers:
        return "ENVIRONMENT"
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(1)[0]
    return most_common[0]

# ============================================
# ИСПРАВЛЕННАЯ СИСТЕМА РАСЧЕТА УРОВНЯ
# ============================================

def calculate_thinking_level_by_scores(level_scores_dict):
    """Определяет уровень мышления (1-9) по системе баллов"""
    if not level_scores_dict:
        return 1
    
    # Преобразуем ключи в числа для правильного сравнения
    numeric_scores = {int(k): v for k, v in level_scores_dict.items() if k.isdigit()}
    
    if not numeric_scores:
        return 1
    
    # Находим максимальный балл
    max_score = max(numeric_scores.values())
    
    # Находим ВСЕ уровни с максимальным баллом
    max_levels = [level for level, score in numeric_scores.items() if score == max_score]
    
    if not max_levels:
        return 1
    
    # Выбираем самый высокий уровень среди тех, у кого максимальный балл
    return max(max_levels)

def calculate_final_level(stage2_level, stage3_scores):
    """Финальный уровень (приоритет поведению)"""
    if not stage3_scores:
        return stage2_level
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    
    # 70% веса поведению (этап 3), 30% мышлению (этап 2)
    weighted = stage3_avg * 0.7 + stage2_level * 0.3
    
    # Правильное математическое округление
    final_level = int(round(weighted))
    
    logger.info(f"Final level: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}, weighted={weighted:.2f}, final={final_level}")
    return final_level

# ============================================
# ФУНКЦИЯ ОЧИСТКИ ДУБЛИРУЮЩИХСЯ ЗАГОЛОВКОВ
# ============================================

def clean_duplicate_headers(text: str, field_type: str) -> str:
    """
    Убирает заголовки, которые уже есть в тексте профиля.
    
    field_type: 'trigger', 'pain', 'immediate_tool', 'cta'
    Возвращает: текст без заголовка в первой строке
    """
    if not text:
        return ""
    
    lines = text.strip().split('\n')
    if not lines:
        return text
    
    # Какие заголовки удалять для каждого типа
    headers = {
        'trigger': ['ЭТО ТЫ, ЕСЛИ...', 'ЭТО ТЫ, ЕСЛИ:'],
        'pain': ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ: ПОЧЕМУ ЭТО ЛОМАЕТ ТВОЮ ЖИЗНЬ?'],
        'immediate_tool': ['ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:'],
        'cta': ['ЧТО ДАЛЬШЕ?', 'ДАЛЬШЕ:']
    }
    
    if field_type in headers and lines:
        first_line = lines[0].strip()
        for header in headers[field_type]:
            if header in first_line:
                # Удаляем эту строку
                lines.pop(0)
                # Убираем возможную пустую строку после заголовка
                if lines and not lines[0].strip():
                    lines.pop(0)
                break
    
    return '\n'.join(lines).strip()

# ============================================
# ФУНКЦИЯ ПОИСКА ПРОФИЛЯ С FALLBACK
# ============================================

def get_profile_fallback(profile_data: dict) -> VariaticaProfile:
    """
    Находит реально существующий файл профиля.
    
    Пример: Ищем ia_3_def → находим ia_3_con
    Возвращает: существующий профиль
    """
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    # Попробуем искомый профиль
    target_key = f"{type_code}_{level}_{dilts_code}"
    profile = loader.get_profile(target_key)
    
    if profile:
        logger.info(f"Profile found: {target_key}")
        return profile
    
    # Если не нашли, ищем альтернативные варианты
    logger.info(f"Profile {target_key} not found, searching alternatives...")
    
    # 1. Ищем с другим суффиксом Дилтса
    all_profiles = loader.get_all_profiles()
    possible_suffixes = ['def', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
    
    for suffix in possible_suffixes:
        if suffix == dilts_code:
            continue
        alt_key = f"{type_code}_{level}_{suffix}"
        if alt_key in all_profiles:
            logger.info(f"Found alternative: {alt_key}")
            profile = loader.get_profile(alt_key)
            if profile:
                return profile
    
    # 2. Ищем ближайший уровень
    best_match = None
    best_diff = float('inf')
    
    for key in all_profiles:
        if key.startswith(f"{type_code}_"):
            try:
                parts = key.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    key_level = int(parts[1])
                    diff = abs(key_level - level)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = key
            except:
                continue
    
    if best_match:
        logger.info(f"Using level fallback: {best_match}")
        return loader.get_profile(best_match)
    
    # 3. Аварийный fallback
    logger.warning(f"No profile found for {target_key}, using sa_1_def")
    return loader.get_profile("sa_1_def")

# ============================================
# ФУНКЦИЯ ПОЛУЧЕНИЯ ОПИСАНИЯ ПРОФИЛЯ
# ============================================

def get_card_description_from_profile(profile: VariaticaProfile, profile_data: dict) -> dict:
    """Получает описание профиля с очисткой заголовков"""
    is_new_format = hasattr(profile, 'archetype') and profile.archetype
    
    if is_new_format:
        # Очищаем каждое поле от дублирующихся заголовков
        clean_trigger = clean_duplicate_headers(profile.trigger, 'trigger')
        clean_pain = clean_duplicate_headers(profile.pain, 'pain')
        clean_tool = clean_duplicate_headers(profile.immediate_tool, 'immediate_tool')
        clean_cta = clean_duplicate_headers(profile.cta, 'cta')
        
        return {
            # Основные поля профиля (очищенные от заголовков)
            "title": profile.title,
            "archetype": profile.archetype,
            "quote": profile.quote,
            "trigger": clean_trigger,
            "pain": clean_pain,
            "immediate_tool": clean_tool,
            "cta": clean_cta,
            
            # Метаданные
            "type_code": profile_data['type_code'],
            "level": profile_data['level'],
            "dilts_code": profile_data['dilts_code'],
        }
    else:
        # Для старого формата
        return {
            "title": profile.title if hasattr(profile, 'title') else f"{profile_data['type_code']} Профиль",
            "profile_name": profile.profile_name if hasattr(profile, 'profile_name') else f"{profile_data['type_code']} Уровень {profile_data['level']}",
            "thinking_level": profile.thinking_level if hasattr(profile, 'thinking_level') else profile_data['level'],
            "dilts_level": profile.dilts_level if hasattr(profile, 'dilts_level') else profile_data['dilts_level'],
            "pain": profile.pain if hasattr(profile, 'pain') else "",
            "world": profile.world if hasattr(profile, 'world') else "",
            "superpower": profile.superpower if hasattr(profile, 'superpower') else "",
            "growth": profile.growth if hasattr(profile, 'growth') else f"Точка роста на уровне {profile_data['level']}",
            "cta": profile.cta if hasattr(profile, 'cta') else ""
        }

# ============================================
# ФУНКЦИЯ РАСЧЕТА ПРОФИЛЯ
# ============================================

def calculate_profile_final(context_data: dict) -> dict:
    """
    ФИНАЛЬНЫЙ алгоритм расчета профиля
    """
    # 1. Определяем тип из этапа 1
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    # 2. Определяем уровень из этапа 2 (система баллов)
    level_scores_dict = context_data.get("stage2_level_scores_dict", {})
    stage2_level = calculate_thinking_level_by_scores(level_scores_dict)
    
    # 3. Корректируем по этапу 3
    stage3_scores = context_data.get("stage3_level_scores", [])
    final_level = calculate_final_level(stage2_level, stage3_scores)
    
    # 4. Ограничиваем диапазон 1-9
    final_level = max(1, min(9, final_level))
    
    # 5. Уровень Дилтса
    dilts_answers = context_data.get("stage4_dilts_answers", [])
    dilts_level = determine_dilts_level(dilts_answers)
    dilts_code = get_dilts_code(dilts_level)
    
    # 6. Проверка согласованности
    coherence = check_profile_coherence(final_level, dilts_level)
    
    logger.info(f" FINAL PROFILE CALCULATION:")
    logger.info(f"   Type: {type_code} ({perception_type})")
    logger.info(f"   Level: {final_level} ({get_level_name(final_level)})")
    logger.info(f"   Dilts: {dilts_level} ({dilts_code})")
    logger.info(f"   Coherence: {coherence['is_coherent']}")
    
    return {
        # Метаданные профиля
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code,
        
        # Для отображения
        "display_name": f"{type_code}_{final_level}_{dilts_code}",
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        
        # Проверка
        "coherence": coherence,
        "stage2_level": stage2_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
    }

def check_profile_coherence(profile_level: int, dilts_level: str) -> dict:
    """
    Проверяет согласованность уровня профиля и уровня Дилтса
    """
    # Маппинг: какие уровни Дилтса ожидаются для каждого уровня профиля
    expected_dilts_by_level = {
        1: ["ENVIRONMENT", "BEHAVIOR"],
        2: ["BEHAVIOR", "CAPABILITIES"],
        3: ["CAPABILITIES", "VALUES"],
        4: ["VALUES", "IDENTITY"],
        5: ["VALUES", "IDENTITY"],
        6: ["IDENTITY", "VALUES"],
        7: ["IDENTITY"],
        8: ["IDENTITY"],
        9: ["IDENTITY"]
    }
    
    expected_dilts = expected_dilts_by_level.get(profile_level, ["VALUES"])
    is_coherent = dilts_level in expected_dilts
    
    result = {
        "is_coherent": is_coherent,
        "profile_level": profile_level,
        "dilts_level": dilts_level,
        "expected_dilts": expected_dilts
    }
    
    return result

# ============================================
# ПРОВЕРКИ УТОЧНЕНИЙ
# ============================================

def need_clarification_stage1(scores):
    """Нужны ли уточнения после ЭТАПА 1"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    clarifications = []
    if abs(external - internal) <= 2:
        clarifications.append("external_internal")
    if abs(symbolic - material) <= 2:
        clarifications.append("symbolic_material")
    
    return clarifications

def need_clarification_stage2(level_scores_dict):
    """Нужны ли уточнения после ЭТАПА 2"""
    if not level_scores_dict:
        return False
    
    # Находим два уровня с максимальными баллами
    sorted_levels = sorted(level_scores_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_levels) >= 2:
        # Если разница между первым и вторым меньше 3 баллов → нужны уточнения
        first_score = sorted_levels[0][1]
        second_score = sorted_levels[1][1]
        
        if abs(first_score - second_score) < 3:
            logger.info(f"Stage2 needs clarification: {sorted_levels[0]} vs {sorted_levels[1]}")
            return True
    
    return False

def need_clarification_stage3(stage2_level, stage3_scores):
    """Нужны ли уточнения после ЭТАПА 3"""
    if not stage3_scores:
        return False
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    return abs(stage2_level - stage3_avg) > 2

def need_clarification_stage4(dilts_answers):
    """Нужны ли уточнения после ЭТАПА 4"""
    if not dilts_answers:
        return False
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(2)
    if len(most_common) >= 2:
        return most_common[0][1] == most_common[1][1]
    return False

# ============================================
# ИСПРАВЛЕННЫЙ ЭКРАН РЕЗУЛЬТАТОВ
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА - исправленная версия с 3 сообщениями"""
    query = update.callback_query
    
    # Проверяем, поделился ли уже пользователь
    has_shared = context.user_data.get("has_shared", False)
    
    # Получаем данные профиля
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        # Если тест только что завершился, вычисляем профиль
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    # Загружаем профиль с fallback
    profile = get_profile_fallback(profile_data)
    
    if not profile:
        error_text = (
            f"❌ <b>ОШИБКА</b>\n\n"
            f"Не удалось найти профиль.\n\n"
            f"Попробуй пройти тест заново: /start"
        )
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    # Создаем описание карточки (очищенное от заголовков)
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    # ====================================================
    # СООБЩЕНИЕ 1: Заголовок + Архетип + Цитата
    # ====================================================
    
    message_1 = ""
    
    # Заголовок профиля в одну строку
    profile_header = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    
    # Используем title или профильное имя
    profile_title = profile_card.get('title', f"ПРОФИЛЬ {profile_data['level']}")
    
    # Добавляем эмодзи в начало, если его нет
    if not profile_title.startswith(('🎯', '🔍', '💔', '🛠', '🚀')):
        profile_title = f"🎯 {profile_title}"
    
    message_1 += f"<b>{profile_title}</b>\n"
    message_1 += f"<code>{profile_header}</code>\n\n"
    
    # Архетип (если есть)
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    # Цитата
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}"
    
    # Отправляем сообщение 1
    if message_1.strip():
        await query.edit_message_text(message_1.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    # ====================================================
    # СООБЩЕНИЕ 2: "Это ты, если..."
    # ====================================================
    
    message_2 = ""
    
    # Это ты, если...
    trigger = profile_card.get('trigger', '')
    if trigger:
        # Убедимся, что нет дублирующего заголовка
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_2 += f"<b>🔍 ЭТО ТЫ, ЕСЛИ...</b>\n\n"
        message_2 += f"{trigger}"
    
    # Отправляем сообщение 2
    if message_2.strip():
        await query.message.reply_text(message_2.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    # ====================================================
    # СООБЩЕНИЕ 3: "Суть проблемы" + "Инструмент прямо сейчас" + "Что дальше?"
    # ====================================================
    
    message_3 = ""
    
    # Суть проблемы
    pain = profile_card.get('pain', '')
    if pain:
        # Убедимся, что нет дублирующего заголовка
        pain_lines = pain.strip().split('\n')
        if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
            pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
        
        if pain.strip():
            message_3 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
            message_3 += f"{pain.strip()}\n\n"
    
    # Инструмент прямо сейчас
    tool = profile_card.get('immediate_tool', '')
    if tool:
        # Убедимся, что нет дублирующего заголовка
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            if message_3:  # Добавляем разделитель, если уже есть текст
                message_3 += "\n"
            message_3 += f"<b>🛠 ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»</b>\n\n"
            message_3 += f"{tool.strip()}\n\n"
    
    # Что дальше?
    cta = profile_card.get('cta', '')
    if cta:
        # Убедимся, что нет дублирующего заголовка
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_3 += f"<b>🚀 ЧТО ДАЛЬШЕ?</b>\n\n"
            message_3 += f"{cta.strip()}\n\n"
    
    # Примечание о несогласованности (если есть)
    coherence = profile_data.get("coherence", {})
    if not coherence.get("is_coherent", True):
        discrepancy_note = (
            f"🔍 <b>ПРИМЕЧАНИЕ:</b>\n"
            f"Есть небольшое расхождение в результатах.\n"
            f"Уровень развития: {profile_data['level_name']}, "
            f"но фокус проблем: {DILTS_LEVELS[profile_data['dilts_level']]['name']}.\n"
            f"Это может указывать на переходный период.\n\n"
        )
        message_3 += discrepancy_note
    
    # Инструкция по подарку
    if not has_shared:
        instruction = (
            f"📄 <b>ПОЛУЧИ ПОЛНЫЙ ПРОФИЛЬ + РЕКОМЕНДАЦИИ</b>\n\n"
            f"💬 Иногда самое большое, что мы можем сделать для близких — это дать зеркало...\n"
            f"Поделись тестом и получи\n"
            f"🎁 <b>БЕСПЛАТНЫЙ ПОДАРОК</b>"
        )
    else:
        instruction = (
            f"🎉 <b>ВАШ ПОДАРОК ГОТОВ!</b>\n"
            f"Спасибо за репост!"
        )
    
    message_3 += f"\n{instruction}"
    
    # Определяем кнопки
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("🎁 Получить подарок", callback_data="get_gift")],
            [InlineKeyboardButton("💎 Подробнее о пакете", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Забрать подарок", callback_data="open_gift")],
            [InlineKeyboardButton("💎 Подробнее о пакете", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение 3 с кнопками
    await query.message.reply_text(message_3.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS

# ============================================
# ОСТАЛЬНЫЕ ЭКРАНЫ (без изменений)
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ИНСТРУКЦИЯ ПО ШАРИНГУ"""
    query = update.callback_query
    await query.answer()
    
    instruction_text = (
        f"📤 <b>ШАГ 1: ПОДЕЛИСЬ ТЕСТОМ</b>\n\n"
        f"Нажми кнопку ниже, чтобы поделиться ссылкой в Telegram.\n\n"
        f"После того как поделишься, вернись сюда и нажми «✅ Я поделился»"
    )
    
    encoded_text = urllib.parse.quote(SHARE_TEXT)
    share_url = f"https://t.me/share/url?url={BOT_LINK}&text={encoded_text}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Поделиться ссылкой", url=share_url)],
        [InlineKeyboardButton("✅ Я поделился", callback_data="confirm_share")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(instruction_text, reply_markup=reply_markup, parse_mode="HTML")
    return GIFT_SCREEN

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    await query.answer("✅ Спасибо за репост! Ваш подарок готов!")
    
    context.user_data["has_shared"] = True
    
    return await show_results_screen(update, context)

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНЫЙ ПАКЕТ"""
    query = update.callback_query
    await query.answer()
    
    package_text = (
        f"💎 <b>ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
        f"<b>Что входит:</b>\n"
        f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
        f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
        f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
        f"• Персональные рекомендации по развитию\n"
        f"• Карта сильных и слабых сторон\n\n"
        f"<b>Цена:</b> 690 ₽\n\n"
        f"После оплаты свяжись со мной для получения материалов:\n"
        f"👉 @meysternlp"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Купить", url=PAYMENT_LINK)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")],
        [InlineKeyboardButton("💬 Консультация", url=f"https://t.me/{AUTHOR_LINK[1:]}" if AUTHOR_LINK.startswith('@') else f"https://t.me/{AUTHOR_LINK}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(package_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ОТКРЫТИЕ ПОДАРКА"""
    query = update.callback_query
    await query.answer()
    
    gift_text = (
        f"🎁 <b>ВАШ ПОДАРОК ГОТОВ!</b>\n\n"
        f"📚 Терапевтическая сказка для трансформации структуры восприятия\n\n"
        f"Эта сказка разрешает внутренние противоречия в конфигурации восприятия вашего профиля.\n\n"
        f"💡 <b>Как использовать:</b>\n"
        f"1. Нажми кнопку ниже, чтобы открыть PDF\n"
        f"2. Прочитай\n"
        f"3. Обращай внимание на символы и метафоры\n\n"
        f"Приятного чтения! 📖✨"
    )
    
    keyboard = [
        [InlineKeyboardButton("📖 Открыть сказку", url=GIFT_PDF_LINK)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(gift_text, reply_markup=reply_markup, parse_mode="HTML")
    return OPEN_GIFT_SCREEN

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Назад' - возвращает к результатам"""
    query = update.callback_query
    await query.answer()
    return await show_results_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    return await start_test(update, context)

# ============================================
# ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (без изменений)
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест ВАРИАТИКА!</b>\n\n"
        f"🔍 <b>Узнай о себе то, что ты ещё не знаешь.</b>\n\n"
        f"<b>Этот тест поможет определить:</b>\n"
        f"• Как ты воспринимаешь реальность \n"
        f"• Каким способом обрабатываешь информацию \n"
        f"• Какие поведенческие паттерны у тебя есть \n"
        f"• Что не дает тебе расти 🚀\n\n"
        f"🎯 <b>Что тебя ждёт:</b>\n\n"
        f"1️⃣ <b>ЭТАП 1:</b> Конфигурация восприятия (8 вопросов)\n"
        f"2️⃣ <b>ЭТАП 2:</b> Конфигурация мышления (8 вопросов)\n"
        f"3️⃣ <b>ЭТАП 3:</b> Поведенческие паттерны (8 вопросов)\n"
        f"4️⃣ <b>ЭТАП 4:</b> Конфликт логических уровней (8 вопросов)\n\n"
        f"⏱ Займёт 10-15 минут\n\n"
        f"📌 Отвечай честно, как есть сейчас, а не как хотелось бы.\n\n"
        f"Готов начать? 🚀"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    logger.info(f"User {update.effective_user.id} started test")
    
    return await show_stage_1_intro(update, context)

async def show_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 1"""
    query = update.callback_query
    
    intro_text = (
        f"<b>🎯 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"Сейчас мы определим твой базовый тип восприятия реальности.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage1_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 1", callback_data="start_stage_1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def show_stage_1_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФИГУРАЦИЯ ВОСПРИЯТИЯ?</b>\n\n"
        f"Это базовая программа, через которую ты воспринимаешь мир.\n\n"
        f"<b>Мы измеряем две оси:</b>\n\n"
        f"<b>1. Направленность внимания:</b>\n"
        f"• ЭКСТЕРНАЛЬНАЯ — фокус на внешнем мире (люди, события)\n"
        f"• ИНТЕРНАЛЬНАЯ — фокус на внутреннем мире (мысли, чувства)\n\n"
        f"<b>2. Доминирующая тревога:</b>\n"
        f"• СИМВОЛИЧЕСКАЯ — страх отвержения, непонимания\n"
        f"• МАТЕРИАЛЬНАЯ — страх потери контроля, ресурсов\n\n"
        f"<b>Результат:</b> Один из четырёх типов восприятия\n\n"
        f"Это определит, какие вопросы ты получишь на следующих этапах."
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage1_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def back_to_stage1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 1"""
    return await show_stage_1_intro(update, context)

async def start_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage1_current"] = 0
    return await ask_stage_1_question(update, context)

async def ask_stage_1_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 1"""
    query = update.callback_query
    current = context.user_data.get("stage1_current", 0)
    
    if current >= len(STAGE_1_QUESTIONS):
        return await finish_stage_1(update, context)
    
    question = STAGE_1_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_1_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage1_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_1

async def handle_stage_1_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 1"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_1
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_1
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_1_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_1
        
        for axis, score in selected_option.get("scores", {}).items():
            context.user_data["scores"][axis] += score
        
        logger.info(f"User {update.effective_user.id}: Stage 1 Q{current} -> {option_id}")
        
        context.user_data["stage1_current"] = current + 1
        return await ask_stage_1_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАП 1"""
    query = update.callback_query
    scores = context.user_data.get("scores", {})
    
    clarifications_needed = need_clarification_stage1(scores)
    
    if clarifications_needed and not context.user_data.get("stage1_clarified", False):
        context.user_data["stage1_clarifications"] = clarifications_needed
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage1"
        
        logger.info(f"User {update.effective_user.id}: Stage 1 needs clarification")
        return await ask_clarification_question(update, context)
    
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация восприятия определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение конфигурации мышления.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def ask_clarification_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт уточняющий вопрос"""
    query = update.callback_query
    
    clarification_stage = context.user_data.get("clarification_stage")
    current = context.user_data.get("clarification_current", 0)
    
    if clarification_stage == "stage1":
        clarifications = context.user_data.get("stage1_clarifications", [])
        if current >= len(clarifications):
            context.user_data["stage1_clarified"] = True
            return await finish_stage_1(update, context)
        
        clarification_type = clarifications[current]
        questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
        
        if not questions:
            context.user_data["clarification_current"] = current + 1
            return await ask_clarification_question(update, context)
        
        question = questions[0]
        
    elif clarification_stage == "stage2":
        questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
        if current >= len(questions):
            context.user_data["stage2_clarified"] = True
            return await finish_stage_2(update, context)
        question = questions[current]
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current >= len(questions):
            context.user_data["stage3_clarified"] = True
            return await finish_stage_3(update, context)
        question = questions[current]
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        if current >= len(questions):
            context.user_data["stage4_clarified"] = True
            return await finish_stage_4(update, context)
        question = questions[current]
    else:
        return STAGE_1
    
    if not question:
        return STAGE_1
    
    question_text = question["text"]
    
    keyboard = []
    if clarification_stage in ["stage1", "stage4"]:
        for option_id, option in question["options"].items():
            keyboard.append([
                InlineKeyboardButton(
                    option["text"], 
                    callback_data=f"clarify_{clarification_stage}_{current}_{option_id}"
                )
            ])
    else:
        for level, answer_text in question["options"].items():
            keyboard.append([
                InlineKeyboardButton(
                    answer_text, 
                    callback_data=f"clarify_{clarification_stage}_{current}_{level}"
                )
            ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return CLARIFICATION

async def handle_clarification_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на уточняющий вопрос"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    if len(parts) < 4:
        return CLARIFICATION
    
    clarification_stage = parts[1]
    current = int(parts[2])
    option_id = parts[3]
    
    if clarification_stage == "stage1":
        clarifications = context.user_data.get("stage1_clarifications", [])
        if current < len(clarifications):
            clarification_type = clarifications[current]
            questions = CLARIFICATION_QUESTIONS.get(f"stage1_{clarification_type}", [])
            if questions:
                question = questions[0]
                selected_option = question["options"].get(option_id)
                if selected_option:
                    for axis, score in selected_option.get("scores", {}).items():
                        context.user_data["scores"][axis] += score
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage2":
        questions = CLARIFICATION_QUESTIONS.get("stage2_borderline", [])
        if current < len(questions):
            question = questions[current]
            selected_level = option_id
            
            if "stage2_level_scores_dict" not in context.user_data:
                context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
            
            if selected_level in context.user_data["stage2_level_scores_dict"]:
                context.user_data["stage2_level_scores_dict"][selected_level] += 3
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current < len(questions):
            question = questions[current]
            selected_level = option_id
            
            if "stage3_level_scores" not in context.user_data:
                context.user_data["stage3_level_scores"] = []
            
            context.user_data["stage3_level_scores"].append(int(selected_level))
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage4":
        questions = CLARIFICATION_QUESTIONS.get("stage4_tie", [])
        if current < len(questions):
            question = questions[current]
            selected_option = question["options"].get(option_id)
            if selected_option:
                dilts = selected_option.get("dilts", "ENVIRONMENT")
                context.user_data["stage4_dilts_answers"].append(dilts)
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
    
    return CLARIFICATION

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Сейчас мы определим твой тип мышления.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~4 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage2_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 2", callback_data="start_stage_2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def show_stage_2_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФИГУРАЦИЯ МЫШЛЕНИЯ?</b>\n\n"
        f"Это тип твоего мышления внутри системы восприятия.\n\n"
        f"<b>9 типов конфигураций мышления:</b>\n\n"
        f"1️⃣ ДЕФИЦИТАРНЫЙ — базовая нужда не удовлетворена\n"
        f"2️⃣ ПОИСКОВЫЙ — активный поиск решения\n"
        f"3️⃣ КОНСТРУКТИВНЫЙ — создание стабильной базы\n"
        f"4️⃣ КРИЗИСНЫЙ — переосмысление достигнутого\n"
        f"5️⃣ ИНТЕГРАТИВНЫЙ — уверенное владение\n"
        f"6️⃣ АЛЬТРУИСТИЧЕСКИЙ — служение другим\n"
        f"7️⃣ МУДРЕЦКИЙ — глубокое понимание\n"
        f"8️⃣ СИСТЕМНЫЙ — управление на системном уровне\n"
        f"9️⃣ ТРАНСЦЕНДЕНТНЫЙ — выход за пределы\n\n"
        f"<b>Результат:</b> Твой текущий способ обработки информации"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def back_to_stage2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 2"""
    return await show_stage_2_intro(update, context)

async def start_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 2"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage2_current"] = 0
    return await ask_stage_2_question(update, context)

async def ask_stage_2_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 2"""
    query = update.callback_query
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    current = context.user_data.get("stage2_current", 0)
    
    questions = STAGE_2_QUESTIONS.get(perception_type, STAGE_2_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
    
    if current >= len(questions):
        return await finish_stage_2(update, context)
    
    question = questions[current]
    progress = calculate_progress(current + 1, len(questions))
    
    question_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for level_num, answer_text in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                answer_text, 
                callback_data=f"stage2_{current}_{level_num}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

async def handle_stage_2_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 2"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_2
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_2
        
        current = int(parts[1])
        selected_level = parts[2]
        
        perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
        
        scoring_table = STAGE_2_SCORING.get(perception_type, {})
        if current in scoring_table and selected_level in scoring_table[current]:
            if "stage2_level_scores_dict" not in context.user_data:
                context.user_data["stage2_level_scores_dict"] = {
                    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0,
                    "6": 0, "7": 0, "8": 0, "9": 0
                }
            
            points = scoring_table[current][selected_level]
            context.user_data["stage2_level_scores_dict"][selected_level] += points
            
            logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> level={selected_level} (+{points} points)")
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2"""
    query = update.callback_query
    level_scores_dict = context.user_data.get("stage2_level_scores_dict", {"1": 0})
    
    needs_clarification = need_clarification_stage2(level_scores_dict)
    
    if needs_clarification and not context.user_data.get("stage2_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage2"
        
        logger.info(f"User {update.effective_user.id}: Stage 2 needs clarification")
        return await ask_clarification_question(update, context)
    
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    context.user_data["thinking_level"] = thinking_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация мышления определена\n"
        f"📊 Уровень: <b>{get_level_name(thinking_level)} ({thinking_level}/9)</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"Сейчас мы уточним твои паттерны через анализ автоматических реакций.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Готов начать?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage3_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 3", callback_data="start_stage_3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def show_stage_3_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ?</b>\n\n"
        f"Это автоматические реакции — то, что ты делаешь не задумываясь.\n\n"
        f"<b>Зачем это нужно:</b>\n\n"
        f"Ты можешь думать одно, а делать другое.\n\n"
        f"Твоё реальное поведение точнее показывает глубинные установки, чем твои представления о себе.\n\n"
        f"Мы зададим вопросы о конкретных действиях, чтобы уточнить твои паттерны.\n\n"
        f"<b>Результат:</b> Подтверждение или корректировка типа из ЭТАПА 2"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def back_to_stage3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 3"""
    return await show_stage_3_intro(update, context)

async def start_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 3"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage3_current"] = 0
    return await ask_stage_3_question(update, context)

async def ask_stage_3_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 3"""
    query = update.callback_query
    current = context.user_data.get("stage3_current", 0)
    
    if current >= len(STAGE_3_QUESTIONS):
        return await finish_stage_3(update, context)
    
    question = STAGE_3_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_3_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage3_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

async def handle_stage_3_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 3"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_3
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_3
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_3_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_3
        
        level = selected_option.get("level", 1)
        context.user_data["stage3_level_scores"].append(level)
        
        logger.info(f"User {update.effective_user.id}: Stage 3 Q{current} -> {option_id} (level={level})")
        
        context.user_data["stage3_current"] = current + 1
        return await ask_stage_3_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3"""
    query = update.callback_query
    
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    
    needs_clarification = need_clarification_stage3(stage2_level, stage3_scores)
    
    if needs_clarification and not context.user_data.get("stage3_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage3"
        
        logger.info(f"User {update.effective_user.id}: Stage 3 needs clarification")
        return await ask_clarification_question(update, context)
    
    final_level = calculate_final_level(stage2_level, stage3_scores)
    context.user_data["final_level"] = final_level
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, final_level={final_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 3 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Поведенческие паттерны проанализированы\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 4</b>: конфликт логических уровней.\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def show_stage_4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 4"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"Сейчас мы определим, на каком уровне находится твоя точка роста.\n\n"
        f"📊 <b>Вопросов:</b> 8\n"
        f"⏱ <b>Время:</b> ~3 минуты\n\n"
        f"Это последний этап! Готов?"
    )
    
    keyboard = [
        [InlineKeyboardButton("ℹ️ Детали", callback_data="stage4_details")],
        [InlineKeyboardButton("▶️ Начать ЭТАП 4", callback_data="start_stage_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(intro_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def show_stage_4_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Детали ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    details_text = (
        f"<b>📖 ЧТО ТАКОЕ КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ?</b>\n\n"
        f"Это модель Роберта Дилтса, которая показывает, на каком уровне находится проблема.\n\n"
        f"<b>5 уровней (снизу вверх):</b>\n\n"
        f"1️⃣ ОКРУЖЕНИЕ — внешние условия\n"
        f"2️⃣ ПОВЕДЕНИЕ — твои действия\n"
        f"3️⃣ СПОСОБНОСТИ — твои навыки\n"
        f"4️⃣ ЦЕННОСТИ — твои мотивы\n"
        f"5️⃣ ИДЕНТИЧНОСТЬ — кто ты\n\n"
        f"<b>Принцип:</b> Проблема на нижнем уровне решается на верхнем.\n\n"
        f"<b>Результат:</b> Твоя точка роста"
    )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_stage4_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(details_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def back_to_stage4_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к экрану ЭТАПА 4"""
    return await show_stage_4_intro(update, context)

async def start_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ЭТАПА 4"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["stage4_current"] = 0
    return await ask_stage_4_question(update, context)

async def ask_stage_4_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Задаёт вопрос ЭТАПА 4"""
    query = update.callback_query
    current = context.user_data.get("stage4_current", 0)
    
    if current >= len(STAGE_4_QUESTIONS):
        return await finish_stage_4(update, context)
    
    question = STAGE_4_QUESTIONS[current]
    progress = calculate_progress(current + 1, len(STAGE_4_QUESTIONS))
    
    question_text = (
        f"<b>🎯 ЭТАП 4: КОНФИГУРАЦИЯ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
        f"<b>{question['text']}</b>\n\n"
        f"{progress}"
    )
    
    keyboard = []
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage4_{current}_{option_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_4

async def handle_stage_4_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа ЭТАПА 4"""
    query = update.callback_query
    
    if context.user_data.get("processing", False):
        await query.answer("⏳ Обрабатываю предыдущий ответ...")
        return STAGE_4
    
    context.user_data["processing"] = True
    
    try:
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            return STAGE_4
        
        current = int(parts[1])
        option_id = parts[2]
        
        question = STAGE_4_QUESTIONS[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_4
        
        dilts = selected_option.get("dilts", "ENVIRONMENT")
        context.user_data["stage4_dilts_answers"].append(dilts)
        
        logger.info(f"User {update.effective_user.id}: Stage 4 Q{current} -> {option_id} (dilts={dilts})")
        
        context.user_data["stage4_current"] = current + 1
        return await ask_stage_4_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def ask_intelligent_clarification(update: Update, context: ContextTypes.DEFAULT_TYPE, profile_data: dict, coherence: dict):
    """Задаёт интеллектуальный уточняющий вопрос на основе Дилтса"""
    query = update.callback_query
    
    profile_level = profile_data["level"]
    current_dilts = profile_data["dilts_level"]
    
    if profile_level <= 3 and current_dilts == "IDENTITY":
        question = (
            f"🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\n"
            f"Ты указал, что твоя главная проблема - в самоопределении (кто ты).\n\n"
            f"Но в остальных ответах ты показываешь уровень начинающего.\n\n"
            f"<b>Что точнее описывает твою ситуацию?</b>"
        )
        options = {
            "a": "Мне сложно с окружающими условиями (место, люди, обстоятельства)",
            "b": "Я не знаю, как действовать в ситуациях",
            "c": "Я действительно переосмысливаю, кто я есть"
        }
        
    elif profile_level >= 7 and current_dilts == "ENVIRONMENT":
        question = (
            f"🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\n"
            f"По твоим ответам у тебя продвинутый уровень развития.\n\n"
            f"Но ты указываешь, что проблема в основном в окружении.\n\n"
            f"<b>Что на самом деле главное?</b>"
        )
        options = {
            "a": "Да, проблема именно в условиях (нужно сменить окружение)",
            "b": "Проблема в моих внутренних ценностях и понимании",
            "c": "Я переосмысливаю свою идентичность"
        }
    
    else:
        question = (
            f"🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\n"
            f"Чтобы уточнить результат, ответь:\n\n"
            f"<b>Где находится корень твоих главных трудностей?</b>"
        )
        options = {
            "a": "В обстоятельствах и окружении",
            "b": "В моих действиях и привычках", 
            "c": "В навыках и способностях",
            "d": "В целях и ценностях",
            "e": "В самоопределении (кто я)"
        }
    
    context.user_data["dilts_clarification_data"] = {
        "profile_data": profile_data,
        "coherence": coherence
    }
    
    keyboard = []
    for opt_id, opt_text in options.items():
        keyboard.append([InlineKeyboardButton(opt_text, callback_data=f"dilts_clarify_{opt_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(question, reply_markup=reply_markup, parse_mode="HTML")
    
    return DILTS_CLARIFICATION

async def handle_dilts_clarification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа на уточняющий вопрос по Дилтсу"""
    query = update.callback_query
    await query.answer()
    
    option_id = query.data.split("_")[-1]
    
    answer_to_dilts = {
        "a": "ENVIRONMENT",
        "b": "BEHAVIOR", 
        "c": "CAPABILITIES",
        "d": "VALUES",
        "e": "IDENTITY"
    }
    
    refined_dilts = answer_to_dilts.get(option_id, "VALUES")
    
    clarification_data = context.user_data.get("dilts_clarification_data", {})
    profile_data = clarification_data.get("profile_data", {})
    
    context.user_data["stage4_dilts_answers"].append(refined_dilts)
    context.user_data["refined_dilts"] = refined_dilts
    
    logger.info(f"User clarified dilts: {option_id} → {refined_dilts}")
    
    profile_data["dilts_level"] = refined_dilts
    profile_data["dilts_code"] = get_dilts_code(refined_dilts)
    profile_data["display_name"] = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    
    profile_data["coherence"] = check_profile_coherence(profile_data["level"], refined_dilts)
    
    context.user_data["profile_data"] = profile_data
    
    return await proceed_to_final_results(update, context)

async def proceed_to_final_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переход к финальным результатам"""
    query = update.callback_query
    
    loading_text = (
        f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\n"
        f"Анализирую твои ответы и определяю профиль..."
    )
    await query.edit_message_text(loading_text, parse_mode="HTML")
    
    await asyncio.sleep(2)
    
    return await show_results_screen(update, context)

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 с интеллектуальной проверкой"""
    query = update.callback_query
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    
    needs_clarification = need_clarification_stage4(dilts_answers)
    
    if needs_clarification and not context.user_data.get("stage4_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage4"
        
        logger.info(f"User {update.effective_user.id}: Stage 4 needs clarification (tie)")
        return await ask_clarification_question(update, context)
    
    profile_data = calculate_profile_final(context.user_data)
    
    coherence = profile_data["coherence"]
    
    context.user_data["profile_data"] = profile_data
    
    if not coherence["is_coherent"] and coherence.get("discrepancy_level", 0) >= 2:
        logger.info(f"Major discrepancy ({coherence.get('discrepancy_level', 0)}) → asking clarification")
        return await ask_intelligent_clarification(update, context, profile_data, coherence)
    else:
        if not coherence["is_coherent"]:
            logger.info(f"Minor discrepancy ({coherence.get('discrepancy_level', 0)}) → showing with note")
        
        return await proceed_to_final_results(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

def check_profiles_on_startup():
    """Проверяет наличие профилей через loader"""
    logger.info("🔍 Checking profile data via loader...")
    
    all_profiles = loader.get_all_profiles()
    actual_count = len(all_profiles)
    
    logger.info(f" Loaded {actual_count} profiles from filesystem via loader")
    
    new_format_count = 0
    old_format_count = 0
    
    for profile_key in all_profiles:
        profile = loader.get_profile(profile_key)
        if profile:
            if hasattr(profile, 'archetype') and profile.archetype:
                new_format_count += 1
            else:
                old_format_count += 1
    
    logger.info(f"📊 Format breakdown: {new_format_count} new format, {old_format_count} old format")
    
    types = ['sa', 'ia', 'sp', 'ip']
    for type_code in types:
        type_profiles = [k for k in all_profiles if k.startswith(type_code)]
        logger.info(f"  {type_code}: {len(type_profiles)} profiles")
    
    if actual_count < 36:
        logger.warning(f"⚠️ Expected 36 profiles, found {actual_count}")
        return False
    
    logger.info(" Profile loading OK")
    return True

def debug_loader():
    """Отладочная информация о загрузчике профилей"""
    print("🔍 Проверка загрузчика профилей...")
    
    try:
        all_profiles = loader.get_all_profiles()
        print(f"📊 Загружено профилей: {len(all_profiles)}")
        
        if not all_profiles:
            print("❌ ПРЕДУПРЕЖДЕНИЕ: Нет загруженных профилей!")
            return
        
        new_format_count = 0
        old_format_count = 0
        
        for profile_key in all_profiles[:5]:
            profile = loader.get_profile(profile_key)
            if profile:
                if hasattr(profile, 'archetype') and profile.archetype:
                    new_format_count += 1
                else:
                    old_format_count += 1
        
        print(f"📝 Форматы: {new_format_count} новый, {old_format_count} старый")
        
        types = ['sa', 'ia', 'sp', 'ip']
        for type_code in types:
            type_profiles = [k for k in all_profiles if k.startswith(type_code)]
            if type_profiles:
                print(f"  {type_code.upper()}: {len(type_profiles)} профилей")
        
        print("\n📈 Распределение по уровням:")
        for type_code in types:
            type_profiles = [k for k in all_profiles if k.startswith(type_code)]
            if type_profiles:
                levels = []
                for profile_key in type_profiles:
                    try:
                        parts = profile_key.split('_')
                        if len(parts) >= 2 and parts[1].isdigit():
                            levels.append(int(parts[1]))
                    except:
                        continue
                
                if levels:
                    levels_str = ", ".join(str(l) for l in sorted(set(levels)))
                    print(f"  {type_code.upper()}: уровни {levels_str}")
        
        test_profiles = ['sa_1_def', 'ia_3_con', 'sp_5_int', 'ip_9_ide']
        print("\n🔑 Проверка ключевых профилей:")
        for key in test_profiles:
            profile = loader.get_profile(key)
            if profile:
                format_type = "НОВЫЙ" if hasattr(profile, 'archetype') and profile.archetype else "старый"
                print(f"  ✅ {key}: Загружен ({format_type} формат)")
            else:
                print(f"  ❌ {key}: Отсутствует")
        
        print("\n📋 Сводка:")
        total_expected = 36
        if len(all_profiles) >= total_expected:
            print(f"✅ Все профили загружены ({len(all_profiles)}/{total_expected})")
        else:
            print(f"⚠️  Не хватает профилей: {len(all_profiles)}/{total_expected}")
            
    except Exception as e:
        print(f"❌ Ошибка при отладке загрузчика: {e}")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*50)
    print("🚀 ЗАПУСК БОТА (ИСПРАВЛЕННАЯ ВЕРСИЯ)")
    print("="*50)
    
    debug_loader()
    
    print("="*50 + "\n")
    
    check_profiles_on_startup()
    
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(show_stage_1_details, pattern="^stage1_details$"),
                CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$"),
                CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            STAGE_2: [
                CallbackQueryHandler(show_stage_2_intro, pattern="^show_stage_2_intro$"),
                CallbackQueryHandler(show_stage_2_details, pattern="^stage2_details$"),
                CallbackQueryHandler(back_to_stage2_intro, pattern="^back_to_stage2_intro$"),
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(show_stage_3_intro, pattern="^show_stage_3_intro$"),
                CallbackQueryHandler(show_stage_3_details, pattern="^stage3_details$"),
                CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$"),
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4: [
                CallbackQueryHandler(show_stage_4_intro, pattern="^show_stage_4_intro$"),
                CallbackQueryHandler(show_stage_4_details, pattern="^stage4_details$"),
                CallbackQueryHandler(back_to_stage4_intro, pattern="^back_to_stage4_intro$"),
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
            ],
            CLARIFICATION: [
                CallbackQueryHandler(handle_clarification_answer, pattern="^clarify_")
            ],
            DILTS_CLARIFICATION: [
                CallbackQueryHandler(handle_dilts_clarification, pattern="^dilts_clarify_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$")
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$")
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    logger.info("🚀 Bot started with FIXED PROFILE SYSTEM!")
    logger.info("📊 System: Fixed suffix mapping + Header cleaning + Beautiful formatting")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
