#!/bin/bash
# render_build.sh - принудительная установка версии 20.7

echo "=== УСТАНОВКА ЗАВИСИМОСТЕЙ ==="

# Удаляем все версии
pip uninstall -y python-telegram-bot python-telegram-bot[job-queue]

# Принудительно устанавливаем версию 20.7
echo "Устанавливаем python-telegram-bot==20.7..."
pip install "python-telegram-bot[job-queue]==20.7"

# Остальные зависимости
pip install requests==2.31.0 python-dotenv==1.0.0

# Проверяем
echo "=== ПРОВЕРКА ВЕРСИЙ ==="
python -c "
import telegram
print(f'✅ python-telegram-bot: {telegram.__version__}')
print(f'Ожидаем: 20.7')
if not telegram.__version__.startswith('20.'):
    print('❌ НЕПРАВИЛЬНАЯ ВЕРСИЯ!')
    exit(1)
else:
    print('✅ Версия корректна')
"

echo "=== ЗАПУСК БОТА ==="
python bot_adaptive.py
