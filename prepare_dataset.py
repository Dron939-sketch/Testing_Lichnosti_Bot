#!/usr/bin/env python3
"""
Подготовка данных для обучения ИИ на ваших JSON-профилях
"""

import json
import os
import glob
from typing import Dict, List
from datetime import datetime

class VariaticaDataset:
    def __init__(self, input_dir: str = "ai_training_data"):
        self.input_dir = input_dir
        self.profiles = []
        self.stats = {
            "total": 0,
            "by_type": {},
            "by_archetype": {},
            "section_stats": {}
        }
    
    def scan_profiles(self):
        """Сканирует все JSON-файлы в папке"""
        json_files = glob.glob(f"{self.input_dir}/*.json")
        print(f"📁 Найдено JSON-файлов: {len(json_files)}")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Проверяем, что это интимный профиль
                if self._is_intimate_profile(data):
                    self.profiles.append({
                        "file": os.path.basename(file_path),
                        "data": data,
                        "type": data.get('profile_type', 'unknown'),
                        "archetype": data.get('archetype', 'unknown')
                    })
                    
                    # Собираем статистику
                    self._update_stats(data)
                    
                    print(f"  ✅ {os.path.basename(file_path)}")
                else:
                    print(f"  ⚠️ {os.path.basename(file_path)} - не интимный профиль")
                    
            except Exception as e:
                print(f"  ❌ {os.path.basename(file_path)}: {e}")
        
        print(f"\n✅ Загружено профилей: {len(self.profiles)}")
    
    def _is_intimate_profile(self, data: dict) -> bool:
        """Проверяет, что это интимный профиль"""
        required = ["profile_type", "archetype", "role", "quote", "description", "sections"]
        return all(field in data for field in required)
    
    def _update_stats(self, data: dict):
        """Обновляет статистику"""
        # По типу
        p_type = data.get('profile_type', 'unknown')
        self.stats["by_type"][p_type] = self.stats["by_type"].get(p_type, 0) + 1
        
        # По архетипу
        arch = data.get('archetype', 'unknown')
        self.stats["by_archetype"][arch] = self.stats["by_archetype"].get(arch, 0) + 1
        
        # По секциям
        for section_name, section_data in data.get('sections', {}).items():
            if section_name not in self.stats["section_stats"]:
                self.stats["section_stats"][section_name] = {
                    "count": 0,
                    "avg_items": 0,
                    "total_items": 0
                }
            
            stats = self.stats["section_stats"][section_name]
            stats["count"] += 1
            
            if 'items' in section_data:
                stats["total_items"] += len(section_data['items'])
            elif 'content' in section_data:
                words = len(section_data['content'].split())
                stats["total_items"] += words // 20  # приблизительно
    
    def calculate_averages(self):
        """Вычисляет средние значения"""
        for section, stats in self.stats["section_stats"].items():
            if stats["count"] > 0:
                stats["avg_items"] = round(stats["total_items"] / stats["count"], 1)
        
        self.stats["total"] = len(self.profiles)
    
    def export_for_training(self, output_file: str = "variatica_training.jsonl"):
        """
        Экспортирует профили в формате для обучения
        Каждая строка: {"messages": [{"role": "system", "content": ...}, ...]}
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for profile in self.profiles:
                data = profile['data']
                
                # Создаём системный промпт
                system_prompt = f"""Ты создаешь интимные психологические профили для системы Variatica.
Стиль: метафоричный, глубокий, с обращением на "ты", без осуждения.
Структура: 15 секций (what_turns_on, what_turns_off, smells_tastes, sounds, dirty_details, fetishes, places, morning, secret_desires, whispers, core, compliments, tells, remains)."""

                # Создаём пользовательский запрос
                user_prompt = f"""Создай интимный профиль для:
Тип: {data['profile_type']}
Архетип: {data['archetype']}
Роль: {data['role']}"""

                # Создаём completion (весь профиль)
                completion = json.dumps(data, ensure_ascii=False)
                
                # Формируем строку в формате OpenAI
                line = json.dumps({
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": completion}
                    ]
                }, ensure_ascii=False)
                
                f.write(line + '\n')
        
        print(f"\n✅ Датасет сохранён: {output_file}")
    
    def print_stats(self):
        """Выводит статистику"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ПРОФИЛЕЙ")
        print("="*60)
        print(f"Всего профилей: {self.stats['total']}")
        
        print("\n📌 ПО ТИПАМ:")
        for p_type, count in sorted(self.stats["by_type"].items()):
            print(f"  {p_type}: {count}")
        
        print("\n🎭 ПО АРХЕТИПАМ:")
        for arch, count in sorted(self.stats["by_archetype"].items()):
            print(f"  {arch}: {count}")
        
        print("\n📏 СЕКЦИИ (среднее количество пунктов):")
        for section, stats in sorted(self.stats["section_stats"].items()):
            if stats["count"] > 0:
                print(f"  {section:20} {stats['avg_items']:5.1f} пунктов (в {stats['count']} профилях)")
        
        print("="*60)

if __name__ == "__main__":
    # Создаём датасет
    dataset = VariaticaDataset("ai_training_data")
    dataset.scan_profiles()
    dataset.calculate_averages()
    dataset.print_stats()
    dataset.export_for_training()
