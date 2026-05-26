import random
from games.engines.base_engine import BaseEngine
from games.registry import register_game

@register_game
class Game2048(BaseEngine):
    slug = "2048"
    template = "games/games_list/2048.html"
    name = "2048"
    avatar = "static/avatars_games/2048.png"
    short_description = "Классическая логическая игра 2048. Соединяй одинаковые плитки и достигни 2048!"
    description = """
    <p>На игровом поле 4x4 с помощью доступных средств (стрелок на клавиатуре или свайпов на мобильных устройствах) перемещайте плитки.</p>
    <p>На каждом раунде в игре появляется новые плитки с цифрами «2» или "4". Нажимая стрелки, нужно сбросить их в сторону, при этом две плитки одного «номинала» при столкновении сливаются в одну с удвоенным значением (складываются). За удачное сложение начисляются очки, в соответствии с номиналом плитки.</p>
    <p>Движение возможно в 4 стороны.</p>
    <div class="text-center">
        
        <img src="/static/pictures/2048_img02.png" alt="2048 стратегия" class="img-fluid mb-3">
    </div>
    
    <hr>

    <h3>Стратегии и советы</h3>
    <p>Несколько советов начинающим игрокам, чтобы лучше разобраться в игре.<p>
    <div class="text-center">
        <img src="/static/pictures/2048_img01.png" alt="2048 стратегия" class="img-fluid mb-3">
    </div>
    <h4>Считайте внимательно</h4>
    <p>В 2048 настолько легко играть, что вы можете привыкнуть проходить партии на одном дыхании, даже не обращая особого внимания на то, что делаете. Это плохая идея. Не торопитесь — в конце концов, за обдумывание ходов нет никакого наказания. Также постарайтесь предсказать, где могут появиться новые блоки и как вы могли бы их разместить. Это как в шахматах.</p>
    <h4>Угловая фиксация - работайте по углам</h4>
    <p>Чтобы выиграть игру, вам нужна определённая стратегия. Если у вас её нет, вы, скорее всего, не продвинетесь дальше 512 очков. Поэтому хорошая стратегия — всегда держать фишку с самым высоким значением в одном из углов. Просто выберите один угол и направьте туда все свои фишки.</p>
    <p>Это не так просто, как кажется, но вы быстро освоите эту стратегию. Чтобы фишка с самым высоким значением не покинула «место короля», постарайтесь расположить вокруг неё фишки. Желательно, чтобы это были другие самые большие фишки.</p>
    <p>Освоив эту простую стратегию, вы скоро достигнете 2048 очков и более!</p>
    
    <p>После того, как вы разместили плитку с наивысшим значением, например, в правом нижнем углу, не перемещайте её. Чтобы гарантировать её неподвижность, необходимо постоянно заполнять последний ряд, нажимая стрелку вниз, чтобы использование стрелок влево и вправо не перемещало плитку с наивысшим значением.</p>
    <p>Объединяйте плитки с малым номиналом в 16 и 32 и двигайте в угол. Ваша цель — оставлять плитку на одном месте как можно дольше и постепенно увеличивать ее числовое значение</p>
    <p>В общем, это самый важный секрет для игры 2048 — держите плитку с наивысшим значением в углу и не перемещайте её.</p>
    <div class="text-center">
        <img src="/static/pictures/2048_img04.png" alt="2048 стратегия" class="img-fluid mb-3">
    </div>
    <h4>Оставляйте ряд с самой крупной плиткой заполненным</h4>
    <p>Например, если самая крупная плитка находится в правом верхнем углу, заполните плитками весь нижний ряд. Поочередно сдвигайте плитки в двух направлениях к углу (в данном примере «вверх» и «вправо»). Когда ряд заполнится, начните двигать плитки влево и вправо по собственному желанию без смещения самой крупной плитки из угла. Следите за этим рядом и вовремя заполняйте все освободившиеся ячейки, не сдвигая угловую плитку.</p>
    <div class="text-center">
        <img src="/static/pictures/2048_img05.png" alt="2048 стратегия" class="img-fluid mb-3">
    </div>
    <h4>Сосредоточьтесь на объединении плиток с малыми числами</h4>
    <p>Значительную часть игры вам намного важнее создавать плитки со значениями 8, 16 и 32, чем одну плитку с более крупным числом. В идеале эти плитки средней величины следует собирать рядом с выбранным углом. Так проще создавать цепные реакции из нескольких комбинаций, которые позволят добиться большего, чем просто создать одну плитку с большим числом.</p>
    
    <hr>

    <h3>Стратегия "Змейка"</h3>
    <p>Другая идеальная стратегия игры заключается в создании "банковой системы" из 4-х плиток. Плитка, обладающая самым крупным «номиналом» будет является «центральным банком», а с меньшими значениями «малыми банками». </p>
    <p>Эту группу нужно расположить линейно. Проще всего, расположить систему по горизонтали на нижней платформе, при этом, следует, исключить движение вверх. Таким образом, сумма продвигается по стеку, справа налево, в «центральный банк», через сеть «малых».</p>
    <div class="text-center">
        <img src="/static/pictures/2048_img03.png" alt="2048 стратегия" class="img-fluid mb-3">
    </div>
    <p>Используя данную стратегию, шанс проиграть крайне мал. Один из игроков смог набрать 131 072 в одной плитке и зафиксировал это на видео:</p>
    <div class="ratio ratio-16x9 mb-3">
        <video class="w-100" controls preload="metadata">
            <source src="/static/files/2048_record_2.mp4" type="video/mp4">
            Ваш браузер не поддерживает встроенное видео.
        </video>
    </div>
    <p>Цель игры — собрать плитку с «номиналом» 2048. Однако мы оставили возможность для Вас продолжить игру и после достижения данного числа. Улучшайте свой результат, следуя нашим советам и стратегиям!</p>
    <p></p>
    """

    def __init__(self, session):
        super().__init__(session)
        if not self.session.data:
            self._init_game()

    def _init_game(self):
        """Инициализация новой игры"""
        # Получаем лучший счет пользователя для этой игры
        from games.models import GameSession
        best_score = 0
        
        if self.session.user:
            best_sessions = GameSession.objects.filter(
                user=self.session.user,
                game__slug=self.slug,
                status='win'
            ).order_by('-data__score')
            
            if best_sessions.exists():
                best_score = best_sessions.first().data.get('score', 0)

        self.session.data = {
            'board': [[0] * 4 for _ in range(4)],
            'score': 0,
            'best_score': best_score,
            'goal': False,
            'win_goal': 2048,
            'is_win': False,
        }
        self._add_new_tile()
        self._add_new_tile()
        self.session.save()

    def _add_new_tile(self):
        """Добавляет новую плитку 2 (90%) или 4 (10%) в случайную свободную ячейку"""
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if self.session.data['board'][i][j] == 0:
                    empty_cells.append((i, j))
        
        if not empty_cells:
            return False
        
        i, j = random.choice(empty_cells)
        self.session.data['board'][i][j] = 2 if random.random() < 0.9 else 4
        return True

    def _compress(self, row):
        """Сжимает все ненулевые элементы влево"""
        new_row = [num for num in row if num != 0]
        new_row += [0] * (4 - len(new_row))
        return new_row

    def _merge(self, row):
        """Сливает одинаковые соседние элементы"""
        score_add = 0
        for i in range(3):
            if row[i] == row[i + 1] and row[i] != 0:
                row[i] *= 2
                score_add += row[i]
                row[i + 1] = 0
        return row, score_add

    def _move_left(self):
        """Выполняет ход влево для всего поля"""
        moved = False
        total_score = 0
        for i in range(4):
            original = self.session.data['board'][i].copy()
            row = self._compress(original)
            row, score = self._merge(row)
            row = self._compress(row)
            total_score += score
            self.session.data['board'][i] = row
            if original != row:
                moved = True
        return moved, total_score

    def _move_right(self):
        """Выполняет ход вправо для всего поля"""
        moved = False
        total_score = 0
        for i in range(4):
            original = self.session.data['board'][i].copy()
            row = original[::-1]
            row = self._compress(row)
            row, score = self._merge(row)
            row = self._compress(row)
            row = row[::-1]
            total_score += score
            self.session.data['board'][i] = row
            if original != row:
                moved = True
        return moved, total_score

    def _transpose(self):
        """Транспонирует матрицу игрового поля"""
        self.session.data['board'] = [list(row) for row in zip(*self.session.data['board'])]

    def _move_up(self):
        """Выполняет ход вверх"""
        self._transpose()
        moved, score = self._move_left()
        self._transpose()
        return moved, score

    def _move_down(self):
        """Выполняет ход вниз"""
        self._transpose()
        moved, score = self._move_right()
        self._transpose()
        return moved, score

    def _check_game_over(self):
        """Проверяет окончена ли игра"""
        # Проверяем есть ли пустые ячейки
        for i in range(4):
            for j in range(4):
                if self.session.data['board'][i][j] == 0:
                    return False
        
        # Проверяем есть ли возможные слияния
        for i in range(4):
            for j in range(4):
                if i < 3 and self.session.data['board'][i][j] == self.session.data['board'][i+1][j]:
                    return False
                if j < 3 and self.session.data['board'][i][j] == self.session.data['board'][i][j+1]:
                    return False
        
        return True

    def _check_win(self):
        """Проверяет достиг ли игрок 2048 и устанавливает флаги goal/is_win"""
        for i in range(4):
            for j in range(4):
                if self.session.data['board'][i][j] >= 2048:
                    if not self.session.data['goal']:
                        self.session.data['goal'] = True
                        self.session.data['is_win'] = True
                    return True
        return False

    def process_action(self, action):
        if not action:
            return

        action = action.strip().lower()
        
        if action in ["win", "lose", "surrender"]:
            self.finish(action)
            return

        if self.session.status != 'active':
            return

        moved = False
        score = 0

        if action == "left":
            moved, score = self._move_left()
        elif action == "right":
            moved, score = self._move_right()
        elif action == "up":
            moved, score = self._move_up()
        elif action == "down":
            moved, score = self._move_down()

        if moved:
            self.session.data['score'] += score
            
            # Обновляем лучший счет если текущий больше
            if self.session.data['score'] > self.session.data['best_score']:
                self.session.data['best_score'] = self.session.data['score']
            
            self._add_new_tile()

            # Проверяем достижение цели 2048 (только устанавливает флаги, не завершает игру)
            self._check_win()
            
            # Проверяем, что больше нет ходов
            if self._check_game_over():
                if self.session.data['goal']:
                    self.finish('win')
                else:
                    self.finish('lose')

        self.session.save()

    @staticmethod
    def get_leaderboard_metric_name() -> str:
        return 'Максимальный счет'

    @staticmethod
    def get_leaderboard_sort_field() -> str:
        return 'score'

    @staticmethod
    def get_leaderboard_secondary_sort_field() -> str:
        return 'session_duration'

    @staticmethod
    def get_leaderboard_sort_order() -> str:
        return 'desc'
        
    @staticmethod
    def get_leaderboard_value(session):
        return session.data.get('score', 0)

    # Показывать статус игры в таблице лидеров
    show_game_status_leaderboard = True

    def get_state(self):
        """Возвращает текущее состояние игры для AJAX запросов"""
        return {
            'board': self.session.data['board'],
            'score': self.session.data['score'],
            'best_score': self.session.data['best_score'],
            'goal': self.session.data['goal'],
            'is_win': self.session.data['is_win'],
            'win_goal': self.session.data['win_goal'],
        }

    def get_game_end_html(self) -> str:
        base_html = super().get_game_end_html()
        
        score = self.session.data.get('score', 0)
        goal = self.session.data.get('goal', False)
        win_goal = self.session.data.get('win_goal', 2048)
        goal_text = f"<i class=\"fas fa-check-circle text-success me-1\"></i>Да" if goal else f"<i class=\"fas fa-times-circle text-danger me-1\"></i>Нет"

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
        
        # Получаем лучший счет пользователя по всем завершённым играм 2048
        from games.models import GameSession
        best_score = self.session.data.get('best_score', 0)
        if self.session.user:
            best_sessions = GameSession.objects.filter(
                user=self.session.user,
                game__slug=self.slug,
                status='win'
            ).order_by('-data__score')
            if best_sessions.exists():
                all_time_best = best_sessions.first().data.get('score', 0)
                best_score = max(best_score, all_time_best)
        
        # Получаем прогресс пользователя по уровням (is_win) в 2048
        total_levels = GameSession.objects.filter(
            user=self.session.user,
            game__slug=self.slug,
        ).exclude(
            status='active'
        ).count()
        
        won_levels = GameSession.objects.filter(
            user=self.session.user,
            game__slug=self.slug,
            data__is_win=True,
        ).exclude(
            status='active'
        ).count()
        
        progress_text = f"Вы достигли цель {won_levels} из {total_levels}" if total_levels > 0 else "Нет завершенных игр"
        
        score_html = f"""
            <p class="mb-2"><strong><i class="fas fa-stopwatch me-2"></i>Затраченное время:</strong> {time_str}</p>
            <p class="mb-2"><strong><i class="fas fa-layer-group me-2"></i>Набранный счет:</strong> {score}</p>
            <p class="mb-2"><strong><i class="fas fa-trophy me-2"></i>Лучший счет:</strong> {best_score}</p>
            <p class="mb-2"><strong><i class="fas fa-bullseye me-2"></i>Цель {win_goal} достигнута:</strong> {goal_text}</p>
            <hr>
            <p class="mb-0"><strong><i class="fas fa-chart-line me-2"></i>Прогресс:</strong> {progress_text}</p>
        """
        
        return base_html.replace('</div>', f'{score_html}</div>')