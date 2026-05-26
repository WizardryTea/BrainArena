from django.utils.timezone import now

class BaseEngine:
    name = None
    slug = None
    template = None
    description = None
    short_description = None
    levels = None
    avatar = "media/avatars_games/game_base.png"
    
    def get_leaderboard_html(self, level_key, level_info) -> str:
        """
        Возвращает HTML-описание конкретной игры для лидерборда.
        Метод для переопределения в наследниках.
        По умолчанию возвращает пустую строку.
        """
        return ''

    @staticmethod
    def get_leaderboard_metric_name() -> str:
        """
        Возвращает название метрики для отображения в таблице лидеров.
        Метод для переопределения в наследниках.
        """
        return ''

    @staticmethod
    def get_leaderboard_sort_field() -> str:
        """
        Возвращает поле из data сессии для сортировки в лидерборде.
        Чем меньше значение, тем лучше (ascending sort).
        Метод для переопределения в наследниках.
        """
        return 'session_duration'

    @staticmethod
    def get_leaderboard_secondary_sort_field() -> str:
        """
        Возвращает поле для вторичной сортировки (если основное поле одинаковое).
        Метод для переопределения в наследниках.
        """
        return None

    @staticmethod
    def get_leaderboard_sort_order() -> str:
        """
        Возвращает направление сортировки для лидерборда.
        'asc' - по возрастанию (меньше = лучше, например ходы, время)
        'desc' - по убыванию (больше = лучше, например счёт)
        Метод для переопределения в наследниках.
        """
        return 'asc'

    def get_levels_html(self, level_key, level_info) -> str:
        """
        Возвращает HTML-описание конкретного уровня сложности.
        Метод для переопределения в наследниках.
        По умолчанию возвращает пустую строку.
        """
        return ''

    def get_game_end_html(self) -> str:
        """
        Возвращает HTML-код со статистикой для отображения в модальном окне.
        По умолчанию возвращает базовую статистику.
        Метод для переопределения.
        """
        status_text = {
            'win': 'Победа',
            'lose': 'Поражение',
            'surrender': 'Сдался'
        }
        status = self.session.status
        status_label = status_text.get(status, status)
        
        return f"""
            <div class="game-stats">
                <p><strong>Состояние игры:</strong> {status_label}</p>
            </div>
        """

    def __init__(self, session):
        self.session = session

    def process_action(self, action):
        # raise NotImplementedError
        if not action:
            return

        # НОРМАЛИЗАЦИЯ
        action = action.strip().lower()
        print(f"ACTION RECEIVED: '{action}'")

        if action in ["win", "lose", "surrender"]:
            self.finish(action)


    def finish(self, status):
        """
        Завершает игру с указанным статусом.
        Статистика пользователя вычисляется через QuerySet из GameSession,
        поэтому дополнительное обновление не требуется.
        """
        self.session.status = status
        self.session.finished_at = now()
        self.session.save()
        # Статистика вычисляется через QuerySet из GameSession
        # Методы GameSession.objects.get_user_stats() и get_user_game_stats()
        # автоматически подсчитывают все завершенные сессии