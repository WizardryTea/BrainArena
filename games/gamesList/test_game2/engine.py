
from games.engines.base_engine import BaseEngine
from games.registry import register_game

@register_game
class TestGame_2(BaseEngine):
    slug = "test_game_2"
    template = "games/games_list/test_game_2.html"
    description = "Описание игры Test Game 2"
    name = "Тестовая игра 2"

    @staticmethod
    def get_leaderboard_metric_name() -> str:
        """Название метрики для таблицы лидеров."""
        return 'Время'

    @staticmethod
    def get_leaderboard_sort_field() -> str:
        """Основное поле для сортировки - время (чем меньше, тем лучше)."""
        return 'session_duration'

    @staticmethod
    def get_leaderboard_secondary_sort_field() -> str:
        """Вторичная сортировка не нужна."""
        return None

    def process_action(self, action):
        if not action:
            return

        # НОРМАЛИЗАЦИЯ
        action = action.strip().lower()
        print(f"ACTION RECEIVED: '{action}'")

        if action == "win":
            self.finish("win")
        elif action == "lose":
            self.finish("lose")
        elif action == "surrender":
            self.finish("surrender")




"""
@register_game
class TestGame(BaseEngine):
    slug = "test_game"
    template = "games/games_list/test_game.html"

    def process_action(self, action):
        if action in ["win", "lose", "surrender"]:
            self.finish(action)
"""