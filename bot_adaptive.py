#!/usr/bin/env python3
"""
БОТ С ОТЛАДКОЙ - чтобы видеть что происходит
"""

import os
import logging
import requests
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

def create_yookassa_payment_debug(payment_id: str, user_id: int) -> dict:
    """Создание платежа с подробной отладкой"""
    try:
        print(f"🔧 СОЗДАЮ ПЛАТЕЖ {payment_id} для пользователя {user_id}")
        
        # Basic Auth
        auth_string = f"{SHOP_ID}:{SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id
        }
        
        # ПРОСТОЙ запрос БЕЗ receipt
        payload = {
            "amount": {"value": "1.00", "currency": "RUB"},  # 1 рубль для теста
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,
            "description": "Тестовая оплата 1 рубль",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id
            }
        }
        
        print(f"📤 Отправляю в ЮKassa: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ УСПЕХ! Данные ответа: {json.dumps(data, indent=2)}")
            
            # Получаем ссылку
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            print(f"🔗 ССЫЛКА ДЛЯ ОПЛАТЫ: {confirmation_url}")
            
            return {
                "success": True,
                "confirmation_url": confirmation_url,
                "payment_id": payment_id,
                "yookassa_id": data.get('id')
            }
        else:
            print(f"❌ ОШИБКА {response.status_code}: {response.text}")
            return {"success": False, "error": response.text[:200]}
            
    except Exception as e:
        print(f"🔥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return {"success": False, "error": str(e)}

def create_payment_in_db_simple(user_id: int) -> dict:
    """Простое создание платежа в БД"""
    try:
        import time
        payment_id = f"test_{user_id}_{int(time.time())}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 1.00,
            "email": f"user_{user_id}@telegram.org",
            "description": "Тест 1 рубль"
        }
        
        print(f"📦 Отправляю в БД: {payload}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        print(f"📊 Ответ БД: {response.status_code}")
        
        if response.status_code == 201:
            print(f"✅ Платеж создан в БД: {payment_id}")
            return {"success": True, "payment_id": payment_id}
        else:
            print(f"❌ Ошибка БД: {response.status_code} - {response.text}")
            return {"success": False, "error": f"API: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}

async def start_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с отладкой"""
    user = update.effective_user
    print(f"👤 ПОЛЬЗОВАТЕЛЬ: {user.id} - {user.first_name}")
    
    keyboard = [[InlineKeyboardButton("🔧 ТЕСТОВАЯ ОПЛАТА (1 рубль)", callback_data="debug_buy")]]
    
    await update.message.reply_text(
        f"🔧 **РЕЖИМ ОТЛАДКИ**\n\n"
        f"Пользователь: {user.first_name}\n"
        f"ID: {user.id}\n\n"
        f"Нажмите кнопку для тестового платежа:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def debug_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback с полной отладкой"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    print(f"🔄 НАЧАЛО СОЗДАНИЯ ПЛАТЕЖА для {user_id}")
    
    # Шаг 1: Создаем в БД
    await query.edit_message_text("📦 Шаг 1: Создаю платеж в базе данных...")
    print("📦 Шаг 1: Создаю в БД...")
    
    db_result = create_payment_in_db_simple(user_id)
    
    if not db_result["success"]:
        print(f"❌ ПРОВАЛ ШАГ 1: {db_result.get('error')}")
        await query.edit_message_text(f"❌ Ошибка БД: {db_result.get('error')}")
        return
    
    payment_id = db_result["payment_id"]
    print(f"✅ Шаг 1 завершен: payment_id = {payment_id}")
    
    # Шаг 2: Создаем в ЮKassa
    await query.edit_message_text("🔗 Шаг 2: Создаю платеж в ЮKassa...")
    print("🔗 Шаг 2: Создаю в ЮKassa...")
    
    yk_result = create_yookassa_payment_debug(payment_id, user_id)
    
    if not yk_result["success"]:
        print(f"❌ ПРОВАЛ ШАГ 2: {yk_result.get('error')}")
        await query.edit_message_text(f"❌ Ошибка ЮKassa: {yk_result.get('error')}")
        return
    
    print(f"✅ Шаг 2 завершен: ссылка = {yk_result['confirmation_url']}")
    
    # Шаг 3: Показываем ссылку
    await query.edit_message_text("✅ Шаг 3: Отправляю ссылку...")
    
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=yk_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"debug_status_{payment_id}")]
    ]
    
    message = (
        f"✅ **ТЕСТОВЫЙ ПЛАТЕЖ СОЗДАН!**\n\n"
        f"📋 ID: `{payment_id}`\n"
        f"💰 Сумма: 1 рубль\n"
        f"🔗 Ссылка: {yk_result['confirmation_url'][:50]}...\n\n"
        f"**Нажмите кнопку для оплаты:**"
    )
    
    print(f"📤 Отправляю сообщение пользователю с ссылкой")
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    print(f"🎯 ВСЕ ШАГИ ЗАВЕРШЕНЫ УСПЕШНО!")

async def debug_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса с отладкой"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("debug_status_"):
        payment_id = query.data[13:]
        print(f"🔍 ПРОВЕРЯЮ СТАТУС: {payment_id}")
        
        try:
            response = requests.get(f"{API_URL}/api/payment-status/{payment_id}", timeout=10)
            print(f"📊 Ответ API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('payment', {}).get('status', 'unknown')
                print(f"📈 Статус платежа: {status}")
                
                await query.edit_message_text(f"📊 Статус платежа `{payment_id}`: **{status}**")
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                await query.edit_message_text(f"❌ Ошибка проверки: {response.status_code}")
        except Exception as e:
            print(f"🔥 Ошибка: {e}")
            await query.edit_message_text("❌ Ошибка подключения")

def main():
    """Запуск бота с отладкой"""
    print("=" * 70)
    print("🔧 БОТ ДЛЯ ОТЛАДКИ ПЛАТЕЖЕЙ")
    print("=" * 70)
    print(f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🔑 Токен: {'ЕСТЬ' if TOKEN else 'НЕТ!'}")
    print(f"🏪 Shop ID: {SHOP_ID}")
    print("=" * 70)
    
    if not TOKEN:
        print("❌ ОШИБКА: Нет токена бота!")
        return
    
    try:
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start_debug))
        app.add_handler(CommandHandler("debug", start_debug))
        app.add_handler(CallbackQueryHandler(debug_buy_callback, pattern="^debug_buy$"))
        app.add_handler(CallbackQueryHandler(debug_status_callback, pattern="^debug_status_"))
        
        print("✅ Бот запущен в режиме отладки")
        print("📱 Используйте команду /start или /debug")
        print("=" * 70)
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"🔥 КРИТИЧЕСКАЯ ОШИБКА: {e}")

if __name__ == "__main__":
    main()
