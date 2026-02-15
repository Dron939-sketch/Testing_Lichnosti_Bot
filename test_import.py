#!/usr/bin/env python3
print("="*50)
print("🧪 ТЕСТ ИМПОРТА sexual_19_7.py")
print("="*50)

try:
    from sexual_19_7 import SEXUAL_DIVIDER
    print(f"✅ SEXUAL_DIVIDER = {SEXUAL_DIVIDER}")
except Exception as e:
    print(f"❌ Ошибка импорта SEXUAL_DIVIDER: {e}")

try:
    from sexual_19_7 import sexual_invite_start
    print(f"✅ sexual_invite_start найден")
except Exception as e:
    print(f"❌ Ошибка импорта sexual_invite_start: {e}")

try:
    from sexual_19_7 import create_invite_callback
    print(f"✅ create_invite_callback найден")
except Exception as e:
    print(f"❌ Ошибка импорта create_invite_callback: {e}")

print("\n" + "="*50)
print("🏁 ТЕСТ ЗАВЕРШЕН")
print("="*50)
