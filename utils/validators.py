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
    
    # 🔥 ИЗМЕНЕНО: учитываем прямые баллы SP/IP/IA/SA
    sp = scores.get("SP", 0)
    ip = scores.get("IP", 0)
    ia = scores.get("IA", 0)
    sa = scores.get("SA", 0)
    
    # Если есть прямые баллы, они имеют приоритет
    if sp + ip + ia + sa > 0:
        # Если есть явный лидер с отрывом
        direct_scores = [sp, ip, ia, sa]
        sorted_direct = sorted(direct_scores, reverse=True)
        if sorted_direct[0] - sorted_direct[1] >= 2:
            return False
    
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
    
    # 🔥 ИЗМЕНЕНО: теперь ожидаем 8 вопросов (было 8)
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
    
    # 🔥 ИЗМЕНЕНО: теперь ожидаем 8 вопросов
    if len(dilts_answers) < 8:
        logger.debug(f"❌ Неполный набор ответов: {len(dilts_answers)}/8")
        return True
    
    # Подсчитываем частоту каждого уровня Дилтса
    counter = Counter(dilts_answers)
    most_common = counter.most_common(2)
    
    # Если есть хотя бы два уровня с одинаковой частотой
    if len(most_common) >= 2:
        return most_common[0][1] == most_common[1][1]
    
    return False

# 🔥 НОВАЯ ФУНКЦИЯ: проверка необходимости уточнений для стратегий
def need_clarification_strategies(strategy_levels: dict) -> bool:
    """
    Проверяет, нужны ли уточнения для стратегий
    Возвращает True, если есть противоречия
    """
    if not strategy_levels:
        return False
    
    # Проверяем, все ли стратегии имеют данные
    for strategy in ["СБ", "ТФ", "УБ", "ЧВ"]:
        if strategy not in strategy_levels or not strategy_levels[strategy]:
            logger.debug(f"❌ Нет данных для стратегии {strategy}")
            return True
    
    # Проверяем на слишком близкие значения (коктейль неясен)
    values = [sum(strategy_levels[s]) / len(strategy_levels[s]) if strategy_levels[s] else 0 
              for s in ["СБ", "ТФ", "УБ", "ЧВ"]]
    
    # Сортируем по убыванию
    sorted_values = sorted(values, reverse=True)
    
    # Если первая и вторая стратегии слишком близки (разница < 0.5)
    if sorted_values[0] - sorted_values[1] < 0.5:
        logger.debug(f"❌ Слишком близкие значения: {sorted_values[0]:.1f} vs {sorted_values[1]:.1f}")
        return True
    
    return False

# 🔥 НОВАЯ ФУНКЦИЯ: проверка согласованности этапов
def check_stages_coherence(context_data: dict) -> list:
    """
    Проверяет согласованность между этапами
    Возвращает список предупреждений
    """
    warnings = []
    
    # Получаем данные
    perception_type = context_data.get("perception_type")
    strategy_levels = context_data.get("strategy_levels", {})
    behavioral_levels = context_data.get("behavioral_levels", {})
    dilts_counts = context_data.get("dilts_counts", {})
    
    # Проверяем соответствие доминанты
    if perception_type and strategy_levels:
        # Маппинг восприятия на стратегии
        type_to_strategy = {
            "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ": "ЧВ",
            "ЭКЗИСТЕНЦИАЛЬНО-РЕФЛЕКСИВНЫЙ": "УБ",
            "ИНСТРУМЕНТАЛЬНО-ДОСТИЖЕНЧЕСКИЙ": "СБ",
            "СТРУКТУРНО-АНАЛИТИЧЕСКИЙ": "ТФ"
        }
        
        expected_strategy = type_to_strategy.get(perception_type)
        
        if expected_strategy:
            # Находим стратегию с максимальным уровнем
            all_values = {}
            for s in ["СБ", "ТФ", "УБ", "ЧВ"]:
                values = strategy_levels.get(s, []) + behavioral_levels.get(s, [])
                if values:
                    all_values[s] = sum(values) / len(values)
            
            if all_values:
                dominant = max(all_values.items(), key=lambda x: x[1])[0]
                
                if dominant != expected_strategy:
                    warnings.append(f"⚠️ Доминанта восприятия ({perception_type}) не совпадает с доминантой стратегий ({dominant})")
    
    return warnings
