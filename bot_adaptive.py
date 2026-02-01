# bot_adaptive.py
"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа:
1. Конфигурация восприятия (8 вопросов)
2. Конфигурация мышления (8-12 вопросов, адаптивно)
3. Конфигурация поведенческих паттернов (8 вопросов)
4. Конфликт логических уровней (8 вопросов)
"""

import logging
import os
import asyncio
import re
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
# ИМПОРТ ГЕНЕРАТОРА КОНТЕНТА
# ============================================
from content_generator import generate_profile

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
STAGE_1, STAGE_2, STAGE_3, STAGE_4, RESULT = range(5)

# ============================================
# ДАННЫЕ ВОПРОСОВ
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

# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ (универсальные для всех типов)
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

# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ (универсальные для всех типов)
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

# УРОВНИ МЫШЛЕНИЯ (описания)
THINKING_LEVELS = {
    1: {
        "name": "ДЕФИЦИТАРНЫЙ",
        "description": "Базовая потребность не удовлетворена. Фокус на нехватке."
    },
    2: {
        "name": "ПОИСКОВЫЙ",
        "description": "Активный поиск решения. Много попыток, мало результата."
    },
    3: {
        "name": "КОНСТРУКТИВНЫЙ",
        "description": "Создание стабильной базы. Первые устойчивые результаты."
    },
    4: {
        "name": "КРИЗИСНЫЙ",
        "description": "Переосмысление достигнутого. Вопрос «А что дальше?»"
    },
    5: {
        "name": "ИНТЕГРАТИВНЫЙ",
        "description": "Уверенное владение. Баланс и целостность."
    },
    6: {
        "name": "АЛЬТРУИСТИЧЕСКИЙ",
        "description": "Служение другим. Вклад в мир."
    },
    7: {
        "name": "МУДРЕЦКИЙ",
        "description": "Глубокое понимание. Видение сути."
    },
    8: {
        "name": "СИСТЕМНЫЙ",
        "description": "Управление на системном уровне. Создание структур."
    },
    9: {
        "name": "ТРАНСЦЕНДЕНТНЫЙ",
        "description": "Выход за пределы. Единство с процессом."
    }
}

# УРОВНИ ДИЛТСА (описания)
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
        "code": "bel",
        "description": "Проблема в мотивации",
        "solution": "Найди свои истинные ценности"
    },
    "IDENTITY": {
        "name": "ИДЕНТИЧНОСТЬ",
        "code": "id",
        "description": "Проблема в самоопределении",
        "solution": "Переопредели, кто ты"
    }
}

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"{bar} {progress}%\nПройдено: {current}/{total}"

def determine_perception_type(scores):
    """Определяет тип восприятия по баллам"""
    focus = "EXTERNAL" if scores.get("EXTERNAL", 0) > scores.get("INTERNAL", 0) else "INTERNAL"
    anxiety = "SYMBOLIC" if scores.get("SYMBOLIC", 0) > scores.get("MATERIAL", 0) else "MATERIAL"
    
    type_data = PERCEPTION_TYPES.get((focus, anxiety), PERCEPTION_TYPES[("EXTERNAL", "SYMBOLIC")])
    return type_data["name"]

def calculate_thinking_level(level_scores):
    """Определяет уровень мышления (1-9)"""
    if not level_scores:
        return 1
    
    avg = sum(level_scores) / len(level_scores)
    
    if avg <= 1.5:
        return 1
    elif avg <= 2.5:
        return 2
    elif avg <= 3.5:
        return 3
    elif avg <= 4.5:
        return 4
    elif avg <= 5.5:
        return 5
    elif avg <= 6.5:
        return 6
    elif avg <= 7.5:
        return 7
    elif avg <= 8.5:
        return 8
    else:
        return 9

def calculate_dilts_level(dilts_answers):
    """Определяет проблемный уровень Дилтса"""
    from collections import Counter
    counter = Counter(dilts_answers)
    
    if counter:
        return counter.most_common(1)[0][0]
    return "ENVIRONMENT"

def get_type_code(perception_type: str) -> str:
    """Возвращает код типа (SA/IA/SP/IP) по названию"""
    type_map = {
        "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "SA",
        "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "IA",
        "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "SP",
        "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "IP"
    }
    return type_map.get(perception_type, "SA")

def calculate_profile_key(context_data: dict) -> str:
    """
    Определяет ключ профиля в формате "SA_1_env"
    
    Args:
        context_data: словарь с данными пользователя
    
    Returns:
        строка вида "SA_1_env"
    """
    # 1. Получаем код типа (SA/IA/SP/IP)
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    # 2. Получаем уровень (1-9)
    level = context_data.get("final_level", 1)
    
    # 3. Получаем код Дилтса (env/beh/cap/bel/id)
    dilts_level = context_data.get("dilts_level", "ENVIRONMENT")
    dilts_code = DILTS_LEVELS.get(dilts_level, DILTS_LEVELS["ENVIRONMENT"])["code"]
    
    profile_key = f"{type_code}_{level}_{dilts_code}"
    
    logger.info(f"Profile key calculated: {profile_key}")
    return profile_key

# ============================================
# КОМАНДЫ БОТА
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест!</b>\n\n"
        f"🔍 <b>Узнай свой текущий психологический профиль и получи персональные рекомендации для развития.</b>\n\n"
        f"Этот тест поможет определить:\n"
        f"• Как ты воспринимаешь реальность 🧠\n"
        f"• На каком уровне развития ты находишься 📊\n"
        f"• Какие поведенческие паттерны у тебя есть 🎯\n"
        f"• Где находится твоя точка роста 🚀\n\n"
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
    """Начало теста - показ экрана ЭТАПА 1"""
    query = update.callback_query
    await query.answer()
    
    # ПОЛНАЯ ОЧИСТКА ДАННЫХ
    context.user_data.clear()
    
    # Инициализация данных пользователя
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores"] = []
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    
    logger.info(f"User {update.effective_user.id} started test")
    
    # Показ экрана ЭТАПА 1
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

async def back_to_stage_1_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # Добавляем баллы
        for axis, score in selected_option.get("scores", {}).items():
            context.user_data["scores"][axis] += score
        
        logger.info(f"User {update.effective_user.id}: Stage 1 Q{current} -> {option_id}")
        
        context.user_data["stage1_current"] = current + 1
        return await ask_stage_1_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 1"""
    query = update.callback_query
    
    scores = context.user_data.get("scores", {})
    perception_type = determine_perception_type(scores)
    context.user_data["perception_type"] = perception_type
    
    logger.info(f"User {update.effective_user.id}: Stage 1 complete, type={perception_type}")
    
    result_text = (
        f"✅ <b>ЭТАП 1 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Конфигурация восприятия определена</b>\n\n"
        f"Твой тип: <b>{perception_type}</b>\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 2</b>: определение конфигурации мышления.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_2_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_2

# ============================================
# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
# ============================================

async def show_stage_2_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экран перед ЭТАПОМ 2"""
    query = update.callback_query
    await query.answer()
    
    intro_text = (
        f"<b>🎯 ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>\n\n"
        f"Сейчас мы определим твой уровень когнитивной зрелости.\n\n"
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
        f"Это уровень развития твоего мышления внутри типа восприятия.\n\n"
        f"<b>9 уровней когнитивной зрелости:</b>\n\n"
        f"1️⃣ ДЕФИЦИТАРНЫЙ — базовая нужда не удовлетворена\n"
        f"2️⃣ ПОИСКОВЫЙ — активный поиск решения\n"
        f"3️⃣ КОНСТРУКТИВНЫЙ — создание стабильной базы\n"
        f"4️⃣ КРИЗИСНЫЙ — переосмысление достигнутого\n"
        f"5️⃣ ИНТЕГРАТИВНЫЙ — уверенное владение\n"
        f"6️⃣ АЛЬТРУИСТИЧЕСКИЙ — служение другим\n"
        f"7️⃣ МУДРЕЦКИЙ — глубокое понимание\n"
        f"8️⃣ СИСТЕМНЫЙ — управление на системном уровне\n"
        f"9️⃣ ТРАНСЦЕНДЕНТНЫЙ — выход за пределы\n\n"
        f"<b>Результат:</b> Твой текущий уровень развития"
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
        
        logger.info(f"User {update.effective_user.id}: Stage 2 Q{current} -> {option_id}")
        
        context.user_data["stage2_current"] = current + 1
        return await ask_stage_2_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 2"""
    query = update.callback_query
    
    level_scores = context.user_data.get("stage2_level_scores", [])
    thinking_level = calculate_thinking_level(level_scores)
    context.user_data["thinking_level"] = thinking_level
    
    logger.info(f"User {update.effective_user.id}: Stage 2 complete, level={thinking_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 2 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Конфигурация мышления определена</b>\n\n"
        f"Твой уровень: <b>{thinking_level}</b>\n\n"
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
    
    intro_text = (
        f"<b>🎯 ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ</b>\n\n"
        f"Сейчас мы уточним твой уровень через анализ автоматических реакций.\n\n"
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
        f"Это автоматические реакции в типичных ситуациях.\n\n"
        f"<b>Зачем это нужно:</b>\n\n"
        f"Человек может не осознавать свой уровень развития, но его поведение его выдаёт.\n\n"
        f"Мы зададим вопросы о реальных действиях (не о мнениях), чтобы уточнить твой уровень.\n\n"
        f"<b>Результат:</b> Подтверждение или корректировка уровня из ЭТАПА 2"
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
        
        logger.info(f"User {update.effective_user.id}: Stage 3 Q{current} -> {option_id}")
        
        context.user_data["stage3_current"] = current + 1
        return await ask_stage_3_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 3"""
    query = update.callback_query
    
    # Корректировка уровня на основе поведенческих паттернов
    stage2_level = context.user_data.get("thinking_level", 1)
    stage3_scores = context.user_data.get("stage3_level_scores", [])
    stage3_avg = sum(stage3_scores) / len(stage3_scores) if stage3_scores else 1
    
    # Если расхождение больше 1 уровня, корректируем
    if abs(stage3_avg - stage2_level) > 1:
        final_level = int((stage2_level + stage3_avg) / 2)
    else:
        final_level = stage2_level
    
    context.user_data["final_level"] = final_level
    
    logger.info(f"User {update.effective_user.id}: Stage 3 complete, final_level={final_level}")
    
    result_text = (
        f"✅ <b>ЭТАП 3 ЗАВЕРШЁН!</b>\n\n"
        f"🎯 <b>Поведенческие паттерны проанализированы</b>\n\n"
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
        f"<b>6 уровней (снизу вверх):</b>\n\n"
        f"1️⃣ ОКРУЖЕНИЕ — внешние условия\n"
        f"2️⃣ ПОВЕДЕНИЕ — твои действия\n"
        f"3️⃣ СПОСОБНОСТИ — твои навыки\n"
        f"4️⃣ ЦЕННОСТИ — твои мотивы\n"
        f"5️⃣ ИДЕНТИЧНОСТЬ — кто ты\n"
        f"6️⃣ МИССИЯ — зачем ты в мире\n\n"
        f"<b>Принцип:</b> Проблема на нижнем уровне решается изменением верхнего.\n\n"
        f"<b>Результат:</b> Твой проблемный уровень + вектор развития"
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
        
        logger.info(f"User {update.effective_user.id}: Stage 4 Q{current} -> {option_id}")
        
        context.user_data["stage4_current"] = current + 1
        return await ask_stage_4_question(update, context)
        
    finally:
        context.user_data["processing"] = False

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4 и показ результата"""
    query = update.callback_query
    
    dilts_answers = context.user_data.get("stage4_dilts_answers", [])
    dilts_level = calculate_dilts_level(dilts_answers)
    context.user_data["dilts_level"] = dilts_level
    
    logger.info(f"User {update.effective_user.id}: Stage 4 complete, dilts={dilts_level}")
    
    return await show_result(update, context)

# ============================================
# РЕЗУЛЬТАТ
# ============================================

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ финального результата с использованием генератора контента"""
    query = update.callback_query
    
    # Получаем данные профиля
    perception_type = context.user_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    final_level = context.user_data.get("final_level", 1)
    dilts_level = context.user_data.get("dilts_level", "ENVIRONMENT")
    
    # Вычисляем ключ профиля
    profile_key = calculate_profile_key(context.user_data)
    type_code = get_type_code(perception_type)
    dilts_code = DILTS_LEVELS.get(dilts_level, DILTS_LEVELS["ENVIRONMENT"])["code"]
    
    # ГЕНЕРИРУЕМ КОНТЕНТ ЧЕРЕЗ ГЕНЕРАТОР
    profile_data = generate_profile(type_code, final_level, dilts_code)
    
    # Получаем описания для итогового экрана
    dilts_info = DILTS_LEVELS.get(dilts_level, DILTS_LEVELS["ENVIRONMENT"])
    
    logger.info(f"User {update.effective_user.id}: Showing result, profile_key={profile_key}")
    
    # ФОРМИРУЕМ ИТОГОВЫЙ ЭКРАН
    result_text = (
        f"🎉 <b>ТЕСТ ЗАВЕРШЁН!</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>📊 ТВОЙ ПРОФИЛЬ:</b>\n\n"
        f"<b>🎯 Тип восприятия:</b>\n{perception_type}\n\n"
        f"<b>📖 КТО ТЫ:</b>\n\n"
        f"{profile_data['who']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>🎪 Проблемный уровень:</b>\n{dilts_info['name']}\n"
        f"<i>{dilts_info['description']}</i>\n\n"
        f"<b>🚀 ВЕКТОР РАЗВИТИЯ:</b>\n"
        f"{dilts_info['solution']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>🔑 Код профиля:</b> <code>{profile_key}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 <b>РАБОЧИЙ ИНСТРУМЕНТ КОРРЕКЦИИ</b>\n\n"
        f"💡 Твой инструмент который корректирует конфигурацию поведения, на уровне конфигурации мышления – это метафорическая форма (ссылка на сказку внизу экрана).\n\n"
        f"💎 <b>ПОЛНЫЙ ПАКЕТ (960 ₽)</b>\n"
        f"✓ Полное описание архетипа и персональные рекомендации (15+ страниц)\n"
        f"✓ Персональная терапевтическая сказка для коррекции других конфликтующих частей\n"
        f"✓ Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (pdf) для самостоятельной коррекции на уровне конфигурации восприятия\n\n"
        f"💬 <b>Хочешь разобраться глубже?</b>\n"
        f"Получить персональную консультацию:\n"
        f"👉 @meysternlp"
    )
    
    story_link = "https://drive.google.com/file/d/1Y0nr2C_sWlQVOF84THLXa3nflFBVSI77/view?usp=sharing"
    bot_link = "https://t.me/Testing_Lichnosti_bot"
    
    keyboard = [
        [InlineKeyboardButton("📖 Читать сказку", url=story_link)],
        [InlineKeyboardButton("💳 Получить полный пакет (960 ₽)", url="https://t.me/meysternlp")],
        [InlineKeyboardButton("🎁 Поделиться тестом и получить подарок", url=f"https://t.me/share/url?url={bot_link}&text=Пройди тест и узнай свой психотип!")],
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        result_text, 
        reply_markup=reply_markup, 
        parse_mode="HTML", 
        disable_web_page_preview=True
    )
    
    # Очистка данных после завершения
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    cancel_text = (
        f"❌ Тест отменён.\n"
        f"Хочешь начать заново?\n"
        f"👉 /start"
    )
    await update.message.reply_text(cancel_text)
    context.user_data.clear()
    return ConversationHandler.END

async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка таймаута"""
    if update.effective_message:
        await update.effective_message.reply_text(
            "⏱ Время сеанса истекло.\n"
            "Начни тест заново: /start"
        )
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ERROR HANDLER
# ============================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Exception: {context.error}", exc_info=context.error)
    
    if update and hasattr(update, 'effective_message'):
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла ошибка. Попробуй начать заново: /start"
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    if hasattr(context, 'user_data') and context.user_data:
        context.user_data.clear()

# ============================================
# MAIN
# ============================================

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(show_stage_1_intro, pattern="^show_stage_1_intro$"),
                CallbackQueryHandler(show_stage_1_details, pattern="^stage1_details$"),
                CallbackQueryHandler(back_to_stage_1_intro, pattern="^back_to_stage1_intro$"),
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
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, timeout_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        conversation_timeout=1800,
        allow_reentry=True,
        per_message=False
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("✅ Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
