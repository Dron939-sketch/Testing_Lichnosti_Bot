"""
МИНИМАЛЬНЫЙ БОТ ДЛЯ ТЕСТА API
Проверяем только /api/create-payment
"""

import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://testing-lichnosti-bot-1.onrender.com"

# ========== ПРОСТАЯ КОМАНДА ДЛЯ ТЕСТА ==========

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестируем создание платежа - МИНИМАЛЬНЫЙ КОД"""
    
    # Шаг 1: Проверяем, доступен ли сервер
    await update.message.reply_text("1. Проверяю сервер...")
    try:
        r = requests.get(f"{API_URL}/", timeout=5)
        await update.message.reply_text(f"✓ Сервер: HTTP {r.status_code}")
    except:
        await update.message.reply_text("✗ Сервер недоступен")
        return
    
    # Шаг 2: Создаем тестовый платеж
    await update.message.reply_text("2. Создаю тестовый платеж...")
    
    test_data = {
        "payment_id": f"test_{update.effective_user.id}",
        "user_id": update.effective_user.id,
        "amount": 1.0,
        "email": "test@test.com"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Шаг 3: Анализируем ответ
        await update.message.reply_text(f"3. Ответ сервера: HTTP {response.status_code}")
        await update.message.reply_text(f"Текст ответа:\n{response.text}")
        
        if response.status_code == 200:
            await update.message.reply_text("✅ УСПЕХ! Запись создана в БД")
        elif response.status_code == 400:
            await update.message.reply_text("⚠️ Ошибка 400: Проверьте данные запроса")
        elif response.status_code == 500:
            await update.message.reply_text("❌ Ошибка 500: Проблема в коде Flask сервера")
        else:
            await update.message.reply_text(f"⚠️ Неожиданный код: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при запросе: {str(e)}")

async def test_raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест RAW запроса - для отладки"""
    await update.message.reply_text("Отправляю RAW запрос...")
    
    data = {
        "payment_id": "raw_test_123",
        "user_id": 123,
        "amount": 1.0,
        "email": "raw@test.com"
    }
    
    try:
        import json
        headers = {'Content-Type': 'application/json'}
        r = requests.post(
            f"{API_URL}/api/create-payment",
            data=json.dumps(data),
            headers=headers,
            timeout=10
        )
        
        await update.message.reply_text(
            f"RAW запрос:\n"
            f"URL: {API_URL}/api/create-payment\n"
            f"Данные: {json.dumps(data)}\n"
            f"Ответ: {r.status_code}\n"
            f"Тело: {r.text}"
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def check_endpoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяем какие эндпоинты доступны"""
    endpoints = [
        "/",
        "/api/create-payment",
        "/test-db",
        "/api/health"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            r = requests.get(f"{API_URL}{endpoint}", timeout=3)
            results.append(f"{endpoint}: HTTP {r.status_code}")
        except:
            results.append(f"{endpoint}: Нет ответа")
    
    await update.message.reply_text("📋 Доступные эндпоинты:\n" + "\n".join(results))

# ========== ЗАПУСК БОТА ==========

def main():
    print("=== МИНИМАЛЬНЫЙ БОТ ДЛЯ ТЕСТА API ===")
    print(f"API: {API_URL}")
    
    app = Application.builder().token(TOKEN).build()
    
    # ТОЛЬКО 3 команды для тестирования
    app.add_handler(CommandHandler("test", test_payment))
    app.add_handler(CommandHandler("raw", test_raw))
    app.add_handler(CommandHandler("endpoints", check_endpoints))
    app.add_handler(CommandHandler("start", test_payment))  # /start тоже вызывает тест
    
    print("✅ Бот запущен. Команды: /test, /raw, /endpoints")
    app.run_polling()

if __name__ == "__main__":
    main()
