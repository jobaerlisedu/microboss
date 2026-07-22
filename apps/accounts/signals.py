from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User
from apps.notifications.models import Notification


@receiver(pre_save, sender=User, dispatch_uid='notify_registration_approval')
def notify_registration_approval(sender, instance, **kwargs):
    if not instance.pk:
        return
    if instance.pending_approval:
        return
    try:
        old = User.objects.get(pk=instance.pk)
        if old.pending_approval and not instance.pending_approval and instance.is_active:
            approver = User.objects.filter(is_admin=True, is_active=True).exclude(pk=instance.pk).first()
            Notification.objects.create(
                recipient=instance,
                notification_type='registration',
                title='Your registration has been approved',
                message='Your registration has been approved. You can login now.',
                link='/cms/',
                created_by=approver,
            )
    except User.DoesNotExist:
        pass
