#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ИСПРАВЛЕННЫЙ ЗАПУСК БОТА ДЛЯ RENDER
"""

import os
import sys
import asyncio

print("="*50)
print("🚀 ЗАПУСК RUN_FINAL.PY")
print("="*50)

# === ДИАГНОСТИКА ===
print("🔍 ДИАГНОСТИКА СИСТЕМЫ:")
print(f"1. Текущая папка: {os.getcwd()}")
print(f"2. Путь к файлу: {__file__}")
print(f"3. Python версия: {sys.version}")
print(f"4. PYTHONPATH: {sys.path}")

# Показываем файлы
print("\n📦 ФАЙЛЫ В ПАПКЕ:")
try:
    files = os.listdir('.')
    for file in files:
        print(f"   - {file}")
except Exception as e:
    print(f"   ❌ Ошибка чтения папки: {e}")

# Проверяем наличие файлов
print("\n✅ ПРОВЕРКА ФАЙЛОВ:")
required_files = ['requirements.txt', 'bot_adaptive.py']
for file in required_files:
    exists = os.path.exists(file)
    print(f"   - {file}: {'✅ Найден' if exists else '❌ Не найден'}")

# === ОСНОВНОЙ КОД ===
async def main_fixed():
    """Исправленная версия бота"""
    
    print("\n" + "="*50)
    print("🤖 ЗАПУСК БОТА")
    print("="*50)
    
    # Получаем токен
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен")
        print("   Установите переменную TELEGRAM_BOT_TOKEN в настройках Render")
        return
    
    print(f"✅ Токен получен: {TOKEN[:10]}...")
    
    try:
        # Импортируем библиотеки
        print("📦 ИМПОРТ БИБЛИОТЕК...")
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import (
            Application,
            CommandHandler,
            CallbackQueryHandler,
            ContextTypes,
            ConversationHandler
        )
        
        print("✅ Библиотеки загружены")
        
        # Определяем функцию start_command
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Команда /start"""
            print(f"📨 Получена команда /start от {update.effective_user.id}")
            
            await update.message.reply_text(
                "🎴 <b>Добро пожаловать в ВАРИАТИКА!</b>\n\n"
                "Это финальная версия бота для Render.\n\n"
                "Нажмите кнопку чтобы начать тест:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Начать тест", callback_data="start_test")]
                ]),
                parse_mode="HTML"
            )
            return "START_MENU"
        
        async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Начало теста"""
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "✅ Тест начался!\n\n"
                "<b>Что будет дальше:</b>\n"
                "1. 4 этапа тестирования\n"
                "2. Анализ профиля\n"
                "3. Персональные рекомендации\n\n"
                "<i>Это демо-версия. Полный функционал в bot_adaptive.py</i>",
                parse_mode="HTML"
            )
            return "TESTING"
        
        async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Отмена"""
            await update.message.reply_text("Тест отменен. Используйте /start чтобы начать заново.")
            return ConversationHandler.END
        
        # Создаем приложение
        print("🤖 СОЗДАНИЕ ПРИЛОЖЕНИЯ...")
        application = Application.builder().token(TOKEN).build()
        
        # Создаем ConversationHandler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start_command),
                CallbackQueryHandler(start_test, pattern="^start_test$")
            ],
            states={
                "START_MENU": [
                    CallbackQueryHandler(start_test, pattern="^start_test$")
                ],
                "TESTING": []
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_message=True
        )
        
        application.add_handler(conv_handler)
        
        # Простые команды для проверки
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "📋 <b>Доступные команды:</b>\n\n"
                "/start - Начать тест\n"
                "/test - Проверка работы\n"
                "/help - Эта справка\n"
                "/cancel - Отмена теста",
                parse_mode="HTML"
            )
        
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("✅ Бот работает корректно!")
        
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test", test_command))
        
        print("✅ Приложение создано")
        print("🌐 ПОДКЛЮЧЕНИЕ К TELEGRAM...")
        
        # Запускаем бота
        await application.run_polling(
            drop_pending_updates=True,
            close_loop=False,  # Важно для Render
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30
        )
        
    except ImportError as e:
        print(f"❌ ОШИБКА ИМПОРТА: {e}")
        print("   Установите зависимости: pip install python-telegram-bot==20.3")
        return
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return

# === ЗАПУСК ===
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎯 ЗАПУСК АСИНХРОННОЙ ФУНКЦИИ")
    print("="*50)
    
    try:
        asyncio.run(main_fixed())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"\n❌ ФАТАЛЬНАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
