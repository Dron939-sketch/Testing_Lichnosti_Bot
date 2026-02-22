"""
Функции для проверки необходимости уточнений
"""

import logging
from collections import Counter

logger = logging.getLogger(__name__)

def need_clarification_stage1(scores):
    """
    Нужны ли уточнения после ЭТАПА 1
    Возвращает список типов уточнений или False, если уточнения не нужны
    """
    external = scores.get("EXTERNAL", 0)
    internal = scores.get("INTERNAL", 0)
    symbolic = scores.get("SYMBOLIC", 0)
    material = scores.get("MATERIAL", 0)
    
    clarifications = []
    
    # Если разница между external и internal <= 2, нужно уточнение
    if abs(external - internal) <= 2:
        clarifications.append("external_internal")
    
    # Если разница между symbolic и material <= 2, нужно уточнение
    if abs(symbolic - material) <= 2:
        clarifications.append("symbolic_material")
    
    return clarifications if clarifications else False

def need_clarification_stage2(level_scores_dict):
    """
    Определяет, нужны ли уточнения после этапа 2
    Возвращает True, если нужны, иначе False
    """
    if not level_scores_dict:
        return False
    
    # Группируем уровни: 1-3, 4-6, 7-9
    level_groups = {0: 0, 1: 0, 2: 0}
    
    for level_str, score in level_scores_dict.items():
        level = int(level_str)
        group = (level - 1) // 3
        level_groups[group] = level_groups.get(group, 0) + score
    
    # Сортируем группы по убыванию баллов
    sorted_groups = sorted(level_groups.items(), key=lambda x: x[1], reverse=True)
    
    # Если есть хотя бы две группы с баллами
    if len(sorted_groups) >= 2:
        first_score = sorted_groups[0][1]
        second_score = sorted_groups[1][1]
        
        # Если разница между первой и второй группой меньше 5 баллов
        return abs(first_score - second_score) < 5
    
    return False

def need_clarification_stage3(stage2_level, stage3_scores):
    """
    Определяет, нужны ли уточнения после этапа 3
    Возвращает True, если нужны, иначе False
    """
    # Если нет ответов - это ошибка, нужны уточнения
    if not stage3_scores:
        logger.debug("❌ stage3_scores пуст, уточнения нужны")
        return True
    
    # Если не все 8 вопросов отвечены
    if len(stage3_scores) < 8:
        logger.debug(f"❌ Неполный набор ответов: {len(stage3_scores)}/8")
        return True
    
    # Проверяем на противоречия (слишком большой разброс)
    if max(stage3_scores) - min(stage3_scores) > 4:
        logger.debug(f"❌ Слишком большой разброс: {min(stage3_scores)}-{max(stage3_scores)}")
        return True
    
    # Проверяем на несоответствие с stage2_level
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    if abs(stage2_level - stage3_avg) > 2:
        logger.debug(f"❌ Несоответствие: stage2={stage2_level}, stage3_avg={stage3_avg:.2f}")
        return True
    
    logger.debug("✅ Уточнения не нужны")
    return False

def need_clarification_stage4(dilts_answers):
    """
    Нужны ли уточнения после ЭТАПА 4
    Возвращает True, если нужны, иначе False
    """
    if not dilts_answers:
        return False
    
    # Подсчитываем частоту каждого уровня Дилтса
    counter = Counter(dilts_answers)
    most_common = counter.most_common(2)
    
    # Если есть хотя бы два уровня с одинаковой частотой
    if len(most_common) >= 2:
        return most_common[0][1] == most_common[1][1]
    
    return False
