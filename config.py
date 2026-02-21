"""
Конфигурация приложения для Variatica Bot и Flask API
Содержит все константы и настройки для психологического теста и платежной системы
"""

import os
import logging
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ===== ТОКЕНЫ И КЛЮЧИ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не установлена!")

API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
GIFT_PDF_LINK = os.getenv("GIFT_PDF_LINK", "https://disk.yandex.ru/i/Cacp7x1Vt3XhbA")

# ===== ССЫЛКИ =====
TELEGRAM_BOT_URL = "https://t.me/Testing_Lichnosti_bot"
BOT_LINK = "t.me/Testing_Lichnosti_bot"
AUTHOR_LINK = "@meysternlp"
SHARE_TEXT = "Мне в руки попало особое зеркало. В нём видно то, что обычно скрыто даже от себя.\n\nЯ посмотрел(а). Увидел(а). Теперь держи — твоя очередь смотреть."

# ===== ТЕКСТЫ =====
GIFT_SCREEN_TEXT = """
⚔️ <b>ВАШ МЕЧ ГОТОВ!</b>

📚 <b>Терапевтическая сказка «Мастер Меча»</b>

Эта сказка работает именно с тем, что мешает вам
расправить плечи на уровне убеждений.

<i>Она не «ломает» старые установки,
а создаёт пространство для новых —
тех, что позволяют стоять прямо и легко.</i>

💡 <b>Как читать для максимального эффекта:</b>
1️⃣ Прочитайте перед сном
2️⃣ Ищите в тексте «металл» (вашу истинную природу)
3️⃣ Отмечайте «зазубрины» (ваши ограничения)
4️⃣ Обращайте внимание на символы тяжести/лёгкости

<i>Приятного чтения и лёгкости в плечах!</i> 🪶✨
"""

# ===== СОСТОЯНИЯ CONVERSATIONHANDLER =====
# Синхронизируем с bot_adaptive.py
STAGE_1, STAGE_2, STAGE_3, STAGE_4, CLARIFICATION, RESULTS = range(10, 16)
GIFT_SCREEN, PACKAGE_SCREEN, OPEN_GIFT_SCREEN = range(16, 19)
PAYMENT_SCREEN = 19

# ===== 18+ СОСТОЯНИЯ =====
try:
    from sexual_18_plus import SEXUAL_STATES
    SEXUAL_PROFILE_SCREEN = SEXUAL_STATES["SEXUAL_PROFILE_SCREEN"]
    SEXUAL_INVITES_LIST = SEXUAL_STATES["SEXUAL_INVITES_LIST"]
    SEXUAL_FRIEND_PROFILE = SEXUAL_STATES["SEXUAL_FRIEND_PROFILE"]
    FOUR_F_PAYMENT_SCREEN = SEXUAL_STATES["FOUR_F_PAYMENT_SCREEN"]
    FOUR_F_CONTENT_SCREEN = SEXUAL_STATES["FOUR_F_CONTENT_SCREEN"]
except (ImportError, KeyError):
    # Если модуль не загружен, создаем заглушки
    logger.warning("⚠️ 18+ модуль не загружен, создаем заглушки для состояний")
    SEXUAL_PROFILE_SCREEN = 20
    SEXUAL_INVITES_LIST = 21
    SEXUAL_FRIEND_PROFILE = 22
    FOUR_F_PAYMENT_SCREEN = 23
    FOUR_F_CONTENT_SCREEN = 24

