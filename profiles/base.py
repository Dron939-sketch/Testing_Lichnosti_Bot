# base.py
class VariaticaProfile:
    def __init__(self, **kwargs):
        # Основные поля
        self.key = kwargs.get('key', '')
        self.type_code = kwargs.get('type_code', '')
        self.level = kwargs.get('level', 1)
        self.number = kwargs.get('number', 0)
        
        # Информация о профиле
        self.title = kwargs.get('title', '')
        self.profile_name = kwargs.get('profile_name', '')
        self.thinking_level = kwargs.get('thinking_level', 1)
        self.dilts_level = kwargs.get('dilts_level', 'ENVIRONMENT')
        
        # Контент профиля
        self.pain = kwargs.get('pain', '')
        self.world = kwargs.get('world', '')
        self.superpower = kwargs.get('superpower', '')
        self.growth = kwargs.get('growth', '')
        self.cta = kwargs.get('cta', '')
        
        # Дополнительные поля (если есть)
        self.archetype = kwargs.get('archetype', '')
        self.quote = kwargs.get('quote', '')
        self.trigger = kwargs.get('trigger', '')
        self.immediate_tool = kwargs.get('immediate_tool', '')
    
    def __repr__(self):
        return f"<VariaticaProfile {self.key}>"
    
    def to_dict(self):
        """Конвертирует в словарь для обратной совместимости"""
        return {
            'key': self.key,
            'type_code': self.type_code,
            'level': self.level,
            'number': self.number,
            'title': self.title,
            'profile_name': self.profile_name,
            'thinking_level': self.thinking_level,
            'dilts_level': self.dilts_level,
            'pain': self.pain,
            'world': self.world,
            'superpower': self.superpower,
            'growth': self.growth,
            'cta': self.cta,
        }
