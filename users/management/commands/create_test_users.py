import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Создает тестовых пользователей'

    def handle(self, *args, **options):
        """Handle the command"""
        def get_available_base_avatars() -> list:
            """Return a list of available base avatars"""
            avatars_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'media',
                'avatars_base'
            )
        def get_available_base_avatars():
            """Возвращает список файлов базовых аватаров"""
            avatars_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media', 'avatars_base')
            if not os.path.exists(avatars_dir):
                return []
            return [
                f for f in os.listdir(avatars_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
            ]

        base_avatars = get_available_base_avatars()
        self.stdout.write(
            self.style.SUCCESS(f"Found {len(base_avatars)} base avatars")
        )
        self.stdout.write(self.style.SUCCESS(f"Найдено базовых аватаров: {len(base_avatars)}"))

        test_users = [
            {
                'username': 'administrator',
                'email': 'admin@brainarena.ru',
                'first_name': 'Алексей',
                'last_name': 'Петров',
                'password': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'profile': {
                    'bio': 'Администратор платформы Brain Arena',
                    'is_public': False,
                    'avatar': 'mirea.png'
                }
            },
            {
                'username': 'moderator',
                'email': 'moderator@brainarena.ru',
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'password': 'admin',
                'is_staff': True,
                'profile': {
                    'bio': 'Модератор игрового сообщества',
                    'is_public': False,
                    'avatar': 'mirea.png'
                }
            },
            {
                'username': 'ivanov',
                'email': 'ivanov@example.com',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'password': 'test',
                'profile': {
                    'bio': 'Люблю судоку и головоломки',
                    'is_public': True,
                    'avatar': 'man.png'
                }
            },
            {
                'username': 'sokolova',
                'email': 'sokolova@example.com',
                'first_name': 'Анна',
                'last_name': 'Соколова',
                'password': 'test',
                'profile': {
                    'bio': 'Фанат логических игр и математики',
                    'is_public': True,
                    'avatar': 'girl2.png'
                }
            },
        ]

        created = 0
        updated = 0

        for data in test_users:
            profile_data = data.pop('profile')
            password = data.pop('password')

            user, is_created = User.objects.get_or_create(
                username=data['username'],
                defaults=data
            )

            if is_created:
                user.set_password(password)
                user.save()
                created += 1
            else:
                for k, v in data.items():
                    setattr(user, k, v)
                user.set_password(password)
                user.save()
                updated += 1

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.bio = profile_data.get('bio', '')
            profile.is_public = profile_data.get('is_public', True)

            avatar_name = profile_data.get('avatar')
            if avatar_name and avatar_name in base_avatars:
                profile.avatar.name = f'avatars_base/{avatar_name}'
            elif base_avatars:
                profile.avatar.name = f'avatars_base/{random.choice(base_avatars)}'

            profile.save()

            self.stdout.write(
                self.style.SUCCESS(f"+++ {user.username} — profile updated")
            )
            self.stdout.write(self.style.SUCCESS(f"+++ {user.username} — профиль обновлён"))

        self.stdout.write(self.style.SUCCESS("\nИТОГ:"))
        self.stdout.write(self.style.SUCCESS(f"Создано пользователей: {created}"))
        self.stdout.write(self.style.SUCCESS(f"Обновлено пользователей: {updated}"))
        self.stdout.write(self.style.SUCCESS(f"Всего пользователей: {User.objects.count()}"))
