# base.py
class VariaticaProfile:
    def __init__(self, **kwargs):
        self.key = kwargs.get('key')
        self.type_code = kwargs.get('type_code')
        self.level = kwargs.get('level')
        self.number = kwargs.get('number')
        self.title = kwargs.get('title')
        self.profile_name = kwargs.get('profile_name')
        self.thinking_level = kwargs.get('thinking_level')
        self.dilts_level = kwargs.get('dilts_level')
        self.pain = kwargs.get('pain')
        self.world = kwargs.get('world')
        self.superpower = kwargs.get('superpower')
        self.growth = kwargs.get('growth')
        self.cta = kwargs.get('cta')
        
        # Дополнительные поля (если нужны)
        self.archetype = kwargs.get('archetype')
        self.quote = kwargs.get('quote')
        self.trigger = kwargs.get('trigger')
        self.immediate_tool = kwargs.get('immediate_tool')
    
    def __repr__(self):
        return f"<VariaticaProfile {self.key}>"
