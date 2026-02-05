#!/bin/bash
# install_deps.sh - установка правильных зависимостей

echo "Удаляем текущую версию python-telegram-bot..."
pip uninstall -y python-telegram-bot

echo "Устанавливаем python-telegram-bot версии 20.7..."
pip install python-telegram-bot==20.7

echo "Устанавливаем остальные зависимости..."
pip install requests==2.31.0 python-dotenv==1.0.0

echo "Проверяем версии..."
python -c "
import telegram
import requests
print(f'✅ python-telegram-bot: {telegram.__version__}')
print(f'✅ requests: {requests.__version__}')
"
