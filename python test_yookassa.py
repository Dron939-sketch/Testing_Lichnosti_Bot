# test_yookassa.py
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_yookassa_connection():
    """Тест подключения к ЮKassa"""
    print("🧪 ТЕСТ ПОДКЛЮЧЕНИЯ К ЮKASSA")
    print("="*50)
    
    # Проверяем переменные
    required_vars = ['TELEGRAM_BOT_TOKEN', 'YOOKASSA_SHOP_ID', 'YOOKASSA_SECRET_KEY']
    
    for var in required_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        print(f"{status} {var}: {'установлен' if value else 'НЕ установлен'}")
        
        if value and var.endswith(('_KEY', '_TOKEN', '_ID')):
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"   Значение: {masked}")
    
    # Проверяем конфигурацию
    try:
        from config import Config
        config = Config()
        
        print("\n⚙️ КОНФИГУРАЦИЯ ПЛАТЕЖЕЙ:")
        print(f"   Shop ID установлен: {'✅' if config.YOOKASSA_SHOP_ID else '❌'}")
        print(f"   Secret Key установлен: {'✅' if config.YOOKASSA_SECRET_KEY else '❌'}")
        print(f"   Тестовый режим: {'🟡 ДА' if config.is_test_mode else '🟢 НЕТ'}")
        print(f"   Платежи включены: {'✅ ДА' if config.is_payment_enabled else '❌ НЕТ'}")
        
        if config.is_payment_enabled:
            print("\n🧪 Тестируем создание платежа...")
            from yookassa_api import YooKassaAPI
            
            yookassa = YooKassaAPI(config)
            result = yookassa.create_payment(
                user_id=999999999,
                description="Тестовый платеж из скрипта"
            )
            
            print(f"\n📊 РЕЗУЛЬТАТ:")
            print(f"   Успех: {'✅' if result['success'] else '❌'}")
            if result['success']:
                print(f"   ID платежа: {result['payment_id']}")
                print(f"   URL оплаты: {result['payment_url'][:50]}...")
                print(f"   Статус: {result['status']}")
            else:
                print(f"   Ошибка: {result.get('error', 'Неизвестно')}")
                print(f"   Детали: {result.get('details', 'Нет деталей')}")
        else:
            print("\n⚠️  Платежи не настроены, тест пропущен")
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yookassa_connection()