# ===== ПСИХОЛОГИЧЕСКИЕ ПОДСКАЗКИ =====
PSYCHOLOGIST_TIPS = {
    "stage1": [
        "🧠 <i>Не думайте слишком долго — важна первая реакция</i>",
        "🧠 <i>Отвечайте так, как есть сейчас, а не как хотелось бы</i>",
        "🧠 <i>Это безопасное пространство для честности с собой</i>",
        "🧠 <i>Все ответы важны для построения точного профиля</i>",
        "🧠 <i>Чем честнее вы будете, тем точнее будут рекомендации</i>",
        "🧠 <i>Не бывает правильных или неправильных ответов</i>",
        "🧠 <i>Это исследование, а не оценка</i>",
        "🧠 <i>Спасибо за доверие в этом процессе самопознания</i>"
    ],
    "stage2": [
        "🧠 <i>Опишите текущую реальность, а не идеальную ситуацию</i>",
        "🧠 <i>Ваши ответы помогают мне понять ваш внутренний мир</i>",
        "🧠 <i>Будьте максимально искренни — это только для вас</i>",
        "🧠 <i>Каждый ответ добавляет деталь к вашему портрету</i>",
        "🧠 <i>Не оценивайте свои ответы как хорошие или плохие</i>",
        "🧠 <i>Это путь к лучшему пониманию себя</i>",
        "🧠 <i>Ваша честность — ключ к точным инсайтам</i>",
        "🧠 <i>Спасибо за открытость в этом диалоге</i>"
    ],
    "stage3": [
        "🧠 <i>Вспомните реальные реакции, а не идеальные</i>",
        "🧠 <i>Автоматизмы — не хорошо и не плохо, это данные</i>",
        "🧠 <i>Рефлексы показывают ваши глубинные программы</i>",
        "🧠 <i>Чем честнее, тем точнее будет ваш профиль</i>",
        "🧠 <i>Стратегии рождаются из осознания автоматизмов</i>",
        "🧠 <i>Это безопасное пространство для изучения себя</i>",
        "🧠 <i>Каждый ответ — ключ к вашим паттернам</i>",
        "🧠 <i>Благодарю за смелость в этом исследовании</i>"
    ],
    "stage4": [
        "🧠 <i>Выбирайте то, что кажется ближе к правде</i>",
        "🧠 <i>Не задумывайтесь слишком долго — важна первая реакция</i>", 
        "🧠 <i>Нет правильных или неправильных ответов</i>",
        "🧠 <i>Каждый выбор показывает ваши глубинные фокусы</i>",
        "🧠 <i>Это последний этап — собираем все данные воедино</i>",
        "🧠 <i>Ваши ответы определят точку для роста</i>",
        "🧠 <i>Доверяйте своему внутреннему ощущению</i>",
        "🧠 <i>Спасибо за завершение этого исследования</i>"
    ]
}

# ===== МОТИВАЦИОННЫЕ ЭКРАНЫ =====
STAGE1_FEEDBACK = {
    "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": """
✅ ЭТАП 1 ЗАВЕРШЁН

🧠 <b>КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>

Внимание направлено туда, где пульсирует живое — люди, контакты, отношения.
Ваша конфигурация первой замечает смену настроения, паузу в разговоре, взгляд.
Входящий сигнал: «кто рядом и что между нами».

🔍 Что дальше?
Следующий этап — исследование того, как мышление работает внутри этой оптики.

📊 Продолжим?
""",
    "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": """
✅ ЭТАП 1 ЗАВЕРШЁН

🧠 <b>КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>

Внимание направлено внутрь, в слои собственных состояний и смыслов.
Ваша конфигурация не пропускает сигнал, пока он не будет понят, прочувствован, назван.
Входящий сигнал: «что это значит для меня».

🔍 Что дальше?
Следующий этап — исследование того, как мышление работает внутри этой оптики.

📊 Продолжим?
""",
    "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": """
✅ ЭТАП 1 ЗАВЕРШЁН

🧠 <b>КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>

Внимание направлено на цели, ресурсы, препятствия и способы их преодоления.
Ваша конфигурация автоматически сканирует среду на предмет «что здесь можно сделать».
Входящий сигнал: «как это использовать и что с этим делать».

🔍 Что дальше?
Следующий этап — исследование того, как мышление работает внутри этой оптики.

📊 Продолжим?
""",
    "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": """
✅ ЭТАП 1 ЗАВЕРШЁН

🧠 <b>КОНФИГУРАЦИЯ ВОСПРИЯТИЯ</b>

Внимание направлено на закономерности, связи между фактами, логику устройства.
Ваша конфигурация не видит разрозненных событий — только элементы одной системы.
Входящий сигнал: «как это устроено и по каким правилам работает».

🔍 Что дальше?
Следующий этап — исследование того, как мышление работает внутри этой оптики.

📊 Продолжим?
"""
}

