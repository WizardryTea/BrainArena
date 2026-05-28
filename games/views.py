
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import GameSession, Game
from .factory import GameFactory
from .registry import get_game as get_engine

from django.db.models import Count
from users.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages


from django.contrib.auth.models import User

def home(request):
    # Показываем на главной странице 3 популярные игры в нужном порядке
    game_slugs = ["2048", "hanoi_towers", "bulls_and_cows"]
    games = [Game.objects.get(slug=slug, is_active=True) for slug in game_slugs]
    
    # Общая статистика сайта
    total_users = User.objects.filter(is_active=True).count()
    total_sessions = GameSession.objects.count()

    return render(request, 'index.html', {
        'games': games,
        'total_users': total_users,
        'total_sessions': total_sessions
    })

def start_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    
    # Проверяем, авторизован ли пользователь
    if not request.user.is_authenticated:
        # Сохраняем URL игры для последующего редиректа после входа
        login_url = f"{reverse('users:login')}?next={reverse('games:start', args=[game_id])}"
        return redirect(login_url)

    # Получаем уровень из query-параметра
    level = request.GET.get('level', None)
    
    # Проверяем наличие активной сессии для этой игры
    active_session = GameSession.objects.filter(
        user=request.user,
        game=game,
        status='active'
    ).first()

    if active_session:
        # Один slug для игры = 1 возможной сессии.
        # Даже если есть разные levels для одного slug, нужно предлагать пересоздавать сессию.
        # Получаем русское название уровня
        level_key = active_session.data.get('level', '')
        level_name = level_key
        if level_key:
            engine_cls = get_engine(game.slug)
            if engine_cls and hasattr(engine_cls, 'levels'):
                level_info = engine_cls.levels.get(level_key, {})
                if isinstance(level_info, dict):
                    level_name = level_info.get('name', level_key)
        return render(request, 'games/game_start_choice.html', {
            'game': game,
            'active_session': active_session,
            'requested_level': level,
            'level_name': level_name,
        })

    # Нет активной сессии - создаем новую
    session_data = {}
    if level:
        # Пытаемся преобразовать в int, если не получается - оставляем строкой
        try:
            session_data['level'] = int(level)
        except (ValueError, TypeError):
            session_data['level'] = level
    
    session = GameSession.objects.create(
        user=request.user,
        game=game,
        data=session_data
    )

    # Формируем URL с параметром level, если он указан
    if level:
        return redirect(f"{reverse('games:game_play', args=[session.id])}?level={level}")
    return redirect('games:game_play', session_id=session.id)


def start_new_game(request, game_id):
    """Начать новую игру, завершив текущую активную сессию"""
    game = get_object_or_404(Game, id=game_id)
    
    # Проверяем, авторизован ли пользователь
    if not request.user.is_authenticated:
        return redirect('users:login')

    # Получаем уровень из query-параметра
    level = request.GET.get('level', None)

    if request.method == 'POST':
        # Завершаем текущую активную сессию
        active_session = GameSession.objects.filter(
            user=request.user,
            game=game,
            status='active'
        ).first()

        if active_session:
            # Меняем статус на 'surrender' (брошено)
            active_session.status = 'surrender'
            active_session.finished_at = timezone.now()
            active_session.save()
            # Статистика теперь вычисляется через QuerySet из GameSession

        # Создаем новую сессию с уровнем (если указан)
        session_data = {}
        if level:
            # Пытаемся преобразовать в int, если не получается - оставляем строкой
            try:
                session_data['level'] = int(level)
            except (ValueError, TypeError):
                session_data['level'] = level
        
        session = GameSession.objects.create(
            user=request.user,
            game=game,
            data=session_data
        )

        # Формируем URL с параметром level, если он указан
        if level:
            return redirect(f"{reverse('games:game_play', args=[session.id])}?level={level}")
        return redirect('games:game_play', session_id=session.id)
    
    return redirect('games:game_detail', game_id=game_id)


def surrender_game(request, session_id):
    """Сдаться в игре"""
    session = get_object_or_404(GameSession, id=session_id)
    
    # Проверяем, принадлежит ли сессия текущему пользователю
    if session.user != request.user:
        return render(request, 'errors/error_access.html')
    
    # Проверяем статус сессии
    if session.status != 'active':
        return render(request, 'errors/error_access.html')
    
    if request.method == 'POST':
        # Завершаем игру со статусом 'surrender'
        session.status = 'surrender'
        session.finished_at = timezone.now()
        session.save()
        # Статистика вычисляется через QuerySet из GameSession
        
        messages.success(request, 'Игра завершена. Вы сдались.')
        return redirect('users:profile')
    
    return redirect('games:game_play', session_id=session_id)


