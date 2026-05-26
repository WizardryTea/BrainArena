"""
Тесты для приложения brain_arena (конфигурация проекта).
Тестирует настройки, URL-конфигурацию, WSGI/ASGI
"""
from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve
from django.conf import settings
import os


class SettingsTest(SimpleTestCase):
    """Тестирование настроек проекта"""

    def test_debug_false_in_test(self):
        """Проверка, что DEBUG=False в тестовом режиме"""
        self.assertFalse(settings.DEBUG)

    def test_language_code(self):
        """Проверка языковых настроек"""
        self.assertEqual(settings.LANGUAGE_CODE, "ru")
        self.assertEqual(settings.TIME_ZONE, "Europe/Moscow")
        self.assertTrue(settings.USE_I18N)
        self.assertTrue(settings.USE_TZ)

    def test_allowed_hosts(self):
        """Проверка ALLOWED_HOSTS"""
        self.assertIn('*', settings.ALLOWED_HOSTS)

    def test_installed_apps(self):
        """Проверка установленных приложений"""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'crispy_forms',
            'crispy_bootstrap5',
            'games',
            'users',
        ]
        for app in required_apps:
            with self.subTest(app=app):
                self.assertIn(app, settings.INSTALLED_APPS)

    def test_middleware(self):
        """Проверка middleware"""
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
        for middleware in required_middleware:
            with self.subTest(middleware=middleware):
                self.assertIn(middleware, settings.MIDDLEWARE)

    def test_static_settings(self):
        """Проверка настроек статических файлов"""
        self.assertEqual(settings.STATIC_URL, '/static/')
        self.assertEqual(settings.MEDIA_URL, '/media/')

    def test_login_urls(self):
        """Проверка настроек авторизации"""
        self.assertEqual(settings.LOGIN_URL, '/accounts/login/')
        self.assertEqual(settings.LOGIN_REDIRECT_URL, '/')
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, '/')

    def test_crispy_settings(self):
        """Проверка настроек crispy forms"""
        self.assertIn('bootstrap5', settings.CRISPY_ALLOWED_TEMPLATE_PACKS)
        self.assertEqual(settings.CRISPY_TEMPLATE_PACK, 'bootstrap5')

    def test_default_auto_field(self):
        """Проверка default_auto_field"""
        self.assertEqual(settings.DEFAULT_AUTO_FIELD, 'django.db.models.BigAutoField')

    def test_template_dirs(self):
        """Проверка директорий шаблонов"""
        self.assertTrue(any('templates' in str(d) for d in settings.TEMPLATES[0]['DIRS']))

    def test_staticfiles_dirs(self):
        """Проверка директорий статических файлов"""
        self.assertTrue(any('static' in str(d) for d in settings.STATICFILES_DIRS))


class URLConfigTest(SimpleTestCase):
    """Тестирование URL-конфигурации"""

    def test_admin_url(self):
        """Проверка URL админки"""
        url = reverse('admin:index')
        self.assertEqual(url, '/admin/')

    def test_home_url(self):
        """Проверка URL главной страницы"""
        url = reverse('home')
        self.assertEqual(url, '/')

    def test_accounts_login_url(self):
        """Проверка URL логина"""
        url = reverse('login')
        self.assertEqual(url, '/accounts/login/')

    def test_accounts_logout_url(self):
        """Проверка URL логаута"""
        url = reverse('logout')
        self.assertEqual(url, '/accounts/logout/')

    def test_users_register_url(self):
        """Проверка URL регистрации"""
        url = reverse('users:register')
        self.assertEqual(url, '/users/register/')

    def test_users_profile_url(self):
        """Проверка URL профиля"""
        url = reverse('users:profile')
        self.assertEqual(url, '/users/profile/')

    def test_games_list_url(self):
        """Проверка URL списка игр"""
        url = reverse('games:game_list')
        self.assertEqual(url, '/games/')

    def test_confidential_url(self):
        """Проверка URL страницы конфиденциальности"""
        url = reverse('confidential')
        self.assertEqual(url, '/confidential/')

    def test_about_url(self):
        """Проверка URL страницы о нас"""
        url = reverse('about')
        self.assertEqual(url, '/about/')


class WSGIASGITest(SimpleTestCase):
    """Тестирование WSGI/ASGI конфигурации"""

    def test_wsgi_application(self):
        """Проверка WSGI application"""
        from brain_arena.wsgi import application
        self.assertIsNotNone(application)

    def test_asgi_application(self):
        """Проверка ASGI application"""
        from brain_arena.asgi import application
        self.assertIsNotNone(application)


class DatabaseSettingsTest(SimpleTestCase):
    """Тестирование настроек базы данных"""

    def test_database_engine(self):
        """Проверка наличия движка БД"""
        self.assertIn('default', settings.DATABASES)
        engine = settings.DATABASES['default']['ENGINE']
        self.assertTrue(
            engine.startswith('django.db.backends.'),
            f"Некорректный движок БД: {engine}"
        )

    def test_database_name_defined(self):
        """Проверка наличия имени БД"""
        self.assertIn('NAME', settings.DATABASES['default'])


class PasswordValidatorsTest(SimpleTestCase):
    """Тестирование валидаторов паролей"""

    def test_password_validators_configured(self):
        """Проверка, что валидаторы паролей настроены"""
        self.assertTrue(len(settings.AUTH_PASSWORD_VALIDATORS) > 0)

    def test_minimum_length_validator(self):
        """Проверка наличия валидатора минимальной длины"""
        validator_names = [v['NAME'] for v in settings.AUTH_PASSWORD_VALIDATORS]
        self.assertIn(
            'django.contrib.auth.password_validation.MinimumLengthValidator',
            validator_names
        )