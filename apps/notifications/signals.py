from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification
from .fcm import send_push


@receiver(post_save, sender=Notification)
def push_on_notification(sender, instance, created, **kwargs):
    if not created:
        return
    if getattr(settings, 'FCM_DISABLED', True):
        return
    try:
        send_push(
            user=instance.recipient,
            title=instance.title,
            body=instance.message[:200],
            data={
                'type': instance.notification_type,
                'id': str(instance.id),
                'link': instance.link or '',
            },
        )
    except Exception:
        pass
