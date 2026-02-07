#!/usr/bin/env python3
"""
Telegram Bot - РАБОЧАЯ версия с полной цепочкой
"""

import os
import time
import json
import base64
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Проверка подключения
def check_api():
    """Проверяет доступность API"""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_payment_full(user_id: int):
    """Полная цепочка создания платежа"""
    try:
        # Генерируем ID платежа
        payment_id = f"pay_{user_id}_{int(time.time())}"
        email = f"user_{user_id}@telegram.org"
        
        print("=" * 60)
        print(f"🔄 СОЗДАЮ ПЛАТЕЖ: {payment_id}")
        print("=" * 60)
        
        # Шаг 1: Проверяем API
        print("🔗 Шаг 1: Проверяю API...")
        if not check_api():
            print("❌ API недоступен!")
            return None
        
        print(f"✅ API доступен: {API_URL}")
        
        # Шаг 2: Создаем в БД
        print("📦 Шаг 2: Создаю в базе данных...")
        db_payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 1.00,
            "email": email,
            "description": "Тест 1 рубль"
        }
        
        db_response = requests.post(
            f"{API_URL}/api/create-payment",
            json=db_payload,
            timeout=10
        )
        
        print(f"📊 Ответ БД: {db_response.status_code}")
        
        if db_response.status_code != 201:
            print(f"❌ Ошибка БД: {db_response.text}")
            return None
        
        print(f"✅ Платеж создан в БД: {payment_id}")
        
        # Шаг 3: Создаем в ЮKassa
        print("💳 Шаг 3: Создаю в ЮKassa...")
        
        auth_string = f"{SHOP_ID}:{SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id
        }
        
        yk_payload = {
            "amount": {"value": "1.00", "currency": "RUB"},
            "payment_method_data": {"type": "bank_card"},
            "confirmation": {
                "type": "redirect", 
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,
            "description": "Тестовая оплата курса ВАРИАТИКА",
            "metadata": {"payment_id": payment_id, "user_id": user_id},
            "receipt": {
                "customer": {"email": email},
                "items": [{
                    "description": "Тестовый доступ к курсу ВАРИАТИКА",
                    "quantity": "1.00",
                    "amount": {"value": "1.00", "currency": "RUB"},
                    "vat_code": 1,
                    "payment_subject": "service",
                    "payment_mode": "full_payment"
                }]
            }
        }
        
        print("📤 Отправляю в ЮKassa...")
        yk_response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=yk_payload,
            timeout=30
        )
        
        print(f"📥 Ответ ЮKassa: {yk_response.status_code}")
        
        if yk_response.status_code != 200:
            print(f"❌ Ошибка ЮKassa: {yk_response.text}")
            return None
        
        data = yk_response.json()
        yookassa_id = data.get('id')
        payment_url = data.get('confirmation', {}).get('confirmation_url')
        
        print(f"✅ Платеж создан в ЮKassa: {yookassa_id}")
        print(f"🔗 Ссылка: {payment_url}")
        
        # Шаг 4: Сохраняем ID ЮKassa в БД
        print("💾 Шаг 4: Сохраняю ID ЮKassa в БД...")
        
        update_payload = {
            "payment_id": payment_id,
            "yookassa_id": yookassa_id,
            "status": "waiting"
        }
        
        update_response = requests.post(
            f"{API_URL}/api/update-yookassa-id",
            json=update_payload,
            timeout=5
        )
        
        print(f"📊 Ответ обновления: {update_response.status_code}")
        
        if update_response.status_code == 200:
            print("✅ ID ЮKassa сохранен в БД")
        else:
            print(f"⚠️ Ошибка сохранения ID: {update_response.text}")
        
        print("=" * 60)
        print("🎯 ПЛАТЕЖ УСПЕШНО СОЗДАН!")
        print(f"📋 ID: {payment_id}")
        print(f"🏪 ЮKassa ID: {yookassa_id}")
        print(f"🔗 Ссылка: {payment_url}")
        print("=" * 60)
        
        return payment_url
        
    except Exception as e:
        print(f"🔥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return None

# Telegram команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверяем API
    if not check_api():
        await update.message.reply_text("❌ API сервер недоступен. Попробуйте позже.")
        return
    
    keyboard = [[InlineKeyboardButton("💳 ТЕСТ 1 РУБЛЬ", callback_data="pay")]]
    
    await update.message.reply_text(
        f"Привет, {user.first_name}!\nAPI: ✅\nНажми для оплаты:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    await query.edit_message_text("🔄 Создаю платеж...")
    
    payment_url = create_payment_full(user_id)
    
    if payment_url:
        keyboard = [[InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=payment_url)]]
        await query.edit_message_text(
            "✅ Готово! Нажмите кнопку для оплаты:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text("❌ Ошибка создания платежа. Попробуйте позже.")

def main():
    print("=" * 60)
    print("🤖 ЗАПУСК БОТА С ПОЛНОЙ ЦЕПОЧКОЙ")
    print("=" * 60)
    print(f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🔗 API URL: {API_URL}")
    
    # Проверяем API перед запуском
    print("🔍 Проверяю подключение к API...")
    if check_api():
        print("✅ API доступен")
    else:
        print("❌ API недоступен! Проверьте URL")
        print(f"Текущий URL: {API_URL}")
    
    print("=" * 60)
    
    if not TOKEN:
        print("❌ Нет токена бота!")
        return
    
    try:
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(pay_callback, pattern="^pay$"))
        
        print("✅ Бот запускается...")
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"🔥 Ошибка: {e}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
