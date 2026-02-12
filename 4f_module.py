#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4f_module.py - Модуль для работы с 4F-ключами
MVP версия: всегда использует sa_4_cap.json
"""

import os
import json
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ============================================
# КОНСТАНТЫ 4F МОДУЛЯ
# ============================================
F4F_BASE_PATH = "профили/4F"
F4F_FUNCTIONS = ["1F", "2F", "3F", "4F"]
F4F_DEFAULT_PROFILE = "sa_4_cap"
F4F_PAYMENT_AMOUNT = 99.00

# ============================================
# ЗАГРУЗЧИК 4F JSON ФАЙЛОВ
# ============================================

class FourFLoader:
    """Загрузчик 4F-функций из JSON-файлов с кэшированием"""
    
    def __init__(self, base_path: str = F4F_BASE_PATH):
        self.base_path = base_path
        self.cache = {}
    
    def get_function(self, function: str, profile_key: str = "sa_4_cap") -> Dict:
        """
        Получить функцию с кэшированием
        - function: 1F,2F,3F,4F
        - profile_key: sa_4_cap, default
        """
        cache_key = f"{function}_{profile_key}"
        
        # Проверяем кэш
        if cache_key in self.cache:
            logger.debug(f"📦 Загружено из кэша: {cache_key}")
            return self.cache[cache_key].copy()
        
        # Валидация
        if function not in F4F_FUNCTIONS:
            raise ValueError(f"Неверная функция: {function}")
        
        # Пытаемся загрузить запрошенный профиль
        file_path = f"{self.base_path}/{function}/{profile_key}.json"
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл {file_path} не найден, использую default.json")
            file_path = f"{self.base_path}/{function}/default.json"
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        # Читаем JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Добавляем метаданные
        content["_meta"] = {
            "function": function,
            "profile_key": profile_key if os.path.exists(f"{self.base_path}/{function}/{profile_key}.json") else "default",
            "source_profile": "sa_4_cap",  # MVP: всегда sa_4_cap
            "is_demo": True,
            "demo_notice": "⚠️ Это демо-версия. Полная версия содержит 3x больше контента и точные триггер-фразы.",
            "upgrade_price": 99
        }
        
        # Сохраняем в кэш
        self.cache[cache_key] = content.copy()
        
        logger.info(f"✅ Загружен 4F ключ: {function}/{profile_key}")
        return content.copy()
    
    def substitute_name(self, content: Dict, friend_name: str) -> Dict:
        """
        Рекурсивно заменить {friend_name} на имя в JSON
        """
        content_str = json.dumps(content, ensure_ascii=False)
        content_str = content_str.replace("{friend_name}", friend_name)
        return json.loads(content_str)
    
    def clear_cache(self):
        """Очистить кэш"""
        self.cache.clear()
        logger.info("🧹 Кэш 4F очищен")

# Создаем глобальный экземпляр загрузчика
f4f_loader = FourFLoader()

# ============================================
# ОСНОВНЫЕ ФУНКЦИИ ДЛЯ БОТА
# ============================================

async def get_4f_function_content(
    function: str,
    profile_key: str = "sa_4_cap",
    friend_name: str = "друг",
    is_purchased: bool = False
) -> Dict:
    """
    Получить содержимое 4F-функции с подстановкой имени
    - Читает JSON из профили/4F/{function}/{profile_key}.json
    - Заменяет {friend_name} на переданное имя
    - Если is_purchased=False и is_demo=True, показывает demo_notice
    - Если is_purchased=True, показывает полный контент
    
    Args:
        function: 1F, 2F, 3F, 4F
        profile_key: sa_4_cap (всегда на MVP)
        friend_name: имя друга для подстановки
        is_purchased: полная версия или демо
    
    Returns:
        Dict: содержимое JSON с подставленным именем
    """
    try:
        # Загружаем функцию
        content = f4f_loader.get_function(function, profile_key)
        
        # Подставляем имя друга
        content = f4f_loader.substitute_name(content, friend_name)
        
        # Если это не купленная версия, убеждаемся что есть demo_notice
        if not is_purchased:
            if "_meta" in content:
                content["_meta"]["is_demo"] = True
                if "demo_notice" not in content["_meta"]:
                    content["_meta"]["demo_notice"] = "⚠️ Это демо-версия. Полная версия содержит 3x больше контента и точные триггер-фразы."
        
        return content
        
    except FileNotFoundError as e:
        logger.error(f"❌ Файл не найден: {e}")
        # Возвращаем заглушку
        return {
            "error": "Ключ временно недоступен",
            "function": function,
            "_meta": {
                "is_demo": True,
                "error": str(e)
            }
        }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки 4F функции: {e}")
        raise

def format_4f_message(content: Dict, friend_name: str) -> str:
    """
    Форматирует JSON 4F в красивое Telegram-сообщение
    
    Правила:
    - Заголовок: эмодзи + function_name
    - Подзаголовок: для кого (У профиля SA-4_CAP «{friend_name}»)
    - Секции с эмодзи
    - Триггеры в виде списка
    - Примеры в виде блоков
    - Цитаты курсивом
    - Демо-заметка (если is_demo)
    - Продажа полной версии (если is_demo)
    
    Args:
        content: JSON контент из get_4f_function_content
        friend_name: имя друга для отображения
    
    Returns:
        str: отформатированное сообщение для Telegram
    """
    lines = []
    
    # 1. Заголовок с эмодзи
    function = content.get("_meta", {}).get("function", "")
    function_emojis = {
        "1F": "🔥",
        "2F": "🍽️",
        "3F": "⚡",
        "4F": "💡"
    }
    emoji = function_emojis.get(function, "🔑")
    
    title = content.get("content", {}).get("title", f"{emoji} {function}: КЛЮЧ")
    lines.append(f"{title}")
    lines.append("")
    
    # 2. Для кого
    lines.append(f"👤 *Для:* У профиля SA-4_CAP «{friend_name}»")
    lines.append("")
    
    # 3. Короткое описание
    short_desc = content.get("content", {}).get("short_description", "")
    if short_desc:
        lines.append(f"📋 *Описание:*")
        lines.append(f"{short_desc}")
        lines.append("")
    
    # 4. Триггеры
    triggers = content.get("content", {}).get("triggers", [])
    if triggers:
        lines.append(f"🎯 *Ключевые триггеры:*")
        for trigger in triggers[:5]:  # Показываем только первые 5 в демо
            lines.append(f"• {trigger}")
        if len(triggers) > 5:
            lines.append(f"  _...и еще {len(triggers)-5} триггеров в полной версии_")
        lines.append("")
    
    # 5. Примеры
    examples = content.get("content", {}).get("examples", [])
    if examples:
        lines.append(f"💬 *Примеры фраз:*")
        for example in examples[:3]:  # Показываем только первые 3 в демо
            lines.append(f"• \"{example}\"")
        if len(examples) > 3:
            lines.append(f"  _...и еще {len(examples)-3} примеров в полной версии_")
        lines.append("")
    
    # 6. Демо-заметка
    is_demo = content.get("_meta", {}).get("is_demo", True)
    if is_demo:
        demo_notice = content.get("_meta", {}).get("demo_notice", "")
        if demo_notice:
            lines.append(f"⚠️ *Демо-версия*")
            lines.append(f"{demo_notice}")
            lines.append("")
        
        # 7. Предложение полной версии
        lines.append(f"💎 *Полная версия содержит:*")
        demo_limitation = content.get("demo_limitation", {})
        demo_content = demo_limitation.get("content", [])
        if demo_content:
            for item in demo_content[:3]:
                lines.append(f"• {item}")
        else:
            lines.append(f"• Точные психологические триггеры")
            lines.append(f"• Пошаговый протокол применения")
            lines.append(f"• Адаптация под конкретную ситуацию")
        
        lines.append("")
        lines.append(f"✨ Купите полную версию за 99₽")
    
    return "\n".join(lines)

async def check_4f_access(buyer_id: int, target_id: int, function: str, api_base_url: str = None) -> bool:
    """
    Проверить через API, куплена ли функция для конкретного друга
    
    Args:
        buyer_id: ID покупателя
        target_id: ID друга
        function: 1F,2F,3F,4F
        api_base_url: базовый URL API (из настроек)
    
    Returns:
        bool: True если доступ есть, иначе False
    """
    if not api_base_url:
        # Fallback: если API не указан, считаем что доступа нет
        logger.warning("⚠️ API base URL не указан, проверка доступа пропущена")
        return False
    
    try:
        url = f"{api_base_url}/api/4f/check-access/{buyer_id}/{target_id}/{function}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("has_access", False)
        else:
            logger.error(f"❌ Ошибка проверки доступа: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке доступа 4F: {e}")
        return False

# ============================================
# ТЕСТОВЫЕ ФУНКЦИИ
# ============================================

def test_4f_module():
    """Тест 4F модуля"""
    print("="*50)
    print("🔑 ТЕСТ 4F МОДУЛЯ")
    print("="*50)
    
    # Создаем загрузчик
    loader = FourFLoader()
    
    # Тест 1: Загрузка 1F
    try:
        content = loader.get_function("1F", "sa_4_cap")
        print("✅ 1F загружен успешно")
    except Exception as e:
        print(f"❌ Ошибка загрузки 1F: {e}")
    
    # Тест 2: Подстановка имени
    try:
        content_with_name = loader.substitute_name(content, "Александр")
        print("✅ Подстановка имени работает")
    except Exception as e:
        print(f"❌ Ошибка подстановки имени: {e}")
    
    # Тест 3: Форматирование сообщения
    try:
        message = format_4f_message(content_with_name, "Александр")
        print("✅ Форматирование сообщения работает")
        print("\n" + "="*30)
        print(message[:200] + "...")
        print("="*30)
    except Exception as e:
        print(f"❌ Ошибка форматирования: {e}")
    
    print("="*50)

if __name__ == "__main__":
    test_4f_module()
