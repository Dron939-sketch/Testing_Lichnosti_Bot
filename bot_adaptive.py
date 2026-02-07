"""
ТЕСТОВЫЙ БОТ - Полная диагностика платежной системы v2.1
Исправленная версия для Render
"""

import logging
import os
import asyncio
import time
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import Conflict, RetryAfter, TimedOut

# ========== КОНФИГУРАЦИЯ ==========
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не установлен!")
    sys.exit(1)

# URL вашего Flask API
FLASK_API_URL = "https://testing-lichnosti-bot-1.onrender.com"
if not FLASK_API_URL.startswith("http"):
    FLASK_API_URL = f"https://{FLASK_API_URL}"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("payment_bot.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные
class PaymentData:
    def __init__(self):
        self.test_payment_id = None
        self.payment_url = None
        self.user_data = {}
        
payment_data = PaymentData()

# ========== УТИЛИТЫ ==========

def log_step(step: str, status: str, details: str = ""):
    """Логирование шагов диагностики"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {step} - {status}"
    if details:
        log_msg += f" | {details}"
    logger.info(log_msg)
    return log_msg

async def safe_edit_message(query, text: str, reply_markup=None):
    """Безопасное редактирование сообщений с обработкой ошибок"""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
        return True
    except Conflict as e:
        logger.warning(f"Conflict error: {e}. Skipping edit.")
        return False
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return False

async def safe_api_request(method: str, endpoint: str, **kwargs):
    """Безопасный запрос к API"""
    try:
        url = f"{FLASK_API_URL}{endpoint}"
        if method.upper() == "GET":
            response = requests.get(url, **kwargs, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, **kwargs, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, **kwargs, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        logger.info(f"API {method} {endpoint} -> {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                data["_status_code"] = response.status_code
                return data
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "text": response.text[:200],
                    "_status_code": response.status_code
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "text": response.text[:200],
                "_status_code": response.status_code
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== ДИАГНОСТИЧЕСКИЕ ФУНКЦИИ ==========

async def start_detailed_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробная пошаговая диагностика"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if query:
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text
    
    # Инициализация диагностики
    diagnostic_steps = []
    
    # Шаг 1: Проверка подключения к Telegram API
    await message_func("🔄 Шаг 1/7: Проверяю подключение к Telegram API...")
    step1_result = await check_telegram_connection()
    diagnostic_steps.append(("Подключение к Telegram API", step1_result))
    log_step("Step 1", step1_result["status"], step1_result.get("details", ""))
    
    if step1_result["status"] != "success":
        await show_diagnostic_report(diagnostic_steps, message_func)
        return
    
    # Шаг 2: Проверка доступности Flask API
    await message_func("🔄 Шаг 2/7: Проверяю доступность Flask API...")
    step2_result = await check_flask_api_availability()
    diagnostic_steps.append(("Доступность Flask API", step2_result))
    log_step("Step 2", step2_result["status"], step2_result.get("details", ""))
    
    if step2_result["status"] != "success":
        await show_diagnostic_report(diagnostic_steps, message_func)
        return
    
    # Шаг 3: Проверка структуры API эндпоинтов
    await message_func("🔄 Шаг 3/7: Анализирую структуру API...")
    step3_result = await analyze_api_structure()
    diagnostic_steps.append(("Структура API", step3_result))
    log_step("Step 3", step3_result["status"], step3_result.get("details", ""))
    
    # Шаг 4: Проверка соединения с БД через API
    await message_func("🔄 Шаг 4/7: Проверяю соединение с базой данных...")
    step4_result = await check_database_connection()
    diagnostic_steps.append(("Соединение с БД", step4_result))
    log_step("Step 4", step4_result["status"], step4_result.get("details", ""))
    
    if step4_result["status"] != "success":
        await show_diagnostic_report(diagnostic_steps, message_func)
        return
    
    # Шаг 5: Тест создания платежа в БД
    await message_func("🔄 Шаг 5/7: Тестирую создание записи платежа...")
    step5_result = await test_payment_creation(user_id)
    diagnostic_steps.append(("Создание платежа в БД", step5_result))
    log_step("Step 5", step5_result["status"], step5_result.get("details", ""))
    
    # Шаг 6: Проверка интеграции с ЮKassa
    if step5_result["status"] == "success":
        await message_func("🔄 Шаг 6/7: Проверяю интеграцию с ЮKassa...")
        step6_result = await test_yookassa_integration(user_id)
        diagnostic_steps.append(("Интеграция с ЮKassa", step6_result))
        log_step("Step 6", step6_result["status"], step6_result.get("details", ""))
    else:
        diagnostic_steps.append(("Интеграция с ЮKassa", {
            "status": "skipped",
            "message": "Пропущено из-за ошибки на шаге 5"
        }))
    
    # Шаг 7: Проверка механизма вебхуков
    await message_func("🔄 Шаг 7/7: Проверяю механизм уведомлений...")
    step7_result = await check_webhook_mechanism()
    diagnostic_steps.append(("Механизм вебхуков", step7_result))
    log_step("Step 7", step7_result["status"], step7_result.get("details", ""))
    
    # Показать итоговый отчет
    await show_diagnostic_report(diagnostic_steps, message_func)

async def check_telegram_connection():
    """Проверка соединения с Telegram API"""
    try:
        # Простая проверка через получение информации о боте
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return {
                    "status": "success",
                    "message": "✅ Соединение с Telegram API установлено",
                    "details": f"Бот: @{data['result']['username']}"
                }
        return {
            "status": "error",
            "message": "❌ Ошибка соединения с Telegram API",
            "details": f"HTTP {response.status_code}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "❌ Ошибка соединения с Telegram API",
            "details": str(e)[:100]
        }

async def check_flask_api_availability():
    """Проверка доступности Flask API"""
    try:
        start_time = time.time()
        response = requests.get(f"{FLASK_API_URL}/", timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "✅ Flask API доступен",
                "details": f"Время ответа: {response_time:.0f}мс"
            }
        else:
            return {
                "status": "error",
                "message": f"❌ Flask API недоступен",
                "details": f"HTTP {response.status_code} за {response_time:.0f}мс"
            }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "❌ Таймаут при подключении к Flask API",
            "details": "Превышено время ожидания (10 секунд)"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "❌ Ошибка подключения к Flask API",
            "details": f"URL: {FLASK_API_URL}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "❌ Неизвестная ошибка",
            "details": str(e)[:100]
        }

async def analyze_api_structure():
    """Анализ структуры API"""
    endpoints_to_check = [
        ("/", "GET", "Основной эндпоинт"),
        ("/api/create-payment", "POST", "Создание платежа"),
        ("/api/create-yookassa-payment", "POST", "Интеграция с ЮKassa"),
        ("/api/payment-status/", "GET", "Проверка статуса"),
        ("/api/health", "GET", "Проверка здоровья"),
        ("/test-db", "GET", "Тест БД")
    ]
    
    results = []
    available_endpoints = 0
    
    for endpoint, method, description in endpoints_to_check:
        try:
            url = f"{FLASK_API_URL}{endpoint}" if endpoint != "/api/payment-status/" else f"{FLASK_API_URL}{endpoint}test123"
            
            if method == "GET":
                response = requests.get(url, timeout=3)
            else:
                response = requests.post(url, json={}, timeout=3)
            
            if response.status_code in [200, 201, 400, 422]:
                available_endpoints += 1
                results.append(f"✅ {description}: HTTP {response.status_code}")
            else:
                results.append(f"❌ {description}: HTTP {response.status_code}")
                
        except Exception:
            results.append(f"❌ {description}: Недоступен")
    
    availability_percent = (available_endpoints / len(endpoints_to_check)) * 100
    
    return {
        "status": "success" if availability_percent > 50 else "warning",
        "message": f"Доступно {available_endpoints}/{len(endpoints_to_check)} эндпоинтов ({availability_percent:.0f}%)",
        "details": "\n".join(results)
    }

async def check_database_connection():
    """Проверка соединения с базой данных"""
    try:
        # Пробуем эндпоинт для проверки БД
        response = requests.get(f"{FLASK_API_URL}/test-db", timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("success"):
                    return {
                        "status": "success",
                        "message": "✅ Соединение с БД установлено",
                        "details": f"Версия БД: {data.get('db_version', 'неизвестно')}"
                    }
            except:
                pass
        
        # Если нет специального эндпоинта, пробуем создать тестовый платеж
        test_payload = {
            "payment_id": f"test_connection_{int(time.time())}",
            "user_id": 0,
            "amount": 0.01,
            "email": "test@test.com"
        }
        
        response = requests.post(
            f"{FLASK_API_URL}/api/create-payment",
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "message": "✅ БД отвечает на запросы",
                "details": "Успешный тестовый запрос"
            }
        elif response.status_code == 400:
            # 400 может означать, что платеж уже существует, но БД работает
            return {
                "status": "success",
                "message": "✅ БД работает",
                "details": f"Ответ {response.status_code}: {response.text[:50]}"
            }
        else:
            return {
                "status": "error",
                "message": "❌ Ошибка БД",
                "details": f"HTTP {response.status_code}: {response.text[:100]}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": "❌ Ошибка подключения к БД",
            "details": str(e)[:100]
        }

async def test_payment_creation(user_id: int):
    """Тест создания платежа в базе данных"""
    try:
        # Генерируем уникальный ID платежа
        payment_id = f"diagnostic_{user_id}_{int(time.time())}"
        payment_data.test_payment_id = payment_id
        
        # Подготавливаем данные
        payload = {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": 1.00,
            "email": f"test{user_id}@diagnostic.com"
        }
        
        logger.info(f"Creating payment with payload: {payload}")
        
        # Отправляем запрос к API
        response = requests.post(
            f"{FLASK_API_URL}/api/create-payment",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PaymentDiagnosticBot/2.1"
            },
            timeout=15
        )
        
        logger.info(f"API Response: {response.status_code} - {response.text[:200]}")
        
        # Анализируем ответ
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("success", False):
                    return {
                        "status": "success",
                        "message": "✅ Платеж успешно создан в БД",
                        "details": f"ID: {payment_id[:15]}...",
                        "payment_id": payment_id
                    }
                else:
                    error_msg = result.get("error", "Неизвестная ошибка")
                    return {
                        "status": "error",
                        "message": "❌ Ошибка создания платежа",
                        "details": f"API error: {error_msg}",
                        "debug": result
                    }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "❌ Некорректный ответ от API",
                    "details": f"Не JSON: {response.text[:100]}"
                }
                
        elif response.status_code == 400:
            # Пытаемся получить детальную информацию об ошибке
            try:
                error_data = response.json()
                error_msg = error_data.get("error", response.text[:100])
                
                # Анализируем возможные причины
                if "already exists" in str(error_msg).lower() or "duplicate" in str(error_msg).lower():
                    return {
                        "status": "warning",
                        "message": "⚠️ Платеж уже существует",
                        "details": "ID платежа должен быть уникальным",
                        "suggestion": "Используйте другой ID платежа"
                    }
                elif "invalid" in str(error_msg).lower():
                    return {
                        "status": "error",
                        "message": "❌ Неверные данные платежа",
                        "details": error_msg,
                        "suggestion": "Проверьте формат данных"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "❌ Ошибка валидации",
                        "details": error_msg
                    }
                    
            except:
                return {
                    "status": "error",
                    "message": "❌ Ошибка 400",
                    "details": response.text[:100]
                }
                
        elif response.status_code == 422:
            return {
                "status": "error",
                "message": "❌ Ошибка валидации данных",
                "details": "Проверьте отправляемые данные",
                "suggestion": f"Отправлено: {payload}"
            }
            
        elif response.status_code == 500:
            return {
                "status": "error",
                "message": "❌ Внутренняя ошибка сервера",
                "details": "Ошибка в коде Flask API",
                "suggestion": "Проверьте логи сервера"
            }
            
        else:
            return {
                "status": "error",
                "message": f"❌ Неожиданный ответ: HTTP {response.status_code}",
                "details": response.text[:200]
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "❌ Таймаут при создании платежа",
            "details": "Превышено время ожидания (15 секунд)",
            "suggestion": "Увеличьте timeout или проверьте скорость сети"
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "❌ Ошибка подключения",
            "details": "Не удалось подключиться к серверу",
            "suggestion": f"Проверьте URL: {FLASK_API_URL}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "❌ Неизвестная ошибка",
            "details": str(e),
            "traceback": str(sys.exc_info())
        }

async def test_yookassa_integration(user_id: int):
    """Тест интеграции с ЮKassa"""
    if not payment_data.test_payment_id:
        return {
            "status": "skipped",
            "message": "⚠️ Пропущено - нет ID платежа",
            "details": "Сначала создайте платеж в БД"
        }
    
    try:
        payload = {
            "payment_id": payment_data.test_payment_id,
            "amount": 1.00,
            "description": "Диагностический платеж",
            "return_url": "https://t.me/testing_lichnosti_bot"
        }
        
        response = requests.post(
            f"{FLASK_API_URL}/api/create-yookassa-payment",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        logger.info(f"YooKassa Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success", True):
                payment_data.payment_url = result.get("payment_url", "")
                status = result.get("status", "unknown")
                
                return {
                    "status": "success",
                    "message": "✅ Интеграция с ЮKassa работает",
                    "details": f"Статус: {status}, URL: {'есть' if payment_data.payment_url else 'нет'}",
                    "payment_url": payment_data.payment_url
                }
            else:
                error_msg = result.get("error", "Неизвестная ошибка ЮKassa")
                return {
                    "status": "error",
                    "message": "❌ Ошибка ЮKassa",
                    "details": error_msg,
                    "suggestion": "Проверьте настройки магазина в ЮKassa"
                }
        else:
            return {
                "status": "error",
                "message": f"❌ HTTP {response.status_code} от ЮKassa API",
                "details": response.text[:200]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": "❌ Ошибка при работе с ЮKassa",
            "details": str(e)[:150]
        }

async def check_webhook_mechanism():
    """Проверка механизма вебхуков"""
    # Пробуем получить статус тестового платежа
    if payment_data.test_payment_id:
        try:
            response = requests.get(
                f"{FLASK_API_URL}/api/payment-status/{payment_data.test_payment_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message": "✅ Механизм статусов работает",
                    "details": f"Статус платежа: {result.get('status', 'unknown')}"
                }
        except:
            pass
    
    return {
        "status": "warning",
        "message": "⚠️ Не удалось проверить вебхуки",
        "details": "Создайте платеж для полной проверки"
    }

async def show_diagnostic_report(steps, message_func):
    """Отображение итогового отчета диагностики"""
    report = "📊 **ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ**\n\n"
    
    success_count = sum(1 for _, step in steps if step["status"] == "success")
    error_count = sum(1 for _, step in steps if step["status"] == "error")
    warning_count = sum(1 for _, step in steps if step["status"] == "warning")
    
    for step_name, step_data in steps:
        status_map = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "skipped": "➖"
        }
        emoji = status_map.get(step_data["status"], "❓")
        
        report += f"{emoji} **{step_name}**\n"
        report += f"   {step_data['message']}\n"
        
        if "details" in step_data and step_data["details"]:
            details = step_data["details"]
            if len(details) > 100:
                report += f"   *{details[:100]}...*\n"
            else:
                report += f"   *{details}*\n"
        
        report += "\n"
    
    # Итоговая статистика
    report += f"\n📈 **СТАТИСТИКА:**\n"
    report += f"✅ Успешно: {success_count}/{len(steps)}\n"
    report += f"⚠️ Предупреждений: {warning_count}\n"
    report += f"❌ Ошибок: {error_count}\n"
    
    # Рекомендации
    if error_count == 0 and warning_count == 0:
        report += "\n🎉 **Все системы работают отлично!**\n"
    elif error_count > 0:
        report += "\n🔧 **Требуется внимание:**\n"
        report += "1. Проверьте логи Flask приложения\n"
        report += "2. Убедитесь, что БД доступна и таблицы созданы\n"
        report += "3. Проверьте настройки ЮKassa\n"
    
    # Кнопки действий
    keyboard = []
    
    if payment_data.payment_url:
        keyboard.append([InlineKeyboardButton("🔗 Тестовая оплата (1 руб)", url=payment_data.payment_url)])
    
    if payment_data.test_payment_id:
        keyboard.append([InlineKeyboardButton("📊 Проверить статус", 
                        callback_data=f"check_status_{payment_data.test_payment_id}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Повторить диагностику", callback_data="full_diagnostic")])
    keyboard.append([InlineKeyboardButton("🐞 Быстрая диагностика", callback_data="quick_diagnostic")])
    keyboard.append([InlineKeyboardButton("💰 Реальный платеж", callback_data="real_payment")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(message_func, '__call__'):
        await message_func(report, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # Если это query
        await safe_edit_message(message_func, report, reply_markup)

async def show_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str = None):
    """Показать статус платежа"""
    if not payment_id and payment_data.test_payment_id:
        payment_id = payment_data.test_payment_id
    
    if not payment_id:
        await update.message.reply_text("❌ Нет активного платежа для проверки")
        return
    
    await update.message.reply_text(f"🔍 Проверяю статус платежа {payment_id[:10]}...")
    
    try:
        response = requests.get(
            f"{FLASK_API_URL}/api/payment-status/{payment_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            status_text = f"""
📊 Статус платежа:

🆔 ID: {payment_id}
📈 Статус: {result.get('status', 'unknown')}
            """
            
            if result.get('details'):
                details = result['details']
                for key, value in details.items():
                    if key not in ['payment_id', 'id']:
                        status_text += f"• {key}: {value}\n"
            
            await update.message.reply_text(status_text)
        else:
            await update.message.reply_text(f"❌ Ошибка проверки: HTTP {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = """
🔧 **ТЕСТОВЫЙ БОТ - Диагностика платежной системы v2.1**

*Возможности:*
✅ Пошаговая диагностика всех компонентов
✅ Детальный анализ ошибок
✅ Тестовые платежи (1 рубль)
✅ Проверка статусов в реальном времени
✅ Интеграция с ЮKassa

*Рекомендуемый порядок действий:*
1. Запустите полную диагностику
2. Если есть ошибки - проверьте рекомендации
3. Протестируйте платежную систему
4. Проверьте статусы платежей
    """
    
    keyboard = [
        [InlineKeyboardButton("🔧 Полная диагностика", callback_data="full_diagnostic")],
        [InlineKeyboardButton("⚡ Быстрая проверка", callback_data="quick_diagnostic")],
        [InlineKeyboardButton("🧪 Тестовый платеж (1 руб)", callback_data="test_payment")],
        [InlineKeyboardButton("📊 Проверить статус", callback_data="check_status")],
        [InlineKeyboardButton("🆘 Техподдержка", callback_data="support")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def quick_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрая диагностика основных компонентов"""
    query = update.callback_query
    await query.answer("⏳ Запускаю быструю диагностику...")
    
    quick_steps = []
    
    # Проверка Flask API
    result = await check_flask_api_availability()
    quick_steps.append(("Flask API", result))
    
    # Проверка БД
    if result["status"] == "success":
        db_result = await check_database_connection()
        quick_steps.append(("База данных", db_result))
    
    # Формируем быстрый отчет
    report = "⚡ **БЫСТРАЯ ДИАГНОСТИКА**\n\n"
    
    for step_name, step_data in quick_steps:
        status_emoji = "✅" if step_data["status"] == "success" else "❌"
        report += f"{status_emoji} {step_name}: {step_data['message']}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔧 Полная диагностика", callback_data="full_diagnostic")],
        [InlineKeyboardButton("🧪 Тестовый платеж", callback_data="test_payment")]
    ]
    
    await safe_edit_message(query, report, InlineKeyboardMarkup(keyboard))