STAGE2_FEEDBACK = {
    ("СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ", "1-3"): """
✅ ЭТАП 2 ЗАВЕРШЁН

🧠 <b>КОНФИГУРАЦИЯ МЫШЛЕНИЯ</b>

Мышление внутри вашей системы восприятия настроено на поиск обратной связи.
Его фокус: «как я соотношусь с другими, видим ли я, принят ли?»
Оно собирает информацию через контакт и сверку с окружением.

🔍 Что дальше?
Следующий этап — анализ поведенческих реакций.

📊 Продолжим?
""",
    # ... остальные варианты будут добавлены по мере необходимости
}

STAGE3_FEEDBACK = {
    1: """
✅ ЭТАП 3 ЗАВЕРШЁН

🔄 <b>ПОВЕДЕНЧЕСКАЯ КОНФИГУРАЦИЯ</b>

Реакции разворачиваются на скорости рефлекса.
Сигнал входит — действие выходит.
Пауза между стимулом и ответом не предусмотрена архитектурой.

Это конфигурация прямой проводимости.
Она оптимальна для ситуаций, где скорость критичнее анализа.
Решения принимаются до включения мышления — и это её штатный режим.

🔍 Что дальше?
Финальный этап — определение точки роста.

📊 Продолжим?
""",
    2: """
✅ ЭТАП 3 ЗАВЕРШЁН

🔄 <b>ПОВЕДЕНЧЕСКАЯ КОНФИГУРАЦИЯ</b>

Реакции — это борьба с симптомами.
Вы уже замечаете, что что-то идёт не так, но пока не можете это изменить.
Возникает внутренний конфликт: «знаю, что так не надо, но продолжаю».

Это конфигурация симптоматической борьбы.
Она характерна для этапа, когда осознание уже есть, но автоматизмы сильнее.

🔍 Что дальше?
Финальный этап — определение точки роста.

📊 Продолжим?
""",
    4: """
✅ ЭТАП 3 ЗАВЕРШЁН

🔄 <b>ПОВЕДЕНЧЕСКАЯ КОНФИГУРАЦИЯ</b>

Реакции осознаны и управляемы.
Вы можете выбирать, как реагировать в разных ситуациях.
Автоматизмы не исчезли, но теперь они под контролем.

Это конфигурация паттернов.
Вы не боретесь с симптомами — вы выбираете стратегии.

🔍 Что дальше?
Финальный этап — определение точки роста.

📊 Продолжим?
""",
    6: """
✅ ЭТАП 3 ЗАВЕРШЁН

🔄 <b>ПОВЕДЕНЧЕСКАЯ КОНФИГУРАЦИЯ</b>

Реакции трансформированы в стратегии.
Вы не просто выбираете поведение — вы создаёте новые способы бытия.
Реакции становятся инструментом, а не ограничением.

Это конфигурация стратегий.
Поведение интегрировано с ценностями и идентичностью.

🔍 Что дальше?
Финальный этап — определение точки роста.

📊 Продолжим?
"""
}

STAGE4_ANALYSIS_SCREEN = """
🧠 АНАЛИЗИРУЮ ДАННЫЕ

Соединяются три слоя информации:
▸ Как работает оптика восприятия
▸ Как внутри неё выстраивается мышление
▸ В каком режиме работают поведенческие реакции

Остаётся добавить четвёртый элемент —
уровень, на котором находится текущая точка сборки.

⏳ Пожалуйста, подождите несколько секунд...
"""

