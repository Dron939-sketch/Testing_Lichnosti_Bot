"""
БОТ ДЛЯ ДИАГНОСТИКИ FLASK ОШИБКИ 500
Проблема: "Failed to create payment record" в /api/create-payment
"""

import os
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://testing-lichnosti-bot-1.onrender.com"

async def diagnose_500_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Диагностика ошибки 500 в Flask"""
    await update.message.reply_text(
        "🔧 **ДИАГНОСТИКА ОШИБКИ 500**\n\n"
        "Проблема: Flask возвращает 'Failed to create payment record'\n"
        "Это значит ошибка ВНУТРИ Flask кода, а не в запросе."
    )
    
    # 1. Проверяем, что сервер вообще отвечает
    await update.message.reply_text("1️⃣ Проверяю базовую доступность...")
    try:
        r = requests.get(f"{API_URL}/", timeout=5)
        await update.message.reply_text(f"✓ Сервер доступен: HTTP {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"✗ Сервер недоступен: {str(e)}")
        return
    
    # 2. Проверяем эндпоинт test-db если есть
    await update.message.reply_text("2️⃣ Проверяю подключение к БД...")
    try:
        r = requests.get(f"{API_URL}/test-db", timeout=5)
        if r.status_code == 200:
            await update.message.reply_text(f"✓ Тест БД: {r.text[:200]}")
        else:
            await update.message.reply_text(f"⚠️ Тест БД: HTTP {r.status_code}")
    except:
        await update.message.reply_text("ℹ️ Эндпоинт /test-db не доступен")
    
    # 3. Анализируем саму ошибку
    await update.message.reply_text(
        "3️⃣ **АНАЛИЗ ОШИБКИ:**\n\n"
        "Сообщение: 'Failed to create payment record'\n\n"
        "📋 **ВОЗМОЖНЫЕ ПРИЧИНЫ:**\n"
        "1. ❌ Таблица 'payments' не существует\n"
        "2. ❌ Неправильный SQL запрос в Flask\n"
        "3. ❌ Ошибка подключения к PostgreSQL\n"
        "4. ❌ Проблема с правами доступа к БД\n"
        "5. ❌ Ошибка в коде обработки запроса"
    )

async def check_database_structure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяем структуру БД через API"""
    await update.message.reply_text(
        "📊 **ПРОВЕРКА СТРУКТУРЫ БД**\n\n"
        "Создаю тестовые запросы для диагностики..."
    )
    
    # Тест 1: Пробуем разные форматы
    test_cases = [
        {
            "name": "Тест 1: Минимальные поля",
            "data": {"payment_id": "diag_1", "user_id": 111, "amount": 1.0}
        },
        {
            "name": "Тест 2: Все поля",
            "data": {"payment_id": "diag_2", "user_id": 222, "amount": 2.0, "email": "test@test.com"}
        },
        {
            "name": "Тест 3: Amount как целое",
            "data": {"payment_id": "diag_3", "user_id": 333, "amount": 3, "email": "test@test.com"}
        }
    ]
    
    results = []
    for test in test_cases:
        try:
            r = requests.post(
                f"{API_URL}/api/create-payment",
                json=test["data"],
                timeout=10
            )
            results.append(f"{test['name']}: HTTP {r.status_code} - {r.text[:100]}")
        except Exception as e:
            results.append(f"{test['name']}: Ошибка - {str(e)[:50]}")
    
    await update.message.reply_text("📋 **РЕЗУЛЬТАТЫ ТЕСТОВ:**\n" + "\n".join(results))

