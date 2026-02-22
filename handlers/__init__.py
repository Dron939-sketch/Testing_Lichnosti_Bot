"""
Пакет обработчиков для всех этапов теста
Версия 3.0 с расширенной диагностикой и универсальным логированием
"""

# ===== АВАРИЙНАЯ ДИАГНОСТИКА =====
import sys
import os
from datetime import datetime

print("\n" + "🚨"*50, file=sys.stderr)
print(f"🚨 handlers/__init__.py ЗАГРУЖАЕТСЯ в {datetime.now()}", file=sys.stderr)
print(f"🚨 Текущий файл: {__file__}", file=sys.stderr)
print(f"🚨 Рабочая директория: {os.getcwd()}", file=sys.stderr)
print("🚨"*50 + "\n", file=sys.stderr)
sys.stderr.flush()
# =================================

import logging
import sys
import traceback
from typing import List, Dict, Any, Optional

# Настройка логирования для пакета
logger = logging.getLogger(__name__)

# ===== УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ЛОГИРОВАНИЯ =====
def log_debug(msg: str, user_id: Optional[int] = None, level: str = "INFO"):
    """Записывает логи в несколько мест для надежности"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    user_part = f"[USER:{user_id}]" if user_id else ""
    log_msg = f"📋 {timestamp} {user_part} {msg}"
    
    # В stderr
    print(log_msg, file=sys.stderr, flush=True)
    
    # В файл
    log_path = '/tmp/bot_handlers.log'
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} {user_part} {msg}\n")
    except:
        pass
    
    # В logger
    if level == "INFO":
        logger.info(msg)
    elif level == "DEBUG":
        logger.debug(msg)
    elif level == "WARNING":
        logger.warning(msg)
    elif level == "ERROR":
        logger.error(msg)

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
    log_debug(f"📦 Попытка импорта из {module_name}...")
    
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
                    log_debug(f"  ✅ {func_name} загружена")
                else:
                    log_debug(f"  ⚠️ {func_name} не найдена в {module_name}", level="WARNING")
            except Exception as e:
                log_debug(f"  ❌ Ошибка при импорте {func_name}: {e}", level="ERROR")
        
        log_debug(f"✅ Загружено {len(result)}/{len(functions)} функций из {module_name}")
        return result
        
    except ImportError as e:
        log_debug(f"❌ Модуль {module_name} не найден: {e}", level="ERROR")
        log_debug(traceback.format_exc(), level="DEBUG")
        return {}
    except Exception as e:
        log_debug(f"❌ Непредвиденная ошибка при импорте {module_name}: {e}", level="ERROR")
        log_debug(traceback.format_exc(), level="DEBUG")
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

print("\n" + "="*70, file=sys.stderr)
print("🔍 ЗАГРУЗКА ПАКЕТА HANDLERS", file=sys.stderr)
print("="*70, file=sys.stderr)

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
    print(f"{status} {module_name}: {len(imported)}/{len(functions)} функций", file=sys.stderr)

print("-" * 70, file=sys.stderr)
print(f"📊 ИТОГО: {successful_imports}/{total_functions} функций загружено", file=sys.stderr)
print("=" * 70 + "\n", file=sys.stderr)

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
    
    for func_name in __all__:
        if func_name not in _imported_functions or _imported_functions[func_name] is None:
            missing.append(func_name)
    
    if missing:
        log_debug(f"⚠️ Отсутствуют функции: {', '.join(missing)}", level="WARNING")
        return False
    else:
        log_debug("✅ Все функции успешно импортированы")
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
    
    # diagnostic
    'log_debug',
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ
# ============================================================================

# Проверяем импорты
all_imported = check_imports()

# Логируем итоги
log_debug(f"📊 Пакет handlers загружен. Всего функций: {len(__all__)}")
log_debug(f"📋 Первые 10 функций: {', '.join(__all__[:10])}")

if not all_imported:
    log_debug("⚠️ Некоторые функции отсутствуют. Проверьте логи выше.", level="WARNING")

# Для отладки в консоли
print("\n" + "="*70, file=sys.stderr)
print("📋 СПИСОК ЭКСПОРТИРУЕМЫХ ФУНКЦИЙ:", file=sys.stderr)
print("-" * 70, file=sys.stderr)
for i, func_name in enumerate(__all__, 1):
    status = "✅" if _imported_functions.get(func_name) else "❌"
    print(f"{status} {i:2d}. {func_name}", file=sys.stderr)
print("="*70 + "\n", file=sys.stderr)

# Финальное сообщение
print(f"\n🚀 ПАКЕТ HANDLERS УСПЕШНО ЗАГРУЖЕН в {datetime.now()}\n", file=sys.stderr)
