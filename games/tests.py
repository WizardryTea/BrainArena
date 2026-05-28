"""
Тесты для приложения games.
Тестирует модели Game, GameSession, GameSessionManager, фабрику, реестр, загрузчик, URLы и представления.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from games.models import Game, GameSession
from games.registry import REGISTRY, register_game, get_game
from games.factory import GameFactory
from games.engines.base_engine import BaseEngine


class GameModelTest(TestCase):
    """Тестирование модели Game"""

    @classmethod
    def setUpTestData(cls):
        cls.game = Game.objects.create(
            name="Тестовая игра",
            slug="test_game",
            description="Описание тестовой игры",
            short_description="Краткое описание",
            is_active=True
        )

    def test_game_creation(self):
        """Проверка создания игры"""
        self.assertEqual(self.game.name, "Тестовая игра")
        self.assertEqual(self.game.slug, "test_game")
        self.assertTrue(self.game.is_active)
        self.assertIsNotNone(self.game.created_at)

    def test_game_str(self):
        """Проверка строкового представления"""
        self.assertEqual(str(self.game), "Тестовая игра")

    def test_game_defaults(self):
        """Проверка значений по умолчанию"""
        game = Game.objects.create(name="Ещё игра", slug="another")
        self.assertEqual(game.description, "Описание игры по умолчанию")
        self.assertEqual(game.short_description, "Краткое описание игры по умолчанию")
        self.assertEqual(game.avatar, "media/avatars_games/game_base.png")
        self.assertTrue(game.is_active)

    def test_game_slug_unique(self):
        """Проверка уникальности slug"""
        with self.assertRaises(Exception):
            Game.objects.create(name="Дубликат", slug="test_game")

    def test_game_verbose_names(self):
        """Проверка verbose_name модели"""
        self.assertEqual(Game._meta.verbose_name, "Игра")
        self.assertEqual(Game._meta.verbose_name_plural, "Игры")


class GameSessionModelTest(TestCase):
    """Тестирование модели GameSession"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="testpass123")
        cls.game = Game.objects.create(name="Тест", slug="test", is_active=True)
        cls.session = GameSession.objects.create(
            user=cls.user,
            game=cls.game,
            status='active',
            data={"level": 1}
        )

    def test_session_creation(self):
        """Проверка создания сессии"""
        self.assertEqual(self.session.user, self.user)
        self.assertEqual(self.session.game, self.game)
        self.assertEqual(self.session.status, 'active')
        self.assertEqual(self.session.data, {"level": 1})

    def test_session_str(self):
        """Проверка строкового представления сессии"""
        expected = f"{self.user.username} - {self.game.name} - active"
        self.assertEqual(str(self.session), expected)

    def test_session_duration_active(self):
        """Проверка вычисления длительности для активной сессии"""
        duration = self.session.session_duration
        self.assertIsNotNone(duration)
        self.assertIn(":", duration)  # Формат ЧЧ:ММ:СС

    def test_session_duration_finished(self):
        """Проверка вычисления длительности для завершённой сессии"""
        self.session.status = 'win'
        self.session.finished_at = self.session.created_at + timedelta(minutes=5)
        self.session.save()
        self.session.refresh_from_db()
        duration = self.session.session_duration
        self.assertEqual(duration, "00:05:00")

    def test_session_duration_timedelta(self):
        """Проверка timedelta длительности"""
        self.session.status = 'win'
        self.session.finished_at = self.session.created_at + timedelta(hours=1, minutes=30)
        self.session.save()
        self.session.refresh_from_db()
        delta = self.session.session_duration_timedelta
        self.assertEqual(delta.total_seconds(), 5400)  # 1:30:00 = 5400 секунд

    def test_session_statuses(self):
        """Проверка всех статусов сессии"""
        for status in ['active', 'win', 'lose', 'surrender']:
            session = GameSession.objects.create(
                user=self.user,
                game=self.game,
                status=status
            )
            self.assertEqual(session.status, status)

    def test_session_ordering(self):
        """Проверка сортировки сессий по умолчанию (новые сверху)"""
        old = GameSession.objects.create(
            user=self.user,
            game=self.game,
            status='win',
            created_at=timezone.now() - timedelta(hours=1)
        )
        new = GameSession.objects.create(
            user=self.user,
            game=self.game,
            status='lose',
            created_at=timezone.now()
        )
        sessions = GameSession.objects.filter(id__in=[old.id, new.id]).order_by('-created_at')
        self.assertEqual(sessions[0], new)
        self.assertEqual(sessions[1], old)

    def test_session_verbose_names(self):
        """Проверка verbose_name модели GameSession"""
        self.assertEqual(GameSession._meta.verbose_name, "Игровая сессия")
        self.assertEqual(GameSession._meta.verbose_name_plural, "Игровые сессии")


