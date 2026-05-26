from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
import json

from django.contrib.auth.forms import UserCreationForm

from games.models import Game, GameSession
from users.models import UserProfile
from users.forms import UserRegistrationForm, UserProfileForm, UserUpdateForm


def users_list(request):
    """Список всех пользователей с агрегированной статистикой из GameSession"""
    from django.contrib.auth.models import User
    from django.db.models import Count, Case, When, IntegerField, F, ExpressionWrapper, FloatField
    
    # Получаем всех активных пользователей
    users = User.objects.filter(is_active=True).select_related('userprofile')
    
    # Аннотируем каждого пользователя статистикой из GameSession
    # Используем subquery для агрегации
    from django.db.models import Subquery, OuterRef
    
    # Подзапрос для подсчета статистики пользователя
    stats_subquery = GameSession.objects.filter(
        user=OuterRef('pk')
    ).values('user').annotate(
        total=Count('id'),
        wins=Count(Case(When(status='win', then=1), output_field=IntegerField())),
        losses=Count(Case(When(status='lose', then=1), output_field=IntegerField())),
    ).values('total', 'wins', 'losses')
    
    # Аннотируем пользователей
    users = users.annotate(
        total_games=Count('game_sessions'),
        games_won=Count(Case(When(game_sessions__status='win', then=1), output_field=IntegerField())),
        games_lost=Count(Case(When(game_sessions__status='lose', then=1), output_field=IntegerField())),
        win_rate=Case(
            When(total_games__gt=0, then=ExpressionWrapper(
                F('games_won') * 100.0 / F('total_games'),
                output_field=FloatField()
            )),
            default=0.0,
            output_field=FloatField()
        )
    ).distinct()
    
    context = {
        'users': users,
    }
    return render(request, 'users/users_list.html', context)


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            
            # Проверяем наличие параметра next в URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Неверные учетные данные')
    return render(request, 'registration/login.html')


