from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Q

from .models import Game, GameSession


@receiver(pre_save, sender=Game)
def auto_surrender_on_disable(sender, instance, **kwargs):
    """
    При выключении игры (is_active=False) все активные сессии этой игры
    автоматически получают статус 'surrender' (сдался).
    """
    if instance.pk:
        try:
            old_instance = Game.objects.get(pk=instance.pk)
            # Если игра была включена, а становится выключенной
            if old_instance.is_active and not instance.is_active:
                from django.db.models import F
                # Помечаем все активные сессии как surrender
                # и добавляем флаг auto_surrendered в data
                affected = GameSession.objects.filter(
                    game=instance,
                    status='active'
                )
                for session in affected:
                    session.status = 'surrender'
                    session.finished_at = timezone.now()
                    session.data['auto_surrendered'] = True
                    session.save(update_fields=['status', 'finished_at', 'data'])
        except Game.DoesNotExist:
            pass
