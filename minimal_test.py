#!/usr/bin/env python3
import os
from openai import OpenAI

# ВСТАВЬТЕ КЛЮЧ СЮДА ПРЯМО (для теста)
API_KEY = "sk-ad37c***********************80bc"  # замените на ваш ключ

client = OpenAI(api_key=API_KEY)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say OK"}],
        max_tokens=5
    )
    print("✅ Успех! Ответ:", response.choices[0].message.content)
except Exception as e:
    print("❌ Ошибка:", e)
