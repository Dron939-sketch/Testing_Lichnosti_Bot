# profiles/base.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class VariaticaProfile:
    """Базовый класс профиля ВАРИАТИКА"""
    
    key: str                    # "SA_1", "SP_9"
    type_code: str              # "SA", "IA", "SP", "IP"
    level: int                  # 1-9
    number: int                 # 1-36
    
    title: str
    archetype: str
    quote: str
    trigger: str
    pain: str
    immediate_tool: str
    cta: str
    
    world: Optional[str] = None
    superpower: Optional[str] = None
    growth: Optional[str] = None
