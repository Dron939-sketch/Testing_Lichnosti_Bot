#!/usr/bin/env python3
"""
Тест DeepSeek API
Запуск: python test_deepseek.py
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_deepseek():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY не найден в .env файле!")
        return
    
    print(f"✅ DeepSeek ключ загружен: {api_key[:8]}...")
    
    # Создаем клиент для DeepSeek
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Say 'Hello from DeepSeek!'"}
            ],
            max_tokens=50
        )
        
        print("\n✅ DeepSeek работает!")
        print(f"Ответ: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🔌 ТЕСТ ПОДКЛЮЧЕНИЯ К DEEPSEEK")
    print("="*60)
    test_deepseek()
  
