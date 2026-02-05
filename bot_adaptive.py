"""
АДАПТИВНЫЙ ТЕСТ: ОПРЕДЕЛЕНИЕ АРХЕТИПА
4 этапа + адаптивные уточнения + СИСТЕМА БАЛЛОВ как в карточном тесте
ВЕРСИЯ 2.0: Добавлена интеграция с ЮKassa для автоматической отправки файлов
"""

import logging
import os
import asyncio
import urllib.parse
import math
import re
import json
import base64
import requests
from datetime import datetime
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

# Импорт загрузчика и профилей
from loader import loader
from base import VariaticaProfile

# ============================================
# КОНСТАНТЫ И КОНФИГУРАЦИЯ
# ============================================

# Получение токена
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

# Данные ЮKassa
YOOKASSA_SHOP_ID = "1262862"
YOOKASSA_SECRET_KEY = "live_5dmnrUoxFCR-6xcdgxd2zPWi8_DSfWoFRgHNxlgxSgs"

# Остальные константы
BOT_LINK = "t.me/Testing_Lichnosti_bot"
GIFT_PDF_LINK = "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Только что узнал о себе то, о чём ещё не знал... Тест показывает скрытые паттерны. КатеГОрически рекомендую.."
OLD_PAYMENT_LINK = "https://yookassa.ru/my/i/aYHvs0MnrXUT/l"  # Старая ссылка

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния ConversationHandler (добавлено PAYMENT_CHECK)
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS, GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN, DILTS_CLARIFICATION, PAYMENT_CHECK = range(11)

# ============================================
# ВОПРОСЫ ЭТАПА 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ
# ============================================

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

# Типы восприятия
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

# ============================================
# ФАЙЛЫ ДЛЯ ОТПРАВКИ ПОСЛЕ ОПЛАТЫ
# ============================================

PAID_FILES = [
    ("📚 Полный разбор профиля (PDF)", "https://disk.yandex.ru/d/full_analysis.pdf"),
    ("📖 Терапевтическая сказка", "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA"),
    ("📘 Книга ВАРИАТИКА", "https://disk.yandex.ru/d/book.pdf"),
    ("📋 Рекомендации по развитию", "https://disk.yandex.ru/d/recommendations.pdf"),
    ("🗺 Карта сильных и слабых сторон", "https://disk.yandex.ru/d/profile_map.pdf")
]

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ЮKASSA
# ============================================

def create_payment_link(user_id: int):
    """Создает платежную ссылку с метаданными"""
    
    payment_data = {
        "amount": {
            "value": "690.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/Testing_Lichnosti_bot"
        },
        "capture": True,
        "description": "Полный пакет ВАРИАТИКА",
        "metadata": {
            "user_id": str(user_id),
            "product": "full_package",
            "telegram_bot": "VariaticaBot"
        }
    }
    
    auth = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Idempotence-Key": str(int(datetime.now().timestamp()))
    }
    
    try:
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payment_data,
            headers=headers,
            auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "payment_url": result["confirmation"]["confirmation_url"],
                "payment_id": result["id"]
            }
        else:
            logger.error(f"YooKassa API error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        return {"success": False, "error": str(e)}

def check_payment_status(payment_id: str):
    """Проверяет статус платежа"""
    
    auth = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
    }
    
    try:
        response = requests.get(
            f"https://api.yookassa.ru/v3/payments/{payment_id}",
            headers=headers,
            auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "status": result["status"],
                "paid": result["status"] == "succeeded",
                "metadata": result.get("metadata", {})
            }
        else:
            return {"success": False, "error": response.text}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# МОДИФИЦИРОВАННАЯ ФУНКЦИЯ ПОКАЗА ПАКЕТА
# ============================================

