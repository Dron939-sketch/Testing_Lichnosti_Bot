#!/usr/bin/env python3
print("Тест импорта sexual_19_7.py")

try:
    from sexual_19_7 import SEXUAL_DIVIDER
    print(f"✅ SEXUAL_DIVIDER: {SEXUAL_DIVIDER}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

try:
    from sexual_19_7 import sexual_invite_start
    print(f"✅ sexual_invite_start найден")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("Тест завершен")