@login_required
def surrender_all_active_games(request):
    """Сдаться по всем активным сессиям"""
    if request.method == 'POST':
        # Получаем все активные сессии пользователя
        active_sessions = GameSession.objects.filter(
            user=request.user,
            status='active'
        )
        
        count = active_sessions.count()
        
        # Обновляем все сессии за один запрос
        active_sessions.update(
            status='surrender',
            finished_at=timezone.now()
        )
        
        if count > 0:
            messages.success(request, f'Завершено {count} активных игр. Вы сдались по всем сессиям.')
        else:
            messages.info(request, 'У вас нет активных игр для завершения.')
        
        return redirect('users:profile')
    
    return redirect('users:profile')

def play(request, session_id):
    # Проверка доступа к сессии
    session = get_object_or_404(GameSession, id=session_id)
    
    # Проверяем, принадлежит ли сессия текущему пользователю
    if session.user != request.user:
        return render(request, 'errors/error_access.html')
    
    # Для завершенных игр показываем ошибку доступа (нельзя вернуться в завершенную игру)
    # Но разрешаем AJAX-запросы для получения статистики
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if session.status != 'active' and not is_ajax:
        return render(request, 'errors/error_access.html')
    
    # Фабрика создает нужный движок
    engine = GameFactory.create(session)

    # Получаем action из POST-данных
    action_raw = request.POST.get('action', '')
    
    # Пытаемся распарсить JSON, если это словарь
    action = action_raw
    if action_raw.startswith('{'):
        try:
            import json
            action = json.loads(action_raw)
        except (json.JSONDecodeError, ValueError):
            action = action_raw.strip().lower()
    else:
        action = action_raw.strip().lower()
    
    if action and session.status == 'active':
        # Вызов логики игры
        engine.process_action(action)
        # После обработки действия обновляем сессию из базы
        session.refresh_from_db()

    # Подготавливаем контекст
    context = {"session": session}
    
    # Если игра завершена, добавляем HTML со статистикой
    if session.status != 'active':
        context['game_end_html'] = engine.get_game_end_html()
        # Добавляем URL для редиректа на страницу статистики игры
        context['redirect_url'] = reverse('games:game_end', args=[session.id])
        
        # Для AJAX-запросов возвращаем отрендеренное модальное окно
        if is_ajax:
            from django.http import JsonResponse
            from django.template.loader import render_to_string
            modal_html = render_to_string('games/includes/game_end_modal.html', context, request=request)
            return JsonResponse({
                'status': session.status,
                'state': engine.get_state(),
                'modal_html': modal_html,
                'redirect_url': context['redirect_url']
            })
        else:
            # Для обычных запросов перенаправляем на страницу статистики
            return redirect('games:game_end', session_id=session.id)
    
    # Для активных игр
    if is_ajax:
        # Для AJAX-запросов возвращаем JSON с текущим состоянием
        from django.http import JsonResponse
        return JsonResponse({
            'status': session.status,
            'state': engine.get_state(),
            'success': True
        })
    
    return render(request, engine.template, context)

def game_end(request, session_id):
    """Страница завершения игры - статистика игры"""
    session = get_object_or_404(GameSession, id=session_id)
    
    # Проверяем, принадлежит ли сессия текущему пользователю
    if session.user != request.user:
        return render(request, 'errors/error_access.html')
    
    # Проверяем, что игра завершена
    if session.status == 'active':
        return redirect('games:game_play', session_id=session_id)
    
    engine = GameFactory.create(session)
    
    context = {
        'session': session,
        'game_end_html': engine.get_game_end_html(),
    }
    return render(request, 'games/game_end.html', context)

