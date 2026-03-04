#!/usr/bin/env python3
"""
test_generation.py - Тест генерации одного профиля
ИСПРАВЛЕНО для OpenAI SDK >=1.0.0
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем ключи
load_dotenv()

def test_generation():
    """Тестирует генерацию одного профиля"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-ваш_реальный_ключ_здесь":
        print("❌ ОШИБКА: Необходимо добавить реальный API ключ в .env файл!")
        print("1. Получите ключ на https://platform.openai.com/api-keys")
        print("2. Добавьте его в .env файл")
        return
    
    print(f"✅ API ключ загружен: {api_key[:8]}...")
    
    # Создаем клиент (НОВЫЙ способ)
    client = OpenAI(api_key=api_key)
    
    try:
        # Используем НОВЫЙ синтаксис
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, World!' in JSON format"}
            ],
            max_tokens=50
        )
        
        print("\n✅ Соединение с OpenAI работает!")
        print(f"Ответ: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ Ошибка соединения: {e}")
        print("\nВозможные причины:")
        print("1. Неверный API ключ")
        print("2. Нет средств на аккаунте")
        print("3. Проблемы с сетью")

if __name__ == "__main__":
    print("="*60)
    print("🔌 ТЕСТ ПОДКЛЮЧЕНИЯ К OPENAI")
    print("="*60)
    test_generation()