async def show_package_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ПОЛНЫЙ ПАКЕТ с созданием платежа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Создаем платеж
    payment_result = create_payment_link(user_id)
    
    if payment_result["success"]:
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить 690 ₽", url=payment_result["payment_url"])],
            [InlineKeyboardButton("✅ Проверить оплату", callback_data=f"check_{payment_result['payment_id']}")],
            [InlineKeyboardButton("📨 Помощь", url="https://t.me/meysternlp")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]
        ]
        
        message_text = (
            f"<b>💎 ПОЛНЫЙ ПАКЕТ ВАРИАТИКА</b>\n\n"
            f"Сумма: <b>690 ₽</b>\n"
            f"ID платежа: <code>{payment_result['payment_id']}</code>\n\n"
            f"<b>Что входит:</b>\n"
            f"• Полный разбор вашего профиля (15+ страниц детального анализа)\n"
            f"• Персональная терапевтическая сказка для коррекции конфликтующих частей\n"
            f"• Книга «ВАРИАТИКА. Библиотека человеческих паттернов» (.PDF)\n"
            f"• Персональные рекомендации по развитию\n"
            f"• Карта сильных и слабых сторон\n\n"
            f"<b>Как получить файлы:</b>\n"
            f"1. Нажмите '💳 Оплатить 690 ₽'\n"
            f"2. Оплатите в открывшемся окне\n"
            f"3. Нажмите '✅ Проверить оплату'\n"
            f"4. Файлы придут автоматически\n\n"
            f"<i>Проблемы с оплатой? Нажмите '📨 Помощь'</i>"
        )
        
    else:
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_results")]]
        message_text = (
            f"❌ <b>Ошибка создания платежа</b>\n\n"
            f"Попробуйте позже или напишите @meysternlp\n\n"
            f"Ошибка: {payment_result.get('error', 'Неизвестно')[:100]}"
        )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode="HTML")
    return PACKAGE_SCREEN

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка оплаты"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("check_", "")
    
    # Проверяем статус платежа через API
    status_result = check_payment_status(payment_id)
    
    if status_result["success"]:
        if status_result["paid"]:
            # УСПЕШНАЯ ОПЛАТА!
            user_id = status_result["metadata"].get("user_id")
            
            if user_id:
                # Отправляем файлы
                await send_files_after_payment(update, context, int(user_id))
                return ConversationHandler.END
            else:
                await query.edit_message_text(
                    "❌ <b>ОШИБКА</b>\n\n"
                    "Не удалось определить пользователя. Напишите @meysternlp для помощи.",
                    parse_mode="HTML"
                )
                
        elif status_result["status"] == "pending":
            # Ожидание оплаты
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_{payment_id}")],
                [InlineKeyboardButton("📨 Помощь", url="https://t.me/meysternlp")]
            ]
            
            await query.edit_message_text(
                f"⏳ <b>ОЖИДАНИЕ ОПЛАТЫ</b>\n\n"
                f"ID: <code>{payment_id}</code>\n"
                f"Статус: ожидание оплаты\n\n"
                f"Если вы уже оплатили:\n"
                f"1. Подождите 2-3 минуты\n"
                f"2. Проверьте снова\n"
                f"3. Или напишите @meysternlp",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            return PAYMENT_CHECK
            
        else:
            # Неуспешный статус
            await query.edit_message_text(
                f"❌ <b>ПЛАТЕЖ НЕ ОПЛАЧЕН</b>\n\n"
                f"ID: <code>{payment_id}</code>\n"
                f"Статус: {status_result['status']}\n\n"
                f"Создать новый платеж?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Создать новый", callback_data="show_package")],
                    [InlineKeyboardButton("📨 Помощь", url="https://t.me/meysternlp")]
                ]),
                parse_mode="HTML"
            )
            return PAYMENT_CHECK
                
    else:
        await query.edit_message_text(
            f"⚠️ <b>ОШИБКА ПРОВЕРКИ</b>\n\n"
            f"ID: <code>{payment_id}</code>\n"
            f"Ошибка: {status_result.get('error', 'Неизвестно')[:100]}\n\n"
            f"Напишите @meysternlp для помощи",
            parse_mode="HTML"
        )
        return PAYMENT_CHECK

