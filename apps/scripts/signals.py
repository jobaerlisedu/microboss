from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Script
from apps.notifications.models import Notification
from apps.accounts.models import User


@receiver(pre_save, sender=Script, dispatch_uid='notify_script_status_change')
def notify_script_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Script.objects.get(pk=instance.pk)
        if old.status == instance.status:
            return
    except Script.DoesNotExist:
        return

    if instance.status == 'pending':
        admins = User.objects.filter(is_admin=True, is_active=True).exclude(pk=instance.writer_id)
        Notification.objects.bulk_create([
            Notification(
                recipient=admin,
                notification_type='Script_Submit',
                title='New Script Submitted',
                message=f'{instance.writer.full_name or instance.writer.username} submitted a script: {instance.headline[:100]}',
                link=f'/cms/scripts/{instance.id}/',
                created_by=instance.updated_by or instance.created_by,
            )
            for admin in admins
        ])

    elif instance.status == 'approved' and instance.writer:
        if instance.approved_by and instance.writer != instance.approved_by:
            Notification.objects.create(
                recipient=instance.writer,
                notification_type='Script_Approve',
                title='Script Approved',
                message=f'Your Script"{instance.headline[:100]}"Has Been Approved.',
                link=f'/cms/scripts/{instance.id}/',
                created_by=instance.approved_by,
            )
