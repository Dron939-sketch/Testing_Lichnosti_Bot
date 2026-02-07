#!/usr/bin/env python3
"""
Telegram Bot для боевого режима ЮKassa
Версия 5.1 - исправлена ошибка Markdown
"""

import os
import sys
import time
import json
import base64
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")  # 1262862
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")  # live_...

# ========== ФУНКЦИЯ ДЛЯ ЮKASSA API ==========
def create_yookassa_payment_test(payment_id: str, user_id: int, email: str = None) -> dict:
    """
    Создание ТЕСТОВОГО платежа (1 рубль) с ПРАВИЛЬНЫМ receipt
    """
    try:
        # Формируем email
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Basic Auth
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id,
            'User-Agent': 'TestBot/1.0'
        }
        
        # ВАЖНО: Для боевого режима НУЖЕН receipt даже для 1 рубля!
        payload = {
            "amount": {
                "value": "1.00",  # Тестовая сумма
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/variatica_bot"
            },
            "capture": True,
            "description": "Тестовая оплата курса ВАРИАТИКА",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id),
                "test": "true"
            },
            "receipt": {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": "Тестовый доступ к курсу ВАРИАТИКА",
                        "quantity": "1.00",
                        "amount": {
                            "value": "1.00",  # Важно: та же сумма что и в amount
                            "currency": "RUB"
                        },
                        "vat_code": 1,  # НДС 20% (обязательно для РФ)
                        "payment_subject": "service",  # Услуга
                        "payment_mode": "full_payment"
                    }
                ]
            }
        }
        
        logger.info(f"🔄 Создаю тестовый платеж {payment_id} на 1 рубль")
        
        # Отладочная информация
        print(f"📤 Отправляю в ЮKassa:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Сохраняем yookassa_id в БД
            try:
                requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={
                        "payment_id": payment_id,
                        "yookassa_id": data.get('id'),
                        "status": "waiting"
                    },
                    timeout=5
                )
                logger.info(f"✅ ID сохранен в БД: {data.get('id')}")
            except Exception as e:
                logger.error(f"⚠️ Ошибка сохранения ID: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": data.get('id'),
                "confirmation_url": data.get('confirmation', {}).get('confirmation_url'),
                "status": data.get('status'),
                "amount": "1.00"
            }
            
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            
            # Показываем детали ошибки для отладки
            print(f"🔥 ДЕТАЛИ ОШИБКИ:")
            print(f"Код: {response.status_code}")
            print(f"Текст: {error_text}")
            
            return {
                "success": False,
                "error": f"ЮKassa error {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)[:200]
        }

