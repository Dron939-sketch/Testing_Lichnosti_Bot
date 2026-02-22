"""
Функции для проверки необходимости уточнений
"""

from collections import Counter

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
    
    # 👇 ВАЖНО: возвращаем False если список пуст
    # Пустой список в Python оценивается как True в условии if, поэтому возвращаем False
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
    if not stage3_scores or len(stage3_scores) < 4:
        return False
    
    # Вычисляем средний уровень поведения
    stage3_avg = sum(stage3_scores) / len(stage3_scores)
    
    # Если разница между мышлением и поведением больше 3 уровней
    return abs(stage2_level - stage3_avg) > 3

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
