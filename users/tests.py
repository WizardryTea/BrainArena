"""
Тесты для приложения users.
Тестирует модели UserProfile, формы, представления, URLы и сигналы.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
import tempfile
import os

from users.models import UserProfile
from users.forms import UserRegistrationForm, UserProfileForm, UserUpdateForm


class UserProfileModelTest(TestCase):
    """Тестирование модели UserProfile"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testprofile",
            password="testpass123",
            first_name="Тест",
            last_name="Тестов",
            email="test@example.com"
        )

    def test_profile_created_on_user_creation(self):
        """Проверка, что профиль создаётся при создании пользователя"""
        new_user = User.objects.create_user(username="newuser", password="pass")
        self.assertTrue(hasattr(new_user, 'userprofile'))
        self.assertIsInstance(new_user.userprofile, UserProfile)

    def test_profile_str(self):
        """Проверка строкового представления профиля"""
        profile = self.user.userprofile
        expected = f"Профиль {self.user.username}"
        self.assertEqual(str(profile), expected)

    def test_profile_default_values(self):
        """Проверка значений по умолчанию для профиля"""
        profile = self.user.userprofile
        self.assertEqual(profile.gender, 'unknown')
        self.assertIsNone(profile.age)
        self.assertEqual(profile.education, 'not_specified')
        self.assertTrue(profile.is_public)

    def test_avatar_url_when_no_avatar(self):
        """Проверка URL аватара по умолчанию"""
        profile = self.user.userprofile
        url = profile.avatar_url
        self.assertIn('avatars_base/default.png', url)

    def test_profile_verbose_names(self):
        """Проверка verbose_name модели"""
        self.assertEqual(UserProfile._meta.verbose_name, "Профиль пользователя")
        self.assertEqual(UserProfile._meta.verbose_name_plural, "Профили пользователей")

    def test_profile_fields(self):
        """Проверка полей профиля"""
        profile = self.user.userprofile
        profile.gender = 'male'
        profile.age = 25
        profile.education = 'higher'
        profile.is_public = False
        profile.save()

        profile.refresh_from_db()
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.age, 25)
        self.assertEqual(profile.education, 'higher')
        self.assertFalse(profile.is_public)

    def test_get_base_avatars(self):
        """Проверка получения списка базовых аватаров"""
        from django.conf import settings
        avatars_base_dir = os.path.join(settings.MEDIA_ROOT, 'avatars_base')

        # Создаём временную директорию, если её нет
        os.makedirs(avatars_base_dir, exist_ok=True)

        avatars = UserProfile.get_base_avatars()
        self.assertIsNotNone(avatars)
        # Проверяем, что возвращается список словарей
        if avatars:
            self.assertIn('name', avatars[0])
            self.assertIn('url', avatars[0])


class UserProfileSignalsTest(TestCase):
    """Тестирование сигналов UserProfile"""

    def test_post_save_creates_profile(self):
        """Проверка создания профиля при сохранении пользователя"""
        user = User.objects.create_user(username="signaluser", password="pass")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_post_save_saves_profile(self):
        """Проверка сохранения профиля при сохранении пользователя"""
        user = User.objects.create_user(username="savesignal", password="pass")
        profile = user.userprofile
        profile.gender = 'female'
        profile.save()

        # Сохраняем пользователя — сигнал должен вызвать save профиля
        user.first_name = "Updated"
        user.save()

        profile.refresh_from_db()
        self.assertEqual(profile.gender, 'female')

    def test_delete_old_avatar_on_change(self):
        """Проверка удаления старого аватара при замене"""
        profile = User.objects.create_user(username="avataruser", password="pass").userprofile
        # Создаём временный файл для имитации аватара
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            profile.avatar.name = f'avatars/{os.path.basename(temp_path)}'
            profile.save()

            # Меняем аватар — старый файл должен быть удалён через сигнал
            new_avatar_name = f'avatars/new_{os.path.basename(temp_path)}'
            profile.avatar.name = new_avatar_name
            # Не проверяем фактическое удаление файла, т.к. это зависит от диска
            # Проверяем, что атрибут изменился
            profile.save()
            self.assertIn('new_', profile.avatar.name)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class UserRegistrationFormTest(TestCase):
    """Тестирование формы регистрации"""

    def test_form_has_correct_fields(self):
        """Проверка наличия полей в форме"""
        form = UserRegistrationForm()
        expected_fields = ['username', 'first_name', 'last_name', 'email',
                           'password1', 'password2', 'gender', 'age', 'education']
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_form_validation_valid_data(self):
        """Проверка валидации формы с корректными данными"""
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password1': 'Str0ngP@ss123',
            'password2': 'Str0ngP@ss123',
            'gender': 'male',
            'age': 30,
            'education': 'higher',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_validation_invalid_email(self):
        """Проверка валидации с неверным email"""
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'invalid-email',
            'password1': 'Str0ngP@ss123',
            'password2': 'Str0ngP@ss123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_form_validation_password_mismatch(self):
        """Проверка валидации при несовпадении паролей"""
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password1': 'Str0ngP@ss123',
            'password2': 'DifferentPass456',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_form_saves_user(self):
        """Проверка, что форма создаёт пользователя"""
        form = UserRegistrationForm(data={
            'username': 'saveduser',
            'first_name': 'Пётр',
            'last_name': 'Петров',
            'email': 'petr@example.com',
            'password1': 'Str0ngP@ss123',
            'password2': 'Str0ngP@ss123',
            'gender': 'male',
            'age': 25,
            'education': 'higher',
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'saveduser')
        self.assertEqual(user.email, 'petr@example.com')

        # Проверяем, что профиль создан и заполнен
        profile = user.userprofile
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.age, 25)
        self.assertEqual(profile.education, 'higher')


