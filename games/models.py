from django.db import models
from django.db.models import Count, Sum, Q, F, Value, Case, When, IntegerField, ExpressionWrapper
from django.db.models.fields import DurationField
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Game(models.Model):
    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(default="Описание игры по умолчанию")
    short_description = models.TextField(default="Краткое описание игры по умолчанию")
    avatar = models.CharField(max_length=255, default="media/avatars_games/game_base.png")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class GameSessionManager(models.Manager):
    """
    Менеджер для GameSession с методами для вычисления статистики через QuerySet.
    Все вычисления выполняются на уровне базы данных для производительности.
    """
    
    def get_user_stats(self, user):
        """
        Возвращает общую статистику пользователя по всем играм.
        Вычисляется через агрегацию QuerySet на уровне БД.
        
        Возвращает dict с полями:
        - total_games: всего игр
        - games_won: побед
        - games_lost: проигрышей
        - games_surrendered: сдался
        - win_rate: процент побед
        """
        # Агрегируем статистику по всем сессиям пользователя
        stats = self.filter(user=user).aggregate(
            total_games=Count('id'),
            games_won=Count(Case(When(status='win', then=1), output_field=IntegerField())),
            games_lost=Count(Case(When(status='lose', then=1), output_field=IntegerField())),
            games_surrendered=Count(Case(When(status='surrender', then=1), output_field=IntegerField())),
        )
        
        total = stats['total_games'] or 0
        won = stats['games_won'] or 0
        lost = stats['games_lost'] or 0
        surrendered = stats['games_surrendered'] or 0
        win_rate = round((won / total) * 100, 2) if total > 0 else 0
        
        return {
            'total_games': total,
            'games_won': won,
            'games_lost': lost,
            'games_surrendered': surrendered,
            'win_rate': win_rate,
        }
    
    def get_user_game_stats(self, user, game):
        """
        Возвращает статистику пользователя по конкретной игре.
        Вычисляется через агрегацию QuerySet на уровне БД.
        
        Возвращает dict с полями:
        - total_games: всего игр
        - games_won: побед
        - games_lost: проигрышей
        - games_surrendered: сдался
        - win_rate: процент побед
        - best_time: лучшее время ( timedelta или None)
        """
        # Базовая агрегация
        stats = self.filter(user=user, game=game).aggregate(
            total_games=Count('id'),
            games_won=Count(Case(When(status='win', then=1), output_field=IntegerField())),
            games_lost=Count(Case(When(status='lose', then=1), output_field=IntegerField())),
            games_surrendered=Count(Case(When(status='surrender', then=1), output_field=IntegerField())),
        )
        
        total = stats['total_games'] or 0
        won = stats['games_won'] or 0
        lost = stats['games_lost'] or 0
        surrendered = stats['games_surrendered'] or 0
        win_rate = round((won / total) * 100, 2) if total > 0 else 0
        
        # Находим лучшее время среди победных сессий
        best_time = None
        winning_sessions = self.filter(
            user=user,
            game=game,
            status='win',
            finished_at__isnull=False
        )
        
        if winning_sessions.exists():
            # Аннотируем длительность каждой сессии и находим минимальную
            from django.db.models import ExpressionWrapper, DurationField, F
            from django.db.models.functions import Abs
            
            # Вычисляем минимальную длительность
            best_session = winning_sessions.annotate(
                duration=ExpressionWrapper(
                    F('finished_at') - F('created_at'),
                    output_field=DurationField()
                )
            ).order_by('duration').first()
            
            if best_session:
                best_time = best_session.finished_at - best_session.created_at
        
        return {
            'total_games': total,
            'games_won': won,
            'games_lost': lost,
            'games_surrendered': surrendered,
            'win_rate': win_rate,
            'best_time': best_time,
        }
    
    def get_user_games_progress(self, user):
        """
        Возвращает прогресс пользователя по каждой игре.
        Использует group_by через values() и annotate() для агрегации на уровне БД.
        
        Возвращает QuerySet с аннотациями:
        - game: объект игры
        - total_games: всего игр
        - games_won: побед
        - games_lost: проигрышей
        - games_surrendered: сдался
        - win_rate: процент побед
        """
        from django.db.models import ExpressionWrapper, DurationField, F
        
        return self.filter(user=user).values(
            'game', 'game__name', 'game__slug', 'game__avatar'
        ).annotate(
            total_games=Count('id'),
            games_won=Count(Case(When(status='win', then=1), output_field=IntegerField())),
            games_lost=Count(Case(When(status='lose', then=1), output_field=IntegerField())),
            games_surrendered=Count(Case(When(status='surrender', then=1), output_field=IntegerField())),
            win_rate=Case(
                When(total_games__gt=0, then=ExpressionWrapper(
                    F('games_won') * 100.0 / F('total_games'),
                    output_field=models.FloatField()
                )),
                default=0.0,
                output_field=models.FloatField()
            )
        ).order_by('-total_games')
    
    def get_all_users_stats(self):
        """
        Возвращает статистику всех пользователей.
        Использует group_by через values() и annotate() для агрегации на уровне БД.
        
        Возвращает QuerySet с аннотациями:
        - user: объект пользователя
        - total_games: всего игр
        - games_won: побед
        - games_lost: проигрышей
        - win_rate: процент побед
        """
        return self.values(
            'user', 'user__username', 'user__first_name', 'user__last_name',
            'user__userprofile__avatar', 'user__userprofile__is_public'
        ).annotate(
            total_games=Count('id'),
            games_won=Count(Case(When(status='win', then=1), output_field=IntegerField())),
            games_lost=Count(Case(When(status='lose', then=1), output_field=IntegerField())),
            win_rate=Case(
                When(total_games__gt=0, then=ExpressionWrapper(
                    F('games_won') * 100.0 / F('total_games'),
                    output_field=models.FloatField()
                )),
                default=0.0,
                output_field=models.FloatField()
            )
        ).order_by('-total_games', '-games_won')
    
    def get_leaderboard(self, game, level=None):
        """
        Возвращает таблицу лидеров для конкретной игры.
        Фильтрует по уровню если указан.
        
        Возвращает QuerySet с аннотациями:
        - user: объект пользователя
        - best_time: лучшее время
        - games_played: сколько игр сыграно
        """
        from django.db.models import ExpressionWrapper, DurationField, F, Min
        
        queryset = self.filter(game=game, status='win', finished_at__isnull=False)
        
        if level is not None:
            queryset = queryset.filter(data__level=level)
        
        return queryset.values(
            'user', 'user__username', 'user__first_name', 'user__last_name',
            'user__userprofile__avatar'
        ).annotate(
            games_played=Count('id'),
            best_time=Min(
                ExpressionWrapper(
                    F('finished_at') - F('created_at'),
                    output_field=DurationField()
                )
            )
        ).order_by('best_time')


class GameSession(models.Model):
    class Meta:
        verbose_name = 'Игровая сессия'
        verbose_name_plural = 'Игровые сессии'
        ordering = ['-created_at']
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('win', 'Win'),
        ('lose', 'Lose'),
        ('surrender', 'Surrender'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(default=timezone.now)
    
    objects = GameSessionManager()
    
    @property
    def session_duration(self):
        """Вычисляет длительность сессии в формате ЧЧ:ММ:СС"""
        if self.finished_at:
            delta = self.finished_at - self.created_at
        else:
            # Если сессия еще не завершена, считаем до текущего времени
            delta = timezone.now() - self.created_at
        
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def session_duration_timedelta(self):
        """Возвращает длительность сессии как timedelta"""
        if self.finished_at:
            return self.finished_at - self.created_at
        return timezone.now() - self.created_at
    
    def __str__(self):
        return f"{self.user.username} - {self.game.name} - {self.status}"