# ===== КОНСТАНТЫ ДЛЯ ПОИСКА ПРОФИЛЕЙ =====
STANDARD_SUFFIXES = ['def', 'sit', 'con', 'exp', 'int', 'aut', 'val', 'tra', 'ide']
LEVEL_DIFFS = [0, 1, -1, 2, -2, 3, -3, 4, -4]
EMERGENCY_PROFILES = [
    "sa_1_def", "sa_2_sit", "sa_3_con",
    "sp_1_def", "sp_2_sit", "sp_3_con", 
    "ia_1_def", "ia_2_sit", "ia_3_con",
    "ip_1_def", "ip_2_sit", "ip_3_con"
]

# ===== КОНСТАНТЫ ДЛЯ ПРИМЕЧАНИЙ О КОНФЛИКТЕ =====
CONFLICT_PHRASES = {
    "ENVIRONMENT": {
        "note": "🔥 <b>ПРИМЕЧАНИЕ:</b> Вы пытаетесь быть собой там, где это невозможно. Ваше окружение не подходит вам — оно не даёт опоры, не поддерживает, а часто и давит. Вы не можете реализовать то, что для вас важно, потому что находитесь не в своей среде.",
        "short": "Вы не на своём месте"
    },
    "BEHAVIOR": {
        "note": "🔥 <b>ПРИМЕЧАНИЕ:</b> Вы делаете не то, что для вас действительно важно. Ваши повседневные действия разошлись с тем, чего вы на самом деле хотите. Вы будто живёте не свою жизнь — выполняете чужие сценарии, а свои откладываете.",
        "short": "Вы живёте не свою жизнь"
    },
    "CAPABILITIES": {
        "note": "🔥 <b>ПРИМЕЧАНИЕ:</b> Вы хотите одного, а умеете — другое. Ваших текущих навыков и способностей не хватает, чтобы реализовать то, что для вас важно. Вы застряли между «хочу» и «могу», и этот разрыв нужно закрывать новыми знаниями и опытом.",
        "short": "Вам не хватает навыков"
    },
    "VALUES": {
        "note": "🔥 <b>ПРИМЕЧАНИЕ:</b> Внутри вас конфликт: вы одновременно хотите противоречивых вещей. Одна часть тянет в одну сторону, другая — в противоположную. Из-за этого вы топчетесь на месте и не можете двинуться ни туда, ни сюда.",
        "short": "Вы разрываетесь между разными желаниями"
    },
    "IDENTITY": {
        "note": "🔥 <b>ПРИМЕЧАНИЕ:</b> Вы не соответствуете своему собственному образу. То, кем вы себя считаете, и то, что для вас важно — живут отдельно. Вы как будто играете роль, которая вам не подходит, и это отнимает силы.",
        "short": "Вы играете чужую роль"
    }
}

SUFFIX_TO_DILTS = {
    "def": "ENVIRONMENT",
    "sit": "BEHAVIOR", 
    "con": "CAPABILITIES",
    "exp": "CAPABILITIES",
    "int": "VALUES",
    "aut": "VALUES",
    "val": "VALUES",
    "tra": "IDENTITY",
    "ide": "IDENTITY"
}

# ===== УРОВНИ ДИЛТСА =====
DILTS_LEVELS = {
    "ENVIRONMENT": {"name": "ОКРУЖЕНИЕ", "code": "env", "description": "Проблема во внешних условиях", "solution": "Измени окружение или отношение к нему"},
    "BEHAVIOR": {"name": "ПОВЕДЕНИЕ", "code": "beh", "description": "Проблема в действиях", "solution": "Начни действовать по-другому"},
    "CAPABILITIES": {"name": "СПОСОБНОСТИ", "code": "cap", "description": "Проблема в навыках", "solution": "Освой новые навыки"},
    "VALUES": {"name": "ЦЕННОСТИ", "code": "val", "description": "Проблема в мотивации", "solution": "Найди свои истинные ценности"},
    "IDENTITY": {"name": "ИДЕНТИЧНОСТЬ", "code": "ide", "description": "Проблема в самоопределении", "solution": "Переопредели, кто ты"}
}

