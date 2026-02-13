# utils/validators.py
"""
Функции для проверки необходимости уточнений
"""

from collections import Counter

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
    """Определяет, нужны ли уточнения после этапа 2"""
    if not level_scores_dict:
        return False
    
    level_groups = {0: 0, 1: 0, 2: 0}
    
    for level_str, score in level_scores_dict.items():
        level = int(level_str)
        group = (level - 1) // 3
        level_groups[group] = level_groups.get(group, 0) + score
    
    sorted_groups = sorted(level_groups.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_groups) >= 2:
        first_score = sorted_groups[0][1]
        second_score = sorted_groups[1][1]
        
        return abs(first_score - second_score) < 5
    
    return False

def need_clarification_stage3(stage2_level, stage3_scores):
    """Определяет, нужны ли уточнения после этапа 3"""
    if not stage3_scores or len(stage3_scores) < 4:
        return False
    
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    
    return abs(stage2_level - stage3_avg) > 3

def need_clarification_stage4(dilts_answers):
    """Нужны ли уточнения после ЭТАПА 4"""
    if not dilts_answers:
        return False
    
    counter = Counter(dilts_answers)
    most_common = counter.most_common(2)
    if len(most_common) >= 2:
        return most_common[0][1] == most_common[1][1]
    return False
