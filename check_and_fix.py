# check_and_fix.py
import os
import sys
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_syntax():
    """Проверяет синтаксис bot_adaptive.py"""
    print("🔍 Проверяю синтаксис bot_adaptive.py...")
    
    try:
        # Попробуем скомпилировать
        with open('bot_adaptive.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Компилируем для проверки синтаксиса
        compile(code, 'bot_adaptive.py', 'exec')
        print("✅ Синтаксис bot_adaptive.py корректен")
        return True
        
    except SyntaxError as e:
        print(f"❌ Синтаксическая ошибка: {e}")
        print(f"   Файл: {e.filename}")
        print(f"   Строка: {e.lineno}")
        print(f"   Позиция: {e.offset}")
        
        # Показываем проблемную строку
        with open('bot_adaptive.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if e.lineno <= len(lines):
            problematic_line = lines[e.lineno - 1].rstrip()
            print(f"   Проблемная строка: '{problematic_line}'")
            
            # Показываем контекст
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            print(f"\n   Контекст (строки {start+1}-{end}):")
            for i in range(start, end):
                prefix = ">>> " if i == e.lineno - 1 else "    "
                print(f"{prefix}{i+1:4}: {lines[i].rstrip()}")
        
        return False

def fix_bot_file():
    """Исправляет синтаксические ошибки в bot_adaptive.py"""
    print("\n🔧 Исправляю bot_adaptive.py...")
    
    with open('bot_adaptive.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes = []
    
    # ФИКС 1: Проблемная функция clean_duplicate_headers
    # Ищем паттерн: def clean_duplicate_headers(...):
    #               (пустая строка)
    #               Русский текст без кавычек
    #               """
    pattern1 = r'(def clean_duplicate_headers\([^)]+\) -> str:\s*\n)\s*\n(\s*[А-Яа-яЁё].*?\n)\s*(""")'
    
    if re.search(pattern1, content, re.DOTALL):
        print("✅ Найдена проблема 1: clean_duplicate_headers")
        content = re.sub(
            pattern1,
            r'\1    """\n\2    """',
            content,
            flags=re.DOTALL
        )
        fixes.append("clean_duplicate_headers")
    
    # ФИКС 2: Проверяем другие функции с похожими проблемами
    pattern2 = r'def (\w+)\([^)]*\)(?: -> \w+)?:\s*\n\s*\n(\s*[А-Яа-яЁё])'
    matches = re.findall(pattern2, content)
    for func_name, _ in matches:
        print(f"⚠️  Возможная проблема в функции: {func_name}")
    
    # ФИКС 3: Проверяем незакрытые тройные кавычки
    # Считаем количество """ в каждой строке
    lines = content.split('\n')
    for i, line in enumerate(lines):
        count = line.count('"""')
        if count % 2 != 0:  # Нечетное количество
            print(f"⚠️  Строка {i+1}: нечетное количество кавычек: {count}")
            print(f"   Строка: '{line[:50]}...'")
    
    # Сохраняем исправленный файл
    with open('bot_adaptive_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Исправления применены: {fixes}")
    print("✅ Создан файл: bot_adaptive_fixed.py")
    
    return 'bot_adaptive_fixed.py'

def create_backup():
    """Создает резервную копию"""
    import shutil
    if os.path.exists('bot_adaptive.py'):
        shutil.copy2('bot_adaptive.py', 'bot_adaptive_backup.py')
        print("✅ Резервная копия создана: bot_adaptive_backup.py")

if __name__ == '__main__':
    print("="*60)
    print("🛠  ИНСТРУМЕНТ ПРОВЕРКИ И ИСПРАВЛЕНИЯ")
    print("="*60)
    
    create_backup()
    
    if check_syntax():
        print("\n✅ Файл bot_adaptive.py корректен.")
        print("🚀 Запускаю run_bot_simple.py...")
        os.system('python run_bot_simple.py')
    else:
        print("\n⚠️  Найдены синтаксические ошибки.")
        answer = input("Исправить автоматически? (y/n): ").strip().lower()
        
        if answer == 'y':
            fixed_file = fix_bot_file()
            print(f"\n🚀 Запускаю исправленную версию: {fixed_file}")
            
            # Модифицируем run_bot_simple.py чтобы использовать исправленный файл
            with open('run_bot_simple.py', 'r', encoding='utf-8') as f:
                run_content = f.read()
            
            # Заменяем импорт
            run_content = run_content.replace(
                'from bot_adaptive import main as bot_main',
                f'from {fixed_file.replace(".py", "")} import main as bot_main'
            )
            
            with open('run_bot_simple_fixed.py', 'w', encoding='utf-8') as f:
                f.write(run_content)
            
            print("✅ Создан run_bot_simple_fixed.py")
            os.system('python run_bot_simple_fixed.py')
        else:
            print("❌ Исправление отменено.")
