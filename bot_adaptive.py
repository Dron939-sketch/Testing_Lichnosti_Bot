#!/usr/bin/env python3
"""
Telegram Bot для платежной системы ЮKassa
Исправленная версия с поддержкой receipt для боевого режима
"""

import os
import sys
import time
import json
import base64
import logging
import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ApplicationBuilder
)

# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Уменьшаем логирование библиотек
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# ========== ПРОВЕРКА КОНФИГУРАЦИИ ==========
def check_configuration():
    """Проверяет все настройки перед запуском"""
    print("=" * 60)
    print("🤖 ЗАПУСК ТЕЛЕГРАМ БОТА")
    print("=" * 60)
    
    errors = []
    
    # Проверка токена
    if not TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN не установлен")
        print("❌ Токен бота: НЕ УСТАНОВЛЕН!")
    else:
        print(f"✅ Токен бота: установлен")
    
    # Проверка URL API
    if not API_URL:
        errors.append("⚠️ API_URL не установлен, используется по умолчанию")
    print(f"✅ API URL: {API_URL}")
    
    # Проверка доступности API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API доступен: {response.status_code}")
        else:
            errors.append(f"⚠️ API недоступен: код {response.status_code}")
            print(f"⚠️ API ответ: {response.status_code}")
    except Exception as e:
        errors.append(f"❌ API недоступен: {str(e)}")
        print(f"❌ API недоступен: {e}")
    
    # Проверка ЮKassa
    if not YOOKASSA_SHOP_ID:
        errors.append("❌ YOOKASSA_SHOP_ID не установлен")
        print("❌ Shop ID: НЕ УСТАНОВЛЕН!")
    else:
        print(f"✅ Shop ID: {YOOKASSA_SHOP_ID[:10]}...")
    
    if not YOOKASSA_SECRET_KEY:
        errors.append("❌ YOOKASSA_SECRET_KEY не установлен")
        print("❌ Secret Key: НЕ УСТАНОВЛЕН!")
    else:
        key_type = "ТЕСТОВЫЙ" if YOOKASSA_SECRET_KEY.startswith('test_') else "БОЕВОЙ"
        print(f"✅ Secret Key: {key_type}")
        if key_type == "БОЕВОЙ":
            print("💡 Режим: БОЕВОЙ (требуется receipt)")
        else:
            print("💡 Режим: ТЕСТОВЫЙ (receipt не требуется)")
    
    print("=" * 60)
    
    if errors:
        print("⚠️ Обнаружены ошибки конфигурации:")
        for error in errors:
            print(f"  {error}")
        return False
    
    print("✅ Конфигурация проверена успешно!")
    return True

