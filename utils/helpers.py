"""
Вспомогательные функции
"""

import time
import random
import sys

def calculate_progress(current: int, total: int) -> str:
    """Вычисляет прогресс с прогресс-баром"""
    progress = int((current / total) * 100)
    filled = int(progress / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"Вопрос {current}/{total}\n{bar} {progress}%"

def generate_unique_callback(base: str, user_id: int, *args) -> str:
    """Генерирует уникальный callback_data с контролем длины"""
    short_user = str(user_id)[-4:]
    
    # 🔥 СПЕЦИАЛЬНАЯ ОБРАБОТКА ДЛЯ УТОЧНЯЮЩИХ ВОПРОСОВ
    if base == "clarify" and len(args) >= 3:
        stage = args[0]      # stage1, stage2, etc
        current = args[1]     # номер текущего вопроса
        option = args[2]      # option_id или level
        callback = f"{base}_{stage}_{current}_{option}_{short_user}"
        print(f"🔧 CLARIFY CALLBACK: {callback}", file=sys.stderr)
    else:
        # Для обычных вопросов этапов
        callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
        if len(args) > 2:
            callback += f"_{args[2]}"
        print(f"🔧 STAGE CALLBACK: {callback}", file=sys.stderr)
    
    # Проверка длины (Telegram ограничение 64 байта)
    if len(callback) > 64:
        old_callback = callback
        if base == "clarify":
            callback = f"{base}_{stage}_{current}_{option[:3]}_{short_user}"
        else:
            callback = f"{base}_{args[0]}_{args[1][:5]}_{short_user}"
        print(f"⚠️ TOO LONG! Trimmed: {old_callback} -> {callback}", file=sys.stderr)
    
    return callback
