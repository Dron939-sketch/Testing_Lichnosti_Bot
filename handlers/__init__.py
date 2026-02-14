"""
Пакет обработчиков для всех этапов теста
Версия 2.0 с расширенной диагностикой
"""

import logging
import sys
import traceback
from typing import List, Dict, Any

# Настройка логирования для пакета
logger = logging.getLogger(__name__)

def safe_import(module_name: str, functions: List[str]) -> Dict[str, Any]:
    """
    Безопасный импорт функций из модуля с диагностикой
    
    Args:
        module_name: имя модуля (например, 'handlers.stage1')
        functions: список импортируемых функций
    
    Returns:
        словарь {имя_функции: функция} или пустой словарь при ошибке
    """
    result = {}
    logger.info(f"📦 Попытка импорта из {module_name}...")
    
    try:
        # Динамический импорт модуля
        __import__(module_name)
        module = sys.modules[module_name]
        
        # Импортируем каждую функцию
        for func_name in functions:
            try:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    result[func_name] = func
                    logger.debug(f"  ✅ {func_name} загружена")
                else:
                    logger.warning(f"  ⚠️ {func_name} не найдена в {module_name}")
            except Exception as e:
                logger.error(f"  ❌ Ошибка при импорте {func_name}: {e}")
        
        logger.info(f"✅ Загружено {len(result)}/{len(functions)} функций из {module_name}")
        return result
        
    except ImportError as e:
        logger.error(f"❌ Модуль {module_name} не найден: {e}")
        logger.debug(traceback.format_exc())
        return {}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при импорте {module_name}: {e}")
        logger.debug(traceback.format_exc())
        return {}

# ============================================================================
# СПИСКИ ФУНКЦИЙ ДЛЯ КАЖДОГО МОДУЛЯ
# ============================================================================

STAGE1_FUNCTIONS = [
    'show_stage_1_intro', 'show_stage_1_details', 'back_to_stage1_intro',
    'start_stage_1', 'ask_stage_1_question', 'handle_stage_1_answer', 'finish_stage_1'
]

STAGE2_FUNCTIONS = [
    'show_stage_2_intro', 'show_stage_2_details', 'back_to_stage2_intro',
    'start_stage_2', 'ask_stage_2_question', 'handle_stage_2_answer', 'finish_stage_2'
]

STAGE3_FUNCTIONS = [
    'show_stage_3_intro', 'show_stage_3_details', 'back_to_stage3_intro',
    'start_stage_3', 'ask_stage_3_question', 'handle_stage_3_answer', 'finish_stage_3'
]

STAGE4_FUNCTIONS = [
    'show_stage_4_intro', 'show_stage_4_details', 'back_to_stage4_intro',
    'start_stage_4', 'ask_stage_4_question', 'handle_stage_4_answer', 'finish_stage_4'
]

COMMON_FUNCTIONS = [
    'ask_clarification_question', 'handle_clarification_answer'
]

RESULTS_FUNCTIONS = [
    'show_results_screen', 'back_to_results', 'back_to_results_after_gift',
    'skip_share', 'confirm_share', 'restart_test'
]

PAYMENT_FUNCTIONS = [
    'buy_command', 'buy_without_test_callback', 'show_payment_screen',
    'check_payment_callback', 'get_materials_callback_payment',
    'materials_command', 'status_command'
]

GIFTS_FUNCTIONS = [
    'get_gift_screen', 'open_gift_screen', 'show_package_screen'
]

# ============================================================================
# ИМПОРТ ВСЕХ МОДУЛЕЙ
# ============================================================================

print("\n" + "="*70)
print("🔍 ЗАГРУЗКА ПАКЕТА HANDLERS")
print("="*70)

# Словарь для хранения всех импортированных функций
_imported_functions = {}

# Импортируем функции из каждого модуля
modules_to_import = [
    ('handlers.stage1', STAGE1_FUNCTIONS),
    ('handlers.stage2', STAGE2_FUNCTIONS),
    ('handlers.stage3', STAGE3_FUNCTIONS),
    ('handlers.stage4', STAGE4_FUNCTIONS),
    ('handlers.common', COMMON_FUNCTIONS),
    ('handlers.results', RESULTS_FUNCTIONS),
    ('handlers.payment', PAYMENT_FUNCTIONS),
    ('handlers.gifts', GIFTS_FUNCTIONS),
]

total_functions = 0
successful_imports = 0

for module_name, functions in modules_to_import:
    imported = safe_import(module_name, functions)
    _imported_functions.update(imported)
    total_functions += len(functions)
    successful_imports += len(imported)
    
    # Выводим статус
    status = "✅" if len(imported) == len(functions) else "⚠️"
    print(f"{status} {module_name}: {len(imported)}/{len(functions)} функций")

print("-" * 70)
print(f"📊 ИТОГО: {successful_imports}/{total_functions} функций загружено")
print("=" * 70 + "\n")

# ============================================================================
# ЯВНОЕ ОБЪЯВЛЕНИЕ ВСЕХ ФУНКЦИЙ В ГЛОБАЛЬНОЙ ОБЛАСТИ
# ============================================================================

# Stage 1
show_stage_1_intro = _imported_functions.get('show_stage_1_intro')
show_stage_1_details = _imported_functions.get('show_stage_1_details')
back_to_stage1_intro = _imported_functions.get('back_to_stage1_intro')
start_stage_1 = _imported_functions.get('start_stage_1')
ask_stage_1_question = _imported_functions.get('ask_stage_1_question')
handle_stage_1_answer = _imported_functions.get('handle_stage_1_answer')
finish_stage_1 = _imported_functions.get('finish_stage_1')