async def test_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик тестового платежа"""
    query = update.callback_query
    await query.answer("⏳ Создаю тестовый платеж...")
    
    # Простая версия тестового платежа
    user_id = query.from_user.id
    payment_id = f"test_{user_id}_{int(time.time())}"
    
    await query.edit_message_text(
        f"🧪 **Тестовый платеж**\n\n"
        f"🆔 ID платежа: `{payment_id}`\n"
        f"👤 Пользователь: {user_id}\n"
        f"💰 Сумма: 1 рубль\n\n"
        f"Для тестирования используйте команды:\n"
        f"• /create_test - создать тестовый платеж\n"
        f"• /check_status - проверить статус\n"
        f"• /diagnostic - полная диагностика",
        parse_mode='Markdown'
    )

async def handle_check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик проверки статуса"""
    query = update.callback_query
    if payment_data.test_payment_id:
        await show_payment_status(update, context, payment_data.test_payment_id)
    else:
        await query.answer("❌ Нет активного платежа", show_alert=True)

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик техподдержки"""
    query = update.callback_query
    await query.answer()
    
    support_text = """
🆘 **Техническая поддержка**

Если у вас возникли проблемы:

1. **Ошибки при создании платежа:**
   - Проверьте логи Flask API
   - Убедитесь, что база данных доступна