async def send_files_after_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Отправляет файлы после успешной оплаты"""
    query = update.callback_query
    
    # Сообщение об успехе
    await query.edit_message_text(
        "🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n"
        "Отправляю ваши файлы...",
        parse_mode="HTML"
    )
    
    # Отправляем файлы
    for file_name, file_url in PAID_FILES:
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=file_url,
                caption=file_name
            )
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error sending file {file_name}: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Не удалось отправить {file_name}\nСсылка: {file_url}"
            )
    
    # Финальное сообщение
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ <b>ВСЕ ФАЙЛЫ ОТПРАВЛЕНЫ!</b>\n\n"
             "Если нужна консультация:\n"
             "👉 @meysternlp",
        parse_mode="HTML"
    )

# ============================================
# ОСТАЛЬНЫЙ КОД (БЕЗ ИЗМЕНЕНИЙ)
# ============================================

# ВОПРОСЫ ЭТАПА 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ
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
                "1": "Боится близости",
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
                "1": "Не могу выбрать (анализ паралич)",
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

# Таблица баллов для этапа 2 (остается без изменений)
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

# ВОПРОСЫ ЭТАПА 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ (без изменений)
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

# ВОПРОСЫ ЭТАПА 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ (без изменений)
STAGE_4_QUESTIONS = [
    {"id": "q4_1", "text": "Как часто ты чувствуешь, что «что-то не так» в жизни?", "options": {"a": {"text": "Постоянно", "dilts": "IDENTITY"}, "b": {"text": "Часто", "dilts": "VALUES"}, "c": {"text": "Иногда", "dilts": "CAPABILITIES"}, "d": {"text": "Редко или никогда", "dilts": "ENVIRONMENT"}}},
    {"id": "q4_2", "text": "Что именно «не так»?\n\nВыбери то, что ближе всего:", "options": {"a": {"text": "Не то окружение (место, люди, условия)", "dilts": "ENVIRONMENT"}, "b": {"text": "Делаю не то, что хочу", "dilts": "BEHAVIOR"}, "c": {"text": "Не умею делать то, что хочу", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимаю, чего хочу", "dilts": "VALUES"}}},
    {"id": "q4_3", "text": "Человек чувствует себя несчастным.\n\nВ чём, скорее всего, причина?", "options": {"a": {"text": "Не те люди вокруг", "dilts": "ENVIRONMENT"}, "b": {"text": "Делает не то, что хочет", "dilts": "BEHAVIOR"}, "c": {"text": "Не умеет делать то, что хочет", "dilts": "CAPABILITIES"}, "d": {"text": "Не понимает, чего хочет", "dilts": "VALUES"}}},
    {"id": "q4_4", "text": "Если бы ты мог изменить что-то одно, что бы это было?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Своё понимание целей", "dilts": "VALUES"}}},
    {"id": "q4_5", "text": "Что для тебя сложнее всего?", "options": {"a": {"text": "Изменить внешние условия", "dilts": "ENVIRONMENT"}, "b": {"text": "Начать действовать", "dilts": "BEHAVIOR"}, "c": {"text": "Научиться новому", "dilts": "CAPABILITIES"}, "d": {"text": "Понять, чего я хочу", "dilts": "VALUES"}}},
    {"id": "q4_6", "text": "Когда ты застреваешь в проблеме, что обычно не хватает?", "options": {"a": {"text": "Ресурсов (время, деньги, связи)", "dilts": "ENVIRONMENT"}, "b": {"text": "Действий (не начинаю)", "dilts": "BEHAVIOR"}, "c": {"text": "Навыков (не умею)", "dilts": "CAPABILITIES"}, "d": {"text": "Понимания (не знаю зачем)", "dilts": "VALUES"}}},
    {"id": "q4_7", "text": "Что мешает тебе быть счастливым?", "options": {"a": {"text": "Обстоятельства", "dilts": "ENVIRONMENT"}, "b": {"text": "Мои действия", "dilts": "BEHAVIOR"}, "c": {"text": "Мои ограничения", "dilts": "CAPABILITIES"}, "d": {"text": "Я не знаю, что такое счастье", "dilts": "VALUES"}}},
    {"id": "q4_8", "text": "Если бы у тебя была волшебная палочка, что бы ты изменил?", "options": {"a": {"text": "Своё окружение", "dilts": "ENVIRONMENT"}, "b": {"text": "Своё поведение", "dilts": "BEHAVIOR"}, "c": {"text": "Свои способности", "dilts": "CAPABILITIES"}, "d": {"text": "Себя (кто я)", "dilts": "IDENTITY"}}}
]

# Уровни Дилтса (без изменений)
DILTS_LEVELS = {
    "ENVIRONMENT": {"name": "ОКРУЖЕНИЕ", "code": "env", "description": "Проблема во внешних условиях", "solution": "Измени окружение или отношение к нему"},
    "BEHAVIOR": {"name": "ПОВЕДЕНИЕ", "code": "beh", "description": "Проблема в действиях", "solution": "Начни действовать по-другому"},
    "CAPABILITIES": {"name": "СПОСОБНОСТИ", "code": "cap", "description": "Проблема в навыках", "solution": "Освой новые навыки"},
    "VALUES": {"name": "ЦЕННОСТИ", "code": "val", "description": "Проблема в мотивации", "solution": "Найди свои истинные ценности"},
    "IDENTITY": {"name": "ИДЕНТИЧНОСТЬ", "code": "ide", "description": "Проблема в самоопределении", "solution": "Переопредели, кто ты"}
}

# АДАПТИВНЫЕ УТОЧНЯЮЩИЕ ВОПРОСЫ (без изменений)
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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (БЕЗ ИЗМЕНЕНИЙ)
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

def calculate_thinking_level_by_scores(level_scores_dict):
    """Определяет уровень мышления (1-9) по системе баллов"""
    if not level_scores_dict:
        return 1
    
    numeric_scores = {int(k): v for k, v in level_scores_dict.items() if k.isdigit()}
    
    if not numeric_scores:
        return 1
    
    max_score = max(numeric_scores.values())
    max_levels = [level for level, score in numeric_scores.items() if score == max_score]
    
    if not max_levels:
        return 1
    
    return max(max_levels)

def calculate_final_level(stage2_level, stage3_scores):
    """Финальный уровень (приоритет поведению)"""
    if not stage3_scores:
        return stage2_level
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    weighted = stage3_avg * 0.7 + stage2_level * 0.3
    final_level = int(round(weighted))
    
    logger.info(f"Final level: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}, weighted={weighted:.2f}, final={final_level}")
    return final_level

def clean_duplicate_headers(text: str, field_type: str) -> str:
    """Убирает заголовки, которые уже есть в тексте профиля."""
    if not text:
        return ""
    
    lines = text.strip().split('\n')
    if not lines:
        return text
    
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
                lines.pop(0)
                if lines and not lines[0].strip():
                    lines.pop(0)
                break
    
    return '\n'.join(lines).strip()

def format_profile_title(profile_title: str, profile_header: str) -> str:
    """Форматирует заголовок профиля."""
    if not profile_title:
        return f"🎯 {profile_header}"
    
    profile_title = profile_title.strip()
    lines = profile_title.split('\n')
    
    if len(lines) == 1:
        title = lines[0].strip()
        return f"🎯 {profile_header} / {title}"
    
    elif len(lines) >= 2:
        line1 = lines[0].strip()
        line2 = lines[1].strip()
        
        if line2 == profile_header or line2.replace('_', ' ').lower() == profile_header.replace('_', ' ').lower():
            return f"🎯 {profile_header} / {line1}"
        else:
            return f"🎯 {profile_header} / {line1}"
    
    return f"🎯 {profile_header}"

def get_profile_fallback(profile_data: dict) -> VariaticaProfile:
    """
    ИСПРАВЛЕННАЯ ВЕРСИЯ: Находит реально существующий файл профиля.
    Приоритет: точное совпадение → разные суффиксы → без суффикса → любой файл уровня → ближайший уровень
    Поддерживает все типы: SA, SP, IA, IP (с обработкой ip/ip-адрес и ip - адрес)
    """
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    logger.info(f"🎯 FALLBACK ПОИСК: type={type_code}, level={level}, dilts={dilts_code}")
    
    search_types = [type_code]
    
    if type_code == "ip" or type_code == "ip-адрес":
        search_types = ["ip", "ip-адрес", "ip - адрес"]
    elif type_code == "ip - адрес":
        search_types = ["ip - адрес", "ip-адрес", "ip"]
    
    logger.info(f"🔍 Варианты поиска для типа {type_code}: {search_types}")
    
    for search_type in search_types:
        target_key = f"{search_type}_{level}_{dilts_code}"
        profile = loader.get_profile(target_key)
        if profile:
            logger.info(f"✅ Exact match: {target_key}")
            return profile
    
    logger.info(f"🔍 Точное совпадение не найдено для {type_code}_{level}_{dilts_code}")
    
    possible_suffixes = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
    
    for search_type in search_types:
        logger.info(f"🔍 Ищу {search_type}_{level}_* с разными суффиксами")
        
        for suffix in possible_suffixes:
            test_key = f"{search_type}_{level}_{suffix}"
            profile = loader.get_profile(test_key)
            if profile:
                logger.info(f"✅ Найден с суффиксом {suffix}: {test_key}")
                return profile
    
    for search_type in search_types:
        test_key = f"{search_type}_{level}"
        profile = loader.get_profile(test_key)
        if profile:
            logger.info(f"✅ Найден без суффикса: {test_key}")
            return profile
    
    logger.info(f"🔍 Ищу любой профиль *_{level}_* для типа {type_code}")
    all_profiles = loader.get_all_profiles()
    
    all_type_profiles = []
    for key in all_profiles:
        key_lower = key.lower()
        for search_type in search_types:
            if key_lower.startswith(f"{search_type}_"):
                all_type_profiles.append((key, key_lower))
                break
    
    logger.info(f"📚 Все доступные профили типа {type_code} (варианты: {search_types}):")
    for key, key_lower in sorted(all_type_profiles):
        logger.info(f"   - {key}")
    
    same_level_profiles = []
    for key, key_lower in all_type_profiles:
        try:
            parts = key_lower.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                key_level = int(parts[1])
                if key_level == level:
                    same_level_profiles.append(key)
        except (ValueError, IndexError):
            continue
    
    logger.info(f"📊 Профили уровня {level} типа {type_code}: {same_level_profiles}")
    
    if same_level_profiles:
        fallback_key = same_level_profiles[0]
        logger.info(f"✅ Найден профиль уровня {level}: {fallback_key}")
        return loader.get_profile(fallback_key)
    
    logger.info(f"⚠️ Нет профилей уровня {level}, ищу ближайший уровень для типа {type_code}")
    
    available_levels = []
    for key, key_lower in all_type_profiles:
        try:
            parts = key_lower.split('_')
            if len(parts) >= 2 and parts[1].isdigit():
                key_level = int(parts[1])
                available_levels.append((key, key_level))
        except (ValueError, IndexError):
            continue
    
    if not available_levels:
        logger.error(f"❌ НЕТ ПРОФИЛЕЙ для типа {type_code}!")
        emergency_key = "sa_1_def"
        logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
        return loader.get_profile(emergency_key)
    
    min_diff = float('inf')
    best_key = None
    best_level = None
    
    for key, key_level in available_levels:
        diff = abs(key_level - level)
        if diff < min_diff:
            min_diff = diff
            best_key = key
            best_level = key_level
        elif diff == min_diff and key_level > best_level:
            best_key = key
            best_level = key_level
    
    if best_key:
        logger.info(f"📈 Найден ближайший уровень {best_level} (разница {min_diff}): {best_key}")
        return loader.get_profile(best_key)
    
    logger.error(f"🔥 КРИТИЧЕСКАЯ ОШИБКА: Ничего не найдено для типа {type_code}, level={level}")
    emergency_key = "sa_1_def"
    logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
    return loader.get_profile(emergency_key)

def get_card_description_from_profile(profile: VariaticaProfile, profile_data: dict) -> dict:
    """Получает описание профиля с очисткой заголовков"""
    is_new_format = hasattr(profile, 'archetype') and profile.archetype
    
    if is_new_format:
        clean_trigger = clean_duplicate_headers(profile.trigger, 'trigger')
        clean_pain = clean_duplicate_headers(profile.pain, 'pain')
        clean_tool = clean_duplicate_headers(profile.immediate_tool, 'immediate_tool')
        clean_cta = clean_duplicate_headers(profile.cta, 'cta')
        
        return {
            "title": profile.title,
            "archetype": profile.archetype,
            "quote": profile.quote,
            "trigger": clean_trigger,
            "pain": clean_pain,
            "immediate_tool": clean_tool,
            "cta": clean_cta,
            
            "type_code": profile_data['type_code'],
            "level": profile_data['level'],
            "dilts_code": profile_data['dilts_code'],
        }
    else:
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

def calculate_profile_final(context_data: dict) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля"""
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    level_scores_dict = context_data.get("stage2_level_scores_dict", {})
    stage2_level = calculate_thinking_level_by_scores(level_scores_dict)
    
    stage3_scores = context_data.get("stage3_level_scores", [])
    final_level = calculate_final_level(stage2_level, stage3_scores)
    final_level = max(1, min(9, final_level))
    
    dilts_answers = context_data.get("stage4_dilts_answers", [])
    dilts_level = determine_dilts_level(dilts_answers)
    dilts_code = get_dilts_code(dilts_level)
    
    coherence = check_profile_coherence(final_level, dilts_level)
    
    logger.info(f" FINAL PROFILE CALCULATION:")
    logger.info(f"   Type: {type_code} ({perception_type})")
    logger.info(f"   Level: {final_level} ({get_level_name(final_level)})")
    logger.info(f"   Dilts: {dilts_level} ({dilts_code})")
    logger.info(f"   Coherence: {coherence['is_coherent']}")
    
    return {
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dilts_level,
        "dilts_code": dilts_code,
        
        "display_name": f"{type_code}_{final_level}_{dilts_code}",
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        
        "coherence": coherence,
        "stage2_level": stage2_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
    }