class GameSessionManagerTest(TestCase):
    """Тестирование GameSessionManager"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="player1", password="pass")
        cls.user2 = User.objects.create_user(username="player2", password="pass")
        cls.game = Game.objects.create(name="Тест игра", slug="test-game")
        cls.game2 = Game.objects.create(name="Игра 2", slug="game2")

        # Создаём тестовые сессии
        for status in ['win', 'win', 'lose', 'surrender', 'win']:
            GameSession.objects.create(
                user=cls.user,
                game=cls.game,
                status=status,
                finished_at=timezone.now()
            )

        # Сессии для другой игры
        GameSession.objects.create(user=cls.user, game=cls.game2, status='win')
        GameSession.objects.create(user=cls.user, game=cls.game2, status='lose')

        # Сессии для другого пользователя
        GameSession.objects.create(user=cls.user2, game=cls.game, status='win')
        GameSession.objects.create(user=cls.user2, game=cls.game, status='lose')

    def test_get_user_stats(self):
        """Проверка получения общей статистики пользователя"""
        stats = GameSession.objects.get_user_stats(self.user)
        self.assertEqual(stats['total_games'], 7)  # 5 + 2
        self.assertEqual(stats['games_won'], 4)     # 3 + 1
        self.assertEqual(stats['games_lost'], 2)    # 1 + 1
        self.assertEqual(stats['games_surrendered'], 1)  # 1

    def test_get_user_stats_no_games(self):
        """Проверка статистики для пользователя без игр"""
        user_empty = User.objects.create_user(username="empty", password="pass")
        stats = GameSession.objects.get_user_stats(user_empty)
        self.assertEqual(stats['total_games'], 0)
        self.assertEqual(stats['games_won'], 0)
        self.assertEqual(stats['games_lost'], 0)
        self.assertEqual(stats['games_surrendered'], 0)
        self.assertEqual(stats['win_rate'], 0)

    def test_get_user_stats_win_rate(self):
        """Проверка процента побед"""
        stats = GameSession.objects.get_user_stats(self.user)
        expected_win_rate = round((4 / 7) * 100, 2)
        self.assertEqual(stats['win_rate'], expected_win_rate)

    def test_get_user_game_stats(self):
        """Проверка статистики по конкретной игре"""
        stats = GameSession.objects.get_user_game_stats(self.user, self.game)
        self.assertEqual(stats['total_games'], 5)
        self.assertEqual(stats['games_won'], 3) # 3 win
        self.assertEqual(stats['games_lost'], 1) # 1 lose
        self.assertEqual(stats['games_surrendered'], 1)  # 1 surrender

    def test_get_user_game_stats_best_time(self):
        """Проверка лучшего времени в игре"""
        # Создаём сессию с заданным временем
        session = GameSession.objects.create(
            user=self.user,
            game=self.game,
            status='win',
            created_at=timezone.now() - timedelta(minutes=2),
            finished_at=timezone.now() - timedelta(minutes=1)
        )
        stats = GameSession.objects.get_user_game_stats(self.user, self.game)
        self.assertIsNotNone(stats['best_time'])

    def test_get_user_games_progress(self):
        """Проверка прогресса пользователя по играм"""
        progress = GameSession.objects.get_user_games_progress(self.user)
        self.assertIsNotNone(progress)
        # Проверяем, что есть записи по обеим играм
        slugs = [p['game__slug'] for p in progress]
        self.assertIn('test-game', slugs)
        self.assertIn('game2', slugs)

    def test_get_all_users_stats(self):
        """Проверка статистики всех пользователей"""
        stats = GameSession.objects.get_all_users_stats()
        # Должно быть 2 пользователя
        self.assertEqual(len(stats), 2)

    def test_get_leaderboard(self):
        """Проверка таблицы лидеров"""
        board = GameSession.objects.get_leaderboard(self.game)
        self.assertIsNotNone(board)


class RegistryTest(TestCase):
    """Тестирование реестра игр"""

    def setUp(self):
        # Очищаем реестр перед каждым тестом
        REGISTRY.clear()

    def test_register_game(self):
        """Проверка регистрации игры через декоратор"""
        @register_game
        class TestRegisteredGame(BaseEngine):
            slug = "registered_game"
            name = "Registered"

        self.assertIn("registered_game", REGISTRY)
        self.assertEqual(REGISTRY["registered_game"], TestRegisteredGame)

    def test_get_game_found(self):
        """Проверка получения зарегистрированной игры"""
        @register_game
        class TestGame(BaseEngine):
            slug = "found_game"

        game_class = get_game("found_game")
        self.assertEqual(game_class, TestGame)

    def test_get_game_not_found(self):
        """Проверка получения незарегистрированной игры"""
        game_class = get_game("nonexistent")
        self.assertIsNone(game_class)

    def test_register_multiple_games(self):
        """Проверка регистрации нескольких игр"""
        @register_game
        class Game1(BaseEngine):
            slug = "game1"

        @register_game
        class Game2(BaseEngine):
            slug = "game2"

        self.assertEqual(len(REGISTRY), 2)
        self.assertIn("game1", REGISTRY)
        self.assertIn("game2", REGISTRY)


class GameFactoryTest(TestCase):
    """Тестирование фабрики игр"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="factoryuser", password="pass")
        cls.game = Game.objects.create(name="Factory Test", slug="factory-test")
        cls.session = GameSession.objects.create(user=cls.user, game=cls.game)

    def setUp(self):
        REGISTRY.clear()

    def test_create_game_from_factory(self):
        """Проверка создания движка через фабрику"""
        @register_game
        class FactoryGame(BaseEngine):
            slug = "factory-test"
            template = "test.html"

        engine = GameFactory.create(self.session)
        self.assertIsInstance(engine, FactoryGame)
        self.assertEqual(engine.session, self.session)

    def test_create_game_not_registered(self):
        """Проверка ошибки при создании незарегистрированной игры"""
        with self.assertRaises(Exception):
            GameFactory.create(self.session)


