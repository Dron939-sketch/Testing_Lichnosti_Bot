# utils/calculations.py
"""
Функции для расчета профиля и уровней
"""

import logging
from collections import Counter
from questions import PERCEPTION_TYPES
from config import logger

def determine_perception_type(scores):
    """Определяет тип восприятия"""
    # Старые баллы по осям
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    # Прямые баллы за типы (из новых вопросов)
    sp = scores.get("SP", 0)
    ip = scores.get("IP", 0)
    ia = scores.get("IA", 0)
    sa = scores.get("SA", 0)
    
    # Логируем для наглядности
    logger.info(f"📊 Прямые баллы: SP={sp}, IP={ip}, IA={ia}, SA={sa}")
    
    # Если есть прямые баллы, они имеют приоритет
    if sp + ip + ia + sa > 0:
        # Взвешенная сумма: прямые баллы имеют вес 2, осевые - вес 1
        sp_total = sp * 2 + external + material
        ip_total = ip * 2 + internal + material
        ia_total = ia * 2 + internal + symbolic
        sa_total = sa * 2 + external + symbolic
        
        totals = {"SP": sp_total, "IP": ip_total, "IA": ia_total, "SA": sa_total}
        dominant = max(totals, key=totals.get)
        
        logger.info(f"🎯 Взвешенные баллы: {totals}, доминанта: {dominant}")
        
        # Маппинг доминантного типа на комбинацию осей
        type_to_axes = {
            "SP": ("EXTERNAL", "MATERIAL"),
            "IP": ("INTERNAL", "MATERIAL"),
            "IA": ("INTERNAL", "SYMBOLIC"),
            "SA": ("EXTERNAL", "SYMBOLIC")
        }
        
        focus, anxiety = type_to_axes[dominant]
        
    else:
        # Старая логика, если прямых баллов нет
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
        "ENVIRONMENT": "def",
        "BEHAVIOR": "sit",
        "CAPABILITIES": "con",
        "VALUES": "val",
        "IDENTITY": "ide"
    }
    return dilts_map.get(dilts_level, "def")

def determine_dilts_level(dilts_answers):
    """Определяет уровень Дилтса"""
    if not dilts_answers:
        return "ENVIRONMENT"
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(1)[0]
    return most_common[0]

def get_level_group(level: int) -> str:
    """Определяет группу уровней (1-3, 4-6, 7-9)"""
    if level <= 3:
        return "1-3"
    elif level <= 6:
        return "4-6"
    else:
        return "7-9"

def calculate_thinking_level_by_scores(level_scores_dict):
    """Определяет уровень мышления (1-9)"""
    if not level_scores_dict:
        return 1
    
    numeric_scores = {int(k): v for k, v in level_scores_dict.items() if k.isdigit()}
    
    if not numeric_scores:
        return 1
    
    max_score = max(numeric_scores.values())
    max_levels = [level for level, score in numeric_scores.items() if score == max_score]
    
    if not max_levels:
        return 1
    
    return min(max_levels)

def calculate_final_level(stage2_level, stage3_scores):
    """Финальный уровень с приоритетом поведению"""
    if not stage3_scores:
        return stage2_level
    
    if len(stage3_scores) == 0:
        return stage2_level
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    
    if stage3_avg > stage2_level + 2:
        stage3_avg = stage2_level + 2
    if stage3_avg < stage2_level - 2:
        stage3_avg = stage2_level - 2
    
    weighted = stage3_avg * 0.6 + stage2_level * 0.4
    final_level = int(round(weighted))
    
    final_level = max(1, min(9, final_level))
    
    logger.info(f"Final level: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}, weighted={weighted:.2f}, final={final_level}")
    return final_level

def check_profile_coherence(profile_level: int, dilts_level: str, actual_suffix: str = None) -> dict:
    """Проверяет согласованность уровня профиля и уровня Дилтса"""
    expected_dilts_by_level = {
        1: ["ENVIRONMENT"],
        2: ["BEHAVIOR"],
        3: ["CAPABILITIES"],
        4: ["BEHAVIOR", "CAPABILITIES"],
        5: ["CAPABILITIES", "VALUES"],
        6: ["VALUES"],
        7: ["VALUES", "IDENTITY"],
        8: ["IDENTITY"],
        9: ["IDENTITY"]
    }
    
    expected_dilts = expected_dilts_by_level.get(profile_level, ["VALUES"])
    is_coherent = dilts_level in expected_dilts
    
    return {
        "is_coherent": is_coherent,
        "profile_level": profile_level,
        "dilts_level": dilts_level,
        "expected_dilts": expected_dilts,
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
    
    # 👇 НОВОЕ: учитываем clarification_scores
    clarification_scores = context_data.get("clarification_scores", {})
    if clarification_scores:
        avg_clarification = sum(clarification_scores.values()) / len(clarification_scores)
        logger.info(f"📊 clarification_scores: {clarification_scores}, avg={avg_clarification:.2f}")
        # Корректируем уровень с учетом уточнений (с небольшим весом)
        final_level = int(round(final_level * 0.8 + avg_clarification * 0.2))
        final_level = max(1, min(9, final_level))
        logger.info(f"📊 После clarification: final_level={final_level}")
    
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
        "clarification_avg": (sum(clarification_scores.values()) / len(clarification_scores)) if clarification_scores else None,
    }
