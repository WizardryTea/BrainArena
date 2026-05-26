from django.contrib import admin
from django.db.models import F, Count, Case, When, IntegerField, ExpressionWrapper, DurationField
from django.utils.html import format_html
from .models import Game, GameSession


def enable_games(modeladmin, request, queryset):
    for game in queryset:
        game.is_active = True
        game.save()  # Вызовет сигнал
enable_games.short_description = 'Включить выбранные игры'


def disable_games(modeladmin, request, queryset):
    for game in queryset:
        game.is_active = False
        game.save()  # Вызовет сигнал auto_surrender_on_disable
disable_games.short_description = 'Выключить выбранные игры'


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'short_description', 'is_active', 'created_at', 'total_sessions_count', 'win_rate_display']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'short_description']
    readonly_fields = ['created_at', 'total_sessions_count', 'win_rate_display', 'sessions_stats']
    actions = [enable_games, disable_games]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'short_description', 'description', 'is_active')
        }),
        ('Статистика игры', {
            'fields': ('total_sessions_count', 'win_rate_display', 'sessions_stats'),
            'description': 'Статистика вычисляется на основе игровых сессий'
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def total_sessions_count(self, obj):
        """Общее количество сессий для этой игры"""
        return obj.sessions.count()
    total_sessions_count.short_description = 'Всего сессий'
    
    def win_rate_display(self, obj):
        """Процент побед для этой игры"""
        total = obj.sessions.count()
        if total == 0:
            return '0%'
        wins = obj.sessions.filter(status='win').count()
        return f'{round(wins / total * 100, 1)}%'
    win_rate_display.short_description = 'Win Rate'
    
    def sessions_stats(self, obj):
        """Подробная статистика сессий"""
        stats = obj.sessions.aggregate(
            total=Count('id'),
            wins=Count(Case(When(status='win', then=1), output_field=IntegerField())),
            losses=Count(Case(When(status='lose', then=1), output_field=IntegerField())),
            surrenders=Count(Case(When(status='surrender', then=1), output_field=IntegerField())),
            active=Count(Case(When(status='active', then=1), output_field=IntegerField())),
        )
        return format_html(
            'Всего: <b>{}</b> | Побед: <b style="color:green">{}</b> | Поражений: <b style="color:red">{}</b> | Сдался: <b style="color:orange">{}</b> | Активных: <b style="color:blue">{}</b>',
            stats['total'], stats['wins'], stats['losses'], stats['surrenders'], stats['active']
        )
    sessions_stats.short_description = 'Детальная статистика'


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'game', 'status', 'created_at', 'finished_at', 'session_duration_display']
    list_filter = ['user', 'status', 'game', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'game__name']
    readonly_fields = ['id', 'session_duration_display', 'user_stats_display', 'game_stats_display']
    
    fieldsets = (
        ('Пользователь и игра', {
            'fields': ('user', 'game')
        }),
        ('Статус сессии', {
            'fields': ('status', 'data')
        }),
        ('Статистика пользователя', {
            'fields': ('user_stats_display',),
            'description': 'Статистика пользователя по этой игре (вычисляется из GameSession)'
        }),
        ('Временные метки', {
            'fields': ('created_at', 'finished_at', 'session_duration_display'),
            'classes': ('collapse',)
        })
    )
    
    def session_duration_display(self, obj):
        """Отображает длительность сессии в админ-панели"""
        return obj.session_duration
    session_duration_display.short_description = 'Время сессии'
    
    def user_stats_display(self, obj):
        """Отображает статистику пользователя по этой игре"""
        # Получаем статистику пользователя по этой игре через QuerySet
        stats = GameSession.objects.get_user_game_stats(obj.user, obj.game)
        return format_html(
            'Всего: <b>{}</b> | Побед: <b style="color:green">{}</b> | Поражений: <b style="color:red">{}</b> | Сдался: <b style="color:orange">{}</b> | Win Rate: <b>{}</b>%',
            stats['total_games'], stats['games_won'], stats['games_lost'], 
            stats['games_surrendered'], stats['win_rate']
        )
    user_stats_display.short_description = 'Статистика пользователя в этой игре'
    
    def game_stats_display(self, obj):
        """Отображает общую статистику пользователя по всем играм"""
        stats = GameSession.objects.get_user_stats(obj.user)
        return format_html(
            'Всего: <b>{}</b> | Побед: <b style="color:green">{}</b> | Поражений: <b style="color:red">{}</b> | Сдался: <b style="color:orange">{}</b> | Win Rate: <b>{}</b>%',
            stats['total_games'], stats['games_won'], stats['games_lost'], 
            stats['games_surrendered'], stats['win_rate']
        )
    game_stats_display.short_description = 'Общая статистика пользователя'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'game')