#!/usr/bin/env python3
"""
Скрипт для восстановления потерянных приглашений
Запускать: python3 restore_invites.py
"""

import requests
import time
import json
from datetime import datetime

API_URL = "https://testing-lichnosti-bot-1.onrender.com"
YOUR_USER_ID = 532205848  # Ваш ID

def print_color(text, color="white"):
    """Цветной вывод в консоль"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def get_all_profiles():
    """Получает все профили пользователей"""
    print_color("📊 Получаю все профили...", "blue")
    
    # Так как у нас нет /all, будем проверять по известным ID
    # Сначала получим всех, кто создавал приглашения
    invites_response = requests.get(f"{API_URL}/api/sexual/get-invites/{YOUR_USER_ID}")
    if invites_response.status_code != 200:
        print_color("❌ Не удалось получить приглашения", "red")
        return []
    
    invites = invites_response.json().get('invites', [])
    
    # Собираем уникальные ID друзей из приглашений
    friend_ids = set()
    for inv in invites:
        if inv.get('friend_id'):
            friend_ids.add(inv['friend_id'])
    
    print_color(f"👥 Найдено ID друзей в приглашениях: {friend_ids}", "yellow")
    
    # Проверяем профили для этих ID
    profiles = []
    for fid in friend_ids:
        resp = requests.get(f"{API_URL}/api/get-user-profile/{fid}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('has_profile'):
                profiles.append({
                    'user_id': fid,
                    'profile_code': data.get('profile_code'),
                    'created_at': data.get('created_at')
                })
                print_color(f"  ✅ {fid}: {data.get('profile_code')}", "green")
    
    return profiles

def get_pending_invites():
    """Получает все ожидающие приглашения"""
    print_color("\n📨 Получаю ожидающие приглашения...", "blue")
    
    response = requests.get(f"{API_URL}/api/sexual/get-invites/{YOUR_USER_ID}")
    if response.status_code != 200:
        print_color("❌ Не удалось получить приглашения", "red")
        return []
    
    invites = response.json().get('invites', [])
    pending = [inv for inv in invites if inv.get('status') == 'pending']
    
    print_color(f"📊 Найдено {len(pending)} ожидающих приглашений", "yellow")
    return pending

def restore_invite(invite_id, friend_id, friend_name, profile_code):
    """Пытается восстановить приглашение"""
    print_color(f"\n🔄 Восстанавливаю {invite_id} -> {friend_name} ({profile_code})", "yellow")
    
    payload = {
        "friend_id": friend_id,
        "friend_name": friend_name,
        "friend_profile": profile_code
    }
    
    response = requests.post(
        f"{API_URL}/api/sexual/update-invite/{invite_id}",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        print_color(f"  ✅ УСПЕХ! Приглашение {invite_id} восстановлено", "green")
        return True
    else:
        print_color(f"  ❌ Ошибка {response.status_code}: {response.text}", "red")
        return False

def main():
    print_color("="*60, "blue")
    print_color("🚀 ВОССТАНОВЛЕНИЕ ПОТЕРЯННЫХ ПРИГЛАШЕНИЙ", "green")
    print_color("="*60, "blue")
    
    # 1. Получаем профили
    profiles = get_all_profiles()
    if not profiles:
        print_color("\n❌ Нет профилей для восстановления", "red")
        return
    
    # 2. Получаем ожидающие приглашения
    pending = get_pending_invites()
    if not pending:
        print_color("\n❌ Нет ожидающих приглашений", "red")
        return
    
    print_color(f"\n🔍 Начинаю сопоставление...", "blue")
    
    restored_count = 0
    
    # 3. Пробуем сопоставить
    for profile in profiles:
        user_id = profile['user_id']
        profile_code = profile['profile_code']
        
        print_color(f"\n👤 Проверяю пользователя {user_id} с профилем {profile_code}", "yellow")
        
        # Ищем подходящее приглашение (по времени или просто первое)
        # В реальности нужно более умное сопоставление
        for invite in pending[:3]:  # Пробуем первые 3
            print_color(f"  ⏳ Пробую привязать к {invite['invite_id']}", "yellow")
            
            success = restore_invite(
                invite['invite_id'],
                user_id,
                f"User_{user_id}",
                profile_code
            )
            
            if success:
                restored_count += 1
                # Убираем восстановленное из списка
                pending = [i for i in pending if i['invite_id'] != invite['invite_id']]
                break
            
            time.sleep(1)  # Пауза между запросами
    
    print_color("\n" + "="*60, "green")
    print_color(f"🎉 Восстановлено {restored_count} приглашений!", "green")
    print_color("="*60, "green")

if __name__ == "__main__":
    main()
