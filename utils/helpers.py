# utils/helpers.py
"""
Вспомогательные функции
"""

import time
import random

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"Вопрос {current}/{total}\n{bar} {progress}%"

def generate_unique_callback(base: str, user_id: int, *args) -> str:
    """Генерирует уникальный callback_data с контролем длины"""
    # Короткий user_id (последние 4 цифры)
    short_user = str(user_id)[-4:]
    
    # Формируем базовый callback
    callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    
    # Если есть дополнительные аргументы (не критично)
    if len(args) > 2:
        callback += f"_{args[2]}"
    
    # Проверка длины
    if len(callback) > 64:
        # Укорачиваем, убирая лишнее
        callback = f"{base}_{args[0]}_{args[1][:5]}_{short_user}"
    
    return callback
