from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notice
from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.notifications.fcm import send_push


@receiver(post_save, sender=Notice, dispatch_uid='notify_new_notice')
def notify_new_notice(sender, instance, created, **kwargs):
    if not created:
        return
    user_ids = list(User.objects.filter(is_active=True).exclude(
        id=instance.created_by_id,
    ).values_list('id', flat=True))
    notifications = [
        Notification(
            recipient_id=uid,
            notification_type='Notice',
            title=instance.title,
            message=instance.content[:200],
            link='/cms/notices/',
            created_by=instance.created_by,
        )
        for uid in user_ids
    ]
    Notification.objects.bulk_create(notifications, batch_size=500)
    if not getattr(settings, 'FCM_DISABLED', True):
        users = User.objects.filter(id__in=user_ids).only('id', 'username')
        for user in users:
            try:
                send_push(
                    user=user,
                    title=instance.title,
                    body=instance.content[:200],
                    data={'type': 'Notice', 'link': '/cms/notices/'},
                )
            except Exception:
                pass