def user_logout(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('home')


def profile(request, username=None):
    """Профиль пользователя с статистикой из GameSession"""
    if username:
        user = get_object_or_404(User, username=username)
        # Получаем профиль
        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(request, 'Профиль пользователя не найден')
            profile = UserProfile.objects.create(user=user)
            return redirect('home')
        
        # Проверяем доступность профиля, но не передаем status=403
        if not profile.is_public and (not request.user.is_authenticated or user != request.user):
            messages.error(request, 'Этот профиль приватный')
            return render(request, 'errors/error_access.html')
    else:
        if not request.user.is_authenticated:
            return redirect('login')
        user = request.user
        profile = user.userprofile

    # Получаем общую статистику пользователя через QuerySet GameSession
    # Все вычисления выполняются на уровне БД
    user_stats = GameSession.objects.get_user_stats(user)
    
    # Получаем прогресс пользователя по каждой игре через QuerySet
    # Использует group_by через values() и annotate() для агрегации на уровне БД
    user_games_progress = GameSession.objects.get_user_games_progress(user)

    # Настройка: показывать ли выключенные игры в прогрессе
    # Для своего профиля — читаем из UserProfile, для чужого — по умолчанию False
    if request.user.is_authenticated and user == request.user:
        show_hidden = profile.show_hidden_games
    else:
        show_hidden = False
    
    if not show_hidden:
        # Фильтруем прогресс - только включенные игры
        active_game_ids = Game.objects.filter(is_active=True).values_list('id', flat=True)
        user_games_progress = [g for g in user_games_progress if g['game'] in active_game_ids]
    
    # Получаем активные игры для продолжения (только включенные игры)
    active_games = GameSession.objects.filter(
        user=user, status='active', game__is_active=True
    ).select_related('game').order_by('-created_at')

    # Добавляем название уровня к каждой активной сессии
    from games.registry import get_game as get_engine
    for session in active_games:
        engine_cls = get_engine(session.game.slug)
        if engine_cls and hasattr(engine_cls, 'levels') and engine_cls.levels:
            level_key = session.data.get('level', '')
            level_info = engine_cls.levels.get(level_key, {})
            if isinstance(level_info, dict):
                session.level_name = level_info.get('name', level_key)
            else:
                session.level_name = str(level_key)
        else:
            session.level_name = ''

    # Получаем любые сессии выключенных игр, которые пользователь должен видеть:
    # 1) Активные сессии выключенных игр (были до нового сигнала, старые данные)
    # 2) Сданные сессии выключенных игр за последние 7 дней (сработал сигнал)
    from django.db.models import Q
    recent_threshold = timezone.now() - timezone.timedelta(days=7)
    disabled_auto_surrendered_sessions = GameSession.objects.filter(
        user=user,
        game__is_active=False,
    ).filter(
        Q(status='active') |
        Q(status='surrender', finished_at__gte=recent_threshold)
    ).select_related('game').order_by('-created_at')

    # Получаем завершенные игры для статистики с пагинацией
    completed_games_query = GameSession.objects.filter(
        user=user, status__in=['win', 'lose', 'surrender']
    ).select_related('game').order_by('-finished_at')
    
    # Пагинация: 10 игр на страницу
    paginator = Paginator(completed_games_query, 10)
    page_number = request.GET.get('page')
    completed_games = paginator.get_page(page_number)
    
    context = {
        'profile_user': user,
        'profile': profile,
        'user_stats': user_stats,  # Общая статистика (dict)
        'user_games_progress': user_games_progress,  # Прогресс по играм (QuerySet)
        'active_games': active_games,
        'disabled_auto_surrendered_sessions': disabled_auto_surrendered_sessions,
        'show_hidden': show_hidden,
        'completed_games': completed_games, # Завершенные игры для статистики
    }
    return render(request, 'users/profile.html', context)


@login_required
def delete_game(request, game_id):
    """Удаление игры (перемещение в список 'Брошено')"""
    game_instance = get_object_or_404(GameSession, id=game_id, user=request.user)
    
    # Меняем статус игры на 'surrender' (сдался)
    game_instance.status = 'surrender'
    game_instance.finished_at = timezone.now()
    game_instance.save()
    # Статистика теперь вычисляется через QuerySet из GameSession
    
    messages.success(request, 'Игра перемещена в список "Брошено"')
    return redirect('users:profile')


@login_required
def user_sessions(request):
    """Страница со статистикой всех завершенных игр пользователя с пагинацией"""
    user = request.user
    
    # Получаем завершенные игры для статистики с пагинацией
    completed_games_query = GameSession.objects.filter(
        user=user, status__in=['win', 'lose', 'surrender']
    ).select_related('game').order_by('-finished_at')
    
    # Пагинация: 15 игр на страницу
    paginator = Paginator(completed_games_query, 15)
    page_number = request.GET.get('page')
    completed_games = paginator.get_page(page_number)
    
    context = {
        'completed_games': completed_games,
    }
    return render(request, 'users/sessions.html', context)


@login_required
def toggle_hidden_games(request):
    """AJAX-эндпоинт для переключения отображения выключенных игр"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не разрешён'}, status=405)
    
    try:
        data = json.loads(request.body)
        show_hidden = data.get('show_hidden', True)
        profile = request.user.userprofile
        profile.show_hidden_games = bool(show_hidden)
        profile.save()
        
        # Пересчитываем прогресс с учётом новой настройки
        user = request.user
        user_games_progress = GameSession.objects.get_user_games_progress(user)
        
        if not show_hidden:
            active_game_ids = Game.objects.filter(is_active=True).values_list('id', flat=True)
            user_games_progress = [g for g in user_games_progress if g['game'] in active_game_ids]
        
        # Рендерим partial-шаблон с обновлёнными данными
        from django.template.loader import render_to_string
        html = render_to_string('users/partials/profile_progress.html', {
            'profile_user': user,
            'user': user,
            'show_hidden': show_hidden,
            'user_games_progress': user_games_progress,
        }, request=request)
        
        return JsonResponse({'status': 'ok', 'show_hidden': show_hidden, 'html': html})
    except (json.JSONDecodeError, AttributeError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def edit_profile(request):
    """Редактирование профиля"""
    profile = request.user.userprofile
    
    if request.method == 'POST':
        # Определяем тип действия
        action = request.POST.get('action')
        
        if action == 'select_base_avatar':
            # Обработка выбора готового аватара
            avatar_name = request.POST.get('base_avatar')
            if avatar_name:
                # Проверяем существование файла в статике
                import os
                from django.conf import settings
                avatar_path = os.path.join(settings.BASE_DIR, 'static', 'avatars_base', avatar_name)
                
                if os.path.exists(avatar_path):
                    # ВАЖНО: Сохраняем путь относительно статики, НЕ используем MEDIA
                    profile.avatar.name = f'avatars_base/{avatar_name}'
                    profile.save()
                    messages.success(request, 'Аватар успешно выбран!')
                else:
                    messages.error(request, 'Выбранный аватар не найден.')
            
            # Перенаправляем на GET-запрос
            return redirect('users:edit_profile')
        
        elif action == 'save_profile':
            # Обработка основной формы
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            user_form = UserUpdateForm(request.POST, instance=request.user)
            
            if profile_form.is_valid() and user_form.is_valid():
                profile_form.save()
                user_form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
        else:
            messages.error(request, 'Неизвестное действие')
    
    else:
        profile_form = UserProfileForm(instance=profile)
        user_form = UserUpdateForm(instance=request.user)
    
    base_avatars = UserProfile.get_base_avatars()
    
    context = {
        'profile_form': profile_form,
        'user_form': user_form,
        'base_avatars': base_avatars,
    }
    return render(request, 'users/edit_profile.html', context)