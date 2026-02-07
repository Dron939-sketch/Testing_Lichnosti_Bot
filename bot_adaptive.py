"""
ТЕСТОВЫЙ БОТ - Полная диагностика платежной системы
"""

import logging
import os
import asyncio
import time
import requests
import json
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не установлен!")
    sys.exit(1)

# URL вашего Flask API
FLASK_API_URL = "https://testing-lichnosti-bot-1.onrender.com"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения ID тестового платежа
TEST_PAYMENT_ID = None

# ========== ДИАГНОСТИЧЕСКИЕ ФУНКЦИИ ==========

async def start_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диагностики"""
    query = update.callback_query
    if query:
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text
    
    await message_func("🔄 Начинаю диагностику платежной системы...")
    
    results = []
    
    # Тест 1: Проверка доступности API
    await message_func("🔍 1. Проверяю доступность Flask API...")
    result1 = await check_api_availability()
    results.append(("1. Доступность API", result1))
    
    # Тест 2: Проверка эндпоинтов
    await message_func("🔍 2. Проверяю эндпоинты API...")
    result2 = await check_api_endpoints()
    results.append(("2. Эндпоинты API", result2))
    
    # Тест 3: Создание тестового платежа в БД
    await message_func("🔍 3. Тестирую создание платежа в БД...")
    result3 = await test_create_payment_db(update.effective_user.id)
    results.append(("3. Создание платежа (БД)", result3))
    
    # Тест 4: Создание платежа ЮKassa
    if "успешно" in result3.lower():
        await message_func("🔍 4. Тестирую создание платежа ЮKassa...")
        result4 = await test_create_yookassa_payment()
        results.append(("4. Создание платежа (ЮKassa)", result4))
    else:
        results.append(("4. Создание платежа (ЮKassa)", "⚠️ Пропущено (ошибка на шаге 3)"))
    
    # Формируем итоговый отчет
    report = "📊 ДИАГНОСТИКА ПЛАТЕЖНОЙ СИСТЕМЫ\n\n"
    success_count = 0
    
    for test_name, result in results:
        if "✅" in result or "успешно" in result.lower():
            status = "✅"
            success_count += 1
        elif "⚠️" in result or "пропущено" in result.lower():
            status = "⚠️"
        else:
            status = "❌"
        
        report += f"{status} {test_name}\n"
        if len(result) > 50:
            report += f"   {result[:50]}...\n"
        else:
            report += f"   {result}\n"
        report += "\n"
    
    # Итог
    report += f"\n📈 РЕЗУЛЬТАТ: {success_count}/{len(results)} тестов пройдено"
    
    if success_count == len(results):
        report += " 🎉"
    elif success_count >= 3:
        report += " ⚠️"
    else:
        report += " ❌"
    
    # Кнопки действий
    keyboard = []
    if TEST_PAYMENT_ID:
        keyboard.append([InlineKeyboardButton("🔗 Открыть ссылку оплаты", url=get_payment_url())])
        keyboard.append([InlineKeyboardButton("📊 Проверить статус", callback_data=f"check_status_{TEST_PAYMENT_ID}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Повторить диагностику", callback_data="diagnostic")])
    keyboard.append([InlineKeyboardButton("❌ Тестовый платеж (1 рубль)", callback_data="test_payment_1")])
    keyboard.append([InlineKeyboardButton("💰 Реальный платеж (690 руб)", callback_data="real_payment")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message_func(report, reply_markup=reply_markup)

async def check_api_availability():
    """Проверка доступности API"""
    try:
        response = requests.get(f"{FLASK_API_URL}/", timeout=10)
        if response.status_code == 200:
            return "✅ API доступен"
        else:
            return f"❌ API отвечает с кодом {response.status_code}"
    except requests.exceptions.Timeout:
        return "❌ Таймаут (10 секунд)"
    except requests.exceptions.ConnectionError:
        return "❌ Ошибка подключения"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def check_api_endpoints():
    """Проверка всех эндпоинтов"""
    endpoints = [
        ("/api/create-payment", "POST"),
        ("/api/create-yookassa-payment", "POST"),
        ("/api/payment-status/test123", "GET"),
        ("/test-api", "GET"),
    ]
    
    results = []
    
    for endpoint, method in endpoints:
        try:
            url = f"{FLASK_API_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                # Для POST отправляем пустой запрос
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code in [200, 201, 400, 422]:
                # 400/422 - нормально для пустых запросов
                results.append(f"{endpoint}: ✅ ({response.status_code})")
            else:
                results.append(f"{endpoint}: ❌ ({response.status_code})")
                
        except Exception as e:
            results.append(f"{endpoint}: ❌ ({str(e)[:30]}...)")
    
    return "\n".join(results)

async def test_create_payment_db(user_id):
    """Тест создания платежа в БД"""
    global TEST_PAYMENT_ID
    
    payment_id = f"diagnostic_{user_id}_{int(time.time())}"
    TEST_PAYMENT_ID = payment_id
    
    payload = {
        "payment_id": payment_id,
        "user_id": user_id,
        "amount": 1,  # 1 рубль для теста
        "email": f"test{user_id}@diagnostic.com"
    }
    
    try:
        response = requests.post(
            f"{FLASK_API_URL}/api/create-payment",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        logger.info(f"DB Payment Response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                return f"✅ Успешно создан платеж ID: {payment_id[:10]}..."
            else:
                return f"❌ Ошибка в ответе: {result.get('error', 'Unknown')}"
        elif response.status_code == 400:
            # Пробуем получить детали ошибки
            try:
                error_data = response.json()
                return f"❌ Ошибка 400: {error_data.get('error', 'Bad Request')}"
            except:
                return f"❌ Ошибка 400: {response.text[:100]}"
        else:
            return f"❌ HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return "❌ Таймаут при создании платежа"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def test_create_yookassa_payment():
    """Тест создания платежа ЮKassa"""
    if not TEST_PAYMENT_ID:
        return "⚠️ Нет ID платежа"
    
    payload = {
        "payment_id": TEST_PAYMENT_ID,
        "amount": 1,
        "description": "Диагностический платеж",
        "return_url": "https://t.me/testing_lichnosti_bot"
    }
    
    try:
        response = requests.post(
            f"{FLASK_API_URL}/api/create-yookassa-payment",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        logger.info(f"YooKassa Response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", True):
                # Сохраняем ссылку на оплату
                global PAYMENT_URL
                PAYMENT_URL = result.get("payment_url", "")
                return f"✅ Успешно. Статус: {result.get('status', 'unknown')}"
            else:
                return f"❌ Ошибка ЮKassa: {result.get('error', 'Unknown')}"
        else:
            return f"❌ HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return "❌ Таймаут при создании платежа ЮKassa"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

def get_payment_url():
    """Получить URL для оплаты"""
    return PAYMENT_URL if 'PAYMENT_URL' in globals() else "#"

async def check_payment_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для проверки статуса"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("check_status_", "")
    await check_payment_status(query, payment_id)

async def check_payment_status(query, payment_id=None):
    """Проверка статуса платежа"""
    if not payment_id:
        payment_id = TEST_PAYMENT_ID
    
    if not payment_id:
        await query.edit_message_text("❌ ID платежа не найден")
        return
    
    try:
        response = requests.get(
            f"{FLASK_API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            details = result.get("details", {})
            
            message = (
                f"📊 Статус платежа\n\n"
                f"🆔 ID: {payment_id[:15]}...\n"
                f"📈 Статус: {status}\n"
            )
            
            if details:
                message += f"\n📋 Детали:\n"
                for key, value in details.items():
                    message += f"• {key}: {value}\n"
            
            if status == "succeeded":
                message += "\n🎉 Оплата прошла успешно!"
            elif status == "pending":
                message += "\n⏳ Ожидание оплаты..."
            
        else:
            message = f"❌ Ошибка проверки: HTTP {response.status_code}\n{response.text[:200]}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"check_status_{payment_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(query, 'edit_message_text'):
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.reply_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        error_msg = f"❌ Ошибка при проверке статуса: {str(e)}"
        if hasattr(query, 'edit_message_text'):
            await query.edit_message_text(error_msg)
        else:
            await query.reply_text(error_msg)

async def test_payment_1_rub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый платеж на 1 рубль"""
    query = update.callback_query
    await query.answer("⏳ Создаю тестовый платеж...")
    
    user_id = query.from_user.id
    payment_id = f"test_1rub_{user_id}_{int(time.time())}"
    global TEST_PAYMENT_ID
    TEST_PAYMENT_ID = payment_id
    
    # Шаг 1: Создаем в БД
    payload = {
        "payment_id": payment_id,
        "user_id": user_id,
        "amount": 1,
        "email": f"test{user_id}@telegram.org"
    }
    
    try:
        response = requests.post(
            f"{FLASK_API_URL}/api/create-payment",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка БД: {response.text}")
        
        # Шаг 2: Создаем в ЮKassa
        yookassa_payload = {
            "payment_id": payment_id,
            "amount": 1,
            "description": "Тестовый платеж (1 рубль)",
            "return_url": "https://t.me/testing_lichnosti_bot"
        }
        
        yookassa_response = requests.post(
            f"{FLASK_API_URL}/api/create-yookassa-payment",
            json=yookassa_payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if yookassa_response.status_code != 200:
            raise Exception(f"Ошибка ЮKassa: {yookassa_response.text}")
        
        yookassa_result = yookassa_response.json()
        
        if not yookassa_result.get("success", True):
            raise Exception(f"ЮKassa: {yookassa_result.get('error', 'Unknown')}")
        
        global PAYMENT_URL
        PAYMENT_URL = yookassa_result.get("payment_url", "")
        
        message = (
            "✅ Тестовый платеж создан!\n\n"
            f"💰 Сумма: 1 рубль\n"
            f"🆔 ID: {payment_id[:10]}...\n"
            f"📊 Статус: {yookassa_result.get('status', 'pending')}\n\n"
            f"Для оплаты используйте тестовую карту:\n"
            f"• 5555 5555 5555 4444 (успех)\n"
            f"• 2200 0000 0000 0004 (ожидание)\n"
            f"• 2200 0000 0000 0005 (отказ)"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔗 Оплатить 1 рубль", url=PAYMENT_URL)],
            [InlineKeyboardButton("📊 Проверить статус", callback_data=f"check_status_{payment_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def real_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реальный платеж на 690 рублей"""
    query = update.callback_query
    await query.answer("⏳ Создаю реальный платеж...")
    
    await query.edit_message_text(
        "💰 РЕАЛЬНЫЙ ПЛАТЕЖ (690 руб)\n\n"
        "⚠️ Внимание: Это реальный платеж!\n"
        "Деньги будут списаны с вашей карты.\n\n"
        "Для продолжения нажмите кнопку ниже.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Я понимаю, продолжить", callback_data="confirm_real_payment")],
            [InlineKeyboardButton("❌ Отмена", callback_data="back_to_start")]
        ])
    )

async def confirm_real_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение реального платежа"""
    query = update.callback_query
    await query.answer("⏳ Создаю платеж...")
    
    user_id = query.from_user.id
    payment_id = f"real_{user_id}_{int(time.time())}"
    global TEST_PAYMENT_ID
    TEST_PAYMENT_ID = payment_id
    
    payload = {
        "payment_id": payment_id,
        "user_id": user_id,
        "amount": 690,
        "email": f"user{user_id}@telegram.org"
    }
    
    try:
        response = requests.post(
            f"{FLASK_API_URL}/api/create-payment",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Ошибка БД: {response.text}")
        
        yookassa_payload = {
            "payment_id": payment_id,
            "amount": 690,
            "description": "Полный пакет ВАРИАТИКА",
            "return_url": "https://t.me/testing_lichnosti_bot"
        }
        
        yookassa_response = requests.post(
            f"{FLASK_API_URL}/api/create-yookassa-payment",
            json=yookassa_payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if yookassa_response.status_code != 200:
            raise Exception(f"Ошибка ЮKassa: {yookassa_response.text}")
        
        yookassa_result = yookassa_response.json()
        
        if not yookassa_result.get("success", True):
            raise Exception(f"ЮKassa: {yookassa_result.get('error', 'Unknown')}")
        
        global PAYMENT_URL
        PAYMENT_URL = yookassa_result.get("payment_url", "")
        
        message = (
            "✅ Платеж создан!\n\n"
            f"💰 Сумма: 690 рублей\n"
            f"🆔 ID: {payment_id[:10]}...\n"
            f"📊 Статус: {yookassa_result.get('status', 'pending')}\n\n"
            f"Инструкция:\n"
            f"1. Нажмите «Оплатить»\n"
            f"2. Введите данные карты\n"
            f"3. Вернитесь и проверьте статус"
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить 690 руб", url=PAYMENT_URL)],
            [InlineKeyboardButton("📊 Проверить статус", callback_data=f"check_status_{payment_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к началу"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔧 Диагностика системы", callback_data="diagnostic")],
        [InlineKeyboardButton("❌ Тестовый платеж (1 рубль)", callback_data="test_payment_1")],
        [InlineKeyboardButton("💰 Реальный платеж (690 руб)", callback_data="real_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 ТЕСТОВЫЙ БОТ - Платежная система\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("🔧 Диагностика системы", callback_data="diagnostic")],
        [InlineKeyboardButton("❌ Тестовый платеж (1 рубль)", callback_data="test_payment_1")],
        [InlineKeyboardButton("💰 Реальный платеж (690 руб)", callback_data="real_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 ТЕСТОВЫЙ БОТ - Платежная система\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

# ========== ЗАПУСК БОТА ==========

def main():
    """Запуск бота"""
    print("="*60)
    print("🔧 ТЕСТОВЫЙ БОТ - Полная диагностика платежной системы")
    print(f"🔗 Flask API: {FLASK_API_URL}")
    print(f"🤖 Токен: {'✅ Установлен' if TOKEN else '❌ Нет!'}")
    print("="*60)
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start_diagnostic, pattern="^diagnostic$"))
    application.add_handler(CallbackQueryHandler(test_payment_1_rub, pattern="^test_payment_1$"))
    application.add_handler(CallbackQueryHandler(real_payment, pattern="^real_payment$"))
    application.add_handler(CallbackQueryHandler(confirm_real_payment, pattern="^confirm_real_payment$"))
    application.add_handler(CallbackQueryHandler(check_payment_status_callback, pattern="^check_status_"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    
    print("\n🤖 Бот запускается...")
    
    # Запуск с обработкой ошибок
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