# ============================================
# КОНСТАНТЫ ДЛЯ FLASK API (из app.py)
# ============================================

# ===== ССЫЛКИ НА ПРОФИЛИ ЯНДЕКС.ДИСК =====
PROFILE_LINKS = {
    # SA Profiles
    "SA_1_DEF": "https://disk.yandex.ru/d/HAcOfAg1tpIedA",
    "SA_2_SIT": "https://disk.yandex.ru/d/MwdMClX9koCTmA",
    "SA_3_CON": "https://disk.yandex.ru/d/NKN_XemK62t5nA",
    "SA_4_EXP": "https://disk.yandex.ru/d/tTSiN5zhSb8LtA",
    "SA_5_INT": "https://disk.yandex.ru/d/xUdv7bsBT3Wbhg",
    "SA_6_AUT": "https://disk.yandex.ru/d/lYWKaOdEkC_5Ag",
    "SA_7_VAL": "https://disk.yandex.ru/d/7BCOKs-6qS6-5g",
    "SA_8_TRA": "https://disk.yandex.ru/d/SqlDISkse1OEGQ",
    "SA_9_IDE": "https://disk.yandex.ru/d/vGzHmuckInNL5g",
    
    # SP Profiles
    "SP_1_DEF": "https://disk.yandex.ru/d/7nmOP7wR2iQ9YA",
    "SP_2_SIT": "https://disk.yandex.ru/d/Ro_mcLDd_QmilA",
    "SP_3_CON": "https://disk.yandex.ru/d/kUJH3BLMnb4CfA",
    "SP_4_EXP": "https://disk.yandex.ru/d/KBSO1g0HYNJBcQ",
    "SP_5_INT": "https://disk.yandex.ru/d/s2jhq2ngz3pmYg",
    "SP_6_AUT": "https://disk.yandex.ru/d/xWBv4TLFosOB5g",
    "SP_7_VAL": "https://disk.yandex.ru/d/K1whXj6C6KAazQ",
    "SP_8_TRA": "https://disk.yandex.ru/d/ZZhRISNn-GNPTg",
    "SP_9_IDE": "https://disk.yandex.ru/d/jBCaEpYOdZI-JQ",
    
    # IA Profiles
    "IA_1_DEF": "https://disk.yandex.ru/d/M1Y7z175uGKIHg",
    "IA_2_SIT": "https://disk.yandex.ru/d/X3yz6IP0pdRmVQ",
    "IA_3_CON": "https://disk.yandex.ru/d/DCkqqALby9UpFg",
    "IA_4_EXP": "https://disk.yandex.ru/d/aLT8oJBu0EGwLg",
    "IA_5_INT": "https://disk.yandex.ru/d/x0QXWi7MDR7h0g",
    "IA_6_AUT": "https://disk.yandex.ru/d/xRjBzTxYh0v4bg",
    "IA_7_VAL": "https://disk.yandex.ru/d/1fHqhIitNuz_XQ",
    "IA_8_TRA": "https://disk.yandex.ru/d/0wSeHeF_SWZyFw",
    "IA_9_IDE": "https://disk.yandex.ru/d/ub0YpQQgS4g6rQ",
    
    # IP Profiles
    "IP_1_DEF": "https://disk.yandex.ru/d/m-WOQwDdgQxsnQ",
    "IP_2_SIT": "https://disk.yandex.ru/d/aL4VlAQdlaZ-6g",
    "IP_3_CON": "https://disk.yandex.ru/d/N8GG9XbnC3bFhg",
    "IP_4_EXP": "https://disk.yandex.ru/d/54RFOZmGhA4cfA",
    "IP_5_INT": "https://disk.yandex.ru/d/l5iFTIX8-gTycQ",
    "IP_6_AUT": "https://disk.yandex.ru/d/bTo_vcCoC1KU7Q",
    "IP_7_VAL": "https://disk.yandex.ru/d/TMx1VP843bnJQw",
    "IP_8_TRA": "https://disk.yandex.ru/d/e9KfJdLcl3gp7g",
    "IP_9_IDE": "https://disk.yandex.ru/d/ZiQPHJSDrrWZhw"
}

