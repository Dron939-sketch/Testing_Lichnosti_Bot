# utils/profile_utils.py
"""
Функции для работы с профилями и их поиском
"""

import logging
from config import STANDARD_SUFFIXES, LEVEL_DIFFS, EMERGENCY_PROFILES, SUFFIX_TO_DILTS, CONFLICT_PHRASES, logger
from loader import loader

class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

def get_profile_fallback(profile_data: dict):
    """Упрощенная логика поиска профиля"""
    from base import VariaticaProfile
    
    type_code = profile_data.get('type_code', 'sa').lower()
    level = profile_data.get('level', 1)
    dilts_code = profile_data.get('dilts_code', 'def').lower()
    
    logger.info(f"🔍 ПОИСК ПРОФИЛЯ: type={type_code}, level={level}, dilts={dilts_code}")
    
    search_order = []
    if dilts_code in STANDARD_SUFFIXES:
        search_order.append(dilts_code)
    search_order.extend(STANDARD_SUFFIXES)
    search_order = list(dict.fromkeys(search_order))
    
    logger.info(f"📋 Порядок поиска суффиксов: {search_order}")
    
    for suffix in search_order:
        profile_key = f"{type_code}_{level}_{suffix}"
        profile = loader.get_profile(profile_key)
        if profile:
            logger.info(f"✅ Найден профиль: {profile_key}")
            return profile
    
    logger.warning(f"⚠️ Не найдено профилей для {type_code}_{level}_*")
    
    for diff in LEVEL_DIFFS:
        test_level = level + diff
        if 1 <= test_level <= 9:
            for suffix in STANDARD_SUFFIXES:
                profile_key = f"{type_code}_{test_level}_{suffix}"
                profile = loader.get_profile(profile_key)
                if profile:
                    logger.info(f"✅ Найден на уровне {test_level} (разница {diff}): {profile_key}")
                    return profile
    
    logger.error(f"❌ Не найдено профилей типа {type_code} на уровнях 1-9")
    
    for emergency_key in EMERGENCY_PROFILES:
        profile = loader.get_profile(emergency_key)
        if profile:
            logger.warning(f"🚨 Использую аварийный профиль: {emergency_key}")
            return profile
    
    error_msg = f"Не найден профиль для type={type_code}, level={level}"
    logger.critical(f"💥 {error_msg}")
    raise ProfileNotFoundError(error_msg)

def get_discrepancy_note(profile_data: dict, actual_profile_key: str) -> str:
    """Возвращает примечание о конфликте Дилтса"""
    if not actual_profile_key:
        logger.warning("⚠️ get_discrepancy_note: actual_profile_key отсутствует")
        return ""
    
    try:
        key_lower = actual_profile_key.lower()
        logger.info(f"🔍 Поиск суффикса в ключе: {key_lower}")
        
        found_suffix = None
        for suffix in STANDARD_SUFFIXES:
            if f"_{suffix}" in key_lower or key_lower.startswith(f"{suffix}_") or key_lower.endswith(f"_{suffix}") or key_lower == suffix:
                found_suffix = suffix
                logger.info(f"✅ Найден суффикс: {found_suffix}")
                break
        
        if found_suffix:
            dilts_level = SUFFIX_TO_DILTS.get(found_suffix, "ENVIRONMENT")
            conflict_phrase = CONFLICT_PHRASES.get(dilts_level, {})
            note = conflict_phrase.get("note", "")
            
            if note:
                logger.info(f"✅ Сформировано примечание о конфликте: суффикс={found_suffix}, dilts={dilts_level}")
                return f"{note}\n\n"
            else:
                return f"🔥 Примечание: Обнаружено несоответствие в вашем профиле.\n\n"
        
        logger.info(f"❌ Суффикс не найден в ключе: {key_lower}")
        return ""
        
    except Exception as e:
        logger.error(f"❌ Ошибка в get_discrepancy_note: {e}", exc_info=True)
        return ""

__all__ = [
    'ProfileNotFoundError',
    'get_profile_fallback',
    'get_discrepancy_note'
]