def leaderboard(request):
    """Таблица лидеров по играм с разделением по уровням сложности"""
    # Получаем все активные игры для выпадающего списка
    games = Game.objects.filter(is_active=True).order_by('name')
    
    # Получаем выбранную игру из параметра
    selected_game_slug = request.GET.get('game', None)
    selected_game = None
    engine_class = None
    leaderboard_levels = {}  # Словарь: level_key -> список записей (топ-3)
    user_best_entries = {}  # Словарь: level_key -> лучшая игра пользователя (если не в топ-3)
    metric_name = 'Время'
    
    if selected_game_slug:
        selected_game = get_object_or_404(Game, slug=selected_game_slug)
        
        # Если игра выключена - 404
        if not selected_game.is_active:
            from django.http import Http404
            raise Http404("Игра выключена администрацией")
        
        # Получаем все завершенные игры со статусом WIN, для 2048 также включаем другие статусы
        status_filters = ['win']
        if selected_game_slug == '2048':
            status_filters = ['win', 'surrender', 'lose']
            
        sessions = GameSession.objects.filter(
            game=selected_game,
            status__in=status_filters
        ).select_related('user').order_by('finished_at')
        
        # Пытаемся получить движок игры для определения метрик
        try:
            from .registry import get_game
            engine_class = get_game(selected_game.slug)
        except Exception:
            engine_class = None
        
        # Получаем название метрики
        if engine_class and hasattr(engine_class, 'get_leaderboard_metric_name'):
            metric_name = engine_class.get_leaderboard_metric_name()
        
        # Получаем допустимые уровни для этой игры
        valid_levels = set()
        if engine_class and hasattr(engine_class, 'levels') and engine_class.levels is not None:
            valid_levels = set(engine_class.levels.keys())
        
        # Группируем сессии по уровням
        for session in sessions:
            level_key = session.data.get('level', 'default')
            
            # Пропускаем сессии с невалидным уровнем (если игра имеет уровни)
            if valid_levels and level_key not in valid_levels:
                continue
            
            if level_key not in leaderboard_levels:
                leaderboard_levels[level_key] = []
            
            # Приоритет статуса для 2048: win=0, surrender=1, lose=2
            status_priority = {'win': 0, 'surrender': 1, 'lose': 2}
            
            entry = {
                'user': session.user,
                'session': session,
                'time': session.session_duration,
                'level': level_key,
                'metric_value': None,
                'status_priority': status_priority.get(session.status, 3),
            }
            
            # Получаем метрику из сессии
            if engine_class:
                sort_field = engine_class.get_leaderboard_sort_field() if hasattr(engine_class, 'get_leaderboard_sort_field') else 'session_duration'
                
                if sort_field == 'session_duration':
                    entry['metric_value'] = session.session_duration
                elif sort_field in session.data:
                    entry['metric_value'] = session.data[sort_field]
                else:
                    entry['metric_value'] = session.session_duration
            else:
                entry['metric_value'] = session.session_duration
            
            leaderboard_levels[level_key].append(entry)
        
        # Сортируем и присваиваем места для каждого уровня
        for level_key, entries in leaderboard_levels.items():
            if engine_class and hasattr(engine_class, 'get_leaderboard_sort_field'):
                sort_field = engine_class.get_leaderboard_sort_field()
                secondary_sort_field = engine_class.get_leaderboard_secondary_sort_field() if hasattr(engine_class, 'get_leaderboard_secondary_sort_field') else None
                sort_order = engine_class.get_leaderboard_sort_order() if hasattr(engine_class, 'get_leaderboard_sort_order') else 'asc'
                
                if sort_order == 'desc':
                    # Для счета и других метрик - сортировка по УБЫВАНИЮ (больше значение = лучше)
                    # Для 2048: дополнительно по статусу (win > surrender > lose), потом по времени
                    if selected_game_slug == '2048':
                        entries.sort(key=lambda x: (
                            -x['metric_value'] if x['metric_value'] is not None else float('-inf'),
                            x['status_priority'],
                            x['time']
                        ))
                    else:
                        entries.sort(key=lambda x: (
                            -x['metric_value'] if x['metric_value'] is not None else float('-inf'),
                            x['time']
                        ))
                else:
                    # Для времени, ходов и других метрик - сортировка по ВОЗРАСТАНИЮ (меньше = лучше)
                    # Вторично по времени (при равных ходах меньше время = лучше)
                    entries.sort(key=lambda x: (
                        x['metric_value'] if x['metric_value'] is not None else float('inf'),
                        x['time']
                    ))
            
            # Присваиваем места
            for i, entry in enumerate(entries):
                rank = i + 1
                if rank == 1:
                    entry['rank'] = 'I'
                elif rank == 2:
                    entry['rank'] = 'II'
                elif rank == 3:
                    entry['rank'] = 'III'
                else:
                    entry['rank'] = str(rank)
            
            # Ограничиваем до топ-3
            top_entries = entries[:3]
            leaderboard_levels[level_key] = top_entries
            
            # Находим лучшую игру текущего пользователя (если не в топ-3)
            if request.user.is_authenticated:
                user_entries = [e for e in entries if e['user'] == request.user]
                if user_entries:
                    best_user_entry = user_entries[0]  # Уже отсортировано - лучший результат
                    # Проверяем, входит ли в топ-3
                    if best_user_entry['rank'] not in ['I', 'II', 'III']:
                        user_best_entries[level_key] = best_user_entry
    
    # Получаем информацию об уровнях для отображения
    levels_info = {}
    if selected_game and engine_class and hasattr(engine_class, 'levels') and engine_class.levels is not None:
        for level_key, level_info in engine_class.levels.items():
            levels_info[level_key] = level_info.get('name', level_key)
    
    # Сортируем уровни для последовательного отображения на странице
    # Числовые ключи сортируются как числа, строковые как строки
    def _level_sort_key(item):
        key = item[0]
        try:
            return (0, int(key))
        except (ValueError, TypeError):
            return (1, str(key))
    
    leaderboard_levels = dict(sorted(leaderboard_levels.items(), key=_level_sort_key))
    levels_info = dict(sorted(levels_info.items(), key=_level_sort_key))
    
    # Проверяем нужно ли показывать статус игры в лидерборде
    show_game_status = False
    if engine_class and hasattr(engine_class, 'show_game_status_leaderboard'):
        show_game_status = engine_class.show_game_status_leaderboard

    context = {
        'games': games,
        'selected_game': selected_game,
        'leaderboard_levels': leaderboard_levels,
        'user_best_entries': user_best_entries,
        'metric_name': metric_name,
        'levels_info': levels_info,
        'show_game_status': show_game_status,
    }
    return render(request, 'pages/leaderboard.html', context)

