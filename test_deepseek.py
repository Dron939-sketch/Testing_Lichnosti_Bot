#!/usr/bin/env python3
"""
Тест DeepSeek API с ключом из Render
Запуск: python test_deepseek.py
"""

import os
from openai import OpenAI

def test_deepseek():
    """Тестирует подключение к DeepSeek API"""
    
    # Берем ключ из переменных окружения (Render)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY не найден в переменных окружения!")
        print("Добавьте ключ в Render через Dashboard → Environment")
        return
    
    print(f"✅ Ключ из Render: {api_key[:8]}...")
    
    # Пробуем подключиться к DeepSeek (через OpenAI SDK)
    try:
        # Вариант 1: Прямое подключение к DeepSeek
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Say 'Hello from DeepSeek!'"}
            ],
            max_tokens=50
        )
        
        print("\n✅ DeepSeek РАБОТАЕТ!")
        print(f"Ответ: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ Ошибка DeepSeek: {e}")
        
        # Вариант 2: Пробуем OpenAI (если ключ от OpenAI)
        try:
            print("\n🔄 Пробую OpenAI...")
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Say 'Hello from OpenAI!'"}
                ],
                max_tokens=50
            )
            
            print("\n✅ OpenAI РАБОТАЕТ!")
            print(f"Ответ: {response.choices[0].message.content}")
            print("\n📌 Это ключ от OpenAI, а не DeepSeek")
            
        except Exception as e2:
            print(f"\n❌ И OpenAI тоже не работает: {e2}")
            print("\n🔑 ПРОБЛЕМА С КЛЮЧОМ:")
            print("1. Убедитесь, что ключ активен")
            print("2. Проверьте баланс на platform.openai.com")
            print("3. Для DeepSeek нужен отдельный ключ с platform.deepseek.com")

if __name__ == "__main__":
    print("="*60)
    print("🔌 ТЕСТ ПОДКЛЮЧЕНИЯ")
    print("="*60)
    test_deepseek()
