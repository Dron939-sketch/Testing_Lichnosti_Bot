#!/usr/bin/env python3
"""
Тест генерации профиля через DeepSeek
Запуск: python test_deepseek_profile.py
"""

import os
import json
from openai import OpenAI

def test_generate_profile():
    """Генерирует тестовый профиль через DeepSeek"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY не найден в переменных окружения!")
        return
    
    print(f"✅ Ключ загружен: {api_key[:8]}...")
    
    # Создаем клиент для DeepSeek
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    # Промпт для генерации профиля
    prompt = """Ты — психолог, создающий интимные профили для системы Variatica.
Сгенерируй JSON-профиль для типа IA-3_BEH с архетипом "АЛХИМИК ЛЖИ".

Профиль должен содержать:
- profile_type: IA-3_BEH
- archetype: АЛХИМИК ЛЖИ
- role: краткая роль (2-3 слова)
- quote: цитата (1 предложение)
- description: описание природы (3-4 предложения)

И секцию "what_turns_on" с 5 пунктами.

Верни ТОЛЬКО JSON, без пояснений."""
    
    try:
        print("\n🤖 Генерирую профиль...")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты создаешь психологические профили в формате JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        # Парсим ответ
        result = json.loads(response.choices[0].message.content)
        
        print("\n✅ ПРОФИЛЬ СГЕНЕРИРОВАН!")
        print("\n" + "="*60)
        print(f"Тип: {result.get('profile_type')}")
        print(f"Архетип: {result.get('archetype')}")
        print(f"Роль: {result.get('role')}")
        print(f"\n💬 ЦИТАТА:\n{result.get('quote')}")
        print(f"\n📝 ОПИСАНИЕ:\n{result.get('description')}")
        
        if 'sections' in result and 'what_turns_on' in result['sections']:
            print(f"\n🔥 ЧТО ЗАВОДИТ (what_turns_on):")
            for i, item in enumerate(result['sections']['what_turns_on'], 1):
                print(f"{i}. {item}")
        
        # Сохраняем в файл
        filename = "test_generated_profile.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Профиль сохранён в {filename}")
        
        # Показываем полный JSON
        print("\n📄 ПОЛНЫЙ JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Ошибка парсинга JSON: {e}")
        print("\n📄 Сырой ответ:")
        print(response.choices[0].message.content[:500])
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🤖 ТЕСТ ГЕНЕРАЦИИ ПРОФИЛЯ (DeepSeek)")
    print("="*60)
    test_generate_profile()
