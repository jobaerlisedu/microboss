from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from apps.notifications.models import Notification


@receiver(post_save, sender=User)
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
                title='আপনার রেজিস্ট্রেশন অনুমোদিত হয়েছে',
                message=f'আপনার রেজিস্ট্রেশন অনুমোদিত হয়েছে। আপনি এখন লগইন করতে পারেন।',
                link='/cms/',
                created_by=approver,
            )
    except User.DoesNotExist:
        pass
