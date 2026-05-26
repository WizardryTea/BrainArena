
from django.utils.timezone import now
from games.engines.base_engine import BaseEngine
from games.registry import register_game

@register_game
class TestGame(BaseEngine):
    slug = "test_game"
    template = "games/games_list/test_game.html"
    name = "Тестовая игра"
    short_description = "Описание тестовой игры"
    description = "Расширенное описание тестовой игры"

    def get_game_end_html(self) -> str:
        # Получаем базовую статистику (состояние игры)
        base_html = super().get_game_end_html()
        
        # Вычисляем затраченное время
        if self.session.finished_at and self.session.created_at:
            time_diff = self.session.finished_at - self.session.created_at
            total_seconds = int(time_diff.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = "00:00:00"
        
        # Добавляем информацию о времени к базовой статистике
        time_html = f"""
            <p><strong>Затраченное время:</strong> {time_str}</p>
        """
        
        # Вставляем время после базовой статистики
        return base_html.replace('</div>', f'{time_html}</div>')

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

        if action in ["win", "lose", "surrender"]:
            self.finish(action)
        """
        if action == "win":
            self.finish("win")
        elif action == "lose":
            self.finish("lose")
        elif action == "surrender":
            self.finish("surrender")
        """