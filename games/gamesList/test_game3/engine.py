
from games.engines.base_engine import BaseEngine
from games.registry import register_game

@register_game
class TestGame_2(BaseEngine):
    slug = "test_game_3"
    template = "games/games_list/test_game_3.html"
    description = "Описание игры Test Game 3"
    is_active = False
    name = "Тестовая игра 3"

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