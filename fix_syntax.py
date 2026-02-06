#!/usr/bin/env python3
"""
Скрипт для исправления синтаксической ошибки в bot_adaptive.py
"""

import re

def fix_bot_file():
    with open('bot_adaptive.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Паттерн для поиска незакрытых тройных кавычек
    # Это простое исправление - замена на одинарные кавычки
    fixed_content = re.sub(
        r'""".*?(""")?',
        lambda m: m.group(0) if m.group(1) else m.group(0).replace('"""', "'''", 1),
        content,
        flags=re.DOTALL
    )
    
    # Или просто добавляем закрывающие кавычки
    lines = content.split('\n')
    for i in range(2890, 2910):  # Ищем вокруг проблемной строки
        if i < len(lines):
            line = lines[i]
            if 'Отмена теста' in line:
                print(f"Найдена проблемная строка {i+1}: {line}")
                # Добавляем закрывающие кавычки
                if line.count('"""') % 2 != 0:
                    lines[i] = line + '"""'
    
    fixed_content = '\n'.join(lines)
    
    # Сохраняем исправленную версию
    with open('bot_adaptive_fixed.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Создан файл bot_adaptive_fixed.py")
    return 'bot_adaptive_fixed.py'

if __name__ == '__main__':
    fix_bot_file()
