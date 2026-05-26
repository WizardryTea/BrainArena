import os
import importlib
from django.db import transaction


def load_games():
    # Путь к папке с модулями игр
    base_path = os.path.join(os.path.dirname(__file__), 'gamesList')

    for folder in os.listdir(base_path):
        game_path = os.path.join(base_path, folder)

        if os.path.isdir(game_path):
            try:
                importlib.import_module(f'games.gamesList.{folder}.engine')
                # print(f"(loader.py) Loaded game: {folder}")
            except ModuleNotFoundError:
                pass


def sync_games(force_update=False):
    """
    Синхронизирует игры из registry с базой данных.
    Если в registry есть игры, но их нет в БД, создает их автоматически.
    
    Args:
        force_update (bool): Если True, принудительно обновляет данные игр (для отладки).
    """
    from .registry import REGISTRY
    
    # Отложенная загрузка модели для избежания AppRegistryNotReady
    from django.apps import apps
    Game = apps.get_model('games', 'Game')
    
    with transaction.atomic():
        for slug, game_class in REGISTRY.items():
            # Если в классе игры задан атрибут name и он не None, используем его, иначе преобразуем slug
            game_name = getattr(game_class, 'name', None) or slug.replace('_', ' ').title()
            # Если в классе игры задан атрибут description и он не None, используем его, иначе создаем описание из Описание + name
            game_description = getattr(game_class, 'description', None) or f"Описание игры {game_name}"
            game_short_description = getattr(game_class, 'short_description', None) or f"Описание игры {game_name}"
            # Если в классе игры задан атрибут avatar, используем его, иначе базовый аватар
            game_avatar = getattr(game_class, 'avatar', None) or "media/avatars_games/game_base.png"
            
            # Только создает, но не обновляет:
            # Game.objects.get_or_create

            # Для разработки с принудительным обновлением:
            # Game.objects.update_or_create

            Game.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": game_name,
                    "is_active": True,
                    "description": game_description,
                    "short_description": game_short_description,
                    "avatar": game_avatar
                }
            )
            # print(f"(loader.py) Synced game: {slug}")
