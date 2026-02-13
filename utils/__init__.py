# utils/__init__.py
"""
Пакет утилит для расчетов и вспомогательных функций
"""

# calculations
from utils.calculations import (
    determine_perception_type,
    get_type_code,
    get_level_name,
    get_dilts_code,
    determine_dilts_level,
    get_level_group,
    calculate_thinking_level_by_scores,
    calculate_final_level,
    check_profile_coherence,
    calculate_profile_final
)

# validators
from utils.validators import (
    need_clarification_stage1,
    need_clarification_stage2,
    need_clarification_stage3,
    need_clarification_stage4
)

# helpers
from utils.helpers import (
    calculate_progress,
    generate_unique_callback
)

# profile_utils
from utils.profile_utils import (
    ProfileNotFoundError,
    get_profile_fallback,
    get_discrepancy_note
)

# text_utils
from utils.text_utils import (
    clean_duplicate_headers,
    format_profile_title,
    get_card_description_from_profile
)

__all__ = [
    # calculations
    'determine_perception_type',
    'get_type_code',
    'get_level_name',
    'get_dilts_code',
    'determine_dilts_level',
    'get_level_group',
    'calculate_thinking_level_by_scores',
    'calculate_final_level',
    'check_profile_coherence',
    'calculate_profile_final',
    
    # validators
    'need_clarification_stage1',
    'need_clarification_stage2',
    'need_clarification_stage3',
    'need_clarification_stage4',
    
    # helpers
    'calculate_progress',
    'generate_unique_callback',
    
    # profile_utils
    'ProfileNotFoundError',
    'get_profile_fallback',
    'get_discrepancy_note',
    
    # text_utils
    'clean_duplicate_headers',
    'format_profile_title',
    'get_card_description_from_profile'
]