# ========== ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ==========
def create_payment_in_db(user_id: int, email: str = None) -> dict:
    """Создает тестовый платеж в базе данных"""
    try:
        timestamp = int(time.time())
        payment_id = f"test_{user_id}_{timestamp}"
        
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 1.00,  # Тестовая сумма
            "email": email,
            "description": "Тестовый платеж 1 рубль"
        }
        
        logger.info(f"📦 Создаю платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"✅ Платеж создан в БД: {payment_id}")
            return {
                "success": True,
                "payment_id": payment_id,
                "email": email
            }
        else:
            logger.error(f"❌ Ошибка БД {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа в БД"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('payment', {}).get('status', 'unknown')
            return {
                "success": True,
                "data": data,
                "status": status
            }
        else:
            return {
                "success": False,
                "error": f"Status: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========== TELEGRAM КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🧪 ТЕСТОВАЯ ОПЛАТА (1 рубль)", callback_data="test_buy")],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data="check_status_menu")]
    ]
    
    message_text = (
        "🧪 *ТЕСТОВЫЙ РЕЖИМ*\n\n"
        f"Привет, {user.first_name}!\n\n"
        "*🔍 Цель:* Проверить всю цепочку платежей\n"
        "*💳 Сумма:* 1 рубль\n"
        "*🎯 Что тестируем:*\n"
        "• Создание платежа в ЮKassa\n"
        "• Отправку чека (по 54-ФЗ)\n"
        "• Получение вебхуков\n"
        "• Обновление статуса в БД\n"
        "• Предоставление доступа\n\n"
        "Нажмите кнопку для теста:"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def test_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая покупка за 1 рубль"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    
    await query.edit_message_text("🧪 *Шаг 1/3:* Создаю тестовый платеж в базе данных...", parse_mode='Markdown')
    
    # Создаем в БД
    db_result = create_payment_in_db(user_id)
    
    if not db_result["success"]:
        await query.edit_message_text(
            f"❌ *Ошибка базы данных:*\n{db_result.get('error', 'Неизвестная ошибка')}",
            parse_mode='Markdown'
        )
        return
    
    payment_id = db_result["payment_id"]
    
    await query.edit_message_text("🧪 *Шаг 2/3:* Создаю платеж в ЮKassa (с чеком)...", parse_mode='Markdown')
    
    # Создаем в ЮKassa с правильным receipt
    payment_result = create_yookassa_payment_test(payment_id, user_id)
    
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        details = payment_result.get('details', '')
        
        error_text = f"❌ *Ошибка ЮKassa:*\n{error_msg}"
        if details:
            # Экранируем специальные символы в деталях ошибки
            safe_details = details.replace('_', r'\_').replace('*', r'\*').replace('[', r'\[').replace(']', r'\]')
            error_text += f"\n\n*Детали:*\n{safe_details[:150]}"
        
        await query.edit_message_text(error_text, parse_mode='Markdown')
        return
    
    await query.edit_message_text("🧪 *Шаг 3/3:* Формирую ссылку для оплаты...", parse_mode='Markdown')
    
    # Формируем кнопку
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус оплаты", callback_data=f"status_{payment_id}")],
        [InlineKeyboardButton("📋 Инструкция по оплате", callback_data="payment_instructions")]
    ]
    
    # Экранируем специальные символы в email
    safe_email = db_result.get('email', 'user@telegram.org').replace('_', r'\_').replace('@', r'\@')
    
    message_text = (
        f"✅ *ТЕСТОВЫЙ ПЛАТЕЖ ГОТОВ!*\n\n"
        f"*📋 ID платежа:* `{payment_id}`\n"
        f"*👤 Пользователь:* {user.first_name}\n"
        f"*💰 Сумма:* 1 рубль\n"
        f"*📧 Email для чека:* {safe_email}\n"
        f"*🎯 Режим:* Боевой (с чеком по 54-ФЗ)\n\n"
        f"*Нажмите кнопку для оплаты:*\n"
        f"После оплаты чек придет на указанный email.\n\n"
        f"⚠️ *ВАЖНО:* Используйте реальную карту, спишется 1 рубль."
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 Проверяю статус платежа `{payment_id}`...", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            await query.edit_message_text("❌ Не удалось проверить статус")
            return
        
        status = result.get("status", "unknown")
        
        if status == "succeeded":
            message = (
                f"🎉 *ОПЛАЧЕНО!*\n\n"
                f"✅ Платеж `{payment_id}` успешно завершен!\n"
                f"💰 Сумма: 1 рубль\n\n"
                f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                f"Тестовая цепочка работает корректно!\n\n"
                f"📧 Чек отправлен на ваш email."
            )
        elif status in ["pending", "waiting"]:
            message = (
                f"⏳ *ОЖИДАЕТ ОПЛАТЫ*\n\n"
                f"Платеж `{payment_id}` еще не оплачен.\n"
                f"💰 Сумма: 1 рубль\n\n"
                f"*Для оплаты нажмите кнопку:*"
            )
            keyboard = [[InlineKeyboardButton("💳 Оплатить 1 рубль", callback_data="test_buy")]]
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        else:
            message = f"📊 Статус платежа `{payment_id}`: *{status}*"
        
        await query.edit_message_text(message, parse_mode='Markdown')

async def payment_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Инструкция по оплате"""
    query = update.callback_query
    await query.answer()
    
    instructions = (
        "💳 *ИНСТРУКЦИЯ ПО ТЕСТОВОЙ ОПЛАТЕ*\n\n"
        
        "*Для теста используйте:*\n"
        "1. *Реальную банковскую карту*\n"
        "2. *Сумма:* 1 (один) рубль\n"
        "3. *Что произойдет:*\n"
        "   - Банк спишет 1 рубль\n"
        "   - ЮKassa отправит нам уведомление\n"
        "   - Мы получим чек по 54-ФЗ\n"
        "   - Статус обновится в базе\n"
        "   - Вам откроется доступ\n\n"
        
        "*Шаги оплаты:*\n"
        "1. Нажмите 'Оплатить 1 рубль'\n"
        "2. На странице ЮKassa введите данные карты\n"
        "3. Подтвердите платеж\n"
        "4. Вернитесь в бот и нажмите 'Проверить статус'\n\n"
        
        "*Чек (по закону 54-ФЗ):*\n"
        "• Чек придет на email, указанный при регистрации\n"
        "• В чеке будет указано: 'Тестовый доступ к курсу ВАРИАТИКА'\n"
        "• Сумма: 1 рубль (включая НДС 20%)\n\n"
        
        "*После успешной оплаты:*\n"
        "Вы увидите статус 'ОПЛАЧЕНО' и получите доступ."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад к оплате", callback_data="test_buy")]]
    
    await query.edit_message_text(
        instructions,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check [payment_id]"""
    if not context.args:
        await update.message.reply_text(
            "Использование: `/check ID_платежа`\n\n"
            "Пример: `/check test_532205848_1234567890`",
            parse_mode='Markdown'
        )
        return
    
    payment_id = context.args[0]
    result = check_payment_status_db(payment_id)
    
    if result["success"]:
        status = result.get("status", "unknown")
        await update.message.reply_text(f"Статус платежа `{payment_id}`: *{status}*", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"Не удалось проверить платеж `{payment_id}`")

async def check_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню проверки статуса"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 *Проверка статуса платежа*\n\n"
        "Для проверки статуса:\n"
        "1. Используйте команду `/check ID_платежа`\n"
        "2. Или создайте новый платеж\n\n"
        "ID платежа выглядит так: `test_123456789_1234567890`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧪 Создать тестовый платеж", callback_data="test_buy")]])
    )

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск тестового бота"""
    print("=" * 70)
    print("🤖 TELEGRAM БОТ ДЛЯ ТЕСТИРОВАНИЯ ПЛАТЕЖЕЙ")
    print("=" * 70)
    print(f"💳 РЕЖИМ: БОЕВОЙ (с чеком 54-ФЗ)")
    print(f"💰 СУММА: 1 рубль для теста")
    print(f"⏰ Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Проверка настроек
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        sys.exit(1)
    
    print(f"✅ Токен бота: установлен")
    print(f"🔗 API URL: {API_URL}")
    print(f"🏪 Shop ID: {'установлен' if YOOKASSA_SHOP_ID else 'НЕТ!'}")
    print(f"🔑 Secret Key: {'установлен' if YOOKASSA_SECRET_KEY else 'НЕТ!'}")
    
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        print("⚠️  ВНИМАНИЕ: Данные ЮKassa неполные!")
        print("Платежи могут не работать")
    
    print("=" * 70)
    print("🔄 Запуск бота...")
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("test", start))
        app.add_handler(CommandHandler("check", check_command))
        
        # Callback обработчики
        app.add_handler(CallbackQueryHandler(test_buy_callback, pattern="^test_buy$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(payment_instructions, pattern="^payment_instructions$"))
        app.add_handler(CallbackQueryHandler(check_status_menu, pattern="^check_status_menu$"))
        
        # Обработчик ошибок
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Обработчик ошибок"""
            logger.error(f"Ошибка при обработке обновления {update}: {context.error}")
            
            if update and hasattr(update, 'callback_query') and update.callback_query:
                try:
                    await update.callback_query.message.reply_text(
                        f"❌ Произошла ошибка: {str(context.error)[:100]}"
                    )
                except:
                    pass
        
        app.add_error_handler(error_handler)
        
        print("✅ Бот запущен!")
        print("📱 Используйте команду /start")
        print("🧪 Для теста нажмите 'ТЕСТОВАЯ ОПЛАТА'")
        print("=" * 70)
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПУСКА: {e}")
        import traceback
        traceback.print_exc()
        print("Перезапуск через 10 секунд...")
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
