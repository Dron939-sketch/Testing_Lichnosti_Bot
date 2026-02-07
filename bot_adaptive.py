"""
БОТ ДЛЯ СОЗДАНИЯ ТАБЛИЦЫ И ТЕСТА
Теперь когда PostgreSQL доступен!
"""

import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://testing-lichnosti-bot-1.onrender.com"

async def setup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройка базы данных - шаг за шагом"""
    
    # Шаг 1: Проверяем доступность API
    await update.message.reply_text("🔍 Проверяю доступность Flask API...")
    
    try:
        r1 = requests.get(API_URL, timeout=5)
        if r1.status_code != 200:
            await update.message.reply_text(f"❌ API недоступен: {r1.status_code}")
            return
        await update.message.reply_text("✅ Flask API доступен!")
    except:
        await update.message.reply_text("❌ Не могу подключиться к Flask API")
        return
    
    # Шаг 2: Создаем таблицу
    await update.message.reply_text("🛠 Создаю таблицу payments в PostgreSQL...")
    
    try:
        r2 = requests.get(f"{API_URL}/create-table", timeout=10)
        await update.message.reply_text(f"Создание таблицы:\nСтатус: {r2.status_code}\nОтвет: {r2.text[:300]}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка создания таблицы: {str(e)}")
        return
    
    # Шаг 3: Проверяем что таблица создана
    await update.message.reply_text("📊 Проверяю создание таблицы...")
    
    try:
        r3 = requests.get(f"{API_URL}/check-db", timeout=10)
        response = r3.json()
        
        if response.get('success') and response.get('payments_exists'):
            await update.message.reply_text(
                "🎉 УСПЕХ! Таблица payments создана!\n\n"
                f"В базе найдено таблиц: {len(response.get('tables', []))}\n"
                f"Таблица payments существует: ✅\n\n"
                "Теперь тестируем создание платежа..."
            )
            
            # Шаг 4: Тестируем платеж
            await test_payment_creation(update)
            
        else:
            await update.message.reply_text(
                "⚠️ Проблема с таблицей:\n"
                f"Ответ: {response}\n\n"
                "Попробуйте создать таблицу вручную через Render PostgreSQL."
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки: {str(e)}")

async def test_payment_creation(update: Update):
    """Тест создания платежа после создания таблицы"""
    await update.message.reply_text("💰 Тестирую создание платежа...")
    
    test_data = {
        "payment_id": f"success_test_{update.effective_user.id}",
        "user_id": update.effective_user.id,
        "amount": 1.0,
        "email": f"test{update.effective_user.id}@success.com",
        "description": "Первый успешный платеж после настройки БД"
    }
    
    try:
        r = requests.post(
            f"{API_URL}/api/create-payment",
            json=test_data,
            timeout=10
        )
        
        if r.status_code in [200, 201]:
            await update.message.reply_text(
                f"🎉🎉🎉 УРА! ВСЁ РАБОТАЕТ!\n\n"
                f"✅ Платеж успешно создан в PostgreSQL!\n"
                f"🆔 ID: {test_data['payment_id']}\n"
                f"👤 Пользователь: {test_data['user_id']}\n"
                f"💰 Сумма: {test_data['amount']} руб\n"
                f"📊 Статус: записан в базу данных\n\n"
                f"Ответ сервера: {r.text[:500]}"
            )
        else:
            await update.message.reply_text(
                f"⚠️ Ошибка при создании платежа:\n"
                f"Статус: {r.status_code}\n"
                f"Ответ: {r.text[:500]}"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка запроса: {str(e)}")

async def quick_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрый тест"""
    await update.message.reply_text(
        "🚀 БЫСТРЫЙ ТЕСТ СИСТЕМЫ\n\n"
        "1. Создать таблицу: /setup\n"
        "2. Или проверьте в браузере:\n"
        f"   • {API_URL}/create-table\n"
        f"   • {API_URL}/check-db\n\n"
        "PostgreSQL теперь доступен! 🎉"
    )

def main():
    print("="*60)
    print("🚀 БОТ ДЛЯ НАСТРОЙКИ POSTGRESQL")
    print("База данных теперь ДОСТУПНА на Render!")
    print("="*60)
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("setup", setup_database))
    app.add_handler(CommandHandler("test", quick_test))
    app.add_handler(CommandHandler("start", setup_database))
    
    print("✅ Бот запущен!")
    print("💡 Используйте /setup для создания таблицы и теста")
    print("="*60)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
