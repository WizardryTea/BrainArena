from django.apps import AppConfig
from django.db.utils import OperationalError
from .loader import load_games, sync_games


class GamesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'games'

    def ready(self):
        # Подключаем сигналы
        import games.signals
        #import games.gamesList.test_game.engine
        try:
            load_games()
            # Только если таблицы существуют
            from django.db import connection
            if connection.introspection.table_names():
                sync_games()
        except OperationalError:
            # База еще не готова — пропускаем
            pass