def game_list(request):
    """Список игр"""
    games = Game.objects.filter(is_active=True)
    context = {
        'games': games,
    }
    return render(request, 'games/game_list.html', context)

def game_detail(request, game_slug):
    """Детали игры"""
    game = get_object_or_404(Game, slug=game_slug)
    
    # Проверка доступа к игре
    if not game.is_active:
        return render(request, 'errors/error_access.html')
    
    # Получаем уровни из движка игры
    levels = None
    try:
        from .registry import get_game
        engine_class = get_game(game.slug)
        if engine_class and hasattr(engine_class, 'levels'):
            levels = []
            # Генерируем уровни с HTML-описанием
            if hasattr(engine_class, 'get_levels_html'):
                # Вызываем статический метод напрямую на классе
                for level_key, level_info in engine_class.levels.items():
                    levels.append({
                        'key': level_key,
                        'info': level_info,
                        'name': level_info.get('name', level_key),
                        'html': engine_class.get_levels_html(level_key, level_info)
                    })
            else:
                # Если метода get_levels_html нет, просто возвращаем уровни
                for level_key, level_info in engine_class.levels.items():
                    levels.append({
                        'key': level_key,
                        'info': level_info,
                        'name': level_info.get('name', level_key),
                        'html': ''
                    })
    except Exception as e:
        pass
    
    # Проверяем есть ли активная сессия для текущего пользователя
    active_session = None
    if request.user.is_authenticated:
        active_session = GameSession.objects.filter(
            user=request.user,
            game=game,
            status='active'
        ).first()
    
    context = {
        'game': game,
        'levels': levels,
        'active_session': active_session,
    }
    return render(request, 'games/game_detail.html', context)

# -------------------------------------------------------

@csrf_exempt
@login_required
def submit_game_result(request, session_id):
    """Обработка результата игры через AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session = get_object_or_404(GameSession, id=session_id, user=request.user)
            
            # Проверяем, что игра еще активна
            if session.status != 'active':
                return JsonResponse({'status': 'error', 'message': 'Игра уже завершена'})
            
            # Определяем статус игры на основе is_completed
            is_completed = data.get('is_completed', False)
            if is_completed:
                session.status = 'win'
            else:
                session.status = 'lose'
            
            session.finished_at = timezone.now()
            session.save()
            # Статистика вычисляется через QuerySet из GameSession
            
            return JsonResponse({'status': 'success', 'game_status': session.status})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