class LoaderTest(TestCase):
    """Тестирование загрузчика игр"""

    def test_sync_games(self):
        """Проверка синхронизации игр с БД"""
        from games.loader import sync_games

        # Регистрируем тестовую игру
        @register_game
        class SyncTestGame(BaseEngine):
            slug = "sync_test"
            name = "Sync Test Game"
            description = "Тестовое описание"
            short_description = "Тест кратко"
            avatar = "test_avatar.png"

        # Синхронизируем
        sync_games(force_update=True)

        # Проверяем, что игра создана в БД
        game = Game.objects.get(slug="sync_test")
        self.assertEqual(game.name, "Sync Test Game")
        self.assertEqual(game.description, "Тестовое описание")
        self.assertTrue(game.is_active)

    def test_sync_games_updates(self):
        """Проверка обновления существующей игры при force_update=True"""
        from games.loader import sync_games

        Game.objects.create(slug="existing", name="Old Name", is_active=False)

        @register_game
        class ExistingGame(BaseEngine):
            slug = "existing"
            name = "Updated Name"

        sync_games(force_update=True)

        game = Game.objects.get(slug="existing")
        self.assertEqual(game.name, "Updated Name")
        self.assertTrue(game.is_active)


class BaseEngineTest(TestCase):
    """Тестирование базового движка"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="engineuser", password="pass")
        cls.game = Game.objects.create(name="Engine Test", slug="engine-test")
        cls.session = GameSession.objects.create(user=cls.user, game=cls.game)

    def test_init(self):
        """Проверка инициализации движка"""
        engine = BaseEngine(self.session)
        self.assertEqual(engine.session, self.session)

    def test_finish_win(self):
        """Проверка завершения игры со статусом win"""
        engine = BaseEngine(self.session)
        engine.finish('win')
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'win')
        self.assertIsNotNone(self.session.finished_at)

    def test_finish_lose(self):
        """Проверка завершения игры со статусом lose"""
        engine = BaseEngine(self.session)
        engine.finish('lose')
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'lose')

    def test_finish_surrender(self):
        """Проверка завершения игры со статусом surrender"""
        engine = BaseEngine(self.session)
        engine.finish('surrender')
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'surrender')

    def test_process_action_win(self):
        """Проверка обработки действия win"""
        engine = BaseEngine(self.session)
        engine.process_action("win")
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'win')

    def test_process_action_lose(self):
        """Проверка обработки действия lose"""
        engine = BaseEngine(self.session)
        engine.process_action("lose")
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'lose')

    def test_process_action_empty(self):
        """Проверка обработки пустого действия"""
        engine = BaseEngine(self.session)
        engine.process_action("")
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'active')

    def test_get_game_end_html(self):
        """Проверка HTML для завершения игры"""
        engine = BaseEngine(self.session)
        html = engine.get_game_end_html()
        self.assertIn("active", html)

        engine.finish('win')
        html = engine.get_game_end_html()
        self.assertIn("Победа", html)

    def test_static_methods(self):
        """Проверка статических методов"""
        self.assertEqual(BaseEngine.get_leaderboard_metric_name(), "")
        self.assertEqual(BaseEngine.get_leaderboard_sort_field(), "session_duration")
        self.assertIsNone(BaseEngine.get_leaderboard_secondary_sort_field())

    def test_levels(self):
        """Проверка атрибута levels"""
        engine = BaseEngine(self.session)
        self.assertIsNone(engine.levels)


class AdminRegistrationTest(TestCase):
    """Тестирование регистрации моделей в админке"""

    def test_admin_import(self):
        """Проверка импорта admin.py без ошибок"""
        try:
            import games.admin
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"games/admin.py вызвал ошибку: {e}")


class URLTest(TestCase):
    """Тестирование URL-маршрутов"""

    def test_game_list_url(self):
        """Проверка URL списка игр"""
        url = reverse('games:game_list')
        self.assertEqual(url, '/games/')

    def test_game_detail_url(self):
        """Проверка URL деталей игры"""
        url = reverse('games:game_detail', args=['test-game'])
        self.assertEqual(url, '/games/test-game/')

    def test_leaderboard_url(self):
        """Проверка URL таблицы лидеров"""
        url = reverse('games:leaderboard')
        self.assertEqual(url, '/games/leaderboard/')


class ViewTest(TestCase):
    """Тестирование представлений"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="viewuser", password="pass12345")
        cls.game = Game.objects.create(
            name="View Test Game",
            slug="view-test",
            is_active=True
        )
        # Создаём игры, которые запрашивает home view
        Game.objects.create(name="2048", slug="2048", is_active=True)
        Game.objects.create(name="Hanoi Towers", slug="hanoi_towers", is_active=True)
        Game.objects.create(name="Bulls and Cows", slug="bulls_and_cows", is_active=True)
        cls.client = Client()

    def test_home_page(self):
        """Проверка главной страницы"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_game_list_view(self):
        """Проверка страницы списка игр"""
        response = self.client.get(reverse('games:game_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'games/game_list.html')

    def test_game_detail_view(self):
        """Проверка страницы деталей игры"""
        response = self.client.get(reverse('games:game_detail', args=['view-test']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'games/game_detail.html')

    def test_game_detail_not_found(self):
        """Проверка 404 для несуществующей игры"""
        response = self.client.get(reverse('games:game_detail', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)

    def test_game_detail_inactive(self):
        """Проверка, что неактивная игра показывает error_access.html"""
        inactive = Game.objects.create(name="Inactive", slug="inactive", is_active=False)
        response = self.client.get(reverse('games:game_detail', args=['inactive']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'errors/error_access.html')

    def test_leaderboard_view(self):
        """Проверка страницы таблицы лидеров"""
        response = self.client.get(reverse('games:leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/leaderboard.html')

    def test_start_game_requires_auth(self):
        """Проверка, что старт игры требует авторизации"""
        response = self.client.get(reverse('games:start', args=[self.game.id]))
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={reverse('games:start', args=[self.game.id])}"
        )

    def test_start_game_authenticated(self):
        """Проверка старта игры для авторизованного пользователя"""
        self.client.login(username="viewuser", password="pass12345")
        response = self.client.get(reverse('games:start', args=[self.game.id]))
        # Проверяем, что создана сессия и произошел редирект на игру
        self.assertEqual(response.status_code, 302)
        session = GameSession.objects.filter(user=self.user, game=self.game, status='active').first()
        self.assertIsNotNone(session)

    def test_surrender_all_active_games(self):
        """Проверка завершения всех активных игр"""
        self.client.login(username="viewuser", password="pass12345")

        # Создаём активные сессии
        session1 = GameSession.objects.create(user=self.user, game=self.game, status='active')

        response = self.client.post(reverse('games:surrender_all_active_games'))
        self.assertRedirects(response, reverse('users:profile'))

        # Проверяем, что сессии завершены
        session1.refresh_from_db()
        self.assertEqual(session1.status, 'surrender')

    def test_game_end_page(self):
        """Проверка страницы завершения игры"""
        # Регистрируем движок для игры, чтобы GameFactory.create не упал
        @register_game
        class ViewTestEngine(BaseEngine):
            slug = "view-test"
            template = "games/games_list/view_test.html"
            name = "View Test Game"

        self.client.login(username="viewuser", password="pass12345")
        session = GameSession.objects.create(
            user=self.user,
            game=self.game,
            status='win',
            finished_at=timezone.now()
        )
        response = self.client.get(reverse('games:game_end', args=[session.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'games/game_end.html')

    def test_game_end_active_session_redirect(self):
        """Проверка редиректа с active сессии на страницу игры"""
        self.client.login(username="viewuser", password="pass12345")
        session = GameSession.objects.create(user=self.user, game=self.game, status='active')
        response = self.client.get(reverse('games:game_end', args=[session.id]))
        # Проверяем только код и URL редиректа, без перехода по нему
        expected_url = reverse('games:game_play', args=[session.id])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