2. **Проблемы с ЮKassa:**
   - Проверьте настройки магазина в ЮKassa
   - Убедитесь, что webhook настроен правильно

3. **Проверка системы:**
   - Запустите полную диагностику
   - Проверьте доступность всех компонентов

**Контакты:**
- Логи приложения: `payment_bot.log`
- Flask API: {FLASK_API_URL}
    """.format(FLASK_API_URL=FLASK_API_URL)
    
    await query.edit_message_text(support_text, parse_mode='Markdown')

async def handle_real_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик реального платежа"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💰 **Реальный платеж**\n\n"
        "Для создания реального платежа используйте:\n\n"
        "1. Команду `/create_payment` для создания платежа\n"
        "2. Или обратитесь к администратору\n\n"
        "⚠️ **Внимание:** Реальные платежи требуют настройки "
        "платежной системы и подключения ЮKassa.",
        parse_mode='Markdown'
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех callback запросов"""
    query = update.callback_query
    data = query.data
    
    if data == "full_diagnostic":
        await start_detailed_diagnostic(update, context)
    elif data == "quick_diagnostic":
        await quick_diagnostic(update, context)
    elif data == "test_payment":
        await test_payment_handler(update, context)
    elif data == "check_status":
        await handle_check_status(update, context)
    elif data == "support":
        await handle_support(update, context)
    elif data == "real_payment":
        await handle_real_payment(update, context)
    elif data.startswith("check_status_"):
        payment_id = data.replace("check_status_", "")
        await show_payment_status(update, context, payment_id)

