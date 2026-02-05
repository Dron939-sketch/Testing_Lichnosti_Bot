#!/bin/bash
echo "=========================================="
echo "🚀 ВАРИАТИКА БОТ v2.0 - ЗАПУСК"
echo "=========================================="

# Принудительная установка нужной версии python-telegram-bot
echo "✅ Проверка зависимостей..."
pip install --force-reinstall python-telegram-bot==20.7

echo "✅ Загрузка переменных окружения..."
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "✅ Запуск бота..."
python main.py