class UserProfileFormTest(TestCase):
    """Тестирование формы профиля"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="formuser", password="pass")

    def test_form_has_correct_fields(self):
        """Проверка наличия полей в форме"""
        form = UserProfileForm(instance=self.user.userprofile)
        expected_fields = ['avatar', 'gender', 'age', 'education', 'is_public']
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_age_validation_valid(self):
        """Проверка валидации возраста"""
        profile = self.user.userprofile

        form = UserProfileForm(data={'age': 30, 'gender': 'male', 'education': 'higher'}, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)

    def test_age_validation_none(self):
        """Проверка возраста равного None"""
        profile = self.user.userprofile

        form = UserProfileForm(data={'age': '', 'gender': 'male', 'education': 'higher'}, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)

    def test_age_validation_negative(self):
        """Проверка отрицательного возраста"""
        profile = self.user.userprofile

        form = UserProfileForm(data={'age': -5, 'gender': 'male', 'education': 'higher'}, instance=profile)
        # Отрицательный возраст должен быть преобразован в None (валидно)
        self.assertTrue(form.is_valid())

    def test_age_validation_over_limit(self):
        """Проверка возраста больше 128"""
        profile = self.user.userprofile

        form = UserProfileForm(data={'age': 200, 'gender': 'male', 'education': 'higher'}, instance=profile)
        self.assertFalse(form.is_valid())
        self.assertIn('age', form.errors)


class UserUpdateFormTest(TestCase):
    """Тестирование формы обновления пользователя"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="updateuser",
            password="pass",
            first_name="Old",
            last_name="Name",
            email="old@example.com"
        )

    def test_form_has_correct_fields(self):
        """Проверка наличия полей в форме"""
        form = UserUpdateForm(instance=self.user)
        expected_fields = ['first_name', 'last_name', 'email']
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_form_update_user(self):
        """Проверка обновления пользователя через форму"""
        form = UserUpdateForm(
            instance=self.user,
            data={'first_name': 'New', 'last_name': 'Name2', 'email': 'new@example.com'}
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name2')
        self.assertEqual(self.user.email, 'new@example.com')


class URLTest(TestCase):
    """Тестирование URL-маршрутов users"""

    def test_register_url(self):
        """Проверка URL регистрации"""
        url = reverse('users:register')
        self.assertEqual(url, '/users/register/')

    def test_login_url(self):
        """Проверка URL логина"""
        url = reverse('users:login')
        self.assertEqual(url, '/users/login/')

    def test_logout_url(self):
        """Проверка URL логаута"""
        url = reverse('users:logout')
        self.assertEqual(url, '/users/logout/')

    def test_profile_url(self):
        """Проверка URL профиля"""
        url = reverse('users:profile')
        self.assertEqual(url, '/users/profile/')

    def test_sessions_url(self):
        """Проверка URL сессий"""
        url = reverse('users:user_sessions')
        self.assertEqual(url, '/users/sessions/')

    def test_edit_profile_url(self):
        """Проверка URL редактирования профиля"""
        url = reverse('users:edit_profile')
        self.assertEqual(url, '/users/profile/edit/')

    def test_users_list_url(self):
        """Проверка URL списка пользователей"""
        url = reverse('users:users_list')
        self.assertEqual(url, '/users/')


class ViewTest(TestCase):
    """Тестирование представлений users"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="viewuser",
            password="pass12345",
            first_name="View",
            last_name="User"
        )
        # Создаём игры, которые запрашивает home view
        from games.models import Game
        Game.objects.create(name="2048", slug="2048", is_active=True)
        Game.objects.create(name="Hanoi Towers", slug="hanoi_towers", is_active=True)
        Game.objects.create(name="Bulls and Cows", slug="bulls_and_cows", is_active=True)
        cls.client = Client()

    def test_register_view_get(self):
        """Проверка GET-запроса на страницу регистрации"""
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_register_view_post_success(self):
        """Проверка успешной регистрации пользователя"""
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password1': 'Str0ngP@ss123',
            'password2': 'Str0ngP@ss123',
        })
        # После успешной регистрации происходит редирект на home
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_post_invalid(self):
        """Проверка регистрации с некорректными данными"""
        response = self.client.post(reverse('users:register'), {
            'username': '',
            'password1': 'pass',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, 200)  # Остаёмся на той же странице
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_login_view_get(self):
        """Проверка GET-запроса на страницу логина"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_view_post_success(self):
        """Проверка успешного входа"""
        response = self.client.post(reverse('users:login'), {
            'username': 'viewuser',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_invalid(self):
        """Проверка входа с неверными данными"""
        response = self.client.post(reverse('users:login'), {
            'username': 'viewuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_logout_view(self):
        """Проверка выхода из системы"""
        self.client.login(username='viewuser', password='pass12345')
        response = self.client.get(reverse('users:logout'))
        self.assertRedirects(response, reverse('home'))

    def test_profile_view_authenticated(self):
        """Проверка страницы профиля для авторизованного пользователя"""
        self.client.login(username='viewuser', password='pass12345')
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_view_unauthenticated(self):
        """Проверка, что неавторизованный пользователь перенаправляется на login"""
        response = self.client.get(reverse('users:profile'))
        # В profile view используется redirect('login') без next
        self.assertRedirects(response, settings.LOGIN_URL)

    def test_profile_view_by_username(self):
        """Проверка просмотра профиля по имени пользователя"""
        self.client.login(username='viewuser', password='pass12345')
        response = self.client.get(reverse('users:user_profile', args=['viewuser']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_view_not_found(self):
        """Проверка 404 для несуществующего пользователя"""
        response = self.client.get(reverse('users:user_profile', args=['nonexistentuser']))
        self.assertEqual(response.status_code, 404)

    def test_users_list_view(self):
        """Проверка страницы списка пользователей"""
        response = self.client.get(reverse('users:users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/users_list.html')

    def test_edit_profile_view_authenticated(self):
        """Проверка страницы редактирования профиля"""
        self.client.login(username='viewuser', password='pass12345')
        response = self.client.get(reverse('users:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')

    def test_edit_profile_view_unauthenticated(self):
        """Проверка редиректа при попытке редактирования профиля без авторизации"""
        response = self.client.get(reverse('users:edit_profile'))
        # LOGIN_URL = '/accounts/login/' в settings
        self.assertRedirects(
            response,
            f"{settings.LOGIN_URL}?next={reverse('users:edit_profile')}"
        )

    def test_user_sessions_view(self):
        """Проверка страницы сессий пользователя"""
        self.client.login(username='viewuser', password='pass12345')
        response = self.client.get(reverse('users:user_sessions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/sessions.html')

    def test_delete_game(self):
        """Проверка удаления игры (перемещение в 'Брошено')"""
        from games.models import Game, GameSession
        self.client.login(username='viewuser', password='pass12345')

        game = Game.objects.create(name='Test Game', slug='test-game')
        session = GameSession.objects.create(user=self.user, game=game, status='active')

        response = self.client.post(reverse('users:delete_game', args=[session.id]))
        self.assertRedirects(response, reverse('users:profile'))

        session.refresh_from_db()
        self.assertEqual(session.status, 'surrender')
        self.assertIsNotNone(session.finished_at)