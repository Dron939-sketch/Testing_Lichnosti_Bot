"""
Пакет обработчиков для всех этапов теста
"""

import logging
logger = logging.getLogger(__name__)

# Импортируем все функции из модулей
from handlers.stage1 import *
from handlers.stage2 import *
from handlers.stage3 import *
from handlers.stage4 import *
from handlers.common import *
from handlers.results import *
from handlers.payment import *
from handlers.gifts import *

# Явно указываем все экспортируемые имена для избежания конфликтов
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

# Логируем успешную загрузку всех обработчиков
logger.info(f"✅ Загружены обработчики: {', '.join(__all__)}")
