"""
МИНИМАЛЬНЫЙ БОТ ДЛЯ ТЕСТА API
Исправление: только одна команда для теста Flask
"""

import os
import sys
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://testing-lichnosti-bot-1.onrender.com"

# ========== ТОЛЬКО ОДНА КОМАНДА ДЛЯ ТЕСТА ==========

async def test_flask_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестирует Flask API - создание платежа"""
    
    # Шаг 1: Проверяем API
    await update.message.reply_text("🔍 Тестирую Flask API...")
    
    try:
        # Тест 1: Проверка доступности
        r1 = requests.get(API_URL, timeout=5)
        await update.message.reply_text(f"✅ API доступен: {r1.status_code}")
        
        # Тест 2: Создаем платеж
        test_data = {
            "payment_id": f"test_{update.effective_user.id}",
            "user_id": update.effective_user.id,
            "amount": 1.0,
            "email": f"test{update.effective_user.id}@test.com"
        }
        
        await update.message.reply_text("💰 Создаю тестовый платеж...")
        
        r2 = requests.post(
            f"{API_URL}/api/create-payment",
            json=test_data,
            timeout=10
        )
        
        # Шаг 3: Анализируем ответ
        if r2.status_code == 200:
            await update.message.reply_text(
                f"🎉 УСПЕХ! Платеж создан!\n\n"
                f"Ответ: {r2.text}"
            )
        elif r2.status_code == 500:
            await update.message.reply_text(
                f"❌ Ошибка 500 в Flask API:\n{r2.text}\n\n"
                f"Проверьте логи Flask на Render!"
            )
        else:
            await update.message.reply_text(
                f"📊 Ответ {r2.status_code}:\n{r2.text}"
            )
            
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Не могу подключиться к Flask API")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def check_flask_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет статус Flask API"""
    try:
        r = requests.get(f"{API_URL}/test-api", timeout=5)
        await update.message.reply_text(
            f"📊 Flask API Status:\n"
            f"Код: {r.status_code}\n"
            f"Ответ: {r.text[:500]}"
        )
    except:
        await update.message.reply_text("❌ Flask API недоступен")

# ========== ЗАПУСК БОТА С ИСПРАВЛЕНИЕМ КОНФЛИКТА ==========

def main():
    print("=== МИНИМАЛЬНЫЙ БОТ ДЛЯ ТЕСТА FLASK API ===")
    print("Исправление конфликта: drop_pending_updates=True")
    
    # Создаем приложение с drop_pending_updates для избежания конфликта
    app = Application.builder().token(TOKEN).build()
    
    # ТОЛЬКО 2 команды для теста
    app.add_handler(CommandHandler("test", test_flask_api))
    app.add_handler(CommandHandler("status", check_flask_status))
    app.add_handler(CommandHandler("start", test_flask_api))
    
    print("✅ Бот запущен. Команды: /test, /status")
    
    # Запускаем с drop_pending_updates=True чтобы избежать конфликта
    try:
        app.run_polling(
            drop_pending_updates=True,  # ⬅️ ЭТО ИСПРАВЛЯЕТ КОНФЛИКТ!
            allowed_updates=Update.ALL_TYPES
        )
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
