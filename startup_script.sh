#!/bin/bash
echo "🚀 Запуск бота ВАРИАТИКА..."

# Проверяем Python
echo "🐍 Python version: $(python --version)"

# Сначала проверяем и исправляем
if [ -f "check_and_fix.py" ]; then
    python check_and_fix.py
elif [ -f "run_bot_simple.py" ]; then
    python run_bot_simple.py
else
    echo "❌ Файлы запуска не найдены!"
    echo "📁 Список файлов:"
    ls -la
fi
