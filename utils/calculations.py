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

# 🔥 НОВАЯ ФУНКЦИЯ: рассчитывает уровни всех 4 стратегий
def calculate_strategy_levels(context_data: dict) -> dict:
    """Рассчитывает уровни всех 4 стратегий (СБ, ТФ, УБ, ЧВ)"""
    
    strategy_levels = context_data.get("strategy_levels", {})
    behavioral_levels = context_data.get("behavioral_levels", {})
    
    result = {}
    
    for strategy in ["СБ", "ТФ", "УБ", "ЧВ"]:
        # Собираем все значения из этапа 2 и этапа 3
        values = strategy_levels.get(strategy, []) + behavioral_levels.get(strategy, [])
        
        if values:
            # Вычисляем среднее
            avg = sum(values) / len(values)
            result[strategy] = round(avg, 1)
        else:
            # Если данных нет, используем значение по умолчанию
            result[strategy] = 3.0
    
    logger.info(f"📊 ИТОГОВЫЕ УРОВНИ СТРАТЕГИЙ: {result}")
    return result

# 🔥 НОВАЯ ФУНКЦИЯ: рассчитывает координаты в системе Воображение vs Ограничения
def calculate_coordinates(strategy_levels: dict) -> dict:
    # x = ограничения (чем выше ТФ и УБ, тем больше ограничений)
    x = (strategy_levels.get("ТФ", 3) + strategy_levels.get("УБ", 3)) / 2
    
    # y = воображение (чем выше УБ и ЧВ, тем больше воображения)
    y = (strategy_levels.get("УБ", 3) + strategy_levels.get("ЧВ", 3)) / 2
    
    # Нормализуем к шкале 0-10
    x = min(10, max(0, x * 1.5))
    y = min(10, max(0, y * 1.5))
    
    # ✅ ПРИНУДИТЕЛЬНОЕ ФОРМАТИРОВАНИЕ С ТОЧКОЙ
    x_str = f"{x:.1f}".replace(',', '.')
    y_str = f"{y:.1f}".replace(',', '.')
    
    return {
        "x": float(x_str),
        "y": float(y_str)
    }

# 🔥 НОВАЯ ФУНКЦИЯ: определяет доминанту по уровням стратегий
def determine_dominant_from_levels(strategy_levels: dict) -> str:
    """Определяет доминирующую стратегию по максимальному уровню"""
    
    if not strategy_levels:
        return "ЧВ"  # значение по умолчанию
    
    dominant = max(strategy_levels.items(), key=lambda x: x[1])[0]
    return dominant

# 🔥 НОВАЯ ФУНКЦИЯ: конвертирует уровень 1-6 в уровень 1-9 для Вариатики
def convert_to_var_level(level: float) -> int:
    """Конвертирует уровень 1-6 в уровень 1-9 для Вариатики"""
    
    level_map = {
        1: 1, 1.5: 2,
        2: 2, 2.5: 3,
        3: 3, 3.5: 4,
        4: 4, 4.5: 5,
        5: 6, 5.5: 7,
        6: 8, 6.0: 9
    }
    
    # Находим ближайший ключ
    closest = min(level_map.keys(), key=lambda x: abs(x - level))
    return level_map[closest]

# 🔥 ИЗМЕНЕНО: обновлённая финальная функция расчёта
def calculate_profile_final(context_data: dict) -> dict:
    """ФИНАЛЬНЫЙ алгоритм расчета профиля"""
    
    # 1. Базовый тип восприятия (из этапа 1)
    perception_type = context_data.get("perception_type", "СОЦИАЛЬНО-АФФИЛИАТИВНЫЙ")
    type_code = get_type_code(perception_type)
    
    # 2. Уровни всех 4 стратегий
    strategy_levels = calculate_strategy_levels(context_data)
    
    # 3. Доминирующая стратегия
    dominant_strategy = determine_dominant_from_levels(strategy_levels)
    
    # 4. Уровень доминанты
    dom_level = strategy_levels[dominant_strategy]
    
    # 5. Уровень мышления из этапа 2 (оригинальные вопросы)
    level_scores_dict = context_data.get("stage2_level_scores_dict", {})
    thinking_level = calculate_thinking_level_by_scores(level_scores_dict)
    
    # 6. Поведенческий уровень из этапа 3
    stage3_scores = context_data.get("stage3_level_scores", [])
    final_level = calculate_final_level(thinking_level, stage3_scores)
    
    # 7. Корректировка с учётом уточнений
    clarification_scores = context_data.get("clarification_scores", {})
    if clarification_scores:
        avg_clarification = sum(clarification_scores.values()) / len(clarification_scores)
        logger.info(f"📊 clarification_scores: {clarification_scores}, avg={avg_clarification:.2f}")
        final_level = int(round(final_level * 0.8 + avg_clarification * 0.2))
        final_level = max(1, min(9, final_level))
        logger.info(f"📊 После clarification: final_level={final_level}")
    
    # 8. Проблемный уровень Дилтса из этапа 4
    dilts_answers = context_data.get("stage4_dilts_answers", [])
    dilts_counts = context_data.get("dilts_counts", {})
    
    if dilts_counts:
        dominant_dilts = max(dilts_counts.items(), key=lambda x: x[1])[0]
    else:
        dominant_dilts = determine_dilts_level(dilts_answers)
    
    dilts_code = get_dilts_code(dominant_dilts)
    
    # 9. Конвертация в уровень Вариатики
    var_level = convert_to_var_level(dom_level)
    
    # 10. Координаты
    coordinates = calculate_coordinates(strategy_levels)
    
    # 11. Согласованность
    coherence = check_profile_coherence(final_level, dominant_dilts)
    
    # 12. Итоговый код профиля
    # Маппинг русских названий на коды
    dom_to_code = {
        "СБ": "SP",
        "ТФ": "IP",
        "УБ": "IA",
        "ЧВ": "SA"
    }
    dom_code = dom_to_code.get(dominant_strategy, type_code)
    
    profile_code = f"{dom_code}_{var_level}_{dilts_code}"
    
    logger.info(f" FINAL PROFILE CALCULATION:")
    logger.info(f"   Type: {perception_type} → {type_code}")
    logger.info(f"   Dominant: {dominant_strategy} = {dom_level}")
    logger.info(f"   Var Level: {var_level}")
    logger.info(f"   Dilts: {dominant_dilts} → {dilts_code}")
    logger.info(f"   Profile code: {profile_code}")
    x_val = coordinates["x"]
    y_val = coordinates["y"]
    logger.info(f"   Coordinates: {{'x': {x_val:.1f}, 'y': {y_val:.1f}}}".replace(',', '.'))
    
    return {
        "type_code": type_code,
        "level": final_level,
        "dilts_level": dominant_dilts,
        "dilts_code": dilts_code,
        "display_name": profile_code.upper(),
        "level_name": get_level_name(final_level),
        "type_name": perception_type,
        "coherence": coherence,
        
        # Новые поля
        "dominant_strategy": dominant_strategy,
        "dominant_level": dom_level,
        "strategy_levels": strategy_levels,
        "coordinates": coordinates,
        "var_level": var_level,
        "profile_code": profile_code,
        
        # Для обратной совместимости
        "stage2_level": thinking_level,
        "stage3_avg": (sum(stage3_scores) / len(stage3_scores)) if stage3_scores else None,
        "clarification_avg": (sum(clarification_scores.values()) / len(clarification_scores)) if clarification_scores else None,
    }
