# simple_server.py
import os
import sys

# Просто перенаправляем на app.py
if __name__ == '__main__':
    # Проверяем что app.py существует
    if os.path.exists('app.py'):
        print("🚀 Перенаправление на app.py...")
        os.execvp('python', ['python', 'app.py'])
    else:
        print("❌ Ошибка: app.py не найден!")
        sys.exit(1)
