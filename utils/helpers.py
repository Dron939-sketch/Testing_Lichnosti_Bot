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
    
    # 🔥 ПОДРОБНОЕ ЛОГИРОВАНИЕ
    print(f"\n🔧 generate_unique_callback CALLED", file=sys.stderr)
    print(f"🔧 base: {base}", file=sys.stderr)
    print(f"🔧 args: {args}", file=sys.stderr)
    print(f"🔧 short_user: {short_user}", file=sys.stderr)
    
    # Для разных типов callback'ов
    if base == "stage1":
        # stage1_current_option_user
        callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    elif base == "stage2":
        # stage2_current_level_user
        callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    elif base == "stage3":
        # stage3_current_option_user
        callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    elif base == "stage4":
        # stage4_current_option_user
        callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    elif base == "clarify":
        # clarify_stage_current_option_user
        if len(args) >= 3:
            callback = f"{base}_{args[0]}_{args[1]}_{args[2]}_{short_user}"
        else:
            callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    else:
        callback = f"{base}_{args[0]}_{args[1]}_{short_user}"
    
    print(f"🔧 FINAL CALLBACK: {callback} (length: {len(callback)})", file=sys.stderr)
    
    # Проверка длины (Telegram лимит 64 байта)
    if len(callback) > 64:
        print(f"⚠️ CALLBACK TOO LONG! {len(callback)} bytes", file=sys.stderr)
        callback = callback[:60]
        print(f"🔧 TRIMMED: {callback}", file=sys.stderr)
    
    return callback
