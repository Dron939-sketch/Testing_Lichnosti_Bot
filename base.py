# base.py
"""
Базовый класс профиля
"""

class VariaticaProfile:
    """Класс профиля Variatica"""
    
    def __init__(self, **kwargs):
        # Инициализируем все переданные атрибуты
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Устанавливаем значения по умолчанию для совместимости
        if not hasattr(self, 'key'):
            # Генерируем ключ на основе других полей
            if hasattr(self, 'type_code') and hasattr(self, 'level'):
                suffix = "def"
                if hasattr(self, 'number'):
                    suffix = ["def", "sit", "con", "exp", "int", "aut", "val", "tra", "ide"][self.number - 1]
                self.key = f"{self.type_code}_{self.level}_{suffix}"
    
    def __repr__(self):
        """Строковое представление профиля"""
        attrs = []
        for key in sorted(self.__dict__.keys()):
            value = getattr(self, key)
            if isinstance(value, str) and len(value) > 50:
                attrs.append(f"{key}: {value[:50]}...")
            else:
                attrs.append(f"{key}: {value}")
        
        return f"VariaticaProfile({', '.join(attrs)})"
    
    def to_dict(self):
        """Конвертирует профиль в словарь"""
        return self.__dict__.copy()
    
    def get(self, key, default=None):
        """Безопасное получение атрибута"""
        return getattr(self, key, default)
