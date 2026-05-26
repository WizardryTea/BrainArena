# Реестр зарегистрированных игр
REGISTRY = {}

def register_game(cls):
    """Декоратор для регистрации игры в реестре"""
    REGISTRY[cls.slug] = cls
    return cls

def get_game(slug):
    """Получение класса игры по slug"""
    return REGISTRY.get(slug)
