#!/usr/bin/env python3
"""
prepare_dataset.py - Подготовка данных для обучения AI на ваших интимных профилях
Запуск: python prepare_dataset.py
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Any

class IntimateProfileDataset:
    def __init__(self, profiles_dir: str = "sexual_18"):
        self.profiles_dir = profiles_dir
        self.profiles = []
        self.stats = {
            "total": 0,
            "by_type": {},
            "by_archetype": {},
            "sections_avg": {},
            "files": []
        }
    
    def load_all_profiles(self) -> List[Dict]:
        """Загружает все JSON-профили из папки"""
        json_files = glob.glob(os.path.join(self.profiles_dir, "*.json"))
        print(f"📁 Найдено JSON-файлов: {len(json_files)}")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Проверяем, что это интимный профиль
                if self._is_intimate_profile(data):
                    profile_info = {
                        "file": os.path.basename(file_path),
                        "data": data,
                        "type": data.get('profile_type', 'unknown'),
                        "archetype": data.get('archetype', 'unknown'),
                        "size": os.path.getsize(file_path)
                    }
                    self.profiles.append(profile_info)
                    self.stats["files"].append(os.path.basename(file_path))
                    print(f"  ✅ {os.path.basename(file_path)}")
                else:
                    print(f"  ⚠️ {os.path.basename(file_path)} - не интимный профиль")
                    
            except Exception as e:
                print(f"  ❌ Ошибка чтения {os.path.basename(file_path)}: {e}")
        
        self.stats["total"] = len(self.profiles)
        return self.profiles
    
    def _is_intimate_profile(self, data: dict) -> bool:
        """Проверяет, что это интимный профиль"""
        required = ["profile_type", "archetype", "role", "quote", "description", "sections"]
        return all(field in data for field in required)
    
    def analyze_profiles(self):
        """Анализирует структуру всех профилей"""
        print("\n" + "="*60)
        print("📊 АНАЛИЗ ПРОФИЛЕЙ")
        print("="*60)
        
        # Статистика по типам
        for profile in self.profiles:
            p_type = profile['type']
            self.stats["by_type"][p_type] = self.stats["by_type"].get(p_type, 0) + 1
            
            arch = profile['archetype']
            self.stats["by_archetype"][arch] = self.stats["by_archetype"].get(arch, 0) + 1
        
        # Анализ секций
        section_lengths = {}
        section_counts = {}
        
        for profile in self.profiles:
            sections = profile['data'].get('sections', {})
            for section_name, section_data in sections.items():
                if section_name not in section_lengths:
                    section_lengths[section_name] = 0
                    section_counts[section_name] = 0
                
                if 'items' in section_data:
                    section_lengths[section_name] += len(section_data['items'])
                elif 'content' in section_data:
                    section_lengths[section_name] += len(section_data['content'].split())
                
                section_counts[section_name] += 1
        
        for section in section_lengths:
            if section_counts[section] > 0:
                self.stats["sections_avg"][section] = round(
                    section_lengths[section] / section_counts[section], 1
                )
    
    def print_stats(self):
        """Выводит статистику"""
        print(f"\n📊 ВСЕГО ПРОФИЛЕЙ: {self.stats['total']}")
        
        print("\n📌 ПО ТИПАМ:")
        for p_type, count in sorted(self.stats["by_type"].items()):
            print(f"  {p_type}: {count}")
        
        print("\n🎭 ПО АРХЕТИПАМ (первые 10):")
        for i, (arch, count) in enumerate(sorted(self.stats["by_archetype"].items())):
            if i < 10:
                print(f"  {arch}: {count}")
        
        print("\n📏 СРЕДНЯЯ ДЛИНА СЕКЦИЙ:")
        for section, avg in sorted(self.stats["sections_avg"].items()):
            if avg > 0:
                if section in ["dirty_details", "core"]:
                    print(f"  {section:20} {avg:.1f} слов")
                else:
                    print(f"  {section:20} {avg:.1f} пунктов")
    
    def export_for_training(self, output_file: str = "intimate_profiles_dataset.jsonl"):
        """Экспортирует профили в формате JSONL для обучения"""
        print(f"\n📝 Экспорт в {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for profile in self.profiles:
                data = profile['data']
                
                # Создаем обучающий пример в формате OpenAI
                example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты создаешь интимные психологические профили для системы Variatica. Стиль: метафоричный, глубокий, с обращением на 'ты', без осуждения. Структура: 15 секций (what_turns_on, what_turns_off, smells_tastes, sounds, dirty_details, fetishes, places, morning, secret_desires, whispers, core, compliments, tells, remains)."
                        },
                        {
                            "role": "user",
                            "content": f"Создай интимный профиль для типа {data['profile_type']} с архетипом {data['archetype']}."
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(data, ensure_ascii=False)
                        }
                    ]
                }
                
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        print(f"✅ Экспортировано {len(self.profiles)} профилей")
        return output_file
    
    def create_prompts_file(self, output_file: str = "prompts_for_generation.txt"):
        """Создает файл с промптами для генерации новых профилей"""
        print(f"\n📝 Создание файла с промптами: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ПРОМПТЫ ДЛЯ ГЕНЕРАЦИИ ИНТИМНЫХ ПРОФИЛЕЙ\n")
            f.write("="*80 + "\n\n")
            
            for profile in self.profiles:
                data = profile['data']
                f.write(f"ТИП: {data['profile_type']}\n")
                f.write(f"АРХЕТИП: {data['archetype']}\n")
                f.write(f"РОЛЬ: {data['role']}\n")
                f.write(f"ЦИТАТА: {data['quote']}\n")
                f.write("-"*40 + "\n\n")

def main():
    print("="*80)
    print("🧠 ПОДГОТОВКА ДАННЫХ ДЛЯ ОБУЧЕНИЯ AI")
    print("="*80)
    
    # Создаем датасет
    dataset = IntimateProfileDataset("sexual_18")
    
    # Загружаем все профили
    profiles = dataset.load_all_profiles()
    
    if not profiles:
        print("❌ Не найдено ни одного профиля!")
        return
    
    # Анализируем
    dataset.analyze_profiles()
    dataset.print_stats()
    
    # Экспортируем
    dataset.export_for_training()
    dataset.create_prompts_file()
    
    print("\n" + "="*80)
    print("✅ ГОТОВО! Файлы созданы:")
    print("   - intimate_profiles_dataset.jsonl  (для обучения AI)")
    print("   - prompts_for_generation.txt       (промпты для генерации)")
    print("="*80)

if __name__ == "__main__":
    main()