def check_profile_coherence(profile_level: int, dilts_level: str) -> dict:
    """Проверяет согласованность уровня профиля и уровня Дилтса"""
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
    
    return {
        "is_coherent": is_coherent,
        "profile_level": profile_level,
        "dilts_level": dilts_level,
        "expected_dilts": expected_dilts
    }

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
    
    sorted_levels = sorted(level_scores_dict.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_levels) >= 2:
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
# ИСПРАВЛЕННЫЙ ЭКРАН РЕЗУЛЬТАТОВ (КОМПАКТНЫЙ)
# ============================================

async def show_results_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН РЕЗУЛЬТАТОВ ТЕСТА - версия 1.9 (исправлен fallback)"""
    query = update.callback_query
    
    has_shared = context.user_data.get("has_shared", False)
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    profile = get_profile_fallback(profile_data)
    
    if not profile:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось найти профиль.\n\nПопробуй пройти тест заново: /start"
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    message_1 = ""
    
    profile_header = f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}"
    raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
    formatted_title = format_profile_title(raw_title, profile_header)
    message_1 += f"<b>{formatted_title}</b>\n\n"
    
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
    
    trigger = profile_card.get('trigger', '')
    if trigger:
        if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
            trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
        
        message_1 += f"<b>🔍 ЭТО ТЫ, ЕСЛИ...</b>\n\n"
        message_1 += f"{trigger}\n\n"
    
    pain = profile_card.get('pain', '')
    if pain:
        pain_lines = pain.strip().split('\n')
        if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
            pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
        
        if pain.strip():
            message_1 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n"
            message_1 += f"{pain.strip()}"
    
    if message_1.strip():
        await query.edit_message_text(message_1.strip(), parse_mode="HTML")
        await asyncio.sleep(0.5)
    
    message_2 = ""
    
    tool = profile_card.get('immediate_tool', '')
    if tool:
        tool_lines = tool.strip().split('\n')
        if tool_lines and any(h in tool_lines[0] for h in ['ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:', 'ПЕРВЫЙ ШАГ / ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»:']):
            tool = '\n'.join(tool_lines[1:]) if len(tool_lines) > 1 else ""
        
        if tool.strip():
            message_2 += f"<b>🛠 ИНСТРУМЕНТ «ПРЯМО СЕЙЧАС»</b>\n\n"
            message_2 += f"{tool.strip()}\n\n"
    
    cta = profile_card.get('cta', '')
    if cta:
        cta_lines = cta.strip().split('\n')
        if cta_lines and cta_lines[0].strip() == 'ЧТО ДАЛЬШЕ?':
            cta = '\n'.join(cta_lines[1:]) if len(cta_lines) > 1 else ""
        
        if cta.strip():
            message_2 += f"<b>🚀 ЧТО ДАЛЬШЕ?</b>\n\n"
            message_2 += f"{cta.strip()}\n\n"
    
    message_2 += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not has_shared:
        message_2 += (
            f"<b>🎁 ПОДАРОК ЗА РЕПОСТ</b>\n"
            f"Поделись тестом с друзьями и получи бонусный материал.\n\n"
        )
    else:
        message_2 += (
            f"<b>🎉 ГОТОВО!</b>\n"
            f"Спасибо за репост! Твой подарок ждёт тебя.\n\n"
        )
    
    if not has_shared:
        keyboard = [
            [InlineKeyboardButton("📤 Поделиться и получить подарок", callback_data="get_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Забрать подарок", callback_data="open_gift")],
            [InlineKeyboardButton("💎 Полный пакет рекомендаций", callback_data="show_package")],
            [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart_test")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
    return RESULTS

# ============================================
# ОСТАЛЬНЫЕ ЭКРАНЫ (БЕЗ ИЗМЕНЕНИЙ)
# ============================================

async def get_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ИНСТРУКЦИЯ ПО ШАРИНГУ"""
    query = update.callback_query
    await query.answer()
    
    instruction_text = (
        f"<b>📤 ШАГ 1: ПОДЕЛИСЬ ССЫЛКОЙ</b>\n\n"
        f"Нажми кнопку ниже, чтобы отправить сообщение с ссылкой на тест.\n\n"
        f"После того как отправишь, вернись сюда и нажми «✅ Я поделился»"
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

async def open_gift_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЭКРАН: ОТКРЫТИЕ ПОДАРКА"""
    query = update.callback_query
    await query.answer()
    
    gift_text = (
        f"<b>🎁 ВАШ ПОДАРОК ГОТОВ!</b>\n\n"
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
# НАЧАЛЬНЫЕ ЭКРАНЫ И КОМАНДЫ (БЕЗ ИЗМЕНЕНИЙ)
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"🎴 <b>Добро пожаловать в психодиагностический тест ВАРИАТИКА ver 2.0!</b>\n\n"
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

# ============================================
# ЭТАПЫ ТЕСТА (БЕЗ ИЗМЕНЕНИЙ - сохраняем все ваши оригинальные функции)
# ============================================

# ЭТАП 1: КОНФИГУРАЦИЯ ВОСПРИЯТИЯ (без изменений)
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

# ЭТАП 2: КОНФИГУРАЦИЯ МЫШЛЕНИЯ (без изменений)
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
        f"🎯 Конфигурация мышления определена\n\n"
        f"🔍 Переходим к <b>ЭТАПУ 3</b>: поведенческие паттерны.\n\n"
        f"Готов продолжить?"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Продолжить", callback_data="show_stage_3_intro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="HTML")
    return STAGE_3

# ЭТАП 3: ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ (без изменений)
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

# ЭТАП 4: КОНФЛИКТ ЛОГИЧЕСКИХ УРОВНЕЙ (без изменений)
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

async def finish_stage_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение ЭТАПА 4"""
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
        
        loading_text = f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\nАнализирую твои ответы и определяю профиль..."
        await query.edit_message_text(loading_text, parse_mode="HTML")
        await asyncio.sleep(2)
        
        return await show_results_screen(update, context)

# ФУНКЦИИ УТОЧНЕНИЙ (без изменений)
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
    
    loading_text = f"⏳ <b>ОБРАБАТЫВАЮ РЕЗУЛЬТАТЫ...</b>\n\nАнализирую твои ответы и определяю профиль..."
    await query.edit_message_text(loading_text, parse_mode="HTML")
    await asyncio.sleep(2)
    
    return await show_results_screen(update, context)

# ============================================
# ОТМЕНА ТЕСТА
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена теста"""
    await update.message.reply_text(
        "❌ Тест отменён.\n\nЧтобы начать заново: /start"
    )
    return ConversationHandler.END

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""
    print("\n" + "="*50)
    print("🚀 ЗАПУСК БОТА ВАРИАТИКА ver 2.0")
    print("="*50)
    print("ОСНОВНЫЕ ИЗМЕНЕНИЯ:")
    print("1. Интеграция с ЮKassa API")
    print("2. Автоматическая отправка файлов после оплаты")
    print("3. Проверка статуса платежей через API")
    print("4. Улучшенный интерфейс оплаты")
    print("="*50 + "\n")
    
    # Проверка загрузки профилей
    print("🔍 ПРОВЕРКА ЗАГРУЗКИ ПРОФИЛЕЙ")
    print("="*30)
    
    all_profiles = loader.get_all_profiles()
    print(f"📊 Всего профилей загружено: {len(all_profiles)}")
    
    # Проверяем профили по типам
    for profile_type in ['sa', 'sp', 'ia', 'ip']:
        type_profiles = [p for p in all_profiles if p.lower().startswith(f"{profile_type}_")]
        print(f"🔍 {profile_type.upper()} профилей: {len(type_profiles)}")
    
    # Тестируем поиск fallback
    test_cases = [
        ("sp", 4, "cap", "sp_4_exp.py"),
        ("ia", 4, "cap", "ia_4_exp.py"),
        ("sa", 4, "cap", "sa_4_exp.py"),
        ("ip", 4, "cap", "ip_4_exp.py"),
        ("sa", 1, "def", "sa_1_def.py"),
        ("ip", 1, "def", "ip_1_def.py"),
    ]
    
    print("\n🧪 Тестируем fallback поиск:")
    for type_code, level, dilts, expected in test_cases:
        test_data = {"type_code": type_code, "level": level, "dilts_code": dilts}
        try:
            profile = get_profile_fallback(test_data)
            status = "✅" if profile else "❌"
            print(f"  {type_code}_{level}_{dilts:3} → {status} {expected}")
        except Exception as e:
            print(f"  {type_code}_{level}_{dilts:3} → ❌ ОШИБКА: {e}")
    
    print("="*30)
    print("✅ Проверка завершена. Запускаю бота...")
    
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
                CallbackQueryHandler(check_payment, pattern="^check_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$")
            ],
            PAYMENT_CHECK: [
                CallbackQueryHandler(check_payment, pattern="^check_"),
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
    
    logger.info("🚀 Bot started: ВАРИАТИКА ver 2.0!")
    logger.info("📊 Changes: Added YooKassa integration for automatic file delivery")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