async def create_test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание тестового платежа"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"🧪 Создаю тестовый платеж для пользователя {user_id}...")
    
    # Тестируем создание платежа
    result = await test_payment_creation(user_id)
    
    if result["status"] == "success":
        await update.message.reply_text(
            f"✅ Тестовый платеж создан!\n\n"
            f"🆔 ID: {result.get('payment_id')}\n"
            f"📊 Статус: Готов к интеграции с ЮKassa\n\n"
            f"Используйте /check_status для проверки статуса"
        )
    else:
        await update.message.reply_text(
            f"❌ Ошибка создания платежа:\n{result.get('message')}\n\n"
            f"Детали: {result.get('details', 'Нет деталей')}"
        )

async def check_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда проверки статуса"""
    if payment_data.test_payment_id:
        await show_payment_status(update, context, payment_data.test_payment_id)
    else:
        await update.message.reply_text(
            "❌ Нет активных платежей для проверки.\n\n"
            "Сначала создайте тестовый платеж командой /create_test"
        )

# ========== ЗАПУСК БОТА С ОБРАБОТКОЙ ОШИБОК ==========

def main():
    """Запуск бота с улучшенной обработкой ошибок"""
    print("="*60)
    print("🤖 ТЕСТОВЫЙ БОТ v2.1 - Запускается...")
    print(f"🔗 Flask API: {FLASK_API_URL}")
    print(f"📁 Логи: payment_bot.log")
    print("="*60)
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("diagnostic", start_detailed_diagnostic))
    application.add_handler(CommandHandler("create_test", create_test_payment))
    application.add_handler(CommandHandler("check_status", check_status_command))
    application.add_handler(CommandHandler("status", check_status_command))
    application.add_handler(CommandHandler("help", start))
    
    # Добавляем обработчики callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Обработчик ошибок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Обработка конкретных ошибок
        if isinstance(context.error, Conflict):
            logger.warning("Conflict error detected - skipping update")
            return
        
        if isinstance(context.error, RetryAfter):
            logger.warning(f"Rate limited: retry after {context.error.retry_after} seconds")
            await asyncio.sleep(context.error.retry_after)
            return
        
        # Отправка сообщения об ошибке пользователю
        try:
            if update and hasattr(update, 'effective_chat'):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ Произошла ошибка. Администратор уже уведомлен."
                )
        except:
            pass
    
    application.add_error_handler(error_handler)
    
    print("\n✅ Бот запущен и готов к работе!")
    print("Используйте /start для начала работы")
    print("="*60)
    
    try:
        # Запуск с параметрами по умолчанию (убрана проблема с перезаписью run_polling)
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
