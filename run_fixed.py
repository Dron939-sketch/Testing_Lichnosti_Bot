#!/usr/bin/env python3
"""
ИСПРАВЛЕННЫЙ ЗАПУСК БОТА
"""

import os
import sys

# Добавляем путь к исходникам
sys.path.append(os.path.dirname(__file__))

# Импортируем и исправляем проблему
from telegram.ext import CommandHandler

# Переопределяем CommandHandler с исправлением
def FixedCommandHandler(command, callback):
    """Исправленная версия CommandHandler"""
    return CommandHandler(command, callback)

# Монтируем исправление
import bot_adaptive

# Заменяем ошибочный вызов в bot_adaptive
import inspect

# Получаем исходный код bot_adaptive.py
with open('bot_adaptive.py', 'r', encoding='utf-8') as f:
    source = f.read()

# Исправляем строку 1496
lines = source.split('\n')
if len(lines) > 1495:  # Python нумерует с 0
    # Найдем и исправим строку с CommandHandler
    for i, line in enumerate(lines):
        if 'CommandHandler("start"' in line and i >= 1490:
            print(f"Найдена проблема на строке {i+1}:")
            print(f"До: {lines[i]}")
            
            # Исправляем
            if 'start_command' in line:
                # Убедимся, что есть запятая
                if not line.strip().endswith(','):
                    lines[i] = line.rstrip() + ','
                    print(f"После: {lines[i]}")
            
            break

# Запускаем исправленный бота
if __name__ == "__main__":
    bot_adaptive.main()
