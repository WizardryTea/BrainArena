from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import uuid
import os


class UserProfile(models.Model):
    """Расширенный профиль пользователя"""
    
    GENDER_CHOICES = [
        ('unknown', 'Неизвестно'),
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]
    
    EDUCATION_CHOICES = [
        ('not_specified', 'Не указано'),
        ('none', 'Не имею образования (детский сад, дети 0+, до 6-7 лет)'),
        ('studying', 'Обучаюсь в настоящее время (школьники, студенты колледжей и вузов)'),
        ('incomplete_secondary', 'Неполное среднее (школа, 9 классов)'),
        ('secondary', 'Среднее общее (школа, 11 классов)'),
        ('vocational', 'Среднее профессиональное образование (колледж, ПТУ)'),
        ('higher', 'Высшее образование (бакалавриат, специалитет, магистратура)'),
        ('postgraduate', 'Послевузовское образование (аспирантура, ординатура, кандидат наук, доктор наук)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='unknown', verbose_name="Пол")
    age = models.IntegerField(null=True, blank=True, default=None, verbose_name="Возраст")
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES, default='not_specified', verbose_name="Образование")
    is_public = models.BooleanField(default=True, verbose_name="Публичный профиль")
    show_hidden_games = models.BooleanField(default=True, verbose_name="Показывать выключенные игры")
    created_at = models.DateTimeField(auto_now_add=True)
        
    @property
    def avatar_url(self):
        """
        Всегда возвращает валидный URL аватара пользователя.
        """
        from django.conf import settings
        
        # Если есть аватар
        if self.avatar and self.avatar.name:
            # Для базовых аватаров (из статики)
            if self.avatar.name.startswith('avatars_base/'):
                return f"{settings.STATIC_URL}{self.avatar.name}"
            
            # Для загруженных аватаров
            try:
                return self.avatar.url
            except (ValueError, OSError):
                # Если ошибка при получении URL
                pass
        
        # Дефолтный аватар
        return f"{settings.STATIC_URL}avatars_base/default.png"


    @staticmethod
    def get_base_avatars():
        """Возвращает список базовых аватаров из avatars_base в статике"""
        import os
        from django.conf import settings
        
        avatars = []
        # ищем папку avatars_base в статических файлах
        # исп-ем STATICFILES_DIRS для поиска
        static_dir = settings.BASE_DIR / 'static'
        avatars_dir = os.path.join(static_dir, 'avatars_base')
        
        if os.path.exists(avatars_dir):
            for filename in sorted(os.listdir(avatars_dir)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    avatars.append({
                        'name': filename,
                        'url': f"{settings.STATIC_URL}avatars_base/{filename}"
                    })
        
        return avatars
            
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        return f"Профиль {self.user.username}"


# Сигналы для автоматического создания профиля пользователя

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()


# --- Сигналы для удаления файла аватара в случае удаления или изменения аватара ---
@receiver(pre_save, sender=UserProfile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    """Удаляет старый файл аватара из media/avatars при замене новым.
    Не трогает файлы из avatars_base."""
    try:
        old = None
        if instance.pk:
            old = UserProfile.objects.get(pk=instance.pk).avatar
        new = instance.avatar
        if old and old != new:
            old_path = old.path
            # Удаляем ТОЛЬКО если это не базовый аватар
            if (os.path.exists(old_path) and 
                '/avatars/' in old_path.replace('\\','/') and
                'avatars_base' not in old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
    except UserProfile.DoesNotExist:
        pass

@receiver(post_delete, sender=UserProfile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    """Удаляет файл аватара при удалении профиля (если он в avatars, не базовый)."""
    if instance.avatar:
        try:
            path = instance.avatar.path
            if (os.path.exists(path) and 
                '/avatars/' in path.replace('\\','/') and
                'avatars_base' not in path):
                os.remove(path)
        except Exception:
            pass