# ========== ФУНКЦИИ ДЛЯ ЮKASSA ==========
def create_yookassa_payment(payment_id: str, user_id: int, amount: float = 1.0, email: str = None) -> dict:
    """Создает платеж в ЮKassa с receipt (для боевого режима)"""
    try:
        # Basic Auth для ЮKassa API v3
        auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Idempotence-Key': payment_id
        }
        
        # Формируем email для чека
        if not email:
            email = f"user_{user_id}@telegram.org"
        
        # Базовая структура платежа
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
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
            "description": f"Тестовый платеж #{payment_id}",
            "metadata": {
                "payment_id": payment_id,
                "user_id": user_id,
                "telegram_id": str(user_id)
            }
        }
        
        # Добавляем receipt если режим БОЕВОЙ
        if YOOKASSA_SECRET_KEY.startswith('live_'):
            payload["receipt"] = {
                "customer": {
                    "email": email
                },
                "items": [
                    {
                        "description": "Тестовый доступ к курсу ВАРИАТИКА",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": "1",  # НДС 20% (обязательно для РФ)
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }
                ]
            }
            logger.info(f"🛡️ Создаю платеж С receipt (боевой режим): {payment_id}")
        else:
            logger.info(f"🧪 Создаю платеж БЕЗ receipt (тестовый режим): {payment_id}")
        
        logger.info(f"📤 Отправляю в ЮKassa: {json.dumps(payload, indent=2)[:500]}...")
        
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📥 Ответ ЮKassa: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            yookassa_id = data.get('id')
            confirmation_url = data.get('confirmation', {}).get('confirmation_url')
            
            if not confirmation_url:
                return {
                    "success": False,
                    "error": "No confirmation URL in response",
                    "details": json.dumps(data)[:200]
                }
            
            # Сохраняем ID ЮKassa в базе
            try:
                save_response = requests.post(
                    f"{API_URL}/api/update-yookassa-id",
                    json={
                        "payment_id": payment_id,
                        "yookassa_id": yookassa_id,
                        "status": "waiting"
                    },
                    timeout=10
                )
                
                if save_response.status_code == 200:
                    logger.info(f"✅ ID сохранен в БД: {yookassa_id}")
                else:
                    logger.error(f"⚠️ Ошибка сохранения ID: {save_response.status_code} - {save_response.text}")
                    
            except Exception as e:
                logger.error(f"⚠️ Ошибка сохранения ID: {e}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "yookassa_id": yookassa_id,
                "confirmation_url": confirmation_url,
                "status": data.get('status'),
                "amount": amount
            }
        else:
            error_text = response.text[:500]
            logger.error(f"❌ Ошибка ЮKassa {response.status_code}: {error_text}")
            
            # Детализация ошибки для отладки
            print(f"🔥 ДЕТАЛИ ОШИБКИ ЮKASSA:")
            print(f"Код: {response.status_code}")
            print(f"Текст: {error_text}")
            print(f"Запрос: {json.dumps(payload, indent=2, ensure_ascii=False)[:1000]}")
            
            return {
                "success": False,
                "error": f"Ошибка {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Исключение при создании платежа: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }

# ========== ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ==========
def create_payment_in_db(user_id: int, amount: float = 1.0) -> dict:
    """Создает запись о платеже в базе данных"""
    try:
        timestamp = int(time.time())
        payment_id = f"test_{user_id}_{timestamp}"
        
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "email": f"user_{user_id}@telegram.org",
            "description": f"Тестовый платеж {amount} руб"
        }
        
        logger.info(f"📦 Создаю платеж в БД: {payment_id}")
        
        response = requests.post(
            f"{API_URL}/api/create-payment",
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Платеж создан в БД: {payment_id}")
            return {
                "success": True,
                "payment_id": payment_id,
                "email": f"user_{user_id}@telegram.org"
            }
        else:
            error_text = response.text[:200]
            logger.error(f"❌ Ошибка БД {response.status_code}: {error_text}")
            return {
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "details": error_text
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_payment_status_db(payment_id: str) -> dict:
    """Проверяет статус платежа"""
    try:
        response = requests.get(
            f"{API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Получаем статус из правильного места
            if 'payment' in data:
                status = data['payment'].get('status', 'unknown')
            else:
                status = data.get('status', 'unknown')
                
            return {
                "success": True,
                "status": status,
                "data": data
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": "Платеж не найден"
            }
        else:
            return {
                "success": False,
                "error": f"Ошибка: {response.status_code}",
                "details": response.text[:200]
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
    
    mode = "БОЕВОЙ" if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_') else "ТЕСТОВЫЙ"
    
    message_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        f"*Тестовая платежная система*\n\n"
        f"💰 *Сумма:* 1 рубль\n"
        f"🎯 *Режим:* {mode}\n"
        f"📡 *API:* `{API_URL}`\n\n"
        
        f"*Что проверяем:*\n"
        f"✅ Создание платежа в БД\n"
        f"✅ Интеграция с ЮKassa\n"
        f"✅ Отправка чека (если боевой режим)\n"
        f"✅ Обработка вебхуков\n"
        f"✅ Выдача доступа\n\n"
        
        f"Нажмите кнопку ниже для теста:"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def test_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка тестовой покупки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # Шаг 1: Создаем в БД
    await query.edit_message_text("📦 *Шаг 1/3: Создаю платеж в базе данных...*", parse_mode='Markdown')
    
    db_result = create_payment_in_db(user_id)
    if not db_result["success"]:
        error_msg = db_result.get('error', 'Неизвестная ошибка')
        details = db_result.get('details', '')
        error_text = f"❌ *Ошибка базы данных:*\n{error_msg}"
        if details:
            error_text += f"\n\n`{details[:100]}`"
        await query.edit_message_text(error_text, parse_mode='Markdown')
        return
    
    payment_id = db_result["payment_id"]
    email = db_result.get("email", f"user_{user_id}@telegram.org")
    
    # Шаг 2: Создаем в ЮKassa
    await query.edit_message_text("💳 *Шаг 2/3: Создаю платеж в ЮKassa...*", parse_mode='Markdown')
    
    # Определяем режим для сообщения
    mode = "БОЕВОЙ (с чеком)" if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_') else "ТЕСТОВЫЙ"
    await query.edit_message_text(f"💳 *Шаг 2/3: Создаю платеж в ЮKassa...*\n\n*Режим:* {mode}", parse_mode='Markdown')
    
    payment_result = create_yookassa_payment(payment_id, user_id, email=email)
    if not payment_result["success"]:
        error_msg = payment_result.get('error', 'Неизвестная ошибка')
        details = payment_result.get('details', '')
        
        # Формируем сообщение об ошибке
        error_text = f"❌ *Ошибка ЮKassa:*\n`{error_msg}`"
        
        if details:
            # Экранируем специальные символы для Markdown
            safe_details = details.replace('_', r'\_').replace('*', r'\*').replace('`', r'\`')
            error_text += f"\n\n*Детали:*\n`{safe_details[:150]}`"
        
        if "Receipt is missing" in details or "Квитанция отсутствует" in details:
            error_text += "\n\n💡 *Решение:* В боевом режиме ЮKassa требует чек по 54-ФЗ.\nИспользуйте тестовый ключ или добавьте receipt в запрос."
        
        await query.edit_message_text(error_text, parse_mode='Markdown')
        return
    
    # Шаг 3: Показываем ссылку
    keyboard = [
        [InlineKeyboardButton("💳 ОПЛАТИТЬ 1 РУБЛЬ", url=payment_result["confirmation_url"])],
        [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"status_{payment_id}")]
    ]
    
    # Информация о режиме
    mode_info = ""
    if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_'):
        safe_email = email.replace('_', r'\_').replace('@', r'\@')
        mode_info = f"📧 *Email для чека:* {safe_email}\n🛡️ *Режим:* Боевой (чек по 54-ФЗ)"
    else:
        mode_info = "🧪 *Режим:* Тестовый (чек не требуется)"
    
    message_text = (
        f"✅ *ПЛАТЕЖ СОЗДАН!*\n\n"
        f"*📋 ID:* `{payment_id}`\n"
        f"*👤 Пользователь:* {user_name}\n"
        f"*💰 Сумма:* 1 рубль\n"
        f"{mode_info}\n\n"
        f"*Для оплаты нажмите кнопку ниже:*\n"
        f"После оплаты чек придет на указанный email."
    )
    
    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса платежа"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("status_"):
        payment_id = query.data[7:]
        
        await query.edit_message_text(f"🔍 *Проверяю статус:*\n`{payment_id}`", parse_mode='Markdown')
        
        result = check_payment_status_db(payment_id)
        
        if not result["success"]:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await query.edit_message_text(f"❌ *Ошибка:* {error_msg}", parse_mode='Markdown')
            return
        
        status = result.get("status", "unknown")
        
        if status == "succeeded":
            message = (
                f"🎉 *ОПЛАЧЕНО!*\n\n"
                f"✅ Платеж `{payment_id}` успешно завершен!\n"
                f"💰 Сумма: 1 рубль\n\n"
                f"*🔓 ДОСТУП ОТКРЫТ!*\n"
                f"Тестовая цепочка работает корректно!\n\n"
                f"📧 Чек отправлен на email."
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
            message = f"📊 *Статус платежа:* `{status}`"
        
        await query.edit_message_text(message, parse_mode='Markdown')

async def check_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню проверки статуса"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📊 *Проверка статуса*\n\n"
        "Используйте команду:\n"
        "`/check ID_платежа`\n\n"
        "Или создайте новый платеж:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧪 Новый тестовый платеж", callback_data="test_buy")]])
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /check"""
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
        error_msg = result.get('error', 'Неизвестная ошибка')
        await update.message.reply_text(f"❌ Не удалось проверить платеж `{payment_id}`:\n{error_msg}")

# ========== ОБРАБОТЧИК ОШИБОК ==========
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Упрощенный обработчик ошибок"""
    error_msg = str(context.error)
    
    # Логируем все ошибки
    logger.error(f"Ошибка: {error_msg}")
    
    # Конфликт с другим ботом
    if "Conflict" in error_msg and "getUpdates" in error_msg:
        logger.warning("⚠️ Конфликт с другим ботом!")
        print("🔄 Ожидаю 10 секунд для разрешения конфликта...")
        await asyncio.sleep(10)
        
    # Уведомляем пользователя только если есть update
    if update and isinstance(update, Update):
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    "⚠️ Произошла ошибка, попробуйте снова через минуту"
                )
            elif update.message:
                await update.message.reply_text(
                    "⚠️ Произошла ошибка, попробуйте снова через минуту"
                )
        except:
            pass

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска"""
    print("=" * 70)
    print("🚀 VARIATICA PAYMENT BOT - ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("=" * 70)
    
    # Проверяем конфигурацию
    if not check_configuration():
        print("❌ Конфигурация неполная, выход...")
        sys.exit(1)
    
    try:
        # Создаем приложение
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("test", start))
        app.add_handler(CommandHandler("check", check_command))
        
        # Callback обработчики
        app.add_handler(CallbackQueryHandler(test_buy_callback, pattern="^test_buy$"))
        app.add_handler(CallbackQueryHandler(status_callback, pattern="^status_"))
        app.add_handler(CallbackQueryHandler(check_status_menu, pattern="^check_status_menu$"))
        
        # Обработчик ошибок
        app.add_error_handler(error_handler)
        
        print("✅ Бот запущен успешно!")
        print(f"📡 API: {API_URL}")
        
        # Информация о режиме
        if YOOKASSA_SECRET_KEY and YOOKASSA_SECRET_KEY.startswith('live_'):
            print(f"🛡️ Режим: БОЕВОЙ (требуется receipt)")
            print(f"💡 Используется чек по 54-ФЗ")
        else:
            print(f"🧪 Режим: ТЕСТОВЫЙ")
        
        print(f"⏰ Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print("📱 Используйте команду /start в Telegram")
        print("🧪 Нажмите 'ТЕСТОВАЯ ОПЛАТА' для проверки")
        print("=" * 70)
        
        # Запускаем с защитой от конфликтов
        app.run_polling(
            drop_pending_updates=True,  # ВАЖНО: очищаем очередь обновлений
            allowed_updates=['message', 'callback_query'],
            close_loop=False,
            stop_signals=[]
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        
    except Exception as e:
        logger.critical(f"Критическая ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        
        # Простой перезапуск через 10 секунд
        print(f"🔄 Перезапуск через 10 секунд...")
        time.sleep(10)
        
        # Перезапускаем процесс
        os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    main()