# Stage 2
show_stage_2_intro = _imported_functions.get('show_stage_2_intro')
show_stage_2_details = _imported_functions.get('show_stage_2_details')
back_to_stage2_intro = _imported_functions.get('back_to_stage2_intro')
start_stage_2 = _imported_functions.get('start_stage_2')
ask_stage_2_question = _imported_functions.get('ask_stage_2_question')
handle_stage_2_answer = _imported_functions.get('handle_stage_2_answer')
finish_stage_2 = _imported_functions.get('finish_stage_2')

# Stage 3
show_stage_3_intro = _imported_functions.get('show_stage_3_intro')
show_stage_3_details = _imported_functions.get('show_stage_3_details')
back_to_stage3_intro = _imported_functions.get('back_to_stage3_intro')
start_stage_3 = _imported_functions.get('start_stage_3')
ask_stage_3_question = _imported_functions.get('ask_stage_3_question')
handle_stage_3_answer = _imported_functions.get('handle_stage_3_answer')
finish_stage_3 = _imported_functions.get('finish_stage_3')

# Stage 4
show_stage_4_intro = _imported_functions.get('show_stage_4_intro')
show_stage_4_details = _imported_functions.get('show_stage_4_details')
back_to_stage4_intro = _imported_functions.get('back_to_stage4_intro')
start_stage_4 = _imported_functions.get('start_stage_4')
ask_stage_4_question = _imported_functions.get('ask_stage_4_question')
handle_stage_4_answer = _imported_functions.get('handle_stage_4_answer')
finish_stage_4 = _imported_functions.get('finish_stage_4')

# Common
ask_clarification_question = _imported_functions.get('ask_clarification_question')
handle_clarification_answer = _imported_functions.get('handle_clarification_answer')

# Results
show_results_screen = _imported_functions.get('show_results_screen')
back_to_results = _imported_functions.get('back_to_results')
back_to_results_after_gift = _imported_functions.get('back_to_results_after_gift')
skip_share = _imported_functions.get('skip_share')
confirm_share = _imported_functions.get('confirm_share')
restart_test = _imported_functions.get('restart_test')

# Payment
buy_command = _imported_functions.get('buy_command')
buy_without_test_callback = _imported_functions.get('buy_without_test_callback')
show_payment_screen = _imported_functions.get('show_payment_screen')
check_payment_callback = _imported_functions.get('check_payment_callback')
get_materials_callback_payment = _imported_functions.get('get_materials_callback_payment')
materials_command = _imported_functions.get('materials_command')
status_command = _imported_functions.get('status_command')

# Gifts
get_gift_screen = _imported_functions.get('get_gift_screen')
open_gift_screen = _imported_functions.get('open_gift_screen')
show_package_screen = _imported_functions.get('show_package_screen')

# ============================================================================
# ПРОВЕРКА ИМПОРТОВ
# ============================================================================

def check_imports():
    """Проверяет, что все необходимые функции импортированы"""
    missing = []
    
    # Проверяем все функции из __all__
    for func_name in __all__:
        if func_name not in _imported_functions or _imported_functions[func_name] is None:
            missing.append(func_name)
    
    if missing:
        logger.warning(f"⚠️ Отсутствуют функции: {', '.join(missing)}")
        return False
    else:
        logger.info("✅ Все функции успешно импортированы")
        return True

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # stage1
    'show_stage_1_intro', 'show_stage_1_details', 'back_to_stage1_intro',
    'start_stage_1', 'ask_stage_1_question', 'handle_stage_1_answer', 'finish_stage_1',
    
    # stage2
    'show_stage_2_intro', 'show_stage_2_details', 'back_to_stage2_intro',
    'start_stage_2', 'ask_stage_2_question', 'handle_stage_2_answer', 'finish_stage_2',
    
    # stage3
    'show_stage_3_intro', 'show_stage_3_details', 'back_to_stage3_intro',
    'start_stage_3', 'ask_stage_3_question', 'handle_stage_3_answer', 'finish_stage_3',
    
    # stage4
    'show_stage_4_intro', 'show_stage_4_details', 'back_to_stage4_intro',
    'start_stage_4', 'ask_stage_4_question', 'handle_stage_4_answer', 'finish_stage_4',
    
    # common
    'ask_clarification_question', 'handle_clarification_answer',
    
    # results
    'show_results_screen', 'back_to_results', 'back_to_results_after_gift',
    'skip_share', 'confirm_share', 'restart_test',
    
    # payment
    'buy_command', 'buy_without_test_callback', 'show_payment_screen',
    'check_payment_callback', 'get_materials_callback_payment',
    'materials_command', 'status_command',
    
    # gifts
    'get_gift_screen', 'open_gift_screen', 'show_package_screen',
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ
# ============================================================================

# Проверяем импорты
all_imported = check_imports()

# Логируем итоги
logger.info(f"📊 Пакет handlers загружен. Всего функций: {len(__all__)}")
logger.info(f"📋 Первые 10 функций: {', '.join(__all__[:10])}")

if not all_imported:
    logger.warning("⚠️ Некоторые функции отсутствуют. Проверьте логи выше.")

# Для отладки в консоли
print("\n" + "="*70)
print("📋 СПИСОК ЭКСПОРТИРУЕМЫХ ФУНКЦИЙ:")
print("-" * 70)
for i, func_name in enumerate(__all__, 1):
    status = "✅" if _imported_functions.get(func_name) else "❌"
    print(f"{status} {i:2d}. {func_name}")
print("="*70 + "\n")