DEFAULT_PROFILE = "SA_1_DEF"  # Профиль по умолчанию

# ============================================
# 18+ МОДУЛЬ - КОНСТАНТЫ
# ============================================
SEXUAL_DEFAULT_PROFILE = "sa_5_int"
SEXUAL_PAYMENT_AMOUNT = 99.00
SEXUAL_PROFILES_DIR = "sexual_18"

# ============================================
# 4F МОДУЛЬ - КОНСТАНТЫ
# ============================================
F4F_BASE_PATH = "профили/4F"
F4F_FUNCTIONS = ["1F", "2F", "3F", "4F"]
F4F_DEFAULT_PROFILE = "sa_4_cap"
F4F_PAYMENT_AMOUNT = 99.00

# ============================================
# НАСТРОЙКИ ПЛАТЕЖЕЙ
# ============================================
PAYMENT_AMOUNT = float(os.getenv('PAYMENT_AMOUNT', '199.00'))
PAYMENT_CURRENCY = os.getenv('PAYMENT_CURRENCY', 'RUB')
PAYMENT_DESCRIPTION = os.getenv('PAYMENT_DESCRIPTION', 'Оплата подписки Variatica')

# ============================================
# URL И ССЫЛКИ ДЛЯ FLASK
# ============================================
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://testing-lichnosti-bot-qyra.onrender.com')
RETURN_URL = os.getenv('RETURN_URL', 'https://t.me/variatica_bot')

# ============================================
# ПРОВЕРКА КОНФИГУРАЦИИ
# ============================================
def validate_config():
    """Проверяет все необходимые настройки"""
    errors = []
    warnings = []
    
    if not TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN не установлен")
    
    if not API_URL:
        warnings.append("API_URL не установлен, используется значение по умолчанию")
    
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        warnings.append("YooKassa ключи не установлены, платежи будут работать через Flask API")
    
    if errors:
        error_msg = "\n".join(errors)
        logger.error(f"❌ Ошибки конфигурации:\n{error_msg}")
        raise ValueError(f"Ошибки конфигурации: {', '.join(errors)}")
    
    if warnings:
        for warning in warnings:
            logger.warning(f"⚠️ {warning}")
    
    logger.info("✅ Конфигурация проверена успешно")
    return True

# Выполняем проверку при импорте
validate_config()

