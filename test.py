# test.py
from utils.validators import need_clarification_stage3

print("="*50)
print("ТЕСТ STAGE3")
print("="*50)

# Тест 1: пустой список
result = need_clarification_stage3(3, [])
print(f"Пустой список: {result} (должно быть True)")

# Тест 2: неполный (3 ответа)
result = need_clarification_stage3(3, [1,2,3])
print(f"Неполный (3/8): {result} (должно быть True)")

# Тест 3: полный, но большой разброс
result = need_clarification_stage3(3, [1,1,9,9,1,1,9,9])
print(f"Большой разброс: {result} (должно быть True)")

# Тест 4: нормальный
result = need_clarification_stage3(3, [3,3,4,4,4,4,5,5])
print(f"Нормальный: {result} (должно быть False)")

print("="*50)