async def get_flask_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предлагаем решение для Flask кода"""
    await update.message.reply_text(
        "🛠 **РЕШЕНИЕ ДЛЯ FLASK КОДА**\n\n"
        "В файле `app.py` найдите функцию для `/api/create-payment`\n\n"
        "📝 **ИСПРАВЛЕННЫЙ КОД ДЛЯ FLASK:**\n\n"
        "```python\n"
        "@app.route('/api/create-payment', methods=['POST'])\n"
        "def create_payment():\n"
        "    try:\n"
        "        data = request.get_json()\n"
        "        \n"
        "        # Проверка обязательных полей\n"
        "        required_fields = ['payment_id', 'user_id', 'amount']\n"
        "        for field in required_fields:\n"
        "            if field not in data:\n"
        "                return jsonify({'error': f'Missing required field: {field}', 'success': False}), 400\n"
        "        \n"
        "        # Подключение к БД\n"
        "        conn = psycopg2.connect(DATABASE_URL)\n"
        "        cursor = conn.cursor()\n"
        "        \n"
        "        # Вставка данных\n"
        "        cursor.execute(\"\"\"\n"
        "            INSERT INTO payments (payment_id, user_id, amount, email, status)\n"
        "            VALUES (%s, %s, %s, %s, 'pending')\n"
        "        \"\"\", (\n"
        "            data['payment_id'],\n"
        "            data['user_id'],\n"
        "            data['amount'],\n"
        "            data.get('email', None)\n"
        "        ))\n"
        "        \n"
        "        conn.commit()\n"
        "        cursor.close()\n"
        "        conn.close()\n"
        "        \n"
        "        return jsonify({\n"
        "            'success': True,\n"
        "            'message': 'Payment record created',\n"
        "            'payment_id': data['payment_id']\n"
        "        }), 200\n"
        "        \n"
        "    except psycopg2.Error as e:\n"
        "        # Логируем SQL ошибку\n"
        "        print(f'Database error: {str(e)}')\n"
        "        return jsonify({'error': f'Database error: {str(e)}', 'success': False}), 500\n"
        "        \n"
        "    except Exception as e:\n"
        "        print(f'Server error: {str(e)}')\n"
        "        return jsonify({'error': f'Server error: {str(e)}', 'success': False}), 500\n"
        "```\n\n"
        "📌 **Что проверить в Render:**\n"
        "1. Логи Flask приложения\n"
        "2. Правильность DATABASE_URL\n"
        "3. Существует ли таблица 'payments'",
        parse_mode='Markdown'
    )

async def create_test_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SQL для создания таблицы"""
    await update.message.reply_text(
        "🗄 **SQL ДЛЯ СОЗДАНИЯ ТАБЛИЦЫ**\n\n"
        "Если таблицы payments нет, создайте её:\n\n"
        "```sql\n"
        "CREATE TABLE IF NOT EXISTS payments (\n"
        "    id SERIAL PRIMARY KEY,\n"
        "    payment_id VARCHAR(100) UNIQUE NOT NULL,\n"
        "    user_id BIGINT NOT NULL,\n"
        "    amount DECIMAL(10, 2) NOT NULL,\n"
        "    email VARCHAR(255),\n"
        "    status VARCHAR(50) DEFAULT 'pending',\n"
        "    yookassa_id VARCHAR(100),\n"
        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        ");\n"
        "```\n\n"
        "📌 **Быстрая проверка в Render PostgreSQL:**\n"
        "1. Зайдите в проект на Render\n"
        "2. Откройте PostgreSQL (вариатика-db)\n"
        "3. Введите команды:\n"
        "```sql\n"
        "-- Проверить таблицы\n"
        "\\dt\n"
        "\n"
        "-- Создать таблицу если её нет\n"
        "CREATE TABLE payments (...)\n"
        "```",
        parse_mode='Markdown'
    )

async def quick_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрый тест после исправлений"""
    await update.message.reply_text("🚀 Запускаю быстрый тест...")
    
    test_data = {
        "payment_id": f"quick_{update.effective_user.id}",
        "user_id": update.effective_user.id,
        "amount": 1.0
    }
    
    try:
        r = requests.post(
            f"{API_URL}/api/create-payment",
            json=test_data,
            timeout=10
        )
        
        if r.status_code == 200:
            await update.message.reply_text(
                "🎉 **УСПЕХ!** Платеж создан!\n\n"
                f"Ответ: {r.text}\n\n"
                "Теперь можно переходить к шагу 2 (ЮKassa)"
            )
        elif r.status_code == 400:
            await update.message.reply_text(
                f"⚠️ Ошибка 400: {r.text}\n\n"
                "Проверьте поля запроса в Flask коде"
            )
        elif r.status_code == 500:
            await update.message.reply_text(
                f"❌ Все ещё ошибка 500: {r.text}\n\n"
                "Проверьте:\n"
                "1. Логи Flask в Render\n"
                "2. SQL ошибки в логах\n"
                "3. Правильность подключения к БД"
            )
        else:
            await update.message.reply_text(
                f"📊 Ответ {r.status_code}: {r.text[:200]}"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка запроса: {str(e)}")

# ========== ЗАПУСК БОТА ==========

def main():
    print("=== БОТ ДЛЯ ИСПРАВЛЕНИЯ FLASK ОШИБКИ 500 ===")
    print("Проблема: 'Failed to create payment record'")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("diagnose", diagnose_500_error))
    app.add_handler(CommandHandler("checkdb", check_database_structure))
    app.add_handler(CommandHandler("solution", get_flask_solution))
    app.add_handler(CommandHandler("sqltable", create_test_table))
    app.add_handler(CommandHandler("test", quick_test))
    app.add_handler(CommandHandler("start", diagnose_500_error))
    
    print("✅ Бот запущен. Команды:")
    print("  /diagnose - диагностика ошибки")
    print("  /checkdb - тесты БД")
    print("  /solution - исправленный Flask код")
    print("  /sqltable - SQL для создания таблицы")
    print("  /test - быстрый тест")
    
    app.run_polling()

if __name__ == "__main__":
    main()
