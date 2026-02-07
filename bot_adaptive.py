"""
diagnostic.py - Диагностическая программа для проверки всей системы
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemDiagnostic:
    """Класс для диагностики всей платежной системы"""
    
    def __init__(self):
        self.api_url = os.getenv("API_URL", "https://testing-lichnosti-bot-1.onrender.com")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.yookassa_shop_id = os.getenv("YOOKASSA_SHOP_ID")
        self.yookassa_secret_key = os.getenv("YOOKASSA_SECRET_KEY")
        
        self.results = {}
    
    def print_header(self, text):
        """Печатает заголовок"""
        print("\n" + "="*70)
        print(f"🔍 {text}")
        print("="*70)
    
    def print_result(self, name, status, message=""):
        """Печатает результат проверки"""
        if status == "✅":
            print(f"{status} {name}: {message}")
            self.results[name] = {"status": "OK", "message": message}
        elif status == "❌":
            print(f"{status} {name}: {message}")
            self.results[name] = {"status": "ERROR", "message": message}
        elif status == "⚠️":
            print(f"{status} {name}: {message}")
            self.results[name] = {"status": "WARNING", "message": message}
        else:
            print(f"{status} {name}: {message}")
    
    def check_environment_variables(self):
        """Проверяет переменные окружения"""
        self.print_header("ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
        
        # API URL
        if self.api_url:
            self.print_result("API_URL", "✅", f"Установлен: {self.api_url}")
        else:
            self.print_result("API_URL", "❌", "Не установлен")
        
        # Bot Token
        if self.bot_token:
            self.print_result("TELEGRAM_BOT_TOKEN", "✅", f"Установлен: {self.bot_token[:10]}...")
        else:
            self.print_result("TELEGRAM_BOT_TOKEN", "❌", "Не установлен - бот не будет работать!")
        
        # YooKassa
        if self.yookassa_shop_id:
            self.print_result("YOOKASSA_SHOP_ID", "✅", f"Установлен: {self.yookassa_shop_id[:10]}...")
        else:
            self.print_result("YOOKASSA_SHOP_ID", "❌", "Не установлен - платежи ЮKassa не будут работать!")
        
        if self.yookassa_secret_key:
            self.print_result("YOOKASSA_SECRET_KEY", "✅", f"Установлен: {self.yookassa_secret_key[:10]}...")
        else:
            self.print_result("YOOKASSA_SECRET_KEY", "❌", "Не установлен - платежи ЮKassa не будут работать!")
    
    def check_api_connection(self):
        """Проверяет соединение с API"""
        self.print_header("ПРОВЕРКА СОЕДИНЕНИЯ С API")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_result("API Connection", "✅", 
                    f"Статус: {data.get('status', 'unknown')}, База: {data.get('database', 'unknown')}")
            else:
                self.print_result("API Connection", "❌", 
                    f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            self.print_result("API Connection", "❌", "Не удалось подключиться к API")
        except Exception as e:
            self.print_result("API Connection", "❌", f"Ошибка: {str(e)}")
    
    def check_database_tables(self):
        """Проверяет таблицы в базе данных"""
        self.print_header("ПРОВЕРКА БАЗЫ ДАННЫХ")
        
        try:
            response = requests.get(f"{self.api_url}/check-db", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    tables = data.get("tables", [])
                    table_status = data.get("table_status", {})
                    
                    # Проверяем основные таблицы
                    expected_tables = ['payments', 'user_access', 'yookassa_webhooks']
                    for table in expected_tables:
                        if table in tables:
                            self.print_result(f"Table: {table}", "✅", "Существует")
                        else:
                            self.print_result(f"Table: {table}", "❌", "Отсутствует")
                    
                    # Показываем структуру payments
                    if 'payments' in tables:
                        response_structure = requests.get(f"{self.api_url}/table-structure", timeout=10)
                        if response_structure.status_code == 200:
                            structure_data = response_structure.json()
                            if structure_data.get("success"):
                                columns = structure_data.get("columns", [])
                                self.print_result("Payments Structure", "✅", 
                                    f"{len(columns)} колонок, есть description: {structure_data.get('has_description')}")
                else:
                    self.print_result("Database Check", "❌", f"Ошибка: {data.get('error', 'Unknown')}")
            else:
                self.print_result("Database Check", "❌", f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Database Check", "❌", f"Ошибка: {str(e)}")
    
    def test_payment_creation(self):
        """Тестирует создание платежа"""
        self.print_header("ТЕСТ СОЗДАНИЯ ПЛАТЕЖА")
        
        test_payment_id = f"diagnostic_{int(datetime.now().timestamp())}"
        test_user_id = 999999
        
        payload = {
            "payment_id": test_payment_id,
            "user_id": test_user_id,
            "amount": 1.0,
            "email": "test@diagnostic.com",
            "description": "Тестовый платеж из диагностики"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/create-payment",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.print_result("Create Payment", "✅", 
                    f"Платеж создан: {data.get('payment_id')}, статус: {data.get('status')}")
                
                # Проверяем статус созданного платежа
                self.check_payment_status(test_payment_id)
            else:
                self.print_result("Create Payment", "❌", 
                    f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.print_result("Create Payment", "❌", f"Ошибка: {str(e)}")
    
    def check_payment_status(self, payment_id):
        """Проверяет статус платежа"""
        try:
            response = requests.get(f"{self.api_url}/api/payment-status/{payment_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    payment = data.get("payment", {})
                    self.print_result("Payment Status", "✅", 
                        f"Статус: {payment.get('status')}, User: {payment.get('user_id')}")
                else:
                    self.print_result("Payment Status", "❌", f"Ошибка: {data.get('error')}")
            else:
                self.print_result("Payment Status", "❌", f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Payment Status", "❌", f"Ошибка: {str(e)}")
    
    def test_yookassa_integration(self):
        """Тестирует интеграцию с ЮKassa"""
        self.print_header("ПРОВЕРКА ИНТЕГРАЦИИ С ЮKASSA")
        
        # Проверяем наличие библиотеки yookassa
        try:
            import yookassa
            self.print_result("YooKassa Library", "✅", f"Версия: {yookassa.__version__}")
        except ImportError:
            self.print_result("YooKassa Library", "❌", "Библиотека 'yookassa' не установлена")
            self.print_result("Quick Fix", "💡", "Добавьте в requirements.txt: yookassa==2.4.0")
            return
        
        # Проверяем конфигурацию
        if self.yookassa_shop_id and self.yookassa_secret_key:
            self.print_result("YooKassa Config", "✅", "Shop ID и Secret Key установлены")
            
            # Пробуем создать тестовый платеж
            try:
                from yookassa import Configuration, Payment
                
                Configuration.account_id = self.yookassa_shop_id
                Configuration.secret_key = self.yookassa_secret_key
                
                # Простой тестовый платеж
                test_payment_data = {
                    "amount": {
                        "value": "1.00",
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": "https://t.me/variatica_bot"
                    },
                    "capture": True,
                    "description": "Тестовый платеж из диагностики",
                    "metadata": {
                        "test": "diagnostic",
                        "timestamp": str(datetime.now().timestamp())
                    }
                }
                
                self.print_result("YooKassa Test", "⚠️", "Пробуем создать тестовый платеж...")
                
                # Пробуем создать платеж
                payment = Payment.create(test_payment_data)
                
                if hasattr(payment, 'id') and payment.id:
                    self.print_result("YooKassa Payment", "✅", 
                        f"Платеж создан! ID: {payment.id[:20]}..., Статус: {payment.status}")
                    
                    # Проверяем ссылку для оплаты
                    if hasattr(payment.confirmation, 'confirmation_url'):
                        self.print_result("Payment URL", "✅", 
                            f"Ссылка: {payment.confirmation.confirmation_url[:50]}...")
                    else:
                        self.print_result("Payment URL", "⚠️", "Нет ссылки для оплаты")
                else:
                    self.print_result("YooKassa Payment", "❌", "Не удалось создать платеж")
                    
            except Exception as e:
                error_msg = str(e)
                self.print_result("YooKassa Error", "❌", f"Ошибка: {error_msg[:100]}")
                
                # Анализируем ошибку
                if "receipt" in error_msg.lower():
                    self.print_result("Problem Detected", "🔧", "Проблема с чеком (receipt). Удалите receipt из платежа.")
                elif "authentication" in error_msg.lower():
                    self.print_result("Problem Detected", "🔧", "Проблема аутентификации. Проверьте Shop ID и Secret Key.")
                elif "invalid" in error_msg.lower():
                    self.print_result("Problem Detected", "🔧", "Неверные данные в запросе.")
        else:
            self.print_result("YooKassa Config", "❌", "Не установлены Shop ID или Secret Key")
    
    def check_webhook_endpoint(self):
        """Проверяет вебхук эндпоинт"""
        self.print_header("ПРОВЕРКА ВЕБХУК ЭНДПОИНТА")
        
        webhook_url = f"{self.api_url}/yookassa-webhook"
        
        # Проверяем, что эндпоинт существует
        try:
            # Отправляем GET запрос (должен вернуть 405 Method Not Allowed)
            response = requests.get(webhook_url, timeout=10)
            if response.status_code == 405:  # Method Not Allowed - это нормально для POST эндпоинта
                self.print_result("Webhook Endpoint", "✅", "Эндпоинт существует (405 Method Not Allowed)")
            else:
                self.print_result("Webhook Endpoint", "⚠️", f"Неожиданный статус: {response.status_code}")
        except Exception as e:
            self.print_result("Webhook Endpoint", "❌", f"Ошибка: {str(e)}")
        
        # Рекомендация по настройке вебхука в ЮKassa
        self.print_result("Webhook Setup", "💡", 
            f"В кабинете ЮKassa укажите: {webhook_url}")
        self.print_result("Webhook Events", "💡", 
            "Выберите события: payment.succeeded, payment.canceled")
    
    def generate_summary(self):
        """Генерирует итоговый отчет"""
        self.print_header("ИТОГОВЫЙ ОТЧЕТ")
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results.values() if r["status"] == "OK")
        errors = sum(1 for r in self.results.values() if r["status"] == "ERROR")
        warnings = sum(1 for r in self.results.values() if r["status"] == "WARNING")
        
        print(f"📊 Всего проверок: {total_tests}")
        print(f"✅ Успешно: {successful}")
        print(f"⚠️ Предупреждений: {warnings}")
        print(f"❌ Ошибок: {errors}")
        
        # Показываем ошибки
        if errors > 0:
            print("\n🔴 КРИТИЧЕСКИЕ ОШИБКИ:")
            for name, result in self.results.items():
                if result["status"] == "ERROR":
                    print(f"  • {name}: {result['message']}")
        
        # Показываем предупреждения
        if warnings > 0:
            print("\n🟡 ПРЕДУПРЕЖДЕНИЯ:")
            for name, result in self.results.items():
                if result["status"] == "WARNING":
                    print(f"  • {name}: {result['message']}")
        
        # Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ:")
        
        if not self.bot_token:
            print("  1. Установите TELEGRAM_BOT_TOKEN в переменные окружения Render")
        
        if not self.yookassa_shop_id or not self.yookassa_secret_key:
            print("  2. Установите YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY")
        
        if errors == 0 and self.yookassa_shop_id:
            print("  3. Настройте вебхук в кабинете ЮKassa:")
            print(f"     URL: {self.api_url}/yookassa-webhook")
            print("     События: payment.succeeded, payment.canceled")
        
        print("\n🚀 Следующие шаги:")
        print("  1. Запустите диагностику: python diagnostic.py")
        print("  2. Исправьте выявленные ошибки")
        print("  3. Запустите бота: python bot.py")
        print("  4. Протестируйте команду /buy в боте")
    
    def run_all_checks(self):
        """Запускает все проверки"""
        print("\n" + "="*70)
        print("🤖 ДИАГНОСТИКА ПЛАТЕЖНОЙ СИСТЕМЫ")
        print("="*70)
        
        # Запускаем проверки
        self.check_environment_variables()
        self.check_api_connection()
        self.check_database_tables()
        self.test_payment_creation()
        self.test_yookassa_integration()
        self.check_webhook_endpoint()
        
        # Итоговый отчет
        self.generate_summary()

def main():
    """Основная функция"""
    diagnostic = SystemDiagnostic()
    diagnostic.run_all_checks()

if __name__ == "__main__":
    main()