# Экспортируем все константы
__all__ = [
    # Основные
    'TOKEN', 'API_URL', 'YOOKASSA_SHOP_ID', 'YOOKASSA_SECRET_KEY', 'GIFT_PDF_LINK',
    'TELEGRAM_BOT_URL', 'BOT_LINK', 'AUTHOR_LINK', 'SHARE_TEXT', 'GIFT_SCREEN_TEXT',
    
    # Состояния бота
    'STAGE_1', 'STAGE_2', 'STAGE_3', 'STAGE_4', 'CLARIFICATION', 'RESULTS',
    'GIFT_SCREEN', 'PACKAGE_SCREEN', 'OPEN_GIFT_SCREEN', 'PAYMENT_SCREEN',
    'SEXUAL_PROFILE_SCREEN', 'SEXUAL_INVITES_LIST', 'SEXUAL_FRIEND_PROFILE',
    'FOUR_F_PAYMENT_SCREEN', 'FOUR_F_CONTENT_SCREEN',
    
    # Психологические константы
    'PSYCHOLOGIST_TIPS', 'STAGE1_FEEDBACK', 'STAGE2_FEEDBACK', 'STAGE3_FEEDBACK',
    'STAGE4_ANALYSIS_SCREEN', 'STANDARD_SUFFIXES', 'LEVEL_DIFFS', 'EMERGENCY_PROFILES',
    'CONFLICT_PHRASES', 'SUFFIX_TO_DILTS', 'DILTS_LEVELS',
    
    # Flask API константы
    'PROFILE_LINKS', 'DEFAULT_PROFILE',
    'SEXUAL_DEFAULT_PROFILE', 'SEXUAL_PAYMENT_AMOUNT', 'SEXUAL_PROFILES_DIR',
    'F4F_BASE_PATH', 'F4F_FUNCTIONS', 'F4F_DEFAULT_PROFILE', 'F4F_PAYMENT_AMOUNT',
    'PAYMENT_AMOUNT', 'PAYMENT_CURRENCY', 'PAYMENT_DESCRIPTION',
    'WEBHOOK_URL', 'RETURN_URL',
    
    # Логгер
    'logger'
]

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 ПРОВЕРКА КОНФИГУРАЦИИ VARIATICA")
    print("="*80)
    
    print(f"✅ TELEGRAM_BOT_TOKEN: {'Установлен' if TOKEN else '❌ ОТСУТСТВУЕТ!'}")
    print(f"✅ API_URL: {API_URL}")
    print(f"✅ WEBHOOK_URL: {WEBHOOK_URL}")
    print(f"✅ YOOKASSA_SHOP_ID: {'Установлен' if YOOKASSA_SHOP_ID else 'Не установлен'}")
    print(f"✅ YOOKASSA_SECRET_KEY: {'Установлен' if YOOKASSA_SECRET_KEY else 'Не установлен'}")
    print(f"✅ PAYMENT_AMOUNT: {PAYMENT_AMOUNT} {PAYMENT_CURRENCY}")
    
    print("\n📊 СОСТОЯНИЯ БОТА:")
    print(f"   STAGE_1: {STAGE_1}")
    print(f"   STAGE_2: {STAGE_2}")
    print(f"   STAGE_3: {STAGE_3}")
    print(f"   STAGE_4: {STAGE_4}")
    print(f"   RESULTS: {RESULTS}")
    
    print("\n📁 ПРОФИЛИ ЯНДЕКС.ДИСК:")
    print(f"   Всего профилей: {len(PROFILE_LINKS)}")
    print(f"   Профиль по умолчанию: {DEFAULT_PROFILE}")
    print(f"   Пример: {DEFAULT_PROFILE} -> {PROFILE_LINKS[DEFAULT_PROFILE][:50]}...")
    
    print("\n🔞 18+ МОДУЛЬ:")
    print(f"   Профиль по умолчанию: {SEXUAL_DEFAULT_PROFILE}")
    print(f"   Стоимость: {SEXUAL_PAYMENT_AMOUNT}₽")
    print(f"   Папка: {SEXUAL_PROFILES_DIR}")
    
    print("\n🔑 4F МОДУЛЬ:")
    print(f"   Функции: {F4F_FUNCTIONS}")
    print(f"   Стоимость: {F4F_PAYMENT_AMOUNT}₽")
    print(f"   Базовая папка: {F4F_BASE_PATH}")
    print(f"   MVP профиль: {F4F_DEFAULT_PROFILE}")
    
    print("\n📝 ПСИХОЛОГИЧЕСКИЕ ПОДСКАЗКИ:")
    print(f"   stage1: {len(PSYCHOLOGIST_TIPS['stage1'])} шт.")
    print(f"   stage2: {len(PSYCHOLOGIST_TIPS['stage2'])} шт.")
    print(f"   stage3: {len(PSYCHOLOGIST_TIPS['stage3'])} шт.")
    print(f"   stage4: {len(PSYCHOLOGIST_TIPS['stage4'])} шт.")
    
    print("\n✅ Конфигурация загружена успешно!")
    print("="*80)
