from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class VariaticaProfile:
    """Базовый класс для всех 36 профилей"""
    
    # Идентификаторы
    key: str                    # "SA_1", "SP_9"
    type_code: str              # "SA", "IA", "SP", "IP"
    level: int                  # 1-9
    number: int                 # 1-36 (сквозная нумерация)
    
    # Основной контент
    title: str                  # "СБ-Туз 'Создавай правила'"
    archetype: str              # "Архитектор порядка..."
    quote: str                  # "Я создал мир по своим законам..."
    
    # Блоки
    trigger: str                # "ЭТО ТЫ, ЕСЛИ..."
    pain: str                   # "СУТЬ ПРОБЛЕМЫ..."
    immediate_tool: str         # "ПЕРВЫЙ ШАГ..."
    cta: str                    # "ЧТО ДАЛЬШЕ?.."
    
    # Для бота
    world: Optional[str] = None
    superpower: Optional[str] = None
    growth: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует профиль в словарь для бота"""
        return asdict(self)
    
    def __str__(self) -> str:
        return f"{self.key}: {self.title}"
