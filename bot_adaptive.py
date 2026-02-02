# bot_adaptive.py
"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа + адаптивные уточнения:
1. Конфигурация восприятия (8 вопросов) → 4 типа
2. Конфигурация мышления (8 вопросов, адаптивно) → 9 уровней
3. Конфигурация поведенческих паттернов (8 вопросов) → уточнение уровня
4. Конфликт логических уровней (8 вопросов) → 5 уровней Дилтса

ИТОГО: 36 профилей (4 типа × 9 уровней)
"""

import logging
import os
import asyncio
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
# ✅ ИСПРАВЛЕННЫЙ ИМПОРТ
# ============================================
from card_data import get_card_description, profile_exists, CARD_DATA

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

# Состояния ConversationHandler
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULT, SHARE_CONFIRM = range(7)

# ============================================
# КОНСТАНТЫ
# ============================================
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://drive.google.com/file/d/1Y0nr2C_sWlQVOF84THLXa3nflFBVSI77/view?usp=sharing"
AUTHOR_LINK = "@meysternlp"

# ============================================
# ДАННЫЕ ВОПРОСОВ (БЕЗ ИЗМЕНЕНИЙ)
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
        "description": "Фокус на внешних достижениях и результатах"
    },
    ("INTERNAL", "MATERIAL"): {
        "name": "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ",
        "code": "IP",
        "description": "Фокус на внутреннем порядке и системах понимания"
    }
}

# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
STAGE_2_QUESTIONS = {
    # ========================================
    # ТИП 1: СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ
    # ========================================
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": [
        {
            "id": "q2_1",
            "text": "Сколько у тебя близких людей?\n\n(С кем можно говорить о личном)",
            "options": {
                "a": {"text": "Нет таких", "level": 1},
                "b": {"text": "1-2 человека", "level": 2},
                "c": {"text": "3-5 человек", "level": 3},
                "d": {"text": "Больше 5", "level": 5}
            }
        },
        {
            "id": "q2_2",
            "text": "Как ты к этому относишься?",
            "options": {
                "a": {"text": "Мне не хватает близости", "level": 1},
                "b": {"text": "Я в процессе поиска своих людей", "level": 2},
                "c": {"text": "Меня это устраивает", "level": 3},
                "d": {"text": "Я не нуждаюсь в этом", "level": 4}
            }
        },
        {
            "id": "q2_3",
            "text": "Как часто за месяц ты отменяешь встречи с друзьями?",
            "options": {
                "a": {"text": "Не отменяю / нет встреч", "level": 1},
                "b": {"text": "1-2 раза", "level": 3},
                "c": {"text": "3-5 раз", "level": 2},
                "d": {"text": "Постоянно отменяю", "level": 1}
            }
        },
        {
            "id": "q2_4",
            "text": "Почему отменяешь?",
            "options": {
                "a": {"text": "Нет сил на людей", "level": 1},
                "b": {"text": "Эти люди не мои", "level": 2},
                "c": {"text": "Появились более важные дела", "level": 5},
                "d": {"text": "Не отменяю", "level": 3}
            }
        },
        {
            "id": "q2_5",
            "text": "Как часто ты чувствуешь, что тебя не понимают?",
            "options": {
                "a": {"text": "Постоянно", "level": 1},
                "b": {"text": "Часто", "level": 2},
                "c": {"text": "Иногда", "level": 4},
                "d": {"text": "Редко или никогда", "level": 3}
            }
        },
        {
            "id": "q2_6",
            "text": "Что ты с этим делаешь?",
            "options": {
                "a": {"text": "Пытаюсь объясниться", "level": 1},
                "b": {"text": "Ищу тех, кто поймёт", "level": 2},
                "c": {"text": "Принимаю это", "level": 4},
                "d": {"text": "Меня понимают", "level": 3}
            }
        },
        {
            "id": "q2_7",
            "text": "Твой друг постоянно меняет компании.\n\nКак думаешь, почему?",
            "options": {
                "a": {"text": "Ищет своих людей", "level": 2},
                "b": {"text": "Боится близости", "level": 1},
                "c": {"text": "Ему везде интересно", "level": 5},
                "d": {"text": "Не может быть собой", "level": 4}
            }
        },
        {
            "id": "q2_8",
            "text": "Что для тебя значит «найти своих людей»?",
            "options": {
                "a": {"text": "Место, где меня принимают", "level": 2},
                "b": {"text": "Люди, с которыми не нужно притворяться", "level": 3},
                "c": {"text": "Глубокая связь на уровне ценностей", "level": 5},
                "d": {"text": "Не думал об этом", "level": 1}
            }
        }
    ],
    
    # ========================================
    # ТИП 2: ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ
    # ========================================
    "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": [
        {
            "id": "q2_1",
            "text": "Как часто ты задаёшь себе вопрос «В чём смысл?»",
            "options": {
                "a": {"text": "Постоянно, это мучительно", "level": 1},
                "b": {"text": "Часто, ищу ответы", "level": 2},
                "c": {"text": "Иногда, это интересно", "level": 4},
                "d": {"text": "Редко, я знаю свой смысл", "level": 5}
            }
        },
        {
            "id": "q2_2",
            "text": "Что ты чувствуешь, когда остаёшься наедине с собой?",
            "options": {
                "a": {"text": "Тревогу, пустоту", "level": 1},
                "b": {"text": "Вопросы без ответов", "level": 2},
                "c": {"text": "Спокойствие, ясность", "level": 4},
                "d": {"text": "Глубину, полноту", "level": 5}
            }
        },
        {
            "id": "q2_3",
            "text": "Сколько времени в день ты проводишь в размышлениях?",
            "options": {
                "a": {"text": "Почти всё время (застреваю)", "level": 1},
                "b": {"text": "Несколько часов", "level": 2},
                "c": {"text": "1-2 часа осознанно", "level": 4},
                "d": {"text": "Мало, я живу в моменте", "level": 5}
            }
        },
        {
            "id": "q2_4",
            "text": "Что происходит после размышлений?",
            "options": {
                "a": {"text": "Ещё больше вопросов", "level": 1},
                "b": {"text": "Новые идеи, но нет действий", "level": 2},
                "c": {"text": "Понимание и действия", "level": 4},
                "d": {"text": "Трансформация опыта", "level": 5}
            }
        },
        {
            "id": "q2_5",
            "text": "Как ты относишься к своим переживаниям?",
            "options": {
                "a": {"text": "Боюсь их, избегаю", "level": 1},
                "b": {"text": "Анализирую, пытаюсь понять", "level": 2},
                "c": {"text": "Принимаю и наблюдаю", "level": 4},
                "d": {"text": "Использую как материал для роста", "level": 5}
            }
        },
        {
            "id": "q2_6",
            "text": "Что для тебя значит «быть собой»?",
            "options": {
                "a": {"text": "Не знаю, кто я", "level": 1},
                "b": {"text": "Ищу себя", "level": 2},
                "c": {"text": "Знаю и принимаю себя", "level": 4},
                "d": {"text": "Я — это процесс, а не статус", "level": 5}
            }
        },
        {
            "id": "q2_7",
            "text": "Человек погружён в экзистенциальный кризис.\n\nЧто ему делать?",
            "options": {
                "a": {"text": "Отвлечься, не думать об этом", "level": 1},
                "b": {"text": "Искать ответы (книги, терапия)", "level": 2},
                "c": {"text": "Прожить это как опыт", "level": 4},
                "d": {"text": "Это не кризис, а трансформация", "level": 5}
            }
        },
        {
            "id": "q2_8",
            "text": "Что для тебя глубина жизни?",
            "options": {
                "a": {"text": "Не понимаю, что это", "level": 1},
                "b": {"text": "Хочу её найти", "level": 2},
                "c": {"text": "Чувствую её в моменты", "level": 4},
                "d": {"text": "Живу в ней постоянно", "level": 5}
            }
        }
    ],
    
    # ========================================
    # ТИП 3: ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ
    # ========================================
    "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": [
        {
            "id": "q2_1",
            "text": "Сколько целей ты достиг за последний год?",
            "options": {
                "a": {"text": "Ни одной (только планировал)", "level": 1},
                "b": {"text": "1-2 цели", "level": 2},
                "c": {"text": "3-5 целей", "level": 4},
                "d": {"text": "Больше 5 целей", "level": 5}
            }
        },
        {
            "id": "q2_2",
            "text": "Как ты себя чувствуешь, когда достигаешь цели?",
            "options": {
                "a": {"text": "Пусто (а что дальше?)", "level": 1},
                "b": {"text": "Радость, но ненадолго", "level": 2},
                "c": {"text": "Удовлетворение", "level": 4},
                "d": {"text": "Уже думаю о следующей", "level": 5}
            }
        },
        {
            "id": "q2_3",
            "text": "Как часто ты откладываешь важные дела?",
            "options": {
                "a": {"text": "Постоянно (прокрастинация)", "level": 1},
                "b": {"text": "Часто", "level": 2},
                "c": {"text": "Иногда", "level": 4},
                "d": {"text": "Редко или никогда", "level": 5}
            }
        },
        {
            "id": "q2_4",
            "text": "Почему откладываешь?",
            "options": {
                "a": {"text": "Страх неудачи", "level": 1},
                "b": {"text": "Не знаю, с чего начать", "level": 2},
                "c": {"text": "Жду подходящего момента", "level": 4},
                "d": {"text": "Не откладываю", "level": 5}
            }
        },
        {
            "id": "q2_5",
            "text": "Что для тебя успех?",
            "options": {
                "a": {"text": "Не знаю, не достигал", "level": 1},
                "b": {"text": "Деньги, статус, признание", "level": 2},
                "c": {"text": "Реализация своих целей", "level": 4},
                "d": {"text": "Влияние и вклад в мир", "level": 5}
            }
        },
        {
            "id": "q2_6",
            "text": "Как ты относишься к конкуренции?",
            "options": {
                "a": {"text": "Избегаю её", "level": 1},
                "b": {"text": "Боюсь проиграть", "level": 2},
                "c": {"text": "Мотивирует меня", "level": 4},
                "d": {"text": "Играю свою игру", "level": 5}
            }
        },
        {
            "id": "q2_7",
            "text": "Человек хочет большего, но не действует.\n\nПочему?",
            "options": {
                "a": {"text": "Не верит в себя", "level": 1},
                "b": {"text": "Не знает, как", "level": 2},
                "c": {"text": "Ждёт готовности", "level": 4},
                "d": {"text": "На самом деле не хочет", "level": 5}
            }
        },
        {
            "id": "q2_8",
            "text": "Что важнее: процесс или результат?",
            "options": {
                "a": {"text": "Результат, но его нет", "level": 1},
                "b": {"text": "Результат любой ценой", "level": 2},
                "c": {"text": "Баланс процесса и результата", "level": 4},
                "d": {"text": "Процесс = результат", "level": 5}
            }
        }
    ],
    
    # ========================================
    # ТИП 4: СТРУКТУРНО-АНАЛИТИЧЕСКИЙ
    # ========================================
    "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": [
        {
            "id": "q2_1",
            "text": "Насколько упорядочена твоя жизнь?",
            "options": {
                "a": {"text": "Хаос, не могу навести порядок", "level": 1},
                "b": {"text": "Пытаюсь структурировать", "level": 2},
                "c": {"text": "Есть система, которая работает", "level": 4},
                "d": {"text": "Гибкая структура под задачи", "level": 5}
            }
        },
        {
            "id": "q2_2",
            "text": "Что происходит, когда нарушается твой порядок?",
            "options": {
                "a": {"text": "Паника, тревога", "level": 1},
                "b": {"text": "Раздражение, дискомфорт", "level": 2},
                "c": {"text": "Адаптируюсь", "level": 4},
                "d": {"text": "Это часть процесса", "level": 5}
            }
        },
        {
            "id": "q2_3",
            "text": "Как ты принимаешь решения?",
            "options": {
                "a": {"text": "Не могу выбрать (анализ-паралич)", "level": 1},
                "b": {"text": "Долго взвешиваю все варианты", "level": 2},
                "c": {"text": "Анализирую и выбираю оптимальное", "level": 4},
                "d": {"text": "Быстро, на основе критериев", "level": 5}
            }
        },
        {
            "id": "q2_4",
            "text": "Что для тебя понимание?",
            "options": {
                "a": {"text": "Не могу понять, как всё устроено", "level": 1},
                "b": {"text": "Ищу логику и закономерности", "level": 2},
                "c": {"text": "Вижу систему и связи", "level": 4},
                "d": {"text": "Создаю новые модели понимания", "level": 5}
            }
        },
        {
            "id": "q2_5",
            "text": "Как ты относишься к неопределённости?",
            "options": {
                "a": {"text": "Не выношу её", "level": 1},
                "b": {"text": "Пытаюсь всё просчитать", "level": 2},
                "c": {"text": "Принимаю как данность", "level": 4},
                "d": {"text": "Использую как ресурс", "level": 5}
            }
        },
        {
            "id": "q2_6",
            "text": "Сколько у тебя систем организации жизни?",
            "options": {
                "a": {"text": "Нет системы", "level": 1},
                "b": {"text": "Пробую разные, ничего не работает", "level": 2},
                "c": {"text": "Одна рабочая система", "level": 4},
                "d": {"text": "Несколько интегрированных систем", "level": 5}
            }
        },
        {
            "id": "q2_7",
            "text": "Человек перегружен информацией.\n\nЧто делать?",
            "options": {
                "a": {"text": "Избегать информации", "level": 1},
                "b": {"text": "Пытаться всё изучить", "level": 2},
                "c": {"text": "Фильтровать по критериям", "level": 4},
                "d": {"text": "Создать систему обработки", "level": 5}
            }
        },
        {
            "id": "q2_8",
            "text": "Что для тебя контроль?",
            "options": {
                "a": {"text": "Не могу контролировать жизнь", "level": 1},
                "b": {"text": "Пытаюсь всё контролировать", "level": 2},
                "c": {"text": "Контролирую важное", "level": 4},
                "d": {"text": "Контроль = осознанность", "level": 5}
            }
        }
    ]
}

# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
STAGE_3_QUESTIONS = [
    {
        "id": "q3_1",
        "text": "Вспомни последнюю неделю.\n\nСколько раз ты сделал что-то, что потом пожалел?",
        "options": {
            "a": {"text": "Ни разу", "level": 5},
            "b": {"text": "1-2 раза", "level": 3},
            "c": {"text": "3-5 раз", "level": 2},
            "d": {"text": "Больше 5 раз", "level": 1}
        }
    },
    {
        "id": "q3_2",
        "text": "Последний конфликт.\n\nЧто ты сделал?",
        "options": {
            "a": {"text": "Избежал", "level": 1},
            "b": {"text": "Уступил", "level": 1},
            "c": {"text": "Отстоял позицию", "level": 3},
            "d": {"text": "Нашёл компромисс", "level": 5}
        }
    },
    {
        "id": "q3_3",
        "text": "Как ты принимаешь важные решения?",
        "options": {
            "a": {"text": "Долго мучаюсь", "level": 1},
            "b": {"text": "Взвешиваю варианты", "level": 3},
            "c": {"text": "Быстро, по интуиции", "level": 5},
            "d": {"text": "Жду, когда решение придёт само", "level": 4}
        }
    },
    {
        "id": "q3_4",
        "text": "Как часто ты делаешь то, что не хочешь, но «надо»?",
        "options": {
            "a": {"text": "Постоянно (вся жизнь — «надо»)", "level": 1},
            "b": {"text": "Часто", "level": 2},
            "c": {"text": "Иногда", "level": 3},
            "d": {"text": "Редко (делаю то, что хочу)", "level": 5}
        }
    },
    {
        "id": "q3_5",
        "text": "Вспомни последнюю сильную эмоцию.\n\nЧто ты с ней сделал?",
        "options": {
            "a": {"text": "Подавил", "level": 1},
            "b": {"text": "Проанализировал", "level": 3},
            "c": {"text": "Выразил (слова/действия/творчество)", "level": 5},
            "d": {"text": "Наблюдал за ней", "level": 4}
        }
    },
    {
        "id": "q3_6",
        "text": "Как ты относишься к своим слабостям?",
        "options": {
            "a": {"text": "Стыжусь их", "level": 1},
            "b": {"text": "Пытаюсь исправить", "level": 2},
            "c": {"text": "Принимаю их", "level": 4},
            "d": {"text": "Вижу в них силу", "level": 6}
        }
    },
    {
        "id": "q3_7",
        "text": "Как часто ты чувствуешь, что живёшь не своей жизнью?",
        "options": {
            "a": {"text": "Постоянно", "level": 1},
            "b": {"text": "Часто", "level": 2},
            "c": {"text": "Иногда", "level": 3},
            "d": {"text": "Редко или никогда", "level": 5}
        }
    },
    {
        "id": "q3_8",
        "text": "Что ты делаешь, когда не знаешь, что делать?",
        "options": {
            "a": {"text": "Паникую", "level": 1},
            "b": {"text": "Ищу информацию", "level": 2},
            "c": {"text": "Действую методом проб", "level": 3},
            "d": {"text": "Жду ясности", "level": 4}
        }
    }
]

# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
STAGE_4_QUESTIONS = [
    {
        "id": "q4_1",
        "text": "Как часто ты чувствуешь, что «что-то не так» в жизни?",
        "options": {
            "a": {"text": "Постоянно", "dilts": "IDENTITY"},
            "b": {"text": "Часто", "dilts": "VALUES"},
            "c": {"text": "Иногда", "dilts": "CAPABILITIES"},
            "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}
        }
    },
    {
        "id": "q4_2",
        "text": "Что именно «не так»?\n\nВыбери то, что ближе всего:",
        "options": {
            "a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"},
            "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"},
            "c": {"text": "Не умею делать то, что хочу", "dilts": "CAPABILITIES"},
            "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_3",
        "text": "Человек чувствует себя несчастным.\n\nВ чём, скорее всего, причина?",
        "options": {
            "a": {"text": "Не те люди вокруг", "dilts": "ENVIRONMENT"},
            "b": {"text": "Делает не то, что хочет", "dilts": "BEHAVIOR"},
            "c": {"text": "Не умеет делать то, что хочет", "dilts": "CAPABILITIES"},
            "d": {"text": "Не понимает, чего хочет", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_4",
        "text": "Если бы ты мог изменить что-то одно, что бы это было?",
        "options": {
            "a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"},
            "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"},
            "c": {"text": "Свои способности", "dilts": "CAPABILITIES"},
            "d": {"text": "Своё понимание целей", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_5",
        "text": "Что для тебя сложнее всего?",
        "options": {
            "a": {"text": "Изменить внешние условия", "dilts": "ENVIRONMENT"},
            "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"},
            "c": {"text": "Научиться новому", "dilts": "CAPABILITIES"},
            "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_6",
        "text": "Когда ты застреваешь в проблеме, что обычно не хватает?",
        "options": {
            "a": {"text": "Ресурсов (время, деньги, связи)", "dilts": "ENVIRONMENT"},
            "b": {"text": "Действий (не начинаю)", "dilts": "BEHAVIOR"},
            "c": {"text": "Навыков (не умею)", "dilts": "CAPABILITIES"},
            "d": {"text": "Понимания (не знаю зачем)", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_7",
        "text": "Что мешает тебе быть счастливым?",
        "options": {
            "a": {"text": "Обстоятельства", "dilts": "ENVIRONMENT"},
            "b": {"text": "Мои действия", "dilts": "BEHAVIOR"},
            "c": {"text": "Мои ограничения", "dilts": "CAPABILITIES"},
            "d": {"text": "Я не знаю, что такое счастье", "dilts": "VALUES"}
        }
    },
    {
        "id": "q4_8",
        "text": "Если бы у тебя была волшебная палочка, что бы ты изменил?",
        "options": {
            "a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"},
            "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"},
            "c": {"text": "Свои способности", "dilts": "CAPABILITIES"},
            "d": {"text": "Себя (кто я)", "dilts": "IDENTITY"}
        }
    }
]

# УРОВНИ ДИЛТСА
DILTS_LEVELS = {
    "ENVIRONMENT": {
        "name": "ОКРУЖЕНИЕ",
        "code": "env",
        "description": "Проблема во внешних условиях",
        "solution": "Измени окружение или отношение к нему"
    },
    "BEHAVIOR": {
        "name": "ПОВЕДЕНИЕ",
        "code": "beh",
        "description": "Проблема в действиях",
        "solution": "Начни действовать по-другому"
    },
    "CAPABILITIES": {
        "name": "СПОСОБНОСТИ",
        "code": "cap",
        "description": "Проблема в навыках",
        "solution": "Освой новые навыки"
    },
    "VALUES": {
        "name": "ЦЕННОСТИ",
        "code": "val",
        "description": "Проблема в мотивации",
        "solution": "Найди свои истинные ценности"
    },
    "IDENTITY": {
        "name": "ИДЕНТИЧНОСТЬ",
        "code": "ide",
        "description": "Проблема в самоопределении",
        "solution": "Переопредели, кто ты"
    }
}

# ============================================
# АДАПТИВНЫЕ УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================

CLARIFICATION_QUESTIONS = {
    "stage1_external_internal": [
        {
            "id": "c1_1",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nПосле напряжённого дня что тебе нужнее?",
            "options": {
                "a": {"text": "Встретиться с людьми", "scores": {"EXTERNAL": 2}},
                "b": {"text": "Побыть в одиночестве", "scores": {"INTERNAL": 2}}
            }
        },
        {
            "id": "c1_2",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда ты думаешь о выходных, что первое приходит в голову?",
            "options": {
                "a": {"text": "Куда пойти, с кем встретиться", "scores": {"EXTERNAL": 2}},
                "b": {"text": "Чем заняться дома, о чём подумать", "scores": {"INTERNAL": 2}}
            }
        }
    ],
    "stage1_symbolic_material": [
        {
            "id": "c1_3",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЧто хуже: потерять деньги или потерять доверие близких?",
            "options": {
                "a": {"text": "Потерять доверие", "scores": {"SYMBOLIC": 2}},
                "b": {"text": "Потерять деньги", "scores": {"MATERIAL": 2}}
            }
        },
        {
            "id": "c1_4",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКогда ты тревожишься, о чём чаще?",
            "options": {
                "a": {"text": "Что обо мне подумают, как меня воспримут", "scores": {"SYMBOLIC": 2}},
                "b": {"text": "Хватит ли денег, успею ли, справлюсь ли", "scores": {"MATERIAL": 2}}
            }
        }
    ],
    "stage2_borderline": [
        {
            "id": "c2_1",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто ты чувствуешь, что застрял на месте?",
            "options": {
                "a": {"text": "Постоянно, не знаю как двигаться", "level": 2},
                "b": {"text": "Иногда, но нахожу выход", "level": 4},
                "c": {"text": "Редко, я в движении", "level": 5}
            }
        },
        {
            "id": "c2_2",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак ты относишься к своим прошлым ошибкам?",
            "options": {
                "a": {"text": "Стыжусь их, избегаю вспоминать", "level": 2},
                "b": {"text": "Анализирую и учусь", "level": 4},
                "c": {"text": "Принимаю как опыт", "level": 5}
            }
        }
    ],
    "stage3_discrepancy": [
        {
            "id": "c3_1",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nВспомни последний месяц. Сколько раз ты действовал не так, как хотел?",
            "options": {
                "a": {"text": "Постоянно", "level": 1},
                "b": {"text": "Часто (больше 5 раз)", "level": 2},
                "c": {"text": "Иногда (2-4 раза)", "level": 3},
                "d": {"text": "Редко (0-1 раз)", "level": 5}
            }
        },
        {
            "id": "c3_2",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак быстро ты замечаешь свои автоматические реакции?",
            "options": {
                "a": {"text": "Не замечаю, действую на автомате", "level": 1},
                "b": {"text": "Замечаю после", "level": 2},
                "c": {"text": "Замечаю в процессе", "level": 4},
                "d": {"text": "Замечаю до и могу изменить", "level": 5}
            }
        },
        {
            "id": "c3_3",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nКак часто ты делаешь то, что обещал себе?",
            "options": {
                "a": {"text": "Почти никогда", "level": 1},
                "b": {"text": "Иногда", "level": 2},
                "c": {"text": "Часто", "level": 4},
                "d": {"text": "Почти всегда", "level": 5}
            }
        }
    ],
    "stage4_tie": [
        {
            "id": "c4_1",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nЕсли бы ты мог изменить только одно, что бы выбрал?",
            "options": {
                "a": {"text": "Где я нахожусь", "dilts": "ENVIRONMENT"},
                "b": {"text": "Что я делаю", "dilts": "BEHAVIOR"},
                "c": {"text": "Что я умею", "dilts": "CAPABILITIES"},
                "d": {"text": "Что для меня важно", "dilts": "VALUES"},
                "e": {"text": "Кто я", "dilts": "IDENTITY"}
            }
        },
        {
            "id": "c4_2",
            "text": "🔍 УТОЧНЯЮЩИЙ ВОПРОС\n\nГде находится твоя главная проблема?",
            "options": {
                "a": {"text": "В обстоятельствах", "dilts": "ENVIRONMENT"},
                "b": {"text": "В моих действиях", "dilts": "BEHAVIOR"},
                "c": {"text": "В моих навыках", "dilts": "CAPABILITIES"},
                "d": {"text": "В моих целях", "dilts": "VALUES"},
                "e": {"text": "В моём самоопределении", "dilts": "IDENTITY"}
            }
        }
    ]
}

# ============================================
# ✅ АЛГОРИТМ ОПРЕДЕЛЕНИЯ ПРОФИЛЯ
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%\nПройдено: {current}/{total}"

def determine_perception_type(scores):
    """✅ Определяет тип восприятия"""
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    focus = "EXTERNAL" if external >= internal else "INTERNAL"
    anxiety = "SYMBOLIC" if symbolic >= material else "MATERIAL"
    
    type_data = PERCEPTION_TYPES.get((focus, anxiety), PERCEPTION_TYPES[("EXTERNAL", "SYMBOLIC")])
    return type_data["name"]

def calculate_thinking_level_optimized(level_scores):
    """✅ Определяет уровень мышления (1-9)"""
    if not level_scores:
        return 1
    
    avg = sum(level_scores) / len(level_scores)
    
    if avg <= 1.3:
        return 1
    elif avg <= 1.8:
        return 2
    elif avg <= 2.5:
        return 3
    elif avg <= 3.2:
        return 4
    elif avg <= 4.0:
        return 5
    elif avg <= 4.5:
        return 6
    elif avg <= 4.8:
        return 7
    elif avg <= 5.2:
        return 8
    else:
        return 9

def determine_dilts_level(dilts_answers):
    """✅ Определяет уровень Дилтса"""
    if not dilts_answers:
        return "ENVIRONMENT"
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(1)[0]
    return most_common[0]

def calculate_final_level(stage2_level, stage3_scores):
    """✅ Финальный уровень (приоритет поведению)"""
    if not stage3_scores:
        return stage2_level
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    final = stage3_avg * 0.7 + stage2_level * 0.3
    final_level = max(1, min(9, round(final)))
    
    logger.info(f"Final level: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}, final={final_level}")
    return final_level

def get_type_code(perception_type: str) -> str:
    """Код типа (SA/IA/SP/IP)"""
    type_map = {
        "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "SA",
        "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "IA",
        "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "SP",
        "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "IP"
    }
    return type_map.get(perception_type, "SA")

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

def find_best_matching_profile(type_code: str, user_level: int, dilts_code: str) -> str:
    """
    ✅ Ищет наиболее подходящий профиль из 36
    
    Приоритет:
    1. Точное совпадение (type_level_dilts)
    2. Тот же тип + уровень, другой Дилтс
    3. Тот же тип, ближайший уровень (±1)
    4. Fallback: первый профиль типа
    """
    # 1. Точное совпадение
    exact_key = f"{type_code}_{user_level}_{dilts_code}"
    if exact_key in CARD_DATA:
        logger.info(f"✅ Exact match: {exact_key}")
        return exact_key
    
    # 2. Тот же тип + уровень, другой Дилтс
    for dilts in ["env", "beh", "cap", "val", "ide"]:
        candidate = f"{type_code}_{user_level}_{dilts}"
        if candidate in CARD_DATA:
            logger.info(f"✅ Same type+level: {candidate}")
            return candidate
    
    # 3. Ближайший уровень
    for offset in [1, -1, 2, -2]:
        level = user_level + offset
        if 1 <= level <= 9:
            for dilts in ["env", "beh", "cap", "val", "ide"]:
                candidate = f"{type_code}_{level}_{dilts}"
                if candidate in CARD_DATA:
                    logger.info(f"✅ Nearby level: {candidate}")
                    return candidate
    
    # 4. Fallback
    for level in range(1, 10):
        for dilts in ["env", "beh", "cap", "val", "ide"]:
            candidate = f"{type_code}_{level}_{dilts}"
            if candidate in CARD_DATA:
                logger.warning(f"⚠️ Fallback: {candidate}")
                return candidate
    
    logger.error(f"❌ No profile found: {type_code}_{user_level}_{dilts_code}")
    return f"{type_code}_1_env"

def calculate_profile_key(context_data: dict) -> str:
    """✅ ГЛАВНАЯ ФУНКЦИЯ: определяет ключ профиля"""
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    level = context_data.get("final_level", 1)
    
    dilts_level = context_data.get("dilts_level", "ENVIRONMENT")
    dilts_code = get_dilts_code(dilts_level)
    
    profile_key = find_best_matching_profile(type_code, level, dilts_code)
    
    logger.info(f"✅ Profile: {profile_key} (requested: {type_code}_{level}_{dilts_code})")
    return profile_key

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

def need_clarification_stage2(level_scores):
    """Нужны ли уточнения после ЭТАПА 2"""
    if not level_scores:
        return False
    avg = sum(level_scores) / len(level_scores)
    return 3.5 <= avg <= 5.5

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
# КОМАНДЫ БОТА
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
    context.user_data["stage2_level_scores"] = []
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    
    logger.info(f"User {update.effective_user.id} started test")
    
    return await show_stage_1_intro(update, context)

# ============================================
# ЭКРАНЫ ПЕРЕД ЭТАПАМИ
# ============================================

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

# ============================================
# ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ
# ============================================

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
    """✅ Завершение ЭТАПА 1"""
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
    
    # ✅ ОБНОВЛЁННЫЙ ТЕКСТ (БЕЗ ТИПА)
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

# ============================================
# УТОЧНЯЮЩИЕ ВОПРОСЫ
# ============================================

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
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"clarify_{clarification_stage}_{current}_{option_id}"
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
            selected_option = question["options"].get(option_id)
            if selected_option:
                level = selected_option.get("level", 1)
                context.user_data["stage2_level_scores"].append(level)
        
        context.user_data["clarification_current"] = current + 1
        return await ask_clarification_question(update, context)
        
    elif clarification_stage == "stage3":
        questions = CLARIFICATION_QUESTIONS.get("stage3_discrepancy", [])
        if current < len(questions):
            question = questions[current]
            selected_option = question["options"].get(option_id)
            if selected_option:
                level = selected_option.get("level", 1)
                context.user_data["stage3_level_scores"].append(level)
        
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

# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    # ✅ ОБНОВЛЁННЫЙ ТЕКСТ
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
    
    # ✅ ОБНОВЛЁННЫЙ ТЕКСТ
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
    for option_id, option in question["options"].items():
        keyboard.append([
            InlineKeyboardButton(
                option["text"], 
                callback_data=f"stage2_{current}_{option_id}"
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
        option_id = parts[2]
        
        perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
        questions = STAGE_2_QUESTIONS.get(perception_type, STAGE_2_QUESTIONS["СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ"])
        
        question = questions[current]
        selected_option = question["options"].get(option_id)
        
        if not selected_option:
            return STAGE_2
        
        level = selected_option.get("level", 1)
        context.user_data["stage2_level_scores"].append(level)
        
        logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> {option_id} (level={level})")
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Завершение ЭТАПА 2"""
    query = update.callback_query
    level_scores = context.user_data.get("stage2_level_scores", [])
    
    needs_clarification = need_clarification_stage2(level_scores)
    
    if needs_clarification and not context.user_data.get("stage2_clarified", False):
        context.user_data["clarification_current"] = 0
        context.user_data["clarification_stage"] = "stage2"
        
        logger.info(f"User {update.effective_user.id}: Stage 2 needs clarification")
        return await ask_clarification_question(update, context)
    
    thinking_level = calculate_thinking_level_optimized(level_scores)
    context.user_data["thinking_level"] = thinking_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}")
    
    # ✅ ОБНОВЛЁННЫЙ ТЕКСТ
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 Конфигурация мышления определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

