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
    """Генерирует уникальный callback_data"""
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
    parts = [base] + [str(arg) for arg in args] + [str(user_id)[-4:], str(timestamp)[-4:], random_suffix]
    return "_".join(parts)
