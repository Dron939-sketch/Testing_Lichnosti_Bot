def get_profile_by_level_and_type(profile_data: dict) -> tuple[VariaticaProfile, dict]:
    """
    НОВАЯ ФУНКЦИЯ: Находит профиль только по типу и уровню.
    Суффикс файла определяется по уровню через LEVEL_TO_SUFFIX.
    
    Возвращает: (профиль, метаданные_поиска)
    """
    # 1. Нормализация типа (решаем проблему ip-адрес)
    type_code = profile_data.get('type_code', 'sa').lower()
    
    if type_code in ["ip", "ip-адрес", "ip - адрес"]:
        normalized_type = "ip"
    elif type_code == "иа":  # русская буква
        normalized_type = "ia"
    elif type_code == "ср":  # русская буква
        normalized_type = "sp"
    elif type_code == "са":  # русская буква
        normalized_type = "sa"
    else:
        normalized_type = type_code
    
    # 2. Получаем уровень (1-9)
    level = profile_data.get('level', 1)
    level = max(1, min(9, level))  # ограничиваем 1-9
    
    # 3. Суффикс ТОЛЬКО по уровню (игнорируем Дилтс!)
    suffix = LEVEL_TO_SUFFIX.get(level, "def")
    
    # 4. Формируем имя профиля
    profile_name = f"{normalized_type}_{level}_{suffix}"
    
    # 5. Пробуем найти точный профиль
    profile = loader.get_profile(profile_name)
    
    # 6. Если не нашли, ищем fallback
    search_metadata = {
        "requested_type": normalized_type,
        "requested_level": level,
        "requested_suffix": suffix,
        "requested_dilts": profile_data.get('dilts_level', 'ENVIRONMENT'),
        "found_profile": None,
        "actual_suffix": None,
        "actual_dilts": None,
        "is_exact_match": False,
        "used_fallback": False
    }
    
    if profile:
        search_metadata.update({
            "found_profile": profile_name,
            "actual_suffix": suffix,
            "actual_dilts": SUFFIX_TO_DILTS.get(suffix, "ENVIRONMENT"),
            "is_exact_match": True
        })
        return profile, search_metadata
    
    # 7. Fallback: пробуем другие суффиксы
    fallback_suffixes = ["def", "sit", "con", "exp", "int", "aut", "val", "tra", "ide"]
    
    for fallback_suffix in fallback_suffixes:
        fallback_name = f"{normalized_type}_{level}_{fallback_suffix}"
        profile = loader.get_profile(fallback_name)
        
        if profile:
            search_metadata.update({
                "found_profile": fallback_name,
                "actual_suffix": fallback_suffix,
                "actual_dilts": SUFFIX_TO_DILTS.get(fallback_suffix, "ENVIRONMENT"),
                "is_exact_match": False,
                "used_fallback": True
            })
            return profile, search_metadata
    
    # 8. Если уровень 4 и тип sp, но нет val, используем exp
    if level == 4 and normalized_type == "sp" and suffix == "val":
        exp_name = "sp_4_exp"
        profile = loader.get_profile(exp_name)
        if profile:
            search_metadata.update({
                "found_profile": exp_name,
                "actual_suffix": "exp",
                "actual_dilts": "CAPABILITIES",
                "is_exact_match": False,
                "used_fallback": True
            })
            return profile, search_metadata
    
    # 9. Если вообще ничего не нашли, возвращаем дефолтный
    default_name = "sa_1_def"
    profile = loader.get_profile(default_name)
    
    search_metadata.update({
        "found_profile": default_name,
        "actual_suffix": "def",
        "actual_dilts": "ENVIRONMENT",
        "is_exact_match": False,
        "used_fallback": True
    })
    
    return profile, search_metadata
