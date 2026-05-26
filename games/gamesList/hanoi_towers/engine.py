from games.engines.base_engine import BaseEngine
from games.registry import register_game

@register_game
class HanoiTowers(BaseEngine):
    """Игровой движок для игры «Ханойская башня»."""
    slug = "hanoi_towers"
    template = "games/games_list/hanoi_towers.html"

    name = "Ханойская башня"
    avatar = "static/avatars_games/hanoi_towers.png"
    short_description = """Логическая игра с дисками и 3 стержнями"""
    description = """<p>Ханойская башня — это головоломка, где нужно перенести пирамиду из дисков с начального стержня на конечный, используя один промежуточный.</p>

<h3>Основные правила:</h3>
<ul>
    <li>Перемещать только по одному диску за раз</li>
    <li>Можно брать только верхний диск</li>
    <li>Нельзя класть больший диск на меньший</li>
</ul>

<p><strong>Цель:</strong> перенести все диски со стержня 1 (самый левый) на стержень 3 (самый правый) за минимальное число ходов.</p>

<h3>Основные правила и цель игры</h3>
<ul>
    <li><strong>Исходные данные:</strong> В игре используются три стержня и несколько дисков, от количества которых будет зависеть сложность.</li>
    <li><strong>Исходная позиция:</strong> Все диски разного размера находятся на первом стержне в порядке убывания (пирамида).</li>
    <li><strong>Цель:</strong> Переместить всю пирамиду на третий стержень.</li>
    <li><strong>Правила перемещения:</strong>
        <ul>
            <li>За один ход можно переместить только один диск.</li>
            <li>Можно брать только верхний диск и переносить его на другой стержень.</li>
            <li>Запрещено класть больший диск на меньший.</li>
        </ul>
    </li>
</ul>

<style>
.hanoi-solution-image {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    margin: 5px auto;
    display: block;
}
</style>

<hr>

<h3>Решение головоломки</h3>

<p>Решить головоломку с одним диском легко — просто переместите его на правый стержень. Головоломка на два диска ненамного сложнее. Сначала нужно переместить маленький диск на стержень посередине, а большой — на стержень справа. Затем переместить маленький диск на большой на правом стержне.</p>

<p>Версия на три диска чуть сложнее, но и ее можно решить с помощью следующих семи шагов:</p>

<ol>
    <li>1. Переместить диск со стержня 1 на стержень 3</li>
    <li>2. Переместить диск со стержня 1 на стержень 2</li>
    <li>3. Переместить диск со стержня 3 на стержень 2</li>
    <li>4. Переместить диск со стержня 1 на стержень 3</li>
    <li>5. Переместить диск со стержня 2 на стержень 1</li>
    <li>6. Переместить диск со стержня 2 на стержень 3</li>
    <li>7. Переместить диск со стержня 1 на стержень 3</li>
</ol>

<img src="/static/files/disks3.gif" alt="Решение Ханойских башен для 3 дисков" class="hanoi-solution-image">

<hr>

<p>На рисунке ниже представлено решение Ханойских башен для 4 дисков за 15 шагов.</p>
<img src="/static/pictures/Решение Ханойские башни для 4 дисков.jpg" alt="Решение Ханойские башни для 4 дисков.jpg" class="hanoi-solution-image">

<h3>Подсчёт количества шагов для решения версии на четыре диска</h3>
<p>Теперь давайте посчитаем, сколько шагов потребуется для решения версии на четыре диска.</p>

<p>Нам нужно обязательно переместить самый большой диск, но для этого придётся сперва поместить все остальные диски на пустой стержень.</p>
<p>Если у нас не три диска, а четыре, то нужно переложить три верхних диска на пустой стержень (7 действий), а затем переместить самый большой диск (1 действие).</p>
<p>Теперь нужно снова переместить три диска с «временного» стержня на самый большой диск (еще 7 действий). Весь процесс будет состоять из 
7+1+7=15 действий.</p>


<hr>

<h3>Обобщим</h3>
<ol>
    <li>1. Чтобы переместить 
n дисков с левого стержня на правый, сначала необходимо переместить n−1 дисков на стержень посередине.</li>
    <li>2. Затем, когда диск под номером 
n, самый большой, оказывается на правом стержне, нужно переместить на него оставшиеся диски со стержня посередине.</li>
    <li>3. Чтобы переместить  n−1 дисков со стержня посередине направо, нужно сначала переместить  n−2 дисков на стержень слева, затем переместить 
(n−1)-й диск вправо, потом переместить 
n−2 дисков с левого стержня на правый и так далее.</li>
</ol>

<hr>
<p>Смело начинайте!</p>
"""
    # Уровни сложности: количество дисков и оптимальное число ходов
    levels = {i: {'name': f'Дисков: {i}', 'disks': i, 'optimal_moves': 2**i - 1} for i in range(2, 9)}

    def __init__(self, session):
        super().__init__(session)
        # Инициализируем игру только если она ещё не была инициализирована
        if 'pegs' not in self.session.data:
            self.initialize_game()

    def initialize_game(self, level=None):
        """Инициализирует или сбрасывает игровое состояние."""
        if level is None:
            level = self.session.data.get('level', 3)
        self.session.data['level'] = level

        # Стержни: три списка, в каждом диски от большого к маленькому (снизу вверх)
        disks = list(range(level, 0, -1))
        self.session.data['pegs'] = [disks, [], []]
        self.session.data['moves'] = 0
        self.session.data['optimal_moves'] = 2**level - 1
        self.session.save()

    def process_action(self, action):
        """Обрабатывает действия, приходящие от клиента.
        
        Поддерживает два формата:
        1. Строка: "win", "lose", "surrender" - для кнопок формы
        2. Словарь: {'type': 'move', 'from': 0, 'to': 2} - для API
        """
        # Обработка строкового формата (от кнопок формы)
        if isinstance(action, str):
            action = action.strip().lower()
            if action in ["win", "lose", "surrender"]:
                self.finish(action)
                return {'status': action}
            return {'error': 'Неизвестная команда'}
        
        # Обработка формата словаря (API)
        action_type = action.get('type')

        if action_type == 'move':
            from_peg = action.get('from')
            to_peg = action.get('to')
            if from_peg is None or to_peg is None:
                return {'error': 'Неверные параметры хода'}
            return self.make_move(from_peg, to_peg)

        elif action_type == 'get_state':
            return self.get_state()

        else:
            return {'error': 'Неизвестный тип действия'}

    def make_move(self, from_peg, to_peg):
        """Проверяет и выполняет ход."""
        # Создаем копию списка стержней для корректного сохранения в JSON
        pegs = [list(peg) for peg in self.session.data['pegs']]

        if not pegs[from_peg]:
            return {'error': 'На исходном стержне нет диска', 'state': self.get_state()}

        disk = pegs[from_peg][-1]  # верхний диск

        if pegs[to_peg] and pegs[to_peg][-1] < disk:
            return {'error': 'Нельзя класть больший диск на меньший', 'state': self.get_state()}

        # Выполняем ход
        pegs[from_peg].pop()
        pegs[to_peg].append(disk)
        
        # Обновляем данные сессии
        self.session.data['pegs'] = pegs
        self.session.data['moves'] = self.session.data.get('moves', 0) + 1
        self.session.save()

        # Проверка победы: все диски на правом стержне (индекс 2)
        if len(pegs[2]) == self.session.data['level']:
            self.finish('win')
            return {'status': 'win', 'state': self.get_state()}

        return {'success': True, 'state': self.get_state()}

    @staticmethod
    def get_levels_html(level_key, level_info) -> str:
        """Возвращает HTML-описание уровня для страницы выбора игры."""
        disks = level_info.get('disks', level_key)
        optimal_moves = level_info.get('optimal_moves', 2**int(disks) - 1)
        return f"Оптимально ходов: {optimal_moves}"

    @staticmethod
    def get_leaderboard_metric_name() -> str:
        """Название метрики для таблицы лидеров."""
        return 'Ходы'

    @staticmethod
    def get_leaderboard_sort_field() -> str:
        """Основное поле для сортировки - ходы (чем меньше, тем лучше)."""
        return 'moves'

    @staticmethod
    def get_leaderboard_secondary_sort_field() -> str:
        """Вторичная сортировка - время (если ходы равны)."""
        return 'session_duration'

    def get_state(self):
        """Возвращает текущее состояние игры для фронтенда."""
        return {
            'pegs': self.session.data['pegs'],
            'moves': self.session.data['moves'],
            'optimal_moves': self.session.data['optimal_moves'],
            'level': self.session.data['level'],
            'status': self.session.status,
        }

    def get_game_end_html(self) -> str:
        """Возвращает HTML-код со статистикой для отображения в модальном окне."""
        # Получаем количество ходов
        moves = self.session.data.get('moves', 0)
        optimal_moves = self.session.data.get('optimal_moves', 0)
        level = self.session.data.get('level', 3)
        
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
        
        # Получаем прогресс пользователя по каждому уровню (количество дисков)
        from games.models import GameSession
        progress_html = ""
        if hasattr(self.__class__, 'levels') and self.__class__.levels:
            progress_lines = []
            for level_key in sorted(self.__class__.levels.keys(), key=int):
                level_info = self.__class__.levels[level_key]
                disks_count = level_info.get('disks', level_key)
                level_optimal = level_info.get('optimal_moves', 2**int(disks_count) - 1)
                
                # Все завершенные сессии для этого уровня
                level_sessions = GameSession.objects.filter(
                    user=self.session.user,
                    game__slug=self.slug,
                    data__level=disks_count,
                ).exclude(
                    status='active'
                )
                total_for_level = level_sessions.count()
                
                # Победные сессии для этого уровня
                won_sessions = level_sessions.filter(status='win')
                won_count = won_sessions.count()
                
                # Сессии с оптимальным решением среди победных (moves == optimal_moves)
                optimal_for_level = won_sessions.filter(
                    data__moves=level_optimal
                ).count()
                
                # Брошенные сессии (surrender)
                surrendered_count = level_sessions.filter(status='surrender').count()
                
                if total_for_level > 0:
                    icon = '<i class="fas fa-check-circle text-success me-1"></i>'
                    surrendered_text = f', брошено: {surrendered_count}' if surrendered_count > 0 else ''
                    progress_lines.append(
                        f'{icon}{disks_count} дисков: {optimal_for_level} оптимальных из {won_count} завершенных Игр{surrendered_text}'
                    )
            
            if progress_lines:
                progress_html = '<hr>\n<p class="mb-2"><strong><i class="fas fa-chart-line me-2"></i>Прогресс:</strong></p>\n'
                for line in progress_lines:
                    progress_html += f'<p class="mb-1 ms-3" style="font-size:0.9rem;">{line}</p>\n'
        
        # Определяем, было ли решение оптимальным
        if moves == optimal_moves:
            optimal_text = f"<i class=\"fas fa-check-circle text-success me-1\"></i>Да"
        else:
            optimal_text = f"<i class=\"fas fa-times-circle text-danger me-1\"></i>Нет"

        # Формируем полную статистику
        stats_html = f"""
            <div class="game-stats">
                <div class="mb-3">
                    <p class="mb-2"><strong><i class="fas fa-stopwatch me-2"></i>Затраченное время:</strong> {time_str}</p>
                    <p class="mb-2"><strong><i class="fas fa-shoe-prints me-2"></i>Сделано ходов:</strong> <span class="fs-5">{moves}</span></p>
                    <p class="mb-2"><strong><i class="fas fa-bullseye me-2"></i>Оптимальное количество ходов:</strong> <span class="fs-5">{optimal_moves}</span></p>
                    <p class="mb-2"><strong><i class="fas fa-layer-group me-2"></i>Уровень:</strong> {level} дисков</p>
                    <p class="mb-2"><strong><i class="fas fa-star me-2"></i>Оптимальное решение:</strong> {optimal_text}</p>
                </div>
                {progress_html}
            </div>
        """
        
        return stats_html

