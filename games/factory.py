from .registry import get_game

class GameFactory:
    @staticmethod
    def create(session):
        cls = get_game(session.game.slug)
        if not cls:
            raise Exception("Game not registered")
        return cls(session)