# ============================================
# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ
# ============================================

async def show_stage_3_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 3"""
    query = update.callback_query
    await query.answer()
    
    # ✅ ОБНОВЛЁННЫЙ ТЕКСТ
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
    
    # ✅ ОБНОВЛЁННЫЙ ТЕКСТ
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
    """✅ Завершение ЭТАПА 3"""
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

# ============================================
# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ
# ============================================

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
        f"<b>🎯 ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ</b>\n\n"
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

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 и показ итогового результата"""
    query = update.callback_query
    await query.answer()
    
    # Подсчёт баллов по уровням
    level_scores = {"environment": 0, "behavior": 0, "capabilities": 0, "values": 0, "identity": 0}
    
    for i in range(len(STAGE_4_QUESTIONS)):
        answer_key = f"stage4_{i}"
        if answer_key in context.user_data:
            option_id = context.user_data[answer_key]
            question = STAGE_4_QUESTIONS[i]
            level = question["options"][option_id]["level"]
            level_scores[level] += 1
    
    # Определение доминирующего уровня
    dominant_level = max(level_scores, key=level_scores.get)
    
    level_names = {
        "environment": "Окружение",
        "behavior": "Поведение",
        "capabilities": "Способности",
        "values": "Ценности",
        "identity": "Идентичность"
    }
    
    level_descriptions = {
        "environment": "Твоя точка роста — изменение окружения. Тебе нужно менять внешние условия.",
        "behavior": "Твоя точка роста — поведение. Тебе нужно менять свои действия.",
        "capabilities": "Твоя точка роста — способности. Тебе нужно развивать навыки.",
        "values": "Твоя точка роста — ценности. Тебе нужно пересмотреть мотивы.",
        "identity": "Твоя точка роста — идентичность. Тебе нужно переосмыслить, кто ты."
    }
    
    context.user_data["stage4_level"] = dominant_level
    
    # Получаем результаты всех этапов
    archetype = context.user_data.get("archetype", "Не определён")
    stage2_result = context.user_data.get("stage2_result", "Не определён")
    stage3_level = context.user_data.get("stage3_level", "Не определён")
    
    # Формируем итоговый текст
    part1 = (
        f"🎉 <b>ПОЗДРАВЛЯЕМ! ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"📊 <b>ТВОИ РЕЗУЛЬТАТЫ:</b>\n\n"
        f"<b>ЭТАП 1: АРХЕТИП</b>\n"
        f"🎭 {archetype}\n\n"
        f"<b>ЭТАП 2: ЖИЗНЕННЫЙ СЦЕНАРИЙ</b>\n"
        f"📜 {stage2_result}\n\n"
    )
    
    part2 = (
        f"<b>ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n"
        f"🔄 Уровень осознанности: {stage3_level}\n\n"
        f"<b>ЭТАП 4: ТОЧКА РОСТА</b>\n"
        f"🎯 {level_names[dominant_level]}\n"
        f"💡 {level_descriptions[dominant_level]}\n\n"
    )
    
    part3 = (
        f"🎁 <b>ХОЧЕШЬ БОЛЬШЕ?</b>\n\n"
        f"Получи полный разбор личности:\n"
        f"✅ Детальный анализ всех 4 этапов\n"
        f"✅ Персональные рекомендации\n"
        f"✅ План развития на 3 месяца\n\n"
        f"💎 <b>Стоимость:</b> 960 ₽\n\n"
        f"👉 Или поделись тестом с другом и получи <b>бесплатный подарок</b>!"
    )
    
    full_text = part1 + part2 + part3
    
    # Проверка длины сообщения
    if len(full_text) > 4096:
        # Разбиваем на части
        
        # ✅ КНОПКИ
        keyboard = [
            [InlineKeyboardButton("🎁 Поделиться тестом", url="https://t.me/share/url?url=https://t.me/Testing_Lichnosti_bot&text=Зацени тест!")],
            [InlineKeyboardButton("✅ Я поделился, дай подарок!", callback_data="share_confirmed")],
            [InlineKeyboardButton("💎 Полный пакет (960 ₽)", url=f"https://t.me/{AUTHOR_LINK.strip('@')}")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(part1, parse_mode="HTML")
        await query.message.reply_text(part2, parse_mode="HTML")
        await query.message.reply_text(part3, parse_mode="HTML", reply_markup=reply_markup)
    else:
        # ✅ КНОПКИ
        keyboard = [
            [InlineKeyboardButton("🎁 Поделиться тестом", url="https://t.me/share/url?url=https://t.me/Testing_Lichnosti_bot&text=Зацени тест!")],
            [InlineKeyboardButton("✅ Я поделился, дай подарок!", callback_data="share_confirmed")],
            [InlineKeyboardButton("💎 Полный пакет (960 ₽)", url=f"https://t.me/{AUTHOR_LINK.strip('@')}")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(full_text, reply_markup=reply_markup, parse_mode="HTML")
    
    return ConversationHandler.END

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Показ результатов с анимацией"""
    query = update.callback_query
    
    # ✅ АНИМИРОВАННЫЙ ЭКРАН
    loading_text = (
        f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\n"
        f"Анализирую твои ответы и определяю профиль..."
    )
    await query.edit_message_text(loading_text, parse_mode="HTML")
    
    await asyncio.sleep(2)
    
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    final_level = context.user_data.get("final_level", 1)
    dilts_level = context.user_data.get("dilts_level", "ENVIRONMENT")
    
    profile_key = calculate_profile_key(context.user_data)
    
    profile_card = get_card_description(profile_key)
    
    if not profile_card:
        error_text = (
            f"❌ <b>ОШИБКА</b>\n\n"
            f"Не удалось найти профиль.\n\n"
            f"Попробуй пройти тест заново: /start"
        )
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    # ✅ ФОРМИРУЕМ ПОЛНОЕ ОПИСАНИЕ ПРОФИЛЯ
    profile_text = (
        f"✅ <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"{profile_card['title']}\n\n"
        f"{profile_card['pain']}\n\n"
        f"<b>🌍 ТВОЙ МИР:</b>\n\n"
        f"{profile_card['world']}\n\n"
        f"<b>⚡️ ТВОЯ СУПЕРСИЛА:</b>\n\n"
        f"{profile_card['superpower']}\n\n"
        f"<b>🚀 ТОЧКА РОСТА:</b>\n\n"
        f"{profile_card['growth']}\n\n"
        f"{profile_card['cta']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 <b>ПОЛНЫЙ ПАКЕТ (960 ₽)</b>\n\n"
        f"✓ Полное описание архетипа и персональные рекомендации (15+ страниц)\n"
        f"✓ Персональная терапевтическая сказка для коррекции других конфликтующих частей\n"
        f"✓ Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (pdf) для самостоятельной коррекции на уровне конфигурации восприятия\n\n"
        f"💬 <b>Хочешь разобраться глубже?</b>\n"
        f"Получить персональную консультацию:\n"
        f"👉 {AUTHOR_LINK}"
    )
    
    # Проверяем длину сообщения
    if len(profile_text) > 4096:
        # Разбиваем на части
        part1 = (
            f"✅ <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
            f"{profile_card['title']}\n\n"
            f"{profile_card['pain']}\n\n"
            f"<b>🌍 ТВОЙ МИР:</b>\n\n"
            f"{profile_card['world']}"
        )
        
        part2 = (
            f"<b>⚡️ ТВОЯ СУПЕРСИЛА:</b>\n\n"
            f"{profile_card['superpower']}\n\n"
            f"<b>🚀 ТОЧКА РОСТА:</b>\n\n"
            f"{profile_card['growth']}\n\n"
            f"{profile_card['cta']}"
        )
        
        part3 = (
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💎 <b>ПОЛНЫЙ ПАКЕТ (960 ₽)</b>\n\n"
            f"✓ Полное описание архетипа и персональные рекомендации (15+ страниц)\n"
            f"✓ Персональная терапевтическая сказка для коррекции других конфликтующих частей\n"
            f"✓ Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (pdf) для самостоятельной коррекции на уровне конфигурации восприятия\n\n"
            f"💬 <b>Хочешь разобраться глубже?</b>\n"
            f"Получить персональную консультацию:\n"
            f"👉 {AUTHOR_LINK}"
        )
        
        # ✅ КНОПКИ
        keyboard = [
            [InlineKeyboardButton("🎁 Поделиться", switch_inline_query="Зацени тест! https://t.me/Testing_Lichnosti_bot")],
            [InlineKeyboardButton("✅ Я поделился, дай подарок!", callback_data="share_confirmed")],
            [InlineKeyboardButton("💎 Полный пакет (960 ₽)", url=f"https://t.me/{AUTHOR_LINK.strip('@')}")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(part1, parse_mode="HTML")
        await query.message.reply_text(part2, parse_mode="HTML")
        await query.message.reply_text(part3, parse_mode="HTML", reply_markup=reply_markup)
    else:
        # ✅ КНОПКИ ПРИКРЕПЛЕНЫ К ТЕКСТУ
        keyboard = [
            [InlineKeyboardButton("🎁 Поделиться и получить подарок", switch_inline_query="Зацени тест! t.me/Testing_Lichnosti_bot")],
            [InlineKeyboardButton("💎 Получить полный пакет (960 ₽)", url=f"https://t.me/{AUTHOR_LINK.strip('@')}")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(profile_text, parse_mode="HTML", reply_markup=reply_markup)
    
    # Сохраняем состояние для подтверждения шаринга
    context.user_data["awaiting_share_confirm"] = True
    
    return SHARE_CONFIRM

# ============================================
# ОБРАБОТКА ШАРИНГА И ПОДАРКА
# ============================================

async def handle_share_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения шаринга"""
    query = update.callback_query
    
    if query.data == "share_confirmed":
        await query.answer()
        
        gift_text = (
            f"🎁 <b>СПАСИБО ЗА РЕПОСТ!</b>\n\n"
            f"Вот твой подарок — терапевтическая сказка:\n\n"
            f"👉 {GIFT_PDF_LINK}\n\n"
            f"Приятного чтения! 📖"
        )
        
        await query.edit_message_text(gift_text, parse_mode="HTML")
        
        context.user_data["awaiting_share_confirm"] = False
        
        return ConversationHandler.END
    
    return SHARE_CONFIRM

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    return await start_test(update, context)

# ============================================
# ОБРАБОТКА ОТМЕНЫ
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

# ============================================
# ✅ ПРОВЕРКА ПРОФИЛЕЙ ПРИ ЗАПУСКЕ
# ============================================

def check_profiles_on_startup():
    """Проверяет наличие всех 36 профилей"""
    logger.info("🔍 Checking profile data...")
    
    expected_types = ["SA", "IA", "SP", "IP"]
    expected_levels = list(range(1, 10))  # 1-9
    
    missing_profiles = []
    found_profiles = []
    
    for type_code in expected_types:
        for level in expected_levels:
            # Проверяем хотя бы один профиль этого типа и уровня
            found = False
            for dilts in ["env", "beh", "cap", "val", "ide"]:
                profile_key = f"{type_code}_{level}_{dilts}"
                if profile_key in CARD_DATA:
                    found = True
                    found_profiles.append(profile_key)
                    break
            
            if not found:
                missing_profiles.append(f"{type_code}_{level}")
    
    logger.info(f"✅ Found {len(found_profiles)} profiles in CARD_DATA")
    
    if missing_profiles:
        logger.warning(f"⚠️ Missing profiles for: {missing_profiles}")
    else:
        logger.info("✅ All profile types covered (at least one per type-level)")
    
    # Проверка общего количества
    total_profiles = len(CARD_DATA)
    logger.info(f"📊 Total profiles in CARD_DATA: {total_profiles}")
    
    if total_profiles < 36:
        logger.warning(f"⚠️ Expected 36 profiles, found {total_profiles}")
    else:
        logger.info("✅ Profile count OK")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    
    # Проверка профилей
    check_profiles_on_startup()
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # ConversationHandler
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
            RESULT: [
    CallbackQueryHandler(handle_share_confirm, pattern="^share_confirmed$"),
    CallbackQueryHandler(restart_test, pattern="^restart_test$")
],
            SHARE_CONFIRM: [
                CallbackQueryHandler(handle_share_confirm, pattern="^share_confirmed$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    # Запуск бота
    logger.info("🚀 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
