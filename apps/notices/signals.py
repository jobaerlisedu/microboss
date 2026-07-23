from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notice
from apps.notifications.models import Notification
from apps.accounts.models import User


@receiver(post_save, sender=Notice, dispatch_uid='notify_new_notice')
def notify_new_notice(sender, instance, created, **kwargs):
    if not created:
        return
    users = User.objects.filter(is_active=True).exclude(
        id=instance.created_by_id,
    ).values_list('id', flat=True)
    notifications = [
        Notification(
            recipient_id=uid,
            notification_type='Notice',
            title=instance.title,
            message=instance.content[:200],
            link='/cms/notices/',
            created_by=instance.created_by,
        )
        for uid in users
    ]
    Notification.objects.bulk_create(notifications, batch_size=500)
